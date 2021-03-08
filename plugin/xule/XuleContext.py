"""XuleContext

Xule is a rule processor for XBRL (X)brl r(ULE). 

The XuleContext module defines classes for managing the processing context. The processing context manages the rule set and stores data
for keeping track of the processing (including the iterations that are created when processing a rule).

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

$Change: 23204 $
DOCSKIP
"""
from .XuleRunTime import XuleProcessingError
from .XuleValue import XuleValue, XuleValueSet
from . import XuleUtility as xu
from arelle import FileSource
from arelle import ModelManager
from queue import Queue
from multiprocessing import Queue as M_Queue, Manager, cpu_count
import datetime
from time import sleep
import copy
import collections
from math import floor
from io import StringIO
import csv
import itertools
#tabulate is used for debugging reports.
try:
    import tabulate
    _has_tablulate = True
except ImportError:
    _has_tablulate = False

class XuleMessageQueue():
    """Message handler
    
    The XuleMessageQueue handles Arelle logging messages. When the processor is run in multiprocessing mode on a server, the messages are not directly 
    sent to Arelle. Instead they are sent on a message queue to handled by the master process. When the plugin is run in stand alone mode, the messages are
    sent to the Arelle logger.
    """
    _queue = None
    _model = None
    _multi = False
    _is_async = False
    _printlist = None
    
    '''
    use self.log to print to the queue
    use self._model to print directly
    '''
    def __init__(self, model, multi=False, is_async=False, cid=None):
        if multi:
            self._queue = M_Queue()
        if model is not None:
            self._model = model
        self._multi = multi
        self._is_async = is_async
        self._cid = cid
        self._printlist = []
        #if not hasattr(self._model, "logger"):
        #    print("Error during XuleMessageQueue init.  No logger available")
        
    def info(self, codes, msg, **args):
        self.log('INFO', codes, msg, **args)

    def warning(self, codes, msg, **args):
        self.log('WARNING', codes, msg, **args)

    def error(self, codes, msg, **args):
        self.log('ERROR', codes, msg, **args)
    
    def log(self, level, codes, msg, **args):
        if self._multi and self._queue is not None:
            # In multi processing mode, the log() call does not call the arelle logger but instead puts the arguments
            # on a queue. The process listening on the other end of the queue pulls the arguments off and does the
            # arelle logging. In order to send something on the queue, it must be pickleable. Arelle objects based on lxml
            # are not pickleable. The modelObject in the args is not picklable. So instead, we send the the objectIndex.
            # This is used on the other side of the queue (see def output) to translate the objectIndex back to a
            # modelObject. The objectIndex is the position in the modelXbrl.modelObjects list.
            if 'modelObject' in args:
                if hasattr(args['modelObject'], 'objectIndex'):
                    args['xuleObjectIndex'] = args['modelObject'].objectIndex
                del args['modelObject']

            self._queue.put((level, codes, msg, args))
        else:
            self.output(level, codes, msg, **args)

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
        #    return keep
        elif not self._is_async:
            self._printlist.append((level, codes, msg, args))
        else:
            self.output(level, codes, msg, **args)
        
        return keep

    def output(self, level, codes, msg, **args): 
        ''' output loop.
            haslogger determined by hasattr(xule_context.global_context, "logger")
        '''
        # handle 'extra' variable if exists
        #if "extra" in args:
        #    for name in args["extra"]:
        #        args[name] = args["extra"][name]
        args["cid"] = self._cid

        # restore the modelObject (lxml object) to args for access
        #   to detailed information for logging
        if 'xuleObjectIndex' in args:
            args['modelObject'] = self._model.modelObjects[args['xuleObjectIndex']]
            del args['xuleObjectIndex']

        if self._model is None:
            print("[%s] [%s] %s" % (level, codes, msg))
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
    """Global Context
    
    The processing context is divided into 2 parts: global context and the rule context. The global context manages the information for the processor
    that is not specific to rule. This includes:
        * command line options
        * the rule set
        * the model of the instance document
        * models for additional taxonomies
        * caching constants and functions
    """
    def __init__(self, rule_set, model_xbrl=None, cntlr=None, options=None):
        """Global Context constructor
        
        :param rule_set: The rule set
        :type rule_set: XuleRuleSet
        :param model_xbrl: The model for the instance document
        :type model_xbrl: ModelXbrl
        :param cntlr: The Arelle controller
        :type cntlr: cntlr
        :param options: The Arelle command line options used when Arelle was invoked
        :type options: optparse
        """
        self.options = options      
        self.cntlr = cntlr
        self.model = model_xbrl
        self.rules_model = None
        self.rule_set = rule_set
        #self.fact_index = None
        self.include_nils = getattr(self.options, "xule_include_nils", False)
        self._constants = {}
        self.preconditions = {}
        self.expression_cache = {}
        self.show_trace = False
        self.show_trace_count = False
        self.trace_count_file = None
        self.show_timing = False
        self.show_debug = False
        self.crash_on_error = False
        self.function_cache = {}
        self.no_cache = False
        self.precalc_constants = False
        self.expression_trace = dict()
        self.other_taxonomies = dict()
        
        # Set up various queues
        self.message_queue = XuleMessageQueue(self.model, getattr(self.options, "xule_multi", False), getattr(self.options, "xule_async", False), cid=id(self.cntlr))
        self.calc_constants_queue = Queue()
        self.rules_queue = M_Queue()    

        self.all_constants = None
        self.all_rules = None

        ## enable only tracking timings        
        # Set up list to track timings.  Each item should include a tuple of
        #   (type, name, time) where type = (constant, rules); name is name 
        #   of the type; time is the time taken for the defined to run
        
        if getattr(self.options, "xule_timing", False):
            self.times = Manager().list()
        
        # Determines the number of threads available for calculating a filing.  If undefined it should be the 
        #   number of processors available to the server divided by the number of threads.
        # If defined it should be that number (treated as an override)
        cpunum = getattr(self.options, "xule_cpu", None)
        if cpunum is None:
            self.num_processors = floor(cpu_count() / getattr(self.options, "xule-numthreads", 1))
            if self.num_processors < 1:
                self.num_processors = 1
        else:
            self.num_processors = int(cpunum)

        '''
        # determine number of processors to use. The number of cpus should be one 
        #   less that what's available or 3 max
        cpunum = getattr(self.options, "xule_cpu", False)
        if cpunum is None:
            self.num_processors = 2 if cpu_count() > 3 else cpu_count() - 2
            if self.num_processors < 0:
                self.num_processors = 0
        else:
            self.num_processors = int(cpunum) - 1
        '''

    @property
    def catalog(self):
        """The rule set catalog"""
        return self.rule_set.catalog
 
    def get_other_taxonomies(self, taxonomy_url):
        """Load a taxonomy

        :param taxonomy_url: Url for the taxonomy to load
        :type taxonomy_url: str
        :returns: A model of the loaded taxonomy
        :rtype: ModelXbrl
        
        Loads a taxonomy into an Arelle model from a url. The taxonomy is stored in the global context. On subsequent requests, will return the stored
        model for the taxonomy.
        """
        if taxonomy_url not in self.other_taxonomies:
            start = datetime.datetime.today()
            rules_taxonomy_filesource = FileSource.openFileSource(taxonomy_url, self.cntlr)            
            modelManager = ModelManager.initialize(self.cntlr)
            modelXbrl = modelManager.load(rules_taxonomy_filesource)
            if 'IOerror' in modelXbrl.errors:
                raise XuleProcessingError(_("Taxonomy {} not found.".format(taxonomy_url)))
            end = datetime.datetime.today()
            
            self.other_taxonomies[taxonomy_url] = modelXbrl                     

            if getattr(self.rules_model, "log", None) is not None:
                self.rules_model.log("INFO",
                                   "other-taxonomy", 
                                   "Load taxonomy time %s from '%s'" % (end - start, taxonomy_url))
            else:
                print("Taxonomy Loaded. Load time %s from '%s' " % (end - start, taxonomy_url))            
        
        return self.other_taxonomies[taxonomy_url]

    @property
    def constant_store(self):
        """Cache for storing constant values"""
        return self._constants
    
    @constant_store.setter
    def constant_store(self, value):
        self._constants = value

    @property
    def fact_index(self):
        if self.model is None:
            None
        else:
            return getattr(self.model, 'xuleFactIndex', dict())

    @fact_index.setter
    def fact_index(self, value):
        if self.model is not None:
            self.model.xuleFactIndex = value

class XuleRuleContext(object):
    """Rule Context
    
    The processing context is divided into 2 parts: global context and the rule context. The rule context manages the information specific to processing a
    rule. This includes:
        * variables
        * local expression cache
        * iteration table
        * facts used during processing of an iteration of a rule
        * tags created during processing of an iteration
        * processing flags
        
    A new rule context is created before processing a rule.
    """
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

    def __init__(self, global_context, rule_name=None, cat_file_num=None):
        """Rule Context constructor
        
        :param global_context: The global context
        :type global_context: XuleGlobalContext
        :param rule_name: The name of the rule being processed
        :type rule_name: str
        :param cat_file_num: The file number from the rule set
        """
        self.global_context = global_context
        self.rule_name = rule_name
        self.cat_file_num = cat_file_num
        
        self.iteration_table = XuleIterationTable(self)
        self.vars = collections.defaultdict(list)
        self.id_prefix = []  
        self.column_prefix = []   
        self.no_alignment = False
        self.ignore_vars = []
        self.nested_factset_filters = []
        self.other_filters = []
        self.alignment_filters = []
        self.trace_level = 0      
        self.trace = collections.deque()
        self.in_where_alignment = None
        self.build_table = False
        self.local_cache = {}
        self.look_for_alignment = False
        self.where_table_ids = None
        self.where_dependent_iterables = None
        self._constant_overrides = None
        
        self.iter_count = 0
        self.iter_pass_count = 0
        self.iter_message_count = 0
        self.iter_misaligned_count = 0
        self.iter_except_count = 0
        
        self.fact_alignments = collections.defaultdict(dict)

    @property
    def tags(self):
        return self.iteration_table.tags
    @tags.setter
    def tags(self, value):
        self.iteration_table.tags = value
        
    @property
    def facts(self):
        return self.iteration_table.facts
    @facts.setter
    def facts(self, value):
        self.iteration_table.facts = value
        
    @property
    def aligned_result_only(self):
        return self.iteration_table.aligned_result_only
    @aligned_result_only.setter
    def aligned_result_only(self, value):
        self.iteration_table.aligned_result_only = value

    @property
    def used_expressions(self):
        return self.iteration_table.used_expressions
    
    @used_expressions.setter
    def used_expressions(self,value):
        self.iteration_table.used_expressions = value

    @property
    def dependent_alignment(self):
        return self.iteration_table.dependent_alignment
    
    @property
    def constant_overrides(self):
        if self._constant_overrides is None:
            overrides = dict()
            for arg in getattr(self.global_context.options,'xule_arg', None) or tuple():
                arg_parts = arg.split('=')
                name = arg_parts[0]
                if len(name) > 0:
                    if len(arg_parts) > 1:
                        val = XuleValue(self, ''.join(arg_parts[1:]), 'string')
                    else:
                        val = XuleValue(self, None, 'none')
                    overrides[name] = val
            self._constant_overridess = overrides

        return self._constant_overridess

    def create_message_copy(self, table_id, processing_id):
        new_context = copy.copy(self)
        new_context.iteration_table = XuleIterationTable(self)
        new_context.iteration_table.add_table(table_id, processing_id)
        new_context.iteration_table.current_table.current_alignment= self.iteration_table.current_table.current_alignment
        new_context.facts = self.facts.copy()
        new_context.tags = self.tags.copy()

        # Convert tagged 'unbound' values to 'none' values. This can happen if there is a factset that does not bind
        # but still a message is produced. i.e. output x @a#a + @b#b message '{$a} + {$b}'. In this case if @b does not
        # bind the value of $b will be 'unbound'. When this is processed in the message, it will cause a stop iteration.
        for tag_name, tag_value in new_context.tags.items():
            if tag_value.type == 'unbound':
                new_tag_value = tag_value.clone()
                # Change the unbound to a none
                new_tag_value.type = 'none'
                new_context.tags[tag_name] = new_tag_value
        return new_context

    def add_tag(self, tag, value):
        self.tags[tag] = value

    def reset_iteration(self):
        """Reset the rule context for the next iteration of a rule"""
        self.vars = collections.defaultdict(list)
        self.id_prefix = []
        self.column_prefix = []
        self.aligned_result_only = False
        self.ignore_vars = []

        self.nested_factset_filters = []
        self.other_filters = []
        self.alignment_filters = []

        self.trace_level = 0
        self.trace = collections.deque()
        
        self.in_where_alignment = None
        self.build_table = False
        
        self.formula_left = None
        self.formula_right = None
        self.formula_difference = None

        self.iteration_table.used_expressions = set()

    def get_processing_id(self, node_id):
        return tuple(self.id_prefix) + (node_id,)   

    def get_column_id(self, node_id):
        if len(self.column_prefix) == 0:
            return node_id
        else:
            return tuple(self.column_prefix) + (node_id,)

    def potential_column_ids(self, node_id):
        for i in range(len(self.column_prefix), -1, -1):
            if i == 0:
                column_id = node_id
            else:
                column_id = tuple(self.column_prefix[:i]) + (node_id,)

            yield column_id

    def add_var(self, name, node_id, tag, expr):
        """Add a variable to the rule context
        
        :param name: The name of the vaiable
        :type name: str
        :param node_id: The expression node_id of the variable declaration. This is used to identify the variable.
        :type node_id: int
        :param tag: Identifies if the variable should also define a tag
        :type tag: bool
        :param expr: The expression which calculates the value for the variable
        :type expr: xule expression as a dict
                
        This only adds the variable declaration to the rule context. It does not calculate the variable or store the value of the variable.
        """
        var_info = {"name": name,
                    "tagged": tag,
                    "type": self._VAR_TYPE_VAR,
                    "expr": expr,
                    "calculated": False
                    }

        self.vars[node_id].append(var_info)
                  
        return var_info
        
    def add_arg(self, name, node_id, tag, value, number):
        """Add an argument (variable) to the rule context
        
        Arguments are just like variables, but they don't have an expression and they are already calculated.
        
        :param name: The name of the vaiable
        :type name: str
        :param node_id: The expression node_id of the variable declaration. This is used to identify the variable.
        :type node_id: int
        :param tag: Identifies if the variable should also define a tag
        :type tag: bool
        :param value: The value of the argument
        :type value: XuleValue
        :param number: Indicates if the argument is a single or multi value
        :type number: str
        """   
        var_info = {"name": name,
                    "tagged": tag,
                    "type": self._VAR_TYPE_ARG,
                    "calculated": True,
                    "value": value,
                    }

        self.vars[node_id].append(var_info)
        if tag is not None:
            self.tags[tag] = value
    
    def del_arg(self, name, node_id):
        """Removes an argument from the variable stack"""
        self.vars[node_id].pop()
        if len(self.vars[node_id]) == 0:
            del self.vars[node_id]

    def find_var(self, var_name, node_id, constant_only=False):
        """Finds a variable in the variable stack
        
        :param var_name: Name of the variable
        :type var_name: str
        :param node_id: The expression node_id of the variable declaration. This is used to identify the variable.
        :type node_id: int
        :param constant_only: A flag if only the constants should be searched
        :type constant_only: bool
        
        A variable can be one of:
            * declared variable
            * built in variable from an expression (i.e. $fact in a fact set expression)
            * a for loop variable
            * a function argument
            * a constant
        """
        if constant_only:
            var_info = None
        else:
            #var_processing_id = self.get_processing_id(node_id)
            var_processing_id = node_id
            var_stack = self.vars.get(var_processing_id)
            var_info = var_stack[-1] if var_stack is not None else None
        if var_info is None:
            #this is a constant
            if var_name in self._BUILTIN_CONSTANTS:
                cat_const =  self.global_context.catalog['constants'].get(var_name)
                if not cat_const:
                    #the variable reference is not in the catalog for constants and it is not in the list of declared variables
                    raise XuleProcessingError(_("Constant declaration for built in constant not found for '$%s'" % var_name), self)
                else:
                    var_info = self.global_context._constants.get(node_id)
                    if var_info is None:
                        ast_const = self.global_context.rule_set.getItem(cat_const)
                        var_value = self._BUILTIN_CONSTANTS[var_name](self)
                        var_info = {"name": var_name,
                                    "tagged": var_name,
                                    "type": self._VAR_TYPE_CONSTANT,
                                    "expr": ast_const,
                                    "calculated": True,
                                    "value": var_value,
                                    }
                        self.global_context._constants[node_id] = var_info
            else:
                var_info = self.global_context._constants.get(node_id)
                if not var_info:
                    #this is the first time for the constant. Need to retrieve it from the catalog
                    cat_const =  self.global_context.catalog['constants'].get(var_name)
                    if not cat_const:
                        #the variable reference is not in the catalog for constants and it is not in the list of declared variables
                        print("Looking for %s - %s - %s" % (var_name, node_id, var_processing_id))
                        print(self.iteration_table.to_csv())
                        raise XuleProcessingError(_("Variable declaration not found for '$%s'" % var_name), self)
                    else:
                        ast_const = self.global_context.rule_set.getItem(cat_const)
                        var_info = {"name": var_name,
                                    "tagged": var_name,
                                    "type": self._VAR_TYPE_CONSTANT,
                                    "expr": ast_const,
                                    "calculated": False,
                                    }
                        self.global_context._constants[node_id] = var_info
                        
        return var_info                
    
    def filter_add(self, filter_type, filter_dict):
        """Add a factset filter to the filter stack
        
        :param filter_type: The type of filter being added.
        :type filter_type: str
        :param filter_dict: The aspect filters being added to the stack
        :type filter_dict: dict
        
        Factset filters are used for nested factsets. When the outer factset is evaluated, the aspect filters are added to the filter stack in the 
        rule context. Then the inner factset is evaluated, these filters are used to determine the facts that match the inner factset.
        """
        self.nested_factset_filters.append((filter_type, filter_dict))

    def filter_del(self):   
        """Pops a factset filter from the filter stack"""        
        self.nested_factset_filters.pop()
        
    def get_current_filters(self):
        """Returns the factset filters currently onthe filter stack
        
        :returns: A 2 item tuple:
                    1. A dictionary of nested factset filters
                    2. A dictionary of other factset filters.
        :rtype: dict
        """
        filter_aspects = set()
        nested_factset_filters = dict()
        other_filters = dict()
        
        for filter_tup in reversed(self.nested_factset_filters):
            filter_type = filter_tup[0]
            filter_dict = filter_tup[1]
            
            for filter_info, filter_member in filter_dict.items():
                # 1 = the aspect name
                if filter_info[1] not in filter_aspects:
                    filter_aspects.add(filter_info[1])
                    if filter_type == 'nested':
                        nested_factset_filters[filter_info] = filter_member
                    else:
                        other_filters[filter_info] = filter_member
                    
        return nested_factset_filters, other_filters    
    
    def find_function(self, function_name):
        """Find a function from the rule set
        
        :param function_name: The name of the function to find
        :type function_name: str
        :returns: A function information dictionary.
        :rtype: dict
        
        The functions in the rule set are xule defined functions created in the rules by the rule author. This method looks up the function
        in the rule set and returns the function expression.
        """
        cat_function = self.global_context.rule_set.catalog['functions'].get(function_name)
        if not cat_function:
            return None
        
        ast_function = self.global_context.rule_set.getItem(cat_function)
        function_info = {"name": function_name,
                         "function_declaration": ast_function}
        return function_info   
    
    def get_other_taxonomies(self, taxonomy_url):
        """Load a taxonomy
        
        See :func:`XuleGlobalContext.get_other_taxonomies`
        """
        return self.global_context.get_other_taxonomies(taxonomy_url)
    
    # The build in constants are commented out. They were originally here for performance reasons when getting the extension namespace.
    # However, when the .entry-point-namespace property was implemented the performance problem was no longer an issue by defining
    # the constant $extension_ns = taxonomy().entry-point-namespace.

    #built in constants
    # def _const_extension_ns(self):
    #     for doc in self.model.modelDocument.hrefObjects:
    #         if doc[0].elementQname.localName == 'schemaRef' and doc[0].elementQname.namespaceURI == 'http://www.xbrl.org/2003/linkbase':
    #             values = XuleValueSet()
    #             values.append(XuleValue(self, doc[1].targetNamespace, 'uri'))
    #             return values
        
    #     values = XuleValueSet()
    #     values.append(XuleValue(self, None, 'unbound'))
    #     return values
    
    # def _const_ext_concepts(self):
    #     extension_ns_value_set = self._const_extension_ns()
    #     if len(extension_ns_value_set.values) > 0:
    #         extension_ns = extension_ns_value_set.values[None][0].value
    #     else:
    #         raise XuleProcessingError(_("Cannot determine extension namespace."), self)
        
    #     concepts = set(XuleValue(self, x, 'concept') for x in self.model.qnameConcepts.values() if (x.isItem or x.isTuple) and x.qname.namespaceURI == extension_ns)
        
    #     return XuleValueSet(XuleValue(self, frozenset(concepts), 'set'))

    # def _const_ext_concept_local_name(self):
    #     extension_ns_value_set = self._const_extension_ns()
    #     if len(extension_ns_value_set.values) > 0:
    #         extension_ns = extension_ns_value_set.values[None][0].value
    #     else:
    #         raise XuleProcessingError(_("Cannot determine extension namespace."), self)
        
    #     base_local_names = list(XuleValue(self, local_part, 'string') for local_part in set(concept.qname.localName for concept in self.model.qnameConcepts.values() if (concept.isItem or concept.isTuple) and concept.qname.namespaceURI == extension_ns))
        
    #     return XuleValueSet(XuleValue(self, tuple(base_local_names), 'list'))

    _BUILTIN_CONSTANTS = {#'extension_ns': _const_extension_ns,
                          #'ext_concepts': _const_ext_concepts,
                          #'EXT_CONCEPT_LOCAL_NAMES': _const_ext_concept_local_name
                          }    

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
        return getattr(self.global_context.options, "xule_trace", False)
        #return self.global_context.show_trace

    @property
    def show_trace_count(self):
        return getattr(self.global_context.options, "xule_trace_count", False)
        #return self.global_context.show_trace_count
    
    @property
    def function_cache(self):
        return self.global_context.function_cache
  
    @property
    def expression_trace(self):
        return self.global_context.expression_trace

class XuleIterationTable:
    """Iteration table
    
    The iteration table keeps track of iterations for a single rule. Iterations are created from evaluating iterable expressions. These include:
        * factsets
        * for loops
        * aggregation functions
        * potentially built in functions
        
    The iteration table is in fact a collection of :class:`XuleContext.XuleIterationSubTable`s. During the processing of a rule, sub tables are created 
    to isolate certain expression evaluations. One of the sub table is always identified as the current table. When operations are performed on the iteration
    table, it will perform the operation on the current sub table.
    """
    def __init__(self, xule_context):
        """Iteration Table Constructor
        
        :param xule_context: The rule context
        :type xule_context: XuleContext
        """
        self._ordered_tables = collections.OrderedDict()
        
        #This is a dictionary of which table the column is in.
        #self._columns = collections.defaultdict(list)
        self._columns = {}
        self.xule_context = xule_context
        #self.add_table(0)
        self.main_table_id = None

    @property
    def current_table(self):
        if self.is_empty:
            return None
        else:
            #return self._tables[-1]
            table_processing_id = next(reversed(self._ordered_tables))
            return self._ordered_tables[table_processing_id]
    
    @property
    def current_alignment(self):
        for table_processing_id in reversed(self._ordered_tables):
            if not self._ordered_tables[table_processing_id].is_empty:
                return self._ordered_tables[table_processing_id].current_alignment
        return None
        
        '''
        for i in range(len(self._tables) - 1, -1, -1):
            if not self._tables[i].is_empty:
                return self._tables[i].current_alignment
        return None
        '''

    @property
    def any_alignment(self):
        for table_processing_id in reversed(self._ordered_tables):
            if not self._ordered_tables[table_processing_id].is_empty and self._ordered_tables[table_processing_id].current_alignment is not None:
                return self._ordered_tables[table_processing_id].current_alignment
        return None
    
    @property
    def is_empty(self):
        return len(self._ordered_tables) == 0

    @property
    def tags(self):
        if self.is_empty:
            return {}
        else:
            return self.current_table.tags
    @tags.setter
    def tags(self, value):
        self.current_table.tags = value
        
    @property
    def facts(self):
        if self.is_empty:
            return collections.OrderedDict()
        else:
            return self.current_table.facts
    @facts.setter
    def facts(self, value):
        self.current_table.facts = value    

    @property
    def aligned_result_only(self):
        if self.is_empty:
            return False
        else:
            return self.current_table.aligned_result_only
        
    @aligned_result_only.setter
    def aligned_result_only(self, value):
        if self.is_empty:
            pass
        else:
            self.current_table.aligned_result_only = value

    @property
    def used_expressions(self):
        if self.is_empty:
            return []
        else:
            return self.current_table.used_expressions
        
    @used_expressions.setter
    def used_expressions(self, value):
        if self.is_empty:
            pass
        else:
            self.current_table.used_expressions = value

    @property
    def is_dependent(self):
        if self.is_empty:
            return False
        else:
            return self.current_table.is_dependent
    
    @property
    def dependent_alignment(self):
        if self.is_empty:
            return None
        else:
            return self.current_table.dependent_alignment

    def __len__(self):
        return len(self._tables)
    
    def current_value(self, processing_id, xule_context):
        """Get current value for a column
        
        :param processing_id: The processing id of the colum. This is based on the node_id of the expression that generates the values for the column
        :type processing_id: tuple
        :param xule_context: The rule context
        :type xule_context: XuleContext
        
        This method gets the current value for a column on the current sub table. If the column is not on the table it will return Nonee.
        """
        if processing_id in self._columns:
            #return self._columns[processing_id][-1].current_value(processing_id, xule_context)
            return self._columns[processing_id].current_value(processing_id, xule_context)
        else:
            return None    

    def next(self, table_id):
        """Next iteration
        
        :param table_id: The id of the sub table
        :type table_id: int
        """
        table_processing_id = self.xule_context.get_processing_id(table_id)
        if table_processing_id in self._ordered_tables:
            if not self._ordered_tables[table_processing_id].is_empty:
                deleted_cols = self._ordered_tables[table_processing_id].next(self.xule_context)
                #remove dependent columns that were deleted
                if deleted_cols is not None and len(deleted_cols) > 0:
                    for del_col in deleted_cols:
                        try:
                            del self._columns[del_col]
                        except KeyError:
                            pass                    
                        '''
                        self._columns[del_col].pop()
                        if len(self._columns[del_col]) == 0:
                            del self._columns[del_col]
                        '''
                       
                '''THIS IS NEEDED SO THE TOP TALBE BECOMES EMPTY, BUT IS IT POSSIBLE THAT A SUB TABLE CAN BE EMPTY BUT THE COLUMN SHOULD BE THERE????'''
                if self._ordered_tables[table_processing_id].is_empty:
                    self.del_table(table_id)
    
                if getattr(self.xule_context.global_context.options, "xule_debug_table", False):
                #if self.xule_context.global_context.show_debug_table:
                    print("After Next")
                    print(self.to_csv())

    def add_column(self, ast_node, table_id, processing_id, values, xule_context):
        """Add a column to a table
        
        :param ast_node: The rule expression for the column
        :type ast_node: xule expression as a dict
        :param table_id: The table id to add the column to
        :type table_id: int
        :param processing_id: The processing id of the colum. This is based on the node_id of the expression that generates the values for the column
        :type processing_id: tuple
        :param values: The values that are being added as the column
        :type values: XuleValueSet
        :param xule_context: The rule context
        :type xule_context: XuleContext  
        """
        if getattr(self.xule_context.global_context.options, "xule_debug_table", False):
            print(ast_node['exprName'] + " " + str(ast_node['node_id']))
            print("node id", ast_node['node_id'])
            print("Before Add (table: %i)" % table_id)
            print(self.to_csv())
            
        table_processing_id = self.xule_context.get_processing_id(table_id)
        if table_processing_id not in self._ordered_tables:
            for k, v in self._ordered_tables.items():
                print("table", k, v.table_id)
            raise XuleProcessingError(_("Table %i has not been created. Processing id: %s. Adding node: %s (id:%s)" % (table_id, table_processing_id, ast_node['exprName'], ast_node['node_id'])), self.xule_context)
            #self.add_table(table_id, processing_id)
        
        sub_table = self._ordered_tables[table_processing_id]

        if processing_id not in self._columns:
            #self._columns[processing_id].append(sub_table)
            self._columns[processing_id] = sub_table
        else:
            print(processing_id)
            raise XuleProcessingError(_("Internal error: adding a column for '%s'(%s) that is already on the table," % (ast_node.getName(), ast_node.node_id)), self.xule_context)

        sub_table.add_column(ast_node, processing_id, values, xule_context)

        if getattr(self.xule_context.global_context.options, "xule_debug_table", False):
        #if self.xule_context.global_context.show_debug_table:
            print(ast_node['exprName'] + " " + str(ast_node['node_id']))
            print("After Add (table: %i)" % table_id)
            print(self.to_csv())


    def add_table(self, table_id, processing_id, is_aggregation=False):
        """Creat a new sub table
        
        :param table_id: The table id for the new table
        :type table_id: int
        :param processing_id: The processing id of the colum. This is based on the node_id of the expression that generates the values for the column
        :type processing_id: tuple
        :param is_aggregation: An indicator if the new sub table is for calculating an aggregation
        :type is_aggregation: bool
        
        DOCSKIP
        THE is_aggregation ARGUMENT IS NO LONGER NEED. THIS CAN BE REMOVED.
        DOCSKIP
        """
        #the table is always dependent if the current table is dependent 
        parent_table = None       
        if not self.is_empty:
            parent_table = self.current_table      

        child_table = XuleIterationSubTable(table_id, self, processing_id, is_aggregation=is_aggregation)
        # copy the tags down to the sub table
        child_table.tags = self.tags.copy()
        table_processing_id = self.xule_context.get_processing_id(table_id)
        self._ordered_tables[table_processing_id] = child_table

        if parent_table is not None:
            child_table.dependent_alignment = parent_table.dependent_alignment
        else:
            self.main_table_id = table_id
            
        return child_table

    def del_table(self, table_id):
        """Delete sub table
        
        :param table_id: The table_id of the sub table to delete
        :type table_id: int
        """
        table_processing_id = self.xule_context.get_processing_id(table_id)
        if table_processing_id not in self._ordered_tables:
            #there is no table, so just return
            return
        
        #remove the columns from the manager for the table that is being deleted
        for column_key in self._ordered_tables[table_processing_id]._columns:
            try:
                del self._columns[column_key]
            except KeyError:
                pass
            '''
            self._columns[column_key].pop()
            if len(self._columns[column_key]) == 0:
                del self._columns[column_key]
            '''
        #remove the table
        del self._ordered_tables[table_processing_id]        
    
    def is_table_empty(self, table_id):
        table_processing_id = self.xule_context.get_processing_id(table_id)
        return table_processing_id not in self._ordered_tables or self._ordered_tables[table_processing_id].is_empty

    def to_csv(self):
        table_strings = [self.xule_context.rule_name]
        if not self.is_empty:
            print("Columns: " + (" | ".join([str((str(t.processing_id), k)) for k, t in self._columns.items()])))
            for table_id, table in self._ordered_tables.items():
                table_strings.append(table.to_csv())
        else:
            print("NO TABLES")
        
        return "\n".join(table_strings)

class XuleIterationSubTable:
    """Iteration sub table
    
    An iteration sub table contains a set of columns of values. The values are the result of evaluating iterable 
    expressions in a rule. The columns are organized by alignemnt. The alignment is the value pairs of aspect 
    name and aspect value for the aspects that are implicitly matched. The alignment is determined when evaluating 
    a factset. Factsets are the only expressions that produce aligned valeus. Other iterable expressions will have 'none' 
    aligned values. Alignment is stored as a dictionary keyed by the aspect name. For the 'none' alignment, the key is None.
    
    The sub table is processed for each alignment. Within an alignment, there may be multiple iterations. The sub table keeps track of a 
    current iteration. The current iteration identifies for each column which value to use. The current iteration is stored as
    a dictionary keyed by column id. The value is the index to the current item in the column. When a table is 'nexted' the 
    current iteration is updated to select the appropiate values in each column.
    
    The sub table keeps track of which alignments and iterations have been processed. When the 'next' operation is at the end, the current iteration 
    will be None which marks the table as empty.
    """    
    def __init__(self, table_id, iteration_table, processing_id=None, is_dependent=False, is_aggregation=False):
        """Iteration sub table constructor
        
        :param table_id: The table id of the new sub table
        :type table_id: int
        :param iteration_table: The iteration table object that creates this sub table
        :type iteration_table: XuleIterationTable
        :param processing_id: The processing id of the operation that is creating this table
        :type processing_id: tuple
        :param is_dependent: Indicator if this table is from an expression that is dependent on another expression
        :type is_dependent: bool
        :param is_aggregation: Indicator if the sub table is being created for an aggregation function
        :type is_aggregation: bool        
        """
        self.is_aggregation = is_aggregation
        #self.is_dependent = is_dependent
        self.processing_id = processing_id
        self.table_id = table_id
        
        self._table = dict()
        self._columns = dict()
        
        self.current_alignment = None
        #These properties keep track of which alignments have been processed and which are waiting to be processed
        self._unprocessed_alignments = set()
        self._processed_alignments = set()
        self._unprocessed_none_alignment = False
        #saved_alignment_queue is a copy of the alignment queues when the current alignment is changed when adding a dependent colum
        self._saved_alignment_queues = None
        #dependent_alignment_switch identifies the master column for a dependent column when alignment was switched.
        self._dependent_alignment_switch = None
        
        self._ordered_columns = []
        self._column_dependencies = collections.defaultdict(set)

        self._current_iteration = dict()
        self._column_data = dict()
        self._used_columns = set()
        
        self.tags = dict()
        #self.facts = []
        self.facts = collections.OrderedDict()
        self.aligned_result_only = False
        self.used_expressions = set()
        
        self.processed_alignments = set()
        
        self.dependent_alignment = None
        
        self._iteration_table = iteration_table
        
    @property
    def is_empty(self):
        #return len(self._table) == 0
              
        return len(self._current_iteration) == 0

    @property
    def is_dependent(self):
        return self.dependent_alignment is not None

    def del_current(self):
        return self.next()

    def make_dependent(self):
        if self.dependent_alignment is None:
            self.dependent_alignment = self.current_alignment

    def current_value(self, processing_id, xule_context):
        """Get current value for a column
        
        :param processing_id: The processing id of the colum. This is based on the node_id of the expression that generates the values for the column
        :type processing_id: tuple
        :param xule_context: The rule context
        :type xule_context: XuleContext
        """        
        if processing_id in self._columns:
            self._used_columns.add(processing_id)
            row_alignment, row_index = self._current_iteration[processing_id]
            if row_index is None:
                return XuleValue(xule_context, None, 'unbound')
            else:
                return self._column_data[processing_id].values[row_alignment][row_index]
        else:
            return None

    def next(self, xule_context):   
        """Next iteration
        
        :param xule_context: The rule context
        :type xule_context: XuleContext
        """        
        deleted_cols = set()
           
        if not self.is_empty:
            no_more_iterations = True
            
            #advance the next iterations
            for col_id in reversed(self._ordered_columns):
                row_alignment, row_index = self._current_iteration[col_id]
                if row_index is None:
                    #This column has no data for the current iteration
                    
                    #print("NEXT", self.table_id, "COLUMN IS EMPTY", col_id)
                    
                    continue
                #if col_id in self._used_columns:
                #if col_id in xule_context.used_expressions:
                if col_id in self.used_expressions:
                    if (self._dependent_alignment_switch is None or
                        col_id not in self._column_dependencies or
                        self._dependent_alignment_switch not in self._column_dependencies[col_id] or
                        (len(self._unprocessed_alignments) == 0 and not self._unprocessed_none_alignment)):
                        
                        if (self._dependent_alignment_switch is not None and
                            (len(self._unprocessed_alignments) == 0 and not self._unprocessed_none_alignment)):
                            #need to reset the alignment queues and turn off the dependent alignment switch. 
                            #These properties were set during the add of the dependent column
                            self.current_alignment = None
                            self._processed_alignments = self._saved_alignment_queues[1]
                            self._unprocessed_alignments = self._saved_alignment_queues[2]
                            self._unprocessed_none_alignment = self._saved_alignment_queues[3]
                            self._saved_alignment_queues = None
                            self._dependent_alignment_switch = None
                            
                            #print("NEXT", self.table_id, "RESET ALIGNMENT DURING ALIGNMENT SWITCH")
            
                        #normal column increment
                        if row_index == len(self._column_data[col_id].values[row_alignment]) - 1:
                            #the current iteration is on the last value
                            #reset to the begining
                            self._current_iteration[col_id] = (row_alignment, 0)
                            deleted_cols |= self.remove_dependent_columns(col_id)
                            
                            #print("NEXT", self.table_id, "ON LAST VALUE", col_id)
                            
                            continue
                        else:
                            #bump up to the next row
                            self._current_iteration[col_id] = (row_alignment, row_index + 1)
                            deleted_cols |= self.remove_dependent_columns(col_id)
                            no_more_iterations = False
                            
                            #print("NEXT", self.table_id, "COLUMN INCREMENT", col_id)
                            
                            break
                    else:
                        #The column is a master where the dependent column switched the alignment.
                        #In this case, instead of incrementing, the alignment will be switched
                        self.next_alignment()
                        self.set_current_iteration(col_id)
                        no_more_iterations = False
                        
                        #print("NEXT", self.table_id, col_id, "NEXT ALIGNMENT DURING DEPENDENT ALIGNMENT SWITCH")
                        
                        break
                else:
                    #This column wasn't used, reset it
                    self._current_iteration[col_id] = (row_alignment, 0)
                    deleted_cols |= self.remove_dependent_columns(col_id)
                    
                    #print("NEXT", self.table_id, "COLUMN NOT USED", col_id)
                    
                    continue
             
            if no_more_iterations:
                self.next_alignment()

                #print("NEXT", self.table_id, "NOT MORE ITERATIONS - NEXT ALIGNMENT")

                if not self.is_empty:
                    self.set_current_iteration()

                            
            #reset tags and facts
            self.tags = dict()
            #self.facts = []
            self.facts = collections.OrderedDict()
            #reset used columns for the next iteration
            self._used_columns = set()
        
        return deleted_cols

    def remove_dependent_columns(self, col_id):
        """Delete columns that were dependent on the column that is having its value changed
        
        :param col_id: The processing id of the master column
        :type col_id: tuple
        
        When a column value is changed (next iteration) or the column is deleted, any column that is dependent on it is 
        delete from the sub table. This will force the expressions for the dependent columns to be re-evaluated based 
        on the new value for the 'master' column.
        """
        deleted_cols = set()
        if col_id in self._column_dependencies:
            for dependent_col_id in self._column_dependencies[col_id]:
                #The column may already have been deleted from a previous dependency.
                if dependent_col_id in self._columns:
                    deleted_cols.add(dependent_col_id)
                    del self._columns[dependent_col_id]
                    self._ordered_columns.remove(dependent_col_id)
                    del self._column_data[dependent_col_id]
                    '''The deletion of self._current_iteration isn't really necessary because self._columns determines if a column is in a table or not. So the extra
                       data in self._current_iteration doesn't cause a problem. Removing it would is nice just to keep all the column information tidy'''
                    del self._current_iteration[dependent_col_id]
                
            del self._column_dependencies[col_id]
        
        if len(self._column_dependencies) == 0:
            self.dependent_alignment = None
        
        return deleted_cols
    
    def next_alignment(self):
        """Advance to the next alignment in the sub table"""
        #All the rows for the alignment are finished, go to the next alignment
        self._processed_alignments.add(self.current_alignment)
        if len(self._unprocessed_alignments) > 0:
            #pick up the next alignment
            self.current_alignment = self._unprocessed_alignments.pop()
        else:
            if self._unprocessed_none_alignment:
                self._unprocessed_none_alignment = False
                self.current_alignment = None
            else:
                #This is the end of the table
                #set the current iteration to an empty dictionary. This signifies that the table is empty.
                self._current_iteration = dict()        
        #reset the dependent_alignment
        self.dependent_alignment = None
    
    def set_current_iteration(self, starting_col_id=None):
        #set up the new current_iteration
        for col_id in reversed(self._ordered_columns):
            if col_id == starting_col_id:
                break
            
            col_data = self._column_data[col_id]
            if self.current_alignment in col_data.values:
                self._current_iteration[col_id] = (self.current_alignment, 0)
            elif None in col_data.values:
                self._current_iteration[col_id] = (None, 0)
            else:
                self._current_iteration[col_id] = (None, None)

    def add_column(self, ast_node, processing_id, value_set, xule_context):    
        """Add a column to the sub table
        
        :param ast_node: The rule expression for the column
        :type ast_node: xule expression as a dict
        :param processing_id: The processing id of the colum. This is based on the node_id of the expression that generates the values for the column
        :type processing_id: tuple
        :param value_set: The values that are being added as the column
        :type value_set: XuleValueSet
        :param xule_context: The rule context
        :type xule_context: XuleContext  
        """        
        if processing_id in self._columns:
            raise XuleProcessingError(_("Internal error: Trying to add an existing column to the iteratoin table"), self.xule_context)

        #add columns
        self._columns[processing_id] = ast_node
        self._ordered_columns.append(processing_id)
        self._column_data[processing_id] = value_set

        #update master columns for dependencies
        is_dependent = False      

        for dep in ast_node['dependent_iterables']:
            #don't include the self reference to the current node
            ''''THIS NEEDS TO BE REMOVED IN THE POST PARSE'''
            if ast_node['node_id'] != dep['node_id']:
                is_dependent = True
                #The only time the master column will not be in the table is if the dependent column is in an isolated table and the master is not. In this case,
                #the dependency does not matter. This may also happen if the master column is in a conditional (if statement) that is not executed.

                # The node id of the master needs to be checked agains a list of potential processing ids based on the column_prefix. This happens becasue
                # the master node may or may not be prefixed (which is used for the filter expressions).
                for master_processing_id in self._iteration_table.xule_context.potential_column_ids(dep['node_id']):
                    #master_processing_id = xule_context.get_processing_id(dep['node_id'])
                    if master_processing_id in self._columns:
                        #dep_processing_id = xule_context.get_processing_id(dep.node_id)
                        self._column_dependencies[master_processing_id].add(processing_id)
                        break

        if is_dependent:
            self.dependent_alignment = self.current_alignment
            #If the the dependent column has unprocessed aligned values and the current alignment is none, then we will switch alignments. But for now, we save the state of the
            #alignment queues
            if (not self.is_empty and 
                self.current_alignment is None and                
                self._saved_alignment_queues is None and
                len(value_set.values.keys() - {None,} - self._processed_alignments) > 0):
                #len(value_set.values.keys() - self._processed_alignments) > 0):
                self._saved_alignment_queues = (self.current_alignment,
                                                        self._processed_alignments.copy(), #this makes a copy
                                                        self._unprocessed_alignments.copy(),
                                                        self._unprocessed_none_alignment)
                self._dependent_alignment_switch = processing_id

        #add alignments
        #get the value alignments that are not already processed and not current.
        unprocessed_column_alignments = value_set.values.keys() - self._processed_alignments - {None,}
        if not self.is_empty and self.current_alignment is not None:
            unprocessed_column_alignments -= {self.current_alignment,}
        self._unprocessed_alignments |= unprocessed_column_alignments
        
        #determine if None alignemnt should be flagged to be processed. The None alignment is kep out of the _unproessed_aligments, so it can always be processed last.
        #the _unproessed_none_alignment flag is used to determine if None alignment should be proessed.
        if None in value_set.values:
            if self.is_empty:
                self._unprocessed_none_alignment = True
            elif None not in self._processed_alignments and self.current_alignment is not None:
                self._unprocessed_none_alignment = True
        
        if self.is_empty:
            if len(self._unprocessed_alignments) == 0:
                if self._unprocessed_none_alignment:
                    self.current_alignment = None
                    self._unprocessed_none_alignment = False
                else:
                    pass
                    #return #there is nothing to add to the table, the value_set is empty
            else:
                self.current_alignment = self._unprocessed_alignments.pop()
        else:
            #change alignment if the current alignment is None and the added column has an unprocessed alignment
            if self.current_alignment is None:
                if len(self._unprocessed_alignments) > 0:
                    #Alignments must have been added to the unprocessed alignment queue. Switch to an alignment
                    #the alignment is switched
                    self.current_alignment = self._unprocessed_alignments.pop()
                    #We were on the None alignment, but now am switching to a non none alignment, so eventually we will need to go back process the None alignments
                    self._unprocessed_none_alignment = True

        #add the current iteration position
        if self.current_alignment in value_set.values:
            self._current_iteration[processing_id] = (self.current_alignment, 0)
        elif None in value_set.values:
            self._current_iteration[processing_id] = (None, 0)
        else:
            self._current_iteration[processing_id] = (None, None)


    def to_csv(self):
        """Create a displayable version of the sub table
        
        This is used for debugging purposes. This will create a string representation of the sub table
        DOCSKIP
        THIS SHOULD BE RENAMED TO display_table. IT USED TO CREATE A CSV OUTPUT, BUT NO CREATES A STRING REPRESENTATION.
        DOCSKIP
        """
        table_string = ""
        #write table title
        table_header = ["TABLE (%i): Processing_id %s - aggregation %s - dependent %s - %i" % (self.table_id, str(self.processing_id), 
                                                                                               "yes" if self.is_aggregation else "no", 
                                                                                               "yes" if self.is_dependent else "no",
                                                                                               len(self.facts))]
        table_string += ' '.join(table_header)
        
        if not self.is_empty:
            #set up table container. If tabulate, the container is a list, otherwise, it is a csv object.
            if _has_tablulate:
                table = []
            else:
                o = StringIO()
                table = csv.writer(o)

            #build list of alignments. These are displayed first with an id number.
            
            #alignments = tuple((x,y) for x, y in enumerate({self.current_alignment,} | self._unprocessed_alignments | ({None,} if self._unprocessed_none_alignment else set())))
            #The none alignment will always be id 0.
            alignments = ((0, None),) if self._unprocessed_none_alignment or self.current_alignment is None else tuple()
            alignments += tuple((x,y) for x, y in enumerate(({self.current_alignment,} | self._unprocessed_alignments) - {None,}, start=1))
            for num, alignment in alignments:
                cur_alignment = "C" if alignment == self.current_alignment else " "
                if alignment is None:
                    row = [cur_alignment, str(num), "ALIGNMENT: None",]
                else:
                    row =[cur_alignment, str(num), "ALIGNMENT: " + str(alignment),]
                self.write_row(table, row)
                
            if _has_tablulate:
                table_string += "\n" + self.write_table(table)
            else:
                table_string += o.getvalue()
                o.close()


            if _has_tablulate:
                table = []
            else:
                o = StringIO()
                table = csv.writer(o) 

            #show list of values
            #build the header for the values. This will be the name of the expression and the col_id
            header = ['A',]
            for col_id in self._ordered_columns: 
                header += [self._columns[col_id]['exprName'] + " " + str(col_id)]
            self.write_row(table, header)
            #go through each alignment
            for alignment_num, alignment in alignments:
                #Each column may have a different number of rows. Loop indefinitely until all columns for the alignment are exhausted.
                for row_num in itertools.count():
                    #create row list.
                    row = []
                    row.append(alignment_num)
                    row_is_empty = True
                    #Go through each column              
                    for col_pos, col_id in enumerate(self._ordered_columns):
                        current_col_alignment, current_col_index = self._current_iteration[col_id]
                        if current_col_alignment == alignment and current_col_index == row_num:
                            is_current = "C "
                        else:
                            is_current = "  "
                        
                        if alignment in self._column_data[col_id].values:
                            if row_num < len(self._column_data[col_id].values[alignment]):    
                                row_is_empty = False
                                row_value = self._column_data[col_id].values[alignment][row_num]
                                if row_value.type == 'string':                                    
                                    row.append(is_current + row_value.format_value()[:10])
                                else:
                                    row.append(is_current + row_value.format_value())
                            else:
                                #All the rows of the column have been processed.
                                row.append('')
                        else:
                            #column does not have this alignment
                            row.append('')
                    if row_is_empty:
                        #all columns are exhausted
                        break
                    self.write_row(table, row)

            if _has_tablulate:
                table_string += "\n" + self.write_table(table)
            else:
                table_string += o.getvalue()
                o.close()
        else:
            table_string += "\nEMPTY"

        return table_string
        
        
    def write_row(self, table, row):
        if _has_tablulate:
            table.append(row)
        else:
            table.writerow(row)
            
    def write_table(self, table):
        return tabulate.tabulate(table, tablefmt=getattr(self._iteration_table.xule_context.global_context.options, "xule_debug_table_style", None) or 'grid')
  