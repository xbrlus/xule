"""XuleProperties

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

$Change: 23260 $
DOCSKIP
"""

from .XuleRunTime import XuleProcessingError
from . import XuleValue as xv
from . import XuleUtility 
from . import XuleFunctions
from arelle.ModelDocument import Type
#from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelValue import QName, qname
import collections
import decimal
import json
import math
import numpy
import re

def property_union(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.add_sets(xule_context, object_value, other_set)

def property_intersect(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.intersect_sets(xule_context, object_value, other_set)

def property_difference(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.subtract_sets(xule_context, object_value, other_set)

def property_symetric_difference(xule_context, object_value, *args):
    other_set = args[0]
    return XuleUtility.symetric_difference(xule_context, object_value, other_set)

def property_contains(xule_context, object_value, *args):
    search_item = args[0]
 
    if search_item.type == 'unbound':
        return xv.XuleValue(xule_context, None, 'unbound')
    elif object_value.type in ('set', 'list'):
        if search_item.type in ('set','list','dictionary'):
            search_value = search_item.shadow_collection
        else:
            search_value = search_item.value
        return xv.XuleValue(xule_context, search_value in object_value.shadow_collection, 'bool')
    elif object_value.type in ('string', 'uri'):
        if search_item.type in ('string', 'uri'):
            return xv.XuleValue(xule_context, search_item.value in object_value.value, 'bool')
    else:
        raise XuleProcessingError(_("Property 'contains' or 'in' expression cannot operate on a '%s' and '%s'" % (object_value.type, search_item.type)), xule_context)

def property_length(xule_context, object_value, *args):
    if object_value.type in ('string', 'uri'):
        cast_value = xv.xule_cast(object_value, 'string', xule_context)
        if xv.xule_castable(object_value, 'string', xule_context):
            return xv.XuleValue(xule_context, len(cast_value), 'int')
        else:
            raise XuleProcessingError(_("Cannot cast '%s' to 'string' for property length" % object_value.type), xule_context)
    else: #set, list or dictionary
        return xv.XuleValue(xule_context, len(object_value.value), 'int')

def property_to_list(xule_context, object_value, *args):
    # The input set is sorted so that two sets that contain the same items will produce identical lists. Because python sets are un ordered, there
    # is no guarentee that the two sets will iterate in the same order.
    def set_sort(item):
        return item.value

    try:
        return xv.XuleValue(xule_context, tuple(sorted(object_value.value, key=set_sort)), 'list')
    except TypeError:
        return xv.XuleValue(xule_context, tuple(object_value.value), 'list')
 
def property_to_set(xule_context, object_value, *args):
    if object_value.type == 'dictionary':
        result = []
        shadow = []
        for k, v in object_value.value:
            item_value = XuleFunctions.agg_list(xule_context, (k, v))
            result.append(item_value)
            shadow.append(item_value.shadow_collection)
        return xv.XuleValue(xule_context, frozenset(result), 'set', shadow_collection=frozenset(shadow))
    else: #list or set
        return XuleFunctions.agg_set(xule_context, object_value.value)

def property_to_dict(xule_context, object_value, *args):
    return XuleFunctions.agg_dict(xule_context, object_value.value)

def property_index(xule_context, object_value, *args):
    index_value = args[0]
    if object_value.type == 'list':
        if index_value.type == 'int':
            index_number = index_value.value
        elif index_value.type == 'float':
            if index_value.value.is_integer():
                index_number = int(index_value.value)
            else:
                raise XuleProcessingError(
                    _("Index of a list must be a whole number, found %s" % str(index_value.value)),
                    xule_context)
        elif index_value.type == 'decimal':
            if index_value.value == int(index_value.value):
                index_number = int(index_value.value)
            else:
                raise XuleProcessingError(
                    _("Index of a list must be a whole number, found %s" % str(index_value.value)),
                    xule_context)
        else:
            raise XuleProcessingError(_("Index of a list must be a number, found %s" % index_value.type),
                                      xule_context)

        # Check if the index number is the value range for the list
        if index_number < 1 or index_number > len(object_value.value):
            raise XuleProcessingError(_("Index value of %i is out of range for the list with length of %i" % (
                index_number, len(object_value.value))),
                                      xule_context)
        return_value = object_value.value[index_number - 1]

    elif object_value.type == 'dictionary':
        if index_value.type in ('set', 'list'):
            key_value = index_value.shadow_collection
        else:
            key_value = index_value.value

        return_value = object_value.key_search_dictionary.get(key_value, xv.XuleValue(xule_context, None, 'none'))

    else:
        raise XuleProcessingError(_("The 'index' property or index expression '[]' can only operate on a list or dictionary, found '%s'" % object_value.type),
                                  xule_context)

    return return_value

def property_is_subset(xule_context, object_value, *args):
    super_values = args[0]

    if super_values.type != 'set':
        raise XuleProcessingError(_("The subset value must be a 'set',, found '{}'".format(super_values.type)), xule_context)

    return xv.XuleValue(xule_context, object_value.shadow_collection <= super_values.shadow_collection, 'bool')

def property_is_superset(xule_context, object_value, *args):
    sub_values = args[0]

    if sub_values.type != 'set':
        raise XuleProcessingError(_("The subset value must be a 'set', found '{}'".format(sub_values.type)), xule_context)

    return xv.XuleValue(xule_context, object_value.shadow_collection >= sub_values.shadow_collection, 'bool')

class xule_json_encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        # Let the base class default method raise the TypeError
        return super.default(self, o)

def property_to_json(xule_context, object_value, *args):
    if object_value.type == 'dictionary':
        unfrozen = dict(object_value.shadow_collection)
    elif object_value.type == 'set':
        unfrozen = tuple(object_value.shadow_collection)
    else:
        unfrozen = object_value.shadow_collection
    
    unfrozen = unfreeze_shadow(object_value, True)

    return xv.XuleValue(xule_context, json.dumps(unfrozen, cls=xule_json_encoder), 'string')

def unfreeze_shadow(cur_val, for_json=False):
    if cur_val.type == 'list':
        return [unfreeze_shadow(x) for x in cur_val.value]
    elif cur_val.type == 'set':
        if for_json:
            # convert the set to a list. JSON does not handle sets
            return [unfreeze_shadow(x) for x in cur_val.value]
        else:
            return {unfreeze_shadow(x) for x in cur_val.value}
    elif cur_val.type == 'dictionary':
        return {unfreeze_shadow(k): unfreeze_shadow(v) for k, v in cur_val.value}
    else:
        return cur_val.value

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
            raise XuleProcessingError(_("The argument of the join property must be a string, found '{}'.".format(pair_sep.type)), xule_context)
        
        result_string = ''
        next_sep = ''
        value_dictionary = object_value.value_dictionary
        try:
            keys = sorted(value_dictionary.keys(), key=lambda x: x.shadow_collection if x.type in ('set', 'list') else x.value)
        except TypeError:
            keys = value_dictionary.keys()
        for k in keys:
            v = value_dictionary[k]
            result_string += next_sep + k.format_value() + pair_sep.value + v.format_value()
            next_sep = main_sep.value
        
    return xv.XuleValue(xule_context, result_string, 'string')
        
def property_sort(xule_context, object_value, *args):
    #sorted_list = sorted(object_value.value, key=lambda x: x.shadow_collection if x.type in ('set', 'list', 'dictionary') else x.value)

    reverse = False
    if len(args) == 1:
        if args[0].type == 'string':
            if args[0].value.lower() == 'asc':
                pass
            elif args[0].value.lower() == 'desc':
                reverse = True
            else:
                raise XuleProcessingError(_("The argument of the sort property must be either 'asc' or 'desc'. Found: '{}'.".format(args[0].value)), xule_context)
        else:
            raise XuleProcessingError(_("The argument of the sort property must be a string with either 'asc' or 'desc'. Found type: '{}'.".format(args[0].type)), xule_context)

    try:
        sorted_list = sorted(object_value.value, key=lambda x: x.sort_value, reverse=reverse)
        return xv.XuleValue(xule_context, tuple(sorted_list), 'list')
    except TypeError:
        # items are not sortable
        return XuleFunctions.agg_list(xule_context, object_value.value)

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
    return xv.XuleValue(xule_context, frozenset(keys), 'set', shadow_collection=frozenset(keys_shadow))

def property_values(xule_context, object_value, *args):
    try:
        keys = sorted(object_value.value_dictionary.keys(), key=lambda x: x.shadow_collection if x.type in ('set', 'list') else x.value)
    except TypeError: #unsortable types
        keys = object_value.value_dictionary.keys()
    vals = list(object_value.value_dictionary[k] for k in keys)
    vals_shadow = list(object_value.shadow_dictionary[k.shadow_colleciton if k.type in ('list', 'set') else k.value] for k in keys)
    
#     vals = list(v for k, v in object_value.value)
#     vals_shadow = list(v for k, v in object_value.shadow_collection)
    return xv.XuleValue(xule_context, tuple(vals), 'list', shadow_collection=tuple(vals_shadow))

def property_has_key(xule_context, object_value, *args):
    key = args[0].value
    return xv.XuleValue(xule_context, key in dict(object_value.shadow_collection), 'bool')

def property_networks(xule_context, object_value, *args):
    
    if len(args) > 0:
        arcrole_value = args[0]
        if arcrole_value.type == 'role':
            arcrole = arcrole_value.value.roleURI
        elif arcrole_value.type in ('uri', 'string'):
            arcrole = arcrole_value.value
        elif arcrole_value.type == 'qname':
            arcrole = XuleUtility.resolve_role(arcrole_value, 'arcrole', object_value.value, xule_context)
        elif arcrole_value.type == 'none':
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
        
    return xv.XuleValue(xule_context, get_networks(xule_context, object_value, arcrole, role), 'set')

def property_role(xule_context, object_value, *args):
    if object_value.type == 'network':
        role_uri = object_value.value[NETWORK_INFO][NETWORK_ROLE]
        #return xv.XuleValue(xule_context, object_value.value[NETWORK_INFO][NETWORK_ROLE], 'uri')
    elif object_value.type == 'relationship':
        role_uri = object_value.value.linkrole
    else: # label or reference
        role_uri = object_value.value.role
        #return xv.XuleValue(xule_context, object_value.value.role, 'uri')

    model_role = XuleUtility.role_uri_to_model_role(xule_context.model, role_uri)
    return xv.XuleValue(xule_context, model_role, 'role')

def property_role_uri(xule_context, object_value, *args):
    if object_value.type == 'network':
        role_uri = object_value.value[NETWORK_INFO][NETWORK_ROLE]
        #return xv.XuleValue(xule_context, object_value.value[NETWORK_INFO][NETWORK_ROLE], 'uri')
    elif object_value.type == 'relationship':
        role_uri = object_value.value.linkrole
    else: # label or reference
        role_uri = object_value.value.role
        #return xv.XuleValue(xule_context, object_value.value.role, 'uri')
    
    return xv.XuleValue(xule_context, role_uri, 'uri')

def property_role_description(xule_context, object_value, *args):
    if object_value.type == 'network':
        role_uri = object_value.value[NETWORK_INFO][NETWORK_ROLE]
        #return xv.XuleValue(xule_context, object_value.value[NETWORK_INFO][NETWORK_ROLE], 'uri')
    elif object_value.type == 'relationship':
        role_uri = object_value.value.linkrole        
    else: # label or reference
        role_uri = object_value.value.role
        #return xv.XuleValue(xule_context, object_value.value.role, 'uri')

    model_role = XuleUtility.role_uri_to_model_role(xule_context.model, role_uri)

    return xv.XuleValue(xule_context, model_role.definition, 'string')
    
def property_arcrole(xule_context, object_value, *args):
    if object_value.type == 'network':
        arcrole_uri = object_value.value[NETWORK_INFO][NETWORK_ARCROLE]
    else: # relationship
        arcrole_uri = object_value.value.arcrole

    model_arcrole = XuleUtility.arcrole_uri_to_model_role(xule_context.model, arcrole_uri)
    return xv.XuleValue(xule_context, model_arcrole, 'role')

def property_arcrole_uri(xule_context, object_value, *args):
    if object_value.type == 'network':
        arcrole_uri = object_value.value[NETWORK_INFO][NETWORK_ARCROLE]
    else: # relationship
        arcrole_uri = object_value.value.arcrole
    return xv.XuleValue(xule_context, arcrole_uri, 'uri')

def property_arcrole_description(xule_context, object_value, *args):
    if object_value.type == 'network':
        arcrole_uri = object_value.value[NETWORK_INFO][NETWORK_ARCROLE]
    else: # relationship
        arcrole_uri = object_value.value.arcrole

    model_arcrole = XuleUtility.arcrole_uri_to_model_role(xule_context.model, arcrole_uri)
    return xv.XuleValue(xule_context, model_arcrole.definition, 'string')

def property_concept(xule_context, object_value, *args):
    '''There are two forms of this property. The first is on a fact (with no arguments). This will return the concept of the fact.
       The second is on a taxonomy (with one argument). This will return the concept of the supplied qname argument in the taxonomy.
    '''
    if object_value.is_fact:
        if len(args) != 0:
            raise XuleProcessingError(_("Property 'concept' when used on a fact does not have any arguments, found %i" % len(args)), xule_context)
 
        return xv.XuleValue(xule_context, object_value.fact.concept, 'concept')
     
    elif object_value.type == 'taxonomy':
        if len(args) != 1:
            raise XuleProcessingError(_("Property 'concept' when used on a taxonomy requires 1 argument, found %i" % len(args)), xule_context)
         
        concept_qname_value = args[0]
         
        if concept_qname_value.type == 'none':
            concept_value = None
        else:
            if concept_qname_value.type != 'qname':
                raise XuleProcessingError(_("The 'concept' property of a taxonomy requires a qname argument, found '%s'" % concept_qname_value.type), xule_context)
             
            concept_value = get_concept(object_value.value, concept_qname_value.value)
         
        if concept_value is not None:
            return xv.XuleValue(xule_context, concept_value, 'concept')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    elif object_value.type == 'dimension':
        if len(args) > 0:
            raise XuleProcessingError(_("Property 'concept' on a dimension cannot have any arguments, found {}.".format(str(len(args)))), xule_context)
        return xv.XuleValue(xule_context, object_value.value.dimension_concept, 'concept')
    else: # None value
        return object_value

def property_period(xule_context, object_value, *args):
    if object_value.is_fact:
        if object_value.fact.context.isStartEndPeriod or object_value.fact.context.isForeverPeriod:
            return xv.XuleValue(xule_context, xv.model_to_xule_period(object_value.fact.context, xule_context), 'duration', from_model=True)
        else:
            return xv.XuleValue(xule_context, xv.model_to_xule_period(object_value.fact.context, xule_context), 'instant', from_model=True)
    else: #none value
        return object_value
          
def property_unit(xule_context, object_value, *args):
    if object_value.is_fact:
        if object_value.fact.unit is None:
            return xv.XuleValue(xule_context, None, 'none')
        else: #none value
            return xv.XuleValue(xule_context, xv.model_to_xule_unit(object_value.fact.unit, xule_context), 'unit')
    else:
        return object_value
    
def property_entity(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, xv.model_to_xule_entity(object_value.fact.context, xule_context), 'entity')
    else: #none value
        return object_value
    
def property_id(xule_context, object_value, *args):
    if object_value.type == 'entity':
        return xv.XuleValue(xule_context, object_value.value[1], 'string')
    elif object_value.type == 'unit':
        if object_value.value.xml_id is None:
            return xv.XuleValue(xule_context, None, 'none')
        else:
            return xv.XuleValue(xule_context, object_value.value.xml_id, 'string')
    elif object_value.is_fact:
        if object_value.fact.id is None:
            return xv.XuleValue(xule_context, None, 'none')
        else:
            return xv.XuleValue(xule_context, object_value.fact.id, 'string')
    else: #none value
        return object_value 
    
def property_scale(xule_context, object_value, *args):
    if object_value.is_fact:
        if hasattr(object_value.fact, 'scaleInt'):
            return xv.XuleValue(xule_context, object_value.fact.scaleInt, 'int')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else: #none value
        return object_value
    
def property_format(xule_context, object_value, *args):
    if object_value.is_fact:
        if hasattr(object_value.fact, 'format'):
            return xv.XuleValue(xule_context, object_value.fact.format, 'qname')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else: #none value
        return object_value

def property_display_value(xule_context, object_value, *args):
    if object_value.is_fact:
        if hasattr(object_value.fact, 'text'):
            return xv.XuleValue(xule_context, object_value.fact.text, 'string')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else: #none value
        return object_value    

def property_negated(xule_context, object_value, *args):
    if object_value.is_fact:
        if hasattr(object_value.fact, 'sign'):
            return xv.XuleValue(xule_context, object_value.fact.sign == '-', 'bool')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else: #none value
        return object_value  

def property_hidden(xule_context, object_value, *args):
    if object_value.is_fact:
        if object_value.fact.modelXbrl.modelDocument.type in (Type.INLINEXBRL, Type.INLINEXBRLDOCUMENTSET):
            return xv.XuleValue(xule_context, qname('http://www.xbrl.org/2013/inlineXBRL', 'hidden') in object_value.fact.ancestorQnames, 'bool')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else:
        return object_value

def property_scheme(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value[0], 'string')

def property_dimension(xule_context, object_value, *args):

    dim_name = args[0]
    if dim_name.type == 'qname':
            dim_qname = dim_name.value
    elif dim_name.type == 'concept':
        dim_qname = dim_name.value.qname
    else:
        raise XuleProcessingError(_("The argument for property 'dimension' must be a qname, found '%s'." % dim_name.type),xule_context)

    if object_value.is_fact:
        if not object_value.is_fact:
            return object_value
        
        model_fact = object_value.fact
        member_model = model_fact.context.qnameDims.get(dim_qname)
        if member_model is None:
            return xv.XuleValue(xule_context, None, 'none')
        else:
            if member_model.isExplicit:
                return xv.XuleValue(xule_context, member_model.member, 'concept')
            else:
                #this is a typed dimension
                return xv.XuleValue(xule_context, member_model.typedMember.xValue, xv.model_to_xule_type(xule_context, member_model.typedMember.xValue))

    else: # taxonomy
        # Get the cubes of the taxonomy
        cubes = [xv.XuleDimensionCube(object_value.value, *cube_base)
                 for cube_base in xv.XuleDimensionCube.base_dimension_sets(object_value.value)]
        dims = dict()
        for cube in cubes:
            for dim in cube.dimensions:
                dims[dim.dimension_concept.qname] = dim

        if dim_qname in dims:
            return xv.XuleValue(xule_context, dims[dim_qname], 'dimension')
        else:
            return xv.XuleValue(xule_context, None, 'none')

def property_dimensions(xule_context, object_value, *args):
    if object_value.type == 'taxonomy':
        # Get the cubes of the taxonomy
        cubes = [xv.XuleDimensionCube(object_value.value, *cube_base)
                 for cube_base in xv.XuleDimensionCube.base_dimension_sets(object_value.value)]
        # For each cube get the dimensions
        dims_shadow = set()
        for cube in cubes:
            dims_shadow |=  cube.dimensions
        dims = [xv.XuleValue(xule_context, x, 'dimension') for x in dims_shadow]
        return xv.XuleValue(xule_context, frozenset(dims), 'set', shadow_collection=frozenset(dims_shadow))
    if object_value.type == 'cube':
        dims_shadow = object_value.value.dimensions
        dims = {xv.XuleValue(xule_context, x, 'dimension') for x in dims_shadow}

        return xv.XuleValue(xule_context, frozenset(dims), 'set', shadow_collection=frozenset(dims_shadow))
    else: #fact
        if not object_value.is_fact:
            return object_value

        result_dict = dict()
        result_shadow = dict()

        for dim_qname, member_model in object_value.fact.context.qnameDims.items():
            dim_value = xv.XuleValue(xule_context, get_concept(xule_context.model, dim_qname), 'concept')
            if member_model.isExplicit:
                member_value = xv.XuleValue(xule_context, member_model.member, 'concept')
            else: # Typed dimension
                member_value = xv.XuleValue(xule_context, member_model.typedMember.xValue, xv.model_to_xule_type(xule_context, member_model.typedMember.xValue))

            result_dict[dim_value] = member_value
            result_shadow[dim_value.value] = member_value.value

        return xv.XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))

def property_dimensions_explicit(xule_context, object_value, *args):
    if not object_value.is_fact:
        return object_value
    
    result_dict = dict()
    result_shadow = dict()
    
    for dim_qname, member_model in object_value.fact.context.qnameDims.items():
        dim_value = xv.XuleValue(xule_context, get_concept(xule_context.model, dim_qname), 'concept')
        if member_model.isExplicit:
            member_value = xv.XuleValue(xule_context, member_model.member, 'concept')
    
            result_dict[dim_value] = member_value
            result_shadow[dim_value.value] = member_value.value
    
    return xv.XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))

def property_dimensions_typed(xule_context, object_value, *args):
    if not object_value.is_fact:
        return object_value
    
    result_dict = dict()
    result_shadow = dict()
    
    for dim_qname, member_model in object_value.fact.context.qnameDims.items():
        dim_value = xv.XuleValue(xule_context, get_concept(xule_context.model, dim_qname), 'concept')
        if not member_model.isExplicit:
            member_value = xv.XuleValue(xule_context, member_model.typedMember.xValue, xv.model_to_xule_type(xule_context, member_model.typedMember.xValue))
            
            result_dict[dim_value] = member_value
            result_shadow[dim_value.value] = member_value.value
    
    return xv.XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))

def property_aspects(xule_context, object_value, *args):
    if not object_value.is_fact:
        return object_value
    
    result_dict = dict()
    result_shadow = dict()
    
    concept_value = property_concept(xule_context, object_value)
    result_dict[xv.XuleValue(xule_context, 'concept', 'string')] = concept_value
    result_shadow['concept'] = concept_value.value
    
    entity_value = property_entity(xule_context, object_value)
    result_dict[xv.XuleValue(xule_context, 'entity', 'string')] = entity_value
    result_shadow['entity'] = entity_value.value
    
    period_value = property_period(xule_context, object_value)
    result_dict[xv.XuleValue(xule_context, 'period', 'string')] = period_value
    result_shadow['period'] = period_value.value
    
    unit_value = property_unit(xule_context, object_value)
    if unit_value.value is not None:
        result_dict[xv.XuleValue(xule_context, 'unit', 'string')] = unit_value
        result_shadow['unit'] = unit_value.value
        
    for dim_qname, member_model in object_value.fact.context.qnameDims.items():
        dim_value = xv.XuleValue(xule_context, get_concept(xule_context.model, dim_qname), 'concept')
        if member_model.isExplicit:
            member_value = xv.XuleValue(xule_context, member_model.member, 'concept')
        else: # Typed dimension
            member_value = xv.XuleValue(xule_context, member_model.typedMember.xValue, xv.model_to_xule_type(xule_context, member_model.typedMember.xValue))
            
        result_dict[dim_value] = member_value
        result_shadow[dim_value.value] = member_value.value
    
    return xv.XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))    

def property_start(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return xv.XuleValue(xule_context, object_value.value, 'instant', from_model=object_value.from_model)
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        return xv.XuleValue(xule_context, object_value.value[0], 'instant', from_model=object_value.from_model)
 
def property_end(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return xv.XuleValue(xule_context, object_value.value, 'instant', from_model=object_value.from_model)
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        return xv.XuleValue(xule_context, object_value.value[1], 'instant', from_model=object_value.from_model)  
 
def property_days(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return xv.XuleValue(xule_context, 0, 'int')
    else:
        return xv.XuleValue(xule_context, (object_value.value[1] - object_value.value[0]).days, 'int')

def property_numerator(xule_context, object_value, *args):
    # A unit is a tuple of numerator, denominator
    if len(object_value.value.numerator) == 1:
        return xv.XuleValue(xule_context, object_value.value.numerator[0], 'qname')
    else:
        # There are multiple measures - return a list
        result = list()
        result_shadow = list()
        for measure in object_value.value.numerator:
            result.append(xv.XuleValue(xule_context, measure, 'qname'))
            result_shadow.append(measure)
        return xv.XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))

def property_denominator(xule_context, object_value, *args):

    if len(object_value.value.denominator) == 1:
        return xv.XuleValue(xule_context, object_value.value.denominator[0], 'qname')
    else:
        # There are multiple measures - return a list
        result = list()
        result_shadow = list()
        for measure in object_value.value.denominator:
            result.append(xv.XuleValue(xule_context, measure, 'qname'))
            result_shadow.append(measure)
        return xv.XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))

def property_attribute(xule_context, object_value, *args):
    attribute_name_value = args[0]
    if attribute_name_value.type != 'qname':
        raise XuleProcessingError(_("The argument for the 'attribute' property must be a qname, found '{}'".format(attribute_name_value.type)), xule_context)
    
    attribute_value = object_value.value.get(attribute_name_value.value.clarkNotation)
    if attribute_value is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, attribute_value, 'string')

def property_balance(xule_context, object_value, *args):
    if object_value.type in ('none'):
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, object_value.value.balance, 'string')    

def property_base_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.value.modelXbrl.qnameTypes[object_value.fact.concept.baseXbrliTypeQname], 'type')
    elif object_value.type == 'concept':
        return xv.XuleValue(xule_context, object_value.value.modelXbrl.qnameTypes[object_value.value.baseXbrliTypeQname], 'type')
    else: #none value
        return object_value
 
def property_data_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.type, 'type')
    elif object_value.type == 'concept':
        return xv.XuleValue(xule_context, object_value.value.type, 'type')
    else: #none value
        return object_value

def property_substitution(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.substitutionGroupQname, 'qname')
    elif object_value.type == 'concept':
        return xv.XuleValue(xule_context, object_value.value.substitutionGroupQname, 'qname')
    else: #none value
        return object_value

def property_enumerations(xule_context, object_value, *args):
    if object_value.is_fact:
        model_type = object_value.fact.concept.type
    elif object_value.type == 'type':
        model_type = object_value.value
    elif object_value.type == 'concept':    
        model_type = object_value.value.type
    else: # None - this should not happen as the property only allows fact, type or concept.
        return object_value
    
    if model_type.facets is None:
        return xv.XuleValue(xule_context, frozenset(), 'set')
    else:
        if 'enumeration' in model_type.facets:
            enumerations = {xv.XuleValue(xule_context, x.value, xv.model_to_xule_type(xule_context, x.value)) for x in model_type.facets['enumeration'].values()}
            return xv.XuleValue(xule_context, frozenset(enumerations), 'set')
        else:
            return xv.XuleValue(xule_context, frozenset(), 'set')

def property_has_enumerations(xule_context, object_value, *args):
    if object_value.is_fact:
        model_type = object_value.fact.concept.type
    elif object_value.type == 'type':
        model_type = object_value.value
    elif object_value.type == 'concept':    
        model_type = object_value.value.type
    else: # None
        return xv.XuleValue(xule_context, False, 'bool')  
    
    if model_type.facets is None:
        return xv.XuleValue(xule_context, False, 'bool')
    else:
        return xv.XuleValue(xule_context, 'enumeration' in model_type.facets, 'bool')  
    
def property_is_type(xule_context, object_value, *args):
    type_name = args[0]
    if type_name.type != 'qname':
        raise XuleProcessingError(_("The argument for the 'is-type' property must ba a qname, found '{}'.".format(type_name.type)), xule_context)
    
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.instanceOfType(type_name.value), 'bool')
    elif object_value.type == 'concept': # concept
        return xv.XuleValue(xule_context, object_value.value.instanceOfType(type_name.value), 'bool')
    else: #none value
        return object_value
    
def property_is_numeric(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.isNumeric, 'bool')
    elif object_value.type == 'concept':
        #concept
        return xv.XuleValue(xule_context, object_value.value.isNumeric, 'bool')
    else:
        return object_value
    
def property_is_monetary(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.isMonetary, 'bool')
    elif object_value.type == 'concept':
        #concept
        return xv.XuleValue(xule_context, object_value.value.isMonetary, 'bool')
    else: #none value
        return object_value
    
def property_is_abstract(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.isAbstract, 'bool')
    elif object_value.type == 'concept':
        return xv.XuleValue(xule_context, object_value.value.isAbstract, 'bool')
    else: #none value
        return object_value

def property_is_nil(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.isNil, 'bool')
    #The object is none
    return object_value

def property_label(xule_context, object_value, *args):
    
    if object_value.is_fact:
        concept = object_value.fact.concept
    elif object_value.type == 'concept':
        concept = object_value.value
    else: #none value
        return object_value
    
    base_label_type = None
    base_lang = None
    if len(args) > 0:
        lang = None
        label_type = args[0]
        if label_type.type == 'none':
            base_label_type = None
        elif xv.xule_castable(label_type, 'string', xule_context):
            base_label_type = xv.xule_cast(label_type, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The first argument for property 'label' must be a string, found '%s'" % label_type.type), xule_context)
    if len(args) > 1: #there are 2 args
        lang = args[1]
        if lang.type == 'none':
            base_lang = None
        elif xv.xule_castable(lang, 'string', xule_context):
            base_lang = xv.xule_cast(lang, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The second argument for property 'label' must be a string, found '%s'" % lang.type), xule_context)        
     
    label = get_label(xule_context, concept, base_label_type, base_lang)
     
    if label is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, label, 'label')
     
def get_label(xule_context, concept, base_label_type, base_lang):
    #label_network = get_relationshipset(concept.modelXbrl, CONCEPT_LABEL)
    label_network = concept.modelXbrl.relationshipSet(CONCEPT_LABEL)
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
                        return label
            #if we are here, there were no matching labels in the ordered list of label types, so just pick one
            return next(iter(label_by_type.values()))
        elif len(label_by_type) > 0:
            #there is only one label just return it
            return next(iter(label_by_type.values()))
        else:
            return None        
    else:
        return None

#def get_relationshipset(model_xbrl, arcrole, linkrole=None, linkqname=None, arcqname=None, includeProhibits=False):
#    # This checks if the relationship set is already built. If not it will build it. The ModelRelationshipSet class
#    # stores the relationship set in the model at .relationshipSets.
#    relationship_key = (arcrole, linkrole, linkqname, arcqname, includeProhibits)
#    return model_xbrl.relationshipSets[relationship_key] if relationship_key in model_xbrl.relationshipSets else ModelRelationshipSet(model_xbrl, *relationship_key)

def property_text(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.textValue, 'string')
 
def property_lang(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.xmlLang, 'string')
 
def property_name(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.qname, 'qname')
    elif object_value.type in ('concept', 'reference-part', 'type'):
        return xv.XuleValue(xule_context, object_value.value.qname, 'qname')
    else: #none value
        return object_value
    
def property_local_name(xule_context, object_value, *args):

    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.qname.localName, 'string')
    elif object_value.type in ('concept', 'reference-part'):
        return xv.XuleValue(xule_context, object_value.value.qname.localName, 'string')
    elif object_value.type == 'qname':
        return xv.XuleValue(xule_context, object_value.value.localName, 'string')
    elif object_value.type == 'none':
        return object_value
    else:
        return xv.XuleValue(xule_context, '', 'string')
     
def property_namespace_uri(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, object_value.fact.concept.qname.namespaceURI, 'uri')
    elif object_value.type in ('concept', 'reference-part'):
        return xv.XuleValue(xule_context, object_value.value.qname.namespaceURI, 'uri')
    elif object_value.type == 'qname':
        return xv.XuleValue(xule_context, object_value.value.namespaceURI, 'uri')
    elif object_value.type == 'none':
        return object_value
    else:
        return xv.XuleValue(xule_context, '', 'uri')

def property_period_type(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.periodType, 'string')

def property_references(xule_context, object_value, *args):
    #reference type
    if len(args) > 0:
        reference_type = args[0]
        if reference_type.type == 'none':
            base_reference_type = None
        elif xv.xule_castable(reference_type, 'string', xule_context):
            base_reference_type = xv.xule_cast(reference_type, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The first argument for property 'reference' must be a string, found '%s'" % reference_type.type), xule_context)
    else:
        base_reference_type = None    
 
    if object_value.is_fact:
        concept = object_value.fact.concept
    else:
        concept = object_value.value

    #If there is no concept, then return an empty set.
    if concept is None:
        return xv.XuleValue(xule_context, frozenset(), 'set')
 
    #reference_network = get_relationshipset(concept.modelXbrl, CONCEPT_REFERENCE)
    reference_network = concept.modelXbrl.relationshipSet(CONCEPT_REFERENCE)
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
                        xule_references = set(xv.XuleValue(xule_context, x, 'reference') for x in references)
                        return xv.XuleValue(xule_context, frozenset(xule_references), 'set')
            #if we are here, there were no matching references in the ordered list of label types, so just pick one
            return xv.XuleValue(xule_context, frozenset(set(xv.XuleValue(xule_context, x, 'reference') for x in next(iter(reference_by_type.values())))), 'set')
        elif len(reference_by_type) > 0:
            #there is only one reference just return it
            return xv.XuleValue(xule_context, frozenset(set(xv.XuleValue(xule_context, x, 'reference') for x in next(iter(reference_by_type.values())))), 'set')
        else:
            return xv.XuleValue(xule_context, frozenset(), 'set')        
    else:
        return xv.XuleValue(xule_context, frozenset(), 'set')       
 
def property_parts(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, tuple(list(xv.XuleValue(xule_context, x, 'reference-part') for x in object_value.value)), 'list')
 
def property_part_value(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.textValue, 'string')
 
def property_part_by_name(xule_context, object_value, *args):
    part_name = args[0]
     
    if part_name.type != 'qname':
        raise XuleProcessingError(_("The argument for property 'part_by_name' must be a qname, found '%s'." % part_name.type), xule_context)
     
    for part in object_value.value:
        if part.qname == part_name.value:
            return xv.XuleValue(xule_context, part, 'reference-part')
     
    #if we get here, then the part was not found
    return xv.XuleValue(xule_context, None, 'none')

def property_order(xule_context, object_value, *args):
    if object_value.type == 'relationship':
        if object_value.value.order is not None:
            return xv.XuleValue(xule_context, float(object_value.value.order), 'float')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else: #reference-part
        part = object_value.value
        reference = part.getparent()
        for position, child in enumerate(reference, 1):
            if child is part:
                return xv.XuleValue(xule_context, position, 'int')
        # Should never get here, but just in case
        return xv.XuleValue(xule_context, None, 'none')

def property_concepts(xule_context, object_value, *args):
     
    if object_value.type == 'taxonomy':
        concepts = set(xv.XuleValue(xule_context, x, 'concept') for x in object_value.value.qnameConcepts.values() if x.isItem or x.isTuple)
    elif object_value.type == 'network':
        concepts = set(xv.XuleValue(xule_context, x, 'concept') for x in (object_value.value[1].fromModelObjects().keys()) | frozenset(object_value.value[1].toModelObjects().keys()))
    else:
        raise XuleProcessingError(_("'concepts' is not a property of '%s'" % object_value.type), xule_context)
 
    return xv.XuleValue(xule_context, frozenset(concepts), 'set')

def property_concept_names(xule_context, object_value, *args):
     
    if object_value.type == 'taxonomy':
        concepts = set(xv.XuleValue(xule_context, x.qname, 'qname') for x in object_value.value.qnameConcepts.values() if x.isItem or x.isTuple)
    elif object_value.type == 'network':
        concepts = set(xv.XuleValue(xule_context, x.qname, 'qname') for x in (object_value.value[1].fromModelObjects().keys()) | frozenset(object_value.value[1].toModelObjects().keys()))
    else:
        raise XuleProcessingError(_("'concept-names' is not a property of '%s'" % object_value.type), xule_context)
 
    return xv.XuleValue(xule_context, frozenset(concepts), 'set')

def property_cube(xule_context, object_value, *args):
    """This returns the tables in a taxonomy

    It will have 2 arguments:
        args[0] - The concept or qname of the hypercube
        args[1] - The drs-role
    """
    if args[0].type == 'qname':
        cube_concept = get_concept(object_value.value, args[0].value)
    elif args[0].type == 'concept':
        cube_concept = args[0].value
    else:
        raise XuleProcessingError(_("The first argument of property 'cube' must be a qname or a concept, found '{}'.".format(args[0].type)), xule_context)

    if args[1].type in ('string', 'uri'):
        drs_role = args[1].value
    elif args[1].type == 'qname':
        drs_role = XuleUtility.resolve_role(args[1], 'role', xule_context.model, xule_context)
    else:
        raise XuleProcessingError(_("The second argument of property 'cube' must be a role uri or a short role, found '{}'.".format(args[1].type)), xule_context)

    cube = xv.XuleDimensionCube(object_value.value, drs_role, cube_concept)

    if cube is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, cube, 'cube')

def property_cubes(xule_context, object_value, *args):
    """This returns all the cubes in a taxonomy.
    """
    cubes = set()
    cubes_shadow = set()
    for cube_base in xv.XuleDimensionCube.base_dimension_sets(object_value.value):
        cube = xv.XuleDimensionCube(object_value.value, *cube_base)
        cubes.add(xv.XuleValue(xule_context, cube, 'cube'))
        cubes_shadow.add(cube)

    return xv.XuleValue(xule_context, frozenset(cubes), 'set', shadow_collection=frozenset(cubes_shadow))

def property_drs_role(xule_context, object_value, *args):
    return xv.XuleValue(xule_context,  object_value.value.drs_role, 'role')

def property_cube_concept(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.hypercube, 'concept')

def property_primary_concepts(xule_context, object_value, *args):
    prim_shadow = object_value.value.primaries
    prim = {xv.XuleValue(xule_context, x, 'concept') for x in prim_shadow}

    return xv.XuleValue(xule_context, frozenset(prim), 'set', shadow_collection=frozenset(prim_shadow))

def property_facts(xule_context, object_value, *args):
    facts_shadow = object_value.value.facts
    facts = {xv.XuleValue(xule_context, x, 'fact', alignment=None) for x in facts_shadow}

    return xv.XuleValue(xule_context, frozenset(facts), 'set', shadow_collection=frozenset(facts_shadow))

def property_default(xule_context, object_value, *args):
    default = object_value.value.default
    if default is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, default, 'concept')

def property_relationships(xule_context, object_value, *args):        
    relationships = set()
     
    for relationship in object_value.value[1].modelRelationships:
        relationships.add(xv.XuleValue(xule_context, relationship, 'relationship'))
     
    return xv.XuleValue(xule_context, frozenset(relationships), 'set')

def property_source_concepts(xule_context, object_value, *args):
    concepts = frozenset(xv.XuleValue(xule_context, x, 'concept') for x in object_value.value[1].fromModelObjects().keys())
    return xv.XuleValue(xule_context, concepts, 'set')
 
def property_target_concepts(xule_context, object_value, *args):
    concepts = frozenset(xv.XuleValue(xule_context, x, 'concept') for x in object_value.value[1].toModelObjects().keys())        
    return xv.XuleValue(xule_context, concepts, 'set')
 
def property_roots(xule_context, object_value, *args):
    concepts = frozenset(xv.XuleValue(xule_context, x, 'concept') for x in object_value.value[1].rootConcepts)
    return xv.XuleValue(xule_context, concepts, 'set')  

def property_source(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.fromModelObject, 'concept')
 
def property_target(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.toModelObject, 'concept')

def property_source_name(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.fromModelObject.qname, 'qname')
 
def property_target_name(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.toModelObject.qname, 'qname')

def property_weight(xule_context, object_value, *args):
    if object_value.value.weight is not None:
        return xv.XuleValue(xule_context, float(object_value.value.weight), 'float')
    else:
        return xv.XuleValue(xule_context, None, 'none')

def property_preferred_label(xule_context, object_value, *args):
    if object_value.value.preferredLabel is not None:
        return xv.XuleValue(xule_context, object_value.value.preferredLabel, 'uri')
    else:
        return xv.XuleValue(xule_context, None, 'none')

def property_link_name(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.linkQname, 'qname')

def property_arc_name(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.qname, 'qname')

def property_network(xule_context, object_value, *args):
    network_info = (object_value.value.arcrole, object_value.value.linkrole, object_value.value.linkQname, object_value.value.qname, False)

    #network = (network_info, 
    #           get_relationshipset(object_value.value.modelXbrl, 
    #                                network_info[NETWORK_ARCROLE],
    #                                network_info[NETWORK_ROLE],
    #                                network_info[NETWORK_LINK],
    #                                network_info[NETWORK_ARC]))
    
    network_relationship_set = object_value.value.modelXbrl.relationshipSet(
        network_info[NETWORK_ARCROLE],
        network_info[NETWORK_ROLE],
        network_info[NETWORK_LINK],
        network_info[NETWORK_ARC]
    )

    network = (network_info, network_relationship_set)
    return xv.XuleValue(xule_context, network, 'network')
    
def property_power(xule_context, object_value, *args):  
    arg = args[0]
     
    if arg.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The 'power' property requires a numeric argument, found '%s'" % arg.type), xule_context)
     
    combine_types = xv.combine_xule_types(object_value, arg, xule_context)
     
    return xv.XuleValue(xule_context, combine_types[1]**combine_types[2], combine_types[0])
 
def property_log10(xule_context, object_value, *args):
    if object_value.value == 0:
        return xv.XuleValue(xule_context, float('-inf'), 'float')
    elif object_value.value < 0:
        return xv.XuleValue(xule_context, float('nan'), 'float')
    else:
        return xv.XuleValue(xule_context, math.log10(object_value.value), 'float')
 
def property_abs(xule_context, object_value, *args):
    try:
        return xv.XuleValue(xule_context, abs(object_value.value), object_value.type)
    except Exception as e:       
        raise XuleProcessingError(_("Error calculating absolute value: %s" % str(e)), xule_context)
 
def property_signum(xule_context, object_value, *args):
    if object_value.value == 0:
        return xv.XuleValue(xule_context, 0, 'int')
    elif object_value.value < 0:
        return xv.XuleValue(xule_context, -1, 'int')
    else:
        return xv.XuleValue(xule_context, 1, 'int')                                    

def property_trunc(xule_context, object_value, *args):
    if len(args) == 0:
        power = 0
    else:
        if args[0].type == 'int':
            power = args[0].value
        elif args[0].type in ('float', 'decimal'):
            if args[0].value == float('inf'):
                return object_value
            if args[0].value == float('-inf'):
                return xv.XuleValue(xule_context, 0, 'int') 
            if int(args[0].value) == args[0].value:                
                if args[0].type == 'float':                   
                    power = int(args[0].value)
                else: #decimal
                    power = args[0].value.to_integral_value()
            else:
                raise XuleProcessingError(_("For the trunc() property, the places argument must be an integer value, found {}".format(args[0].value)), xule_context)
        else:
            raise XuleProcessingError(_("For the trunc() property, the places argument must be an integer value, found {}".format(args[0].type)), xule_context)

    #working in decimals because we cannot combine a decimal and a float in arithmetic operations (like power and multiply).
    working_value = decimal.Decimal(object_value.value)

    return xv.XuleValue(xule_context, math.trunc(working_value*decimal.Decimal(10)**power)*decimal.Decimal(10)**-power, 'decimal')

def property_round(xule_context, object_value, *args):
    if args[0].type == 'int':
        round_to = args[0].value
    elif args[0].type == 'float':
        if args[0].value == float('inf'):
            return object_value
        if args[0].value == float('-inf'):
            return xv.XuleValue(xule_context, 0, 'int')
        if args[0].value.is_integer():
            round_to = int(args[0].value)
        else:
            raise XuleProcessingError(_("The argument to the 'round' property must be an integer value, found {}.".format(args[0].value)), xule_context)
    elif args[0].type == 'decimal':
        if args[0].value.to_integral_value() == args[0].value:
            round_to = int(args[0].value)
        else:
            raise XuleProcessingError(_("The argument to the 'round' property must be an integer value, found {}.".format(args[0].value)), xule_context)            
    else:
        raise XuleProcessingError(_("The argument to the 'round' property must be a number, found {}.".format(args[0].type)), xule_context)
    
    return xv.XuleValue(xule_context, round(object_value.value, round_to), object_value.type)

def property_mod(xule_context, object_value, *args):

    if args[0].type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The argument for the 'mod' property must be numeric, found '%s'" % args[0].type), xule_context)
    
    combined_type, numerator_compute_value, denominator_compute_value = xv.combine_xule_types(object_value, args[0], xule_context)
    return xv.XuleValue(xule_context, numerator_compute_value % denominator_compute_value, combined_type)    

def property_substring(xule_context, object_value, *args):     
    if len(args) == 0:
        raise XuleProcessingError(_("Substring reuqires at least 1 argument, found none."), xule_context)
    cast_value = xv.xule_cast(object_value, 'string', xule_context)
    
    if xv.xule_castable(args[0], 'int', xule_context):
        start_value = xv.xule_cast(args[0], 'int', xule_context) - 1
    else:
        raise XuleProcessingError(_("The first argument of property 'substring' is not castable to a 'int', found '%s'" % args[0].type), xule_context)
    
    if len(args) == 1:
        return xv.XuleValue(xule_context, cast_value[start_value:], 'string')
    else:
        if xv.xule_castable(args[1], 'int', xule_context):
            end_value = xv.xule_cast(args[1], 'int', xule_context)
        else:
            raise XuleProcessingError(_("The second argument of property 'substring' is not castable to a 'int', found '%s'" % args[1].type), xule_context)
 
        return xv.XuleValue(xule_context, cast_value[start_value:end_value], 'string')
     
def property_index_of(xule_context, object_value, *args):
    cast_value = xv.xule_cast(object_value, 'string', xule_context)
 
    arg_result = args[0]
    if xv.xule_castable(arg_result, 'string', xule_context):
        index_string = xv.xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
     
    return xv.XuleValue(xule_context, cast_value.find(index_string) + 1, 'int')
 
def property_last_index_of(xule_context, object_value, *args):
    cast_value = xv.xule_cast(object_value, 'string', xule_context)
     
    arg_result = args[0]
    if xv.xule_castable(arg_result, 'string', xule_context):
        index_string = xv.xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'last-index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
     
    return xv.XuleValue(xule_context, cast_value.rfind(index_string) + 1, 'int')
 
def property_lower_case(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, xv.xule_cast(object_value, 'string', xule_context).lower(), 'string')
 
def property_upper_case(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, xv.xule_cast(object_value, 'string', xule_context).upper(), 'string')

def property_split(xule_context, object_value, *args):
    if args[0].type != 'string':
        raise XuleProcessingError(_("The separator argument for property 'string' must be a 'string', found '%s'" % args[0].type), xule_context)

    if args[0].value == '':
        # just return the entire string in a list. This is different from python which will raise an error
        return xv.XuleValue(xule_context,(xv.XuleValue(xule_context, object_value.value, 'string'), ), 'list', shadow_collection=(object_value.value, ))

    shadow = tuple(object_value.value.split(args[0].value))

    return xv.XuleValue(xule_context, tuple(xv.XuleValue(xule_context, x, 'string') for x in shadow), 'list', shadow_collection=shadow)

def property_trim(xule_context, object_value, *args):
    if len(args) == 0:
        side = 'both'
    else:
        if args[0].value.lower() in ('left', 'right', 'both'):
            side = args[0].value.lower()
        else:
            raise XuleProcessingError(_("The argument for property 'trim' must be one of 'left', 'right' or 'both', found '%s'" % args[0]), xule_context)

    if side == 'both':
        new_value = object_value.value.strip()
    elif side == 'left':
        new_value = object_value.value.lstrip()
    else:
        new_value = object_value.value.rstrip()
    
    return xv.XuleValue(xule_context, new_value, 'string')

def property_to_qname(xule_context, object_value, *args):
    '''Create a qname from a single string with an optional namespace prefix.

    QNames created with this property use the prefix defined in the rule set.'''

    # This property has an optional parameter of a namespace map. A namespace map is a dictionary
    # keyed by prefix of namespace uris. If the parameter is not supplied, the namespace
    # declaratoins in the rule set are used.

    if len(args) == 1:
        # namespace map is supplied
        if args[0].type != 'dictionary':
            raise XuleProcessingError(
                _("When a namespace map is supplied as the argument to the .to-qname(nsmap) property, it must be a dictionary,"
                  " found '{}'".format(args[0].type)), xule_context)

        namespace_map = args[0].shadow_dictionary
    else:
        namespace_map = {None if k == '*' else k: v.get('uri') for k, v in xule_context.global_context.catalog['namespaces'].items()}

    if object_value.value.count(':') > 1:
        raise XuleProcessingError(
            _("The local part of the 'to-qname' property can contain only 1 ':' to designate the namespace prefix. "
              "Found {} colons in {}".format(object_value.value.count(':'), object_value.value)), xule_context)
    elif ':' in object_value.value:
        # the name contains a colon
        prefix, local_name = object_value.value.split(':')
    else:
        prefix = None
        local_name = object_value.value

    #namespace_uri = xule_context.global_context.catalog['namespaces'].get(prefix if prefix is not None else '*', dict()).get('uri')
    namespace_uri = namespace_map.get(prefix)
    if namespace_uri is None:
        raise XuleProcessingError(_("In the 'to-qname' property, could not resolve the namespace prefix '{}' "
                                    "to a namespace uri in '{}'".format(prefix, object_value.value)), xule_context)

    return xv.XuleValue(xule_context, QName(prefix, namespace_uri, local_name), 'qname')


def property_day(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.day, 'int')

def property_month(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.month, 'int')

def property_year(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.value.year, 'int') 

def property_uri(xule_context, object_value, *args):
    if object_value.type == 'role':
        uri_value = getattr(object_value.value, 'roleURI', None) or getattr(object_value.value, 'arcroleURI', None)
        return xv.XuleValue(xule_context, uri_value, 'uri')
    if object_value.type == 'taxonomy':
        return xv.XuleValue(xule_context, object_value.value.fileSource.url, 'uri')
 
def property_description(xule_context, object_value, *args): 
    return xv.XuleValue(xule_context, object_value.value.definition, 'string')
 
def property_used_on(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, tuple(list(xv.XuleValue(xule_context, x, 'qname') for x in object_value.value.usedOns)), 'list')

def property_dts_document_locations(xule_context, object_value, *args):
    locations = set()
    for doc_url in object_value.value.urlDocs:
        locations.add(xv.XuleValue(xule_context, doc_url, 'uri'))
    return xv.XuleValue(xule_context, frozenset(locations), 'set') 

def property_document_location(xule_context, object_value, *args):
    if hasattr(object_value.value, 'modelDocument'):
        return xv.XuleValue(xule_context, object_value.value.modelDocument.uri, 'uri')
    else:
        return xv.XuleValue(xule_context, None, 'none')

def cleanDocumentUri(doc):
    if doc.filepathdir.endswith('.zip'):
        pathParts = doc.filepathdir.split('/')
        pathParts.pop()
        pathParts.append(doc.basename)
        return '/'.join(pathParts)
    else:
        return doc.uri

def property_entry_point(xule_context, object_value, *args):
    dts = object_value.value
    
    dtstype, documentlist = get_taxonomy_entry_point_doc(dts)
    uri_list = {}
    uri = None

    if dtstype in (Type.INSTANCE, Type.INLINEXBRL):
        for item in documentlist:
            uri_list[item.uri] = item
    elif dtstype == Type.INLINEXBRLDOCUMENTSET:
        for topitem in documentlist:
            for item in topitem.referencesDocument:
                uri_list[item.uri] = item
    else:
        uri_list[documentlist.uri] = documentlist
    
    for u in sorted(uri_list):
        uri = cleanDocumentUri(uri_list[u])
        break    
    
    return xv.XuleValue(xule_context, uri, 'uri')
    
def get_taxonomy_entry_point_doc(dts):
    if dts.modelDocument.type in (Type.INSTANCE, Type.INLINEXBRL, Type.INLINEXBRLDOCUMENTSET):
        # This will take the first document
        return dts.modelDocument.type, dts.modelDocument.referencesDocument
    else:
        return dts.modelDocument.type, dts.modelDocument

def property_entry_point_namespace(xule_context, object_value, *args):
    dts = object_value.value
    dtstype, documentlist = get_taxonomy_entry_point_doc(dts)
    namespaces = {}
    namespace = None

    if dtstype in (Type.INSTANCE, Type.INLINEXBRL):
        for item in documentlist:
            namespaces[item.uri] = item.targetNamespace
    elif dtstype == Type.INLINEXBRLDOCUMENTSET:
        for topitem in documentlist:
            for item in topitem.referencesDocument:
                namespaces[item.uri] = item.targetNamespace
    else:
        namespaces[documentlist.uri] = documentlist.targetNamespace
    
    for uri in sorted(namespaces.keys()):
        namespace = namespaces[uri]
        break
    
    if namespace is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, namespace, 'uri')

def get_concept(dts, concept_qname):
    concept = dts.qnameConcepts.get(concept_qname)
    if concept is None:
        return None
    else:
        if concept.isItem or concept.isTuple:
            return concept
        else:
            return None
 
def property_decimals(xule_context, object_value, *args):
    if object_value.is_fact and object_value.fact.decimals is not None:
        return xv.XuleValue(xule_context, float(object_value.fact.decimals), 'float')
    else:
        return xv.XuleValue(xule_context, None, 'none')
    

def get_networks(xule_context, dts_value, arcrole=None, role=None, link=None, arc=None):
    networks = set()
    dts = dts_value.value
    network_infos = get_base_set_info(dts, arcrole, role, link, arc)
    
    for network_info in network_infos:
        '''I THINK THESE NETWORKS ARE REALLY COMBINATION OF NETWORKS, SO I AM IGNORING THEM.
           NEED TO CHECK IF THIS IS TRUE.'''
        if (network_info[NETWORK_ROLE] is not None and
            network_info[NETWORK_LINK] is not None and
            network_info[NETWORK_ARC] is not None):
            
            #if network_info in dts.relationshipSets:
            #    net = xv.XuleValue(xule_context, (network_info, dts.relationshipSets[network_info]), 'network')
            #else:
            #    net = xv.XuleValue(xule_context, 
            #                    (network_info, 
            #                        get_relationshipset(dts, 
            #                                   network_info[NETWORK_ARCROLE],
            #                                   network_info[NETWORK_ROLE],
            #                                   network_info[NETWORK_LINK],
            #                                   network_info[NETWORK_ARC])),
            #                         'network')
            
            network_relationship_set = dts.relationshipSet(
                network_info[NETWORK_ARCROLE],
                network_info[NETWORK_ROLE],
                network_info[NETWORK_LINK],
                network_info[NETWORK_ARC]
            )
            net = xv.XuleValue(xule_context, (network_info, network_relationship_set), 'network')
            networks.add(net)

    return frozenset(networks)

def get_base_set_info(dts, arcrole=None, role=None, link=None, arc=None):
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

def property_sum(xule_context, object_value, *args):
    if len(object_value.value) == 0:
        sum_value = xv.XuleValue(xule_context, None, 'none')
    else:
        values = list(object_value.value)
        sum_value = values[0].clone()
        for next_value in values[1:]:
            combined_type, left, right = xv.combine_xule_types(sum_value, next_value, xule_context)
            if combined_type == 'set':
                sum_value = xv.XuleValue(xule_context, left | right, combined_type)
            else:
                sum_value = xv.XuleValue(xule_context, left + right, combined_type)
                
    sum_value.tags = object_value.tags
    sum_value.facts = object_value.facts
    
    return sum_value

def property_max(xule_context, object_value, *args):
    if len(object_value.value) == 0:
        max_value = xv.XuleValue(xule_context, None, 'none')
    else:
        values = list(object_value.value)
        max_value = values[0].clone()
        for next_value in values[1:]:
            if next_value.value > max_value.value:
                max_value = next_value.clone()
    
    max_value.tags = object_value.tags
    max_value.facts = object_value.facts
    
    return max_value

def property_min(xule_context, object_value, *args):
    if len(object_value.value) == 0:
        min_value = xv.XuleValue(xule_context, None, 'none')
    else:
        values = list(object_value.value)
        min_value = values[0].clone()
        for next_value in values[1:]:
            if next_value.value < min_value.value:
                min_value = next_value.clone()
    
    min_value.tags = object_value.tags
    min_value.facts = object_value.facts
    
    return min_value

def property_count(xule_context, object_value, *args):
    count_value = xv.XuleValue(xule_context, len(object_value.value), 'int')
    count_value.tags = object_value.tags
    count_value.facts = object_value.facts
    return count_value

def property_first(xule_context, object_value, *args):
    if len(object_value.value) == 0:
        first_value = xv.XuleValue(xule_context, None, 'none')
    else:
        if object_value.type == 'list':
            first_value = object_value.value[0].clone()
        else:
            first_value = list(object_value.value)[0].clone()
    
    first_value.tags = object_value.tags
    first_value.facts = object_value.facts
    return first_value

def property_last(xule_context, object_value, *args):
    if len(object_value.value) == 0:
        last_value = xv.XuleValue(xule_context, None, 'none')
    else:
        if object_value.type == 'list':
            last_value = object_value.value[-1].clone()
        else:
            last_value = list(object_value.value)[-1].clone()
    
    last_value.tags = object_value.tags
    last_value.facts = object_value.facts
    return last_value

def property_any(xule_context, object_value, *args):
    any_value = False
    for next_value in list(object_value.value):
        if next_value.type != 'bool':
            raise XuleProcessingError(_("Property any can only operator on booleans, but found '%s'." % next_value.type), xule_context)
        
        any_value = any_value or next_value.value
    
    any_value = xv.XuleValue(xule_context, any_value, 'bool')
    any_value.tags = object_value.tags
    any_value.facts = object_value.facts
    return any_value

def property_all(xule_context, object_value, *args):
    all_value = True
    for next_value in list(object_value.value):
        if next_value.type != 'bool':
            raise XuleProcessingError(_("Property all can only operator on booleans, but found '%s'." % next_value.type), xule_context)
        
        all_value = all_value and next_value.value
    
    all_value = xv.XuleValue(xule_context, all_value, 'bool')
    all_value.tags = object_value.tags
    all_value.facts = object_value.facts
    return all_value

def property_stats(xule_context, object_value, stat_function, *args):
    values = list()
    for next_value in object_value.value:
        if next_value.type not in ('int', 'float', 'decimal'):
            raise XuleProcessingError(_("Statistic properties expect nuemric inputs, found '{}'.".format(next_value.type)), xule_context)
        values.append(next_value.value)
    
    stat_calc_value = stat_function(values)
    stat_value = xv.XuleValue(xule_context, stat_calc_value, 'float')
    stat_value.tags = object_value.tags
    stat_value.facts = object_value.facts
    return stat_value

def property_number(xule_context, object_value, *args):

    if object_value.type in ('int', 'float', 'decimal'):
        return object_value
    elif object_value.type == 'string':
        try:
            if '.' in object_value.value:
                return xv.XuleValue(xule_context, decimal.Decimal(object_value.value), 'decimal')
            elif object_value.value.lower() in ('inf', '+inf', '-inf'):
                return xv.XuleValue(xule_context, float(object_value.value), 'float')
            else:
                return xv.XuleValue(xule_context, int(object_value.value), 'int')
        except Exception:
            raise XuleProcessingError(_("Cannot convert '%s' to a number" % object_value.value), xule_context)
    else:
        raise XuleProcessingError(_("Property 'number' requires a string or numeric argument, found '%s'" % object_value.type), xule_context)

def property_is_fact(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.is_fact, 'bool')
        
def property_type(xule_context, object_value, *args):
    if object_value.is_fact:
        return xv.XuleValue(xule_context, 'fact', 'string')
    else:
        return xv.XuleValue(xule_context, object_value.type, 'string') 
 
def property_compute_type(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.type, 'string')
 
def property_string(xule_context, object_value, *args):
    '''SHOULD THE META DATA BE INCLUDED???? THIS SHOULD BE HANDLED BY THE PROPERTY EVALUATOR.'''
    return xv.XuleValue(xule_context, object_value.format_value(), 'string')
 
def property_context_facts(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, "\n".join([str(f.qname) + " " + str(f.xValue) for f in xule_context.facts]), 'string')
 
def property_from_model(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, object_value.from_model, 'bool')
 
def property_alignment(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, str(object_value.alignment), 'string') 
 
def property_hash(xule_context, object_value, *args):
    return xv.XuleValue(xule_context, str(hash(object_value)), 'string')   
 
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
     
    return xv.XuleValue(xule_context, s, 'string')

def property_effective_weight(xule_context, object_value, *args):
    dts = object_value.value
    if args[0].type == 'concept':
        top = args[0].value
    elif args[0].type == 'qname':
        top = get_concept(dts, args[0].value)
    else:
        raise XuleProcessingError(_("The start concept argument for the 'effective-weight' property must be a 'concept' or 'qname', found '{}'.".format(args[0].type)), xule_context)
    
    if args[1].type == 'concept':
        bottom = args[1].value
    elif args[1].type == 'qname':
        bottom = get_concept(dts, args[1].value)
    else:
        raise XuleProcessingError(_("The end concept argument for the 'effective-weight' property must be a 'concept' or 'qname', found '{}'.".format(args[0].type)), xule_context)
    
    if top is None or bottom is None:
        # The top or bottom is not in the taxonomy
        return xv.XuleValue(xule_context, None, 'none')
    
    weights = set()
    for network in get_networks(xule_context, object_value, CORE_ARCROLES['summation-item']):
        if len(network.value[1].fromModelObject(top)) > 0 and len(network.value[1].toModelObject(bottom)) > 0:
            weights.add( numpy.sum([numpy.prod(x) for x in traverse_for_weight(network.value[1], top, bottom)]))

    if len(weights) == 1:
        return xv.XuleValue(xule_context, next(iter(weights)), 'float')
    else:
        return xv.XuleValue(xule_context, float(0), 'float')

def property_effective_weight_network(xule_context, object_value, *args):
    dts = object_value.value
    if args[0].type == 'concept':
        top = args[0].value
    elif args[0].type == 'qname':
        top = get_concept(dts, args[0].value)
    else:
        raise XuleProcessingError(_("The start concept argument for the 'effective-weight-network' property must be a 'concept' or 'qname', found '{}'.".format(args[0].type)), xule_context)
    
    if args[1].type == 'concept':
        bottom = args[1].value
    elif args[1].type == 'qname':
        bottom = get_concept(dts, args[1].value)
    else:
        raise XuleProcessingError(_("The end concept argument for the 'effective-weight-network' property must be a 'concept' or 'qname', found '{}'.".format(args[0].type)), xule_context)
    
    # Optional network argument
    if len(args) > 2:
        if args[2].type == 'network':
            networks = (args[2],) # one item tuple
        elif args[2].type == 'role':
            role = args[2].value.roleURI
            networks = get_networks(xule_context, object_value, CORE_ARCROLES['summation-item'], role)
        elif args[2].type in ('uri', 'string'):
            role = args[2].value
            networks = get_networks(xule_context, object_value, CORE_ARCROLES['summation-item'], role)
        elif args[2].type == 'qname':
            role = XuleUtility.resolve_role(args[2], 'role', object_value.value, xule_context)
            networks = get_networks(xule_context, object_value, CORE_ARCROLES['summation-item'], role)
        elif args[2].type in ('set', 'list'):
            networks = args[2].value
        else:
            raise XuleProcessingError(_("The optional network argument for the 'effective-weight-network' property must be one of 'network, role, uri, role uri string, short role name or set/list of networks', found '{}'".format(args[2].type)), xule_context)
        
        bad_networks = tuple("\tArc role: {}, Role: {}".format(x.value[NETWORK_INFO][NETWORK_ARCROLE], x.value[NETWORK_INFO][NETWORK_ROLE]) 
                             for x in networks if x.value[NETWORK_INFO][NETWORK_ARCROLE] != CORE_ARCROLES['summation-item'])
        
        if len(bad_networks) > 0:
            raise XuleProcessingError(_("Network passed to 'effective-weight-network' is not a summation-item network. "
                                        "The 'effective-weight-network' property can only be used on summation-item networks. "
                                        "The invalid networks are:\n{}".format("\n".join(bad_networks))))

    else:
        networks = get_networks(xule_context, object_value, CORE_ARCROLES['summation-item'])
    
    if top is None or bottom is None:
        # The top or bottom is not in the taxonomy
        return xv.XuleValue(xule_context, None, 'none')
    
    return_set = set()

    for network in networks:
        if len(network.value[1].fromModelObject(top)) > 0 and len(network.value[1].toModelObject(bottom)) > 0:
            # For each path, multiple the weights. Then add the products together to get the effective weight.
            effective_weight = numpy.sum([numpy.prod(x) for x in traverse_for_weight(network.value[1], top, bottom)])
            effective_weight_value = xv.XuleValue(xule_context, effective_weight, 'float')

            return_set.add(xv.XuleValue(xule_context, (effective_weight_value, network), 'list'))
            
    return xv.XuleValue(xule_context, frozenset(return_set), 'set')

def traverse_for_weight(network, parent, stop_concept, previous_concepts=None, previous_weights=None):
    """Find all the weights between two concepts in a network.

    Returns a list of lists. Each inner list represents a path within the network. The items of the list are the weights
    for the path.
    """
    if parent is stop_concept:
        # should only get here is if the initial call the parent is the stop concept. In this case, the effective weight is 1
        return [1,]
    
    results = []
    
    previous_concepts = (previous_concepts or []) + [parent,]
    previous_weights = previous_weights or []
    
    for child_rel in network.fromModelObject(parent):
        if child_rel.toModelObject in previous_concepts:
            # In a cycle - skip this child.
            continue
        if child_rel.toModelObject is stop_concept:
            results.append(previous_weights + [child_rel.weight,])
        else:
            next_result = traverse_for_weight(network, child_rel.toModelObject, stop_concept, previous_concepts, previous_weights + [child_rel.weight,])
            if len(next_result) > 0:
                for x in next_result:
                    results.append(x)
    
    return results

def property_namespaces(xule_context, object_value, *args):
    namespaces = set(object_value.value.namespaceDocs.keys())
    namespaces_value = set(xv.XuleValue(xule_context, x, 'uri') for x in namespaces)
    return xv.XuleValue(xule_context, frozenset(namespaces_value), 'set', shadow_collection=namespaces)

def property_namespace_map(xule_context, object_value, *args):
    nsmap = object_value.fact.nsmap
    result = {xv.XuleValue(xule_context, prefix, 'stirng'): xv.XuleValue(xule_context, uri, 'uri') for prefix, uri in nsmap.items()}
    return xv.XuleValue(xule_context, frozenset(result.items()), 'dictionary')

def property_regex_match(xule_context, object_value, pattern, *args):
    if pattern.type != 'string':
        raise XuleProcessingError(_("Property regex match requires a string for the regex pattern, found '{}'".format(pattern.type)))

    return regex_match_object(xule_context, object_value.value, pattern)

def property_regex_match_all(xule_context, object_value, pattern, *args):
    if pattern.type != 'string':
        raise XuleProcessingError(_("Property regex match requires a string for the regex pattern, found '{}'".format(pattern.type)))

    search_start = 0
    xule_matches = []
    # Need to repeat match
    while search_start < len(object_value.value):
        match_object = regex_match_object(xule_context, object_value.value[search_start:], pattern, search_start)
        if match_object.shadow_dictionary['match-count'] == 0:
            break
        xule_matches.append(match_object)
        if match_object.shadow_dictionary['start'] > match_object.shadow_dictionary['end']:
            search_start += 1
        else:
            search_start = match_object.shadow_dictionary['end']

    return xv.XuleValue(xule_context, tuple(xule_matches), 'list')

def regex_match_object(xule_context, search_string, pattern, start=0):

    try:
        re_result = re.search(pattern.value, search_string)
    except Exception as e:
        raise XuleProcessingError(_("Error evaluaing regular exparession. Message: {}".format(e)))

    if re_result is None:
        # There were no matches
        xule_result = {xv.XuleValue(xule_context, 'match', 'string'): xv.XuleValue(xule_context, None, 'none'),
                       xv.XuleValue(xule_context, 'start', 'string'): xv.XuleValue(xule_context, 0, 'int'),
                       xv.XuleValue(xule_context, 'end', 'string'): xv.XuleValue(xule_context, 0, 'int'),
                       xv.XuleValue(xule_context, 'match-count', 'string'): xv.XuleValue(xule_context, 0, 'int'),
                       xv.XuleValue(xule_context, 'groups', 'string'): xv.XuleValue(xule_context, tuple(), 'list')}
    else:
        xule_result = dict()
        xule_result[xv.XuleValue(xule_context, 'match', 'string')] =  xv.XuleValue(xule_context, re_result.group(), 'string')
        xule_result[xv.XuleValue(xule_context, 'start', 'string')] = xv.XuleValue(xule_context, re_result.start() + 1 + start, 'int')
        xule_result[xv.XuleValue(xule_context, 'end', 'string')] = xv.XuleValue(xule_context, re_result.end() + start, 'int')
        xule_result[xv.XuleValue(xule_context, 'match-count', 'string')] = xv.XuleValue(xule_context, len(re_result.groups()) + 1, 'int')
        # Now process each group
        xule_groups = []

        for group_num in range(len(re_result.groups())):
            xule_group = dict()

            xule_group[xv.XuleValue(xule_context, 'group', 'string')] = xv.XuleValue(xule_context, group_num + 1, 'int')
            xule_group[xv.XuleValue(xule_context, 'match', 'string')] =  xv.XuleValue(xule_context, re_result.group(group_num + 1), 'string')
            xule_group[xv.XuleValue(xule_context, 'start', 'string')] = xv.XuleValue(xule_context, re_result.start(group_num + 1) + 1 + start, 'int')
            xule_group[xv.XuleValue(xule_context, 'end', 'string')] = xv.XuleValue(xule_context, re_result.end(group_num + 1) + start, 'int')

            xule_groups.append(xv.XuleValue(xule_context, frozenset(xule_group.items()), 'dictionary'))
        
        xule_result[xv.XuleValue(xule_context, 'groups', 'string')] = xv.XuleValue(xule_context, tuple(xule_groups), 'list') 
        
    return xv.XuleValue(xule_context, frozenset(xule_result.items()), 'dictionary')

def property_regex_match_string(xule_context, object_value, *args):
    if len(args) == 0 :
        raise XuleProcessingError(_("Property regex-match-stirng requires a match pattern"))

    if args[0].type != 'string':
        raise XuleProcessingError(_("Property regex match requires a string for the regex pattern, found '{}'".format(args[0].type)))
    else:
        pattern = args[0]
    
    if len(args) == 2:
        try:
            group_num = int(args[1].value)
        except (ValueError, TypeError):
            raise XuleProcessingError(_("Second argument of regex-match-string cannot be converted to an integer, found value '{}'".format(args[1].value)))
    else:
        group_num = None

    return regex_match_string(xule_context, object_value.value, pattern, group_num)[0]

def property_regex_match_string_all(xule_context, object_value, *args):
    if len(args) == 0 :
        raise XuleProcessingError(_("Property regex-match-stirng requires a match pattern"))

    if args[0].type != 'string':
        raise XuleProcessingError(_("Property regex match requires a string for the regex pattern, found '{}'".format(args[0].type)))
    else:
        pattern = args[0]
    
    if len(args) == 2:
        try:
            group_num = int(args[1].value)
        except (ValueError, TypeError):
            raise XuleProcessingError(_("Second argument of regex-match-string cannot be converted to an integer, found value '{}'".format(args[1].value)))
    else:
        group_num = None

    search_start = 0
    xule_matches = []
    # Need to repeat match
    while search_start < len(object_value.value):
        match_object, new_end = regex_match_string(xule_context, object_value.value[search_start:], pattern, group_num)
        if match_object.type == 'none':
            break
        xule_matches.append(match_object)
        if new_end == 0:
            search_start += 1
        else:
            search_start += new_end

    return xv.XuleValue(xule_context, tuple(xule_matches), 'list')

def regex_match_string(xule_context, search_string, pattern, group_num=None):

    try:
        re_result = re.search(pattern.value, search_string)
    except Exception as e:
        raise XuleProcessingError(_("Error evaluaing regular exparession. Message: {}".format(e)))

    if re_result is None:
        return xv.XuleValue(xule_context, None, 'none'), 0
    else:
        try:
            return xv.XuleValue(xule_context, re_result.group(group_num or 0), 'string'), re_result.end()
        except IndexError:
            raise XuleProcessingError(_("Group does not exist for group number {} for regex-match-string".format(group_num)))

#Property tuple
PROP_FUNCTION = 0
PROP_ARG_NUM = 1 #arg num allows negative numbers to indicated that the arguments are optional
PROP_OPERAND_TYPES = 2
PROP_UNBOUND_ALLOWED = 3
PROP_DATA = 4
PROP_VERSION = 5

PROPERTIES = {
              #NEW PROPERTIES
              'union': (property_union, 1, ('set',), False),
              'intersect': (property_intersect, 1, ('set',), False),
              'difference': (property_difference, 1, ('set',), False),
              'symmetric-difference': (property_symetric_difference, 1, ('set',), False),
              'contains': (property_contains, 1, ('set', 'list', 'string', 'uri'), False),
              'length': (property_length, 0, ('string', 'uri', 'set', 'list', 'dictionary'), False),
              'to-list': (property_to_list, 0, ('list', 'set'), False),
              'to-set': (property_to_set, 0, ('list', 'set', 'dictionary'), False),
              'to-dict': (property_to_dict, 0, ('list', 'set'), False),
              'index': (property_index, 1, ('list', 'dictionary'), False),
              'is-subset': (property_is_subset, 1, ('set',), False),
              'is-superset': (property_is_superset, 1, ('set',), False),
              'to-json': (property_to_json, 0, ('list', 'set', 'dictionary'), False),           
              'join': (property_join, -2, ('list', 'set', 'dictionary'), False),
              'sort': (property_sort, -1, ('list', 'set'), False),
              'keys': (property_keys, -1, ('dictionary',), False),
              'values': (property_values, 0, ('dictionary', ), False),
              'has-key': (property_has_key, 1, ('dictionary',), False),
              'decimals': (property_decimals, 0, (), True),
              'networks':(property_networks, -2, ('taxonomy',), False),
              'role': (property_role, 0, ('network', 'label', 'reference', 'relationship'), False),
              'role-uri': (property_role_uri, 0, ('network', 'label', 'reference', 'relationship'), False),
              'role-description': (property_role_description, 0, ('network', 'label', 'reference', 'relationship'), False),
              'arcrole':(property_arcrole, 0, ('network', 'relationship'), False),
              'arcrole-uri':(property_arcrole_uri, 0, ('network', 'relationship'), False),
              'arcrole-description':(property_arcrole_description, 0, ('network', 'relationship'), False),
              'concept': (property_concept, -1, ('fact', 'taxonomy', 'dimension'), True),
              'period': (property_period, 0, ('fact',), True),
              'unit': (property_unit, 0, ('fact',), True),
              'entity': (property_entity, 0, ('fact',), True),
              'namespace-map': (property_namespace_map, 0, ('fact',), True),
              'id': (property_id, 0, ('entity','unit','fact'), True),
              'scheme': (property_scheme, 0, ('entity',), False),
              'dimension': (property_dimension, 1, ('fact', 'taxonomy'), True),
              'dimensions': (property_dimensions, 0, ('fact', 'cube', 'taxonomy'), True),
              'dimensions-explicit': (property_dimensions_explicit, 0, ('fact',), True),
              'dimensions-typed': (property_dimensions_typed, 0, ('fact',), True),                            
              'aspects': (property_aspects, 0, ('fact',), True),
              'start': (property_start, 0, ('instant', 'duration'), False),
              'end': (property_end, 0, ('instant', 'duration'), False),
              'days': (property_days, 0, ('instant', 'duration'), False),
              'numerator': (property_numerator, 0, ('unit', ), False),
              'denominator': (property_denominator, 0, ('unit',), False),
              'attribute': (property_attribute, 1, ('concept', 'relationship', 'role'), False),
              'balance': (property_balance, 0, ('concept',), False),              
              'base-type': (property_base_type, 0, ('concept', 'fact'), True),
              'data-type': (property_data_type, 0, ('concept', 'fact'), True), 
              'substitution': (property_substitution, 0, ('concept', 'fact'), True),   
              'enumerations': (property_enumerations, 0, ('type', 'concept', 'fact'), True), 
              'has-enumerations': (property_has_enumerations, 0, ('type', 'concept', 'fact'), True),
              'is-type': (property_is_type, 1, ('concept', 'fact'), True),          
              'is-numeric': (property_is_numeric, 0, ('concept', 'fact'), True),
              'is-monetary': (property_is_monetary, 0, ('concept', 'fact'), True),
              'is-abstract': (property_is_abstract, 0, ('concept', 'fact'), True),
              'is-nil': (property_is_nil, 0, ('fact',), True),
              'is-fact': (property_is_fact, 0, (), True),
              'inline-scale': (property_scale, 0, ('fact',), True),
              'inline-format': (property_format, 0, ('fact',), True),
              'inline-display-value': (property_display_value, 0, ('fact',), True),
              'inline-negated': (property_negated, 0, ('fact',), True),
              'inline-hidden': (property_hidden, 0, ('fact',), True),
              'label': (property_label, -2, ('concept', 'fact'), True),
              'text': (property_text, 0, ('label',), False),
              'lang': (property_lang, 0, ('label',), False),              
              'name': (property_name, 0, ('fact', 'concept', 'reference-part', 'type'), True),
              'local-name': (property_local_name, 0, ('qname', 'concept', 'fact', 'reference-part'), True),
              'namespace-uri': (property_namespace_uri, 0, ('qname', 'concept', 'fact', 'reference-part'), True),              
              'period-type': (property_period_type, 0, ('concept',), False),
              'parts': (property_parts, 0, ('reference',), False),
              'part-value': (property_part_value, 0, ('reference-part',), False),
              'part-by-name': (property_part_by_name, 1, ('reference',), False),              
              'references':(property_references, -1, ('concept', 'fact'), True),
              'relationships': (property_relationships, 0, ('network',), False),
              'concepts': (property_concepts, 0, ('taxonomy', 'network'), False),
              'concept-names': (property_concept_names, 0, ('taxonomy', 'network'), False),
              'source-concepts': (property_source_concepts, 0, ('network',), False),
              'target-concepts': (property_target_concepts, 0, ('network',), False),
              'roots': (property_roots, 0, ('network',), False),
              'uri': (property_uri, 0, ('role', 'taxonomy'), False),
              'description': (property_description, 0, ('role',), False),
              'used-on': (property_used_on, 0, ('role',), False),
              'source': (property_source, 0, ('relationship',), False),
              'target': (property_target, 0, ('relationship',), False),              
              'source-name': (property_source_name, 0, ('relationship',), False),
              'target-name': (property_target_name, 0, ('relationship',), False),              
              'weight': (property_weight, 0, ('relationship',), False),
              'order': (property_order, 0, ('relationship', 'reference-part'), False),
              'preferred-label': (property_preferred_label, 0, ('relationship',), False),
              'link-name': (property_link_name, 0, ('relationship',), False),
              'arc-name': (property_arc_name, 0, ('relationship',), False),
              'network': (property_network, 0, ('relationship',), False),
              'power': (property_power, 1, ('int', 'float', 'decimal'), False),
              'log10': (property_log10, 0, ('int', 'float', 'decimal'), False),
              'abs': (property_abs, 0, ('int', 'float', 'decimal', 'fact'), False),
              'signum': (property_signum, 0, ('int', 'float', 'decimal', 'fact'), False),
              'trunc': (property_trunc, -1, ('int', 'float', 'decimal', 'fact'), False),
              'round': (property_round, 1, ('int', 'float', 'decimal', 'fact'), False),
              'mod': (property_mod, 1 ,('int', 'float', 'decimal', 'fact'), False),
              'number': (property_number, 0, ('int', 'float', 'decimal', 'fact'), False),
              'substring': (property_substring, -2, ('string', 'uri'), False),
              'index-of': (property_index_of, 1, ('string', 'uri'), False),
              'last-index-of': (property_last_index_of, 1, ('string', 'uri'), False),
              'lower-case': (property_lower_case, 0, ('string', 'uri'), False),
              'upper-case': (property_upper_case, 0, ('string', 'uri'), False),
              'split': (property_split, 1, ('string', 'uri'), False),
              'to-qname': (property_to_qname, -1, ('string'), False),
              'day': (property_day, 0, ('instant',), False),
              'month': (property_month, 0, ('instant',), False),
              'year': (property_year, 0, ('instant',), False),
              'string': (property_string, 0, (), False),
              'trim': (property_trim, -1, ('string', 'uri'), False),
              'dts-document-locations': (property_dts_document_locations, 0, ('taxonomy',), False),
              'entry-point': (property_entry_point, 0, ('taxonomy',), False),
              'entry-point-namespace': (property_entry_point_namespace, 0, ('taxonomy',), False),
              'effective-weight': (property_effective_weight, 2, ('taxonomy',), False),
              'effective-weight-network': (property_effective_weight_network, -3, ('taxonomy',), False),
              'document-location': (property_document_location, 0, (), False),
              'all': (property_all, 0, ('set', 'list'), False),
              'any': (property_any, 0, ('set', 'list'), False),
              'first': (property_first, 0, ('set', 'list'), False),
              'last': (property_last, 0, ('set', 'list'), False),
              'count': (property_count, 0, ('set', 'list'), False),
              'sum': (property_sum, 0, ('set', 'list'), False),
              'max': (property_max, 0, ('set', 'list'), False),
              'min': (property_min, 0, ('set', 'list'), False),           
              'stdev': (property_stats, 0, ('set', 'list'), False, numpy.std),
              'avg': (property_stats, 0, ('set', 'list'), False, numpy.mean),
              'prod': (property_stats, 0, ('set', 'list'), False, numpy.prod),
              'cube': (property_cube, 2, ('taxonomy',), False),
              'cubes': (property_cubes, 0, ('taxonomy',), False),
              'drs-role': (property_drs_role, 0, ('cube',), False),
              'cube-concept': (property_cube_concept, 0, ('cube',), False),
              'primary-concepts': (property_primary_concepts, 0, ('cube',), False),
              'facts': (property_facts, 0, ('cube',), False),
              'default': (property_default, 0, ('dimension',), False),
              'namespaces': (property_namespaces, 0, ('taxonomy',), False),

              # Version 1.1 properties
              #'regex-match-first': (property_regex_match_first, 1, ('string', 'uri'), False),
              'regex-match': (property_regex_match, 1, ('string', 'uri'), False),
              'regex-match-all': (property_regex_match_all, 1, ('string', 'uri'), False),
              'regex-match-string': (property_regex_match_string, -2, ('string', 'uri'), False),
              'regex-match-string-all': (property_regex_match_string_all, -2, ('string', 'uri'), False),

              # Debugging properties
              '_type': (property_type, 0, (), False),
              '_alignment': (property_alignment, 0, (), False),
              '_compute-type': (property_compute_type, 0, (), False),
              '_facts': (property_context_facts, 0, (), False),
              '_from-model': (property_from_model, 0, (), False),
              '_hash': (property_hash, 0, (), True),
              
              #Generate a list of available properties  
              '_list-properties': (property_list_properties, 0, ('unbound',), True),
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
