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

    if cat_commands[0] == 'dict':
        rule_set = xr.XuleRuleSet()
        rule_set.open(options.xule_rule_set, open_packages=False)
    
        for file_info in rule_set.catalog['files']:
            parse_tree = rule_set.getFile(file_info['file'])
            pprint.pprint(parse_tree) 

def xuleCmdXbrlLoaded(cntlr, options, modelXbrl, entryPoint=None):   
    pass

         

__pluginInfo__ = {
    'name': 'DQC XBRL rule processor (xule) catalog manager',
    'version': '1.0',
    'description': 'This plug-in provides a DQC 1.- catalog manager.',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None, 
    'CntlrCmdLine.Options': xuleCmdOptions,
    'CntlrCmdLine.Utility.Run': xuleCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': xuleCmdXbrlLoaded,
    }
