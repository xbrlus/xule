
from . import XuleProperties as xp
from . import XuleValue as xv
from arelle.ModelXbrl import ModelXbrl
import collections

_TAXONOMY_CONCEPTS = dict()

_TRAIT_CONCEPT_2021 = 'http://www.xbrl.org/2021/arcrole/trait-concept'
_TRAIT_CONCEPT_2023 = 'http://www.xbrl.org/2023/arcrole/trait-concept'
_CLASS_SUBCLASS_2021 = 'http://www.xbrl.org/2021/arcrole/class-subclass'
_CLASS_SUBCLASS_2023 = 'http://www.xbrl.org/2023/arcrole/class-subclass'

def property_traits(xule_context, object_value, *args):
    
    traits = _get_traits_for_concept(object_value.value)

    return_values = frozenset(xv.XuleValue(xule_context, trait, 'concept') for trait in traits)
    return xv.XuleValue(xule_context, return_values, 'set', shadow_collection=frozenset(traits))

def _get_traits_for_concept(model_concept):
    traits = set()
    concepts = {model_concept,} # add the concept
    concepts |= get_ancestors(model_concept, (_CLASS_SUBCLASS_2021, _CLASS_SUBCLASS_2023), False)
    for concept in concepts:
        traits |= get_ancestors(concept, (_TRAIT_CONCEPT_2021, _TRAIT_CONCEPT_2023))

    return traits

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


def property_concepts_by_trait(xule_context, object_value, *args):
    '''This will return the concept that have all the traits listed in the argument.
    
    The argument can either be a single value or a collection (set/list) of values.
    The values can be qnames or concepts (concepts that are traits).'''

    if args[0].type in ('set', 'list'):
        traits = args[0].value
    else:
        traits = {args[0],}

    result_concepts = set()

    tax_concepts = _get_concepts_for_taxonomy(object_value.value)

    for i, trait_value in enumerate(traits):
        if trait_value.type == 'concept':
            trait = trait_value.value.qname
        elif trait_value.type == 'qname':
            trait = trait_value.value
        else:
            raise xp.XuleProcessingError(_(f"The argument to the 'concepts-by-trait' property must be a concept or a qname, found {trait_value.type}."), xule_context)

        if i == 0:
            result_concepts.update(tax_concepts.get(trait, set())) # use update to make a copy
        else:
            result_concepts &= (tax_concepts.get(trait, set())) # intersection

    return_values = frozenset(xv.XuleValue(xule_context, con, 'concept') for con in result_concepts)

    return xv.XuleValue(xule_context, return_values, 'set', shadow_collection=frozenset(result_concepts))

def _get_concepts_for_taxonomy(taxonomy: ModelXbrl):
    if taxonomy not in _TAXONOMY_CONCEPTS:
        all_concepts_with_traits = _find_concepts_with_traits(taxonomy)

        tax_concepts = {x for x in all_concepts_with_traits
                       if (x.isItem or x.isTuple) and
                           x.qname.clarkNotation not in ('{http://www.xbrl.org/2003/instance}tuple', '{http://www.xbrl.org/2003/instance}item')}
        
        # this is a dictionary keyed by trait and the value is a list of concepts that have that trait
        tax_traits = collections.defaultdict(set)
        _TAXONOMY_CONCEPTS[taxonomy] = tax_traits
        
        for concept in tax_concepts:
            traits = _get_traits_for_concept(concept)
            for trait in traits:
                tax_traits[trait.qname].add(concept)


    return _TAXONOMY_CONCEPTS[taxonomy]

def _find_concepts_with_traits(taxonomy: ModelXbrl):
    '''This will find all concepts in the taxonomy that could have traits. This is used to narrow down the number of
       concepts that need to be checked for traits.'''
    results = set()

    # check all the trait-concept relationships
    network_infos = xp.get_base_set_info(taxonomy, _TRAIT_CONCEPT_2021) + \
                     xp.get_base_set_info(taxonomy, _TRAIT_CONCEPT_2023)
    for network_info in network_infos:
        network = taxonomy.relationshipSet(
                network_info[xp.NETWORK_ARCROLE],
                network_info[xp.NETWORK_ROLE],
                network_info[xp.NETWORK_LINK],
                network_info[xp.NETWORK_ARC])
        results.update(network.toModelObjects().keys())

    network_infos = xp.get_base_set_info(taxonomy, _CLASS_SUBCLASS_2021) + \
                    xp.get_base_set_info(taxonomy, _CLASS_SUBCLASS_2023)
    for network_info in network_infos:
        network = taxonomy.relationshipSet(
                network_info[xp.NETWORK_ARCROLE],
                network_info[xp.NETWORK_ROLE],
                network_info[xp.NETWORK_LINK],
                network_info[xp.NETWORK_ARC])
        for concept in  network.toModelObjects() | network.fromModelObjects():
            results.add(concept)

    return results

def trait_properties():
    props = {
              #NEW PROPERTIES
              'traits': (property_traits, 0, ('concept',), False),
              'concepts-by-trait': (property_concepts_by_trait, 1, ('taxonomy',), False),
    }

    return props