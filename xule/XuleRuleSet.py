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
                constants[cur.constantName] = {"file": file_num, "index": i}
            elif cur_name == "raiseDeclaration":
                full_name = package_name + "." + cur.raiseName
                if full_name not in rules.keys():
                    rules[full_name] = {"file": file_num, "index": i, "type": "raise", "full_name": full_name}
                else:
                    print("duplicate rule name: %s" % full_name)
            elif cur_name == "reportDeclaration":
                full_name = package_name + "." + cur.reportName
                if full_name not in rules.keys():
                    rules[full_name] = {"file": file_num, "index": i, "type": "report", "full_name": full_name}
                else:
                    print("duplicate rule name: %s" % full_name)
            elif cur_name == "formulaDeclaration":
                full_name = package_name + "." + cur.formulaName
                if full_name not in rules.keys():
                    rules[full_name] = {"file": file_num, "index": i, "type": "formula", "full_name": full_name}
                else:
                    print("duplicate rule name: %s" % full_name)
            elif cur_name == "functionDeclaration":
                functions[cur.functionName] = {"file": file_num, "index": i}
            elif cur_name == "macroDeclaration":
                macros[cur.macroName] = {"file": file_num, "index": i}
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
