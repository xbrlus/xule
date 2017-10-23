from .XuleContext import XuleGlobalContext, XuleRuleContext #XuleContext
from .XuleRunTime import XuleProcessingError, XuleIterationStop, XuleException, XuleBuildTableError, XuleReEvaluate
from .XuleValue import *
from . import XuleUtility
from . import XuleFunctions

def property_union(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.add_sets(xule_context, object_value, other_set)

def property_intersect(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.intersect_sets(xule_context, object_value, other_set)

def property_contains(xule_context, object_value, *args):
    search_item = args[0]
 
    if search_item.type == 'unbound':
        return XuleValue(xule_context, None, 'unbound')
    elif object_value.type in ('set', 'list'):
        if search_item.type in ('set','list'):
            search_value = search_item.shadow_collection
        else:
            search_value = search_item.value
        return XuleValue(xule_context, search_value in object_value.shadow_collection, 'bool')
    elif object_value.type in ('string', 'uri'):
        if search_item.type in ('string', 'uri'):
            return XuleValue(xule_context, search_item.value in object_value.value, 'bool')
    else:
        raise XuleProcessingError(_("Property 'contains' cannot operator on a '%s' and '%s'" % (object_value.type, search_item.type)), xule_context)

def property_length(xule_context, object_value, *args):
    if object_value.type in ('string', 'uri'):
        cast_value = xule_cast(object_value, 'string', xule_context)
        if xule_castable(object_value, 'string', xule_context):
            return XuleValue(xule_context, len(cast_value), 'int')
        else:
            raise XuleProcessingError(_("Cannot cast '%s' to 'string' for property length" % object_value.type), xule_context)
    else: #set, list or dictionary
        return XuleValue(xule_context, len(object_value.value), 'int')

def property_to_list(xule_context, object_value, *args):
    # The input set is sorted so that two sets that ocntain the same items will produce identical lists. Because python sets are un ordered, there
    # is no guarentee that the two sets will iterate in the same order.
    def set_sort(item):
        return item.value
     
    return XuleValue(xule_context, tuple(sorted(object_value.value, key=set_sort)), 'list')
 
def property_to_set(xule_context, object_value, *args):
    return XuleFunctions.agg_set(xule_context, object_value.value)

def property_join(xule_context, object_value, *args):
    if object_value.type in ('list', 'set'):
        if len(args) != 1:
            raise XuleProcessingError(_("For lists and sets, the join property must have one argument, found {}".format(len(args))), xule_context)
        sep = args[0]
        if sep.type != 'string':
            raise XuleProcessingError(_("The argument of the join property must be a string, found '{}'".format(sep.type)), xule_context)
        
        result_string = ''   
        next_sep = '' 
        for item in object_value.value:
            result_string += next_sep + item.format_value()
            next_sep = sep.value
        
    else: # dictionary
        if len(args) != 2:
            raise XuleProcessingError(_("For dictionaries, the join property must have 2 arguments, found {}".format(len(args))), xule_context)
        main_sep = args[0]
        pair_sep = args[1]
        if main_sep.type != 'string':
            raise XuleProcessingError(_("The argument of the join property must be a string, found '{}'".format(main_sep.type)), xule_context)
        if pair_sep.type != 'string':
            raise XuleProcessingError(_("The argument of the join property must be a string, found '{}'.".format(pair_spe.type)), xule_context)
        
        result_string = ''
        next_sep = ''
        value_dictionary = object_value.value_dictionary
        for k in sorted(value_dictionary.keys(), key=lambda x: x.shadow_collection if x.type in ('set', 'list') else x.value):
            v = value_dictionary[k]
            result_string += next_sep + k.format_value() + pair_sep.value + v.format_value()
            next_sep = main_sep.value
        
    return XuleValue(xule_context, result_string, 'string')
        
def property_sort(xule_context, object_value, *args):
    sorted_list = sorted(object_value.value, key=lambda x: x.shadow_collection if x.type in ('set', 'list', 'dictionary') else x.value)
    
    return XuleValue(xule_context, tuple(sorted_list), 'list')
    
def property_keys(xule_context, object_value, *args):
    if len(args) == 1:
        val = args[0]
        keys = set()
        keys_shadow = set()
        for k, v in object_value.value:
            if val.type in ('list', 'set', 'dictionary'):
                if val.shadow_colleciton == v.shadow_collection:
                    keys.add(k)
                    keys_shadow.add(k.shadow_collection if k.type in ('list', 'set') else k.value)
            else:
                if val.value == v.value:
                    keys.add(k)
                    keys_shadow.add(k.shadow_collection if k.type in ('list', 'set') else k.value)
    else:    
        keys = set(k for k, v in object_value.value)
        keys_shadow = set(k for k, v in object_value.shadow_collection)
    return XuleValue(xule_context, frozenset(keys), 'set', shadow_collection=frozenset(keys_shadow))

def property_values(xule_context, object_value, *args):
    keys = sorted(object_value.value_dictionary.keys(), key=lambda x: x.shadow_collection if x.type in ('set', 'list') else x.value)
    vals = list(object_value.value_dictionary[k] for k in keys)
    vals_shadow = list(object_value.shadow_dictionary[k.shadow_colleciton if k.type in ('list', 'set') else k.value] for k in keys)
    
#     vals = list(v for k, v in object_value.value)
#     vals_shadow = list(v for k, v in object_value.shadow_collection)
    return XuleValue(xule_context, tuple(vals), 'list', shadow_collection=tuple(vals_shadow))

def property_networks(xule_context, object_value, *args):
    
    if len(args) > 0:
        arcrole_value = args[0]
        if arcrole_value.type == 'role':
            arcrole = arcrole_value.value.roleURI
        elif arcrole_value.type in ('uri', 'string'):
            arcrole = arcrole_value.value
        elif arcrole_value.type == 'qname':
            arcrole = XuleUtility.resolve_role(arcrole_value, 'arcrole', object_value.value, xule_context)
        elif arcrole_value.type == 'unbound':
            arcrole = None
        else:
            raise XuleProcessingError(_("The first argument (arc role) of the networks property must be a uri, found '{}'.".format(arcrole_value.type)), xule_context)
    else:
        arcrole = None
    
    if len(args) > 1:
        role_value = args[1]
        if role_value.type == 'role':
            role = role_value.value.roleURI
        elif role_value.type in ('uri', 'string'):
            role = role_value.value
        elif role_value.type == 'qname':
            role = XuleUtility.resolve_role(role_value, 'role', object_value.value, xule_context)
        else:
            raise XuleProcessingError(_("The second argument (role) of the networks property must be a uri, found '{}'.".format(role_value.type)), xule_context)
    else:
        role = None
        
    return XuleValue(xule_context, get_networks(xule_context, object_value, arcrole, role), 'set')

def property_role(xule_context, object_value, *args):
    if object_value.type == 'network':
        role_uri = object_value.value[NETWORK_INFO][NETWORK_ROLE]
        #return XuleValue(xule_context, object_value.value[NETWORK_INFO][NETWORK_ROLE], 'uri')
    else:
        role_uri = object_value.value.role
        #return XuleValue(xule_context, object_value.value.role, 'uri')
     
    if role_uri in xule_context.model.roleTypes:
        return XuleValue(xule_context, xule_context.model.roleTypes[role_uri][0], 'role')
    else:
        return XuleValue(xule_context, XuleRole(role_uri), 'role')
    
def property_arc_role(xule_context, object_value, *args):
    arcrole_uri = object_value.value[NETWORK_INFO][NETWORK_ARCROLE]
    if arcrole_uri in xule_context.model.arcroleTypes:
        return XuleValue(xule_context, xule_context.model.arcroleTypes[arcrole_uri][0], 'role')
    else:
        return XuleValue(xule_context, XuleRole(arcrole_uri), 'role')
    #return XuleValue(xule_context, XuleRole(), 'role')

def property_concept(xule_context, object_value, *args):
    '''There are two forms of this property. The first is on a fact (with no arguments). This will return the concept of the fact.
       The second is on a taxonomy (with one argument). This will return the concept of the supplied qname argument in the taxonomy.
    '''
    if object_value.is_fact:
        if len(args) != 0:
            raise XuleProcessingError(_("Property 'concept' when used on a fact does not have any arguments, found %i" % len(args)), xule_context)
 
        return XuleValue(xule_context, object_value.fact.concept, 'concept')
     
    elif object_value.type == 'taxonomy':
        if len(args) != 1:
            raise XuleProcessingError(_("Property 'concept' when used on a taxonomy requires 1 argument, found %i" % len(args)), xule_context)
         
        concept_qname_value = args[0]
         
        if concept_qname_value.type == 'unbound':
            concept_value = None
        else:
            if concept_qname_value.type != 'qname':
                raise XuleProcessingError(_("The 'concept' property of a taxonomy requires a qname argument, found '%s'" % concept_qname_value.type), xule_context)
             
            concept_value = get_concept(object_value.value, concept_qname_value.value)
         
        if concept_value is not None:
            return XuleValue(xule_context, concept_value, 'concept')
        else:
            '''SHOULD THIS BE AN EMPTY RESULT SET INSTEAD OF AN UNBOUND VALUE?'''
            return XuleValue(xule_context, None, 'unbound')

def property_period(xule_context, object_value, *args):
    if object_value.fact.context.isStartEndPeriod or object_value.fact.context.isForeverPeriod:
        return XuleValue(xule_context, model_to_xule_period(object_value.fact.context, xule_context), 'duration', from_model=True)
    else:
        return XuleValue(xule_context, model_to_xule_period(object_value.fact.context, xule_context), 'instant', from_model=True)
          
def property_unit(xule_context, object_value, *args):
    if object_value.fact.unit is None:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return XuleValue(xule_context, model_to_xule_unit(object_value.fact.unit, xule_context), 'unit')
 
def property_entity(xule_context, object_value, *args):
    return XuleValue(xule_context, model_to_xule_entity(object_value.fact.context, xule_context), 'entity')
 
def property_id(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value[1], 'string')
 
def property_scheme(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value[0], 'string')

def property_dimension(xule_context, object_value, *args):
    dim_name = args[0]
    model_fact = object_value.fact
    
    if dim_name.type == 'qname':
        dim_qname = dim_name.value
    elif dim_name.type == 'concept':
        dim_qname = dim_name.value.qname
    else:
        raise XuleProcessingError(_("The argument for property 'dimension' must be a qname, found '%s'." % dim_name.type),xule_context)
     
    member = model_fact.context.qnameDims.get(dim_name.value)
    if member is None:
        return XuleValue(xule_context, None, 'none')
    else:
        if member.isExplicit:
            return XuleValue(xule_context, member.memberQname, 'qname')
        else:
            #this is a typed dimension
            return XuleValue(xule_context, member.typedMember.xValue, model_to_xule_type(xule_context, member.typedMember.xValue))

def property_dimensions(xule_context, object_value, *args):
    result_dict = dict()
    result_shadow = dict()
    
    for dim_qname, member_model in object_value.fact.context.qnameDims.items():
        dim_value = XuleValue(xule_context, get_concept(xule_context.model, dim_qname), 'concept')
        if member_model.isExplicit:
            member_value = XuleValue(xule_context, member_model.member, 'concept')
        else: # Typed dimension
            member_value = XuleValue(xule_context, member.typedMember.xValue, model_to_xule_type(xule_context, member.typedMember.xValue))
            
        result_dict[dim_value] = member_value
        result_shadow[dim_value.value] = member_value.value
    
    return XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))

def property_start(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return XuleValue(xule_context, object_value.value, 'instant', from_model=object_value.from_model)
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        return XuleValue(xule_context, object_value.value[0], 'instant', from_model=object_value.from_model)
 
def property_end(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return XuleValue(xule_context, object_value.value, 'instant', from_model=object_value.from_model)
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        return XuleValue(xule_context, object_value.value[1], 'instant', from_model=object_value.from_model)  
 
def property_days(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return XuleValue(xule_context, 0, 'int')
    else:
        return XuleValue(xule_context, (object_value.value[1] - object_value.value[0]).days, 'int')

def property_numerator(xule_context, object_value, *args):
    # A unit is a tuple of numerator, denominator
    if len(object_value.value.numerator) == 1:
        return XuleValue(xule_context, object_value.value.numerator[0], 'qname')
    else:
        # There are multiple measures - return a list
        result = list()
        result_shadow = list()
        for measure in object_value.value.numerator:
            result.append(XuleValue(xule_context, measure, 'qname'))
            result_shadow.append(measure)
        return XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))

def property_denominator(xule_context, object_value, *args):

    if len(object_value.value.denominator) == 1:
        return XuleValue(xule_context, object_value.value.denominator[0], 'qname')
    else:
        # There are multiple measures - return a list
        result = list()
        result_shadow = list()
        for measure in object_value.value.denominator:
            result.append(XuleValue(xule_context, measure, 'qname'))
            result_shadow.append(measure)
        return XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))










 
def property_summation_item_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, SUMMATION_ITEM), 'set')
 
def property_parent_child_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, PARENT_CHILD), 'set')
 
def property_domain_member_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, DOMAIN_MEMBER), 'set')
 
def property_hypercube_dimension_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, HYPERCUBE_DIMENSION), 'set')
 
def property_dimension_default_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, DIMENSION_DEFAULT), 'set')
 
def property_dimension_domain_networks(xule_context, object_value, *args):
    return XuleValue(xule_context, get_networks(xule_context, object_value, DIMENSION_DOMAIN), 'set')
 
def property_concept_hypercube_all(xule_context, object_value, *args):
    return get_single_network(xule_context, object_value, args[0], ALL, 'hypercube-all')
 
def property_dimension_default(xule_context, object_value, *args):    
    return get_single_network(xule_context, object_value, args[0], DIMENSION_DEFAULT, 'dimension-default')
 
def property_dimension_domain(xule_context, object_value, *args):
    return get_single_network(xule_context, object_value, args[0], DIMENSION_DOMAIN, 'dimension-domain')
 
def property_domain_member(xule_context, object_value, *args):    
    return get_single_network(xule_context, object_value, args[0], DOMAIN_MEMBER, 'domain-member')
     
def property_hypercube_dimension(xule_context, object_value, *args):
    return get_single_network(xule_context, object_value, args[0], HYPERCUBE_DIMENSION, 'hypercube-dimension')
 
def property_summation_item(xule_context, object_value, *args):
    return get_single_network(xule_context, object_value, args[0], SUMMATION_ITEM, 'summation-item')
 
def property_parent_child(xule_context, object_value, *args):
    return get_single_network(xule_context, object_value, args[0], PARENT_CHILD, 'parent-child')
 

 
def property_uri(xule_context, object_value, *args):
    if object_value.type == 'role':
        return XuleValue(xule_context, object_value.value.roleURI or object_value.value.arcroleURI, 'uri')
    if object_value.type == 'taxonomy':
        return XuleValue(xule_context, object_value.value.fileSource.url, 'uri')
 
def property_definition(xule_context, object_value, *args): 
    return XuleValue(xule_context, object_value.value.definition, 'string')
 
def property_used_on(xule_context, object_value, *args):
    return XuleValue(xule_context, tuple(list(XuleValue(xule_context, x, 'qname') for x in object_value.value.usedOns)), 'list')
 
def property_descendant_relationships(xule_context, object_value, *args):
    relationships = set()
     
    network = object_value.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
     
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type in ('unbound', 'none'):
        return XuleValue(xule_context, frozenset(), 'set')
    else:
        raise XuleProcessingError(_("First argument of the 'descendant-relationships' property must be a qname or a concept. Found '%s'" % concept_arg.type), xule_context)
 
    if xule_castable(depth_arg, 'float', xule_context):
        depth = xule_cast(depth_arg, 'float', xule_context)
    else:
        raise XuleProcessingError(_("Second argument for property 'descendant-relationships' must be numeric. Found '%s'" % depth_arg.type), xule_context)
 
    #depth = depth_arg.value  
     
    descendant_rels = descend(network, model_concept, depth, set(), 'relationship')
     
    for descendant_rel in descendant_rels:
        relationships.add(XuleValue(xule_context, descendant_rel, 'relationship'))
     
    return XuleValue(xule_context, frozenset(relationships), 'set')
 
def property_descendants(xule_context, object_value, *args):
 
    concepts = set()
 
    network = object_value.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
     
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type in ('unbound', 'none'):
        return XuleValue(xule_context, frozenset(), 'set')
    else:
        raise XuleProcessingError(_("First argument of the 'descendants' property must be a qname or a concept. Found '%s'" % concept_arg.type), xule_context)
     
    if depth_arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("Second argument for property 'descendants' must be numeric. Found '%s'" % depth_arg.type), xule_context)
     
    if xule_castable(depth_arg, 'float', xule_context):
        depth = xule_cast(depth_arg, 'float', xule_context)
    else:
        raise XuleProcessingError(_("Second argument for property 'descendants' must be numeric. Found '%s'" % depth_arg.type), xule_context)
 
    #depth = depth_arg.value
                 
    descendants = descend(network, model_concept, depth, set(), 'concept')
     
    for descendant in descendants:
        concepts.add(XuleValue(xule_context, descendant, 'concept'))
         
    return XuleValue(xule_context, frozenset(concepts), 'set')
 
def property_ancestor_relationships(xule_context, object_value, *args):
    relationships = set()
 
    network = object_value.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
     
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type in ('unbound', 'none'):
        return XuleValue(xule_context, frozenset(), 'set')
    else:
        raise XuleProcessingError(_("First argument of the 'ancestor-relationships' property must be a qname or a concept. Found '%s'" % concept_arg.type), xule_context)
     
    if depth_arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("Second argument for property 'ancestor-relationships' must be numeric. Found '%s'" % depth_arg.type), xule_context)
     
    if xule_castable(depth_arg, 'float', xule_context):
        depth = xule_cast(depth_arg, 'float', xule_context)
    else:
        raise XuleProcessingError(_("Second argument for property 'ancestor-relationships' must be numeric. Found '%s'" % depth_arg.type), xule_context)
 
    #depth = depth_arg.value
                 
    ancestor_rels = ascend(network, model_concept, depth, set(), 'relationship')
     
    for ancestor_rel in ancestor_rels:
        relationships.add(XuleValue(xule_context, ancestor_rel, 'relationship'))
         
    return XuleValue(xule_context, frozenset(relationships), 'set')
 
def property_ancestors(xule_context, object_value, *args):   
    concepts = set()
 
    network = object_value.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
 
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleValue(xule_context, frozenset(), 'set')
    elif concept_arg.type in ('unbound', 'none'):
        return XuleValue(xule_context, frozenset(), 'set')
    else:
        raise XuleProcessingError(_("First argument of the 'ancesotors' property must be a qname of a concept or a concept. Found '%s'" % args[0].type), xule_context)
     
    if depth_arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("Second argument (depth) must be numeric. Found '%s'" % args[1].type), xule_context)
     
     
    if xule_castable(depth_arg, 'float', xule_context):
        depth = xule_cast(depth_arg, 'float', xule_context)
    else:
        raise XuleProcessingError(_("Second argument for property 'ancestorss' must be numeric. Found '%s'" % depth_arg.type), xule_context)
     
    #depth = depth_arg.value
                 
    ascendants = ascend(network, model_concept, depth, set(), 'concept')
     
    for ascendant in ascendants:
        concepts.add(XuleValue(xule_context, ascendant, 'concept'))
     
    return XuleValue(xule_context, frozenset(concepts), 'set')
 
def property_children(xule_context, object_value, *args):
    return property_descendants(xule_context, object_value, args[0], XuleValue(xule_context, 1, 'int'))
 
def property_parents(xule_context, object_value, *args):
    return property_ancestors(xule_context, object_value, args[0], XuleValue(xule_context, 1, 'int'))
 
def property_source_concepts(xule_context, object_value, *args):
    concepts = frozenset(XuleValue(xule_context, x, 'concept') for x in object_value.value[1].fromModelObjects().keys())
    return XuleValue(xule_context, concepts, 'set')
 
def property_target_concepts(xule_context, object_value, *args):
    concepts = frozenset(XuleValue(xule_context, x, 'concept') for x in object_value.value[1].toModelObjects().keys())        
    return XuleValue(xule_context, concepts, 'set')
 
def property_relationships(xule_context, object_value, *args):        
    relationships = set()
     
    for relationship in object_value.value[1].modelRelationships:
        relationships.add(XuleValue(xule_context, relationship, 'relationship'))
     
    return XuleValue(xule_context, frozenset(relationships), 'set')
 
def property_source(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.fromModelObject, 'concept')
 
def property_target(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.toModelObject, 'concept')
 
def property_weight(xule_context, object_value, *args):
    if object_value.value.weight is not None:
        return XuleValue(xule_context, float(object_value.value.weight), 'float')
    else:
        return XuleValue(xule_context, None, 'unbound')
 
def property_order(xule_context, object_value, *args):
    if object_value.value.order is not None:
        return XuleValue(xule_context, float(object_value.value.order), 'float')
    else:
        return XuleValue(xule_context, None, 'unbound')
     
def property_preferred_label(xule_context, object_value, *args):
    if object_value.value.preferredLabel is not None:
        return XuleValue(xule_context, object_value.value.preferredLabel, 'uri')
    else:
        return XuleValue(xule_context, None, 'unbound')    
         

def property_concepts(xule_context, object_value, *args):
     
    if object_value.type == 'taxonomy':
        concepts = set(XuleValue(xule_context, x, 'concept') for x in object_value.value.qnameConcepts.values() if x.isItem or x.isTuple)
    elif object_value.type == 'network':
        concepts = set(XuleValue(xule_context, x, 'concept') for x in (object_value.value[1].fromModelObjects().keys()) | frozenset(object_value.value[1].toModelObjects().keys()))
    else:
        raise XuleProcessingError(_("'concepts' is not a property of '%s'" % object_value.type), xule_context)
 
    return XuleValue(xule_context, frozenset(concepts), 'set')
 
def property_dts_document_locations(xule_context, object_value, *args):
    locations = set()
    for doc_url in object_value.value.urlDocs:
        locations.add(XuleValue(xule_context, doc_url, 'uri'))
    return XuleValue(xule_context, frozenset(locations), 'set')    
 

 
def property_substring(xule_context, object_value, *args):     
    cast_value = xule_cast(object_value, 'string', xule_context)
    if xule_castable(args[0], 'int', xule_context):
        start_value = xule_cast(args[0], 'int', xule_context)
    else:
        raise XuleProcessingError(_("The first argument of property 'substring' is not castable to a 'int', found '%s'" % args[0].type), xule_context)
     
    if xule_castable(args[1], 'int', xule_context):
        end_value = xule_cast(args[1], 'int', xule_context)
    else:
        raise XuleProcessingError(_("The second argument of property 'substring' is not castable to a 'int', found '%s'" % args[1].type), xule_context)
 
    return XuleValue(xule_context, cast_value[start_value:end_value], 'string')
     
def property_index_of(xule_context, object_value, *args):
    cast_value = xule_cast(object_value, 'string', xule_context)
 
    arg_result = args[0]
    if xule_castable(arg_result, 'string', xule_context):
        index_string = xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
     
    return XuleValue(xule_context, cast_value.find(index_string), 'int')
 
def property_last_index_of(xule_context, object_value, *args):
    cast_value = xule_cast(object_value, 'string', xule_context)
     
    arg_result = args[0]
    if xule_castable(arg_result, 'string', xule_context):
        index_string = xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'last-index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
     
    return XuleValue(xule_context, cast_value.rfind(index_string), 'int')
 
def property_lower_case(xule_context, object_value, *args):
    return XuleValue(xule_context, xule_cast(object_value, 'string', xule_context).lower(), 'string')
 
def property_upper_case(xule_context, object_value, *args):
    return XuleValue(xule_context, xule_cast(object_value, 'string', xule_context).upper(), 'string')
 


 
def property_item(xule_context, object_value, *args):
    arg = args[0]
     
    if arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The 'item' property requires a numeric argument, found '%s'" % arg.type), xule_context)
     
    arg_value = int(arg.value)
     
    if arg_value >= len(object_value.value) or arg_value < 0:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return object_value.value[arg_value]
         
def property_power(xule_context, object_value, *args):  
    arg = args[0]
     
    if arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The 'power' property requires a numeric argument, found '%s'" % arg.type), xule_context)
     
    combine_types = combine_xule_types(object_value, arg, xule_context)
     
    return XuleValue(xule_context, combine_types[1]**combine_types[2], combine_types[0])
 
def property_log10(xule_context, object_value, *args):
    if object_value.value == 0:
        return XuleValue(xule_context, float('-inf'), 'float')
    elif object_value.value < 0:
        return XuleValue(xule_context, float('nan'), 'float')
    else:
        return XuleValue(xule_context, math.log10(object_value.value), 'float')
 
def property_abs(xule_context, object_value, *args):
    try:
        return XuleValue(xule_context, abs(object_value.value), object_value.type)
    except Exception as e:       
        raise XuleProcessingError(_("Error calculating absolute value: %s" % str(e)), xule_context)
 
def property_signum(xule_context, object_value, *args):
    if object_value.value == 0:
        return XuleValue(xule_context, 0, 'int')
    elif object_value.value < 0:
        return XuleValue(xule_context, -1, 'int')
    else:
        return XuleValue(xule_context, 1, 'int')
 
def property_name(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.qname, 'qname')
 
def property_local_part(xule_context, object_value, *args):
    if object_value.value is not None:
        return XuleValue(xule_context, object_value.value.localName, 'string')
    else:
        return XuleValue(xule_context, '', 'string')
     
def property_namespace_uri(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.namespaceURI, 'uri')
 
def property_debit(xule_context, object_value, *args):
    return XuleValue(xule_context, 'debit', 'balance')
 
def property_credit(xule_context, object_value, *args):
    return XuleValue(xule_context, 'credit', 'balance')
 
def property_balance(xule_context, object_value, *args):
    if object_value.type in ('unbound','none'):
        return XuleValue(xule_context, None, 'balance')
    else:
        return XuleValue(xule_context, object_value.value.balance, 'balance')
 
def property_instant(xule_context, object_value, *args):
    return XuleValue(xule_context, 'instant', 'period-type')
 
def property_duration(xule_context, object_value, *args):
    return XuleValue(xule_context, 'duration', 'period-type')
 
def property_period_type(xule_context, object_value, *args):
    if object_value.type in ('unbound', 'none'):
        return XuleValue(xule_context, None, 'period-type')
    else:
        return XuleValue(xule_context, object_value.value.periodType, 'period-type')
 
def property_is_numeric(xule_context, object_value, *args):
    if object_value.is_fact:
        return XuleValue(xule_context, object_value.fact.concept.isNumeric, 'bool')
    else:
        #concept
        return XuleValue(xule_context, object_value.value.isNumeric, 'bool')
 
def property_is_monetary(xule_context, object_value, *args):
    if object_value.is_fact:
        return XuleValue(xule_context, object_value.fact.concept.isMonetary, 'bool')
    else:
        #concept
        return XuleValue(xule_context, object_value.value.isMonetary, 'bool')
 
def property_abstract(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.isAbstract, 'bool')
def property_xbrl_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return XuleValue(xule_context, object_value.fact.concept.baseXbrliTypeQname, 'type')
    else:
        return XuleValue(xule_context, object_value.value.baseXbrliTypeQname, 'type')
 
def property_schema_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return XuleValue(xule_context, object_value.fact.concept.typeQname, 'type')
    else:
        return XuleValue(xule_context, object_value.value.typeQname, 'type')
 
def property_label(xule_context, object_value, *args):
    role = None
    lang = None
    if len(args) > 0:
        lang = None
        label_type = args[0]
        if label_type.type == 'none':
            base_label_type = None
        elif xule_castable(label_type, 'string', xule_context):
            base_label_type = xule_cast(label_type, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The first argument for property 'label' must be a string, found '%s'" % label_type.type), xule_context)
    if len(args) > 1: #there are 2 args
        lang = args[1]
        if lang.type == 'none':
            base_lang = None
        elif xule_castable(lang, 'string', xule_context):
            base_lang = xule_cast(lang, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The second argument for property 'label' must be a string, found '%s'" % lang.type), xule_context)        
     
    if object_value.is_fact:
        concept = object_value.fact.concept
    else:
        concept = object_value.value
     
    label = get_label(xule_context, concept, base_label_type, base_lang)
     
    if label is None:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return XuleValue(xule_context, label, 'label')
     
def get_label(xule_context, concept, base_label_type, base_lang):#label type
    label_network = ModelRelationshipSet(concept.modelXbrl, CONCEPT_LABEL)
    label_rels = label_network.fromModelObject(concept)
    if len(label_rels) > 0:
        #filter the labels
        label_by_type = dict()
        for lab_rel in label_rels:
            label = lab_rel.toModelObject
            if ((base_lang is None or label.xmlLang.lower().startswith(base_lang.lower())) and
                (base_label_type is None or label.role == base_label_type)):
                label_by_type[label.role] = label
 
        if len(label_by_type) > 1:
            if base_label_type is None:
                for role in ORDERED_LABEL_ROLE:
                    label = label_by_type.get(role)
                    if label is not None:
                        return XuleValue(xule_context, label, 'label')
            #if we are here, there were no matching labels in the ordered list of label types, so just pick one
            return next(iter(label_by_type.values()))
        elif len(label_by_type) > 0:
            #there is only one label just return it
            return next(iter(label_by_type.values()))
        else:
            return None        
    else:
        return None
 
def property_text(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.textValue, 'string')
 
def property_lang(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.xmlLang, 'string')
 
def property_references(xule_context, object_value, *args):
    #reference type
    if len(args) > 0:
        reference_type = args[0]
        if reference_type.type == 'none':
            base_reference_type = None
        elif xule_castable(reference_type, 'string', xule_context):
            base_reference_type = xule_cast(reference_type, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The first argument for property 'reference' must be a string, found '%s'" % reference_type.type), xule_context)
    else:
        base_reference_type = None    
 
    if object_value.is_fact:
        concept = object_value.fact.concept
    else:
        concept = object_value.value
 
    reference_network = ModelRelationshipSet(concept.modelXbrl, CONCEPT_REFERENCE)
    reference_rels = reference_network.fromModelObject(concept)
    if len(reference_rels) > 0:
        #filter the references
        reference_by_type = collections.defaultdict(list)
        for reference_rel in reference_rels:
            reference = reference_rel.toModelObject
            if base_reference_type is None or reference.role == base_reference_type:
                reference_by_type[reference.role].append(reference)
 
        if len(reference_by_type) > 1:
            if base_reference_type is None:
                for role in ORDERED_REFERENCE_ROLE:
                    references = reference_by_type.get(role)
                    if references is not None:
                        xule_references = set(XuleValue(xule_context, x, 'reference') for x in references)
            #if we are here, there were no matching references in the ordered list of label types, so just pick one
            return XuleValue(xule_context, frozenset(set(XuleValue(xule_context, x, 'reference') for x in next(iter(reference_by_type.values())))), 'set')
        elif len(reference_by_type) > 0:
            #there is only one reference just return it
            return XuleValue(xule_context, frozenset(set(XuleValue(xule_context, x, 'reference') for x in next(iter(reference_by_type.values())))), 'set')
        else:
            return XuleValue(xule_context, frozenset(), 'set')        
    else:
        return XuleValue(xule_context, frozenset(), 'set')       
 
def property_parts(xule_context, object_value, *args):
    return XuleValue(xule_context, tuple(list(XuleValue(xule_context, x, 'reference-part') for x in object_value.value)), 'list')
 
def property_part_value(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.textValue, 'string')
 
def property_part_by_name(xule_context, object_value, *args):
    part_name = args[0]
     
    if part_name.type != 'qname':
        raise XuleProcessingError(_("The argument for property 'part_by_name' must be a qname, found '%s'." % part_name.type), xule_context)
     
    for part in object_value.value:
        if part.qname == part_name.value:
            return XuleValue(xule_context, part, 'reference-part')
     
    #if we get here, then the part was not found
    return XuleValue(xule_context, None, 'unbound')
 
def property_decimals(xule_context, object_value, *args):
    if object_value.fact.decimals is not None:
        return XuleValue(xule_context, float(object_value.fact.decimals), 'float')
    else:
        return Xulevalue(xule_context, None, 'unbound')
 
def property_round_by_decimals(xule_context, object_value, *args):
    if object_value.type not in ('int', 'decimal', 'float'):
        raise XuleProcessingError(_("Property 'round-by-decimals' can only be used on a number, found '%s'." % object_value.type), xule_context)
     
    arg = args[0]
     
    if arg.type not in ('int', 'decimal', 'float'):
        raise XuleProcessingError(_("Property 'round-by-decimals' requires a numeric argument, found '%s'" % arg.type), xule_context)
 
    if arg.value == float('inf'):
        return object_value
    else:
        #convert to int
        decimals = int(arg.value)
        rounded_value = round(object_value.value, decimals)
        return XuleValue(xule_context, rounded_value, object_value.type)
 

 


def property_add_time_period(xule_context, object_value, *args):
    arg = args[0]
    if arg.type != 'time-period':
        raise XuleProcessingError(_("Property 'add-time-period' requires a time-period argument, found '%s'" % arg.type), xule_context)
     
    return XuleValue(xule_context, object_value.value + arg.value, 'instant', from_model=object_value.from_model)
 
def property_subtract_time_period(xule_context, object_value, *args):
    arg = args[0]
    if arg.type != 'time-period':
        raise XuleProcessingError(_("Property 'add-time-period' requires a time-period argument, found '%s'" % arg.type), xule_context)
     
    return XuleValue(xule_context, object_value.value - arg.value, 'instant', from_model=object_value.from_model)
 

     
def property_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return XuleValue(xule_context, 'fact', 'string')
    else:
        return XuleValue(xule_context, object_value.type, 'string') 
 
def property_compute_type(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.type, 'string')
 
def property_string(xule_context, object_value, *args):
    '''SHOULD THE META DATA BE INCLUDED???? THIS SHOULD BE HANDLED BY THE PROPERTY EVALUATOR.'''
    return XuleValue(xule_context, str(object_value.value), 'string')
 
def property_facts(xule_context, object_value, *args):
    return XuleValue(xule_context, "\n".join([str(f.qname) + " " + str(f.xValue) for f in xule_context.facts]), 'string')
 
def property_from_model(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.from_model, 'bool')
 
def property_alignment(xule_context, object_value, *args):
    return XuleValue(xule_context, str(object_value.alignment), 'string') 
 
def property_hash(xule_context, object_value, *args):
    return XuleValue(xule_context, str(hash(object_value)), 'string')   
 
def property_list_properties(xule_context, object_value, *args):
    object_prop = collections.defaultdict(list)
     
    s = "Property Names:"
 
    for prop_name, prop_info in PROPERTIES.items():
        s += "\n" + prop_name + "," + str(prop_info[PROP_ARG_NUM])
        prop_objects = prop_info[PROP_OPERAND_TYPES]
        if not isinstance(prop_objects, tuple):
            XuleProcessingError(_("Property object types are not a tuple %s" % prop_name), xule_context)
             
        if len(prop_objects) == 0:
            object_prop['unbound'].append((prop_name, str(prop_info[PROP_ARG_NUM])))
        else:
            for prop_object in prop_objects:
                object_prop[prop_object].append((prop_name, str(prop_info[PROP_ARG_NUM])))
                 
    s += "\nProperites by type:"
    for object_type, props in object_prop.items():
        s += "\n" + object_type
        for prop in props:
            s += "\n\t" + prop[0] + "," + prop[1]
     
    return XuleValue(xule_context, s, 'string')

def get_networks(xule_context, dts_value, arcrole=None, role=None, link=None, arc=None):
    #final_result_set = XuleResultSet()
    networks = set()
    dts = dts_value.value
    network_infos = get_base_set_info(xule_context, dts, arcrole, role, link, arc)
    
    for network_info in network_infos:
        '''I THINK THESE NETWORKS ARE REALLY COMBINATION OF NETWORKS, SO I AM IGNORING THEM.
           NEED TO CHECK IF THIS IS TRUE.'''
        if (network_info[NETWORK_ROLE] is not None and
            network_info[NETWORK_LINK] is not None and
            network_info[NETWORK_ARC] is not None):
            
            if network_info in dts.relationshipSets:
                net = XuleValue(xule_context, (network_info, dts.relationshipSets[network_info]), 'network')
            else:
                net = XuleValue(xule_context, 
                                (network_info, 
                                    ModelRelationshipSet(dts, 
                                               network_info[NETWORK_ARCROLE],
                                               network_info[NETWORK_ROLE],
                                               network_info[NETWORK_LINK],
                                               network_info[NETWORK_ARC])),
                                     'network')
            
            #final_result_set.append(net)
            networks.add(net)
    #return final_result_set
    return frozenset(networks)

def get_single_network(xule_context, dts, role_result, arc_role, property_name):
    
    if xule_castable(role_result, 'uri', xule_context):
        role_uri = xule_cast(role_result, 'uri', xule_context)
    else:
        raise XuleProcessingError(_("The '%s' property requires an uri argument, found '%s'" % (property_name, role_result.type)), xule_context)
    
    networks = get_networks(xule_context, dts, arc_role, role=role_uri)
    if len(networks) == 0:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return next(iter(networks))

  
def get_base_set_info(xule_context, dts, arcrole=None, role=None, link=None, arc=None):
#     return [x + (False,) for x in dts.baseSets if x[NETWORK_ARCROLE] == arcrole and
#                                        (True if role is None else x[NETWORK_ROLE] == role) and
#                                        (True if link is None else x[NETWORK_LINK] == link) and
#                                        (True if arc is None else x[NETWORK_ARC] == arc)]

    info = list()
    for x in dts.baseSets:
        keep = True
        if x[NETWORK_ARCROLE] is None or (x[NETWORK_ARCROLE] != arcrole and arcrole is not None): keep = False
        if x[NETWORK_ROLE] is None or (x[NETWORK_ROLE] != role and role is not None): keep = False
        if x[NETWORK_LINK] is None or (x[NETWORK_LINK] != link and link is not None): keep = False
        if x[NETWORK_ARC] is None or (x[NETWORK_ARC] != arc and arc is not None): keep = False

        if keep:
            info.append(x + (False,))
    return info

def load_networks(dts):
    for network_info in dts.baseSets:
        if (network_info[NETWORK_ARCROLE] is not None and
            network_info[NETWORK_ROLE] is not None and
            network_info[NETWORK_LINK] is not None and
            network_info[NETWORK_ARC] is not None):
            
            if (network_info[NETWORK_LINK].namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
                network_info[NETWORK_LINK].localName in ('definitionLink', 'presentationLink', 'calculationLink')):

                ModelRelationshipSet(dts,
                                     network_info[NETWORK_ARCROLE],
                                     network_info[NETWORK_ROLE],
                                     network_info[NETWORK_LINK],
                                     network_info[NETWORK_ARC])
         
def get_concept(dts, concept_qname):
    concept = dts.qnameConcepts.get(concept_qname)
    if concept is None:
        return None
    else:
        if concept.isItem or concept.isTuple:
            return concept
        else:
            return None

def descend(network, parent, depth, previous_concepts, return_type):
    if depth < 1:
        return set()
    
    descendants = set()
    for rel in network.fromModelObject(parent):
        child = rel.toModelObject
        if return_type == 'concept':
            descendants.add(child)
        else:
            descendants.add(rel)
        if child not in previous_concepts:
            previous_concepts.add(child)
            descendants = descendants | descend(network, child, depth -1, previous_concepts, return_type)
            
    return descendants

def ascend(network, parent, depth, previous_concepts, return_type):
    if depth == 0:
        return set()
    
    ascendants = set()
    for rel in network.toModelObject(parent):
        parent = rel.fromModelObject
        if return_type == 'concept':
            ascendants.add(parent)
        else:
            ascendants.add(rel)
        if parent not in previous_concepts:
            previous_concepts.add(parent)
            ascendants = ascendants | ascend(network, parent, depth -1, previous_concepts, return_type)
            
    return ascendants


#Property tuple
PROP_FUNCTION = 0
PROP_ARG_NUM = 1 #arg num allows negative numbers to indicated that the arguments are optional
PROP_OPERAND_TYPES = 2
PROP_UNBOUND_ALLOWED = 3

PROPERTIES = {
              #NEW PROPERTIES
              'union': (property_union, 1, ('set',), False),
              'intersect': (property_intersect, 1, ('set',), False),
              'contains': (property_contains, 1, ('set', 'list', 'string', 'uri'), False),
              'length': (property_length, 0, ('string', 'uri', 'set', 'list', 'dictionary'), False),
              'to-list': (property_to_list, 0, ('list', 'set'), False),
              'to-set': (property_to_set, 0, ('list', 'set'), False),              
              'join': (property_join, -2, ('list', 'set', 'dictionary'), False),
              'sort': (property_sort, 0, ('list', 'set'), False),
              'keys': (property_keys, -1, ('dictionary',), False),
              'values': (property_values, 0, ('dictionary', ), False),
              'decimals': (property_decimals, 0, ('fact',), False),
              'networks':(property_networks, -2, ('taxonomy',), False),
              'role': (property_role, 0, ('network', 'label'), False),
              'arcrole':(property_arc_role, 0, ('network',), False),
              'concept': (property_concept, -1, ('fact', 'taxonomy'), False),
              'period': (property_period, 0, ('fact',), False),
              'unit': (property_unit, 0, ('fact',), False),
              'entity': (property_entity, 0, ('fact',), False),
              'id': (property_id, 0, ('entity',), False),
              'scheme': (property_scheme, 0, ('entity',), False),
              'dimension': (property_dimension, 1, ('fact',), False),
              'dimensions': (property_dimensions, 0, ('fact',), False),
              'start': (property_start, 0, ('instant', 'duration'), False),
              'end': (property_end, 0, ('instant', 'duration'), False),
              'days': (property_days, 0, ('instant', 'duration'), False),
              'numerator': (property_numerator, 0, ('unit', ), False),
              'denominator': (property_denominator, 0, ('unit',), False),
              
              
              
              
              
              #OLD PROPERTIES
               # taxonomy navigations
               'concepts': (property_concepts, 0, ('taxonomy', 'network'), False),
               'summation-item-networks': (property_summation_item_networks, 0, ('taxonomy',), False),
               'parent-child-networks': (property_parent_child_networks, 0, ('taxonomy',), False),
               'domain-member-networks': (property_domain_member_networks, 0, ('taxonomy',), False),
               'hypercube-dimension-networks': (property_hypercube_dimension_networks, 0, ('taxonomy',), False),
               'dimension-default-networks': (property_dimension_default_networks, 0, ('taxonomy',), False),
               'dimension-domain-networks': (property_dimension_domain_networks, 0, ('taxonomy',), False),
                
               'concept-hypercube-all': (property_concept_hypercube_all, 1, ('taxonomy',), False),
               'dimension-default': (property_dimension_default, 1, ('taxonomy',), False),
               'dimension-domain': (property_dimension_domain, 1, ('taxonomy',), False),
               'domain-member': (property_domain_member, 1, ('taxonomy',), False),
               'hypercube-dimension': (property_hypercube_dimension, 1, ('taxonomy',), False),
               'summation-item': (property_summation_item, 1, ('taxonomy',), False),
               'parent-child': (property_parent_child, 1, ('taxonomy',), False),
                
               'source-concepts': (property_source_concepts, 0, ('network',), False),
               'target-concepts': (property_target_concepts, 0, ('network',), False),
               'descendants': (property_descendants, 2, ('network',), False),
               'children': (property_children, 1, ('network',), False),
               'ancestors': (property_ancestors, 2, ('network',), False),
               'parents': (property_parents, 1, ('network',), False),
                
               'relationships': (property_relationships, 0, ('network',), False),
               'descendant-relationships': (property_descendant_relationships, 2, ('network',), False),
               'ancestor-relationships': (property_ancestor_relationships, 2, ('network',), False),
                
               'source': (property_source, 0, ('relationship',), False),
               'target': (property_target, 0, ('relationship',), False),
               'weight': (property_weight, 0, ('relationship',), False),
               'order': (property_order, 0, ('relationship',), False),
               'preferred-label': (property_preferred_label, 0, ('relationship',), False),
                
               'concept': (property_concept, -1, ('fact', 'taxonomy'), False),
               'balance': (property_balance, 0, ('concept', 'unbound', 'none'), True),
               'debit': (property_debit, 0, ('balance',), False),
               'credit': (property_credit, 0, ('balance',), False),
               'period-type': (property_period_type, 0, ('concept', 'unbound', 'none'), True),
               'duration': (property_duration, 0, ('period-type',), False),
               'instant': (property_instant, 0, ('period-type',), False),
               'is-numeric': (property_is_numeric, 0, ('concept', 'fact'), False),
               'is-monetary': (property_is_monetary, 0, ('concept', 'fact'), False),
               'abstract': (property_abstract, 0, ('concept', 'fact'), False),
               'xbrl-type': (property_xbrl_type, 0, ('concept', 'fact'), False),
               'schema-type': (property_schema_type, 0, ('concept', 'fact'), False),
               'label': (property_label, -2, ('concept', 'fact'), False),
               'references':(property_references, -1, ('concept', 'fact'), False),
                 
               
               'round-by-decimals': (property_round_by_decimals, 1, ('fact', 'int', 'decimal', 'float'), False),


               'add-time-period': (property_add_time_period, 1, ('instant',), False),
               'subtract-time-period': (property_subtract_time_period, 1, ('instant',), False),
  
               'dts-document-locations': (property_dts_document_locations, 0, ('taxonomy',), False),
                
               'substring': (property_substring, 2, ('string', 'uri'), False),
               'index-of': (property_index_of, 1, ('string', 'uri'), False),
               'last-index-of': (property_last_index_of, 1, ('string', 'uri'), False),
               'lower-case': (property_lower_case, 0, ('string', 'uri'), False),
               'upper-case': (property_upper_case, 0, ('string', 'uri'), False),

               'item': (property_item, 1, ('list',), False),
                
               'power': (property_power, 1, ('int', 'float', 'decimal'), False),
               'log10': (property_log10, 0, ('int', 'float', 'decimal'), False),
               'abs': (property_abs, 0, ('int', 'float', 'decimal', 'fact'), False),
               'signum': (property_signum, 0, ('int', 'float', 'decimal', 'fact'), False),
                
               
               'uri': (property_uri, 0, ('role', 'taxonomy'), False),
               'definition': (property_definition, 0, ('role',), False),
               'used-on': (property_used_on, 0, ('role',), False),
               'name': (property_name, 0, ('concept', 'reference-part'), False),
               'local-part': (property_local_part, 0, ('qname',), False),
               'namespace-uri': (property_namespace_uri, 0, ('qname',), False),
                
               'text': (property_text, 0, ('label',), False),
               'lang': (property_lang, 0, ('label',), False),
               'parts': (property_parts, 0, ('reference',), False),
               'part-value': (property_part_value, 0, ('reference-part',), False),
               'part-by-name': (property_part_by_name, 1, ('reference',), False),
                

 
               'type': (property_type, 0, (), False),
               'alignment': (property_alignment, 0, (), False),
               'compute-type': (property_compute_type, 0, (), False),
               'string': (property_string, 0, (), False),
               'facts': (property_facts, 0, (), False),
               'from-model': (property_from_model, 0, (), False),
               'hash': (property_hash, 0, (), True),
                
               'list-properties': (property_list_properties, 0, ('unbound',), True)
              }


#Network tuple
NETWORK_INFO = 0
NETWORK_RELATIONSHIP_SET = 1

#Network info tuple
NETWORK_ARCROLE = 0
NETWORK_ROLE = 1
NETWORK_LINK = 2
NETWORK_ARC = 3

#arcroles
CORE_ARCROLES = {
                 'fact-footnote': 'http://www.xbrl.org/2003/arcrole/fact-footnote'
                ,'concept-label':'http://www.xbrl.org/2003/arcrole/concept-label'
                ,'concept-reference':'http://www.xbrl.org/2003/arcrole/concept-reference'
                ,'parent-child':'http://www.xbrl.org/2003/arcrole/parent-child'
                ,'summation-item':'http://www.xbrl.org/2003/arcrole/summation-item'
                ,'general-special':'http://www.xbrl.org/2003/arcrole/general-special'
                ,'essence-alias':'http://www.xbrl.org/2003/arcrole/essence-alias'
                ,'similar-tuples':'http://www.xbrl.org/2003/arcrole/similar-tuples'
                ,'requires-element':'http://www.xbrl.org/2003/arcrole/requires-element'
                }

SUMMATION_ITEM = 'http://www.xbrl.org/2003/arcrole/summation-item'
PARENT_CHILD = 'http://www.xbrl.org/2003/arcrole/parent-child'
ESSENCE_ALIAS = 'http://www.xbrl.org/2003/arcrole/essence-alias'
DOMAIN_MEMBER = 'http://xbrl.org/int/dim/arcrole/domain-member'
DIMENSION_DEFAULT = 'http://xbrl.org/int/dim/arcrole/dimension-default'
DIMENSION_DOMAIN = 'http://xbrl.org/int/dim/arcrole/dimension-domain'
HYPERCUBE_DIMENSION = 'http://xbrl.org/int/dim/arcrole/hypercube-dimension'
ALL = 'http://xbrl.org/int/dim/arcrole/all'
NOT_ALL = 'http://xbrl.org/int/dim/arcrole/notAll'
CONCEPT_LABEL = 'http://www.xbrl.org/2003/arcrole/concept-label'
CONCEPT_REFERENCE = 'http://www.xbrl.org/2003/arcrole/concept-reference'
ORDERED_LABEL_ROLE = ['http://www.xbrl.org/2003/role/label'
                    ,'http://www.xbrl.org/2003/role/terseLabel'
                    ,'http://www.xbrl.org/2003/role/verboseLabel'
                    ,'http://www.xbrl.org/2003/role/totalLabel'
                    ,'http://www.xbrl.org/2009/role/negatedTerseLabel'
                    ,'http://xbrl.us/us-gaap/role/label/negated'
                    ,'http://www.xbrl.org/2009/role/negatedLabel'
                    ,'http://xbrl.us/us-gaap/role/label/negatedTotal'
                    ,'http://www.xbrl.org/2009/role/negatedTotalLabel'
                    ,'http://www.xbrl.org/2003/role/periodStartLabel'
                    ,'http://www.xbrl.org/2003/role/periodEndLabel'
                    ,'http://xbrl.us/us-gaap/role/label/negatedPeriodEnd'
                    ,'http://www.xbrl.org/2009/role/negatedPeriodEndLabel'
                    ,'http://xbrl.us/us-gaap/role/label/negatedPeriodStart'
                    ,'http://www.xbrl.org/2009/role/negatedPeriodStartLabel'
                    ,'http://www.xbrl.org/2009/role/negatedNetLabel']
ORDERED_REFERENCE_ROLE = ['http://www.xbrl.org/2003/role/reference',
                        'http://www.xbrl.org/2003/role/definitionRef',
                        'http://www.xbrl.org/2003/role/disclosureRef',
                        'http://www.xbrl.org/2003/role/mandatoryDisclosureRef',
                        'http://www.xbrl.org/2003/role/recommendedDisclosureRef',
                        'http://www.xbrl.org/2003/role/unspecifiedDisclosureRef',
                        'http://www.xbrl.org/2003/role/presentationRef',
                        'http://www.xbrl.org/2003/role/measurementRef',
                        'http://www.xbrl.org/2003/role/commentaryRef',
                        'http://www.xbrl.org/2003/role/exampleRef']
