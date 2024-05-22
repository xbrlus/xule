"""__init__.py

Xule is a rule processor for XBRL (X)brl r(ULE). 

This is the package init file xule catalog.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2018 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 22342 $
DOCSKIP
"""

from arelle.plugin.xule import XuleRuleSet as xr
from optparse import OptionParser, SUPPRESS_HELP
import optparse
import pprint


def xuleCmdOptions(parser):
    # extend command line options to compile rules
    parserGroup = optparse.OptionGroup(parser,
                                       "Xule Business rule - catalog manager")
    parser.add_option_group(parserGroup)
    
    parserGroup.add_option("--xule-cat",
                           action="store",
                           dest="xule_cat",
                           help=_("Display rule set catatlog information."))    

def xuleCmdUtilityRun(cntlr, options, **kwargs):     
    #check option combinations
    parser = OptionParser()

    if getattr(options, "xule_cat", None) is not None and getattr(options, "xule_rule_set", None) is None:
        parser.error(_("--xule-cat requires --xule-rule-set"))
    
    cat_commands = options.xule_cat.split()
    rule_set = xr.XuleRuleSet()
    rule_set.open(options.xule_rule_set, open_packages=False)
            
    if cat_commands[0] == 'dict':
        display_as_dictionary(cat_commands, rule_set)
    elif cat_commands[0] == 'text':
        display_as_text(cat_commands, rule_set)
    elif cat_commands[0] == 'cat':
        display_catalog(rule_set)
    elif cat_commands[0] == 'expr-list':
        display_expr(cat_commands, rule_set)
    else:
        print("'{}' is not a valid --xule-cat command".format(cat_commands[0]))

def display_as_dictionary(cat_commands, rule_set):
    files_in = cat_commands[1:]
    file_numbers = list()
    all_files = {x['name']: x['file'] for x in rule_set.catalog['files']}
    for file_name in files_in:
        try:
            # see if the file name is an integer
            if int(file_name) in all_files.values():
                file_numbers.append(int(file_name))
            else:
                print("File number {} is not in the catalog.".format(file_name))
        except ValueError:
            # assuming the file_name is the file name
            for file_info in rule_set.catalog['files']:
                if file_info['name'] == file_name:
                    file_numbers.append(file_info['file'])
                    break
            else:
                # file name is not found
                print("File {} is not in the rule set".format(file_name))
    
    for file_info in rule_set.catalog['files']:
        if (len(files_in) == 0 or file_info['file'] in file_numbers) and len(files_in) == len(file_numbers):
            parse_tree = rule_set.getFile(file_info['file'])
            print("File: {} ({})".format(file_info['name'], file_info['file']))
            pprint.pprint(parse_tree)

def display_as_text(cat_commands, rule_set):
    files_in = cat_commands[1:]
    file_numbers = list()
    all_files = {x['name']: x['file'] for x in rule_set.catalog['files']}
    for file_name in files_in:
        try:
            # see if the file name is an integer
            if int(file_name) in all_files.values():
                file_numbers.append(int(file_name))
            else:
                print("File number {} is not in the catalog.".format(file_name))
        except ValueError:
            # assuming the file_name is the file name
            for file_info in rule_set.catalog['files']:
                if file_info['name'] == file_name:
                    file_numbers.append(file_info['file'])
                    break
            else:
                # file name is not found
                print("File {} is not in the rule set".format(file_name))

    for file_info in rule_set.catalog['files']:
        if (len(files_in) == 0 or file_info['file'] in file_numbers) and len(files_in) == len(file_numbers):
            parse_tree = rule_set.getFile(file_info['file'])
            print("File: {} ({})".format(file_info['name'], file_info['file']))
            lines, _args, _kwargs = traverse(parse_tree, list(), collect_text)

            largest_node_id = max(lines, key=lambda x: x[0] if x[0] else 0)[0]
            node_id_size = len(str(largest_node_id))

            print('\n'.join([collect_text_format(x, node_id_size) for x in lines]))

def collect_text_format(line, node_id_size):
    node_id = str(line[0]).rjust(node_id_size, ' ') if line[0] is not None else ''.rjust(node_id_size-1, ' ')
    node_name = (line[3] + ': ') if line[3] is not None else ''
    expr_name = line[2] or ''
    iterable = ('i' if line[4] else ' ') if len(line) > 4 else ' '
    table_id = ' (tid: {})'.format(str(line[5])) if len(line) > 5 and line[5] is not None else ''
    text = line[6] if len(line) > 6 else ''


    return '{node_id}{iterable}{tab}{node_name}{expr_name}{table_id}{text}'.format(node_id=node_id,
                                                               tab=line[1]*'  ', # 2 spaces
                                                               node_name=node_name,
                                                               expr_name=expr_name,
                                                               text=text,
                                                               iterable=iterable,
                                                               table_id=table_id)

def collect_text(lines, node, node_name, depth, *args, **kwargs):
    stop_list = set()
    new_line = []
    # line: 0-node_id, 1-depth, 2-expr_name, 3-node_name, 4-iterable, 5-table_id, 6-text,
    if isinstance(node, dict) and 'exprName' in node:
        line = [node['node_id'],
                depth,
                node.get('exprName'),
                node_name,
                node.get('is_iterable', None), # is_iterable is always true if it is present
                node.get('table_id', None)]
        new_line.append(line)

    elif isinstance(node, list) and node_name and len(node) > 0:
        line = [None, depth, None, node_name]
        new_line.append(line)

    elif node_name is not None:
        line = [None, depth, None, node_name, None, None, node]
        new_line.append(line)
    else:
        pass

    return lines + new_line, stop_list, args, kwargs

def display_catalog(rule_set):
    pprint.pprint(rule_set.catalog)
    
def display_expr(cat_commands, rule_set):
    files_in = cat_commands[1:]
    file_numbers = list()
    all_files = {x['name']: x['file'] for x in rule_set.catalog['files']}
    for file_name in files_in:
        try:
            # see if the file name is an integer
            if int(file_name) in all_files.values():
                file_numbers.append(int(file_name))
            else:
                print("File number {} is not in the catalog.".format(file_name))
        except ValueError:
            # assuming the file_name is the file name
            for file_info in rule_set.catalog['files']:
                if file_info['name'] == file_name:
                    file_numbers.append(file_info['file'])
                    break
            else:
                # file name is not found
                print("File {} is not in the rule set".format(file_name))

    expr_names = set()
    for file_info in rule_set.catalog['files']:
        if (len(files_in) == 0 or file_info['file'] in file_numbers) and len(files_in) == len(file_numbers):
            parse_tree = rule_set.getFile(file_info['file'])

            file_expr_names, _args, _kwargs = traverse(parse_tree, set(), collect_expr_names, 0)
            expr_names |= file_expr_names

    print("\n".join(sorted(expr_names)))

def collect_expr_names(collection, node, node_name, *args, **kwargs):
    additions = set()
    if isinstance(node, dict) and 'exprName' in node:
        additions.add(node['exprName'])

    return (collection | additions) if len(additions) > 0 else collection, None, args, kwargs

def traverse(top_node, collection, func, *args, **kwargs):
    return traverse_worker(top_node, None, collection, func, 0, *args, **kwargs)

def traverse_worker(parent, parent_name, collection, func, depth, *args, **kwargs):
    collection, stop_list, args, kwargs = func(collection, parent, parent_name, depth, *args, **kwargs)

    if isinstance(parent, dict):
        def node_order_sort(kv):
            return _NODE_ORDER.get((parent.get('exprName'), kv[0]), float('inf'))

        e = parent.get('exprName')
        sorted_kv = sorted(parent.items(), key=node_order_sort)

        for k, v in sorted_kv:
            if k not in _NODE_STOPS and not {k, 'all'} & set(stop_list or tuple()):
                collection, args, kwargs = traverse_worker(v, k, collection, func, depth + 1,  *args, **kwargs)
    elif isinstance(parent, list):
        for x in parent:
            collection, args, kwargs = traverse_worker(x, None, collection, func, depth + 1, *args, **kwargs)

    return collection, args, kwargs


def node_orders(node_order_base):
    '''Organize the node orders in a way that is more useful for processing'''

    node_order = dict()
    for expr_name, child_list in node_order_base.items():
        for order, child_name in enumerate(child_list):
            node_order[(expr_name, child_name)] = order

    return node_order

_NODE_STOPS = ('var_refs', 'dependent_iterables', 'number', 'is_dependent', 'exprName', 'node_id', 'has_alignment')
_NODE_ORDER_BASE = {'aspectFilter': ('coverType', 'aspectName', 'aspectOperator','aspectExpr', 'wildcard'),
                    'blockExpr': ('varDeclarations',),
                    'factset': ('aspectFilters', 'whereExpr'),
                    'outputRule': ('ruleName', 'severity', 'body'),
                    'qname': ('prefix', 'localName'),
                    'varDeclaration': ('varName', 'body'),
                    'varRef':  ('varName', 'varDeclaration'),

                }
_NODE_ORDER = node_orders(_NODE_ORDER_BASE)


def xuleCmdXbrlLoaded(cntlr, options, modelXbrl, entryPoint=None):   
    pass

__pluginInfo__ = {
    'name': 'DQC XBRL rule processor (xule) catalog manager',
    'version': '1.0',
    'description': 'This plug-in provides a DQC 1.- catalog manager.',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017',
    'import': 'xule',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None, 
    'CntlrCmdLine.Options': xuleCmdOptions,
    'CntlrCmdLine.Utility.Run': xuleCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': xuleCmdXbrlLoaded,
    }
