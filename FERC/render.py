from arelle import PluginManager
from arelle.CntlrWebMain import Options
from copy import deepcopy
from lxml import etree

import datetime
import decimal
import collections
import html
import io
import json
import logging
import optparse
import os.path
import tempfile
import zipfile

# This will hold the xule plugin module
_xule_plugin_info = None

# xule namespace used in the template
_XULE_NAMESPACE_MAP = {'xule': 'http://xbrl.us/xule/2.0/template', 
                       'xhtml': 'http://www.w3.org/1999/xhtml',
                       'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
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
    2. identify stylesheets
    3. identify where in the template to substitute calculated values
    4. create a template set
    '''

    # Open the template
    try:
        with open(template_file_name, 'rb') as fp:
            template_tree = etree.fromstring(fp.read().decode('utf-8')).getroottree()
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
    # Create list of Xule nodes in the template
    xule_node_locations = {template_tree.getelementpath(xule_node): node_number for  node_number, xule_node in enumerate(template_tree.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}
    # create the rules for xule and retrieve the update template with the substitutions identified.
    xule_rules, substitutions, line_number_subs = build_xule_rules(template_tree, template_file_name, xule_node_locations)

    # Get the css file name from the template
    css_file_names = tuple(x for x in template_tree.xpath('/xhtml:html/xhtml:head/xhtml:link[@rel="stylesheet" and @type="text/css"]/@href', namespaces=_XULE_NAMESPACE_MAP))

    return '{}\n{}\n{}'.format(xule_namespaces, xule_constants, xule_rules), substitutions,  line_number_subs, template_tree, css_file_names

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

def build_xule_rules(template_tree, template_file_name, xule_node_locations):
    '''Extract the rules and identify the subsititions in the template

    1. Create the xule rules
    2. Identify where the subsitutions will be
    '''
    
    substitutions = collections.defaultdict(list)
    xule_rules = []
    next_rule_number = 1
    # Using an ordered dict so that the named rules are build in the order of the rule in the template.
    named_rules = collections.OrderedDict()

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
    # Create rules for starting line numbers.                                                                                 
    line_number_subs, xule_rules, next_rule_number = build_line_number_rules(xule_rules, next_rule_number, template_tree, xule_node_locations)   

    return '\n\n'.join(xule_rules), substitutions, line_number_subs

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
                extra_expressions = tuple()
            else: # this is a xule:replace
                # process xule:class nodes
                extra_expressions = format_extra_expressions(replacement_node)

            comment_text = '    // {} - line {}'.format(template_file_name, xule_expression.sourceline)
            if xule_expression.get('fact','').lower() == 'true':
                sub_content ={'part': None, 
                              'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                              'expression-node': xule_node_locations[template_tree.getelementpath(xule_expression)],
                              'result-focus-index': 0,
                              'template-line-number': xule_expression.sourceline}
                #rule_text = 'output {}\n{}\nlist((({})#rv-0).string).to-json\nrule-focus list($rv-0)'.format(rule_name, comment_text, xule_expression.text.strip())

                rule_text = 'output {rule_name}\n{comment}\n{result_text}\nrule-focus list($rv-0)'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             'f',
                                                                                             extra_expressions))
                             )
            else: # not a fact
                sub_content = {'part': None, 
                               'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                               'result-text-index': 0,
                               'template-line-number': xule_expression.sourceline}
                #rule_text = 'output {}\n{}\nlist(({}).string).to-json'.format(rule_name, comment_text, xule_expression.text.strip())
                rule_text = 'output {rule_name}\n{comment}\n{result_text}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             's',
                                                                                             extra_expressions))
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

def format_rule_result_text_part(expression_text, part, type, extra_expressions):

    output_dictionary = dict()
    output_dictionary['type'] = "'{}'".format(type)
    

    if type == 'f':
        output_dictionary['is-fact'] = 'if exists({exp}) (({exp}).is-fact).string else \'false\''.format(exp=expression_text)
    if part is None:
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
    else:
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=part)
        output_dictionary['part'] = part
    # Extra expressions (i.e. class, format, scale)
    for extra_name, extra_expression in extra_expressions.items():
        output_extra_expressions = "list({})".format(', '.join(extra_expression)) if len(extra_expression) > 0 else None
        if output_extra_expressions is not None:
            output_dictionary[extra_name] = output_extra_expressions
    
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
                extra_expressions = tuple()
            else: # this is a xule:replace
                extra_expressions = format_extra_expressions(replacement_node)

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
                                                                                                extra_expressions)
                                                        )
                    )
                    
                    rule_focus.append('$rv-{}'.format(next_text_number))
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                                   'expression-node': xule_node_locations[template_tree.getelementpath(expression)],
                                   'result-focus-index': next_focus_number,
                                   'result-text-index': next_text_number,
                                   'template-line-number': expression.sourceline}
                    if expression.get('html', 'false').lower() == 'true':
                        sub_content['html'] = True
                    substitutions[rule_name].append(sub_content)
                    next_focus_number += 1
                else:
                    #result_parts.append('({}).string'.format(expression.text.strip()))
                    result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                                next_text_number,
                                                                                                's',
                                                                                                extra_expressions)
                                                        )
                    )
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                                   'result-text-index': next_text_number,
                                   'template-line-number': expression.sourceline}
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

def format_extra_expressions(replacement_node):
    extra_expressions= collections.defaultdict(list)
    for extra_node in replacement_node.findall('{{{}}}*'.format(etree.QName(replacement_node).namespace)):
        extra_name = etree.QName(extra_node.tag).localname
        if extra_name == 'class':
            location = extra_node.attrib.get('location', 'self')
        elif extra_name in ('format', 'scale', 'sign', 'decimals'): # this are inline attributes
            location = 'inline'
        else:
            # This is some other element in the xule:replace, just skip it.
            continue
        
        extra_expressions[extra_name].append('list("{}",{})'.format(location, extra_node.text.strip())) 

    #for class_node in replacement_node.findall('{{{}}}class'.format(etree.QName(replacement_node).namespace)): # This is just a easy way to get the ns of the replacement_node
    #    extra_expressions.append('list("{}",{})'.format(class_node.attrib.get('location', 'self'), class_node.text.strip())) 

    return extra_expressions      

def build_line_number_rules(xule_rules, next_rule_number, template_tree, xule_node_locations):
    line_number_subs = collections.defaultdict(list)
    for line_number_node in template_tree.findall('//xule:lineNumber', _XULE_NAMESPACE_MAP):
        name = line_number_node.get('name')
        if name is not None:
            # Check if there is a staring number
            start_expression_node = line_number_node.find('xule:startNumber', _XULE_NAMESPACE_MAP)
            if start_expression_node is None:
                start_value = 1
                is_simple = True
            else:
                try:
                    # if this is a simple integer, there is no need to create a rule for it. 
                    start_value = int(start_expression_node.text.strip())
                    is_simple = True
                except ValueError:
                    # The expression is not a simple integer. Need to create a rule for it
                    is_simple = False
                    rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
                    next_rule_number += 1
                    rule_text = 'output {rule_name}\n{rule_text}'.format(rule_name=rule_name, rule_text=start_expression_node.text.strip())
                    xule_rules.append(rule_text)
            if is_simple:
                line_number_subs[name].append({'line-number-node': xule_node_locations[template_tree.getelementpath(line_number_node)], 
                                               'start-number': start_value,
                                               'template-line-number': line_number_node.sourceline})
            else:
                line_number_subs[name].append({'line-number-node': xule_node_locations[template_tree.getelementpath(line_number_node)], 
                                               'start-rule': rule_name,
                                               'template-line-number': line_number_node.sourceline})

    return line_number_subs, xule_rules, next_rule_number

def substituteTemplate(substitutions, line_number_subs, rule_results, template, modelXbrl, main_html):
    '''Subsititute the xule expressions in the template with the generated values.'''
    xule_node_locations = {node_number: xule_node for  node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}
    
    set_line_number_starts(line_number_subs, rule_results)

    context_ids = set()
    unit_ids = set()

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
                substitute_line_numbers(repeat_count, line_number_subs, subs[0]['name'], model_tree, new_tree, modelXbrl, xule_node_locations)
                
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
                            content = None
                        else:
                            fact_object_index = rule_result.refs[rule_focus_index]['objectId']
                            model_fact = modelXbrl.modelObject(fact_object_index)
                            content = format_fact(xule_node_locations[sub['expression-node']], model_fact, main_html, sub.get('html', False))
                            # Save the context and unit ids
                            context_ids.add(model_fact.contextID)
                            if model_fact.unitID is not None:
                                unit_ids.add(model_fact.unitID)
                    elif json_result['type'] == 's': # result is a string
                        if sub.get('html', False):
                            content = etree.fromstring('<div class="sub-html">{}</div>'.format(json_result['value']))
                        elif json_result['value'] is not None:
                            content = html.escape(json_result['value'])
                        else:
                            content = None

                    if content is None:
                        span_classes += ['sub-value', 'sub-no-replacement']
                    else:
                        span_classes += ['sub-value', 'sub-replacement']
                        
                    span = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
                    span.set('class', ' '.join(span_classes))
                    if isinstance(content, str):
                        span.text = content
                    elif content is not None:
                        span.append(content)

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
        span = etree.Element('div')
        span.set('class', 'sub-value sub-no-replacement')
        parent.replace(xule_node, span)

    # Remove any left over xule template nodes
    for xule_node in template.findall('//xule:*', _XULE_NAMESPACE_MAP):
        parent = xule_node.getparent()
        parent.remove(xule_node)
    
    # Remove any left over xule attributes
    for xule_node in template.xpath('//*[@xule:*]', namespaces=_XULE_NAMESPACE_MAP):
        for att_name in xule_node.keys():
            if att_name.startswith('{{{}}}'.format(_XULE_NAMESPACE_MAP['xule'])):
                del xule_node.attrib[att_name]

    return template, context_ids, unit_ids

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

def set_line_number_starts(line_number_subs, rule_results):
    for line_numbers in line_number_subs.values():
        for line_number_info in line_numbers:
            if 'start-rule' in line_number_info:
                start_result = rule_results.get(line_number_info['start-rule'], None)
                if start_result is None:
                    # didn't get a result, just assume 1
                    start_value = 1
                else:
                    try:
                        start_value = int(start_result[0].msg.strip())
                    except ValueError:
                        # didn't an integer back, default to 1
                        start_value = 1
                line_number_info['start-number'] = start_value

def substitute_line_numbers(line_number, line_number_subs, name, model_tree, new_tree, modelXbrl, xule_node_locations):

    # Substitute xule:lineNumber nodes in the repeating model
    for line_number_info in line_number_subs.get(name, tuple()):
        line_number_node = xule_node_locations[line_number_info['line-number-node']]
        # Find the xule:lineNumber node in the repeating model node
        try:
            model_path = model_tree.getelementpath(line_number_node)
        except ValueError:
            # The node to be replaced is not a descendant of the repeating note.
            modelXbrl.warning("RenderError", "A 'lineNumber' replacement for '{}' is not a descendant of the repeating HTML element.".format(name))
        else:
            start_value = line_number_info.get('start-number', 1) - 1

            sub_node = new_tree.find(model_path)
            # Create new span with the line number
            new_line_number_span = etree.Element('{{{}}}span'.format(_XHTM_NAMESPACE))
            new_line_number_span.set('class', 'sub-line-number')
            new_line_number_span.text = str(line_number + start_value)
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

    for item in json_result.get('class', tuple()):
        # item[0] is the location for the class (self or parent)
        # item[1] is the generated value for the class, if it exists
        # The split will normalize whitespaces in the result
        if len(item) == 2:
            # If the item only has one item in it, then the class expression did not create a value and it can be skipped.
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

def setup_inline_html(modelXbrl):
    # Create the new HTML rendered document
    # Add namespace prefixes
    namespaces = {None: "http://www.w3.org/1999/xhtml",
        'xtr2': "http://www.xbrl.org/inlineXBRL/transformation/2010-04-20",
        'xbrli': "http://www.xbrl.org/2003/instance",
        'ix': "http://www.xbrl.org/2013/inlineXBRL",
        'xbrldi': "http://xbrl.org/2006/xbrldi",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'link': "http://www.xbrl.org/2003/linkbase",
        'xlink': "http://www.w3.org/1999/xlink"}
    # Find namespaces in the instance document and add them
    for prefix, uri in modelXbrl.modelDocument.xmlRootElement.nsmap.items():
        if uri not in namespaces.values():
            if prefix not in namespaces:
                namespaces[prefix] = uri
            else:
                # Handle case when the prefix is already there, but for a different namespace uri
                i = 0
                while 'ns{}'.format(i) in namespaces:
                    i += 1
                namespaces['ns{}'.format(i)] = uri
    namespace_string = ' '.join(('{}="{}"'.format('xmlns' if k is None else 'xmlns:{}'.format(k), v) for k, v in namespaces.items()))

    initial_html_content = \
        '<?xml version="1.0"?>' \
        '<html {}>' \
        '<head>' \
        '<title>FERC Form</title>' \
        '<meta content="text/html; charset=UTF-8" http-equiv="Content-Type"/>' \
        '<style>div.sub-value {{display: inline-block;}}</style>' \
        '</head>' \
        '<body><div style="display:none"><ix:header><ix:references/><ix:resources/></ix:header></div></body>' \
        '</html>'.format(namespace_string)

    html = etree.fromstring(initial_html_content)

    # Add schema and linbase references
    irefs = html.find('.//ix:references', namespaces=_XULE_NAMESPACE_MAP)
    for doc_ref in modelXbrl.modelDocument.referencesDocument.values():
        if doc_ref.referringModelObject.elementNamespaceURI == 'http://www.xbrl.org/2003/linkbase':
            if doc_ref.referringModelObject.localName == 'schemaRef' and doc_ref.referenceType == 'href':
                link = etree.SubElement(irefs, '{http://www.xbrl.org/2003/linkbase}schemaRef')
                link.set('{http://www.w3.org/1999/xlink}type', 'simple')
                link.set('{http://www.w3.org/1999/xlink}href', doc_ref.referringModelObject.attrib['{http://www.w3.org/1999/xlink}href'])
            elif doc_ref.referringModelObject.localName == 'linbaseRef' and doc_ref.referenceType == 'href':
                link = etree.SubElement(irefs, '{http://www.xbrl.org/2003/linkbase}linkbaseRef')
                link.set('{http://www.w3.org/1999/xlink}type', 'simple')
                link.set('{http://www.w3.org/1999/xlink}href', doc_ref.referringModelObject.attrib['{http://www.w3.org/1999/xlink}href'])
                if '{http://www.w3.org/1999/xlink}arcrole' in doc_ref.referringModelObject.attrib:
                    link.set('{http://www.w3.org/1999/xlink}arcrole', doc_ref.referringModelObject.attrib['{http://www.w3.org/1999/xlink}arcrole'])
                if '{http://www.w3.org/1999/xlink}role' in doc_ref.referringModelObject.attrib:
                    link.set('{http://www.w3.org/1999/xlink}role', doc_ref.referringModelObject.attrib['{http://www.w3.org/1999/xlink}role'])

    return html

def add_contexts_to_inline(main_html, modelXbrl, context_ids):
    '''Add context to the inline document'''

    # Contexts are added to the ix:resources element in the inline
    resources = main_html.find('.//ix:resources', namespaces=_XULE_NAMESPACE_MAP)
    for context_id in context_ids:
        model_context = modelXbrl.contexts[context_id]
        # The model_context is a modelObject, but it is based on etree.Element so it can be added to 
        # the inline tree 
        resources.append(model_context)

        # inline_context = etree.SubElement(resources, '{http://www.xbrl.org/2003/instance}context')
        # inline_context.set('id', context_id)
        # # Entity
        # inline_entity = etree.SubElement(inline_context, '{http://www.xbrl.org/2003/instance}entity')
        # inline_identifier = etree.SubElement(inline_entity, '{http://www.xbrl.org/2003/instance}identifier')
        # inline_identifier.set('scheme', model_context.entityIdentifier[0])
        # inline_identifier.text = model_context.entityIdentifier[1]
        # # Period
        # inline_period = etree.SubElement(inline_context, '{http://www.xbrl.org/2003/instance}period')
        # if model_context.isInstantPeriod:
        #     inline_instant = etree.SubElement(inline_period, '{http://www.xbrl.org/2003/instance}instant')
        #     inline_instant.text = model_context.period[0].svalue
        # elif model_context.isStartEndPeriod:
        #     inline_instant = etree.SubElement(inline_period, '{http://www.xbrl.org/2003/instance}startDate')
        #     if model_context.period[0].localName == 'startDate':
        #         inline_instant.text = model_context.period[0].textValue
        #     else:
        #         inline_instant.text = model_context.period[1].textValue
        #     inline_instant = etree.SubElement(inline_period, '{http://www.xbrl.org/2003/instance}endDate')
        #     if model_context.period[1].localName == 'endDate':
        #         inline_instant.text = model_context.period[1].textValue
        #     else:
        #         inline_instant.text = model_context.period[0].textValue   
        # else: # Forever
        #     etree.SubElement(inline_period, '{http://www.xbrl.org/2003/instance}forever')
        # # Dimensions
        # for dim_qname, model_dim_value in model_context.qnameDims.items():
        #     inline_segment = etree.SubElement(inline_entity, '{http://www.xbrl.org/2003/instance}segment')
        #     if model_dim_value.isExplicit:
        #         inline_explicit = etree.SubElement(inline_segment, '{http://xbrl.org/2006/xbrldi}explicitMember')
        #         inline_explicit.set('dimension', dim_qname.clarkNotation)
        #         if getattr(dim_qname, 'prefix', None) is None:
        #             inline_explicit.text = dim_qname

def add_units_to_inline(main_html, modelXbrl, unit_ids):

    resources = main_html.find('.//ix:resources', namespaces=_XULE_NAMESPACE_MAP)
    for unit_id in unit_ids:
        model_unit = modelXbrl.units[unit_id]
        resources.append(model_unit)


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
    
    parserGroup.add_option("--ferc-render-compile", 
                      action="store_true", 
                      dest="ferc_render_compile", 
                      help=_("Indicator to compile a template set. Reuires --ferc-render-template and --ferc-render-template_set options"))

    parserGroup.add_option("--ferc-render-render", 
                      action="store_true", 
                      dest="ferc_render_render", 
                      help=_("Indicator to render an instance with a template set. Reuires --ferc-render-template_set options and XBRL instnace (-f)"))

    parserGroup.add_option("--ferc-render-template", 
                      action="append", 
                      dest="ferc_render_template", 
                      help=_("The HTML template file"))

    parserGroup.add_option("--ferc-render-template-set", 
                      action="store", 
                      dest="ferc_render_template_set", 
                      help=_("Compiled template set file"))

    parserGroup.add_option("--ferc-render-css-file", 
                      action="store", 
                      dest="ferc_render_css_file", 
                      help=_("CSS file to include in the generated rendering"))

    parserGroup.add_option("--ferc-render-inline", 
                      action="store", 
                      dest="ferc_render_inline", 
                      help=_("The generated Inline XBRL file"))        

    parserGroup.add_option("--ferc-render-save-xule", 
                      action="store", 
                      dest="ferc_render_save_xule", 
                      help=_("Name of the generated xule file to save before complining the rule set."))  

def fercCmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()
    
    if options.ferc_render_compile is None and options.ferc_render_render is None:
        parser.error(_("The render plugin requires either --ferc-render-compile and/or --ferc-render-render"))

    if options.ferc_render_compile:
        if options.ferc_render_template is None and options.ferc_render_template_set is None:
            parser.error(_("Compiling a template set requires --ferc-render-template and --ferc-render-template-set."))
    
    if options.ferc_render_render:
        if options.ferc_render_template_set is None:
            parser.error(_("Rendering requires --ferc-render-template-set"))

    if options.ferc_render_compile:
        compile_templates(cntlr, options)

def compile_templates(cntlr, options):

    template_catalog = {'templates': []}
    template_set_file_name = os.path.split(options.ferc_render_template_set)[1]

    css_file_names = set()
    with zipfile.ZipFile(options.ferc_render_template_set, 'w') as template_set_file:    
        for template_full_file_name in getattr(options, 'ferc_render_template', tuple()):
            css_file_names.update(process_single_template(cntlr, options, template_catalog['templates'], template_set_file, template_full_file_name))

        template_catalog['css'] = list(css_file_names)
        # # Add CSS file
        # if options.ferc_render_css_file is not None:
        #     if os.path.exists(options.ferc_render_css_file):
        #         template_catalog['css'] = os.path.split(options.ferc_render_css_file)[1]
        #         template_set_file.write(options.ferc_render_css_file, 'css/{}'.format(os.path.split(options.ferc_render_css_file)[1]))
        #     else:
        #         cntlr.addToLog(_("CSS file does not exist: {}".format(options.ferc_render_css_file)), "error")

        # Write catalog
        template_set_file.writestr('catalog.json', json.dumps(template_catalog, indent=4))


    cntlr.addToLog(_("Writing template set file: {}".format(template_set_file_name)), 'info')

def process_single_template(cntlr, options, template_catalog, template_set_file, template_full_file_name):
    # Create a temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process the HTML template.
        xule_rule_text, substitutions, line_number_subs, template, css_file_names = process_template(cntlr, template_full_file_name)
        
        # Save the xule rule file if indicated
        if options.ferc_render_save_xule is not None:
            with open(options.ferc_render_save_xule, 'w') as xule_file:
                xule_file.write(xule_rule_text)

        # Compile Xule rules
        title = template.find('//xhtml:title', _XULE_NAMESPACE_MAP)
        if title is None:
            cntlr.addToLog("Template does not have a title", "error")
            raise FERCRenderException

        # Get some names set up
        template_file_name = os.path.split(template_full_file_name)[1]
        template_file_name_base = os.path.splitext(template_file_name)[0]

        template_file_name = "templates/{}/{}.html".format(template_file_name_base, template_file_name_base)
        xule_text_file_name = "templates/{}/{}.xule".format(template_file_name_base, template_file_name_base)
        xule_rule_set_file_name = "templates/{}/{}-ruleset.zip".format(template_file_name_base, template_file_name_base)
        substitution_file_name = "templates/{}/{}-substitutions.json".format(template_file_name_base, template_file_name_base)
        line_number_file_name = "templates/{}/{}-linenumbers.json".format(template_file_name_base, template_file_name_base)

        # xule file name
        xule_rule_file_name = os.path.join(temp_dir, '{}.xule'.format(template_file_name_base))   #'{}.xule'.format(title.text)
        with open(xule_rule_file_name, 'w') as xule_file:
            xule_file.write(xule_rule_text)

        # xule rule set name
        xule_rule_set_name = os.path.join(temp_dir, '{}-ruleset.zip'.format(template_file_name_base))
        compile_method = getXuleMethod(cntlr, 'Xule.compile')
        compile_method(xule_rule_file_name, xule_rule_set_name, 'json')

        template_catalog.append({'name': template_file_name_base,
                            'template': template_file_name,
                            'xule-text': xule_text_file_name,
                            'xule-rule-set': xule_rule_set_file_name,
                            'substitutions': substitution_file_name,
                            'line-numbers': line_number_file_name})

        template_set_file.write(template_full_file_name, template_file_name) # template
        template_set_file.writestr(xule_text_file_name, xule_rule_text) # xule text file
        template_set_file.write(xule_rule_set_name, xule_rule_set_file_name) # xule rule set
        template_set_file.writestr(substitution_file_name, json.dumps(substitutions, indent=4)) # substitutions file
        template_set_file.writestr(line_number_file_name, json.dumps(line_number_subs, indent=4)) # line number substitutions file

    return css_file_names

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    '''Render a filing'''
    
    if options.ferc_render_render and options.ferc_render_template_set is not None:
        used_context_ids = set()
        used_unit_ids = set()

        main_html = setup_inline_html(modelXbrl)

        schedule_spans = []
        with zipfile.ZipFile(options.ferc_render_template_set, 'r') as ts:
            with ts.open('catalog.json', 'r') as catalog_file:
                template_catalog = json.load(io.TextIOWrapper(catalog_file))

            # Get name of rendered html file
            if options.ferc_render_inline is None:
                inline_name = '{}.html'.format(os.path.splitext(os.path.split(options.ferc_render_template_set)[1])[0])
            else:
                inline_name = options.ferc_render_inline

            # Add css link
            head = main_html.find('xhtml:head', _XULE_NAMESPACE_MAP)
            for css_file_name in template_catalog.get('css',tuple()):
                link = etree.SubElement(head, "link")
                link.set('rel', 'stylesheet')
                link.set('type', 'text/css')
                link.set('href', css_file_name)

            # if 'css' in template_catalog:
            #     head = main_html.find('xhtml:head', _XULE_NAMESPACE_MAP)
            #     link = etree.SubElement(head, "link")
            #     link.set('rel', 'stylesheet')
            #     link.set('type', 'text/css')
            #     link.set('href', template_catalog['css'])
            #     # Write the css file
            #     #ts.extract('css/{}'.format(template_catalog['css']), os.path.dirname(inline_name))
            #     css_content = ts.read('css/{}'.format(template_catalog['css'])).decode()
            #     with open(os.path.join(os.path.dirname(inline_name), template_catalog['css']), 'w') as css_file:
            #         css_file.write(css_content)
            # else:
            #     cntlr.addToLog(_("There is not css file in the template set. The rendered file being created without a reference to a css file."))

            # Iterate through each of the templates in the catalog
            for catalog_item in template_catalog['templates']: # A catalog item is a set of files for a single template
                # Get the html template
                with ts.open(catalog_item['template']) as template_file:
                    try:
                        template = etree.parse(template_file)
                    except etree.XMLSchemaValidateError:
                        cntlr.addToLog("Template file '{}' is not a valid XHTML file.".format(catalog_item['template']), 'error', level=logging.ERROR)
                        raise FERCRenderException  
                # Get the substitutions
                with ts.open(catalog_item['substitutions']) as sub_file:
                    substitutions = json.load(io.TextIOWrapper(sub_file))
                # Get line number substitutions
                with ts.open(catalog_item['line-numbers']) as line_number_file:
                    line_number_subs = json.load(io.TextIOWrapper(line_number_file))

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
                 # Get xule rule set
                with ts.open(catalog_item['xule-rule-set']) as rule_set_file:
                    call_xule_method(cntlr, modelXbrl, io.BytesIO(rule_set_file.read()), run_options)
                
                # Remove the handler from the logger. This will stop the capture of messages
                cntlr.logger.removeHandler(log_capture_handler)
                
                # Substitute template
                rendered_template, template_context_ids, template_unit_ids = substituteTemplate(substitutions, line_number_subs, log_capture_handler.captured, template, modelXbrl, main_html)
                used_context_ids |= template_context_ids
                used_unit_ids |= template_unit_ids
                # Save the body as a div
                body = rendered_template.find('xhtml:body', namespaces=_XULE_NAMESPACE_MAP)
                if body is None:
                    cntlr.addToLog(_("Cannot find body of the template: {}".format(os.path.split(catalog_item['template'])[1])), 'error')
                    raise FERCRenderException    
                body.tag = 'div'
                schedule_spans.append(body)

        main_body = main_html.find('xhtml:body', namespaces=_XULE_NAMESPACE_MAP)
        for span in schedule_spans:
            main_body.append(span)
            if span is not schedule_spans[-1]: # If it is not the last span put a separator in
                main_body.append(etree.fromstring('<hr xmlns="{}"/>'.format(_XHTM_NAMESPACE)))

        add_contexts_to_inline(main_html, modelXbrl, used_context_ids)
        add_units_to_inline(main_html, modelXbrl, used_unit_ids)
        # Write generated html
        main_html.getroottree().write(inline_name, pretty_print=True, method="xml", encoding='utf8', xml_declaration=True)

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

def format_fact(xule_expression_node, model_fact, inline_html, is_html):
    '''Format the fact to a string value'''

    preamble = None
    if xule_expression_node is None:
        format = None
    else:
        format = xule_expression_node.get('format')
    if format is None:
        display_value = str(model_fact.xValue)
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

        display_value,  *preamble = format_function(model_fact, 
                                        -1 if xule_expression_node.get('sign', '+') == '-' else 1, # sign
                                        xule_expression_node.get('scale'))

    if model_fact.isNumeric:
        ix_node =  etree.Element('{{{}}}nonFraction'.format(_XULE_NAMESPACE_MAP['ix']), nsmap=_XULE_NAMESPACE_MAP)
        ix_node.set('unitRef', model_fact.unitID)
        ix_node.set('decimals', xule_expression_node.get('decimals', 'INF'))
    else:
        ix_node = etree.Element('{{{}}}nonNumeric'.format(_XULE_NAMESPACE_MAP['ix']), nsmap=_XULE_NAMESPACE_MAP)

    ix_node.set('contextRef', model_fact.contextID)
    ix_node.set('name', str(model_fact.qname))
    if model_fact.id is not None:
        ix_node.set('id', model_fact.id)
    if xule_expression_node.get('format') is not None:
        # need to handle the namespace of the format value
       
        format = xule_expression_node.get('format')
        if ':' in format:
            prefix, local_name = format.split(':')
        else:
            prefix = None
            local_name = format
        format_namespace_uri_source = xule_expression_node.nsmap.get(prefix)
        if format_namespace_uri_source is None:
            model_fact.modelXbrl.error("RENDERERROR", _("Cannot resolve namespace of format. Format is '{}'".format(format)))
            raise FERCRenderException
        
        rev_nsmap = {v: k for k, v in inline_html.nsmap.items()}

        if format_namespace_uri_source in rev_nsmap:
            format_prefix_inline = rev_nsmap.get(format_namespace_uri_source)
        else:
            model_fact.modelXbrl.error("RENDERERROR",_("Do not have the namespace in the generated inline document for namespace '{}'".format(format_namespace_uri_source)))
            raise FERCRenderException
        
        if format_prefix_inline is None:
            format_inline = local_name
        else:
            format_inline = '{}:{}'.format(format_prefix_inline, local_name)
    
        ix_node.set('format', format_inline)
    if xule_expression_node.get('sign', '') == '-':
        ix_node.set('sign', '-')
    if xule_expression_node.get('scale') is not None:
        ix_node.set('scale', xule_expression_node.get('scale'))

    if is_html:
        content_node = etree.fromstring('<div class="sub-html">{}</div>'.format(display_value))
        ix_node.append(content_node)
    else:
        ix_node.text = display_value

    # check the preamble. If there is one, this will go before the ix_node
    if preamble is not None and len(preamble) > 0 and preamble[0] is not None and len(preamble[0]) > 0:
        div_node = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
        div_node.set('class', 'sub-preamble')
        div_node.text = preamble[0]
        div_node.append(ix_node)
        return div_node
    else:
        return ix_node

def format_numcommadot(model_fact, sign, scale, *args, **kwargs):
    if not model_fact.isNumeric:
        model_fact.modelXbrl.error(_("Cannot format non numeric fact using numcommadoc. Concept: {}, Value: {}".format(model_fact.concept.qname.clarkNotation, model_fact.xValue)))
        raise FERCRenderException

    val = model_fact.xValue * sign
    if scale is not None:
        # Convert scale from string to number
        try:
            scale_num = int(scale)
        except ValueError:
            scale_num = float(scale)
        except:
            model_fact.modelXblr.error("RENDERERROR", _("Unable to convert scale from the template to number. Scale value is: '{}'".format(scale)))
            raise FERCRenderException
        
        try:
            scaled_val = val * 10**-scale_num
        except TypeError:
            # the val may be a decimal and the 10**-scale_num a float which causes a type error
            if isinstance(val, decimal.Decimal):
                scaled_val = val * decimal.Decimal(10)**-decimal.Decimal(scale_num)
            else:
                model_fact.modelXbrl.error("RENDERERROR", _("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale)))
                raise FERCRenderException
        except:
            model_fact.modelXbrl.error("RENDERERROR", _("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale)))
            raise FERCRenderException

        if (scaled_val % 1) == 0 and not isinstance(scaled_val, int): 
            # need to convert to int
            scaled_val = int(scaled_val)
        else:
            if (scaled_val % 1) == 0: # this is a float or a decimal, but a whole number
                scaled_val = int(scaled_val)
        val = scaled_val

    if val < 0:
        val = val * -1
        return '{:,}'.format(val), '-'
    else:
        return '{:,}'.format(val), # The comma at the end is important, it prevents the first value from being split up into the preamble

def format_dateslahus(model_fact, *args, **kwargs):
    return model_fact.xValue.strftime('%m/%d/%Y'), # The comma at the end is important, it prevents the first value from being split up into the preamble

_formats = {'{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}numcommadot': format_numcommadot,
            '{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}dateslashus': format_dateslahus
            }

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