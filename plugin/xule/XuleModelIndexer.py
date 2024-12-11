"""XuleModelIndexer

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2024 XBRL US, Inc.

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
from arelle.ModelValue import qname
from arelle.XmlValidate import VALID
from .XuleValue import model_to_xule_entity, model_to_xule_period, model_to_xule_unit, XuleDimensionCube
import collections
import datetime
import itertools as it   
from .XuleRunTime import XuleProcessingError

def index_model(xule_context, model=None):
    """Index the facts in the Arelle model
    
    :param xule_context: The rule context
    :type xule_context: XuleRuleContext
    :returns: A dictionary of the facts. The dictionary is keyed by index keys.
    :rtype: dict
    
    This fucntion goes through all the facts in the Arelle model and organizes them by potential index keys. The index is used
    for factset evaluation. The keys are the aspects of the facts. Additional keys are based on properties of the aspects 
    (i.e. concept.is-monetary).
    """

    if model is None:
        model = xule_context.model

    if model is not None and getattr(model, 'xuleFactIndex', None) is None:
        fact_index = collections.defaultdict(lambda: collections.defaultdict(set))
        facts_to_index = collections.defaultdict(list)
        for model_fact in model.facts:
            if not fact_is_complete(model_fact):
                # Fact is incomplete. This can be caused by a filing that is still in the process of being built.
                # Ignore the fact and continue validating the rest of the filing.
                continue
            all_aspects = list()
            all_aspects.append((('builtin', 'concept'), model_fact.qname))

            period = model_to_xule_period(model_fact.context, xule_context)
            all_aspects.append((('builtin', 'period'), period))

            if model_fact.isNumeric:
                unit = model_to_xule_unit(model_fact.unit, xule_context)
                all_aspects.append((('builtin', 'unit'), unit))

            entity = model_to_xule_entity(model_fact.context, xule_context)
            all_aspects.append((('builtin', 'entity'), entity))

            for dim, mem in sorted(model_fact.context.qnameDims.items()):
                if mem.isExplicit:
                    all_aspects.append((('explicit_dimension', dim), mem.memberQname))
                else:
                    all_aspects.append((('explicit_dimension', dim), mem.typedMember.xValue))

            all_aspects = tuple(all_aspects)

            if getattr(xule_context.global_context.options, "xule_include_dups", False):
                facts_to_index[all_aspects].append(model_fact)
            else:
                # Need to eliminate duplicate facts.
                # Duplicate facts are facts that have the same aspects and same value (taking accuracy into account for numeric facts). If there are duplicates
                # with different values, then the duplicate is not eliminated.
                if all_aspects in facts_to_index:
                    # there is a fact already
                    found_match = False
                    for position in range(len(facts_to_index[all_aspects])):
                        saved_fact = facts_to_index[all_aspects][position]
                        if model_fact.isNumeric:
                            saved_value, saved_decimals, cur_value, cur_decimals = get_decimalized_value(saved_fact,
                                                                                                         model_fact,
                                                                                                         xule_context)
                            if cur_value == saved_value:
                                found_match = True
                                if cur_decimals > saved_decimals:
                                    facts_to_index[all_aspects][position] = model_fact
                                # otherwise, the saved fact is the better fact to index
                        else:
                            # fact is non numeric
                            if model_fact.xValue == saved_fact.xValue:
                                found_match = True

                    if not found_match:
                        # this is a duplicate with a different value
                        facts_to_index[all_aspects].append(model_fact)
                else:
                    # First time adding fact
                    facts_to_index[all_aspects].append(model_fact)

        # add the facts to the fact index.
        for all_aspects, facts in facts_to_index.items():
            for model_fact in facts:
                for aspect in all_aspects:
                    # aspect[0] is the aspect(dimension) name. aspect[1] is the aspect(dimension) value
                    fact_index[aspect[0]][aspect[1]].add(model_fact)
                for property in index_properties(model_fact):
                    fact_index[property[0]][property[1]].add(model_fact)

        # get all the facts
        all_facts = {fact for facts in facts_to_index.values() for fact in facts}

        # for each aspect add a set of facts that don't have that aspect with a key value of None
        for aspect_key in fact_index:
            fact_index[aspect_key][None] = all_facts - set(it.chain.from_iterable(fact_index[aspect_key].values()))

        # save the list of all facts.
        fact_index['all'] = all_facts

        # Save the fact index
        model.xuleFactIndex = fact_index

        # Create table index properties
        index_table_properties(model)

        # Add the None facts for the table properites. These are the facts that don't have the property.
        for aspect_key in fact_index:
            if aspect_key != 'all' and None not in fact_index[aspect_key]:
                fact_index[aspect_key][None] = all_facts - set(it.chain.from_iterable(fact_index[aspect_key].values()))


def index_properties(model_fact):
    """Calculate the properties for the fact.
    
    :param model_fact: The fact
    :type model_value: ModelFact
    :returns: A list of properties to add to the fact index. The items of the list are 2 item tuples of property identifier and property value.
    :rtype: list
    """
    prop_list = list()
    for property_key, property_function in FACT_INDEX_PROPERTIES.items():
        property_value = property_function(model_fact)
        if property_value is not None:
            prop_list.append((property_key, property_value))

    for attribute in model_fact.concept.elementAttributesTuple:
        # Create an aspect property for the concept aspect for any additional xml attributes that are on the concept.
        # attribute[0] is the attribute name. For qnames this will be in clarknotation
        # attribute[1] is the attribute value
        if attribute[0] not in ('id', 'name', 'substitutionGroup', 'type', '{http://www.xbrl.org/2003/instance}balance',
                                '{http://www.xbrl.org/2003/instance}periodType'):
            prop_list.append((('property', 'concept', 'attribute', qname(attribute[0])), attribute[1]))

    return prop_list


def index_property_start(model_fact):
    if model_fact.context.isStartEndPeriod:
        return model_fact.context.startDatetime
    elif model_fact.context.isInstantPeriod:
        return model_fact.context.endDatetime - datetime.timedelta(days=1)


def index_property_end(model_fact):
    if model_fact.context.isStartEndPeriod:
        return model_fact.context.endDatetime - datetime.timedelta(days=1)
    elif model_fact.context.isInstantPeriod:
        return model_fact.context.endDatetime - datetime.timedelta(days=1)


def index_property_days(model_fact):
    if model_fact.context.isStartEndPeriod:
        return (model_fact.context.endDatetime - model_fact.context.startDatetime).days
    elif model_fact.context.isInstantPeriod:
        return 0


def index_property_balance(model_fact):
    if model_fact.concept.balance is not None:
        return model_fact.concept.balance


# These are aspect properties that are used in a factset. I.e. @concept.is-monetary. The 'is-monetary' is an aspect property of the
# aspect 'concept'. This list identifies all the expected properties that will be in the fact index. This a dictionary with the key
# being the property identifier and the value being the function to calculate the value of the property with a fact. The property identifier
# is a 3 part tuple:
#    1 - 'property' - This part is always 'property'.
#    2 - the aspect name
#    3 - the property name
FACT_INDEX_PROPERTIES = {
    ('property', 'concept', 'period-type'): lambda f: f.concept.periodType,
    ('property', 'concept', 'balance'): index_property_balance,
    ('property', 'concept', 'data-type'): lambda f: f.concept.typeQname,
    ('property', 'concept', 'base-type'): lambda f: f.concept.baseXbrliTypeQname,
    ('property', 'concept', 'is-monetary'): lambda f: f.concept.isMonetary,
    ('property', 'concept', 'is-numeric'): lambda f: f.concept.isNumeric,
    ('property', 'concept', 'substitution'): lambda f: f.concept.substitutionGroupQname,
    ('property', 'concept', 'namespace-uri'): lambda f: f.concept.qname.namespaceURI,
    ('property', 'concept', 'local-name'): lambda f: f.concept.qname.localName,
    ('property', 'concept', 'is-abstract'): lambda f: f.concept.isAbstract,
    ('property', 'concept', 'id'): lambda f: f.id,
    ('property', 'period', 'start'): index_property_start,
    ('property', 'period', 'end'): index_property_end,
    ('property', 'period', 'days'): index_property_days,
    ('property', 'entity', 'scheme'): lambda f: f.context.entityIdentifier[0],  # entityIdentifier[0] is the scheme
    ('property', 'entity', 'id'): lambda f: f.context.entityIdentifier[1]
# entityIdentifer[1] is the id
}

TABLE_INDEX_PROPERTIES = {
    ('property', 'cube', 'name'),
    ('property', 'cube', 'drs-role')
}

def index_table_properties(model):
    """"Add the table properites to the fact index

    :type model: ModelXbrl
    """
    # Go through each table.
    for cube_base in XuleDimensionCube.base_dimension_sets(model):
        cube = XuleDimensionCube(model, *cube_base, include_facts=True)
        model.xuleFactIndex[('builtin', 'cube')][cube] |= cube.facts
        model.xuleFactIndex[('property', 'cube', 'name')][cube.hypercube.qname] |= cube.facts
        model.xuleFactIndex[('property', 'cube', 'drs-role')][cube.drs_role.roleURI] |= cube.facts

def get_decimalized_value(fact_a, fact_b, xule_context):
    """Adjust 2 fact values based on accuracy.
    
    :param fact_a: First fact
    :type fact_a: ModelFact
    :param fact_b: Second fact
    :type fact_b: ModelFact
    :returns: A tuple of the rounded fact values and the new decimals value for each
    :rtype: tuple
    
    Round the fact values to the minimum accuracy defined by the decimals attribute of the facts. 
    
    Example:
        Fact value of 1,234,567 with decimals -3 is rounded to 1,235,000
        
    Arguments:
        fact_a (ModelFact): First fact
        fact_b (ModelFact): Second fact
        xule_context (XuleRuleContext): Processing context
    """
    fact_a_decimals = get_decimals(fact_a, xule_context)
    fact_b_decimals = get_decimals(fact_b, xule_context)

    min_decimals = min(fact_a_decimals, fact_b_decimals)

    fact_a_value = fact_a.xValue if fact_a_decimals == float('inf') else round(fact_a.xValue, min_decimals)
    fact_b_value = fact_b.xValue if fact_b_decimals == float('inf') else round(fact_b.xValue, min_decimals)

    return fact_a_value, fact_a_decimals, fact_b_value, fact_b_decimals

def fact_is_complete(model_fact):
    if model_fact.xValid < VALID:
        return False
    if model_fact.context is None or not context_has_period(model_fact.context):
        return False
    if model_fact.isNumeric and model_fact.unit is None:
        return False
    return True


def context_has_period(model_context):
    return model_context.isStartEndPeriod or model_context.isInstantPeriod or model_context.isForeverPeriod

def get_decimals(fact, xule_context):
    """Return the decimals of a fact as a number.
    
    :param fact: The fact to get the accuracy from
    :type fact: ModelFact
    :param xule_context: Rule processing context
    :type xule_context: XuleRuleContext
    """
    if fact.decimals is None:
        return float('inf')

    if fact.decimals.strip() == 'INF':
        return float('inf')
    else:
        try:
            return int(fact.decimals)
        except ValueError:
            raise XuleProcessingError(_("%s Fact contains invalid decimal value of %s" % (fact.qname, fact.decimals)),
                                      xule_context)