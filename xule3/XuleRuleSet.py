'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21691 $
'''
import pickle
import os
import datetime
import zipfile
import tempfile
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
    
    def __init__(self):
        """Constructor
        """

        self._open_for_add = False
        self.catalog = None
        self.name = None
        self._xule_file_expression_trees = {}
        self.next_id = -1
        self._var_exprs = {}
        self._file_status = {}
    
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
                
    def open(self, ruleSetLocation, open_packages=True):
        """Open a rule set.
        
        Arguments:
            ruleSetLocation (string): The directory of the ruleset
        """
        #self.name = os.path.splitext(os.path.basename(ruleSetLocation))[0]
        self.location = ruleSetLocation
        pickle_start = datetime.datetime.today()
        try:
            with zipfile.ZipFile(self.location, 'r') as zf:
                self.catalog = pickle.loads(zf.open('catalog','r').read())
                #open packages in the ruleset
                if open_packages:
                    self._open_packages(zf)
            self.name = self.catalog['name']
            self._open_for_add = False                
        except KeyError:
            print("Error in the rule set. Cannot open catalog.") #, file=sys.stderr)
            raise
        except FileNotFoundError:
            raise
        
        #load up all the rules.
        for file_info in self.catalog['files']:
            self.getFile(file_info['file'])
    
        #Check for packages
        pickle_end = datetime.datetime.today()
        print("Rule Set Loaded", pickle_end - pickle_start)
    
    def _open_packages(self, rule_file):
        temp_dir = tempfile.TemporaryDirectory()
        for file_name in rule_file.namelist():
            if file_name.startswith('packages/'):
                package_file = rule_file.extract(file_name, temp_dir.name)
                package_info = PackageManager.addPackage(self, package_file)
                if package_info:
                    print("Activation of package {0} successful.".format(package_info.get("name")))    
#                     self.cntlr.addToLog(_("Activation of package {0} successful.").format(package_info.get("name")), 
#                                   messageCode="info", file=package_info.get("URL"))
                else:
                    print("Unable to load package \"{}\". ".format(file_name))
                   
#                     self.cntlr.addToLog(_("Unable to load package \"%(name)s\". "),
#                                   messageCode="arelle:packageLoadingError", 
#                                   messageArgs={"name": cmd, "file": cmd}, level=logging.ERROR)
    
    def getFile(self, file_num):
        """Return the AST from a file in the ruleset.
        """
        if file_num not in self._xule_file_expression_trees.keys():
            #get the file info from the catalog
            file_item = next((file_item for file_item in self.catalog['files'] if file_item['file'] == file_num), None)
            if not file_item:
                raise XuleRuleSetError("File number %s not found" % str(file_num))
                return
            
            try:
                with zipfile.ZipFile(self.location, 'r') as zf:
                    with zf.open(file_item['pickle_name'], "r") as p:
                        self._xule_file_expression_trees[file_num] = pickle.load(p, encoding="utf8")
            except (FileNotFoundError, KeyError): #KeyError if the file is not in the archive
                raise XuleRuleSetError("Pickle file %s not found." % file_item['pickle_name'])
                return
            
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



