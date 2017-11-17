'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21535 $
'''
from .XuleValue import XuleValue, iso_to_date, model_to_xule_unit, XuleUnit
from .XuleRunTime import XuleProcessingError
from arelle.ModelValue import qname, QName
import collections
from . import XuleRollForward as rf
from aniso8601 import parse_duration

class XuleSDic(XuleValue):
    def __init__(self, xule_context, name):
        super().__init__(xule_context, None, 'sdic')
        self.name = name
        self.data = collections.defaultdict(list)
        self.keys = dict()

    def __repr__(self):
        return "sdic('%s')" % self.name
    
    def __str__(self):
        return_string = self.__repr__()
        for k, v in self.data.items():
            for v_item in v:
                return_string += "\n" + self.keys[k].format_value() + ": " + v_item.format_value() 
            
        return return_string

    def format_value(self):
        return self.__str__()

    def append(self, key, value):
        if not isinstance(key, XuleValue):
            raise KeyError
        if not isinstance(value, XuleValue):
            raise TypeError
        
        self.data[key.value].append(value)
        if key.value not in self.keys:
            self.keys[key.value] = key
        
        return self
    
    def find_items(self, value):
        if not isinstance(value, XuleValue):
            raise TypeError
        
        found_keys = set()
        for k, vs in self.data.items():
            for v in vs:
                if value.value == v.value:
                    found_keys.add(self.keys[k])
        
        return XuleValue(None, frozenset(found_keys), 'set')

    def get_item(self, key):
        if not isinstance(key, XuleValue):
            raise KeyError
        
        if key.value in self.data:
            return self.data[key.value][0]
            
        else:
            return XuleValue(None, None, 'unbound')
    
    def get_items(self, key):
        if not isinstance(key, XuleValue):
            raise KeyError
    
        if key.value in self.data:
            return XuleValue(None, tuple(self.data[key.value]), 'list')
        else:
            return XuleValue(None, None, 'unbound')
        
    def has_key(self, key):
        if not isinstance(key, XuleValue):
            raise KeyError
        
        return XuleValue(None, key.value in self.data, 'bool')
    
    def remove_item(self, key):
        if not isinstance(key, XuleValue):
            raise KeyError
        
        if key.value in self.data:
            del self.data[key.value]
            del self.keys[key.value]
            
        return self
    
    def set_item(self, key, value):
        if not isinstance(key, XuleValue):
            raise KeyError
        if not isinstance(value, XuleValue):
            raise TypeError
        
        self.data[key.value] = [value,]
        if key.value not in self.keys:
            self.keys[key.value] = key
            
        return self

def func_exists(xule_context, *args):   
    #return XuleValue(xule_context, args[0].type not in ('unbound', 'none'), 'bool')
    return XuleValue(xule_context, args[0].type != 'unbound', 'bool')

def func_missing(xule_context, *args):
    #return XuleValue(xule_context, args[0].type in ('unbound', 'none'), 'bool')
    return XuleValue(xule_context, args[0].type == 'unbound', 'bool')

def func_date(xule_context, *args):
    arg = args[0]

    if arg.type == 'instant':
        return arg
    elif arg.type == 'string':
        return XuleValue(xule_context, iso_to_date(xule_context, arg.value), 'instant')
    else:
        raise XuleProcessingError(_("function 'date' requires a string argument, found '%s'" % arg.type), xule_context)

def func_duration(xule_context, *args):
    start = args[0]
    end = args[1]
    
    start_instant = func_date(xule_context, start)
    end_instant = func_date(xule_context, end)
    
    if end_instant.value < start_instant.value:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return XuleValue(xule_context, (start_instant.value, end_instant.value), 'duration', from_model=start.from_model or end.from_model)

def func_forever(xule_context, *args):
    return XuleValue(xule_context, (datetime.datetime.min, datetime.datetime.max), 'duration')

def func_unit(xule_context, *args):
    
    if len(args) == 0 or len(args) > 2:
        raise XuleProcessingError(_("The unit() function takes 1 or 2 arguments, found {}".format(len(args))), xule_context)
    
    return XuleValue(xule_context, XuleUnit(*args), 'unit')

def func_entity(xule_context, *args):
    scheme = args[0]
    identifier = args[1]
    
    if scheme.type != 'string' or identifier.type != 'string':
        raise XuleProcessingError(_("The entity scheme and identifier must be strings. Found '%s' and '%s'" % (scheme.type, identifier.type)), xule_context)
    
    return XuleValue(xule_context, (scheme.value, identifier.value), 'entity')

def func_qname(xule_context, *args):
    namespace_uri = args[0]
    local_name = args[1]
    
    if namespace_uri.type not in ('string', 'uri', 'unbound', 'none'):
        raise XuleProcessingError(_("Function 'qname' requires the namespace_uri argument to be a string, uri or none, found '%s'" % namespace_uri.type), xule_context)
    if local_name.type != 'string':
        raise XuleProcessingError(_("Function 'qname' requires the local_part argument to be a string, found '%s'" % local_name.type), xule_context)
    
    if namespace_uri.type == 'unbound':
        return XuleValue(xule_context, qname(local_name.value, noPrefixIsNoNamespace=True), 'qname')
    else:
        '''INSTEAD OF PASSING None FOR THE PREFIX, THIS SHOULD FIND THE PREFIX FOR THE NAMESPACE URI FROM THE RULE FILE. IF IT CANNOT FIND ONE, IT SHOULD CREATE ONE.'''
        return XuleValue(xule_context, QName(None, namespace_uri.value, local_name.value), 'qname')
 
def func_uri(xule_context, *args):
    arg = args[0]

    if arg.type == 'string':
        return XuleValue(xule_context, arg.value, 'uri')
    elif arg.type == 'uri':
        return arg
    else:
        raise XuleProcessingError(_("The 'uri' function requires a string argument, found '%s'." % arg.type), xule_context) 

def func_time_span(xule_context, *args):
    arg = args[0]
    
    if arg.type != 'string':
        raise XuleProcessingError(_("Function 'time-span' expects a string, fount '%s'." % arg.type), xule_context)
    
    try:
        return XuleValue(xule_context, parse_duration(arg.value.upper()), 'time-period')
    except:
        raise XuleProcessingError(_("Could not convert '%s' into a time-period." % arg.value), xule_context)

def func_schema_type(xule_context, *args):
    arg = args[0]
    
    if arg.type == 'qname':
        return XuleValue(xule_context, arg.value, 'type')
    else:
        raise XuleProcessingError(_("Function 'schema' expects a qname argument, found '%s'" % arg.type), xule_context)

def func_num_to_string(xule_context, *args):
    arg = args[0]
    
    if arg.type in ('int', 'float', 'decimal'):
        return XuleValue(xule_context, format(arg.value, ","), 'string')
    else:
        raise XuleProcessingError(_("function 'num_to_string' requires a numeric argument, found '%s'" % arg.type), xule_context)

def func_number(xule_context, *args):
    arg = args[0]
    
    if arg.type in ('int', 'float', 'decimal'):
        return arg
    elif arg.type == 'string':
        try:
            if '.' in arg.value:
                return XuleValue(xule_context, decimal.Decimal(arg.value), 'decimal')
            elif arg.value.lower() in ('inf', '+inf', '-inf'):
                return XuleValue(xule_context, float(arg.value), 'float')
            else:
                return XuleValue(xule_context, int(arg.value), 'int')
        except Exception:
            raise XuleProcessingError(_("Cannot convert '%s' to a number" % arg.value), xule_context)
    else:
        raise XuleProcessingError(_("Property 'number' requires a string or numeric argument, found '%s'" % arg.type), xule_context)
        
def func_mod(xule_context, *args):
    numerator = args[0]
    denominator = args[1]
    
    if numerator.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The numerator for the 'mod' function must be numeric, found '%s'" % numerator.type), xule_context) 
    if denominator.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The denominator for the 'mod' function must be numeric, found '%s'" % denominator.type), xule_context)
    
    combined_type, numerator_compute_value, denominator_compute_value = combine_xule_types(numerator, denominator, xule_context)
    return XuleValue(xule_context, numerator_compute_value % denominator_compute_value, combined_type)

def func_extension_concept(xule_context, *args):   
    extension_ns_value_set = xule_context._const_extension_ns()
    if len(extension_ns_value_set.values) > 0:
        extension_ns = extension_ns_value_set.values[None][0].value
    else:
        raise XuleProcessingError(_("Cannot determine extension namespace."), xule_context)
    
    concepts = set(XuleValue(xule_context, x, 'concept') for x in xule_context.model.qnameConcepts.values() if (x.isItem or x.isTuple) and x.qname.namespaceURI == extension_ns)
    
    return XuleValue(xule_context, frozenset(concepts), 'set')

def agg_count_concurrent(xule_context, current_agg_value, current_value, value_alignment):
    if current_agg_value is None:
        return XuleValue(xule_context, 1, 'int', alignment=value_alignment)
    else:
        current_agg_value.value += 1
        return current_agg_value

def agg_sum_concurrent(xule_context, current_agg_value, current_value, value_alignment):
    if current_agg_value is None:
        return current_value.clone()
    else:
        combined_types = combine_xule_types(current_agg_value, current_value, xule_context)
        if combined_types[0] == 'set':
            current_agg_value.value = current_agg_value.value | current_value.value 
        else:
            current_agg_value.value = combined_types[1] + combined_types[2]
            current_agg_value.type  = combined_types[0]
        return current_agg_value    

def agg_all_concurrent(xule_context, current_agg_value, current_value, value_alignment):
    if current_value.type != 'bool':
        raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % current_value.type), xule_context)    
    
    if current_agg_value is None:
        return current_value.clone()
    else:
        current_agg_value.value = current_agg_value.value and current_value.value   
        return current_agg_value

def agg_count(xule_context, values):
    alignment = values[0].alignment if len(values) > 0 else None
    return_value = XuleValue(xule_context, len(values), 'int', alignment=alignment)
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #XuleValue(xule_context, len(values), 'int', alignment=alignment)

def agg_sum(xule_context, values):
    agg_value = values[0].clone()
    tags = {} if agg_value.tags is None else agg_value.tags
    facts = collections.OrderedDict() if agg_value.facts is None else agg_value.facts
    
    for current_value in values[1:]:
        combined_types = combine_xule_types(agg_value, current_value, xule_context)
        if combined_types[0] == 'set':
            agg_value = XuleValue(xule_context, combined_types[1] | combined_types[2], combined_types[0], alignment=agg_value.alignment)
        else:
            agg_value = XuleValue(xule_context, combined_types[1] + combined_types[2], combined_types[0], alignment=agg_value.alignment)
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
            
    if len(tags) > 0:
        agg_value.tags = tags
    if len(facts) > 0:
        agg_value.facts = facts
    
    return agg_value 

def agg_all(xule_context, values):
    all_value = True
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type != 'bool':
            raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % current_value.type), xule_context)
        if current_value.value and current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.value and current_value.facts is not None:
            facts.update(current_value.facts)      
        all_value = all_value and current_value.value
        if not all_value:
            break
    
    return_value = XuleValue(xule_context, all_value, 'bool')
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
        
    return return_value #XuleValue(xule_context, all_value, 'bool')

def agg_any(xule_context, values):
    any_value = False
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type != 'bool':
            raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % current_value.type), xule_context)
        if current_value.value and current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.value and current_value.facts is not None:
            facts.update(current_value.facts)
                    
        any_value = any_value or current_value.value
        if any_value:
            break
    return_value = XuleValue(xule_context, any_value, 'bool')
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0 :
        return_value.facts = facts
    return return_value #XuleValue(xule_context, any_value, 'bool')

def agg_first(xule_context, values):
    return values[0].clone()

def agg_max(xule_context, values):
    agg_value = values[0].clone()
    
    for current_value in values[1:]:
        if agg_value.value < current_value.value:
            agg_value = current_value.clone()
            
    return agg_value

def agg_min(xule_context, values):
    agg_value = values[0].clone()
    
    for current_value in values[1:]:
        if agg_value.value > current_value.value:
            agg_value = current_value.clone()
            
    return agg_value    
    
def agg_list(xule_context, values):
#Commented out for elimination of the shadow_collection
#     list_values = []
#     shadow = []
#     
#     for current_value in values:
#         list_values.append(current_value)
#         shadow.append(current_value.shadow_collection if current_value.type in ('list','set') else current_value.value)
#         
#     return XuleValue(xule_context, tuple(list_values), 'list', shadow_collection=tuple(shadow))

    list_values = []
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        list_values.append(current_value)
        shadow.append(current_value.shadow_collection if current_value.type in ('list','set') else current_value.value)
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
    
    return_value = XuleValue(xule_context, tuple(list_values), 'list', shadow_collection=tuple(shadow))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #XuleValue(xule_context, tuple(list_values), 'list')

def agg_set(xule_context, values):
#Commented out for the elimination of the shadow_collection
#     set_values = []
#     shadow = []
#     
#     for current_value in values:
#         if current_value.type in ('set', 'list'):
#             if current_value.shadow_collection not in shadow:
#                 set_values.append(current_value)
#                 shadow.append(current_value.shadow_collection)
#         else:
#             if current_value.value not in shadow:
#                 set_values.append(current_value)
#                 shadow.append(current_value.value)
#     
#     return XuleValue(xule_context, frozenset(set_values), 'set', shadow_collection=frozenset(shadow)) 

    set_values = []
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type in ('set', 'list', 'dictionary'):
            if current_value.shadow_collection not in shadow:
                set_values.append(current_value)
                shadow.append(current_value.shadow_collection)
                if current_value.tags is not None:
                    tags.update(current_value.tags)
                if current_value.facts is not None:
                    facts.update(current_value.facts)
        else:
            if current_value.value not in shadow:
                set_values.append(current_value)
                shadow.append(current_value.value)
                if current_value.tags is not None:
                    tags.update(current_value.tags)
                if current_value.facts is not None:
                    facts.update(current_value.facts)
    
    return_value = XuleValue(xule_context, frozenset(set_values), 'set', shadow_collection=frozenset(shadow))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #XuleValue(xule_context, frozenset(set_values), 'set') 
        
'''        
        if current_value.is_fact:
            set_values[current_value.fact] = current_value
        else:
            set_values[current_value.value] = current_value
        
        shadow.append(current_value.shadow_collection if current_value.type in ('list','set') else current_value.value)

    return XuleValue(xule_context, frozenset(set_values.values()), 'set', shadow_collection=frozenset(shadow))
''' 

def agg_dict(xule_context, values):
    set_values = []
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    dict_values = dict()
    shadow = dict()
    
    for current_value in values:
        if current_value.type != 'list':
            raise XuleProcessingError(_("Arguments for the dict() function must be lists of key/value pairs, found %s" % current_value.type),
                                      xule_context)
        if len(current_value.value) != 2:
            raise XuleProcessingError(_("Arguments for the dict() function must be lists of length 2 (key/value pair). Found list of length %i" % len(current_value.value)))
    
        key = current_value.value[0]
        if key.type == 'dictionary':
            raise XuleProcessingError(_("Key to a dictionary cannot be a dictionary."), xule_context)
        
        value = current_value.value[1]
        
        if key.tags is not None:
            tags.update(key.tags)
        if value.tags is not None:
            tags.update(value.tags)
        if key.facts is not None:
            facts.update(key.facts)     
        if value.facts is not None:
            facts.update(value.facts)                       
        
        dict_values[key] = value
  
        shadow[key.shadow_collection if key.type in ('list', 'set') else key.value] = value.shadow_collection if value.type in ('list', 'set', 'dictionary') else value.value

    
    return_value = XuleValue(xule_context, frozenset(dict_values.items()), 'dictionary', shadow_collection=frozenset(shadow.items()))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value  

def func_sdic_create(xule_context, *args):
    name = args[0].value

    return XuleSDic(xule_context, name)

def func_sdic_from_paired_list(xule_context, *args):
    name = args[0].value
    pairs = args[1]
    unique = args[2]
    
    dic = XuleSDic(xule_context, name)
    
    if pairs.type == 'unbound':
        return dic
    
    if pairs.type not in  ('list','set'):
        raise XuleProcessingError(_("Second argument to 'sdic_from_paired_list' must be a list or set, found %s" % pairs.type), xule_context)
    
    if unique.type != 'bool':
        raise XuleProcessingError(_("Third argument to 'sdic_from_paired_list' must be a boolean, found %s" % unique.type), xule_context)
    
    for pair in pairs.value:
        if pair.type != 'list':
            raise XuleProcessingError(_("In 'sdic_from_paried_list', the second level must be a list, found %s" % pair.type), xule_context)
        if len(pair.value) != 2:
            raise XuleProcessingError(_("In 'sdic_from_paried_list', the second level must be a list of length 2, found %i" % len(pair.value)), xule_context)
        
        if unique.value:
            func_sdic_set_item(xule_context, dic, pair.value[0], pair.value[1])
        else:
            func_sdic_append(xule_context, dic, pair.value[0], pair.value[1])
    
    return dic
    
def func_sdic_append(xule_context, *args):
    dic = args[0]
    key = args[1]
    value = args[2]

    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_append' must be a sdic, found %s" % dic.type), xule_context)

    if key.type == 'unbound':
        return dic

    return dic.append(key, value)

def func_sdic_find_items(xule_context, *args):
    dic = args[0]
    value = args[1]
    
    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_find_items' must be a sdic, found %s" % dic.type), xule_context)    

    return dic.find_items(value)
    
def func_sdic_get_item(xule_context, *args):
    dic = args[0]
    key = args[1]
    
    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        #return XuleValue(xule_context, None, 'unbound')
        raise XuleProcessingError(_("First argument to 'sdic_get_item' must be a sdic, found %s" % dic.type), xule_context)    
    if key.type == 'unbound':
        raise XuleProcessingError(_("Key for a sdic cannout be missing"), xule_context)
    
    return dic.get_item(key)

def func_sdic_get_items(xule_context, *args):
    dic = args[0]
    key = args[1]

    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_get_items' must be a sdic, found %s" % dic.type), xule_context)    
    if key.type == 'unbound':
        raise XuleProcessingError(_("Key for a sdic cannout be missing"), xule_context)
    
    return dic.get_items(key)

def func_sdic_has_key(xule_context, *args):
    dic = args[0]
    key = args[1]

    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_has_key' must be a sdic, found %s" % dic.type), xule_context)    
    if key.type == 'unbound':
        raise XuleProcessingError(_("Key for a sdic cannout be missing"), xule_context)    
    
    return dic.has_key(key)

def func_sdic_remove_item(xule_context, *args):
    dic = args[0]
    key = args[1]

    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_remove_item' must be a sdic, found %s" % dic.type), xule_context)    
    if key.type == 'unbound':
        raise XuleProcessingError(_("Key for a sdic cannout be missing"), xule_context)  

    return dic.remove_item(key)

def func_sdic_set_item(xule_context, *args):
    dic = args[0]
    key = args[1]
    value = args[2]

    if dic.type == 'unbound':
        return dic
    if dic.type != 'sdic':
        raise XuleProcessingError(_("First argument to 'sdic_set_item' must be a sdic, found %s" % dic.type), xule_context)    
    if key.type == 'unbound':
        raise XuleProcessingError(_("Key for a sdic cannout be missing"), xule_context) 
    
    return dic.set_item(key, value)

def func_taxonomy(xule_context, *args):
    if len(args) == 0:
        setattr(xule_context.model, 'taxonomy_name', 'instance')
        return XuleValue(xule_context, xule_context.model, 'taxonomy')
    elif len(args) == 1:
        taxonomy_url = args[0]
        if taxonomy_url.type not in ('string', 'uri'):
            raise XuleProcessingError(_("The taxonomy() function takes a string or uri, found {}.".format(taxonomy_url.type)), xule_context)
        
        other_taxonomy = xule_context.get_other_taxonomies(taxonomy_url.value)
        setattr(other_taxonomy, 'taxonomy_name', taxonomy_url.value)
        return XuleValue(xule_context, other_taxonomy , 'taxonomy')
    else:
        raise XuleProcessingError(_("The taxonomy() function takes at most 1 argument, found {}".format(len(args))))


#the position of the function information
FUNCTION_TYPE = 0
FUNCTION_EVALUATOR = 1
FUNCTION_ARG_NUM = 2
#aggregate only 
FUNCTION_DEFAULT_VALUE = 3
FUNCTION_DEFAULT_TYPE = 4
#non aggregate only
FUNCTION_ALLOW_UNBOUND_ARGS = 3
FUNCTION_RESULT_NUMBER = 4

   

def built_in_functions():
    funcs = {
#              'all': ('aggregate', agg_all, 1, True, 'bool'),
#              'any': ('aggregate', agg_any, 1, False, 'bool'),
#              'first': ('aggregate', agg_first, 1, None, None),
#              'count': ('aggregate', agg_count, 1, 0, 'int'),
#              'sum': ('aggregate', agg_sum, 1, None, None),
#              'max': ('aggregate', agg_max, 1, None, None), 
#              'min': ('aggregate', agg_min, 1, None, None),
             'list': ('aggregate', agg_list, 1, tuple(), 'list'),
             #'list': ('aggregate', agg_list, 1, None, None),
             'set': ('aggregate', agg_set, 1, frozenset(), 'set'),
             #'set': ('aggregate', agg_set, 1, None, None),
             'dict': ('aggregate', agg_dict, 1, frozenset(), 'dictionary'),
             
             'exists': ('regular', func_exists, 1, True, 'single'),
             'missing': ('regular', func_missing, 1, True, 'single'),
             #'instant': ('regular', func_instant, 1, False, 'single'),
             'date': ('regular', func_date, 1, False, 'single'),
             'duration': ('regular', func_duration, 2, False, 'single'),
             'forever': ('regular', func_forever, 0, False, 'single'),
             'unit': ('regular', func_unit, -2, False, 'single'),
             'entity': ('regular', func_entity, 2, False, 'single'),
             'qname': ('regular', func_qname, 2, True, 'single'),
             'uri': ('regular', func_uri, 1, False, 'single'),
             'time-span': ('regular', func_time_span, 1, False, 'single'),
             'schema-type': ('regular', func_schema_type, 1, False, 'single'),
             'num_to_string': ('regular', func_num_to_string, 1, False, 'single'),
             'number': ('regular', func_number, 1, False, 'single'),
             'mod': ('regular', func_mod, 2, False, 'single'),
             'extension_concepts': ('regular', func_extension_concept, 0, False, 'single'),             
             'sdic_create': ('regular', func_sdic_create, 1, False, 'single'),
             'sdic_from_paired_list': ('regular', func_sdic_from_paired_list, 3, True, 'single'),
             'sdic_append': ('regular', func_sdic_append, 3, True, 'single'),             
             'sdic_find_items': ('regular', func_sdic_find_items, 2, True, 'single'),
             'sdic_get_item': ('regular', func_sdic_get_item, 2, True, 'single'),
             'sdic_get_items': ('regular', func_sdic_get_items, 2, True, 'single'),
             'sdic_has_key': ('regular', func_sdic_has_key, 2, True, 'single'),
             'sdic_remove_item': ('regular', func_sdic_remove_item, 2, True, 'single'),
             'sdic_set_item': ('regular', func_sdic_set_item, 3, True, 'single'),
             
             'taxonomy': ('regular', func_taxonomy, -1, False, 'single'),

             }    
    
    
    try:
        funcs.update(rf.BUILTIN_FUNCTIONS)
    except NameError:
        pass
    
    return funcs

BUILTIN_FUNCTIONS = built_in_functions()



#BUILTIN_FUNCTIONS = {}
