'''
xendrCompile

This file contains code to compile xendr templates

Reivision number: $Change: $
'''
from arelle import FileSource
from .xendrCommon import (XendrException, clean_entities, get_file_or_url, XULE_NAMESPACE_MAP, 
                          XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME, XENDR_FOOTNOTE_FACT_XULE_FUNCTION_NAME,
                          XENDR_OBJECT_ID_XULE_FUNCTION_NAME, XENDR_FORMAT_FOOTNOTE)
from lxml import etree

import collections
import json
import io
import os
import tempfile
import zipfile

_RULE_NAME_PREFIX = 'rule-'
_EXTRA_ATTRIBUTES = ('format', 'scale', 'sign', 'decimals')

def compile_templates(cntlr, options):

    template_catalog = {'templates': []}
    template_set_file_name = os.path.split(options.xendr_template_set)[1]

    css_file_names = set()
    with zipfile.ZipFile(options.xendr_template_set, 'w') as template_set_file: 
        template_number = 0   
        for template_full_file_name in getattr(options, 'xendr_template', tuple()):
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
        if options.xendr_save_xule is not None:
            with open(options.xendr_save_xule, 'w') as xule_file:
                xule_file.write(xule_rule_text)

        # Compile Xule rules
        title = template.find('//xhtml:title', XULE_NAMESPACE_MAP)
        if title is None:
            raise XendrException("Template does not have a title")

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
        try:
            from .xule import __pluginInfo__ as xule_plugin_info
        except (ModuleNotFoundError, ImportError):
            from xule import __pluginInfo__ as xule_plugin_info
        
        compile_method = xule_plugin_info['Xule.compile']
        compile_method(xule_rule_file_name, xule_rule_set_name, 'pickle', getattr(options, "xule_max_recurse_depth"), getattr(options, "xule_compile_workers"))

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

def list_templates(cntlr, options):
    zipIO = get_file_or_url(options.xendr_template_set, cntlr)
    with zipfile.ZipFile(zipIO, 'r') as ts_file:
        try:
            catalog_file_info = ts_file.getinfo('catalog.json')
        except KeyError:
            # This zip file does not contain a catalog so it is not a template set
            raise XendrException("The file '{}' is not a template set.".format(options.xendr_template_set))
        with ts_file.open(catalog_file_info, 'r') as catalog_file:
            catalog = json.load(io.TextIOWrapper(catalog_file))
        for template_info in catalog['templates']:
            cntlr.addToLog(template_info['name'],'info')

def extract_templates(cntlr, options):  
    zipIO = get_file_or_url(options.xendr_template_set, cntlr)          
    with zipfile.ZipFile(zipIO, 'r') as ts_file:
        try:
            catalog_file_info = ts_file.getinfo('catalog.json')
        except KeyError:
            # This zip file does not contain a catalog so it is not a template set
            raise XendrException("The file '{}' is not a template set.".format(options.xendr_template_set))
        with ts_file.open(catalog_file_info, 'r') as catalog_file:
            catalog = json.load(io.TextIOWrapper(catalog_file))
        # Check that the destination folder exists
        os.makedirs(options.xendr_extract, exist_ok=True)
        
        for template_info in catalog['templates']:
            # Extract the tempalte
            contents = ts_file.read(template_info['template']) 
            new_name = os.path.join(options.xendr_extract, '{}.html'.format(template_info['name']))
            with open(new_name, 'wb') as new_file:
                new_file.write(contents)
            cntlr.addToLog("Extracted: {}".format(new_name),'info')  

            # Extract the individual template set
            ts_name = os.path.join(options.xendr_extract, '{}.zip'.format(template_info['name']))
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
    template_sets = get_list_of_template_sets(options.xendr_combine, cntlr)
    new_catalog = {'templates': [], 'css': []}
    loaded_template_names = set()
    template_number = 0
    # Create the new combined template set file
    with zipfile.ZipFile(options.xendr_template_set, 'w') as combined_file:
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
            raise XendrException("Template set or folder not found: {}".format(file_or_folder))
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
        raise XendrException("Template file '{}' is not found.".format(template_file_name))

    except etree.XMLSchemaValidateError:
        raise XendrException("Template file '{}' is not a valid XHTML file.".format(template_file_name))

    # build the namespace declaration for xule
    xule_namespaces = build_xule_namespaces(template_tree, options)
    # build constants
    xule_constants = build_constants(options, template_tree)
    # Create list of Xule nodes in the template
    xule_node_locations = {template_tree.getelementpath(xule_node): node_number for  node_number, xule_node in enumerate(template_tree.xpath('//xule:*', namespaces=XULE_NAMESPACE_MAP))}
    # create the rules for xule and retrieve the update template with the substitutions identified.
    xule_rules, rule_meta_data = build_xule_rules(template_tree, template_file_name, xule_node_locations)

    # Get the css file name from the template
    css_file_names = tuple(x for x in template_tree.xpath('/xhtml:html/xhtml:head/xhtml:link[@rel="stylesheet" and @type="text/css"]/@href', namespaces=XULE_NAMESPACE_MAP))

    return '{}\n{}\n{}'.format(xule_namespaces, xule_constants, xule_rules), rule_meta_data, template_tree, template_string, css_file_names

def build_xule_namespaces(template_tree, options):
    '''build the namespace declarations for xule

    Convert the namespaces on the template to namespace declarations for xule. This will only use the 
    namespaces that are declared on the root element of the template.

    Namespaces provided on the command line using --xendr-namespace take precidence
    '''
    namespace_dict = template_tree.getroot().nsmap.copy()
    # Overwrite with namespaces from the command line
    namespace_dict.update(options.namespace_map)

    namespaces = ['namespace {}={}'.format(k, v) if k is not None else 'namespace {}'.format(v) for k, v in namespace_dict.items()]

    return '\n'.join(namespaces)

def build_constants(options, template_tree):
    '''Create constants used by the expressions. '''

    constants = []
    # Constants are found in a specified file (xendr-constants.xule is the default) or in the <xule:global> element
    # The default constant file is eliminated. Now if the xendr-constants option is not used there is no default
    constant_file_name = getattr(options, 'xendr_global')
    constants = []
    if constant_file_name is not None:
        try:
            with open(constant_file_name, 'r') as constant_file:
                constants.append(constant_file.read())
        except FileNotFoundError:
            raise XendrException("Constant file {} is not found.".format(constant_file_name))

    # Find all the <xule:global> nodes
    for node in template_tree.findall('//xule:global', XULE_NAMESPACE_MAP):
        constants.append(node.text)

    # Add constant for fact ids for footnotes. This is used by the footnote rules.
    constants.append(f'constant ${XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME} = none')
    
    return '\n'.join(constants)

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

    # divide the rules into regular rules and footnote rules
    standard_rules = []
    footnote_rules = []
    for rule_name, rule_info in substitutions.items():
        if 'footnote-name' in rule_info:
            footnote_rules.append(rule_name)
        else:
            standard_rules.append(rule_name)

    rule_meta_data = {'substitutions': substitutions,
                      'line-numbers': line_number_subs,
                      'showifs': showifs,
                      'footnotes': get_footnote_info(template_tree), # find footnote productions - these are the footnote elements where a rule will write a footnote
                      'standard-rules': standard_rules,
                      'footnote-rules': footnote_rules} 

    return '\n\n'.join(showif_rules + xule_rules), rule_meta_data

def build_template_show_if(xule_rules, next_rule_number, template_tree, template_file_name, node_pos):
    '''Conditional Template Rules

    This funciton finds the xule:showif rule, if there is one, and creates the xule rule for it.
    '''
    meta_data = collections.defaultdict(list)
    xule_rules = list()
    # The <xule:showif> must be a node under the html body node.
    for showif_node in template_tree.findall('xhtml:body/xule:showif', XULE_NAMESPACE_MAP):
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
    footnotes = dict() # keyed by footnote name, value dictionary of groups, style
    # Go through each of the xule expressions in the template
    for xule_expression in template_tree.findall('//xule:expression', XULE_NAMESPACE_MAP) + template_tree.findall('//xule:footnoteNumber', XULE_NAMESPACE_MAP) + template_tree.findall('//xule:footnote', XULE_NAMESPACE_MAP): 
        named_rule = xule_expression.get("name")
        if xule_expression.tag in ('{http://xbrl.us/xendr/2.0/template}footnoteNumber', '{http://xbrl.us/xendr/2.0/template}footnote') and named_rule is None:
            # This is a footnoteNumber for a footnote, but it doesn't have a name. It doesn't do anything, so just skip it otherwise it will try to build a rule from it.
            continue
        if named_rule is None:
            # This is a single rule
            rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
            next_rule_number += 1

            replacement_node = xule_expression.getparent()
            if replacement_node.tag != '{{{}}}{}'.format(XULE_NAMESPACE_MAP['xule'], 'replace'):
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
                rule_text = 'output {rule_name}\n{comment}\n{result_text}'\
                    ''.format(rule_name=rule_name,
                              comment=comment_text,
                              result_text='({}).to-json'.format(format_rule_result_text_part(xule_expression.text.strip(),
                                                                                             None,
                                                                                             None,
                                                                                             'f',
                                                                                             extra_expressions))
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
            # Check if we are in a footnote group that is collecting facts.
            footnote_groups = get_footnote_groups(xule_expression)
            if len(footnote_groups) > 0:
                sub_content['footnote-collectors'] = footnote_groups
            substitutions[rule_name].append(sub_content)
        else: # This is a named rule
            # Saved the named rule part for later
            part = xule_expression.get('part', None)
            if named_rule not in named_rules:
                named_rules[named_rule] = []

            if xule_expression.tag == '{http://xbrl.us/xendr/2.0/template}footnoteNumber':
                named_rules[named_rule].append(('number', None, xule_expression))
            elif xule_expression.tag == '{http://xbrl.us/xendr/2.0/template}footnote':
                named_rules[named_rule].append(('footnote', None, xule_expression))
            elif part is None:
                named_rules[named_rule].append(('start', part, xule_expression))
            else:
                named_rules[named_rule].append(('part', part, xule_expression))

    return substitutions, xule_rules, next_rule_number, named_rules

def format_rule_result_text_part(expression_text, part, value_number, type, extra_expressions, inside=False):

    output_dictionary = collections.OrderedDict()
    output_dictionary['type'] = "'{}'".format(type)
    
    if part is None:
        value_variable_name = '$rv-0'
    else:
        value_variable_name = f'$rv-{part}'
        output_dictionary['part'] = part
    
    output_dictionary['value'] = f'first-value-or-none({value_variable_name}).string'

    # if part is None:
    #     output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-0).string else (none)#rv-0).string'.format(exp=expression_text)
    # else:
    #     output_dictionary['part'] = part
    #     output_dictionary['value'] = '(if exists({exp}) (({exp})#rv-{part}).string else (none)#rv-{part}).string'.format(exp=expression_text, part=value_number)

    if type == 'f':
        # if inside:
        #     # Inside expressions have an extra component to capture the fact. This is used to build the rule focus.
            output_dictionary['fact'] = f"({expression_text}).xendr-object-id"       
    # Extra expressions (i.e. class, format, scale)
    for extra_name, extra_expression in extra_expressions.items():
        if extra_name == 'fact':
            # rename this so it doesn't conflict with the name 'fact' for inside expression. See code a few lines up.
            extra_name = 'dynamic-fact'
        if isinstance(extra_expression, list):
            output_extra_expressions = "list({})".format(','.join(extra_expression)) if len(extra_expression) > 0 else None
        else:
            output_extra_expressions = extra_expression
        if output_extra_expressions is not None:
            output_dictionary[extra_name] = output_extra_expressions
    
    output_items = ("list('{key}', {val})".format(key=k, val=v) for k, v in output_dictionary.items())
    # output_string = "dict({})".format(', '.join(output_items))
    new_line = '\n'
    output_string = f"{value_variable_name} = {expression_text};{new_line}dict({', '.join(output_items)})"

    return output_string

def part_sort(part):
    if part[0] == 'start':
        return (1, '')
    elif part[0] == 'part':
        return (2, part[1])
    elif part[0] == 'number': # footnote number
        return (3, '')
    elif part[0] == 'footnote':
        # its important that the footnote is at the end of the subs because there isn't a replacement for the footnote
        # when doing the substitutions. The footnote is used to identify the footnote resource and the fact that has
        # the footnote.
        return (4,'')

def build_named_rule_info(named_rule, part_list, next_rule_number, template_tree, template_file_name, 
                          xule_node_locations, node_pos, next_text_number=0, inside=False):
    '''Build the body of the rule

    Builds the rule text and sets up the subsitution information.
    '''
    # Sort the part list by the part number
    part_list.sort(key=part_sort)
    result_parts = []
    comments = []
    preliminary_rule_text = ''
    substitutions = []
    sequence_number = 0

    rule_name = _RULE_NAME_PREFIX + str(next_rule_number)
    next_rule_number += 1
    for part_type, part, expression in part_list:
        replacement_node = expression.getparent()
        if replacement_node.tag != '{{{}}}{}'.format(XULE_NAMESPACE_MAP['xule'], 'replace'):
            replacement_node = expression
            extra_expressions = dict()
        else: # this is a xule:replace
            extra_expressions = format_extra_expressions(replacement_node)

        extra_attributes = get_extra_attributes(expression)
        footnote_groups = get_footnote_groups(expression)

        comments.append('    // {} - {}'.format(template_file_name, expression.sourceline))
        if part_type == 'start':
            preliminary_rule_text = expression.text.strip()
        elif part_type == 'part':
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

                sub_content = {'name': named_rule, 
                                'part': part, 
                                'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)],
                                'expression-node': xule_node_locations[template_tree.getelementpath(expression)],
                                'template-line-number': expression.sourceline,
                                'node-pos': node_pos[replacement_node]}
                if expression.get('html', 'false').lower() == 'true':
                    sub_content['html'] = True
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
            
            # Check if we should be capturing footnotes        
            if len(footnote_groups) > 0:
                sub_content['footnote-collectors'] = footnote_groups                                  
            # Check if we are in a footnote production (writing a footnote)
            footnote_name = get_footnote_productions(expression)
            if footnote_name is not None:
                sub_content['footnote-name'] = footnote_name

            substitutions.append(sub_content)
            next_text_number += 1
            sequence_number += 1

        elif part_type == 'footnote': # part_type is footnote number
            result_parts.append('{result_text}'.format(result_text=format_rule_result_text_part(f"{XENDR_FORMAT_FOOTNOTE}({expression.text.strip()})",
                                                                                            sequence_number,
                                                                                            next_text_number,
                                                                                            'fn',
                                                                                            extra_expressions,
                                                                                            inside)))
            sub_content = {'name': named_rule, 
                            'part': part, 
                            'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                            'template-line-number': expression.sourceline,
                            'extras': extra_attributes,
                            'node-pos': node_pos[replacement_node],
                            'footnote-name': named_rule,
                            'footnote-part': 'footnote'}
            substitutions.append(sub_content)
            next_text_number += 1
            sequence_number += 1
        elif part_type == 'number':
            sub_content = {'name': named_rule, 
                            'part': part, 
                            'replacement-node': xule_node_locations[template_tree.getelementpath(replacement_node)], 
                            'template-line-number': expression.sourceline,
                            'extras': extra_attributes,
                            'node-pos': node_pos[replacement_node],
                            'footnote-name': named_rule,
                            'footnote-part': 'number'}
            substitutions.append(sub_content)
            next_text_number += 1
            sequence_number += 1

    rule_info = {'rule_name': rule_name,
                 'comments': comments,
                 'preliminary_rule_text': preliminary_rule_text,
                 'result_parts': result_parts}
    
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
        # If there is a child sub that is for a footnote, then this is a footnote rule.
        for child_sub in substitutions[rule_info['rule_name']]['subs']:
            if 'footnote-name' in child_sub: # this is a footnote rule
                substitutions[rule_info['rule_name']]['footnote-name'] = child_sub['footnote-name']
            break
        rule_info['result_parts'] += child_parts
        #build rule text
        rule_text = 'output {}\n'.format(rule_info['rule_name'])
        
        rule_text += '\n'.join(rule_info['comments']) + '\n'
        if 'footnote-name' in substitutions[rule_info['rule_name']]: # This is a footnote rule - add the $footnoteFacts variable
            rule_text += '\n$footnoteFacts = {}(${})'.format(XENDR_FOOTNOTE_FACT_XULE_FUNCTION_NAME, XENDR_FOOTNOTE_FACT_ID_CONSTANT_NAME)
        rule_text += '\n{}'.format(rule_info['preliminary_rule_text'])
        result_text = ',\n'.join(["{}".format(expression) for expression in rule_info['result_parts']])
        
        rule_text += '\nlist({}).to-json'.format(result_text)
        # rule_focus = rule_info['rule_focus']
        composite_rule_focus = []
        # if len(rule_focus) > 0:
        #     composite_rule_focus.append('list({})'.format(', '.join(rule_focus)))
        # if len(child_focus) > 0:
        #     composite_rule_focus.append(' + '.join(child_focus))
        # if len(composite_rule_focus) > 0:
        #     rule_text += '\nrule-focus {}'.format(' + '.join(composite_rule_focus))

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
                raise XendrException("The repeating name '{}' has no xule:expression".format(child_name))

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

            inside_value_text = 'list({prelim_text}\nlist({value_text}))'.format(
                                        prelim_text=child_rule_info['preliminary_rule_text'],
                                        value_text=inside_list_text)

#             inside_variable_text = '${inside_name}-val = list({prelim_text}\nlist({value_text}));'.format(
#                                         inside_name=child_name,
#                                         prelim_text=child_rule_info['preliminary_rule_text'],
#                                         value_text=inside_list_text)
#             inside_value_text = f'''
# {inside_variable_text}
# ${child_name}-val
# '''
            
#             inside_value_text = \
# '''
# // Get results
# {variable_text} 


# // Find the rule focus facts
# ${inside_name}-rf = list(
#     for $res in ${inside_name}-val
#         for $part in $res
#             if $part['type'] == 'f'
#                 $part['fact']
#             else    
#                 skip
# );

# // Get rid of the 'fact' component of the part
# list(
#     for $res in ${inside_name}-val
#         list(
#             for $part in $res
#                 dict(
#                     for $key in $part.keys
#                         if $key != 'fact'
#                             list($key, $part[$key])
#                         else
#                             skip
#                     )
#         )
# )
# '''.format(inside_name=child_name, variable_text=inside_variable_text)

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

    for node in template_tree.xpath('.//*[@xule:repeat]', namespaces=XULE_NAMESPACE_MAP):
        parent = node.get('{{{}}}repeatWithin'.format(XULE_NAMESPACE_MAP['xule']))
        child = node.get('{{{}}}repeat'.format(XULE_NAMESPACE_MAP['xule']))
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
            raise XendrException("Found in  a a loop in hierarchy of named rules in the template. {}".format(' --> '.join(ancestry + (child,))))
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
                        raise XendrException("The <xule:attribute> element does not have a name attribute. Found on line {} of the template".format(extra_node.sourceline))  
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

def get_footnote_groups(expression_node):
    # find the ancestor footnoteFact elements and make a list of all the group identifiers
    return list({x.get('group') for x in expression_node.iterancestors('{{{}}}footnoteFacts'.format(XULE_NAMESPACE_MAP['xule'])) if x.get('group') is not None})

def get_footnote_productions(expression_node):
    # find the ancestor footnote elements and make a list of all the group identifiers
    for footnote_node in expression_node.iterancestors('{{{}}}footnotes'.format(XULE_NAMESPACE_MAP['xule'])):
        if 'name' not in footnote_node.keys():
            raise XendrException("{{{}}}footnotes must have a 'name' attribute".foramt(XULE_NAMESPACE_MAP['xule']))
        if footnote_node.get('name') == expression_node.get('name'):
            return footnote_node.get('name')
        else:
            return None
  
def build_line_number_rules(xule_rules, next_rule_number, template_tree, xule_node_locations):
    line_number_subs = collections.defaultdict(list)
    for line_number_node in template_tree.findall('//xule:lineNumber', XULE_NAMESPACE_MAP):
        name = line_number_node.get('name')
        if name is not None:
            # Check if there is a staring number
            start_expression_node = line_number_node.find('xule:startNumber', XULE_NAMESPACE_MAP)
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

def get_footnote_info(template_tree):
    footnote_info = dict() # keyed by name.
    for footnote_node in template_tree.findall('//{{{}}}footnotes'.format(XULE_NAMESPACE_MAP['xule'])):
        if next(footnote_node.iterancestors('{{{}}}footnotes'.format(XULE_NAMESPACE_MAP['xule'])), False) != False:
            # The <footnotes> is nested. This is not allowed
            raise XendrException("Found a <footnotes> inside another <footnotes>")
        if next(footnote_node.iterancestors('{{{}}}footnoteFacts'.format(XULE_NAMESPACE_MAP['xule'])), False) != False:
            # the <footnotes> is inside a <footnoteFacts>. This is not allowed
            raise XendrException("Found a <footnotes> inside a <footnoteFacts>")
        footnote_name = footnote_node.get('name')
        if footnote_name is None:
            raise XendrException("Found a <footnotes> without a name attribute")
        footnote_groups = footnote_node.get('groups', '').split() # this will split on whitespace
        if len(footnote_groups) == 0:
            raise XendrException("Found a <footnotes> wihtout a group")
        #footnote_style = footnote_node.get('list-style') # its okay if there isn't a style. It will be defaulted to lowercase letters
        footnote_info[footnote_name] = {'groups': footnote_groups}
    
    return footnote_info