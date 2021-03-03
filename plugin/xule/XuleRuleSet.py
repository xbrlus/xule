"""XuleRuleSet

Xule is a rule processor for XBRL (X)brl r(ULE). 

The XuleRuleSet module contains the XuleRuleSet class. This class is used to manage the rule set during rule processing.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2021 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23197 $
DOCSKIP
"""

import datetime
import io
import json
import logging
import os
import pickle
import tempfile
import zipfile
from arelle import PackageManager
from pickle import UnpicklingError
from . import XuleConstants as xc
from . import XuleUtility as xu

class XuleRuleSetError(Exception):
    """An exception class for handling errors managing the rule set"""
    def __init__(self, msg):
        print(msg)

class XuleRuleCompatibilityError(Exception):
    def __init__(self, msg):
        print(msg)
    


class XuleRuleSet(object):
    """The XuleRuleSet class.
    
    
    The rule set is a zip archive of compiled rules, a catalog, taxonomy packages. The archive is structured with the catalog and
    compiled rules at the top directory level. The is a 'packages' directory which contains taxonomy packages. When the rule set
    is loaded, the catalog and files are loaded and any packages are activated as taxonomy packages in Arelle.

    The catalog identifies the top level components of the rule set. This includes:
        * rules (assertions and output)
        * functions
        * constants
        * namespace declarations

    The catalog identifies where a componet is in the rule set.
    """
    
    def __init__(self, cntlr=None):
        """XuleRuleSet constructor
        
        :param cntlr: The Arelle controller
        :type cntlr: Arelle.Cntlr
        """
        self.catalog = None
        self.name = None
        self._xule_file_expression_trees = {}
        self.next_id = -1
        self._var_exprs = {}
        self._cntlr = cntlr
    
    def __del__(self):
        self.close()
    
    @property
    def xuleCompiledVersion(self):
        if self.catalog is not None:
            return self.catalog.get('xule_compiled_version')

    def close(self):
        """Close the ruleset"""
        pass
    
    def getFileInfoByName(self, file_name):
        """Get file catalog information by file name
        
        :returns: File information
        :rtype: dict
        """
        for file_info in self.catalog['files']:
            if file_info.get('name') == file_name:
                return file_info
                
    def open(self, rule_set_location, open_packages=True, open_files=True):
        """Open a rule set
        
        :param rule_set_location: The url for the rule set file
        :type rule_set_location: str
        :param open_packages: An indicator that determines if the packages in the rule set should be activated.
        :type open_packages: bool
        :param open_files: An indicator that determines if the rule files should be loaded into memory
        """

        if isinstance(rule_set_location, io.IOBase):
            file_object = rule_set_location
        else:
            # Only set the location if the the rule set file is a filename (not a file-like object)
            self.location = rule_set_location
            #Using arelle file source object. This will handle files from the web.
            file_object = self._get_rule_set_file_object()
        try:
            with zipfile.ZipFile(file_object, 'r') as zf:
                try: # pickle file first
                    with zf.open('catalog', 'r') as catalog_file:
                        self.catalog = pickle.loads(zf.open('catalog','r').read())
                except UnpicklingError: # json file
                    with zf.open('catalog', 'r') as catalog_file:
                        self.catalog = json.load(io.TextIOWrapper(catalog_file))

                #open packages in the ruleset
                if open_packages:
                    self._open_packages(zf)
                
                #load the files
                if open_files:
                    for file_info in self.catalog['files']:
                        try: # pickle file first
                            with zf.open(file_info['pickle_name'], "r") as p:
                                self._xule_file_expression_trees[file_info['file']] = pickle.load(p, encoding="utf8")                            
                        except UnpicklingError: # json file                         
                            with zf.open(file_info['pickle_name'], "r") as p:
                                self._xule_file_expression_trees[file_info['file']] = json.load(io.TextIOWrapper(p))

                            
            self.name = self.catalog['name']    
            self.verify_verson_compatability()           
        except KeyError:
            raise XuleRuleSetError(_("Error in the rule set. Cannot open catalog."))
        except FileNotFoundError:
            raise
        except zipfile.BadZipFile:
            raise XuleRuleSetError(_("Cannot open rule set file. Does not appear to be  zip file. File: {}".format(rule_set_location)))
        finally:
            file_object.close()

    def _get_rule_set_file_object(self):
        from arelle import FileSource
        file_source = FileSource.openFileSource(self.location, self._cntlr)
        file_object = file_source.file(self.location, binary=True)[0]    
        return file_object
    
    def _open_packages(self, rule_file):
        if self._cntlr is None:
            raise XuleRuleSetError("Internal error, cannot open packages from rule set.")
        temp_dir = tempfile.TemporaryDirectory()
        for file_name in rule_file.namelist():
            if file_name.startswith('packages/'):
                package_file = rule_file.extract(file_name, temp_dir.name)
                if self.open_package_file(package_file) is None:
                    raise XuleRuleSetError(_("Cannot open package '{}' from rule set.".format(file_name.partition('packages/')[2])))
    
    def open_package_file(self, file_name):
        """Open a taxonomy package in the rule set
        
        :param file_name: the name of the package file in the rule set
        :type file_name: str
        :return: The package information. This is the return from Arelle when activating the package
        """
        package_info = PackageManager.addPackage(self._cntlr, file_name)
        if package_info:
#                     print("Activation of package {0} successful.".format(package_info.get("name")))    
            self._cntlr.addToLog(_("Activation of package {0} successful.").format(package_info.get("name")), 
                          messageCode="info", file=package_info.get("URL"))
        else:
#                     print("Unable to load package \"{}\". ".format(file_name))                
            self._cntlr.addToLog(_("Unable to load package \"%(name)s\". "),
                          messageCode="arelle:packageLoadingError", 
                          level=logging.ERROR) 
        return package_info

    def get_packages_info(self):
        """Get a list of taxonomy packages in the rule set
        
        :returns: List of package information. The package information is returned when activating the package in Arelle
        :rtype: list
        """
        results = []
        temp_dir = tempfile.TemporaryDirectory()
        #Using arelle file source object. This will handle files from the web.
        file_object = self._get_rule_set_file_object()
        try:
            with zipfile.ZipFile(file_object, 'r') as zf:
                for package_file_name in zf.namelist():
                    if package_file_name.startswith('packages/'):
                        package_file = zf.extract(package_file_name, temp_dir.name)
                        package_info = PackageManager.addPackage(self._cntlr, package_file)
                        results.append(package_info)
        finally:
            file_object.close()
            
        return results

    def manage_packages(self, package_files, mode):
        """Add or remove taxonomy packages in the rule set
        
        :param package_files: A list of files to add or remove
        :type package_files: list
        :param mode: Indicates if the files should be added or removed. Valid values are 'add', 'del'
        :type mode: str
        """
        #The zipfile module cannot remove files or replace files. So, The original zip file will be opened and the contents
        #copied to a new zip file without the packages. Then the packages will be added.

        #open the rule set
        if self._cntlr is None:
            raise xr.XuleRuleSetException("Internal error, cannot add packages.")
        try:
            working_dir = tempfile.TemporaryDirectory()
            new_zip_file_name = os.path.join(working_dir.name, 'new.zip')
            new_package_names = [os.path.basename(x) for x in package_files]
            old_package_names = set()
            with zipfile.ZipFile(new_zip_file_name, 'w', zipfile.ZIP_DEFLATED) as new_zip:            
                with zipfile.ZipFile(self.location, 'r') as old_zip:
                    #copy the files from the original zip to the new zip excluding new packages
                    for old_file in old_zip.namelist():
                        keep = False
                        if old_file.startswith('packages/'):
                            package_name = old_file.partition('packages/')[2]
                            old_package_names.add(package_name)
                            if package_name not in new_package_names:
                                keep = True
                            elif mode == 'del':
                                print("Removing package '{}' from rule set.".format(package_name))
                        else:
                            keep = True
                        if keep:
                            new_zip.writestr(old_file, old_zip.open(old_file).read())
                    
                    if mode == 'add':
                        #add new packages
                        for package_file in package_files:
                            if os.path.isfile(package_file):
                                #open the package to make sure it is valie
                                if self.open_package_file(package_file) is None:
                                    raise xr.XuleRuleSetError(_("Package '{}' is not a valid package.".format(os.path.basename(package_file))))
                                new_zip.write(package_file, 'packages/' + os.path.basename(package_file))
                            else:
                                raise FileNotFoundError("Package '{}' is not found.".format(package_file))
                    
                    if mode == 'del':
                        for package_name in set(new_package_names) - old_package_names:
                            print("Package '{}' was not in the rule set.".format(package_name))
            #replace the old file with the new
            os.replace(new_zip_file_name, self.location)
              
        except KeyError:
            raise xr.XuleRuleSetError(_("Error in rule set. Cannot open catalog."))
               
    def getFile(self, file_num):
        """Gets the expressions tree (ast) for a rule file
        
        :param file_num: The file number of the desired file
        :type file_num: int
        
        The catalog identifies rule files by a number (an iteger).
        """
        return self._xule_file_expression_trees[file_num]
                
    def getItem(self, *args):
        """Get a top level component from the rule set
        
        :param args: The item to get
        :returns: Expression tree of the item
        :rtype: xule expression as a dict
        
        This function can be called in 2 ways:
            #. With one argument which is a catalog entry. The catalog entry is a dictionary which contains meta data about the item
            #. With two arguments, the first is the file number and the second is the index location in the file for the item.
        """        
        if len(args) == 2:
            file_num = args[0]
            index = args[1]
            
            self.getFile(file_num)
            if index >= len(self._xule_file_expression_trees[file_num]['xuleDoc']):
                raise XuleRuleSetError("Item index %s for file %s is out of range" % (str(index), str(file_num)))
                return
            
            return self._xule_file_expression_trees[file_num]['xuleDoc'][index]
        elif len(args) == 1:
            catalog_item = args[0]
            return self.getItem(catalog_item['file'], catalog_item['index'])

    def getItemByName(self, name, cat_type):
        """Get a top level component from the rule set by name
        
        :param name: The name of the item. (i.e. rule name, function name, constant name)
        :type name: str
        :param cat_type: The type of item to get (i.e. 'rule', 'function', 'constant')
        :type cat_type: str
        :returns: Expression tree of the item
        :rtype: xule expression as a dict        
        """
        if cat_type not in ('rule','function','constant','macro'):
            raise XuleRuleSetError("%s is an invalid catalog type" % cat_type)
            return
        
        item = self.catalog[cat_type + "s"].get(name)
        
        if not item:
            raise XuleRuleSetError("%s not found in the catalog." % name)
            return
        
        return (self.getItem(item['file'], item['index']), item)
    
    def getFunction(self, name):
        """Get function expression from the rule set
        
        :param name: Function name
        :type name: str
        :returns: Expression tree of the item
        :rtype: xule expression as a dict
        """        
        return self.getItemByName(name, 'function')
    
    def getRule(self, name):
        """Get rule expression from the rule set
        
        :param name: Rule name
        :type name: str
        :returns: Expression tree of the item
        :rtype: xule expression as a dict
        """         
        return self.getItemByName(name, 'rule')
    
    def getConstant(self, name):
        """Get constant expression from the rule set
        
        :param name: Constant name
        :type name: str
        :returns: Expression tree of the item
        :rtype: xule expression as a dict
        """         
        return self.getItemByName(name, 'constant')
    
    def hasOutputAttribute(self, name):
        """Check if the output attribute exists in the catalog
        
        :param name: Name of the output attribute
        :type name: str
        :rtype: boolean
        """
        return name in self.catalog['output_attributes']
        
    def getNamespaceUri(self, prefix):
        """Get namespace uri for a prefix from the rule set
        
        :param prefix: The prefix to look up
        :type prefix: str
        :return: The namespace uri
        :rtype: str or None if not found
        """
        #This case there is a file, but it didn't have any namespace declarations
        if prefix not in self.catalog['namespaces']:
            if prefix == '*':
                return None
                #raise XuleRuleSetError("There is no default namespace declaration.")
            else:
                raise XuleRuleSetError("Prefix %s does not have a namespace declaration." % prefix)
        
        return self.catalog['namespaces'][prefix]['uri']
        
    def getNamespaceInfoByUri(self, namespace_uri):   
        """Get catalog information for a namespace
        
        :param namespace_uri: The namespace uri
        :returns: The catalog entry for the namespace
        :rtype: dict or None if not found
        """    
        for namespace_info in self.catalog['namespaces'].values():
            if namespace_info['uri'] == namespace_uri:
                return namespace_info
        
        return    
    
    def get_constant_list(self, constant_name):
        """Identify a constant's dependency
        
        :param constant_name: The name of the constant
        :type constant_name: str
        :returns: decpendency code
        :rtype: str
        
        This method identifies what a constant depends upon. The dependency codes are:
            * rfrc - instance, external taxonomy
            * frc - instantce only
            * rtc - external taxonomy only
            * c - none
        """
        #ctype = 'c'
        #with self.catalog['constants'][constant_name]['dependencies']: # as const:
        if self.catalog['constants'][constant_name]['dependencies']['instance'] and \
            self.catalog['constants'][constant_name]['dependencies']['rules-taxonomy']:
            return 'rfrc'
        elif self.catalog['constants'][constant_name]['dependencies']['instance']:
            return 'frc'
        elif self.catalog['constants'][constant_name]['dependencies']['rules-taxonomy']:
            return 'rtc'
        return 'c'

    def get_grouped_constants(self):
        """Organize the constants by their dependencies.
        
        :returns: Dictionary keyed by dependence code. The value of the dictionary item is a list of constants
        :rtype: dict
        
        This method groups the constants by their dependencies. This is used when preloading constants to 
        determine which constants can be evaluate without certain data (instance data and external taxonomy data).
        
        The dependency codes are:
            * rfrc - instance, external taxonomy
            * frc - instantce only
            * rtc - external taxonomy only
            * c - none
        """
        self.all_constants = { 'rfrc': [],
                               'rtc' : [],
                               'frc' : [],
                               'c': [] 
                             }
        
        for constant in self.catalog['constants'].keys():
            if constant != ('extension_ns'):
                if 'unused' not in self.catalog['constants'][constant]:
                    constant_type = self.get_constant_list(constant)
                    self.all_constants[constant_type].append(constant)
        
        # remove any empty types
        del_const = []
        for constant_type in self.all_constants:
            if len(self.all_constants[constant_type]) <= 0:
                del_const.append(constant_type)
        for constant_type in del_const:
            del self.all_constants[constant_type]
    
        return self.all_constants
    
    
    def get_rule_list(self, rule_name):
        """Identify a rules's dependency
        
        :param rule_name: The name of the rule
        :type rule_name: str
        :returns: decpendency code
        :rtype: str
        
        This method identifies what a rule depends upon. The dependency codes are:
            * alldepr - instance, external taxonomy, constants
            * rtcr - external taxonomy, constants (not instance)
            * fcr - instance and constants
            * cr - constants
            * crap - constants but not instance or external taxonomy
            * r - none
        """        
        #ctype = 'c'
        #with self.catalog['constants'][constant_name]['dependencies']: # as const:
        if self.catalog['rules'][rule_name]['dependencies']['instance'] and \
            self.catalog['rules'][rule_name]['dependencies']['rules-taxonomy'] and \
            self.catalog['rules'][rule_name]['dependencies']['constants'] != set():
            return 'alldepr'
        elif self.catalog['rules'][rule_name]['dependencies']['rules-taxonomy'] and \
            not self.catalog['rules'][rule_name]['dependencies']['instance'] and \
            self.catalog['rules'][rule_name]['dependencies']['constants'] != set():
            return 'rtcr'
        elif self.catalog['rules'][rule_name]['dependencies']['instance'] and \
            self.catalog['rules'][rule_name]['dependencies']['constants'] != set():
            # and \
            #not self.catalog['rules'][rule_name]['dependencies']['rules-taxonomy'] and \
            #not self.catalog['rules'][rule_name]['dependencies']['instance']:
            return 'fcr'
        elif self.catalog['rules'][rule_name]['dependencies']['constants'] != set():
            return 'cr'
        elif not self.catalog['rules'][rule_name]['dependencies']['instance'] and \
            self.catalog['rules'][rule_name]['dependencies']['constants'] == set() and \
            not self.catalog['rules'][rule_name]['dependencies']['rules-taxonomy']:
            return 'crap'
        return 'r'
        
    def get_grouped_rules(self):
        """Organize the rules by their dependencies.
        
        :returns: Dictionary keyed by dependence code. The value of the dictionary item is a list of rules
        :rtype: dict
        
        This method groups the rules by their dependencies. 
        
        The dependency codes are:
            * alldepr - instance, external taxonomy, constants
            * rtcr - external taxonomy, constants (not instance)
            * fcr - instance and constants
            * cr - constants
            * crap - constants but not instance or external taxonomy
            * r - none
        """        
        self.all_rules = { 'alldepr' : [],
                           'rtr' : [],
                           'rtfcr' : [],
                           'rtcr' : [],
                           'fcr' : [],
                           'cr' : [],
                           'r' : [],
                           'crap' : []
                    }
        
        for rule in self.catalog['rules'].keys():
            rule_type = self.get_rule_list(rule)
            #for dependant in self.catalog['rules'][rule]['dependencies']['constants']:
            #    if self.get_constant_list(dependant) == 'rtc':
            #        constant_type = 'rfrc'
            #        break

            self.all_rules[rule_type].append(rule)
            #if rule in ('xbrlus-cc.oth.invalid_member.r14117'):
            #all_rules[rule_type][rule] = self.getRule(rule)
            # remove any empty types
        del_rules = []
        for rule_type in self.all_rules:
            if len(self.all_rules[rule_type]) <= 0:
                del_rules.append(rule_type)
        for rule_type in del_rules:
            del self.all_rules[rule_type]   
            
        return self.all_rules

    def verify_verson_compatability(self):
        if not (self.catalog.get('xule_compiled_version') is not None and int(self.catalog.get('xule_compiled_version')) in xu.get_rule_set_compatibility_version()):
            
            raise XuleRuleCompatibilityError("The rule set version '{}' is not compatible with version {} of the Xule Rule Processor".format(
                self.catalog.get('xule_compiled_version'), xu.version())
            )

                