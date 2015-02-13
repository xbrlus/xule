'''
Created on Dec 12, 2014

copywrite (c) 2014 XBRL US, Inc.
'''

import pickle
from pickle import Pickler
from pyparsing import ParseResults
import os
import shutil
import glob


class XuleRuleSetError(Exception):
    def __init__(self, msg):
        print(msg)
    
class XuleRuleSet(object):
    '''
    The ast is stored as a set of pickled files. There is a file for each rule file in the ruleset.
    Plus an additional file for the catalog.
    '''
    
    def __init__(self):
        '''
        Constructor
        '''     
        
        self._openForAdd = False
        self.catalog = None
        self.name = None
        self._pickles = {}
    
    def __del__(self):
        self.close()
    
    def new(self, location):
        if self._openForAdd:
            raise XuleRuleSetError("Trying to create a new rule set in an open rule set.")
        else:
            self.name = os.path.splitext(os.path.basename(location))[0]
            self.location = location
            if not os.path.exists(location):
                os.makedirs(location)
                
            self.catalog = {
                            "name": self.name,
                            "files": [],
                            "namespaces": {},
                            "rules": {},
                            "rules_by_file": {}, 
                            "functions": {},
                            "macros": {},
                            "constants": {},
                            "preconditions": {},
                            "packages": [],
                            "rule_bases": [],
                            "rules_dts_location": None
                            }
            
            #delete existing files
            existing_files = glob.glob(os.path.join(self.name,"*.pik"))
            for f in existing_files:
                os.remove(f)
            
            self._openForAdd = True
        
    def close(self):
        #Need to write the catalog
        if self._openForAdd:
            with open(os.path.join(self.location,"catalog.pik"),"wb") as o:
                pickle.dump(self.catalog, o, protocol=1)
        
        self._openForAdd = False
    
    def add(self, parseRes, file_time=None, file_name=None):
        
        file_num = self._addXuleFile(file_time, file_name)
        
        # update the catalog
        namespaces = {}
        rules = {}
        functions = {}
        macros = {}
        constants = {}
        preconditions = {}
        package = None
        package_name = ""
        rule_base = None
        
        #top level analysis
        for i in range(len(parseRes.xuleFile)):
            cur = parseRes.xuleFile[i]
            cur_name = cur.getName()
            
            if cur_name == "nsDeclaration":
                # add to the list of namespaces
                prefix = cur.prefix[0] if cur.prefix else "*"
                if prefix not in namespaces.keys():
                    namespaces[prefix] = {"file": file_num, "index": i, "prefix": prefix, "uri": cur.namespaceUri}
                else:
                    #duplicate namespace prefix
                    print("Duplicate namespace prefix: %s" % prefix)
                    
            elif cur_name == "preconditionDeclaration":
                preconditions[cur.preconditionName] = {"file": file_num, "index": i}
                
            elif cur_name == "package":
                package = {"file": file_num, "index": i}
                package_name = cur.packageName
                
            elif cur_name == "constantAssign":
                #check immediate dependencies
                dependencies = self._immediate_dependencies(cur)
                constants[cur.constantName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                
            elif cur_name == "raiseDeclaration":
                full_name = package_name + "." + cur.raiseName
                if full_name not in rules.keys():
                    #check immediate dependencies
                    dependencies = self._immediate_dependencies(cur)
                    
                    rules[full_name] = {"file": file_num, "index": i, "type": "raise", "full_name": full_name, "immediate_dependencies": dependencies}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "reportDeclaration":
                full_name = package_name + "." + cur.reportName
                if full_name not in rules.keys():
                    #check immediate dependencies
                    dependencies = self._immediate_dependencies(cur)
                    rules[full_name] = {"file": file_num, "index": i, "type": "report", "full_name": full_name, "immediate_dependencies": dependencies}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "formulaDeclaration":
                full_name = package_name + "." + cur.formulaName
                if full_name not in rules.keys():
                    #check immediate dependencies
                    dependencies = self._immediate_dependencies(cur)
                    rules[full_name] = {"file": file_num, "index": i, "type": "formula", "full_name": full_name, "immediate_dependencies": dependencies}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "functionDeclaration":
                #check immediate dependencies
                dependencies = self._immediate_dependencies(cur)
                functions[cur.functionName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                
            elif cur_name == "macroDeclaration":
                #check immediate dependencies
                dependencies = self._immediate_dependencies(cur)
                macros[cur.macroName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                
            elif cur_name == "ruleBase":
                rule_base = {"file": file_num, "index": i}
            else:
                print("Unknown top level parse result: %s" % parseRes.getName()) 
        
        self._saveFilePickle(file_num, parseRes)
            
        #Check for duplicate names
        self._dup_names(preconditions.keys(), self.catalog['preconditions'].keys())
        self._dup_names(constants.keys(), self.catalog['constants'].keys())
        self._dup_names(rules.keys(), self.catalog['rules'].keys())
        self._dup_names(functions.keys(), macros.keys())
        self._dup_names(functions.keys(), self.catalog['functions'].keys())
        self._dup_names(macros.keys(), self.catalog['macros'].keys())
        
        #merge current catalog info into the shelf catalog
        self.catalog['namespaces'][file_num] = namespaces
        self.catalog['rules_by_file'][file_num] = rules
        self.catalog['preconditions'].update(preconditions)
        self.catalog['rules'].update(rules)
        self.catalog['constants'].update(constants)
        self.catalog['functions'].update(functions)
        self.catalog['macros'].update(macros)
        if package:
            self.catalog['packages'].append(package)
        if rule_base:
            self.catalog['rule_bases'].append(rule_base)         
                
    def _dup_names(self, one, two):
        dups = set(one) & set(two)
        if len(dups) != 0:
            print("duplicate names:")
            for x in dups:
                print(x)

    def _immediate_dependencies(self, parseRes, varNames=None):
        #initialize the varNames list - this is used to deterime if a variable reference is a variable or constant
        if varNames is None:
            varNames = []
            
        dependencies = {'constants': set(),
                        'functions': set(),
                        'instance': False,
                        'rules-taxonomy': False}
        
        current_part = parseRes.getName()
        
        #add variable names
        if current_part == 'blockExpr':
            var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
            for varAssign in var_assignments:
                varNames.append(varAssign.varName)
        if current_part == 'formulaDeclaration':
            if 'varAssigns' in parseRes:
                for var_assign in parseRes.varAssigns:
                    varNames.append(var_assign.varName)
        if current_part == 'forExpr':
            varNames.append(parseRes.forVar)
        if current_part == 'factset':
            if 'aspectFilters' in parseRes:
                for aspect_filter in parseRes.aspectFilters:
                    if 'aspectVar' in aspect_filter:
                        varNames.append(aspect_filter.aspectVar)
        if current_part == 'whereExpr':
            varNames.append('item')
        if current_part == 'functionDeclaration':
            for arg in parseRes.functionArgs:
                varNames.append(arg.argName)
        if current_part == 'macroDeclaration':
            for arg in parseRes.macroArgs:
                varNames.append(arg.argName)
            
        #dependencies
        if current_part == 'varRef':
            if parseRes.varName not in varNames:
                #this must be a constant
                dependencies['constants'].add(parseRes.varName)
        if current_part == 'functionReference':
            dependencies['functions'].add(parseRes.functionName)
        if current_part == 'property':
            if parseRes.propertyName == 'rules-taxonomy':
                dependencies['rules-taxonomy'] = True
            elif parseRes.propertyName == 'taxonomy':
                dependencies['instance'] = True
        if current_part == 'factset':
            dependencies['instance'] = True
        
        #decend the syntax tree
        for next_part in parseRes:
            if isinstance(next_part, ParseResults):
                next_dependencies = self._immediate_dependencies(next_part, varNames)
                self._combine_dependencies(dependencies, next_dependencies)
                dependencies['constants'] |= next_dependencies['constants']
                dependencies['functions'] |= next_dependencies['functions']
                dependencies['instance'] = dependencies['instance'] or next_dependencies['instance']
                dependencies['rules-taxonomy'] = dependencies['rules-taxonomy'] or next_dependencies['rules-taxonomy']
                
        #remove variable names
        if current_part == 'blockExpr':
            var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
            for varAssign in var_assignments:
                varNames.pop()
        if current_part == 'formulaDeclaration':
            if 'varAssigns' in parseRes:
                for var_assign in parseRes.varAssigns:
                    varNames.pop()                
        if current_part == 'forExpr':
            varNames.pop()
        if current_part == 'factset':
            if 'aspectFilters' in parseRes:
                for aspect_filter in parseRes.aspectFilters:
                    if 'aspectVar' in aspect_filter:
                        varNames.pop()
        if current_part == 'whereExpr':
            varNames.pop()
        if current_part == 'functionDeclaration':
            for arg in parseRes.funcitonArgs:
                varNames.pop()
        if current_part == 'macroDeclaration':
            for arg in parseRes.macroArgs:
                varNames.pop()

        return dependencies

    def build_dependencies(self):
        for const_info in self.catalog['constants'].values():
            self._get_all_dependencies(const_info)
            
        for func_info in self.catalog['functions'].values():
            self._get_all_dependencies(func_info)
            
        for macro_info in self.catalog['macros'].values():
            self._get_all_dependencies(macro_info)
            
        for rule_info in self.catalog['rules'].values():
            self._get_all_dependencies(rule_info)
        
        #check if constants are used
        used_constants = set()
        for rule_info in self.catalog['rules'].values():
            for const_name in rule_info['dependencies']['constants']:
                used_constants.add(const_name)
        
        unused_constants = set(self.catalog['constants'].keys()) - used_constants
        for const_name in unused_constants:
            self.catalog['constants'][const_name]['unused'] = True

    def _get_all_dependencies(self, info):
        
        if 'dependencies' in info:
            return

        dependencies = {'constants': set(),
                        'functions': set(),
                        'instance': False,
                        'rules-taxonomy': False} 
        self._combine_dependencies(dependencies, info['immediate_dependencies'])
        
        for const_name in info['immediate_dependencies']['constants']:
            const_info = self.catalog['constants'][const_name]
            if 'dependencies' not in const_info:
                self._get_all_dependencies(const_info)
                
            self._combine_dependencies(dependencies, const_info['dependencies'])
        
        for func_name in info['immediate_dependencies']['functions']:
            if func_name in self.catalog['functions']:
                #if the fucntion name is not in the list, it is assumed to be a built in fucntion
                func_info = self.catalog['functions'][func_name]
                if 'dependencies' not in func_info:
                    self._get_all_dependencies(func_info)
                    
                self._combine_dependencies(dependencies, func_info['dependencies']) 
                
            #also need to check macros
            if func_name in self.catalog['macros']:
                macro_info = self.catalog['macros'][func_name]
                if 'dependencies' not in macro_info:
                    self._get_all_dependences(macro_info)
                    
                self._combine_dependencies(dependencies, macro_info['dependencies'])          
        
        info['dependencies'] = dependencies

    def _combine_dependencies(self, base, additional):
        base['constants'] |= additional['constants']
        base['functions'] |= additional['functions']
        base['instance'] = base['instance'] or additional['instance']
        base['rules-taxonomy'] = base['rules-taxonomy'] or additional['rules-taxonomy']

    def _addXuleFile(self, file_time, file_name):
        
        #get the next file number
        file_num = len(self.catalog["files"])
        pickle_name = "%s.%i.pik" %(self.name, file_num)
        file_dict = {"file": file_num, "pickle_name": pickle_name}
        if file_time:
            file_dict['mtime'] = file_time
        if file_name:
            file_dict['name'] = file_name
        self.catalog['files'].append(file_dict)
        
        return file_num
    
    def getFileInfoByName(self, file_name):
        for file_info in self.catalog['files']:
            if file_info.get('name') == file_name:
                return file_info
    
    def _saveFilePickle(self, file_num, parseRes):
        
        pickle_name = "%s.%i.pik" %(self.name, file_num)
        #save the pickle
        with open(os.path.join(self.location, pickle_name),"wb") as o:
            pickle.dump(parseRes, o, protocol=1)
    
        return pickle_name
                
    def open(self, ruleSetLocation):
        #self.name = os.path.splitext(os.path.basename(ruleSetLocation))[0]
        self.location = ruleSetLocation
        try:
            with open(os.path.join(ruleSetLocation,"catalog.pik"),"rb") as i:
                self.catalog = pickle.load(i)
            self.name = self.catalog['name']
            self._openForAdd = True
        except FileNotFoundError:
            print("Cannot open catalog.")
            raise
        
    def getFile(self, file_num):
        if file_num not in self._pickles.keys():
            #get the file info from the catalog
            file_item = next((file_item for file_item in self.catalog['files'] if file_item['file'] == file_num), None)
            if not file_item:
                raise XuleRuleSetError("File number %s not found" % str(file_num))
                return
            
            try:
                with open(os.path.join(self.location, file_item['pickle_name']),"rb") as p:
                    self._pickles[file_num] = pickle.load(p, encoding="utf8")
            except FileNotFoundError:
                raise XuleRuleSetError("Pickle file %s not found." % file_item['pickle_name'])
                return
        
        return self._pickles[file_num]
                
    
    def getItem(self, *args):
        
        if len(args) == 2:
            file_num = args[0]
            index = args[1]
            
            if file_num not in self._pickles.keys():
                #get the file info from the catalog
                file_item = next((file_item for file_item in self.catalog['files'] if file_item['file'] == file_num), None)
                if not file_item:
                    raise XuleRuleSetError("File number %s not found" % str(file_num))
                    return
                
                try:
                    with open(os.path.join(self.location, file_item['pickle_name']),"rb") as p:
                        self._pickles[file_num] = pickle.load(p, encoding="utf8")
                except FileNotFoundError:
                    raise XuleRuleSetError("Pickle file %s not found." % file_item['pickle_name'])
                    return
                
            if index >= len(self._pickles[file_num][0]):
                raise XuleRuleSetError("Item index %s for file %s is out of range" % (str(index), str(file_num)))
                return
            
            return self._pickles[file_num][0][index]
        elif len(args) == 1:
            catalog_item = args[0]
            return self.getItem(catalog_item['file'], catalog_item['index'])

    def getItemByName(self, name, cat_type):
        
        if cat_type not in ('rule','function','constant','macro'):
            raise XuleRuleSetError("%s is an invalid catalog type" % cat_type)
            return
        
        item = self.catalog[cat_type + "s"].get(name)
        
        if not item:
            raise XuleRuleSetError("Function %s not found in the catalog." % name)
            return
        
        return self.getItem(item['file'], item['index'])
    
    def getFunction(self, name):
        return self.getItemByName(name, 'function')
    
    def getMacro(self, name):
        return self.getItemByName(name, 'macro')
    
    def getRule(self, name):
        return self.getItemByName(name, 'rule')
    
    def getConstant(self, name):
        return self.getItemByName(name, 'constant')
    
    def getNamespaceUri(self, prefix, file_num):
        if file_num >= len(self.catalog['files']):
            raise XuleRuleSetError("File number %s is not in the catalog" % str(file_num))
        
        #This case there is a file, but it didn't have any namespace declarations
        if file_num not in self.catalog['namespaces'].keys():
            raise XuleRuleSetError("Namespace declaration for %s does not exist in file %s" % (prefix, str(file_num)))
        
        if prefix not in self.catalog['namespaces'][file_num].keys():
            raise XuleRuleSetError("Prefix %s is not dcleared in file %s" % (prefix, str(file_num)))
        
        return self.catalog['namespaces'][file_num][prefix]['uri']
        
    def getNamespaceInfoByUri(self, namespaceUri, file_num):
        if file_num not in self.catalog['namespaces']:
            return
        
        for namespace_info in self.catalog['namespaces'][file_num].values():
            if namespace_info['uri'] == namespaceUri:
                return namespace_info
        
        return
        
    def addTaxonomy(self, taxonomy_location, entry_point):
        base_location = os.path.join(self.location, 'base_taxonomy')
        
        if not os.path.isdir(taxonomy_location):
            raise XuleRuleSetError(_("Taxonomy location '%s' is not a directory" % taxonomy_location))
        
        if not os.path.isfile(os.path.join(taxonomy_location, entry_point)):
            raise XuleRuleSetError(_("Taxonomy entry point '%s' is not in '%s'" % (entry_point, taxonomy_location)))
        
        if os.path.exists(base_location):
            if not os.path.isdir(base_location):
                raise XuleRuleSetError(_("Taxonomy location '%s' is not a directory" % base_location))
            else:
                shutil.rmtree(base_location)

        #copy the taxonomy location to the rule set
        shutil.copytree(taxonomy_location, base_location)
        
        self.catalog['rules_dts_location'] = entry_point
            
    def getRulesTaxonomyLocation(self):
        if self.catalog['rules_dts_location'] is not None:
            return os.path.join(self.location, 'base_taxonomy', self.catalog['rules_dts_location'])
        else:
            return None
    
    
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

                
    def findnode(mylist, value):
        ''' returns the node for the value in mylist where 
            mylist is an llist.sllist 
        '''
        x = -1
        for num in range(len(mylist)):
            if mylist[num] == value:
                x = num
                break
        return mylist.nodeat(x) if x != -1 else None                
                        
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
            
        '''
        from llist import sllist
        for constant_type in self.all_constants:
            with self.all_constants[constant_type] as all_type:
                if len(all_type) > 1:
                    link_list = sllist(all_type)
                    for constant in link_list:
                        constant_index = link_list.index(constant)
                        low_index = constant_index
                        for dep in self.catalog['constants'][constant]['dependencies']['constants']:
                            dep_index = index(link_list, dep)
                            if dep_index > low_index:
                                low_index = dep_index
                        if low_index != constant_index:
                            
         '''               
                    
            #if constant in ('DEPRECATED_NAMES', 'TOTAL_LABEL_URIS', 'DIM_CONCEPTS'):
            #    constant_type = 'c'
            #elif constant in ('calcNetwork'):
            #    constant_type = 'rtc'
            #elif 2 == 2:
            #    constant_type = 'frc'
            #else:
            #    constant_type = 'c'
            #self.all_constants[constant_type][constant] = self.getConstant(constant)

        
        
        
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


