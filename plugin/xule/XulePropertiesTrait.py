
from . import XuleProperties as xp
from . import XuleValue as xv

_TRAIT_CONCEPT_2021 = 'http://www.xbrl.org/2021/arcrole/trait-concept'
_TRAIT_CONCEPT_2023 = 'http://www.xbrl.org/2023/arcrole/trait-concept'
_CLASS_SUBCLASS_2021 = 'http://www.xbrl.org/2021/arcrole/class-subclass'
_CLASS_SUBCLASS_2023 = 'http://www.xbrl.org/2023/arcrole/class-subclass'

def property_traits(xule_context, object_value, *args):
    
    traits = set()
    concepts = {object_value.value,} # add the concept
    concepts |= get_ancestors(object_value.value, (_CLASS_SUBCLASS_2021, _CLASS_SUBCLASS_2023), False)
    for concept in concepts:
        traits |= get_ancestors(concept, (_TRAIT_CONCEPT_2021, _TRAIT_CONCEPT_2023))

    return_values = frozenset(xv.XuleValue(xule_context, trait, 'concept') for trait in traits)
    return xv.XuleValue(xule_context, return_values, 'set', shadow_collection=frozenset(traits))

def get_ancestors(concept, arc_roles, parent_only=True):
    dts = concept.modelXbrl
    network_infos = []
    for arc_role in arc_roles:
        network_infos.extend(xp.get_base_set_info(dts, arc_role))
    
    ancestors = set()

    for network_info in network_infos:
        network = dts.relationshipSet(
                network_info[xp.NETWORK_ARCROLE],
                network_info[xp.NETWORK_ROLE],
                network_info[xp.NETWORK_LINK],
                network_info[xp.NETWORK_ARC])
        for parent in  network.toModelObject(concept):
            ancestors.add(parent.fromModelObject)

    if not parent_only:
        next_ancestors = set()
        for ancestor in ancestors:
            next_ancestors |= get_ancestors(ancestor, arc_roles, parent_only)
        ancestors |= next_ancestors

    return ancestors

def trait_properties():
    props = {
              #NEW PROPERTIES
              'traits': (property_traits, 0, ('concept',), False),
    }

    return props