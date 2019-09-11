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
        for plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
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

    return '{}\n{}\n{}'.format(xule_namespaces, xule_constants, xule_rules), substitutions, template_tree

def build_xule_namespaces(template_tree):
    '''build the namespace declarations for xule

    Convert the namespaces on the template to namespace declarations for xule. This will only use the 
    namespaces that are declared on the root element of the template.
    '''
    namespaces = ['namespace {}={}'.format(k, v) if k is not None else 'namespace {}'.format(v) for k, v in template_tree.getroot().nsmap.items()]
    return '\n'.join(namespaces)

def build_constants():
    '''Create constants used by the expressions.

    $currentInstant
    $currentDuration
    $priorInstant
    $priorDuration
    '''
    constants = '''
        constant $currentDuration = {@ferc:ReportYear}.periood
        constant $currentInstant = $currentDuration.end
        constant $priorDuration = $currentDuration
        constant $priorInstant = $currentInstant
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
    named_rules = collections.defaultdict(list)

    substitutions, xule_rules, next_rule_number, named_rules = build_unamed_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name)
    substitutions, xule_rules, next_rule_number, named_rules = build_named_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name)
    return '\n\n'.join(xule_rules), substitutions

def build_unamed_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name):

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
                classes = None
            else: # this is a xule:replace
                # process xule:class nodes
                classes, xule_rules, next_rule_number = build_class_rules(replacement_node, xule_rules, next_rule_number)

            comment_text = '    // {} - line {}'.format(template_file_name, xule_expression.sourceline)
            if xule_expression.get('fact','').lower() == 'true':
                sub_content ={'part': None, 
                              'replacement-node': replacement_node, 
                              'result-focus-index': 0, 
                              'classes': classes}
                #rule_text = 'output {}\n{}\nlist((({})#rv-0).string).to-json\nrule-focus list($rv-0)'.format(rule_name, comment_text, xule_expression.text.strip())

                rule_text = 'output {rule_name}\n{comment}\n{result_text}\nrule-focus list($rv-0)'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             'f'))
                             )
            else: # not a fact
                sub_content = {'part': None, 
                               'replacement-node': replacement_node, 
                               'result-text-index': 0, 
                               'classes': classes}
                #rule_text = 'output {}\n{}\nlist(({}).string).to-json'.format(rule_name, comment_text, xule_expression.text.strip())
                rule_text = 'output {rule_name}\n{comment}\n{result_text}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             's'))
                             )
            xule_rules.append(rule_text)

            if xule_expression.get('html', 'false').lower() == 'true':
                sub_content['html'] = True
            substitutions[rule_name].append(sub_content)
        else: # This is a named rule
            # Saved the named rule part for later
            part = xule_expression.get('part', None)
            named_rules[named_rule].append((part, xule_expression))

    return substitutions, xule_rules, next_rule_number, named_rules

def format_rule_result_text_part(expression_text, part, type):
    output_is_fact = 'if exists({exp}) (({exp}).is-fact).string else \'false\''.format(exp=expression_text)
    if part is None:
        output_expression = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
        return "dict(list('type', '{type}'), list('is-fact', {is_fact}), list('value', {val}))".format(
            type=type, 
            is_fact=output_is_fact, 
            val=output_expression)
    else:
        output_expression = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=part)
        return "dict(list('type', '{type}'), list('is-fact', {is_fact}), list('value', {val}), list('part', {part}))".format(
            type=type, 
            is_fact=output_is_fact, 
            val=output_expression,
            part=part)

def build_named_rules(substitutions, xule_rules, next_rule_number, named_rules, template_tree, template_file_name):
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
                class_expressions = None
            else: # this is a xule:replace
                class_expressions = format_class_expressions(replacement_node, next_text_number)

            comments.append('    // {} - {}'.format(template_file_name, expression.sourceline))
            if part is None:
                preliminary_rule_text = expression.text.strip()
            else:
                if expression.get("type") == 'fact':
                    # If the this part of the rule is a fact, then add a tag that will be used in the rule focus
                    #result_parts.append('list((({exp})#rv-{part}).string, exists({exp}))'.format(exp=expression.text.strip(), part=part))
                    result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                                next_text_number,
                                                                                                'f')
                                                        )
                    )
                    
                    rule_focus.append('$rv-{}'.format(next_text_number))
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': replacement_node, 
                                   'expression-node': expression,
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
                                                                                                's')
                                                        )
                    )
                    sub_content = {'name': named_rule, 
                                   'part': part, 
                                   'replacement-node': replacement_node, 
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

def build_class_rules(replacement_node, xule_rules, next_rule_number):
    classes = []
    for class_node in replacement_node.findall('{{{}}}class'.format(etree.QName(replacement_node).namespace)): # This is just a easy way to get the ns of the replacement_node
        class_rule_name = _CLASS_RULE_NAME_PREFIX + str(next_rule_number)
        next_rule_number += 1
        
        class_rule_text = 'output {}\n({}).string'.format(class_rule_name, class_node.text.strip())
        xule_rules.append(class_rule_text)
        classes.append(class_rule_name)

    return classes, xule_rules, next_rule_number

def get_class_expressions(replacement_node):
    class_expressions= []
    for class_node in replacement_node.findall('{{{}}}class'.format(etree.QName(replacement_node).namespace)): # This is just a easy way to get the ns of the replacement_node
        class_expressions.append(class_node.text.strip)  

    return class_expressions      

def substituteTemplate(substitutions, rule_results, template, modelXbrl):
    '''Subsititute the xule expressions in the template with the generated values.'''

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
        return len([x for x in subs[0]['replacement-node'].iterancestors()])

    repeating.sort(key=sort_by_ancestors, reverse=True)

    for rule_name, subs in non_repeating + repeating:
        # Determine if this is a repeating rule.
        new_nodes = []
        if len(subs) > 0 and subs[0].get('name') in repeating_nodes:
            # This is a repeating rule
            repeating_model_node = repeating_nodes[subs[0].get('name')]
            model_tree = etree.ElementTree(repeating_model_node)
            
        else:
            repeating_model_node = None

        for rule_result in rule_results[rule_name]:
            json_rule_result = json.loads(rule_result.msg)

            if repeating_model_node is not None:
                new_node = deepcopy(repeating_model_node)
                new_nodes.append(new_node)
                new_tree = etree.ElementTree(new_node)

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
                
                classes = get_classes(sub, rule_results)

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
                            text_content, inline_format_clark = format_fact(sub['expression-node'], model_fact)
                    else: # Result is not a fact
                        text_content = json_result['value']

                    if text_content is None:
                        span_content = '<span/>'
                        classes += ['sub-value', 'sub-no-replacement']
                    else:
                        if not sub.get('html', False):
                            # This is not html content, so the text needs to be escaped
                            text_content = html.escape(text_content)
                        span_content = '<span>{}</span>'.format(text_content)  
                        classes += ['sub-value', 'sub-replacement']
                    
                    span = etree.fromstring(span_content)
                    span.set('class', ' '.join(classes))
                    # Get the node in the template to replace
                    if repeating_model_node is None:
                        sub_node = sub['replacement-node']
                    else:
                        # Find the node in the repeating model node
                        model_path = model_tree.getelementpath(sub['replacement-node'])
                        sub_node = new_tree.find(model_path)

                    sub_parent = sub_node.getparent()
                    sub_parent.replace(sub_node, span) 
            
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
        # This is a list of results
        for i in range(part + 1):
            if (i in results_by_part and 
                results_by_part[i]['type'] == 'f' and 
                results_by_part[i]['value'] is not None and 
                results_by_part[i]['is-fact'].lower() == 'true'):
                rule_focus_index +=1
    else:
        # The results is really just a single dictionary of one results. Just check if the fact is there
        if json_results['is-fact']:
            rule_focus = 0

    return rule_focus_index if rule_focus_index >= 0 else None

def get_classes(sub, rule_results):
    classes = []
    for class_rule_name in sub.get('classes'):
        for class_result in rule_results.get(class_rule_name, tuple()):
            classes.append(class_result.msg)

    return classes

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
        xule_rule_text, substitutions, template = process_template(cntlr, options.ferc_render_template)
        
        # Compile Xule rules
        title = template.find('//xhtml:title', _XULE_NAMESPACE_MAP)
        if title is None:
            cntlr.addToLog("Template does not have a title", "error")
            raise FERCRenderException

        # xule file name
        xule_rule_file_name = options.ferc_render_xule_file or '{}.xule'.format(title.text)
        with open(xule_rule_file_name, 'w') as xule_file:
            xule_file.write(xule_rule_text)

        if options.ferc_render_xule_only:
            cntlr.addToLog(_("Generated xule rule file '{}'".format(xule_rule_file_name)))
            # Stop the processing
            return

        # xule rule set name
        xule_rule_set_name = options.ferc_render_xule_rule_set or '{}.zip'.format(title.text)
        compile_method = getXuleMethod(cntlr, 'Xule.compile')
        compile_method(xule_rule_file_name, xule_rule_set_name, 'json')
        
        # Run Xule rules
        # Create a log handler that will capture the messages when the rules are run.
        log_capture_handler = _logCaptureHandler()
        cntlr.logger.addHandler(log_capture_handler)

        # Call the xule processor to run the rules
        call_xule_method = getXuleMethod(cntlr, 'Xule.callXuleProcessor')
        call_xule_method(cntlr, modelXbrl, xule_rule_set_name, options)
        
        # Remove the handler from the logger. This will stop the capture of messages
        cntlr.logger.removeHandler(log_capture_handler)
        
        # Substitute template
        rendered_template = substituteTemplate(substitutions, log_capture_handler.captured, template, modelXbrl)
        

        # Write rendered template
        if options.ferc_render_inline is None:
            inline_name = '{} - rendered.html'.format(title.text)
        else:
            inline_name = options.ferc_render_inline

        rendered_template.write(inline_name, pretty_print=True, method="xml", encoding='utf8', xml_declaration=True)

        cntlr.addToLog(_("Rendered template '{}' as '{}'".format(options.ferc_render_template, inline_name)))
        
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