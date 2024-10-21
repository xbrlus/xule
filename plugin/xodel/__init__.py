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
from arelle import PluginManager
from .xodel import process_xodel

import optparse

_PLUGINS = {}

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

    parserGroup.add_option("--xodel-file-type",
                            action="store",
                            choices=('xml',),
                            default="xml",
                            help=_("Type of output for the taxonomy. Currently only 'xml' is suppoprted"))

    parserGroup.add_option("--xince-file-type",
                            action="store",
                            choices=('json', 'xml'),
                            default="json",
                            help=_("Type of output for the instance files. values are 'json', 'xml'"))

    parserGroup.add_option("--xodel-show-xule-log",
                            action="store_true",
                            help=_("Indicates to output the xule log"))
    
    parserGroup.add_option("--xodel-compile",
                           action="store",
                           help=_("Causes Xodel to compile the supplied rule set. This is the same as --xule-compile. However, --xodel-compile ensures that the rule set is compiled before xodel is run. This is necessary when compiling and runing Xodel in the same command."))
    
def cmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()

    if options.xodel_location is not None and options.xule_rule_set is None:
        parser.error("Xince and Xodel requires a xule rule set (--xule-rule-set)")

    # Cannot have both --xule-compile and --xodel-compile
    if options.xule_compile is not None and options.xodel_compile is not None:
        parser.error("--xule-compile and --xodel-compile cannot be used togher. Only use --xodel-compile")

    # Cannot use --xule-compile is there is no -f entry file
    if options.xule_compile is not None and options.entrypointFile is None:
        parser.error("--xule-compile cannot be used if there is not -f entry point file. Use --xodel-compile instead")

    if options.entrypointFile is None:
        # init the serializer - this may not have been done 
        try:
            from .serializer import __pluginInfo__ as serializer_info
        except (ModuleNotFoundError, ImportError):
            from serializer import __pluginInfo__ as serializer_info
        serializer_info['Serializer.Init'](cntlr)

        # compile the rules is needed
        if options.xodel_compile is not None:
            try:
                from .xule import __pluginInfo__ as xule_plugin_info
            except (ModuleNotFoundError, ImportError):
                from xule import __pluginInfo__ as xule_plugin_info
            
            compile_method = xule_plugin_info['Xule.compile']
            compile_method(options.xodel_compile, options.xule_rule_set, 'pickle', getattr(options, "xule_max_recurse_depth"))

        # try running the xule processor - This is when rules are run without an instance document
        cmdLineXbrlLoaded(cntlr, options, None)

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