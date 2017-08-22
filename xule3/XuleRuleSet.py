'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21691 $
'''
import pickle
#from pickle import Pickler
from pyparsing import ParseResults
import os
import shutil
import glob
import collections
import datetime

class XuleRuleSetError(Exception):
    def __init__(self, msg):
        print(msg)

BUILTIN_FUNCTIONS = {'list': ('aggregate', ''),
                     'sdic_get_item': ('regular', 'single'),
                     'duration': ('regular', 'single'),
                     'uri': ('regular', 'single'),
                     'time-period': ('regular', 'single'),
                     'sdic_append': ('regular', 'single'),
                     'sum': ('aggregate', ''),
                     'max': ('aggregate', ''),
                     'instant': ('regular', 'single'),
                     'sdic_set_item': ('regular', 'single'),
                     'extension_concepts': ('regular', 'single'),
                     'schema-type': ('regular', 'single'),
                     'count': ('aggregate', ''),
                     'number': ('regular', 'single'),
                     'roll_forward_recalc': ('regular', 'multi'),
                     'sdic_find_items': ('regular', 'single'),
                     'find_roll_forward': ('regular', 'single'),
                     'entity': ('regular', 'single'),
                     'all': ('aggregate', ''),
                     'sdic_create': ('regular', 'single'),
                     'set': ('aggregate', ''),
                     'mod': ('regular', 'single'),
                     'any': ('aggregate', ''),
                     'qname': ('regular', 'single'),
                     'exists': ('regular', 'single'),
                     'min': ('aggregate', ''),
                     'forever': ('regular', 'single'),
                     'sdic_remove_item': ('regular', 'single'),
                     'sdic_get_items': ('regular', 'single'),
                     'unit': ('regular', 'single'),
                     'first': ('aggregate', ''),
                     'sdic_has_key': ('regular', 'single'),
                     'missing': ('regular', 'single'),
                     'num_to_string': ('regular', 'single')}


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
        self.next_id = -1
        self._var_exprs = {}
    
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
                            "rule_base": None,
                            "rules_dts_location": None,
                            "pre_calc_expressions": [],
                            "node_index": {}
                            }
            
            #delete existing files
            existing_files = glob.glob(os.path.join(self.name,"*.pik"))
            for f in existing_files:
                os.remove(f)
            
            self._openForAdd = True
        
    def close(self):
        if self._openForAdd:
            #write the pickled rule files
            for file_num, parseRes in self._pickles.items():
                self._saveFilePickle(file_num, parseRes)
            
            #write the catalog
            with open(os.path.join(self.location,"catalog.pik"),"wb") as o:
                pickle.dump(self.catalog, o, protocol=1)
        
        self._openForAdd = False
    
    def add(self, parseRes, file_time=None, file_name=None):
        
        if self._openForAdd == False:
            raise XuleRuleSetError(_("Attempting to add rule file, but rule set is not open for add"))
        
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
        
        #assign node_ids
        self.next_id = self._assign_node_ids(file_num, parseRes, self.next_id + 1)
        
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
                preconditions[cur.preconditionName] = {"file": file_num, "index": i, "node_id": cur.node_id}
                
            elif cur_name == "package":
                package = {"file": file_num, "index": i}
                package_name = cur.packageName
                
            elif cur_name == "constantAssign":
                #check immediate dependencies
#                 dependencies = self._immediate_dependencies(cur)
#                 constants[cur.constantName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                constants[cur.constantName] = {"file": file_num, "index": i, "node_id": cur.node_id}
                
            elif cur_name == "raiseDeclaration":
                full_name = package_name + "." + cur.raiseName
                if full_name not in rules.keys():
                    #check immediate dependencies
#                     dependencies = self._immediate_dependencies(cur)
#                     rules[full_name] = {"file": file_num, "index": i, "type": "raise", "full_name": full_name, "immediate_dependencies": dependencies}
                    precon_names =  []                    
                    if 'preconditionRef' in cur:
                        precon_names = [name for name in cur.preconditionRef.preconditionNames]

                    rules[full_name] = {"file": file_num, "index": i, "type": "raise", "full_name": full_name, "preconditions": precon_names}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "reportDeclaration":
                full_name = package_name + "." + cur.reportName
                if full_name not in rules.keys():
                    #check immediate dependencies
#                     dependencies = self._immediate_dependencies(cur)
#                     rules[full_name] = {"file": file_num, "index": i, "type": "report", "full_name": full_name, "immediate_dependencies": dependencies}                
                    precon_names =  []                    
                    if 'preconditionRef' in cur:
                        precon_names = [name for name in cur.preconditionRef.preconditionNames]
                    rules[full_name] = {"file": file_num, "index": i, "type": "report", "full_name": full_name, "preconditions": precon_names}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "formulaDeclaration":
                full_name = package_name + "." + cur.formulaName
                if full_name not in rules.keys():
                    #check immediate dependencies
#                     dependencies = self._immediate_dependencies(cur)
#                     rules[full_name] = {"file": file_num, "index": i, "type": "formula", "full_name": full_name, "immediate_dependencies": dependencies}
                    precon_names =  []                    
                    if 'preconditionRef' in cur:
                        precon_names = [name for name in cur.preconditionRef.preconditionNames]

                    rules[full_name] = {"file": file_num, "index": i, "type": "formula", "full_name": full_name, "preconditions": precon_names}
                else:
                    print("duplicate rule name: %s" % full_name)
                    
            elif cur_name == "functionDeclaration":
                #check immediate dependencies
#                 dependencies = self._immediate_dependencies(cur)
#                 functions[cur.functionName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                functions[cur.functionName] = {"file": file_num, "index": i}
                
            elif cur_name == "macroDeclaration":
                #check immediate dependencies
#                 dependencies = self._immediate_dependencies(cur)
#                 macros[cur.macroName] = {"file": file_num, "index": i, "immediate_dependencies": dependencies}
                macros[cur.macroName] = {"file": file_num, "index": i}
                
            elif cur_name == "ruleBase":
                rule_base = {"file": file_num, "index": i}
            else:
                print("Unknown top level parse result: %s" % parseRes.getName()) 
        
        #self._saveFilePickle(file_num, parseRes)
        self._pickles[file_num] = parseRes
            
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
            if self.catalog['rule_base'] is not None:
                raise XuleRuleSetError(_("Only one 'rule-base' is allowed."))
            else:
                self.catalog['rule_base'] = rule_base         
                
    def _dup_names(self, one, two):
        dups = set(one) & set(two)
        if len(dups) != 0:
            print("duplicate names:")
            for x in dups:
                print(x)
                
    def _assign_node_ids(self, file_num, parseRes, next_id, chain=None):
        if isinstance(parseRes, ParseResults):
            if chain is None:
                chain = [file_num,]
            parseRes['node_id'] = next_id
#             self.catalog['node_index'][next_id] = chain
            for i, next_part in enumerate(parseRes):
                if isinstance(next_part, ParseResults):
                    next_id += 1
                    next_id = self._assign_node_ids(file_num, next_part, next_id, chain + [i,]) 
            return next_id
        else:
            return next_id
        
#     def _immediate_dependencies(self, parseRes): 
#         dependencies = self._immediate_dependencies_detail(parseRes)
#         return dependencies
# 
#     def _immediate_dependencies_detail(self, parseRes, var_names=None, var_exclusions=None):
#         
#         #initialize the varNames list - this is used to deterime if a variable reference is a variable or constant
#         if var_names is None:
#             var_names = collections.defaultdict(list)
#         if var_exclusions is None:
#             var_exclusions = []
#             
#         dependencies = {'constants': set(),
#                         'functions': set(),
#                         'instance': False,
#                         'rules-taxonomy': False,
#                         #'number': 0 # 0 = singleton, > 0 is multiton
#                         }
#         
#         current_part = parseRes.getName()
#         
#         #add variable names
#         if current_part == 'blockExpr':
#             var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
#             for var_assign in var_assignments:
#                 var_names[var_assign.varName].append(var_assign.node_id)
#                 self._var_exprs[var_assign.node_id] = var_assign.expr[0]
#         if current_part == 'varAssign':
#             var_exclusions.append(parseRes.node_id)
#         if current_part == 'formulaDeclaration':
#             if 'varAssigns' in parseRes:
#                 for var_assign in parseRes.varAssigns:
#                     var_names[var_assign.varName].append(var_assign.node_id)
#                     self._var_exprs[var_assign.node_id] = var_assign.expr[0]
#         if current_part == 'forExpr':
#             #var_names[parseRes.forVar].append(parseRes.node_id)
#             var_names[parseRes.forControl.forVar].append(parseRes.forControl.node_id)
#             self._var_exprs[parseRes.forControl.node_id] = parseRes.forControl           
#         if current_part == 'factset':
#             if 'aspectFilters' in parseRes:
#                 for aspect_index, aspect_filter in enumerate(parseRes.aspectFilters,1):
#                     if 'aspectVar' in aspect_filter:
#                         var_names[aspect_filter.aspectVar].append((parseRes.node_id, aspect_index))
#             if 'whereExpr' in parseRes:
#                 var_names['item'].append((parseRes.node_id, 0))
#         if current_part == 'functionDeclaration':
#             for arg in parseRes.functionArgs:
#                 var_names[arg.argName].append(arg.node_id)
#         if current_part == 'macroDeclaration':
#             for arg in parseRes.macroArgs:
#                 var_names[arg.argName].append(arg.node_id)
#             
#         #dependencies
#         if current_part == 'varRef':
#             if parseRes.varName not in var_names:
#                 #this must be a constant
#                 dependencies['constants'].add(parseRes.varName)
#                 parseRes['is_constant'] = True
#             else:
#                 #this is a variable reference. Find the declaration
#                 #parseRes['var_declaration'] = var_names[parseRes.varName][-1]
#                 for declaration_id in reversed(var_names[parseRes.varName]):
#                     if declaration_id not in var_exclusions and (declaration_id < parseRes.node_id if not isinstance(declaration_id, tuple) else True):
#                         parseRes['var_declaration'] = declaration_id
#                         break
#                 parseRes['is_constant'] = False
#         if current_part == 'functionReference':
#             dependencies['functions'].add(parseRes.functionName)
#         if current_part == 'property':
#             if parseRes.propertyName == 'rules-taxonomy':
#                 dependencies['rules-taxonomy'] = True
#             elif parseRes.propertyName == 'taxonomy':
#                 dependencies['instance'] = True
#         if current_part == 'factset':
#             dependencies['instance'] = True
#             #dependencies['number'] += 1
#         #if current_part == 'forExpr':
#             #dependencies['number'] += 1
#         
#         #decend the syntax tree
#         for next_part in parseRes:
#             if isinstance(next_part, ParseResults):
#                 next_dependencies = self._immediate_dependencies_detail(next_part, var_names, var_exclusions)
#                 self._combine_dependencies(dependencies, next_dependencies)
#                 dependencies['constants'] |= next_dependencies['constants']
#                 dependencies['functions'] |= next_dependencies['functions']
# #                 dependencies['instance'] = dependencies['instance'] or next_dependencies['instance']
# #                 dependencies['rules-taxonomy'] = dependencies['rules-taxonomy'] or next_dependencies['rules-taxonomy']
#                 
#         #remove variable names
#         if current_part == 'blockExpr':
#             var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
#             for var_assign in var_assignments:
#                 var_names[var_assign.varName].pop()
#         if current_part == 'varAssign':
#             var_exclusions.pop()                
#         if current_part == 'formulaDeclaration':
#             if 'varAssigns' in parseRes:
#                 for var_assign in parseRes.varAssigns:
#                     var_names[var_assign.varName].pop()                
#         if current_part == 'forExpr':
#             var_names[parseRes.forControl.forVar].pop()
# 
#         if current_part == 'factset':
#             if 'aspectFilters' in parseRes:
#                 for aspect_filter in parseRes.aspectFilters:
#                     if 'aspectVar' in aspect_filter:
#                         var_names[aspect_filter.aspectVar].pop()
#             if 'whereExpr' in parseRes:
#                 var_names['item'].pop
#         if current_part == 'functionDeclaration':
#             for arg in parseRes.funcitonArgs:
#                 var_names[arg.argName].pop()
#         if current_part == 'macroDeclaration':
#             for arg in parseRes.macroArgs:
#                 var_names[arg.argName].pop()
# 
#         return dependencies


    def dependencies_top(self, info):
        if 'dependencies' not in info:
            ast = self.getItem(info['file'], info['index'])
            dependencies, immediate_dependencies = self.dependencies_detail(ast)
            info['dependencies'] = dependencies
            info['immediate_dependencies'] = immediate_dependencies
        
    def dependencies_detail(self, parseRes, var_names=None, var_exclusions=None):
        
        #initialize the varNames list - this is used to deterime if a variable reference is a variable or constant
        if var_names is None:
            var_names = collections.defaultdict(list)
        if var_exclusions is None:
            var_exclusions = []
        
        dependencies = {'constants': set(),
                        'functions': set(),
                        'instance': False,
                        'rules-taxonomy': False,
                        }
        immediate_dependencies = {'constants': set(),
                'functions': set(),
                'instance': False,
                'rules-taxonomy': False,
                }
        
        current_part = parseRes.getName()
        
        #add variable names
        if current_part == 'blockExpr':
            var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
            for var_assign in var_assignments:
                var_names[var_assign.varName].append(var_assign)
                self._var_exprs[var_assign.node_id] = var_assign.expr[0]
        if current_part == 'varAssign':
            var_exclusions.append(parseRes)
        if current_part == 'formulaDeclaration':
            if 'varAssigns' in parseRes:
                for var_assign in parseRes.varAssigns:
                    var_names[var_assign.varName].append(var_assign)
                    self._var_exprs[var_assign.node_id] = var_assign.expr[0]
        if current_part == 'forExpr':
            #var_names[parseRes.forVar].append(parseRes)
            var_names[parseRes.forControl.forVar].append(parseRes.forControl)
            self._var_exprs[parseRes.forControl.node_id] = parseRes.forControl
        if current_part == 'factset':
            if 'aspectFilters' in parseRes:
                for aspect_index, aspect_filter in enumerate(parseRes.aspectFilters,1):
                    if 'aspectVar' in aspect_filter:
                        #var_names[aspect_filter.aspectVar].append((parseRes, aspect_index))
                        var_names[aspect_filter.aspectVar].append(aspect_filter)
            if 'whereExpr' in parseRes:
                #var_names['item'].append((parseRes, 0))
                var_names['item'].append(parseRes.whereExpr)
       
        if current_part == 'functionDeclaration':
            for arg in parseRes.functionArgs:
                var_names[arg.argName].append(arg)
        if current_part == 'macroDeclaration':
            for arg in parseRes.macroArgs:
                var_names[arg.argName].append(arg)
            
        #dependencies
        if current_part == 'varRef':
            if parseRes.varName not in var_names:
                #this must be a constant
                const_info = self.catalog['constants'][parseRes.varName]
                self.dependencies_top(const_info) 
                self._combine_dependencies(dependencies, const_info['dependencies'])
           
                dependencies['constants'].add(parseRes.varName)
                immediate_dependencies['constants'].add(parseRes.varName)
                parseRes['is_constant'] = True
            else:
                #this is a variable reference. Find the declaration
                #parseRes['var_declaration'] = var_names[parseRes.varName][-1]
                #for declaration_id in reversed(var_names[parseRes.varName]):
                for declaration in reversed(var_names[parseRes.varName]):
                    #if declaration not in var_exclusions and (declaration.node_id < parseRes.node_id if not isinstance(declaration, tuple) else True):
                    if declaration not in var_exclusions and declaration.node_id < parseRes.node_id:
                        #if isinstance(declaration, tuple):
                        if declaration.getName() in ('aspectFilter', 'whereExpr'):
                            #parseRes['var_declaration'] = (declaration[0].node_id, declaration[1])
                            parseRes['var_declaration'] = declaration.node_id
                            #The only place the var declaration is a tuple is in the where clause of a factset. In this case the variable reference is always 'instance' dependent.
                            dependencies['instance'] = True
                            immediate_dependencies['instance'] = True
                        else:
                            parseRes['var_declaration'] = declaration.node_id
                            if declaration.get('instance'):
                                dependencies['instance'] = True
                                immediate_dependencies['instance'] = True
                            if declaration.get('rules-taxonomy'):
                                dependencies['rules-taxonomy'] = True
                                immediate_dependencies['rules-taxonomy'] = True
                        break
                parseRes['is_constant'] = False
        if current_part == 'functionReference':
            func_info = self.catalog['functions'].get(parseRes.functionName)
            if func_info is not None:
                self.dependencies_top(func_info)
                self._combine_dependencies(dependencies, func_info['dependencies'])
            dependencies['functions'].add(parseRes.functionName)
            immediate_dependencies['functions'].add(parseRes.functionName)
        if current_part == 'property':
            if parseRes.propertyName == 'rules-taxonomy':
                dependencies['rules-taxonomy'] = True
                immediate_dependencies['rules-taxonomy'] = True
            elif parseRes.propertyName == 'taxonomy':
                dependencies['instance'] = True
                immediate_dependencies['instance'] = True
        if current_part == 'factset':
            dependencies['instance'] = True
            immediate_dependencies['instance'] = True
        
        #decend the syntax tree
        for next_part in parseRes:
            if isinstance(next_part, ParseResults):
                next_dependencies, next_immediate_dependencies = self.dependencies_detail(next_part, var_names, var_exclusions)
                self._combine_dependencies(dependencies, next_dependencies)
                self._combine_dependencies(immediate_dependencies, next_immediate_dependencies)
                dependencies['constants'] |= next_dependencies['constants']
                dependencies['functions'] |= next_dependencies['functions']
                immediate_dependencies['constants'] |= next_immediate_dependencies['constants']
                immediate_dependencies['functions'] |= next_immediate_dependencies['functions']
        
#         if dependencies['instance']:
#             parseRes['instance'] = True
#         if dependencies['rules-taxonomy']:
#             parseRes['rules-taxonomy'] = True
                
        #remove variable names
        if current_part == 'blockExpr':
            var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
            for var_assign in var_assignments:
                var_names[var_assign.varName].pop()
        if current_part == 'varAssign':
            var_exclusions.pop()                
        if current_part == 'formulaDeclaration':
            if 'varAssigns' in parseRes:
                for var_assign in parseRes.varAssigns:
                    var_names[var_assign.varName].pop()                
        if current_part == 'forExpr':
            var_names[parseRes.forControl.forVar].pop()

        if current_part == 'factset':
            if 'aspectFilters' in parseRes:
                for aspect_filter in parseRes.aspectFilters:
                    if 'aspectVar' in aspect_filter:
                        var_names[aspect_filter.aspectVar].pop()
            if 'whereExpr' in parseRes:
                var_names['item'].pop
        if current_part == 'functionDeclaration':
            for arg in parseRes.funcitonArgs:
                var_names[arg.argName].pop()
        if current_part == 'macroDeclaration':
            for arg in parseRes.macroArgs:
                var_names[arg.argName].pop()

        return dependencies, immediate_dependencies

    _PRE_CALC_EXPRESSIONS = ['qName',
                            'integer',
                            'float',
                            'string',
                            'boolean',
                            'void',
                            'ifExpr',
                            'forExpr',
                            'withExpr',
                            'taggedExpr',
                            'unaryExpr',
                            'propertyExpr',
                            'multExpr',
                            'addExpr',
                            'compExpr',
                            'notExpr',
                            'andExpr',
                            'orExpr',
                            'blockExpr',
                            'functionReference']
    
    def _walk_for_iterable(self, parseRes, part_name, file_num, var_defs=None, all_expr=None):
        '''This walk:
            1 - if an expression can produce a singleton value or a multiple values
            2 - if an expression can produce a single alignment or multiple alignments
            3 - what are the upstream variables that are used in the expression
        '''
        pre_calc = []  
        top = False
        
        if 'number' not in parseRes:
            if var_defs is None:
                var_defs = {}
            if all_expr is None:
                all_expr = set()
                top = True
                          
            current_part = parseRes.getName()

            if current_part == 'forExpr':
                #add the for control to the forBodyExpr
                parseRes.forBodyExpr['forControl'] = parseRes.forControl

            #descend
            descendant_number = 'single'
            descendant_has_alignment = False
            descendant_var_refs = set()
            descendant_is_dependent = False
            descendant_dependent_vars = set()
            descendant_dependent_iterables = set()
            descendant_downstream_iterables = set()
            
            for next_part in parseRes:
                if isinstance(next_part, ParseResults):
                    descendent_pre_calc = self._walk_for_iterable(next_part, part_name, file_num, var_defs, all_expr)
                    if next_part.number == 'multi':
                        descendant_number = 'multi'
                    if next_part.has_alignment == True:
                        descendant_has_alignment = True
                    if next_part.is_dependent == True:
                        descendant_is_dependent = True
                    descendant_var_refs |= next_part.var_refs
                    descendant_dependent_vars |= next_part.dependent_vars
                    descendant_dependent_iterables |= next_part.dependent_iterables
                    descendant_downstream_iterables |= next_part.downstream_iterables
                    pre_calc += descendent_pre_calc
            
            #defaults
            parseRes['var_refs'] = descendant_var_refs
            parseRes['number'] = descendant_number
            parseRes['has_alignment'] = descendant_has_alignment
            parseRes['is_dependent'] = descendant_is_dependent
            parseRes['dependent_vars'] = descendant_dependent_vars
            parseRes['dependent_iterables'] = descendant_dependent_iterables
            parseRes['downstream_iterables'] = descendant_downstream_iterables
            
            if current_part == 'factset':
                parseRes['number'] = 'multi'
                parseRes['has_alignment'] = True
                remove_refs = set()
                
                factset_var_def_ids = [parseRes.whereExpr.node_id] if 'whereExpr' in parseRes else []
                if 'aspectFilters' in parseRes:
                    factset_var_def_ids += [aspectFilter.node_id for aspectFilter in parseRes.aspectFilters]

                for x in parseRes['var_refs']:
                    #if isinstance(x[0], tuple):
                    
                    if x[0] in factset_var_def_ids:
                        remove_refs.add(x)
                
                parseRes['var_refs'] -= remove_refs
                parseRes['dependent_vars'] -= remove_refs

#                 var_ref_ids = []
#                 if 'aspectFilters' in parseRes:
#                     for aspect_index, aspect_filter in enumerate(parseRes.aspectFilters,1):
#                         if 'aspectVar' in aspect_filter:
#                             var_ref_ids.append((parseRes, aspect_index))
#                 if 'whereExpr' in parseRes:
#                     var_ref_ids.append((parseRes, 0))
# 
#                 parseRes['var_refs'] = {var_ref for var_ref in parseRes.var_refs if var_ref[0] in var_ref_ids}
#                 parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] not in var_ref_ids} 
                
                parseRes['is_iterable'] = True
                
#                 dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                 if len(dependent_vars) == 0:
#                     parseRes['is_dependent'] = False
#                     parseRes['dependent_vars'] = dependent_vars
#                 else:
#                     parseRes['is_dependent'] = True
#                     parseRes['dependent_vars'] = dependent_vars
                #parseRes['is_dependent'] = any([var_defs[x[0]].number == 'multi' for x in parseRes['var_refs']])
                
#             elif current_part == 'forExpr':
#                 parseRes['var_refs'] -= {(parseRes.node_id, parseRes.forVar),}
#                 parseRes['dependent_vars'] -= {(parseRes.node_id, parseRes.forVar),}
            
            #elif current_part == 'whereExpr':
                #reset the dependent iterables. So the only ones will be the iterables from dependent var refs.
                #This is because this expresion is performed in an isolated table
                #parseRes['dependent_iterables'] = set()
            
            elif current_part == 'whereExpr':
                #set as iterable. The whereExpr is never directly evaluated. It is evaluated as part of the factset evaluator. However, it is used as the declaration for
                #the $item variable. So it is set as iterable so that any referenc eto $item will be treated as depending on $item
                #parseRes['is_iterable'] = True
                
                #set the table id
                self.assign_table_id(parseRes, var_defs)
        
#             elif current_part == 'aspectFilter':
#                 parseRes['is_iterable'] = True
        
            elif current_part == 'forExpr':
                '''ALL OF THESE LINES SHOULD BE MOVED INTO THE 'forControl' SECTION'''
#                 parseRes['var_refs'] -= {(parseRes.forControl.node_id, parseRes.forControl.forVar),}
#                 parseRes['dependent_vars'] -= {(parseRes.forControl.node_id, parseRes.forControl.forVar),}  
                parseRes['var_refs'] = {var_ref for var_ref in parseRes.var_refs if var_ref[0] != parseRes.forControl.node_id}
                #parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] != parseRes.forControl.node_id}
                
#                 parseRes['number'] = 'multi'
#                 parseRes['is_iterable'] = True
#                 dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                 if len(dependent_vars) == 0:
#                     parseRes['is_dependent'] = False
#                     parseRes['dependent_vars'] = dependent_vars
#                 else:
#                     parseRes['is_dependent'] = True
#                     parseRes['dependent_vars'] = dependent_vars

                #parseRes.forControl.dependent_iterables |= {parseRes.forControl.forLoopExpr}
            elif current_part == 'forBodyExpr':
                parseRes['number'] = 'multi'
                parseRes['is_iterable'] = True
                
                var_ref_ids = [var_ref[0] for var_ref in parseRes.var_refs]
                if parseRes.forControl.node_id in var_ref_ids:
                    parseRes.var_refs.update(parseRes.forControl.var_refs)
                
                
                #set table ids
                self.assign_table_id(parseRes, var_defs, override_node_id=parseRes.node_id)     
                
#                 #mark all the downstream iterables as being in a loop
#                 for it in parseRes.downstream_iterables:
#                     it['in_loop'] = True
#             elif current_part == 'forControl':
#                 #This is marked as iterable so that anything using the for control variable will be dependent on the for control expression.
#                 parseRes['number'] = 'multi'
#                 parseRes['is_iterable'] = True
# #                 dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
# #                 if len(dependent_vars) == 0:
# #                     parseRes['is_dependent'] = False
# #                     parseRes['dependent_vars'] = dependent_vars
# #                 else:
# #                     parseRes['is_dependent'] = True
# #                     parseRes['dependent_vars'] = dependent_vars
#                     
# #             elif current_part == 'forLoop':
# #                 parseRes['number'] = 'multi'
# #                 parseRes['is_iterable'] = True
# #                 dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
# #                 if len(dependent_vars) == 0:
# #                     parseRes['is_dependent'] = False
# #                     parseRes['dependent_vars'] = dependent_vars
# #                 else:
# #                     parseRes['is_dependent'] = True
# #                     parseRes['dependent_vars'] = dependent_vars
# #                 parseRes['is_dependent'] = any([var_defs[x[0]].number == 'multi' for x in parseRes['var_refs']])


            elif current_part == "ifExpr":
                condition_dependent_vars = self.get_dependent_vars(parseRes.condition, var_defs)
                condition_iterables = parseRes.condition.downstream_iterables | self.get_dependent_var_iterables(parseRes.condition, condition_dependent_vars, var_defs)
                #update the iterables in the then expression
                if len(condition_iterables)> 0:
                    for iterable_expr in parseRes.thenExpr.downstream_iterables:
                        iterable_expr.dependent_iterables.update(condition_iterables)
                
                #update the else if conditions
                for elseIfExpr in parseRes:
                    if elseIfExpr.getName() == 'elseIfExpr':
                        condition_dependent_vars = self.get_dependent_vars(elseIfExpr.condition, var_defs)
                        condition_iterables.update(elseIfExpr.condition.downstream_iterables | self.get_dependent_var_iterables(elseIfExpr.condition, condition_dependent_vars, var_defs))
                        if len(condition_iterables) > 0:
                            for iterable_expr in elseIfExpr.thenExpr.downstream_iterables:
                                iterable_expr.dependent_iterables.update(condition_iterables)
                
                #update the else
                for iterable_expr in parseRes.elseExpr.downstream_iterables:
                    iterable_expr.dependent_iterables.update(condition_iterables)
                
#             elif current_part == 'ifExpr':# or current_part == 'elseIfExpr':
#                 previous_dependent_condition_iterables = set()
#                 #update the iterables in the then expression of the 'if' statement
#                 if parseRes.condition.number == 'multi':
#                     previous_dependent_condition_iterables.update(parseRes.condition.downstream_iterables)
#                     #print("condition iteralbs", [x.node_id for x in previous_dependent_condition_iterables])
#                     for iterable_expr in parseRes.thenExpr.downstream_iterables:
#                         #print("downstream", iterable_expr.node_id)
#                         iterable_expr.dependent_iterables.update(previous_dependent_condition_iterables)
#                 #go through each else if expression
#                 for elseIfExpr in parseRes:
#                     if elseIfExpr.getName() == 'elseIfExpr':
#                         #update the iterables in the condition
#                         for iterable_expr in elseIfExpr.condition.downstream_iterables:
#                             iterable_expr.dependent_iterables.update(previous_dependent_condition_iterables)
#                         previous_dependent_condition_iterables.update(elseIfExpr.condition.dependent_iterables)
#                         #udpate the iterables in the then expression
#                         for iterable_expr in elseIfExpr.thenExpr.downstream_iterables:
#                             iterable_expr.dependent_iterables.update(previous_dependent_condition_iterables)
#                 #update the iterables in the else expression
#                 for iterable_expr in parseRes.elseExpr.downstream_iterables:
#                     iterable_expr.dependent_iterables.update(previous_dependent_condition_iterables)
#                 
#        
#                 '''
#                 if parseRes.condition.number == 'multi':
#                     for dep_expr in parseRes.thenExpr.dependent_iterables | (parseRes.elseExpr.dependent_iterables if 'elseExpr' in parseRes else set()):
#                         dep_expr.dependent_iterables.update(parseRes.condition.dependent_iterables)
#                         
#                 #Each elseIfExpr condidtion is dependent and any previous condition.
#                 if current_part == 'ifExpr':
#                     #seed with the first if condition dependent iterables.
#                     previous_dependent_condition_iterables = parseRes.condition.dependent_iterables
#                     for elseIfExpr in parseRes:
#                         if isinstance(elseIfExpr, ParseResults):
#                             if elseIfExpr.getName() == 'elseIfExpr':
#                                 for dep_expr in elseIfExpr.dependent_iterables:
#                                     dep_expr.dependent_iterables.update(previous_dependent_condition_iterables)
#                                 previous_dependent_condition_iterables.
# 
# 
# 
#                                 elseIfExpr.dependent_iterables.update(previous_dependent_condition_iterables)
#                                 previous_dependent_condition_iterables.update = elseIfExpr.dependent_iterables
#                 '''
            
            elif current_part == 'functionReference':
                if parseRes.functionName in self.catalog['functions'] and parseRes.functionName not in BUILTIN_FUNCTIONS:
                    #Xule defined function
                    parseRes['function_type'] = 'xule_defined'
                    func_expr, func_info = self.getFunction(parseRes.functionName)
                    self._walk_for_iterable(func_expr, parseRes.functionName, func_info['file'], var_defs, all_expr)
                    if func_expr.number == 'multi' or descendant_number == 'multi':
                        parseRes['number'] = 'multi'
                        parseRes['is_iterable'] = True
                        #reset the dependent iterables. So the only ones will be itself and the iterables from dependent var refs.
                        #This is because this expresion is performed in an isolated table
                        #parseRes['dependent_iterables'] = set()
#                         dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                         if len(dependent_vars) == 0:
#                             parseRes['is_dependent'] = False
#                             parseRes['dependent_vars'] = dependent_vars
#                         else:
#                             parseRes['is_dependent'] = True
#                             parseRes['dependent_vars'] = dependent_vars
                    else:
                        parseRes['number'] = 'single'
                    parseRes['has_alignment'] = func_expr.has_alignment or descendant_has_alignment
                    #parseRes['dependent_iterables'] |= {(parseRes.node_id,) + di for di in func_expr.dependent_iterables}
                    
                    if len( parseRes.downstream_iterables) == 0:
                        parseRes['cacheable'] = True
                    
                    #set table ids
                    #self.assign_table_id(parseRes, var_defs, override_node_id=func_expr.node_id)

                else:
                    #otherwise it is a built in function
                    if parseRes.functionName in BUILTIN_FUNCTIONS:
                        if BUILTIN_FUNCTIONS[parseRes.functionName][0] == 'aggregate':
                            parseRes['function_type'] = 'aggregation'
                            parseRes['cacheable'] = True
                            #aggregation is a special case. If the arguments are not alignable, then the aggregation will always colapse into a single result.
                            if descendant_has_alignment == False:
                                parseRes['number'] = 'single'
                                parseRes['has_alignment'] = False
                            else:
                                parseRes['number'] = 'multi'
                                parseRes['has_alignment'] = True
                            
                            parseRes['is_iterable'] = True
                            #reset the dependent iterables. So the only ones will be itself and the iterables from dependent var refs.
                            #This is because this expresion is performed in an isolated table
                            #parseRes['dependent_iterables'] = set()
#                             dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                             if len(dependent_vars) == 0:
#                                 parseRes['is_dependent'] = False
#                                 parseRes['dependent_vars'] = dependent_vars
#                             else:
#     #                             '''This wsa an attempt to appropiately deterime if an aggregate function is dependent or not. However, rule 14988 (roll forward) did not work correctly after
#     #                                this change. This change was meant to correct a rule like:
#     #                                    a = Assets[period=*];
#     #                                    count($a)
#     #                                Currently this would give a series of '1' values for the count even when there are more than one value for the same alignment (exlcuding period).
#     #                                If the variable isn't used, "count(Assets[period=*])" the value is correct (for an mgm filing the value was '2'). 
#     #                                
#     #                                At this time, we are accepting the difference between using the variable and not using the variable. I am leaving this comment in case this decision
#     #                                changes.'''
#     #                             #an aggregation function is only dependent if the expression of the argument is dependent. This is a bit differenct than other dependencies.
#     #                             is_dependent = False
#     #                             for var in dependent_vars:
#     #                                 if var_defs[var[0]].is_dependent:
#     #                                     is_dependent = True
#     #                             if is_dependent:
#     #                                 parseRes['is_dependent'] = True
#     #                                 parseRes['dependent_vars'] = dependent_vars
#     #                             else:
#     #                                 parseRes['is_dependent'] = False
#     #                                 parseRes['dependent_vars'] = set()
#                                  
#                                 parseRes['is_dependent'] = True
#                                 parseRes['dependent_vars'] = dependent_vars
                                
                            #set the table ids
                            self.assign_table_id(parseRes, var_defs)    
                        elif BUILTIN_FUNCTIONS[parseRes.functionName][1] == 'multi':
                            parseRes['function_type'] = 'builtin'
                            parseRes['number'] = 'multi'
                            parseRes['has_alignment'] = True
                            parseRes['is_iterable'] = True
#                             
#                             dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                             if len(dependent_vars) == 0:
#                                 parseRes['is_dependent'] = False
#                                 parseRes['dependent_vars'] = dependent_vars
#                             else:
#                                 parseRes['is_dependent'] = True
#                                 parseRes['dependent_vars'] = dependent_vars
                            
                        #all other built in functions use the defaults
            elif current_part == 'functionDeclaration':
#                 for arg in parseRes.functionArgs:
#                     parseRes['var_refs'] -= {(arg.node_id, arg.argName),} 
#                     parseRes['dependent_vars'] -= {(arg.node_id, arg.argName),}           
                arg_node_ids = [arg.node_id for arg in parseRes.functionArgs]
                parseRes['var_refs'] = {var_ref for var_ref in parseRes.var_refs if var_ref[0] not in arg_node_ids}
                #parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] not in arg_node_ids}                    
            elif current_part == 'macroDeclaration':
#                 for arg in parseRes.macroArgs:
#                     parseRes['var_refs'] -= {(arg.node_id, arg.argname),} 
#                     parseRes['dependent_vars'] -= {(arg.node_id, arg.argname),}
                arg_node_ids = [arg.node_id for arg in parseRes.macroArgs]
                parseRes['var_refs'] = {var_ref for var_ref in parseRes.var_refs if var_ref[0] not in arg_node_ids}
                #parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] not in arg_node_ids}                        
                    
            elif current_part == 'varRef':
                #var_ref tuple: 0 = var declaration id, 1 = var name, 2 = var ref ast, 3 = var type (1=block variable or 'for' variable, 2=constant, 3=function argument, factset variable)
                if parseRes.is_constant:
                    const_info = self.catalog['constants'][parseRes.varName]
                    const_expr = self.getItem(const_info['file'], const_info['index'])
                    self._walk_for_iterable(const_expr, parseRes.varName, const_info['file'], var_defs, all_expr)
                    parseRes['var_declaration'] = const_expr.node_id
                    parseRes['number'] = const_expr.number
                    parseRes['has_alignment'] = const_expr.has_alignment
                    #save the declaration parse result object
                    var_defs[const_expr.node_id] = const_expr
                    parseRes['var_refs'] = {(parseRes.var_declaration, parseRes.varName, parseRes, 2),}
                    
#                     #if the constant creates iterations, then it needs to be added to the list of dependent iterables
#                     if const_expr.number == 'multi':                
#                         parseRes['is_iterable'] = True        
#                         parseRes['dependent_vars'] = set()
#                         #parseRes['dependent_iterables'].add(parseRes)
                else:
                    var_expr = self._var_exprs.get(parseRes.var_declaration)
                    if var_expr is not None:
                        self._walk_for_iterable(var_expr, part_name, file_num, var_defs, all_expr)
                        parseRes['number'] = var_expr.number
                        parseRes['has_alignment'] = var_expr.has_alignment
                        #save the declaration parse result object
                        var_defs[parseRes.var_declaration] = var_expr
                        parseRes['var_refs'] = {(parseRes.var_declaration, parseRes.varName, parseRes, 1),}
                        
#                         if var_expr.getName() == 'forControl':
#                             parseRes['downstream_iterables'] |= {var_expr,}
                    
                        #The dependent iterables of variable declaration are added tot he variable reference. This way anything that uses the variables
                        #will be dependent on the what the variable declaration is dependent on
                        parseRes['dependent_iterables'].update(var_expr.dependent_iterables)
                    else:
                        parseRes['var_refs'] = {(parseRes.var_declaration, parseRes.varName, parseRes, 3),}
                        #function declaration arguments - in this case the number and alignment are unknown because it is based 
                        #on what is passed in the function reference. Just use the default values.
                        #parseRes['number'] = 'single'
                        #parseRes['has_alignment'] = False
            
            elif current_part == 'withExpr':
                parseRes['number'] = 'multi'
                parseRes['has_alignment'] = True
                parseRes['is_iterable'] = True
                #reset the dependent iterables. So the only ones will be itself and the iterables from dependent var refs.
                #This is because this expresion is performed in an isolated table
                #parseRes['dependent_iterables'] = set()

#                 dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                 if len(dependent_vars) == 0:
#                     parseRes['is_dependent'] = False
#                     parseRes['dependent_vars'] = dependent_vars
#                 else:
#                     parseRes['is_dependent'] = True
#                     parseRes['dependent_vars'] = dependent_vars
                
                #set the table id
                self.assign_table_id(parseRes.expr[0], var_defs, override_node_id=parseRes.node_id)
                                      
            elif current_part == 'valuesExpr':
                parseRes['has_alignment'] = False #alignment is lost in the values expression    
                parseRes[0]['values_expression'] = True
                 
#                 if parseRes[0].getName() == 'taggedExpr':
#                     parseRes[0].expr[0]['values_expression'] = True
#                 else:     
#                     parseRes[0]['values_expression'] = True
                
                
#                 #the expression is a var ref to a constant.
#                 if parseRes[0].getName() == 'varRef':
#                     
#                     parseRes['is_iterable'] = True
#                     parseRes['is_dependent'] = False
#                     parseRes['dependent_vars'] = set()
#                     parseRes['var_refs'] = set()
#                 #otherwise - the values is infront of an iterable expression.

            elif current_part == 'blockExpr':

                
                var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
#                 for var_assign in var_assignments:
#                     parseRes['var_refs'] -= {(var_assign.node_id, var_assign.varName),}
#                     parseRes['dependent_vars'] -= {(var_assign.node_id, var_assign.varName),}
                #check if the variable is used
                var_ref_ids = {var_ref[0] for var_ref in parseRes.var_refs}
                for var_assign in var_assignments:
                    if var_assign.node_id not in var_ref_ids:
                        var_assign['not_used'] = True
                
                #removed defined variables from the var_refs and dependent vars
                var_assign_ids = [var_assign.node_id for var_assign in var_assignments]
                parseRes['var_refs'] = {var_ref for var_ref in parseRes.var_refs if var_ref[0] not in var_assign_ids}
                #parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] not in var_assign_ids}                       
                
#             elif current_part == 'formulaDeclaration':
#                 if 'varAssigns' in parseRes:
#                     for var_assign in parseRes.varAssigns:
#                         
#                         parseRes['var_refs'] -= {(var_assign.node_id, var_assign.varName),}
#                         parseRes['dependent_vars'] -= {(var_assign.node_id, var_assign.varName),}
            elif current_part == 'qName':
                #find the namespace uri for the prefix
                parseRes['namespace_uri'] = self.getNamespaceUri(parseRes.prefix, file_num)

            elif current_part == 'constantAssign':
                if parseRes.number == 'multi':
                    parseRes['is_iterable'] = True
#                     dependent_vars = {x for x in parseRes['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi'}
#                     if len(dependent_vars) == 0:
#                         parseRes['is_dependent'] = False
#                         parseRes['dependent_vars'] = dependent_vars
#                     else:
#                         parseRes['is_dependent'] = True
#                         parseRes['dependent_vars'] = dependent_vars

#             if not pre_calc and not parseRes.get('instance') and current_part in self._PRE_CALC_EXPRESSIONS:
#                 self.catalog['pre_calc_expressions'].append(parseRes)
#                 pre_calc = True
            
            #set the table id for the iterables under the top level node. 
            if current_part in ('raiseDeclaration', 'reportDeclaration', 'formulaDeclaration', 'functionDeclaration', 'constantAssign', 'preconditionDeclaration'):
                self.assign_table_id(parseRes, var_defs)
#                 print(current_part, parseRes.node_id)
#                 for it in parseRes.downstream_iterables:
#                     if 'table_id' not in it:
#                         it['table_id'] = parseRes.node_id 
                #assign table id to variable references to constants.
                for var_ref in parseRes.var_refs:
                    #if len(var_ref) == 3: #this is a variable reference to a constant
                    if var_ref[3] == 2: #this is reference to a constant
                        if 'table_id' not in var_ref[2]:
                            var_ref[2]['table_id'] = parseRes.node_id

            #Update the dependant iteratables
            if 'is_iterable' in parseRes:
                #set dependent variables
                dependent_vars = self.get_dependent_vars(parseRes, var_defs)
                if len(dependent_vars) == 0:
                    #parseRes['is_dependent'] = False
                    parseRes['dependent_vars'] = dependent_vars
                else:
                    #parseRes['is_dependent'] = True
                    parseRes['dependent_vars'] = dependent_vars
                    
                parseRes['downstream_iterables'].add(parseRes)
                    
                #reset the dependent_iterables. The iterable will not include downstream dependencies which is what the dependent_iterables currently contains.
                parseRes['dependent_iterables'] = set()
                parseRes['dependent_iterables'].add(parseRes)
#                 if current_part == 'forControl':
#                     parseRes['dependent_iterables'] |= control_dependent_iterables
                #add iterables from the expresions for variable refs, but only if the expressions is upstream
                additional_dependent_iterables = self.get_dependent_var_iterables(parseRes, dependent_vars, var_defs)
                parseRes['dependent_iterables'] |= additional_dependent_iterables
                
                #add downstream iterables for fucntion references. This makes the function reference dependent on the iterables in the arguments.
                #This is needed when passing iterables (i.e. factset) in the argument.
                if current_part == 'functionReference' and parseRes.function_type == 'xule_defined':
                    parseRes['dependent_iterables'] |= parseRes.functionArgs.downstream_iterables

                parseRes['is_dependent'] = len(parseRes.dependent_iterables) > 1 #The dependent_iterables list will always include itself, so the miniumn count is 1

#                
#                 if current_part != 'constantAssign':
#                     #constantAssign expressions are never dependent.
#                     for var in parseRes.dependent_vars:
#                         var_def_expr = var_defs[var[0]]
#                         if var_def_expr.getName() == 'constantAssign':
#                             parseRes['dependent_iterables'] |= {var_def_expr,}
#                         else:
#                             #the variable has to be assigned upstream                    
#                             if var_def_expr.node_id < parseRes.node_id:
#                                 if var_def_expr.getName() == 'forControl':
#                                     parseRes['dependent_iterables'] |= {var_def_expr,}
#                                 else:
#                                     if 'dependent_iterables' in var_def_expr:
#                                         parseRes['dependent_iterables'] |= var_def_expr.dependent_iterables
            
#             '''THIS CAN PROBABLY BE REMOVED - THE PRE CALC CACHE IS NOT BEING USED ANYMORE. CAUSE SIGNIFICANT MEMORY ISSUES'''
#             if not parseRes.get('instance') and current_part in self._PRE_CALC_EXPRESSIONS:
#                 #verify that only upstream constants are allowed.
#                 #if all([len(var_ref) == 3 for var_ref in parseRes.var_refs]):
#                 if all([var_ref[3] == 2 for var_ref in parseRes.var_refs]):
#                     for pre_calc_node in pre_calc:
#                         self.catalog['pre_calc_expressions'].remove(pre_calc_node)
# 
#                     self.catalog['pre_calc_expressions'].append(parseRes.node_id)
#                     pre_calc = [parseRes.node_id,]

#             if top:
#                 print('CLEANING')
#                 #Do a little cleaning up
#                 for expr in all_expr:
#                     print(expr.node_id)
#                     if 'is_iterable' in expr:
#                         expr.dependent_iterables.discard(expr.node_id)
#                     else:
#                         del expr['dependent_iterables']
#             else:
#                 all_expr.add(parseRes)      
        
        return pre_calc
    
    def get_dependent_vars(self, rule_part, var_defs):
        return {x for x in rule_part['var_refs'] if x[0] in var_defs if var_defs[x[0]].number == 'multi' or var_defs[x[0]].is_dependent}
    
    def get_dependent_var_iterables(self, rule_part, dependent_vars, var_defs):
        
        additional_iterables = set()

        #for body expressions - add the dependent iterables in the control.       
        if rule_part.getName() == 'forBodyExpr':
            additional_iterables.update(rule_part.forControl.forLoopExpr.dependent_iterables)
        
        if rule_part.getName() != 'constantAssign':
            #constantAssign expressions are never dependent.
            for var in dependent_vars:
                var_def_expr = var_defs[var[0]]
                if var_def_expr.getName() == 'constantAssign':
                    additional_iterables.add(var_def_expr)
                else:
                    #the variable has to be assigned upstream   
                    if var_def_expr.node_id < rule_part.node_id:
#                         if 'dependent_iterables' in var_def_expr:
#                             additional_iterables.update(var_def_expr.dependent_iterables)
                        if var_def_expr.getName() in ('forControl', 'aspectFilter', 'whereExpr'):
                            additional_iterables.add(var_def_expr)
                        else:
                            if 'dependent_iterables' in var_def_expr:
                                additional_iterables.update(var_def_expr.dependent_iterables)

        return additional_iterables

    def assign_table_id(self, rule_part, var_defs, override_node_id=None):
        node_id = override_node_id or rule_part.node_id
        for it in rule_part.downstream_iterables:
            if 'table_id' not in it:
                it['table_id'] = node_id                

    def build_dependencies(self):
        
        #immediate dependencies
        for const_info in self.catalog['constants'].values():
            self.dependencies_top(const_info)
        for func_info in self.catalog['functions'].values():
            self.dependencies_top(func_info)
        for macro_info in self.catalog['macros'].values():
            self.dependencies_top(macro_info)
        for rule_info in self.catalog['rules'].values():
            self.dependencies_top(rule_info)        
        for precondition_info in self.catalog['preconditions'].values():
            self.dependencies_top(precondition_info)      
               
        '''
        #immediate dependencies
        for const_info in self.catalog['constants'].values():
            const_info['immediate_dependencies'] = self._immediate_dependencies(self.getItem(const_info['file'], const_info['index']))
        for func_info in self.catalog['functions'].values():
            func_info['immediate_dependencies'] = self._immediate_dependencies(self.getItem(func_info['file'], func_info['index']))
        for macro_info in self.catalog['macros'].values():
            macro_info['immediate_dependencies'] = self._immediate_dependencies(self.getItem(macro_info['file'], macro_info['index']))
        for rule_info in self.catalog['rules'].values():
            rule_info['immediate_dependencies'] = self._immediate_dependencies(self.getItem(rule_info['file'], rule_info['index']))
        
        #all dependencies
        for const_info in self.catalog['constants'].values():
            self._get_all_dependencies(const_info)
            
        for func_info in self.catalog['functions'].values():
            self._get_all_dependencies(func_info)
            
        for macro_info in self.catalog['macros'].values():
            self._get_all_dependencies(macro_info)
            
        for rule_info in self.catalog['rules'].values():
            self._get_all_dependencies(rule_info)
        '''
            
        #check if constants are used
        used_constants = set()
        for rule_info in self.catalog['rules'].values():
            for const_name in rule_info['dependencies']['constants']:
                used_constants.add(const_name)
        
        for function_info in self.catalog['functions'].values():
            for const_name in function_info['dependencies']['constants']:
                used_constants.add(const_name) 
   
        for precondition_info in self.catalog['preconditions'].values():
            for const_name in precondition_info['dependencies']['constants']:
                used_constants.add(const_name)                               
        
        #if a constant is used only by a constant (as long as that constant was used)
        constant_of_constants = set()
        for used_constant in used_constants:
            for const_name in self.catalog['constants'][used_constant]:
                constant_of_constants.add(const_name)
        used_constants -= constant_of_constants

        unused_constants = set(self.catalog['constants'].keys()) - used_constants
        for const_name in unused_constants:
            self.catalog['constants'][const_name]['unused'] = True          

        #Check if a precondition is used
        used_preconditions = set()
        for rule_info in self.catalog['rules'].values():
            used_preconditions.update(set(rule_info['preconditions']))
        for precon in set(self.catalog['preconditions'].keys()) - used_preconditions:
            self.catalog['preconditions'][precon]['unused'] = True


        #determine number (single, multi) for each expression
        for const_name, const_info in self.catalog['constants'].items():
            self._walk_for_iterable(self.getItem(const_info['file'], const_info['index']), const_name, const_info['file'])
        for precon_name, precon_info in self.catalog['preconditions'].items():    
            self._walk_for_iterable(self.getItem(precon_info['file'], precon_info['index']), precon_name, precon_info['file'])            
        for func_name, func_info in self.catalog['functions'].items():
            self._walk_for_iterable(self.getItem(func_info['file'], func_info['index']), func_name, func_info['file'])
        for macro_name, macro_info in self.catalog['macros'].items():
            self._walk_for_iterable(self.getItem(macro_info['file'], macro_info['index']), macro_name, macro_info['file'])
        for rule_name, rule_info in self.catalog['rules'].items():
            ast_rule = self.getItem(rule_info['file'], rule_info['index'])
            self._walk_for_iterable(ast_rule, rule_name, rule_info['file'])
#             if ast_rule.expr[0].getName() == 'factset':
#                 factset = ast_rule.expr[0]
#                 #for concept[]
#                 if 'lineItemAspect' in factset:
#                     ast_rule['pre_check'] = factset.lineItemAspect.qName
#                 else:
#                     #for [lineItem = ]
#                     if 'aspectFilters' in factset:
#                         for aspect_filter in factset.aspectFilters:
#                             if (aspect_filter.aspectName.qName.prefix == "*" and
#                                 aspect_filter.aspectName.qName.localName == 'lineItem'):
#                                 if aspect_filter.aspectOperator == "=":
#                                     if aspect_filter.aspectExpr[0].getName() == 'qName':
#                                         ast_rule['pre_check'] = aspect_filter.aspectExpr[0]

        self.catalog['pre_calc_expressions'].sort()
        
        self._cleanup_ruleset()

    def _cleanup_ruleset(self):
        '''This function removes parseRes properties that were added during the post parse procesing that are not needed for processing. This includes:
            number, dependent_vars, dependent_iterables (except for iterables) and downstream_iterables
        '''
        for parseRes in self._pickles.values():
            self._cleanup_ruleset_detail(parseRes)
    
    def _cleanup_ruleset_detail(self, parseRes):
        for prop in ('number', 'dependent_vars', 'downstream_iterables'):
            if prop in parseRes:
                del parseRes[prop]
        if 'dependent_iterables' in parseRes and parseRes.get('is_iterable') != True:
            del parseRes['dependent_iterables']
        
        for child_parseRes in parseRes:
            if isinstance(child_parseRes, ParseResults):
                self._cleanup_ruleset_detail(child_parseRes)
            
    
    def _get_all_dependencies(self, info):
        
        if 'dependencies' in info:
            return

        dependencies = {'constants': set(),
                        'functions': set(),
                        'instance': False,
                        'rules-taxonomy': False,
                        }
         
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
        #base['number'] = base['number'] + additional['number']

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
                
    def open(self, ruleSetLocation, open_for_add=True):
        #self.name = os.path.splitext(os.path.basename(ruleSetLocation))[0]
        self.location = ruleSetLocation
        pickle_start = datetime.datetime.today()
        try:
            with open(os.path.join(ruleSetLocation,"catalog.pik"),"rb") as i:
                self.catalog = pickle.load(i)
            self.name = self.catalog['name']
            self._openForAdd = open_for_add
        except FileNotFoundError:
            print("Cannot open catalog.")
            raise
        
        if not open_for_add:
            for file_info in self.catalog['files']:
                self.getFile(file_info['file'])
                
        pickle_end = datetime.datetime.today()
        print("Rule Set Loaded", pickle_end - pickle_start)
        
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
            
            
            self.getFile(file_num)
#             if file_num not in self._pickles.keys():
#                 #get the file info from the catalog
#                 file_item = next((file_item for file_item in self.catalog['files'] if file_item['file'] == file_num), None)
#                 if not file_item:
#                     raise XuleRuleSetError("File number %s not found" % str(file_num))
#                     return
#                 
#                 try:
#                     pickle_start = datetime.datetime.today()
#                     with open(os.path.join(self.location, file_item['pickle_name']),"rb") as p:
#                         self._pickles[file_num] = pickle.load(p, encoding="utf8")
#                     pickle_end = datetime.datetime.today()
#                     print("Opening pickle file", file_item['pickle_name'], file_item['name'], pickle_end - pickle_start)
#                 except FileNotFoundError:
#                     raise XuleRuleSetError("Pickle file %s not found." % file_item['pickle_name'])
#                     return
                
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
            raise XuleRuleSetError("%s not found in the catalog." % name)
            return
        
        return (self.getItem(item['file'], item['index']), item)
    
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
            raise XuleRuleSetError("Prefix %s is not declared in file %s" % (prefix, str(file_num)))
        
        return self.catalog['namespaces'][file_num][prefix]['uri']
        
    def getNamespaceInfoByUri(self, namespaceUri, file_num):
        if file_num not in self.catalog['namespaces']:
            return
        
        for namespace_info in self.catalog['namespaces'][file_num].values():
            if namespace_info['uri'] == namespaceUri:
                return namespace_info
        
        return
        
#     def getNodeById(self, node_id):
#         location = self.catalog['node_index'].get(node_id)
#         if location is None:
#             raise XuleRuleSet("Node id %i not found in node index" % node_id)
#         
#         file_num = location[0]
#         self.getFile(file_num)
#         parent = self._pickles[file_num]
#         for step in location[1:]:
#             parent = parent[step]
#         
#         return parent        
    
    def addTaxonomy(self, taxonomy_location, entry_point):
        if self._openForAdd == True:
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
        else:
            raise XuleRuleSetError(_("Attempting to add taxonomy but the rule set is not open for add"))
            
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

                
#     def findnode(mylist, value):
#         ''' returns the node for the value in mylist where 
#             mylist is an llist.sllist 
#         '''
#         x = -1
#         for num in range(len(mylist)):
#             if mylist[num] == value:
#                 x = num
#                 break
#         return mylist.nodeat(x) if x != -1 else None                
                        
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



