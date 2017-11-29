'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21745 $
'''
from .XuleContext import XuleGlobalContext, XuleRuleContext #XuleContext
from .XuleRunTime import XuleProcessingError, XuleIterationStop, XuleException, XuleBuildTableError, XuleReEvaluate
from .XuleValue import *
from . import XuleConstants as xc
from . import XuleUtility
#from  .XuleFunctions import *
from .XuleMultiProcessing import output_message_queue
from pyparsing import ParseResults
import itertools as it
from arelle.ModelValue import QName, dayTimeDuration, DateTime, gYear, gMonthDay, gYearMonth, qname
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelDtsObject import ModelConcept
import decimal
import datetime
import math
import re 
from aniso8601 import parse_duration, parse_datetime, parse_date
import collections
import copy
from lxml import etree as et
from threading import Thread
from . import XuleFunctions
#from . import XuleProperties
from . import XuleProperties
import os

def process_xule(rule_set, model_xbrl, cntlr, options):
    """Run Xule rules against a filing.
    
    This is the main function to process a Xule ruleset against a filing. This function just sets a few things up. The most import item is the processor context. The context saves the state of the processor
    throughout the processing of the rules.
    
    Arguments:
        rule_set(XuleRuleSet): An opened rule set
        model_xbrl (ModelXbrl): An XBRL instance as a ModelXbrl object from Arelle
        cntlr (Cntrl): A controller object from Arelle
        options (optparse.Values): Command line options
    """

    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, options)   
    
    # Set up trace files
    if getattr(global_context.options, "xule_trace_count", False):
        try:
            os.remove(global_context.options.xule_trace_count + ".csv")
        except FileNotFoundError:
            pass
        try:
            os.remove(global_context.options.xule_trace_count + ".txt")
        except FileNotFoundError:
            pass

    if getattr(global_context.options, "xule_time", None) is not None:
        total_start = datetime.datetime.today()
        
    if getattr(global_context.options, "xule_multi", False):
        t = Thread(target=output_message_queue, args=(global_context,))
        t.name = "Message Queue"
        t.start()
  
    # Create the processing context
    xule_context = XuleRuleContext(global_context)

    if getattr(global_context.options, "xule_time", None) is not None:
        fact_index_start = datetime.datetime.today()
    
    # Build an index on the facts in the model.
    global_context.fact_index = index_model(xule_context)
    
    if getattr(global_context.options, "xule_time", None) is not None:
        fact_index_end = datetime.datetime.today()
        global_context.message_queue.print("Index build time %s." % (fact_index_end - fact_index_start))

    # Create a list of rules to skip. These are determined by the --xule-skip option on the command line.
    skip_rules = getattr(global_context.options, "xule_skip", None).split(",") if getattr(global_context.options, "xule_skip", None) is not None else None

    # Determine is constants should be precalced. This is determined by the --xule-precalc-constants optoin on the command line. This is useful to simulate how the processor works in the server
    # environment.
    if getattr(global_context.options, "xule_precalc_constants", False):
        constant_start = datetime.datetime.today()
        process_precalc_constants(global_context)
        #process_precalc_preconditions(global_context)
        constant_end = datetime.datetime.today()
        constant_time = constant_end - constant_start
        global_context.message_queue.print("Time to calculated non instance constants: %s" % (constant_time))

    global_context.message_queue.logging("Processing Filing...")
    evaluate_rule_set(global_context, skip_rules)
    
    if getattr(global_context.options, "xule_time", None) is not None:
        total_end = datetime.datetime.today()
        if getattr(global_context.options, "xule_precalc_constants", False):
            global_context.message_queue.print("Time to process excluding non instance constant: %s." % (total_end - total_start - constant_time))       
        global_context.message_queue.print("Total time to process: %s." % (total_end - total_start))
    # Shutdown Message Queue
    if getattr(global_context.options, "xule_multi", False):
        global_context.message_queue.stop()
        global_context.message_queue.clear()
        t.join()  
    
        
def evaluate_rule_set(global_context, skip_rules):
    """Process the rule set.
    
    Arguments:
        global_context (XuleGlobalContext): Global running context
        skip_rules (list): List of rules to skip
    """
    if getattr(global_context.options, "xule_time", None) is not None:
        times = []

    #use the term "cat" for catalog information. Read through the list of rules in the catalog.
    for file_num, cat_rules in global_context.catalog['rules_by_file'].items():
        for rule_name in sorted(cat_rules.keys()):
            cat_rule = cat_rules[rule_name]
        
            if skip_rules is not None and rule_name in skip_rules:
                global_context.message_queue.print("Skipping rule: %s" % rule_name)
                continue
            
            #get the AST for the rule from the ruleset
            rule = global_context.rule_set.getItem(cat_rule)
            
            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.print("Processing: %s - %s" % (rule_name, datetime.datetime.today().strftime("%H:%M:%S.%f")))
                if global_context.model is not None:
                    global_context.message_queue.print(global_context.model.modelDocument.uri)
            
            # Preconditions - Currently not supported in Xule3    
            # if check_precondition(rule.preconditionRef, global_context) if 'preconditionRef' in rule else True:                                        
            try:
                if getattr(global_context.options, "xule_time", None) is not None or getattr(global_context.options, "xule_trace_count", False):
                    rule_start = datetime.datetime.today()
 
                # Establish the rule context. A new context is created for each rule.
                xule_context = XuleRuleContext(global_context,
                                               rule_name,
                                               file_num)
                #add the main table
                xule_context.iteration_table.add_table(rule['node_id'], xule_context.get_processing_id(rule['node_id']))
                
                # Evaluate the rule. 
                evaluate(rule, xule_context)
                 
            except (XuleProcessingError, XuleBuildTableError) as e:
                if getattr(global_context.options, "xule_crash", False):
                #if global_context.crash_on_error:
                    raise
                else:
                    xule_context.global_context.message_queue.error("xule:error", str(e))
 
            except XuleIterationStop:
                pass
             
            except Exception as e:
                if getattr(global_context.options, "xule_crash", False):
                #if global_context.crash_on_error:
                    raise
                else:
                    xule_context.global_context.message_queue.error("xule:error","rule %s: %s" % (rule_name, str(e)))
            
            
            if getattr(global_context.options, "xule_time", None) is not None:
                rule_end = datetime.datetime.today()
                times.append((xule_context.rule_name, rule_end - rule_start))
                if getattr(global_context.options, "xule_debug", False):
                    global_context.message_queue.print("%s time took: %s - %s " % (rule_name, (rule_end - rule_start).total_seconds(), datetime.datetime.today().strftime("%H:%M:%S.%f")))
            
            if getattr(global_context.options, "xule_trace_count", False):
                total_time = datetime.datetime.today() - rule_start
                print("Total iterations:", xule_context.iter_count, 
                      "Messages:", xule_context.iter_message_count, 
                      "Pass:", xule_context.iter_pass_count, 
                      "Non alignment:", xule_context.iter_misaligned_count,
                      "Exception:", xule_context.iter_except_count)
                write_trace_count_csv(global_context.options.xule_trace_count, rule_name, global_context.expression_trace, rule, xule_context.iter_count, total_time)
                write_trace_count_string(global_context.options.xule_trace_count, rule_name, global_context.expression_trace, rule, xule_context.iter_count, total_time)

    # Display timing information
    if getattr(global_context.options, "xule_time", None) is not None:
        global_context.message_queue.print("Total number of rules processed: %i" % len(times))
        #slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > 0.001]
        slow_rules = sorted([timing_info for timing_info in times if timing_info[1].total_seconds() > getattr(global_context.options, "xule_time", None)],
                            key=lambda tup: tup[1], reverse=True)
        #slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > global_context.show_timing]
        global_context.message_queue.print("Number of rules over %ss: %i" % (getattr(global_context.options, "xule_time", None), len(slow_rules)))
        for slow_rule in slow_rules:
            global_context.message_queue.print("Rule %s end. Took %s" % (slow_rule[0], slow_rule[1]))   
        #global_context.message_queue.print("Global expression cache size: %i" % len(global_context.expression_cache))

def index_model(xule_context):
    fact_index = collections.defaultdict(lambda :collections.defaultdict(set))

    #fact_index[('builtin', 'concept')] = xule_context.model.factsByQname
    
    facts_to_index = collections.defaultdict(list)
    if xule_context.model is not None:
        for model_fact in xule_context.model.factsInInstance:
            all_aspects = list()
            all_aspects.append((('builtin', 'concept'),model_fact.qname))
            
            period = model_to_xule_period(model_fact.context, xule_context)
            #fact_index[('builtin', 'period')][period].add(model_fact)
            all_aspects.append((('builtin', 'period'), period))
    #         
    #         if model_fact.isStartEndPeriod:
    #             fact_index[('builtin','period-start')][period[0]].add(model_fact)
    #             fact_index[('builtin','period-end')][period[1]].add(model_fact)
    #         else:
    #             fact_index[('builtin','period-start')][period].add(model_fact)
    #             fact_index[('builtin','period-end')][period].add(model_fact)
    #         #MIGHT NEED TO HANBDLE FOREVER PERIODS
            
            if model_fact.isNumeric:
                unit = model_to_xule_unit(model_fact.unit, xule_context)
                #fact_index[('builtin', 'unit')][unit].add(model_fact)
                all_aspects.append((('builtin', 'unit'), unit))
            
            entity = model_to_xule_entity(model_fact.context, xule_context)
            #fact_index[('builtin', 'entity')][entity].add(model_fact)
            all_aspects.append((('builtin', 'entity'), entity))
            
            for dim, mem in sorted(model_fact.context.qnameDims.items()):
                if mem.isExplicit:
                    #fact_index['explicit_dimension', dim][mem.memberQname].add(model_fact)
                    all_aspects.append((('explicit_dimension', dim), mem.memberQname))
                else:
                    #fact_index['explicit_dimension', dim][mem.typedMember.xValue].add(model_fact)
                    all_aspects.append((('explicit_dimension', dim), mem.typedMember.xValue))
            
            all_aspects = tuple(all_aspects)
            
            if getattr(xule_context.global_context.options, "xule_include_dups", False):
                facts_to_index[all_aspects].append(model_fact)
            else:
                ''' Need to eliminate duplicate facts.
                    Duplicate facts are facts that have the same aspects and same value (taking accuracy into account for numeric facts). If there are duplicates
                    with different values, then the duplicate is not eliminated.
                '''
                if all_aspects in facts_to_index:
                    #there is a fact already
                    found_match = False
                    for position in range(len(facts_to_index[all_aspects])):  
                        saved_fact = facts_to_index[all_aspects][position]
                        if model_fact.isNumeric:
                            saved_value, saved_decimals, cur_value, cur_decimals = get_decimalized_value(saved_fact, model_fact, xule_context)
                            if cur_value == saved_value:
                                found_match = True
                                if cur_decimals > saved_decimals:
                                    facts_to_index[all_aspects][position] = model_fact
                                #otherwise, the saved fact is the better fact to index
                        else:
                            #fact is non numeric
                            if model_fact.xValue == saved_fact.xValue:
                                found_match = True
        
                    if not found_match:
                        #this is a duplicate with a different value
                        facts_to_index[all_aspects].append(model_fact)
                else:
                    #First time adding fact
                    facts_to_index[all_aspects].append(model_fact)
        
        #add the facts to the fact index.        
        for all_aspects, facts in facts_to_index.items():
            for model_fact in facts:
                for aspect in all_aspects:
                    #aspect[0] is the aspect(dimension) name. aspect[1] is the aspect(dimension) value
                    fact_index[aspect[0]][aspect[1]].add(model_fact)
                for property in index_properties(model_fact):
                    fact_index[property[0]][property[1]].add(model_fact)
            
        #get all the facts
        all_facts = {fact for facts in facts_to_index.values() for fact in facts}
        #for each aspect add a set of facts that don't have that aspect with a key value of None
        for aspect_key in fact_index:
            fact_index[aspect_key][None] = all_facts - set(it.chain.from_iterable(fact_index[aspect_key].values()))
        #save the list of all facts. 
        fact_index['all'] = all_facts
    
    return fact_index

def index_properties(model_fact):
    return index_concept_properites(model_fact) + index_period_properties(model_fact) + index_entity_properties(model_fact)

def index_concept_properites(model_fact):
    """Gather the concept properties for the fact index"""
    props = list()
    
    props.append((('property', 'concept', 'period-type'), model_fact.concept.periodType))
    if model_fact.concept.balance is not None:
        props.append((('property', 'concept', 'balance'), model_fact.concept.balance))
    props.append((('property', 'concept', 'data-type'), model_fact.concept.typeQname))
    props.append((('property', 'concept', 'base-type'), model_fact.concept.baseXbrliTypeQname))
    props.append((('property', 'concept', 'is-monetary'), model_fact.concept.isMonetary))
    props.append((('property', 'concept', 'is-numeric'), model_fact.concept.isNumeric))
    props.append((('property', 'concept', 'substitution'), model_fact.concept.substitutionGroupQname))
    props.append((('property', 'concept', 'namespace-uri'), model_fact.concept.qname.namespaceURI))
    props.append((('property', 'concept', 'local-part'), model_fact.concept.qname.localName))
    props.append((('property', 'concept', 'is-abstract'), model_fact.concept.isAbstract))
    for attribute in model_fact.concept.elementAttributesTuple:
        # attribute[0] is the attribute name. For qnames this will be in clarknotation
        # attribute[1] is the attribute value
        if attribute[0] not in ('name', 'substitutionGroup', 'type', '{http://www.xbrl.org/2003/instance}balance', '{http://www.xbrl.org/2003/instance}periodType'):
            props.append((('property', 'concept', 'attribute', qname(attribute[0])), attribute[1]))
    
    return props

def index_period_properties(model_fact):
    """Gather the period properties for the fact index"""
    props = list()
    
    if model_fact.context.isStartEndPeriod:
        props.append((('property', 'period', 'start'), model_fact.context.startDatetime))
        props.append((('property', 'period', 'end'), model_fact.context.endDatetime - datetime.timedelta(days=1)))
        props.append((('property', 'period', 'days'), (model_fact.context.endDatetime - model_fact.context.startDatetime).days))
    elif model_fact.context.isInstantPeriod:
        props.append((('property', 'period', 'start'), model_fact.context.endDatetime - datetime.timedelta(days=1)))
        props.append((('property', 'period', 'end'), model_fact.context.endDatetime - datetime.timedelta(days=1)))
        props.append((('property', 'period', 'days'), 0))
        
    '''NEED TO ADD INDEXES FOR FISCAL PERIODS'''
    return props   

def index_entity_properties(model_fact):
    """Gather the entity properties for the fact index"""
    props = list()
    
    props.append((('property', 'entity', 'scheme'), model_fact.context.entityIdentifier[0])) # entityIdentifier[0] is the scheme
    props.append((('property', 'entity', 'id'), model_fact.context.entityIdentifier[1])) # entityIdentifer[1] is the id

    return props

def get_decimalized_value(fact_a, fact_b, xule_context):
    """Adjust 2 fact values based on accuracy.
    
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

def get_decimals(fact, xule_context):
    """Return the decimals of a fact as a number.
    
    Arguments:
            fact (ModelFact): A fact
            xule_context (XuleRuleContext): Processing context
    """
    if fact.decimals is None:
        return float('inf')
    
    if fact.decimals.strip() == 'INF':
        return float('inf')
    else:
        try:
            return int(fact.decimals)
        except ValueError:
            raise XuleProcessingError(_("%s Fact contains invalid decimal value of %s" % (fact.qname, fact.decimals)), xule_context)
        
def evaluate(rule_part, xule_context, is_values=False, trace_dependent=False, override_table_id=None):
    """General evaluator for an expression.
    
    This evaluator determines the type of expressions and calls the appropriate evaluator. It also manages the cache for iterable expressions.
    
    Arguments:
        rule_part (dictionary): Expression from the rule AST
        xule_context (XuleRuleContext): Processing context
        is_values (boolean): Used if this is being called from a values expression
        trace_dependent (boolean):
        override_table_id (int): 
    """
    #print("evaluate: ", rule_part['exprName'], rule_part['node_id'])    
    try:
        # Setup trace information.
        if getattr(xule_context.global_context.options, "xule_trace", False) or getattr(xule_context.global_context.options, "xule_trace_count", False):    
            trace_is_dependent = "D" if trace_dependent else " "
            trace_source = "U"
            trace_written = False
        if getattr(xule_context.global_context.options, "xule_trace_count", False):
            if rule_part['node_id'] not in xule_context.expression_trace:
                xule_context.expression_trace[rule_part['node_id']] = {'iterations': 1, # total 
                                                                    'iterations-t': datetime.timedelta(0),
                                                                    'U': 0, # unknown iterations - should always be none
                                                                    'U-t': datetime.timedelta(0),
                                                                    'E': 0, # evaluated iterables 
                                                                    'E-t': datetime.timedelta(0),                                                                    
                                                                    'c': 0, # from cache
                                                                    'c-t': datetime.timedelta(0),
                                                                    'T': 0, # from table
                                                                    'T-t': datetime.timedelta(0),
                                                                    'e': 0, # evaluate non iterable
                                                                    'e-t': datetime.timedelta(0),
                                                                    'R': 0, # re-evaluate
                                                                    'R-t': datetime.timedelta(0),
                                                                    'r': 0, # re-evaluate non iterable
                                                                    'r-t': datetime.timedelta(0),
                                                                    'isE': 0, # iteration stop on evaluation of iterable
                                                                    'isE-t': datetime.timedelta(0),
                                                                    'ise': 0, # iteration stop on evaluate of non iterable
                                                                    'ise-t': datetime.timedelta(0),
                                                                    'isu': 0, # iteration stop on unbound during post value processing
                                                                    'isu-t': datetime.timedelta(0),
                                                                    'ex': 0, # exception during iteration evaluation
                                                                    'ex-t': datetime.timedelta(0),                                                                    
                                                                    'name': rule_part['exprName']
                                                                    }
            else:
                xule_context.expression_trace[rule_part['node_id']]['iterations'] += 1
            expression_trace_start = datetime.datetime.today()            
            
        processing_id = xule_context.get_processing_id(rule_part['node_id'])
        rule_part_name = rule_part['exprName']
        #trace
        if getattr(xule_context.global_context.options, "xule_trace", False):
            xule_context.trace_level += 1
             
            trace = "  " * xule_context.trace_level
            trace += rule_part_name + " " + str(processing_id) #+ " " + str(rule_part)
            print(">",trace_is_dependent, " ", processing_id, trace.replace("\n", " "))
    
        if ('is_iterable' in rule_part):
            #is_iterable is always true if it is present, so done't need to check the actual value 
            xule_context.used_expressions.add(processing_id)
              
            if 'is_dependent' in rule_part:
                is_dependent = rule_part['is_dependent']
    
                value = xule_context.iteration_table.current_value(processing_id, xule_context)
                if value is None: 
                    #Will evaluate or get from cache.   
                    values = None       
                    if is_dependent:
                        xule_context.iteration_table.current_table.make_dependent()
                    try:   
                        if getattr(xule_context.global_context.options, "xule_no_cache", False):                 
                        #if xule_context.global_context.no_cache:
                            values = None
                        else:
                            if (rule_part.get('table_id') != xule_context.iteration_table.main_table_id or
                                is_dependent):     
                                local_cache_key = get_local_cache_key(rule_part, xule_context) 
                                if local_cache_key is not None:                                                                                  
                                    values = xule_context.local_cache.get(local_cache_key)
                                else:
                                    values = None
                        if values is None:                        
                            values = EVALUATOR[rule_part_name](rule_part, xule_context)
                            trace_source = "E" 
                            if not getattr(xule_context.global_context.options, "xule_no_cache", False):
                            #if not xule_context.global_context.no_cache:
                                if (rule_part.get('table_id') != xule_context.iteration_table.main_table_id or
                                is_dependent):
                                    local_cache_key =  get_local_cache_key(rule_part, xule_context) 
                                    if local_cache_key is not None:  
                                        #print("caching", rule_part['node_id'], [(x[0], x[1].format_value()[:10]) for x in local_cache_key[1]], len(values.values))
                                        xule_context.local_cache[local_cache_key] = values 
                        else:
                            #print("using cache", rule_part['node_id'], [x[0] for x in local_cache_key[1]])
                            trace_source = "c"
                    except XuleIterationStop:
                        if getattr(xule_context.global_context.options, "xule_trace", False):
                        #if xule_context.show_trace: 
                            xule_context.trace_level -= 1
                        if getattr(xule_context.global_context.options, "xule_trace_count", False):
                        #if xule_context.show_trace_count:
                            xule_context.expression_trace[rule_part['node_id']]['iterations-t'] += datetime.datetime.today() - expression_trace_start
                            xule_context.expression_trace[rule_part['node_id']]['isE-t'] += datetime.datetime.today() - expression_trace_start
                            xule_context.expression_trace[rule_part['node_id']]['isE'] += 1
                            trace_written = True
                        raise
                    except XuleReEvaluate:
                        trace_source = 'R'
                        raise
#                     except Exception as e:
#                         import traceback
#                         import sys
#                         print("Exception 3", "iteration", ii, "rule id", rule_part['node_id'], rule_part_name, sys.exc_info()[0])
#                         traceback.print_tb(sys.exc_info()[2], file=sys.stdout)
#                         raise                                        
                    else:
                        #add - add values to expression cache
                        xule_context.iteration_table.add_column(rule_part, override_table_id or rule_part['table_id'], processing_id, values, xule_context)
                        value = xule_context.iteration_table.current_value(processing_id, xule_context)           
                else:
                    trace_source = "T"
            else:
                raise XuleProcessingError(_("Internal error: Found iterable (%s) that does not have a dependency flag." % rule_part_name),xule_context)
        else: # is_iterable
            trace_source = "e"
            # Check the cache - only if the expression does have something in it that produces multiple results and its not a varRef.
            if getattr(xule_context.global_context.options, "xule_no_cache", False): 
                local_cache_key = None
            else: 
                if rule_part['number'] == 'single' and rule_part['exprName'] not in ('varRef', 'tagRef'):
                    local_cache_key = get_local_cache_key(rule_part, xule_context)
                else:
                    local_cache_key = None
            if local_cache_key is None:
                value = None
            else:
                cache_value = xule_context.local_cache.get(local_cache_key)
                value = cache_value.clone() if cache_value is not None else None
                if value is not None and value.tags is not None:
                    new_tags = value.tags.copy()
                    new_tags.update(xule_context.tags)
                    value.tags = new_tags                 
            if value is None:
                try:
                    value = EVALUATOR[rule_part_name](rule_part, xule_context)
                except XuleIterationStop:
                    if getattr(xule_context.global_context.options, "xule_trace", False):
                    #if xule_context.show_trace: 
                        xule_context.trace_level -= 1
                    if getattr(xule_context.global_context.options, "xule_trace_count", False):
                    #if xule_context.show_trace_count:
                        xule_context.expression_trace[rule_part['node_id']]['iterations-t'] += datetime.datetime.today() - expression_trace_start
                        xule_context.expression_trace[rule_part['node_id']]['ise-t'] += datetime.datetime.today() - expression_trace_start
                        xule_context.expression_trace[rule_part['node_id']]['ise'] += 1
                        trace_written = True
                    raise
                except XuleReEvaluate as e:
                    trace_source = 'r'
                    raise
                
                if not getattr(xule_context.global_context.options, "xule_no_cache", False):  
                    if local_cache_key is not None:
                        xule_context.local_cache[local_cache_key] = value
    
        #If the look_for_alignment flag is set, check if there is now alignment after adding the column. This is used in 'where' clause processing.
        #if xule_context.look_for_alignment and xule_context.iteration_table.any_alignment is not None:
        if (xule_context.look_for_alignment and 
            #rule_part.has_alignment and
            value.aligned_result_only and
            rule_part.get('table_id') in xule_context.where_table_ids and
            rule_part['node_id'] in xule_context.where_dependent_iterables):
                raise XuleReEvaluate(xule_context.iteration_table.any_alignment)
    
        if getattr(xule_context.global_context.options, "xule_trace", False):
        #if xule_context.show_trace:
            sugar = sugar_trace(value, rule_part, xule_context)
            trace_info = (xule_context.trace_level, rule_part_name, sugar, value)
            xule_context.trace.appendleft(trace_info)
            
            post_trace = "  " * xule_context.trace_level
            post_trace += ("NONE" if value is None else value.format_value()) + format_trace_info(trace_info[1], trace_info[2], {}, xule_context)    
            print("<", trace_is_dependent, trace_source, processing_id, post_trace.replace("\n", " "))
        
            xule_context.trace_level -= 1
        try:
            value = post_evaluate_value(rule_part, value, xule_context)
#         except XuleIterationStop:
#             raise
#         except Exception as e:
#             import traceback
#             import sys
#             print("Exception 2", "iteation", ii, "rule id", rule_part['node_id'], rule_part_name, sys.exc_info()[0])
#             traceback.print_tb(sys.exc_info()[2], file=sys.stdout)
#             raise
        finally:
            if getattr(xule_context.global_context.options, "xule_trace_count", False):
            #if xule_context.show_trace_count:
                xule_context.expression_trace[rule_part['node_id']][trace_source] += 1
                xule_context.expression_trace[rule_part['node_id']]['iterations-t'] += (datetime.datetime.today() - expression_trace_start)
                xule_context.expression_trace[rule_part['node_id']][trace_source + '-t'] += (datetime.datetime.today() - expression_trace_start)
                trace_written = True
    finally:
        if getattr(xule_context.global_context.options, "xule_trace_count", False) and not trace_written:
        #if xule_context.show_trace_count and not trace_written:
#            print("trace not written", "iteration", ii, "rule id", rule_part['node_id'], trace_source)
            xule_context.expression_trace[rule_part['node_id']]['iterations-t'] += datetime.datetime.today() - expression_trace_start
            xule_context.expression_trace[rule_part['node_id']][trace_source + '-t'] += (datetime.datetime.today() - expression_trace_start)
            xule_context.expression_trace[rule_part['node_id']][trace_source] += 1  
            trace_written = True      
    return value

def post_evaluate_value(rule_part, value, xule_context):

    if value is None:
        raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
        #value = XuleValue(xule_context, None, 'unbound')

    if value.fact is not None:
        #xule_context.facts.append(value.fact)  
        xule_context.facts[value.fact] = None      
    if value.facts is not None:
#         print("before", len(xule_context.facts), len(set(xule_context.facts)))
#         xule_context.facts.extend(value.facts)
#         print("after", len(xule_context.facts), len(set(xule_context.facts)))
        xule_context.facts.update(value.facts)
    if value.tags is not None:
#         # Need to make sure that the current version of the tags stay and the update only adds new tags from the value.
#         new_tags = value.tags.copy()
#         new_tags.update(xule_context.tags)
#         xule_context.tags = new_tags 
         xule_context.tags.update(value.tags)
    if value.aligned_result_only == True:
        xule_context.aligned_result_only = True
    
#     if value.used_vars is not None:
#         new_keys = value.used_vars.keys() - xule_context.vars.keys() 
#         for new_key in new_keys:
#             xule_context.vars[new_key] = value.used_vars[new_key]
    
    if value.used_expressions is not None:
        #print("add",rule_part['exprName'], rule_part['node_id'], len(xule_context.used_expressions), len(value.used_expressions))
        xule_context.used_expressions.update(value.used_expressions)
    
    if value.type == 'unbound':
        raise XuleIterationStop(value)


    return value

# def get_cache_key(rule_part, dependent_alignment, xule_context):
#     
#     if rule_part['exprName'] in ('constantAssign','forControl'):
#         return None
#     
#     if rule_part['exprName'] == 'functionReference' and len(rule_part.functionArgs) > 0:
#         return None
#     
#     cache_var_key = {}
# 
#     for dep_expr in rule_part.dependent_iterables:
#         if dep_expr['node_id'] != rule_part['node_id']:
#             cache_var_key[dep_expr['node_id']] = evaluate(dep_expr, xule_context)
#     '''
#     This is removed. The cache key is now based on the dependent_iterables instead of dependent vars
# 
#     for var_ref in rule_part.var_refs:
#         #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
#         var_info = xule_context.find_var(var_ref[1], var_ref[0])
#         var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context) 
#         cache_var_key[var_ref[0]] = var_value     
#     '''
#     return (rule_part['node_id'], dependent_alignment, frozenset(cache_var_key.items()))
        
def get_local_cache_key(rule_part, xule_context):
    #processing_id = xule_context.get_processing_id(rule_part['node_id'])
    #value = xule_context.iteration_table.current_value(processing_id, xule_context)
    
    #Don't cache for function refs that are not cacheable
    if (rule_part['exprName'] in ('functionReference', 'macroRef') and rule_part.get('cacheable') != True) or rule_part['exprName'] == 'forBodyExpr':
        return None

    dep_var_index = set()
    for var_ref in rule_part['var_refs']:
        #var_ref tuple: 0 = var declaration id, 1 = var name, 2 = var ref ast, 3 = var type (1=block variable or 'for' variable, 2=constant, 3=function argument, factset variable)
        var_info = xule_context.find_var(var_ref[1], var_ref[0])
        if var_info['type'] == xule_context._VAR_TYPE_CONSTANT:
            #If it is a constant, the var_info will not contain the value. To determine if the constant is used, the used_expressions are checked.
            if xule_context.get_processing_id(var_info['expr']['node_id']) in xule_context.used_expressions:
                const_value = evaluate(var_info['expr'], 
                                                   xule_context, 
                                                   override_table_id=var_ref[2].table_id, 
                                                   is_values='values_expression' in var_ref[2])
                dep_var_index.add((var_info['name'], const_value))
        else:
            if var_ref[0] in xule_context.vars:
                if var_info['calculated']:
                    dep_var_index.add((var_info['name'], var_info['value']))
       
    alignment = xule_context.iteration_table.current_alignment if rule_part['has_alignment'] else None
    
    cache_key = (rule_part['node_id'], frozenset(dep_var_index), alignment)
    return cache_key

def evaluate_assertion(assert_rule, xule_context):
    """Evaluator for an assertion rule.
    """

    # Keep evaluating the rule while there are iterations. This is done in a While True loop so there is always at least one iteration. This is for rules that 
    # do not have iterable expressions in them (i.e. 1 + 2).
    while True:
        xule_context.iter_count += 1
        try:
            xule_value = evaluate(assert_rule['body'], xule_context)
        except XuleIterationStop:
            xule_context.iter_pass_count += 1
            pass
        except:
            xule_context.iter_except_count += 1
            raise
        else:
            # There were no exceptions. Check the results of the rule and create the message.
            
            # Check if the rule expects only aligned values. When a rule has aligned values then the none aligned results are ignored.
            # This prevents a rule like 1 + @Assets from producing a result when there are no Assets in a filing. When this happens, the @Assetss will have 
            # a none aligned unbound value. The plus operation will treat this as 0 and produce a value of 1. However, this value should not result in a message.
            # When a factset is evluated, it trips the aligned_result_only flag. 
            if xule_value.type != 'unbound' and not(xule_context.iteration_table.current_alignment is None and xule_context.aligned_result_only): 

                if xule_value.type != 'bool':
                    raise XuleProcessingError(_("Raise %s did not evaluate to a boolean, found '%s'." % (xule_context.rule_name, xule_value.type)), xule_context)
                      
                # Determine if a message should be sent
                send_message = ((assert_rule['satisfactionType'] == 'satisfied' and xule_value.value == True) or
                                (assert_rule['satisfactionType'] == 'unsatisfied' and xule_value.value == False))
                
                if send_message:
                    xule_context.iter_message_count += 1
                    messages = dict()
                    # Process each of the results in the rule. The Results are the messages that are produced.
                    for rule_result in assert_rule.get('results', list()):
                        #message_context = xule_context.create_message_copy(xule_context.get_processing_id(assert_rule['node_id']))
                        #messages[rule_result['resultName']] = get_message(assert_rule, xule_value, xule_context.iteration_table.current_alignment, message_context)
                        messages[rule_result['resultName']] = result_message(assert_rule, rule_result, xule_value, xule_context)
                    
                    #get severity
                    if 'severity' not in messages:
                        #default severity
                        messages['severity'] = 'error'
                    severity = messages['severity']
                    
                    #message - this is the main message
                    main_message = messages.get('message', 'No message supplied')
                    messages.pop('message', None)
                    
                    full_rule_name = xule_context.rule_name
                    # Handle rule suffix
                    if 'rule-suffix' in messages:
                        full_rule_name += '.' + messages['rule-suffix']                    
                    
                    source_location = get_element_identifier(xule_value, xule_context)
                    filing_url = xule_context.model.modelDocument.uri if xule_context.model is not None else ''
             
                    xule_context.global_context.message_queue.log(severity.upper(),
                                                                  full_rule_name, 
                                                                  main_message,
                                                                  sourceFileLine=[source_location],
                                                                  filing_url=filing_url,
                                                                  **messages)        
                else:
                    xule_context.iter_pass_count += 1
            else:
                xule_context.iter_misaligned_count += 1
                
                
        #xule_context.iteration_table.del_current()
        #if xule_context.iteration_table.is_empty:
        xule_context.iteration_table.next(assert_rule['node_id'])
        if xule_context.iteration_table.is_table_empty(assert_rule['node_id']):
            break
        else:
            xule_context.reset_iteration()

def evaluate_output_rule(output_rule, xule_context):
    """Evaluator for a output rule.
    """
    # Keep evaluating the rule while there are iterations. This is done in a While True loop so there is always at least one iteration. This is for rules that 
    # do not have iterable expressions in them (i.e. 1 + 2).
    while True:
        xule_context.iter_count += 1
        try:
            xule_value = evaluate(output_rule['body'], xule_context)
        except XuleIterationStop:
            xule_context.iter_pass_count += 1
            pass
        except:
            xule_context.iter_except_count += 1
            raise
        else:
            # There were no exceptions. Check the results of the rule and create the message.
            
            # Check if the rule expects only aligned values. When a rule has aligned values then the none aligned results are ignored.
            # This prevents a rule like 1 + @Assets from producing a result when there are no Assets in a filing. When this happens, the @Assetss will have 
            # a none aligned unbound value. The plus operation will treat this as 0 and produce a value of 1. However, this value should not result in a message.
            # When a factset is evluated, it trips the aligned_result_only flag. 
            if xule_value.type != 'unbound' and not(xule_context.iteration_table.current_alignment is None and xule_context.aligned_result_only): 
                # Determine if a message should be sent

                xule_context.iter_message_count += 1
                messages = dict()
                # Process each of the results in the rule. The Results are the messages that are produced.
                for rule_result in output_rule.get('results', list()):
                    #message_context = xule_context.create_message_copy(xule_context.get_processing_id(output_rule['node_id']))
                    messages[rule_result['resultName']] = result_message(output_rule, rule_result, xule_value, xule_context)
                
                #get severity
                if 'severity' not in messages:
                    severity = 'INFO'
                
                #message - this is the main message
                #main_message = messages.get('message', xule_value.format_value())
                #main_message = messages.get('message', process_message("${value} ${context}", xule_value, xule_context))
                main_message = messages.get('message', xule_value.format_value())
                messages.pop('message', None)
                
                full_rule_name = xule_context.rule_name
                # Handle rule suffix
                if 'rule-suffix' in messages:
                    full_rule_name += '.' + messages['rule-suffix']
                
                source_location = get_element_identifier(xule_value, xule_context)
                filing_url = xule_context.model.modelDocument.uri if xule_context.model is not None else ''
         
                xule_context.global_context.message_queue.log(severity.upper(),
                                                              full_rule_name, 
                                                              main_message,
                                                              sourceFileLine=[source_location],
                                                              filing_url=filing_url,
                                                              **messages)        
            else:
                xule_context.iter_misaligned_count += 1
                
                
        #xule_context.iteration_table.del_current()
        #if xule_context.iteration_table.is_empty:
        xule_context.iteration_table.next(output_rule['node_id'])
        if xule_context.iteration_table.is_table_empty(output_rule['node_id']):
            break
        else:
            xule_context.reset_iteration()

def evaluate_bool_literal(literal, xule_context):
    if literal['value'] == "true":
        return XuleValue(xule_context, True, 'bool')
    elif literal['value'] == "false":
        return XuleValue(xule_context, False, 'bool')
    else:
        raise XuleProcessingError(_("Invalid boolean literal found: %s" % literal.value), xule_context)

def evaluate_string_literal(literal, xule_context):
    """Evaluate a string literal
    
    A string can consist of a string of characters, escaped characters or an expression to evaluate. This is handled as a list of 
    string expressions (baseString, escape, and an expression)."""
    
    result_string = ''
    
    for string_item in literal['stringList']:
        if string_item['exprName'] == 'baseString':
            result_string += string_item['value']
        elif string_item['exprName'] == 'escape':
            if string_item['value'] == 'n':
               result_string += '\n'
            elif string_item['value'] == 't':
                result_string += '\t'
            else:
                result_string += string_item['value']
        else:
            # This is an expression.
            expr_value = evaluate(string_item, xule_context)
            result_string += expr_value.format_value()
        
    return XuleValue(xule_context, result_string, 'string')
    
#     string_literal = literal['value']
#     
#     string_literal = string_literal.replace('\\n', '\n')
#     string_literal = string_literal.replace('\\t', '\t')
#     string_literal = string_literal.replace('\\"', '"')
#     string_literal = string_literal.replace("\\'", "'")
#     string_literal = string_literal.replace('\\\\', '\\')
# 
#     return XuleValue(xule_context, string_literal, 'string')

def evaluate_int_literal(literal, xule_context):
    return XuleValue(xule_context, int(literal['value']), 'int')

def evaluate_float_literal(literal, xule_context):
    return XuleValue(xule_context, float(literal['value']), 'float')

def evaluate_void_literal(literal, xule_context):
    ''' This could be 'none' or 'skip'.
    '''
    return XuleValue(xule_context, None, 'none' if literal['value'] == 'none' else 'unbound')

def evaluate_qname_literal(literal, xule_context):
    prefix = literal['prefix']
    return XuleValue(xule_context, QName(prefix if prefix != '*' else None, literal['namespace_uri'], literal['localName']), 'qname')

def evaluate_severity(severity_expr, xule_context):
    return XuleValue(xule_context, severity_expr['value'], 'severity')

def evaluate_string_keyword(expr, xule_context):
    return XuleValue(xule_context, expr['value'], 'string')

def evaluate_tagged(tagged_expr, xule_context):
    try:
        tagged_value = evaluate(tagged_expr['expr'], xule_context)
    except XuleIterationStop as xis:
        xule_context.tags[tagged_expr['tagName']] = xis.stop_value.tag          
        raise
    else:
        #xule_context.tags[tagged_expr.tagName] = tagged_value
        if tagged_value.tags is None:
            tagged_value.tags = {tagged_expr['tagName']: tagged_value}
        else:
            tagged_value.tags[tagged_expr['tagName']] = tagged_value
        
    return tagged_value

def tag_default_for_factset(expr, xule_context):
    """Get the value of the concept aspect for tagging the default None fact of a factset
    """

    for aspect_filter in expr.get('aspectFilters', list()):
        if aspect_filter.get('aspectName') == 'concept':
            if 'aspectOperator' in aspect_filter:
                if aspect_filter['aspectOperator'] == '=':
                    if 'wildcard' in aspect_filter:
                        return 'unknown'
                    else:
                        aspect_member_value = evaluate(aspect_filter['aspectExpr'], xule_context)
                        return str(aspect_member_value)
                elif aspect_filter['aspectOperator'] == 'in':
                    aspect_member_set = evaluate(aspect_filter['aspectExpr'], xule_context)
                    if len(aspect_member_set.value) > 0:
                        concepts = []
                        for aspect_member_value in aspect_member_set.value:
                            if aspect_member_value.type == 'qname':
                                concepts.append(str(aspect_member_value.value))
                            elif aspect_member_value.type == 'concept':
                                concepts.append(str(aspect_member_value.value.qname))
                        if len(concepts) == 1:
                            return str(concepts[0])
                        else:
                            return 'one of (' + ', '.join(concepts) + ')'
                    else:
                        return 'unknown'
                else:
                    return 'unknown'
            else:
                # There is no aspectoperator
                return 'unknown'
            
        elif 'aspectDimensionName' in aspect_filter:
            #check if this is dimension concept. If not, then this is the default concept aspect
            aspect_dimension_qname = evaluate(aspect_filter['aspectDimensionName'], xule_context)
            aspect_filter_model_concept = xule_context.model.qnameConcepts.get(aspect_dimension_qname.value)
            if aspect_filter_model_concept is None:
                raise XuleProcessingError(_("Error while processing factset aspect. Concept %s not found." % aspect_filter_qname.value.clarkNotation), xule_context)            
            if not aspect_filter_model_concept.isDimensionItem:
                #This is the default concept aspect where the qname is the aspect member.
                return str(aspect_dimension_qname.value)
        
    # Doesn't have a concept aspect at all 
    return 'unknown'


def evaluate_block(block_expr, xule_context):
    for var_assignment in block_expr['varDeclarations']:
    #for var_assignment in var_assignments:
        var_info = xule_context.add_var(var_assignment['varName'],
                             var_assignment['node_id'],
                             True, #tagged - all variables are tagged
                             var_assignment['body'])
        calc_var(var_info, None, xule_context)
    
    return evaluate(block_expr['expr'], xule_context)

def evaluate_var_ref(var_ref, xule_context):
    #print(var_ref['node_id'], var_ref.varName)
    var_info = xule_context.find_var(var_ref['varName'], var_ref['var_declaration'])
    #xule_context.used_vars.append(var_ref.var_declaration)
    
    try:
        var_value = calc_var(var_info, var_ref, xule_context)
    except XuleIterationStop as xis:
        var_value = xis.stop_value
        raise
 
    return var_value 

def calc_var(var_info, const_ref, xule_context):
    if var_info['type'] == xule_context._VAR_TYPE_ARG:
        var_value = var_info['value']
    elif var_info['type'] == xule_context._VAR_TYPE_VAR:   
        if var_info['calculated'] == False:
            try:
                saved_aligned_result_only = xule_context.aligned_result_only
                saved_used_expressions = xule_context.used_expressions
                xule_context.aligned_result_only = False
                xule_context.used_expressions = set()
                try:
                    var_info['value'] = evaluate(var_info['expr'], xule_context)
                    var_info['value'].aligned_result_only = xule_context.aligned_result_only
                    var_info['value'].used_expressions = xule_context.used_expressions
                    var_info['calculated'] = True
                except XuleIterationStop as xis:
                    var_info['value'] = xis.stop_value
                    var_info['value'].aligned_result_only = xule_context.aligned_result_only
                    var_info['value'].used_expressions = xule_context.used_expressions
                    var_info['calculated'] = True
                    #raise
            finally:
                xule_context.aligned_result_only = xule_context.aligned_result_only or saved_aligned_result_only
                xule_context.used_expressions = saved_used_expressions | xule_context.used_expressions

        var_value = var_info['value']
    elif var_info['type'] == xule_context._VAR_TYPE_CONSTANT:
        #We should only end up here the first time the constant is referenced for the iteration.
        #The var_info is really the constant info from the global context
        var_value = evaluate(var_info['expr'], xule_context, override_table_id=const_ref['table_id'], is_values='values_expression' in const_ref)
    else:
        raise XuleProcessingError(_("Internal error: unkown variable type '%s'" % var_info['type']), xule_context) 
    
    var_value = var_value.clone()
    #if var_info['tagged']:
    xule_context.tags[var_info['name']] = var_value

    return var_value

def calc_constant(const_info, const_context):
    const_context.iteration_table.add_table(const_info['expr']['node_id'], const_context.get_processing_id(const_info['expr']['node_id']))
    
    const_values = XuleValueSet()
    
    while True:
        const_context.aligned_result_only = False
        const_context.used_expressions = set()
        try:
            const_value = evaluate(const_info['expr']['body'], const_context)
        except XuleIterationStop as xis:
            const_value = xis.stop_value #XuleValue(const_context, None, 'unbound')
        
        const_value.facts = const_context.facts
        const_value.tags = const_context.tags
        const_value.aligned_result_only = const_context.aligned_result_only
        #const_value.used_expressions = const_context.used_expressions
        try:
            const_value.alignment = const_context.iteration_table.current_table.current_alignment
        except AttributeError:
            #This happens if there isn't a current table because it was never created.
            pass
        const_values.append(const_value)
        
        #const_context.iteration_table.del_current()
        if not const_context.iteration_table.is_empty:
            const_context.iteration_table.next(const_context.iteration_table.current_table.table_id)
        #if const_context.iteration_table.is_empty:
        if const_context.iteration_table.is_table_empty(const_info['expr']['node_id']):
            break
#         else:
#             const_context.reset_iteration()
        
    #reset the aligned only results.
    const_info['expr']['aligned_only_results'] = const_context.aligned_result_only
    
    const_info['value'] = const_values
    const_info['calculated'] = True

def evaluate_constant_assign(const_assign, xule_context):
    const_info = xule_context.find_var(const_assign['constantName'], const_assign['node_id'], constant_only=True)
    if const_info is None:
        raise XuleProcessingError(_("Constant '%s' not found" % const_assign['constantName']), xule_context)
    
    if not const_info['calculated']:
        const_context = XuleRuleContext(xule_context.global_context, xule_context.rule_name + ":" + const_info['name'], xule_context.cat_file_num)
        calc_constant(const_info, const_context)        
    
    if 'is_iterable' in const_assign:
        #return the entire value set
        return const_info['value']
    else:
        #retrieve the single value
        return const_info['value'].values[None][0]

def process_precalc_constants(global_context):
    global_context.message_queue.logging("Precalcing non-instance constants")
    for constant_name, cat_constant in global_context.rule_set.catalog['constants'].items():
        if ('unused' not in cat_constant and
            not cat_constant['dependencies']['instance']):
            
            const_context = XuleRuleContext(global_context, constant_name, cat_constant['file'])
            const_info = const_context.find_var(constant_name, cat_constant['node_id'])
            if not const_info['calculated']:
                calc_constant(const_info, const_context)

# def process_precalc_preconditions(global_context):
#     global_context.message_queue.logging("Precalcing non-instance preconditions")
#     for precon_name, cat_precon in global_context.rule_set.catalog['preconditions'].items():
#         if ('unused' not in cat_precon and
#             not cat_precon['dependencies']['instance']
#             and cat_precon['node_id'] not in global_context.preconditions):
#             
#             calc_precondition(precon_name, global_context)
            
# def check_precondition(preconditionRef, global_context):
#     '''When checking multiple preconditions, all must be true.'''
#     for precon_name in preconditionRef.preconditionNames:
#         precon_node_id = global_context.catalog['preconditions'][precon_name]['node_id']
#         if precon_node_id not in global_context.preconditions:
#             calc_precondition(precon_name, global_context)
#         
#         if getattr(global_context.options, "xule_debug", False):
#         #if global_context.show_debug:
#             global_context.message_queue.print("Precondition {} {}".format(precon_name, global_context.preconditions[precon_node_id]))
#             
#         if not global_context.preconditions[precon_node_id]:
#             return False
#     
#     #No false precondition was found
#     return True

def calc_precondition(precon_name, global_context):
    '''A precondition is true if at least one evaluation returns true'''

    cat_precon = global_context.catalog['preconditions'][precon_name]
    precon_context = XuleRuleContext(global_context, precon_name, cat_precon['file'])
    
    precon_rule_part = precon_context.global_context.rule_set.getItem(cat_precon)
    
    precon_table = precon_context.iteration_table.add_table(precon_rule_part['node_id'], precon_context.get_processing_id(precon_rule_part['node_id']))
    
    while True:
        precon_context.aligned_result_only = False
        precon_context.used_expressions = set()
        try:
            precon_value = evaluate(precon_rule_part.expr, precon_context)
        except XuleIterationStop:
            continue
        if precon_value.type != 'bool':
            raise XuleProcessingError(_("Precondition {} did not evaluate to a boolean, got {} instead.".format(precon_rule_part.preconditionName, precon_value.type)), precon_context)
        
        if precon_value.value:
            precon_context.global_context.preconditions[precon_rule_part['node_id']] = True
            return

        precon_table.next(precon_table.table_id)
        if precon_table.is_empty:
            break
        
    #if we get here, then there was not an evaluation that return true, the precondition is false
    precon_context.global_context.preconditions[precon_rule_part['node_id']] = False
               
# def pre_calc_expressions(global_context):
#     for node_id in global_context.rule_set.catalog['pre_calc_expressions']:
#         if node_id not in global_context.expression_cache:
#             expr = global_context.rule_set.getNodeById(node_id)
#             global_context.expression_cache[node_id] = calc_expression(expr, global_context)
# 
# def calc_expression(expr, global_context):
#     #print("calcing", expr['node_id'], expr['exprName'])
#     expr_context = XuleRuleContext(global_context)
#     expr_values = XuleValueSet()
#     
#     while True:
#         expr_context.aligned_result_only = False
#         try:
#             expr_value = evaluate(expr, expr_context)
#         except XuleIterationStop as xis:
#             expr_value = xis.stop_value #XuleValue(const_context, None, 'unbound')
#         
#         expr_value.facts = expr_context.facts
#         expr_value.tags = expr_context.tags
#         expr_value.aligned_result_only = expr_context.aligned_result_only
#         expr_value.alignment = expr_context.iteration_table.current_table.current_alignment
#         expr_values.append(expr_value)
# 
#         expr_context.iteration_table.del_current()
#         if expr_context.iteration_table.is_empty:
#             break
#         
#     if expr.number == 'multi':
#         return expr_values
#     else:
#         return expr_values.values[None][0]  
  
def evaluate_print(print_expr, xule_context):
    print_value = evaluate(print_expr.printValue[0], xule_context)
    xule_context.global_context.message_queue.log("INFO", "xule:print", "%s: %s" % (print_value.type, print_value.format_value()))
    pass_through_value = evaluate(print_expr.passThroughExpr[0], xule_context)
    return pass_through_value

def evaluate_if(if_expr, xule_context):
    if_thens = []
    if_thens.append((if_expr['condition'], if_expr['thenExpr']))

    for else_if in if_expr.get('elseIfExprs', []):
        if_thens.append((else_if['condition'], else_if['thenExpr']))
    
    for if_then in if_thens:
        condition_value = evaluate(if_then[0], xule_context)
        if condition_value.type in ('unbound', 'none'):
            return XuleValue(xule_context, None, 'unbound')
        elif condition_value.type != 'bool':
            raise XuleProcessingError(_("If condition is not a boolean, found '%s'" % condition_value.type), xule_context) 
        else:
            if condition_value.value:
                return evaluate(if_then[1], xule_context)
    
    #This is only hit if none of the if conditions passed
    return evaluate(if_expr['elseExpr'], xule_context)

def evaluate_for(for_expr, xule_context):
    for_values = XuleValueSet()
    
    saved_used_expressions = xule_context.used_expressions
    xule_context.used_expressions = set()
    try: 
        for_loop_collection = evaluate(for_expr['forLoopExpr'], xule_context)
    finally:
        used_expressions = xule_context.used_expressions
        xule_context.used_expressions = saved_used_expressions | used_expressions

    for for_loop_var in for_loop_collection.value:
        if for_loop_var.used_expressions is None:
            for_loop_var.used_expressions = used_expressions
        else:
            for_loop_var.used_expressions.update(used_expressions)
        xule_context.add_arg(for_expr['forVar'],
                              for_expr['forLoopExpr']['node_id'],
                              True, #tagged - all variables are automatically tagged
                              for_loop_var,
                              'single')

        try:
            body_values = evaluate_for_body_detail(for_expr['forBodyExpr'], 
                                                   for_expr['node_id'], 
                                                   for_loop_var, 
                                                   for_expr['forVar'], #tag name 
                                                   xule_context)
        finally:
            xule_context.del_arg(for_expr['forVar'], for_expr['forLoopExpr']['node_id'])
 
        if for_loop_var.alignment is None:
            #add all
            for body_value in body_values.values.values():
                for_values.append(body_value)
        else:
            if for_loop_var.alignment in body_values.values:
                #take the aligned values
                for body_value in body_values.values[for_loop_var.alignment]:
                    for_values.append(body_value)
            else:
                #take only none aligned values and add alignment
                for body_value in body_values.values[None]:
                    body_value.alignment = for_loop_var.alignment
                    for_values.append(body_value)
      
    return for_values

def evaluate_for_body_detail(body_expr, table_id, for_loop_var, for_loop_tag, xule_context):
    body_values = XuleValueSet()
  
    aligned_result_only = False      
    save_aligned_result_only = xule_context.aligned_result_only
    save_used_expressions = xule_context.used_expressions
    #for_body_table = xule_context.iteration_table.add_table(xule_context.get_processing_id(body_expr['node_id']), is_aggregation=True)
    
    for_body_table = xule_context.iteration_table.add_table(table_id, xule_context.get_processing_id(table_id), is_aggregation=True)
    for_body_table.dependent_alignment = for_loop_var.alignment
    
    #add the loop control to the table
    #xule_context.iteration_table.add_column(rule_part, for_body_table.table_id, processing_id, values, xule_context)    
    
    try:  
        while True:
            xule_context.aligned_result_only = False
            xule_context.used_expressions = set()
            xule_context.tags[for_loop_tag] = for_loop_var
            body_value = XuleValue(xule_context, None, 'unbound')
            try:
                body_value = evaluate(body_expr, xule_context)
            except XuleIterationStop:
                pass

            aligned_result_only = aligned_result_only or xule_context.aligned_result_only
            body_value.alignment = for_body_table.current_alignment #xule_context.iteration_table.dependent_alignment or xule_context.iteration_table.current_table.current_alignment
            body_value.aligned_result_only = aligned_result_only
            body_value.facts = xule_context.iteration_table.facts
            body_value.tags = xule_context.iteration_table.tags
            #print("for", body_expr['exprName'], body_expr['node_id'], len(xule_context.used_expressions), len(body_value.used_expressions))
            body_value.used_expressions = xule_context.used_expressions
            body_values.append(body_value)

            xule_context.iteration_table.next(for_body_table.table_id)
            if for_body_table.is_empty:
                break
    finally:
        xule_context.aligned_result_only = save_aligned_result_only
        xule_context.used_expressions = save_used_expressions
        xule_context.iteration_table.del_table(for_body_table.table_id)
    return body_values


    
def evaluate_unary(unary_expr, xule_context):
    initial_value = evaluate(unary_expr['expr'], xule_context)
    
    if initial_value.type in ('unbound', 'none'):
        return initial_value
    
    if initial_value.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("Unary operator requires a numeric operand, found '%s'" % initial_value.type), xule_context)
    
    if unary_expr['op'] == '-':
        return XuleValue(xule_context, initial_value.value * -1, initial_value.type)
    else:
        return initial_value

def evaluate_mult(mult_expr, xule_context):
    left = evaluate(mult_expr['leftExpr'], xule_context)
    
    for right_side in mult_expr['rights']:
        operator = right_side['op']
        right = evaluate(right_side['rightExpr'], xule_context)

        if left.type in ('unbound', 'none') or right.type in ('unbound', 'none'):
            left = XuleValue(xule_context, None, 'unbound')
        else:
#             if left.type == 'unit' and right.type == 'unit':
#                 #units have special handling
#                 if operator == '*':
#                     left = XuleValue(xule_context, unit_multiply(left.value, right.value), 'unit')
#                 else:
#                     left = XuleValue(xule_context, unit_divide(left.value, right.value), 'unit')
#             else:
                #at this point there should only be numerics.
                if left.type not in ('int', 'float', 'decimal'):
                    raise XuleProcessingError(_("The left operand of '%s' is not numeric, found '%s'" % (operator, left.type)), xule_context)
                if right.type not in ('int', 'float', 'decimal'):
                    raise XuleProcessingError(_("The right operand of '%s' is not numeric, found '%s'" % (operator, right.type)), xule_context)
                
                combined_type, left_compute_value, right_compute_value = combine_xule_types(left, right, xule_context)
                '''NEED TO HANDLE CHNAGES IN UNIT ALIGNMENT'''
                if operator == '*':
                    left = XuleValue(xule_context, left_compute_value * right_compute_value, combined_type)
                else:
                    if right_compute_value == 0:
                        raise XuleProcessingError(_("Divide by zero error."), xule_context) 
                    left = XuleValue(xule_context, left_compute_value / right_compute_value, combined_type)
    return left

def evaluate_intersect(inter_expr, xule_context):
    left = evaluate(inter_expr['leftExpr'], xule_context)
    for right_side in inter_expr['rights']:
        right = evaluate(right_side['rightExpr'], xule_context)
        if left.type in ('unbound', 'none') or right.type in ('unbound', 'none'):
            left = XuleValue(xule_context, None, 'unbound')
        if left.type != 'set':
            raise XuleProcessingError(_("Intersection can only operatate on sets. The left side is a '{}'.".format(left.type)), xule_context)
        if right.type != 'set':
            raise XuleProcessingError(_("Intersection can only operatate on sets. The right side is a '{}'.".format(right.type)), xule_context)
    
        left = XuleUtility.intersect_sets(xule_context, left, right)
    
    return left

def evaluate_symetric_difference(sym_diff_expr, xule_context):
    left = evaluate(sym_diff_expr['leftExpr'], xule_context)
    for right_side in sym_diff_expr['rights']:
        right = evaluate(right_side['rightExpr'], xule_context)
        if left.type in ('unbound', 'none') or right.type in ('unbound', 'none'):
            left = XuleValue(xule_context, None, 'unbound')
        if left.type != 'set':
            raise XuleProcessingError(_("Symetric difference can only operatate on sets. The left side is a '{}'.".format(left.type)), xule_context)
        if right.type != 'set':
            raise XuleProcessingError(_("Symetric difference can only operatate on sets. The right side is a '{}'.".format(right.type)), xule_context)
    
        left = XuleUtility.symetric_difference(xule_context, left, right)
    
    return left

def evaluate_add(add_expr, xule_context):
    left_bar = add_expr['rights'][0]['op'][0] == '<' # the first operator
    if left_bar:
        left = evaluate(add_expr['leftExpr'], xule_context)
    else:
        # unbound is allowed, so it needs to be captured.
        try:
            left = evaluate(add_expr['leftExpr'], xule_context)
        except XuleIterationStop as xis:
            left = xis.stop_value #XuleValue(xule_context, None, 'unbound')
    
    for right in add_expr['rights']:
        
        operator = right['op']
        right_bar = operator[-1] == '>' 
        left_bar = operator[0] == '<'
        right_expr = right['rightExpr']
        
        if left.type not in ('int', 'float', 'decimal', 'string', 'uri', 'instant', 'time-period', 'set', 'list', 'unbound'):
            raise XuleProcessingError(_("Left side of a {} operation cannot be {}.".format(operator, left.type)), xule_context)
        
        if right_bar:
            right = evaluate(right_expr, xule_context)
        else:
            # unbound is allowed, so it needs to be captured.
            try:
                right = evaluate(right_expr, xule_context)
            except XuleIterationStop as xis:
                right = xis.stop_value 

        if right.type not in ('int', 'float', 'decimal', 'string', 'uri', 'instant', 'time-period', 'set', 'list', 'unbound'):
            raise XuleProcessingError(_("Right side of a {} operation cannot be {}.".format(operator, right.type)), xule_context)

        # A time-period can be on the left only if the right is also a time period.
        if left.type == 'time-period' and right.type != 'time-period':
            raise XuleProcessingError(_("Incompatabile operands {} {} {}.".format(left.type, operator, right.type)), xule_context)

        do_calc = True
        
        if left_bar and right_bar: # <+>
            if left.type == 'unbound' or right.type =='unbound':
                raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
        elif left_bar and not right_bar: #<+
            if left.type == 'unbound':
                raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
            if right.type == 'unbound':
                #the left value is the interim value
                do_calc = False
        elif not left_bar and right_bar: # +>
            if right.type == 'unbound':
                raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
            if left.type == 'unbound':
                left = right
                do_calc = False
        else: #no bars
            if left.type == 'unbound':
                left = right
                do_calc = False
            elif right.type == 'unbound':
                do_calc = False #the value is already in the left
        
        if do_calc:
            combined_type, left_compute_value, right_compute_value = combine_xule_types(left, right, xule_context)
            if combined_type == 'unbound':
                raise XuleProcessingError(_("Incompatabile operands {} {} {}.".format(left.type, operator, right.type)), xule_context)
            
            if '+' in operator:
                if left.type == 'set' and right.type == 'set':
                    #use union for sets
                    #left = XuleValue(xule_context, left_compute_value | right_compute_value, 'set')
                    left = XuleUtility.add_sets(xule_context, left, right)
                else:
                    left = XuleValue(xule_context, left_compute_value + right_compute_value, combined_type)
            elif '-' in operator:
                if left.type == 'set' and right.type == 'set':
                    left = XuleUtility.subtract_sets(xule_context, left, right)
                else:
                    left = XuleValue(xule_context, left_compute_value - right_compute_value, combined_type)
            else:
                raise XuleProcessingError(_("Unknown operator '%s' found in addition/subtraction operation." % operator), xule_context)
    
    return left  

def evaluate_comp(comp_expr, xule_context):
    left = evaluate(comp_expr['leftExpr'], xule_context)

    for right in comp_expr['rights']:
        operator = right['op']
        right_expr = right['rightExpr']

        right = evaluate(right_expr, xule_context)
            
        interim_value = None
        
        combined_type, left_compute_value, right_compute_value = combine_xule_types(left, right, xule_context)
        
        if left.type in ('instant', 'duration') and right.type in ('instant', 'duration'):
            left_compute_value = XulePeriodComp(left_compute_value)
            right_compute_value = XulePeriodComp(right_compute_value)

        if left.type in ('list','set'):
            left_compute_value = left.shadow_collection
        if left.type == 'dictionary':
            left_compute_value = dict(left.shadow_collection)
        if right.type in ('list','set'):
            right_compute_value = right.shadow_collection
        if right.type == 'dictionary':
            right_compute_value = dict(right.shadow_collection)

        if operator == '==':
            interim_value = XuleValue(xule_context, left_compute_value == right_compute_value, 'bool')
        elif operator == '!=':
            interim_value = XuleValue(xule_context, left_compute_value != right_compute_value, 'bool')
        elif operator == '<':
            interim_value = XuleValue(xule_context, left_compute_value < right_compute_value, 'bool')
        elif operator == '<=':
            interim_value = XuleValue(xule_context, left_compute_value <= right_compute_value, 'bool')
        elif operator == '>':
            interim_value = XuleValue(xule_context, left_compute_value > right_compute_value, 'bool')
        elif operator == '>=':
            interim_value = XuleValue(xule_context, left_compute_value >= right_compute_value, 'bool')  
        elif operator == 'in':
            interim_value = XuleValue(xule_context, left_compute_value in right_compute_value, 'bool')
        elif operator == 'not in':
            interim_value = XuleValue(xule_context, left_compute_value not in right_compute_value, 'bool')
        else:
            raise XuleProcessingError(_("Unknown operator '%s'." % operator), xule_context)  

        left = interim_value
        
    return left

def evaluate_not(not_expr, xule_context):
    initial_value = evaluate(not_expr['expr'], xule_context)
    
    if initial_value.type in ('unbound', 'none'):
        return initial_value
    
    if initial_value.type != 'bool':
        raise XuleProcessingError(_("The operand of the 'not' expression must be boolean, found '%s'" % initial_value.type), xule_context)
    
    return XuleValue(xule_context, not initial_value.value, 'bool')

def evaluate_and(and_expr, xule_context):
    value_found = False
    has_unbound = False
    left = XuleValue(xule_context, None, 'unbound')
    # Create a single list of expressions combing the left and each of the rights.
    exprs = [and_expr['leftExpr'],]  + [x['rightExpr'] for x in and_expr['rights']]
    
    # This process will allow unbounds if at some point a false is found. In this case the and expression is false. Otherwise, unbounds will make the result unbound.
    for expr in exprs:
        if value_found:
            break
        else:
            try:
                right = evaluate(expr, xule_context)
            except XuleIterationStop as xis:
                right = xis.stop_value #XuleValue(xule_context, None, 'unbound')
            if right.type == 'unbound':
                has_unbound = True
            if left.type not in ('unbound', 'bool') or right.type not in ('unbound', 'bool'):
                raise XuleProcessingError(_("Operand of 'and' expression is not boolean. Left and right operand types are '%s' and '%s'." % (left.type, right.type)), xule_context)
            
            if left.type == 'bool' and right.type == 'bool':
                left = XuleValue(xule_context, left.value and right.value, 'bool')
                if left.value == False:
                    value_found = True
            elif left.type == 'unbound' and right.type == 'unbound':
                continue
            elif left.type == 'unbound' and right.type == 'bool':
                left = right
                if left.value == False:
                    value_found = True
            elif left.type == 'bool' and right.type == 'unbound':
                if left.value == False:
                    value_found = True
    
    if (has_unbound and value_found) or not has_unbound:
        return left
    else:
        return XuleValue(xule_context, None, 'unbound')

def evaluate_or(or_expr, xule_context):
    value_found = False
    has_unbound = False
    left = XuleValue(xule_context, None, 'unbound')
    
    # Create a single list of expressions combing the left and each of the rights.
    exprs = [or_expr['leftExpr'],]  + [x['rightExpr'] for x in or_expr['rights']]
    for expr in exprs:
        if value_found:
            break

        else:
            try:
                right = evaluate(expr, xule_context)
            except XuleIterationStop as xis:
                right = xis.stop_value #XuleValue(xule_context, None, 'unbound')
            if right.type == 'unbound':
                has_unbound = True
            if left.type not in ('unbound', 'bool') or right.type not in ('unbound', 'bool'):
                raise XuleProcessingError(_("Operand of 'or' expression is not boolean. Left and right operand types are '%s' and '%s'." % (left.type, right.type)), xule_context)
            
            if left.type == 'bool' and right.type == 'bool':
                left = XuleValue(xule_context, left.value or right.value, 'bool')
                if left.value == True:
                    value_found = True
            elif left.type == 'unbound' and right.type == 'unbound':
                continue
            elif left.type == 'unbound' and right.type == 'bool':
                left = right
                if left.value == True:
                    value_found = True
            elif left.type == 'bool' and right.type == 'unbound':
                if left.value == True:
                    value_found = True
    if (has_unbound and value_found) or not has_unbound:
        return left
    else:
        return XuleValue(xule_context, None, 'unbound')

def evaluate_values(values_expr, xule_context):
    pass

def validate_values(values_expr, xule_context):
    #The 'values' expression is only allowed on an expression that is iterable with alignment. These are factsets and aggregations where the content is a factset).
    #The expression can also be a constant if the constant expression is iterable with alignment.
    if values_expr[0]['exprName'] == 'taggedExpr':
        inner_expression = values_expr[0].expr[0]
    else:
        inner_expression = values_expr[0]

    if not(inner_expression.get('has_alignment') == True and inner_expression.get('is_iterable') == True):
        if inner_expression.get('is_constant') == True:
            #Check the constant expression
            const_info = xule_context.find_var(inner_expression.varName, inner_expression.var_declaration)
            if const_info is None:
                raise XuleProcessingError(_("Internal error: constant not found during 'values' evaluation"), xule_context)
            else:
                if not(const_info['expr'].get('has_alignment') == True and const_info['expr'].get('is_iterable') == True):
                    raise XuleProcessingError(_("'values' can only preceed expressions that return aligned values"), xule_context)
        else:
            raise XuleProcessingError(_("'values' can only preceed expressions that return aligned values"), xule_context)
  
# 
#     
#     #For constants, take the values of the constant and remove the alignments
#     if values_expr[0].get('is_constant') == True:
#         if const_info['type'] != xule_context._VAR_TYPE_CONSTANT:
#             raise XuleProcessingError(_("Internal error: var ref in a 'values' expression must be a constant"), xule_context)
#         else:
#             if const_info['calculated'] == False:
#                 aligned_values = calc_constant(const_info, xule_context)
#                 const_info['calculated'] = True
#                 const_info['value'] = aligned_values
#             else:
#                 aligned_values = const_info['value']
#         #The 'values' expression can only be infront of an iterable expression that has alignment. The 'None' aligned values are really default values that are
#         #used if they are combined with something with alignment. When applying the 'values' expressions, these 'None' aligned values are discarded.
#         unaligned_values = XuleValueSet()
#         for alignment, values in aligned_values.values.items():
#             if alignment is not None:
#                 for value in values:
#                     unaligned_value = value.clone()
#                     unaligned_value.alignment = None
#                     unaligned_value.aligned_result_only = False
#                     unaligned_values.append(unaligned_value)
#         return unaligned_values
#     else:
#         #The expression is not a constant, so it needs to be evaluated.
#         xule_context.no_alignment = True
#         try:
#             return_value = evaluate(values_expr[0], xule_context)
#         finally:
#             xule_context.no_alignment = False
#         return return_value

import time

class Timer:
    def __enter__(self):
            self.start = time.clock()
            return self
    def __exit__(self, *args):
        self.end = time.clock()
        self.interval = self.end - self.start
        print("timing %s" % self.interval)


def evaluate_factset(factset, xule_context):
    """Evaluator for a factset
    
    There are two flavors of factsets.
    1. Starndard factset - finds facts in the instance (i.e. @Assets)
    2. Factset with inner expression - This is really an envelope that sets up aspect filters for other factsets that are inside the envelope.
    """
    if 'innerExpr' in factset:
        return evaluate_nesting_factset(factset, xule_context)
    else:
        return evaluate_factset_detail(factset, xule_context)

def evaluate_nesting_factset(factset, xule_context):
    """Evaluate a factset envolope
    
    This is a factset with nested factsets inside. Instead of getting facts from the instance, this is an envolope with aspect filters that will apply 
    to the inner factset. This allows the evaluation of the inner factset to have a different alignment than the results of this envelope.
    """
    
    aspect_filters, _x, aspect_vars = process_factset_aspects(factset, xule_context)
     
    #verify that there are not already filters in place
    current_filters, _x = xule_context.get_current_filters()
    current_aspects = {aspect_info[ASPECT] for aspect_info in current_filters}
     
    factset_aspects = {aspect_info[ASPECT] for aspect_info in aspect_filters}
     
    if current_aspects & factset_aspects:
        raise XuleProcessingError(_("A nested factset clause cannot include aspects in an outer factset clause, found '%s'." % ", ".join(current_aspects & factset_aspects)), xule_context)
         
    #add the align aspects to the nested_filter in the context
    xule_context.filter_add('nested', aspect_filters)
 
    save_aligned_result_only = xule_context.aligned_result_only
    save_used_expressions = xule_context.used_expressions
 
    nested_table = xule_context.iteration_table.add_table(factset['node_id'], xule_context.get_processing_id(factset['node_id']), is_aggregation=True)
    nested_values = XuleValueSet()
    try:
        while True:
            xule_context.aligned_result_only = False
            xule_context.used_expressions = set()
            try:
                nested_value = evaluate(factset['innerExpr'], xule_context)
            except XuleIterationStop:
                '''THIS COULD BE CREATE AN UNBOUND AND ADD IT TO THE WITH_VALUE. SIMILAR TO THE WAY THIS IS HANDLED IN FOR_BODY_DETAIL'''
                pass
            else:
                #if not(xule_context.iteration_table.current_table.current_alignment is None and xule_context.aligned_result_only):
                    #remove the with portion of the alignment
                if xule_context.iteration_table.current_table.current_alignment is not None: #this should be the alignment on the with table
                    remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in aspect_filters]
                    new_alignment = remove_from_alignment(xule_context.iteration_table.current_alignment, remove_aspects, xule_context)
                    nested_value.alignment = new_alignment
                     
                nested_value.facts = xule_context.facts
                nested_value.tags = xule_context.tags
                 
     
                nested_values.append(nested_value)
 
            #xule_context.iteration_table.del_current()
            xule_context.iteration_table.next(nested_table.table_id)
            if nested_table.is_empty:
                break
    finally:
        xule_context.aligned_result_only = save_aligned_result_only
        xule_context.used_expressions = save_used_expressions
        #delete the with table (in case it is left behind from an exception)
        xule_context.iteration_table.del_table(nested_table.table_id)    
        xule_context.filter_del()
 
    return nested_values

def evaluate_factset_detail(factset, xule_context):
    '''THIS CODE NEEDS A LITTLE REFACTORING. BREAK IT DOWN INTO FUNCTIONS. IMPROVE REUSE OF CODE FOR HANDLING 'IN' OPERATOR'''
    '''Evaluator for a factset
    
       The factset is divided into two parts. The first part contains aspects that will be used to filter the fact and will NOT
       be used for alignment. For example: "Assets[]" or "[lineItem=Assets]". These factsets will find all the 'Assets' facts in the 
       instance, but when these facts are compared to facts in other fact sets, the 'concept' aspect will not be used to check alignment.
       
       Actual aspects of the fact that are not specified in the first part of the factset will be used for alignment.
       
       Nested alignment:
           This would be put in the context for nested factset expressions. It would cause downstream factset evaluations
           to include the filter as part of getting facts. If the filter is 'closed', it would act like a closed factset and not allow
           facts that have dimenions in fact's alignment that are not in the filter. 'open' filters wouldn't care.
           
           This provides an alternative mechanism for handling alignment. Instead of getting all results for each side of an operation (i.e. property) 
           and then aligning them, it would allow the expression to iterate over one operand result set and evaluate for each result of the other operand. 
           By pushing the filter, first, only the aligned results will come back. 
    '''
    
    f_start = datetime.datetime.today()
    
#     #The no alignment flag indicates that the results of the factset should all have none alignment. It is set by the 'values' expression.
#     #current_no_alignment = xule_context.no_alignment
#     current_no_alignment = True if factset.get('values_expression') == True else False
#     
    #reset to false. This will prevent any downstream factsets for not having alignment. For example: values [where $item::period==$a::period] 
    #xule_context.no_alignment = False # this flag is not longer used, instead the parse result has a flag of 'values_expression'.
    
    saved_used_expressions = xule_context.used_expressions
    xule_context.used_expressions = set()
    try:
        non_align_aspects, align_aspects, aspect_vars = process_factset_aspects(factset, xule_context)
    finally:
        used_expressions = xule_context.used_expressions
        xule_context.used_expressions = saved_used_expressions | xule_context.used_expressions

    #check if any non_align_aspects overlap with nested_filters
    nested_factset_filters, other_filters = xule_context.get_current_filters()
    #This restriction is removed to suport rules like r1923
#     if with_aspects & factset_aspects:
#         raise XuleProcessingError(_("The factset cannont contain any aspects in any bounding 'with' clause, found '%s'." % ", ".join(with_aspects & factset_aspects)), xule_context)
    
    #combine all the filtering aspects.   
    all_aspect_filters = list(nested_factset_filters.items()) + list(other_filters.items()) + list(non_align_aspects.items()) 

    #If the the factset is dependent, then we only need to find facts that also match the current alignment. Create filters based on the current alignment.
    if not factset.get('covered') and factset['is_dependent']:
        if xule_context.dependent_alignment is None:
            #The table may acquire the dependent alignment after evaluating the aspect filters
            xule_context.iteration_table.current_table.make_dependent()        
        try:
            if xule_context.dependent_alignment is not None:
                unfrozen_alignment = {k: v for k, v in xule_context.dependent_alignment}
                align_aspects |= set(alignment_to_aspect_info(unfrozen_alignment, xule_context).items())
        except IndexError:
            pass
    all_aspect_filters += list(align_aspects.items())
    
    '''Match facts based on the aspects in the first part of the factset and any additional filters.
       This is done by intersecting the sets of the fact_index. The fact index is a dictionary of dictionaries.
       The outer dictionary is keyed by aspect and the inner by member. So fact_index[aspect][member] contains a 
       set of facts that have that aspect and member.'''       
    pre_matched_facts = factset_pre_match(factset, all_aspect_filters, non_align_aspects, align_aspects, xule_context)   
    
    
    pre_count1 = len(pre_matched_facts)
    f_pre_end = datetime.datetime.today()
    
    #For dependent factset, set flag to check if the iteration table becomes aligned. 
    #Bassically, there is no alignment yet. During the evaluation of the where clause a first time evaluated variable can create alignment.
    #If this happens, the pre matched facts should only include those facts that have matching alignment. So a flag in the context is set to check if the table becomes aligned.
    #When this happens a XuleReEvaluate exception is raised (this happens in the main evaluator()).

    saved_look_for_alignment = xule_context.look_for_alignment
    saved_where_table_ids = xule_context.where_table_ids
    saved_where_dependent_iterables = xule_context.where_dependent_iterables
    
    if factset['is_dependent'] and xule_context.iteration_table.any_alignment is None:
        xule_context.look_for_alignment = True
        #xule_context.where_table_ids = list(xule_context.iteration_table._ordered_tables.keys())
        xule_context.where_table_ids = [table.table_id for table in xule_context.iteration_table._ordered_tables.values()]        
        xule_context.where_dependent_iterables = [di['node_id'] for di in factset['dependent_iterables']]        
    else:
        #set_look_for_alignment = False
        xule_context.look_for_alignment = False
    #print(factset['node_id'], fact_value, no_pre_where_alignment, xule_context.iteration_table.current_table.table_id)
    
    default_where_used_expressions = set()
    
    recalc = False
    recalc_none = False
    
    try:
        results, default_where_used_expressions = process_filtered_facts(factset, pre_matched_facts, factset.get('covered', False), non_align_aspects, nested_factset_filters, aspect_vars, used_expressions, xule_context)
    except XuleReEvaluate as xac:
        recalc = True
        #turn off looking for changes during the where evaluation. At this point either there is no alignment, so the result will be empty or
        #there is alignment and the pre_matched_facts will be refiltered with the alignment. In this case, we don't need to continue looking for
        #evaluating an iterable that can produce alignment.
        
        xule_context.iteration_table.current_table.make_dependent()
        
        xule_context.look_for_alignment = False               
        if xac.alignment is None:
            recalc_none = True
            #there are no matching facts in the dependent iterable (that has alignments)
            results = XuleValueSet()
        else:
            #This occurs if the alignment is created while processing where clause. Re-filter the pre_matched facts with the alignment information and try the where clause again
            #Add the alignment to the all_aspect filters
#             if xac.alignment is None:
#                 #in this case the no facts can match because the dependency is unaligned but would normally have alignment. This is basicaly the default value of 'unbound'
#                 #for a factset.
#                 results = XuleValueSet()
#             else:
                unfrozen_alignment = {k: v for k, v in xac.alignment}
                additional_aspect_filters = list(alignment_to_aspect_info(unfrozen_alignment, xule_context).items())
                pre_matched_facts = factset_pre_match(factset, additional_aspect_filters, non_align_aspects, align_aspects, xule_context, starting_facts=pre_matched_facts)
                #try again
                try:
                    results, default_where_used_expressions = process_filtered_facts(factset, pre_matched_facts, not factset.get('covered'), non_align_aspects, nested_factset_filters, aspect_vars, used_expressions, xule_context)
                except XuleReEvaluate as xac:
                    #In the second pass, the alignment change should not happen.
                    raise XuleProcessingError(_("Encountered 2nd alignment change while processing the 'where' clause for a factset"), xule_context)
    finally:
        #if set_look_for_alignment:
            xule_context.look_for_alignment = saved_look_for_alignment
            xule_context.where_table_ids = saved_where_table_ids
            xule_context.where_dependent_iterables = saved_where_dependent_iterables
        
    if None not in results.values:        
        default_value = XuleValue(xule_context, None, 'unbound', tag=XuleValue(xule_context, tag_default_for_factset(factset, xule_context), 'empty_fact'))
        '''The current list of facts and tags are not inlcuded on the default None fact in a factset. This was causing problems with a exists() and missing().
           The default None fact in the missing would have the tags and facts from the first evaluation, but then these would be applied on consequent
           iterations where the tags from the first iteration would overwrite the tags on the consequent iterations.'''
        #default_value.facts = xule_context.facts
        #default_value.tags = xule_context.tags
        #default_value.used_vars = get_used_vars(xule_context, xule_context.used_vars)
        default_value.used_expressions = used_expressions | default_where_used_expressions
        #print("default fact", factset['exprName'], factset['node_id'], len(xule_context.used_expressions), len(default_value.used_expressions))
        if not factset.get('covered'):
            default_value.aligned_result_only = True
        results.append(default_value)

    f_end = datetime.datetime.today()

#     res_count = sum(len(v) for v in results.values.values())
#     pre_count2 = len(pre_matched_facts)
#     x = [a if v is None else v.format_value() for a, v in all_aspect_filters]   
# 
#     print("factset: {} res-count: {} pre-count1: {} pre-count2: {} total-time: {} pre-time: {} where-time: {} {} {} {}".format(factset['node_id'], res_count, pre_count1, pre_count2, 
# 
#                                                                                  (f_end - f_start).total_seconds(),
#                                                                                  (f_pre_end - f_start).total_seconds(),
#                                                                                  (f_end - f_pre_end).total_seconds(),
#                                                                                  'RECALC' if recalc else '',
#                                                                                  'None' if recalc_none else '',
#                                                                                  "; ".join(x)))
        
    return results

def factset_pre_match(factset, filters, non_aligned_filters, aligned_filters, xule_context, starting_facts=None):
    '''Match facts based on the aspects in the first part of the factset and any additional filters.
    
       This is done by intersecting the sets of the fact_index. The fact index is a dictionary of dictionaries.
       The outer dictionary is keyed by aspect and the inner by member. So fact_index[aspect][member] contains a 
       set of facts that have that aspect and member.'''
    if starting_facts is None:
        pre_matched_facts = None
        first = True
    else:
        pre_matched_facts = copy.copy(starting_facts)
        first = False
    #first = pre_matched_facts is None

    for aspect_info, filter_member in filters:
        
        if aspect_info[ASPECT_PROPERTY] is None:
            index_key = (aspect_info[TYPE], aspect_info[ASPECT])
        else:
            # aspect_info[ASPECT_PROPERTY][0] is the aspect property name
            # aspect_info[ASPECT_PROPERTY][1] is a tuple of the arguments
            index_key = ('property', aspect_info[ASPECT], aspect_info[ASPECT_PROPERTY][0]) + aspect_info[ASPECT_PROPERTY][1]
            if index_key not in xule_context.fact_index:
                raise XuleProcessingError(_("Factset aspect property '{}' is not a valid property.".format(index_key[2])), xule_context)
            
        facts_by_aspect = set()
        
        '''THIS MIGHT BE MORE EFFICIENTLY HANDLED BY IGNORING THE ASPECT IF THE MEMBER IS None OR ELIMINATING ALL FACTS'''
        #When the aspect key is not in the fact index, then the instance doesn't use this aspect (dimension). So create an entry for the 'None' key and put all the facts in it.
        if index_key not in xule_context.fact_index:
            xule_context.fact_index[index_key][None] = xule_context.fact_index['all']
        
        if aspect_info[SPECIAL_VALUE] is not None:
            if aspect_info[SPECIAL_VALUE] == '*':
                if aspect_info[ASPECT_OPERATOR] == '=':
                    if aspect_info[TYPE] == 'builtin' and aspect_info[ASPECT] in ('concept', 'period', 'entity'):
                        #this is all facts
                        continue
                    else:
                        #need to combine all the facts that have that aspect
                        facts_by_aspect = set(it.chain.from_iterable(v for k, v in xule_context.fact_index[index_key].items() if k is not None))
                else: # the operator is != ('in' and 'not in' are not allowed with a special value)
                    if aspect_info[TYPE] == 'builtin' and aspect_info[ASPECT] in ('concept', 'period', 'entity'):
                        # No facts can match these aspects not equal to * (i.e. @concept != *)
                        pre_matched_facts = []
                        break
                    else:
                        facts_by_aspect = xule_context.fact_index[index_key][None]
        else:                
            if aspect_info[ASPECT_OPERATOR] == 'in' and filter_member.type not in ('list', 'set'):
                    raise XuleProcessingError(_("The value for '%s' with 'in' must be a set or list, found '%s'" % (index_key[ASPECT], filter_member.type)), xule_context)

            #fix for aspects that take qname members (concept and explicit dimensions. The member can be a concept or a qname. The index is by qname.
            if index_key == ('builtin', 'concept'):
                if aspect_info[ASPECT_OPERATOR] in ('=', '!='):
                    member_values = {convert_value_to_qname(filter_member, xule_context),}
                else:
                    member_values = {convert_value_to_qname(x, xule_context) for x in filter_member.value}
            elif index_key[TYPE] == 'explicit_dimension':
                if aspect_info[ASPECT_OPERATOR] in ('=', '!='):
                    if filter_member.type == 'concept':
                        member_values = {convert_value_to_qname(filter_member, xule_context),}
                    else:
                        member_values = {filter_member.value,}
                else:
                    member_values = {convert_value_to_qname(x, xule_context) if x.type == 'concept' else x.value for x in filter_member.value}
            #Also fix for period aspect
            elif index_key == ('builtin', 'period'):
                if aspect_info[ASPECT_OPERATOR] in ('=', '!='):
                    member_values = {convert_value_to_model_period(filter_member, xule_context),}
                else:
                    member_values= {convert_value_to_model_period(x, xule_context) for x in filter_member.value}
            # Allow units to be a qname or a xule 'unit'
            elif index_key == ('builtin', 'unit'):
                conversion_function = lambda x: XuleUnit(x.value) if x.type == 'qname' else x.value
                if aspect_info[ASPECT_OPERATOR] in ('=', '!='):
                    member_values = {conversion_function(filter_member),}
                else:
                    member_values = {conversion_function(x) for x in filter_member.value}
            else:
                if aspect_info[ASPECT_OPERATOR] in ('=', '!='):
                    member_values = {filter_member.value,}
                else:
                    member_values = {x.value for x in filter_member.value}
                    '''THIS COULD USE THE SHADOW COLLECTION
                    member_values = set(filter_member.shadow_collection)
                    ''' 
            if aspect_info[ASPECT_OPERATOR] in ('=', 'in'):       
                found_members = member_values & xule_context.fact_index[index_key].keys()      
            else: # aspect operator is '!=' or 'not in'
                found_members = (xule_context.fact_index[index_key].keys() - {None,}) - member_values 

            for member in found_members:
                facts_by_aspect |= xule_context.fact_index[index_key][member]
                
        #intersect the facts with previous facts by aspect
        if first:
            first = False
            pre_matched_facts = facts_by_aspect
        else:
            pre_matched_facts &= facts_by_aspect
        
        
    if first:
        #there were no apsects to start the matching, so use the full set
        #pre_matched_facts = xule_context.model.factsInInstance 
        pre_matched_facts = xule_context.fact_index['all']
    
    if starting_facts is None: 
        #Check the alignment of pre matched facts to the dependent alignment
        if xule_context.dependent_alignment is not None and factset.is_dependent:
            match_aligned_facts = set()
            for fact in pre_matched_facts:
    #             print("dep", xule_context.dependent_alignment)
    #             print("fact", frozenset(get_alignment(fact, non_aligned_filters, xule_context)))
    #             print("matches?", frozenset(get_alignment(fact, non_aligned_filters, xule_context).items()) == xule_context.dependent_alignment)
                fact_alignment = calc_fact_alignment(factset, fact, non_aligned_filters, True, xule_context)
#                 if fact in xule_context.fact_alignments[factset['node_id']]:
#                     fact_alignment = xule_context.fact_alignments[factset['node_id']][fact]
#                 else:
#                     fact_alignment = frozenset(get_alignment(fact, non_aligned_filters, xule_context).items())
#                     xule_context.fact_alignments[factset['node_id']][fact] = fact_alignment
                    
                if fact_alignment == xule_context.dependent_alignment:
                    match_aligned_facts.add(fact)
            pre_matched_facts = match_aligned_facts
    
        '''  
        #This code reduces the pre matched facts to those that match alignment of the dependent alignment by using the fact index of dimensions that are not
        #in the dependent alignment. The method of checking the alignment used above proved to be more efficient. However, it may be that if the pre match includes a large number
        #of facts this method may be better.  
        if xule_context.dependent_alignment is not None and factset.is_dependent:
            if not hasattr(factset, 'empty_dimension_list'):            
                aligned_dimensions = [(k[0], k[1]) for k, v in aligned_filters if k[0] == 'explicit_dimension']
                empty_dimensions = [k for k in xule_context.fact_index.keys() if k[0] == 'explicit_dimension' and k not in aligned_dimensions]
                factset.empty_dimension_list = empty_dimensions
                
            for empty_dim_key in factset.empty_dimension_list:
                pre_matched_facts &= xule_context.fact_index[empty_dim_key][None]
        '''
    return pre_matched_facts

def calc_fact_alignment(factset, fact, non_aligned_filters, frozen, xule_context):
    if fact in xule_context.fact_alignments[factset['node_id']]:
        return xule_context.fact_alignments[factset['node_id']][fact][0 if frozen else 1]
    else:
        unfrozen_alignment = get_alignment(fact, non_aligned_filters, xule_context)
        fact_alignment = frozenset(unfrozen_alignment.items())
        xule_context.fact_alignments[factset['node_id']][fact] = (fact_alignment, unfrozen_alignment)    
        return fact_alignment if frozen else unfrozen_alignment
    
def process_filtered_facts(factset, pre_matched_facts, current_no_alignment, non_align_aspects, nested_filters, aspect_vars, pre_matched_used_expressoins_ids, xule_context):
    results = XuleValueSet()
    default_used_expressions = set()
    
    for model_fact in pre_matched_facts:
        #assume the fact will matach the where clause.
        matched = True
        
        #check if nill
        #print("nils", getattr(xule_context.global_context.options, "xule_include_nils", False))
        if not getattr(xule_context.global_context.options, "xule_include_nils", False) and model_fact.isNil:
        #if not xule_context.include_nils and model_fact.isNil:
            continue
        
        '''The alignment is all the aspects that were not specified in the first part of the factset (non_align_aspects).'''
        #set up potential fact result
        if current_no_alignment:
            alignment = None
        else:
            #alignment = get_alignment(model_fact, non_align_aspects, xule_context) 
            alignment = calc_fact_alignment(factset, model_fact, non_align_aspects, False, xule_context)       
    #         if len(alignment) == 0:
    #             alignment = None
            '''If we are in a with clause, the alignment needs to be adjusted. Each aspect in the with should be in the alignment even if
               if it is in the factset aspects (which would normally take that aspect out of the alignment).'''
            for nested_aspect_info in nested_filters:
                alignment_info = (nested_aspect_info[TYPE], nested_aspect_info[ASPECT])
                if alignment_info not in alignment:
                    if alignment_info == ('builtin', 'concept'):
                        alignment_value = model_fact.qname
                        #alignment_value = model_fact.elementQname
                    elif alignment_info == ('builtin', 'unit'):
                        if model_fact.isNumeric:
                            alignment_value = model_to_xule_unit(model_fact.unit, xule_context)
                    elif alignment_info == ('builtin', 'period'):
                        alignment_value = model_to_xule_period(model_fact.context, xule_context)
                    elif alignment_info == ('builtin', 'entity'):
                        alignment_value = model_to_xule_entity(model_fact.context, xule_context)
                    elif alignment_info[TYPE] == 'explicit_dimension':
                        model_dimension = model_fact.context.qnameDims.get(alignment_info[ASPECT])
                        if model_dimension is None:
                            alignment_value = None
                        else:
                            if model_dimension.isExplicit:
                                alignment_value = model_dimension.memberQname
                            else:
                                alignment_value = model_dimension.typedMember.xValue
                    #NEED TO CHECK WHAT THE VALUE SHOULD BE
                    else:
                        raise XuleProcessingError(_("Pushing nested factset filter alignment, found unknown alignment '%s : %s'" % alignment_info), xule_context)
                    
                    alignment[alignment_info] = alignment_value           
        
        '''Check closed factset'''
        if factset['factsetType'] == 'closed':
            aspect_dimensions = {aspect_info[ASPECT] for aspect_info in non_align_aspects}
            if set(model_fact.context.qnameDims.keys()) - aspect_dimensions:
                continue

        '''Check alignment filter'''
#         if alignment is not None:
#             if not current_no_alignment and xule_context.iteration_table.is_dependent:
#                 if xule_context.iteration_table.current_alignment is not None:
#                     if frozenset(alignment.items()) != xule_context.iteration_table.current_alignment:
#                         #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
#                         #from a higher table which will not inlucde the with filter aspects.
#                         if len(nested_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
#                             remove_aspects = [(nested_filter[0], nested_filter[1]) for nested_filter in nested_filters]
#                             adjusted_alignment = remove_from_alignment(frozenset(alignment.items()), remove_aspects, xule_context)
#                             if adjusted_alignment != xule_context.iteration_table.current_alignment:
#                                 continue
#                         else:
#                             continue

        if alignment is not None:
            #if not current_no_alignment and xule_context.iteration_table.is_dependent:
            if not current_no_alignment and factset['is_dependent']:
                if xule_context.dependent_alignment is not None:
                    if frozenset(alignment.items()) != xule_context.dependent_alignment:
                        #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
                        #from a higher table which will not inlucde the with filter aspects.
                        if len(nested_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
                            remove_aspects = [(nested_filter[0], nested_filter[1]) for nested_filter in nested_filters]
                            adjusted_alignment = remove_from_alignment(frozenset(alignment.items()), remove_aspects, xule_context)
                            if adjusted_alignment != xule_context.dependent_alignment:
                                continue #try the next fact from the pre match
                        else:
                            continue #try the next fact from the pre match
            
        fact_value = XuleValue(xule_context, model_fact, 'fact', alignment=None if alignment is None else frozenset(alignment.items()))
        if not current_no_alignment:
            fact_value.aligned_result_only = True
        
        '''Where clause'''
        if 'whereExpr' in factset:
            
            #push the apsect variables
            ''' aspect_var_info is a tuple: 0 = aspect type, 1 = aspect name'''
            
#                 aspect_vars_flat = list(aspect_vars.items())
#                 for declaration_index, aspect_var_flat in enumerate(aspect_vars_flat, 1):
            for var_name, aspect_var_tuple in aspect_vars.items():
                aspect_type = aspect_var_tuple[0]
                aspect_name = aspect_var_tuple[1]
                #declaration_index = aspect_var_tuple[2]
                #declaration_id = (factset['node_id'], declaration_index)
                declaration_id = aspect_var_tuple[2]
                if aspect_type == 'builtin':
                    if aspect_name == 'concept':
                        xule_context.add_arg(var_name,
                                             declaration_id,
                                             None,
                                             XuleValue(xule_context, model_fact.concept, 'concept'),
                                             'single')
                    elif aspect_name == 'period':
                        if model_fact.context.isStartEndPeriod:
                            xule_context.add_arg(var_name,
                                                 declaration_id,
                                                 None,
                                                 XuleValue(xule_context, (model_fact.context.startDatetime,
                                                                          model_fact.context.endDatetime),
                                                                        'duration', from_model=True),
                                                 'single')
                        elif model_fact.context.isInstantPeriod:
                            xule_context.add_arg(var_name,
                                                 declaration_id,
                                                 None,
                                                 XuleValue(xule_context, model_fact.context.instantDatetime,
                                                                          'instant', from_model=True),
                                                 'single')
                        else:
                            xule_context.add_arg(var_name,
                                                 declaration_id,
                                                 None,
                                                 XuleValue(xule_context, (datetime.datetime.min, datetime.datetime.max),
                                                                          'duration', from_model=True),
                                                 'single')                           
                    elif aspect_name == 'unit':
                        xule_context.add_arg(var_name,
                                             declaration_id,
                                             None,
                                             XuleValue(xule_context, model_to_xule_unit(model_fact.unit, xule_context), 'unit'),
                                             'single')
                    elif aspect_name == 'entity':
                        xule_context.add_arg(var_name,
                                             declaration_id,
                                             None,
                                             XuleValue(xule_context, model_fact.context.entityIdentifier,
                                                                      'entity'),
                                             'single')
                    else:
                        raise XuleProcessingError(_("Unknown built in aspect '%s'" % aspect_name), xule_context)
                elif aspect_type == 'explicit_dimension':
                    model_dimension = model_fact.context.qnameDims.get(aspect_name)
                    if model_dimension is None:
                        member = XuleValue(xule_context, None, 'qname')
                    else:
                        if model_dimension.isExplicit:
                            member = XuleValue(xule_context, model_dimension.memberQname, 'qname')
                        else:
                            #This is a typed dimension
                            member = XuleValue(xule_context, model_dimension.typedMember.xValue, model_to_xule_type(xule_context, model_dimension.typedMember.xValue))
                        
                    xule_context.add_arg(var_name,
                                         declaration_id,
                                         None, #tagged,
                                         member,
                                         'single')
       
                        
            #add the $item variable for the fact
            xule_context.add_arg('fact',
                                 #(factset['node_id'], 0),
                                 factset['whereExpr']['node_id'],
                                 None, #tagged
                                 fact_value,
                                 'single')
            
            '''The where clause is evaluated in a sub table.'''
#                 switched_alignment = False
#                 if xule_context.dependent_alignment is None and alignment is not None:
#                     switched_alignment = True
#                     #xule_context.iteration_table.current_table.dependent_alignment = frozenset(alignment.items())
            save_aligned_result_only = xule_context.aligned_result_only
            #save_used_vars = xule_context.used_vars
            save_used_expressions = xule_context.used_expressions
            
            #pre_aggregation_table_list_size = len(xule_context.iteration_table)
            where_table = xule_context.iteration_table.add_table(factset['whereExpr']['node_id'], xule_context.get_processing_id(factset['whereExpr']['node_id']), is_aggregation=True)
#                 if switched_alignment:
#                     where_table.dependent_alignment = frozenset(alignment.items())
            
            try:
                while True:
                    xule_context.aligned_result_only = False
                    #xule_context.used_vars = []
                    xule_context.used_expressions = set()
                    where_matched = True
                    try:
                        where_value = evaluate(factset['whereExpr'], xule_context)
                    except XuleIterationStop as xis:
                        where_value = xis.stop_value #XuleValue(xule_context, None, 'unbound')
                    finally:
#                             if xule_context.iteration_table.current_table.current_alignment is None and xule_context.aligned_result_only: 
#                                 where_value = XuleValue(xule_context, None, 'unbound')
                        xule_context.aligned_result_only = save_aligned_result_only


                    #check alignment again after evaluating the where clause. If the clause is dependent, only want results that align with the current row.
                    #if factset.is_dependent:
#                         if alignment is not None:
#                             if not current_no_alignment and xule_context.iteration_table.is_dependent:
#                                 if xule_context.iteration_table.current_alignment is not None:
#                                     if frozenset(alignment.items()) != xule_context.iteration_table.current_alignment:
#                                         #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
#                                         #from a higher table which will not inlucde the with filter aspects.
#                                         if len(nested_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
#                                             remove_aspects = [(nested_filter[0], nested_filter[1]) for nested_filter in nested_filters]
#                                             adjusted_alignment = remove_from_alignment(frozenset(alignment.items()), remove_aspects, xule_context)
#                                             if adjusted_alignment != xule_context.iteration_table.current_alignment:
#                                                 where_matched = False
#                                         else:
#                                             where_matched = False

#                         #check if the alignment went from None to aligned during the where evaluation
#                         if factset.is_dependent and no_pre_where_alignment and xule_context.iteration_table.any_alignment is not None:
#                             #If this happens, then re-filter the pre_matched facts with the alignment
#                             raise XuleReEvaluate(xule_context.iteration_table.any_alignment)

                    if alignment is not None:
                        #if not current_no_alignment and xule_context.iteration_table.is_dependent:
                        if not current_no_alignment and factset['is_dependent']:
                            if xule_context.dependent_alignment is not None:
                                if frozenset(alignment.items()) != xule_context.dependent_alignment:
                                    #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
                                    #from a higher table which will not inlucde the with filter aspects.
                                    if len(nested_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
                                        remove_aspects = [(nested_filter[0], nested_filter[1]) for nested_filter in nested_filters]
                                        adjusted_alignment = remove_from_alignment(frozenset(alignment.items()), remove_aspects, xule_context)
                                        if adjusted_alignment != xule_context.dependent_alignment:
                                            where_matched = False
                                    else:
                                        where_matched = False



                    if where_matched:
                        default_used_expressions.update(set(xule_context.used_expressions))
                        if where_value.type == 'unbound':
                            pass
                        elif where_value.type == 'bool':                                
                            if where_value.value:
                                new_fact_value = copy.copy(fact_value)
                                new_fact_value.facts = xule_context.iteration_table.facts
                                new_fact_value.tags = xule_context.iteration_table.tags
                                #new_fact_value.used_vars = get_used_vars(xule_context, pre_matched_used_var_ids + xule_context.used_vars)
                                new_fact_value.used_expressions = pre_matched_used_expressoins_ids | xule_context.used_expressions
                                results.append(new_fact_value)
                            '''It may be that the false value should also be included with an unbound value'''
                        else:
                            raise XuleProcessingError(_("Where clause in a factset did not evaluate to a boolean. Found '%s'." % where_value.type), xule_context)
                            
                    #xule_context.iteration_table.del_current()
                    #if len(xule_context.iteration_table) == pre_aggregation_table_list_size:
                    xule_context.iteration_table.next(where_table.table_id)
                    if where_table.is_empty:
                        break                

            finally:
                #remove $item
                xule_context.del_arg('item', #(factset['node_id'], 0),
                                 factset['whereExpr']['node_id'],)
                #remove aspect variables
                for var_name, aspect_var_tuple in aspect_vars.items():
                    declaration_id = aspect_var_tuple[2]
                    xule_context.del_arg(var_name, declaration_id)
                #remove where table (if this is the result of an exception the where table may be left behind)
                xule_context.iteration_table.del_table(where_table.table_id)
                #restore aligned results, used_vars and used_expressoins
                #xule_context.aligned_result_only = save_aligned_result_only  
                #xule_context.used_vars = save_used_vars
                xule_context.used_expressions = save_used_expressions                     
        else:
            #fact_value.used_vars = get_used_vars(xule_context, pre_matched_used_var_ids)
            fact_value.used_expressions = pre_matched_used_expressoins_ids
            results.append(fact_value)    

    return results, default_used_expressions

def evaluate_dict(dict_expr, xule_context):
    result_dict = dict()
    result_shadow = dict()
    
    for pair in dict_expr['items']:
        key = evaluate(pair['key'], xule_context)
        value = evaluate(pair['value'], xule_context)
    
        if key.type == 'dictionary':
            raise XuleProcessingError(_("Key to a dictionary cannot be a dictionary."), xule_context)
        
        if key.shadow_collection if key.type in ('set', 'list') else key.value  not in result_shadow:
            result_dict[key] = value
            result_shadow[key.shadow_collection if key.type in ('set', 'list') else key.value] = value.shadow_collection if value.type in ('set', 'list', 'dictionary') else value.value
    
    return XuleValue(xule_context, frozenset(result_dict.items()), 'dictionary', shadow_collection=frozenset(result_shadow.items()))

def evaluate_list(list_expr, xule_context):
    result = list()
    result_shadow = list()
    for item in list_expr['items']:
        item_value = evaluate(item, xule_context)
        result.append(item_value)
        result_shadow.append(item_value.value)
    
    return XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))

def evaluate_set(set_expr, xule_context):
    result = list()
    result_shadow = list()
    for item in set_expr['items']:
        item_value = evaluate(item, xule_context)
        if item_value.shadow_collection if item_value.type in ('set', 'list', 'dictionary') else item_value.value not in result_shadow:
            result.append(item_value)
            result_shadow.append(item_value.value)
    
    return XuleValue(xule_context, frozenset(result), 'set', shadow_collection=frozenset(result_shadow))

def evaluate_filter(filter_expr, xule_context):

    collection_value = evaluate(filter_expr['expr'], xule_context)
    
    if collection_value.type not in ('set', 'list'):
        raise XuleProcessingError(_("Filter expresssion can only be used on a 'set' or 'list', found '{}'.".format(collection_value.type)), xule_context)
    
    # do nothing if there is no filtering
    if 'whereExpr' not in filter_expr and 'returnsExpr' not in filter_expr:
        return collection_value
    
    if collection_value.type == 'set':
        results = set()
        results_shadow = set()
    else: # list
        results = list()
        results_shadow = list()
    
    for item_value in collection_value.value:
        xule_context.add_arg('item',
                             filter_expr['expr']['node_id'],
                             True,
                             item_value,
                             'single')
        
        try:
            keep = True
            if 'whereExpr' in filter_expr:
                keep = False
                filter_where_result = evaluate(filter_expr['whereExpr'], xule_context)
                
                if filter_where_result.type == 'bool':
                    keep = filter_where_result.value
                elif filter_where_result.type != 'unbound':
                    raise XuleProcessingError(_("The where clause on a filter expression must evaluate to a boolean, found '{}'.".format(filter_where_result.type)), xule_context)            
            
            if keep:
                if 'returnsExpr' in filter_expr:
                    keep_item = evaluate(filter_expr['returnsExpr'], xule_context) 
                else:
                    keep_item = item_value
            
                if collection_value.type == 'set':
                    if (keep_item.shadow_collection if keep_item.type in ('list', 'set', 'dictionary') else keep_item.value) not in results_shadow:
                        results.add(keep_item)
                        results_shadow.add(keep_item.shadow_collection if keep_item.type in ('list', 'set', 'dictionary') else keep_item.value)
                    # otherwise, this a duplicate
                else: #list
                    results.append(keep_item)
                    results_shadow.append(keep_item.shadow_collection if keep_item.type in ('list', 'set', 'dictionary') else keep_item.value)            
            
        finally:    
            #remove the args
            xule_context.del_arg('item',
                                 filter_expr['expr']['node_id'])

    if collection_value.type == 'set':
        return XuleValue(xule_context, frozenset(results), 'set', shadow_collection=frozenset(results_shadow))
    else: # list
        return XuleValue(xule_context, tuple(results), 'list', shadow_collection=tuple(results_shadow))


def evaluate_navigate(nav_expr, xule_context):
    
    '''WILL NEED TO HANDLE CASE WHEN THERE IS NOT AN ARCROLE. THIS WILL NEED TO GATHER ALL THE BASESETS ACROSS ALL ARCROLLS'''
    if 'arcrole' not in nav_expr and 'dimensional' not in nav_expr:
        raise XuleProcessingError(_("Not including an arcrole for navigation is currently not supported."))
    
    # Get the taxonomy
    if 'taxonomy' in nav_expr:
        dts_value = evaluate(nav_expr['taxonomy'], xule_context)
        if dts_value.type != 'taxonomy':
            raise XuleProcessingError(_("Expecting a taxonomy for the 'taxonomy' clause of navigate. Found {}.".format(dts_value.type)), xule_context)
        dts = dts_value.value
    else:
        # Default to the taxonomy of the instance
        dts = xule_context.model 


    # Set up the variables for the results of the traversal
    return_by_networks = nav_expr.get('return', dict()).get('byNetwork', False)
    if return_by_networks:
        results_by_networks = dict()
    result_items = list()

    # Determine if we are returning paths.
    paths = nav_expr.get('return', dict()).get('paths', False)
    
    return_names = get_return_component_names(nav_expr, xule_context)
    
    #Get the from and to concepts if they are supplied in the expression
    nav_from_concepts = nav_get_element(nav_expr, 'from', dts,  xule_context)
    nav_to_concepts = nav_get_element(nav_expr, 'to', dts, xule_context)
    
    # This checks if there was 'from' concept in the expression, but no concepts were return. Same for the 'to' concept in the expression. Then there is not navigation to do
    if (nav_from_concepts is None or len(nav_from_concepts) > 0) and (nav_to_concepts is None or len(nav_to_concepts) > 0):    
        arcrole = nav_get_role(nav_expr, 'arcrole', dts, xule_context)       
        role = nav_get_role(nav_expr, 'role', dts, xule_context)
        link_qname = evaluate(xule_context, nav_expr['link']).value if 'link' in nav_expr else None
        arc_qname = None # This is always none. 
        dimension_arcroles = None
        
        # Find the relationships
        if (('arcrole' in nav_expr and arcrole is None) or
            ('role' in nav_expr and role is None) or
            ('link' in nav_expr and link_qname is None)):
            #There are no networks to navigate
            relationship_sets = list()
        else:
            #get the relationships
            if nav_expr.get('dimensional'):
                drs_role = nav_get_role(nav_expr, 'drsRole', dts, xule_context)
                table_concepts = nav_get_element(nav_expr, 'table', dts, xule_context)
                if arcrole is not  None:
                    dimension_arcroles = xc.DIMENSION_PSEDDO_ARCROLES.get(arcrole, ('all', {arcrole,}))
                relationship_sets = [XuleUtility.dimension_set(dts, x) for x in XuleUtility.base_dimension_sets(dts) if ((drs_role is None or x[XuleUtility.DIMENSION_SET_ROLE] == drs_role) and
                                                                                                                         (table_concepts is None or x[XuleUtility.DIMENSION_SET_HYPERCUBE] in table_concepts))]
            else:
                relationship_set_infos = XuleProperties.get_base_set_info(dts, arcrole, role, link_qname, arc_qname)
                # The relationship_set_info includes the includeProhibits at the end of the tuple
                relationship_sets = [XuleUtility.relationship_set(dts, x) for x in relationship_set_infos]
    
        direction = nav_expr['direction']
        include_start = nav_expr.get('includeStart', False)

        for relationship_set in relationship_sets:
            if nav_from_concepts is None:
                # The from was not in tne navigate expression. Use the roots
                from_concepts = relationship_set.rootConcepts
            else:
                from_concepts = nav_from_concepts
              
            for from_concept in from_concepts:
    #             if direction == 'self':
    #                 # include_start is always False for the self direction since the self concept is always included.
    #                 for rel in relationship_set.fromModelObject(from_concept):
    #                     result_items += nav_decorate({'relationship': rel, 'network': get_network_info(relationship_set, xule_context)}, 'from', return_names, False, xule_context)
    #                 for rel in relationship_set.toModelObject(from_concept):
    #                     result_items += nav_decorate({'relationship':rel, 'network': get_network_info(relationship_set, xule_context)}, 'to', return_names, False, xule_context) 
    #                 #result_items += list(y for y in (nav_decorate(rel, 'from', nav_expr, False, xule_context) for rel in relationship_set.fromModelObject(from_concept))) + list(y for y in (nav_decorate(rel, 'to', nav_expr, xule_context) for rel in relationship_set.toModelObject(from_concept))) # This will be a list            
                if direction == 'descendants':
                    for rel in nav_traverse(nav_expr, xule_context, 'down', relationship_set, from_concept, nav_to_concepts, int(nav_expr['depth']), return_names, dimension_arcroles):
                        result_items += nav_decorate(rel, 'down', return_names, include_start, paths, xule_context)
                if direction == 'children':
                    for rel in nav_traverse(nav_expr, xule_context, 'down', relationship_set, from_concept, nav_to_concepts, 1, return_names, dimension_arcroles):
                        result_items += nav_decorate(rel, 'down', return_names, include_start, paths, xule_context)
                if direction == 'ancestors':
                    for rel in nav_traverse(nav_expr, xule_context, 'up', relationship_set, from_concept, nav_to_concepts, int(nav_expr['depth']), return_names, dimension_arcroles):
                        result_items += nav_decorate(rel, 'up', return_names, include_start, paths, xule_context)
                if direction == 'parents':
                    for rel in nav_traverse(nav_expr, xule_context, 'up', relationship_set, from_concept, nav_to_concepts, 1, return_names, dimension_arcroles):
                        result_items += nav_decorate(rel, 'up', return_names, include_start, paths, xule_context)
                if direction == 'siblings':
                    for parent_rel in nav_traverse(nav_expr, xule_context, 'up', relationship_set, from_concept, None, 1, list(), dimension_arcroles):
                        for sibling_rel in nav_traverse(nav_expr, xule_context, 'down', relationship_set, parent_rel['relationship'].fromModelObject, nav_to_concepts, 1, return_names, dimension_arcroles):
                            if include_start or sibling_rel['relationship'] is not parent_rel['relationship']:
                                result_items += nav_decorate(sibling_rel, 'up', return_names, False, paths, xule_context)
                if direction == 'previous-siblings':
                    for parent_rel in nav_traverse(nav_expr, xule_context, 'up', relationship_set, from_concept, None, 1, list(), dimension_arcroles):
                        for sibling_rel in nav_traverse(nav_expr, xule_context, 'down', relationship_set, parent_rel['relationship'].fromModelObject, nav_to_concepts, 1, return_names, dimension_arcroles):
                            if include_start or sibling_rel['relationship'] is not parent_rel['relationship']:
                                result_items += nav_decorate(sibling_rel, 'up', return_names, False, paths, xule_context)                
                            if sibling_rel['relationship'] is parent_rel['relationship']:
                                break # We are done.            
                if direction == 'following-siblings':
                    for parent_rel in nav_traverse(nav_expr, xule_context, 'up', relationship_set, from_concept, None, 1, list(), dimension_arcroles):
                        start_rel_found = False
                        for sibling_rel in nav_traverse(nav_expr, xule_context, 'down', relationship_set, parent_rel['relationship'].fromModelObject, nav_to_concepts, 1, return_names, dimension_arcroles):
                            if sibling_rel['relationship'] is parent_rel['relationship']:
                                start_rel_found = True
                            if start_rel_found:
                                if include_start or sibling_rel['relationship'] is not parent_rel['relationship']:
                                    result_items += nav_decorate(sibling_rel, 'up', return_names, False, paths, xule_context)                
            
            if return_by_networks:
                if len(result_items) > 0:
                    results_by_networks[get_network_info(relationship_set, xule_context)] = result_items
                result_items = list()
    
    if return_by_networks:
        return nav_finish_results(nav_expr, results_by_networks, 'result-order' in return_names, xule_context)
    else:
        return nav_finish_results(nav_expr, result_items, 'result-order' in return_names, xule_context)

def nav_traverse(nav_expr, xule_context, direction, network, parent, end_concepts, remaining_depth, return_names, dimension_arcroles=None, previous_concepts=None, nav_depth=1, result_order=0, arc_attribute_names=None):
    """Traverse a network
    
    Arguments:
        direction (string): Either 'down' or 'up'
        network (ModelRelationshipSet): The network of relationships.
        parent (ModelConcept): The parent concept
        end_concepts (set of ModelConcepts): A set of concepts if encountered the traversal should stop
        depth (int): How many levels to traverse. -1 is infinite depth.
        previous_concepts (set of ModelConcepts): List concepts already traversed. Used to prevent loops in the traversal
        include_start (boolean): Indicates that the starting concept should be included in the results
    
    Return:
        list of tuples of (ModelRelationship, top)
    """
    # Initialize previous_concepts
    if previous_concepts is None: # this only happens on the intial call.
        previous_concepts = {parent, }
        arc_attribute_names = {x for x in return_names if isinstance(x, QName)}
        first_time = True
    else:
        first_time = False
    
    if end_concepts is None:
        end_concepts = set()
    
    #initialize depth
    if remaining_depth == -1:
        depth = float('inf') 
           
    if remaining_depth == 0:
        return list()
    
    paths = nav_expr.get('return', dict()).get('paths', False)
    
    # 'children' are parents if the direction is up.
    children = list()
    
    if parent in end_concepts:
        # This should only happen if in the inital call to nav_traverse the parent is in the list of 
        # end concepts. In this case there is no navigation.
        return children
    
    children_method = network.fromModelObject if direction == 'down' else network.toModelObject
    for rel_number, rel in enumerate(sorted(children_method(parent),key=lambda x: x.order or 1), 1):
        inner_children = list()

        child = rel.toModelObject if direction == 'down' else rel.fromModelObject
        rel_info = {'relationship':rel}
        
        if first_time:
            rel_info['first'] = True
        if 'network' in return_names:
            rel_info['network'] = get_network_info(network, xule_context)
        if 'navigation-order' in return_names:
            rel_info['navigation-order'] = rel_number
        if 'navigation-depth' in return_names:
            rel_info['navigation-depth'] = nav_depth
#         if 'result-order' in return_names:
#             rel_info['result-order'] = result_order
        for arc_attribute_name in arc_attribute_names:
            rel_info[arc_attribute_name] = rel.arcElement.get(arc_attribute_name.clarkNotation)
        
        # Decide if the child will be in the results. If the child is not in the results, the navigation does not stop.
        if (
            nav_traverse_where(nav_expr, rel, xule_context) and
            (
                dimension_arcroles is None or 
                'dimensional' not in nav_expr or
                ('dimensional' in nav_expr and rel.arcrole in dimension_arcroles[xc.DIMENSION_PSEUD0_ARCROLE_PART] and
                 (
                  dimension_arcroles[xc.DIMENSION_PSEUD0_SIDE] == 'all' or
                  rel.side == dimension_arcroles[xc.DIMENSION_PSEUD0_SIDE]
                 )
                )
            )
           ):
            keep_rel = rel_info
            #inner_children.append(rel_info)
        else:
            keep_rel = None
        
        #if child not in end_concepts:
        
        
        if child not in previous_concepts:
            previous_concepts.add(child)
            
            if child in end_concepts:
                # This is the end of the traversal because the child is a 'to' concept.
                if paths:
                    inner_children.append([keep_rel,])
                else:
                    inner_children += [keep_rel,]
            else:
                next_children = nav_traverse(nav_expr, 
                                             xule_context, 
                                             direction, 
                                             network, 
                                             child, 
                                             end_concepts, 
                                             remaining_depth - 1, 
                                             return_names, 
                                             dimension_arcroles, 
                                             previous_concepts, 
                                             nav_depth + 1, 
                                             result_order, 
                                             arc_attribute_names)
                                
                if len(next_children) == 0 and len(end_concepts) > 0: # The to concept was never found
                    # Reset the inner_child list. This will throw away all reseults that lead to this moment.
                    inner_children = list()
                else:
                    if paths:
                        if len(next_children) == 0:
                            # On a leaf. This is where a path is initially created.
                            inner_children.append([keep_rel,])
                        else:
                            # There are children of the current child (keep_rel), add the current child to each of the paths from the current childs children
                            for i in next_children:
                                inner_children.append([keep_rel,] + i)
                    else:
                        inner_children += [keep_rel,] + next_children
#                     if 'result-order' in return_names:
#                         result_order = inner_children[-1]['result-order']
        else:
            if keep_rel is not None:
                #indicates a cycle
                keep_rel['cycle'] = True
            if paths:
                inner_children.append([keep_rel,])
            else:
                inner_children.append(keep_rel)

        children += inner_children
        # This only allows the first child of the initial call to nav_traverse to be marked as first.The first is used to indicate when to use
        # the from side of the relationship for 'ionclude start'.
        if not paths:
            first_time = False 
    return children

def nav_traverse_where(nav_expr, relationship, xule_context):
    if 'whereExpr' not in nav_expr:
        return True
    else:
        xule_context.add_arg('relationship',
                             nav_expr['whereExpr']['node_id'],
                             True,
                             XuleValue(xule_context, relationship, 'relationship'),
                             'single')
        
        try:
            nav_where_results = evaluate(nav_expr['whereExpr'], xule_context)
        finally:    
            #remove the args
            xule_context.del_arg('relationship',
                                 nav_expr['whereExpr']['node_id'])

        if nav_where_results.type == 'bool':
            return nav_where_results.value
        elif nav_where_results.type == 'unbound':
            return False
        elif filter_where_result.type != 'unbound':
            raise XuleProcessingError(_("The where clause on a navigation expression must evaluate to a boolean, found '{}'.".format(nav_where_results.type)), xule_context)

        
#         if 'is_iterable' in nav_expr['whereExpr']:
#             raise XuleProcessingError(_("Where expression in a navigation cannot return multiple values"))
#         
#         xule_context.add_arg('relationship',
#                              nav_expr['whereExpr']['node_id'],
#                              True,
#                              XuleValue(xule_context, relationship, 'relationship'),
#                              'single')                          
#         def cleanup_function():
#             #remove the args
#             xule_context.del_arg('relationship',
#                                  nav_expr['whereExpr']['node_id'])
# 
#         nav_where_results = isolated_evaluation(xule_context,
#                                                      nav_expr['whereExpr']['node_id'], 
#                                                      nav_expr['whereExpr'], 
#                                                      cleanup_function=cleanup_function
#                                                      
#                                                      )
# 
#         if None in nav_where_results.values:
#             if nav_where_results.values[None][0].type == 'bool':
#                 return nav_where_results.values[None][0].value
#             elif nav_where_results.values[None][0].type == 'unbound':
#                 return False
#         else:
#             return False

def nav_get_role(nav_expr, role_type, dts, xule_context):
    """Get the full role from the navigation expression.
    
    A role in the navigation expressions is either a string, uri or a non prefixed qname. If it is a string or uri, it is a full arcrole. If it is
    a non prefixed qname, than the local name of the qname is used to match an arcrole that ends in 'localName'. If more than one arcrole is found then
    and error is raise. This allows short form of an arcrole i.e parent-child.
    """
    if role_type in nav_expr:
        role_value = evaluate(nav_expr[role_type], xule_context)
        if role_value.type in ('string', 'uri'):
            return role_value.value
        elif role_value.type == 'qname':
            return XuleUtility.resolve_role(role_value, role_type, dts, xule_context)
    else:
        return None # There is no arcrole on the navigation expression

def nav_get_element(nav_expr, side, dts, xule_context):
    """Get the element or set of elements on the from or to side of a navigation expression'
    
    This determines the from/to elements of a navigation expression. If the navigation expression includes the from/to component, this will be evaluated.
    The result can be a qname, concept or a set/list of qname or concepts.
    
    Arguments:
        nav_expr (dictionary): The navigation expression AST node
        side (string): Either 'from' or 'to'.
        xule_context (XuleRuleContext): The processing context
        
    Returns:
        None - indicates that the side is not in the navigation expression
        set of concepts - the set of the concepts if the side evaluates to a set or list of concept/concepts
    """
    
    if side in nav_expr:
        side_value = evaluate(nav_expr[side], xule_context)
        if side_value.type == 'qname':
            concept = XuleProperties.get_concept(dts, side_value.value)
            if concept is None:
                return set()
            else:
                return {concept,}
        elif side_value.type == 'concept':
            return {side_value.value,}
        elif side_value.type in ('set', 'list'):
            concepts = set()
            for item in side_value.value:
                if item.type == 'qname':
                    concept = XuleProperties.get_concept(dts, item.value)
                    if concept is not None:
                        concepts.add(concept)
                elif item.type == 'concept':
                    concepts.add(time.value)
                else:
                    raise XuleProcessingError(_("In navigation, expecting a collection of concepts or concepts, but found {}.".format(item.type)))
            return concepts
        else:
            raise XuleProcessingError(_("In navigation, expecting a concept or qname, but found {}.".format(side_value.type)))
    else:
        return None # The side is not in the navigation expression


def nav_decorate(rel, direction, return_names, include_start, paths, xule_context):
    """Determine what will be outputted for a single navigation item.
    
    Arguments:
        rel (dict): A dition of the relationship and additional information from the traversal
        direction (string): 'up' or 'down'. Direction of the traversal
        return_names (list of strings): List of the return components to decoreate the relationship.
        include_start (boolean or 'start_only'): Indicates if the start concept should be returned.
        xule_context (XuleRuleContext): Processing context
        
    Returns:
        A tuple of tuples of the return components for the relationship. The tuple is composed of:
        0. value
        1. xule type
        2. return component name
    """
    result = list()
    if paths:
        # In this case, rel is a list of relatioships in the path.
        path = list()
        for i in rel:
            if include_start and i.get('first', False):
                path.append(nav_decorate_gather_components(i, direction, return_names, True, xule_context))
            path.append(nav_decorate_gather_components(i, direction, return_names, False, xule_context))
        result.append(path)
    else:
        if rel is not None:
            if include_start and rel.get('first', False): 
                result.append(nav_decorate_gather_components(rel, direction, return_names, True, xule_context))
            result.append(nav_decorate_gather_components(rel, direction, return_names, False, xule_context))
    
    return result

def get_return_component_names(nav_expr, xule_context):
    component_names = list()
    
    if 'return' in nav_expr:
        if 'returnComponents' in nav_expr['return']:
            for component in nav_expr['return']['returnComponents']:
                if isinstance(component, dict):
                    #This is an expression which should evluate to a qname. This is an arc attribute name.
                    component_name_value = evaluate(component, xule_context)
                    if component_name_value.type != 'qname':
                        raise XuleProcessingError(_("Expression in return components of a navigate expression did not evaluate to a qname. Expecting a qname for the name of a arc attribute. Found {}").format(component_name_value.type), xule_context)
                    component_names.append(component_name_value.value)
                else:
                    component_names.append(component)
        else:
            component_names.append('target')
    else:
        component_names.append('target')
    return component_names
    
    #nav_expr.get('return', {'returnComponents': ('target',)}).get('returnComponents', ('target',))

def nav_decorate_gather_components(rel, direction, component_names, is_start, xule_context):
    """Get the values for all the return components for a relationship.
    
    Arguments:
        rel (dict): A dition of the relationship and additional information from the traversal
        direction (string): 'up' or 'down'. Direction of the traversal
        component_names (list of strings): The list of return components to get for the relationship.
        is_start (boolean): Indicates if the relationship should be treated as a starting relationship. This is used if the 'include start' keyword is
                            is included in the navigation expression and the relationship is from the start of the navigation. In this case there is
                            an extra result for the relationships for the starting concept.
        xule_context (XuleRuleContext): The processing context.
    Returns:
        A tupple of return component values. Each value is a tuple of:
            1. component value
            2. xule type for the value
            3. component name (used for ease of debugging)
    """
    result = list()
    
    for component_name in component_names:
        if component_name == 'result-order':
            result.append('result-order') # This will be handled in the finishing step
        else:
            result.append(nav_decorate_component_value(rel, direction, component_name, is_start, xule_context))
    return result

def nav_decorate_component_value(rel, direction, component_name, is_start, xule_context):
    """Get the return component value for a relationship and a single return component.
    
    Arguments:
        rel (dict): A dition of the relationship and additional information from the traversal
        direction (string): 'up' or 'down'. Direction of the traversal
        component_name (string): Component name
        is_start (boolean): Indicates if the relationship should be treated as a starting relationship. This is used if the 'include start' keyword is
                            is included in the navigation expression and the relationship is from the start of the navigation. In this case there is
                            an extra result for the relationships for the starting concept.
        xule_context (XuleRuleContext): The processing context.
    Returns:
        A tuple of:
            1. component value
            2. xule type for the value
            3. component name (used for ease of debugging)
    """   
    
    if component_name in NAVIGATE_RETURN_COMPONENTS:
        if rel is None:
            return (None, 'none', component_name)
        
        if NAVIGATE_RETURN_COMPONENTS[component_name][NAVIGATE_ALLOWED_ON_START]:
            if rel is None:
                return (None, 'none', componend_name)
            else:
                return NAVIGATE_RETURN_COMPONENTS[component_name][NAVIGATE_RETURN_FUCTION](rel, direction, component_name, is_start, xule_context)
        else:
            if is_start:
                return(None, 'none', component_name)
            else:
                if rel is None:
                    return (None, 'none', component_name)
                else:
                    return NAVIGATE_RETURN_COMPONENTS[component_name][NAVIGATE_RETURN_FUCTION](rel, direction, component_name, xule_context)
    else:
        # Could be an arc attribute name (qname)
        if isinstance(component_name, QName):
            if rel is None:
                return (None, 'none', component_name)
            else:
                attribute_value = rel[component_name]
                if attribute_value is None:
                    return (None, 'none', component_name)
                else:
                    return (attribute_value, 'string', component_name)
        else:
            raise XuleProcessingError(_("Component {} is not currently supported.".format(component_name)), xule_context)        

def nav_decorate_component_target(rel, direction, component_name, is_start, xule_context):     
    if is_start:
        # If it is the start concept, then get the opposide side of the relationship. 
        if component_name == 'target':
            if direction == 'up':
                return (rel['relationship'].toModelObject, 'concept', component_name)
            else:
                return (rel['relationship'].fromModelObject, 'concept', component_name)
        elif component_name == 'target-name':
            if direction == 'up':
                return (rel['relationship'].toModelObject.qname, 'qname', component_name)
            else:
                return (rel['relationship'].fromModelObject.qname, 'qname', component_name)            
    else:
        if component_name == 'target':
            if direction == 'up':
                return (rel['relationship'].fromModelObject, 'concept', component_name)
            else:
                return (rel['relationship'].toModelObject, 'concept', component_name)
        if component_name == 'target-name':
            if direction == 'up':
                return (rel['relationship'].fromModelObject.qname, 'qname', component_name)
            else:
                return (rel['relationship'].toModelObject.qname, 'qname', component_name)            

def nav_decorate_component_source(rel, direction, component_name, xule_context): 

    if component_name == 'source':
        if direction == 'up':
            return (rel['relationship'].toModelObject, 'concept', component_name)
        else:
            return (rel['relationship'].fromModelObject, 'concept', component_name)
    elif component_name == 'source-name':
        if direction == 'up':
            return (rel['relationship'].toModelObject.qname, 'qname', component_name)
        else:
            return (rel['relationship'].fromModelObject.qname, 'qname', component_name) 
            
def nav_decorate_component_order(rel, direction, component_name, xule_context):
    return (rel['relationship'].orderDecimal, 'decimal', component_name)

def nav_decorate_component_weight(rel, direction, component_name, xule_context):
    if rel['relationship'].weightDecimal is None:
        return (None, 'none', component_name)
    else:
        return (rel['relationship'].weightDecimal, 'decimal', component_name)

def nav_decorate_component_preferred_label_role(rel, direction, component_name, xule_context):
    if rel['relationship'].preferredLabel is not None:
        return (rel['relationship'].preferredLabel, 'uri', component_name)
    else:
        return (None, 'none', component_name)  

def nav_decorate_component_preferred_label(rel, direction, component_name, xule_context): 
    if rel['relationship'].preferredLabel is not None:
        label = get_label(xule_context, rel['relationship'].toModelObject, rel['relationship'].preferredLabel, None)
        if label is None:
            return (None, 'none', component_name)
        else:
            return (label, 'label', component_name)
    else:
        return (None, 'none', component_name)
    
def nav_decorate_component_relationship(rel, direction, component_name, xule_context):
    return (rel['relationship'], 'relationship', component_name)

def nav_decorate_component_role(rel, direction, component_name, xule_context):
    role = get_role(rel['relationship'], xule_context)
    return (role, 'role', component_name)

def get_role(relationship, xule_context):
    role_uri = relationship.linkrole
    if role_uri in xule_context.model.roleTypes:
        return xule_context.model.roleTypes[role_uri][0]
    else:
        return XuleRole(role_uri)

def nav_decorate_component_role_uri(rel, direction, component_name, xule_context):
    role_uri = rel['relationship'].linkrole

    return (role_uri, 'uri', component_name)

def nav_decorate_component_role_description(rel, direction, component_name, xule_context):
    role = get_role(rel['relationship'], xule_context)
    
    return (role.definition, 'string', component_name)

def nav_decorate_component_arcrole(rel, direction, component_name, xule_context):
    arcrole = get_arcrole(rel['relationship'], xule_context)
    return (arcrole, 'arcrole', component_name)

def get_arcrole(relationship, xule_context):
    arcrole_uri = relationship.arcrole
    if arcrole_uri in xule_context.model.arcroleTypes:
        return xule_context.model.arcroleTypes[arcrole_uri][0]
    else:
        return XuleArcrole(arcrole_uri)

def nav_decorate_component_arcrole_uri(rel, direction, component_name, xule_context):
    return (rel['relationship'].arcrole, 'uri', component_name)

def nav_decorate_component_arcrole_description(rel, direction, component_name, xule_context):
    arcrole = get_arcrole(rel['relationship'], xule_context)
    return (arcrole.definition, 'string', component_name)

def nav_decorate_component_cycles_allowed(rel, direction, component_name, xule_context):
    arcrole = get_arcrole(rel['relationship'], xule_context)
    return (arcrole.cyclesAllowed, 'string', component_name)

def nav_decorate_component_link_name(rel, direction, component_name, xule_context):
    return (rel['relationship'].linkQname, 'qname', component_name)

def nav_decorate_component_arc_name(rel, direction, component_name, xule_context):
    return (rel['relationship'].qname, 'qname', component_name)

def nav_decorate_component_network(rel, direction, component_name, xule_context):
    return (rel['network'], 'network', component_name)

def get_network_info(network, xule_context):
    network_info = (network.arcrole, network.linkrole, network.arcqname, network.linkqname, False)
    return (network_info, network)

def nav_decorate_component_cycle(rel, direction, component_name, xule_context):
    return (rel.get('cycle', False), 'bool', component_name)

def nav_decorate_component_navigation_order(rel, direction, component_name, is_start, xule_context):
    if is_start:
        return(0, 'int', component_name)
    else:
        return (rel['navigation-order'], 'int', component_name)

def nav_decorate_component_navigation_depth(rel, direction, component_name, is_start, xule_context):
    if is_start:
        return (0, 'int', component_name)
    else:
        return (rel['navigation-depth'], 'int', component_name)

def nav_decorate_component_result_order(rel, direction, component_name, is_start, xule_context):
    if is_start:
        return (0, 'int', component_name)
    else:
        return (rel['result-order'], 'int', component_name)

def nav_decorate_component_drs_role(rel, direction, component_name, is_start, xule_context):
    #if hasattr(rel['relationship'], 'dimension_set'):
    if isinstance(rel['relationship'], DimensionRelationship):
        return (rel['relationship'].dimension_set.drs_role, 'uri', component_name)
    else:
        return (None, 'none', component_name)    
    
def nav_decorate_component_dimension_type(rel, direction, component_name, is_start, xule_context):
    if isinstance(rel['relationship'], DimensionRelationship):
        if (is_start and direction == 'down') or (not is_start and direction == 'up'):
            dim_type = rel['relationship'].fromDimensionType
        else:
            dim_type = rel['relationship'].toDimensionType
        
        if dim_type is None:
            return (None, 'none', component_name)
        else:
            return (dim_type, 'string', component_name)
    else:
        return (None, 'none', component_name)
            
def nav_decorate_component_dimension_sub_type(rel, direction, component_name, is_start, xule_context):
    if isinstance(rel['relationship'], DimensionRelationship):
        if (is_start and direction == 'down') or (not is_start and direction == 'up'):
            dim_type = rel['relationship'].fromDimensionSubType
        else:
            dim_type = rel['relationship'].toDimensionSubType
        
        if dim_type is None:
            return (None, 'none', component_name)
        else:
            return (dim_type, 'string', component_name)
    else:
        return (None, 'none', component_name)

def nav_decorate_component_usable(rel, direction, component_name, is_start, xule_context):
    if isinstance(rel['relationship'], DimensionRelationship):
        if (is_start and direction == 'down') or (not is_start and direction == 'up'):
            concept = rel['relationship'].fromModelObject
        else:
            concept = rel['relationship'].toModelObject
        
        if rel['relationship'].dimension_set.isUsable(concept) is None:
            return (None, 'none', component_name)
        else:
            return (rel['relationship'].dimension_set.isUsable(concept), 'bool', component_name)
    else:
        return (None, 'none', component_name)

# Navigation return component tuple locations
NAVIGATE_RETURN_FUCTION = 0
NAVIGATE_ALLOWED_ON_START = 1

NAVIGATE_RETURN_COMPONENTS = {'source': (nav_decorate_component_source, False),
                              'source-name': (nav_decorate_component_source, False),
                              'target': (nav_decorate_component_target, True),
                              'target-name': (nav_decorate_component_target, True),
                              'order': (nav_decorate_component_order, False),
                              'weight': (nav_decorate_component_weight, False),
                              'preferred-label-role': (nav_decorate_component_preferred_label_role, False),
                              'preferred-label': (nav_decorate_component_preferred_label, False),
                              'relationship': (nav_decorate_component_relationship, False),
                              'role': (nav_decorate_component_role, False),
                              'role-uri': (nav_decorate_component_role_uri, False),
                              'role-description': (nav_decorate_component_role_description, False),
                              'arcrole': (nav_decorate_component_arcrole, False),
                              'arcrole-uri': (nav_decorate_component_arcrole_uri, False),
                              'arcrole-description': (nav_decorate_component_arcrole_description, False),
                              'arcrole-cycles-allowed': (nav_decorate_component_cycles_allowed, False),
                              'link-name': (nav_decorate_component_link_name, False),
                              'arc-name': (nav_decorate_component_arc_name, False),
                              'network': (nav_decorate_component_network, False),
                              'cycle': (nav_decorate_component_cycle, False),
                              'navigation-order': (nav_decorate_component_navigation_order, True),
                              'navigation-depth': (nav_decorate_component_navigation_depth, True),
                              'result-order': (nav_decorate_component_result_order, True),
                              'drs-role': (nav_decorate_component_drs_role, True),
                              'dimension-type': (nav_decorate_component_dimension_type, True),
                              'dimension-sub-type': (nav_decorate_component_dimension_sub_type, True),
                              'usable': (nav_decorate_component_usable, True),
                              }


def nav_finish_results(nav_expr, return_items, add_result_order, xule_context):
    """Format the results of navigation.
    
    This function processes the list of results and puts them in their final form.
    The options for the final forma are if the results are:
     1. a list of relationships
     2. a set of relations
     3. a dictionary organzed by network of relationships
     4. a nested list of paths of the traversal. The outer list is a path and the inner list contains the relationships that make up the path.

    Arguments:
        nav_expr (dictionary): The navigation expression AST node
        return_items (list): The list of the decorated return items. 
        add_result_order (bool): An indicator if the result order should be added to the results. This is calculated as the return_items are processed.
        xule_context (XuleRuleContext): The processing context.
        
    Returns a XuleValue which is the final result of the navigation.
    """

    if nav_expr.get('return', dict()).get('byNetwork', False):
        by_network = dict()
        by_network_shadow = dict()
        for network, network_return_items in return_items.items():
            processed_items = nav_finish_return_items(nav_expr, network_return_items, add_result_order, xule_context)
            by_network[XuleValue(xule_context, network, 'network')] = processed_items
            by_network_shadow[network] = processed_items.shadow_collection
        return XuleValue(xule_context, frozenset(by_network.items()), 'dictionary', shadow_collection=frozenset(by_network_shadow.items()))
    else:
        return nav_finish_return_items(nav_expr, return_items, add_result_order, xule_context)
    
def nav_finish_return_items(nav_expr, return_items, add_result_order, xule_context):
    paths = nav_expr.get('return',dict()).get('paths', False)
    
    if 'return' in nav_expr:
        return_type = nav_expr['return'].get('returnType', 'list')
    else:
        return_type = 'list'
    
    # The return_component_type determins if the return concompents are a list or a dictionary keyed by the component name.
    return_component_type = nav_expr.get('return',dict()).get('returnComponentType', 'list')

    cur_order = 1
    
    final_results = list()
    final_shadow = list()
    
    def handle_return_item(return_item, cur_order):
        
        if add_result_order:
            # replace reuslt-order
            return_item = [x if x != 'result-order' else (cur_order, 'int', 'result-order') for x in return_item]
            #return_item.append((cur_order, 'int', 'result-order'))
            cur_order += 1
        
        if return_component_type == 'list':
            if len(return_item) == 1:
                # A list of single items is returned. 
                # The return item only has one return component
                return XuleValue(xule_context, return_item[0][0], return_item[0][1]), return_item[0][0], cur_order
#             
#                 if return_type == 'list' or (return_type == 'set' and return_item[0][0] not in results_shadow):
#                     if return_component_type == 'list':
#                         results.append(XuleValue(xule_context, return_item[0][0], return_item[0][1]))
#                         results_shadow.append(return_item[0][0])
            else:
                # A list of list of components is returned.
                # The return_item has multiple return componenets
                multi_result = list()
                multi_shadow = list()
                for return_component in return_item:
                    multi_result.append(XuleValue(xule_context, return_component[0], return_component[1]))
                    multi_shadow.append(return_component[0])
                multi_shadow_tuple = tuple(multi_shadow)
                
                return XuleValue(xule_context, tuple(multi_result), 'list', shadow_collection=tuple(multi_shadow)), tuple(multi_shadow_tuple), cur_order
                
#                 if return_type == 'list' or (return_type == 'set' and  multi_shadow_tuple not in results_shadow):
#                     results.append(XuleValue(xule_context, tuple(multi_result), 'list', shadow_collection=tuple(multi_shadow)))
#                     results_shadow.append(multi_shadow_tuple)
        else: # the return_component_type is a dictionary
            multi_result = dict()
            multi_shadow = dict()
            for return_component in return_item:
                multi_result[XuleValue(xule_context, return_component[2], 'string')] = XuleValue(xule_context, return_component[0], return_component[1])
                multi_shadow[return_component[2]] = return_component[0]
            
            return XuleValue(xule_context, frozenset(multi_result.items()), 'dictionary'), frozenset(multi_shadow.items()), cur_order
#         
#             if return_type == 'list' or (return_type == 'set' and frozenset(multi_shadow.items()) not in results_shadow):
#                 results.append(XuleValue(xule_context, frozenset(multi_result.items()), 'dictionary'))
#                 results_shadow.append(frozenset(multi_shadow.items()))
# 
#         return results, results_shadow
    
    for return_item in return_items:
        if paths:
            path_result = list()
            path_shadow = list()
            # The return item is a list of the items that make up a path. Process each item in the path.
            for path_item in return_item:
                path_item_result, path_item_shadow, cur_order = handle_return_item(path_item, cur_order)
                path_result.append(path_item_result)
                path_shadow.append(path_item_shadow)
            # Now the path is complete
            item_result = XuleValue(xule_context, tuple(path_result), 'list', shadow_collection=tuple(path_shadow))
            item_shadow = tuple(path_shadow)

        else:
            item_result, item_shadow, cur_order = handle_return_item(return_item, cur_order)
            
        if return_type == 'list':
            final_results.append(item_result)
            final_shadow.append(item_shadow)
        else: # Set
            if item_shadow not in final_shadow:
                final_results.append(item_result)
                final_shadow.append(item_shadow)
            
    if return_type == 'list':
        return XuleValue(xule_context, tuple(final_results), 'list', shadow_collection=tuple(final_shadow))
    else:
        return XuleValue(xule_context, frozenset(final_results), 'set', shadow_collection=frozenset(final_shadow))    

def evaluate_function_ref(function_ref, xule_context):
    if function_ref['functionName'] in BUILTIN_FUNCTIONS:
        function_info = BUILTIN_FUNCTIONS.get(function_ref['functionName'])
        if function_info[FUNCTION_TYPE] == 'aggregate':
            return evaluate_aggregate_function(function_ref, function_info, xule_context)
        elif function_info[FUNCTION_TYPE] == 'regular':
            return regular_function(xule_context, function_ref, function_info)
        else:
            raise XuleProcessingError(_("Unknown function type '{}'.".format(function_info[FUNCTION_TYPE])), xule_context)
    elif function_ref['functionName'] in XuleProperties.PROPERTIES:
        return property_as_function(xule_context, function_ref)
    else:
        #xule defined function
        return user_defined_function(xule_context, function_ref)

def property_as_function(xule_context, function_ref):
    """Evaluate a function that is a property.
    
    Some functions are just a function version of a property. In these cases, the first argument is the object of the property and the rest of the args are
    arguments to the property. 
    
    Example:
        -10.abs is the same as abs(-10)
    """
    # Get the property information
    property_info = XuleProperties.PROPERTIES[function_ref['functionName']]
    
    # Check that there is at least one argument. This is the property object
    if len(function_ref['functionArgs']) == 0:
        raise XuleProcessingError(_("The '{}' function must have at least one argumenrt, found none.".format(function_ref['functionName'])), xule_context)
    
    # Check that the first argument is the right type
    property_object = evaluate(function_ref['functionArgs'][0], xule_context)
    
    if len(property_info[XuleProperties.PROP_OPERAND_TYPES]) > 0:
        if not (property_object.type in property_info[XuleProperties.PROP_OPERAND_TYPES] or
                property_object.is_fact and 'fact' in property_info[XuleProperties.PROP_OPERAND_TYPES] or
                any([xule_castable(property_object, allowable_type, xule_context) for allowable_type in property_info[XuleProperties.PROP_OPERAND_TYPES]])):
    
            raise XuleProcessingError(_("The first argument of function '{}' must be {}, found '{}'.".format(function_ref['functionName'],
                                                                                                                                     ', '.join(property_info[XuleProperties.PROP_OPERAND_TYPES]),
                                                                                                                                     property_object.type)), xule_context)
    
    
    if property_info[XuleProperties.PROP_ARG_NUM] is not None:
        property_args = function_ref['functionArgs'][1:]
        if property_info[XuleProperties.PROP_ARG_NUM] >= 0 and len(property_args) != property_info[XuleProperties.PROP_ARG_NUM]:
            raise XuleProcessingError(_("Property '%s' must have %s arguments. Found %i." % (function_ref['functionName'],
                                                                                             property_info[XuleProperties.PROP_ARG_NUM],
                                                                                             len(property_args))), 
                                      xule_context)
        elif len(property_args) > property_info[XuleProperties.PROP_ARG_NUM] * -1 and property_info[XuleProperties.PROP_ARG_NUM] < 0:
            raise XuleProcessingError(_("Property '%s' must have no more than %s arguments. Found %i." % (function_ref['functionName'],
                                                                                             property_info[XuleProperties.PROP_ARG_NUM] * -1,
                                                                                             len(property_args))), 
                                      xule_context)
    #prepare the arguments
    arg_values = []
    for arg_expr in property_args:
        arg_value = evaluate(arg_expr, xule_context)
        arg_values.append(arg_value)
    
    if len(property_info) > 4:
        return property_info[XuleProperties.PROP_FUNCTION](xule_context, property_object, property_info[XuleProperties.PROP_DATA], *arg_values)
    else:
        return property_info[XuleProperties.PROP_FUNCTION](xule_context, property_object, *arg_values)
    
def regular_function(xule_context, function_ref, function_info):
        if function_info[FUNCTION_ARG_NUM] >= 0:
            if function_info[FUNCTION_TYPE] == 'regular' and len(function_ref['functionArgs']) != function_info[FUNCTION_ARG_NUM]:
                raise XuleProcessingError(_("The '%s' function must have only %i argument, found %i." % (function_ref['functionName'], 
                                                                                               function_info[FUNCTION_ARG_NUM],
                                                                                               len(function_ref['functionArgs']))), xule_context)
        else:
            # The fucntion may have a variable number of arguments.
            if function_info[FUNCTION_TYPE] == 'regular' and len(function_ref['functionArgs']) > (function_info[FUNCTION_ARG_NUM] * -1):
                raise XuleProcessingError(_("The '%s' function must have no more than %i arguments, found %i." % (function_ref['functionName'], 
                                                                                               function_info[FUNCTION_ARG_NUM] * -1,
                                                                                               len(function_ref['functionArgs']))), xule_context)                
            
        function_args = []
        for function_arg in function_ref['functionArgs']:
        #for i in range(len(function_ref.functionArgs)):
            if function_info[FUNCTION_ALLOW_UNBOUND_ARGS]:
                try:
                    arg = evaluate(function_arg, xule_context)
                except XuleIterationStop as xis:
                    arg = xis.stop_value
            else:
                arg = evaluate(function_arg, xule_context)
                          
            function_args.append(arg)

        return function_info[FUNCTION_EVALUATOR](xule_context, *function_args)

def user_defined_function(xule_context, function_ref):
    #check fucntion cache - The function cache is very basic. It only caches on functions that have no args.
    if len(function_ref['functionArgs']) == 0 and function_ref['functionName'] in xule_context.global_context.function_cache:
        return xule_context.global_context.function_cache[function_ref['functionName']]                

    function_info = xule_context.find_function(function_ref['functionName'])
    if function_info is None:
        raise XuleProcessingError("Function '%s' not found" % function_ref['functionName'], xule_context)
    else:
        #Get the list of variables and their values. This will put the current single value for the variable as an argument
        for var_ref in sorted(function_ref['var_refs'], key=lambda x: x[1]):
            '''NOT SURE THIS IS NEEDED. THE ARGUMENTS WILL BE EXVALUTED WHEN THE for arg in matched_args IS PROCESSED'''
            #0 = var declaration id, 1 = var name, 2 = var_ref, 3 = var type (1 = var/arg, 2 = constant)
            var_value = evaluate(var_ref[2], xule_context)
                        
        matched_args = match_function_arguments(function_ref, function_info['function_declaration'], xule_context)
        for arg in matched_args:
            try:
                arg_value = evaluate(arg['expr'], xule_context)
            except XuleIterationStop as xis:
                arg_value = xis.stop_value
            xule_context.add_arg(arg['name'],
                                 arg['node_id'],
                                 arg['tagged'],
                                 arg_value,
                                 'single')            

        #add the node_id of the function reference to the prefix used for calculating the processing node id
        #This is done before adding the args so the id prefix is set with the function delcaration id before the args are added as varaiables.
        xule_context.id_prefix.append(function_ref['node_id'])
        
        body_expr = function_info['function_declaration']['body']
        save_aligned_result_only = xule_context.aligned_result_only
                
        def cleanup_function():
            #remove the args
            for arg in matched_args:
                xule_context.del_arg(arg['name'],
                                     arg['node_id'])

            #pop the function reference node id off the prefix
            xule_context.id_prefix.pop()    
            #reset the aligned only results.
            xule_context.aligned_result_only = save_aligned_result_only
            #xule_context.used_expressions = save_used_expressions    
        

        function_result_values = isolated_evaluation(xule_context,
                                                     function_info['function_declaration']['node_id'], 
                                                     body_expr, 
                                                     cleanup_function=cleanup_function #, 
                                                     #iteration_reset_function=iteration_reset,
                                                     )
        if 'is_iterable' in function_ref:
            function_results = function_result_values
        else:
            if None in function_result_values.values:
                function_results = function_result_values.values[None][0]
            else:
                function_results = XuleValue(xule_context, None, 'unbound')
        
        #Cache fucntion results that don't have any arguments.
        if len(function_ref['functionArgs']) == 0:
            xule_context.global_context.function_cache[function_ref['functionName']] = function_results
#             if function_ref.get('cacheable') == True:
#                 xule_context.global_context.function_cache[cache_key] = function_results
#             
        return function_results
         
def isolated_evaluation(xule_context, node_id, expr, setup_function=None, cleanup_function=None, iteration_reset_function=None):
    save_aligned_result_only = xule_context.aligned_result_only
    save_used_expressions = xule_context.used_expressions
    #pre_aggregation_table_list_size = len(xule_context.iteration_table)
    isolated_table = xule_context.iteration_table.add_table(node_id, xule_context.get_processing_id(node_id), is_aggregation=True)
    try:
        if setup_function is not None:
            setup_function()   
        
        return_values = XuleValueSet()
    
        while True:
            xule_context.aligned_result_only = False
            xule_context.used_expressions = set()
            try:
                return_value = evaluate(expr, xule_context) #, glob_cache_key=body_expr['node_id'] if len(matched_args)==0 else None)
            except XuleIterationStop as xis:
                return_value = xis.stop_value #XuleValue(xule_context, None, 'unbound')                           

            return_value.facts = xule_context.facts
            return_value.tags = xule_context.tags
            return_value.aligned_result_only = xule_context.aligned_result_only
            return_value.used_expressions = xule_context.used_expressions
            return_value.alignment = xule_context.iteration_table.current_table.current_alignment
            #return_value.alignment = isolated_table.current_alignment
            return_values.append(return_value)
    
            #xule_context.iteration_table.del_current()
            xule_context.iteration_table.next(isolated_table.table_id)
            if iteration_reset_function is not None:
                iteration_reset_function()
            #if len(xule_context.iteration_table) == pre_aggregation_table_list_size:
            if isolated_table.is_empty:
                break
    finally:
        #ensure that the isolated table is removed if there is an exception.
        xule_context.iteration_table.del_table(isolated_table.table_id)
        #reset the aligned only results.
        xule_context.aligned_result_only = save_aligned_result_only
        xule_context.used_expressions = save_used_expressions
        if cleanup_function is not None:
            cleanup_function()
        
    return return_values

def evaluate_aggregate_function(function_ref, function_info, xule_context):
#     if function_ref.functionName.lower() in ('count', 'sum', 'all'):
#         return evaluate_aggregate_function_concurrent(function_ref, function_info, xule_context)
    
    values_by_alignment = collections.defaultdict(list)
    facts_by_alignment = collections.defaultdict(collections.OrderedDict)
    aligned_result_only = False 
    save_aligned_result_only = xule_context.aligned_result_only
    used_expressions = set()
    save_used_expressions = xule_context.used_expressions
    for function_arg in function_ref['functionArgs']:
        #pre_aggregation_table_list_size = len(xule_context.iteration_table)
        aggregation_table = xule_context.iteration_table.add_table(function_ref['node_id'], xule_context.get_processing_id(function_ref['node_id']), is_aggregation=True)
        try:
            while True:
                xule_context.aligned_result_only = False
                xule_context.used_expressions = set()
                arg = XuleValue(xule_context, None, 'unbound')
                try:
                    arg = evaluate(function_arg, xule_context)
                except XuleIterationStop:
                    pass

                if arg.tags is None:
                    arg.tags = xule_context.iteration_table.tags
                else:
                    arg.tags.update(xule_context.iteration_table.tags)
                if arg.facts is None:
                    arg.facts = xule_context.iteration_table.facts
                else:
                    arg.facts.update(xule_context.iteration_table.facts)                
                
                if arg.type == 'unbound':
                    values_by_alignment[None].append(arg)
                else:
                    values_by_alignment[xule_context.iteration_table.current_table.current_alignment].append(arg)
                    
                aligned_result_only = aligned_result_only or xule_context.aligned_result_only
                used_expressions.update(set(xule_context.used_expressions)) 
                
                xule_context.iteration_table.next(function_ref['node_id'])
                if aggregation_table.is_empty:
                    break

        finally:
            xule_context.aligned_result_only = save_aligned_result_only 
            xule_context.used_expressions = save_used_expressions
            
            #ensure the aggregation table is removed in the event of an exception.
            xule_context.iteration_table.del_table(aggregation_table.table_id)
    
    agg_values = XuleValueSet()
    
    #add default value if there are no None aligned results and the aggregation has a default value.
    if None not in values_by_alignment and function_info[FUNCTION_DEFAULT_VALUE] is not None:
        agg_values.append(XuleValue(xule_context, function_info[FUNCTION_DEFAULT_VALUE], function_info[FUNCTION_DEFAULT_TYPE]))
            
    for alignment in values_by_alignment:
        values = [x for x in values_by_alignment[alignment] if x.type != 'unbound']
        
        if len(values) > 0:
            agg_value = function_info[FUNCTION_EVALUATOR](xule_context, values)
        else:
            if function_info[FUNCTION_DEFAULT_VALUE] is not None:
                agg_value = XuleValue(xule_context, function_info[FUNCTION_DEFAULT_VALUE], function_info[FUNCTION_DEFAULT_TYPE])
            else:
                agg_value = None
        
        if agg_value is not None:
            agg_value.alignment = alignment
            agg_value.aligned_result_only = aligned_result_only
            #print("agg", function_ref['exprName'], function_ref['node_id'], len(xule_context.used_expressions), len(used_expressions))
            agg_value.used_expressions = used_expressions
            agg_values.append(agg_value)

    return agg_values

def evaluate_aggregate_function_concurrent(function_ref, function_info, xule_context):
    values_by_alignment = collections.defaultdict(list)
    agg_result_by_alignment = collections.defaultdict(lambda: None)
    facts_by_alignment = collections.defaultdict(collections.OrderedDict)
    tags_by_alignment = collections.defaultdict(dict)
    aligned_result_only = False 
    save_aligned_result_only = xule_context.aligned_result_only
    used_expressions = set()
    save_used_expressions = xule_context.used_expressions   

    if function_ref.functionName.lower() == 'count':
        concurrent_function = XuleFunctions.agg_count_concurrent
    elif function_ref.functionName.lower() == 'sum':
        concurrent_function = XuleFunctions.agg_sum_concurrent
    elif function_ref.functionName.lower() == 'all':
        concurrent_function = XuleFunctions.agg_all_concurrent        

    for i in range(len(function_ref.functionArgs)):
        #pre_aggregation_table_list_size = len(xule_context.iteration_table)
        aggregation_table = xule_context.iteration_table.add_table(function_ref['node_id'], xule_context.get_processing_id(function_ref['node_id']), is_aggregation=True)
        try:
            while True:     
                xule_context.aligned_result_only = False
                xule_context.used_expressions = set()
                try:
                    arg = evaluate(function_ref.functionArgs[i][0], xule_context)
                except XuleIterationStop as xis:
                    arg = xis.stop_value

                arg_alignment = xule_context.iteration_table.current_table.current_alignment
                tags_by_alignment[arg_alignment].update(xule_context.iteration_table.tags)
#                 if arg.tags is not None:
#                     tags_by_alignment[arg_alignment].update(arg.tags)

                facts_by_alignment[arg_alignment].update(xule_context.iteration_table.facts)
#                 if arg.facts is not None:
#                     facts_by_alignment[arg_alignment].update(arg.facts)


                if arg.type != 'unbound':                    
                    agg_result_by_alignment[arg_alignment] = concurrent_function(xule_context, 
                                                                                 agg_result_by_alignment[arg_alignment], 
                                                                                 arg, 
                                                                                 arg_alignment)
                    
                aligned_result_only = aligned_result_only or xule_context.aligned_result_only
                used_expressions.update(set(xule_context.used_expressions)) 
                
                xule_context.iteration_table.next(function_ref['node_id'])
                if aggregation_table.is_empty:
                    break

        finally:
            xule_context.aligned_result_only = save_aligned_result_only 
            xule_context.used_expressions = save_used_expressions
            
            #ensure the aggregation table is removed in the event of an exception.
            xule_context.iteration_table.del_table(aggregation_table.table_id)
            
    agg_values = XuleValueSet()
    
    #add default value if there are no None aligned results and the aggregation has a default value.
    if None not in agg_result_by_alignment and function_info[FUNCTION_DEFAULT_VALUE] is not None:
        agg_values.append(XuleValue(xule_context, function_info[FUNCTION_DEFAULT_VALUE], function_info[FUNCTION_DEFAULT_TYPE]))
            
    for alignment, agg_value in agg_result_by_alignment.items():
        #agg_value.alignment = alignment
        agg_value.aligned_result_only = aligned_result_only
        #print("agg", function_ref['exprName'], function_ref['node_id'], len(xule_context.used_expressions), len(used_expressions))
        agg_value.used_expressions = used_expressions
        agg_value.tags = tags_by_alignment[alignment]
        agg_value.facts = facts_by_alignment[alignment]
        agg_values.append(agg_value)

    return agg_values

def evaluate_property(property_expr, xule_context):
    
    # The object_value is the left side of the property expression
    object_value = evaluate(property_expr['expr'], xule_context)
        
    #The properties expression is an object and then a chain of properties (i.e. Assets[]::concept::name::local-part)
    for current_property_expr in property_expr['properties']:
        #Check that this is a valid property
        if current_property_expr['propertyName'] not in XuleProperties.PROPERTIES:
            raise XuleProcessingError(_("'%s' is not a valid property." % current_property_expr['propertyName']), xule_context)
        
        property_info = XuleProperties.PROPERTIES[current_property_expr['propertyName']]
        
        #Check if the property can operate on a set or list. 
        if object_value.type not in ('set', 'list') or (object_value.type in ('set', 'list') and len({'set', 'list'} & set(property_info[XuleProperties.PROP_OPERAND_TYPES])) > 0): 
            pass
            object_value = process_property(current_property_expr, object_value, property_info, xule_context)
        else:
            # This is a set or list. The property is not for a set or list, so try to create a new set or list after applying the property to the members.
            if object_value.type == 'set':
                new_list = set()
                new_shadow = set()
            else:
                new_list = list()
                new_shadow = list()
            for item in object_value.value:
                new_value = process_property(current_property_expr, item, property_info, xule_context)
                if object_value.type == 'set':
                    if (new_value.shadow_collection if new_value.type in ('set', 'list', 'dictionary') else new_value.value) not in new_shadow:
                        new_list.add(new_value)
                        new_shadow.add(new_value.shadow_collection if new_value.type in ('set', 'list', 'dictionary') else new_value.value)
                else: #list
                    new_list.append(new_value)
                    new_shadow.append(new_value.shadow_collection if new_value.type in ('set', 'list', 'dictionary') else new_value.value)
                
            if object_value.type == 'set':
                object_value = XuleValue(xule_context, frozenset(new_list), 'set', shadow_collection=frozenset(new_shadow))
            else: #list
                object_value = XuleValue(xule_context, tuple(new_list), 'list', shadow_collection=frozenset(new_shadow))
                
    return object_value
                
def process_property(current_property_expr, object_value, property_info, xule_context):
    #Check that the left object is the right type
    #if the left object is unbound then return unbound
    if not property_info[XuleProperties.PROP_UNBOUND_ALLOWED] and object_value.type in ('unbound', 'none'):
        return object_value
    else:
        #check the left object is the right type
        if len(property_info[XuleProperties.PROP_OPERAND_TYPES]) > 0:
            if not (object_value.type in property_info[XuleProperties.PROP_OPERAND_TYPES] or
                    object_value.is_fact and 'fact' in property_info[XuleProperties.PROP_OPERAND_TYPES] or
                    any([xule_castable(object_value, allowable_type, xule_context) for allowable_type in property_info[XuleProperties.PROP_OPERAND_TYPES]]) or
                    (object_value.type in ('none', 'unbound') and property_info[XuleProperties.PROP_UNBOUND_ALLOWED])):
                #print(current_property_expr['node_id'])
                raise XuleProcessingError(_("Property '%s' is not a property of a '%s'.") % (current_property_expr['propertyName'],
                                                                                             object_value.type), 
                                          xule_context) 
    
    #property_info = XuleProperties.PROPERTIES[current_property_expr['propertyName']]

    if property_info[XuleProperties.PROP_ARG_NUM] is not None:
        property_args = current_property_expr.get('propertyArgs', [])
        if property_info[XuleProperties.PROP_ARG_NUM] >= 0 and len(property_args) != property_info[XuleProperties.PROP_ARG_NUM]:
            raise XuleProcessingError(_("Property '%s' must have %s arguments. Found %i." % (current_property_expr['propertyName'],
                                                                                             property_info[XuleProperties.PROP_ARG_NUM],
                                                                                             len(property_args))), 
                                      xule_context)
        elif len(property_args) > property_info[XuleProperties.PROP_ARG_NUM] * -1 and property_info[XuleProperties.PROP_ARG_NUM] < 0:
            raise XuleProcessingError(_("Property '%s' must have no more than %s arguments. Found %i." % (current_property_expr['propertyName'],
                                                                                             property_info[XuleProperties.PROP_ARG_NUM] * -1,
                                                                                             len(property_args))), 
                                      xule_context)
    #prepare the arguments
    arg_values = []
    for arg_expr in property_args:
        arg_value = evaluate(arg_expr, xule_context)
        arg_values.append(arg_value)
    
    if len(property_info) > 4: # There is property data
        object_value = property_info[XuleProperties.PROP_FUNCTION](xule_context, object_value, property_info[XuleProperties.PROP_DATA], *arg_values)
    else:    
        object_value = property_info[XuleProperties.PROP_FUNCTION](xule_context, object_value, *arg_values)
    
    if 'tagName' in current_property_expr:
        xule_context.tags[current_property_expr.tagName] = object_value

    return object_value

def evaluate_index(index_expr, xule_context):
    
    # evaluate the left side of the expression
    left_value = evaluate(index_expr['expr'], xule_context)
    
    for index in index_expr['indexes']:
        index_value = evaluate(index, xule_context)
        # An index expression is used for lists and dictionaries.
        if left_value.type == 'list':
            if index_value.type == 'int':
                index_number = index_value.value
            elif index_value.type == 'float':
                if index_value.value.is_integer():
                    index_number = int(index_value.value)
                else:
                    raise XuleProcessingError(_("Index of a list must be a whole number, found %s" % str(index_value.value)),
                                              xule_context)
            elif index_value.type == 'decimal':
                if index_value.value == int(index_value.value):
                    index_number = int(index_value.value)
                else:
                    raise XuleProcessingError(_("Index of a list must be a whole number, found %s" % str(index_value.value)),
                                              xule_context)
            else:
                raise XuleProcessingError(_("Index of a list must be a number, found %s" % index_value.type),
                                          xule_context)
            
            # Check if the index number is the value range for the list
            if index_number < 1 or index_number > len(left_value.value):
                raise XuleProcessingError(_("Index value of %i is out of range for the list with length of %i" % (index_number, len(left_value.value))),
                                          xule_context)
            left_value = left_value.value[index_number -1]
        elif left_value.type == 'dictionary':
            if index_value.type in ('set', 'list'):
                key_value = index_value.shadow_collection
            else:
                key_value = index_value.value
            
            return left_value.key_search_dictionary.get(key_value, XuleValue(xule_context, None, 'none'))
        
        else:
            raise XuleProcessingError(_("Index epxressions can only operate on a list, found '%s'" % left_value.type), 
                                        xule_context)
        
    return left_value

def evaluate_tag_ref(tag_ref, xule_context):
    if tag_ref['varName'] in xule_context.tags:
        return xule_context.tags[tag_ref['varName']]
    else:
        return XuleValue(xule_context, None, 'none')
                 
#aspect info indexes
TYPE = 0
ASPECT = 1
SPECIAL_VALUE = 2
ASPECT_OPERATOR = 3
ASPECT_PROPERTY = 4


     

EVALUATOR = {
    #rules
    "assertion": evaluate_assertion,
    "outputRule": evaluate_output_rule,
    
    #literals
    "boolean": evaluate_bool_literal,
    "integer": evaluate_int_literal,
    "float": evaluate_float_literal,
    "string": evaluate_string_literal,
    "qname": evaluate_qname_literal,
    #"skip": evaluate_void_literal,
    "none": evaluate_void_literal,
    
    #atomic expressions
    "constantDeclaration": evaluate_constant_assign,
    "printExpr": evaluate_print,
    "ifExpr": evaluate_if,
    "forExpr": evaluate_for,
    #"forControl": evaluate_for_control,
    #"forLoop": evaluate_for_loop,
    #"forBodyExpr": evaluate_for_body,
    #"withExpr": evaluate_with,
    
    "blockExpr": evaluate_block,
    "varRef": evaluate_var_ref,
    "tagRef": evaluate_tag_ref,
    "functionReference": evaluate_function_ref,
    "taggedExpr": evaluate_tagged,
    "propertyExpr": evaluate_property,
    "indexExpr": evaluate_index,
    
    "factset": evaluate_factset,
    "navigation": evaluate_navigate,
    "filter": evaluate_filter,
    "dictExpr": evaluate_dict,
    "listExpr": evaluate_list,
    "setExpr": evaluate_set,
    #'valuesExpr': evaluate_values,
    
    #expressions with order of operations
    "unaryExpr": evaluate_unary,
    "multExpr": evaluate_mult,
    "addExpr": evaluate_add,
    "intersectExpr": evaluate_intersect,
    "symetricDifferenceExpr": evaluate_symetric_difference,
    "compExpr": evaluate_comp,
    "notExpr": evaluate_not,
    "andExpr": evaluate_and,
    "orExpr": evaluate_or,
    
    #severity
    'severity': evaluate_severity,
    
    #balance
    'balance': evaluate_string_keyword,
    'periodType': evaluate_string_keyword,
    
    }


 
    
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
    return XuleFunctions.BUILTIN_FUNCTIONS

BUILTIN_FUNCTIONS = XuleFunctions.BUILTIN_FUNCTIONS



def process_factset_aspects(factset, xule_context):
    """Build list of aspects as descried in the factset
    
    This function returns 3 dictionaries. 
    1. A dictionary of aspect filters that will not be included in the alignment. These are indicated with @ (single) in the factset expression.
    2. A dictionary of aspect filters that will be included in the alginment. These are indicated with @@ (double) in the factset expression.
    3. A dictionary of variables based on aspect aliases.
    
    The aspect filters dictionaries (the first 2 dictionaries) are keyed by a tuple of 4 items:    
    1. aspect type - This is either 'builtin' or 'explicit_dimension'
    2. aspect name - For built in aspects it is one of 'concept', 'entity', 'period', 'unit' or 'table'
                     For dimensional aspects it is the qname of the dimension
    3. special value - If the aspect uses a wildcard, this will contain the wildcard character '*'. Otherwise it is None.
    4. aspect operator - This is the operator used for the filter. It is one of '=', '!=', 'in' or 'not in'. If there is not aspect operator
                         the value is None.
    5. aspect properties - This is a tuple. The first time is the property name and second item is a list of evaluated tuple of arguments.
    
    The value of the key is the evaluated expression on the right of the aspect operator. If there is no operator, then the value is None.                     
    
    The dictionary of aspect variables is key by a the alias name. The value is a tuple of 3 items:
    1. aspect type - This is either 'builtin' or 'explicit_dimension'
    2. aspect name - For built in aspects it is one of 'concept', 'entity', 'period', 'unit' or 'table'
                     For dimensional aspects it is the qname of the dimension
    3. aspect index - This is the node_id of the aspect filter.

    """
    non_align_aspects = {}
    align_aspects = {}
    aspect_vars = {}
    alternate_notation = False

    '''COULD CHECK FOR DUPLICATE ASPECTS IN THE FACTSET'''
    for aspect_filter in factset.get('aspectFilters', list()):
        # Set the dictionary to use based on if the aspect is covered (single @ - non aligned) vs. uncoverted (double @ - aligned)
        aspect_dictionary = non_align_aspects if aspect_filter['coverType'] == 'covered' else align_aspects        
        aspect_var_name = aspect_filter.get('alias')
        if 'aspectName' in aspect_filter:
            # This is a built in aspect - one of concept, period, entity, unit or table
            add_aspect_var(aspect_vars, 'builtin', aspect_filter['aspectName'], aspect_var_name, aspect_filter['node_id'], xule_context)
            if aspect_filter['aspectName'] == 'concept' and alternate_notation:
                raise XuleProcessingError(_("The factset specifies the concept aspect as both @{0} and @concept={0}. Only one method should be used".format(aspect_filter_qname.value)), xule_context)
            aspect_info, aspect_value = process_aspect_expr(aspect_filter, 'builtin', aspect_filter['aspectName'], xule_context)
            if aspect_info is not None:
                aspect_dictionary[aspect_info] = aspect_value
        else:
            # This is either a dimension aspect or the default concept aspect. The aspect name is determined by evaluating the aspectDimensionName
            aspect_filter_qname = evaluate(aspect_filter['aspectDimensionName'], xule_context)
            #Get the model concept to determine if the aspect is a dimension
            aspect_filter_model_concept = xule_context.model.qnameConcepts.get(aspect_filter_qname.value)
            if aspect_filter_model_concept is None:
                raise XuleProcessingError(_("Error while processing factset aspect. Concept %s not found." % aspect_filter_qname.value.clarkNotation), xule_context)
            if aspect_filter_model_concept.isDimensionItem:
                # This is a dimension aspect
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname.value, aspect_var_name, aspect_filter['node_id'], xule_context)
                aspect_info, aspect_value = process_aspect_expr(aspect_filter, 'explicit_dimension', aspect_filter_qname.value, xule_context)
                if aspect_info is not None:
                    aspect_dictionary[aspect_info] = aspect_value                   
            else:
                # This is a concept aspect and the filter name is really the aspect value (i.e. @Assets
                if aspect_in_filters('builtin', 'concept', aspect_dictionary):
                    raise XuleProcessingError(_("The factset specifies the concept aspect as both @{0} and @concept={0}. Only one method should be used".format(aspect_filter_qname.value)), xule_context)
                alternate_notation = True #Indicate that the concept aspect is provided
                aspect_dictionary[('builtin', 'concept', None, '=', None)] = aspect_filter_qname
                add_aspect_var(aspect_vars, 'builtin', 'concept', aspect_var_name, aspect_filter['node_id'], xule_context)


#         aspect_filter_qname = evaluate(aspect_filter.aspectName.qName, xule_context).value
#         #verify that lineItem is not used in both forms of the notation, i.e. Assets[lineItem=Liabilities].
#         aspect_var_name = aspect_filter.get('aspectVar')
#         if aspect_filter_qname.prefix is None and aspect_filter_qname.localName in BUILTIN_ASPECTS:
#             #the aspect is builtin
#             if aspect_filter_qname.localName == 'concept' and alternate_notation:
#                 XuleProcessingError(_("The factset specifies the lineItem both outside and inside the factset."), xule_context)
#                  
#             if aspect_filter.get('all'):
#                 aspect_info = ('builtin', aspect_filter_qname.localName, aspect_filter.all, aspect_filter.aspectOperator)
#                 non_align_aspects[aspect_info] = XuleValue(xule_context, None, 'none')
#                 add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter['node_id'], xule_context)    
#             elif aspect_filter.get('void'):
#                 non_align_aspects[('builtin', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
#                 add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter['node_id'], xule_context)                            
#             else:
#                 aspect_info = ('builtin', aspect_filter_qname.localName, None, aspect_filter.aspectOperator)
#                 non_align_aspects[aspect_info] = evaluate(aspect_filter.aspectExpr[0], xule_context)
#                 add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter['node_id'], xule_context)
#         else:
#             #This is a dimensional aspect.
#             if aspect_filter.get('all'):
#                 non_align_aspects[('explicit_dimension', aspect_filter_qname, aspect_filter.all, aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
#                 add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter['node_id'], xule_context)
#             elif aspect_filter.get('void'):
#                 non_align_aspects[('explicit_dimension', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
#                 add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter['node_id'], xule_context)                
#             else:
#                 if not(aspect_filter.get('aspectExpr')):
#                     #There is no member. In this case the aspect may have varname, but it dones not participate in the non_align.
#                     add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter['node_id'], xule_context)
#                 else:
#                     member_rs = evaluate(aspect_filter.aspectExpr[0], xule_context)
#                     non_align_aspects[('explicit_dimension', aspect_filter_qname, None, aspect_filter.aspectOperator)] = member_rs
#                     add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter['node_id'], xule_context)
    
    return (non_align_aspects, align_aspects, aspect_vars) 

def aspect_in_filters(aspect_type, aspect_name, filters):
    """Checks if an aspect is in the existing set of filters
    
    Arguments:
    aspect_type (string): Either 'builtin' or 'dimension'
    aspect_name (string or qname): if 'builtin' this will be a string with values of 'concept', 'unit', 'period', 'entity' or 'table', otherwise it is a qname
                                   of the dimensional aspect name.
    filters (dictionary): Dictionary of aspect filters.
    """
    for filter_type, filter_name, _x, _y, _z in filters:
        if filter_type == aspect_type and filter_name == aspect_name:
            return True
    # This will only hit if the aspect was not found in the filters.
    return False

def process_aspect_expr(aspect_filter, aspect_type, aspect_name, xule_context):
    """Process the expression on the right side of an aspect filter.
    
    This looks at the aspectExpr for the aspect filter (if there is on). This will return a 2 item tuple of the aspect_info key and 
    the evaluated aspect expression value.
    
    Arguments:
        aspect_filter (dict): AST node for the aspect filter
        aspect_type (string): Either 'builtin' or 'explicit_dimension'
        xule_context (XuleContext): The processing context
    """
    aspect_info = None
    aspect_value = None
    prop = None
    
    # Properties 
    if 'propertyName' in aspect_filter:
        prop = (aspect_filter['propertyName'], tuple(evaluate(arg, xule_context).value for arg in aspect_filter.get('propertyArgs', tuple())))    
    
    if 'wildcard' in aspect_filter:
        if aspect_filter['aspectOperator'] not in ('=', '!='):
            raise XuleProcessingError(_("In a factset a '*' can only be used with '=' or '!=', found '{}'".format(aspect_filter['aspectOperator'] + ' *')), xule_context)
        if aspect_filter['aspectOperator'] == '=':
            aspect_info = (aspect_type, aspect_name, aspect_filter['wildcard'], aspect_filter['aspectOperator'], prop)
            aspect_value = XuleValue(xule_context, None, 'none')
        else:
            # This is aspect_name != *. Really this is the fact does not have this aspect (this aspect is in the default)
            aspect_info = (aspect_type, aspect_name, None, '=', prop)
            aspect_value = XuleValue(xule_context, None, 'none')   
    else:
        # Not a wildcard
        if 'aspectExpr' in aspect_filter:
            aspect_info = (aspect_type, aspect_name, None, aspect_filter['aspectOperator'], prop)
            aspect_value = evaluate(aspect_filter['aspectExpr'], xule_context)
        #Else this aspect does not have an expressions so it does not create a filter. It is only here for the alias which has already been dealt with.

    return (aspect_info, aspect_value)
    
def add_aspect_var(aspect_vars, aspect_type, aspect_name, var_name, aspect_index, xule_context):
    if var_name:
        if var_name in aspect_vars:
            raise XuleProcessingError(_("Found multiple aspects with same variable name '%s' in a factset." % (var_name)), xule_context) 
        else:
            aspect_vars[var_name] = (aspect_type, aspect_name, aspect_index)

def convert_value_to_qname(value, xule_context):
    if value.type == 'concept':
        return value.value.qname
    elif value.type == 'qname':
        return value.value
    elif value.type in ('unbound', 'none'):
        return None
    else:
        raise XuleProcessingError(_("The value for a line item or dimension must be a qname or concept, found '%s'." % value.type), xule_context)

def convert_value_to_model_period(value, xule_context):
    if value.type in ('unbound', 'none'):
        return None
    
    if value.from_model:
        return value.value
    else:
        #need to adjust instant and end_date. The model has instant and end dates of the next day because python treats midnight as the begining of the day.
        if value.type == 'instant':
            return value.value + datetime.timedelta(days=1)
        elif value.type == 'duration':
            if value.value[0] == datetime.datetime.min and value.value[1] == datetime.datetime.max:
                #this is forever, don't do anything
                return value.value
            else:
                return (value.value[0], value.value[1] + datetime.timedelta(days=1))
        else:
            raise XuleProcessingError(_("Converting result to a period, expected 'instant' or 'duration' but found '%s'" % value.type), xule_context)

def convert_value_to_model_unit(value, xule_context):
    if value.type == 'unit':
        return value.value
    elif value.type == 'qname':
        # A xule 'unit' is a tuple 
        return ((value.value,),tuple())
    
    
# def get_used_vars(xule_context, var_ids):    
#     return {var_id: xule_context.vars.get(var_id) for var_id in var_ids}

def match_function_arguments(reference, declaration, xule_context):
    ''' This function matches the arguments on the function reference (call) to the function declaration.
        It returns a list of matched arguments as a dictionary.
    '''
    if len(reference['functionArgs']) != len(declaration['functionArgs']):
        raise XuleProcessingError(_("Function call for '%s' has mismatched arguments." % reference['functionName']), xule_context)
    else:
        matched = []
        for i in range(len(reference['functionArgs'])):
            arg_name = declaration['functionArgs'][i]['argName']
                
            matched.append({"name": arg_name, 
                            "node_id": declaration['functionArgs'][i]['node_id'], 
                            "expr": reference['functionArgs'][i],
                            "tagged": declaration['functionArgs'][i].get('tagged', False)})

    
    return matched    

def remove_from_alignment(alignment, remove_aspects, xule_context):
    unfrozen_alignment = {k: v for k, v in alignment}
    for aspect_key in remove_aspects:
        if aspect_key in unfrozen_alignment:
            del unfrozen_alignment[aspect_key]
    new_alignment = frozenset(unfrozen_alignment.items())
    return new_alignment
    

def alignment_to_aspect_info(alignment, xule_context):
    aspect_dict = {}
    for align_key, align_value in alignment.items():
        aspect_info = (align_key[0], align_key[1], None, '=')

        if align_key[0] == 'builtin':
            if align_key[1] == 'concept':
                aspect_value = XuleValue(xule_context, align_value, 'qname')
            elif align_key[1] == 'unit':
                aspect_value = XuleValue(xule_context, align_value, 'unit')
                
            elif align_key[1] == 'period':           
                period_value = align_value
                if isinstance(period_value, tuple):
                    if period_value[1] == datetime.datetime.max:
                        #this is forever
                        aspect_value = XuleValue(xule_context, period_value, 'duration', from_model=True)
                    else:
                        #need to adjust the end date
#                         aspect_value = XuleResultSet(XuleResult((period_value[0],
#                                                                  period_value[1] - datetime.timedelta(days=1))
#                                                                 ,'duration'))
                        aspect_value = XuleValue(xule_context, (period_value[0],
                                                                 period_value[1])
                                                                ,'duration',
                                                                from_model=True)
                else:
                    #need to adjust the date. This is from the model which handles midnight (end of day) as beginning of next day.
#                     aspect_value = XuleResultSet(XuleResult(period_value - datetime.timedelta(days=1), 'instant'))
                    aspect_value = XuleValue(xule_context, period_value, 'instant', from_model=True)
                    
            elif align_key[1] == 'entity':
                aspect_value = XuleValue(xule_context, align_value, 'entity')
                
            else:
                raise XuleProcessingError(_("Unknown built in aspect '%s'" % align_key[1]), xule_context)
        elif align_key[0] == 'explicit_dimension':
            aspect_value = XuleValue(xule_context, align_value, model_to_xule_type(xule_context, align_value))
            
        else:
            raise XuleProcessingError(_("Unknown aspect type '%s'" % align_key[0]), xule_context)
            
        aspect_dict[aspect_info] = aspect_value
    
    return aspect_dict

def sugar_trace(value, rule_part, xule_context):
    part_name = rule_part['exprName']
    if part_name == 'forExpr':
        return (rule_part['forLoopExpr']['forVar'],)
    elif part_name == 'varRef':
        return (rule_part['varName'],)
    elif part_name == 'functionReference':
        function_info = xule_context.find_function(rule_part['functionName'])
        if function_info is None:
            return (rule_part['functionName'], tuple())
        else:
            args = tuple([x.argName for x in function_info['function_declaration']['functionArgs']])
            return (rule_part['functionName'], args)
    elif part_name == 'factset':
        return (value,)
    else:
        return tuple()

def format_trace(xule_context):
    trace_string = ""
    for step in xule_context.trace:
        trace_string += "  " * step[0] + step[3].format_value() + format_trace_info(step[1], step[2], {}, xule_context) + "\n"
    return trace_string

def format_trace_info(expr_name, sugar, common_aspects, xule_context):
    trace_info = ""
    
    if expr_name == 'forExpr':
        trace_info += 'for ($%s)' % sugar[0]
    elif expr_name == 'ifExpr':
        trace_info += 'if'
    elif expr_name == 'varRef':
        trace_info += 'var ($%s)' % sugar[0]
    elif expr_name == 'functionReference':
        if len(sugar[1]) == 0:
            args = "..."
        else:
            args = ",".join(sugar[1])
        trace_info += '%s(%s)' % (sugar[0], args)
    elif expr_name == 'addExpr':
        trace_info += 'add/subtract'
    elif expr_name == 'multExpr':
        trace_info += 'multiply/divide'
    elif expr_name == 'compExpr':
        trace_info += 'comparison'
    elif expr_name == 'andExpr':
        trace_info += 'and'
    elif expr_name == 'orExpr':
        trace_info += 'or'
    elif expr_name == 'property':
        trace_info += "::%s" % sugar[0]
    elif expr_name == 'factset':
        if sugar[0].fact is not None:
            fact_context = get_uncommon_aspects(sugar[0].fact, common_aspects, xule_context)
            trace_info = 'factset '
            if ('builtin', 'concept') not in fact_context:
                trace_info += str(sugar[0].qname) + " "
            trace_info +=  format_alignment(fact_context, xule_context)
    else:
        trace_info += expr_name
    
    if len(trace_info) > 0:
        trace_info = " - " + trace_info
    
    return trace_info


def result_message(rule_ast, result_ast, xule_value, xule_context):
    message_context = xule_context.create_message_copy(xule_context.get_processing_id(rule_ast['node_id']))
    message_context.tags['rule-value'] = xule_value
    try:
        # Caching does not work for expressions with tagRefs. The The results portion of a rule will have a tagRef for each varRef. This conversion is
        # done during the post parse step. So it is neccessary to turn local caching off when evaluating the result expression. There is a command line option
        # for doing this. This code will turn this command line option on.
        saved_no_cache = getattr(message_context.global_context.options, 'xule_no_cache')
        xule_context.global_context.options.xule_no_cache = True
        
        message_value = evaluate(result_ast['resultExpr'], message_context)
    finally:
        if hasattr(message_context.global_context.options, 'xule_no_cache'):
            xule_context.global_context.options.xule_no_cache = saved_no_cache   
                 
    if message_value.type == 'unbound':
        message_string = ""
    else:
        message_string = str(message_value.value)
        
        #message_string = process_message(message_string, xule_value, xule_context)
        
    return str(message_string)
    
# def get_message(rule, xule_value, alignment, xule_context):
#     if 'message' in rule:
#         message_value = evaluate(rule.message[0], xule_context)
#         if message_value.type == 'unbound':
#             message_string = ""
#         else:
#             message_string = message_value.value
#     else:
#         message_string = ""
#     
#     if message_string == "":
#         #create a default message
#         if rule['exprName'] == 'reportDeclaration':
#                 message_string = "${value} ${context}"
#         elif rule['exprName'] == 'raiseDeclaration':
#             if len(xule_context.facts) > 0:
#                 message_string = "${default_fact.value} ${default_fact.context}${context}"
#                 xule_context.add_tag('default_fact', XuleValue(xule_context, next(iter(xule_context.facts)), 'fact'))
#             else:
#                 message_string = "${value}"
#         elif rule['exprName'] == 'formulaDeclaration':
#             message_string = "${left.value} != ${right.value} ${context}"
#     
#     return process_message(message_string, xule_value, alignment, xule_context)

# def process_message(message_string, xule_value, xule_context):    
# 
#     alignment = xule_context.iteration_table.current_alignment
# 
#     common_facts = [tag_value.fact for tag_value in xule_context.tags.values() if tag_value.is_fact]
#     if not common_facts: #common_facts is empty, no facts are tagged.
#         common_facts = xule_context.facts
# 
#     common_aspects = get_common_aspects(common_facts, xule_context)
#     
#     #Check if there is a fact tag that uses the .context. If so and the lineItem is in the common aspects, the line item should be removed from the common aspects
#     if ('builtin','concept') in common_aspects:
#         for tag_name, tag_value in xule_context.tags.items():
#             if tag_value.is_fact or tag_value.type == 'empty_fact':
#                 tag_context_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)context\s*}'
#                 if re.search(tag_context_pattern, message_string):
#                     del common_aspects[('builtin','concept')]
#                     break
#      
#     for tag_name, tag_value in xule_context.tags.items():        
#         replacement_value = tag_value.format_value() or ''
#         
#         if tag_value.is_fact: 
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)
#             
#             for tag_sub_part in MESSAGE_TAG_SUB_PARTS:
#                 tag_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)' + tag_sub_part[0] + '\s*}'
#                 if re.search(tag_pattern, message_string) is not None:
#                     if tag_sub_part[1] == format_alignment:
#                         message_string = re.sub(tag_pattern, format_alignment(get_uncommon_aspects(tag_value.fact, common_aspects, xule_context), xule_context), message_string)
#                     else:
#                         new_value = tag_sub_part[1](xule_context, tag_value)
#                         message_string = re.sub(tag_pattern, new_value or "", message_string)
#                         
#         elif tag_value.type == 'empty_fact':
#             if alignment is not None and ('builtin', 'concept') in alignment:
#                     tag_context = format_qname(alignment[('builtin', 'concept')], xule_context)
#             else:
#                 tag_context = str(tag_value.value)
#                 
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', 'missing', message_string)
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', 'missing', message_string)
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*context\s*}', tag_context, message_string)
#             
#             for tag_sub_part in MESSAGE_TAG_SUB_PARTS:
#                 tag_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)' + tag_sub_part[0] + '\s*}'
#                 if re.search(tag_pattern, message_string) is not None:
#                     message_string = re.sub(tag_pattern, 'missing', message_string)
# 
#         else:
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
#             message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)
# 
#     message_string = re.sub('\$\s*{\s*context\s*}', format_alignment(common_aspects, xule_context), message_string)
#     message_string = re.sub('\$\s*{\s*value\s*}', xule_value.format_value() or '', message_string)
#     '''ADD TRACE'''
# #     if xule_context.show_trace:
# #         message_string = re.sub('\$\s*{\s*trace\s*}', format_trace(xule_context, result, common_aspects), message_string)
#     message_string = message_string.replace('%', '%%')
# 
#     return message_string

# def get_common_aspects(dict_model_facts, xule_context):
#     
#     model_facts = list(dict_model_facts)
#     
#     if len(model_facts) > 0:
#         common_aspects = get_all_aspects(model_facts[0], xule_context)
#     else:
#         common_aspects = {}    
#     
#     for model_fact in model_facts[1:]:
#         fact_aspects = get_all_aspects(model_fact, xule_context)
#         for aspect_info, aspect_value in fact_aspects.items():
#             if aspect_info in common_aspects:
#                 if aspect_value != common_aspects[aspect_info]:
#                     del common_aspects[aspect_info]
#         for missing_aspect in common_aspects.keys() - fact_aspects.keys():
#             del common_aspects[missing_aspect]
#         
#     #remove lineItem
#     if ('builtin', 'concept') in common_aspects and len(model_facts) > 1:
#         del common_aspects[('builtin', 'concept')]
#     
#     return common_aspects

def get_all_aspects(model_fact, xule_context):
    '''This function gets all the apsects of a fact'''
    return get_alignment(model_fact, {}, xule_context)

def get_alignment(model_fact, non_align_aspects, xule_context):
    '''The alingment contains the aspect/member pairs that are in the fact but not in the non_align_aspects.
       The alignment is done in two steps. First check each of the builtin aspects. Then check the dimesnions.'''
    
    '''non_align_aspect - dictionary
            Key is a tuple with the following parts:
                0 = TYPE -'builtin' or 'explicit_dimension', 
                1 = ASPECT - aspect, 
                2 = SPECIALVALUE - 'all' or 'allWithDefault', 
            value = MEMBER (None if there is a SPECIAL_VALUE)'''
    
    alignment = {}
    #builtin alignment
    non_align_builtins = {aspect_info[ASPECT] for aspect_info in non_align_aspects if aspect_info[TYPE] == 'builtin'}
    
    #lineItem
    if 'concept' not in non_align_builtins:
        alignment[('builtin', 'concept')] = model_fact.qname
        #alignment[('builtin', 'concept')] = model_fact.elementQname
    
    #unit
    if model_fact.isNumeric:
        if 'unit' not in non_align_builtins:
            alignment[('builtin', 'unit')] = model_to_xule_unit(model_fact.unit, xule_context)
            
    #period
    if 'period' not in non_align_builtins:
        alignment[('builtin', 'period')] = model_to_xule_period(model_fact.context, xule_context)
        
    #entity
    if 'entity' not in non_align_aspects:
        alignment[('builtin', 'entity')] = model_to_xule_entity(model_fact.context, xule_context)
          
    #dimensional apsects
    non_align_dimensions = {aspect_info[ASPECT] for aspect_info in non_align_aspects if aspect_info[TYPE] == 'explicit_dimension'}
    for fact_dimension_qname, dimension_value in model_fact.context.qnameDims.items():
        if fact_dimension_qname not in non_align_dimensions:
            
            alignment[('explicit_dimension', fact_dimension_qname)] = dimension_value.memberQname if dimension_value.isExplicit else dimension_value.typedMember.xValue
        
    return alignment          

def get_uncommon_aspects(model_fact, common_aspects, xule_context):
    
    uncommon_aspects = {}
    
    fact_aspects = get_all_aspects(model_fact, xule_context)
    for aspect_info, aspect_value in fact_aspects.items():
        if aspect_info == ('builtin', 'concept'):
            uncommon_aspects[aspect_info] = aspect_value
        elif aspect_info not in common_aspects:
                uncommon_aspects[aspect_info] = aspect_value
    
    return uncommon_aspects     

def format_alignment(aspects, xule_context):

    if len(aspects) == 0:
        return ''
    
    aspect_strings = []
    line_item_string = ""
    
    #built in aspects
    if ('builtin', 'concept') in aspects:
        line_item_string = format_qname(aspects[('builtin', 'concept')], xule_context)
    
    if ('builtin', 'period') in aspects:
        period_info = aspects[('builtin', 'period')]
        if isinstance(period_info, tuple):
            if period_info[0] == datetime.datetime.min and period_info[1] == datetime.datetime.max:
                aspect_strings.append("period=forever")
            else:
                aspect_strings.append("period=duration('%s', '%s')" % (period_info[0].strftime("%Y-%m-%d"), (period_info[1] - datetime.timedelta(days=1)).strftime("%Y-%m-%d")))
        else:
            aspect_strings.append("period=instant('%s')" % (period_info - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    
    if ('builtin', 'unit') in aspects:
        model_unit = aspects[('builtin', 'unit')]
        aspect_strings.append(str(model_unit))
#         if len(model_unit[1]) == 0:
#             #no denominator
#             aspect_strings.append("unit=%s" % " * ".join([x.localName for x in model_unit[0]]))
#         else:
#             aspect_strings.append("unit=%s/%s" % (" * ".join([x.localName for x in model_unit[0]]), 
#                                                   " * ".join([x.localName for x in model_unit[1]])))
            
    if ('builtin', 'entity') in aspects:
        entity_info = aspects[('builtin', 'entity')]
        aspect_strings.append("entity=(%s) %s" % (entity_info[0], entity_info[1]))      
        
    #dimensions
    dimension_aspects = [(aspect_info[ASPECT],aspect_info, aspect_member) for aspect_info, aspect_member in aspects.items() if aspect_info[TYPE] == 'explicit_dimension']
    #sort by the dimension qname
    dimension_aspects.sort(key=lambda tup: tup[0])
    
    #for aspect_info, aspect_member in aspects.items():
    for dimension_aspect in dimension_aspects:
        aspect_info = dimension_aspect[1]
        aspect_member = dimension_aspect[2]
        if aspect_info[TYPE] == 'explicit_dimension':
            aspect_member = aspects[aspect_info]
            '''THE formatted_member SHOULD HANDLE FORMATTING OF NON QNAME VALUES'''
            formatted_member = format_qname(aspect_member, xule_context) if type(aspect_member) == QName else aspect_member
            aspect_strings.append("%s=%s" % (format_qname(aspect_info[ASPECT], xule_context), formatted_member))
            
    if len(aspect_strings) > 0:
        aspect_string = "[" + ",\n".join(aspect_strings) + "]"
    else:
        aspect_string = ""
        
    return line_item_string + aspect_string  

def format_fact_line_item(xule_context, xule_fact):
    return format_qname(xule_fact.fact.concept.qname, xule_context)

def format_fact_period(xule_context, xule_fact):
    if xule_fact.fact.context.isStartEndPeriod:
        period_string = xule_fact.fact.context.startDatetime.strftime("%m/%d/%Y") + " - " + (xule_fact.fact.context.endDatetime - datetime.timedelta(days=1)).strftime("%m/%d/%Y")
    elif xule_fact.fact.context.isInstantPeriod:
        period_string = (xule_fact.fact.context.endDatetime - datetime.timedelta(days=1)).strftime("%m/%d/%Y")
    else:
        period_string = "Forever"
    
    return period_string

def format_fact_unit(xule_context, xule_fact):
    if xule_fact.fact.isNumeric:
        numerator = tuple(sorted(xule_fact.fact.unit.measures[0]))
        denominator = tuple(sorted(xule_fact.fact.unit.measures[1]))
        
        if len(denominator) == 0:
            #no denominator
            return " * ".join([x.localName for x in numerator])
        else:
            return "%s/%s" % (" * ".join([x.localName for x in numerator]), 
                              " * ".join([x.localName for x in denominator]))
    else:
        return None

def format_fact_all_aspects(xule_context, xule_fact):
    aspect_strings = ["Line Item: " + format_fact_line_item(xule_context, xule_fact),]
    aspect_strings.append("Period: " + format_fact_period(xule_context, xule_fact))
    unit = format_fact_unit(xule_context, xule_fact)
    if unit is not None:
        aspect_strings.append("Unit: " + unit)
    dimensions = format_fact_dimensions(xule_context, xule_fact)
    if dimensions is not None:
        aspect_strings.append("Dimensions:\n" + dimensions)
    return "\n".join(aspect_strings)

def format_fact_dimensions(xule_context, xule_fact):
    if len(xule_fact.fact.context.qnameDims) > 0:
        dim_pairs = []
        for axis_qname in sorted(xule_fact.fact.context.qnameDims):
            dim_pairs.append(format_qname(axis_qname, xule_context) + " = " + format_qname(xule_fact.fact.context.qnameDims[axis_qname].memberQname, xule_context))
        return "\n".join(dim_pairs)
    else:
        return None
     
def format_fact_label(xule_context, fact):
    label = property_label(xule_context, fact)
    if label.type in ('unbound', 'none'):
        return "missing"
    else:
        return label.value.textValue

def format_qname(qname, xule_context):
    cat_namespace = xule_context.rule_set.getNamespaceInfoByUri(qname.namespaceURI)
    if cat_namespace:
        if cat_namespace['prefix'] == '*':
            return qname.localName
        else:
            return cat_namespace['prefix'] + ":" + qname.localName
    else:
        return str(qname)       

MESSAGE_TAG_SUB_PARTS = (('context', format_alignment),
                              ('label', format_fact_label),
                              ('concept', format_fact_line_item),
                              ('period', format_fact_period),
                              ('unit', format_fact_unit),
                              ('aspects', format_fact_all_aspects),
                              ('dimensions', format_fact_dimensions)
                              )
    
def get_element_identifier(xule_value, xule_context):
    if len(xule_context.facts) > 0:
        model_fact = list(xule_context.facts)[0]
        
        if model_fact.id is not None:
            return (model_fact.modelDocument.uri + "#" + model_fact.id, model_fact.sourceline)
        else:
            #need to build the element scheme
            location = get_tree_location(model_fact)
            return (model_fact.modelDocument.uri + "#element(" + location + ")", model_fact.sourceline)
            
def get_tree_location(model_fact):
    
    parent = model_fact.getparent()
    if parent is None:
        return "/1"
    else:
        prev_location = get_tree_location(parent)
        return prev_location + "/" + str(parent.index(model_fact) + 1)
    
#     if hasattr(model_fact.parentElement, '_elementSequence'):
#         prev_location = get_tree_location(model_fact.parentElement)
#     else:
#         prev_location = "/1"
#     
#     return "abc"
#     return prev_location + "/" + str(model_fact._elementSequence)


def write_trace_count_string(trace_count_file, rule_name, traces, rule_part, total_iterations, total_time):
    display_string = display_trace_count(traces, rule_part, total_iterations, total_time)

    with open(trace_count_file + ".txt", 'a', newline='') as o:
        o.write(display_string)
        
def display_trace_count(traces, rule_part, total_iterations, total_time, level=0, display_string=""):
    if isinstance(rule_part, ParseResults):
        additional = ''
        if rule_part['exprName'] == 'varRef':
            if rule_part.is_constant:
                additional =  " ($" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + ") - constant)"
            else:
                additional = " ($" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + ")"
        elif rule_part['exprName'] == 'varAssign':
            additional = " (" + rule_part.varName + ")" + (" NOT USED" if rule_part.get('not_used') == True else "")
        elif rule_part['exprName'] == 'constantAssign':
            additional = " (" + rule_part.constantName + ")"
        elif rule_part['exprName'] == 'functionArg':
            additional = " (" + rule_part.argName + ")"
        elif rule_part['exprName'] == 'forExpr':
            additional = " (" + rule_part.forControl.forVar + ")"
        elif rule_part['exprName'] == 'reportDeclaration':
            additional = " (" + rule_part.reportName + ")"
        elif rule_part['exprName'] == 'raiseDeclaration':
            additional = " (" + rule_part.raiseName + ")"  
        elif rule_part['exprName'] == 'formulaDeclaration':
            additional = " (" + rule_part.formulaName + ")"                      
#         elif rule_part['exprName'] in ('functionDeclaration', 'functionReference'):
#             additional = " (" + rule_part.functionName + ")"  + (" CACHEABLE" if rule_part.get('cacheable') == True else "") 
        
        if rule_part.number != '':
            additional += (" [" + 
                           ('i, ' if rule_part.get('instance') else '') +
                           ('r, ' if rule_part.get('rules-taxonomy') else '') +
                           ('1' if rule_part.number == 'single' else "*")  + 
                           (", Align" if rule_part.has_alignment else ", NoAlign") + 
                           ((", " + ("D" if rule_part.is_dependent else "I")) if 'is_dependent' in rule_part else "") +
                           #((", " + str(parse_res.var_refs)) if len(parse_res.var_refs) > 0 else "") + 
#                            ((", v" + str({(x[0], x[1]) for x in rule_part.dependent_vars})) if len(rule_part.dependent_vars) > 0 else "") +
#                            ((", V" + str({(x[0], x[1]) for x in rule_part.var_refs})) if len(rule_part.var_refs) > 0 else "") +
#                            ((", VIds" + str(rule_part.var_ref_ids)) if 'var_ref_ids' in rule_part else "")  +
                           ((", i" + str({dep['node_id'] for dep in rule_part.dependent_iterables})) if len(rule_part.dependent_iterables) > 0 else "") +         
#                            ((", di" + str({dep['node_id'] for dep in rule_part.downstream_iterables})) if len(rule_part.downstream_iterables) > 0 else "") +                    
                           (", Values" if rule_part.get('values_expression') == True else "") +
                           (", Table %i" % rule_part.table_id if rule_part.get('table_id') is not None else "") +
                           "]")
        
        if 'is_iterable' in rule_part:
            additional += " iterable"
        if 'in_loop' in rule_part:
            additional += " LOOP"
        display_string += ("  " * level) + str(rule_part['node_id']) + ":" + rule_part['exprName'] + additional + "\n"
        if rule_part['node_id'] in traces:
            trace = traces[rule_part['node_id']]
            total_count = 0
            #display_string += ", ".join(trace.keys()) + "\n"
            for key in ('iterations', 'U', 'E', 'c', 'T', 'e', 'R', 'r', 'isE', 'ise', 'isu', 'ex'):
                if trace[key] > 0:
                    if key == 'iterations':
                        display_string += "{}{} {} {}\n".format("  " * (level + 1), 
                                                                            key, 
                                                                            trace[key],
                                                                            (trace[key] / total_iterations) if total_iterations > 0 else 0)
                        #add step values
                        children_time, child_nodes = trace_count_next_time(rule_part, traces)
                        step_time = trace['iterations-t'] - children_time 
                        display_string += "{}{} {} {} {}\n".format("  " * (level + 1),
                                                                "Step",
                                                                step_time.total_seconds(),
                                                                (step_time / total_time) if total_time.total_seconds() > 0 else 0,
                                                                str(child_nodes)[1:-1])                       
                    else:
                        try:
                            display_string += "{}{} {} - Avg: {}  Tot: {} - Avg: {:%}  Tot: {:%}\n".format("  " * (level + 2), 
                                                                                key, 
                                                                                trace[key], 
                                                                                trace[key + '-t'].total_seconds() / trace[key] if trace[key] > 0 else 0, 
                                                                                trace[key + '-t'].total_seconds(),
                                                                                ((trace[key + '-t'].total_seconds() / trace[key] if trace[key] > 0 else 0) / total_iterations) if total_iterations > 0 else 0,
                                                                                (trace[key + '-t'] / total_time) if total_time.total_seconds() > 0 else 0)
                        except:
                            print("key", key, "key time", trace[key+'-t'])
                            raise
                    if key != 'iterations':
                        total_count += trace[key]
            if total_count != trace['iterations']:
                display_string += "%sCalc Total %i\n" % ("  " * (level + 1), total_count)
            display_string += "%sTime %f Average %f\n\n" % ("  " * (level + 1), trace['iterations-t'].total_seconds(), (trace['iterations-t'].total_seconds() / total_count) if total_count > 0 else 0)
        for next_part in rule_part:
            display_string = display_trace_count(traces, next_part, total_iterations, total_time, level + 1, display_string)
    return display_string

def write_trace_count_csv(trace_count_file, rule_name, traces, rule_part, total_iterations, total_time):
    import csv
    
    trace_count = calc_trace_count(rule_name, traces, rule_part, total_iterations, total_time)
    with open(trace_count_file + ".csv", 'a', newline='') as o:
        csv_writer = csv.writer(o)
        csv_writer.writerows(trace_count)        
    
def calc_trace_count(rule_name, traces, rule_part, total_iterations, total_time, level=0, rows=None):
    if rows is None:
        rows = [['','', '', '', '', '', '', '', '', '', ''
                 ,'Total', '', '', '', '', '' #total iteraions
                 ,'Step', '', '', '' ,'' #Step time
                 ,'Evaluations', '', '', '', '', '' #Evaluations
                 ,'Table', '', '', '', '', '' #Table
                 ,'Cache', '', '', '', '', '' #cache
                 ,'Recalc', '', '', '', '', '' #Recalc
                 ,'Stop', '', '', '', '', '' #Iteration Stop
                 ],
                ['Rule', 'Id', 'Name', 'Notes', 'Instance', 'Rule Taxonomy', 'Number', 'Aligned', 'Dependent', 'Dependent Iterables', 'Iterable'
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #total iteraions
                 ,'secs', 'secs %', 'avg', 'avg %', 'nodes' #step times
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #Evaluations
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #Table
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #cache
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #Recalc
                 ,'it', 'it %', 'secs', 'secs %', 'avg', 'avg %' #Iteration Stop
                 ]]
    
    #Rows: name, notes, inst, rule tax, number, aligned, dependency, dependent iterables, iterable,
    #      For each count includes: iterations, percent, time, percent, avg time, percent
    #          total, E, T, c, R, is
    
    if isinstance(rule_part, ParseResults):
        additional = ''
        if rule_part['exprName'] == 'varRef':
            if rule_part.is_constant:
                additional =  "$" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + " - constant)"
            else:
                additional = "$" + rule_part.varName + " declaration: " + str(rule_part.var_declaration)
        elif rule_part['exprName'] == 'varAssign':
            additional = rule_part.varName + (" NOT USED" if rule_part.get('not_used') == True else "")
        elif rule_part['exprName'] == 'constantAssign':
            additional = rule_part.constantName
        elif rule_part['exprName'] == 'functionArg':
            additional = rule_part.argName
        elif rule_part['exprName'] == 'forExpr':
            additional = rule_part.forControl.forVar
        elif rule_part['exprName'] == 'reportDeclaration':
            additional = rule_part.reportName
        elif rule_part['exprName'] == 'raiseDeclaration':
            additional = rule_part.raiseName  
        elif rule_part['exprName'] == 'formulaDeclaration':
            additional = rule_part.formulaName                       
        elif rule_part['exprName'] in ('functionDeclaration', 'functionReference'):
            additional = rule_part.functionName + (" CACHEABLE" if rule_part.get('cacheable') == True else "") 

        row = [rule_name
               ,rule_part['node_id']
               ,('  ' * level) + rule_part['exprName']                              #name
               ,additional                                      #notes
               ,True if rule_part.get('instance') else False    #instance
               ,True if rule_part.get('rules-taxonomy') else False #rule taxonomy
               ,rule_part.number == 'single'                    #nubmer
               ,True if rule_part.has_alignment else False      #aligned
               ,("D" if rule_part.is_dependent else "I") if 'is_dependent' in rule_part else "" #dependency
               ,str({dep['node_id'] for dep in rule_part.dependent_iterables}) if len(rule_part.dependent_iterables) > 0 else "" #dependent iterables
               ,'is_iterable' in rule_part                      #iterable
               ]
        
        if rule_part['node_id'] in traces:            
            trace = traces[rule_part['node_id']]
            
            #add total values to the row
            row += trace_count_by_type('iterations', trace, total_iterations, total_time)
            
            #add step values
            children_time, child_nodes = trace_count_next_time(rule_part, traces)
            step_time = trace['iterations-t'] - children_time 
            row += [step_time.total_seconds()
                    ,((step_time.total_seconds() / total_time.total_seconds()) if total_time.total_seconds() > 0 else 0) * 100
                    ,(step_time.total_seconds() / trace['iterations']) if trace['iterations'] > 0 else 0
                    ,((((step_time.total_seconds() / trace['iterations']) if trace['iterations'] > 0 else 0) / total_iterations) if total_iterations > 0 else 0) * 100
                    , str(child_nodes)[1:-1]]
            
            #row += ['','','','','']
                       
            #add values by evaluation type
            calc_total = 0
            for count_codes in [['E','e'],['T'],['c'],['R','r'],['isE', 'ise']]:
                if len(count_codes) == 1:
                    count_code = count_codes[0]
                else:
                    count_code = count_codes[0] if trace[count_codes[0]] != 0 else count_codes[1]
                calc_total += trace[count_code]
                row += trace_count_by_type(count_code, trace, total_iterations, total_time)
            
            if calc_total != trace['iterations']:
                row.append("ITERATION COUNT DOES NOT TOTAL. Calc total is", calc_total)
            
        rows.append(row)
              
        for next_part in rule_part:
            rows = calc_trace_count(rule_name, traces, next_part, total_iterations, total_time, level + 1, rows)
    return rows

def trace_count_by_type(count_code, trace, total_iterations, total_time):
    time_code = count_code + '-t'
    return [trace[count_code]
            ,''
            ,trace[time_code].total_seconds()
            ,(trace[time_code].total_seconds() / total_time.total_seconds() * 100) if total_time.total_seconds() > 0 else 0
            ,(trace[time_code].total_seconds() / trace[count_code]) if trace[count_code] > 0 else 0
            ,(((trace[time_code].total_seconds() / trace[count_code] if trace[count_code] > 0 else 0) / total_iterations) if total_iterations > 0 else 0) * 100
            ]    

def trace_count_next_time(rule_part, traces):
    total_child_times = datetime.timedelta()
    total_child_nodes = []
    
    if isinstance(rule_part, ParseResults):
        for child in rule_part:

            if isinstance(child, ParseResults):
                if child['exprName'] != 'varAssign':
                    if child['node_id'] in traces:
                        total_child_times += traces[child['node_id']]['iterations-t']
                        total_child_nodes.append(child['node_id'])
                        #return (traces[child['node_id']]['iterations-t'], child['node_id'])
                    else:
                        child_info = trace_count_next_time(child, traces)
                        total_child_times += child_info[0]
                        total_child_nodes += child_info[1]
    return (total_child_times, total_child_nodes)
    
            
    