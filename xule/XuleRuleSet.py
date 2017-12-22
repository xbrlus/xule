"""XuleContext

Xule is a rule processor for XBRL (X)brl r(ULE). 

The XuleContext module defines classes for managing the processing context. The processing context manages the rule set and stores data
for keeping track of the processing (including the iterations that are created when processing a rule).

DOCSKIP
Copyright 2017 XBRL US Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 21691 $
DOCSKIP
"""




'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved


'''
import pickle
import os
import datetime
import zipfile
import tempfile
import logging
from arelle import PackageManager

class XuleRuleSetError(Exception):
    def __init__(self, msg):
        print(msg)

class XuleRuleSet(object):
    """The XuleRuleSet class.
    
    The rule set contains the 'compiled' rules. This class manages the creation and querying of the ruleset. A ruleset is made of
    a collection of Xule rule files. The files are parsed and added to the ruleset. The ruleset has a catalog with keeps track of top
    level components (such as, rules, namespaces, user defined functions, constants). The catalog identifies which file these components
    are in and their index in the file.
    
    When all the files are added, a post parse operation which determines dependencies and between components (i.e. rule A uses constant C
    and function F. It also links variable references their declarations and identifies which expressions create iterations.
    
    The ruleset is stored as a set of pickled files.
    """
    
    def __init__(self, cntlr=None):
        """Constructor
        """

        self._open_for_add = False
        self.catalog = None
        self.name = None
        self._xule_file_expression_trees = {}
        self.next_id = -1
        self._var_exprs = {}
        self._file_status = {}
        self._cntlr = cntlr
    
    def __del__(self):
        self.close()
    
    def new(self, location):
        """Create a new ruleset
        
        This will establish the directory of the ruleset.
        
        Arguments:
            location (string): directory for the new ruleset
        """
        
        #check if the ruleset is already opened.
        if self._open_for_add:
            raise XuleRuleSetError("Trying to create a new rule set in an open rule set.")
        else:
            self.name = os.path.basename(location)
            self.location = location
            self.path = os.path.dirname(location)

            self.catalog = {
                            "name": self.name,
                            "files": [],
                            "namespaces": {},
                            "rules": {},
                            "rules_by_file": {}, 
                            "functions": {},
                            "constants": {},
                            "output_attributes": {},
                            }
            
            self._open_for_add = True
    
    def close(self):
        """Close the ruleset.
        
        If the ruleset was opened for adding, this will write out the pickle files.
        """
        if self._open_for_add:
            path = os.path.dirname(self.location)
            #Make sure the directory exists
            if len(path) > 0 and not os.path.exists(path):
                os.makedirs(path)
            
            #Create the zip file
            with zipfile.ZipFile(self.location, 'w', zipfile.ZIP_DEFLATED) as zf:
                #write the pickled rule files
                for file_num, parse_tree in self._xule_file_expression_trees.items():
                    self._saveFilePickle(zf, file_num, parse_tree)

                #write the catalog
                zf.writestr('catalog', pickle.dumps(self.catalog, protocol=2))        
        self._open_for_add = False
        self._file_status = {}
    
    def getFileInfoByName(self, file_name):
        """Get file catalog information by file name.
        """
        for file_info in self.catalog['files']:
            if file_info.get('name') == file_name:
                return file_info
                
    def open(self, ruleSetLocation, open_packages=True, open_files=True):
        """Open a rule set.
        
        Arguments:
            ruleSetLocation (string): The directory of the ruleset
        """
        #self.name = os.path.splitext(os.path.basename(ruleSetLocation))[0]
        self.location = ruleSetLocation
        pickle_start = datetime.datetime.today()
        
        #Using arelle file source object. This will handle files from the web.
        file_object = self._get_rule_set_file_object()
        try:
            with zipfile.ZipFile(file_object, 'r') as zf:
                self.catalog = pickle.loads(zf.open('catalog','r').read())
                #open packages in the ruleset
                if open_packages:
                    self._open_packages(zf)
                
                #load the files
                if open_files:
                    for file_info in self.catalog['files']:
                        with zf.open(file_info['pickle_name'], "r") as p:
                            self._xule_file_expression_trees[file_info['file']] = pickle.load(p, encoding="utf8")
                            
            self.name = self.catalog['name']
            self._open_for_add = False                
        except KeyError:
            print("Error in the rule set. Cannot open catalog.") #, file=sys.stderr)
            raise
        except FileNotFoundError:
            raise
        finally:
            file_object.close()

#         #load up all the rules.
#         if open_files:
#             for file_info in self.catalog['files']:
#                 self.getFile(file_info['file'])
    
        #Check for packages
        pickle_end = datetime.datetime.today()
        print("Rule Set Loaded", pickle_end - pickle_start)

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
        """Return the AST from a file in the ruleset.
        """
#         if file_num not in self._xule_file_expression_trees.keys():
#             #get the file info from the catalog
#             file_item = next((file_item for file_item in self.catalog['files'] if file_item['file'] == file_num), None)
#             if not file_item:
#                 raise XuleRuleSetError("File number %s not found" % str(file_num))
#                 return
#             
#             try:
#                 with zipfile.ZipFile(self.location, 'r') as zf:
#                     with zf.open(file_item['pickle_name'], "r") as p:
#                         self._xule_file_expression_trees[file_num] = pickle.load(p, encoding="utf8")
#             except (FileNotFoundError, KeyError): #KeyError if the file is not in the archive
#                 raise XuleRuleSetError("Pickle file %s not found." % file_item['pickle_name'])
#                 return
            
        return self._xule_file_expression_trees[file_num]
                
    def getItem(self, *args):
        """Get AST of a top level component.
        
        This method can take 1 or 2 arguments. If there is one argument, it is a catalog entry (which is a tuple). If there are two
        arguments, the first is the file number and second is the index within the file for the top level component.
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
        """Get the AST of a top level component by name.
        
        Arguments:
            name (string): Name of the component (i.e. rule name, function name, constanct name)
            cat_type (stirng): Type of component (constant, function, rule, namespace)
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
        return self.getItemByName(name, 'function')
    
    def getRule(self, name):
        return self.getItemByName(name, 'rule')
    
    def getConstant(self, name):
        return self.getItemByName(name, 'constant')
    
    def getNamespaceUri(self, prefix):
        #This case there is a file, but it didn't have any namespace declarations
        if prefix not in self.catalog['namespaces']:
            if prefix == '*':
                raise XuleRuleSetError("There is no default namespace declaration.")
            else:
                raise XuleRuleSetError("Prefix %s does not have a namespace declaration." % prefix)
        
        return self.catalog['namespaces'][prefix]['uri']
        
    def getNamespaceInfoByUri(self, namespaceUri):       
        for namespace_info in self.catalog['namespaces'].values():
            if namespace_info['uri'] == namespaceUri:
                return namespace_info
        
        return    
    
    def get_constant_list(self, constant_name):
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



