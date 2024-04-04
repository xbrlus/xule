'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change$
'''
from .XuleContext import XuleGlobalContext, XuleRuleContext #XuleContext
from .XuleRunTime import XuleProcessingError, XuleIterationStop, XuleException, XuleBuildTableError, XuleReEvaluate
from .XuleValue import *
#from  .XuleFunctions import *
from .XuleMultiProcessing import output_message_queue
from pyparsing import ParseResults
import itertools as it
from arelle.ModelValue import QName, dayTimeDuration, DateTime, gYear, gMonthDay, gYearMonth
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelDtsObject import ModelConcept
import decimal
import datetime
import math
import re 
from aniso8601.__init__ import parse_duration, parse_datetime, parse_date
import collections
import copy
from lxml import etree as et
from threading import Thread
from . import XuleFunctions as xf
import os

def process_xule(rule_set, model_xbrl, cntlr, options):

    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, options
                                       #multi=getattr(options, "xule_multi", False), async=getattr(options, "xule_async", False),
                                       #cpunum=getattr(options, "xule_cpu", None)
                                       )
     
    global_context.options = options
   
    #global_context.show_timing = show_timing
    #global_context.show_debug = show_debug
    #global_context.show_debug_table = show_debug_table
    #global_context.show_trace = show_trace
    if getattr(global_context.options, "xule_trace_count", False):
    #if trace_count_file is not None:        
        #global_context.show_trace_count = True
        #global_context.trace_count_file = trace_count_file
        try:
            os.remove(global_context.options.xule_trace_count + ".csv")
        except FileNotFoundError:
            pass
        try:
            os.remove(global_context.options.xule_trace_count + ".txt")
        except FileNotFoundError:
            pass
    #global_context.crash_on_error = crash_on_error
    #if no_cache == True:
    #    global_context.no_cache = True
        
    #if precalc_constants == True:
    #    global_context.precalc_constants = True
    
    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        total_start = datetime.datetime.today()
        
    if getattr(global_context.options, "xule_multi", False):
        t = Thread(target=output_message_queue, args=(global_context,))
        t.name = "Message Queue"
        t.start()
  
    xule_context = XuleRuleContext(global_context)

    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        fact_index_start = datetime.datetime.today()
    global_context.fact_index = index_model(xule_context)
    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        fact_index_end = datetime.datetime.today()
        global_context.message_queue.print("Index build time %s." % (fact_index_end - fact_index_start))

#     if pre_calc:
#         if global_context.show_timing is not None:
#             pre_calc_start = datetime.datetime.today()
#         pre_calc_expressions(global_context)
#         if global_context.show_timing is not None:
#             pre_calc_end = datetime.datetime.today()
#             global_context.message_queue.print("Pre-calc build time %s." % (pre_calc_end - pre_calc_start))

    skip_rules = getattr(global_context.options, "xule_skip", None).split(",") if getattr(global_context.options, "xule_skip", None) is not None else None

    if getattr(global_context.options, "xule_precalc_constants", False):
    #if global_context.precalc_constants:
        constant_start = datetime.datetime.today()
        process_precalc_constants(global_context)
        process_precalc_preconditions(global_context)
        constant_end = datetime.datetime.today()
        constant_time = constant_end - constant_start
        global_context.message_queue.print("Time to calculated non instance constants: %s" % (constant_time))

    global_context.message_queue.logging("Processing Filing...")
    evaluate_rule_set(global_context, skip_rules)
    
    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        total_end = datetime.datetime.today()
        if getattr(global_context.options, "xule_precalc_constants", False):
        #if global_context.precalc_constants:
            global_context.message_queue.print("Time to process excluding non instance constant: %s." % (total_end - total_start - constant_time))       
        global_context.message_queue.print("Total time to process: %s." % (total_end - total_start))
    # Shutdown Message Queue
    if getattr(global_context.options, "xule_multi", False):
        global_context.message_queue.stop()
        global_context.message_queue.clear()
        t.join()  
    
        
def evaluate_rule_set(global_context, skip_rules):
    ''' NEED TO CHECK THE RULE BASE PRECONDITION '''
    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        times = []

    #Check rule base preconditions
    if not rule_base_preconditions_pass(global_context):
        if getattr(global_context.options, "xule_debug", False):
        #if global_context.show_debug:
            global_context.message_queue.print("Rule base preconditions did not pass")
    else:
        #use the term "cat" for catalog information
        for file_num, cat_rules in global_context.catalog['rules_by_file'].items():
            for rule_name in sorted(cat_rules.keys()):
                cat_rule = cat_rules[rule_name]
            
                if skip_rules and rule_name in skip_rules:
                    global_context.message_queue.print("Skipping rule: %s" % rule_name)
                    continue
                
                rule = global_context.rule_set.getItem(cat_rule)
                
                if getattr(global_context.options, "xule_debug", False):
                #if global_context.show_debug:
                    global_context.message_queue.print("Processing: %s - %s" % (rule_name, datetime.datetime.today().strftime("%H:%M:%S.%f")))
                    global_context.message_queue.print(global_context.model.modelDocument.uri)
                    
                if check_precondition(rule.preconditionRef, global_context) if 'preconditionRef' in rule else True:                                        
                    try:
                        if getattr(global_context.options, "xule_time", None) is not None or getattr(global_context.options, "xule_trace_count", False):
                        #if global_context.show_timing is not None or global_context.show_trace_count:
                            rule_start = datetime.datetime.today()
        
                        xule_context = XuleRuleContext(global_context,
                                                       rule_name,
                                                       file_num)
                        #add the main table
                        xule_context.iteration_table.add_table(rule.node_id, xule_context.get_processing_id(rule.node_id))
                        assign_severity(rule, xule_context)
        
                        #if pre_check(rule, xule_context):
                        
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
                #if global_context.show_timing is not None:
                    rule_end = datetime.datetime.today()
                    times.append((xule_context.rule_name, rule_end - rule_start))
                    if getattr(global_context.options, "xule_debug", False):
                        global_context.message_queue.print("%s time took: %s - %s " % (rule_name, (rule_end - rule_start).total_seconds(), datetime.datetime.today().strftime("%H:%M:%S.%f")))
                
                if getattr(global_context.options, "xule_trace_count", False):
                #if global_context.show_trace_count:
                    total_time = datetime.datetime.today() - rule_start
                    print("Total iterations:", xule_context.iter_count, 
                          "Messages:", xule_context.iter_message_count, 
                          "Pass:", xule_context.iter_pass_count, 
                          "Non alignment:", xule_context.iter_misaligned_count,
                          "Exception:", xule_context.iter_except_count)
                    write_trace_count_csv(global_context.options.xule_trace_count, rule_name, global_context.expression_trace, rule, xule_context.iter_count, total_time)
                    write_trace_count_string(global_context.options.xule_trace_count, rule_name, global_context.expression_trace, rule, xule_context.iter_count, total_time)

    if getattr(global_context.options, "xule_time", None) is not None:
    #if global_context.show_timing is not None:
        global_context.message_queue.print("Total number of rules processed: %i" % len(times))
        #slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > 0.001]
        slow_rules = sorted([timing_info for timing_info in times if timing_info[1].total_seconds() > getattr(global_context.options, "xule_time", None)],
                            key=lambda tup: tup[1], reverse=True)
        #slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > global_context.show_timing]
        global_context.message_queue.print("Number of rules over %ss: %i" % (getattr(global_context.options, "xule_time", None), len(slow_rules)))
        for slow_rule in slow_rules:
            global_context.message_queue.print("Rule %s end. Took %s" % (slow_rule[0], slow_rule[1]))   
        #global_context.message_queue.print("Global expression cache size: %i" % len(global_context.expression_cache))

def rule_base_preconditions_pass(global_context):
    if global_context.catalog['rule_base'] is None:
        return True
    else:
        rule_base = global_context.rule_set.getItem(global_context.catalog['rule_base'])
        if 'preconditionRef' in rule_base:
            return check_precondition(rule_base.preconditionRef, global_context)
        else:
            return True

def pre_check(rule, xule_context):
    if 'pre_check' in rule:
        xule_qname = evaluate_qname_literal(rule.pre_check, xule_context)
        if xule_qname.value in xule_context.fact_index[('builtin', 'lineItem')]:
            return True
        else:
            return False
    else:
        return True

def index_model(xule_context):
    fact_index = collections.defaultdict(lambda :collections.defaultdict(set))

    #fact_index[('builtin', 'lineItem')] = xule_context.model.factsByQname
    
    facts_to_index = collections.defaultdict(list)
    for model_fact in xule_context.model.factsInInstance:
        all_aspects = list()
        all_aspects.append((('builtin', 'lineItem'),model_fact.qname))
        
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
            unit = model_to_xule_unit(model_fact.unit.measures, xule_context)
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
        
    #get all the facts
    all_facts = {fact for facts in facts_to_index.values() for fact in facts}
    #for each aspect add a set of facts that don't have that aspect with a key value of None
    for aspect_key in fact_index:
        fact_index[aspect_key][None] = all_facts - set(it.chain.from_iterable(fact_index[aspect_key].values()))
    #save the list of all facts. 
    fact_index['all'] = all_facts
    
    return fact_index

def get_decimalized_value(fact_a, fact_b, xule_context):
    fact_a_decimals = get_decimals(fact_a, xule_context)
    fact_b_decimals = get_decimals(fact_b, xule_context)
    
    min_decimals = min(fact_a_decimals, fact_b_decimals)
    
    fact_a_value = fact_a.xValue if fact_a_decimals == float('inf') else round(fact_a.xValue, min_decimals)
    fact_b_value = fact_b.xValue if fact_b_decimals == float('inf') else round(fact_b.xValue, min_decimals)
    
    return fact_a_value, fact_a_decimals, fact_b_value, fact_b_decimals

def get_decimals(fact, xule_context):
    if fact.decimals is None:
        return float('inf')
    
    if fact.decimals.strip() == 'INF':
        return float('inf')
    else:
        try:
            return int(fact.decimals)
        except ValueError:
            raise XuleProcessingError(_("%s Fact contains invalid decimal value of %s" % (fact.qname, fact.decimals)), xule_context)


def assign_severity(rule, xule_context):
    severity = rule.get('severity')
    if severity:
        if severity in xule_context.STATIC_SEVERITIES:
            xule_context.severity_type = xule_context.SEVERITY_TYPE_STATIC
            xule_context.severity = severity
        else:
            #the severity must be a severity function
            function_info = xule_context.find_function(severity)
            if function_info is None:
                raise XuleProcessingError(_("Severity function '%s' does not exist" % severity), xule_context)
            else:
                xule_context.severity_type = xule_context.SEVERITY_TYPE_FUNCTION
                xule_context.severity = severity   
    else:
        if rule.getName() == 'reportDeclaration':
            #default to ERROR for report rules
            xule_context.severity_type = xule_context.SEVERITY_TYPE_STATIC
            xule_context.severity = xule_context.SEVERITY_INFO
        else:
            #dynamic severity
            xule_context.severity_type = xule_context.SEVERITY_TYPE_DYNAMIC  
        
def evaluate(rule_part, xule_context, constant_id=None, is_values=False, trace_dependent=False, override_table_id=None):
    #print("evaluate: ", rule_part.getName(), rule_part.node_id)    
    try:
        #values expression. The expression inside the 'values' expression is substituted for the rule_part.
        if rule_part.getName() == 'valuesExpr':
            validate_values(rule_part, xule_context)
            rule_part = rule_part[0]
        
        if getattr(xule_context.global_context.options, "xule_trace", False) or getattr(xule_context.global_context.options, "xule_trace_count", False):    
        #if xule_context.show_trace or xule_context.show_trace_count:
            trace_is_dependent = "D" if trace_dependent else " "
            trace_source = "U"
            trace_written = False
        if getattr(xule_context.global_context.options, "xule_trace_count", False):
        #if xule_context.show_trace_count:
            if rule_part.node_id not in xule_context.expression_trace:
                xule_context.expression_trace[rule_part.node_id] = {'iterations': 1, # total 
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
                                                                    'name': rule_part.getName()
                                                                    }
            else:
                xule_context.expression_trace[rule_part.node_id]['iterations'] += 1
            expression_trace_start = datetime.datetime.today()            
            
        processing_id = xule_context.get_processing_id((rule_part.node_id + .1) if is_values else rule_part.node_id)
        rule_part_name = rule_part.getName()
        #trace
        if getattr(xule_context.global_context.options, "xule_trace", False):
        #if xule_context.show_trace:
            xule_context.trace_level += 1
             
            trace = "  " * xule_context.trace_level
            trace += rule_part_name + " " + str(processing_id) #+ " " + str(rule_part)
            print(">",trace_is_dependent, " ", processing_id, trace.replace("\n", " "))
    
        if ('is_iterable' in rule_part or 
            constant_id is not None):
            
            xule_context.used_expressions.add(processing_id)
            
            #is_iterable is always true if it is present, so done't need to check the actual value   
            if 'is_dependent' in rule_part:
                is_dependent = rule_part.is_dependent
    
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
                            if (rule_part.table_id != xule_context.iteration_table.main_table_id or
                                is_dependent):
                                
                                local_cache_key =  get_local_cache_key(rule_part, xule_context) 
                                if local_cache_key is not None:                                                                                  
                                    values = xule_context.local_cache.get(local_cache_key)
                                    #print("checking", "not found" if values is None else "found", rule_part.node_id, [(x[0], x[1].format_value()[:10]) for x in local_cache_key[1]])
                        
                        if values is None:                        
                            values = EVALUATOR[rule_part_name](rule_part, xule_context)
                            trace_source = "E" 
                            if rule_part.get('values_expression') == True and not rule_part_name == 'factset':
                                values = strip_alignment(values)
                            if not getattr(xule_context.global_context.options, "xule_no_cache", False):
                            #if not xule_context.global_context.no_cache:
                                if (rule_part.table_id != xule_context.iteration_table.main_table_id or
                                is_dependent):
                                    local_cache_key =  get_local_cache_key(rule_part, xule_context) 
                                    if local_cache_key is not None:  
                                        #print("caching", rule_part.node_id, [(x[0], x[1].format_value()[:10]) for x in local_cache_key[1]], len(values.values))
                                        xule_context.local_cache[local_cache_key] = values 
                        else:
                            #print("using cache", rule_part.node_id, [x[0] for x in local_cache_key[1]])
                            trace_source = "c"
                    except XuleIterationStop:
                        if getattr(xule_context.global_context.options, "xule_trace", False):
                        #if xule_context.show_trace: 
                            xule_context.trace_level -= 1
                        if getattr(xule_context.global_context.options, "xule_trace_count", False):
                        #if xule_context.show_trace_count:
                            xule_context.expression_trace[rule_part.node_id]['iterations-t'] += datetime.datetime.today() - expression_trace_start
                            xule_context.expression_trace[rule_part.node_id]['isE-t'] += datetime.datetime.today() - expression_trace_start
                            xule_context.expression_trace[rule_part.node_id]['isE'] += 1
                            trace_written = True
                        raise
                    except XuleReEvaluate:
                        trace_source = 'R'
                        raise
#                     except Exception as e:
#                         import traceback
#                         import sys
#                         print("Exception 3", "iteration", ii, "rule id", rule_part.node_id, rule_part_name, sys.exc_info()[0])
#                         traceback.print_tb(sys.exc_info()[2], file=sys.stdout)
#                         raise                                        
                    else:
                        #add - add values to expression cache
                        xule_context.iteration_table.add_column(rule_part, override_table_id or rule_part.table_id, processing_id, values, xule_context)
                        value = xule_context.iteration_table.current_value(processing_id, xule_context)           
                else:
                    trace_source = "T"
            else:
                raise XuleProcessingError(_("Internal error: Found iterable (%s) that does not have a dependency flag." % rule_part_name),xule_context)
        else: # is_iterable
            trace_source = "e"
            try:
                value = EVALUATOR[rule_part_name](rule_part, xule_context)
            except XuleIterationStop:
                if getattr(xule_context.global_context.options, "xule_trace", False):
                #if xule_context.show_trace: 
                    xule_context.trace_level -= 1
                if getattr(xule_context.global_context.options, "xule_trace_count", False):
                #if xule_context.show_trace_count:
                    xule_context.expression_trace[rule_part.node_id]['iterations-t'] += datetime.datetime.today() - expression_trace_start
                    xule_context.expression_trace[rule_part.node_id]['ise-t'] += datetime.datetime.today() - expression_trace_start
                    xule_context.expression_trace[rule_part.node_id]['ise'] += 1
                    trace_written = True
                raise
            except XuleReEvaluate as e:
                trace_source = 'r'
                raise
#             except Exception as e:
#                 import traceback
#                 import sys
#                 print("Exception 1", "iteration", ii, "rule id", rule_part.node_id, rule_part_name, sys.exc_info()[0])
#                 traceback.print_tb(sys.exc_info()[2], file=sys.stdout)
#                 raise
    
        #If the look_for_alignment flag is set, check if there is now alignment after adding the column. This is used in 'where' clause processing.
        #if xule_context.look_for_alignment and xule_context.iteration_table.any_alignment is not None:
        if (xule_context.look_for_alignment and 
            #rule_part.has_alignment and
            value.aligned_result_only and
            rule_part.table_id in xule_context.where_table_ids and
            rule_part.node_id in xule_context.where_dependent_iterables):
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
#             print("Exception 2", "iteation", ii, "rule id", rule_part.node_id, rule_part_name, sys.exc_info()[0])
#             traceback.print_tb(sys.exc_info()[2], file=sys.stdout)
#             raise
        finally:
            if getattr(xule_context.global_context.options, "xule_trace_count", False):
            #if xule_context.show_trace_count:
                xule_context.expression_trace[rule_part.node_id][trace_source] += 1
                xule_context.expression_trace[rule_part.node_id]['iterations-t'] += (datetime.datetime.today() - expression_trace_start)
                xule_context.expression_trace[rule_part.node_id][trace_source + '-t'] += (datetime.datetime.today() - expression_trace_start)
                trace_written = True
    finally:
        if getattr(xule_context.global_context.options, "xule_trace_count", False) and not trace_written:
        #if xule_context.show_trace_count and not trace_written:
#            print("trace not written", "iteration", ii, "rule id", rule_part.node_id, trace_source)
            xule_context.expression_trace[rule_part.node_id]['iterations-t'] += datetime.datetime.today() - expression_trace_start
            xule_context.expression_trace[rule_part.node_id][trace_source + '-t'] += (datetime.datetime.today() - expression_trace_start)
            xule_context.expression_trace[rule_part.node_id][trace_source] += 1  
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
        xule_context.tags.update(value.tags)
    if value.aligned_result_only == True:
        xule_context.aligned_result_only = True
    
#     if value.used_vars is not None:
#         new_keys = value.used_vars.keys() - xule_context.vars.keys() 
#         for new_key in new_keys:
#             xule_context.vars[new_key] = value.used_vars[new_key]
    
    if value.used_expressions is not None:
        #print("add",rule_part.getName(), rule_part.node_id, len(xule_context.used_expressions), len(value.used_expressions))
        xule_context.used_expressions.update(value.used_expressions)
    
    if value.type == 'unbound':
        raise XuleIterationStop(value)


    return value

# def get_cache_key(rule_part, dependent_alignment, xule_context):
#     
#     if rule_part.getName() in ('constantAssign','forControl'):
#         return None
#     
#     if rule_part.getName() == 'functionReference' and len(rule_part.functionArgs) > 0:
#         return None
#     
#     cache_var_key = {}
# 
#     for dep_expr in rule_part.dependent_iterables:
#         if dep_expr.node_id != rule_part.node_id:
#             cache_var_key[dep_expr.node_id] = evaluate(dep_expr, xule_context)
#     '''
#     This is removed. The cache key is now based on the dependent_iterables instead of dependent vars
# 
#     for var_ref in rule_part.var_refs:
#         #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
#         var_info = xule_context.find_var(var_ref[1], var_ref[0])
#         var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context) 
#         cache_var_key[var_ref[0]] = var_value     
#     '''
#     return (rule_part.node_id, dependent_alignment, frozenset(cache_var_key.items()))
        
def get_local_cache_key(rule_part, xule_context):
    #processing_id = xule_context.get_processing_id(rule_part.node_id)
    #value = xule_context.iteration_table.current_value(processing_id, xule_context)
    
    #Don't cache for function refs that are not cacheable
    if (rule_part.getName() in ('functionReference', 'macroRef') and rule_part.get('cacheable') != True) or rule_part.getName() == 'forBodyExpr':
        return None
    
    dep_var_index = set()
    for var_ref in rule_part.var_refs:
        #var_ref tuple: 0 = var declaration id, 1 = var name, 2 = var ref ast, 3 = var type (1=block variable or 'for' variable, 2=constant, 3=function argument, factset variable)
        var_info = xule_context.find_var(var_ref[1], var_ref[0])
        if var_info['type'] == xule_context._VAR_TYPE_CONSTANT:
            #If it is a constant, the var_info will not contain the value. To determine if the constant is used, the used_expressions are checked.
            if xule_context.get_processing_id(var_info['expr'].node_id) in xule_context.used_expressions:
                const_value = evaluate(var_info['expr'], 
                                                   xule_context, 
                                                   override_table_id=var_ref[2].table_id, 
                                                   is_values='values_expression' in var_ref[2])
                dep_var_index.add((var_info['name'], const_value))
        else:
            if var_ref[0] in xule_context.vars:
                if var_info['calculated']:
                    dep_var_index.add((var_info['name'], var_info['value']))
       
    alignment = xule_context.iteration_table.current_alignment if rule_part.has_alignment else None
    
    cache_key = (rule_part.node_id, frozenset(dep_var_index), alignment)

#         master_index = set()  
#         for dep in rule_part.dependent_iterables:
#             #don't include the self reference to the current node
#             ''''THIS NEEDS TO BE REMOVED IN THE POST PARSE'''
#             if rule_part.node_id != dep.node_id:
#                 master_processing_id = xule_context.get_processing_id(dep.node_id)
#                 #create the master index for the dependent column
#                 if master_processing_id in xule_context.iteration_table._columns:
#                     master_table = xule_context.iteration_table._columns[master_processing_id]
#                     if master_processing_id in master_table._used_columns:
#                         master_index.add((master_processing_id, master_table._current_iteration[master_processing_id]))        
#             
#         cache_key = (rule_part.node_id, frozenset(master_index))

    return cache_key

def evaluate_raise_declaration(raise_rule, xule_context):

    '''NEED TO CHECK THE PRE CONDITION'''

    if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
        raise XuleProcessingError(_("A raise rule cannot have a severity function, found '%s'" % xule_context.severity_type), xule_context)

    while True:
        xule_context.iter_count += 1
        try:
            xule_value = evaluate(raise_rule.expr[0], xule_context)
        except XuleIterationStop:
            xule_context.iter_pass_count += 1
            pass
        except:
            xule_context.iter_except_count += 1
            raise
        else:
            if not(xule_context.iteration_table.current_alignment is None and xule_context.aligned_result_only): 
#                 if xule_context.show_trace:
#                     print(format_trace(xule_context))
                
                send_message = True
                
                if xule_value.type == 'unbound':
                    send_message = False
                
                if send_message:
                    if xule_context.severity_type == xule_context.SEVERITY_TYPE_STATIC:
                        severity = xule_context.severity.upper()
                        if not isinstance(xule_value.value, bool):
                            raise XuleProcessingError(_("Raise %s did not evaluate to a boolean, found '%s'." % (xule_context.rule_name, xule_value.type)), xule_context)
                        
                        if xule_value.value == False:
                            #skip this result
                            send_message = False
                    else:
                        if xule_value.type != 'severity':
                            raise XuleProcessingError(_("Dynamic severity rules must return a severity, found '%s'" % xule_value.type), xule_context)
                        
                        if xule_value.value == 'pass':
                            send_message = False
                        
                        severity = xule_value.value.upper()
            
                if send_message:
                    xule_context.iter_message_count += 1
                    message_context = xule_context.create_message_copy(xule_context.get_processing_id(raise_rule.node_id))
                    message = get_message(raise_rule, xule_value, xule_context.iteration_table.current_alignment, message_context)
                    source_location = get_element_identifier(xule_value, xule_context)
                    filing_url = xule_context.model.modelDocument.uri
            
                    xule_context.global_context.message_queue.log(severity,
                                                                  xule_context.rule_name, 
                                                                  #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                                                  message,
                                                                  #sourceFileLine=[node.sourceFileLine] + 
                                                                  #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                                                  sourceFileLine=[source_location],
                                                                  severity=severity,
                                                                  filing_url=filing_url)        
                else:
                    xule_context.iter_pass_count += 1
            else:
                xule_context.iter_misaligned_count += 1
        #xule_context.iteration_table.del_current()
        #if xule_context.iteration_table.is_empty:
        xule_context.iteration_table.next(raise_rule.node_id)
        if xule_context.iteration_table.is_table_empty(raise_rule.node_id):
            break
        else:
            xule_context.reset_iteration()

def evaluate_report_declaration(report_rule, xule_context): 
    
    '''NEED TO CHECK THE PRECONDITION'''
    
    if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
        raise XuleProcessingError(_("A report rule cannot have a severity function, found '%s'" % xule_context.severity_type), xule_context)
    
    while True:
        try:
            xule_value = evaluate(report_rule.expr[0], xule_context)
        except XuleIterationStop as xis:
            pass
        else:   
            if not(xule_context.iteration_table.current_alignment is None and xule_context.aligned_result_only):    
        #         if xule_context.severity_type == xule_context.SEVERITY_TYPE_STATIC:
        #             severity = xule_context.severity.upper()
        #         else:
        #             raise XuleProcessingError(_("Dynamic severity rules must return a severity, found '%s'" % result.type), xule_context)
        
        #            severity = result.value.upper()
        
#                 if xule_context.show_trace:
#                     print(format_trace(xule_context))
        
                message_context = xule_context.create_message_copy(xule_context.get_processing_id(report_rule.node_id))
                message = get_message(report_rule, xule_value, xule_context.iteration_table.current_alignment, message_context)
                source_location = get_element_identifier(xule_value, xule_context)
                filing_url = xule_context.model.modelDocument.uri
                
                '''
                xule_context.model.log(xule_context.severity.upper(),
                                       xule_context.rule_name, 
                                       #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                       message,
                                       #sourceFileLine=[node.sourceFileLine] + 
                                       #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                       sourceFileLine=source_location,
                                       severity=xule_context.severity,
                                       filing_url=filing_url)
                '''
                xule_context.global_context.message_queue.log(xule_context.severity.upper(),
                                                              xule_context.rule_name, 
                                                              #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                                              message,
                                                              #sourceFileLine=[node.sourceFileLine] + 
                                                              #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                                              sourceFileLine=source_location,
                                                              severity=xule_context.severity.upper(),
                                                              filing_url=filing_url) 
            
        #xule_context.iteration_table.del_current()    
        #if xule_context.iteration_table.is_empty:
        xule_context.iteration_table.next(report_rule.node_id)
        if xule_context.iteration_table.is_table_empty(report_rule.node_id):
            break
        else:
            xule_context.reset_iteration()

def evaluate_formula_declaration(formula_rule, xule_context):
    '''NEED TO CHECK THE PRECONDITION'''
    if xule_context.severity_type == xule_context.SEVERITY_TYPE_DYNAMIC:
        raise XuleProcessingError(_("A formula rule cannot have dynamic severity, found '%s'" % xule_context.severity_type), xule_context)
    
    xule_context.formula_bind = formula_rule.bind[0]

    while True:
        try:
            xule_value = evaluate(formula_rule.expr[0], xule_context)
        except XuleIterationStop:
            pass
        else:
#             print("aligned only", xule_context.aligned_result_only)
#             print("current alignment", xule_context.iteration_table.current_alignment if xule_context.iteration_table.current_alignment is not None else "none")
#             if not(xule_context.iteration_table.current_alignment is None and xule_context.aligned_result_only): 
#                 if xule_context.show_trace:
#                     print(format_trace(xule_context))

#                 print("left", xule_context.formula_left)
#                 print("right", xule_context.formula_right)
#                 print("diff", xule_context.formula_difference)
                    
                if 'left' not in xule_context.tags or 'right' not in xule_context.tags or 'difference' not in xule_context.tags:
                    raise XuleProcessingError(_("The formula rule did not execute a formula operation (:=)"), xule_context)
                
                if xule_value.type != 'formula':
                    raise XuleProcessingError(_("The formula result must be a formula expression (:=), found '%s'" % xule_value.type), xule_context)

                send_message = True
                
                if xule_value.type == 'unbound':
                    send_message = False
    
                if send_message:
                    if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
                        # severity function
                        function_info = xule_context.find_function(xule_context.severity)   
                        
                        if 'functionArgs' in function_info['function_declaration']:
                            for functionArg in function_info['function_declaration'].functionArgs:
                                if functionArg.argName == 'difference':
                                    xule_context.add_arg('difference',
                                          functionArg.node_id,
                                          False,
                                          xule_context.tags['difference'],
                                          'single')
                                elif functionArg.argName == 'left':     
                                    xule_context.add_arg('left',
                                          functionArg.node_id,
                                          False,
                                          xule_context.tags['left'],
                                          'single')
                                elif functionArg.argName == 'right':                            
                                    xule_context.add_arg('right',
                                          functionArg.node_id,
                                          False,
                                          xule_context.tags['right'],
                                          'single')                
                                    
                        severity_context = xule_context.create_message_copy(xule_context.get_processing_id(formula_rule.node_id))
                        
                        function_info = xule_context.find_function(xule_context.severity)                        
                        severity_function_value = evaluate(function_info['function_declaration'].expr[0], severity_context)
                        
                        if severity_function_value.type != 'severity':
                            raise XuleProcessingError(_("severity function did not return a severity, fount '%s'" % severity_function_value.type), xule_context)
                        else:
                            severity = severity_function_value.value.upper()
                    else:
                        if xule_context.tags['difference'].value != 0:
                            severity = xule_context.severity.upper()
                        else:
                            severity = 'PASS'
            
                    if severity != 'PASS':
        
                        message_context = xule_context.create_message_copy(xule_context.get_processing_id(formula_rule.node_id))
                        message = get_message(formula_rule, XuleValue(message_context, False, 'bool'), xule_context.iteration_table.current_alignment, message_context)
                        source_location = get_element_identifier(xule_value, xule_context)
                        filing_url = xule_context.model.modelDocument.uri
                            
                        xule_context.global_context.message_queue.log(severity,
                                                                      xule_context.rule_name, 
                                                                      #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                                                      message,
                                                                      #sourceFileLine=[node.sourceFileLine] + 
                                                                      #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                                                      sourceFileLine=[source_location],
                                                                      severity=severity,
                                                                      filing_url=filing_url)    

        #xule_context.iteration_table.del_current()    
        #if xule_context.iteration_table.is_empty:
        xule_context.iteration_table.next(formula_rule.node_id)
        if xule_context.iteration_table.is_table_empty(formula_rule.node_id):
            break
        else:
            xule_context.reset_iteration()
    
def evaluate_bool_literal(literal, xule_context):
    if literal.value == "true":
        return XuleValue(xule_context, True, 'bool')
    elif literal.value == "false":
        return XuleValue(xule_context, False, 'bool')
    else:
        raise XuleProcessingError(_("Invalid boolean literal found: %s" % literal.value), xule_context)

def evaluate_string_literal(literal, xule_context):
    quote_char = literal.value[0]
    string_literal = literal.value[1:-1] #this removes the first and last characters. These are the quotes around the string
    
    string_literal = string_literal.replace('\\\\', '\a\a\a') # \a is the bell character
    string_literal = string_literal.replace('\\' + quote_char, quote_char)
    string_literal = string_literal.replace('\\n', '\n')
    string_literal = string_literal.replace('\\t', '\t')
    string_literal = string_literal.replace('\a\a\a', '\\')

    return XuleValue(xule_context, string_literal, 'string')

def evaluate_int_literal(literal, xule_context):
    return XuleValue(xule_context, int(literal.value), 'int')

def evaluate_float_literal(literal, xule_context):
    return XuleValue(xule_context, float(literal.value), 'float')

def evaluate_void_literal(literal, xule_context):
    ''' This could be 'none' or 'unbound'.
    '''
    return XuleValue(xule_context, None, literal.value)

def evaluate_qname_literal(literal, xule_context):
    prefix = literal.prefix #if literal.prefix == '*' else literal.prefix[0]
    #'''THIS NEEDS FIXING. THE file_num IS THE ORIGNAL FILE NUMBER, BUT IT MAY HAVE CHANGED WHEN PROCESSING FUNCTIONS OR CONSTANTS'''
    #namespace = xule_context.rule_set.getNamespaceUri(prefix, xule_context.cat_file_num)
    return XuleValue(xule_context, QName(prefix if prefix != '*' else None, literal.namespace_uri, literal.localName), 'qname')

def evaluate_severity(severity_expr, xule_context):
    severity_value = XuleValue(xule_context, severity_expr.severityName, 'severity')
    
    for severity_arg in severity_expr.severityArgs:
        try:
            arg_value = evaluate(severity_arg.argExpr[0], xule_context)
        except XuleIterationStop as xis:
            arg_value = xis.stop_value #XuleValue(xule_context, None, 'unbound')
        xule_context.tags[severity_arg.tagName] = arg_value.tag
 
    return severity_value

def evaluate_tagged(tagged_expr, xule_context):
    try:
        tagged_value = evaluate(tagged_expr.expr[0], xule_context)
    except XuleIterationStop as xis:
        xule_context.tags[tagged_expr.tagName] = xis.stop_value.tag          
        raise
    else:
        #xule_context.tags[tagged_expr.tagName] = tagged_value
        if tagged_value.tags is None:
            tagged_value.tags = {tagged_expr.tagName: tagged_value}
        else:
            tagged_value.tags[tagged_expr.tagName] = tagged_value
        
    return tagged_value

def tag_default_for_factset(expr, xule_context):
    #for lineItem[]
    if 'lineItemAspect' in expr:
        fact_name_value = evaluate(expr.lineItemAspect.qName, xule_context)
        return str(fact_name_value.value)
    else:
        #for [lineItem =/in ]
        if 'aspectFilters' in expr:
            found_line_item = False
            for aspect_filter in expr.aspectFilters:
                if (aspect_filter.aspectName.qName.prefix == "*" and
                    aspect_filter.aspectName.qName.localName == 'lineItem'):
                    found_line_item = True
                    if aspect_filter.aspectOperator == "=":
                        #for [lineItem=] - this will pick up the first result
                        aspect_member_value = evaluate(aspect_filter.aspectExpr[0], xule_context)
                        return str(aspect_member_value.value)
                    else:
                        #for [lineItem in} - this will pick up each
                        aspect_member_set = evaluate(aspect_filter.aspectExpr[0], xule_context)
                        if len(aspect_member_set.value) > 0:
                            line_items = []
                            for aspect_member_value in aspect_member_set.value:
                                if aspect_member_value.type == 'qname':
                                    line_items.append(str(aspect_member_value.value))
                                elif aspect_member_value.type == 'concept':
                                    line_items.append(str(aspect_member_value.value.qname))
                            if len(line_items) == 1:
                                line_item_string = str(line_items[0])
                            else:
                                line_item_string = "one of (" + ", ".join(line_items) + ")"
                            return line_item_string
                        else:
                            return 'unknown'
            if not found_line_item:
                #doesn't have a line item at all
                return 'unknown'
        else:
            #there are no aspect fitlers
            return 'unknown'

def evaluate_block(block_expr, xule_context):
    var_assignments = [i for i in block_expr if i.getName() == 'varAssign']
    
    for var_assignment in var_assignments:
        xule_context.add_var(var_assignment.varName,
                             var_assignment.node_id,
                             var_assignment.tagged == '#',
                             var_assignment.expr[0])
    
#     var_info = xule_context.find_var(var_assignment.varName, var_assignment.node_id)
#     calc_var(var_info, None, xule_context)
    
    return evaluate(block_expr.expr[0], xule_context)

def evaluate_var_ref(var_ref, xule_context):
    #print(var_ref.node_id, var_ref.varName)
    var_info = xule_context.find_var(var_ref.varName, var_ref.var_declaration)
    #xule_context.used_vars.append(var_ref.var_declaration)
    
    try:
        var_value = calc_var(var_info, var_ref, xule_context)
    except XuleIterationStop as xis:
        var_value = xis.stop_value
        raise
#     finally:
#         if var_info['tagged']:
#             print("tagged: ", var_info['name'])
#             xule_context.tags[var_ref.varName] = var_value.tag
            #xule_context.tags[var_ref.varName] = var_value

#     print(1,var_info['name'])
#     print(2,var_value)
#     print(3,var_value.value)
 
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
                    raise
            finally:
                xule_context.aligned_result_only = xule_context.aligned_result_only or saved_aligned_result_only
                xule_context.used_expressions = saved_used_expressions | xule_context.used_expressions
                
#         else:
#             var_info['value'] = evaluate(var_info['expr'], xule_context)
        var_value = var_info['value']
    elif var_info['type'] == xule_context._VAR_TYPE_CONSTANT:
        #We should only end up here the first time the constant is referenced for the iteration.
        #The var_info is really the constant info from the global context
        var_value = evaluate(var_info['expr'], xule_context, override_table_id=const_ref.table_id, is_values='values_expression' in const_ref)
        #add the calculated value as an iteration variable.
#         const_info = xule_context.add_var(var_info['name'],
#                                          var_info['expr'].node_id,
#                                          var_info['tagged'],
#                                          var_info['expr'])
#         const_info['calculated'] = True
#         const_info['value'] = var_value
    
        '''
        if var_info['calculated'] == False:
            const_values = calc_constant(var_info, xule_context)
            var_info['calculated'] = True
            var_info['value'] = const_values
            #xule_context.global_context._constants[var_info['expr'].node_id] = const_values
        if 'is_iterable' not in const_ref:
        #if var_info['expr'].number == 'single':
            var_value = var_info['value'].values[None][0]
            #var_value = xule_context.global_context._constants[var_ref.var_declaration]['values'].values[None][0]
        else:  
            var_value = var_info['value']
            #var_value = const_values
            #var_value = evaluate(var_info['expr'], xule_context, constant_id=const_ref.var_declaration, is_values=True if const_ref.get('values_expression') == True else False)
        '''
    else:
        raise XuleProcessingError(_("Internal error: unkown variable type '%s'" % var_info['type']), xule_context) 
    
    var_value = var_value.clone()
    if var_info['tagged']:
        xule_context.tags[var_info['name']] = var_value

    return var_value

def calc_constant(const_info, const_context):
    const_context.iteration_table.add_table(const_info['expr'].node_id, const_context.get_processing_id(const_info['expr'].node_id))
    
    const_values = XuleValueSet()
    
    while True:
        const_context.aligned_result_only = False
        const_context.used_expressions = set()
        try:
            const_value = evaluate(const_info['expr'].expr[0], const_context)
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
        if const_context.iteration_table.is_table_empty(const_info['expr'].node_id):
            break
#         else:
#             const_context.reset_iteration()
        
    #reset the aligned only results.
    const_info['expr']['aligned_only_results'] = const_context.aligned_result_only
    
    const_info['value'] = const_values
    const_info['calculated'] = True

def evaluate_constant_assign(const_assign, xule_context):
    const_info = xule_context.find_var(const_assign.constantName, const_assign.node_id, constant_only=True)
    if const_info is None:
        raise XuleProcessingError(_("Constant '%s' not found" % const_assign.constantName), xule_context)
    
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

def process_precalc_preconditions(global_context):
    global_context.message_queue.logging("Precalcing non-instance preconditions")
    for precon_name, cat_precon in global_context.rule_set.catalog['preconditions'].items():
        if ('unused' not in cat_precon and
            not cat_precon['dependencies']['instance']
            and cat_precon['node_id'] not in global_context.preconditions):
            
            calc_precondition(precon_name, global_context)
            
def check_precondition(preconditionRef, global_context):
    '''When checking multiple preconditions, all must be true.'''
    for precon_name in preconditionRef.preconditionNames:
        precon_node_id = global_context.catalog['preconditions'][precon_name]['node_id']
        if precon_node_id not in global_context.preconditions:
            calc_precondition(precon_name, global_context)
        
        if getattr(global_context.options, "xule_debug", False):
        #if global_context.show_debug:
            global_context.message_queue.print("Precondition {} {}".format(precon_name, global_context.preconditions[precon_node_id]))
            
        if not global_context.preconditions[precon_node_id]:
            return False
    
    #No false precondition was found
    return True

def calc_precondition(precon_name, global_context):
    '''A precondition is true if at least one evaluation returns true'''

    cat_precon = global_context.catalog['preconditions'][precon_name]
    precon_context = XuleRuleContext(global_context, precon_name, cat_precon['file'])
    
    precon_rule_part = precon_context.global_context.rule_set.getItem(cat_precon)
    
    precon_table = precon_context.iteration_table.add_table(precon_rule_part.node_id, precon_context.get_processing_id(precon_rule_part.node_id))
    
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
            precon_context.global_context.preconditions[precon_rule_part.node_id] = True
            return

        precon_table.next(precon_table.table_id)
        if precon_table.is_empty:
            break
        
    #if we get here, then there was not an evaluation that return true, the precondition is false
    precon_context.global_context.preconditions[precon_rule_part.node_id] = False
               
# def pre_calc_expressions(global_context):
#     for node_id in global_context.rule_set.catalog['pre_calc_expressions']:
#         if node_id not in global_context.expression_cache:
#             expr = global_context.rule_set.getNodeById(node_id)
#             global_context.expression_cache[node_id] = calc_expression(expr, global_context)
# 
# def calc_expression(expr, global_context):
#     #print("calcing", expr.node_id, expr.getName())
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
    if_thens.append((if_expr.condition[0], if_expr.thenExpr[0]))

    for else_if in if_expr:
        if else_if.getName() == 'elseIfExpr':
            if_thens.append((else_if.condition[0], else_if.thenExpr[0]))
    
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
    return evaluate(if_expr.elseExpr[0], xule_context)
            
#     result = None
#     master_columns = []
#     for if_then in if_thens:
#         condition_value = evaluate(if_then[0], xule_context)
#         
#         #set up the iterables of the condition as being masters to any newly added columns
#         for master_col in if_then[0].downstream_iterables:
#             master_col_id = xule_context.get_processing_id(master_col.node_id)
#             master_columns.append(master_col_id)
#             xule_context.iteration_table.current_table.force_master_columns.append(master_col_id) 
#          
#         def cleanup():
#             for master_col_id in master_columns:
#                 xule_context.iteration_table.current_table.force_master_columns.pop()
# 
#         
#         if condition_value.type in ('unbound', 'none'):
#             try:
#                 result = XuleValue(xule_context, None, 'unbound')
#             except XuleIterationStop:
#                 cleanup()
#                 raise
#             break
#         elif condition_value.type != 'bool':
#             raise XuleProcessingError(_("If condition is not a boolean, found '%s'" % condition_value.type), xule_context)
#         else:
#             if condition_value.value:
#                 try:    
#                     result = evaluate(if_then[1], xule_context)
#                 except XuleIterationStop:
#                     cleanup()
#                     raise
#                 break
# 
#     if result is None:
#         #This only happens if all the 'if' coniditions aren't met. Like the condition expression, a fresh table is created.
#         result = evaluate(if_expr.elseExpr[0], xule_context)
# 
#     cleanup()
#     
#     return result

# def evaluate_forz(for_expr, xule_context):
#     for_loop_var_value = evaluate(for_expr.forControl, xule_context)
#     xule_context.add_arg(for_expr.forControl.forVar,
#                               for_expr.forControl.node_id,
#                               for_expr.forControl.tagged == '#',
#                               for_loop_var_value,
#                               'single')
#     try:
#         for_value = evaluate(for_expr.expr[0], xule_context)
#     finally:
#         xule_context.del_arg(for_expr.forControl.forVar, for_expr.forControl.node_id)
#     
#     return for_value
#     
# def evaluate_for_controlz(for_control, xule_context):
#     for_control_values = XuleValueSet()
#     
#     for_loop_collection = evaluate(for_control.forLoopExpr, xule_context)
#     
#     #Expand the the for loop collection. This will convert the set/list to a set of separate values
#     for for_var_value in for_loop_collection.value:
#         for_control_values.append(for_var_value)
#         
#     return for_control_values

def evaluate_for(for_expr, xule_context):
    return evaluate(for_expr.forBodyExpr, xule_context)
    
def evaluate_for_body(for_body_expr, xule_context):
    for_values = XuleValueSet()
    
    saved_used_expressions = xule_context.used_expressions
    xule_context.used_expressions = set()
    try: 
        for_loop_collection = evaluate(for_body_expr.forControl.forLoopExpr, xule_context)
    finally:
        used_expressions = xule_context.used_expressions
        xule_context.used_expressions = saved_used_expressions | used_expressions
#   
#     #pre-calc upstream variables
#     for var_ref in for_expr.expr[0].var_refs:
#         #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
#         if var_ref[1] != for_expr.forVar:
#             var_info = xule_context.find_var(var_ref[1], var_ref[0])
#             if var_info['calculated'] != True:
#                 var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context)
  
#    xule_context.iteration_table.add_dependent_table(xule_context.get_processing_id(for_expr.expr[0].node_id))

    for for_loop_var in for_loop_collection.value:
        if for_loop_var.used_expressions is None:
            for_loop_var.used_expressions = used_expressions
        else:
            for_loop_var.used_expressions.update(used_expressions)
        xule_context.add_arg(for_body_expr.forControl.forVar,
                              for_body_expr.forControl.node_id,
                              for_body_expr.forControl.tagged == '#',
                              for_loop_var,
                              'single')
       
#         #This will put the foor loop control value on the table.
#         evaluate(for_body_expr.forControl, xule_context)

        try:
            body_values = evaluate_for_body_detail(for_body_expr[0], 
                                                   for_body_expr.node_id, for_loop_var, 
                                                   for_body_expr.forControl.forVar if for_body_expr.forControl.tagged == '#' else None, 
                                                   xule_context)
        finally:
            xule_context.del_arg(for_body_expr.forControl.forVar, for_body_expr.forControl.node_id)
 
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
    #for_body_table = xule_context.iteration_table.add_table(xule_context.get_processing_id(body_expr.node_id), is_aggregation=True)
    
    for_body_table = xule_context.iteration_table.add_table(table_id, xule_context.get_processing_id(table_id), is_aggregation=True)
    for_body_table.dependent_alignment = for_loop_var.alignment
    
    #add the loop control to the table
    #xule_context.iteration_table.add_column(rule_part, for_body_table.table_id, processing_id, values, xule_context)    
    
    try:  
        while True:
            xule_context.aligned_result_only = False
            xule_context.used_expressions = set()
            if for_loop_tag is not None:
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
            #print("for", body_expr.getName(), body_expr.node_id, len(xule_context.used_expressions), len(body_value.used_expressions))
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

def evaluate_for_control(for_control, xule_context):
    control_values = XuleValueSet()
    control_arg = xule_context.find_var(for_control.varName, for_control.node_id)
    control_values.append(control_arg['value'])
    return control_values

# def evaluate_forx(for_expr, xule_context):
# 
# #     #pre-calc upstream variables
# #     for var_ref in for_expr.expr[0].var_refs:
# #         #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
# #         if var_ref[1] != for_expr.forVar:
# #             var_info = xule_context.find_var(var_ref[1], var_ref[0])
# #             if var_info['calculated'] != True:
# #                 var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context)
#             
#     for_loop_var = evaluate(for_expr.forLoop, xule_context, extra=for_expr)
#     
#     #print("loop value", for_loop_var.format_value())
#     
#     xule_context.add_arg(for_expr.forVar,
#                           for_expr.node_id,
#                           for_expr.tagged == '#',
#                           for_loop_var,
#                           for_expr.forLoop.number)
#     
#     #evaluate the for body in a new table
#     #pre-calc upstream variables
#     if for_expr.expr[0].number == 'multi': 
# #         for var_ref in for_expr.expr[0].var_refs:
# #             #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
# #             var_info = xule_context.find_var(var_ref[1], var_ref[0])
# #             if var_info['calculated'] != True:
# #                 var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context)
#      
#         xule_context.iteration_table.add_dependent_table(xule_context.get_processing_id(for_expr.expr[0].node_id))
#     
#     try:
#         for_body = evaluate(for_expr.expr[0], xule_context)
#     except (XuleIterationStop, XuleProcessingError):
#         raise
#     finally:
#         xule_context.del_arg(for_expr.forVar,
#                               for_expr.node_id)
#     
#     return for_body
# 
# def evaluate_for_loop(for_loop_expr, xule_context, for_expr):
#     for_loop_values = XuleValueSet()
#     
#     for_loop_collection = evaluate(for_loop_expr[0], xule_context)
#     
#     if for_loop_collection.type in ('set','list'):
#         if len(for_loop_collection.value) > 0:
#             #The for_loop_collection is only for the current row, so create a dependent table. This table is used to expand the collection
#             #pre-calc upstream variables
#             for var_ref in for_expr.expr[0].var_refs:
#                 #0 = var declaration id, 1 = var name, 2 = var_ref (only for constants)
#                 if var_ref[1] != for_expr.forVar:
#                     var_info = xule_context.find_var(var_ref[1], var_ref[0])
#                     if var_info['calculated'] != True:
#                         var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context)
#             
#             xule_context.iteration_table.add_dependent_table(xule_context.get_processing_id(for_loop_expr[0].node_id))
#             for for_loop_value in for_loop_collection.value:
#                 for_loop_values.append(for_loop_value)
#     elif for_loop_collection.type != 'unbound':
#         raise XuleProcessingError(_("For loop expects a set or list, found '%s'" % for_loop_collection.type), xule_context)
#     
#     return for_loop_values  

def evaluate_with(with_expr, xule_context):
    if with_expr.controlExpr[0].getName() != 'factset':
        raise XuleProcessingError(_("The control expression for the 'with' clause must be a factset, found '%s'." % with_expr.controlExpr[0].getName()), xule_context)
    
    if 'whereExpr' in with_expr.controlExpr.factset:
        raise XuleProcessingError(_("The control factset for the 'with' clause cannot not contain a 'where' clause."), xule_context)
    
    with_filters, aspect_vars = process_factset_aspects(with_expr.controlExpr.factset, xule_context)
    
    #verify that there are not already filters in place
    current_filters, x = xule_context.get_current_filters()
    current_aspects = {aspect_info[ASPECT] for aspect_info in current_filters}
    
    with_aspects = {aspect_info[ASPECT] for aspect_info in with_filters}
    
    if current_aspects & with_aspects:
        raise XuleProcessingError(_("An inner 'with' clause cannot include aspects in an outer 'with' clause, found '%s'." % ", ".join(current_aspects & with_aspects)), xule_context)
        
    #add the align aspects to the with_filter in the context
    xule_context.filter_add('with', with_filters)

    save_aligned_result_only = xule_context.aligned_result_only
    save_used_expressions = xule_context.used_expressions

    with_table = xule_context.iteration_table.add_table(with_expr.node_id, xule_context.get_processing_id(with_expr.node_id), is_aggregation=True)
    with_values = XuleValueSet()
    try:
        while True:
            xule_context.aligned_result_only = False
            xule_context.used_expressions = set()
            try:
                with_value = evaluate(with_expr.expr[0], xule_context)
            except XuleIterationStop:
                '''THIS COULD BE CREATE AN UNBOUND AND ADD IT TO THE WITH_VALUE. SIMILAR TO THE WAY THIS IS HANDLED IN FOR_BODY_DETAIL'''
                pass
            else:
                #if not(xule_context.iteration_table.current_table.current_alignment is None and xule_context.aligned_result_only):
                    #remove the with portion of the alignment
                if xule_context.iteration_table.current_table.current_alignment is not None: #this should be the alignment on the with table
                    remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in with_filters]
                    new_alignment = remove_from_alignment(xule_context.iteration_table.current_alignment, remove_aspects, xule_context)
                    with_value.alignment = new_alignment
                    
                with_value.facts = xule_context.facts
                with_value.tags = xule_context.tags
                
    
                with_values.append(with_value)

            #xule_context.iteration_table.del_current()
            xule_context.iteration_table.next(with_table.table_id)
            if with_table.is_empty:
                break
    finally:
        xule_context.aligned_result_only = save_aligned_result_only
        xule_context.used_expressions = save_used_expressions
        #delete the with table (in case it is left behind from an exception)
        xule_context.iteration_table.del_table(with_table.table_id)    
        xule_context.filter_del()

    return with_values

def evaluate_formula(formula_expr, xule_context):
    if xule_context.formula_bind is None:
        raise XuleProcessingError(_("A formula expression (:=) can only be in a formula rule."), xule_context)
    
    if xule_context.formula_bind == 'both':
        formula_left = evaluate(formula_expr[0], xule_context)
        formula_right = evaluate(formula_expr[1], xule_context)
    elif xule_context.formula_bind == 'left':
        formula_left = evaluate(formula_expr[0], xule_context)
        try:
            formula_right = evaluate(formula_expr[1], xule_context)
        except XuleIterationStop:
            formula_right = XuleValue(xule_context, 0, 'int')
    elif xule_context.formula_bind == 'right':
        try:
            formula_left = evaluate(formula_expr[0], xule_context)
        except XuleIterationStop:
            formula_left = XuleValue(xule_context, 0, 'int')
        formula_right = evaluate(formula_expr[1], xule_context)
    else:
        raise XuleProcessingError(_("Invalid bind value for formula rule, found '%s'" % xule_context.formula_bind), xule_context)
    
    difference_type, left_compute_value, right_compute_value = combine_xule_types(formula_left, formula_right, xule_context)
    difference_compute_value = left_compute_value - right_compute_value
    
#     difference_compute_value = formula_left.value - formula_right.value
#     difference_type = combine_xule_types(formula_left, formula_right, xule_context)[0]
    formula_difference = XuleValue(xule_context, difference_compute_value, difference_type)
    
    #Set up the tags
    #There is a risk that the tags could be overwritten by a tagged expression.
    xule_context.tags['left'] = formula_left
    xule_context.tags['right'] = formula_right
    xule_context.tags['difference'] = formula_difference
    
    return XuleValue(xule_context, None, 'formula')
    
def evaluate_unary(unary_expr, xule_context):
    initial_value = evaluate(unary_expr.expr[0], xule_context)
    
    if initial_value.type in ('unbound', 'none'):
        return initial_value
    
    if initial_value.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("Unary operator requires a numeric operand, found '%s'" % initial_value.type), xule_context)
    
    if unary_expr.unaryOp == '-':
        return XuleValue(xule_context, initial_value.value * -1, initial_value.type)
    else:
        return initial_value

def evaluate_mult(mult_expr, xule_context):
    left = evaluate(mult_expr[0], xule_context)
    for tok in mult_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right = evaluate(tok, xule_context)

            if left.type in ('unbound', 'none') or right.type in ('unbound', 'none'):
                left = XuleValue(xule_context, None, 'unbound')
            else:
                if left.type == 'unit' and right.type == 'unit':
                    #units have special handling
                    if operator == '*':
                        left = XuleValue(xule_context, unit_multiply(left.value, right.value), 'unit')
                    else:
                        left = XuleValue(xule_context, unit_divide(left.value, right.value), 'unit')
                else:
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

def evaluate_add(add_expr, xule_context):
    try:
        left = evaluate(add_expr[0], xule_context)
    except XuleIterationStop as xis:
        left = xis.stop_value #XuleValue(xule_context, None, 'unbound')
        
    for tok in add_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right_expr = tok
            try:
                right = evaluate(tok, xule_context)
            except XuleIterationStop as xis:
                right = xis.stop_value #XuleValue(xule_context, None, 'unbound')
            
            left_bar = operator[0] == '|'
            right_bar = operator[-1] == '|'
            
#             if operator[0] != '|' and left.type == 'unbound': # and right.type in ('int', 'float', 'decimal'):
#                 left = XuleValue(xule_context, 0, 'int')
#             
#             if operator[-1] != '|' and right.type == 'unbound': # and left.type in ('int', 'float', 'decimal'):
#                 right = XuleValue(xule_context, 0, 'int')
#             
#             if left.type == 'unbound' or right.type == 'unbound':
#                 raise XuleIterationStop
 
            left_bar = operator[0] == '|'
            right_bar = operator[-1] == '|' 
            do_calc = True
            
            if left_bar and right_bar: # |+|
                if left.type == 'unbound' or right.type =='unbound':
                    raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
            elif left_bar and not right_bar: #|+
                if left.type == 'unbound':
                    raise XuleIterationStop(XuleValue(xule_context, None, 'unbound'))
                if right.type == 'unbound':
                    #the left value is the interim value
                    do_calc = False
            elif not left_bar and right_bar: # +|
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
                
                if '+' in operator:
                    if left.type == 'set' and right.type == 'set':
                        #use union for sets
                        #left = XuleValue(xule_context, left_compute_value | right_compute_value, 'set')
                        left = add_sets(xule_context, left, right)
                    else:
                        left = XuleValue(xule_context, left_compute_value + right_compute_value, combined_type)
                elif '-' in operator:
                    left = XuleValue(xule_context, left_compute_value - right_compute_value, combined_type)
                else:
                    raise XuleProcessingError(_("Unknown operator '%s' found in addition/subtraction operation." % operator), xule_context)
    
    return left  

def add_sets(xule_context, left, right):
    new_set_values = list(left.value)
    new_shadow = list(left.shadow_collection)

    for item in right.value:
        if item.value not in new_shadow:
            new_shadow.append(item.shadow_collection if item.type in ('set','list') else item.value)
            new_set_values.append(item)
    
    return XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

'''
def get_native_collection(xule_value):
    native_collection = []
    
    for item in xule_value.value:
        if item.type in ('list', 'set'):
            native_value = get_native_collection(item)
        else:
            if item.fact is None:
                native_value = item.value
            else:
                native_value = item.fact
        native_collection.append(native_value)
        
    if xule_value.type == 'set':
        return frozenset(native_collection)
    else:
        return tuple(native_collection)
'''
def evaluate_comp(comp_expr, xule_context):
    left = evaluate(comp_expr[0], xule_context)

    for tok in comp_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right = evaluate(tok, xule_context)
            
            interim_value = None
            
            combined_type, left_compute_value, right_compute_value = combine_xule_types(left, right, xule_context)
            
            if left.type in ('instant', 'duration') and right.type in ('instant', 'duration'):
                left_compute_value = XulePeriodComp(left_compute_value)
                right_compute_value = XulePeriodComp(right_compute_value)
#             else:
#                 left_compute_value = left.value
#                 right_compute_value = right.value
            if left.type in ('list','set'):
                left_compute_value = left.shadow_collection
            if right.type in ('list','set'):
                right_compute_value = right.shadow_collection
                
#             if left.type == 'unbound' or right.type == 'unbound':
#                 interim_value = XuleValue(xule_context, None, 'unbound')
#             elif operator == '==':
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

            left = interim_value
        
    return left

def evaluate_not(not_expr, xule_context):
    initial_value = evaluate(not_expr[0], xule_context)
    
    if initial_value.type in ('unbound', 'none'):
        return initial_value
    
    if initial_value.type != 'bool':
        raise XuleProcessingError(_("The operand of the 'not' expression must be boolean, found '%s'" % initial_value.type), xule_context)
    
    return XuleValue(xule_context, not initial_value.value, 'bool')

def evaluate_and(and_expr, xule_context):
    value_found = False
    has_unbound = False
    left = XuleValue(xule_context, None, 'unbound')
    for expr in and_expr:
        if value_found:
            break
#             #In this case, we don't need the value from the right expression, but we do need to evaluate to populate the table incase there are more iterations.
#             try:
#                 evaluate(expr, xule_context)
#             except:
#                 pass
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
    for expr in or_expr:
        if value_found:
            break
#             try:
#                 evaluate(expr, xule_context)
#             except:
#                 pass
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
    if values_expr[0].getName() == 'taggedExpr':
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

def strip_alignment(aligned_values):
    unaligned_values = XuleValueSet()
    for alignment, values in aligned_values.values.items():
        if alignment is not None:
            for value in values:
                unaligned_value = value.clone()
                unaligned_value.alignment = None
                unaligned_value.aligned_result_only = False
                unaligned_values.append(unaligned_value)
    return unaligned_values    
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
    '''THIS CODE NEEDS A LITTLE REFACTORING. BREAK IT DOWN INTO FUNCTIONS. IMPROVE REUSE OF CODE FOR HANDLING 'IN' OPERATOR'''
    '''Evaluator for a factset
    
       The factset is divided into two parts. The first part contains aspects that will be used to filter the fact and will NOT
       be used for alignment. For example: "Assets[]" or "[lineItem=Assets]". These factsets will find all the 'Assets' facts in the 
       instance, but when these facts are compared to facts in other fact sets, the 'lineItem' aspect will not be used to check alignment.
       
       Actual aspects of the fact that are not specified in the first part of the factset will be used for alignment.
       
       With alignment:
           This would be put in the context for 'with' expr. It would cause downstream factset evaluations
           to include the filter as part of getting facts. If the filter is 'closed', it would act like a closed factset and not allow
           facts that have dimenions in fact's alignment that are not in the filter. 'open' filters wouldn't care.
           
           This provides an alternative mechanism for handling alignment. Instead of getting all results for each side of an operation (i.e. property) 
           and then aligning them, it would allow the expression to iterate over one operand result set and evaluate for each result of the other operand. 
           By pushing the filter, first, only the aligned results will come back. 
    '''
    
    f_start = datetime.datetime.today()
    
    #The no alignment flag indicates that the results of the factset should all have none alignment. It is set by the 'values' expression.
    #current_no_alignment = xule_context.no_alignment
    current_no_alignment = True if factset.get('values_expression') == True else False
    #reset to false. This will prevent any downstream factsets for not having alignment. For example: values [where $item::period==$a::period] 
    #xule_context.no_alignment = False # this flag is not longer used, instead the parse result has a flag of 'values_expression'.
    
    saved_used_expressions = xule_context.used_expressions
    xule_context.used_expressions = set()
    try:
        non_align_aspects, aspect_vars = process_factset_aspects(factset, xule_context)
    finally:
        used_expressions = xule_context.used_expressions
        xule_context.used_expressions = saved_used_expressions | xule_context.used_expressions

    #check if any non_align_aspects overlap with with_filters
    with_filters, other_filters = xule_context.get_current_filters()
    #This restriction is removed to suport rules like r1923
#     if with_aspects & factset_aspects:
#         raise XuleProcessingError(_("The factset cannont contain any aspects in any bounding 'with' clause, found '%s'." % ", ".join(with_aspects & factset_aspects)), xule_context)
    
    #combine all the filtering aspects.   
    all_aspect_filters = list(with_filters.items()) + list(other_filters.items()) + list(non_align_aspects.items())
    #if factset.is_dependent:
    #if not current_no_alignment and xule_context.iteration_table.is_dependent:
    aligned_aspects = []
    if not current_no_alignment and factset.is_dependent:
        if xule_context.dependent_alignment is None:
            #The table may acquire the dependent alignment after evaluating the aspect filters
            xule_context.iteration_table.current_table.make_dependent()        
        try:
            if xule_context.dependent_alignment is not None:
                unfrozen_alignment = {k: v for k, v in xule_context.dependent_alignment}
                aligned_aspects += list(alignment_to_aspect_info(unfrozen_alignment, xule_context).items())
                #all_aspect_filters += list(alignment_to_aspect_info(unfrozen_alignment, xule_context).items())
                all_aspect_filters += aligned_aspects
#         if xule_context.iteration_table.current_alignment is not None:
#             unfrozen_alignment = {k: v for k, v in xule_context.iteration_table.current_alignment}
#             all_aspect_filters += list(alignment_to_aspect_info(unfrozen_alignment, xule_context).items())        
        except IndexError:
            pass
        #For the aligned filters, get the list of dimensions. Facts that have 
    '''Match facts based on the aspects in the first part of the factset and any additional filters.
       This is done by intersecting the sets of the fact_index. The fact index is a dictionary of dictionaries.
       The outer dictionary is keyed by aspect and the inner by member. So fact_index[aspect][member] contains a 
       set of facts that have that aspect and member.'''       
    pre_matched_facts = factset_pre_match(factset, all_aspect_filters, non_align_aspects, aligned_aspects, xule_context)   
    
    
    pre_count1 = len(pre_matched_facts)
    f_pre_end = datetime.datetime.today()
    
    #For dependent factset, set flag to check if the iteration table becomes aligned. 
    #Bassically, there is no alignment yet. During the evaluation of the where clause a first time evaluated variable can create alignment.
    #If this happens, the pre matched facts should only include those facts that have matching alignment. So a flag in the context is set to check if the table becomes aligned.
    #When this happens a XuleReEvaluate exception is raised (this happens in the main evaluator()).

    saved_look_for_alignment = xule_context.look_for_alignment
    saved_where_table_ids = xule_context.where_table_ids
    saved_where_dependent_iterables = xule_context.where_dependent_iterables
    
    if factset.is_dependent and xule_context.iteration_table.any_alignment is None:
        xule_context.look_for_alignment = True
        #xule_context.where_table_ids = list(xule_context.iteration_table._ordered_tables.keys())
        xule_context.where_table_ids = [table.table_id for table in xule_context.iteration_table._ordered_tables.values()]        
        xule_context.where_dependent_iterables = [di.node_id for di in factset.dependent_iterables]        
    else:
        #set_look_for_alignment = False
        xule_context.look_for_alignment = False
    #print(factset.node_id, fact_value, no_pre_where_alignment, xule_context.iteration_table.current_table.table_id)
    
    default_where_used_expressions = set()
    
    recalc = False
    recalc_none = False
    
    try:
        results, default_where_used_expressions = process_filtered_facts(factset, pre_matched_facts, current_no_alignment, non_align_aspects, with_filters, aspect_vars, used_expressions, xule_context)
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
                pre_matched_facts = factset_pre_match(factset, additional_aspect_filters, non_align_aspects, aligned_aspects, xule_context, starting_facts=pre_matched_facts)
                #try again
                try:
                    results, default_where_used_expressions = process_filtered_facts(factset, pre_matched_facts, current_no_alignment, non_align_aspects, with_filters, aspect_vars, used_expressions, xule_context)
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
        #print("default fact", factset.getName(), factset.node_id, len(xule_context.used_expressions), len(default_value.used_expressions))
        if not current_no_alignment:
            default_value.aligned_result_only = True
        results.append(default_value)

    f_end = datetime.datetime.today()

#     res_count = sum(len(v) for v in results.values.values())
#     pre_count2 = len(pre_matched_facts)
#     x = [a if v is None else v.format_value() for a, v in all_aspect_filters]   
# 
#     print("factset: {} res-count: {} pre-count1: {} pre-count2: {} total-time: {} pre-time: {} where-time: {} {} {} {}".format(factset.node_id, res_count, pre_count1, pre_count2, 
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
        
        aspect_key = (aspect_info[TYPE], aspect_info[ASPECT])
        facts_by_aspect = set()
        
        '''THIS MIGHT BE MORE EFFICIENTLY HANDLED BY IGNORING THE ASPECT IF THE MEMBER IS None OR ELIMINATING ALL FACTS'''
        '''When the aspect key is not in the fact index, then the instance doesn't use this aspect (dimension). So create an entry for the 'None' key and put all the facts in it.'''
        if aspect_key not in xule_context.fact_index:
            #xule_context.fact_index[aspect_key][None] = xule_context.model.factsInInstance
            xule_context.fact_index[aspect_key][None] = xule_context.fact_index['all']
        
        if aspect_info[SPECIAL_VALUE] is not None:
            if aspect_info[SPECIAL_VALUE] == 'all':
                if aspect_info[TYPE] == 'builtin' and aspect_info[ASPECT] in ('lineItem', 'period', 'entity'):
                    #this is all facts
                    continue
                else:
                    #need to combine all the facts that have that aspect
                    facts_by_aspect = set(it.chain.from_iterable(v for k, v in xule_context.fact_index[aspect_key].items() if k is not None))
            elif aspect_info[SPECIAL_VALUE] == 'allWithDefault':
                continue
        else:                
            if aspect_info[ASPECT_OPERATOR] == 'in' and filter_member.type not in ('list', 'set'):
                    raise XuleProcessingError(_("The value for '%s' with 'in' must be a set or list, found '%s'" % (aspect_key[ASPECT], filter_member.type)), xule_context)

            #fix for aspects that take qname members (lineItem and explicit dimensions. The member can be a concept or a qname. The index is by qname.
            if aspect_key == ('builtin', 'lineItem'):
                if aspect_info[ASPECT_OPERATOR] == '=':
                    member_values = {convert_value_to_qname(filter_member, xule_context),}
                else:
                    member_values = {convert_value_to_qname(x, xule_context) for x in filter_member.value}
            elif aspect_key[TYPE] == 'explicit_dimension':
                if aspect_info[ASPECT_OPERATOR] == '=':
                    if filter_member.type == 'concept':
                        member_values = {convert_value_to_qname(filter_member, xule_context),}
                    else:
                        member_values = {filter_member.value,}
                else:
                    member_values = {convert_value_to_qname(x, xule_context) if x.type == 'concept' else x.value for x in filter_member.value}
            #Also fix for period aspect
            elif aspect_key == ('builtin', 'period'):
                if aspect_info[ASPECT_OPERATOR] == '=':
                    member_values = {convert_value_to_model_period(filter_member, xule_context),}
                else:
                    member_values= {convert_value_to_model_period(x, xule_context) for x in filter_member.value}
            else:
                if aspect_info[ASPECT_OPERATOR] == '=':
                    member_values = {filter_member.value,}
                else:
                    member_values = {x.value for x in filter_member.value}
                    '''THIS COULD USE THE SHADOW COLLECTION
                    member_values = set(filter_member.shadow_collection)
                    '''        
            found_members = member_values & xule_context.fact_index[aspect_key].keys()      
            for member in found_members:
                facts_by_aspect |= xule_context.fact_index[aspect_key][member]
        
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
#                 if fact in xule_context.fact_alignments[factset.node_id]:
#                     fact_alignment = xule_context.fact_alignments[factset.node_id][fact]
#                 else:
#                     fact_alignment = frozenset(get_alignment(fact, non_aligned_filters, xule_context).items())
#                     xule_context.fact_alignments[factset.node_id][fact] = fact_alignment
                    
                if fact_alignment == xule_context.dependent_alignment:
                    match_aligned_facts.add(fact)
            pre_matched_facts = match_aligned_facts
    
        '''  
        #This code reduces the pre matched facts to those that match alignment of the dependent alignment by using the fact index of dimensions that are not
        #in the dependent alignment. The method of checking the alignment used above proved to be more efficient. However, it may be that if ther pre match includes a large number
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
    if fact in xule_context.fact_alignments[factset.node_id]:
        return xule_context.fact_alignments[factset.node_id][fact][0 if frozen else 1]
    else:
        unfrozen_alignment = get_alignment(fact, non_aligned_filters, xule_context)
        fact_alignment = frozenset(unfrozen_alignment.items())
        xule_context.fact_alignments[factset.node_id][fact] = (fact_alignment, unfrozen_alignment)    
        return fact_alignment if frozen else unfrozen_alignment
    
def process_filtered_facts(factset, pre_matched_facts, current_no_alignment, non_align_aspects, with_filters, aspect_vars, pre_matched_used_expressoins_ids, xule_context):
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
            for with_aspect_info in with_filters:
                alignment_info = (with_aspect_info[TYPE], with_aspect_info[ASPECT])
                if alignment_info not in alignment:
                    if alignment_info == ('builtin', 'lineItem'):
                        alignment_value = model_fact.qname
                        #alignment_value = model_fact.elementQname
                    elif alignment_info == ('builtin', 'unit'):
                        if model_fact.isNumeric:
                            alignment_value = model_to_xule_unit(model_fact.unit.measures, xule_context)
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
                        raise XuleProcessingError(_("Pushing 'with' filter alignment found unknown alignment '%s : %s'" % alignment_info), xule_context)
                    
                    alignment[alignment_info] = alignment_value           
        
        '''Check closed factset'''
        if factset.factsetType == 'closed':
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
#                         if len(with_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
#                             remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in with_filters]
#                             adjusted_alignment = remove_from_alignment(frozenset(alignment.items()), remove_aspects, xule_context)
#                             if adjusted_alignment != xule_context.iteration_table.current_alignment:
#                                 continue
#                         else:
#                             continue

        if alignment is not None:
            #if not current_no_alignment and xule_context.iteration_table.is_dependent:
            if not current_no_alignment and factset.is_dependent:
                if xule_context.dependent_alignment is not None:
                    if frozenset(alignment.items()) != xule_context.dependent_alignment:
                        #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
                        #from a higher table which will not inlucde the with filter aspects.
                        if len(with_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
                            remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in with_filters]
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
                #declaration_id = (factset.node_id, declaration_index)
                declaration_id = aspect_var_tuple[2]
                if aspect_type == 'builtin':
                    if aspect_name == 'lineItem':
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
                                             XuleValue(xule_context, model_to_xule_unit(model_fact.unit.measures, xule_context), 'unit'),
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
            xule_context.add_arg('item',
                                 #(factset.node_id, 0),
                                 factset.whereExpr.node_id,
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
            where_table = xule_context.iteration_table.add_table(factset.whereExpr.node_id, xule_context.get_processing_id(factset.whereExpr[0].node_id), is_aggregation=True)
#                 if switched_alignment:
#                     where_table.dependent_alignment = frozenset(alignment.items())
            
            try:
                while True:
                    xule_context.aligned_result_only = False
                    #xule_context.used_vars = []
                    xule_context.used_expressions = set()
                    where_matched = True
                    try:
                        where_value = evaluate(factset.whereExpr[0], xule_context)
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
#                                         if len(with_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
#                                             remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in with_filters]
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
                        if not current_no_alignment and factset.is_dependent:
                            if xule_context.dependent_alignment is not None:
                                if frozenset(alignment.items()) != xule_context.dependent_alignment:
                                    #If this is in a 'with' clause, the first factset to be added to the with/agg table may be empty, The current alignment will be
                                    #from a higher table which will not inlucde the with filter aspects.
                                    if len(with_filters) > 0 and xule_context.iteration_table.current_table.current_alignment is None:
                                        remove_aspects = [(with_filter[0], with_filter[1]) for with_filter in with_filters]
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
                xule_context.del_arg('item', #(factset.node_id, 0),
                                 factset.whereExpr.node_id,)
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

def evaluate_function_ref(function_ref, xule_context):
    if function_ref.functionName in BUILTIN_FUNCTIONS:
        function_info = BUILTIN_FUNCTIONS[function_ref.functionName]
        if function_info[FUNCTION_TYPE] == 'aggregate':
            return evaluate_aggregate_function(function_ref, function_info, xule_context)
        else:
            if function_info[FUNCTION_TYPE] == 'regular' and len(function_ref.functionArgs) != function_info[FUNCTION_ARG_NUM]:
                raise XuleProcessingError(_("The '%s' function must have only %i argument, found %i." % (function_ref.functionName, 
                                                                                               function_info[FUNCTION_ARG_NUM],
                                                                                               len(function_ref.functionArgs))), xule_context)
            function_args = []
            for i in range(len(function_ref.functionArgs)):
                if function_info[FUNCTION_ALLOW_UNBOUND_ARGS]:
                    try:
                        arg = evaluate(function_ref.functionArgs[i][0], xule_context)
                    except XuleIterationStop as xis:
                        arg = xis.stop_value
                else:
                    arg = evaluate(function_ref.functionArgs[i][0], xule_context)
                              
                function_args.append(arg)

            return function_info[FUNCTION_EVALUATOR](xule_context, *function_args)
    else:
        #xule defined function
        
        #check fucntion cache
        if len(function_ref.functionArgs) == 0 and function_ref.functionName in xule_context.global_context.function_cache:
            return xule_context.global_context.function_cache[function_ref.functionName]                

        function_info = xule_context.find_function(function_ref.functionName)
        if function_info is None:
            raise XuleProcessingError("Function '%s' not found" % function_ref.functionName, xule_context)
        else:
            #Get the list of variables and their values. This will put the current single value for the variable as an argument
            for var_ref in sorted(function_ref.var_refs, key=lambda x: x[1]):
  
                #0 = var declaration id, 1 = var name, 2 = var_ref, 3 = var type (1 = var/arg, 2 = constant)
                var_value = evaluate(var_ref[2], xule_context)
#                 if function_ref.get('cacheable') == True:
#                     var_refs.append(var_value)
                      
#                 var_info = xule_context.find_var(var_ref[1], var_ref[0])
#                 #raise XuleProcessingError(_("Dependent variable '$%s' for function reference %s() is not calculated." % (var_ref[1], function_ref.functionName)))
#                 var_value = calc_var(var_info, var_ref[2] if var_info['type'] == xule_context._VAR_TYPE_CONSTANT else None, xule_context)    
#                 var_refs.append((var_ref[0], var_info['name'], var_value))

# #             #check the function cache
#             if function_ref.get('cacheable') == True:
#                 arg_values = []
#                 for arg in function_ref.functionArgs:
#                     arg_value = evaluate(arg[0], xule_context)
#                     arg_values.append((arg_value.value, arg_value.fact.id if arg_value.is_fact else None))
#                     
#                 cache_key = (function_ref.functionName, tuple(arg_values))
#                 if cache_key in xule_context.global_context.function_cache:
#                     print("using cache", len(function_ref.functionArgs))
#                     return xule_context.global_context.function_cache[cache_key]
          
            
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
            xule_context.id_prefix.append(function_ref.node_id)
            
#             #add downstream variables as arguments. This will put any var references that are in the arguments on the variable stack with calculated values
#             for var_ref in var_refs:
#                 xule_context.add_arg(var_ref[1],
#                                      var_ref[0],
#                                      False,
#                                      var_ref[2],
#                                      'single')
            
#             #process the arguments - they are added as variables so they will be first calculated on the isolated table.
#             matched_args = match_function_arguments(function_ref, function_info['function_declaration'], xule_context)
#             for arg in matched_args:
#                 xule_context.add_var(arg['name'],
#                                      arg['node_id'],
#                                      arg['tagged'],
#                                      arg['expr'])
            
            
            body_expr = function_info['function_declaration'].expr[0]
            save_aligned_result_only = xule_context.aligned_result_only
            #save_used_expressions = xule_context.used_expressions
            
#             for arg in matched_args:
#                 xule_context.add_arg(arg['name'],
#                                      arg['node_id'],
#                                      arg['tagged'],
#                                      arg['value'],
#                                      arg['number'])                

#             def iteration_reset():
#                 #reset the arguments
#                 for arg in matched_args:
#                     xule_context.del_arg(arg['name'], arg['node_id'])
#                     xule_context.add_var(arg['name'],
#                                          arg['node_id'],
#                                          arg['tagged'],
#                                          arg['expr'])
                    
            def cleanup_function():
                #remove the args
                for arg in matched_args:
                    xule_context.del_arg(arg['name'],
                                         arg['node_id'])
#                 #remove dependent variables as args
#                 for var_ref in var_refs:
#                     xule_context.del_arg(var_ref[1],
#                                          var_ref[0])
                #pop the function reference node id off the prefix
                xule_context.id_prefix.pop()    
                #reset the aligned only results.
                xule_context.aligned_result_only = save_aligned_result_only
                #xule_context.used_expressions = save_used_expressions    
            

            function_result_values = isolated_evaluation(xule_context,
                                                         function_info['function_declaration'].node_id, 
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
            if len(function_ref.functionArgs) == 0:
                xule_context.global_context.function_cache[function_ref.functionName] = function_results
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
                return_value = evaluate(expr, xule_context) #, glob_cache_key=body_expr.node_id if len(matched_args)==0 else None)
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
    for i in range(len(function_ref.functionArgs)):
        #pre_aggregation_table_list_size = len(xule_context.iteration_table)
        aggregation_table = xule_context.iteration_table.add_table(function_ref.node_id, xule_context.get_processing_id(function_ref.node_id), is_aggregation=True)
        try:
            while True:
                xule_context.aligned_result_only = False
                xule_context.used_expressions = set()
                arg = XuleValue(xule_context, None, 'unbound')
                try:
                    arg = evaluate(function_ref.functionArgs[i][0], xule_context)
                except XuleIterationStop:
                    pass
    #             except XuleProcessingError as e:
    #                 #clean up the aggregation table that was created
    #                 while len(xule_context.iteration_table) > pre_aggregation_table_list_size:
    #                     xule_context.iteration_table.del_table()
    #                 raise

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
                
                xule_context.iteration_table.next(function_ref.node_id)
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
            #print("agg", function_ref.getName(), function_ref.node_id, len(xule_context.used_expressions), len(used_expressions))
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
        concurrent_function = xf.agg_count_concurrent
    elif function_ref.functionName.lower() == 'sum':
        concurrent_function = xf.agg_sum_concurrent
    elif function_ref.functionName.lower() == 'all':
        concurrent_function = xf.agg_all_concurrent        

    for i in range(len(function_ref.functionArgs)):
        #pre_aggregation_table_list_size = len(xule_context.iteration_table)
        aggregation_table = xule_context.iteration_table.add_table(function_ref.node_id, xule_context.get_processing_id(function_ref.node_id), is_aggregation=True)
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
                
                xule_context.iteration_table.next(function_ref.node_id)
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
        #print("agg", function_ref.getName(), function_ref.node_id, len(xule_context.used_expressions), len(used_expressions))
        agg_value.used_expressions = used_expressions
        agg_value.tags = tags_by_alignment[alignment]
        agg_value.facts = facts_by_alignment[alignment]
        agg_values.append(agg_value)

    return agg_values

def evaluate_property(property_expr, xule_context):
    
    if 'expr' in property_expr:
        object_value = evaluate(property_expr.expr[0], xule_context)
    else:
        #there is no object of the property. (i.e. ::taxonomy)
        object_value = XuleValue(xule_context, None, 'unbound')
        
    #The properties expression is an optional object and then a chain of properties (i.e. Assets[]::concept::name::local-part)
    for current_property_expr in property_expr.properties:
        #Check that this is a valid property
        if current_property_expr.propertyName not in PROPERTIES:
            raise XuleProcessingError(_("'%s' is not a valid property." % current_property_expr.propertyName), xule_context)
        
        property_info = PROPERTIES[current_property_expr.propertyName]
        
        #Check that the left object is the right type
        #if the left object is unbound then return unbound
        if not property_info[PROP_UNBOUND_ALLOWED] and object_value.type in ('unbound', 'none'):
            return object_value
        else:
            #check the left object is the right type
            if len(property_info[PROP_OPERAND_TYPES]) > 0:
                if not (object_value.type in property_info[PROP_OPERAND_TYPES] or
                        object_value.is_fact and 'fact' in property_info[PROP_OPERAND_TYPES] or
                        any([xule_castable(object_value, allowable_type, xule_context) for allowable_type in property_info[PROP_OPERAND_TYPES]])):
                    #print(current_property_expr.node_id)
                    raise XuleProcessingError(_("Property '%s' is not a property of a '%s'.") % (current_property_expr.propertyName,
                                                                                                 object_value.type), 
                                              xule_context) 
        
        property_info = PROPERTIES[current_property_expr.propertyName]
    
        if property_info[PROP_ARG_NUM] is not None:
            
            if len(current_property_expr.propertyArgs) != property_info[PROP_ARG_NUM] and property_info[PROP_ARG_NUM] >= 0:
                raise XuleProcessingError(_("Property '%s' must have %s arguments. Found %i." % (current_property_expr.propertyName,
                                                                                                 property_info[PROP_ARG_NUM],
                                                                                                 len(current_property_expr.propertyArgs))), 
                                          xule_context)
            elif len(current_property_expr.propertyArgs) > property_info[PROP_ARG_NUM] * -1 and property_info[PROP_ARG_NUM] < 0:
                raise XuleProcessingError(_("Property '%s' must have no more than %s arguments. Found %i." % (current_property_expr.propertyName,
                                                                                                 property_info[PROP_ARG_NUM] * -1,
                                                                                                 len(current_property_expr.propertyArgs))), 
                                          xule_context)
        #prepare the arguments
        arg_values = []
        for arg_expr in current_property_expr.propertyArgs:
            arg_value = evaluate(arg_expr[0], xule_context)
            arg_values.append(arg_value)
            
        object_value = property_info[PROP_FUNCTION](xule_context, object_value, *arg_values)
        
        if 'tagName' in current_property_expr:
            xule_context.tags[current_property_expr.tagName] = object_value
        
    return object_value
                
                
                
                 
#aspect info indexes
TYPE = 0
ASPECT = 1
SPECIAL_VALUE = 2
ASPECT_OPERATOR = 3

BUILTIN_ASPECTS = ['lineItem', 'unit', 'period', 'entity']
     

EVALUATOR = {
    #rules
    "raiseDeclaration": evaluate_raise_declaration,
    "reportDeclaration": evaluate_report_declaration,
    "formulaDeclaration": evaluate_formula_declaration,
    
    #literals
    "boolean": evaluate_bool_literal,
    "integer": evaluate_int_literal,
    "float": evaluate_float_literal,
    "string": evaluate_string_literal,
    "qName": evaluate_qname_literal,
    "void": evaluate_void_literal,
    
    #atomic expressions
    "constantAssign": evaluate_constant_assign,
    "printExpr": evaluate_print,
    "ifExpr": evaluate_if,
    "forExpr": evaluate_for,
    "forControl": evaluate_for_control,
    #"forLoop": evaluate_for_loop,
    "forBodyExpr": evaluate_for_body,
    "withExpr": evaluate_with,
    
    "blockExpr": evaluate_block,
    "varRef": evaluate_var_ref,
    "functionReference": evaluate_function_ref,
    "taggedExpr": evaluate_tagged,
    "propertyExpr": evaluate_property,
    
    "factset": evaluate_factset,
    'valuesExpr': evaluate_values,
    
    #expressions with order of operations
    "formulaExpr": evaluate_formula,
    "unaryExpr": evaluate_unary,
    "multExpr": evaluate_mult,
    "addExpr": evaluate_add,
    "compExpr": evaluate_comp,
    "notExpr": evaluate_not,
    "andExpr": evaluate_and,
    "orExpr": evaluate_or,
    
    #severity
    'severity': evaluate_severity,
    
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
    return xf.BUILTIN_FUNCTIONS

BUILTIN_FUNCTIONS = xf.BUILTIN_FUNCTIONS


def property_dimension(xule_context, object_value, *args):
    dim_name = args[0]
    model_fact = object_value.fact
    
    if dim_name.type != 'qname':
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

def property_taxonomy(xule_context, object_value, *args):
    xule_context.model.xule_taxonomy_type = 'taxonomy'
    return XuleValue(xule_context, xule_context.model, 'taxonomy')

def property_rules_taxonomy(xule_context, object_value, *args):
    rules_dts = xule_context.get_rules_dts()
    if rules_dts is None:
        raise XuleProcessingError(_("The rule set does not contain a rule taxonomy"), xule_context)
    rules_dts.xule_taxonomy_type = 'rules_taxonomy'
    return XuleValue(xule_context, rules_dts, 'taxonomy')

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

def property_uri(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value.roleURI, 'uri')

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

def property_length(xule_context, object_value, *args):
    cast_value = xule_cast(object_value, 'string', xule_context)
    if xule_castable(object_value, 'string', xule_context):
        return XuleValue(xule_context, len(cast_value), 'int')
    else:
        raise XuleProcessingError(_("Cannot cast '%s' to 'string' for property length" % object_value.type), xule_context)

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
            
def property_size(xule_context, object_value, *args):
    return XuleValue(xule_context, len(object_value.value), 'int')

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
    #label type
    if len(args) > 0:
        label_type = args[0]
        if label_type.type == 'none':
            base_label_type = None
        elif xule_castable(label_type, 'string', xule_context):
            base_label_type = xule_cast(label_type, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The first argument for property 'label' must be a string, found '%s'" % label_type.type), xule_context)
    else:
        base_label_type = None

    #lang
    if len(args) > 1:
        lang = args[1]
        if lang.type == 'none':
            base_lang = None
        elif xule_castable(lang, 'string', xule_context):
            base_lang = xule_cast(lang, 'string', xule_context)
        else:
            raise XuleProcessingError(_("The second argument for property 'label' must be a string, found '%s'" % lang.type), xule_context)
    else:
        base_lang = None

    if object_value.is_fact:
        concept = object_value.fact.concept
    else:
        concept = object_value.value

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
            return XuleValue(xule_context, next(iter(label_by_type.values())), 'label')
        elif len(label_by_type) > 0:
            #there is only one label just return it
            return XuleValue(xule_context, next(iter(label_by_type.values())), 'label')
        else:
            return XuleValue(xule_context, None, 'none')        
    else:
        return XuleValue(xule_context, None, 'none')

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
    return XuleValue(xule_context, float(object_value.fact.decimals), 'float')

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

def property_unit(xule_context, object_value, *args):
    if object_value.fact.unit is None:
        return XuleValue(xule_context, None, 'unbound')
    else:
        return XuleValue(xule_context, model_to_xule_unit(object_value.fact.unit.measures, xule_context), 'unit')

def property_entity(xule_context, object_value, *args):
    return XuleValue(xule_context, model_to_xule_entity(object_value.fact.context, xule_context), 'entity')

def property_identifier(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value[1], 'string')

def property_scheme(xule_context, object_value, *args):
    return XuleValue(xule_context, object_value.value[0], 'string')

def property_period(xule_context, object_value, *args):
    if object_value.fact.context.isStartEndPeriod or object_value.fact.context.isForeverPeriod:
        return XuleValue(xule_context, model_to_xule_period(object_value.fact.context, xule_context), 'duration', from_model=True)
    else:
        return XuleValue(xule_context, model_to_xule_period(object_value.fact.context, xule_context), 'instant', from_model=True)

def property_start_date(xule_context, object_value, *args):
    if object_value.type == 'instant':
        return XuleValue(xule_context, object_value.value, 'instant', from_model=object_value.from_model)
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        return XuleValue(xule_context, object_value.value[0], 'instant', from_model=object_value.from_model)

def property_end_date(xule_context, object_value, *args):
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

def property_to_list(xule_context, object_value, *args):
    '''The input set is sorted so that two sets that ocntain the same items will produce identical lists. Because python sets are un ordered, there
       is no guarentee that the two sets will iterate in the same order.
    '''
    def set_sort(item):
        return item.value
    
    return XuleValue(xule_context, tuple(sorted(object_value.value, key=set_sort)), 'list')

def property_to_set(xule_context, object_value, *args):
    return xf.agg_set(xule_context, object_value.value)
    
    values = {}
    for item in object_value.value:
        if  item.is_fact:
            values[item.fact] = item
        else:
            values[item.value] = item
    
    return XuleValue(xule_context, frozenset(values.values()), 'set')
    
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

def get_networks(xule_context, dts_value, arcrole, role=None, link=None, arc=None):
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

  
def get_base_set_info(xule_context, dts, arcrole, role=None, link=None, arc=None):
    return [x + (False,) for x in dts.baseSets if x[NETWORK_ARCROLE] == arcrole and
                                       (True if role is None else x[NETWORK_ROLE] == role) and
                                       (True if link is None else x[NETWORK_LINK] == link) and
                                       (True if arc is None else x[NETWORK_ARC] == arc)]

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
               'dimension': (property_dimension, 1, ('fact',), False),
              
               # taxonomy navigations
               'taxonomy': (property_taxonomy, 0, ('unbound',), True),
               'rules-taxonomy': (property_rules_taxonomy, 0, ('unbound',), True),
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
                
               'decimals': (property_decimals, 0, ('fact',), False),
               'round-by-decimals': (property_round_by_decimals, 1, ('fact', 'int', 'decimal', 'float'), False),
               'unit': (property_unit, 0, ('fact',), False),
               'entity': (property_entity, 0, ('fact',), False),
               'identifier': (property_identifier, 0, ('entity',), False),
               'scheme': (property_scheme, 0, ('entity',), False),
               'period': (property_period, 0, ('fact',), False),
               'start-date': (property_start_date, 0, ('instant', 'duration'), False),
               'end-date': (property_end_date, 0, ('instant', 'duration'), False),
               'days': (property_days, 0, ('instant', 'duration'), False),
               'add-time-period': (property_add_time_period, 1, ('instant',), False),
               'subtract-time-period': (property_subtract_time_period, 1, ('instant',), False),
 
               'dts-document-locations': (property_dts_document_locations, 0, ('taxonomy',), False),
               
               'length': (property_length, 0, ('string', 'uri'), False),
               'substring': (property_substring, 2, ('string', 'uri'), False),
               'index-of': (property_index_of, 1, ('string', 'uri'), False),
               'last-index-of': (property_last_index_of, 1, ('string', 'uri'), False),
               'lower-case': (property_lower_case, 0, ('string', 'uri'), False),
               'upper-case': (property_upper_case, 0, ('string', 'uri'), False),
               'contains': (property_contains, 1, ('set', 'list', 'string', 'uri'), False),
               'size': (property_size, 0, ('list', 'set'), False),
               'item': (property_item, 1, ('list',), False),
               
               'power': (property_power, 1, ('int', 'float', 'decimal'), False),
               'log10': (property_log10, 0, ('int', 'float', 'decimal'), False),
               'abs': (property_abs, 0, ('int', 'float', 'decimal', 'fact'), False),
               'signum': (property_signum, 0, ('int', 'float', 'decimal', 'fact'), False),
               
               'role': (property_role, 0, ('network', 'label'), False),
               'uri': (property_uri, 0, ('role',), False),
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
               
               'to-list': (property_to_list, 0, ('list', 'set'), False),
               'to-set': (property_to_set, 0, ('list', 'set'), False),

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




def process_factset_aspects(factset, xule_context):
    '''Build list of aspects as descried in the factset'''
    non_align_aspects = {}
    aspect_vars = {}
    alternate_notation = False
    #line_item_info = None
    
    #if the factset used the lineItem[] notation add the line item to non_align_aspect
    if 'lineItemAspect' in factset:
        alternate_notation = True
        #line_item_info = ('builtin', 'lineItem', None, '=')
        non_align_aspects[('builtin', 'lineItem', None, '=')]  = evaluate(factset.lineItemAspect.qName, xule_context)

    for aspect_filter in factset.aspectFilters:
        '''IS IT POSSIBLE FOR THE NAME TO RETURN MORE THAN ONE RESULT? WHAT WOULD HAPPEN IF NAME WAS A '*'. CURRENTLY NOT ALLOWING THIS.'''
        aspect_filter_qname = evaluate(aspect_filter.aspectName.qName, xule_context).value
        #verify that lineItem is not used in both forms of the notation, i.e. Assets[lineItem=Liabilities].
        aspect_var_name = aspect_filter.get('aspectVar')
        if aspect_filter_qname.prefix is None and aspect_filter_qname.localName in BUILTIN_ASPECTS:
            #the aspect is builtin
            if aspect_filter_qname.localName == 'lineItem' and alternate_notation:
                XuleProcessingError(_("The factset specifies the lineItem both outside and inside the factset."), xule_context)
                
            if aspect_filter.get('all'):
                aspect_info = ('builtin', aspect_filter_qname.localName, aspect_filter.all, aspect_filter.aspectOperator)
                non_align_aspects[aspect_info] = XuleValue(xule_context, None, 'none')
                add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter.node_id, xule_context)    
            elif aspect_filter.get('void'):
                non_align_aspects[('builtin', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
                add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter.node_id, xule_context)                            
            else:
                aspect_info = ('builtin', aspect_filter_qname.localName, None, aspect_filter.aspectOperator)
                non_align_aspects[aspect_info] = evaluate(aspect_filter.aspectExpr[0], xule_context)
                add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, aspect_filter.node_id, xule_context)
        else:
            #This is a dimensional aspect.
            if aspect_filter.get('all'):
                non_align_aspects[('explicit_dimension', aspect_filter_qname, aspect_filter.all, aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter.node_id, xule_context)
            elif aspect_filter.get('void'):
                non_align_aspects[('explicit_dimension', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleValue(xule_context, None, 'none')
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter.node_id, xule_context)                
            else:
                if not(aspect_filter.get('aspectExpr')):
                    #There is no member. In this case the aspect may have varname, but it dones not participate in the non_align.
                    add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter.node_id, xule_context)
                else:
                    member_rs = evaluate(aspect_filter.aspectExpr[0], xule_context)
                    non_align_aspects[('explicit_dimension', aspect_filter_qname, None, aspect_filter.aspectOperator)] = member_rs
                    add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, aspect_filter.node_id, xule_context)
    
    return (non_align_aspects,
            aspect_vars) #,
            #line_item_info) 

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

# def get_used_vars(xule_context, var_ids):    
#     return {var_id: xule_context.vars.get(var_id) for var_id in var_ids}

def match_function_arguments(reference, declaration, xule_context):
    ''' This function matches the arguments on the function reference (call) to the function declaration.
        It returns a list of matched arguments as a dictionary.
    '''
    if len(reference.functionArgs) != len(declaration.functionArgs):
        raise XuleProcessingError(_("Function call for '%s' has mismatched arguments." % reference.functionName), xule_context)
    else:
        matched = []
        for i in range(len(reference.functionArgs)):
            arg_name = declaration.functionArgs[i].argName
#             try:
#                 arg_value = evaluate(reference.functionArgs[i][0], xule_context)
#             except XuleIterationStop as xis:
#                 arg_value = xis.stop_value #XuleValue(xule_context, None, 'unbound')
                
            matched.append({"name": arg_name, 
                            "node_id": declaration.functionArgs[i].node_id, 
                            "expr": reference.functionArgs[i][0],
                            #"value": arg_value, 
                            "tagged": declaration.functionArgs[i].tagged})#,
                            #"number": reference.functionArgs[i][0].number})
    
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
            if align_key[1] == 'lineItem':
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
    part_name = rule_part.getName()
    if part_name == 'forExpr':
        return (rule_part.forControl.forVar,)
    elif part_name == 'varRef':
        return (rule_part.varName,)
    elif part_name == 'functionReference':
        function_info = xule_context.find_function(rule_part.functionName)
        if function_info is None:
            return (rule_part.functionName, tuple())
        else:
            args = tuple([x.argName for x in function_info['function_declaration'].functionArgs])
            return (rule_part.functionName, args)
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
            if ('builtin', 'lineItem') not in fact_context:
                trace_info += str(sugar[0].qname) + " "
            trace_info +=  format_alignment(fact_context, xule_context)
    else:
        trace_info += expr_name
    
    if len(trace_info) > 0:
        trace_info = " - " + trace_info
    
    return trace_info


def get_message(rule, xule_value, alignment, xule_context):

    if 'message' in rule:
        message_value = evaluate(rule.message[0], xule_context)
        if message_value.type == 'unbound':
            message_string = ""
        else:
            message_string = message_value.value
    else:
        message_string = ""
    
    if message_string == "":
        #create a default message
        if rule.getName() == 'reportDeclaration':
                message_string = "${value} ${context}"
        elif rule.getName() == 'raiseDeclaration':
            if len(xule_context.facts) > 0:
                message_string = "${default_fact.value} ${default_fact.context}${context}"
                xule_context.add_tag('default_fact', XuleValue(xule_context, next(iter(xule_context.facts)), 'fact'))
            else:
                message_string = "${value}"
        elif rule.getName() == 'formulaDeclaration':
            message_string = "${left.value} != ${right.value} ${context}"
    
    return process_message(message_string, xule_value, alignment, xule_context)

def process_message(message_string, xule_value, alignment, xule_context):    

    common_facts = [tag_value.fact for tag_value in xule_context.tags.values() if tag_value.is_fact]
    if not common_facts: #common_facts is empty, no facts are tagged.
        common_facts = xule_context.facts

    common_aspects = get_common_aspects(common_facts, xule_context)
    
    #Check if there is a fact tag that uses the .context. If so and the lineItem is in the common aspects, the line item should be removed from the common aspects
    if ('builtin','lineItem') in common_aspects:
        for tag_name, tag_value in xule_context.tags.items():
            if tag_value.is_fact or tag_value.type == 'empty_fact':
                tag_context_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)context\s*}'
                if re.search(tag_context_pattern, message_string):
                    del common_aspects[('builtin','lineItem')]
                    break
     
    for tag_name, tag_value in xule_context.tags.items():        
        replacement_value = tag_value.format_value() or ''
        
        if tag_value.is_fact: 
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)
            
            for tag_sub_part in MESSAGE_TAG_SUB_PARTS:
                tag_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)' + tag_sub_part[0] + '\s*}'
                if re.search(tag_pattern, message_string) is not None:
                    if tag_sub_part[1] == format_alignment:
                        message_string = re.sub(tag_pattern, format_alignment(get_uncommon_aspects(tag_value.fact, common_aspects, xule_context), xule_context), message_string)
                    else:
                        new_value = tag_sub_part[1](xule_context, tag_value)
                        message_string = re.sub(tag_pattern, new_value or "", message_string)
                        
        elif tag_value.type == 'empty_fact':
            if alignment is not None and ('builtin', 'lineItem') in alignment:
                    tag_context = format_qname(alignment[('builtin', 'lineItem')], xule_context)
            else:
                tag_context = str(tag_value.value)
                
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', 'missing', message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', 'missing', message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*context\s*}', tag_context, message_string)
            
            for tag_sub_part in MESSAGE_TAG_SUB_PARTS:
                tag_pattern = '\$\s*{\s*' + tag_name + '\s*\.\s*(?i)' + tag_sub_part[0] + '\s*}'
                if re.search(tag_pattern, message_string) is not None:
                    message_string = re.sub(tag_pattern, 'missing', message_string)

        else:
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)

    message_string = re.sub('\$\s*{\s*context\s*}', format_alignment(common_aspects, xule_context), message_string)
    message_string = re.sub('\$\s*{\s*value\s*}', xule_value.format_value() or '', message_string)
    '''ADD TRACE'''
#     if xule_context.show_trace:
#         message_string = re.sub('\$\s*{\s*trace\s*}', format_trace(xule_context, result, common_aspects), message_string)
    message_string = message_string.replace('%', '%%')

    return message_string

def get_common_aspects(dict_model_facts, xule_context):
    
    model_facts = list(dict_model_facts)
    
    if len(model_facts) > 0:
        common_aspects = get_all_aspects(model_facts[0], xule_context)
    else:
        common_aspects = {}    
    
    for model_fact in model_facts[1:]:
        fact_aspects = get_all_aspects(model_fact, xule_context)
        for aspect_info, aspect_value in fact_aspects.items():
            if aspect_info in common_aspects:
                if aspect_value != common_aspects[aspect_info]:
                    del common_aspects[aspect_info]
        for missing_aspect in common_aspects.keys() - fact_aspects.keys():
            del common_aspects[missing_aspect]
        
    #remove lineItem
    if ('builtin', 'lineItem') in common_aspects and len(model_facts) > 1:
        del common_aspects[('builtin', 'lineItem')]
    
    return common_aspects

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
    if 'lineItem' not in non_align_builtins:
        alignment[('builtin', 'lineItem')] = model_fact.qname
        #alignment[('builtin', 'lineItem')] = model_fact.elementQname
    
    #unit
    if model_fact.isNumeric:
        if 'unit' not in non_align_builtins:
            alignment[('builtin', 'unit')] = model_to_xule_unit(model_fact.unit.measures, xule_context)
            
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
        if aspect_info == ('builtin', 'lineItem'):
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
    if ('builtin', 'lineItem') in aspects:
        line_item_string = format_qname(aspects[('builtin', 'lineItem')], xule_context)
    
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
        if len(model_unit[1]) == 0:
            #no denominator
            aspect_strings.append("unit=%s" % " * ".join([x.localName for x in model_unit[0]]))
        else:
            aspect_strings.append("unit=%s/%s" % (" * ".join([x.localName for x in model_unit[0]]), 
                                                  " * ".join([x.localName for x in model_unit[1]])))
            
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
    cat_namespace = xule_context.rule_set.getNamespaceInfoByUri(qname.namespaceURI, xule_context.cat_file_num)
    if cat_namespace:
        if cat_namespace['prefix'] == '*':
            return qname.localName
        else:
            return cat_namespace['prefix'] + ":" + qname.localName
    else:
        return str(qname)       

MESSAGE_TAG_SUB_PARTS = (('context', format_alignment),
                              ('label', format_fact_label),
                              ('lineitem', format_fact_line_item),
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
        if rule_part.getName() == 'varRef':
            if rule_part.is_constant:
                additional =  " ($" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + ") - constant)"
            else:
                additional = " ($" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + ")"
        elif rule_part.getName() == 'varAssign':
            additional = " (" + rule_part.varName + ")" + (" NOT USED" if rule_part.get('not_used') == True else "")
        elif rule_part.getName() == 'constantAssign':
            additional = " (" + rule_part.constantName + ")"
        elif rule_part.getName() == 'functionArg':
            additional = " (" + rule_part.argName + ")"
        elif rule_part.getName() == 'forExpr':
            additional = " (" + rule_part.forControl.forVar + ")"
        elif rule_part.getName() == 'reportDeclaration':
            additional = " (" + rule_part.reportName + ")"
        elif rule_part.getName() == 'raiseDeclaration':
            additional = " (" + rule_part.raiseName + ")"  
        elif rule_part.getName() == 'formulaDeclaration':
            additional = " (" + rule_part.formulaName + ")"                      
#         elif rule_part.getName() in ('functionDeclaration', 'functionReference'):
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
                           ((", i" + str({dep.node_id for dep in rule_part.dependent_iterables})) if len(rule_part.dependent_iterables) > 0 else "") +         
#                            ((", di" + str({dep.node_id for dep in rule_part.downstream_iterables})) if len(rule_part.downstream_iterables) > 0 else "") +                    
                           (", Values" if rule_part.get('values_expression') == True else "") +
                           (", Table %i" % rule_part.table_id if rule_part.get('table_id') is not None else "") +
                           "]")
        
        if 'is_iterable' in rule_part:
            additional += " iterable"
        if 'in_loop' in rule_part:
            additional += " LOOP"
        display_string += ("  " * level) + str(rule_part.node_id) + ":" + rule_part.getName() + additional + "\n"
        if rule_part.node_id in traces:
            trace = traces[rule_part.node_id]
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
        if rule_part.getName() == 'varRef':
            if rule_part.is_constant:
                additional =  "$" + rule_part.varName + " declaration: " + str(rule_part.var_declaration) + " - constant)"
            else:
                additional = "$" + rule_part.varName + " declaration: " + str(rule_part.var_declaration)
        elif rule_part.getName() == 'varAssign':
            additional = rule_part.varName + (" NOT USED" if rule_part.get('not_used') == True else "")
        elif rule_part.getName() == 'constantAssign':
            additional = rule_part.constantName
        elif rule_part.getName() == 'functionArg':
            additional = rule_part.argName
        elif rule_part.getName() == 'forExpr':
            additional = rule_part.forControl.forVar
        elif rule_part.getName() == 'reportDeclaration':
            additional = rule_part.reportName
        elif rule_part.getName() == 'raiseDeclaration':
            additional = rule_part.raiseName  
        elif rule_part.getName() == 'formulaDeclaration':
            additional = rule_part.formulaName                       
        elif rule_part.getName() in ('functionDeclaration', 'functionReference'):
            additional = rule_part.functionName + (" CACHEABLE" if rule_part.get('cacheable') == True else "") 

        row = [rule_name
               ,rule_part.node_id
               ,('  ' * level) + rule_part.getName()                              #name
               ,additional                                      #notes
               ,True if rule_part.get('instance') else False    #instance
               ,True if rule_part.get('rules-taxonomy') else False #rule taxonomy
               ,rule_part.number == 'single'                    #nubmer
               ,True if rule_part.has_alignment else False      #aligned
               ,("D" if rule_part.is_dependent else "I") if 'is_dependent' in rule_part else "" #dependency
               ,str({dep.node_id for dep in rule_part.dependent_iterables}) if len(rule_part.dependent_iterables) > 0 else "" #dependent iterables
               ,'is_iterable' in rule_part                      #iterable
               ]
        
        if rule_part.node_id in traces:            
            trace = traces[rule_part.node_id]
            
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
                if child.getName() != 'varAssign':
                    if child.node_id in traces:
                        total_child_times += traces[child.node_id]['iterations-t']
                        total_child_nodes.append(child.node_id)
                        #return (traces[child.node_id]['iterations-t'], child.node_id)
                    else:
                        child_info = trace_count_next_time(child, traces)
                        total_child_times += child_info[0]
                        total_child_nodes += child_info[1]
    return (total_child_times, total_child_nodes)
    
            
    