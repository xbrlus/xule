
from .XuleValue import *


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
