"""__init__.py

Xince and Xodel is the Xbrl instance and model creator. 

This is the package init file.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2023 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: $
DOCSKIP
"""

from .xodel import process_xodel

import optparse

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, optparse.OptionParser):
        parserGroup = optparse.OptionGroup(parser,
                                           "Xule to Instance")
        parser.add_option_group(parserGroup)
    else:
        parserGroup = parser
    
    parserGroup.add_option("--xodel-location",
                            action="store",
                            help=_("Directory where files are create"))

    parserGroup.add_option("--xince-file-type",
                            action="store",
                            choices=('json', 'xml'),
                            default="json",
                            help=_("type of output for the taxonomy. values are 'json', 'xml'"))

    parserGroup.add_option("--xodel-show-xule-log",
                            action="store_true",
                            help=_("Indicates to output the xule log"))
    
def cmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()

    if options.xodel_location is not None and options.xule_rule_set is None:
        parser.error("Xince and Xodel requires a xule rule set (--xule-rule-set)")

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    # Model is create (file loaded) now ready to create an instance

    if options.xodel_location is None:
        # nothing to do
        modelXbrl.info("Xodel plugin is installed but the --xodel-location option was not provided. Not creating a package.", "XodelInfo")
    else:
        process_xodel(cntlr, options, modelXbrl)

__pluginInfo__ = {
    'name': 'Xince and Xodel',
    'version': '1.0',
    'description': "Xince and Xodel- Xule Instance and taxonomy creator",
    'copyright': '(c) Copyright 2022 XBRL US Inc., All rights reserved.',
    'import': ('xule', 'SimpleXBRLModel', 'serializer'),
    # classes of mount points (rquired)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}