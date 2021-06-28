'''
Reivision number: $Change: 23263 $
'''
from arelle import FileSource
from arelle import PluginManager
from arelle.CntlrWebMain import Options
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelDocument import Type
from arelle.ModelValue import QName
from arelle.XmlValidate import VALID
from copy import deepcopy, copy
from lxml import etree, html
from lxml.builder import E

import datetime
import decimal
import calendar
import collections
import io
import json
import logging
import optparse
import os
import os.path
import re
import tempfile
import uuid
import zipfile

# This will hold the xule plugin module
_xule_plugin_info = None

# xule namespace used in the template
_XULE_NAMESPACE_MAP = {'xule': 'http://xbrl.us/xule/2.0/template', 
                       'xhtml': 'http://www.w3.org/1999/xhtml',
                       'ix': 'http://www.xbrl.org/2013/inlineXBRL'}
_XBRLI_NAMESPACE = 'http://www.xbrl.org/2003/instance'
_XHTM_NAMESPACE = 'http://www.w3.org/1999/xhtml'
_RULE_NAME_PREFIX = 'rule-'
_EXTRA_ATTRIBUTES = ('format', 'scale', 'sign', 'decimals')
_PHRASING_CONTENT_TAGS = {'a', 'audio', 'b', 'bdi', 'bdo', 'br', 'button', 'canvas', 'cite', 'code', 'command',
                          'datalist', 'del', 'dfn', 'em', 'embed', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'keygen',
                          'label', 'map', 'mark', 'math', 'meter', 'noscript', 'object', 'output', 'progress', 'q',
                          'ruby', 's', 'samp', 'script', 'select', 'small', 'span', 'strong', 'sub', 'sup', 'svg',
                          'textarea', 'time', 'u', 'var', 'video', 'wbr'}
_NAMESPACE_DECLARATION = 'TEMPORARY_NAMESPACE_DECLARATION'
_ORIGINAL_FACT_ID_ATTRIBUTE = 'original_fact_id'

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


def process_template(cntlr, template_file_name, options):
    '''Prepare the template to substitute values

    1. build the xule rules from the template
    2. identify stylesheets
    3. identify where in the template to substitute calculated values
    4. create a template set
    '''

    # Open the template
    try:
        with open(template_file_name, 'rb') as fp:
            template_string = clean_entities(fp.read().decode('utf-8'))
            template_tree = etree.fromstring(template_string).getroottree()
    except FileNotFoundError:
        raise FERCRenderException("Template file '{}' is not found.".format(template_file_name))

    except etree.XMLSchemaValidateError:
        raise FERCRenderException("Template file '{}' is not a valid XHTML file.".format(template_file_name))

    # build the namespace declaration for xule
    xule_namespaces = build_xule_namespaces(template_tree, options)
    # build constants
    xule_constants = build_constants(options)
    # Create list of Xule nodes in the template
    xule_node_locations = {template_tree.getelementpath(xule_node): node_number for  node_number, xule_node in enumerate(template_tree.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}
    # create the rules for xule and retrieve the update template with the substitutions identified.
    xule_rules, rule_meta_data = build_xule_rules(template_tree, template_file_name, xule_node_locations)

    # Get the css file name from the template
    css_file_names = tuple(x for x in template_tree.xpath('/xhtml:html/xhtml:head/xhtml:link[@rel="stylesheet" and @type="text/css"]/@href', namespaces=_XULE_NAMESPACE_MAP))

    return '{}\n{}\n{}'.format(xule_namespaces, xule_constants, xule_rules), rule_meta_data, template_tree, template_string, css_file_names

def build_xule_namespaces(template_tree, options):
    '''build the namespace declarations for xule

    Convert the namespaces on the template to namespace declarations for xule. This will only use the 
    namespaces that are declared on the root element of the template.

    Namespaces provided on the command line using --ferc-render-namespace take precidence
    '''
    namespace_dict = template_tree.getroot().nsmap.copy()
    # Overwrite with namespaces from the command line
    namespace_dict.update(options.namespace_map)

    namespaces = ['namespace {}={}'.format(k, v) if k is not None else 'namespace {}'.format(v) for k, v in namespace_dict.items()]

    return '\n'.join(namespaces)

def build_constants(options):
    '''Create constants used by the expressions. '''

    constant_file_name = getattr(options, 'ferc_render_constants') or os.path.join(os.path.dirname(os.path.realpath(__file__)), 'render-constants.xule')
    try:
        with open(constant_file_name, 'r') as constant_file:
            constants = constant_file.read()
    except FileNotFoundError:
        raise FERCRenderException("Constant file {} is not found.".format(constant_file_name))

    return constants

def build_xule_rules(template_tree, template_file_name, xule_node_locations):
    '''Extract the rules and identify the subsititions in the template

    1. Create the xule rules
    2. Identify where the subsitutions will be
    '''

    xule_rules = []
    next_rule_number = 1
    # Using an ordered dict so that the named rules are build in the order of the rule in the template.
    named_rules = collections.OrderedDict()

    node_pos = dict()
    pos = 0
    for node in template_tree.findall('.//*'):
        pos += 1
        node_pos[node] = pos

    substitutions = collections.defaultdict(list)
    # Build showif condition for the template
    showifs, showif_rules, next_rule_number = build_template_show_if(xule_rules,
                                                                         next_rule_number,
                                                                         template_tree,
                                                                         template_file_name,
                                                                         node_pos)

    unamed_substitutions, xule_rules, next_rule_number, named_rules = build_unamed_rules(xule_rules, 
                                                                                  next_rule_number, 
                                                                                  named_rules, 
                                                                                  template_tree, 
                                                                                  template_file_name, 
                                                                                  xule_node_locations,
                                                                                  node_pos)
    substitutions.update(unamed_substitutions)

    named_substitutions, xule_rules, next_rule_number, named_rules = build_named_rules(xule_rules, 
                                                                                 next_rule_number, 
                                                                                 named_rules, 
                                                                                 template_tree, 
                                                                                 template_file_name,
                                                                                 xule_node_locations,
                                                                                 node_pos)
    substitutions.update(named_substitutions)
    # Create rules for starting line numbers.                                                                                 
    line_number_subs, xule_rules, next_rule_number = build_line_number_rules(xule_rules, next_rule_number, template_tree, xule_node_locations)   

    rule_meta_data = {'substitutions': substitutions,
                      'line-numbers': line_number_subs,
                      'showifs': showifs}

    return '\n\n'.join(showif_rules + xule_rules), rule_meta_data

def build_template_show_if(xule_rules, next_rule_number, template_tree, template_file_name, node_pos):
    '''Conditional Template Rules

    This funciton finds the xule:showif rule, if there is one, and creates the xule rule for it.
    '''
    meta_data = collections.defaultdict(list)
    xule_rules = list()
    # The <sule:showif> must be a node under the html body node.
    for showif_node in template_tree.findall('xhtml:body/xule:showif', _XULE_NAMESPACE_MAP):
        rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
        next_rule_number += 1 
        
        comment_text = '    //xule:showif rule\n    // {} - line {}'.format(template_file_name, showif_node.sourceline)
        rule_body = showif_node.text.strip()
        xule_rules.append('output {rule_name}\n{comment}\n{rule_body}'\
                          ''.format(rule_name=rule_name,
                                   comment=comment_text,
                                   rule_body=rule_body)
        )

        meta_data[rule_name] = {'type': 'showif',
                                'template-line-number': showif_node.sourceline}

    return meta_data, xule_rules, next_rule_number

def build_unamed_rules(xule_rules, next_rule_number, named_rules, template_tree, template_file_name, xule_node_locations, node_pos):
    substitutions = collections.defaultdict(list)
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
                extra_expressions = dict()
            else: # this is a xule:replace
                # process xule:class nodes
                extra_expressions = format_extra_expressions(replacement_node)
            
            extra_attributes = get_extra_attributes(xule_expression)
            comment_text = '    // {} - line {}'.format(template_file_name, xule_expression.sourceline)            
            if xule_expression.get('fact','').lower() == 'true' or 'fact' in extra_expressions:
                sub_content = {'part': None, 
                              'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                              'expression-node': xule_node_locations[template_tree.getelementpath(xule_expression)],
                              'template-line-number': xule_expression.sourceline,
                              'node-pos': node_pos[replacement_node]}
                #rule_text = 'output {}\n{}\nlist((({})#rv-0).string).to-json\nrule-focus list($rv-0)'.format(rule_name, comment_text, xule_expression.text.strip())

   

                rule_text = 'output {rule_name}\n{comment}\n{result_text}{rule_focus}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             None,
                                                                                             'f',
                                                                                             extra_expressions)),
                              rule_focus='\nrule-focus list(if $rv-0.is-fact $rv-0 else none)' 
                             )
            else: # not a fact
                sub_content = {'part': None, 
                               'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                               'template-line-number': xule_expression.sourceline,
                               'node-pos': node_pos[replacement_node]}
                #rule_text = 'output {}\n{}\nlist(({}).string).to-json'.format(rule_name, comment_text, xule_expression.text.strip())
                rule_text = 'output {rule_name}\n{comment}\n{result_text}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
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

def format_rule_result_text_part(expression_text, part, value_number, type, extra_expressions, inside=False):

    output_dictionary = collections.OrderedDict()
    output_dictionary['type'] = "'{}'".format(type)
    

    if part is None:
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
    else:
        output_dictionary['part'] = part
        output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=value_number)
    if type == 'f':
        output_dictionary['is-fact'] = 'if exists({exp}) (({exp}).is-fact).string else \'false\''.format(exp=expression_text)
        if inside:
            # Inside expressions have an extra component to capture the fact. This is used to build the rule focus.
            output_dictionary['fact'] = expression_text        
    # Extra expressions (i.e. class, format, scale)
    for extra_name, extra_expression in extra_expressions.items():
        if extra_name == 'fact':
            # rename this so it doesn't conflict with the name 'fact' for inside expression. Sell code a few lines up.
            extra_name = 'dynamic-fact'
        if isinstance(extra_expression, list):
            output_extra_expressions = "list({})".format(','.join(extra_expression)) if len(extra_expression) > 0 else None
        else:
            output_extra_expressions = extra_expression
        if output_extra_expressions is not None:
            output_dictionary[extra_name] = output_extra_expressions
    
    output_items = ("list('{key}', {val})".format(key=k, val=v) for k, v in output_dictionary.items())
    output_string = "dict({})".format(', '.join(output_items))

    return output_string

def build_named_rule_info(named_rule, part_list, next_rule_number, template_tree, template_file_name, 
                          xule_node_locations, node_pos, next_text_number=0, inside=False):
    '''Build the body of the rule

    Builds the rule text and sets up the subsitution information.
    '''
    # Sort the part list by the part number
    part_list.sort(key=lambda x: (x[0] is not None, x[0]) if x is not None else (False, '')) # This will put the None part first
    result_parts = []
    rule_focus = []
    comments = []
    preliminary_rule_text = ''
    substitutions = []
    sequence_number = 0

    rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
    next_rule_number += 1
    for part, expression in part_list:
        replacement_node = expression.getparent()
        if replacement_node.tag != '{{{}}}{}'.format(_XULE_NAMESPACE_MAP['xule'], 'replace'):
            replacement_node = expression
            extra_expressions = dict()
        else: # this is a xule:replace
            extra_expressions = format_extra_expressions(replacement_node)

        extra_attributes = get_extra_attributes(expression)

        comments.append('    // {} - {}'.format(template_file_name, expression.sourceline))
        if part is None:
            preliminary_rule_text = expression.text.strip()
        else:
            if expression.get("fact", "").lower() == 'true' or 'fact' in extra_expressions:
                # If the this part of the rule is a fact, then add a tag that will be used in the rule focus
                #result_parts.append('list((({exp})#rv-{part}).string, exists({exp}))'.format(exp=expression.text.strip(), part=part))
                result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                            sequence_number,
                                                                                            next_text_number,
                                                                                            'f',
                                                                                            extra_expressions,
                                                                                            inside)
                                                    )
                )
                
                rule_focus.append('if $rv-{ntn}.is-fact $rv-{ntn} else none'.format(ntn=next_text_number))
                sub_content = {'name': named_rule, 
                                'part': part, 
                                'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                                'expression-node': xule_node_locations[template_tree.getelementpath(expression)],
                                'template-line-number': expression.sourceline,
                                'node-pos': node_pos[replacement_node]}
                if expression.get('html', 'false').lower() == 'true':
                    sub_content['html'] = True
                substitutions.append(sub_content)
            else: # not a fact, just a string result
                #result_parts.append('({}).string'.format(expression.text.strip()))
                result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(expression.text.strip(),
                                                                                            sequence_number,
                                                                                            next_text_number,
                                                                                            's',
                                                                                            extra_expressions,
                                                                                            inside)
                                                    )
                )
                sub_content = {'name': named_rule, 
                                'part': part, 
                                'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                                'template-line-number': expression.sourceline,
                                'extras': extra_attributes,
                                'node-pos': node_pos[replacement_node]}
                if expression.get('html', 'false').lower() == 'true':
                    sub_content['html'] = True                                   
                substitutions.append(sub_content)

            next_text_number += 1
            sequence_number += 1
    
    rule_info = {'rule_name': rule_name,
                 'comments': comments,
                 'preliminary_rule_text': preliminary_rule_text,
                 'result_parts': result_parts,
                 'rule_focus': rule_focus}
    
    return rule_info, substitutions, next_rule_number, next_text_number

def build_named_rules(xule_rules, next_rule_number, named_rules, template_tree, template_file_name, xule_node_locations, node_pos):
    # Handle named rules
    substitutions = dict()

    # Get named rules that are linked with repeating nodes in the template
    repeating_name_hierarchy, all_repeating_names = get_name_chain(template_tree)
    # These are named rules that don't repeat
    non_repeating_named_rules = named_rules.keys() - all_repeating_names

    for named_rule in repeating_name_hierarchy.keys() | non_repeating_named_rules:
        part_list = named_rules[named_rule]

    #for named_rule, part_list in named_rules.items():

        rule_info, rule_substitutions, next_rule_number, next_text_number = \
            build_named_rule_info(named_rule, 
                                  part_list,  
                                  next_rule_number, 
                                  template_tree, 
                                  template_file_name, 
                                  xule_node_locations,
                                  node_pos)
        
        # Find the child rules and add them to the main rule.substitute_rule(rule_name, subs, line_number_subs, rule_results, template, modelXbrl, main_html, repeating_nodes)
        child_substitutions, child_parts, child_focus, next_text_number = \
            add_child_rules(named_rule,
                            repeating_name_hierarchy.get(named_rule, tuple()),
                            len(rule_info['result_parts']),
                            next_text_number,
                            named_rules,
                            template_tree,
                            template_file_name,
                            xule_node_locations,
                            node_pos)

        substitutions[rule_info['rule_name']] = {'name': named_rule, 'subs': rule_substitutions + child_substitutions}
        rule_info['result_parts'] += child_parts
        #build rule text
        rule_text = 'output {}\n'.format(rule_info['rule_name'])
        rule_text += '\n'.join(rule_info['comments']) + '\n'
        rule_text += '\n{}'.format(rule_info['preliminary_rule_text'])
        result_text = ',\n'.join(["{}".format(expression) for expression in rule_info['result_parts']])
        
        rule_text += '\nlist({}).to-json'.format(result_text)
        rule_focus = rule_info['rule_focus']
        composite_rule_focus = []
        if len(rule_focus) > 0:
            composite_rule_focus.append('list({})'.format(', '.join(rule_focus)))
        if len(child_focus) > 0:
            composite_rule_focus.append(' + '.join(child_focus))
        if len(composite_rule_focus) > 0:
            rule_text += '\nrule-focus {}'.format(' + '.join(composite_rule_focus))

        xule_rules.append(rule_text)

    return substitutions, xule_rules, next_rule_number, named_rules

def add_child_rules(parent_name, hierarchy, next_part_number, next_text_number,named_rules, 
                    template_tree, template_file_name, xule_node_locations, node_pos):
    substitutions = []
    parts = list()
    focus = list()
    for children in hierarchy:
        if not isinstance(children, dict):
            # This is leaf node of name hierachy.
            children = {children: []}

        for child_name, next_level in children.items():
            if child_name not in named_rules:
                raise FERCRenderException("The repeating name '{}' has no xule:expression".format(child_name))

            child_rule_info, child_substitutions, _y, next_text_number = \
                build_named_rule_info(child_name,
                                      named_rules[child_name],
                                      0,
                                      template_tree,
                                      template_file_name,
                                      xule_node_locations,
                                      node_pos,
                                      next_text_number=next_text_number,
                                      inside=True)
            next_substitutions, next_parts, next_focus, next_text_number = \
                add_child_rules(child_name,
                                next_level,
                                len(child_rule_info['result_parts']),
                                next_text_number,
                                named_rules,
                                template_tree,
                                template_file_name,
                                xule_node_locations,
                                node_pos)

            inside_list_text = ', '.join(["{}".format(expression) for expression in child_rule_info['result_parts'] + next_parts])
            inside_variable_text = '${inside_name}-val = list({prelim_text}\nlist({value_text}));'.format(
                                        inside_name=child_name,
                                        prelim_text=child_rule_info['preliminary_rule_text'],
                                        value_text=inside_list_text)
            inside_value_text = \
'''
// Get results
{variable_text} 


// Find the rule focus facts
${inside_name}-rf = list(
    for $res in ${inside_name}-val
        for $part in $res
            if $part['type'] == 'f'
                $part['fact']
            else    
                skip
);

// Get rid of the 'fact' component of the part
list(
    for $res in ${inside_name}-val
        list(
            for $part in $res
                dict(
                    for $key in $part.keys
                        if $key != 'fact'
                            list($key, $part[$key])
                        else
                            skip
                    )
        )
)
'''.format(inside_name=child_name, variable_text=inside_variable_text)

            list_part_text = "dict(list('type', 'l'),  list('part', {}), list('is-fact', 'false'), " \
                             "list('value', {}))".format(next_part_number,
                                                         inside_value_text)

            parts.append(list_part_text)
            focus.extend(['${}-rf'.format(child_name)] + next_focus)

            substitutions.append({'name': child_name, 
                                  'subs': child_substitutions + next_substitutions})
            next_part_number += 1

    return substitutions, parts, focus, next_text_number

def get_name_chain(template_tree):
    '''Get nested repeating names.

    Named rules can be nested. This discovers the nested relationship of the names.
    '''
    parents = collections.defaultdict(list)
    all_repeating = set()
    roots = set()

    for node in template_tree.xpath('.//*[@xule:repeat]', namespaces=_XULE_NAMESPACE_MAP):
        parent = node.get('{{{}}}repeatWithin'.format(_XULE_NAMESPACE_MAP['xule']))
        child = node.get('{{{}}}repeat'.format(_XULE_NAMESPACE_MAP['xule']))
        all_repeating.add(child)
        if parent is  None:
            roots.add(child)
        else:
            parents[parent].append(child)

    chain = dict()
    for root in roots:
        chain[root] = traverse_names(root, parents)

    return chain, all_repeating

def traverse_names(parent, parents, ancestry=None):
    children = []
    if ancestry is None: ancestry = tuple()
    for child in parents[parent]:
        if child in ancestry:
            raise FERCRenderException("Found in  a a loop in hierarchy of named rules in the template. {}".format(' --> '.join(ancestry + (child,))))
        if child in parents:
            children.append({child: traverse_names(child, parents, ancestry + (child,))})
        else:
            children.append(child)
    return children

def format_extra_expressions(replacement_node):
    extra_expressions = dict()
    for extra_node in replacement_node.findall('{{{}}}*'.format(etree.QName(replacement_node).namespace)):
        extra_name = etree.QName(extra_node.tag).localname
        if extra_name in _EXTRA_ATTRIBUTES + ('class', 'colspan', 'attribute', 'fact', 'html'):
            if extra_node.text is not None:
                exists_extra_expression = '$test-expr = {expr}; if exists($test-expr) $test-expr else none'.format(expr=extra_node.text.strip())
                if extra_name == 'class':
                    if 'class' not in extra_expressions: 
                        extra_expressions['class'] = list()
                    location = extra_node.attrib.get('location', 'self')
                    extra_expressions[extra_name].append('list("{}",{})'.format(location, exists_extra_expression)) 
                elif extra_name in _EXTRA_ATTRIBUTES + ('colspan', 'fact', 'html'): # these are inline attributes
                    extra_expressions[extra_name] = exists_extra_expression
                elif extra_name == 'attribute':
                    att_name = extra_node.get('name')
                    if att_name is None:
                        raise FERCRenderException("The <xule:attribute> element does not have a name attribute. Found on line {} of the template".format(extra_node.sourceline))  
                    att_loc = extra_node.get('location', 'self')
                    if extra_name not in extra_expressions:
                        extra_expressions[extra_name] = list()
                    extra_expressions[extra_name].append('list("{name}", "{loc}", {exp})'.format(
                        name=att_name, 
                        loc=att_loc,
                        exp=exists_extra_expression))
                else:
                    # This is some other element in the xule:replace, just skip it.
                    continue

    return extra_expressions      

def get_extra_attributes(expression_node):
    extra_attributes = dict()
    for name, val in expression_node.items():
        if name in _EXTRA_ATTRIBUTES:
            extra_attributes[name] = val
    return extra_attributes


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
                line_number_content = {'line-number-node': xule_node_locations[template_tree.getelementpath(line_number_node)],
                                               'start-number': start_value,
                                               'template-line-number': line_number_node.sourceline}
            else:
                line_number_content = {'line-number-node': xule_node_locations[template_tree.getelementpath(line_number_node)],
                                               'start-rule': rule_name,
                                               'template-line-number': line_number_node.sourceline}
            # Check if theres is a sub number
            if line_number_node.get('subNumber', '').lower() == 'true':
                line_number_content['sub-number'] = True

            line_number_subs[name].append(line_number_content)

    return line_number_subs, xule_rules, next_rule_number

def substituteTemplate(rule_meta_data, rule_results, template, modelXbrl, main_html, template_number, fact_number, processed_facts, processed_footnotes):
    '''Subsititute the xule expressions in the template with the generated values.'''

    # Determine if the template should be rendered
    if len(rule_meta_data.get('showifs', dict())) > 0:
        show_template_results = set()
        for showif_rule_name in rule_meta_data.get('showifs', dict()).keys():
            for showif_result in rule_results.get(showif_rule_name, tuple()):
                show_template_results.add(showif_result.getMessage().lower().strip() != 'false')

        # there is an evaluation that is False and no evaluation was True
        if False in show_template_results and not True in show_template_results:
            return 

    xule_node_locations = {node_number: xule_node for node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP))}
    
    # add the node locations to the nodes as attributes. This makes finding the node easier
    for node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=_XULE_NAMESPACE_MAP)):
        xule_node.set('{{{}}}xule-pos'.format(_XULE_NAMESPACE_MAP['xule']), str(node_number))

    line_number_subs = rule_meta_data['line-numbers']
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
    for rule_name, sub_info in rule_meta_data['substitutions'].items():
        if 'name' in sub_info and sub_info['name'] in repeating_nodes:
        #if len(subs) > 0 and subs[0].get('name') in repeating_nodes:
            repeating.append((rule_name, sub_info))
        else:
            non_repeating.append((rule_name, sub_info))

    # Sort the repeating so that the deepest template node substitutions are processed first. This will allow repeating within
    # repeating.
    def sort_by_ancestors(key):
        sub_info = key[1]
        if 'name' in sub_info:
            subs = sub_info['subs']
        else:
            subs = sub_info

        if len(subs) == 0:
            return 0
        return max([x.get('node-pos', 0) for x in subs ])
        #return len([x for x in xule_node_locations[subs[0]['replacement-node']].iterancestors()])

    repeating.sort(key=sort_by_ancestors, reverse=True)
    footnotes = collections.defaultdict(list)
    has_confidential = False
    for rule_name, sub_info in non_repeating + repeating:
        rule_has_confidential = substitute_rule(rule_name, sub_info, line_number_subs, rule_results[rule_name], template, 
                                                modelXbrl, main_html, repeating_nodes, xule_node_locations,
                                                context_ids, unit_ids, footnotes, template_number, fact_number, processed_facts)
        if rule_has_confidential: has_confidential = True

    footnote_page = build_footnote_page(template, template_number, footnotes, processed_footnotes, fact_number)
    if footnote_page is not None:
        template_body = template.find('xhtml:body', namespaces=_XULE_NAMESPACE_MAP)
        if template_body is None:
            raise FERCRenderException("Cannot find body of the template")  
        template_body.append(etree.Element('{{{}}}hr'.format(_XHTM_NAMESPACE), attrib={"class": "xbrl footnote-separator screen-page-separator"}))
        template_body.append(etree.Element('{{{}}}div'.format(_XHTM_NAMESPACE), attrib={'class': 'print-page-separator footnote-separator'}))
        template_body.append(footnote_page)

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

    return template, context_ids, unit_ids, has_confidential

def substitute_rule(rule_name, sub_info, line_number_subs, rule_results, template,
                    modelXbrl, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, 
                    footnotes, template_number, fact_number, processed_facts, 
                    all_result_part=None, refs=None, template_nsmap=None):
    # Determine if this is a repeating rule.
    new_nodes = []
    attribute_nodes = []

    has_confidential = False

    if template_nsmap is None:
        template_nsmap = template.getroot().nsmap

    #determing this rule is repeating
    repeating_model_node = None
    if 'name' in sub_info:
        repeat_attribute_name = '{{{}}}{}'.format(_XULE_NAMESPACE_MAP['xule'], 'repeat')
        repeating_nodes = {x.get(repeat_attribute_name): x for x in template.findall('//*[@xule:repeat]', _XULE_NAMESPACE_MAP)}
        if  sub_info['name'] in repeating_nodes:
            # This is a repeating rule
            repeating_model_node = repeating_nodes[sub_info['name']]
            model_tree = etree.ElementTree(repeating_model_node)
            repeat_count = 0 
    
    # Get the substitutions
    if 'name' in sub_info:
        subs = sub_info['subs']
    else:
        subs = sub_info

    for rule_result in rule_results:
        if isinstance(rule_result, list):
            json_rule_result = rule_result
        else:
            json_rule_result = json.loads(rule_result.getMessage())

        if repeating_model_node is not None:
            # Copy the model of the repeating node. This will be used to do the actual substitutions
            repeat_count += 1
            new_node = deepcopy(repeating_model_node)
            new_nodes.append(new_node)
            new_tree = etree.ElementTree(new_node)
            
            # Replace lineNumber nodes
            substitute_line_numbers(repeat_count, line_number_subs, sub_info['name'], model_tree, new_tree, modelXbrl, xule_node_locations)

        # need to get all the nodes that will be substitued from the new tree before doing the substitutions. Once the first substitution
        # is done, the structure of the new tree changes and and the path of the node to substitute in the model will be different than
        # in the new tree.
        sub_nodes = dict()
        for sub in subs:
            if 'replacement-node' in sub:
                # Get the node in the template to replace
                if repeating_model_node is None:
                    #sub_node = xule_node_locations[sub['replacement-node']]
                    sub_node = get_node_by_pos(template, sub['replacement-node'])
                    if sub_node is None:
                        break
                else:
                    # Find the node in the repeating model node
                    try:
                        model_sub_node = get_node_by_pos(model_tree, sub['replacement-node']) 
                        model_path = model_tree.getelementpath(model_sub_node)
                    except ValueError:
                        # The node to be replaced is not a descendant of the repeating note.
                        modelXbrl.warning("RenderError", "A 'replace' replacement for '{}' is not a descendant of the repeating HTML element.".format(sub['name']))
                        sub_node = None
                    else:                        
                        sub_node = new_tree.find(model_path)

                if sub_node is not None:
                    sub_nodes[sub['replacement-node']] = sub_node

        if sub_node is not None:
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

                if 'subs' in sub:
                    # This is a repeating within a repeating
                    substitute_rule(rule_name, sub, line_number_subs, json_result['value'], new_tree,
                        modelXbrl, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, 
                        footnotes, template_number, fact_number, processed_facts,
                        all_result_part or json_rule_result, refs or rule_result.refs, template_nsmap=template_nsmap)
                    continue

                classes_from_result = get_classes(json_result)
                attributes_from_result = get_attributes(json_result)
                # Add classes that go on the span that will replace the xule:relace node
                span_classes = classes_from_result.get('self',[])
                # if the json_result is none, there is nothing to substitute
                if json_result is not None:
                    # Check if the result is a fact
                    content = None
                    current_footnote_ids = []
                    is_redacted = False
                    is_confidential = False
                    parent_classes = []
                    if is_actual_fact(json_result, modelXbrl):
                        rule_focus_index = get_rule_focus_index(all_result_part or json_rule_result, json_result)
                        if rule_focus_index is not None:
                            use_refs = refs or rule_result.refs
                            fact_object_index = use_refs[rule_focus_index]['objectId']
                            model_fact = modelXbrl.modelObject(fact_object_index)
                            processed_facts.add(model_fact)
                            expression_node = get_node_by_pos(template, sub['expression-node'])
                            content, new_fact_id = format_fact(expression_node, 
                                                               model_fact, 
                                                               main_html, 
                                                               # This will check if the html flag is in meta data (sub) or calculated in the result
                                                               sub.get('html', json_result.get('html', False)), 
                                                               json_result, 
                                                               template_nsmap, 
                                                               fact_number)

                                            
                            # Save the context and unit ids
                            context_ids.add(model_fact.contextID)
                            if model_fact.unitID is not None:
                                unit_ids.add(model_fact.unitID)
                            # Check if the fact is redacted
                            is_redacted = fact_is_marked(model_fact, 'http://www.ferc.gov/arcrole/Redacted')
                            # Check if the fact is confidential
                            is_confidential = fact_is_marked(model_fact, 'http://www.ferc.gov/arcrole/Confidential')                                
                            # Check if there are footnotes
                            current_footnote_ids = get_footnotes(footnotes, model_fact, sub, new_fact_id, is_confidential, is_redacted)

                    else: # json_result['type'] == 's': # result is a string
                        # This will check if the html flag is in meta data (sub) or calculated in the result
                        if sub.get('html', json_result.get('html', False)):
                        #if sub.get('html', False):
                            content = etree.fromstring('<div class="sub-html">{}</div>'.format(clean_entities(json_result['value'])))
                        elif json_result['value'] is not None:
                            content = json_result['value']

                    if content is None:
                        span_classes += ['sub-value', 'sub-no-replacement']
                    else:
                        span_classes += ['sub-value', 'sub-replacement']
                    
                    if is_redacted: 
                        span_classes.append('redacted')
                        parent_classes.append('parent-redacted')
                    if is_confidential: 
                        has_confidential = True
                        span_classes.append('confidential')
                        parent_classes.append('parent-confidential')

                    # This is the node that will be replaced
                    sub_node = sub_nodes.get(sub['replacement-node'])

                    # If the node is going into an <a> or <span> then it needs to be a <span> otherwise it can be a <div>
                    xhtml_ancestry = {etree.QName(x.tag).localname.lower() for x in sub_node.xpath('ancestor-or-self::*') if etree.QName(x).namespace == _XHTM_NAMESPACE}

                    # Create the replacement node
                    if len({'a','span'} & xhtml_ancestry) > 0: #intersect the two sets
                        span = etree.Element('span', nsmap=_XULE_NAMESPACE_MAP)
                    else:
                        span = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)

                    span.set('class', ' '.join(span_classes))
                    for footnote_id in current_footnote_ids:
                        footnote_ref = etree.Element('a', attrib={"class": "xbrl footnote-ref", "id":"fr-{}-{}".format(template_number, footnote_id)}, nsmap=_XULE_NAMESPACE_MAP)
                        span.append(footnote_ref)
                    if isinstance(content, str):
                        span.text = content
                    elif etree.iselement(content): 
                        span.append(content)
                    elif content is not None:
                        span.text = str(content)
                    
                    if sub_node is not None:
                        sub_parent = sub_node.getparent()
                        sub_parent.replace(sub_node, span)
                        # Add classes to the parent
                        if len(classes_from_result['parent']) + len(parent_classes) > 0:
                            sub_parent.set('class', ' '.join(sub_parent.get('class','').split() + classes_from_result['parent'] + parent_classes))
                        # Add colspans to the parent
                        if json_result.get('colspan') is not None:
                            sub_parent.set('colspan', str(json_result['colspan']).strip())

                        # Add attributes
                        for att_loc, att in attributes_from_result.items():
                            for att_name, att_value in att.items():
                                attribute_nodes.append((att_loc, att_name, att_value, span))
    
    # Add the new repeating nodes
    for new_node in reversed(new_nodes):
        repeating_model_node.addnext(new_node)
    
    # Remove the model node
    if repeating_model_node is not None:
        model_parent = repeating_model_node.getparent()
        model_parent.remove(repeating_model_node)

    # Add calculated attributes
    for att_loc, att_name, att_value, node in attribute_nodes:
        if att_loc == 'self':
            att_node = node
        elif att_loc == 'parent':
            att_node = node.getparent()
        elif att_loc == 'grand':
            att_node = node.getparent().getparent()
        if att_node is not None:
            att_node.set(att_name, att_value)
    return has_confidential

def is_actual_fact(json_result, model_xbrl):
    if json_result['type'] == 'f':
        if 'dynamic-fact' in json_result:
            dynamic_fact = json_result.get('dynamic-fact')
            # Allow the strings 'true' and 'false' to be treated like booleans
            if isinstance(dynamic_fact, str):
                if dynamic_fact.lower().strip() == 'false':
                    dynamic_fact = False
                elif dynamic_fact.lower().strip() == 'true':
                    dynamic_fact = True
            if dynamic_fact is not None and not isinstance(dynamic_fact, bool) :
                model_xbrl.warning("RenderError", "Result of <xule:fact> in template is not boolean. Found '{}'".format(str(dynamic_fact)))
                # Set to none.
                dynamic_fact = False

            if dynamic_fact is None:
                return False
            else:
                return dynamic_fact
        else:
            return True
    else:
        return False

def clean_entities(text):
    '''Clean up HTML entities 
    
    lxml does not recognize HTML entities like &mdash;. As a work around this is converting these entities to 
    their HTML hex equivalent.
    '''

    if text is None:
        return text
    else:
        text = text.replace('&ldquo;', '&#x201c;')
        text = text.replace('&rdquo;', '&#x201d;')
        text = text.replace('&lsquo;', '&#x2018;')
        text = text.replace('&rsquo;', '&#x2019;')
        text = text.replace('&mdash;', '&#x2014;')
        text = text.replace('&ndash;', '&#x2013;')
        return text

def get_rule_focus_index(json_all_results, current_result):
    
    if current_result['is-fact'].lower() == 'false':
        # If the current result isn't really a fact, then there is no rule focus to get
        return None

    if isinstance(json_all_results, list):
        rule_focus_index, _x = traverse_for_facts(json_all_results, current_result)
    else:
        # The results is really just a single dictionary of one results. Just check if the fact is there
        if current_result['is-fact'].lower() == 'true':
            rule_focus_index = 0

    return rule_focus_index if rule_focus_index >= 0 else None  

def traverse_for_facts(json_results, current_result, focus_index=-1):
    found = False
    for child_result in json_results:
        if (child_result['type'] == 'f' and
            #child_result['value'] is not None and
            child_result['is-fact'].lower() == 'true'):
            focus_index += 1
        elif child_result['type'] == 'l':
            # This is an inner set of results. The value is a list of lists. The inner list being the parts of the 
            # inner repeat.
            for child_result_2 in child_result['value']:
                focus_index, found = traverse_for_facts(child_result_2, current_result, focus_index)
                if found:
                    break
        
        if child_result is current_result:
            found = True
            break
    
    return focus_index, found

def get_node_by_pos(template, pos):
    '''Find HTML node by the posiition in the tree'''
    pos_nodes =  template.xpath('.//*[@xule:xule-pos = {}]'.format(str(pos)), namespaces=_XULE_NAMESPACE_MAP)
    if len(pos_nodes) > 0:
        return pos_nodes[0]
    else:
        return None

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
                        start_value = int(start_result[0].getMessage().strip())
                    except ValueError:
                        # didn't an integer back, default to 1
                        start_value = 1
                line_number_info['start-number'] = start_value

def substitute_line_numbers(line_number, line_number_subs, name, model_tree, new_tree, modelXbrl, xule_node_locations):

    current_line_number = None
    # Substitute xule:lineNumber nodes in the repeating model
    for line_number_info in sorted(line_number_subs.get(name, tuple()), key=lambda k: k['line-number-node']):
        #line_number_node = xule_node_locations[line_number_info['line-number-node']]
        line_number_node = get_node_by_pos(model_tree, line_number_info['line-number-node'])
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
            if line_number_info.get('sub-number', False):
                new_line_number_span.text = "{}.{}".format(line_number_info.get('start-number', 1), line_number)
                current_line_number = current_line_number or "{}.{}".format(line_number_info.get('start-number', 1), line_number) 
            else:
                start_value = line_number_info.get('start-number', 1) - 1
                new_line_number_span.text = str(line_number + start_value)
                current_line_number = current_line_number or str(line_number + start_value)
            # Substitute
            sub_parent = sub_node.getparent()
            sub_parent.replace(sub_node, new_line_number_span)   

        # Current line number will have the first value for the line number
        return current_line_number  

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
            if item[1] is not None:
                classes[item[0]].extend(item[1].split())

    return classes
    

    #return [' '.join(x.split()) for x in json_result.get('classes', tuple())]

def get_attributes(json_result):
    '''Get the attributes fromthe evaluation of the xule:attribute expressions'''

    attributes = collections.defaultdict(dict)
    if json_result is None:
        return attributes

    working_attributes = collections.defaultdict(list)
    for item in json_result.get('attribute', tuple()):
        # item[0] is the attribute name
        # item[1] is the location: self, parent, grand
        # item[2] is the calculated value
        if len(item) == 3:
            # If the result doesn't have 3 items in it then there was no calculated value for the expression.
            working_attributes[(item[0], item[1])].append(str(item[2]))
    for att_name_and_loc, values in working_attributes.items():
        # att_name_and_loc: 0 = attribute name, 1 = attribute location
        attributes[att_name_and_loc[1]][att_name_and_loc[0]] = ' '.join(values)
    
    return attributes

def get_footnotes(footnotes, model_fact, sub, fact_id, is_confidential, is_redacted):
    ''' Find if there is a footnote for this fact

    This will find the the footnote and if there is one will add it to the footnotes dictionary.
    Also, the ids of the currently found footnotes are returned as a list
    '''
    network =  get_relationshipset(model_fact.modelXbrl,'http://www.xbrl.org/2003/arcrole/fact-footnote')
    rels = network.fromModelObject(model_fact)
    current_footnotes = []
    if len(rels) > 0:
        current_count = count_footnotes(footnotes) - 1
        for rel in rels:
            current_count += 1
            footnote_info = {'node': rel.toModelObject,
                            'model_fact': rel.fromModelObject,
                            'id': current_count,
                            'fact_id': fact_id,
                            'is_confidential': is_confidential,
                            'is_redacted': is_redacted}                        
            footnotes[sub['node-pos']].append(footnote_info)
            current_footnotes.append(current_count)
    
    return current_footnotes

def count_footnotes(footnotes):
    i = 0
    for k, v in footnotes.items():
        i += len(v)
    return i

def fact_is_marked(model_fact, arcrole):
    '''Check if the fact is marked as redacted or confdential based on the special footnote relationships'''
    network = get_relationshipset(model_fact.modelXbrl, arcrole)
    rels = network.fromModelObject(model_fact)
    if len(rels) > 0:
        return True
    else:
        return False

def get_relationshipset(model_xbrl, arcrole, linkrole=None, linkqname=None, arcqname=None, includeProhibits=False):
    # This checks if the relationship set is already built. If not it will build it. The ModelRelationshipSet class
    # stores the relationship set in the model at .relationshipSets.
    relationship_key = (arcrole, linkrole, linkqname, arcqname, includeProhibits)
    return model_xbrl.relationshipSets[relationship_key] if relationship_key in model_xbrl.relationshipSets else ModelRelationshipSet(model_xbrl, *relationship_key)

def build_footnote_page(template, template_number, footnotes, processed_footnotes, fact_number):
    '''Create the footnote page for the schedule'''

    footnote_counter = 0
    footnote_table = etree.Element('table', attrib={"class": "xbrl footnote-table"})
    for footnote_key in sorted(footnotes):
        for footnote in footnotes[footnote_key]:
            footnote_reference_id = 'fr-{}-{}'.format(template_number, footnote['id']) # This is the <a> around the footnote letter before the fact value
            #footnote_id = 'fn-{}-{}'.format(template_number, footnote['id'])
            footnote_id = 'fn-{}-t{}-n{}'.format(footnote['fact_id'], template_number, footnote_counter)
            footnote_ref_letter = convert_number_to_letter(footnote_counter)
            footnote_header_id = 'fh-{}-{}'.format(template_number, footnote['id'])
            #footnote_header_id = 'fn-{}'.format(uuid.uuid4().hex)
            concept_name = footnote['model_fact'].concept.qname.localName
            footnote_header_row = etree.Element('tr', attrib={"class":"xbrl footnote-header-row"})
            footnote_table.append(footnote_header_row)
            footnote_header_cell = etree.Element('td', attrib={"class":"xbrl footnote-header-cell"})
            footnote_header_row.append(footnote_header_cell)
            fact_ref = etree.Element('a', attrib={'class': 'xbrl footnote-to-fact-ref'})
            fact_ref.text = "({})".format(footnote_ref_letter)
            fact_ref.set('href', '#{}'.format(footnote_reference_id))
            header_text = " Concept: {}".format(concept_name)
            footnote_header_cell.append(fact_ref)
            fact_ref.tail = header_text
            footnote_header_cell.set('id', footnote_header_id)
            footnote_data_row = etree.Element('tr', attrib={"class": "xbrl footnote-data-row"})
            footnote_table.append(footnote_data_row)
            
            # # This section would only produce a single ix:footnote note no matter howmany times the footnote is outputted in the 
            # # rendering. This would prvent duplicate footnote nodes in the inline document. Change to create an ix:footnote
            # # node each time the footnote is outputted. Preserving this code incase it is decided to change back.
            # if footnote['node'] in processed_footnotes:
            #     # The footnote is expressed as an ix:footnote already, so just output the footnote text in the data cell
            #     if is_valid_xml(footnote['node'].xValue):
            #         footnote_data_cell = etree.fromstring('<td class="xbrl footnote-data-cell">{}</td>'.format(footnote['node'].xValue))
            #     else:
            #         footnote_data_cell = etree.Element('td', attrib={"class": "xbrl footnote-data-cell"})
            #         footnote_data_cell.text = footnote['node'].xValue     
            # else: # First time footnote - need to create the ix:footnote tag in the td
            #     footnote_data_cell = etree.Element('td', attrib={"class": "xbrl footnote-data-cell"})
            #     inline_footnote = create_inline_footnote_node(footnote['node'])
            #     footnote_data_cell.append(inline_footnote)
            #     processed_footnotes[footnote['node']]['footnote_id'] = footnote['node'].id
            #     processed_footnotes[footnote['node']]['fact_ids'].append(footnote['model_fact'].id)

            footnote_data_cell = etree.Element('td')
            footnote_data_cell_classes = ['xbr', 'footnote-data-cell']
            if footnote.get('is_confidential', False): 
                footnote_data_cell_classes.append('confidential')
            if footnote.get('is_redacted', False):
                footnote_data_cell_classes.append('redacted')
            footnote_data_cell.set('class', ' '.join(footnote_data_cell_classes))
            inline_footnote, is_preformatted = create_inline_footnote_node(footnote['node'])
            inline_footnote.set('id', footnote_id)
            if is_preformatted:
                div_node = etree.Element('div')
                div_node.set('class', 'preformatted-text')
                div_node.append(inline_footnote)
                footnote_data_cell.append(div_node)
            else:
                footnote_data_cell.append(inline_footnote)
            processed_footnotes[footnote['node']]['refs'].append((footnote['fact_id'], footnote_id))

            footnote_data_row.append(footnote_data_cell)
            
            # Update the footnote reference in the template
            footnote_ref_node = template.find("//*[@id='{}']".format(footnote_reference_id))
            if footnote_ref_node is not None:
                footnote_ref_node.text = '({})'.format(footnote_ref_letter)
                footnote_ref_node.set('href', '#{}'.format(footnote_header_id))

            footnote_counter += 1
    if len(footnote_table) == 0:
        return # there are no footnotes

    page = etree.Element('div', attrib={"class":"xbrl footnote-page"})
    # Add page header
    for node in nodes_for_class(template, 'schedule-header'):
        new_header = deepcopy(node)
        # Dedup fact ids in the copied schedule header
        for ix_node in node.xpath('.//ix:*', namespaces=_XULE_NAMESPACE_MAP):
            if _ORIGINAL_FACT_ID_ATTRIBUTE in ix_node.keys():
                ix_node.set('id', dedup_id(ix_node.get(_ORIGINAL_FACT_ID_ATTRIBUTE), fact_number))
        page.append(new_header)
        break

    page.append(
        E.table(
            E.tr(
                E.td("FOOTNOTE DATA", {"class": "xbrl footnote-page-title"})
            )
        , {"class": "xbrl footnote-page-title"})
    )

    # Add footnote table
    page.append(etree.Element('br'))
    page.append(footnote_table)

    # Add page footer
    for node in nodes_for_class(template, 'schedule-footer'):
        footer = deepcopy(node)
        # If there are facts in the footer, they will be duplicated. Need to update the fact ids to make
        # them unique.
        # dedup ids in the page footer.
        for ix_node in footer.xpath('.//ix:*', namespaces=_XULE_NAMESPACE_MAP):
            if _ORIGINAL_FACT_ID_ATTRIBUTE in ix_node.keys():
                ix_node.set('id', dedup_id(ix_node.get(_ORIGINAL_FACT_ID_ATTRIBUTE), fact_number))

        page.append(footer)
        break

    return page

def is_valid_xml(potential_text):
    '''Check if the passed string is valid XML'''
    try:
        # Wrap the text in a tag and see if it is valid xml. If it is not valid it etree will raise a syntax exception
        etree.fromstring('<test>{}</test>'.format(potential_text))
        return True
    except etree.XMLSyntaxError:
        return False

def create_inline_footnote_node(footnote_node):
    inline_footnote = etree.Element('{{{}}}footnote'.format(_XULE_NAMESPACE_MAP['ix']))
    inline_footnote.set('{http://www.w3.org/XML/1998/namespace}lang', footnote_node.get('{http://www.w3.org/XML/1998/namespace}lang'))
    if footnote_node.xValue is not None:
        inline_footnote.text = footnote_node.text
        for child in footnote_node.getchildren():
            inline_footnote.append(deepcopy(child))

    #inline_footnote.set('id', footnote_node.id)
    return inline_footnote, len(footnote_node) == 0

def convert_number_to_letter(num):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    result = ''
    while True:
        quotient, remainder = divmod(num, len(alphabet))
        result += alphabet[remainder]
        if quotient == 0:
            break
        else:
            num = quotient - 1
    return result[::-1] # reverse the string

def nodes_for_class(root, node_class):
    class_xpath = "descendant-or-self::*[@class and contains(concat(' ', normalize-space(@class), ' '), ' {} ')]".format(node_class)
    for node in root.xpath(class_xpath):
        yield node

def get_dates(modelXbrl):
    '''This returns a dictionary of dates for the filing'''

    if modelXbrl.modelDocument.type == Type.SCHEMA:
        # This will be a blank rendering
        return (
            'current-start',
            'current-end',
            'prior-start',
            'prior-end',
            'prior2-start',
            'prior2-end',
            'month-ends'
            )        

    report_year_fact = get_fact_by_local_name(modelXbrl, 'ReportYear')
    report_period_fact = get_fact_by_local_name(modelXbrl, 'ReportPeriod')
    report_year = report_year_fact.value if report_year_fact is not None else None
    report_period = report_period_fact.value if report_period_fact is not None else None
    if not report_year or not report_period:
        report_year_period_fact = get_fact_by_local_name(modelXbrl, 'ReportYearPeriod')
        if report_year_period_fact is not None:
            year_match = re.match(r'.*([1-2][0-9]{3})', report_year_period_fact.value)
            period_match = re.match(r'.*([qQ][1-4])', report_year_period_fact.value)
            report_year = year_match[1] if year_match is not None else None
            report_period = period_match[1].upper() if period_match is not None else None

    if not report_year or not report_period:
        raise FERCRenderException(
            'Cannot obtain a valid report year({year}) or report period({period}) from the XBRL document'.format(
                year=report_year, period=report_period
            )
        )
    month_day = {
        'Q4': ('01-01', '12-31'),
        'Q3': ('01-01', '09-30'),
        'Q2': ('01-01', '06-30'),
        'Q1': ('01-01', '03-31')
    }

    return (
        ('current-start={}-{}'.format(report_year, '01-01')),
        ('current-end={}-{}'.format(report_year, month_day[report_period][1])),
        ('prior-start={}-{}'.format(int(report_year) - 1, '01-01')),
        ('prior-end={}-{}'.format(int(report_year) - 1, month_day[report_period][1])),
        ('prior2-start={}-{}'.format(int(report_year) - 2, '01-01')),
        ('prior2-end={}-{}'.format(int(report_year) - 2, month_day[report_period][1])),
        ('month-ends={}'.format(','.join(tuple(str(calendar.monthrange(int(report_year), x)[1]) for x in range(1,13)))))
    )

def get_fact_by_local_name(modelXbrl, fact_name):
    for fact in modelXbrl.factsInInstance:
        if fact.concept.qname.localName == fact_name:
            return fact
    return None


def setup_inline_html(modelXbrl):
    # Create the new HTML rendered document
    # Add namespace prefixes
    namespaces = {None: "http://www.w3.org/1999/xhtml",
        'ixt1': "http://www.xbrl.org/inlineXBRL/transformation/2010-04-20",
        'xbrli': "http://www.xbrl.org/2003/instance",
        'ix': "http://www.xbrl.org/2013/inlineXBRL",
        'xbrldi': "http://xbrl.org/2006/xbrldi",
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'link': "http://www.xbrl.org/2003/linkbase",
        'xlink': "http://www.w3.org/1999/xlink",
        'ixtsec': "http://www.sec.gov/inlineXBRL/transformation/2015-08-31",
        'ixt4': "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12"}
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
        '</head>' \
        '<body><div style="display:none"><ix:header><ix:references/><ix:resources/></ix:header></div></body>' \
        '</html>'.format(namespace_string)

    html = etree.fromstring(initial_html_content)

    # Add schema and linbase references
    irefs = html.find('.//ix:references', namespaces=_XULE_NAMESPACE_MAP)
    for doc_ref in modelXbrl.modelDocument.referencesDocument.values():
        if doc_ref.referringModelObject.elementNamespaceURI == 'http://www.xbrl.org/2003/linkbase':
            if (doc_ref.referringModelObject.localName == 'schemaRef' and
                    ((hasattr(doc_ref, 'referenceType') and doc_ref.referenceType == 'href') or
                     (hasattr(doc_ref, 'referenceTypes') and 'href' in doc_ref.referenceTypes))):
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

def add_unused_facts_and_footnotes(main_html, modelXbrl, processed_facts, fact_number,footnotes, options):
    '''Add any facts that were not picked up in the templates.

    These are added to the hidden section of the inline document.
    '''
    context_ids = set()
    unit_ids = set()
    footnote_rels = set()
    # Find the ix:hiddent element
    hidden = get_hidden(main_html)
    # Get network of footnote arcs
    footnote_network =  get_relationshipset(modelXbrl,'http://www.xbrl.org/2003/arcrole/fact-footnote')
    # Get list of concept local names that should be excluded from displaying (these will still be in the inline document)
    show_exceptions = set(x.strip().lower() for x in (getattr(options, 'ferc_render_show_hidden_except', []) or []))
    hidden_count = 0
    displayed_hidden_count = 0
    # Process the unused facts
    unused_facts = set(modelXbrl.facts) - processed_facts
    for model_fact in unused_facts:
        hidden_count += 1
        if options.ferc_render_show_hidden and model_fact.concept.qname.localName.lower() not in show_exceptions:
            modelXbrl.info("HiddenFact",'\n{}'.format(display_fact_info(model_fact)))
            displayed_hidden_count += 1

        content, new_fact_id = format_fact(None, model_fact, main_html, False, None, None, fact_number)
        inline_content = content.xpath("descendant-or-self::*[namespace-uri()='{}']".format(_XULE_NAMESPACE_MAP['ix']))        
        hidden.append(inline_content[0]) 

        # Save the context and unit ids
        context_ids.add(model_fact.contextID)
        if model_fact.unitID is not None:
            unit_ids.add(model_fact.unitID)

        # Get any footnotes for unused concepts
        rels = footnote_network.fromModelObject(model_fact)
        for rel in rels:
            footnote_id = 'fn-{}'.format(new_fact_id)
            ix_footnote, is_preformatted = create_inline_footnote_node(rel.toModelObject)
            ix_footnote.set('id', footnote_id)
            hidden.append(ix_footnote)
            footnotes[rel.toModelObject]['refs'].append((new_fact_id, footnote_id))

    if options.ferc_render_show_hidden:
        modelXbrl.info("HiddenFactCount", "{} hidden facts, {} excluded from being displayed".format(hidden_count, hidden_count - displayed_hidden_count))

    return context_ids, unit_ids

def get_hidden(html):
    hidden = html.find('.//ix:hidden', namespaces=_XULE_NAMESPACE_MAP)
    if hidden is None:
        header = html.find('.//ix:header', namespaces=_XULE_NAMESPACE_MAP)
        hidden = etree.Element('{{{}}}hidden'.format(_XULE_NAMESPACE_MAP['ix']))
        header.insert(0, hidden) # insert as the first element
    return hidden

def add_contexts_to_inline(main_html, modelXbrl, context_ids):
    '''Add context to the inline document'''

    # Contexts are added to the ix:resources element in the inline
    resources = main_html.find('.//ix:resources', namespaces=_XULE_NAMESPACE_MAP)
    for context_id in context_ids:
        model_context = modelXbrl.contexts[context_id]
        # The model_context is a modelObject, but it is based on etree.Element so it can be added to 
        # the inline tree 
        copy_xml_node(model_context, resources) # This will copy the node and add it to the parent (resources)

def add_units_to_inline(main_html, modelXbrl, unit_ids):

    resources = main_html.find('.//ix:resources', namespaces=_XULE_NAMESPACE_MAP)
    for unit_id in unit_ids:
        model_unit = modelXbrl.units[unit_id]
        copy_xml_node(model_unit, resources) # This will copy the node and add it to the parent (resources)

def copy_xml_node(node, parent):
    '''Copies an xml node and handles qname values.

    Qname values are not recognized as qnames, so the namespace handling is not 
    managed correctly.
    '''
    new_node = etree.Element(node.qname.clarkNotation)
    parent.append(new_node)
    for att_name, att_value in node.xAttributes.items():
        if att_value.xValid >= VALID:
            new_node.set(att_name, copy_xml_value(new_node, att_value.xValue))

    if isinstance(node.xValue, QName):
        new_node.text = get_qname_value(new_node, node.xValue)
    else:
        new_node.text = node.text

    for child in node:
        copy_xml_node(child, new_node)

def get_qname_value(node, qname_value):
    # Get the root to find the namespace prefix
    root = node.getroottree().getroot()
    prefix_found = False
    nsmap = get_nsmap(root)

    for prefix in nsmap:
        if nsmap[prefix] == qname_value.namespaceURI:
            prefix_found = True
            break
    if not prefix_found:
        # Need to add a new namespace declaration
        # Make sure the prefix is not in the map.
        dup_num = 0
        prefix = qname_value.prefix or 'ns'
        while prefix in nsmap:
            prefix = '{}_{}'.format(prefix, dup_num)
            dup_num += 1
        # Add this namespace as a temporary element to the root.
        namespace_node = etree.Element(_NAMESPACE_DECLARATION)
        namespace_node.text = '{}:{}'.format(prefix, qname_value.namespaceURI)
        root.append(namespace_node) # This will be removed later

        #raise FERCRenderException("Cannot determine QName prefix for namespace '{}'".format(qname_value.namespaceURI))

    return '{}{}{}'.format(prefix or '', '' if prefix is None else ':', qname_value.localName)

def get_nsmap(root):
    # Get list of namepspaces on the root.
    nsmap = root.nsmap
    # Add in additional namespaces
    for child in root:
        if child.tag == _NAMESPACE_DECLARATION:
            additional_prefix, additional_namespace = child.text.split(':', 1)
            nsmap[additional_prefix] = additional_namespace
    
    return nsmap

def copy_xml_value(node, xValue):
    if isinstance(xValue, QName):
        return get_qname_value(node, xValue)
    else:
        return xValue




def copy_unit(model_unit):
    # The messure value of the unites are qname. If you just copy the model_unit to the new inline
    # tree, it will not handle the qname values of the <measure> elements correctly.
    new_unit = etree.Element('{http://www.xbrl.org/2003/instance}unit')
    
    if model_unit.isDivide:
        pass
    else:
        for child in model_unit:
            if child.tag == '{http://www.xbrl.org/2003/instance}measure':
                new_measure = etree.Element('{http://www.xbrl.org/2003/instance}measure')
                new_measure.text = child.xValue # This should be a qname value
                new_unit.append(new_measure)
    
    return new_unit






    '''
    if model_unit.isDivide:
        new_unit_parent = etree.Element('{{{}}}divide'.format(_XBRLI_NAMESPACE))
        new_unit.append(new_unit_parent)
        for child in model_unit:
            if child.tag == '{http://www.xbrl.org/2003/instance}divide':
                measure_parent = child
                break
    else:
        new_unit_parent = new_unit
        measure_parent = model_unit

    for child_node in measure_parent:
        # The child will be either a <measure> or a <divide>
        if child_node.tag == '{http://www.xbrl.org/2003/instance}measure':
            new_measure = etree.Element('{http://www.xbrl.org/2003/instance}measure')
            new_measure.text = child_node.xValue
            new_unit_parent.append(new_measure)
    '''
def add_footnote_relationships(main_html, processed_footnotes):

    resources = main_html.find('.//ix:resources', namespaces=_XULE_NAMESPACE_MAP)
    for footnote_info in processed_footnotes.values():
        # # This code was used when the footnote was only created once in the inline document
        #rel = etree.Element('{{{}}}relationship'.format(_XULE_NAMESPACE_MAP['ix']))
        #rel.set('arcrole', 'http://www.xbrl.org/2003/arcrole/fact-footnote')
        #rel.set('linkRole', 'http://www.xbrl.org/2003/role/link')        
        #rel.set('fromRefs', ' '.join(footnote_info['fact_ids']))
        #rel.set('toRefs', footnote_info['footnote_id'])

        for fact_id, footnote_id in footnote_info['refs']:
            rel = etree.Element('{{{}}}relationship'.format(_XULE_NAMESPACE_MAP['ix']))
            rel.set('arcrole', 'http://www.xbrl.org/2003/arcrole/fact-footnote')
            rel.set('linkRole', 'http://www.xbrl.org/2003/role/link')        
            rel.set('fromRefs', fact_id)
            rel.set('toRefs', footnote_id)

            resources.append(rel)
    

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
    if isinstance(parser, optparse.OptionParser):
        parserGroup = optparse.OptionGroup(parser,
                                           "FERC Renderer")
        parser.add_option_group(parserGroup)
    else:
        parserGroup = parser
    
    parserGroup.add_option("--ferc-render-compile", 
                      action="store_true", 
                      dest="ferc_render_compile", 
                      help=_("Indicator to compile a template set. Reuires --ferc-render-template and --ferc-render-template_set options"))

    parserGroup.add_option("--ferc-render-render", 
                      action="store_true", 
                      dest="ferc_render_render", 
                      help=_("Indicator to render an instance with a template set. Reuires --ferc-render-template_set options and XBRL instnace (-f)"))

    parserGroup.add_option("--ferc-render-combine", 
                      action="store", 
                      dest="ferc_render_combine", 
                      help=_("Combine indicated template sets into a single template set. This argument can take a '|' separated list of "
                             "template sets or folders. Template will be added in the order this list. If a folder is indicated, then all "
                             " the template sets in the filder and its decendants will be added."))

    parserGroup.add_option("--ferc-render-list", 
                      action="store_true", 
                      dest="ferc_render_list", 
                      help=_("List the templates in a template set."))

    parserGroup.add_option("--ferc-render-extract", 
                      action="store", 
                      dest="ferc_render_extract", 
                      help=_("Extract the templates from a template set. This option identifies the folder to extract the templates to."))                      

    parserGroup.add_option("--ferc-render-namespace",
                      action="append",
                      dest="ferc_render_namespaces",
                      help=_("Create namespace mapping for prefix used in the template in the form of prefix=namespace. To map multiple "
                             "namespaces use separate --ferc-render-space for each one."))

    parserGroup.add_option("--ferc-render-template", 
                      action="append", 
                      dest="ferc_render_template", 
                      help=_("The HTML template file"))

    parserGroup.add_option("--ferc-render-template-set", 
                      action="store", 
                      dest="ferc_render_template_set", 
                      help=_("Compiled template set file"))

    parserGroup.add_option("--ferc-render-inline", 
                      action="store", 
                      dest="ferc_render_inline", 
                      help=_("The generated Inline XBRL file"))        

    parserGroup.add_option("--ferc-render-css-file", 
                      action="store", 
                      dest="ferc_render_css_file", 
                      help=_("Identify the CSS file that sould be used. This will overwrite the name of the CSS file that is included in the template set."))   

    parserGroup.add_option("--ferc-render-inline-css", 
                      action="store_true", 
                      dest="ferc_render_inline_css", 
                      help=_("Indicates that the CSS should be inlined in the generated HTML file. This option must be used with --frec-render-css-file."))   

    parserGroup.add_option("--ferc-render-save-xule", 
                      action="store", 
                      dest="ferc_render_save_xule", 
                      help=_("Name of the generated xule file to save before complining the rule set."))

    parserGroup.add_option("--ferc-render-show-xule-log",
                      action="store_true",
                      dest="ferc_render_show_xule_log",
                      help=_("Show the log messages when running the xule rules. By default these messages are not displayed."))

    parserGroup.add_option("--ferc-render-constants", 
                      action="store", 
                      dest="ferc_render_constants", 
                      help=_("Name of the constants file. This will default to render-constants.xule."))  

    parserGroup.add_option("--ferc-render-partial",
                      action="store_true",
                      dest="ferc_render_partial",
                      help=_("Indicates that this is a partial rendering such as a single schedule. This will prevent outputing unused facts in the "
                             "hidden section of the inline document."))

    parserGroup.add_option("--ferc-render-show-hidden",
                      action="store_true",
                      dest="ferc_render_show_hidden",
                      help=_("Display facts that are are written to the hidden section of the inline XBRL document."))   

    parserGroup.add_option("--ferc-render-show-hidden-except",
                      action="append",
                      dest="ferc_render_show_hidden_except",
                      help=_("Concept local name for facts that should not be displayed when showing hidden facts. To list multiples, use this option for each name."))                                                  

    parserGroup.add_option("--ferc-render-debug",
                      action="store_true",
                      dest="ferc_render_debug",
                      help=_("Run the rendered in debug mode."))

    parserGroup.add_option("--ferc-render-only",
                      action="store",
                      dest="ferc_render_only",
                      help=_("List of template names to render. All others will be skipped. Template names are separated by '|' character."))


def fercCmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()
    
    if (options.ferc_render_compile is None and 
        options.ferc_render_render is None and 
        options.ferc_render_combine is None and 
        options.ferc_render_list is None and
        options.ferc_render_extract is None):
        parser.error(_("The render plugin requires either --ferc-render-compile, --ferc-render-render, --ferc-render-combine, --ferc-render-list and/or --ferc-render-extract"))

    if options.ferc_render_compile:
        if options.ferc_render_template is None and options.ferc_render_template_set is None:
            parser.error(_("Compiling a template set requires --ferc-render-template and --ferc-render-template-set."))
    
    if options.ferc_render_render:
        if options.ferc_render_template_set is None:
            parser.error(_("Rendering requires --ferc-render-template-set"))

    if options.ferc_render_combine is not None:
        if options.ferc_render_template_set is None:
            parser.error(_("Combining template sets requires --ferc-render-template-set"))

    if options.ferc_render_combine is not None:
        combine_template_sets(cntlr, options)

    if options.ferc_render_list and options.ferc_render_template_set is None:
        parser.error(_("Listing the templates in a template set requires a --ferec-render-template-set."))

    if options.ferc_render_extract and options.ferc_render_template_set is None:
        parser.error(_("Extracting the templates from a template set requires a --ferec-render-template-set."))        

    if options.ferc_render_inline_css and not options.ferc_render_css_file:
        parser.error(_("--ferc-render-inline-css requires the --ferc-render-css-file option to identify the css file."))

    if options.ferc_render_inline_css and options.ferc_render_css_file:
        # make sure the css file exists
        if not os.path.exists(options.ferc_render_css_file):
            parser.error(_("CSS file '{}' does not exists.".format(options.ferc_render_css_file)))

    validate_namespace_map(options, parser)

    if options.ferc_render_compile:
        compile_templates(cntlr, options)

    if options.ferc_render_list:
        list_templates(cntlr, options)     

    if options.ferc_render_extract:
        extract_templates(cntlr, options)


def validate_namespace_map(options, parser):
    options.namespace_map = dict()
    default_namespace = None
    for map in getattr(options, "ferc_render_namespaces") or tuple():
        map_list = map.split('=', 1)
        if len(map_list) == 1:
            if map_list[0].strip == '':
                parser.error(_("--ferc-render-namespace namespace without a prefix (default) must have a non space value."))
            elif None in options.namespace_map:
                parser.error(_("--ferc-render-namespace there can only be one default namespace"))
            else:
                options.namespace_map[None] = map_list[0].strip()
        elif len(map_list) == 2:
            prefix = map_list[0].strip()
            ns = map_list[1].strip()
            if prefix == '':
                parser.error(_("--ferc-render-namespace prefix must have a non space value"))
            if ns == '':
                parser.error(_("--ferc-render-namespace namespace must have non space value"))
            if prefix in options.namespace_map:
                parser.error(_("--ferc-render-namespace prefix '{}' is mapped more than once".format(prefix)))
            options.namespace_map[prefix] = ns
        else:
            parser.error(_("--ferc-render-namespace invalid content: {}".format(map)))

def compile_templates(cntlr, options):

    template_catalog = {'templates': []}
    template_set_file_name = os.path.split(options.ferc_render_template_set)[1]

    css_file_names = set()
    with zipfile.ZipFile(options.ferc_render_template_set, 'w') as template_set_file: 
        template_number = 0   
        for template_full_file_name in getattr(options, 'ferc_render_template', tuple()):
            css_file_names.update(process_single_template(cntlr, options, template_catalog['templates'], template_set_file, template_full_file_name, template_number))
            template_number += 1

        template_catalog['css'] = list(css_file_names)
        template_set_file.writestr('catalog.json', json.dumps(template_catalog, indent=4))

    cntlr.addToLog(_("Writing template set file: {}".format(template_set_file_name)), 'info')

def process_single_template(cntlr, options, template_catalog, template_set_file, template_full_file_name, template_number):
    # Create a temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Process the HTML template.
        xule_rule_text, rule_meta_data, template, template_string, css_file_names = process_template(cntlr, template_full_file_name, options)
        
        # Save the xule rule file if indicated
        if options.ferc_render_save_xule is not None:
            with open(options.ferc_render_save_xule, 'w') as xule_file:
                xule_file.write(xule_rule_text)

        # Compile Xule rules
        title = template.find('//xhtml:title', _XULE_NAMESPACE_MAP)
        if title is None:
            raise FERCRenderException("Template does not have a title")

        # Get some names set up
        template_file_name = os.path.split(template_full_file_name)[1]
        template_name = os.path.splitext(template_file_name)[0]

        template_file_name = "templates/t{tn}/t{tn}.html".format(tn=str(template_number))
        xule_text_file_name = "templates/t{tn}/t{tn}.xule".format(tn=str(template_number))
        xule_rule_set_file_name = "templates/t{tn}/t{tn}-ruleset.zip".format(tn=str(template_number))
        rule_meta_data_file_name = "templates/t{tn}/t{tn}-rule-meta.json".format(tn=str(template_number))

        # xule file name
        xule_rule_file_name = os.path.join(temp_dir, 'temp_rule_file.xule')   #'{}.xule'.format(title.text)
        with open(xule_rule_file_name, 'w') as xule_file:
            xule_file.write(xule_rule_text)

        # xule rule set name
        xule_rule_set_name = os.path.join(temp_dir, 'temp-ruleset.zip')
        compile_method = getXuleMethod(cntlr, 'Xule.compile')
        compile_method(xule_rule_file_name, xule_rule_set_name, 'pickle', getattr(options, "xule_max_recurse_depth"))

        template_catalog.append({'name': template_name,
                            'template': template_file_name,
                            'xule-text': xule_text_file_name,
                            'xule-rule-set': xule_rule_set_file_name,
                            'rule-meta-data': rule_meta_data_file_name})

        template_set_file.writestr(template_file_name, template_string) # template
        template_set_file.writestr(xule_text_file_name, xule_rule_text) # xule text file
        template_set_file.write(xule_rule_set_name, xule_rule_set_file_name) # xule rule set
        template_set_file.writestr(rule_meta_data_file_name, json.dumps(rule_meta_data, indent=4)) # substitutions filef

    return css_file_names

def get_file_or_url(file_name, cntlr):
    try:
        file_source = FileSource.openFileSource(file_name, cntlr)
        file_object = file_source.file(file_name, binary=True)[0]    
        return file_object
    except:
        raise FERCRenderException("Cannot open file: {}".format(file_name))

def list_templates(cntlr, options):
    zipIO = get_file_or_url(options.ferc_render_template_set, cntlr)
    with zipfile.ZipFile(zipIO, 'r') as ts_file:
        try:
            catalog_file_info = ts_file.getinfo('catalog.json')
        except KeyError:
            # This zip file does not contain a catalog so it is not a template set
            raise FERCRenderException("The file '{}' is not a template set.".format(options.ferc_render_template_set))
        with ts_file.open(catalog_file_info, 'r') as catalog_file:
            catalog = json.load(io.TextIOWrapper(catalog_file))
        for template_info in catalog['templates']:
            cntlr.addToLog(template_info['name'],'info')

def extract_templates(cntlr, options):  
    zipIO = get_file_or_url(options.ferc_render_template_set, cntlr)          
    with zipfile.ZipFile(zipIO, 'r') as ts_file:
        try:
            catalog_file_info = ts_file.getinfo('catalog.json')
        except KeyError:
            # This zip file does not contain a catalog so it is not a template set
            raise FERCRenderException("The file '{}' is not a template set.".format(options.ferc_render_template_set))
        with ts_file.open(catalog_file_info, 'r') as catalog_file:
            catalog = json.load(io.TextIOWrapper(catalog_file))
        # Check that the destination folder exists
        os.makedirs(options.ferc_render_extract, exist_ok=True)
        
        for template_info in catalog['templates']:
            # Extract the tempalte
            contents = ts_file.read(template_info['template']) 
            new_name = os.path.join(options.ferc_render_extract, '{}.html'.format(template_info['name']))
            with open(new_name, 'wb') as new_file:
                new_file.write(contents)
            cntlr.addToLog("Extracted: {}".format(new_name),'info')  

            # Extract the individual template set
            ts_name = os.path.join(options.ferc_render_extract, '{}.zip'.format(template_info['name']))
            with zipfile.ZipFile(ts_name, 'w', zipfile.ZIP_DEFLATED) as new_ts_file:
                new_catalog = {'templates': [], 'css': []}
                new_catalog['css'] = catalog['css'] # copy the css from the combined template set to the new one
                # Set the file names to 't0'
                # Copy the files
                # 'line-numbers' and 'substitutions' is being replace with 'rule-meta-data', but left here for backward compatibility
                new_info = {'name': template_info['name']}
                for key in ('line-numbers', 'substitutions', 'template', 'xule-rule-set', 'xule-text', 'rule-meta-data'):
                    orig_file_name = template_info.get(key)
                    if orig_file_name is not None:
                        orig_file_ext = os.path.splitext(orig_file_name)[1]
                        new_file_name = 'templates/t0/t0-{key}{ext}'.format(key=key, ext=orig_file_ext)
                        file_data = ts_file.read(orig_file_name)
                        new_ts_file.writestr(new_file_name, file_data)
                        new_info[key] = new_file_name
                new_catalog['templates'].append(new_info)
                new_ts_file.writestr('catalog.json', json.dumps(new_catalog, indent=4))
            cntlr.addToLog("Extracted: {}".format(ts_name),'info') 

def combine_template_sets(cntlr, options):
    template_sets = get_list_of_template_sets(options.ferc_render_combine, cntlr)
    new_catalog = {'templates': [], 'css': []}
    loaded_template_names = set()
    template_number = 0
    # Create the new combined template set file
    with zipfile.ZipFile(options.ferc_render_template_set, 'w') as combined_file:
        for template_set in template_sets:
            # check that it is a zip file
            try:
                with zipfile.ZipFile(template_set, 'r') as ts_file:
                    try:
                        catalog_file_info = ts_file.getinfo('catalog.json')
                    except KeyError:
                        # This zip file does not contain a catalog so it is not a template set
                        continue
                    with ts_file.open(catalog_file_info, 'r') as catalog_file:
                        catalog = json.load(io.TextIOWrapper(catalog_file))
                    
                    # Update the css list
                    new_catalog['css'] = list(set(catalog['css'] + new_catalog['css']))

                    for template_info in catalog['templates']:
                        # Check if there is already a template loaded
                        if template_info['name'] in loaded_template_names:
                            cntlr.addToLog(_("Template '{}' is already loaded. Skipping.".format(template_info['name'])), "warning")
                            continue
                        
                        new_info = {'name': template_info['name']}
                        # Copy the files
                        # 'line-numbers' and 'substitutions' is being replace with 'rule-meta-data', but left here for backward compatibility
                        for key in ('line-numbers', 'substitutions', 'template', 'xule-rule-set', 'xule-text', 'rule-meta-data'):
                            orig_file_name = template_info.get(key)
                            if orig_file_name is not None:
                                orig_file_ext = os.path.splitext(orig_file_name)[1]
                                new_file_name = 'templates/t{tn}/t{tn}-{key}{ext}'.format(tn=template_number, key=key, ext=orig_file_ext)
                                file_data = ts_file.read(orig_file_name)
                                combined_file.writestr(new_file_name, file_data)
                                new_info[key] = new_file_name
                    
                        # Copy the catalog
                        new_catalog['templates'].append(new_info)

                        template_number += 1
            except (FileNotFoundError, zipfile.BadZipFile, OSError):
                # ignore the file if it is not a zip file
                pass
        
        # Write the catalog
        combined_file.writestr('catalog.json', json.dumps(new_catalog, indent=4))

def get_list_of_template_sets(ts_value, cntlr):
    # iterate through the list of files and folders and find all the files.
    file_list = []
    manifest_list = None
    for file_or_folder in ts_value.split("|"):
        if not os.path.exists(file_or_folder):  
            raise FERCRenderException("Template set or folder not found: {}".format(file_or_folder))
        if os.path.isfile(file_or_folder):
            file_list.append(file_or_folder)
        elif os.path.isdir(file_or_folder):
            if os.path.exists(os.path.join(file_or_folder, 'template-manifest.txt')):
                # use the manifest file to determine the order of files.
                cntlr.addToLog(_("Using template-manifest.txt file."), "info")
                with open(os.path.join(file_or_folder, 'template-manifest.txt'), 'r') as manifest:
                    manifest_list = [os.path.realpath(os.path.join(file_or_folder, x.strip())) for x in manifest.readlines()]
                for template_file in manifest_list:
                    if os.path.exists(template_file):
                        file_list.append(template_file)
                    else:
                        cntlr.addToLog(_("File in template-manifest.txt but not found: {}.".format(template_file)), "warning")
            else:
                for dirpath, dirnames, filenames in os.walk(file_or_folder):
                    for filename in sorted(filenames):
                        template_file = os.path.realpath(os.path.join(dirpath, filename))
                        file_list.append(template_file)
    
    return file_list

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    '''Render a filing'''
    
    if options.ferc_render_render and options.ferc_render_template_set is not None:
        render_report(cntlr, options, modelXbrl, *args, **kwargs)

def render_report(cntlr, options, modelXbrl, *args, **kwargs):
    if options.ferc_render_debug:
        start_time = datetime.datetime.now()

    used_context_ids = set()
    used_unit_ids = set()

    template_number = 0
    fact_number = initialize_fact_number(modelXbrl)
    processed_facts = set() # track which facts have been outputed

    # Footnotes were originally only outputted once as an ix
    processed_footnotes = collections.defaultdict(lambda: {'footnote_id': None, 'fact_ids': list(), 'refs': list()}) # track when a footnote is outputted.

    has_confidential = False

    main_html = setup_inline_html(modelXbrl)

    schedule_divs = []
    zipIO = get_file_or_url(options.ferc_render_template_set, cntlr)
    with zipfile.ZipFile(zipIO, 'r') as ts:
        with ts.open('catalog.json', 'r') as catalog_file:
            template_catalog = json.load(io.TextIOWrapper(catalog_file))

        # Get name of rendered html file
        if options.ferc_render_inline is None:
            inline_name = '{}.html'.format(os.path.splitext(os.path.split(options.ferc_render_template_set)[1])[0])
        else:
            inline_name = options.ferc_render_inline

        # Add css link
        add_css(main_html, template_catalog, options)

        # Iterate through each of the templates in the catalog
        for catalog_item in template_catalog['templates']: # A catalog item is a set of files for a single template

            if options.ferc_render_only is not None:
                if catalog_item['name'] not in options.ferc_render_only.split('|'):
                    continue

            if options.ferc_render_debug:
                cntlr.addToLog("{} Processing template '{}'".format(str(datetime.datetime.now()), catalog_item.get('name', 'UNKNOWN')),"info")
            # Get the html template
            with ts.open(catalog_item['template']) as template_file:
                try:
                    template = etree.parse(template_file)
                except etree.XMLSchemaValidateError:
                    raise FERCRenderException("Template file '{}' is not a valid XHTML file.".format(catalog_item['template']))

            if 'rule-meta-data' in catalog_item:
                with ts.open(catalog_item['rule-meta-data']) as meta_file:
                    rule_meta_data = json.load(io.TextIOWrapper(meta_file))
            else:
                # This is for backward compatibility. The new templates put the substitutions and line_number_subs in the rule meta data.
                # The old format had separate entries in the catalog for the substitutions and line_number_subs.
                # Get the substitutions
                with ts.open(catalog_item['substitutions']) as sub_file:
                    meta_substitutions = json.load(io.TextIOWrapper(sub_file))
                # Get line number substitutions
                with ts.open(catalog_item['line-numbers']) as line_number_file:
                    meta_line_number_subs = json.load(io.TextIOWrapper(line_number_file))

                rule_meta_data = {'substitutions': meta_substitutions,
                                    'line-numbers': meta_line_number_subs}

            # Get the date values from the instance
            xule_date_args = get_dates(modelXbrl)

            # Run Xule rules
            # Create a log handler that will capture the messages when the rules are run.
            log_capture_handler = _logCaptureHandler()
            if not options.ferc_render_show_xule_log:
                cntlr.logger.removeHandler(cntlr.logHandler)
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
            if not options.ferc_render_show_xule_log:
                cntlr.logger.addHandler(cntlr.logHandler)
            
            # Substitute template
            template_number += 1
            template_result = substituteTemplate(rule_meta_data, 
                                                    log_capture_handler.captured, template, modelXbrl, main_html,
                                                    template_number, fact_number, processed_facts, processed_footnotes)
            if template_result is not None: # the template_result is none when a xule:showif returns false
                rendered_template, template_context_ids, template_unit_ids, template_has_confidential = template_result
                used_context_ids |= template_context_ids
                used_unit_ids |= template_unit_ids
                if template_has_confidential: has_confidential = True
                # Save the body as a div
                body = rendered_template.find('xhtml:body', namespaces=_XULE_NAMESPACE_MAP)
                if body is None:
                    raise FERCRenderException("Cannot find body of the template: {}".format(os.path.split(catalog_item['template'])[1]))   
                body.tag = 'div'
                schedule_divs.append(body)

    main_body = main_html.find('xhtml:body', namespaces=_XULE_NAMESPACE_MAP)

    # Add confidential indicator
    # if has_confidential: 
    #     watermark_div = etree.Element('{{{}}}div'.format(_XHTM_NAMESPACE))
    #     watermark_div.set('id', 'watermark')
    #     watermark_p = etree.Element('{{{}}}p'.format(_XHTM_NAMESPACE))
    #     watermark_p.set('id', 'watermark')
    #     watermark_p.text = "Contains confidential information"
    #     watermark_div.append(watermark_p)
    #     main_body.append(watermark_div)
    for div in schedule_divs:
        main_body.append(div)
        if div is not schedule_divs[-1]: # If it is not the last span put a separator in
            #main_body.append(etree.fromstring('<hr xmlns="{}"/>'.format(_XHTM_NAMESPACE)))
            main_body.append(etree.Element('{{{}}}hr'.format(_XHTM_NAMESPACE), attrib={'class': 'screen-page-separator schedule-separator'}))
            main_body.append(etree.Element('{{{}}}div'.format(_XHTM_NAMESPACE), attrib={'class': 'print-page-separator sechedule-separator'}))
    
    if not options.ferc_render_partial:
        additional_context_ids, additional_unit_ids = add_unused_facts_and_footnotes(main_html, 
                                                                                        modelXbrl, 
                                                                                        processed_facts, 
                                                                                        fact_number, 
                                                                                        processed_footnotes,
                                                                                        options)
        used_context_ids |= additional_context_ids
        used_unit_ids |= additional_unit_ids

    add_contexts_to_inline(main_html, modelXbrl, used_context_ids)
    add_units_to_inline(main_html, modelXbrl, used_unit_ids)
    add_footnote_relationships(main_html, processed_footnotes)
    
    # Write generated html
    #main_html.getroottree().write(inline_name, pretty_print=True, method="xml", encoding='utf8', xml_declaration=True)
    # Using c14n becaue it will force empty elements to have a start and end tag. This is necessary becasue a <div/> element is
    # interpreted by a browser as not having an end tag. When you have <div/><div>content</div> the browser interprets it as
    # <div><div>content</div></div>
    
    #main_html.getroottree().write(inline_name, pretty_print=True, method="c14n")
    dedup_id_full_document(main_html, fact_number)
    for elem in main_html.iter():
        # Clean up empty tags
        if elem.text == None:
            elem.text = ''
        # Fix XHTML tags. Sometimes template authors use upper case in the tag names i.e. <Span> instead of <span>.
        # Most browsers will ignore the case so it appears valid, but it is not valid to the XHTM schema.
        tag = elem.tag
        if isinstance(tag, str):
            tag_qname = etree.QName(tag)
            if tag_qname.namespace == _XHTM_NAMESPACE:
                elem.tag = tag.lower()
        # Removed _ORIGINAL_FACT_ID_ATTRIBUTE
        if _ORIGINAL_FACT_ID_ATTRIBUTE in elem.attrib:
            elem.attrib.pop(_ORIGINAL_FACT_ID_ATTRIBUTE)

    main_html = fix_namespace_declarations(main_html)

    output_string = etree.tostring(main_html.getroottree(), pretty_print=True, method="xml")
    # Fix the <br></br> tags. When using the c14n method all empty elements will be written out with start and end tags. 
    # This causes issues with browsers that will interpret <br></br> as 2 <br> tags.
    output_string = output_string.decode().replace('<br></br>', '<br/>')

    # Write the file or output to zip
    
    # Code snippet to unescape the "greater than" signs in the .css that the lxml is escaping.
    output_string = re.sub('<style>(.*?)</style>',fix_style, output_string, 1, re.DOTALL)

    responseZipStream = kwargs.get("responseZipStream")
    if responseZipStream is not None:
        _zip = zipfile.ZipFile(responseZipStream, "a", zipfile.ZIP_DEFLATED, True)
        if responseZipStream is not None:
            _zip.writestr(inline_name, output_string)
            _zip.writestr("log.txt", cntlr.logHandler.getJson())
            _zip.close()
            responseZipStream.seek(0)
    else:
        with open(inline_name, 'w') as output_file:
            output_file.write(output_string)

    cntlr.addToLog(_("Rendered template as '{}'".format(inline_name)), 'info')

    if options.ferc_render_debug:
        end_time = datetime.datetime.now()
        cntlr.addToLog(_("Processing time: {}".format(str(end_time - start_time))), "info")

def dedup_id_full_document(root, fact_number):
    all_ids = collections.defaultdict(set)

    for elem in root.xpath('.//*[@id]'):
        all_ids[elem.get('id')].add(elem)

    dup_ids = [x for x in all_ids if len(all_ids[x]) > 1]
    # These are the duplicate ids
    for dup_id in dup_ids:
        xbrl_elements = {x for x in all_ids[dup_id] if etree.QName(x).namespace in (_XULE_NAMESPACE_MAP['ix'], _XBRLI_NAMESPACE)}
        # XBRL elements should already be dudupped, and it is important that these ids don't change.
        for elem in all_ids[dup_id] - xbrl_elements: 
            elem.set('id', dedup_id(dup_id, fact_number))

def fix_namespace_declarations(root):
    '''This adds additional namespace declarations to the <html> element.

    The namespace declarations are added element nodes of <namespace_declaration> that contain the 
    prefix and the namespace URI for namespaces to be added. These nodes are added when copying
    context and unit nodes and there are attributes or element VALUES that are qnames. lxml does
    not handle the namespace when the value of an element or attribute is a qname.
    '''
    # Get the full ns_map
    new_nsmap = get_nsmap(root)
    new_root = etree.Element(root.tag, nsmap=new_nsmap)
    # Copy any attributes
    for aname, avalue in root.attrib.items():
        new_root.set(aname, avalue)
    # Move the childern
    for child in root:
        if child.tag != _NAMESPACE_DECLARATION:
            new_root.append(child)

    return new_root

def fix_style(style_match):
    if len(style_match.groups()) > 0:
        style_text = style_match.group(1)
        return '<style type="text/css">\n{}{}{}\n</style>'.format(
            '/*<![CDATA[*/',
            style_text.replace("&gt;",">"),
            '/*]]>*/')
    else:
        return '<style type="text/css"></style>'


def add_css(main_html, template_catalog, options):
    """This will add the css style info to the html file.

    If the --ferc-render-inline-css option is used, the css file will be copied."""
    
    head = main_html.find('xhtml:head', _XULE_NAMESPACE_MAP)
    if options.ferc_render_css_file:
        # Then the file name is identified by this option.
        if options.ferc_render_inline_css:
            # the contents of the file should be copied
            try:
                with open(options.ferc_render_css_file, 'r') as css_file:
                    css_contents = css_file.read()
            except:
                raise FERCRenderException("Unable to open CSS file '{}'".format(options.ferc_render_css_file))
            style = etree.SubElement(head, 'style')
            style.text = css_contents
        else: # just add a link to the file
            link = etree.SubElement(head, "link")
            link.set('rel', 'stylesheet')
            link.set('type', 'text/css')
            link.set('href', options.ferc_render_css_file)

    else: # the file name is in the catalog
        for css_file_name in template_catalog.get('css',tuple()):
            link = etree.SubElement(head, "link")
            link.set('rel', 'stylesheet')
            link.set('type', 'text/css')
            link.set('href', css_file_name)

class _logCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._captured = collections.defaultdict(list)

    def emit(self, record):
        self._captured[record.messageCode].append(record)
    
    @property
    def captured(self):
        return self._captured

def format_fact(xule_expression_node, model_fact, inline_html, is_html, json_result, nsmap, fact_number):
    '''Format the fact to a string value'''

    new_fact_id = None
    try:
        if xule_expression_node is None:
            format = None
        else:
            # Try getting the format from the xule:format expression first, if not see if there is a format attribute
            format = json_result.get('format', xule_expression_node.get('format'))

        if model_fact.isNumeric:
            ix_node =  etree.Element('{{{}}}nonFraction'.format(_XULE_NAMESPACE_MAP['ix']), nsmap=_XULE_NAMESPACE_MAP)
            ix_node.set('unitRef', model_fact.unitID)
            if model_fact.decimals is not None:
                ix_node.set('decimals', xule_expression_node.get('decimals', model_fact.decimals) if xule_expression_node is not None else model_fact.decimals)
        else:
            ix_node = etree.Element('{{{}}}nonNumeric'.format(_XULE_NAMESPACE_MAP['ix']), nsmap=_XULE_NAMESPACE_MAP)

        ix_node.set('contextRef', model_fact.contextID)
        # Add the name to the inline node. The html_inline is used to resolve the qname
        ix_node.set('name', get_qname_value(inline_html, model_fact.qname))
        # Assign fact id
        if model_fact.id is not None:
            new_fact_id = dedup_id(model_fact.id, fact_number)
            ix_node.set('id', new_fact_id)
            # Save the original fact id. This will be removed later before serializing the document. It is used when copying
            # a section of the inline xbrl (i.e. page header). The ids on the fact will have to be dedupped.
            ix_node.set(_ORIGINAL_FACT_ID_ATTRIBUTE, model_fact.id)

        # Get the formated value
        result_sign = None # this will indicate the sign for numeric results
        if model_fact.isNil:
            display_value = ''
            ix_node.set(r'{http://www.w3.org/2001/XMLSchema-instance}nil', 'true')
        if model_fact.xValue is None:
            display_value = ''
        elif format is None:
            #check if boolean
            if isinstance(model_fact.xValue, bool):
                display_value = str(model_fact.xValue).lower()
            elif model_fact.isNumeric:
                display_value = str(abs(model_fact.xValue))
                result_sign = '-' if model_fact.xValue < 0 else '+' if model_fact.xValue > 0 else '0'
            else:
                display_value = str(model_fact.xValue)               
        else:
            # convert format to clark notation 
            if ':' in format:
                prefix, local_name = format.split(':', 1)
            else:
                prefix = ''
                local_name = format
            format_ns = nsmap.get(prefix)
            if format_ns is None:
                raise FERCRenderException('Format {} is not a valid format'.format(format))

            format_clark = '{{{}}}{}'.format(format_ns, local_name)
            format_function, deprecated = _formats.get(format_clark, (None, False))
            if format_function is None:
                raise FERCRenderException('Format {} is not a valid format'.format(format))
            if deprecated:
                model_fact.modelXbrl.warning('RenderWarning', 'Template uses a deprecated inline xbrl transformation: {}'.format(format_clark))

            display_sign = json_result.get('sign', xule_expression_node.get('sign'))
            scale = json_result.get('scale', xule_expression_node.get('scale'))

            display_value = format_function(model_fact, 
                                            display_sign,
                                            scale)
            if isinstance(display_value, tuple):
                result_sign = display_value[1]
                display_value = display_value[0]

        if format is not None and model_fact.xValue is not None:
            rev_nsmap = {v: k for k, v in inline_html.nsmap.items()}

            if format_ns in rev_nsmap:
                format_prefix_inline = rev_nsmap.get(format_ns)
            else:
                raise FERCRenderException("Do not have the namespace in the generated inline document for namespace '{}'".format(format_ns))
            
            if format_prefix_inline is None:
                format_inline = local_name
            else:
                format_inline = '{}:{}'.format(format_prefix_inline, local_name)
        
            ix_node.set('format', format_inline)

        if xule_expression_node is not None and xule_expression_node.get('scale') is not None:
            ix_node.set('scale', xule_expression_node.get('scale'))

        # this is the node that will be returned.
        return_node = ix_node
        if is_html:
            try:
                # Fact content that is intended as html must first be unescaped becasue XBRL does not allow fact content to contain xml/html element
                div_node = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
                div_node.set('class', 'sub-html')
                content_node = etree.fromstring('<content>{}</content>'.format(display_value))
                # copy the content of the content node to the ix_node
                ix_node.text = content_node.text
                for x in content_node:
                    ix_node.append(x)
                # Check if the content only has html phrasing content. If so, then mark it to preserve white space
                descendant_tags = {x.tag.replace('{http://www.w3.org/1999/xhtml}', '') for x in (ix_node.findall('.//*') or tuple())}
                if ('{http://www.xbrl.org/dtr/type/non-numeric}textBlockItemType' in type_ancestry(model_fact.concept.type) and
                
                
                    (re.search(r'\s\s', display_value) or '\t' in display_value or '\n' in display_value) and
                    len(descendant_tags - _PHRASING_CONTENT_TAGS) == 0):
                    div_node.set('class', 'sub-html preformatted-text')
             
                div_node.append(ix_node)

                return_node = div_node
            except etree.XMLSyntaxError as e:
                # The content was not valid xml/xhtml - put out a warning and 
                model_fact.modelXbrl.warning("Warning", "For fact:\n{}\nAttempting to substitute invalid XHTML into the template. "
                                                        "Inserted as plain text.".format(display_fact_info(model_fact)))
                ix_node.text = display_value
                div_node = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
                div_node.set('class', 'sub-html sub-html-error')
                div_node.append(ix_node)
                return_node = div_node
        else:
            if '{http://www.xbrl.org/dtr/type/non-numeric}textBlockItemType' in type_ancestry(model_fact.concept.type):
                # set as preformatted text around the content
                div_node = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
                div_node.set('class', 'preformatted-text')
                div_node.append(ix_node)
                return_node = div_node
            ix_node.text = display_value

        # handle sign
        value_sign = None
        if model_fact.isNumeric and not model_fact.isNil and model_fact.xValid >= VALID and model_fact.xValue < 0:
            ix_node.set('sign', '-')

        wrapped = False
        if result_sign is not None:
            sign_wrapper = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
            if result_sign == '-':
                sign_wrapper.set('class', 'sign sign-negative')
            elif result_sign == '+':
                sign_wrapper.set('class', 'sign sign-postive')
            else:
                sign_wrapper.set('class', 'sign sign-zero')
            sign_wrapper.append(return_node)
            return_node = sign_wrapper
            wrapped = True

        # handle units for numeric facts
        if model_fact.isNumeric:
            unit_wrapper = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
            unit_wrapper.set('class', 'unit unit-{}'.format(unit_string(model_fact.unit)))
            unit_wrapper.append(return_node)
            return_node = unit_wrapper
            wrapped = True
        
        if wrapped:
            append_classes(return_node, ['xbrl', 'fact'])
        else:
            wrapper = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
            wrapper.set('class', 'xbrl fact')
            wrapper.append(return_node)
            return_node = wrapper
        
        return return_node, new_fact_id

    except FERCRenderException as e:
        model_fact.modelXbrl.error('RenderFormattingError', '{} - {}'.format(' - '.join(e.args), str(model_fact)))
        div_node = etree.Element('div', nsmap=_XULE_NAMESPACE_MAP)
        div_node.set('class', 'format-error')
        div_node.text = str(model_fact.xValue)
        return div_node, new_fact_id

def initialize_fact_number(model_xbrl):
    fact_number = collections.defaultdict(int)
    # Load context and unit ids. This will prevent and edge case where a fact id after deduping is a context
    # or unit id
    for cid in model_xbrl.contexts:
        fact_number[cid] = 1
    for uid in model_xbrl.units:
        fact_number[uid] = 1

    return fact_number

def dedup_id(fact_id, fact_number):
    while True:
        if fact_id in fact_number:
            new_fact_id =  "{}-dup-{}".format(fact_id, fact_number[fact_id])
        else:
            new_fact_id = "{}".format(fact_id)
        fact_number[fact_id] += 1
        if new_fact_id not in fact_number:
            fact_number[new_fact_id] = 1
            break
    return new_fact_id

def type_ancestry(model_type):
    if model_type.typeDerivedFrom is None:
        return [model_type.qname.clarkNotation]
    else:
        return [model_type.qname.clarkNotation] + type_ancestry(model_type.typeDerivedFrom)

def append_classes(node, classes):
    # Added classes to an existing node
    existing_classes = node.get('class','').split()
    if len(existing_classes + classes) > 0:
        node.set('class', ' '.join(existing_classes + classes))

def display_fact_info(model_fact):
    if model_fact is None:
        return ('No Fact')

    display_value = str(model_fact.xValue)
    display = ['fact id: {fact_id} context id: {context_id} unit_id: {unit_id}'.format(fact_id=model_fact.id,
                                                                                       context_id=model_fact.contextID,
                                                                                       unit_id=model_fact.unitID),
                'concept: {}'.format(model_fact.concept.qname.clarkNotation)]
    if model_fact.concept.isNumeric:
        display.append('unit: {}'.format(model_fact.unit.stringValue))
    display.append('value: {}'.format(display_value[:50], '...' if len(display_value) > 50 else ''))      
    display.append('period: {}'.format(model_fact.context.period.stringValue))   
    if len(model_fact.context.qnameDims) > 0:
        dims = '\n'.join(sorted(['\t{d}={m}'.format(d=k.clarkNotation, m=v.memberQname.clarkNotation if v.isExplicit else v.stringValue) for k, v in model_fact.context.qnameDims.items()]))
        display.append('dimensions:\n{}'.format(dims))

    return '\n'.join(display)

def unit_string(model_unit):
    numerator = '--'.join(x.localName for x in model_unit.measures[0])
    denominator = '--'.join(x.localName for x in model_unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '-'.join((numerator, denominator))
        else:
            return numerator

def format_numcommadot(model_fact, sign, scale, *args, **kwargs):
    if not model_fact.isNumeric:
        raise FERCRenderException("Cannot format non numeric fact using numcommadot. Concept: {}, Value: {}".format(model_fact.concept.qname.clarkNotation, model_fact.xValue))

    sign_mult = -1 if sign == '-' else 1
    val = model_fact.xValue * sign_mult

    # Decimals allow -0 (yes I know its weird, but its must be a math thing). If I get a -0 make it a regualr 0
    try:
        if val == 0:
            val = abs(val)
    except TypeError:
        pass

    if scale is not None:
        # Convert scale from string to number
        try:
            scale_num = int(scale)
        except ValueError:
            scale_num = float(scale)
        except:
            raise FERCRenderException("Unable to convert scale from the template to number. Scale value is: '{}'".format(scale))
        
        try:
            scaled_val = val * 10**-scale_num
        except TypeError:
            # the val may be a decimal and the 10**-scale_num a float which causes a type error
            if isinstance(val, decimal.Decimal):
                scaled_val = val * decimal.Decimal(10)**-decimal.Decimal(scale_num)
            else:
                raise FERCRenderException("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale))
        except:
            raise FERCRenderException("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale))

        if (scaled_val % 1) == 0 and not isinstance(scaled_val, int): 
            # need to convert to int
            scaled_val = int(scaled_val)
        else:
            if (scaled_val % 1) == 0: # this is a float or a decimal, but a whole number
                scaled_val = int(scaled_val)
        if isinstance(scaled_val, decimal.Decimal):
            val = scaled_val.normalize()
        else:
            val = scaled_val

    if val < 0:
        val = val * -1
        return '{:,}'.format(val), '-'
    elif val > 0:
        return '{:,}'.format(val), '+' 
    else:
        return '{:,}'.format(val), '0' 

def format_dateslahus(model_fact, *args, **kwargs):
    return model_fact.xValue.strftime('%m/%d/%Y')

def format_durwordsen(model_fact, *args, **kwargs):
    pattern = r'P((?P<year>\d+)Y)?((?P<month>\d+)M)?((?P<week>\d+)W)?((?P<day>\d+)D)?(T((?P<hour>\d+)H)?((?P<minute>\d+)M)?((?P<second>\d+(\.\d+)?)S)?)?'
    duration_res = re.match(pattern, str(model_fact.xValue))
    if duration_res is None:
        raise FERCRenderException("Invalid duration '{}'".format(model_fact.xValue))
    duration_parts = duration_res.groupdict()
    duration_string_parts = []
    for part_name in ('year', 'month', 'week', 'day', 'hour', 'minute', 'second'):
        if duration_parts.get(part_name) is not None:
            plural = 's' if duration_parts[part_name] != '1' else ''
            duration_string_parts.append('{} {}{}'. format(duration_parts[part_name], part_name, plural))
    return ', '.join(duration_string_parts)

def format_durhour(model_fact, *args, **kwargs):
    pattern = r'^PT(\d+)H$'
    duration_res = re.match(pattern, str(model_fact.xValue))
    if duration_res is None:
        raise FERCRenderException("Invalid durhour '{}'. durhour should be in the format of PT#H where #=1 or more digits.".format(model_fact.xValue))
    else:
        return duration_res.group(1)

# Inline XBRL transformations. The value of this dictionary contains the formatter function followed by a deprecated indicator.
_formats = {'{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}numcommadot': (format_numcommadot, True),
            '{http://www.xbrl.org/inlineXBRL/transformation/2010-04-20}dateslashus': (format_dateslahus, True),
            '{http://www.sec.gov/inlineXBRL/transformation/2015-08-31}durwordsen' : (format_durwordsen, False),
            '{http://www.sec.gov/inlineXBRL/transformation/2015-08-31}durhour' : (format_durhour, False),
            '{http://www.xbrl.org/inlineXBRL/transformation/2020-02-12}date-month-day-year': (format_dateslahus, False),
            '{http://www.xbrl.org/inlineXBRL/transformation/2020-02-12}num-dot-decimal': (format_numcommadot, False)
            }

__pluginInfo__ = {
    'name': 'FERC Renderer',
    'version': '0.9',
    'description': "FERC Tools",
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': fercCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}