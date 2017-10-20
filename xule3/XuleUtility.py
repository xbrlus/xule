
from .XuleValue import *
from . import XuleProperties

def add_sets(xule_context, left, right):
    new_set_values = list(left.value)
    new_shadow = list(left.shadow_collection)

    for item in right.value:
        if item.value not in new_shadow:
            new_shadow.append(item.shadow_collection if item.type in ('set','list','dictionary') else item.value)
            new_set_values.append(item)
    
    return XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def subtract_sets(xule_context, left, right):
    new_set_values = set()
    new_shadow = set()
    
    for item in left.value:
        left_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if left_compute_value not in right.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
            
    return XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def symetric_difference(xule_context, left, right):
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

    return XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def intersect_sets(xule_context, left, right):
    new_set_values = set()
    new_shadow = set()
    
    for item in right.value:
        right_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if right_compute_value in left.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
    
    return XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def resolve_role(role_value, role_type, dts, xule_context):
    """Resolve a role.
    
    A role is either a string, uri or a non prefixed qname. If it is a string or uri, it is a full arcrole. If it is
    a non prefixed qname, than the local name of the qname is used to match an arcrole that ends in 'localName'. If more than one arcrole is found then
    and error is raise. This allows short form of an arcrole i.e parent-child.
    """

    if role_value.value.prefix is not None:
        raise XuleProcessingError(_("Invalid {}. {} should be a string, uri or short role name. Found qname with value of {}".format(role_type, role_type.capitalize(), role_value.format_value())))
    else:
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
