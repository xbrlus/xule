'''
Created on Dec 16, 2014

copywrite (c) 2014 XBRL US Inc. All rights reserved.
'''
from .XuleRunTime import XuleProcessingError, XuleResultSet, XuleResult
from arelle import FileSource
from arelle import ModelManager
import datetime


class XuleGlobalContext(object):
    
    def __init__(self, rule_set, model_xbrl=None, cntlr=None, include_nils=False):
        '''
        Constructor
        '''
        self.cntlr = cntlr
        self.model = model_xbrl
        self.rules_model = None
        self.rule_set = rule_set
        self.fact_index = None
        self.include_nils = include_nils
        self._constants = {}
        self.show_trace = False
        self.show_timing = False
        self.show_debug = False
        self.crash_on_error = False
        self.function_cache = {}
        
        if getattr(self.cntlr, "base_taxonomy", None) is None:
            self.get_rules_dts()        
        
    @property
    def catalog(self):
        return self.rule_set.catalog
    
    def get_rules_dts(self):
        if getattr(self.cntlr, "base_taxonomy", None) is None:
            start = datetime.datetime.today()
            rules_taxonomy_filesource = FileSource.openFileSource(self.rule_set.getRulesTaxonomyLocation(), self.cntlr)            
            modelManager = ModelManager.initialize(self.cntlr)
            modelXbrl = modelManager.load(rules_taxonomy_filesource)            
            setattr(self.cntlr, "base_taxonomy", modelXbrl)          
            end = datetime.datetime.today()

            if getattr(self.rules_model, "log", None) is not None:
                self.rules_model.log("INFO",
                                   "rules-taxonomy", 
                                   "Load time %s from '%s'" % (end - start, self.rule_set.getRulesTaxonomyLocation()))
            else:
                print("Rules Taxonomy Loaded. Load time %s from '%s' " % (end - start, self.rule_set.getRulesTaxonomyLocation()))
      
        return self.cntlr.base_taxonomy  


class XuleRuleContext(object):

    #CONSTANTS
    SEVERITY_ERROR = 'error'
    SEVERITY_WARNING = 'warning'
    SEVERITY_INFO = 'info'
    SEVERITY_PASS = 'pass'
    STATIC_SEVERITIES = [SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO, SEVERITY_PASS]
    SEVERITY_TYPE_STATIC = 'STATIC'
    SEVERITY_TYPE_FUNCTION = 'FUNCTION'
    SEVERITY_TYPE_DYNAMIC = 'DYNAMIC'
    _VAR_TYPE_VAR = 1
    _VAR_TYPE_CONSTANT = 2
    _VAR_TYPE_ARG = 3

    def __init__(self, global_context, rule_name=None, cat_file_num=None, severity_type=None, severity=None):
        '''
        Constructor
        '''
        self.global_context = global_context
        self.severity_type = severity_type
        self.severity = severity
        self.rule_name = rule_name
        self.cat_file_num = cat_file_num
        
        self._vars = []
        self.hash_table = {}
        self.with_filters = []
        self.other_filters = []

        self.trace_level = 0
        
        self.in_where_alignment = None

    def add_var(self, name, tag, expr):

        next_var_index = len(self._vars)
        self._vars.append({"name": name,
                           "index": next_var_index,
                           "tag": tag,
                           "type": self._VAR_TYPE_VAR,
                           "expr": expr,
                           "calculated": False,
                           "contains_facts": False,
                           "other_values": {}
                           })     
        
    def add_arg(self, name, tag, value):
        #arguments are just like variables, but they don't have an expression and they are already calculated
        next_var_index = len(self._vars)
        var_info = {"name": name,
                    "index": next_var_index,
                    "tag": tag,
                    "type": self._VAR_TYPE_ARG,
                    "calculated": True,
                    "value": value,
                    "contains_facts": False,
                    "other_values": {}}
        
        #add the variable information to the results
#         for res_index, arg_res in enumerate(value.results):
#             if var_info['tag'] == True:
#                 arg_res.add_tag(var_info['name'], arg_res)
#             arg_res.add_var(var_info['index'], res_index)
            
        self._vars.append(var_info) 
            
    def del_var(self, var_name, result_set):

        if var_name != self._vars[-1]['name']:
            
            message = "Remove variable mismatch. Tried to remove '%s', but found '%s'\n" % (var_name, self._vars[-1]['name'])
            for var in self._vars:
                message += "    %s (%s)" % (var['name'], str(var['index']))                                                        
            
            raise XuleProcessingError(_(message), self)
 
        #remove the variable from the processing context
        var_info = self._vars.pop()
        #remove the variable references from the variable results
        if 'value' in var_info: #if the variable was never calculated then there is nothing to do.
            for var_result in var_info['value'].results:
                var_result.vars = {k: v for k, v in var_result.vars.items() if k != var_info['index']}
                
        #remove the variable references from the generated results, if it is a variable (not argument)
        if var_info['type'] == self._VAR_TYPE_VAR:
            for res in result_set:
                res.del_var(var_info['index'])   
        
    def var_by_index(self, var_index):
        if type(var_index) == str:
            #this is constant
            if var_index in self.global_context._constants:
                return self.global_context._constants[var_index]
            else:
                '''THIS IS AN ERROR, NEED TO REPORT ERROR'''
                print("ERROR IN CONSTANT")
                pass
        if var_index >= len(self._vars):
            #raise XuleProcessingError(_("Internal error, var index out of range. Index = %i, Number of vars = %i" % (var_index, len(self._vars))), self)
            print("ERROR IN VARIABLE")
        else:
            return self._vars[var_index]    
    
    def find_var(self, var_name):
        #First look for the vairable in the current list of variables
        try:
            #The search is reversed so if there are multiple variables with the same name, we get the latest one.
            #This allows nested block expressions with same variable names,
            var_info =  next(var for var in reversed(self._vars) if var['name'] == var_name)
        except StopIteration:
            #this exceptions happens if there is no mathcing variable name
            #Now look in constants
            if var_name in self._BUILTIN_CONSTANTS:
                var_value = self._BUILTIN_CONSTANTS[var_name](self)
                var_info = {"name": var_name,
                        "index": var_name,
                        "tag": None,
                        "type": self._VAR_TYPE_CONSTANT,
                        "expr": None,
                        "calculated": True,
                        "value": var_value,
                        "contains_facts": False,
                        "other_values": {}}
            else:
                var_info = self.global_context._constants.get(var_name)
                if not var_info:
                    #this is the first time for the constant. Need to retrieve it from the catalog
                    cat_const =  self.global_context.catalog['constants'].get(var_name)
                    if not cat_const:
                        #the constant is not in the catalog
                        var_info = None
                    else:
                        ast_const = self.global_context.rule_set.getItem(cat_const)
                        var_info = {"name": var_name,
                                    "index": var_name,
                                    "tag": None,
                                    "type": self._VAR_TYPE_CONSTANT,
                                    "expr": ast_const.expr[0],
                                    "calculated": False,
                                    "contains_facts": False,
                                    "other_values": {}}
                        self.global_context._constants[var_name] = var_info
        
        return var_info

    def var_add_value(self, var_name, value):
        #This may acutally return a variable or a constant.
        var_info = self.find_var(var_name)
        #add the variable information to the results
        var_info['contains_facts'] = False
        for res_index, arg_res in enumerate(value.results):
            if len(arg_res.facts) != 0:
                var_info["contains_facts"] = True
            if var_info['tag'] == True:
                arg_res.add_tag(var_info['name'], arg_res)
            arg_res.add_var(var_info['index'], res_index)  
                  
        var_info['calculated'] = True
        var_info['value'] = value 
    
    def filter_add(self, filter_type, filter_dict):
        self.with_filters.append((filter_type, filter_dict))

    def filter_del(self):           
        self.with_filters.pop()    
    
    def get_current_filters(self):
        filter_aspects = set()
        with_filters = dict()
        other_filters = dict()
        
        for filter_tup in reversed(self.with_filters):
            filter_type = filter_tup[0]
            filter_dict = filter_tup[1]
            
            for filter_info, filter_member in filter_dict.items():
                # 1 = the aspect name
                if filter_info[1] not in filter_aspects:
                    filter_aspects.add(filter_info[1])
                    if filter_type == 'with':
                        with_filters[filter_info] = filter_member
                    else:
                        other_filters[filter_info] = filter_member
                    
        return with_filters, other_filters    
    
    def find_function(self, function_name):
        '''
        This is created so the processor uses the context to retrieve the function. A performance enhancement
        may be to save the value of function for a given set of arguments, so that if it is called again with the
        same arguments, it doesn't need to be recalculated. This however, could create a memory issue.
        '''
        cat_function = self.global_context.rule_set.catalog['functions'].get(function_name)
        if not cat_function:
            return None
        
        ast_function = self.global_context.rule_set.getItem(cat_function)
        function_info = {"name": function_name,
                         "function_declaration": ast_function}
        return function_info   
      
    
    def get_rules_dts(self):
        return self.global_context.get_rules_dts()
    
    
    #built in constants
    def _const_extension_ns(self):
        for doc in self.model.modelDocument.hrefObjects:
            if doc[0].elementQname.localName == 'schemaRef' and doc[0].elementQname.namespaceURI == 'http://www.xbrl.org/2003/linkbase':
                return XuleResultSet(XuleResult(doc[1].targetNamespace, 'uri'))
        
        return XuleResultSet()
    
    _BUILTIN_CONSTANTS = {'extension_ns': _const_extension_ns}    

    #properties from the global_context   
    @property
    def model(self):
        return self.global_context.model
        
    @property
    def rules_model(self):
        return self.global_context.rules_model
    
    @property
    def rule_set(self):
        return self.global_context.rule_set
    
    @property
    def fact_index(self):
        return self.global_context.fact_index
    
    @property
    def include_nils(self):
        return self.global_context.include_nils
 
    @property
    def show_trace(self):
        return self.global_context.show_trace
    
    @property
    def function_cache(self):
        return self.global_context.function_cache

class XuleContextXXX(object):
    '''
    classdocs
    '''
    #CONSTANTS
    SEVERITY_ERROR = 'error'
    SEVERITY_WARNING = 'warning'
    SEVERITY_INFO = 'info'
    SEVERITY_PASS = 'pass'
    STATIC_SEVERITIES = [SEVERITY_ERROR, SEVERITY_WARNING, SEVERITY_INFO, SEVERITY_PASS]
    SEVERITY_TYPE_STATIC = 'STATIC'
    SEVERITY_TYPE_FUNCTION = 'FUNCTION'
    SEVERITY_TYPE_DYNAMIC = 'DYNAMIC'
    _VAR_TYPE_VAR = 1
    _VAR_TYPE_CONSTANT = 2
    _VAR_TYPE_ARG = 3

    def __init__(self, rule_set, model_xbrl=None, cntlr=None, include_nils=False):
        '''
        Constructor
        '''
        self.cntlr = cntlr
        self.model = model_xbrl
        self.rules_model = None
        self.rule_set = rule_set
        self.fact_index = None
        
        self.severity_type = None
        self.severity = None
        self.severity_arguments = None
        self.rule_name = None
        self.cat_file_num = None
        
        self._vars = []
        self._constants = {}
        self.networks = {}
        self.hash_table = {}
        self.with_filters = []
        self.other_filters = []
        
        self.trace_level = 0
        self.include_nils = include_nils
        
        self.in_where_alignment = None
        
        
    def __str__(self):
        return ("Ruleset Name: %s\n"
                "Rule Name: %s\n"
               "Severity Type: %s\n"
               "Severity: %s\n" 
               "Variables:\n\t%s\n"
               "Constants: \n\t%s" % 
               (self.rule_set.name,
                self.rule_name,
                self.severity_type,
                self.severity,
                "\n\t".join(["Name: %s, Calculated: %s, Value: %s" % 
                 (x['name'], x['calculated'], x['value'] if 'value' in x.keys() else None)
                 for x in self._vars]),
                "\n\t".join(["Name: %s, Calculated: %s, Value: %s" % 
                 (x['name'], x['calculated'], x['value'] if 'value' in x.keys() else None)
                 for k, x in self._constants.items()])))
            
    @property
    def catalog(self):
        return self.rule_set.catalog
    
    def clear_rule(self):
        self.severity_type = None
        self.severity = None
        self.rule_name = None
        self.cat_file_num = None  
        
        self._vars = []
        self.hash_table = {}
        self.with_filters = []
        self.other_filter = []
        
        self.trace_level = 0
        
        
    def add_var(self, name, tag, expr):

        next_var_index = len(self._vars)
        self._vars.append({"name": name,
                           "index": next_var_index,
                           "tag": tag,
                           "type": self._VAR_TYPE_VAR,
                           "expr": expr,
                           "calculated": False,
                           "contains_facts": False,
                           "other_values": {}
                           })       
        
    def add_arg(self, name, tag, value):
        #arguments are just like variables, but they don't have an expression and they are already calculated
        next_var_index = len(self._vars)
        var_info = {"name": name,
                    "index": next_var_index,
                    "tag": tag,
                    "type": self._VAR_TYPE_ARG,
                    "calculated": True,
                    "value": value,
                    "contains_facts": False,
                    "other_values": {}}
        
        #add the variable information to the results
#         for res_index, arg_res in enumerate(value.results):
#             if var_info['tag'] == True:
#                 arg_res.add_tag(var_info['name'], arg_res)
#             arg_res.add_var(var_info['index'], res_index)
            
        self._vars.append(var_info) 

    
    def del_var(self, var_name, result_set):

        if var_name != self._vars[-1]['name']:
            
            message = "Remove variable mismatch. Tried to remove '%s', but found '%s'\n" % (var_name, self._vars[-1]['name'])
            for var in self._vars:
                message += "    %s (%s)" % (var['name'], str(var['index']))                                                        
            
            raise XuleProcessingError(_(message), self)
 
        #remove the variable from the processing context
        var_info = self._vars.pop()
        #remove the variable references from the variable results
        if 'value' in var_info: #if the variable was never calculated then there is nothing to do.
            for var_result in var_info['value'].results:
                var_result.vars = {k: v for k, v in var_result.vars.items() if k != var_info['index']}
        #remove the variable references from the gnerated results, if it is a variable (not argument)
        if var_info['type'] == self._VAR_TYPE_VAR:
            for res in result_set:
                res.del_var(var_info['index'])   
    
    def var_by_index(self, var_index):
        if type(var_index) == str:
            #this is constant
            if var_index in self._constants:
                return self._constants[var_index]
            else:
                '''THIS IS AN ERROR, NEED TO REPORT ERROR'''
                print("ERROR IN CONSTANT")
                pass
        if var_index >= len(self._vars):
            #raise XuleProcessingError(_("Internal error, var index out of range. Index = %i, Number of vars = %i" % (var_index, len(self._vars))), self)
            print("ERROR IN VARIABLE")
        else:
            return self._vars[var_index]
    
    def find_var(self, var_name):
        #First look for the vairable in the current list of variables
        try:
            #The search is reversed so if there are multiple variables with the same name, we get the latest one.
            #This allows nested block expressions with same variable names,
            var_info =  next(var for var in reversed(self._vars) if var['name'] == var_name)
        except StopIteration:
            #this exceptions happens if there is no mathcing variable name
            #Now look in constants
            var_info = self._constants.get(var_name)
            if not var_info:
                #this is the first time for the constant. Need to retrieve it from the catalog
                cat_const =  self.catalog['constants'].get(var_name)
                if not cat_const:
                    #the constant is not in the catalog
                    var_info = None
                else:
                    ast_const = self.rule_set.getItem(cat_const)
                    var_info = {"name": var_name,
                                "index": var_name,
                                "tag": None,
                                "type": self._VAR_TYPE_CONSTANT,
                                "expr": ast_const.expr[0],
                                "calculated": False,
                                "contains_facts": False,
                                "other_values": {}}
                    self._constants[var_name] = var_info
        
        return var_info

    
    def filter_add(self, filter_type, filter_dict):
        self.with_filters.append((filter_type, filter_dict))

    def filter_del(self):           
        self.with_filters.pop()
            
    def get_current_filters(self):
        filter_aspects = set()
        with_filters = dict()
        other_filters = dict()
        
        for filter_tup in reversed(self.with_filters):
            filter_type = filter_tup[0]
            filter_dict = filter_tup[1]
            
            for filter_info, filter_member in filter_dict.items():
                # 1 = the aspect name
                if filter_info[1] not in filter_aspects:
                    filter_aspects.add(filter_info[1])
                    if filter_type == 'with':
                        with_filters[filter_info] = filter_member
                    else:
                        other_filters[filter_info] = filter_member
                    
        return with_filters, other_filters
    
    def var_add_value(self, var_name, value):
        #This may acutally return a variable or a constant.
        var_info = self.find_var(var_name)
        #add the variable information to the results
        var_info['contains_facts'] = False
        for res_index, arg_res in enumerate(value.results):
            if len(arg_res.facts) != 0:
                var_info["contains_facts"] = True
            if var_info['tag'] == True:
                arg_res.add_tag(var_info['name'], arg_res)
            arg_res.add_var(var_info['index'], res_index)  
                  
        var_info['calculated'] = True
        var_info['value'] = value      
        
    def find_function(self, function_name):
        '''
        This is created so the processor uses the context to retrieve the function. A performance enhancement
        may be to save the value of function for a given set of arguments, so that if it is called again with the
        same arguments, it doesn't need to be recalculated. This however, could create a memory issue.
        '''
        cat_function = self.rule_set.catalog['functions'].get(function_name)
        if not cat_function:
            return None
        
        ast_function = self.rule_set.getItem(cat_function)
        function_info = {"name": function_name,
                         "function_declaration": ast_function}
        return function_info
        
    def get_rules_dts(self):
        if self.rules_model is None:
            start = datetime.datetime.today()
            rules_taxonomy_filesource = FileSource.openFileSource(self.rule_set.getRulesTaxonomyLocation(), self.cntlr)            
            modelManager = ModelManager.initialize(self.cntlr)
            modelXbrl = modelManager.load(rules_taxonomy_filesource)            
            self.rules_model = modelXbrl
            end = datetime.datetime.today()

            self.model.log("INFO",
                               "rules-taxonomy", 
                               "Load time %s from '%s'" % (end - start, self.rule_set.getRulesTaxonomyLocation()))
    
        return self.rules_model
    
