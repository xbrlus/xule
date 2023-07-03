"""__init__.py

Add date funtions to xule

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
from . import xuleDateFunctions

def cmdUtilityRun(cntlr, options, **kwargs): 
    # This try block is not quite understood. The first import works when xuleDateFunctions is included on the --plugins options
    # But this does not work if it is imported using the 'imports' keywoard in the __pluginInfo__ of another pluging. So the
    # second import works for that. It has something to do with the way the plugins are imported.
    try:
        from .xule.XuleFunctions import add_normal_function
    except:
        from ..xule.XuleFunctions import add_normal_function
    add_normal_function('date-month-ends', xuleDateFunctions.date_month_ends, 1)

def dummy(*args, **kwrgs):
    pass

__pluginInfo__ = {
    'name': 'Xule Date Functions',
    'version': '0.9',
    'description': "Xule Date Functions",
    'copyright': '(c) Copyright 2023 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': dummy,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    #'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}