"""XuleRuleSetBuilder

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2022 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23211 $
DOCSKIP
"""
import pickle
import os
import shutil
import collections
import datetime
import json
import zipfile
import tempfile
from . import XuleFunctions as xf
from . import XuleRuleSet as xr
from . import XuleUtility as xu

PARSER_FILES = tuple(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__), x)) 
                        for x in ('XuleRuleSetBuilder.py', 'XuleRuleSet.py', 'XuleParser.py', 'xule_grammar.py'))

class JSONEncoderForSet(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        else:
            return json.JSONEncoder.encode(self, obj)

class XuleRuleSetBuilder(xr.XuleRuleSet):
    
    def __init__(self, compile_type, cntlr=None):
        self._compile_type = compile_type
        self._file_status = {}
        self._open_for_add = False
        self.recompile_all = False
        super().__init__(cntlr)
    
    def markFileKeep(self, file_name):
        file_info = self.getFileInfoByName(file_name)
        self._file_status[file_info['file']] = 'keep'
        self._top_level_analysis(self._xule_file_expression_trees[file_info['file']], file_info['file'])
    
    def add(self, parse_tree, file_time=None, file_name=None, file_hash=None):
        """Add a parsed Xule rule file to the ruleset.
        
        This adds a file to the ruleset. When the file is added the catalog is updated with the top level components.
        
        Arguments:
            parse_tree (dictionary): AST of the rule file
            file_time (number): The modify time of the original Xule rule file. See os.path.getmtime()
            file_name (string): The base name of the Xule rule file.
        """
        if self._open_for_add == False:
            raise xr.XuleRuleSetError(_("Attempting to add rule file, but rule set is not open for add"))
        
        file_num = self._addXuleFile(file_time, file_name, file_hash)
    
        self._top_level_analysis(parse_tree, file_num)

    def new(self, location):
        """Create a new ruleset
        
        This will establish the directory of the ruleset.
        
        Arguments:
            location (string): directory for the new ruleset
        """
        
        #check if the ruleset is already opened.
        if self._open_for_add:
            raise xr.XuleRuleSetError("Trying to create a new rule set in an open rule set.")
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
                            "version": None,
                            "xule_compiled_version": xu.version(PARSER_FILES)
                            }
            
            self._open_for_add = True
    
    def append(self, location):
        try:
            self.open(location)
        except FileNotFoundError:
            self.new(location)
            
    def open(self, ruleSetLocation):

        try:
            super().open(ruleSetLocation, open_packages=False)
        except xr.XuleRuleCompatibilityError:
            self.recompile_all = True
            print("Due to rule set incompatibility, recompiling all files")
        self._open_for_add = True

        #clear out the catalog. This will be rebuilt as files are added.
        self.catalog['namespaces'] = {}
        self.catalog['rules'] = {}
        self.catalog['rules_by_file'] = {}
        self.catalog['functions'] = {}
        self.catalog['constants'] = {}
        self.catalog['output_attributes'] = {}
        self.catalog['version'] = None
        self.catalog['xule_compiled_version'] = xu.version(PARSER_FILES)
    
    def close(self):
        """Close the ruleset"""
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
                if self._compile_type == 'pickle':
                    zf.writestr('catalog', pickle.dumps(self.catalog, protocol=2))
                elif self._compile_type == 'json': 
                    zf.writestr('catalog', json.dumps(self.catalog, cls=JSONEncoderForSet, indent=4))
                else:
                    raise xr.XuleRuleSetError("Unknown compile type: {}.".format(self._compile_type))
                
        self._open_for_add = False
        self._file_status = {}
        
        super().close()
    
    def _top_level_analysis(self, parse_tree, file_num):
        # update the catalog
        namespaces = {}
        rules = {}
        functions = {}
        constants = {}
#         preconditions = {}
        output_attributes = {}
        
        #defaults
        rule_name_prefix = ''
        rule_name_separator = '.'
        
        #assign node_ids
        self.next_id = self._assign_node_ids(parse_tree, self.next_id + 1)
        
        error_in_file = False
        #top level analysis
        for i, cur_node in enumerate(parse_tree['xuleDoc']):
            cur_name = cur_node['exprName']
            cur_node_id = cur_node['node_id']
            
            if cur_name == "nsDeclaration":
                # add to the list of namespaces
                prefix = cur_node.get('prefix', '*')
                if prefix not in namespaces.keys():
                    namespaces[prefix] = {"file": file_num, "index": i, "prefix": prefix, "uri": cur_node['namespaceURI']}
                else:
                    #duplicate namespace prefix
                    print("Duplicate namespace prefix: %s" % prefix) #, file=stderr)
                    error_in_file = True
                
            elif cur_name == 'outputAttributeDeclaration':
                output_attributes[cur_node['attributeName']] = {"file": file_num, "index": i}
                
            elif cur_name == 'ruleNamePrefix':
                if cur_node['prefix'].lower() == 'none':
                    rule_name_prefix = ''
                else:
                    rule_name_prefix = cur_node['prefix']
                
            elif cur_name == 'ruleNameSeparator':
                #print("SEPARATOR", cur_node['separator'], cur_node['separator'].lower() == 'none')
                if cur_node['separator'].lower() == 'none':
                    rule_name_separator = ''
                else:
                    rule_name_separator = cur_node['separator']                
                
            elif cur_name == "constantDeclaration":
                constants[cur_node['constantName']] = {"file": file_num, "index": i, "node_id": cur_node_id}
                
            elif cur_name == "assertion":
                full_name = ('' if rule_name_prefix == '' else (rule_name_prefix + rule_name_separator)) + cur_node['ruleName']
                cur_node['fullName'] = full_name
                if full_name not in rules.keys():
#                     precon_names =  []                    
#                     if 'preconditionRef' in cur:
#                         precon_names = [name for name in cur.preconditionRef.preconditionNames]
                    rules[full_name] = {"file": file_num, "index": i, "type": "assert", "full_name": full_name}#, "preconditions": precon_names}
                else:
                    print("duplicate rule name: %s" % full_name)
                    error_in_file = True
                    
            elif cur_name == "outputRule":
                full_name = ('' if rule_name_prefix == '' else (rule_name_prefix + rule_name_separator)) + cur_node['ruleName']
                cur_node['fullName'] = full_name
                if full_name not in rules.keys():                   
#                     if 'preconditionRef' in cur:
#                         precon_names = [name for name in cur.preconditionRef.preconditionNames]
                    rules[full_name] = {"file": file_num, "index": i, "type": "output", "full_name": full_name}#, "preconditions": precon_names}
                else:
                    print("duplicate rule name: %s" % full_name)
                    error_in_file = True
                    
            elif cur_name == "functionDeclaration":
                functions[cur_node['functionName']] = {"file": file_num, "index": i}

            elif cur_name == "versionDeclaration":
                if self.catalog.get('version') is None:
                    self.catalog['version'] = cur_node['version']
                elif self.catalog['version'] != cur_node['version']:
                        raise xr.XuleRuleSetError("Duplicate version declarations {} and {}".format(self.catalog['version'], cur_node['version']))
            else:
                error_in_file = True
                raise xr.XuleRuleSetError("Unknown top level parse result: %s" % cur_name)

#         with open(file_name + '_post_parse.json', 'w') as o:
#             import json
#             o.write(json.dumps(parse_tree, indent=4)) 
        
        #self._saveFilePickle(file_num, parseRes)
        self._xule_file_expression_trees[file_num] = parse_tree
            
        #Check for duplicate names
#         self._dup_names(preconditions.keys(), self.catalog['preconditions'].keys())
        error_in_file = self._dup_names(constants.keys(), self.catalog['constants'].keys()) or error_in_file
        error_in_file = self._dup_names(rules.keys(), self.catalog['rules'].keys()) or error_in_file
        error_in_file = self._dup_names(functions.keys(), self.catalog['functions'].keys()) or error_in_file
        error_in_file = self._dup_names(output_attributes.keys(), self.catalog['output_attributes'].keys()) or error_in_file
        error_in_file = self._dup_namespace_declarations(namespaces) or error_in_file
        
        if error_in_file:
            raise xr.XuleRuleSetError("Duplicate names.")
        
        #merge current catalog info into the shelf catalog
        self.catalog['namespaces'].update(namespaces)
        self.catalog['rules_by_file'][file_num] = rules
#         self.catalog['preconditions'].update(preconditions)
        self.catalog['rules'].update(rules)
        self.catalog['constants'].update(constants)
        self.catalog['functions'].update(functions)
        self.catalog['output_attributes'].update(output_attributes)    
                
    def _dup_names(self, one, two):
        """Determine if two sets of names have duplicates.
        
        Arguments:
            one (set): First set
            two (set): Second set
        """
        dups = set(one) & set(two)
        if len(dups) != 0:
            print("duplicate names:") 
            for x in dups:
                print(x) 
            return True
        else:
            return False
                
    def _dup_namespace_declarations(self, new_namespaces):
        """Determine if a new namespace is a duplicate.
        
        This will check the new namespace against the namespaces in the catalog. A duplicate is allowed if the prefix and namespace uri
        are the same. Otherwise, an error is raised.
        
        Arguments:
            new_namespaces (dictionary): A dictionary keyed by prefix of namespace uris
        """
        for prefix, ns in new_namespaces.items():
            if prefix in self.catalog['namespaces']:
                if self.catalog['namespaces'][prefix]['uri'] != ns['uri']:
                    raise xr.XuleRuleSetError("Duplicate namespace prefix with different namespace. Prefix is '%s' - namespaces are %s and %s" 
                                           % (prefix, self.catalog['namespaces'][prefix]['uri'], ns['uri']))
                
    def _assign_node_ids(self, parse_tree, next_id):
        """Add a unique node_id to each of the dictionaries in the AST.
        
        Arguments:
            parse_tree (dictionary): AST of the Xule rule file
            next_id (integer): The next id to be assigned
        """
        if isinstance(parse_tree, dict) or isinstance(parse_tree, list):
            if isinstance(parse_tree, dict):
                next_id += 1
                parse_tree['node_id'] = next_id
                
            children = parse_tree.values() if isinstance(parse_tree, dict) else parse_tree
            for child in children:
                next_id = self._assign_node_ids(child, next_id)
            return next_id       
        else: #neither dict nor list
            return next_id

    def dependencies_top(self, info):
        """Determine which constants and functions are used by an expression.
        
        Also determine if the the expression uses the instance taxonomy or a base taxonomy
        """
        if 'dependencies' not in info:
            ast = self.getItem(info['file'], info['index'])
            dependencies, immediate_dependencies = self.dependencies_detail(ast)
            info['dependencies'] = dependencies
            info['immediate_dependencies'] = immediate_dependencies
        
    def dependencies_detail(self, parse_node, var_names=None, var_exclusions=None):
        
        current_part = parse_node['exprName']
        #initialize the varNames list - this is used to determine if a variable reference is a variable or constant
        if var_names is None:
            var_names = collections.defaultdict(list)
        if var_exclusions is None:
            var_exclusions = []

        if current_part == 'filter':                         
            if 'whereExpr' in parse_node:
                parse_node['whereExpr']['location'] = 'filter'
            if 'returnsExpr' in parse_node:
                parse_node['returnsExpr']['location'] = 'filter'
        if current_part == 'navigation':
            if 'whereExpr' in parse_node:
                parse_node['whereExpr']['location'] = 'navigation'
            if 'stopExpr' in parse_node:
                parse_node['stopExpr']['location'] = 'navigation'

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

        #add variable names
        if current_part == 'blockExpr':
#             var_assignments = [i for i in parseRes if i.getName() == 'varAssign']
#             for var_assign in var_assignments:
#                 var_names[var_assign.varName].append(var_assign)
#                 self._var_exprs[var_assign.node_id] = var_assign.expr[0]    
                    
            for var_decl in parse_node['varDeclarations']:
                var_names[var_decl['varName']].append(var_decl)
                self._var_exprs[var_decl['node_id']] = var_decl['body']
                
            #set up the exclusions. This is so that a variable can only reference variables that come before it.
            exclusion_var_ids = []
            for var_decl in reversed(parse_node['varDeclarations']):
                exclusion_var_ids.append(var_decl['node_id'])
                var_decl['var_exclusion_ids'] = exclusion_var_ids.copy()

        if current_part == 'varDeclaration':
            #When in a var declaration, the current declaration is excluded while traversing down the expression for the variable.
            #This allows $a = 10 $a = $a + 5. The var reference of $a in the second expression is to the first variable declaration.
            #var_exclusions.append(parse_node['node_id'])
            var_exclusions.extend(parse_node['var_exclusion_ids'])

        if current_part == 'forExpr':
            #var_names[parseRes.forVar].append(parseRes)
            var_names[parse_node['forVar']].append(parse_node['forLoopExpr'])
            self._var_exprs[parse_node['forLoopExpr']['node_id']] = parse_node['forLoopExpr']
            
        if current_part == 'factset':
            if 'aspectFilters' in parse_node:
                for aspect_index, aspect_filter in enumerate(parse_node['aspectFilters'],1):
                    if 'alias' in aspect_filter:
                        var_names[aspect_filter['alias']].append(aspect_filter)
            if 'whereExpr' in parse_node:
                var_names['fact'].append(parse_node['whereExpr'])
                #identify that this whereExpr is from a factset. This is needed to identify that this whereExpr is dependant on an instance
                parse_node['whereExpr']['location'] = 'factset'
                
        # if current_part == 'navigation':
        #     if 'whereExpr' in parse_node:
        #         #var_names['relationship'].append(parse_node['whereExpr'])
        #         parse_node['whereExpr']['location'] = 'navigation'
        #     if 'stopExpr' in parse_node:
        #         parse_node['stopExpr']['location'] = 'navigation'
        # if current_part == 'filter':                         
        #     if 'whereExpr' in parse_node:
        #         #var_names['item'].append(parse_node['whereExpr'])
        #         parse_node['whereExpr']['location'] = 'filter'
        #     if 'returnsExpr' in parse_node:
        #         #var_names['item'].append(parse_node['returnsExpr'])
        #         parse_node['returnsExpr']['location'] = 'filter'
        if current_part == 'functionDeclaration':
            for arg in parse_node['functionArgs']:
                var_names[arg['argName']].append(arg)
        
        if parse_node.get('location')  == 'filter':
            var_names['item'].append(parse_node['parent']['expr'])
            
        if parse_node.get('location') == 'navigation':
            var_names['relationship'].append(parse_node)
            
        #dependencies
        if current_part == 'varRef':
            if parse_node['varName'] not in var_names:
                # this must be a constant
                const_info = self.catalog['constants'][parse_node['varName']]
                self.dependencies_top(const_info) 
                self._combine_dependencies(dependencies, const_info['dependencies'])
           
                dependencies['constants'].add(parse_node['varName'])
                immediate_dependencies['constants'].add(parse_node['varName'])
                
                const_expr = self.getItem(const_info['file'], const_info['index'])
                parse_node['var_declaration'] = const_expr['node_id']
                           
                parse_node['is_constant'] = True
            else:
                # this is a variable reference. Find the declaration
                found = False
                for declaration in reversed(var_names[parse_node['varName']]):
                    # The declaration['node_id'] < parse_node['node_id'] is needed so we don't pick up a variable defined later. This can
                    # happen if you have "$a = 10; $a = $a + 15; $a = 5;" The second $a should not pick up the 3rd one. This check prevents that from happening.
                    if declaration['node_id'] not in var_exclusions: # and declaration['node_id'] < parse_node['node_id']:
                        found = True
                        parse_node['var_declaration'] = declaration['node_id']
                        if declaration.get('location') == 'factset' or declaration['exprName'] == 'aspectFilter':
                            dependencies['instance'] = True
                            immediate_dependencies['instance'] = True
                        else:
                            if declaration.get('instance'):
                                dependencies['instance'] = True
                                immediate_dependencies['instance'] = True
                        if declaration.get('rules-taxonomy'):
                            dependencies['rules-taxonomy'] = True
                            immediate_dependencies['rules-taxonomy'] = True
                        break
                if not found:
                    raise xr.XuleRuleSetError("Error in variables, cannot find variable '{}'".format(parse_node['varName']))
                parse_node['is_constant'] = False
                
        if current_part == 'functionReference':
            func_info = self.catalog['functions'].get(parse_node['functionName'])
            if func_info is not None:
                self.dependencies_top(func_info)
                self._combine_dependencies(dependencies, func_info['dependencies'])
            dependencies['functions'].add(parse_node['functionName'])
            immediate_dependencies['functions'].add(parse_node['functionName'])
            
            if parse_node['functionName'] == 'taxonomy':
                if len(parse_node['functionArgs']) == 0:
                    # This a reference to the taxonomy of the instance
                    dependencies['instance'] = True
                    immediate_dependencies['instance'] = True
                else:
                    # This refers to another taxonomy
                    dependencies['rules-taxonomy'] = True
                    immediate_dependencies['rules-taxonomy'] = True

        if current_part == 'navigation':
            if 'taxonomy' not in parse_node:
                # Navigation that does not include an 'in' is against the instance taxonomy
                dependencies['instance'] = True
                immediate_dependencies['instance'] = True

        if current_part == 'factset':
            dependencies['instance'] = True
            immediate_dependencies['instance'] = True
        
        #descend the syntax tree
        for key, child in parse_node.items():
            if key != 'parent':
                next_parts = []
                if isinstance(child, dict):
                    next_parts.append(child)
                elif isinstance(child, list):
                    next_parts = child
                
                # At this point, next_parts is a list of dictionaries. The parse tree does not have lists of list. So if the child is a list, the children
                # of the list will all be dictionaries. If the child was neither a list or dictionary, the the next_parts list will be empty.
                for next_part in next_parts:
                    # the parser will only create a list of dictionaries, however, the build dependencies can add lists of other things (i.e. var_eclusion_ids). These should be skipped.
                    if isinstance(next_part, dict):
                        next_part['parent'] = parse_node
                        next_dependencies, next_immediate_dependencies = self.dependencies_detail(next_part, var_names, var_exclusions)
                        self._combine_dependencies(dependencies, next_dependencies)
                        self._combine_dependencies(immediate_dependencies, next_immediate_dependencies)
                        dependencies['constants'] |= next_dependencies['constants']
                        dependencies['functions'] |= next_dependencies['functions']
                        immediate_dependencies['constants'] |= next_immediate_dependencies['constants']
                        immediate_dependencies['functions'] |= next_immediate_dependencies['functions']
                        del next_part['parent']
#         if dependencies['instance']:
#             parseRes['instance'] = True
#         if dependencies['rules-taxonomy']:
#             parseRes['rules-taxonomy'] = True

        #remove variable names
        if current_part == 'blockExpr':
            for var_decl in parse_node['varDeclarations']:
                var_names[var_decl['varName']].pop()
        if current_part == 'varDeclaration':
            for i in parse_node['var_exclusion_ids']:
                var_exclusions.pop()                               
        if current_part == 'forExpr':
            var_names[parse_node['forVar']].pop()
        if current_part == 'factset':
            if 'aspectFilters' in parse_node:
                for aspect_filter in parse_node['aspectFilters']:
                    if 'alias' in aspect_filter:
                        var_names[aspect_filter['alias']].pop()
            if 'whereExpr' in parse_node:
                var_names['fact'].pop()
#         if current_part == 'navigation':
#             if 'whereExpr' in parse_node:
#                 var_names['relationship'].pop()
#         if current_part == 'filter':
#             if 'whereExpr' or 'returnsExpr' in parse_node:
#                 var_names['item'].pop()
        # if current_part == 'filter':
        #     if 'returnsExpr' in parse_node:
        #         var_names['item'].pop()
        #     if 'whereExpr' in parse_node:
        #         var_names['item'].pop()
        if current_part == 'functionDeclaration':
            for arg in parse_node['functionArgs']:
                var_names[arg['argName']].pop()

        #if parse_node.get('location') == 'filter':
        #    var_names['item'].pop()
            
        if parse_node.get('location') == 'navigation':
            var_names['relationship'].pop()
        if parse_node.get('location') == 'filter':
            var_names['item'].pop()

        return dependencies, immediate_dependencies
    
    def _walk_for_iterable(self, item_name, parse_node, var_defs=None):
        """Walk the AST
        
        This walk:
            1 - if an expression can produce a singleton value or a multiple values
            2 - if an expression can produce a single alignment or multiple alignments
            3 - what are the upstream variables that are used in the expression
            
        Arguments:
            parse_node (dictionary): Current node in the AST
            var_defs (list): The variables that have been declared at this point in the AST
        """
        pre_calc = []  
        # Number is used as an indicator that this node has already been walked
        if 'number' not in parse_node:
            if var_defs is None:
                var_defs = {}
                          
            current_part = parse_node['exprName']

            #descend
            descendant_number = 'single'
            descendant_has_alignment = False
            descendant_var_refs = list()
            descendant_is_dependent = False
            descendant_dependent_vars = list()
            descendant_dependent_iterables = list()
            descendant_downstream_iterables = list()
            
            for child in parse_node.values():
                next_parts = []
                if isinstance(child, dict):
                    next_parts.append(child)
                elif isinstance(child, list):
                    next_parts = child
                    
                for next_part in next_parts:
                    # the parser will only create a list of dictionaries, however, the build dependencies can add lists of other things (i.e. var_eclusion_ids). These should be skipped.
                    if isinstance(next_part, dict):
                        descendent_pre_calc = self._walk_for_iterable(item_name, next_part, var_defs)
                        if next_part['number'] == 'multi':
                            descendant_number = 'multi'
                        if next_part['has_alignment'] == True:
                            descendant_has_alignment = True
                        if next_part['is_dependent'] == True:
                            descendant_is_dependent = True
                        descendant_var_refs += next_part['var_refs']
                        descendant_dependent_vars += next_part['dependent_vars']
                        descendant_dependent_iterables += next_part['dependent_iterables']
                        descendant_downstream_iterables += next_part['downstream_iterables']
                        pre_calc += descendent_pre_calc
            
            #defaults
            parse_node['var_refs'] = descendant_var_refs
            parse_node['number'] = descendant_number
            parse_node['has_alignment'] = descendant_has_alignment
            parse_node['is_dependent'] = descendant_is_dependent
            parse_node['dependent_vars'] = descendant_dependent_vars
            parse_node['dependent_iterables'] = descendant_dependent_iterables
            parse_node['downstream_iterables'] = descendant_downstream_iterables

            if current_part == 'factset':
                parse_node['is_iterable'] = True
                parse_node['number'] = 'multi'
                if parse_node.get('covered') == True:
                    parse_node['has_alignment'] = False
                else:
                    parse_node['has_alignment'] = True
                
                #remove_refs = set()
                
                factset_var_def_ids = [parse_node['whereExpr']['node_id']] if 'whereExpr' in parse_node else []
                if 'aspectFilters' in parse_node:
                    factset_var_def_ids += [aspectFilter['node_id'] for aspectFilter in parse_node['aspectFilters']]

#                 for x in parse_node['var_refs']:
#                     if x[0] in factset_var_def_ids:
#                         remove_refs.add(x)
                
                #parse_node['var_refs'] -= remove_refs
                parse_node['var_refs'] = [x for x in parse_node['var_refs'] if x[0] not in factset_var_def_ids]
                #parse_node['dependent_vars'] -= remove_refs
                parse_node['dependent_vars'] = [x for x in parse_node['dependent_vars'] if x[0] not in factset_var_def_ids]

#             '''NEED TO CHECK IF THIS SHOULD BE UPDATED FOR FACTSETS WITHIN FACTSET'''
#             elif current_part == 'withExpr':
#                 parseRes['number'] = 'multi'
#                 parseRes['has_alignment'] = True
#                 parseRes['is_iterable'] = True
# 
#                 self.assign_table_id(parseRes.expr[0], var_defs, override_node_id=parseRes.node_id)
#
                if 'innerExpr' in parse_node:
                    self.assign_table_id(parse_node['innerExpr'], var_defs, override_node_id=parse_node['node_id'])

                if 'whereExpr' in parse_node:
                    self.assign_table_id(parse_node['whereExpr'], var_defs)

            
            elif current_part == 'navigation':
                if 'whereExpr' in parse_node:
                    parse_node['var_refs'] = [x for x in parse_node['var_refs'] if x[0] != parse_node['whereExpr']['node_id']]
                if 'stopExpr' in parse_node:
                    parse_node['var_refs'] = [x for x in parse_node['var_refs'] if x[0] != parse_node['stopExpr']['node_id']]                    
                    
            elif current_part == 'filter':
                if 'whereExpr' in parse_node or 'returnsExpr' in parse_node:
                    parse_node['var_refs'] = [x for x in parse_node['var_refs'] if x[0] != parse_node['expr']['node_id']]
                #self.assign_table_id(parse_node, var_defs, skip=parse_node['expr'])

                # colleciton_dependent_vars = self.get_dependent_vars(parse_node['expr'], var_defs)
                # collection_iterables = parse_node['expr']['downstream_iterables'] + self.get_dependent_var_iterables(parse_node['expr'], colleciton_dependent_vars, var_defs)
        
                # collection_iterables = parse_node['expr']['dependent_iterables']

                # if 'whereExpr' in parse_node:
                #     for iterable_expr in parse_node['whereExpr']['downstream_iterables']:
                #         iterable_expr['dependent_iterables'].extend(collection_iterables)
                #     #parse_node['whereExpr']['dependent_iterables'].extend(collection_iterables)
                # if 'returnsExpr' in parse_node:
                #     for iterable_expr in parse_node['returnsExpr']['downstream_iterables']:
                #         iterable_expr['dependent_iterables'].extend(collection_iterables)
                #     #parse_node['returnsExpr']['dependent_iterables'].extend(collection_iterables)

            elif current_part == 'forExpr':
                parse_node['number'] = 'multi'
                parse_node['is_iterable'] = True
                
                parse_node['var_refs'] = [var_ref for var_ref in parse_node['var_refs'] if var_ref[0] != parse_node['forLoopExpr']['node_id']]
                # If the for body uses the loop variable (which it normally would), the var_refs from the loop control should be 
                # added to the for body expression.
                var_ref_ids = [var_ref[0] for var_ref in parse_node['forBodyExpr']['var_refs']]
                if parse_node['forLoopExpr']['node_id'] in var_ref_ids:
                    parse_node['forBodyExpr']['var_refs'] += parse_node['forLoopExpr']['var_refs']

                #set table ids
                self.assign_table_id(parse_node, var_defs, skip=parse_node['forLoopExpr'])

            elif current_part == "ifExpr":
                condition_dependent_vars = self.get_dependent_vars(parse_node['condition'], var_defs)
                condition_iterables = parse_node['condition']['downstream_iterables'] + self.get_dependent_var_iterables(parse_node['condition'], condition_dependent_vars, var_defs)
                #update the iterables in the then expression
                if len(condition_iterables)> 0:
                    for iterable_expr in parse_node['thenExpr']['downstream_iterables']:
                        iterable_expr['dependent_iterables'].extend(condition_iterables)
                
                #update the else if conditions
                for elseIfExpr in parse_node.get('elseIfs', []):
                    condition_dependent_vars = self.get_dependent_vars(elseIfExpr['condition'], var_defs)
                    condition_iterables.update(elseIfExpr['condition']['downstream_iterables'] + self.get_dependent_var_iterables(elseIfExpr['condition'], condition_dependent_vars, var_defs))
                    if len(condition_iterables) > 0:
                        for iterable_expr in elseIfExpr['thenExpr']['downstream_iterables']:
                            iterable_expr['dependent_iterables'].extend(condition_iterables)
                
                #update the else
                for iterable_expr in parse_node['elseExpr']['downstream_iterables']:
                    iterable_expr['dependent_iterables'].extend(condition_iterables)
            
            elif current_part == 'functionReference':
                if parse_node['functionName'] in self.catalog['functions'] and parse_node['functionName'] not in xf.BUILTIN_FUNCTIONS:
                    #Xule defined function
                    parse_node['function_type'] = 'xule_defined'
                    func_expr, func_info = self.getFunction(parse_node['functionName'])
                    self._walk_for_iterable(item_name, func_expr, var_defs)
                    if func_expr['number'] == 'multi' or descendant_number == 'multi':
                        parse_node['number'] = 'multi'
                        parse_node['is_iterable'] = True
                    else:
                        parse_node['number'] = 'single'
                    parse_node['has_alignment'] = func_expr['has_alignment'] or descendant_has_alignment

                    if len( parse_node['downstream_iterables']) == 0:
                        parse_node['cacheable'] = True
                else:
                    #otherwise it is a built in function
                    if parse_node['functionName'] in xf.BUILTIN_FUNCTIONS:
                        if xf.BUILTIN_FUNCTIONS[parse_node['functionName']][xf.FUNCTION_TYPE] == 'aggregate':
                            parse_node['function_type'] = 'aggregation'
                            parse_node['cacheable'] = True
                            #aggregation is a special case. If the arguments are not alignable, then the aggregation will always colapse into a single result.
                            if descendant_has_alignment == False:
                                parse_node['number'] = 'single'
                                parse_node['has_alignment'] = False
                            else:
                                parse_node['number'] = 'multi'
                                parse_node['has_alignment'] = True
                            
                            parse_node['is_iterable'] = True
   
                            self.assign_table_id(parse_node, var_defs)
                                
                        elif xf.BUILTIN_FUNCTIONS[parse_node['functionName']][xf.FUNCTION_RESULT_NUMBER] == 'multi':
                            parse_node['function_type'] = 'builtin'
                            parse_node['number'] = 'multi'
                            parse_node['is_iterable'] = True
                        else:
                            #regular builtin function
                            if parse_node['number'] == 'single':
                                parse_node['cacheable'] = True     
                        #all other built in functions use the defaults
                        
            elif current_part == 'functionDeclaration':        
                arg_node_ids = [arg['node_id'] for arg in parse_node['functionArgs']]
                parse_node['var_refs'] = [var_ref for var_ref in parse_node['var_refs'] if var_ref[0] not in arg_node_ids]

            elif current_part == 'varRef':
                if parse_node['is_constant']:
                    const_info = self.catalog['constants'][parse_node['varName']]
                    const_expr = self.getItem(const_info['file'], const_info['index'])
                    self._walk_for_iterable(item_name, const_expr, var_defs)
                    #this is done in the dependencies.
                    #parse_node['var_declaration'] = const_expr['node_id']
                    parse_node['number'] = const_expr['number']
                    parse_node['has_alignment'] = const_expr['has_alignment']
                    #save the declaration parse result object
                    var_defs[const_expr['node_id']] = const_expr
                    parse_node['var_refs'] = [(parse_node['var_declaration'], parse_node['varName'], parse_node, 2),]
                # is a variable (not constant)
                else:
                    var_expr = self._var_exprs.get(parse_node.get('var_declaration'))
                    if var_expr is not None:
                        self._walk_for_iterable(item_name, var_expr, var_defs)
                        parse_node['number'] = var_expr['number']
                        parse_node['has_alignment'] = var_expr['has_alignment']
                        #save the declaration parse result object
                        var_defs[parse_node['var_declaration']] = var_expr
                        parse_node['var_refs'] = [(parse_node['var_declaration'], parse_node['varName'], parse_node, 1),]
                        parse_node['dependent_iterables'].extend(var_expr['dependent_iterables'])
                    else:
                        parse_node['var_refs'] = [(parse_node['var_declaration'], parse_node['varName'], parse_node, 3),]

            elif current_part == 'blockExpr':
                var_assignments = parse_node['varDeclarations']

                #check if the variable is used
                var_ref_ids = {var_ref[0] for var_ref in parse_node['var_refs']}
                for var_assign in var_assignments:
                    if var_assign['node_id'] not in var_ref_ids:
                        var_assign['not_used'] = True
                
                #removed defined variables from the var_refs and dependent vars
                var_assign_ids = [var_assign['node_id'] for var_assign in var_assignments]
                parse_node['var_refs'] = [var_ref for var_ref in parse_node['var_refs'] if var_ref[0] not in var_assign_ids]
                #parseRes['dependent_vars'] = {var_ref for var_ref in parseRes.dependent_vars if var_ref[0] not in var_assign_ids}                       
                
            elif current_part == 'qname':
                #find the namespace uri for the prefix
                parse_node['namespace_uri'] = self.getNamespaceUri(parse_node['prefix'])

            elif current_part == 'constantDeclaration':
                if parse_node['number'] == 'multi':
                    parse_node['is_iterable'] = True
                    
            elif current_part == 'result':
                #if parse_node['number'] == 'multi' or len(parse_node['downstream_iterables']) > 0:
                #    raise xr.XuleRuleSetError("In rule {} the message of a rule cannot contain expressions that create multiple values (i.e factsets or for loops).".format(item_name))

                # Check that the result name is valid. It can be one of 'message' or 'severity' or it must be defined
                # with an output-attribute
                if not parse_node['resultName'] in ('message', 'severity', 'rule-suffix', 'rule-focus'):
                     if not self.hasOutputAttribute(parse_node['resultName']):
                         raise xr.XuleRuleSetError("In rule {}, the result name '{}' is not defined as an output-attribute.".format(item_name, parse_node['resultName']))
            
            #set the table id for the iterables under the top level node. 
            if current_part in ('assertion', 'outputRule', 'functionDeclaration', 'constantDeclaration'):
                self.assign_table_id(parse_node, var_defs)

                #assign table id to variable references to constants.
                for var_ref in parse_node['var_refs']:
                    if var_ref[3] == 2: #this is reference to a constant
                        if 'table_id' not in var_ref[2]:
                            var_ref[2]['table_id'] = parse_node['node_id']

            #Update the dependent iteratables
            if 'is_iterable' in parse_node:
                #set dependent variables
                dependent_vars = self.get_dependent_vars(parse_node, var_defs)
                parse_node['dependent_vars'] = dependent_vars
                    
                parse_node['downstream_iterables'].append(parse_node)
                    
                #reset the dependent_iterables. The iterable will not include downstream dependencies which is what the dependent_iterables currently contains.
                parse_node['dependent_iterables'] = list()
                parse_node['dependent_iterables'].append(parse_node)

                #add iterables from the expresions for variable refs, but only if the expressions is upstream
                additional_dependent_iterables = self.get_dependent_var_iterables(parse_node, dependent_vars, var_defs)
                parse_node['dependent_iterables'] += additional_dependent_iterables
                
                #add downstream iterables for function references. This makes the function reference dependent on the iterables in the arguments.
                #This is needed when passing iterables (i.e. factset) in the argument.
                if current_part == 'functionReference' and parse_node['function_type'] == 'xule_defined':
                    for dependent_node in parse_node['functionArgs']:
                        #parse_node['dependent_iterables'] += [x['downstream_iterables'] for x in parse_node['functionArgs']]
                        parse_node['dependent_iterables'].extend(dependent_node['downstream_iterables'])
                #This is needed for "for loop" when the loop control variable is iterable
                if current_part == 'forExpr' and parse_node['forLoopExpr'].get('is_iterable', False):
                    parse_node['dependent_iterables'].append(parse_node['forLoopExpr'])
                parse_node['is_dependent'] = len(parse_node['dependent_iterables']) > 1 #The dependent_iterables list will always include itself, so the miniumn count is 1     
        
        return pre_calc
    
    def get_dependent_vars(self, rule_part, var_defs):
        return [x for x in rule_part['var_refs'] if x[0] in var_defs if var_defs[x[0]]['number'] == 'multi' or var_defs[x[0]]['is_dependent']]
    
    def get_dependent_var_iterables(self, rule_part, dependent_vars, var_defs): 
        additional_iterables = list()

        #for body expressions - add the dependent iterables in the control.       
        if rule_part['exprName'] == 'forBodyExpr':
            additional_iterables.extend(rule_part['forControl']['forLoopExpr']['dependent_iterables'])
        
        if rule_part['exprName'] != 'constantDeclaration':
            #constantAssign expressions are never dependent.
            for var in dependent_vars:
                var_def_expr = var_defs[var[0]]
                if var_def_expr['exprName'] == 'constantDeclaration':
                    additional_iterables.append(var_def_expr)
                else:
                    #the variable has to be assigned upstream   
                    #if var_def_expr['node_id'] < rule_part['node_id']:
                        if var_def_expr['exprName'] in ('forControl', 'aspectFilter', 'whereExpr'):
                            additional_iterables.append(var_def_expr)
                        else:
                            if 'dependent_iterables' in var_def_expr:
                                additional_iterables.extend(var_def_expr['dependent_iterables'])

        return additional_iterables

    def assign_table_id(self, rule_part, var_defs, override_node_id=None, skip=None):
        """Add table_id to iterable nodes.
        
        This will assign the parent table_id to unassigned iterables.
        """
        
        if skip is None:
            skip_list = []
        else:
            skip_list = [skip['node_id'],] + [x['node_id'] for x in skip['downstream_iterables']]
        
        node_id = override_node_id or rule_part['node_id']
        for it in rule_part['downstream_iterables']:
            if it['node_id'] not in skip_list:
                if 'table_id' not in it:
                    it['table_id'] = node_id                

    def post_parse(self):
        """Identify constants and functions used by expressions.
        
        Also identifies if a top level component (assert, output, constant, function) uses instance data or non instance taxonomy data.
        """
        
        self._cleanup_for_append()
        
        #immediate dependencies
        for const_info in self.catalog['constants'].values():
            self.dependencies_top(const_info)
        for func_info in self.catalog['functions'].values():
            self.dependencies_top(func_info)
        for rule_info in self.catalog['rules'].values():
            self.dependencies_top(rule_info)            
            
        #check if constants are used
        used_constants = set()
        for rule_info in self.catalog['rules'].values():
            for const_name in rule_info['dependencies']['constants']:
                used_constants.add(const_name)
        
        for function_info in self.catalog['functions'].values():
            for const_name in function_info['dependencies']['constants']:
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

        #determine number (single, multi) for each expression
        for const_name, const_info in self.catalog['constants'].items():
            self._walk_for_iterable(const_name, self.getItem(const_info['file'], const_info['index']))            
        for func_name, func_info in self.catalog['functions'].items():
            self._walk_for_iterable(func_name, self.getItem(func_info['file'], func_info['index']))
        for rule_name, rule_info in self.catalog['rules'].items():
            ast_rule = self.getItem(rule_info['file'], rule_info['index'])
            self._walk_for_iterable(rule_name, ast_rule)

        self._cleanup_ruleset()

    def _cleanup_ruleset(self):
        '''This function removes parseRes properties that were added during the post parse processing that are not needed for processing. 
        '''
        for parseRes in self._xule_file_expression_trees.values():
            self._cleanup_ruleset_detail(parseRes)
    
    def _cleanup_ruleset_detail(self, parse_node):
        #for prop in ('number', 'dependent_vars', 'downstream_iterables', 'var_exclusion_ids'):
        for prop in ('dependent_vars', 'downstream_iterables', 'var_exclusion_ids', 'location', 'parent'):
            if prop in parse_node:
                del parse_node[prop]
        if 'dependent_iterables' in parse_node:
            if parse_node.get('is_iterable') == True:
                #get rid of the self reference in dependent_iterables
                parse_node['dependent_iterables'] = [x for x in parse_node['dependent_iterables'] if x['node_id'] != parse_node['node_id']]
            else:
                del parse_node['dependent_iterables']
                
        if 'var_refs' in parse_node:
            #Get rid of the self reference in var_refs
            parse_node['var_refs'] = [x for x in parse_node['var_refs'] if x[2]['node_id'] != parse_node['node_id']]
            
        for child in parse_node.values():
            next_parts = []
            if isinstance(child, dict):
                next_parts.append(child)
            elif isinstance(child, list):
                next_parts = child
                
            for next_part in next_parts:
                # the parser will only create a list of dictionaries, however, the build dependencies can add lists of other things (i.e. var_eclusion_ids). These should be skipped.
                if isinstance(next_part, dict):
                    self._cleanup_ruleset_detail(next_part)
    
    def _cleanup_for_append(self):
        #clean up catalog - remove dependency information. This will be recalculated.
        for info in list(self.catalog['rules'].values()) + list(self.catalog['functions'].values()) + list(self.catalog['constants'].values()):
            try:
                del info['dependencies']
            except KeyError:
                pass
            try:
                del info['immediate_dependencies']
            except KeyError:
                pass
            
        delete_file_numbers = []
        for file_info in self.catalog['files']:
            if self._file_status.get(file_info['file']) == 'keep':
                #clean up ast in ruleset
                self._cleanup_for_append_ruleset_detail(self._xule_file_expression_trees[file_info['file']])
            elif self._file_status.get(file_info['file']) is None:
                delete_file_numbers.append(file_info['file'])
        
        if len(delete_file_numbers) > 0:
            #pickled files
            for file_number in delete_file_numbers:
                del self._xule_file_expression_trees[file_number]
                
            #delete catalog files
            self.catalog['files'] = [x for x in self.catalog['files'] if x['file'] not in delete_file_numbers]

    def _cleanup_for_append_ruleset_detail(self, parse_node):
        remove_list = ('var_refs', 'number', 'is_constant', 'var_declaration', 'has_alignment', 'is_dependent', 
                       'dependent_iterables', 'is_iterable', 'function_type', 'cacheable', 'not_used', 'namespace_uri',
                       'table_id')
        for prop in remove_list:
            if prop in parse_node:
                del parse_node[prop]

        for child in parse_node.values():
            next_parts = []
            if isinstance(child, dict):
                next_parts.append(child)
            elif isinstance(child, list):
                next_parts = child
                
            for next_part in next_parts:
                # the parser will only create a list of dictionaries, however, the build dependencies can add lists of other things (i.e. var_eclusion_ids). These should be skipped.
                if isinstance(next_part, dict):
                    self._cleanup_for_append_ruleset_detail(next_part)
            
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

    def _addXuleFile(self, file_time, file_name, file_hash):
        
        #get the next file number
        if len(self.catalog['files']) == 0:
            file_num = 0
        else:
            file_num = max([x['file'] for x in self.catalog["files"]]) + 1
            
        pickle_name = "rule_file%i" %(file_num,)
        file_dict = {"file": file_num, "pickle_name": pickle_name}
        if file_time:
            file_dict['mtime'] = file_time
        if file_name:
            file_dict['name'] = file_name
        file_dict['file_hash'] = file_hash
        self._file_status[file_num] = 'new'
        self.catalog['files'].append(file_dict)
        
        return file_num    
    
    def getFileHash(self, file_name):
        file_info = self.getFileInfoByName(file_name)
        if file_info is not None:
            return file_info['file_hash']
        return None
    
    def _saveFilePickle(self, rule_set_file, file_num, parseRes):
        
        pickle_name = "rule_file%i" %(file_num,)
        #save the pickle
        if self._compile_type.lower() == 'pickle':
            rule_set_file.writestr(pickle_name, pickle.dumps(parseRes, protocol=2))
        elif self._compile_type.lower() == 'json':
            rule_set_file.writestr(pickle_name, json.dumps(parseRes, indent=4))
        else:
            raise xr.XuleRuleSetError("Unknown compile type: {}.".format(self._compile_type))       
         
        return pickle_name
