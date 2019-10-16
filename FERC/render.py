from arelle import PluginManager
from arelle.CntlrWebMain import Options
from copy import deepcopy
from lxml import etree

import datetime
import collections
import html
import json
import logging
import optparse

# This will hold the xule plugin module
_xule_plugin_info = None

# xule namespace used in the template
_XULE_NAMESPACE_MAP = {'xule': 'http://xbrl.us/xule/2.0/template', 'xhtml': 'http://www.w3.org/1999/xhtml'}
_XHTM_NAMESPACE = 'http://www.w3.org/1999/xhtml'
_RULE_NAME_PREFIX = 'rule-'
_CLASS_RULE_NAME_PREFIX = 'class-'

class FERCRenderException(Exception):
    pass

def getXulePlugin(cntlr):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
    """
    global _xule_plugin_info
    if _xule_plugin_info is None:
        for _plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == 'xule':
                _xule_plugin_info = plugin_info
                break
        else:
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run DQC rules. This plugin should be automatically loaded."))
    
    return _xule_plugin_info

def getXuleMethod(cntlr, method_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(method_name)


def process_template(cntlr, template_file_name):
    '''Prepare the template to substitute values

    1. build the xule rules from the template
    2. identify where in the template to substitution caluldated values
    '''

    # Open the template
    try:
        with open(template_file_name) as fp:
            template_tree = etree.parse(fp)
    except FileNotFoundError:
        cntlr.addToLog("Template file '{}' is not found.".format(template_file_name), 'error', level=logging.ERROR)
        raise FERCRenderException

    except etree.XMLSchemaValidateError:
        cntlr.addToLog("Template file '{}' is not a valid XHTML file.".format(template_file_name), 'error', level=logging.ERROR)
        raise FERCRenderException  

    # build the namespace declaration for xule
    xule_namespaces = build_xule_namespaces(template_tree)
    # build constants
    xule_constants = build_constants()
    # create the rules for xule and retrieve the update template with the substitutions identified.
    xule_rules, substitutions = build_xule_rules(template_tree, template_file_name)

    line_number_subs = build_line_number_subs(template_tree)

    return '{}\n{}\n{}'.format(xule_namespaces, xule_constants, xule_rules), substitutions,  line_number_subs, template_tree

def build_xule_namespaces(template_tree):
    '''build the namespace declarations for xule

    Convert the namespaces on the template to namespace declarations for xule. This will only use the 
    namespaces that are declared on the root element of the template.
    '''
    namespaces = ['namespace {}={}'.format(k, v) if k is not None else 'namespace {}'.format(v) for k, v in template_tree.getroot().nsmap.items()]
    return '\n'.join(namespaces)


def build_constants():
    '''Create constants used by the expressions. '''
    constants = \
'''
// These constants need to be overwritten when processing.
constant $current-start = None
constant $current-end = None
constant $prior-start = None
constant $prior-end = None

constant $currentInstant = date($current-end)
constant $currentDuration = duration(date($current-start), date($current-end))
constant $priorInstant = date($prior-end)
constant $priorDuration = duration(date($prior-start), date($prior-end))
'''

    return constants

def build_xule_rules(template_tree, template_file_name):
    '''Extract the rules and identify the subsititions in the template

    1. Create the xule rules
    2. Identify where the subsitutions will be
    '''
    
    substitutions = collections.defaultdict(list)
    xule_rules = []
    next_rule_number = 1
    # Using an ordered dict so that the named rules are build in the order of the rule in the template.
    named_rules = collections.OrderedDict()
    xule_node_locations = {template_tree.getelementpath(xule_node): node_number for  node_number, xule_node in enumerate(template_tree.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}

    substitutions, xule_rules, next_rule_number, named_rules = build_unamed_rules(substitutions, 
                                                                                  xule_rules, 
                                                                                  next_rule_number, 
                                                                                  named_rules, 
                                                                                  template_tree, 
                                                                                  template_file_name, xule_node_locations)
    substitutions, xule_rules, next_rule_number, named_rules = build_named_rules(substitutions, 
                                                                                 xule_rules, 
                                                                                 next_rule_number, 
                                                                                 named_rules, 
                                                                                 template_tree, 
                                                                                 template_file_name,
                                                                                 xule_node_locations)
    return '\n\n'.join(xule_rules), substitutions

def build_unamed_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name, xule_node_locations):

    # Go through each of the xule expressions in the template
    for xule_expression in template_tree.findall('//xule:expression', _XULE_NAMESPACE_MAP):
        named_rule = xule_expression.get("name")
        if named_rule is None:
            # This is a single rule
            rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
            next_rule_number += 1

            replacement_node = xule_expression.getparent()
            if replacement_node.tag != '{{{}}}{}'.format(_XULE_NAMESPACE_MAP['xule'], 'replace'):
                replacement_node = xule_expression
                class_expressions = tuple()
            else: # this is a xule:replace
                # process xule:class nodes
                class_expressions = format_class_expressions(replacement_node)

            comment_text = '    // {} - line {}'.format(template_file_name, xule_expression.sourceline)
            if xule_expression.get('fact','').lower() == 'true':
                sub_content ={'part': None, 
                              'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                              'expression-node': xule_node_locations[template_tree.getelementpath(xule_expression)],
                              'result-focus-index': 0}
                #rule_text = 'output {}\n{}\nlist((({})#rv-0).string).to-json\nrule-focus list($rv-0)'.format(rule_name, comment_text, xule_expression.text.strip())

                rule_text = 'output {rule_name}\n{comment}\n{result_text}\nrule-focus list($rv-0)'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             'f',
                                                                                             class_expressions))
                             )
            else: # not a fact
                sub_content = {'part': None, 
                               'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                               'result-text-index': 0}
                #rule_text = 'output {}\n{}\nlist(({}).string).to-json'.format(rule_name, comment_text, xule_expression.text.strip())
                rule_text = 'output {rule_name}\n{comment}\n{result_text}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             's',
                                                                                             class_expressions))
                             )
            xule_rules.append(rule_text)

            if xule_expression.get('html', 'false').lower() == 'true':
                sub_content['html'] = True
            substitutions[rule_name].append(sub_content)
        else: # This is a named rule
            # Saved the named rule part for later
            part = xule_expression.get('part', None)
            if named_rule not in named_rules:
                named_rules[named_rule] = []
            named_rules[named_rule].append((part, xule_expression))

    return substitutions, xule_rules, next_rule_number, named_rules

def format_rule_result_text_part(expression_text, part, type, class_expressions):

    output_dictionary = dict()
    output_dictionary['type'] = "'{}'".format(type)
    if type == 'f':
        output_dictionary['is-fact'] = 'if exists({exp}) (({exp}).is-fact).string else \'false\''.format(exp=expression_text)
    if part is None:
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
    else:
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=part)
        output_dictionary['part'] = part
    
    output_items = ("list('{key}', {val})".format(key=k, val=v) for k, v in output_dictionary.items())
    output_string = "dict({})".format(', '.join(output_items))

    return output_string
    '''
    # If the output is not fact then we don't need the is-fact in the result.
    output_is_fact = None
    if type == 'f':
        output_is_fact = 'if exists({exp}) (({exp}).is-fact).string else \'false\''.format(exp=expression_text)
    output_class_expressions = ", list('classes', list({}))".format(', '.join(class_expressions)) if len(class_expressions) > 0 else ''
    if part is None:
        output_expression = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
        return "dict(list('type', '{type}'), list('is-fact', {is_fact}), list('value', {val}){classes})".format(
            type=type, 
            is_fact=output_is_fact, 
            val=output_expression,
            classes=output_class_expressions)
    else:
        output_expression = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=part)
        return "dict(list('type', '{type}'), list('is-fact', {is_fact}), list('value', {val}), list('part', {part}){classes})".format(
            type=type, 
            is_fact=output_is_fact, 
            val=output_expression,
            part=part,
            classes=output_class_expressions)
    '''
def build_named_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name, xule_node_locations):
    # Handle named rules
    for named_rule, part_list in named_rules.items():
        # Sort the part list by the part number
        part_list.sort(key=lambda x: (x[0] is not None, x[0]) if x is not None else (False, '')) # This will put the None part first
        result_parts = []
        rule_focus = []
        comments = []
        preliminary_rule_text = ''

        rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
        next_rule_number += 1
        next_focus_number = 0
        next_text_number = 0
        for part, expression in part_list:
            replacement_node = expression.getparent()
            if replacement_node.tag != '{{{}}}{}'.format(_XULE_NAMESPACE_MAP['xule'], 'replace'):
                replacement_node = expression
                class_expressions = tuple()
            else: # this is a xule:replace
                class_expressions = format_class_expressions(replacement_node)

            comments.append('    // {} - {}'.format(template_file_name, expression.sourceline))
            if part is None:
                preliminary_rule_text = expression.text.strip()
            else:
                if expression.get("fact", "").lower() == 'true':
                    # If the this part of the rule is a fact, then add a tag that will be used in the rule focus
                    #result_parts.append('list((({exp})#rv-{part}).string, exists({exp}))'.format(exp=expression.text.strip(), part=part))
                    result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                                next_text_number,
                                                                                                'f',
                                                                                                class_expressions)
                                                        )
                    )
                    
                    rule_focus.append('$rv-{}'.format(next_text_number))
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': xule_node_locations[tempalte_tree.getelementpath(replacement_node)],
                                   'expression-node': xule_node_locations[template_tree.getelementpath(expression)],
                                   'result-focus-index': next_focus_number,
                                   'result-text-index': next_text_number}
                    if expression.get('html', 'false').lower() == 'true':
                        sub_content['html'] = True
                    substitutions[rule_name].append(sub_content)
                    next_focus_number += 1
                else:
                    #result_parts.append('({}).string'.format(expression.text.strip()))
                    result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                                next_text_number,
                                                                                                's',
                                                                                                class_expressions)
                                                        )
                    )
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                                   'result-text-index': next_text_number}
                    if expression.get('html', 'false').lower == 'true':
                        sub_content['html'] = True                                   
                    substitutions[rule_name].append(sub_content)

                next_text_number += 1

        #build rule text
        rule_text = 'output {}\n'.format(rule_name)
        rule_text += '\n'.join(comments) + '\n'
        rule_text += '\n{}'.format(preliminary_rule_text)
        result_text = ',\n'.join(["{}".format(expression) for expression in result_parts])
        
        rule_text += '\nlist({}).to-json'.format(result_text)
        if len(rule_focus) > 0:
            focus_text = 'list({})'.format(', '.join(rule_focus))
            rule_text += '\nrule-focus {}'.format(focus_text)

        xule_rules.append(rule_text)
    return substitutions, xule_rules, next_rule_number, named_rules

def format_class_expressions(replacement_node):
    class_expressions= []
    for class_node in replacement_node.findall('{{{}}}class'.format(etree.QName(replacement_node).namespace)): # This is just a easy way to get the ns of the replacement_node
        class_expressions.append('list("{}",{})'.format(class_node.attrib.get('location', 'self'), class_node.text.strip())) 

    return class_expressions      

def build_line_number_subs(template_tree):
    line_number_subs = collections.defaultdict(list)
    for line_number_node in template_tree.findall('//xule:lineNumber', _XULE_NAMESPACE_MAP):
        name = line_number_node.get('name')
        if name is not None:
            line_number_subs[name].append(line_number_node)

    return line_number_subs

def substituteTemplate(substitutions, line_number_subs, rule_results, template, modelXbrl):
    '''Subsititute the xule expressions in the template with the generated values.'''
    xule_node_locations = {node_number: xule_node for  node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}
    
    repeat_attribute_name = '{{{}}}{}'.format(_XULE_NAMESPACE_MAP['xule'], 'repeat')
    repeating_nodes = {x.get(repeat_attribute_name): x for x in template.findall('//*[@xule:repeat]', _XULE_NAMESPACE_MAP)}

    # Separtate the substitutions that repeat from the non repeating. This will allow the non repeating substitutions to be
    # done first, so if a repeating node has a non repeating substitution, it will happend before the repeating node
    # is copied.
    non_repeating = []
    repeating = []
    for rule_name, subs in substitutions.items():
        if len(subs) > 0 and subs[0].get('name') in repeating_nodes:
            repeating.append((rule_name, subs))
        else:
            non_repeating.append((rule_name, subs))

    # Sort the repeating so that the deepest template node substitutions are processed first. This will allow repeating within
    # repeating.
    def sort_by_ancestors(key):
        subs = key[1]
        if len(subs) == 0:
            return 0
        return len([x for x in xule_node_locations[subs[0]['replacement-node']].iterancestors()])

    repeating.sort(key=sort_by_ancestors, reverse=True)

    for rule_name, subs in non_repeating + repeating:
        # Determine if this is a repeating rule.
        new_nodes = []
        if len(subs) > 0 and subs[0].get('name') in repeating_nodes:
            # This is a repeating rule
            repeating_model_node = repeating_nodes[subs[0].get('name')]
            model_tree = etree.ElementTree(repeating_model_node)
            repeat_count = 0            
        else:
            repeating_model_node = None

        for rule_result in rule_results[rule_name]:
            json_rule_result = json.loads(rule_result.msg)

            if repeating_model_node is not None:
                # Copy the model of the repeating node. This will be used to do the actual substitutions
                repeat_count += 1
                new_node = deepcopy(repeating_model_node)
                new_nodes.append(new_node)
                new_tree = etree.ElementTree(new_node)
                
                # Replace lineNumber nodes
                substitute_line_numbers(repeat_count, line_number_subs, subs[0]['name'], model_tree, new_tree, modelXbrl)
                
            for sub_index, sub in enumerate(subs):
                # The value for the replacement is either text from running the rule or a fact
                # The sub is a dictionary. If it has a result-text-index key, then the text is taken
                # If it has a rule-focus-index key, then the value is a fact
                if isinstance(json_rule_result, list):
                    json_result = None
                    for x in json_rule_result:
                        if x['part'] == sub_index:
                            json_result = x
                            break
                elif sub_index == 0:
                    json_result = json_rule_result
                else:
                    raise FERCRenderException('internal error: expected a list of results from the rule but only got one')
                
                classes_from_result = get_classes(json_result)
                # Add classes that go on the span that will replace the xule:relace node
                span_classes = classes_from_result.get('self',[])
                # if the json_result is none, there is nothing to substitute
                if json_result is not None:
                    # Check if the result is a fact
                    if json_result['type'] == 'f':
                        rule_focus_index = adjust_result_focus_index(json_rule_result, json_result.get('part', None))
                        if rule_focus_index is None:
                            # No fact was found in the instance
                            text_content = None
                        else:
                            fact_object_index = rule_result.refs[rule_focus_index]['objectId']
                            model_fact = modelXbrl.modelObject(fact_object_index)
                            text_content, inline_format_clark = format_fact(xule_node_locations[sub['expression-node']], model_fact)
                    elif json_result['type'] == 's': # result is a string
                        text_content = json_result['value']

                    if text_content is None:
                        span_content = '<span/>'
                        span_classes += ['sub-value', 'sub-no-replacement']
                    else:
                        if not sub.get('html', False):
                            # This is not html content, so the text needs to be escaped
                            text_content = html.escape(text_content)
                        span_content = '<span>{}</span>'.format(text_content)  
                        span_classes += ['sub-value', 'sub-replacement']
                    
                    span = etree.fromstring(span_content)
                    span.set('class', ' '.join(span_classes))

                    # Get the node in the template to replace
                    if repeating_model_node is None:
                        sub_node = xule_node_locations[sub['replacement-node']]
                    else:
                        # Find the node in the repeating model node
                        try:
                            model_path = model_tree.getelementpath(xule_node_locations[sub['replacement-node']])
                        except ValueError:
                            # The node to be replaced is not a descendant of the repeating note.
                            modelXbrl.warning("RenderError", "A 'replace' replacement for '{}' is not a descendant of the repeating HTML element.".format(sub['name']))
                            sub_node = None
                        else:                        
                            sub_node = new_tree.find(model_path)
                            
                    if sub_node is not None:
                        sub_parent = sub_node.getparent()
                        sub_parent.replace(sub_node, span)
                        if len(classes_from_result['parent']) > 0:
                            sub_parent.set('class', ' '.join(sub_parent.get('class','').split() + classes_from_result['parent']))
            
        # Add the new repeating nodes
        for new_node in reversed(new_nodes):
            repeating_model_node.addnext(new_node)
        
        # Remove the model node
        if repeating_model_node is not None:
            model_parent = repeating_model_node.getparent()
            model_parent.remove(repeating_model_node)

    # Remove any left over xule:replace nodes
    for xule_node in template.findall('//xule:replace', _XULE_NAMESPACE_MAP):
        parent = xule_node.getparent()
        span = etree.Element('span')
        span.set('class', '"sub-value sub-no-replacement')
        parent.replace(xule_node, span)

    # Remove any left over xule template nodes
    for xule_node in template.findall('//xule:*', _XULE_NAMESPACE_MAP):
        parent = xule_node.getparent()
        parent.remove(xule_node)

    return template

def adjust_result_focus_index(json_results, part):
    '''Adjust the index for the rule focus fact

    The original index is the the index of the rule focus list where the fact is. However, if there is no fact,
    the rule focus list will just skip that place in the list. For example, if a result has three facts, the rule focus list should be
    list(fact1, fact2, fact3). However, if fact 2 is missing, then the rule focus list will only be list(fact1, fact2). The index for
    fact3 is 1 instead of the expected 2.
    '''
    rule_focus_index = -1

    if isinstance(json_results, list):
        results_by_part = {x['part']: x for x in json_results}

        # If the part did not return a fact than there is nothing in the rule focus to find.
        if results_by_part[part]['is-fact'].lower() == 'false':
            return None

        # This is a list of results
        for i in range(part + 1):
            if (i in results_by_part and 
                results_by_part[i]['type'] == 'f' and 
                results_by_part[i]['value'] is not None and 
                results_by_part[i]['is-fact'].lower() == 'true'):
                rule_focus_index +=1
    else:
        # The results is really just a single dictionary of one results. Just check if the fact is there
        if json_results['is-fact'].lower() == 'true':
            rule_focus_index = 0

    return rule_focus_index if rule_focus_index >= 0 else None

def substitute_line_numbers(line_number, line_number_subs, name, model_tree, new_tree, modelXbrl):

    # Substitute xule:lineNumber nodes in the repeating model
    for line_number_node in line_number_subs.get(name, tuple()):
        # Find the xule:lineNumber node in the repeating model node
        try:
            model_path = model_tree.getelementpath(line_number_node)
        except ValueError:
            # The node to be replaced is not a descendant of the repeating note.
            modelXbrl.warning("RenderError", "A 'lineNumber' replacement for '{}' is not a descendant of the repeating HTML element.".format(name))
        else:
            sub_node = new_tree.find(model_path)
            # Create new span with the line number
            new_line_number_span = etree.Element('{{{}}}span'.format(_XHTM_NAMESPACE))
            new_line_number_span.set('class', 'sub-line-number')
            new_line_number_span.text = str(line_number)
            # Substitute
            sub_parent = sub_node.getparent()
            sub_parent.replace(sub_node, new_line_number_span)     

def get_classes(json_result):
    '''Get the classes from the evaluation of the xule:class expressions

    This is returned as a list of strings.
    '''

    # The join/split will normalize whitespaces in the result
    # Get a list of classes for each class location. The class location will be at index 0 and the class value will be at intext 1
    classes = collections.defaultdict(list)
    if json_result is None:
        return classes

    for item in json_result.get('classes', tuple()):
        # The split will normalize whitespaces in the result
        classes[item[0]].extend(item[1].split())

    return classes
    

    #return [' '.join(x.split()) for x in json_result.get('classes', tuple())]

def get_dates(modelXbrl):
    '''This returns a dictionary of dates for the filing'''

    report_year_fact = get_fact_by_local_name(modelXbrl, 'ReportYear')
    report_period_fact = get_fact_by_local_name(modelXbrl, 'ReportPeriod')
    if report_period_fact is None:
        report_period_fact = get_fact_by_local_name(modelXbrl, 'ReportYearPeriod')

    if report_year_fact is None or report_period_fact is None:
        modelXbrl.error(_("Cannot obtain the report year or report period from the XBRL document"))
        raise FERCRenderException

    month_day = {'Q4': ('01-01', '12-31'),
                 'Q3': ('07-01', '12-31'),
                 'Q2': ('04-01', '06-30'),
                 'Q1': ('01-01', '03-31')}
    
    current_start = '{}-{}'.format(report_year_fact.value, month_day[report_period_fact.value][0])
    current_end ='{}-{}'.format(report_year_fact.value, month_day[report_period_fact.value][1])
    prior_start = '{}-{}'.format(int(report_year_fact.value) - 1, month_day[report_period_fact.value][0])
    prior_end = '{}-{}'.format(int(report_year_fact.value) - 1, month_day[report_period_fact.value][1])
    
    return (('current-start={}'.format(current_start)),
            ('current-end={}'.format(current_end)),
            ('prior-start={}'.format(prior_start)),
            ('prior-end={}'.format(prior_end)))

def get_fact_by_local_name(modelXbrl, fact_name):
    for fact in modelXbrl.factsInInstance:
        if fact.concept.qname.localName == fact_name:
            return fact
    
    return None

# def fercMenuTools(cntlr, menu):
#     import tkinter
  
#     def fercRender():
#         global _INSTANCE_MODEL
#         if _INSTANCE_MODEL is None:
#             tkinter.messagebox.showinfo("FERC Renderer", "Need to load an instance document in order to render")
#         elif _INSTANCE_MODEL.modelDocument.type not in (Type.INSTANCE, Type.INLINEXBRL):
#             tkinter.messagebox.showinfo("FERC Renderer", "Loaded document is not an instance")
#         else:
#             # Extract the formLocation references from the Arelle model
#             refs = get_references(_INSTANCE_MODEL, _CONCEPT_REFERENCE)
            
#             if _INSTANCE_MODEL.modelManager.cntlr.userAppDir is None:
#                 raise Exception(_("Arelle does not have a user application data directory. Cannot save rendered file"))            
#             render_file_name = os.path.join(cntlr.userAppDir, 'plugin', 'ferc',  os.path.splitext(_INSTANCE_MODEL.modelDocument.basename)[0] + '.html')            
            
#             render(render_file_name, _INSTANCE_MODEL, refs)        
#             webbrowser.open(render_file_name)

#     fercMenu = tkinter.Menu(menu, tearoff=0)
#     fercMenu.add_command(label=_("Render"), underline=0, command=fercRender)

#     menu.add_cascade(label=_("FERC"), menu=fercMenu, underline=0)

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "FERC Renderer")
        parser.add_option_group(parserGroup)
    
    parserGroup.add_option("--ferc-render-template", 
                      action="store", 
                      dest="ferc_render_template", 
                      help=_("The HTML template file"))

    parserGroup.add_option("--ferc-render-inline", 
                      action="store", 
                      dest="ferc_render_inline", 
                      help=_("The generated Inline XBRL file"))        
                      
    parserGroup.add_option("--ferc-render-xule-file", 
                      action="store", 
                      dest="ferc_render_xule_file", 
                      help=_("The generated xule rule file")) 

    parserGroup.add_option("--ferc-render-xule-rule-set", 
                      action="store", 
                      dest="ferc_render_xule_rule_set", 
                      help=_("The generated xule rule set file")) 

    parserGroup.add_option("--ferc-render-xule-only", 
                      action="store_true", 
                      dest="ferc_render_xule_only", 
                      help=_("Only generate the xule rule file. This option will not parse the file or create the rendered template"))  

def fercCmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()
    
    if options.ferc_render_template is None:
        parser.error(_("--ferc-render-template is required."))

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):

    if options.ferc_render_template is not None:
        # Process the HTML template.
        xule_rule_text, substitutions, line_number_subs, template = process_template(cntlr, options.ferc_render_template)
        
        # Compile Xule rules
        title = template.find('//xhtml:title', _XULE_NAMESPACE_MAP)
        if title is None:
            cntlr.addToLog("Template does not have a title", "error")
            raise FERCRenderException

        # xule file name
        xule_rule_file_name = options.ferc_render_xule_file or '{}.xule'.format(title.text)
        with open(xule_rule_file_name, 'w') as xule_file:
            xule_file.write(xule_rule_text)

        cntlr.addToLog(_("Writing xule rule file: {}".format(xule_rule_file_name)), 'info')

        if options.ferc_render_xule_only:
            cntlr.addToLog(_("Generated xule rule file '{}'".format(xule_rule_file_name)))
            # Stop the processing
            return

        # xule rule set name
        xule_rule_set_name = options.ferc_render_xule_rule_set or '{}.zip'.format(title.text)
        compile_method = getXuleMethod(cntlr, 'Xule.compile')
        compile_method(xule_rule_file_name, xule_rule_set_name, 'json')
        
        # Get the date values from the instance
        xule_date_args = get_dates(modelXbrl)

        # Run Xule rules
        # Create a log handler that will capture the messages when the rules are run.
        log_capture_handler = _logCaptureHandler()
        cntlr.logger.addHandler(log_capture_handler)

        # Call the xule processor to run the rules
        call_xule_method = getXuleMethod(cntlr, 'Xule.callXuleProcessor')
        run_options = deepcopy(options)
        xule_args = getattr(run_options, 'xule_arg', []) or []
        xule_args += list(xule_date_args)
        setattr(run_options, 'xule_arg', xule_args)

        call_xule_method(cntlr, modelXbrl, xule_rule_set_name, run_options)
        
        # Remove the handler from the logger. This will stop the capture of messages
        cntlr.logger.removeHandler(log_capture_handler)
        
        # Substitute template
        rendered_template = substituteTemplate(substitutions, line_number_subs, log_capture_handler.captured, template, modelXbrl)
        

        # Write rendered template
        if options.ferc_render_inline is None:
            inline_name = '{} - rendered.html'.format(title.text)
        else:
            inline_name = options.ferc_render_inline

        rendered_template.write(inline_name, pretty_print=True, method="xml", encoding='utf8', xml_declaration=True)

        cntlr.addToLog(_("Rendered template '{}' as '{}'".format(options.ferc_render_template, inline_name)), 'info')
        
class _logCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._captured = collections.defaultdict(list)

    def emit(self, record):
        self._captured[record.messageCode].append(record)
    
    @property
    def captured(self):
        return self._captured

def format_fact(xule_expression_node, model_fact):
    if xule_expression_node is None:
        format = None
    else:
        format = xule_expression_node.get('format')
    if format is None:
        return str(model_fact.xValue), None
    else:
        # convert format to clark notation 
        if ':' in format:
            prefix, local_name = format.split(':', 1)
        else:
            prefix = ''
            local_name = format
        ns = xule_expression_node.nsmap.get(prefix)
        if ns is None:
            raise FERCRenderException('Format {} is not a valid format'.format(format))

        format_clark = '{{{}}}{}'.format(ns, local_name)
        format_function = _formats.get(format_clark)
        if format_function is None:
            raise FERCRenderException('Format {} is not a valid format'.format(format))

        return format_function(model_fact), format_clark

_formats = {'{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}numcommadot': lambda mf: '{:,}'.format(mf.xValue),
            '{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}dateslashus': lambda mf: mf.xValue.strftime('%m/%d/%Y')}

__pluginInfo__ = {
    'name': 'FERC Tools',
    'version': '0.9',
    'description': "FERC Tools",
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': fercCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}