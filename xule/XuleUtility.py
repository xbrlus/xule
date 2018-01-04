"""XuleMultiProcessing

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2018 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change$
DOCSKIP
"""
from arelle.ModelRelationshipSet import ModelRelationshipSet
import collections

from . import XuleConstants as xc
# XuleValue is a module. It is imported in the _imports() function to avoid a circular relative import error.
XuleValue = None
XuleProperties = None

def _imports():
    """Imports
    
    This function handles the imports. These imports are here to prevent circular relative import errors which happens in version priof to 3.5.
    """
    global XuleValue
    if XuleValue is None:
        from . import XuleValue
        
    global XuleProperties
    if XuleProperties is None:
        from . import XuleProperties

def add_sets(xule_context, left, right):
    _imports()
    new_set_values = list(left.value)
    new_shadow = list(left.shadow_collection)

    for item in right.value:
        if item.value not in new_shadow:
            new_shadow.append(item.shadow_collection if item.type in ('set','list','dictionary') else item.value)
            new_set_values.append(item)
    
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def subtract_sets(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in left.value:
        left_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if left_compute_value not in right.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
            
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def symetric_difference(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in left.value:
        compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if compute_value not in right.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
            
    for item in right.value:
        compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if compute_value not in left.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)                    

    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def intersect_sets(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in right.value:
        right_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if right_compute_value in left.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
    
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def resolve_role(role_value, role_type, dts, xule_context):
    """Resolve a role.
    
    A role is either a string, uri or a non prefixed qname. If it is a string or uri, it is a full arcrole. If it is
    a non prefixed qname, than the local name of the qname is used to match an arcrole that ends in 'localName'. If more than one arcrole is found then
    and error is raise. This allows short form of an arcrole i.e parent-child.
    """
    _imports()
    if role_value.value.prefix is not None:
        raise XuleProcessingError(_("Invalid {}. {} should be a string, uri or short role name. Found qname with value of {}".format(role_type, role_type.capitalize(), role_value.format_value())))
    else:
        if role_type == 'arcrole' and role_value.value.localName in xc.DIMENSION_PSEDDO_ARCROLES:
            return role_value.value.localName
        # Check that the dictionary of short arcroles is in the context. If not, build the diction are arcrole short names
        short_attribute_name = 'xule_{}_short'.format(role_type)
        if not hasattr(dts, short_attribute_name):
            if role_type == 'arcrole':
                setattr(dts, short_attribute_name, XuleProperties.CORE_ARCROLES.copy())
                dts_roles = dts.arcroleTypes
            else:
                setattr(dts, short_attribute_name, {'link': 'http://www.xbrl.org/2003/role/link'})
                dts_roles = dts.roleTypes
            
            short_role_dict = getattr(dts, short_attribute_name)
            for role in dts_roles:
                short_name = role.split('/')[-1] if '/' in role else role
                if short_name in short_role_dict:
                    short_role_dict[short_name] = None # indicates that there is a dup shortname
                else:
                    short_role_dict[short_name] = role
        
        short_role_dict = getattr(dts, short_attribute_name)
        short_name = role_value.value.localName
        if short_name not in short_role_dict:
            return None
            #raise XuleProcessingError(_("The {} short name '{}' does not match any arcrole.".format(role_type, short_name)))
        if short_name in (XuleProperties.CORE_ARCROLES if role_type == 'arcrole' else {'link': 'http://www.xbrl.org/2003/role/link'}) and short_role_dict[short_name] is None:
            raise XuleProcessingError(_("A taxonomy defined {role} has the same short name (last portion of the {role}) as a core specification {role}. " 
                                        "Taxonomy defined {role} is '{tax_role}'. Core specification {role} is '{core_role}'."
                                        .format(role=role_type, 
                                                tax_role=getattr(dts, short_attribute_name)[short_name], 
                                                core_role=XuleProperties.CORE_ARCROLES[short_name] if role_type == 'arcrole' else 'http://www.xbrl.org/2003/role/link')))
        if short_name in short_role_dict and short_role_dict[short_name] is None:
            raise XuleProcessingError(_("The {} short name '{}' resolves to more than one arcrole in the taxonomy.".format(role_type, short_name)))
        
        return short_role_dict[short_name]

def base_dimension_sets(dts):
    """Get the Xule base dimension sets.
    
    This is like the baseSets dictionary of a model. The base dimension set is a dictionary keyed by the drs role and hypercube. The drs role is the role of the initial 'all' relationship or the target role of the initial
    'all' relationship if ther eis a target role. The value of the diction is a set of the 'all' relationships.
    """
    _imports() 
    if not hasattr(dts, 'xuleBaseDimensionSets'):
        dts.xuleBaseDimensionSets = collections.defaultdict(set)
        for base_set in dts.baseSets:
            if (base_set[XuleProperties.NETWORK_ARCROLE] == 'http://xbrl.org/int/dim/arcrole/all' and 
                base_set[XuleProperties.NETWORK_ROLE] is not None and 
                base_set[XuleProperties.NETWORK_LINK] is not None and 
                base_set[XuleProperties.NETWORK_ARC] is not None):
                # This is an 'all' dimension base set find the hypercubes
                relationship_set =dts.relationshipSets.get(base_set,
                                                            ModelRelationshipSet(dts, 
                                                                               base_set[XuleProperties.NETWORK_ARCROLE],
                                                                               base_set[XuleProperties.NETWORK_ROLE],
                                                                               base_set[XuleProperties.NETWORK_LINK],
                                                                               base_set[XuleProperties.NETWORK_ARC]))
                
                for rel in relationship_set.modelRelationships:
                    drs_role = rel.targetRole or base_set[XuleProperties.NETWORK_ROLE]
                    hypercube = rel.toModelObject
                    dts.xuleBaseDimensionSets[(drs_role, hypercube)].add(rel)

    return dts.xuleBaseDimensionSets

def dimension_sets(dts):
    """The dimension sets in a dts.
    
    A dimension set is identified by a drs role and hypercube. 
    """
    _imports()
    if not hasattr(dts, 'xuleDimensionSets'):
        dts.xuleDimensionSets = dict()
    
    return dts.xuleDimensionSets

def dimension_set(dts, dimension_set_info):
    _imports()
    if dimension_set_info not in dimension_sets(dts):
        import datetime
        dimension_sets(dts)[dimension_set_info] = XuleValue.XuleDimensionRelationshipSet(dts, *dimension_set_info)

    return dimension_sets(dts)[dimension_set_info]                                                         
                                                                                        
def relationship_set(dts, relationship_set_info):
    _imports()
    return (dts.relationshipSets[relationship_set_info] 
                if relationship_set_info in dts.relationshipSets 
                else ModelRelationshipSet(dts, 
                                          relationship_set_info[XuleProperties.NETWORK_ARCROLE],
                                          relationship_set_info[XuleProperties.NETWORK_ROLE],
                                          relationship_set_info[XuleProperties.NETWORK_LINK],
                                          relationship_set_info[XuleProperties.NETWORK_ARC]))
    
DIMENSION_SET_ROLE = 0
DIMENSION_SET_HYPERCUBE = 1