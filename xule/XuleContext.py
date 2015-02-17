'''
Created on Dec 16, 2014

copywrite (c) 2014 XBRL US Inc. All rights reserved.
'''
from .XuleRunTime import XuleProcessingError, XuleResultSet, XuleResult
from arelle import FileSource
from arelle import ModelManager
from queue import Queue
from multiprocessing import Queue as M_Queue, Manager, cpu_count
import datetime
from time import sleep

class XuleMessageQueue():
    _queue = None
    _model = None
    _multi = False
    _async = False
    _printlist = []
    
    '''
    use self.log to print to the queue
    use self._model to print directly
    '''
    
    def __init__(self, model, multi=False, async = False):
        self._queue = M_Queue()
        if model is not None:
            self._model = model
        self._multi = multi
        self._async = async
        #if not hasattr(self._model, "logger"):
        #    print("Error during XuleMessageQueue init.  No logger available")
        
    def info(self, codes, msg, **args):
        self.log('INFO', codes, msg, **args)

    def warning(self, codes, msg, **args):
        self.log('WARNING', codes, msg, **args)

    def error(self, codes, msg, **args):
        self.log('ERROR', codes, msg, **args)
    

    def log(self, level, codes, msg, **args):
        self._queue.put((level, codes, msg, args))

    def logging(self, msg):
        ''' Logging statements for any text '''
        self.print(msg)
        
    def print(self, msg):
        print(msg)

    def file(self, msg):
        pass

    def stop(self):
        self.log('STOP', None, None)
        
    def clear(self):
        ''' clears what's in the queue '''
        for level, codes, msg, args in self._printlist:
            self.output(level, codes, msg, **args)
        

    def loopoutput(self):
        keep = True
        (level, codes, msg, args) = self._queue.get()

        if level == 'STOP':
            ''' Break Loop '''
            if self.size > 0:
                print("aborting message break")
            else:
                keep = False
        #elif 1 == 1:
        #    return keep
        elif not self._async:
            self._printlist.append((level, codes, msg, args))
        else:
            self.output(level, codes, msg, **args)
        
        return keep

    def output(self, level, codes, msg, **args): 
        ''' output loop.
            haslogger determined by hasattr(xule_context.global_context, "logger")
        '''
        if self._model is None:
            print("[%s] [%s] %s" % (level, codes, msg))
#         elif not hasattr(self._model, "logger"):
#             print("Error, no logger in model")
#             print("[%s] [%s] %s" % (level, codes, msg))
        elif level == "ERROR":
            self._model.error(codes, msg, **args)
        elif level == "INFO":
            self._model.info(codes, msg, **args)
        elif level == "WARNING":
            self._model.warning(codes, msg, **args)
        else:
            self._model.log(level, codes, msg, **args)

            

    @property
    def size(self):
        return self._queue.qsize()
    

class XuleGlobalContext(object):
    
    # Constants
    _NUM_PROCESSES = 2

    
    def __init__(self, rule_set, model_xbrl=None, cntlr=None, include_nils=False, multi=False, async=False, cpunum=None):
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
        
        # Set up various queues
        self.message_queue = XuleMessageQueue(self.model, multi, async)
        self.calc_constants_queue = Queue()
        self.rules_queue = M_Queue()    
        #self.shutdown_queue = Queue()
        #self.stop_watch = 0

        self.all_constants = None
        self.all_rules = None
        self.constants_done = False 
        self.stopped_constants = False    
        

         # Set up list to track timings.  Each item should include a tuple of
        #   (type, name, time) where type = (constant, rules); name is name 
        #   of the type; time is the time taken for the defined to run
        self.times = Manager().list()
        
        # determine number of processors to use. The number of cpus should be one 
        #   less that what's available or 3 max
        if cpunum is None:
            self.num_processors = 2 if cpu_count() > 3 else cpu_count() - 2
            if self.num_processors < 0:
                self.num_processors = 0
        else:
            self.num_processors = int(cpunum) - 1
        
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

    @property
    def constant_store(self):
        return self._constants
    
    @constant_store.setter
    def constant_store(self, value):
        self._constants = value

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
        self.ignore_vars = []
        self.hash_table = {}
        self.with_filters = []
        self.other_filters = []
        self.alignment_filters = []

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
                raise XuleProcessingError(_("Internal error, cannot find constant '%s' in catalog" % (var_index)), self)
                #print("ERROR IN CONSTANT")
        if var_index >= len(self._vars):
            raise XuleProcessingError(_("Internal error, var index out of range. Index = %i, Number of vars = %i" % (var_index, len(self._vars))), self)
            #print("ERROR IN VARIABLE")
        else:
            return self._vars[var_index]    
    
    def find_var(self, var_name):
        #First look for the vairable in the current list of variables
        try:
            #The search is reversed so if there are multiple variables with the same name, we get the latest one.
            #This allows nested block expressions with same variable names,
            var_info =  next(var for var in reversed(self._vars) if var['name'] == var_name and var['index'] not in self.ignore_vars)
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

    
