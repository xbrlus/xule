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
    elif cat_commands[0] == 'cat':
        display_catalog(rule_set)
    elif cat_commands[0] == 'expr-list':
        display_expr(cat_commands, rule_set)

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
            
            expr_names |= traverse(parse_tree)
            
    print("\n".join(sorted(expr_names)))
            
def traverse(parent):
    expr_names = set()
    
    if isinstance(parent, dict):
        for k, v in parent.items():
            if k == 'exprName':
                expr_names.add(v)
            else:
                expr_names |= traverse(v)
    elif isinstance(parent, list):
        for x in parent:
            expr_names |= traverse(x)
    
    return expr_names
    
                     
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
