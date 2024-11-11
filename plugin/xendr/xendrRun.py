'''
xendrRun

This file contains code to run a xendr rendering

Reivision number: $Change: $
'''
from arelle.ModelDtsObject import ModelResource
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelDocument import Type
from arelle.ModelValue import QName
from arelle.XmlValidate import VALID
from copy import deepcopy
from lxml import etree
from lxml.builder import E
from .xendrCommon import (XendrException, clean_entities, get_file_or_url, 
                          XULE_NAMESPACE_MAP, XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME, 
                          XENDR_FOOTNOTE_FACT_XULE_FUNCTION_NAME, XENDR_OBJECT_ID_XULE_FUNCTION_NAME,
                          XENDR_FORMAT_FOOTNOTE)
from . import xendrXuleFunctions as xxf
from . import XendrVars as xv
import datetime
import decimal
import collections
import io
import json
import logging
import os
import os.path
import re
import zipfile

_XBRLI_NAMESPACE = 'http://www.xbrl.org/2003/instance'
_XHTM_NAMESPACE = 'http://www.w3.org/1999/xhtml'
_PHRASING_CONTENT_TAGS = {'a', 'audio', 'b', 'bdi', 'bdo', 'br', 'button', 'canvas', 'cite', 'code', 'command',
                          'datalist', 'del', 'dfn', 'em', 'embed', 'i', 'iframe', 'img', 'input', 'ins', 'kbd', 'keygen',
                          'label', 'map', 'mark', 'math', 'meter', 'noscript', 'object', 'output', 'progress', 'q',
                          'ruby', 's', 'samp', 'script', 'select', 'small', 'span', 'strong', 'sub', 'sup', 'svg',
                          'textarea', 'time', 'u', 'var', 'video', 'wbr'}
_NAMESPACE_DECLARATION = 'TEMPORARY_NAMESPACE_DECLARATION'
_ORIGINAL_FACT_ID_ATTRIBUTE = 'original_fact_id'

_OPTIONS = None

def substituteTemplate(rule_meta_data, rule_results, template, modelXbrl, main_html, template_number,
                       used_ids, processed_facts, processed_footnotes, template_set, catalog_item, cntlr, options):
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

    xule_node_locations = {node_number: xule_node for node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=XULE_NAMESPACE_MAP))}
    
    # add the node locations to the nodes as attributes. This makes finding the node easier
    for node_number, xule_node in enumerate(template.xpath('//xule:*', namespaces=XULE_NAMESPACE_MAP)):
        xule_node.set('{{{}}}xule-pos'.format(XULE_NAMESPACE_MAP['xule']), str(node_number))

    line_number_subs = rule_meta_data['line-numbers']
    set_line_number_starts(line_number_subs, rule_results)

    context_ids = set()
    unit_ids = set()

    repeat_attribute_name = '{{{}}}{}'.format(XULE_NAMESPACE_MAP['xule'], 'repeat')
    repeating_nodes = {x.get(repeat_attribute_name): x for x in template.findall('//*[@xule:repeat]', XULE_NAMESPACE_MAP)}

    # Separtate the substitutions that repeat from the non repeating. This will allow the non repeating substitutions to be
    # done first, so if a repeating node has a non repeating substitution, it will happend before the repeating node
    # is copied.
    non_repeating = []
    repeating = []
    footnote_rules = []
    for rule_name, sub_info in rule_meta_data['substitutions'].items():
        if 'footnote-name' in sub_info:
            # This is a footnote rule. Put it to the side. These will be processed after
            footnote_rules.append((rule_name, sub_info))
        elif 'name' in sub_info and sub_info['name'] in repeating_nodes:
            repeating.append((rule_name, sub_info))
        else:
            non_repeating.append((rule_name, sub_info))

    # Sort the repeating so that the deepest template node substitutions are processed first. This will allow repeating within
    # repeating.
    repeating.sort(key=sort_by_ancestors, reverse=True)
    # Also sort the footnote rules in the same way. These will be processed later
    footnote_rules.sort(key=sort_by_ancestors, reverse=True)

    footnotes = collections.defaultdict(list)

    for rule_name, sub_info in non_repeating + repeating:
        substitute_rule(rule_name, sub_info, line_number_subs, rule_results[rule_name], template, 
                                                modelXbrl, main_html, repeating_nodes, xule_node_locations,
                                                context_ids, unit_ids, footnotes, template_number, used_ids, processed_facts, processed_footnotes, cntlr=cntlr)
    # Process the footnotes
    # if the default footnote page option was selected
    if getattr(_OPTIONS, 'xendr_default_footnote_page', False):
        footnote_page = build_footnote_page(template, template_number, footnotes, processed_footnotes, used_ids)
        if footnote_page is not None:
            template_body = template.find('xhtml:body', namespaces=XULE_NAMESPACE_MAP)
            if template_body is None:
                raise XendrException("Cannot find body of the template")  
            template_body.append(etree.Element('{{{}}}hr'.format(_XHTM_NAMESPACE), attrib={"class": "xbrl footnote-separator screen-page-separator"}))
            template_body.append(etree.Element('{{{}}}div'.format(_XHTM_NAMESPACE), attrib={'class': 'print-page-separator footnote-separator'}))
            template_body.append(footnote_page)
    else: # process any footnotes
        process_footnotes(rule_meta_data, template, footnote_rules, footnotes, template_set, catalog_item, cntlr, modelXbrl, options,
                          line_number_subs, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, footnotes,
                          template_number, used_ids, processed_facts, processed_footnotes)
        
    # Remove any left over xule:replace nodes
    for xule_node in template.findall('//xule:replace', XULE_NAMESPACE_MAP):
        parent = xule_node.getparent()
        span = etree.Element('div')
        span.set('class', 'sub-value sub-no-replacement')
        parent.replace(xule_node, span)

    # Remove any left over xule template nodes
    for xule_node in template.findall('//xule:*', XULE_NAMESPACE_MAP):
        parent = xule_node.getparent()
        if xule_node.tag in ('{{{}}}footnoteFacts'.format(XULE_NAMESPACE_MAP['xule']), '{{{}}}footnotes'.format(XULE_NAMESPACE_MAP['xule'])):
            # move the children to after the current xule:footnoteFacts or xule:footnotes element
            for child in xule_node:
                xule_node.addprevious(child) # use addprevious instead of addnext, otherwise the children are added in reverse order
        parent.remove(xule_node)
    
    # Remove any left over xule attributes
    for xule_node in template.xpath('//*[@xule:*]', namespaces=XULE_NAMESPACE_MAP):
        for att_name in xule_node.keys():
            if att_name.startswith('{{{}}}'.format(XULE_NAMESPACE_MAP['xule'])):
                del xule_node.attrib[att_name]

    return template, context_ids, unit_ids

def sort_by_ancestors(key):
    # Sort the repeating so that the deepest template node substitutions are processed first. This will allow repeating within
    # repeating.
    sub_info = key[1]
    if 'name' in sub_info:
        subs = sub_info['subs']
    else:
        subs = sub_info

    if len(subs) == 0:
        return 0
    return max([x.get('node-pos', 0) for x in subs ])
    #return len([x for x in xule_node_locations[subs[0]['replacement-node']].iterancestors()])

def substitute_rule(rule_name, sub_info, line_number_subs, rule_results, template,
                    modelXbrl, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, 
                    footnotes, template_number, used_ids, processed_facts, processed_footnotes,
                    all_result_part=None, refs=None, template_nsmap=None, footnote_style=None, footnote_fact_sub_nodes=None, cntlr=None):
    # Determine if this is a repeating rule.
    new_nodes = []
    attribute_nodes = []

    footnote_number = 0

    if template_nsmap is None:
        template_nsmap = template.getroot().nsmap

    #determing this rule is repeating
    repeating_model_node = None
    if 'name' in sub_info:
        repeat_attribute_name = '{{{}}}{}'.format(XULE_NAMESPACE_MAP['xule'], 'repeat')
        repeating_nodes = {x.get(repeat_attribute_name): x for x in template.findall('//*[@xule:repeat]', XULE_NAMESPACE_MAP)}
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
        footnote_info = None # This will be used to capture the footnote info from a footnote rule
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
        for sub_index, sub in enumerate(subs):
            if 'replacement-node' in sub:
                # check if it is a footnote node. If so, save the footnote information
                if sub.get('footnote-part', '') == 'footnote':
                    # This is the footnote information.
                    # need to get the result from the rule.
                    for x in json_rule_result:
                        if x['part'] == sub_index:
                            footnote_info = json.loads(x['value'])
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

        # if sub_node is not None:
        for sub_index, sub in enumerate(subs):
            # The value for the replacement is either text from running the rule or a fact
            # The sub is a dictionary. If it has a result-text-index key, then the text is taken
            # If it has a rule-focus-index key, then the value is a fact

            # if 'replacement-node' not in sub:
            #     # There is nothing to replace
            #     continue

            possible_footnotes_fact = None

            if isinstance(json_rule_result, list):
                json_result = None
                for x in json_rule_result:
                    if x['part'] == sub_index:
                        json_result = x
                        break
            elif sub_index == 0:
                json_result = json_rule_result
            else:
                raise XendrException('internal error: expected a list of results from the rule but only got one')

            if 'subs' in sub:
                # This is a repeating within a repeating
                substitute_rule(rule_name, sub, line_number_subs, json_result['value'], new_tree,
                    modelXbrl, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, 
                    footnotes, template_number, used_ids, processed_facts, processed_footnotes,
                    all_result_part or json_rule_result, refs or rule_result.refs, template_nsmap=template_nsmap,
                    cntlr=cntlr)
                continue

            classes_from_result = get_classes(json_result)
            attributes_from_result = get_attributes(json_result)
            # Add classes that go on the span that will replace the xule:relace node
            span_classes = classes_from_result.get('self',[])
            # This is the node that will be replaced
            sub_node = sub_nodes.get(sub['replacement-node'])
            if sub_node.tag == '{http://xbrl.us/xendr/2.0/template}footnoteNumber':
                # Create a dummy result. There is no rule value for the footnote Number.
                json_result = {'type': 's', 'part': sub_index, 'value': ''}
            # if the json_result is none, there is nothing to substitute.
            if json_result is None:
                continue
            # Check if the result is a fact
            content = None
            current_footnote_ids = []
            # parent_classes = []
            if is_actual_fact(json_result, modelXbrl):
                # get modelFact
                if json_result.get('fact') is not None:
                    model_fact = get_model_object(json_result['fact'], cntlr)


                # rule_focus_index = get_rule_focus_index(all_result_part or json_rule_result, json_result)
                # if rule_focus_index is not None:
                #     #use_refs = refs or rule_result.refs
                #     use_facts = [modelXbrl.modelObject(x['objectId']) for x in refs or rule_result.refs]
                #     # Check if the number of facts in the rule result matches the number of fact in used_refs (rule focus)
                #     if isinstance(json_rule_result, list):
                #         result_fact_count = count_facts_in_result(all_result_part or json_rule_result)
                #         if result_fact_count != len(use_facts):
                #             list_facts = "\n".join([f"{x.concept.qname.localName}: {x.sValue}" for x in use_facts])
                #             modelXbrl.warning("RenderError", "Mismatch between the number of facts returned in the rule result and the number of "
                #                                     "facts in the rule focus. This is likely due to duplicate facts. The facts on the row "
                #                                     "in question are:\n{}".format(list_facts))
                #             break

                #     #fact_object_index = use_refs[rule_focus_index]['objectId']
                #     #model_fact = modelXbrl.modelObject(fact_object_index)
                #     model_fact = use_facts[rule_focus_index]

                    processed_facts.add(model_fact)
                    expression_node = get_node_by_pos(template, sub['expression-node'])
                    content, new_fact_id = format_fact(expression_node, 
                                                        model_fact, 
                                                        main_html, 
                                                        # This will check if the html flag is in meta data (sub) or calculated in the result
                                                        sub.get('html', json_result.get('html', False)), 
                                                        json_result, 
                                                        template_nsmap, 
                                                        used_ids)

                    # Save the context and unit ids
                    context_ids.add(model_fact.contextID)
                    if model_fact.unitID is not None:
                        unit_ids.add(model_fact.unitID)                               
                    # Check if there are footnotes
                    if getattr(_OPTIONS, 'xendr_default_footnote_page', False):
                        current_footnote_ids = get_footnotes(footnotes, model_fact, sub, new_fact_id)
                    else:
                        possible_footnotes_fact = model_fact

            elif json_result['type'] in ('s', 'f'): # result is a string
                # This will check if the html flag is in meta data (sub) or calculated in the result
                if sub.get('html', json_result.get('html', False)):
                #if sub.get('html', False):
                    content = etree.fromstring('<div class="sub-html">{}</div>'.format(clean_entities(json_result['value'])))
                elif json_result['value'] is not None:
                    content = json_result['value']
            elif json_result['type'] == 'fn': # This is a footnote
                content = get_footnote_content(footnote_info, footnote_fact_sub_nodes, modelXbrl, used_ids, processed_footnotes, processed_facts, main_html)

            if content is None:
                span_classes += ['sub-value', 'sub-no-replacement']
            else:
                span_classes += ['sub-value', 'sub-replacement']

            if sub_node.tag == '{http://xbrl.us/xendr/2.0/template}footnoteNumber':
                # This is a footnote number
                # Get the fact for the footnote. This is in the footnote_info from the <xendr:footnote> node
                if footnote_info is None:
                    footnote_fact = None
                else:
                    footnote_fact = footnote_info['fact'] # This is the model object id of the fact
                content = get_footnote_number(footnote_fact, footnote_number, sub_node.get('footnote-style'), footnote_fact_sub_nodes, template, rule_name)
                footnote_number += 1

            # If the node is going into an <a> or <span> then it needs to be a <span> otherwise it can be a <div>
            xhtml_ancestry = {etree.QName(x.tag).localname.lower() for x in sub_node.xpath('ancestor-or-self::*') if etree.QName(x).namespace == _XHTM_NAMESPACE}

            # Create the replacement node
            if len({'a','span'} & xhtml_ancestry) > 0: #intersect the two sets
                span = etree.Element('span', nsmap=XULE_NAMESPACE_MAP)
            else:
                span = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)

            span.set('class', ' '.join(span_classes))

            # handle footnotes for the fact
            if getattr(_OPTIONS, 'xendr_default_footnote_page', False):
                for footnote_id in current_footnote_ids:
                    footnote_ref = etree.Element('a', attrib={"class": "xbrl footnote-ref", "id":"fr-{}-{}".format(template_number, footnote_id)}, nsmap=XULE_NAMESPACE_MAP)
                    span.append(footnote_ref)
            elif possible_footnotes_fact is not None:
                # Only need to worry about footnotes if this is in a footnote group
                for footnote_group in sub.get('footnote-collectors', tuple()):
                    footnotes[footnote_group].append((possible_footnotes_fact, span))

            if isinstance(content, str):
                span.text = content
            elif etree.iselement(content): 
                span.append(content)
            elif content is not None:
                span.text = str(content)

            if sub_node is not None:
                sub_parent = sub_node.getparent()
                sub_parent.replace(sub_node, span)
                # Add classes to the parent or grand parent
                if len(classes_from_result['parent']) > 0:
                    class_node = sub_parent
                    classes_to_add = classes_from_result['parent']
                elif len(classes_from_result['grand']) > 0:
                    class_node = sub_parent.getparent()
                    classes_to_add = classes_from_result['grand']
                else:
                    class_node = None
                if class_node is not None:
                    class_node.set('class', ' '.join(class_node.get('class','').split() + classes_to_add))

                # # Add classes to the parent
                # if len(classes_from_result['parent']) + len(parent_classes) > 0:
                #     sub_parent.set('class', ' '.join(sub_parent.get('class','').split() + classes_from_result['parent'] + parent_classes))
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
                model_xbrl.warning("RenderError", "Result of <xendr:fact> in template is not boolean. Found '{}'".format(str(dynamic_fact)))
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

# def get_rule_focus_index(json_all_results, current_result):
    
#     if current_result['is-fact'].lower() == 'false':
#         # If the current result isn't really a fact, then there is no rule focus to get
#         return None

#     if isinstance(json_all_results, list):
#         rule_focus_index, _x = traverse_for_facts(json_all_results, current_result)
#     else:
#         # The results is really just a single dictionary of one results. Just check if the fact is there
#         if current_result['is-fact'].lower() == 'true':
#             rule_focus_index = 0

#     return rule_focus_index if rule_focus_index >= 0 else None  

def get_model_object(object_string, cntlr):
    arelle_model_id, object_id = json.loads(object_string)
    arelle_model = xv.get_arelle_model(cntlr, arelle_model_id)
    return arelle_model.modelObject(object_id)

def count_facts_in_result(json_all_results):
    if isinstance(json_all_results, list):
        rule_focus_count, _x = traverse_for_facts(json_all_results, None)
        return rule_focus_count + 1 # base 0 index
    else:
        return None

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
    pos_nodes =  template.xpath('.//*[@xule:xule-pos = {}]'.format(str(pos)), namespaces=XULE_NAMESPACE_MAP)
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

def get_footnote_content(footnote_info, footnote_fact_sub_nodes, model_xbrl, used_ids, processed_footnotes, processed_facts, main_html):
        
        # Get the fact ids from the template that will be linked to this footnote
        fact_ids = [x.get('id') for x in find_inline_facts(footnote_fact_sub_nodes.get(footnote_info['fact'], tuple()))]

        # Build the content 
        footnote_id = None
        footnote_model = model_xbrl.modelObject(footnote_info['content'])
        if footnote_info['type'] == 'fact':
            content, _x = format_fact(None, footnote_model, main_html, False, None, None, used_ids)
            processed_facts.add(footnote_model)
            for fact in find_inline_facts((content,)):
                footnote_id = fact.get('id')
        else: # its a footnote resouce
            content, _x = create_inline_footnote_node(footnote_model)
            footnote_id = dedup_id(footnote_model.get('id', f"fn-{fact_ids[0] if len(fact_ids) > 0 else 'fn'}"), used_ids)

        content.set('id', footnote_id)

        # update processed_footnotes - this is used later to create the relationships
        for fact_id in fact_ids:
            processed_footnotes[footnote_info['content']]['refs'].append((fact_id, footnote_id, footnote_info['arcrole']))    

        return content

def find_inline_facts(fact_sub_nodes):
    inline_facts = []
    # This will find all the inline facts that were created for a specified fact.
    # The fact_sub_nodes is a dictionary by the model fact object id. The value is a list of html nodes that are or contain the inline fact
    for html_node in fact_sub_nodes:
        possible_facts = html_node.xpath('.//descendant-or-self::ix:*[local-name() = "nonNumeric" or local-name() = "nonFraction" or local-name() = "fraction"]', namespaces=XULE_NAMESPACE_MAP) 
        if len(possible_facts) > 0:
            # just get the first one. There should not be more than one.
            inline_facts.append(possible_facts[0])

    return inline_facts

def get_footnotes(footnotes, model_fact, sub, fact_id):
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
                            'fact_id': fact_id}                        
            footnotes[sub['node-pos']].append(footnote_info)
            current_footnotes.append(current_count)
    
    return current_footnotes

def count_footnotes(footnotes):
    i = 0
    for k, v in footnotes.items():
        i += len(v)
    return i

def get_relationshipset(model_xbrl, arcrole, linkrole=None, linkqname=None, arcqname=None, includeProhibits=False):
    # This checks if the relationship set is already built. If not it will build it. The ModelRelationshipSet class
    # stores the relationship set in the model at .relationshipSets.
    relationship_key = (arcrole, linkrole, linkqname, arcqname, includeProhibits)
    return model_xbrl.relationshipSets[relationship_key] if relationship_key in model_xbrl.relationshipSets else ModelRelationshipSet(model_xbrl, *relationship_key)

def build_footnote_page(template, template_number, footnotes, processed_footnotes, used_ids):
    '''Create the footnote page for the schedule. This is the default footnote page'''

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
            footnote_data_cell_classes = ['xbrl', 'footnote-data-cell']
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
            processed_footnotes[footnote['node']]['refs'].append((footnote['fact_id'], footnote_id, None))

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
        for ix_node in node.xpath('.//ix:*', namespaces=XULE_NAMESPACE_MAP):
            if _ORIGINAL_FACT_ID_ATTRIBUTE in ix_node.keys():
                ix_node.set('id', dedup_id(ix_node.get(_ORIGINAL_FACT_ID_ATTRIBUTE), used_ids))
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
        for ix_node in footer.xpath('.//ix:*', namespaces=XULE_NAMESPACE_MAP):
            if _ORIGINAL_FACT_ID_ATTRIBUTE in ix_node.keys():
                ix_node.set('id', dedup_id(ix_node.get(_ORIGINAL_FACT_ID_ATTRIBUTE), used_ids))

        page.append(footer)
        break

    return page

def process_footnotes(rule_meta_data, template, footnote_rules, footnote_facts, template_set, catalog_item, cntlr, modelXbrl, options,
                      line_number_subs, main_html, repeating_nodes, xule_node_locations, context_ids, unit_ids, footnotes,
                      template_number, used_ids, processed_facts, processed_footnotes):
    
    # footnote_rules is a dictionary keyed by rule name and the value is the substitution information for just footnote rules.
    # footnote_facts is a dictionary keyed by the footnote group and the value is a list of model facts
    for rule_name, sub_info in footnote_rules:
        footnote_name_to_groups = rule_meta_data['footnotes'].get(sub_info['footnote-name'])
        groups = footnote_name_to_groups.get('groups')
        footnote_style = footnote_name_to_groups.get('style')
        fact_sub_nodes = collections.defaultdict(list) # this will track where facts are in the template so they can get a footnote number
        facts = []
        for group in groups:
            for fact, sub_node in footnote_facts.get(group, []):
                facts.append(fact)
                fact_sub_nodes[fact.objectId()].append(sub_node)
        fact_ids = [x.objectId() for x in facts]

        fact_ids_xule_arg = [f'{XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME}={",".join(fact_ids)}']
        rule_results = run_xule_rules(cntlr, options, modelXbrl, template_set, (rule_name,), catalog_item['xule-rule-set'], fact_ids_xule_arg)
        substitute_rule(rule_name, sub_info, line_number_subs, rule_results[rule_name], template, 
                        modelXbrl, main_html, repeating_nodes, xule_node_locations,
                        context_ids, unit_ids, footnotes, template_number, used_ids, processed_facts, processed_footnotes,
                        footnote_style=footnote_style, footnote_fact_sub_nodes=fact_sub_nodes,cntlr=cntlr)

def get_footnote_lang(footnote_info, modelXbrl):
    footnote_model = modelXbrl.modelObject(footnote_info['content'])
    return footnote_model.get('{http://www.w3.org/XML/1998/namespace}lang')
                              
def get_footnote_number(fact_id, footnote_number, footnote_style, footnote_fact_nodes, template, rule_name):

    footnote_id = f"fn_{rule_name}_{footnote_number}"
    if (footnote_style or 'letter') not in _footnote_styles:
        raise XendrException(f"Invlaid footnote style '{footnote_style}'")
    styled_footnote_number = _footnote_styles[footnote_style or 'letter'](footnote_number)
    footnote_node = etree.Element('a', nsmap=XULE_NAMESPACE_MAP)
    footnote_node.set('id', footnote_id)
    footnote_node.set('class', 'xbrl footnote-number')
    footnote_node.text = styled_footnote_number

    first_fact = True
    for fact_node in footnote_fact_nodes.get(fact_id, []):
        # This will be the parent span/div that contains the actual fact value that is being footnoted
        footnote_ref_node = etree.Element('a', nsmap=XULE_NAMESPACE_MAP)
        footnote_ref_node.set('href', f'#{footnote_id}')
        footnote_ref_node.set('class', 'xbrl footnote-ref')
        footnote_ref_node.text = styled_footnote_number
        fact_parent = fact_node.getparent()
        fact_node_index = fact_parent.index(fact_node)
        fact_parent.insert(fact_node_index, footnote_ref_node)
        if first_fact:
            # link the footnote number to the first fact
            first_fact = False
            actual_fact_node = find_inline_facts((fact_node,))[0]
            footnote_node.set('href', f'#{actual_fact_node.get("id")}')

        #fact_node.insert(0, footnote_ref_node)


    return footnote_node

def is_valid_xml(potential_text):
    '''Check if the passed string is valid XML'''
    try:
        # Wrap the text in a tag and see if it is valid xml. If it is not valid it etree will raise a syntax exception
        etree.fromstring('<test>{}</test>'.format(potential_text))
        return True
    except etree.XMLSyntaxError:
        return False

def create_inline_footnote_node(footnote_node):
    inline_footnote = etree.Element('{{{}}}footnote'.format(XULE_NAMESPACE_MAP['ix']))

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

def convert_number_to_roman(num):
    # the footnote number is based 0, so add 1
    num += 1
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
        ]
    syb = [
        "m", "cm", "d", "cd",
        "c", "xc", "l", "xl",
        "x", "ix", "v", "iv",
        "i"
        ]
    roman_num = ''
    i = 0
    while  num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

def convert_number_to_number(num):
    # the footnote number is based 0, so add 1
    return str(num + 1)

def convert_number_to_symbol(num):

    #1. asterisk (*), 2. dagger (†), 3. double dagger (‡), 4. paragraph symbol (¶), 5. section mark (§), 6. parallel rules (¶), 7. number sign (#)

    symbols = ('*', '†', '‡', '¶', '§', '¶', '#')
    multiplier = (num // 7) + 1
    index = num % 7

    return symbols[index] * multiplier


_footnote_styles = {'letter': convert_number_to_letter,
                    'roman': convert_number_to_roman,
                    'number': convert_number_to_number,
                    'symbol': convert_number_to_symbol}

def nodes_for_class(root, node_class):
    class_xpath = "descendant-or-self::*[@class and contains(concat(' ', normalize-space(@class), ' '), ' {} ')]".format(node_class)
    for node in root.xpath(class_xpath):
        yield node

def get_fact_by_local_name(modelXbrl, fact_name):
    for fact in modelXbrl.factsInInstance:
        if fact.concept.qname.localName == fact_name:
            return fact
    return None

def setup_inline_html(modelXbrl, title=None):
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
        '<meta content="text/html; charset=UTF-8" http-equiv="Content-Type"/>' \
        '</head>' \
        '<body><div style="display:none"><ix:header><ix:references/><ix:resources/></ix:header></div></body>' \
        '</html>'.format(namespace_string)

    html = etree.fromstring(initial_html_content)
    if title is not None:
        meta_node = html.find('{http://www.w3.org/1999/xhtml}head/{http://www.w3.org/1999/xhtml}meta')
        title_node = etree.Element('{http://www.w3.org/1999/xhtml}title')
        meta_node.addprevious(title_node)
        title_node.text = title

    # Add schema and linbase references
    irefs = html.find('.//ix:references', namespaces=XULE_NAMESPACE_MAP)
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

def add_unused_facts_and_footnotes(main_html, modelXbrl, processed_facts, used_ids, footnotes, options):
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
    show_exceptions = set(x.strip().lower() for x in (getattr(options, 'xendr_show_hidden_except', []) or []))
    hidden_count = 0
    displayed_hidden_count = 0
    # Process the unused facts
    unused_facts = set(modelXbrl.facts) - processed_facts
    for model_fact in unused_facts:
        hidden_count += 1
        if options.xendr_show_hidden and model_fact.concept.qname.localName.lower() not in show_exceptions:
            modelXbrl.info("HiddenFact",'\n{}'.format(display_fact_info(model_fact)))
            displayed_hidden_count += 1

        content, new_fact_id = format_fact(None, model_fact, main_html, False, None, None, used_ids)
        inline_content = content.xpath("descendant-or-self::*[namespace-uri()='{}']".format(XULE_NAMESPACE_MAP['ix']))        
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
            footnotes[rel.toModelObject]['refs'].append((new_fact_id, footnote_id, None))

    if options.xendr_show_hidden:
        modelXbrl.info("HiddenFactCount", "{} hidden facts, {} excluded from being displayed".format(hidden_count, hidden_count - displayed_hidden_count))

    return context_ids, unit_ids

def get_hidden(html):
    hidden = html.find('.//ix:hidden', namespaces=XULE_NAMESPACE_MAP)
    if hidden is None:
        header = html.find('.//ix:header', namespaces=XULE_NAMESPACE_MAP)
        hidden = etree.Element('{{{}}}hidden'.format(XULE_NAMESPACE_MAP['ix']))
        header.insert(0, hidden) # insert as the first element
    return hidden

def add_contexts_to_inline(main_html, modelXbrl, context_ids):
    '''Add context to the inline document'''

    # Contexts are added to the ix:resources element in the inline
    resources = main_html.find('.//ix:resources', namespaces=XULE_NAMESPACE_MAP)
    for context_id in context_ids:
        model_context = modelXbrl.contexts.get(context_id)
        if model_context is not None:
            # The model_context is a modelObject, but it is based on etree.Element so it can be added to
            # the inline tree
            copy_xml_node(model_context, resources) # This will copy the node and add it to the parent (resources)

def add_units_to_inline(main_html, modelXbrl, unit_ids):

    resources = main_html.find('.//ix:resources', namespaces=XULE_NAMESPACE_MAP)
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

        #raise XendrException("Cannot determine QName prefix for namespace '{}'".format(qname_value.namespaceURI))

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

    resources = main_html.find('.//ix:resources', namespaces=XULE_NAMESPACE_MAP)
    for footnote_info in processed_footnotes.values():
        # # This code was used when the footnote was only created once in the inline document
        #rel = etree.Element('{{{}}}relationship'.format(XULE_NAMESPACE_MAP['ix']))
        #rel.set('arcrole', 'http://www.xbrl.org/2003/arcrole/fact-footnote')
        #rel.set('linkRole', 'http://www.xbrl.org/2003/role/link')        
        #rel.set('fromRefs', ' '.join(footnote_info['fact_ids']))
        #rel.set('toRefs', footnote_info['footnote_id'])

        for fact_id, footnote_id, arcrole in footnote_info['refs']:
            rel = etree.Element('{{{}}}relationship'.format(XULE_NAMESPACE_MAP['ix']))
            rel.set('arcrole', arcrole or 'http://www.xbrl.org/2003/arcrole/fact-footnote')
            rel.set('linkRole', 'http://www.xbrl.org/2003/role/link')        
            rel.set('fromRefs', fact_id)
            rel.set('toRefs', footnote_id)

            resources.append(rel)

def render_report(cntlr, options, modelXbrl, *args, **kwargs):
    # Save options to a global
    global _OPTIONS
    _OPTIONS = options

    if options.xendr_debug:
        start_time = datetime.datetime.now()

    used_context_ids = set()
    used_unit_ids = set()

    # Xendr needs to add a xule function to convert modelObject ids to footnotes
    try:
        from .xule.XuleFunctions import add_normal_function as add_normal_function_to_xule
    except (ModuleNotFoundError, ImportError):
        from xule.XuleFunctions import add_normal_function as add_normal_function_to_xule
    add_normal_function_to_xule(XENDR_FOOTNOTE_FACT_XULE_FUNCTION_NAME, xxf.get_footnotes_from_fact_ids, 1)
    add_normal_function_to_xule(XENDR_OBJECT_ID_XULE_FUNCTION_NAME, xxf.get_internal_model_id, 1)
    add_normal_function_to_xule(XENDR_FORMAT_FOOTNOTE, xxf.format_footnote_info, 1)
    try:
        from .xule.XuleProperties import add_property as add_property_to_xule
    except (ModuleNotFoundError, ImportError):
        from xule.XuleProperties import add_property as add_property_to_xule
    add_property_to_xule('xendr-object-id', xxf.property_xendr_model_object, 0, ())
  
    template_number = 0
    used_ids = initialize_used_ids(modelXbrl)
    processed_facts = set() # track which facts have been outputed

    # Footnotes were originally only outputted once as an ix
    processed_footnotes = collections.defaultdict(lambda: {'footnote_id': None, 'fact_ids': list(), 'refs': list()}) # track when a footnote is outputted.

    main_html = setup_inline_html(modelXbrl, options.xendr_title)

    schedule_divs = []
    zipIO = get_file_or_url(options.xendr_template_set, cntlr)
    with zipfile.ZipFile(zipIO, 'r') as ts:
        with ts.open('catalog.json', 'r') as catalog_file:
            template_catalog = json.load(io.TextIOWrapper(catalog_file))

        # Get name of rendered html file
        if options.xendr_inline is None:
            inline_name = '{}.html'.format(os.path.splitext(os.path.split(options.xendr_template_set)[1])[0])
        else:
            inline_name = options.xendr_inline

        # Add css link
        add_css(main_html, template_catalog, options)

        # Iterate through each of the templates in the catalog
        for catalog_item in template_catalog['templates']: # A catalog item is a set of files for a single template

            if options.xendr_only is not None:
                if catalog_item['name'] not in options.xendr_only.split('|'):
                    continue

            if options.xendr_debug:
                cntlr.addToLog("{} Processing template '{}'".format(str(datetime.datetime.now()), catalog_item.get('name', 'UNKNOWN')),"info")
            # Get the html template
            with ts.open(catalog_item['template']) as template_file:
                try:
                    template = etree.parse(template_file)
                except etree.XMLSchemaValidateError:
                    raise XendrException("Template file '{}' is not a valid XHTML file.".format(catalog_item['template']))

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

            rule_results = run_xule_rules(cntlr, options, modelXbrl, ts, rule_meta_data['standard-rules'] + list(rule_meta_data['showifs'].keys()), catalog_item['xule-rule-set'])
            
            # Substitute template
            template_number += 1
            template_result = substituteTemplate(rule_meta_data, 
                                                    rule_results, template, modelXbrl, main_html,
                                                    template_number, used_ids, processed_facts, processed_footnotes, 
                                                    ts, catalog_item, cntlr, options)
            if template_result is not None: # the template_result is none when a xule:showif returns false
                rendered_template, template_context_ids, template_unit_ids = template_result
                used_context_ids |= template_context_ids
                used_unit_ids |= template_unit_ids
                # Save the body as a div
                body = rendered_template.find('xhtml:body', namespaces=XULE_NAMESPACE_MAP)
                if body is None:
                    raise XendrException("Cannot find body of the template: {}".format(os.path.split(catalog_item['template'])[1]))   
                body.tag = 'div'
                schedule_divs.append(body)

    main_body = main_html.find('xhtml:body', namespaces=XULE_NAMESPACE_MAP)

    for div in schedule_divs:
        main_body.append(div)
        if div is not schedule_divs[-1]: # If it is not the last span put a separator in
            #main_body.append(etree.fromstring('<hr xmlns="{}"/>'.format(_XHTM_NAMESPACE)))
            main_body.append(etree.Element('{{{}}}hr'.format(_XHTM_NAMESPACE), attrib={'class': 'screen-page-separator schedule-separator'}))
            main_body.append(etree.Element('{{{}}}div'.format(_XHTM_NAMESPACE), attrib={'class': 'print-page-separator sechedule-separator'}))
    
    if not options.xendr_partial:
        additional_context_ids, additional_unit_ids = add_unused_facts_and_footnotes(main_html, 
                                                                                        modelXbrl, 
                                                                                        processed_facts, 
                                                                                        used_ids, 
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
    dedup_id_full_document(main_html, used_ids)
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

    # If the xendr_inline_css_type is 'element', then inline the css
    if options.xendr_inline_css_type == 'element':
        try:
            import css_inline
        except ModuleNotFoundError:
            raise XendrException("Not able to inline css at the element level. Need to install the css_inline python module.")
        output_string = css_inline.inline(output_string)
        # # This is necessary because the css_inline.inline() unescapes some characters that need to be escaped in order to write the file out. Otherwise I was getting this error:
        # #  UnicodeEncodeError: 'ascii' codec can't encode character '\u2610' in position 12642: ordinal not in range(128)
        # from lxml import html
        # tree = html.fromstring(output_string)
        
        # output_string = etree.tostring(tree).decode(encoding="utf-8")

    responseZipStream = kwargs.get("responseZipStream")
    if responseZipStream is not None:
        _zip = zipfile.ZipFile(responseZipStream, "a", zipfile.ZIP_DEFLATED, True)
        if responseZipStream is not None:
            _zip.writestr(inline_name, output_string)
            _zip.writestr("log.txt", cntlr.logHandler.getJson())
            _zip.close()
            responseZipStream.seek(0)
    else:
        with open(inline_name, 'w', encoding='utf-8') as output_file:
            output_file.write(output_string)

    cntlr.addToLog(_("Rendered template as '{}'".format(inline_name)), 'info')

    if options.xendr_debug:
        end_time = datetime.datetime.now()
        cntlr.addToLog(_("Processing time: {}".format(str(end_time - start_time))), "info")

def run_xule_rules(cntlr, options, modelXbrl, taxonomy_set, rule_names, rule_set_file_name, xule_args=None):
        # Run Xule rules
        # Create a log handler that will capture the messages when the rules are run.
        log_capture_handler = _logCaptureHandler()
        if not options.xendr_show_xule_log:
            cntlr.logger.removeHandler(cntlr.logHandler)
        cntlr.logger.addHandler(log_capture_handler)

        # Call the xule processor to run the rules
        try:
            from .xule import __pluginInfo__ as xule_plugin_info
        except (ModuleNotFoundError, ImportError):
            from xule import __pluginInfo__ as xule_plugin_info
        call_xule_method = xule_plugin_info['Xule.callXuleProcessor']

        run_options = deepcopy(options)
        if xule_args is None:
            xule_args = []
        xule_args += getattr(run_options, 'xule_arg', []) or []
        setattr(run_options, 'xule_arg', xule_args)
        # run only standard rules (the other rules are footnote rules and they will be run later)
        setattr(run_options, "xule_run_only", ",".join(rule_names))
        # Get xule rule set
        with taxonomy_set.open(rule_set_file_name) as rule_set_file:
            call_xule_method(cntlr, modelXbrl, io.BytesIO(rule_set_file.read()), run_options)
        
        # Remove the handler from the logger. This will stop the capture of messages
        cntlr.logger.removeHandler(log_capture_handler)
        if not options.xendr_show_xule_log:
            cntlr.logger.addHandler(cntlr.logHandler)

        return log_capture_handler.captured

def dedup_id_full_document(root, used_ids):
    all_ids = collections.defaultdict(set)

    for elem in root.xpath('.//*[@id]'):
        all_ids[elem.get('id')].add(elem)

    dup_ids = [x for x in all_ids if len(all_ids[x]) > 1]
    # These are the duplicate ids
    for dup_id in dup_ids:
        xbrl_elements = {x for x in all_ids[dup_id] if etree.QName(x).namespace in (XULE_NAMESPACE_MAP['ix'], _XBRLI_NAMESPACE)}
        # XBRL elements should already be dudupped, and it is important that these ids don't change.
        for elem in all_ids[dup_id] - xbrl_elements: 
            elem.set('id', dedup_id(dup_id, used_ids))

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

    If the --xendr-inline-css option is used, the css file will be copied."""
    
    head = main_html.find('xhtml:head', XULE_NAMESPACE_MAP)
    if options.xendr_css_file:
        # Then the file name is identified by this option.
        if options.xendr_inline_css or options.xendr_inline_css_type is not None:
            # the contents of the file should be copied
            try:
                with open(options.xendr_css_file, 'r') as css_file:
                    css_contents = css_file.read()
            except:
                raise XendrException("Unable to open CSS file '{}'".format(options.xendr_css_file))
            style = etree.SubElement(head, 'style')
            style.text = css_contents
        else: # just add a link to the file
            link = etree.SubElement(head, "link")
            link.set('rel', 'stylesheet')
            link.set('type', 'text/css')
            link.set('href', options.xendr_css_file)

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

def format_fact(xule_expression_node, model_fact, inline_html, is_html, json_result, nsmap, used_ids):
    '''Format the fact to a string value'''

    new_fact_id = None
    scale = None
    try:
        if xule_expression_node is None:
            format = None
        else:
            # Try getting the format from the xule:format expression first, if not see if there is a format attribute
            format = json_result.get('format', xule_expression_node.get('format'))

        if model_fact.isNumeric:
            ix_node =  etree.Element('{{{}}}nonFraction'.format(XULE_NAMESPACE_MAP['ix']), nsmap=XULE_NAMESPACE_MAP)
            if model_fact.unitID is not None:
                ix_node.set('unitRef', model_fact.unitID)
            if model_fact.decimals is not None:
                ix_node.set('decimals', xule_expression_node.get('decimals', model_fact.decimals) if xule_expression_node is not None else model_fact.decimals)
        else:
            ix_node = etree.Element('{{{}}}nonNumeric'.format(XULE_NAMESPACE_MAP['ix']), nsmap=XULE_NAMESPACE_MAP)

        if model_fact.contextID is not None:
            ix_node.set('contextRef', model_fact.contextID)
        # Add the name to the inline node. The html_inline is used to resolve the qname
        ix_node.set('name', get_qname_value(inline_html, model_fact.qname))
        # Assign fact id
        if model_fact.id is not None:
            new_fact_id = dedup_id(getattr(model_fact, 'id', 'f'), used_ids) # This ensures there is always a fact id
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
                raise XendrException('Format {} is not a valid format'.format(format))

            format_clark = '{{{}}}{}'.format(format_ns, local_name)
            format_function, deprecated = _formats.get(format_clark, (None, False))
            if format_function is None:
                raise XendrException('Format {} is not a valid format'.format(format))
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
                raise XendrException("Do not have the namespace in the generated inline document for namespace '{}'".format(format_ns))
            
            if format_prefix_inline is None:
                format_inline = local_name
            else:
                format_inline = '{}:{}'.format(format_prefix_inline, local_name)
        
            ix_node.set('format', format_inline)

        # if xule_expression_node is not None and xule_expression_node.get('scale') is not None:
        #     ix_node.set('scale', xule_expression_node.get('scale'))
        if scale is not None:
            ix_node.set('scale', scale)

        # this is the node that will be returned.
        return_node = ix_node
        if is_html:
            try:
                # Fact content that is intended as html must first be unescaped becasue XBRL does not allow fact content to contain xml/html element
                div_node = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
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
                div_node = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
                div_node.set('class', 'sub-html sub-html-error')
                div_node.append(ix_node)
                return_node = div_node
        else:
            if '{http://www.xbrl.org/dtr/type/non-numeric}textBlockItemType' in type_ancestry(model_fact.concept.type):
                # set as preformatted text around the content
                div_node = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
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
            sign_wrapper = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
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
        if model_fact.isNumeric and model_fact.unit is not None:
            unit_wrapper = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
            unit_wrapper.set('class', 'unit unit-{}'.format(unit_string(model_fact.unit)))
            unit_wrapper.append(return_node)
            return_node = unit_wrapper
            wrapped = True
        
        if wrapped:
            append_classes(return_node, ['xbrl', 'fact'])
        else:
            wrapper = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
            wrapper.set('class', 'xbrl fact')
            wrapper.append(return_node)
            return_node = wrapper
        
        return return_node, new_fact_id

    except XendrException as e:
        model_fact.modelXbrl.error('RenderFormattingError', '{} - {}'.format(' - '.join(e.args), str(model_fact)))
        div_node = etree.Element('div', nsmap=XULE_NAMESPACE_MAP)
        div_node.set('class', 'format-error')
        div_node.text = str(model_fact.xValue)
        return div_node, new_fact_id

def initialize_used_ids(model_xbrl):
    used_ids = collections.defaultdict(int)
    # Load context and unit ids. This will prevent and edge case where a fact id after deduping is a context
    # or unit id
    # for cid in model_xbrl.contexts:
    #     used_ids[cid] = 1
    # for uid in model_xbrl.units:
    #     used_ids[uid] = 1

    for model_object in model_xbrl.modelObjects:
        if not isinstance(model_object, ModelFact) and hasattr(model_object, 'id'):
            used_ids[model_object.id]

    return used_ids

def dedup_id(fact_id, used_ids):
    while True:
        if fact_id in used_ids:
            new_fact_id =  "{}-dup-{}".format(fact_id, used_ids[fact_id])
        else:
            new_fact_id = "{}".format(fact_id)
        used_ids[fact_id] += 1
        if new_fact_id not in used_ids:
            used_ids[new_fact_id] = 1
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
        raise XendrException("Cannot format non numeric fact using numcommadot. Concept: {}, Value: {}".format(model_fact.concept.qname.clarkNotation, model_fact.xValue))

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
            raise XendrException("Unable to convert scale from the template to number. Scale value is: '{}'".format(scale))
        
        try:
            scaled_val = val * 10**-scale_num
        except TypeError:
            # the val may be a decimal and the 10**-scale_num a float which causes a type error
            if isinstance(val, decimal.Decimal):
                scaled_val = val * decimal.Decimal(10)**-decimal.Decimal(scale_num)
            else:
                raise XendrException("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale))
        except:
            raise XendrException("Cannot calculate the value for a fact using the scale. Fact value of {} and scale of {}".format(model_fact.xValue, scale))

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
    try:
        return model_fact.xValue.strftime('%m/%d/%Y')
    except AttributeError:
        raise XendrException(
            "Invalid date '{}'. Can not convert value to month/day/year format".format(model_fact.xValue)
        )

def format_durwordsen(model_fact, *args, **kwargs):
    pattern = r'P((?P<year>\d+)Y)?((?P<month>\d+)M)?((?P<week>\d+)W)?((?P<day>\d+)D)?(T((?P<hour>\d+)H)?((?P<minute>\d+)M)?((?P<second>\d+(\.\d+)?)S)?)?'
    duration_res = re.match(pattern, str(model_fact.xValue))
    if duration_res is None:
        raise XendrException("Invalid duration '{}'".format(model_fact.xValue))
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
        raise XendrException("Invalid durhour '{}'. durhour should be in the format of PT#H where #=1 or more digits.".format(model_fact.xValue))
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
