import collections
import copy

class XuleProcessingError(Exception):
    def __init__(self, msg, xule_context=None):
        self.msg = msg
        self.xule_context = xule_context
        
    def __str__(self):
        if hasattr(self.xule_context, 'rule_name'):
            return "Rule: %s - %s" % (self.xule_context.rule_name, self.msg)
        else:
            return self.msg
        
class XuleResult:
    def __init__(self, value, value_type='unknown', *args, meta=None, alignment=None, tags=None, facts=None, var_refs=None, from_model=False):
        if len(args) != 0:
            import inspect
            print(inspect.stack()[1][3])
            raise XuleProcessingError(_("Internal error, recieved unamed argument to XuleResult __init__"))
        
        self.value = value
        self.type = value_type
        #This the common aspects for fact alignment
        if meta is not None:
            self.meta = meta
        else:
            self.meta = [alignment, 
                         tags if tags else {}, 
                         facts if facts else [], 
                         var_refs if var_refs else {}, 
                         from_model]
        #self.alignment = alignment
        #self.facts = facts if facts else []
        #self.tags = tags if tags else {}
        self.trace = []
        '''A varible on a result is a reference to the variable in the processing context and the index of the result
           that contains the value. This is a dictionary indexed by the position in the context variable stack, with the value
           being the result index.'''
        #self.vars = var_refs if var_refs else {}
        #self.from_model = from_model

    ''' 
    def __str__(self):
        return "(%s)%s" % (self.type, self.value)
    '''
    #Meta data constants
    _ALIGNMENT = 0
    _TAGS = 1
    _FACTS = 2
    _VARS = 3
    _FROM_MODEL = 4
    _SKIPPED_RESULTS = 5

    @property
    def alignment(self):
        return self.meta[self._ALIGNMENT]
    @alignment.setter
    def alignment(self, value):
        self.meta[self._ALIGNMENT] = value
    
    @property
    def tags(self):
        return self.meta[self._TAGS]
    @tags.setter
    def tags(self, value):
        self.meta[self._TAGS] = value
    
    @property
    def facts(self):
        return self.meta[self._FACTS]
    @facts.setter
    def facts(self, value):
        self.meta[self._FACTS] = value

    @property
    def vars(self):
        return self.meta[self._VARS]
    @vars.setter
    def vars(self, value):
        self.meta[self._VARS] = value

    @property
    def from_model(self):
        return self.meta[self._FROM_MODEL]
    @from_model.setter
    def from_model(self, value):
        self.meta[self._FROM_MODEL] = value

    def add_fact(self, fact):
        self.fact.append(fact)
        
    def add_tag(self, tag, value):
        self.tags[tag] = value
        
    def add_var(self, var_index, var_result_index):
        self.vars[var_index] = var_result_index
    
    def del_var(self, var_index):
        if var_index in self.vars:
            del self.vars[var_index]
    
    def dup(self):
        new_result = XuleResult(self.value, self.type, 
                                alignment=copy.deepcopy(self.alignment),
                                tags=self.tags,
                                facts=self.facts,
                                var_refs=self.vars,
                                from_model=self.from_model)
        if hasattr(self, 'original_result'):
            new_result.original_result = self.original_result
        
        return new_result

    def __str__(self):
        
        out_str = "%s - " % (str(self.alignment))
        out_str = ""
        
        if self.type in ('list', 'set'):
            return out_str + str([x for x in self.value])
        elif self.type == 'bool':
            if self.value:
                return out_str + 'true'
            else:
                return out_str + 'false'
        else:
            return out_str + str(self.value)
    
    def __repr__(self):
        return self.__str__()
    
    ''' The __eq__ and __hash__ are need for creating sets so that duplicate items are eliminated.'''
    def __eq__(self, other):
        '''DOES THIS NEED TO INCLUDE facts?'''
        return (self.value == other.value and
            self.type == other.type and
            self.alignment == other.alignment)
    
    def __hash__(self):
        '''DOES THIS NEED TO INCLUDE facts?'''
        if self.alignment is None:
            hashable_alignment = None
        else:
            hashable_alignment = frozenset(self.alignment.items())
        
        
        return hash((self.value, self.type, hashable_alignment))

class XuleResultSet:
    '''
    This class is just a set of results.
    
    When instantiating and appending, the input can be a XuleResult, an iterable that produces XuleResult or a XuleResultSet to combine.
    '''
    def __init__(self, results=None):
        self.results = []
#         self.results_by_alignment = collections.defaultdict(list)
        self.default = XuleResult(None, 'unbound')
        
        if results is not None:
            self.append(results)
            
    def __str__(self):
        "\n".join([str(res) for res in self.results])
    
    #makes this iterable returning each individual result in the set
    def __iter__(self):
        for result in self.results:
            yield result

    def _append_check(self, result):
        if isinstance(result, XuleResult):
            self.results.append(result)
#             hashed_alignment = hash(None if result.alignment is None else (frozenset(result.alignment), frozenset(result.alignment.values()))) 
#             self.results_by_alignment[hashed_alignment].append(result)
        else:
            raise XuleProcessingError(_("XuleResultSet can only contain XuleResults. Received '%s'." % type(result)))
        
    def append(self, results):
        if hasattr(results, '__iter__'):
            #got a list of results
            for result in results:
                self._append_check(result)
        else:
            self._append_check(results)    
    
    def dup(self):
        new_rs = XuleResultSet()
        for res in self.results:
            new_rs.append(res.dup())
        return new_rs
