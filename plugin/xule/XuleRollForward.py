'''
Xule is rule processor for XBRL (X)brl r(ULE). 

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

$Change: 23204 $
DOCSKIP
'''
import collections
import re
import datetime
import copy
from arelle.ModelValue import QName
from . import XuleValue as xv
from .XuleRunTime import XuleProcessingError

def get_networks(*args):
    '''This function is a proxy for the real get_networks function in XuleProcessor. It is called this way to prevent a circular import.'''
    from .XuleProperties import get_networks
    return get_networks(*args)

def func_sdic_create(*args):
    from . import XuleFunctions as xf
    return xf.func_sdic_create(*args)

def func_sdic_append(*args):
    from . import XuleFunctions as xf
    return xf.func_sdic_append(*args)


def func_find_roll_forward(xule_context, *args):
    base_dts = args[0]
    if base_dts.type != 'taxonomy':
        raise XuleProcessingError(_("The argument of the 'find_rollforward' function must be a taxonomy, found '{}".format(base_dts.type)), xule_context)

    roll_forward_patterns = []
    
    _prep_roll_forward_constants(xule_context)
    
    start_rels = _get_balance(xule_context)
    
    for start_concept, start_infos in start_rels.items():
        base_total_concepts = _get_base_period_increase_decrease(xule_context, start_concept, base_dts)
        if base_total_concepts is None:
            continue
        for start_info in start_infos:
            pres_net, start_rel = start_info
            roll_forward_contribs = _get_contributing_concepts(xule_context, pres_net, start_rel, base_total_concepts, base_dts)
            if roll_forward_contribs is not None:
                contributing_concepts, total_concept, addins, subouts = roll_forward_contribs
                if len(contributing_concepts) > 0 or total_concept is not None:
                    dimension_info = _get_axis_member_pairs(xule_context, pres_net, start_concept)
                    roll_forward_patterns.append({'balance_concept': start_concept,
                                               'pres_net': pres_net,
                                               'dimension_info': dimension_info,
                                               'contributing_concepts': contributing_concepts,
                                               'addins': addins,
                                               'subouts': subouts,
                                               'total_concept': total_concept,
                                               'base_total_concepts': base_total_concepts,
                                               'base_taxonomy': base_dts})
    
    '''Leave the roll forward constants for the next rule'''
    #_clean_up_roll_forward_constants(xule_context)

    return xv.XuleValue(xule_context, tuple(roll_forward_patterns), 'roll_forward_set')

def _prep_roll_forward_constants(xule_context):
    xule_context.roll_forward = dict()
    
    us_gaap_ns = [ns for ns in xule_context.model.namespaceDocs if re.match(r'(http://fasb.org/|http://xbrl.us/)us-gaap/', ns)]
    if len(us_gaap_ns) == 0:
        raise XuleProcessingError(_("US GAAP taxonomy is not found."), xule_context)
    if len(us_gaap_ns) > 1:
        raise XuleProcessingError(_("Found more than one version for the US GAAP taxonomy: %s" % ", ".join(us_gaap_ns)), xule_context)
    
    xule_context.roll_forward['US_GAAP_NS'] = us_gaap_ns = us_gaap_ns[0] 
    xule_context.roll_forward['INCOME_STATEMENT_LOCATION_AXIS'] = QName(None, xule_context.roll_forward['US_GAAP_NS'], 'IncomeStatementLocationAxis')
    xule_context.roll_forward['ROLL_FORWARD_EXCEPTIONS'] = \
        {QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ShareBasedCompensationArrangementByShareBasedPaymentAwardEquityInstrumentsOtherThanOptionsNonvestedWeightedAverageGrantDateFairValue')
           ,QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingWeightedAverageExercisePrice')
           ,QName(None, xule_context.roll_forward['US_GAAP_NS'], 'SharebasedCompensationArrangementBySharebasedPaymentAwardOptionsNonvestedWeightedAverageGrantDateFairValue')
           ,QName(None, xule_context.roll_forward['US_GAAP_NS'], 'PartnersCapital')
           ,QName(None, xule_context.roll_forward['US_GAAP_NS'], 'PartnersCapitalAccountUnits')}
    
    xule_context.roll_forward['TOTAL_LABELS'] = ('http://www.xbrl.org/2003/role/totalLabel','http://www.xbrl.org/2009/role/negatedTotalLabel')

    xule_context.roll_forward['BASE_RF_CALCS'] = None
    xule_context.roll_forward['BASE_PERIOD_TOTALS'] = None
    xule_context.roll_forward['EXT_DEFAULTS'] = None
    xule_context.roll_forward['CALC_EXCEPTIONS'] = \
        {QName(None, xule_context.roll_forward['US_GAAP_NS'], 'AllowanceForLoanAndLeaseLossesPeriodIncreaseDecrease'):{QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ProvisionForLoanAndLeaseLosses'): 1,
                                                                                                                       QName(None, xule_context.roll_forward['US_GAAP_NS'], 'AllowanceForLoanAndLeaseLossesRecoveriesOfBadDebts'):1},
         QName(None, xule_context.roll_forward['US_GAAP_NS'], 'DefinedBenefitPlanBenefitObligationPeriodIncreaseDecrease'):{QName(None, xule_context.roll_forward['US_GAAP_NS'], 'DefinedBenefitPlanForeignCurrencyExchangeRateChangesBenefitObligation'):-1,
                                                                                                                            QName(None, xule_context.roll_forward['US_GAAP_NS'], 'DefinedBenefitPlanActuarialGainLoss'):-1,
                                                                                                                            QName(None, xule_context.roll_forward['US_GAAP_NS'], 'DefinedBenefitPlanOtherChanges'):1},
         QName(None, xule_context.roll_forward['US_GAAP_NS'], 'FiniteLivedIntangibleAssetsPeriodIncreaseDecrease'):{QName(None, xule_context.roll_forward['US_GAAP_NS'], 'AmortizationOfIntangibleAssets'):-1,
                                                                                                                    QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ImpairmentOfIntangibleAssetsFinitelived'):-1},
         QName(None, xule_context.roll_forward['US_GAAP_NS'], 'RestructuringReservePeriodIncreaseDecrease'):{QName(None, xule_context.roll_forward['US_GAAP_NS'], 'RestructuringReserveSettledWithCash'):-1,
                                                                                                             QName(None, xule_context.roll_forward['US_GAAP_NS'], 'RestructuringReserveSettledWithoutCash'):-1},         
         QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingPeriodIncreaseDecrease'):{QName(None, xule_context.roll_forward['US_GAAP_NS'], 'ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsGrantsInPeriod'):1}
        }  
        
    xule_context.roll_forward['EFFECTIVE_WEIGHTS'] = dict()
    xule_context.roll_forward['HAS_CALC'] = dict()
    xule_context.roll_forward['LINE_ITEM_CUBE'] = None
                                                  
def _clean_up_roll_forward_constants(xule_context):
    del xule_context.roll_forward
    
def _get_balance(xule_context):
    start_rels = collections.defaultdict(list)
    
    for pres_net in get_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), 'http://www.xbrl.org/2003/arcrole/parent-child'):
        for rel in pres_net.value[1].modelRelationships:
            if rel.preferredLabel == 'http://www.xbrl.org/2003/role/periodStartLabel':
                if rel.toModelObject.qname not in xule_context.roll_forward['ROLL_FORWARD_EXCEPTIONS']:
                    start_rels[rel.toModelObject].append((pres_net.value[1], rel))
                
    return start_rels

def _get_contributing_concepts(xule_context, pres_net, start_rel, base_total_concepts, base_dts):
    start_concept = start_rel.toModelObject
#     base_total_concepts = _get_base_period_increase_decrease(xule_context, start_concept)
#     if base_total_concepts is None:
#         return None
    total_concept = None
    contributing_concepts = []
    addins = []
    subouts = []
    end_found = False
    start_found = False
    
    return_total_only = False
    
    for rel in pres_net.fromModelObject(start_rel.fromModelObject):
        child_concept = rel.toModelObject
        if (rel.preferredLabel == 'http://www.xbrl.org/2003/role/periodEndLabel' and
            child_concept is start_concept):
            #found the end relationship
            end_found = True
            break
        elif child_concept is start_concept:
            #this is the start relationship
            start_found = True
        elif start_found:
            #This is a possible contributing concept.
            #The contributing concept's base type must match the balance concept.

            #check if it is the period total concept
            if (rel.preferredLabel in xule_context.roll_forward['TOTAL_LABELS'] and
              _verify_total_concept(xule_context, child_concept, start_concept, base_dts)):
                total_concept = child_concept     
            #it is not the period total concept, it could be a contributing concept
            elif child_concept.baseXbrliTypeQname == start_concept.baseXbrliTypeQname:
                contributing_concepts.append(child_concept)
                calc_sign =  _deterime_calc_sign(xule_context, child_concept, base_total_concepts, base_dts)
                if calc_sign == 1:
                    addins.append(child_concept)
                elif calc_sign == -1:
                    subouts.append(child_concept)
                else:
                    return_total_only = True
            else:
                '''THE _get_sub_pres_concepts NEEDS TO BE TESTED'''
                sub_children = _get_sub_pres_concepts(xule_context, pres_net, child_concept, start_concept, base_dts)
                contributing_concepts += sub_children
                for sub_child in sub_children:
                    calc_sign =  _deterime_calc_sign(xule_context, sub_child, base_total_concepts, base_dts)
                    if calc_sign == 1:
                        addins.append(sub_child)
                    elif calc_sign == -1:
                        subouts.append(sub_child)
                    else:
                        return_total_only = True
                        
    if end_found:  
        if return_total_only and total_concept is not None:
            return ([], total_concept, [], [])
        elif return_total_only:
            return None
        else:
            return (contributing_concepts, total_concept, addins, subouts)
    else:
        #return (contributing_concepts, total_concept, addins, subouts)
        return None
    
def _get_sub_pres_concepts(xule_context, pres_net, parent_concept, balance_concept, base_dts):
    sub_rels = [rel for rel in pres_net.fromModelObject(parent_concept) if rel.toModelObject.baseXbrliTypeQname == balance_concept.baseXbrliTypeQname]
    if len(sub_rels) == 0:
        return []
    else:
        #check the last concept to see if it has a total label
        last_rel = sub_rels[-1]
        before_rels = sub_rels[:-1]

        if last_rel.preferredLabel in xule_context.roll_forward['TOTAL_LABELS']:
            return [last_rel.toModelObject]
        else:
            #It may be a total concept, but just didn't have the preferred label. To find out, check if the is a calc for the last concept.
            if _has_matching_calc(xule_context, last_rel.toModelObject, before_rels, base_dts):
                return [last_rel.toModelObject]
            else:       
                #otherwise, all the matching sub_rels are contributing
                return [rel.toModelObject for rel in sub_rels]

def _has_matching_calc(xule_context, sum_concept, contrib_concepts, base_dts):
    if xule_context.roll_forward['BASE_RF_CALCS'] is None:
        calcs = collections.defaultdict(list)
        for calc_net in get_networks(xule_context, base_dts, 'http://www.xbrl.org/2003/arcrole/summation-item'):
            calc_items = [item for item in calc_net.value[1].fromModelObject(sum_concept)]
            calcs[sum_concept].append(calc_items)
            
        _BASE_RF_CALCS = calcs

    for base_calcs in _BASE_RF_CALCS.get(sum_concept):
        if len(set(base_calcs) & set(contrib_concepts)) == len(contrib_concepts):
            return True
    
    return False

def _verify_total_concept(xule_context, total_concept, balance_concept, base_dts):
    base_total_concepts = _get_base_period_increase_decrease(xule_context, balance_concept, base_dts)
    if base_total_concepts is not None:
        if total_concept.qname in [x.qname for x in base_total_concepts]:
            return True
    return False

def _get_base_period_increase_decrease(xule_context, balance_concept, base_dts):
    if xule_context.roll_forward['BASE_PERIOD_TOTALS'] is None:
        period_totals = collections.defaultdict(set)
        for base_pres_net in get_networks(xule_context, base_dts, 'http://www.xbrl.org/2003/arcrole/parent-child'):
            for start_rel in base_pres_net.value[1].modelRelationships:
                if start_rel.preferredLabel == 'http://www.xbrl.org/2003/role/periodStartLabel':
                    #found start concept, now look for the total in the
                    start_concept = start_rel.toModelObject
                    for total_rel in base_pres_net.value[1].fromModelObject(start_rel.fromModelObject):
                        if total_rel.preferredLabel in xule_context.roll_forward['TOTAL_LABELS'] and total_rel.toModelObject.periodType == 'duration':
                            period_totals[start_concept.qname].add(total_rel.toModelObject)
                            break
        _BASE_PERIOD_TOTALS = period_totals
    
    return _BASE_PERIOD_TOTALS.get(balance_concept.qname)

def _get_ext_default(xule_context, dimension_name):
    
    if xule_context.roll_forward['EXT_DEFAULTS'] is None:
        defaults = dict()
        for net in get_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), 'http://xbrl.org/int/dim/arcrole/dimension-default'):
            for rel in net.value[1].modelRelationships:
                defaults[rel.fromModelObject.qname] = rel.toModelObject.qname
        xule_context.roll_forward['EXT_DEFAULTS'] = defaults
    
    return xule_context.roll_forward['EXT_DEFAULTS'].get(dimension_name)

def _get_axis_member_pairs(xule_context, pres_net, balance_concept):
    pairs = dict()

    #If the line item is not in any cube, then return None.
    if not _in_any_cube(xule_context, balance_concept):
        return None
    
    #The balance item is not in a cube in the presentation linkrole
#     if not _in_any_cube(xule_context, balance_concept, linkrole=pres_net.linkrole):
#         return pairs
    
    line_items = {balance_concept,} | _ascend(pres_net, balance_concept, float('inf'), set(), 'concept')
    arcroles = ['http://xbrl.org/int/dim/arcrole/all',
                'http://xbrl.org/int/dim/arcrole/hypercube-dimension']

    dimensions = _navigate_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), line_items, pres_net.linkrole, arcroles, 1)
    if len(dimensions) == 0:
        return pairs
    
    for dimension in dimensions:
        domains = _navigate_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), [dimension], pres_net.linkrole, ['http://xbrl.org/int/dim/arcrole/dimension-domain'], 1)
        if len(domains) > 0:
            default = _get_ext_default(xule_context, dimension.qname)
            members = _navigate_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), domains, pres_net.linkrole, ['http://xbrl.org/int/dim/arcrole/domain-member'], float('inf'))  
            pairs[dimension.qname] = {"has_default": default is not None, "members": {x.qname for x in members}}
        
    return pairs

def _in_any_cube(xule_context, line_item, linkrole=None):
    #if the linkrole is none, than all networks are checked. otherwise only the network for the linkrole
    if xule_context.roll_forward['LINE_ITEM_CUBE'] is None:
        cubed_line_items = collections.defaultdict(set)
        for net in get_networks(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), 'http://xbrl.org/int/dim/arcrole/all'):
            for rel in net.value[1].modelRelationships:
                cubed_line_items[rel.fromModelObject].add(net.value[1].linkrole)
                domain_member_net = _get_single_network(xule_context, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'), 'http://xbrl.org/int/dim/arcrole/domain-member', net.value[1].linkrole)
                if domain_member_net is not None:
                    for mem_concept in _descend(domain_member_net, rel.fromModelObject, float('inf'), set(), 'concept'):
                        cubed_line_items[mem_concept].add(net.value[1].linkrole)

        xule_context.roll_forward['LINE_ITEM_CUBE'] = cubed_line_items

    if linkrole is None:
        return line_item in xule_context.roll_forward['LINE_ITEM_CUBE']
    else:
        if line_item in xule_context.roll_forward['LINE_ITEM_CUBE']:
            if linkrole in xule_context.roll_forward['LINE_ITEM_CUBE'][line_item]:
                return True
            else:
                return False
        else:
            return False
    
def _navigate_networks(xule_context, dts, starts, linkrole, arcroles, depth, return_type='concept'):
    children = set()
    net = _get_single_network(xule_context, dts, arcroles[0], linkrole)
    if net is None:
        return children
    for start in starts:
        children |= _descend(net, start, depth, set(), return_type)
    
    if len(arcroles) > 1:
        return _navigate_networks(xule_context, dts, children, linkrole, arcroles[1:], depth, return_type)
    else:
        return children

def _descend(network, parent, depth, previous_concepts, return_type):
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
            descendants = descendants | _descend(network, child, depth - 1, previous_concepts, return_type)

    return descendants

def _ascend(network, parent, depth, previous_concepts, return_type):
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
            ascendants = ascendants | _ascend(network, parent, depth - 1, previous_concepts, return_type)

    return ascendants

def _get_single_network(xule_context, dts, arc_role, role):
    nets = get_networks(xule_context, dts, arc_role, role)
    if nets is None:
        return None
    elif len(nets) == 0:
        return None
    else:
        return next(iter(nets)).value[1]
    
def _deterime_calc_sign(xule_context, contrib_concept, base_total_concepts, base_dts):
    if contrib_concept.qname.namespaceURI == xule_context.roll_forward['US_GAAP_NS']:
        #first check the calc exceptions
        for base_total_concept in base_total_concepts:
            if base_total_concept.qname in xule_context.roll_forward['CALC_EXCEPTIONS']:
                weight = xule_context.roll_forward['CALC_EXCEPTIONS'][base_total_concept.qname].get(contrib_concept.qname)
                if weight is not None:
                    return weight
        #check the base taxonomy effective weight between the total and the contrib
        for base_total_concept in base_total_concepts:
            base_contrib_concept = base_dts.value.qnameConcepts.get(contrib_concept.qname)
            if base_contrib_concept is None:
                return None
            weight = _get_effective_weight(xule_context, base_total_concept, base_contrib_concept, base_dts)
            if weight is not None:
                return weight
    #check the effetive weitht in the extension taxonomy
    for base_total_concept in base_total_concepts:
        ext_total_concept = xule_context.model.qnameConcepts.get(base_total_concept.qname)
        if ext_total_concept is not None:
            weight = _get_effective_weight(xule_context, ext_total_concept, contrib_concept, xv.XuleValue(xule_context, xule_context.model, 'taxonomy'))
            if weight is not None:
                return weight
    
    return None

def _get_effective_weight(xule_context, total_concept, contrib_concept, xule_dts):
    key = (xule_dts.value, total_concept.qname, contrib_concept.qname)
    if key in xule_context.roll_forward['EFFECTIVE_WEIGHTS']:
        return xule_context.roll_forward['EFFECTIVE_WEIGHTS'][key]
    else:
        for net in get_networks(xule_context, xule_dts, 'http://www.xbrl.org/2003/arcrole/summation-item'):
            effective_weight = 1
            '''This method of finding the effective will not work if there are indirect cycles.'''
            top_down_rels = _descend(net.value[1], total_concept, float('inf'), set(), 'relationship')
            bottom_up_rels = _ascend(net.value[1], contrib_concept, float('inf'), set(), 'relationship')
            top_to_bottom_rels = top_down_rels & bottom_up_rels
            if len(top_to_bottom_rels) > 0:
                for rel in top_to_bottom_rels:
                    effective_weight *= rel.weight  
                xule_context.roll_forward['EFFECTIVE_WEIGHTS'][key] = effective_weight
                return effective_weight
        xule_context.roll_forward['EFFECTIVE_WEIGHTS'][key] = None
        return None


'''
roll_forward_patterns.append({'balance_concept': start_concept,
                           'pres_net': pres_net,
                           'dimension_info': dimension_info,
                           'contributing_concept': contributing_concepts,
                           'total_concept': total_concept})
'''
   
def func_roll_forward_recalc(xule_context, *args):
    all_results = xv.XuleValueSet()
    
    roll_forward_pattern_set = args[0]
    if roll_forward_pattern_set.type != 'roll_forward_set':
        raise XuleProcessingError(_("Function 'roll_forward_recalc' requires a 'roll_forward_set', found '%s'" % roll_forward_pattern_set.type), xule_context)
    
    #process each found pattern
    for roll_forward_pattern in roll_forward_pattern_set.value:
        start_concept = roll_forward_pattern['balance_concept']
        fact_filters = [(('builtin','concept'), start_concept.qname)]
        balance_facts = _get_facts(xule_context, fact_filters)
        #eliminate facts that don't match the allowed dimensions from the pattern
        balance_facts = _valid_fact_dims(xule_context, balance_facts, roll_forward_pattern['dimension_info'])
        
        for start_fact in balance_facts:
            end_facts = [fact for fact in balance_facts if (fact.context.endDatetime > start_fact.context.endDatetime
                                                            and _aspects_match(fact, start_fact))]
            for end_fact in end_facts:     
                if roll_forward_pattern['total_concept'] is None:
                    period_total_fact = None
                else:
                    period_total_fact = _get_contrib_fact(xule_context, roll_forward_pattern['total_concept'].qname, start_fact, end_fact)    
                    
                if period_total_fact is not None:
                    addins = [period_total_fact]
                    subouts = []
                    ordered_facts = [period_total_fact]
                else:
                    contrib_facts = []
                    for contrib_concept in roll_forward_pattern['contributing_concepts']:
                        contrib_fact = _get_contrib_fact(xule_context, contrib_concept.qname, start_fact, end_fact)
                        if contrib_fact is not None:
                            contrib_facts.append(contrib_fact)
                            #weight = '+' if contrib_concept in roll_forward_pattern['addins'] else '-' if contrib_concept in roll_forward_pattern['subouts'] else 'NONE'
                            #print("  Contrib", contrib_fact.concept.qname, weight, contrib_fact.xValue, contrib_fact.context.startDatetime, contrib_fact.context.endDatetime)
                    #narrow down the list of concepts to just those that have facts
                    contrib_fact_concepts = [contrib_fact.concept for contrib_fact in contrib_facts]
                    discard_facts = set()
                    for contrib_fact in contrib_facts:
                        if _in_any_calc(xule_context, contrib_fact_concepts, contrib_fact.concept, roll_forward_pattern['base_taxonomy']):
                            discard_facts.add(contrib_fact)
                    
                    addins = []
                    subouts = []
                    ordered_facts = []
                    for contrib_fact in contrib_facts:
                        if contrib_fact not in discard_facts:
                            ordered_facts.append(contrib_fact)
                            if contrib_fact.concept in roll_forward_pattern['addins']:
                                addins.append(contrib_fact)
                            else:
                                subouts.append(contrib_fact)
                
                #calculate
                if len(ordered_facts) > 0:

#                     print("FOUND NONE", len(addins))
#                     for x in addins:
#                         if x is not None:
#                             print(x.concept.qname, x.xValue, x.isNil)
#                 
                    movement = sum(fact.xValue if not fact.isNil else 0 for fact in addins) - sum(fact.xValue if not fact.isNil else 0 for fact in subouts)
                    end_calc = start_fact.xValue + movement
                    
                    diff = end_fact.xValue - end_calc
                    
                    date_format = "%m/%d/%Y"
                    value_format = "{:,}"
                    
                    
                    display = []
                    role_uri = roll_forward_pattern['pres_net'].linkrole
                    role_description = xule_context.model.roleTypes[role_uri][0].definition 
                    #display.append('In role "' + role_description + '" - ' + role_uri)
                    display.append("For the period of " + start_fact.context.endDatetime.strftime(date_format) + " to " + (end_fact.context.endDatetime - datetime.timedelta(days=1)).strftime(date_format))
                    display.append("\t  " + value_format.format(start_fact.xValue) +  "\t" + str(start_fact.concept.qname) + " (BEGINNING BALANCE)")
                    for fact in ordered_facts:
                        sign = '+ ' if fact in addins else '- '
                        display.append("\t" + sign + value_format.format(fact.xValue) + "\t" + str(fact.concept.qname))
                    display.append("\t  " + value_format.format(end_fact.xValue) + "\t" + str(end_fact.concept.qname) + " (ENDING BALANMCE)")
                    display = "\n".join(display)
                                            
                    # #set up result sdic
                    # result = func_sdic_create(xule_context, xv.XuleValue(xule_context, "ROLL-FORWARD-RESULT", 'string'))
                    # if diff != 0:
                    #     result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "RECONCILED", 'string'), xv.XuleValue(xule_context, False, 'bool'))
                    # else:
                    #     result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "RECONCILED", 'string'), xv.XuleValue(xule_context, True, 'bool'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "END_VALUE", 'string'), xv.XuleValue(xule_context, end_fact, 'fact'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "CALC_VALUE", 'string'), xv.XuleValue(xule_context, end_calc, 'decimal'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "START_VALUE", 'string'), xv.XuleValue(xule_context, start_fact, 'fact'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "DIFFERENCE", 'string'), xv.XuleValue(xule_context, diff, 'decimal'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "MOVEMENT", 'string'), xv.XuleValue(xule_context, movement, 'decimal'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "START_PERIOD", 'string'), xv.XuleValue(xule_context, start_fact.context.endDatetime, 'instant', from_model=True))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "END_PERIOD", 'string'), xv.XuleValue(xule_context, end_fact.context.endDatetime, 'instant', from_model=True))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "DURATION", 'string'), xv.XuleValue(xule_context, (start_fact.context.endDatetime, end_fact.context.endDatetime), 'duration', from_model=True))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "DISPLAY", 'string'), xv.XuleValue(xule_context, display, 'string'))
                    # result = func_sdic_append(xule_context, result, xv.XuleValue(xule_context, "NETWORK_ROLE", 'string'), xv.XuleValue(xule_context, role_description + '" - ' + role_uri, 'string'))
                    #
                    # #add facts
                    # all_facts = dict()
                    # all_facts[start_fact] = None
                    # all_facts[end_fact] = None
                    # for ordered_fact in ordered_facts:
                    #     all_facts[ordered_fact] = None
                    # result.facts = all_facts
                    #
                    # all_results.append(result)

                    result = {}
                    result[xv.XuleValue(xule_context, 'RECONCILED', 'string')] = xv.XuleValue(xule_context, diff == 0, 'bool')
                    result[xv.XuleValue(xule_context, 'DISPLAY', 'string')] = xv.XuleValue(xule_context, display, 'string')
                    result[xv.XuleValue(xule_context, 'END_VALUE', 'string')] = xv.XuleValue(xule_context, end_fact, 'fact')
                    result[xv.XuleValue(xule_context, 'CALC_VALUE', 'string')] = xv.XuleValue(xule_context, end_calc, 'decimal')
                    result[xv.XuleValue(xule_context, 'START_VALUE', 'string')] = xv.XuleValue(xule_context, start_fact, 'fact')
                    result[xv.XuleValue(xule_context, 'DIFFERENCE', 'string')] = xv.XuleValue(xule_context, diff, 'decimal')
                    result[xv.XuleValue(xule_context, 'MOVEMENT', 'string')] = xv.XuleValue(xule_context, movement, 'decimal')
                    result[xv.XuleValue(xule_context, 'START_PERIOD', 'string')] = xv.XuleValue(xule_context, start_fact.context.endDatetime, 'instant', from_model=True)
                    result[xv.XuleValue(xule_context, 'END_PERIOD', 'string')] = xv.XuleValue(xule_context, end_fact.context.endDatetime, 'instant', from_model=True)
                    result[xv.XuleValue(xule_context, "DURATION", 'string')] = xv.XuleValue(xule_context, (start_fact.context.endDatetime, end_fact.context.endDatetime), 'duration', from_model=True)
                    result[xv.XuleValue(xule_context, "DISPLAY", 'string')] = xv.XuleValue(xule_context, display, 'string')
                    result[xv.XuleValue(xule_context, "NETWORK_ROLE", 'string')] = xv.XuleValue(xule_context, role_description + '" - ' + role_uri, 'string')

                    #add facts
                    all_facts = dict()
                    all_facts[start_fact] = None
                    all_facts[end_fact] = None
                    for ordered_fact in ordered_facts:
                        all_facts[ordered_fact] = None

                    result_value = xv.XuleValue(xule_context, frozenset(result.items()), 'dictionary')
                    result_value.facts = all_facts

                    all_results.append(result_value)

    return all_results


def _aspects_match(fact1, fact2):
    return (fact1.context.entityIdentifier == fact2.context.entityIdentifier and
            fact1.unit == fact2.unit and
            _normalize_dims(fact1.context.qnameDims) == _normalize_dims(fact2.context.qnameDims))
        
def _normalize_dims(dims):
    new_dims = set()
    for dim, dim_info in dims.items():
        new_dims.add((dim, dim_info.memberQname))
    return new_dims
    
def _get_facts(xule_context, filters):
    pre_facts = None
    facts = []
    #index is dict dict set
    for aspect_filter in filters:
        filter_key = aspect_filter[0]
        member = aspect_filter[1]
        
        if filter_key in xule_context.fact_index:
            if member in xule_context.fact_index[filter_key]:
                if pre_facts is None:
                    pre_facts = copy.copy(xule_context.fact_index[filter_key][member])
                else:
                    pre_facts &= xule_context.fact_index[filter_key][member]
            else:
                return facts
        else:
            return facts
        
    for fact in pre_facts:
        if not fact.isNil or (xule_context.include_nils):
            facts.append(fact)
            if fact.isNil and fact.isNumeric:
                fact.xValue = 0 
    if len(facts) > 0:
        return facts
    else:
        return facts


def _valid_fact_dims(xule_context, facts, pairs):
    # if paris is none, than any dimensionally qualified facts are allowed.
    if pairs is None:
        return facts
    
    new_facts = set()
    '''pairs[dimension.qname] = {"has_default": default is not None, "members": {x.qname for x in members}}'''
    for fact in facts:
        if len(fact.context.qnameDims) == 0:
            new_facts.add(fact)
        else:
            #the fact has dims, but no dims are allowed
            if len(pairs) == 0:
                continue
            
            fact_dims = []
            dim_check = True
            for dim, dim_info in fact.context.qnameDims.items():
                if dim not in pairs:
                    dim_check = False
                    break
                else:
                    if dim_info.memberQname not in pairs[dim]['members']:
                        dim_check = False
                        break
                fact_dims.append(dim)
            if not dim_check:
                continue
            for unused_dim in pairs.keys() - fact.context.qnameDims.keys():
                if not pairs[unused_dim]['has_default']:
                    dim_check = False
                    break
            if dim_check:
                new_facts.add(fact)
    return new_facts

def _get_contrib_fact(xule_context, concept_name, start_fact, end_fact):
    aspect_filters = [(('builtin','concept'), concept_name),
                      (('builtin','period'),(start_fact.context.endDatetime, end_fact.context.endDatetime))]
    start_normalized_dims = _normalize_dims(start_fact.context.qnameDims)
    facts = _get_facts(xule_context, aspect_filters)
    #print("getting", start_fact.concept.qname, concept_name, len(facts))
    if facts is not None:
        for fact in facts:
            normal_fact_dims = _normalize_dims(fact.context.qnameDims)
            if normal_fact_dims == start_normalized_dims:
                return fact
            
        for fact in facts:
            #check the income statment location axis
            normal_fact_dims = _normalize_dims(fact.context.qnameDims)
            if (len(normal_fact_dims) - 1  == len(start_normalized_dims) and 
                xule_context.roll_forward['INCOME_STATEMENT_LOCATION_AXIS'] not in start_fact.context.qnameDims and
                xule_context.roll_forward['INCOME_STATEMENT_LOCATION_AXIS'] in fact.context.qnameDims):
                #check that all the other dimensions match
                fact_dims_minus_income_statement = {x for x in normal_fact_dims if x[0] != xule_context.roll_forward['INCOME_STATEMENT_LOCATION_AXIS']}
                if fact_dims_minus_income_statement == start_normalized_dims:
                    return fact

    return None

def _in_any_calc(xule_context, possible_parents, concept, base_dts):
    check_net = []
    for possible_parent in possible_parents:
        key = (possible_parent.qname, concept.qname)
        in_calc = xule_context.roll_forward['HAS_CALC'].get(key)
        if in_calc is None:
            check_net.append(possible_parent.qname)
        elif in_calc == True:
            return True
    
    if len(check_net) > 0:
        base_concept = base_dts.value.qnameConcepts.get(concept.qname)
        if base_concept is None:
            xule_context.roll_forward['HAS_CALC'][key] = False
            return False
        for net in get_networks(xule_context, base_dts, 'http://www.xbrl.org/2003/arcrole/summation-item'):
            child = base_concept
            
            while True:
                parents = _ascend(net.value[1], child, 1, set(), 'concept')
                if len(parents) == 0:
                    break
                parent = next(iter(parents))
                key = (parent.qname, concept.qname)
                if parent.qname in check_net:
                    xule_context.roll_forward['HAS_CALC'][key] = True
                    return True
#                 else:
#                     xule_context.roll_forward['HAS_CALC'][key] = False
                child = parent
    for parent_qname in check_net:
        key = (parent_qname, concept.qname)
        xule_context.roll_forward['HAS_CALC'][key] = False
    return False       

def built_in_functions():
    funcs = {'find_roll_forward': ('regular', func_find_roll_forward, 1, False, 'single'),
             'roll_forward_recalc':('regular', func_roll_forward_recalc, 1, False, 'multi')}
    
    return funcs

BUILTIN_FUNCTIONS = built_in_functions()




