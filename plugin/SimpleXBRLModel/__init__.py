<<<<<<< HEAD
"""__init__.py

Simple XBRL odel

This is the package init file.

This plugin provides a simplified object model for XBRL. This model is independent of the the physical structure of the XBRL 
that is loaded.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2019 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23092 $
DOCSKIP
"""
import collections
import inspect
import sys

from . import SXM

def sxmGetModule():
    '''Returns the members of a the SXM module

    The return value is an object (really a namedtuple) that has a an attribute for each member in the module.
    This can be used like a module.
    '''
    clsMembers = inspect.getmembers(SXM, inspect.isclass)
    # Create a dummy class
    class _SXM:
        pass
    # Instantiate the class
    sxm = _SXM()
    # Add the members as properties
    for mem in clsMembers:
        setattr(sxm, mem[0], mem[1])

    return sxm

    # # Remove classes whose names start with an underscore. These are not allowed in named tuples and they shouldn't be 
    # # called from outside the module anyway.
    # clsDict = {x[0]: x[1] for x in clsMembers if not x[0].startswith('_')}
    # clsObject = collections.namedtuple('ModuleClasses', clsDict.keys())(*clsDict.values())
    # return clsObject

def sxmCmdUtilityRun(*args, **kwargs):
    pass
    #xsmGetModule()

def dummy(*args, **kwargs):
    pass

__pluginInfo__ = {
    'name': 'Simple XBRL Model Plugin',
    'version': '0.1',
    'description': 'T',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017-2020',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None,
    #'CntlrWinMain.Menu.Tools': sxmMenuTools,
    #'CntlrWinMain.Menu.Validation':sxmValidateMenuTools,
    'CntlrCmdLine.Options': dummy,
    'CntlrCmdLine.Utility.Run': dummy,
    #'CntlrCmdLine.Xbrl.Loaded': sxmCmdXbrlLoaded,
    #'Validate.Finally': sxmValidate,
    #'TestcaseVariation.Xbrl.Loaded': sxmTestXbrlLoaded,
    #'TestcaseVariation.Xbrl.Validated': sxmTestValidated,
    'SXM.getModule': sxmGetModule
=======
"""__init__.py

Simple XBRL odel

This is the package init file.

This plugin provides a simplified object model for XBRL. This model is independent of the the physical structure of the XBRL 
that is loaded.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2019 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23092 $
DOCSKIP
"""
import collections
import inspect
import sys

from . import SXM

def sxmGetModule():
    '''Returns the members of a the SXM module

    The return value is an object (really a namedtuple) that has a an attribute for each member in the module.
    This can be used like a module.
    '''
    clsMembers = inspect.getmembers(SXM, inspect.isclass)
    # Create a dummy class
    class _SXM:
        pass
    # Instantiate the class
    sxm = _SXM()
    # Add the members as properties
    for mem in clsMembers:
        setattr(sxm, mem[0], mem[1])

    return sxm

    # # Remove classes whose names start with an underscore. These are not allowed in named tuples and they shouldn't be 
    # # called from outside the module anyway.
    # clsDict = {x[0]: x[1] for x in clsMembers if not x[0].startswith('_')}
    # clsObject = collections.namedtuple('ModuleClasses', clsDict.keys())(*clsDict.values())
    # return clsObject

def sxmCmdUtilityRun(*args, **kwargs):
    pass
    #xsmGetModule()

def dummy(*args, **kwargs):
    pass

__pluginInfo__ = {
    'name': 'Simple XBRL Model Plugin',
    'version': '0.1',
    'description': 'T',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017-2020',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None,
    #'CntlrWinMain.Menu.Tools': sxmMenuTools,
    #'CntlrWinMain.Menu.Validation':sxmValidateMenuTools,
    'CntlrCmdLine.Options': dummy,
    'CntlrCmdLine.Utility.Run': dummy,
    #'CntlrCmdLine.Xbrl.Loaded': sxmCmdXbrlLoaded,
    #'Validate.Finally': sxmValidate,
    #'TestcaseVariation.Xbrl.Loaded': sxmTestXbrlLoaded,
    #'TestcaseVariation.Xbrl.Validated': sxmTestValidated,
    'SXM.getModule': sxmGetModule
>>>>>>> old/main
    }