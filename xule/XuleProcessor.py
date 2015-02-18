'''
Created on Dec 16, 2014

Copywrite (c) 2014 XBRL US Inc. All rights reserved.
'''

from .XuleContext import XuleGlobalContext, XuleRuleContext #XuleContext
from .XuleRunTime import XuleProcessingError, XuleResult, XuleResultSet, XulePeriodComp
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
from aniso8601.__init__ import parse_duration, parse_datetime, parse_date
import collections
from lxml import etree as et
from threading import Thread

def process_xule(rule_set, model_xbrl, cntlr, show_timing=False, show_debug=False, show_trace=False, crash_on_error=False,
                 multi=False, async=False, cpunum=None):
    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, 
                                       multi=multi, async=async,
                                       cpunum=cpunum)    
    global_context.show_timing = show_timing
    global_context.show_debug = show_debug
    global_context.show_trace = show_trace
    global_context.crash_on_error = crash_on_error

    t = Thread(target=output_message_queue, args=(global_context,))
    t.name = "Message Queue"
    t.start()
  
    xule_context = XuleRuleContext(global_context)
    global_context.fact_index = index_model(xule_context)
        
    global_context.message_queue.logging("Processing Filing...")
    evaluate_rule_set(global_context)
    
    # Shutdown Message Queue
    global_context.message_queue.stop()
    global_context.message_queue.clear()
    t.join()  
    
        
def evaluate_rule_set(global_context):

    ''' NEED TO CHECK THE RULE BASE PRECONDITION '''
    if global_context.show_timing:
        times = []
        total_start = datetime.datetime.today()
    #use the term "cat" for catalog information
    for file_num, cat_rules in global_context.catalog['rules_by_file'].items():
        for rule_name in sorted(cat_rules.keys()):
            cat_rule = cat_rules[rule_name]
        #for rule_name, cat_rule in cat_rules.items():
            if global_context.show_debug:
                global_context.message_queue.print("Processing: %s" % rule_name)
                global_context.message_queue.print(global_context.model.modelDocument.uri)
            try:
                if global_context.show_timing:
                    rule_start = datetime.datetime.today()
                rule = global_context.rule_set.getItem(cat_rule)
                xule_context = XuleRuleContext(global_context,
                                               rule_name,
                                               file_num)
                assign_severity(rule, xule_context)

                evaluate(rule, xule_context)

            except XuleProcessingError as e:
                if global_context.crash_on_error:
                    raise
                else:
                    xule_context.global_context.message_queue.error("xule:error", str(e))
            
            except Exception as e:
                if global_context.crash_on_error:
                    raise
                else:
                    xule_context.global_context.message_queue.error("xule:error","rule %s: %s" % (rule_name, str(e)))
            
            if global_context.show_timing:
                rule_end = datetime.datetime.today()
                times.append((xule_context.rule_name, rule_end - rule_start))
                
    if global_context.show_timing:
        total_end = datetime.datetime.today()
        global_context.message_queue.print("Total number of rules processed: %i" % len(times))
        global_context.message_queue.print("Total time to process: %s." % (total_end - total_start))
        #slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > 0.001]
        slow_rules = [timing_info for timing_info in times if timing_info[1].total_seconds() > 0.5]
        global_context.message_queue.print("Number of rules over 0.5s: %i" % len(slow_rules))
        for slow_rule in slow_rules:
            global_context.message_queue.print("Rule %s end. Took %s" % (slow_rule[0], slow_rule[1]))

def index_model(xule_context):
    fact_index = collections.defaultdict(lambda :collections.defaultdict(set))
    
    fact_index[('builtin', 'lineItem')] = xule_context.model.factsByQname
    
    for model_fact in xule_context.model.factsInInstance:
        period = model_to_xule_period(model_fact.context, xule_context)
        fact_index[('builtin', 'period')][period].add(model_fact)
        
        if model_fact.isNumeric:
            unit = model_to_xule_unit(model_fact.unit.measures, xule_context)
            fact_index[('builtin', 'unit')][unit].add(model_fact)
        
        entity = model_to_xule_entity(model_fact.context, xule_context)
        fact_index[('builtin', 'entity')][entity].add(model_fact)
        
        for dim, mem in model_fact.context.qnameDims.items():
            fact_index['explicit_dimension', dim][mem.memberQname].add(model_fact)
    
    #for each aspect add a set of facts that don't hae that aspect with a key value of None
    for aspect_key in fact_index:
        fact_index[aspect_key][None] = xule_context.model.factsInInstance - set(it.chain.from_iterable(fact_index[aspect_key].values()))
        
    return fact_index
    
def evaluate(rule_part, xule_context):
    if xule_context.show_trace:
        xule_context.trace_level += 1
        cur_trace_level = xule_context.trace_level
    
#     if xule_context.show_trace:
#         print("  " * xule_context.trace_level + trace_info(rule_part))

    result_set = EVALUATOR[rule_part.getName()](rule_part, xule_context) 
    
    if xule_context.show_trace:
        if result_set is not None:
            for res in result_set:
                #res.trace = (rule_part.getName(), rule_part.asDict(), res, [] if res.trace is None else res.trace if isinstance(res.trace, list) else [res.trace])
                #res.trace = (rule_part.getName(), '', res, [] if res.trace is None else res.trace if isinstance(res.trace, list) else [res.trace])
                res.trace.appendleft((cur_trace_level, rule_part.getName(), sugar_trace(res, rule_part, xule_context), res))
            result_set.default.trace.appendleft((cur_trace_level, rule_part.getName(), sugar_trace(result_set.default, rule_part, xule_context), result_set.default))
            
        xule_context.trace_level -= 1
    return result_set

def sugar_trace(res, rule_part, xule_context):
    part_name = rule_part.getName()
    if part_name == 'forExpr':
        return (rule_part.forVar,)
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
        return (res,)
    else:
        return tuple()

def trace_info(rule_part):
    trace = rule_part.getName()
    
    if trace == 'reportDeclaration':
        trace += ": " + rule_part.reportName
        
    if trace == 'raiseDeclaration':
        trace += ": " + rule_part.raiseName
    
    if trace == 'qName':
        trace += ": " + rule_part.localName
        
    if trace == 'varRef':
        trace += ": " + rule_part.varName
        
    if trace == 'functionReference':
        trace += ": " + rule_part.functionName
        
    if trace == 'property':
        trace += ": " + rule_part.propertyName
        
    return trace
    
def evaluate_raise(raise_rule, xule_context):
 
    '''NEED TO CHECK THE PRE CONDITION'''

    if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
        raise XuleProcessingError(_("A raise rule cannot have a severity function, found '%s'" % xule_context.severity_type), xule_context)
  
    result_set = evaluate(raise_rule.expr[0], xule_context)
    
    for result in result_set:
        if result.type == 'unbound':
            continue
        
        if xule_context.severity_type == xule_context.SEVERITY_TYPE_STATIC:
            severity = xule_context.severity.upper()
            if not isinstance(result.value, bool):
                raise XuleProcessingError(_("Raise %s did not evalute to a boolean, found '%s'." % (xule_context.rule_name, result.type)), xule_context)
            
            if result.value == False:
                #skip this result
                continue
        else:
            if result.type != 'severity':
                raise XuleProcessingError(_("Dynamic severity rules must return a severity, found '%s'" % result.type), xule_context)
            
            if result.value == 'pass':
                continue
            
            severity = result.value.upper()
    
        message = get_message(raise_rule, result, xule_context)
        source_location = get_element_identifier(result, xule_context)
        filing_url = xule_context.model.modelDocument.uri

        '''
        xule_context.model.log(severity,
                               xule_context.rule_name, 
                               #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                               message,
                               #sourceFileLine=[node.sourceFileLine] + 
                               #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                               sourceFileLine=[source_location],
                               severity=xule_context.severity,
                               filing_url=filing_url)
        '''
        xule_context.global_context.message_queue.log(severity,
                                                      xule_context.rule_name, 
                                                      #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                                      message,
                                                      #sourceFileLine=[node.sourceFileLine] + 
                                                      #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                                      sourceFileLine=[source_location],
                                                      severity=xule_context.severity,
                                                      filing_url=filing_url)        
           
def evaluate_report(report_rule, xule_context): 
    
    '''NEED TO CHECK THE PRECONDITION'''
    
    if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
        raise XuleProcessingError(_("A report rule cannot have a severity function, found '%s'" % xule_context.severity_type), xule_context)
    
    result_set = evaluate(report_rule.expr[0], xule_context)
    
    for result in result_set:
#         if xule_context.severity_type == xule_context.SEVERITY_TYPE_STATIC:
#             severity = xule_context.severity.upper()
#         else:
#             raise XuleProcessingError(_("Dynamic severity rules must return a severity, found '%s'" % result.type), xule_context)

#            severity = result.value.upper()

        message = get_message(report_rule, result, xule_context)
        source_location = get_element_identifier(result, xule_context)
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
                                                      severity=xule_context.severity,
                                                      filing_url=filing_url)        
    
def evaluate_formula(formula_rule, xule_context):
    '''NEED TO CHECK THE PRECONDITION'''
    if xule_context.severity_type == xule_context.SEVERITY_TYPE_DYNAMIC:
        raise XuleProcessingError(_("A formula rule cannot have dynamic severity, found '%s'" % xule_context.severity_type), xule_context)

    var_assignments = [i for i in formula_rule.varAssigns if i.getName() == 'varAssign']
    
    '''Need to push variables, evaluate and del variables for the left and right separately, so the del_var can clean up the result sets.'''
    #push the variables into the context
    for var_assignment in var_assignments:
        xule_context.add_var(var_assignment.varName,
                             var_assignment.tagged == "#",
                             var_assignment.expr[0])
        
    left_result_set = evaluate(formula_rule.exprLeft[0], xule_context)
    
    #remove the variables for the formula
    for var_assignment in var_assignments[::-1]:
        xule_context.del_var(var_assignment.varName, left_result_set)  
    
    #push the variables into the context
    for var_assignment in var_assignments:
        xule_context.add_var(var_assignment.varName,
                             var_assignment.tagged == "#",
                             var_assignment.expr[0])
    right_result_set = evaluate(formula_rule.exprRight[0], xule_context)
    #remove the variables for the formula
    for var_assignment in var_assignments[::-1]:
        xule_context.del_var(var_assignment.varName, right_result_set)    
  
    for combine in align_result_sets(left_result_set, right_result_set, xule_context, require_binding=False):
        left_type, left_value = get_type_and_compute_value(combine['left'], xule_context)
        right_type, right_value = get_type_and_compute_value(combine['right'], xule_context)
        
        binding = formula_rule.bind[0]
        
        if binding == 'both':
            if left_type == 'unbound' or right_type == 'unbound':
                continue
        
        if binding == 'left':
            if right_type == 'unbound':
                right_value = 0
                right_type = 'int'
        if binding == 'right':
            if left_type == 'unbound':
                left_value = 0
                left_type = 'int'

        if xule_context.severity_type == xule_context.SEVERITY_TYPE_FUNCTION:
            # severity function
            xule_context.add_arg('left', None, XuleResultSet(combine['left']))
            xule_context.add_arg('right', None, XuleResultSet(combine['right']))
            difference_value = left_value - right_value
            difference_type = TYPE_SYSTEM_TO_XULE[type(difference_value)]
            xule_context.add_arg('difference', None, XuleResultSet(XuleResult(left_value - right_value, difference_type)))
        
            function_info = xule_context.find_function(xule_context.severity)
                    
            severity_function_result_set = evaluate(function_info['function_declaration'].expr[0], xule_context)
            
            xule_context.del_var('difference', severity_function_result_set)
            xule_context.del_var('right', severity_function_result_set)
            xule_context.del_var('left', severity_function_result_set)
            
            if len(severity_function_result_set.results) != 1:
                raise XuleProcessingError(_("Severity function did not return a single result, got %i" % len(severity_function_result_set.results)), xule_context)
            if severity_function_result_set.results[0].type != 'severity':
                raise XuleProcessingError(_("severity function did not return a severity, fount '%s'" % severity_function_result_set.results[0].type), xule_context)
            
            severity = severity_function_result_set.results[0].value.upper()
        else:
            if left_value != right_value:
                severity = xule_context.severity.upper()
            else:
                severity = 'PASS'

        if severity != 'PASS':
            
            if 'message' in formula_rule:
                
                #combine the tags
                combine['right'].meta = combine['meta']
#                 combine['right'].tags = combine['tags']
#                 combine['right'].facts = combine['facts']
#                 combine['right'].vars = combine['vars']
                
                #push left, right and difference tags
                combine['right'].add_tag('left', XuleResult(left_value, left_type))
                combine['right'].add_tag('right', XuleResult(right_value, right_type))
                combine['right'].add_tag('difference', XuleResult(left_value - right_value, combine['type']))
                
                message = message = get_message(formula_rule, combine['right'], xule_context)
            else:
                message = str(left_value) + " does not equal " + str(right_value)
            
            filing_url = xule_context.model.modelDocument.uri
            
            '''
            xule_context.model.log(severity,
                                   xule_context.rule_name, 
                                   #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                   message,
                                   #sourceFileLine=[node.sourceFileLine] + 
                                   #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                   sourceFileLine=None,
                                   severity=severity,
                                   filing_url=filing_url)
            '''
            xule_context.global_context.message_queue.log(severity,
                                                          xule_context.rule_name, 
                                                          #evaluateMessage(node.message, sphinxContext, resultTags, hsBindings),
                                                          message,
                                                          #sourceFileLine=[node.sourceFileLine] + 
                                                          #[(fact.modelDocument.uri, fact.sourceline) for fact in hsBindings.boundFacts],
                                                          sourceFileLine=None,
                                                          severity=severity,
                                                          filing_url=filing_url)
            
def evaluate_bool_literal(literal, xule_context):
    if literal.value == "true":
        return XuleResultSet(XuleResult(True,'bool'))
    elif literal.value == "false":
        return XuleResultSet(XuleResult(False,'bool'))
    else:
        raise XuleProcessingError(_("Invalid boolean literal found: %s" % literal.value), xule_context)

def evaluate_int_literal(literal, xule_context):
    return XuleResultSet(XuleResult(int(literal.value), 'int'))

def evaluate_float_literal(literal, xule_context):
    return XuleResultSet(XuleResult(float(literal.value), 'float'))

def evaluate_string_literal(literal, xule_context):
    return XuleResultSet(XuleResult(literal.value,'string'))

def evaluate_qname_literal(literal, xule_context):
    prefix = literal.prefix #if literal.prefix == '*' else literal.prefix[0]
    namespace = xule_context.rule_set.getNamespaceUri(prefix, xule_context.cat_file_num)
    return XuleResultSet(XuleResult(QName(prefix if prefix != '*' else None, namespace, literal.localName), 'qname'))

def evaluate_void_literal(literal, xule_context):
    ''' This could be 'none' or 'unbound'.
    '''
    return XuleResultSet(XuleResult(None, literal.value))
        
def evaluate_list_literal(literal, xule_context):
    '''
    This will call the agg_list function.
    '''
    
    list_arg = XuleResultSet()
    for lit_expr in literal:
        for result in evaluate(lit_expr, xule_context):
            list_arg.append(result)
    
    return agg_list(xule_context, list_arg)


def evaluate_set_literal(literal, xule_context):
    final_result_set = []
    for set_expr in literal:
        for result in evaluate(set_expr, xule_context):
            final_result_set.append(result)
    return XuleResultSet(XuleResult(frozenset(final_result_set), 'set'))


def evaluate_unary(unary_expr, xule_context):

    unary_result_set = evaluate(unary_expr.expr[0], xule_context)
    
    if unary_expr.unaryOp == '-':  
        final_result_set = XuleResultSet()   
        for expr_result in unary_result_set:
            xule_type, xule_value = get_type_and_compute_value(expr_result, xule_context)
            if xule_value is not None:
                final_result_set.append(XuleResult(xule_value * -1, 
                                                   xule_type, 
                                                   meta = expr_result.meta 
#                                                    expr_result.alignment, 
#                                                    expr_result.tags, 
#                                                    expr_result.facts,
#                                                    expr_result.vars
                                                   ))                
                #expr_result.value = expr_result.value if expr_result.type in ('unbound', 'none') else expr_result.value * -1 
        #pass the default forward
        default_type, default_value = get_type_and_compute_value(unary_result_set.default, xule_context)
        if default_type in ('int', 'float', 'decimal'):
            final_result_set.default = unary_result_set.default
            final_result_set.default.value = -1 * default_value
        return final_result_set
    else:
        return unary_result_set

def evaluate_not(not_expr, xule_context):
    '''SHOULD BE USING get_type_and_compute_value'''
    not_result_set = XuleResultSet()
    expr_result_set = evaluate(not_expr[0], xule_context)
    for expr_result in expr_result_set:
        not_result_set.append(XuleResult(expr_result.value if expr_result.type in ('unbound', 'none') else not expr_result.value, 
                                         expr_result.type, 
                                         meta = expr_result.meta
#                                          expr_result.alignment,
#                                          expr_result.tags,
#                                          expr_result.facts,
#                                          expr_result.vars
                                         ))
    #pass the default forward
    if expr_result_set.default.type == 'bool':
        not_result_set.default = expr_result_set.default
        not_result_set.default.value = not not_result_set.default.value

    return not_result_set 

def evaluate_mult(mult_expr, xule_context):
    ''' This handles both multiplication and division '''
    
    def evaluate_mult_operation(combined, xule_context):
        new_alignment = combined['meta'][XuleResult._ALIGNMENT]
        if combined['left'].type in ('unbound', 'none') or combined['right'].type in ('unbound', 'none'):
        #if combined['left_compute_value'] is None or combined['right_compute_value'] is None:
            #default to unbound if either or both sides are None
            #interim_rs.append(XuleResult(None, 'unbound', combined['alignment'], combined['tags']))
            return
        elif operator == '*':
            if combined['left'].type == 'unit' and combined['right'].type == 'unit':
                #units have special handling
                new_value = unit_multiply(combined['left'].value, combined['right'].value)
            else:
                new_value = combined['left_compute_value'] * combined['right_compute_value']

                if combined['left'].type == 'fact' and combined['right'].type == 'fact':
                    if combined['left'].value.isNumeric and combined['right'].value.isNumeric:
                        #need to manage the units
                        new_unit = unit_multiply(combined['left'].value.unit.measures, combined['right'].value.unit.measures)
                        if ('builtin', 'unit') in new_alignment:
                            new_alignment[('builtin', 'unit')] = hash(new_unit)
                            combined['meta'][XuleResult._ALIGNMENT] = new_alignment
                        xule_context.hash_table[('unit', hash(new_unit))] = new_unit

            return XuleResult(new_value, combined['type'], meta=combined['meta'])
            #return XuleResult(new_value, combined['type'], new_alignment, combined['tags'], combined['facts'], combined['vars'])
        elif operator == '/':
            if combined['left'].type == 'unit' and combined['right'].type == 'unit':
                #units have special handling
                new_value = unit_divide(combined['left'].value, combined['right'].value)
            else:
            
                if combined['right_compute_value'] == 0:
                    raise XuleProcessingError(_("Divide by zero error."), xule_context)
                new_value = combined['left_compute_value'] / combined['right_compute_value']

                if combined['left'].type == 'fact' and combined['right'].type == 'fact':
                    if combined['left'].value.isNumeric and combined['right'].value.isNumeric:
                        #need to manage the units
                        new_unit = unit_divide(combined['left'].value.unit.measures, combined['right'].value.unit.measures)
                        if ('builtin', 'unit') in new_alignment:
                            new_alignment[('builtin', 'unit')] = hash(new_unit)
                            combined['meta'][XuleResult._ALIGNMENT] = new_alignment
                        xule_context.hash_table[('unit', hash(new_unit))] = new_unit
            
            return XuleResult(new_value, combined['type'], meta=combined['meta'])
            #return XuleResult(new_value, combined['type'], new_alignment, combined['tags'], combined['facts'], combined['vars'])
        else:
            raise XuleProcessingError(_("Unknown operator '%s' found in multiplication/division operation." % operator), xule_context)

    left_rs = evaluate(mult_expr[0], xule_context)
    for tok in mult_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right_rs = evaluate(tok, xule_context)
            interim_rs = XuleResultSet()
            
            for combined in align_result_sets(left_rs, right_rs, xule_context,
                                              trace_info=collections.deque([(xule_context.trace_level + 1, '', None, XuleResult(operator, 'string'))])):
                result = evaluate_mult_operation(combined, xule_context)
                if result is not None:
                    interim_rs.append(result)
                    
            left_rs = interim_rs
    
    return left_rs

def evaluate_add(add_expr, xule_context):
    ''' This handles both adding and subtracting '''       
    def evaluate_add_operation(combined, xule_context):
        if operator[0] != '|':
            if combined['left_compute_value'] is None:
                if type(combined['right_compute_value']) in (int, float, decimal.Decimal):
                    left_value = 0
                else:
                    return
            else:
                left_value = combined['left_compute_value']
        else:
            if combined['left'].type in ('unbound', 'none'):
                return
            else:
                left_value = combined['left_compute_value']
        
        if operator[-1] != '|':
            if combined['right_compute_value'] is None:
                if type(combined['left_compute_value']) in (int, float, decimal.Decimal):
                    right_value = 0
                else:
                    return
            else:
                right_value = combined['right_compute_value']
        else:
            if combined['right'].type in ('unbound', 'none'):
                return
            else:
                right_value = combined['right_compute_value']
        
    #                 if left_value is None or right_value is None:
    #                     #interim_rs.append(XuleResult(None, 'unbound', combined['alignment'], combined['tags']))
    #                     pass
        if '+' in operator:
            '''SHOULD REALLY CHECK THE RESULT SET TYPE INSTEAD OF INSTANCEOF.'''
            if isinstance(combined['left_compute_value'], frozenset) and isinstance(combined['right_compute_value'], frozenset):
                #use union for sets
                return XuleResult(left_value | right_value, combined['type'], meta=combined['meta'])
            else:
                return XuleResult(left_value + right_value, combined['type'], meta=combined['meta'])
        elif '-' in operator:
            return XuleResult(left_value - right_value, combined['type'], meta=combined['meta'])
        else:
            raise XuleProcessingError(_("Unknown operator '%s' found in addition/subtraction operation." % operator), xule_context)
            
    left_rs = evaluate(add_expr[0], xule_context)
    for tok in add_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right_rs = evaluate(tok, xule_context)
            interim_rs = XuleResultSet()
            
            for combined in align_result_sets(left_rs, right_rs, xule_context, require_binding=False, 
                                              trace_info=collections.deque([(xule_context.trace_level + 1, '', None, XuleResult(operator, 'string'))])):
                ''' determine if unbound should be zero '''
                result = evaluate_add_operation(combined, xule_context)
                if result is not None:
                    interim_rs.append(evaluate_add_operation(combined, xule_context))
                
            left_rs = interim_rs
            
    return left_rs

def evaluate_comp(comp_expr, xule_context):
    ''' This handles all forms of comparison operations.
        Like add and multiplication expressions, there can be a series
        of operands and operators.
    '''
    
    def evaluate_comp_operation(combined, xule_context):
        left_type, left_value = get_type_and_compute_value(combined['left'], xule_context)
        right_type, right_value = get_type_and_compute_value(combined['right'], xule_context)
        
        if left_type in ('instant', 'duration') and right_type in ('instant', 'duration'):
            left_compute_value = XulePeriodComp(combined['left_compute_value'])
            right_compute_value = XulePeriodComp(combined['right_compute_value'])
        else:
            left_compute_value = combined['left_compute_value']
            right_compute_value = combined['right_compute_value']
            
        if combined['left'].type == 'unbound' or combined['right'].type == 'unbound':
            return XuleResult(None, 'unbound', meta=combined['meta'])
        elif operator == '==':
            return XuleResult(left_compute_value == right_compute_value, 'bool', meta=combined['meta'])
        elif operator == '!=':
            return XuleResult(left_compute_value != right_compute_value, 'bool', meta=combined['meta'])
        elif operator == '<':
            return XuleResult(left_compute_value < right_compute_value, 'bool', meta=combined['meta'])
        elif operator == '<=':
            return XuleResult(left_compute_value <= right_compute_value, 'bool', meta=combined['meta'])
        elif operator == '>':
            return XuleResult(left_compute_value > right_compute_value, 'bool', meta=combined['meta'])
        elif operator == '>=':
            return XuleResult(left_compute_value >= right_compute_value, 'bool', meta=combined['meta'])
        else:
            raise XuleProcessingError(_("Unknown operator '%s' found in comparison operation." % operator), xule_context)
    
    orig_left_rs = evaluate(comp_expr[0], xule_context)
    left_rs = orig_left_rs#.dup()
    for tok in comp_expr[1:]:
        if tok.getName() == "op":
            operator = tok.value
        else:
            right_rs = evaluate(tok, xule_context)
            interim_rs = XuleResultSet()
            
            for combined in align_result_sets(left_rs, right_rs, xule_context, require_binding=True,
                                              trace_info=collections.deque([(xule_context.trace_level + 1, '', None, XuleResult(operator, 'string'))])):
                interim_rs.append(evaluate_comp_operation(combined, xule_context))

            left_rs = interim_rs
    
    left_rs.default = evaluate_comp_operation(combine_defaults(orig_left_rs, right_rs, xule_context), xule_context)
    return left_rs

def evaluate_and(and_expr, xule_context):
    ''' If any operand evaluates to none, the and expressiion will result to false. 
        May need to handle none so the expression returns none.
    '''
    '''THIS IS THE NON LAZY VERSION. 2015-01-09'''
#     left_rs = evaluate(and_expr[0], xule_context)
#     for right_expr in and_expr[1:]:
#         right_rs = evaluate(right_expr, xule_context)
#  
#         interim_rs = XuleResultSet()
#          
#         for combined in align_result_sets(left_rs, right_rs, xule_context):
#             if combined['left_compute_value'] is None or combined['right_compute_value'] is None:
#                 interim_rs.append(XuleResult(None, 'unbound', combined['alignment'], combined['tags']))
#             else:
#                 interim_rs.append(XuleResult(combined['left_compute_value'] and combined['right_compute_value'], 'bool', combined['alignment'], combined['tags']))
#  
#         left_rs = interim_rs
#  
#     return left_rs 

    '''THIS IS THE LAZY VERSION 2015-01-09'''
    left_result_set = evaluate(and_expr[0], xule_context)
    return lazy_iteration_new(left_result_set, and_expr[1:], boolean_and, False, xule_context)

def boolean_and(left, right):
    if left is not None and right is not None:
        return left and right
    elif left is None and right is None:
        return None
    else:
        #one is none
        if left is None:
            if right == False:
                return False
            else:
                return None
        else:
            if left == False:
                return False
            else:
                return None


def lazy_iteration_new(left_result_set, right_exprs, operation_function, stop_value, xule_context):
    final_result_set = XuleResultSet()
    new_left_result_set = XuleResultSet()
    
    #track the alignments that processed on the left.
    left_alignments = collections.defaultdict(lambda : {'all': 0, 'stopped': 0})
    
    for left_result in left_result_set:
        alignment_key = None if left_result.alignment is None else frozenset(left_result.alignment.items())
        left_alignments[alignment_key]['alignment'] = left_result.alignment
        left_alignments[alignment_key]['all'] += 1
        left_type, left_value = get_type_and_compute_value(left_result, xule_context)
        if left_value == stop_value:
            final_result_set.append(left_result)
            left_alignments[alignment_key]['stopped'] += 1
        else:
            new_left_result_set.append(left_result)

    final_result_set.default = left_result_set.default
    new_left_result_set.default = left_result_set.default

    for alignment_key, alignment_counts in left_alignments.items():
        if alignment_counts['all'] == alignment_counts['stopped']:
            #this alignment is no longer need in the evaluatin of the right
            xule_context.alignment_filters.append(None if alignment_key is None else dict(alignment_key))
    
    if len(right_exprs) > 0:
        right_expr = right_exprs[0]       
        right_result_set = evaluate(right_expr, xule_context)
        
        interim_result_set = XuleResultSet()
        for combined in align_result_sets(new_left_result_set, right_result_set, xule_context, require_binding=False, use_defaults='left' if len(new_left_result_set.results) == 0 else 'both'):
            if not(len(new_left_result_set.results) == 0 and combined['alignment'] is None):
                interim_result_set.append(lazy_iteration_combine(combined, operation_function, xule_context))
        
        interim_result_set.default = lazy_iteration_combine(combine_defaults(new_left_result_set, right_result_set, xule_context), operation_function, xule_context)
           
        if len(right_exprs) > 1:
            next_iteration_result_set = lazy_iteration_new(interim_result_set, right_exprs[1:], operation_function, stop_value, xule_context)
            final_result_set.append(next_iteration_result_set)
            final_result_set.default = next_iteration_result_set.default
        else:
            final_result_set.append(interim_result_set)
            final_result_set.defaul = interim_result_set.default
    
    #reset the alignment filters
    xule_context.alignment_filters = []
    
    return final_result_set

def lazy_iteration_combine(combined, operation_function, xule_context):
    new_value = operation_function(combined['left_compute_value'], combined['right_compute_value'])
    return XuleResult(new_value,
                                         'unbound' if new_value is None else 'bool',
                                         meta=combined['meta'])    

# def lazy_iteration_start(left_result_set, operand_exprs, operation_function, stop_value, xule_context):
#     final_result_set = XuleResultSet()
#      
#     has_unaligned_results = False
#     matched_alignments = []
#     for left_result in left_result_set:
#         if left_result.alignment is None:
#             has_unaligned_results = True
#         lazy_result_set, matched_alignments = lazy_iteration(left_result, False, matched_alignments, operand_exprs, operation_function, stop_value, xule_context)
#         final_result_set.append(lazy_result_set)
#      
#     if not has_unaligned_results:
#         final_result_set.append(lazy_iteration(left_result_set.default, True, matched_alignments, operand_exprs, operation_function, stop_value, xule_context))
#      
#     return final_result_set    
#      
# def lazy_iteration(left_result, is_left_default, matched_alignments, operand_exprs, operation_function, stop_value, xule_context):
#      
#     final_result_set = XuleResultSet()
#  
#     left_type, left_value = get_type_and_compute_value(left_result, xule_context)
#      
# #     if left_value is None:
# #         final_result_set.append(XuleResult(None, 'unbound', meta=left_result.meta))
# #         if not is_left_default:
# #             matched_alignments.append(left_result.alignment)
# #     
# #     else:
#  
#     if left_value == stop_value and not is_left_default:
#         #stop for this result
#         final_result_set.append(XuleResult(stop_value, 'bool',
#                                            meta=left_result.meta 
#                                            ))
#         if not is_left_default:
#             matched_alignments.append(left_result.alignment)
#     else:
#         #'''DONT PUSH THE FILTER. LET THE ALGIN DO THE FILTERING.'''
#         #push the filter and evaluate the right
# #             if left_result.alignment is not None:
# #                 xule_context.filter_add('other', alignment_to_aspect_info(left_result.alignment, xule_context))
#  
#         right_expr = operand_exprs[0]
#  
#         '''Add the single value left resulte variables'''   
#         single_vars = push_single_value_variables(left_result.vars, xule_context)       
#         right_result_set = evaluate(right_expr, xule_context)            
#         '''Will pop at the end of this iteration'''
#          
# #             if left_result.alignment is not None:
# #                 xule_context.filter_del()
#  
#         new_left_result_set = XuleResultSet()
#          
#         for combine in align_result_sets(XuleResultSet(left_result), right_result_set, xule_context, require_binding=False, use_defaults='none' if is_left_default else 'right'):            
#             right_result = combine['right']
#             right_value = combine['right_compute_value']
#              
#             if not is_left_default or (is_left_default and combine['alignment'] not in matched_alignments):
#                 combined_value = operation_function(left_value, right_value)
#                 new_left_result_set.append(XuleResult(combined_value,
#                                                       'unbound' if combined_value is None else 'bool',
#                                                       meta=combine['meta']
#                                                       ))                        
#                 if not is_left_default:
#                     matched_alignments.append(combine['alignment'])
#          
#         if len(operand_exprs) > 1:
#             final_result_set.append(lazy_iteration_start(new_left_result_set, operand_exprs[1:], operation_function, stop_value, xule_context))
#         else:
#             final_result_set.append(new_left_result_set)
#          
#         '''Remove the pushed single value left result variables.'''
#         pop_single_value_variables(single_vars, right_result_set, xule_context) 
#      
#     if not is_left_default:        
#         return final_result_set, matched_alignments
#     else:
#         return final_result_set

def evaluate_or(or_expr, xule_context): 
    ''' If any operand evaluates to none, the and expressiion will result to false. 
        May need to handle none so the expression returns none.
    '''
#     '''THIS IS THE NON LAZY VERSION 2015-01-09'''
#     left_rs = evaluate(or_expr[0], xule_context)
#     for right_expr in or_expr[1:]:
#         right_rs = evaluate(right_expr, xule_context)
#         interim_rs = XuleResultSet()
#         
#         for combined in align_result_sets(left_rs, right_rs, xule_context):
#             if combined['left_compute_value'] is None or combined['right_compute_value'] is None:
#                 interim_rs.append(XuleResult(None, 'unbound', combined['alignment'], combined['tags']))
#             else:
#                 interim_rs.append(XuleResult(combined['left_compute_value'] or combined['right_compute_value'], 'bool', combined['alignment'], combined['tags']))
# 
#         left_rs = interim_rs
#     
#     return left_rs   


    '''THIS IS THE LAZY VERSION 2015-01-09'''
    left_result_set = evaluate(or_expr[0], xule_context)
    return lazy_iteration_new(left_result_set, or_expr[1:], boolean_or, True, xule_context)

def boolean_or(left, right):
    if left is not None and right is not None:
        return left or right
    elif left is None and right is None:
        return None
    else:
        #one is none
        if left is None:
            if right == False:
                return None
            else:
                return True
        else:
            if left == False:
                return None
            else:
                return True


def evaluate_block(block_expr, xule_context):
    var_assignments = [i for i in block_expr if i.getName() == 'varAssign']
    #push the variables into the context
    for var_assignment in var_assignments:
        xule_context.add_var(var_assignment.varName,
                             var_assignment.tagged == "#",
                             var_assignment.expr[0])
    
    result_set = evaluate(block_expr.expr[0], xule_context)
    
    #remove the variables for the block
    for var_assignment in var_assignments[::-1]:
        #remove the variable definision from the context
        var_info = xule_context.del_var(var_assignment.varName, result_set)
        
    return result_set

def evaluate_var_ref(var_ref, xule_context):
    #Look for the variable in the xule_context
    var_info = xule_context.find_var(var_ref.varName)

    #verify that a variable was found
    if not var_info:
        raise XuleProcessingError(_("Variable '%s' does not exist" % var_ref.varName), xule_context)
    else:
            if var_info['calculated']:
                var_value_rs = var_info['value']
            else:
                #first refererence to the variable, need to evaluate it.
                #suspend any alignment_filters - want the variable to represent all the facts, the alignment filter will be used during the retrieval of the values.
                saved_alignment_filters = xule_context.alignment_filters
                xule_context.alignment_filters = []
                #need to ignore variables from this point in the stack to the end of the stack. This prevents infinite recursion if a variable refers to a variable with the same name.
                if var_info['type'] == xule_context._VAR_TYPE_VAR:
                    saved_ignore_vars = xule_context.ignore_vars[:]
                    xule_context.ignore_vars = range(var_info['index'], len(xule_context._vars))
                var_value_rs = evaluate(var_info['expr'], xule_context)
                if var_info['type'] == xule_context._VAR_TYPE_CONSTANT:
                    var_value_rs = var_value_rs.dup() 
                #restore the alignment filters
                xule_context.alignment_filters = saved_alignment_filters
                if var_info['type'] == xule_context._VAR_TYPE_VAR:
                    xule_context.ignore_vars = saved_ignore_vars
                
                xule_context.var_add_value(var_ref.varName, var_value_rs)
    
    #A copy is returned so the var reference can never be messed up
    copy_rs = XuleResultSet()
    copy_rs.default = var_value_rs.default
    if var_info['tag'] == True and 'expr' in var_info:
        tag_default(copy_rs, var_info['expr'], var_info['name'], xule_context)
    
    for res in var_value_rs:
        #check if the result alignment is in the alignment filters
        if res.alignment in xule_context.alignment_filters:
            continue
        
        #copy_result = XuleResult(res.value, res.type, res.alignment, res.tags, res.facts, res.vars)
        copy_result = res.dup()
        #adjust the trace levels in the trace. The original level is based on when the variable was declared. It needs to be adjusted for where
        #it is referenced.
        if xule_context.show_trace:
            if len(copy_result.trace) > 0:
                trace_diff = xule_context.trace_level - copy_result.trace[0][0] + 1
                new_trace = collections.deque()
                for step in copy_result.trace:
                    new_trace.append((step[0] + trace_diff, step[1], step[2], step[3]))
                copy_result.trace = new_trace
        #this is backdoor to the original value
        copy_result.original_result = res
        copy_rs.append(copy_result)
    
    return copy_rs
    #return var_value_rs.dup()

def evaluate_function_ref(function_ref, xule_context):
    if function_ref.functionName in BUILTIN_FUNCTIONS:
        #this is xule built in function
        function_info = BUILTIN_FUNCTIONS[function_ref.functionName]
        #if function_info[FUNCTION_TYPE] == 'aggregate':
        
        if function_info[FUNCTION_TYPE] == 'regular' and len(function_ref.functionArgs) != function_info[FUNCTION_ARG_NUM]:
            raise XuleProcessingError(_("The '%s' function must have only %i argument, found %i." % (function_ref.functionName, 
                                                                                           function_info[FUNCTION_ARG_NUM],
                                                                                           len(function_ref.functionArgs))), xule_context)
     
        function_args = []
        for i in range(len(function_ref.functionArgs)):
            function_args.append(evaluate(function_ref.functionArgs[i][0], xule_context))
        
        return function_info[FUNCTION_EVALUATOR](xule_context, *function_args)
    else:
        #find the function
        function_info = xule_context.find_function(function_ref.functionName)
        if not function_info:
            raise XuleProcessingError("Function '%s' not found" % function_ref.functionName, xule_context)
        else:
            matched_args = match_function_arguments(function_ref, function_info['function_declaration'], xule_context)
            
            for arg in matched_args:
                xule_context.add_arg(arg['name'],
                                     arg['tagged'],
                                     arg['value'])
                if arg['tagged']:
                    for result in arg['value']:
                        result.add_tag(arg['name'], result)
                        
            if len(matched_args) == 0 and function_ref.functionName in xule_context.function_cache:
                result_set = xule_context.function_cache[function_ref.functionName]
            else:                    
                result_set = evaluate(function_info['function_declaration'].expr[0], xule_context)
                if len(matched_args) == 0:
                    xule_context.function_cache[function_ref.functionName] = result_set
            
            #remove the args
            for x in matched_args[::-1]:
                xule_context.del_var(x['name'], result_set)

            return result_set

def evaluate_tagged(tagged_expr, xule_context):
    result_set = evaluate(tagged_expr.expr[0], xule_context)
    
    for result in result_set:
        result.add_tag(tagged_expr.tagName, result)
    
    tag_default(result_set, tagged_expr.expr[0], tagged_expr.tagName, xule_context)
    
    return result_set

def tag_default(result_set, expr, tag_name, xule_context):
    if expr.getName() == 'factset':
        #for lineItem[]
        if 'lineItemAspect' in expr:
            fact_name_rs = evaluate(expr.lineItemAspect.qName, xule_context)
            result_set.default.add_tag(tag_name, XuleResult(fact_name_rs.results[0], 'empty_fact'))
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
                            aspect_member_rs = evaluate(aspect_filter.aspectExpr[0], xule_context)
                            if len(aspect_member_rs.results) > 0:
                                result_set.default.add_tag(tag_name, XuleResult(aspect_member_rs.results[0], 'empty_fact'))
                            else:
                                result_set.default.add_tag(tag_name, XuleResult('unknown', 'empty_fact'))
                        else:
                            #for [lineItem in} - this will pick up each
                            aspect_member_rs = aspect_member_rs = evaluate(aspect_filter.aspectExpr[0], xule_context)
                            if len(aspect_member_rs.results) > 0:
                                line_items = []
                                for aspect_member_result in aspect_member_rs.results[0].value:
                                    if aspect_member_result.type == 'qname':
                                        line_items.append(str(aspect_member_result.value))
                                    elif aspect_member_result.type == 'concept':
                                        line_items.append(str(aspect_member_result.value.qname))
                                if len(line_items) == 1:
                                    line_item_string = str(line_items[0])
                                else:
                                    line_item_string = "one of (" + ", ".join(line_items) + ")"
                                result_set.default.add_tag(tag_name, XuleResult(line_item_string, 'empty_fact'))
                            else:
                                result_set.default.add_tag(tag_name, XuleResult('unknown', 'empty_fact'))
                if not found_line_item:
                    #doesn't have a line item at all
                    result_set.default.add_tag(tag_name, XuleResult('unknown', 'empty_fact'))
            else:
                #there are no aspect fitlers
                result_set.default.add_tag(tag_name, XuleResult('unknown', 'empty_fact'))

def evaluate_property(property_expr, xule_context):


    if 'expr' in property_expr:
        left_result_set = evaluate(property_expr.expr[0], xule_context)
    else:
        #if there is no object of the property.
        left_result_set = XuleResultSet(XuleResult(None, 'unbound'))

    
    #This is the chain of properties
    properties = [x for x in property_expr.properties]
    
    final_result_set = evaluate_property_detail(properties, left_result_set, xule_context)
    
    return final_result_set
    
def evaluate_property_detail(property_exprs, left_result_set, xule_context):
    
    #need to copy so not to mess up the list when recursing back up
    current_property_exprs = property_exprs[:]
    current_property_expr = current_property_exprs.pop(0)
    
    if current_property_expr.propertyName not in PROPERTIES:
        raise XuleProcessingError(_("'%s' is not a valid property." % current_property_expr.propertyName), xule_context)
    
    #The property table contains a row for each combination of left objects and all arguments.
    xule_context.trace_level += 1
    property_table = prepare_property_args(left_result_set, current_property_expr.propertyArgs, current_property_expr.propertyName, xule_context)
    xule_context.trace_level -= 1
    
    property_info = PROPERTIES[current_property_expr.propertyName] 
    
    if property_info[PROP_ARG_NUM] is not None:
        if len(current_property_expr.propertyArgs) != property_info[PROP_ARG_NUM]:
            raise XuleProcessingError(_("Property '%s' must have %s arguments. Found %i." % (current_property_expr.propertyName,
                                                                                             property_info[PROP_ARG_NUM],
                                                                                             len(current_property_expr.propertyArgs))), 
                                      xule_context)    
    
    current_property_result_set = XuleResultSet()
    
    for property_record in property_table:
        left_result = property_record[0]
        property_args = property_record[1] #this is a tuple

        #if the left object is unbound then return unbound
        if not property_info[PROP_UNBOUND_ALLOWED] and left_result.type in ('unbound', 'none'):
            property_result_set = XuleResultSet(XuleResult(left_result.value, left_result.type))
        else:
            #check the left object is the right type
            if len(property_info[PROP_OPERAND_TYPES]) > 0:
                if left_result.type not in property_info[PROP_OPERAND_TYPES]:
                    if not any([xule_castable(left_result, allowable_type, xule_context) for allowable_type in property_info[PROP_OPERAND_TYPES]]):
                        raise XuleProcessingError(_("Property '%s' is not a property of a '%s'.") % (current_property_expr.propertyName,
                                                                                                     left_result.type), 
                                                  xule_context) 
                        
            '''Add the single value left resulte variables'''
            single_vars = push_single_value_variables(left_result.vars, xule_context)       
            
            property_result_set = property_info[PROP_FUNCTION](xule_context, left_result, *property_args)
            
            '''Remove the pushed single value left result variables.'''
            pop_single_value_variables(single_vars, property_result_set, xule_context)

        for property_result in property_result_set:
            property_result.meta = combine_result_meta(property_result, left_result, xule_context,
                                                       trace_info=collections.deque([(xule_context.trace_level + 1, 'property', (current_property_expr.propertyName,), property_result)]))
#             property_result.alignment = left_result.alignment
#             property_result.tags = left_result.tags
#             property_result.facts = left_result.facts
#             property_result.vars = left_result.vars
            
            if 'tagName' in current_property_expr:
                property_result.add_tag(current_property_expr.tagName, property_result)
            
            current_property_result_set.append(property_result)


    if len(current_property_exprs) == 0:
        #we are at the end of the property chain, so this is the final result
        return current_property_result_set
    else:  
        #there are more properties, so recurse to process the next property in the chain
        return evaluate_property_detail(current_property_exprs, current_property_result_set, xule_context)          

def evaluate_print(print_expr, xule_context):
    print_rs = evaluate(print_expr.printValue[0], xule_context)
    
    for res in print_rs:
        xule_context.model.log("INFO", "xule:print", "%s: %s" % (res.type, res.value))

    return evaluate(print_expr.passThroughExpr[0], xule_context)

def evaluate_if(if_expr, xule_context):
    condition_result_set = evaluate(if_expr.condition[0], xule_context)
    
    else_ifs = [x for x in if_expr if x.getName() == 'elseIfExpr']
    return evaluate_if_start(condition_result_set, if_expr.thenExpr[0], else_ifs, if_expr.elseExpr[0], xule_context)

def evaluate_if_start(condition_result_set, then_expr, else_if_exprs, else_expr, xule_context):
    final_result_set = XuleResultSet()
    matched_alignments = []
    
    for condition_result in condition_result_set:
        then_else_result_set, matched_alignments = evaluate_if_detail(condition_result, False, then_expr, else_if_exprs, else_expr, matched_alignments, xule_context)
        final_result_set.append(then_else_result_set)
        
    final_result_set.append(evaluate_if_detail(condition_result_set.default, True, then_expr, else_if_exprs, else_expr, matched_alignments, xule_context))

    return final_result_set

def evaluate_if_detail(condition_result, is_left_default, then_expr, else_if_exprs, else_expr, matched_alignments, xule_context):
    
    final_result_set = XuleResultSet()

    condition_type, condition_value = get_type_and_compute_value(condition_result, xule_context)
    if condition_type is None:
        raise XuleProcessingError(_("If condition evaluated to unbound"), xule_context)

    '''Push the variables from the condition result. This will override the same variable with the full result set
       to just the single value on the condition result.'''
    single_vars = push_single_value_variables(condition_result.vars, xule_context)
    
    if condition_type in ('unbound', 'none'):
        interim_result_set = XuleResultSet(XuleResult(None, 'unbound', 
                                                      meta=condition_result.meta
#                                                       condition_result.alignment, 
#                                                       condition_result.tags,
#                                                       condition_result.facts,
#                                                       condition_result.vars
                                                      ))
    elif condition_type != 'bool':
        raise XuleProcessingError(_("If condition is not a boolean, found '%s'" % condition_type), xule_context)
    
    elif condition_value:
        interim_result_set = evaluate(then_expr, xule_context)
    else:
        if len(else_if_exprs) > 0:
            current_list = else_if_exprs[:]
            current_else_if_expr = current_list.pop(0)
            next_control_result_set = evaluate(current_else_if_expr.condition[0], xule_context)
            interim_result_set = evaluate_if_start(next_control_result_set, current_else_if_expr.thenExpr[0], current_list, else_expr, xule_context)
        
        else:
            interim_result_set = evaluate(else_expr, xule_context)

    #removed pushed single value vars
    pop_single_value_variables(single_vars, interim_result_set, xule_context)

    #align condition and results
    for combined in align_result_sets(XuleResultSet(condition_result), interim_result_set, xule_context, align_only=True, require_binding=False, use_defaults='none' if is_left_default else 'right'):
        if not is_left_default or (is_left_default and combined['alignment'] not in matched_alignments):
            if not (is_left_default and combined['left'].type == 'unbound' and combined['right'].type == 'unbound'):
                final_result_set.append(XuleResult(combined['right'].value, combined['right'].type,
                                                   meta=combined['meta']
    #                                                combined['alignment'],
    #                                                combined['tags'],
    #                                                combined['facts'],
    #                                                combined['vars']
                                                   ))
                if not is_left_default:
                    matched_alignments.append(combined['alignment'])
    
    if not is_left_default:
        return final_result_set, matched_alignments
    else:
        return final_result_set        

'''THIS IS NOT USED'''
def evaluate_if_orig(if_expr, xule_context):
    
    final_result_set = XuleResultSet()
    
    condition_rs = evaluate(if_expr.condition[0], xule_context)
    
    for condition_result in condition_rs:
        '''Push the variables from the condition result. This will override the same variable with the full result set
           to just the single value on the condition result.'''
        
        single_vars = push_single_value_variables(condition_result.vars, xule_context)
 
        interim_result_set = XuleResultSet()
        
        if condition_result.value:
            interim_result_set = evaluate(if_expr.thenExpr[0], xule_context)

            #interim_result_set.append(evaluate(if_expr.thenExpr[0], xule_context))
        else:
            #create a list of of the elseif expressions with the final else at the end.
            else_ifs = [x for x in if_expr if x.getName() == 'elseIfExpr']

            else_ifs.append(if_expr.elseExpr)
                
            interim_result_set = evaluate_else_if(else_ifs, xule_context)
            
        '''Remove the pushed condition variables.'''
        pop_single_value_variables(single_vars, interim_result_set, xule_context)

        #align condition and results
        for combined in align_result_sets(XuleResultSet(condition_result), interim_result_set, xule_context, align_only=True, use_defaults='right'):
            final_result_set.append(XuleResult(combined['right'].value, combined['right'].type,
                                               meta=combined['meta']
#                                                combined['alignment'],
#                                                combined['tags'],
#                                                combined['facts'],
#                                                combined['vars']
                                               )) 
    
    return final_result_set

'''THIS IS NOT USED'''
def evaluate_else_if(else_if_exprs, xule_context):
    final_result_set = XuleResultSet()
    
    #at the end, return the empty result set.
    if len(else_if_exprs) == 0:
        return final_result_set
    
    current_list = else_if_exprs[:]
    current_else_if_expr = current_list.pop(0)
    
    if current_else_if_expr.getName() == "elseExpr":
        #we have fallen into the else condition, so just evaluate it
        final_result_set.append(evaluate(current_else_if_expr[0], xule_context))
        return final_result_set

    condition_rs = evaluate(current_else_if_expr.condition[0], xule_context)
    
    for else_if_result in condition_rs:
        
        '''Push the single values for variables from the evaluation of the else if condition.'''
        single_vars = push_single_value_variables(else_if_result.vars, xule_context)
        
        interim_result_set = XuleResultSet()
        
        if else_if_result.value:
            interim_result_set.append(evaluate(current_else_if_expr.thenExpr[0], xule_context))
        else:
            interim_result_set.append(evaluate_else_if(current_list, xule_context))

        #removed pushed single value vars
        pop_single_value_variables(single_vars, interim_result_set, xule_context)

        #align condition and results
        for combined in align_result_sets(XuleResultSet(else_if_result), interim_result_set, xule_context, align_only=True, use_defaults='right'):
            #re-asign the alignment from the result of the combining
            combined['right'].meta = combined['meta']
#             combined['right'].alignment = combined['alignment']
#             combined['right'].tags = combined['tags']
#             combined['right'].facts = combined['facts']
#             combined['right'].vars = combined['vars']
            final_result_set.append(combined['right'])
    
    return final_result_set

'''THIS IS NOT USED'''    
def evaluate_for_orig(for_expr, xule_context):
    final_result_set = XuleResultSet()
    #evaluated = False
    
    #print("Enter for %s: %s" % (for_expr.forVar, str(datetime.datetime.today())))
      
    '''This evaluates the for loop expressions that controls the looping.
       The result should be something that is iterable (list, set, sequence).
    '''
    control_rs = evaluate(for_expr.forLoop[0], xule_context)

    #need to flatten lists and sets and combine with all other results
    control_results = []
    for control_result in control_rs:
        if control_result.type in ('list','set'):
            for sub_result in control_result.value:
                control_results.append(sub_result)
        else:
            control_results.append(control_result)
    
    #use the flatten list instead of the control result set
    for control_result in control_results:
        
        #Push the single value vars in the control result
        single_vars = push_single_value_variables(control_result.vars, xule_context)
            
        #push the control variable          
        xule_context.add_arg(for_expr.forVar,
                             for_expr.tagged == '#',
                             XuleResultSet(control_result))
        
        for_body_result_set = evaluate(for_expr.expr[0], xule_context)
    
        #remove the control variable for the for loop
        xule_context.del_var(for_expr.forVar, for_body_result_set)
        
        '''Remove the pushed single value control variables.'''
        pop_single_value_variables(single_vars, for_body_result_set, xule_context)
 
        #align
        for combined in align_result_sets(XuleResultSet(control_result), for_body_result_set, xule_context, align_only=True, use_defaults='none'):
            #re-asign the alignment from the result of the combining
            combined['right'].meta = combined['meta']
#             combined['right'].alignment = combined['alignment']
#             combined['right'].tags = combined['tags']
#             combined['right'].facts = combined['facts']
#             combined['right'].vars= combined['vars']
            if 'tagged' in for_expr:
                combined['right'].add_tag(for_expr.forVar, control_result)
        
            final_result_set.append(combined['right'])            

    return final_result_set 

def evaluate_for(for_expr, xule_context):
    final_result_set = XuleResultSet()
    
    control_rs = evaluate(for_expr.forLoop[0], xule_context)

    #need to flatten lists and sets and combine with all other results
    control_results = []
    for control_result in control_rs:
        if control_result.type in ('list','set'):
            for sub_result in control_result.value:
                control_results.append(sub_result)
        else:
            control_results.append(control_result)
    
    matched_alignments = []
    #use the flatten list instead of the control result set
    for control_result in control_results:
         if control_result.type != 'unbound':
            for_body_result_set, matched_alignments = evaluate_for_body(control_result, False, for_expr, matched_alignments, xule_context)
            final_result_set.append(for_body_result_set)  
        
    '''THIS IS A BIT A KLUGE
       If the default is a list or set, it will be empty anyway, so there is nothing to atempt another iteration of the loop on.'''
    if control_rs.default.type not in ('list', 'set'):
        final_result_set.append(evaluate_for_body(control_rs.default, True, for_expr, matched_alignments, xule_context))
    
    return final_result_set
    
def evaluate_for_body(control_result, is_left_default, for_expr, matched_alignments, xule_context):
    final_result_set = XuleResultSet()
    
    #Push the single value vars in the control result
    single_vars = push_single_value_variables(control_result.vars, xule_context)
        
    #push the control variable          
    xule_context.add_arg(for_expr.forVar,
                         for_expr.tagged == '#',
                         XuleResultSet(control_result))
    
    for_body_result_set = evaluate(for_expr.expr[0], xule_context)
    
    #remove the control variable for the for loop
    xule_context.del_var(for_expr.forVar, for_body_result_set)
    
    '''Remove the pushed single value control variables.'''
    pop_single_value_variables(single_vars, for_body_result_set, xule_context)
    
    #align
    for combined in align_result_sets(XuleResultSet(control_result), for_body_result_set, xule_context, align_only=True, require_binding=False, use_defaults='none' if is_left_default else 'right'):
        #re-asign the alignment from the result of the combining
        if not is_left_default or (is_left_default and combined['alignment'] not in matched_alignments):
            combined['right'].meta = combined['meta']
#             combined['right'].alignment = combined['alignment']
#             combined['right'].tags = combined['tags']
#             combined['right'].facts = combined['facts']
#             combined['right'].vars= combined['vars']
            if 'tagged' in for_expr:
                combined['right'].add_tag(for_expr.forVar, control_result)
        
            final_result_set.append(combined['right'])    
            
            if not is_left_default:
                matched_alignments.append(combined['alignment'])
        
    if not is_left_default:
        return final_result_set, matched_alignments
    else:
        return final_result_set

def evaluate_with(with_expr, xule_context):
    '''
    With expressions create a non-aligned filter for any factsets in the expression. This is implemented by adding the aspect filters
    to the context. They can be picked up in the factset evaluator.
    '''

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
    
    final_result_set = evaluate(with_expr.expr[0], xule_context)
    
    #remove the filter
    xule_context.filter_del()
    
    return final_result_set

def convert_result_to_qname(result, xule_context):
    res_type, res_value = get_type_and_compute_value(result, xule_context)
    
    if res_type == 'concept':
        return res_value.qname
    elif res_type == 'qname':
        return res_value
    elif res_type in ('unbound', 'none'):
        return None
    else:
        raise XuleProcessingError(_("The value for lineItem must be a qname or concept, found '%s'." % result.type), xule_context)

def convert_result_to_model_period(result, xule_context):
    res_type, res_value = get_type_and_compute_value(result, xule_context)
    
    if result.from_model:
        return res_value
    else:
        #need to adjust instant and end_date. The model has instant and end dates of the next day because python treats midnight as the begining of the day.
        if res_type == 'instant':
            return res_value + datetime.timedelta(days=1)
        elif res_type == 'duration':
            if result.value[0] == datetime.datetime.min and result.value[1] == datetime.datetime.max:
                #this is forever, don't do anything
                return res_value
            else:
                return (res_value[0], res_value[1] + datetime.timedelta(days=1))
        else:
            raise XuleProcessingError(_("Converting result to a period, expected 'instant' or 'duration' but found '%s'" % result.type), xule_context)

def convert_results_to_values(results, aspect_type, aspect, xule_context):
    if (aspect_type == 'builtin' and aspect == 'lineItem') or aspect_type == 'explicit_dimension':
        convert_function = convert_result_to_qname
    elif aspect_type == 'builtin' and aspect == 'period':
        convert_function = convert_result_to_model_period
    else:
        convert_function = lambda x, y: x.value
    #the member_alignments will contains members that have an alignment. This is used in the factset evaluation to align the matched fact with te member
    member_alignments = []
    member_values = set()
    
    for result in results:
        member_values.add(convert_function(result, xule_context))
        if result.alignment is not None:
            member_alignments.append((result, aspect_type, aspect, convert_function(result, xule_context)))

    return member_values, member_alignments

def update_member_table(aspect_type, aspect, member_table, member_results, xule_context):
    '''THESE CONVERT FUNCTIONS SHOULD GET THE VALUE VIA get_type_and_compute_value, SO IF THE MEMBER IS A FACT, IT LOOKS AT THE UNDERLYING VALUE.'''
    if (aspect_type == 'builtin' and aspect == 'lineItem') or aspect_type == 'explicit_dimension':
        convert_function = convert_result_to_qname
    elif aspect_type == 'builtin' and aspect == 'period':
        convert_function = convert_result_to_model_period
    else:
        convert_function = lambda x, y: get_type_and_compute_value(x, y)[1]
    
    member_values = set()
    if member_table is None:
        #first time
        interim_result_set = XuleResultSet()
        interim_result_set.aspects = ((aspect_type, aspect),)
        for member_res in member_results:
            new_res = XuleResult(None, 'unbound', meta=member_res.meta)
            #member_type, member_value = get_type_and_compute_value(member_res, xule_context)
            converted_member_value = convert_function(member_res, xule_context)
            new_res.members = (converted_member_value,)
            interim_result_set.append(new_res)
            member_values.add(converted_member_value)
    else:
        #member_results is a set. Convert it to a result set
        member_result_set = XuleResultSet(member_results)
        interim_result_set = XuleResultSet()
        #update the aspect list
        interim_result_set.aspects = member_table.aspects + ((aspect_type, aspect),)
        
        for combine in align_result_sets(member_table, member_result_set, xule_context, align_only=True, use_defaults='none', require_binding=False):
            #member_type, member_value = get_type_and_compute_value(combine['right'], xule_context)  
            interim_result = XuleResult(None, 'unbound', meta=combine['meta'])
            converted_member_value = convert_function(combine['right'], xule_context)
            interim_result.members = combine['left'].members + (converted_member_value,)
            interim_result_set.append(interim_result)
            member_values.add(converted_member_value)
    
    return member_values, interim_result_set

def evaluate_factset(factset, xule_context):
    '''THIS CODE NEEDS A LITTLE REFACTORING. BREAK IT DOWN INTO FUNCTIONS. IMPROVE REUSE OF CODE FOR HANDLING 'IN' OPERATOR'''
    '''Evaluator for a factset
    
       The factset is divided into two parts. The first part contains aspects that will be used to filter the fact and will NOT
       be used for alignment. For example: "Assets[]" or "[lineItem=Assets]". These factsets will find all the 'Assets' facts in the 
       instance, but when these facts are compared to facts in other fact sets, the 'lineItem' aspect will not be used to check alignment.
       
       Actual aspects of the fact that are not specified in the first part of the factset will be used for alignment.
       
       With alingment:
           This would be put in the context for 'with' expr. It would cause downstream factset evaluations
           to include the filter as part of getting facts. If the filter is 'closed', it would act like a closed factset and not allow
           facts that have dimenions in fact's alignment that are not in the filter. 'open' filters wouldn't care.
           
           This provides an alternative mechanism for handling alignment. Instead of getting all results for each side of an operation (i.e. property) 
           and then aligning them, it would allow the expression to iterate over one operand result set and evaluate for each result of the other operand. 
           By pushing the filter, first, only the aligned results will come back. 
    '''
    results = XuleResultSet()
    
    non_align_aspects, aspect_vars = process_factset_aspects(factset, xule_context)
    
    #check if any non_align_aspects overlap with with_filters
    with_filters, other_filters = xule_context.get_current_filters()

    #This restriction is removed to suport rules like r1923
#     if with_aspects & factset_aspects:
#         raise XuleProcessingError(_("The factset cannont contain any aspects in any bounding 'with' clause, found '%s'." % ", ".join(with_aspects & factset_aspects)), xule_context)
    
    #combine all the filtering aspects.   
    all_aspect_filters = list(with_filters.items()) + list(other_filters.items()) + list(non_align_aspects.items())
       
    '''Match facts based on the aspects in the first part of the factset and any additional filters.
       This is done by intersecting the sets of the fact_index. The fact index is a dictionary of dictionaries.
       The outer dictionary is keyed by aspect and the inner by member. So fact_index[aspect][member] contains a 
       set of facts that have that aspect and member.'''
    pre_matched_facts = None
    first = True
#     member_alignments = []
    #create an empty result set to contain the aligned members across the different aspects.
    member_table = None
        
    for aspect_info, filter_member_rs in all_aspect_filters:
        aspect_key = (aspect_info[TYPE], aspect_info[ASPECT])
        facts_by_aspect = set()
        
        '''When the aspect key is not in the fact index, then the instance doesn't use this aspect (dimension). So create an entry for the 'None' key and put all the facts in it.'''
        if aspect_key not in xule_context.fact_index:
            xule_context.fact_index[aspect_key][None] = xule_context.model.factsInInstance
        
        # get set of member XuleResults
        member_results = set()
        new_member_results = []
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
            if aspect_info[ASPECT_OPERATOR] == '=':
                #member_results = set(filter_member_rs.results)
                new_member_results = filter_member_rs.results
            else:
                #operator is "in"
                for member_set_result in filter_member_rs:
                    if member_set_result.type in ('list', 'set'):
                        #member_results |= set(member_set_result.value)
                        new_member_results += member_set_result.value
                    else:
                        raise XuleProcessingError(_("The value for '%s' with 'in' must be a set or list, found '%s'" % (aspect_key[ASPECT], member_set_result.type)), xule_context)
                      
            #convert the results to the underlying values
#             member_values, aspect_member_alignments = convert_results_to_values(member_results, aspect_info[TYPE], aspect_info[ASPECT], xule_context)
#             member_alignments += aspect_member_alignments
            
            member_values, member_table = update_member_table(aspect_info[TYPE], aspect_info[ASPECT], member_table, new_member_results, xule_context)
#             print(member_table.aspects)
#             for r in member_table:
#                 print(r.members)
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
        pre_matched_facts = xule_context.model.factsInInstance

#     '''For members that have alignment, create this dictionary by the aspect and member witht he set of alginments. This will be used when
#        iterating through the facts.'''
#     aspect_member_alignment = collections.defaultdict(lambda : collections.defaultdict(list))
#     for member_alignment in member_alignments:
#         '''(result, aspect_type, aspect, convert_function(result, xule_context)'''
#         mem_align_result = member_alignment[0]
#         mem_align_aspect_type = member_alignment[1]
#         mem_align_aspect = member_alignment[2]
#         mem_align_value = member_alignment[3]
#         #aspect_member_alignment[(mem_align_aspect_type, mem_align_aspect)][mem_align_value ] += [mem_align_result.alignment]
#         aspect_member_alignment[(mem_align_aspect_type, mem_align_aspect)][mem_align_value ] += [mem_align_result.meta]
    
    #start matching to facts
    for model_fact in pre_matched_facts:
        '''There are two steps to matching facts. The first is to match the non_aglin_aspects. Then check the where clause.'''
        #Start by assuming the fact will be a match. the filtering will determine if it should be including in the final result set
        matched = True
        
        #check if nill
        if not xule_context.include_nils and model_fact.isNil:
            continue
        
        '''The alignment is all the aspects that were not specified in the first part of the factset (non_align_aspects).'''
        #set up potential fact result
        alignment = get_alignment(model_fact, non_align_aspects, xule_context)        
        if len(alignment) == 0:
            alignment = None
        '''If we are in a with clause, the alignment needs to be adjusted. Each aspect in the with should be in the alignment even if
           if it is in the factset aspects (which would normally take that aspect out of the alignment).'''
        for with_aspect_info in with_filters:
            alignment_info = (with_aspect_info[TYPE], with_aspect_info[ASPECT])
            if alignment_info not in alignment:
                if alignment_info == ('builtin', 'lineItem'):
                    alignment_value = model_fact.elementQname
                elif alignment_info == ('builtin', 'unit'):
                    if model_fact.isNumeric:
                        unit_value = model_to_xule_unit(model_fact.unit.measures, xule_context)
                        unit_hash = hash(unit_value)
                        xule_context.hash_table[('unit', unit_hash)] = unit_value
                        alignment_value = unit_hash
                elif alignment_info == ('builtin', 'period'):
                    period_value = model_to_xule_period(model_fact.context, xule_context)
                    period_hash = hash(period_value)
                    xule_context.hash_table[('period', period_hash)] = period_value
                    alignment_value = period_hash
                elif alignment_info == ('builtin', 'entity'):
                    entity_value = model_to_xule_entity(model_fact.context, xule_context)
                    entity_hash = hash(entity_value)
                    xule_context.hash_table[('entity', entity_hash)] = entity_value
                elif alignment_info[TYPE] == 'explicit_dimension':
                    member_value = model_fact.context.qnameDims.get(alignment_info[ASPECT])
                    if member_value is not None:
                        member_hash = hash((member_value.namespaceURI, member_value.localName))
                        xule_context.hash_table[('member', member_hash)] = member_value
                        alignment_value = member_hash
                    else:
                        alignment_value = None
                else:
                    raise XuleProcessingError(_("Pushing 'with' filter alignment found unknown alignment '%s : %s'" % alignment_info), xule_context)
                
                alignment[alignment_info] = alignment_value           
        
        fact_result = XuleResult(model_fact, 'fact', alignment=alignment, facts=[model_fact])

        #check if the fact matched any filters that had members that had alignment. In this case, the alignment must match
        '''aspect_member_alignment'''
        if member_table is not None:
            matched_rows = []
            for member_row_res in member_table.results:
                member_row = member_row_res.members
                row_matches = True
                
                #check alignment
                if member_row_res.alignment is not None and member_row_res.alignment != fact_result.alignment:
                    row_matches = False
                    continue
                
                #check if aspects match what is in the member table.
                for index, aspect_info in enumerate(member_table.aspects):
                    if aspect_info == ('builtin', 'lineItem'):
                        if model_fact.elementQname != member_row[index]:
                            row_matches = False
                    elif aspect_info == ('builtin', 'period'):
                        if model_to_xule_period(model_fact.context, xule_context) != member_row[index]:
                            row_matches = False
                    elif aspect_info == ('builtin', 'unit'):
                        if model_fact.isNumeric:
                            if model_to_xule_unit(model_fact.unit.measures, xule_context) != member_row[index]:
                                row_matches = False
                    elif aspect_info == ('builtin', 'entity'):
                        if model_to_xule_entity(model_fact.context, xule_context) != member_row[index]:
                            row_matches = False
                    elif aspect_info[TYPE] == 'explicit_dimension':
                        model_fact_dim = model_fact.context.qnameDims.get(aspect_info[ASPECT])
                        if model_fact_dim is not None:
                            if model_fact_dim.memberQname != member_row[index]:
                                row_matches = False
                    else:
                        raise XuleProcessingError(_("Internal error. Unknown aspect, found ('%s', '%s')" % aspect_info), xule_context)
            
                if row_matches:
                    matched_rows.append(member_row_res)
            if len(matched_rows) == 0:
                matched = False
            else:
                #combine meta data from the matched rows
                for matched_row_res in matched_rows:
                    combined_meta = combine_result_meta(fact_result, XuleResult(None, 'unbound', meta=matched_row_res.meta), xule_context)
                    fact_result.meta = combined_meta
       
        
        '''OLD MEMBER ALIGNMENT SECTION'''
#         for aspect_key, member_alignment in aspect_member_alignment.items():
#             member_alignments = None
#             member_metas = None
#             if aspect_key[TYPE] == 'builtin':
#                 if aspect_key[ASPECT] == 'lineItem':
#                     member_metas = member_alignment.get(model_fact.elementQname)
#                     member_alignments = None if member_metas is None else [meta[XuleResult._ALIGNMENT] for meta in member_metas]
#                     #member_alignments = member_alignment.get(model_fact.elementQname)
#                 elif aspect_key[ASPECT] == 'period':
#                     member_metas = member_alignment.get(model_to_xule_period(model_fact.context, xule_context))
#                     member_alignments = None if member_metas is None else [meta[XuleResult._ALIGNMENT] for meta in member_metas]
#                     #member_alignments = member_alignment.get(model_to_xule_period(model_fact.context, xule_context))
#                 elif aspect_key[ASPECT] == 'unit':
#                     member_metas = member_alignment.get(model_to_xule_unit(model_fact.unit.measures, xule_context))
#                     member_alignments = None if member_metas is None else [meta[XuleResult._ALIGNMENT] for meta in member_metas]
#                     #member_alignments = member_alignment.get(model_to_xule_unit(model_fact.unit.measures, xule_context))
#                 elif aspect_key[ASPECT] == 'entity':
#                     member_metas = member_alignment.get(model_to_xule_entity(model_fact.context, xule_context))
#                     member_alignments = None if member_metas is None else [meta[XuleResult._ALIGNMENT] for meta in member_metas]
#                     #member_alignments = member_alignment.get(model_to_xule_entity(model_fact.context, xule_context))
#                 else:
#                     raise XuleProcessingError(_("Invalid builtin aspect '%s'" % aspect_key[ASPECT]), xule_context)
#             else:
#                 if aspect_key[ASPECT] in model_fact.context.qnameDims:
#                     member_metas = member_alignment.get(model_fact.context.qnameDims[aspect_key[ASPECT]].memberQname)
#                     member_alignments = None if member_metas is None else [meta[XuleResult._ALIGNMENT] for meta in member_metas]
#                     #member_alignments = member_alignment.get(model_fact.context.qnameDims[aspect_key[ASPECT]].memberQname)
#             if member_metas is not None and member_alignments is not None:
#                 if fact_result.alignment not in member_alignments:
#                     matched = False
#                     break
#                 else:
#                     #copy the meta data to the fact
#                     for member_meta in member_metas:
#                         if fact_result.alignment == member_meta[XuleResult._ALIGNMENT] or member_meta[XuleResult._ALIGNMENT] is None:
#                             combined_meta = combine_result_meta(fact_result, XuleResult(None, 'unbound', meta=member_meta))
#                             saved_alignment = fact_result.alignment
#                             fact_result.meta = combined_meta
#                             fact_result.alignment = saved_alignment
# 
# #             if member_alignment is not None:
# #                 if fact_result.alignment not in member_alignments:
# #                     matched = False
# #                     break
        
        '''Check closed factset'''
        '''DO I NEED TO HANDLE BUILT IN ASPECTS????? I DON'T THINK SO. 
           THERE ARE SEVERAL RULES WITH ONLY A PRIMARY AND [[]]. IF BUILT IN ASPECTS
           WHERE CHECKED, THEN NOTHING WOULD MATCH BECAUSE PERIOD IS NOT IN THE NON_ALIGN_ASPECTS BUT
           IS ON THE FACT.
        '''
        if matched and factset.factsetType == 'closed':
            aspect_dimensions = {aspect_info[ASPECT] for aspect_info in non_align_aspects}
            if set(model_fact.context.qnameDims.keys()) - aspect_dimensions:
                matched = False

        '''Filter where clause'''          
        if matched:
            if 'whereExpr' in factset:
                #push the apsect variables
                ''' aspect_var_info is a tuple: 0 = aspect type, 1 = aspect name'''
                
                aspect_vars_flat = list(aspect_vars.items())
                for var_name, aspect_var_info in aspect_vars_flat:
                    if aspect_var_info[0] == 'builtin':
                        if aspect_var_info[1] == 'lineItem':
                            xule_context.add_arg(var_name,
                                                     None,
                                                     XuleResultSet(XuleResult(model_fact.concept, 'concept')))
                        elif aspect_var_info[1] == 'period':
                            if model_fact.context.isStartEndPeriod:
                                xule_context.add_arg(var_name,
                                                     None,
                                                     XuleResultSet(XuleResult((model_fact.context.startDatetime,
                                                                               model_fact.context.endDatetime),
                                                                               'duration')))
                            elif model_fact.context.isInstantPeriod:
                                xule_context.add_arg(var_name,
                                                     None,
                                                     XuleResultSet(XuleResult(model_fact.context.instantDatetime,
                                                                              'instant')))
                            else:
                                xule_context.add_arg(var_name,
                                                     None,
                                                     XuleResultSet(XuleResult((datetime.datetime.min, datetime.datetime.max),
                                                                              'duration')))                             
                        elif aspect_var_info[1] == 'unit':
                            xule_context.add_arg(var_name,
                                                 None,
                                                 XuleResultSet(XuleResult(model_to_xule_unit(model_fact.unit.measures, xule_context), 'unit')))
                        elif aspect_var_info[1] == 'entity':
                            xule_context.add_arg(var_name,
                                                 None,
                                                 XuleResultSet(XuleResult(model_fact.context.entityIdentifier,
                                                                          'entity')))
                        else:
                            raise XuleProcessingError(_("Unknown built in aspace '%s'" % aspect_var_info[1]), xule_context)
                    elif aspect_var_info[0] == 'explicit_dimension':
                        if aspect_var_info[1] in model_fact.context.qnameDims:
                            member_qname = model_fact.context.qnameDims.get(aspect_var_info[1]).memberQname
                        else:
                            member_qname = None
                            
                        xule_context.add_arg(var_name,
                                     None, #tagged,
                                 XuleResultSet(XuleResult(member_qname, 'qname')))

                #add the $item variable for the fact
                xule_context.add_arg('item',
                                     None, #tagged
                                     XuleResultSet(fact_result))
                
#                 #push alignment as an "other" filter. This will restrict evaluation of any facgtsets used in the where clause
#                 in_where = False
#                 if  xule_context.in_where_alignment is None and fact_result.alignment is not None:
#                     xule_context.filter_add('other', alignment_to_aspect_info(fact_result.alignment, xule_context))
#                     xule_context.in_where_alignment = fact_result.alignment
#                     in_where = True
                    
                where_rs = evaluate(factset.whereExpr[0], xule_context)
                
#                 #remove "other" filter.
#                 if in_where:
#                     in_where = False
#                     xule_context.filter_del()
#                     xule_context.in_where_alignment = None
                
                #remove the variables for the blcok
                #first the $item
                xule_context.del_var('item', where_rs)
                #then the aspect_vars
                for var_name, var_aspect_info in aspect_vars_flat[::-1]:
                    xule_context.del_var(var_name, where_rs)

                '''need to align the results.'''
                where_matches = False
                for combine in align_result_sets(XuleResultSet(fact_result), where_rs, xule_context, align_only=True, use_defaults='right'):
                    if bool(combine['right'].value):
                        where_matches = True
                        #aggregate the meta
                        combine_meta = combine_result_meta(fact_result, combine['right'], xule_context)
                        saved_alignment = fact_result.alignment
                        fact_result.meta = combine_meta
                        fact_result.alignment = saved_alignment
              
                matched = where_matches
        if matched:
#             print(model_fact.elementQname.localName + " " + str(model_fact.xValue))
#             print("\n".join([str(x) for x in alignment.items()]))

            #check if the fact should be eliminated because of an alignment filter
            if fact_result.alignment not in xule_context.alignment_filters:
                results.append(fact_result)

    
    '''MAYBE THIS SHOULD ALWAYS PUT A DEFAULT UNBOUND RESULT IN?'''
    #return unbound if no facts matched    
    
    #don't need this anymore because the result set is created with a default.
    #results.default = XuleResult(None, 'unbound')
        
#     if match_count == 0:
#         results.append(XuleResult(None, 'unbound'))
#     else:
#         #default unbound result
#         results.append(XuleResult(None, 'unbound', is_default=True))

    return results

def evaluate_values(values_expr, xule_context):
    '''The values keywork effectively returns a factset that doesn't have alignment.'''
    final_result_set = XuleResultSet()
    #suspend the alignment filters
    '''SHOULD WITH FILTERS ALSO BE SUSPENDED?'''
#     saved_alginment_filters = xule_context.alignment_filters
#     xule_context.alignment_filters = []
    factset_rs = evaluate(values_expr[0], xule_context)
#     xule_context.alignment_filters = saved_alginment_filters
    
    final_result_set.default = factset_rs.default
    #Need to recheck the alignment filters because the alignment is being changed on these results.
    if None not in xule_context.alignment_filters:
        for result in factset_rs:
            final_result_set.append(result)
            result.alignment = None
    #otherwise, there shoulde be no results because the alignment filter is blocking 'None' alingments

    return final_result_set

def evaluate_severity(severity_expr, xule_context):

    severity_result = XuleResult(severity_expr.severityName, 'severity')
    
    for severity_arg in severity_expr.severityArgs:
        arg_value_rs = evaluate(severity_arg.argExpr[0], xule_context)
        if len(arg_value_rs.results) > 0:
            arg_value = arg_value_rs.results[0]
        else:
            arg_value = XuleResult(None, 'unbound')
        
        severity_result.add_tag(severity_arg.tagName, arg_value)
        
    return XuleResultSet(severity_result)

#aspect info indexes
TYPE = 0
ASPECT = 1
SPECIAL_VALUE = 2
ASPECT_OPERATOR = 3

BUILTIN_ASPECTS = ['lineItem', 'unit', 'period', 'entity']
          
EVALUATOR = {
    #rules
    "raiseDeclaration": evaluate_raise,
    "reportDeclaration": evaluate_report,
    "formulaDeclaration": evaluate_formula,
    
    #literals
    "boolean": evaluate_bool_literal,
    "integer": evaluate_int_literal,
    "float": evaluate_float_literal,
    "string": evaluate_string_literal,
    "qName": evaluate_qname_literal,
    "void": evaluate_void_literal,
    "list": evaluate_list_literal,
    "set": evaluate_set_literal,
    
    #atomic expressions
    "printExpr": evaluate_print,
    "ifExpr": evaluate_if,
    "forExpr": evaluate_for,
    "withExpr": evaluate_with,
    
    "blockExpr": evaluate_block,
    "varRef": evaluate_var_ref,
    "functionReference": evaluate_function_ref,
    "taggedExpr": evaluate_tagged,
    "propertyExpr": evaluate_property,
    
    "factset": evaluate_factset,
    'valuesExpr': evaluate_values,
    
    #expressions with order of operations
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

#built in functions
def agg_all(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    
    results_by_alignment = organize_aggregation(xule_context, *args)
    has_unaligned_result = False
    for res in results_by_alignment.values():  
        if len(res.value) > 0:
            if res.alignment is None:
                has_unaligned_result = True
            new_res = XuleResult(True, 'bool', meta=res.meta)
            for sub_res in res.value:
                sub_type, sub_value = get_type_and_compute_value(sub_res, xule_context)
                if sub_type != 'bool':
                    raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % sub_type), xule_context)
                new_res.value = new_res.value and sub_value
            final_result_set.append(new_res)

    if not has_unaligned_result:     
        if len(final_result_set.results) == 0:
            final_result_set.append(XuleResult(True, 'bool'))
        else:
            final_result_set.default = XuleResult(True, 'bool')
        
    return final_result_set
    
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             xule_type, compute_value = get_type_and_compute_value(res, xule_context)
#             
#             if xule_type == 'unbound':
#                 continue
#             
#             if xule_type != 'bool':
#                 raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % xule_type), xule_context)
#             
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
#             if key is None:
#                 has_unaligned_result = True
#             
#             if key not in results_by_alignment:
#                 results_by_alignment[key] = XuleResult(True, 'bool')
#             
#             new_meta = combine_result_meta(res, results_by_alignment[key])
#             results_by_alignment[key].meta = new_meta
#             
#             if compute_value == False:
#                 results_by_alignment[key].value = False
#                 #Could break here to perform lazy aggregation, but then would loose the rest of the tags.
# 
#     if not has_unaligned_result:     
#         if len(results_by_alignment) == 0 :
#             results_by_alignment[None] = XuleResult(True, 'bool')
#         else:
#             final_result_set.default = XuleResult(True, 'bool')
#              
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set

def agg_any(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    
    results_by_alignment = organize_aggregation(xule_context, *args)
    has_unaligned_result = False
    for res in results_by_alignment.values():
        if len(res.value) > 0:
            if res.alignment is None:
                has_unaligned_result = True
            new_res = XuleResult(False, 'bool', meta=res.meta)
            for sub_res in res.value:
                sub_type, sub_value = get_type_and_compute_value(sub_res, xule_context)
                if sub_type != 'bool':
                    raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % sub_type), xule_context)
                new_res.value = new_res.value or sub_value
            final_result_set.append(new_res)

    if not has_unaligned_result:     
        if len(final_result_set.results) == 0:
            final_result_set.append(XuleResult(False, 'bool'))
        else:
            final_result_set.default = XuleResult(False, 'bool')
        
    return final_result_set

#     
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             xule_type, compute_value = get_type_and_compute_value(res, xule_context)
#             
#             if xule_type == 'unbound':
#                 continue
#             
#             if xule_type != 'bool':
#                 raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % xule_type), xule_context)
#             
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
#             if key is None:
#                 has_unaligned_result = True
#             
#             if key not in results_by_alignment:
#                 results_by_alignment[key] = XuleResult(False, 'bool')
#             
#             new_meta= combine_result_meta(res, results_by_alignment[key])
#             results_by_alignment[key].meta = new_meta
#             
#             if compute_value == True:
#                 results_by_alignment[key].value = True
#                 #Could break here to perform lazy aggregation, but then would loose the rest of the tags.
# 
#     if not has_unaligned_result:     
#         if len(results_by_alignment) == 0 :
#             results_by_alignment[None] = XuleResult(False, 'bool')
#         else:
#             final_result_set.default = XuleResult(False, 'bool')
#                   
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set    

def agg_sum(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    results_by_alignment = organize_aggregation(xule_context, *args)

    for res in results_by_alignment.values():
        if len(res.value) > 0:
            new_res = None
            for sub_res in res.value:
                if new_res is None:
                    new_type, new_value = get_type_and_compute_value(sub_res, xule_context)
                    new_res = XuleResult(new_value, new_type, meta=res.meta)
                else:
                    combined_values = combine_xule_types(new_res, sub_res, xule_context)
                    new_res.value = combined_values[1] + combined_values[2]
                    new_res.type = combined_values[0]
            final_result_set.append(new_res)
            
    return final_result_set    
    
#     final_result_set = XuleResultSet()   
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             
#             if res.type == 'unbound':
#                 continue
#             
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
#             if key is None:
#                 has_unaligned_result = True
#                 
#             if key not in results_by_alignment:
#                 initial_type, initial_value = get_type_and_compute_value(res, xule_context)
#                 results_by_alignment[key] = XuleResult(initial_value, initial_type, meta=res.meta)
#             else:
#                 for combined in align_result_sets(XuleResultSet(results_by_alignment[key]), XuleResultSet(res), xule_context):
#                     results_by_alignment[key].value = combined['left_compute_value'] + combined['right_compute_value']
#                     results_by_alignment[key].meta = combined['meta']
#                     
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set
    
def agg_first(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    results_by_alignment = organize_aggregation(xule_context, *args)
    for res in results_by_alignment.values():
        if len(res.value) > 0:
            final_result_set.append(XuleResult(res.value[0].value, res.value[0].type, meta=res.meta))
    return final_result_set
  
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
# #             if key is None:
# #                 has_unaligned_result = True
#             
#             if key not in results_by_alignment:
#                 results_by_alignment[key] = res
#             else:
#                 new_meta = combine_result_meta(res, results_by_alignment[key])
#                 results_by_alignment[key].meta = new_meta
#                     
#     for res in results_by_alignment.values():
#         final_result_set.append(res)    
#     
#     return final_result_set    
 
def agg_count(xule_context, *args):    
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    
    has_unaligned_result = False
    results_by_alignment = organize_aggregation(xule_context, *args)
    for res in results_by_alignment.values():
        if res.alignment is None:
            has_unaligned_result = True
        final_result_set.append(XuleResult(len(res.value), 'int', meta=res.meta))

    if not has_unaligned_result:
        if len(final_result_set.results) == 0: 
            final_result_set.append(XuleResult(0, 'int'))
        else:
            final_result_set.default = XuleResult(0, 'int')
     
    return final_result_set
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             if res.type != 'unbound':
#                 #need to freeze the key to use as dictionary key
#                 key = None if res.alignment is None else frozenset(res.alignment.items())
#                 if key is None:
#                     has_unaligned_result = True
#                     
#                 if key not in results_by_alignment:
#                     results_by_alignment[key] = XuleResult(1, 'int')
#                 else:
#                     results_by_alignment[key].value += 1
#                   
#                 new_meta = combine_result_meta(res, results_by_alignment[key])
#                 results_by_alignment[key].meta = new_meta  
# 
#     if not has_unaligned_result:     
#         if len(results_by_alignment) == 0 :
#             results_by_alignment[None] = XuleResult(0, 'int')
#         else:
#             final_result_set.default = XuleResult(0, 'int')
#                   
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set

def agg_max(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    
    results_by_alignment = organize_aggregation(xule_context, *args)
    for res in results_by_alignment.values():
        if len(res.value) > 0:
            max_res = None
            for sub_res in res.value:
                if max_res is None:
                    max_res = sub_res
                else:
                    sub_type, sub_value = get_type_and_compute_value(sub_res, xule_context)
                    max_type, max_value = get_type_and_compute_value(max_res, xule_context)
                    if sub_value > max_value:
                        max_res = sub_res
        final_result_set.append(XuleResult(max_res.value, max_res.type, meta=res.meta))
    return final_result_set     
    
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:            
#             if res.type == 'unbound':
#                 continue
#             
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
#             if key is None:
#                 has_unaligned_result = True
#                 
#             if key not in results_by_alignment:
#                 results_by_alignment[key] = XuleResult(res.value, res.type, meta=res.meta)
#             else:
#                 for combined in align_result_sets(XuleResultSet(results_by_alignment[key]), XuleResultSet(res), xule_context):
#                     if combined['left_compute_value'] < combined['right_compute_value']:
#                         results_by_alignment[key].value = combined['right'].value
#                     results_by_alignment[key].meta = combined['meta']
#                     
#     for res in results_by_alignment.values():
#         final_result_set.append(res)    
#     
#     return final_result_set

def agg_min(xule_context, *args):
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    
    results_by_alignment = organize_aggregation(xule_context, *args)
    for res in results_by_alignment.values():
        if len(res.value) > 0:
            min_res = None
            for sub_res in res.value:
                if min_res is None:
                    min_res = sub_res
                else:
                    sub_type, sub_value = get_type_and_compute_value(sub_res, xule_context)
                    min_type, min_value = get_type_and_compute_value(min_res, xule_context)
                    if sub_value < min_value:
                        min_res = sub_res
        final_result_set.append(XuleResult(min_res.value, min_res.type, meta=res.meta))
    return final_result_set     
    
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:       
#             if res.type == 'unbound':
#                 continue
#             
#             #need to freeze the key to use as dictionary key
#             key = None if res.alignment is None else frozenset(res.alignment.items())
#             if key is None:
#                 has_unaligned_result = True
#                 
#             if key not in results_by_alignment:
#                 results_by_alignment[key] = XuleResult(res.value, res.type, meta=res.meta)
#             else:
#                 for combined in align_result_sets(XuleResultSet(results_by_alignment[key]), XuleResultSet(res), xule_context):
#                     if combined['right_compute_value'] < combined['left_compute_value']:
#                         results_by_alignment[key].value = combined['right'].value
#                     results_by_alignment[key].meta = combined['meta']
#                     
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set

def agg_list(xule_context, *args):    
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    results_by_alignment = organize_aggregation(xule_context, *args)
    for res in results_by_alignment.values():
        final_result_set.append(XuleResult(tuple(res.value), 'list', meta=res.meta))
    
    final_result_set.default = XuleResult(tuple(), 'list')
    
    if len(final_result_set.results) == 0:
        final_result_set.append(XuleResult(tuple(), 'list'))

    return final_result_set

def agg_set(xule_context, *args):    
    '''In aggregation the results are created for each alignment'''
    final_result_set = XuleResultSet()
    final_result_set.default = XuleResult(frozenset(), 'set')
    
    results_by_alignment = organize_aggregation(xule_context, *args)
    
    for res in results_by_alignment.values():
        final_result_set.append(XuleResult(frozenset(res.value), 'set', meta=res.meta))
        
    if len(final_result_set.results) == 0:
        final_result_set.append(XuleResult(frozenset(), 'set'))
    
    return final_result_set

    
#     final_result_set = XuleResultSet()
#     
#     results_by_alignment = dict()
#     has_unaligned_result = False
#     
#     for arg in args:
#         for res in arg:
#             if res.type != 'unbound':
#                 #need to freeze the key to use as dictionary key
#                 key = None if res.alignment is None else frozenset(res.alignment.items())
#                 if key is None:
#                     has_unaligned_result = True
#                     
#                 if key not in results_by_alignment:
#                     results_by_alignment[key] = XuleResult(frozenset(), 'set')
# 
#                 results_by_alignment[key].value |= frozenset([res])
#                   
#                 new_meta = combine_result_meta(res, results_by_alignment[key])  
#                 results_by_alignment[key].meta = new_meta
# 
#     if not has_unaligned_result:     
#         if len(results_by_alignment) == 0 :
#             results_by_alignment[None] = XuleResult(frozenset(), 'set')
#         else:
#             final_result_set.default = XuleResult(frozenset(), 'set')
#                   
#     for res in results_by_alignment.values():
#         final_result_set.append(res)
#     
#     return final_result_set

def organize_aggregation(xule_context, *args):
  
    
#     left_arg = XuleResultSet()
#     
#     #convert the first argnument to a tuple.
#     if len(args) > 0:
#         first_arg = args[0]
#         for res in first_arg.results:
#             left_arg.append(XuleResult((res,), 'list', meta=res.meta))
# 
#         #do the same for the default value
#         left_arg.default = first_arg.default
#         left_arg.default.value = (left_arg.default.value,)
#         left_arg.default.type = 'list'
#         left_arg.default.meta = first_arg.default.meta
#         
#         #combine with each of the right arguments
#         for right_arg in args[1:]:
#             new_left_arg = XuleResultSet()
#             for combined in align_result_sets(left_arg, right_arg, xule_context, align_only=True, require_binding=False):
#                 new_left_arg.append(XuleResult(combined['left'].value + (combined['right'],),
#                                                'list',
#                                                meta=combined['meta']))
#             left_arg = new_left_arg
#     
#     return left_arg
    

    results_by_alignment = dict()
    for arg in args:
        for res in arg:
            #All aggregations ignore unbound results
            if res.type == 'unbound':
                continue
            #need to freeze the key to use as dictionary key
            key = None if res.alignment is None else frozenset(res.alignment.items())
                
            if key not in results_by_alignment:
                if None in results_by_alignment:
                    #reults with alignment get all the None aligned results as a starting point.
                    results_by_alignment[key] = results_by_alignment[None].dup()
                else:
                    results_by_alignment[key] = XuleResult(tuple(), 'list')

            if key is None:
                for agg_res in results_by_alignment.values():
                    agg_res.value += tuple([res])
                    new_meta = combine_result_meta(res, agg_res, xule_context)  
                    agg_res.meta = new_meta
            else:
                results_by_alignment[key].value += tuple([res])
              
                new_meta = combine_result_meta(res, results_by_alignment[key], xule_context)  
                results_by_alignment[key].meta = new_meta

    if None in results_by_alignment and len(results_by_alignment) > 1: #it is not the only result
            del results_by_alignment[None]
  
#     if len(results_by_alignment) == 0 :
#         results_by_alignment[None] = XuleResult(tuple(), 'list')

    return results_by_alignment

def func_exists(xule_context, *args):

    final_result_set = XuleResultSet()
    
    has_unaligned_result = False
    
    for item in args[0].results:
        final_result_set.append(XuleResult(item.value is not None, 'bool', meta=item.meta))
        if item.alignment is None:
            has_unaligned_result = True
            
#     if not has_unaligned_result:
#         final_result_set.default = XuleResult(False, 'bool')
    
#     if not has_unaligned_result:     
#         if len(final_result_set.results) == 0 :
#             final_result_set.append(XuleResult(False, 'bool'))
#         else:
#             final_result_set.default = XuleResult(False, 'bool')

    final_result_set.default = XuleResult(False, 'bool', meta=args[0].default.meta)
    return final_result_set

def func_missing(xule_context, *args):
    '''IF WE WANT missing(nothing[]) TO CREATE A RESULT, WE NEED TO CREATE THE RESULT INSTEAD OF CREATING THE DEFAULT IF THERE ARE NO ARGS.
       LIKEWISE FOR EXISTS.'''
    final_result_set = XuleResultSet()
    
    has_unaligned_result = False
    
    for item in args[0].results:
        final_result_set.append(XuleResult(item.value is None, 'bool', meta=item.meta))
        if item.alignment is None:
            has_unaligned_result = True
    
#     if not has_unaligned_result:
#         #there wasn't a result where there was no alignment, need to create a default one
#         final_result_set.default = XuleResult(True, 'bool')
        
#     if not has_unaligned_result:     
#         if len(final_result_set.results) == 0 :
#             final_result_set.append(XuleResult(True, 'bool'))
#         else:
#             final_result_set.default = XuleResult(True, 'bool')        
    final_result_set.default = XuleResult(True, 'bool', meta=args[0].default.meta)
    return final_result_set  

def func_instant(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:    
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        
        if xule_type == 'instant':
            final_result_set.append(XuleResult(compute_value,
                                               'instant',
                                               meta=arg_result.meta
#                                                arg_result.alignment,
#                                                arg_result.tags,
#                                                arg_result.facts,
#                                                arg_result.vars
                                               ))            
        elif xule_type != 'string':
            raise XuleProcessingError(_("Function 'instant' requires a string argument, found '%s'" % xule_type), xule_context)
        else:
            final_result_set.append(XuleResult(iso_to_date(xule_context, compute_value), 
                                                             'instant', 
                                                             meta=arg_result.meta
#                                                              arg_result.alignment, 
#                                                              arg_result.tags,
#                                                              arg_result.facts,
#                                                              arg_result.vars
                                                             ))        
    return final_result_set

def iso_to_date(xule_context, date_string):
        try:
            '''THIS COULD USE A BETTER METHOD FOR CONVERTING THE ISO FORMATTED DATE TO A DATETIME.'''
            if len(date_string) == 10:
                return date_to_datetime(parse_date(date_string))
                #return datetime.datetime.strptime(date_string,'%Y-%m-%d')
            else:
                return parse_datetime(date_string)
                #return datetime.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S')
        except NameError:
            raise XuleProcessingError(_("'%s' could not be converted to a date." % date_string), xule_context)    

def func_duration(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for combine in align_result_sets(args[0], args[1], xule_context, align_only=True):
        left_xule_type, left_compute_value = get_type_and_compute_value(combine['left'], xule_context)
        right_xule_type, right_compute_value = get_type_and_compute_value(combine['right'], xule_context)
        
        if left_xule_type == 'string':
            start_date = iso_to_date(xule_context, left_compute_value)
        elif left_xule_type == 'instant':
            start_date = left_compute_value
        else:
            raise XuleProcessingError(_("The start date argument of the 'duration' function must be a string or an instant, found '%s'#" % left_xule_type), xule_context)
        
        if right_xule_type == 'string':
            end_date = iso_to_date(xule_context, right_compute_value)
        elif right_xule_type == 'instant':
            end_date = right_compute_value
        else:
            raise XuleProcessingError(_("The end date argument of the 'duration' function must be a string or an instant, found '%s'#" % left_xule_type), xule_context)

        final_result_set.append(XuleResult((start_date, end_date), 
                                           'duration', 
                                           meta=combine['meta']
#                                            combine['alignment'], 
#                                            combine['tags'],
#                                            combine['facts'],
#                                            combine['vars']
                                           ))
    return final_result_set

def func_forever(xule_context, *args):

    return XuleResultSet(XuleResult((datetime.datetime.min, datetime.datetime.max), 'duration'))

def func_time_period(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        if xule_type != 'string':
            raise XuleProcessingError(_("Function 'time-period' expects a string, fount '%s'." % xule_type), xule_context)
        
        try: 
            final_result_set.append(XuleResultSet(XuleResult(parse_duration(compute_value.upper()), 
                                                             'time-period', 
                                                             meta=arg_result.meta
#                                                              arg_result.alignment, 
#                                                              arg_result.tags,
#                                                              arg_result.facts,
#                                                              arg_result.vars
                                                             )))
        except:
            raise XuleProcessingError(_("Could not convert '%s' into a time-period." % compute_value), xule_context)
        
    return final_result_set

def func_unit(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        
        if xule_type != 'qname':
            raise XuleProcessingError(_("The 'unit' function requires a qname argument, found '%s'." % xule_type), xule_context)
        
        xule_unit = ((compute_value,),tuple())
        #xule_unit = (([arg_result.value]), frozenset())
        
        final_result_set.append(XuleResult(xule_unit, 'unit', meta=arg_result.meta))
        
    return final_result_set

def func_entity(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for combine in align_result_sets(args[0], args[1], xule_context, align_only=True):
        scheme_xule_type, scheme_compute_value = get_type_and_compute_value(combine['left'], xule_context)
        identifier_xule_type, identifier_compute_value = get_type_and_compute_value(combine['right'], xule_context)
        
        if scheme_xule_type != 'string' or identifier_xule_type != 'string':
            raise XuleProcessingError(_("The entity scheme and identifier must be strings."), xule_context)
        final_result_set.append(XuleResult((scheme_compute_value, identifier_compute_value), 'entity', meta=combine['meta']))
    
    return final_result_set

def func_qname(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for combine in align_result_sets(args[0], args[1], xule_context, align_only=True):
        namespace_xule_type, namespace_compute_value = get_type_and_compute_value(combine['left'], xule_context)
        local_name_xule_type, local_name_compute_value = get_type_and_compute_value(combine['right'], xule_context)
        
        if namespace_xule_type in ('string', 'uri') and local_name_xule_type == 'string':
            final_result_set.append(XuleResult(QName(None, namespace_compute_value, local_name_compute_value), 
                                    'qname',
                                    meta=combine['meta']
#                                     combine['alignment'],
#                                     combine['tags'],
#                                     combine['facts'],
#                                     combine['vars']
                                    ))
        else:
            raise XuleProcessingError(_("'qname' function requires 2 string arguments, found '%s' and '%s'" % (combine['left'].type, combine['right'].type)))
        
    return final_result_set    

def func_uri(xule_context, *args):            
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        
        
        if xule_type not in  ('string', 'uri'):
            raise XuleProcessingError(_("The 'uri' function requires a string argument, found '%s'." % xule_type), xule_context)
        final_result_set.append(XuleResult(compute_value, 'uri', meta=arg_result.meta))
        
    return final_result_set   

def func_schema_type(xule_context, *args):
    
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        
        if xule_type != 'qname':
            raise XuleProcessingError(_("Function 'schema' expects a qname argument, found '%s'" % xule_type), xule_context)

        final_result_set.append(XuleResult(compute_value, 'type', meta=arg_result.meta))
        
    return final_result_set

def func_num_to_string(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        final_result_set.append(XuleResult(format(compute_value, ","), 'string', meta=arg_result.meta))
    
    return final_result_set

def func_number(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for arg_result in args[0]:
        xule_type, compute_value = get_type_and_compute_value(arg_result, xule_context)
        if xule_type not in ('string', 'int', 'decimal', 'float'):
            raise XuleProcessingError(_("Property 'number' requires a string or numeric argument, found '%s'" % xule_type), xule_context)
        try:
            if xule_type == 'int':
                final_result_set.append(XuleResult(compute_value, 'int', meta=arg_result.meta))
            elif xule_type == 'decimal':
                final_result_set.apend(XuleResult(compute_value, 'decimal', meta=arg_result.meta))
            elif xule_type == 'float':
                final_result_set.append(XuleResult(compute_value, 'float', meta=arg_result.meta))
            elif '.' in compute_value:
                final_result_set.append(XuleResult(decimal.Decimal(compute_value), 'decimal', meta=arg_result.meta))
            elif compute_value.lower() in ('inf', '+inf', '-inf'):
                final_result_set.append(XuleResult(float(compute_value), 'float', meta=arg_result.meta))
            else:
                final_result_set.append(XuleResult(int(compute_value), 'int', meta=arg_result.meta))
        except Exception:
            raise XuleProcessingError(_("Cannot convert '%s' to a number" % compute_value), xule_context)
    
    return final_result_set            

def func_mod(xule_context, *args):
    final_result_set = XuleResultSet()
    
    for combine in align_result_sets(args[0], args[1], xule_context):
        num_xule_type, num_value = get_type_and_compute_value(combine['left'], xule_context)
        denom_xule_type, denom_value = get_type_and_compute_value(combine['right'], xule_context)
        
        if num_xule_type not in ('int', 'float', 'decimal'):
            raise XuleProcessingError(_("The numerator for the 'mod' function must be numeric, found '%s'" % num_xule_type), xule_context)
        if denom_xule_type not in ('int', 'float', 'decimal'):
            raise XuleProcessingError(_("The numerator for the 'mod' function must be numeric, found '%s'" % denom_xule_type), xule_context)
        
        final_result_set.append(XuleResult(combine['left_compute_value'] % combine['right_compute_value'],
                                       combine['type'],
                                       meta=combine['meta']))
    
    return final_result_set

    
#the position of the function information
FUNCTION_TYPE = 0
FUNCTION_EVALUATOR = 1
FUNCTION_ARG_NUM = 2

BUILTIN_FUNCTIONS = {'all': ('aggregate', agg_all, 1),
                     'any': ('aggregate', agg_any, 1),
                     'first': ('aggregate', agg_first, 1),
                     'count': ('aggregate', agg_count, 1),
                     'sum': ('aggregate', agg_sum, 1),
                     'max': ('aggregate', agg_max, 1), 
                     'min': ('aggregate', agg_min, 1),
                     'list': ('aggregate', agg_list, 1),
                     'set': ('aggregate', agg_set, 1),
                     
                     'exists': ('regular', func_exists, 1),
                     'missing': ('regular', func_missing, 1),
                     'instant': ('regular', func_instant, 1),
                     'duration': ('regular', func_duration, 2),
                     'forever': ('regular', func_forever, 0),
                     'unit': ('regular', func_unit, 1),
                     'entity': ('regular', func_entity, 2),
                     'qname': ('regular', func_qname, 2),
                     'uri': ('regular', func_uri, 1),
                     'time-period': ('regular', func_time_period, 1),
                     'schema-type': ('regular', func_schema_type, 1),
                     'num_to_string': ('regular', func_num_to_string, 1),
                     'number': ('regular', func_number, 1),
                     'mod': ('regular', func_mod, 2)
                     }

#duration tuple
DURATION_START = 0
DURATION_END = 1


#properties
def property_dimension(xule_context, left_result, *args):
    '''dimension(dimension_qname)'''
    final_result = XuleResultSet()
    model_fact = left_result.value
           
    dimension_qname_result = args[0]
    dimension_type, dimension_compute_value = get_type_and_compute_value(dimension_qname_result, xule_context)

    if dimension_type != 'qname':
        raise XuleProcessingError(_("The argument for property 'dimension' must be a qname, found '%s'." % dimension_type),xule_context)

    if dimension_compute_value in model_fact.context.qnameDims:
        final_result.append(XuleResult(model_fact.context.qnameDims[dimension_compute_value].memberQname, 'qname'))
    else:
        final_result.append(XuleResult(None, 'none'))
    
    return final_result

def property_contains(xule_context, left_result, *args):
    
    final_result = XuleResultSet()
    
    item_result = args[0]
    
    xule_type, compute_value = get_type_and_compute_value(item_result, xule_context)
    
    if xule_type == 'unbound':
        final_result.append(XuleResult(None, 'unbound', meta=item_result.meta))
    elif left_result.type in ('set', 'list'):
        final_result.append(XuleResult(compute_value in xule_group_to_system(left_result, xule_context), 'bool'))
    elif left_result.type in ('string', 'uri'):
        if xule_type in ('string', 'uri'):
            final_result.append(XuleResult(compute_value in left_result.value, 'bool'))
    else:
        raise XuleProcessingError(_("Property 'contains' cannot operator on a '%s' and '%s'" % (left_result.type, xule_type)), xule_context)
            
    return final_result
    
#relatoinship traversal properities

def property_taxonomy(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(xule_context.model, 'taxonomy'))

def property_rules_taxonomy(xule_context, left_result, *args):
    rules_dts = xule_context.get_rules_dts()
    if rules_dts is None:
        raise XuleProcessingError(_("The rule set does not contain a rule taxonomy"), xule_context)
    
    return XuleResultSet(XuleResult(rules_dts, 'taxonomy'))

def property_summation_item_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, SUMMATION_ITEM), 'set'))

def property_parent_child_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, PARENT_CHILD), 'set'))

def property_domain_member_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, DOMAIN_MEMBER), 'set'))

def property_hypercube_dimension_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, HYPERCUBE_DIMENSION), 'set'))

def property_dimension_default_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, DIMENSION_DEFAULT), 'set'))

def property_dimension_domain_networks(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(get_networks(xule_context, left_result, DIMENSION_DOMAIN), 'set'))

def property_concept_hypercube_all(xule_context, left_result, *args):
    return get_single_network(xule_context, left_result, args[0], ALL, 'hypercube-all')

def property_dimension_default(xule_context, left_result, *args):    
    return get_single_network(xule_context, left_result, args[0], DIMENSION_DEFAULT, 'dimension-default')

def property_dimension_domain(xule_context, left_result, *args):
    return get_single_network(xule_context, left_result, args[0], DIMENSION_DOMAIN, 'dimension-domain')

def property_domain_member(xule_context, left_result, *args):    
    return get_single_network(xule_context, left_result, args[0], DOMAIN_MEMBER, 'domain-member')
    
def property_hypercube_dimension(xule_context, left_result, *args):
    return get_single_network(xule_context, left_result, args[0], HYPERCUBE_DIMENSION, 'hypercube-dimension')

def property_summation_item(xule_context, left_result, *args):
    return get_single_network(xule_context, left_result, args[0], SUMMATION_ITEM, 'summation-item')

def property_role(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value[NETWORK_INFO][NETWORK_ROLE], 'uri')) 
    
def get_networks(xule_context, dts_result, arcrole, role=None, link=None, arc=None):
    #final_result_set = XuleResultSet()
    networks = set()
    dts = dts_result.value
    network_infos = get_base_set_info(xule_context, dts, arcrole, role, link, arc)
    
    for network_info in network_infos:
        '''I THINK THESE NETWORKS ARE REALLY COMBINATION OF NETWORKS, SO I AM IGNORING THEM.
           NEED TO CHECK IF THIS IS TRUE.'''
        if (network_info[NETWORK_ROLE] is not None and
            network_info[NETWORK_LINK] is not None and
            network_info[NETWORK_ARC] is not None):
            
            if network_info in dts.relationshipSets:
                net = XuleResult((network_info, dts.relationshipSets[network_info]), 'network')
            else:
                net = XuleResult((network_info, 
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

def get_single_network(xule_context, left_result, role_result, arc_role, property_name):
    
    if xule_castable(role_result, 'uri', xule_context):
        role_uri = xule_cast(role_result, 'uri', xule_context)
    else:
        raise XuleProcessingError(_("The '%s' property requires an uri argument, found '%s'" % (property_name, role_result.type)), xule_context)
    
    networks = get_networks(xule_context, left_result, arc_role, role=role_uri)
    if len(networks) == 0:
        return XuleResultSet(XuleResult(None, 'unbound'))
    else:
        return XuleResultSet(next(iter(networks)))

  
def get_base_set_info(xule_context, dts, arcrole, role=None, link=None, arc=None):
    return [x + (False,) for x in dts.baseSets if x[NETWORK_ARCROLE] == arcrole and
                                       (True if role is None else x[NETWORK_ROLE] == role) and
                                       (True if link is None else x[NETWORK_LINK] == link) and
                                       (True if arc is None else x[NETWORK_ARC] == arc)]

def property_descendant_relationships(xule_context, left_result, *args):
    relationships = set()
    
    network = left_result.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
    
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type in ('unbound', 'none'):
        return XuleResultSet(XuleResult(frozenset(), 'set'))
    else:
        raise XuleProcessingError(_("First argument of the 'descendant-relationships' property must be a qname or a concept. Found '%s'" % concept_arg.type), xule_context)

    if xule_castable(depth_arg, 'float', xule_context):
        depth = xule_cast(depth_arg, 'float', xule_context)
    else:
        raise XuleProcessingError(_("Second argument for property 'descendant-relationships' must be numeric. Found '%s'" % depth_arg.type), xule_context)

    #depth = depth_arg.value  
    
    descendant_rels = descend(network, model_concept, depth, set(), 'relationship')
    
    for descendant_rel in descendant_rels:
        relationships.add(XuleResult(descendant_rel, 'relationship'))
    
    return XuleResultSet(XuleResult(frozenset(relationships), 'set'))

def property_descendants(xule_context, left_result, *args):

    concepts = set()

    network = left_result.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
    
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type in ('unbound', 'none'):
        return XuleResultSet(XuleResult(frozenset(), 'set'))
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
        concepts.add(XuleResult(descendant, 'concept'))
        
    return XuleResultSet(XuleResult(frozenset(concepts), 'set'))    

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
    
def get_concept(dts, concept_qname):
    return dts.qnameConcepts.get(concept_qname)

def property_ancestor_relationships(xule_context, left_result, *args):
    relationships = set()

    network = left_result.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]
    
    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type in ('unbound', 'none'):
        return XuleResultSet(XuleResult(frozenset(), 'set'))
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
        relationships.add(XuleResult(ancestor_rel, 'relationship'))
        
    return XuleResultSet(XuleResult(frozenset(relationships), 'set'))

def property_ancestors(xule_context, left_result, *args):   
    concepts = set()

    network = left_result.value[NETWORK_RELATIONSHIP_SET]
    concept_arg = args[0]
    depth_arg = args[1]

    if concept_arg.type == 'qname':
        model_concept = get_concept(network.modelXbrl, concept_arg.value)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type == 'concept':
        #The concept may not have come fromt he same model, so re-get the concept by its qname
        model_concept = get_concept(network.modelXbrl, concept_arg.value.qname)
        if model_concept is None:
            return XuleResultSet(XuleResult(frozenset(), 'set'))
    elif concept_arg.type in ('unbound', 'none'):
        return XuleResultSet(XuleResult(frozenset(), 'set'))
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
        concepts.add(XuleResult(ascendant, 'concept'))
    
    return XuleResultSet(XuleResult(frozenset(concepts), 'set'))

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
        
def property_children(xule_context, left_result, *args):
    return property_descendants(xule_context, left_result, args[0], XuleResult(1, 'int'))

def property_parents(xule_context, left_result, *args):
    return property_ancestors(xule_context, left_result, args[0], XuleResult(1, 'int'))

def property_source_concepts(xule_context, left_result, *args):
    concepts = frozenset(XuleResult(x, 'concept') for x in left_result.value[1].fromModelObjects().keys())
    return XuleResultSet(XuleResult(concepts, 'set'))

def property_target_concepts(xule_context, left_result, *args):
    concepts = frozenset(XuleResult(x, 'concept') for x in left_result.value[1].toModelObjects().keys())        
    return XuleResultSet(XuleResult(concepts, 'set'))

def property_relationships(xule_context, left_result, *args):        
    relationships = set()
    
    for relationship in left_result.value[1].modelRelationships:
        relationships.add(XuleResult(relationship, 'relationship'))
    
    return XuleResultSet(XuleResult(frozenset(relationships), 'set'))

def property_source(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value.fromModelObject, 'concept'))

def property_target(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value.toModelObject, 'concept'))

def property_weight(xule_context, left_result, *args):
    if left_result.value.weight is not None:
        return XuleResultSet(XuleResult(float(left_result.value.weight), 'float'))
    else:
        return XuleResultSet(XuleResult(None, 'unbound'))

def property_order(xule_context, left_result, *args):
    if left_result.value.order is not None:
        return XuleResultSet(XuleResult(float(left_result.value.order), 'float'))
    else:
        return XuleResultSet(XuleResult(None, 'unbound'))
    
def property_preferred_label(xule_context, left_result, *args):
    if left_result.value.preferredLabel is not None:
        return XuleResultSet(XuleResult(left_result.value.preferredLabel, 'uri'))
    else:
        return XuleResultSet(XuleResult(None, 'unbound'))        

def property_concept(xule_context, left_result, *args):
    '''There are two forms of this property. The first is on a fact (with no arguments). This will return the concept of the fact.
       The second is on a taxonomy (with one argument). This will return the concept of the supplied qname argument in the taxonomy.
    '''
    if left_result.type == 'fact':
        if len(args) != 0:
            raise XuleProcessingError(_("Property 'concept' when used on a fact does not have any arguments, found %i" % len(args)), xule_context)

        return XuleResultSet(XuleResult(left_result.value.concept, 'concept'))
    
    elif left_result.type == 'taxonomy':
        if len(args) != 1:
            raise XuleProcessingError(_("Property 'concept' when used on a taxonomy requires 1 argument, found %i" % len(args)), xule_context)
        
        final_result = XuleResultSet()

        concept_qname_result = args[0]
        concept_qname_type, concept_qname_value = get_type_and_compute_value(concept_qname_result, xule_context)
        
        if concept_qname_type != 'qname':
            raise XuleProcessingError(_("The 'concept' property of a taxonomy requires a qname argument, found '%s'" % concept_qname_type), xule_context)
        
        concept_value = get_concept(left_result.value, concept_qname_value)
        
        if concept_value is not None:
            final_result.append(XuleResult(concept_value, 'concept'))
        else:
            '''SHOULD THIS BE AN EMPTY RESULT SET INSTEAD OF AN UNBOUND VALUE?'''
            final_result.append(XuleResult(None, 'unbound'))
        
        return final_result
    
def property_concepts(xule_context, left_result, *args):
    
    if left_result.type == 'taxonomy':
        concepts = set(XuleResult(x, 'concept') for x in left_result.value.qnameConcepts.values())
    elif left_result.type == 'network':
        concepts = set(XuleResult(x, 'concept') for x in (left_result.value[1].fromModelObjects().keys()) | frozenset(left_result.value[1].toModelObjects().keys()))
    else:
        raise XuleProcessingError(_("'concepts' is not a property of '%s'" % left_result.type), xule_context)

    return XuleResultSet(XuleResult(frozenset(concepts), 'set'))

def property_dts_document_locations(xule_context, left_result, *args):
    final_result_set = XuleResultSet()
    for doc_url in left_result.value.urlDocs:
        final_result_set.append(XuleResult(doc_url, 'uri'))
    return final_result_set

def property_length(xule_context, left_result, *args):
    if xule_castable(left_result, 'string', xule_context):
        return XuleResultSet(XuleResult(len(xule_cast(left_result, 'string', xule_context)), 'int'))
    else:
        raise XuleProcessingError(_("Cannot cast '%s' to 'string' for property length" % left_result.type), xule_context)

def property_substring(xule_context, left_result, *args):     
    left_value = xule_cast(left_result, 'string', xule_context)
    if xule_castable(args[0], 'int', xule_context):
        start_value = xule_cast(args[0], 'int', xule_context)
    else:
        raise XuleProcessingError(_("The first argument of property 'substring' is not castable to a 'int', found '%s'" % args[0].type), xule_context)
    
    if xule_castable(args[1], 'int', xule_context):
        end_value = xule_cast(args[1], 'int', xule_context)
    else:
        raise XuleProcessingError(_("The second argument of property 'substring' is not castable to a 'int', found '%s'" % args[1].type), xule_context)

    return XuleResultSet(XuleResult(left_value[start_value:end_value], 'string'))
    
def property_index_of(xule_context, left_result, *args):
    left_value = xule_cast(left_result, 'string', xule_context)

    arg_result = args[0]
    if xule_castable(arg_result, 'string', xule_context):
        index_string = xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
    
    return XuleResultSet(XuleResult(left_value.find(index_string), 'int'))

def property_last_index_of(xule_context, left_result, *args):
    left_value = xule_cast(left_result, 'string', xule_context)
    
    arg_result = args[0]
    if xule_castable(arg_result, 'string', xule_context):
        index_string = xule_cast(arg_result, 'string', xule_context)
    else:
        raise XuleProcessingError(_("The argument for property 'last-index-of' must be castable to a 'string', found '%s'" % arg_result.type), xule_context)
    
    return XuleResultSet(XuleResult(left_value.rfind(index_string), 'int'))

def property_lower_case(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(xule_cast(left_result, 'string', xule_context).lower(), 'string'))

def property_upper_case(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(xule_cast(left_result, 'string', xule_context).upper(), 'string'))
            
def property_size(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(len(left_result.value), 'int'))

def property_item(xule_context, left_result, *args):

    arg_result = args[0]
    arg_type, arg_value = get_type_and_compute_value(arg_result, xule_context)
    
    if arg_type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The 'item' property requires a numeric argument, found '%s'" % arg_result.type), xule_context)
    
    arg_value = int(arg_value)
    
    if arg_value >= len(left_result.value) or arg_value < 0:
        return XuleResultSet(XuleResult(None, 'unbound'))
    else:
        result = left_result.value[arg_value]
        return XuleResultSet(XuleResult(result.value, result.type))

def property_power(xule_context, left_result, *args):
    
    arg_result = args[0]
    arg_type, arg_value = get_type_and_compute_value(arg_result, xule_context)
    
    if arg_type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The 'power' property requires a numeric argument, found '%s'" % arg_result.type), xule_context)
    
    combine_types = combine_xule_types(left_result, arg_result, xule_context)
    
    return XuleResultSet(XuleResult(combine_types[1]**combine_types[2], combine_types[0]))

def property_log10(xule_context, left_result, *args):
    xule_type, compute_value = get_type_and_compute_value(left_result, xule_context)
    
    if compute_value == 0:
        return XuleResultSet((XuleResult(float('-inf'), 'float')))
    elif compute_value < 0:
        return XuleResultSet((XuleResult(float('nan'), 'float')))
    else:
        return XuleResultSet((XuleResult(math.log10(compute_value), 'float')))

def property_abs(xule_context, left_result, *args):
    
    xule_type, compute_value = get_type_and_compute_value(left_result, xule_context)
    try:
        return XuleResultSet(XuleResult(abs(compute_value), xule_type))
    except Exception as e:
        raise XuleProcessingError(_("Error calculating absolute value: %s" % str(e)), xule_context)

def property_signum(xule_context, left_result, *args):
    
    xule_type, xule_value = get_type_and_compute_value(left_result, xule_context)
    
    if xule_value == 0:
        return XuleResultSet(XuleResult(0, 'int'))
    elif xule_value < 0:
        return XuleResultSet(XuleResult(-1, 'int'))
    else:
        return XuleResultSet(XuleResult(1, 'int'))

def property_name(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value.qname, 'qname'))

def property_local_part(xule_context, left_result, *args):
    if left_result.value is not None:
        return XuleResultSet(XuleResult(left_result.value.localName, 'string'))
    else:
        return XuleResultSet(XuleResult('', 'string'))
    
def property_namespace_uri(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value.namespaceURI, 'uri'))

def property_debit(xule_context, left_result, *args):
    return XuleResultSet(XuleResult('debit', 'balance'))

def property_credit(xule_context, left_result, *args):
    return XuleResultSet(XuleResult('credit', 'balance'))

def property_balance(xule_context, left_result, *args):
    if left_result.type in ('unbound','none'):
        return XuleResultSet(XuleResult(None, 'balance'))
    else:
        return XuleResultSet(XuleResult(left_result.value.balance, 'balance'))

def property_instant(xule_context, left_result, *args):
    return XuleResultSet(XuleResult('instant', 'period-type'))

def property_duration(xule_context, left_result, *args):
    return XuleResultSet(XuleResult('duration', 'period-type'))

def property_period_type(xule_context, left_result, *args):
    if left_result.type in ('unbound', 'none'):
        return XuleResultSet(XuleResult(None, 'period-type'))
    else:
        return XuleResultSet(XuleResult(left_result.value.periodType, 'period-type'))

def property_is_numeric(xule_context, left_result, *args):
    if left_result.type == 'fact':
        return XuleResultSet(XuleResult(left_result.value.concept.isNumeric, 'bool'))
    else:
        #concept
        return XuleResultSet(XuleResult(left_result.value.isNumeric, 'bool'))

def property_is_monetary(xule_context, left_result, *args):
    if left_result.type == 'fact':
        return XuleResultSet(XuleResult(left_result.value.concept.isMonetary, 'bool'))
    else:
        #concept
        return XuleResultSet(XuleResult(left_result.value.isMonetary, 'bool'))

def property_xbrl_type(xule_context, left_result, *args):
    if left_result.type == 'fact':
        return XuleResultSet(XuleResult(left_result.value.concept.baseXbrliTypeQname, 'type'))
    else:
        return XuleResultSet(XuleResult(left_result.value.baseXbrliTypeQname, 'type'))

def property_schema_type(xule_context, left_result, *args):
    if left_result.type == 'fact':
        return XuleResultSet(XuleResult(left_result.value.concept.typeQname, 'type'))
    else:
        return XuleResultSet(XuleResult(left_result.value.typeQname, 'type'))

def property_decimals(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(float(left_result.value.decimals), 'float'))

def property_round_by_decimals(xule_context, left_result, *args):

    #check the value on the left. This is needed if the left is a fact that it is numeric
    left_type, left_value = get_type_and_compute_value(left_result, xule_context)
        
    if left_type not in ('int', 'decimal', 'float'):
        raise XuleProcessingError(_("Property 'round-by-decimals' can only be used on a number, found '%s'." % left_type), xule_context)
    
    arg_result = args[0]
    
    arg_type, arg_value = get_type_and_compute_value(arg_result, xule_context)
    if arg_type not in ('int', 'decimal', 'float'):
        raise XuleProcessingError(_("Property 'round-by-decimals' requires a numeric argument, found '%s'" % arg_type), xule_context)

    if arg_value == float('inf'):
        return XuleResultSet(XuleResult(left_value, left_type))
    else:
        #convert to int
        decimals = int(arg_value)
        rounded_value = round(left_value, decimals)
        return XuleResultSet(XuleResult(rounded_value, left_type))

def property_unit(xule_context, left_result, *args):
    if left_result.value.unit is None:
        return XuleResultSet(XuleResult(None, 'unbound'))
    else:
        return XuleResultSet(XuleResult(model_to_xule_unit(left_result.value.unit.measures, xule_context), 'unit'))

def property_entity(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(model_to_xule_entity(left_result.value.context, xule_context), 'entity'))

def property_identifier(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value[1], 'string'))

def property_scheme(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.value[0], 'string'))

def property_period(xule_context, left_result, *args):
    if left_result.value.context.isStartEndPeriod or left_result.value.context.isForeverPeriod:
        return XuleResultSet(XuleResult(model_to_xule_period(left_result.value.context, xule_context), 'duration', from_model=True))
    else:
        return XuleResultSet(XuleResult(model_to_xule_period(left_result.value.context, xule_context), 'instant', from_model=True))

def property_start_date(xule_context, left_result, *args):
    if left_result.type == 'instant':
        date_value = left_result.value
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        date_value = left_result.value[0]
        
    return XuleResultSet(XuleResult(date_to_datetime(date_value), 'instant'))

def property_end_date(xule_context, left_result, *args):
    if left_result.type == 'instant':
        date_value = left_result.value
    else:
        '''WHAT SHOULD BE RETURNED FOR FOREVER. CURRENTLY THIS WILL RETURN THE LARGEST DATE THAT PYTHON CAN HOLD.'''
        date_value = left_result.value[1]  
    
    return XuleResultSet(XuleResult(date_to_datetime(date_value), 'instant'))

def property_days(xule_context, left_result, *args):
    if left_result.type == 'instant':
        return XuleResultSet(XuleResult(0, 'int'))
    else:
        return XuleResultSet(XuleResult((left_result.value[1] - left_result.value[0]).days, 'init'))

def property_add_time_period(xule_context, left_result, *args):
    arg_result = args[0]
    if arg_result.type != 'time-period':
        raise XuleProcessingError(_("Property 'add-time-period' requires a time-period argument, found '%s'" % arg_result.type), xule_context)
    
    return XuleResultSet(XuleResult(left_result.value + arg_result.value, 'instant', meta=arg_result.meta))

def property_to_list(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(tuple(left_result.value), 'list'))

def property_to_set(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(set(left_result.value), 'set'))

def property_iter(xule_context, left_result, *args):
    final_result_set = XuleResultSet()
    for result in left_result.value:
        final_result_set.append(result)
    return final_result_set

def property_type(xule_context, left_result, *args):
    return XuleResultSet(XuleResult(left_result.type, 'string'))

def property_string(xule_context, left_result, *args):
    '''SHOULD THE META DATA BE INCLUDED???? THIS SHOULD BE HANDLED BY THE PROPERTY EVALUATOR.'''
    return XuleResultSet(XuleResult(str(left_result.value), 'string', meta=left_result.meta))

def property_facts(xule_context, left_result, *args):
    return XuleResultSet(XuleResult("\n".join([str(f.qname) + " " + str(f.xValue) for f in left_result.facts]), 'string'))

def property_from_model(xule_contet, left_result, *args):
    return XuleResultSet(XuleResult(left_result.from_model, 'bool'))

#Property tuple
PROP_FUNCTION = 0
PROP_ARG_NUM = 1
PROP_OPERAND_TYPES = 2
PROP_UNBOUND_ALLOWED = 3

PROPERTIES = {'dimension': (property_dimension, 1, ('fact'), False),
              'contains': (property_contains, 1, ('set', 'list', 'string', 'uri'), False),
              # taxonomy navigations
              'taxonomy': (property_taxonomy, 0, ('unbound'), True),
              'rules-taxonomy': (property_rules_taxonomy, 0, ('unbound'), True),
              'concepts': (property_concepts, 0, ('taxonomy', 'network'), False),
              'summation-item-networks': (property_summation_item_networks, 0, ('taxonomy'), False),
              'parent-child-networks': (property_parent_child_networks, 0, ('taxonomy'), False),
              'domain-member-networks': (property_domain_member_networks, 0, ('taxonomy'), False),
              'hypercube-dimension-networks': (property_hypercube_dimension_networks, 0, ('taxonomy'), False),
              'dimension-default-networks': (property_dimension_default_networks, 0, ('taxonomy'), False),
              'dimension-domain-networks': (property_dimension_domain_networks, 0, ('taxonomy'), False),
              
              'concept-hypercube-all': (property_concept_hypercube_all, 1, ('taxonomy'), False),
              'dimension-default': (property_dimension_default, 1, ('taxonomy'), False),
              'dimension-domain': (property_dimension_domain, 1, ('taxonomy'), False),
              'domain-member': (property_domain_member, 1, ('taxonomy'), False),
              'hypercube-dimension': (property_hypercube_dimension, 1, ('taxonomy'), False),
              'summation-item': (property_summation_item, 1, ('taxonomy'), False),
              
              'source-concepts': (property_source_concepts, 0, ('network'), False),
              'target-concepts': (property_target_concepts, 0, ('network'), False),
              'descendants': (property_descendants, 2, ('network'), False),
              'children': (property_children, 1, ('network'), False),
              'ancestors': (property_ancestors, 2, ('network'), False),
              'parents': (property_parents, 1, ('network'), False),
              
              'relationships': (property_relationships, 0, ('network'), False),
              'descendant-relationships': (property_descendant_relationships, 2, ('network'), False),
              'ancestor-relationships': (property_ancestor_relationships, 2, ('network'), False),
              
              'source': (property_source, 0, ('relationship'), False),
              'target': (property_target, 0, ('relationship'), False),
              'weight': (property_weight, 0, ('relationship'), False),
              'order': (property_order, 0, ('relationship'), False),
              'preferred-label': (property_preferred_label, 0, ('relationship'), False),
              
              'concept': (property_concept, None, ('fact', 'taxonomy'), False),
              'balance': (property_balance, 0, ('concept', 'unbound', 'none'), True),
              'debit': (property_debit, 0, ('balance'), False),
              'credit': (property_credit, 0, ('balance'), False),
              'period-type': (property_period_type, 0, ('concept', 'unbound', 'none'), True),
              'duration': (property_duration, 0, ('period-type'), False),
              'instant': (property_instant, 0, ('period-type'), False),
              'is-numeric': (property_is_numeric, 0, ('concept', 'fact'), False),
              'is-monetary': (property_is_monetary, 0, ('concept', 'fact'), False),
              'xbrl-type': (property_xbrl_type, 0, ('concept', 'fact'), False),
              'schema-type': (property_schema_type, 0, ('concept', 'fact'), False),

              
              'decimals': (property_decimals, 0, ('fact'), False),
              'round-by-decimals': (property_round_by_decimals, 1, ('fact', 'int', 'decimal', 'float'), False),
              'unit': (property_unit, 0, ('fact'), False),
              'entity': (property_entity, 0, ('fact'), False),
              'identifier': (property_identifier, 0, ('entity'), False),
              'scheme': (property_scheme, 0, ('entity'), False),
              'period': (property_period, 0, ('fact'), False),
              'start-date': (property_start_date, 0, ('instant', 'duration'), False),
              'end-date': (property_end_date, 0, ('instant', 'duration'), False),
              'days': (property_days, 0, ('instant', 'duration'), False),
              'add-time-period': (property_add_time_period, 1, ('instant'), False),

              'dts-document-locations': (property_dts_document_locations, 0, ('taxonomy'), False),
              
              'length': (property_length, 0, ('string', 'uri'), False),
              'substring': (property_substring, 2, ('string', 'uri'), False),
              'index-of': (property_index_of, 1, ('string', 'uri'), False),
              'last-index-of': (property_last_index_of, 1, ('string', 'uri'), False),
              'lower-case': (property_lower_case, 0, ('string', 'uri'), False),
              'upper-case': (property_upper_case, 0, ('string', 'uri'), False),
              'size': (property_size, 0, ('list', 'set'), False),
              'item': (property_item, 1, ('list'), False),
              
              'power': (property_power, 1, ('int', 'float', 'decimal'), False),
              'log10': (property_log10, 0, ('int', 'float', 'decimal'), False),
              'abs': (property_abs, 0, ('int', 'float', 'decimal', 'fact'), False),
              'signum': (property_signum, 0, ('int', 'float', 'decimal', 'fact'), False),
              
              'role': (property_role, 0, ('network'), False),
              'name': (property_name, 0, ('concept'), False),
              'local-part': (property_local_part, 0, ('qname'), False),
              'namespace-uri': (property_namespace_uri, 0, ('qname'), False),
              
              'to-list': (property_to_list, 0, ('list', 'set'), False),
              'to-set': (property_to_set, 0, ('list', 'set'), False),
              'iter': (property_iter, 0, ('list', 'set'), False),
              'for-each': (property_iter, 0, ('list', 'set'), False),
              
              'type': (property_type, 0, (), False),
              'string': (property_string, 0, (), False),
              'facts': (property_facts, 0, (), False),
              'from-model': (property_from_model, 0, (), False),
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

#evaluate helper funtions    

XBRL_PURE = QName(None, 'http://www.xbrl.org/2003/instance', 'pure')

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
            #dyanmic seveirty
            xule_context.severity_type = xule_context.SEVERITY_TYPE_DYNAMIC        
    
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
            arg_value = evaluate(reference.functionArgs[i][0], xule_context)
            matched.append({"name": arg_name, "value": arg_value, "tagged": declaration.functionArgs[i].tagged})
    
    return matched    

def date_to_datetime(date_value):
    if isinstance(date_value, datetime.datetime):
        return date_value
    else:
        return datetime.datetime.combine(date_value, datetime.datetime.min.time())

def unit_multiply(left_unit, right_unit):
    
    left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
    left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
                  
    right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
    right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
    
    #new nuemrator and denominator before (pre) canceling
    new_num_pre = tuple(sorted(left_num + right_num))
    new_denom_pre = tuple(sorted(left_denom + right_denom))
    
    new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
    
    if len(new_num) == 0:
        new_num = (XBRL_PURE,)   
    
    return (new_num, new_denom)

def unit_cancel(left, right):
    #need mutable structure
    left_list = list(left)
    right_list = list(right)
    
    for l in range(len(left_list)):
        for r in range(len(right_list)):
            if left_list[l] == right_list[r]:
                left_list[l] = None
                right_list[r] = None
    
    return tuple(x for x in left_list if x is not None), tuple(x for x in right_list if x is not None)
    
def unit_divide(left_unit, right_unit):
    
    left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
    left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
                  
    right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
    right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
    
    #new nuemrator and denominator before (pre) canceling
    new_num_pre = tuple(sorted(left_num + right_denom))
    new_denom_pre = tuple(sorted(left_denom + right_num))
    
    new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
    
    if len(new_num) == 0:
        new_num = (XBRL_PURE,)   
    
    return (new_num, new_denom)

'''THESE match_... FUNCTIONS ARE NO LONGER USED. THEY WERE USED FOR ASPECT MATCHING BEFORE THE FACT INDEX WAS CREATED.'''    
def match_dimension(model_fact, aspect_info, member_result, xule_context):
    filter_dimension_qname = aspect_info[ASPECT]
    if filter_dimension_qname in model_fact.context.qnameDims:
        #Check for * or **, this is where aspect_info[SPECIAL_VALUE] = 'all' or 'allWithDefault'
        if aspect_info[SPECIAL_VALUE]:
            return True
        elif member_result.type in ('unbound', 'none'):
            return False
        else:
            '''THIS WILL NOT WORK FOR TYPED DIMENSIONS, WELL ATLEAST IT WON'T BE A QNAME.'''
            filter_member_qname = member_result.value
            if filter_member_qname != model_fact.context.qnameDims[filter_dimension_qname].memberQname:
                return False
    else:
        if aspect_info[SPECIAL_VALUE]:
            if aspect_info[SPECIAL_VALUE] == 'all':
                return False
            #otherwise the apsect_info[ALL] == 'allWithDefault', which is ok so do nothing
        elif member_result.type in ('unbound', 'none'):
            return True
        else:
            #The fact does not have this dimensions, so it cannot match the fitler.
            return False
    return True


def match_entity(model_fact, aspect_info, entity_result, xule_context):
    if aspect_info[SPECIAL_VALUE]:
        return True
    elif entity_result.type in ('unbound', 'none'):
        return False    
    elif entity_result.type == 'entity':
        if model_fact.context.entityIdentifier != entity_result.value:
            return False
    else:
        raise XuleProcessingError(_("The value of the entity aspect must be an entity, found '%s'." % entity_result.type), xule_context)
    return True

def match_unit(model_fact, aspect_info, unit_result, xule_context):
    if aspect_info[SPECIAL_VALUE] == 'all':
        if not model_fact.isNumeric:
            return False
    elif unit_result.type in ('none', 'unbound'):
        if model_fact.isNumeric:
            #all numeric facts have a unit, so they do not match when the unit=none.
            return False
    elif unit_result.type == 'unit':
        if model_fact.isNumeric:
            if model_to_xule_unit(model_fact.unit.measures, xule_context) != unit_result.value:
                return False
        else:
            #there is no unit on the fact (non numeric)
            return False
    else:
        raise XuleProcessingError(_("The value of the unit aspect must be a unit, found '%s'." % unit_result.type), xule_context)
    return True

def match_line_item(model_fact, aspect_info, line_item_result, xule_context):
    if aspect_info[SPECIAL_VALUE]:
        return True
    elif line_item_result.type in ('unbound', 'none'):
        return False
    elif line_item_result.type == 'qname':
        if model_fact.elementQname != line_item_result.value:
            return False
    elif line_item_result.type == 'concept':
        if model_fact.elementQname != line_item_result.value.qname:
            return False
    else:
        raise XuleProcessingError(_("The value of the line item aspect must be a qname, found '%s'" % line_item_result.type), xule_context)
    
    return True

def match_period(model_fact, aspect_info, period_result, xule_context): 
    if aspect_info[SPECIAL_VALUE]:
        return True
    elif period_result.type in ('unbound', 'none'):
        return False
    elif period_result.type == 'instant':
        if not model_fact.context.isInstantPeriod:
            return False
        if period_result.value != model_fact.context.endDatetime - datetime.timedelta(days=0 if period_result.from_model else 1): # - datetime.timedelta(days=1):
            return False
    elif period_result.type == 'duration':
        if model_fact.context.isStartEndPeriod:
            if (period_result.value[DURATION_START] != model_fact.context.startDatetime or 
                period_result.value[DURATION_END] != model_fact.context.endDatetime) - datetime.timedelta(days=0 if period_result.from_model else 1): # - datetime.timedelta(days=1)):
                return False
        elif model_fact.context.isForeverPeriod:
            if (period_result.value[DURATION_START] != datetime.datetime.min or 
                period_result.value[DURATION_END] != datetime.datetime.max):
                return False
        else:
            return False
    else:
        raise XuleProcessingError(_("The value of the period aspect must be either an instant or duration, found '%s'." % period_result.type), xule_context)
    return True

def add_aspect_var(aspect_vars, aspect_type, aspect_name, var_name, xule_context):
    if var_name:
        if var_name in aspect_vars:
            raise XuleProcessingError(_("Found multiple aspects with same variable name '%s' in a factset." % (var_name)), xule_context) 
        else:
            aspect_vars[var_name] = (aspect_type, aspect_name)
           
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
        aspect_filter_qname = evaluate(aspect_filter.aspectName.qName, xule_context).results[0].value
        #verify that lineItem is not used in both forms of the notation, i.e. Assets[lineItem=Liabilities].
        aspect_var_name = aspect_filter.get('aspectVar')
        if aspect_filter_qname.prefix is None and aspect_filter_qname.localName in BUILTIN_ASPECTS:
            #the aspect is builtin
            if aspect_filter_qname.localName == 'lineItem' and alternate_notation:
                XuleProcessingError(_("The factset specifies the lineItem both outside and inside the square brackets.", xule_context))
                
            if aspect_filter.get('all'):
                aspect_info = ('builtin', aspect_filter_qname.localName, aspect_filter.all, aspect_filter.aspectOperator)
                non_align_aspects[aspect_info] = XuleResultSet(XuleResult(None, 'none'))
                add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, xule_context)    
            elif aspect_filter.get('void'):
                non_align_aspects[('builtin', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleResultSet(XuleResult(None, 'none'))
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)                            
            else:
                aspect_info = ('builtin', aspect_filter_qname.localName, None, aspect_filter.aspectOperator)
                non_align_aspects[aspect_info] = evaluate(aspect_filter.aspectExpr[0], xule_context)
                add_aspect_var(aspect_vars, 'builtin', aspect_filter_qname.localName, aspect_var_name, xule_context)
        else:
            #This is a dimensional aspect.
            if aspect_filter.get('all'):
                non_align_aspects[('explicit_dimension', aspect_filter_qname, aspect_filter.all, aspect_filter.aspectOperator)] = XuleResultSet(XuleResult(None, 'none'))
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)
            elif aspect_filter.get('void'):
                non_align_aspects[('explicit_dimension', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleResultSet(XuleResult(None, 'none'))
                add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)                
            else:
                if not(aspect_filter.get('aspectExpr')):
                    #There is no member. In this case the aspect may have varname, but it dones not participate in the non_align.
                    add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)
                else:
                    member_rs = evaluate(aspect_filter.aspectExpr[0], xule_context)
                    #Check that only one result came back.
#                     if len(member_rs.results) > 1:                        
#                         raise XuleProcessingError(_("The member of an aspect must be a single item, for '%s' found %i members" % (aspect_filter_qname, len(member_rs.results))), xule_context)
#                     elif len(member_rs.results) == 0:
#                         non_align_aspects[('explicit_dimension', aspect_filter_qname, 'none', aspect_filter.aspectOperator)] = XuleResultSet(XuleResult(None, 'none'))
#                         add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)
#                     else:
                    '''TYPED ASPECT HANDLING OF THE ASPECT GOES IN HERE'''
                    non_align_aspects[('explicit_dimension', aspect_filter_qname, None, aspect_filter.aspectOperator)] = member_rs
                    add_aspect_var(aspect_vars, 'explicit_dimension', aspect_filter_qname, aspect_var_name, xule_context)
    
    return (non_align_aspects,
            aspect_vars) #,
            #line_item_info)   

def alignment_to_aspect_info(alignment, xule_context):
    aspect_dict = {}
    for align_key, align_value in alignment.items():
        aspect_info = (align_key[0], align_key[1], None, '=')

        if align_key[0] == 'builtin':
            if align_key[1] == 'lineItem':
                aspect_value = XuleResultSet(XuleResult(align_value, 'qname'))
            elif align_key[1] == 'unit':
                unit_hash = align_value
                unit_value = xule_context.hash_table[('unit', unit_hash)]
                aspect_value = XuleResultSet(XuleResult(unit_value, 'unit'))
                
            elif align_key[1] == 'period':           
                period_hash = align_value
                period_value = xule_context.hash_table[('period', period_hash)]
                if isinstance(period_value, tuple):
                    if period_value[1] == datetime.datetime.max:
                        #this is forever
                        aspect_value = XuleResultSet(XuleResult(period_value, 'duration'))
                    else:
                        #need to adjust the end date
#                         aspect_value = XuleResultSet(XuleResult((period_value[0],
#                                                                  period_value[1] - datetime.timedelta(days=1))
#                                                                 ,'duration'))
                        aspect_value = XuleResultSet(XuleResult((period_value[0],
                                                                 period_value[1])
                                                                ,'duration'))
                else:
                    #need to adjust the date. This is from the model which handles midnight (end of day) as beginning of next day.
#                     aspect_value = XuleResultSet(XuleResult(period_value - datetime.timedelta(days=1), 'instant'))
                    aspect_value = XuleResultSet(XuleResult(period_value, 'instant'))
                    
            elif align_key[1] == 'entity':
                entity_hash = align_value
                entity_value = xule_context.hash_table['entity', entity_hash]
                aspect_value = XuleResultSet(XuleResult(entity_value, 'entity'))
                
            else:
                raise XuleProcessingError(_("Unknown built in aspect '%s'" % align_key[1]), xule_context)
        elif align_key[0] == 'explicit_dimension':
            member_hash = align_value
            member_value = xule_context.hash_table['member', member_hash]
            aspect_value = XuleResultSet(XuleResult(member_value, 'qname'))
            
        else:
            raise XuleProcessingError(_("Unknown aspect type '%s'" % align_key[0]), xule_context)
            
        aspect_dict[aspect_info] = aspect_value
    
    return aspect_dict

def model_to_xule_unit(model_unit_measures, xule_context):
    numerator = tuple(sorted(model_unit_measures[0]))
    denominator = tuple(sorted(model_unit_measures[1]))
    
    model_unit = (numerator, denominator)
    
    #this is done to force the unit to be normalized. This will convert something like USD/pure to just USD.
    normalized_unit = unit_multiply(model_unit, ((XBRL_PURE,),()))
    
    return normalized_unit

def model_to_xule_model_datetime(model_date_time, xule_context):
    '''This is used for datetimes that are stored as values of facts. These use arelle.ModelValue.DateTime type.'''
    return iso_to_date(xule_context, str(model_date_time))

def model_to_xule_model_g_year(model_g_year, xule_context):
    return model_g_year.year

def model_to_xule_model_g_month_day(model_g_month_day, xule_context):
    return "--%s-%s" % (str(model_g_month_day.month).zfill(2),str(model_g_month_day.day).zfill(2))

def model_to_xule_model_g_year_month(model_g_year_month, xule_context):
    return str(model_g_year_month)

def model_to_xule_period(model_context, xule_context):
    if model_context.isStartEndPeriod:
        return (model_context.startDatetime, model_context.endDatetime)# - datetime.timedelta(days=1))
    elif model_context.isInstantPeriod:
        return model_context.endDatetime # - datetime.timedelta(days=1)
    elif model_context.isForeverPeriod:
        return (datetime.datetime.min(), datetime.datetime.max)
    else:
        raise XuleProcessingError(_("Period is not duration, instant or forever"), xule_context)

def model_to_xule_entity(model_context, xule_context):
    return (model_context.entityIdentifier[0], model_context.entityIdentifier[1])

def push_single_value_variables(result_vars, xule_context):
    #single_vars = list(result_vars.items())
    single_vars = []
    for var_index, var_result_indexes in result_vars.items():
        var_info = xule_context.var_by_index(var_index)
        #check that there isn't already a single value pushed.
        if var_info.get('has_single_value_var') != True:
            if 'value' in var_info:
                var_info['has_single_value_var'] = True
                var_result_set = XuleResultSet()
                #build the variable result set
                for var_result_index in var_result_indexes:
                    var_result_set.append(var_info['value'].results[var_result_index].dup())
                
                xule_context.add_arg(var_info['name'],
                                     var_info['tag'],
                                     var_result_set) 
                single_vars.append((var_index, var_result_indexes))
            
    return single_vars

def pop_single_value_variables(single_vars, result_set, xule_context):
    #process the single_vars in reverse order
    orig_var_indexes = []
    for var_index, var_result_indexes in single_vars[::-1]:
        if isinstance(var_index, int):
            orig_var_indexes.append(var_index)
        var_info = xule_context.var_by_index(var_index)
        #remove the indicator that the variable has a single value pushed on the variable stack.
        del var_info['has_single_value_var']
        var_info = xule_context.del_var(var_info['name'], result_set) 
         
    '''Need to "reset" variables that depended on this single value variable. "resetting" is done by marking it as not calculated.'''
    for res in result_set:
        for var_index, var_result_indexes in res.vars.items():
            #verify this is a var and that it is not one of the original vars.
            if isinstance(var_index, int) and var_index not in orig_var_indexes:
                var_info = xule_context._vars[var_index]
                #verify that it has been calculated
                if var_info['calculated'] and var_info['type'] == xule_context._VAR_TYPE_VAR:
                    for var_result_index in var_result_indexes:
                        var_result = var_info['value'].results[var_result_index]
                        for sub_var_index in var_result.vars:
                            if sub_var_index in orig_var_indexes:
                                #reset the variable in var_info
                                if var_info['calculated']:
                                    var_info['calculated'] = False
                                    del var_info['value']
     
TYPE_XULE_TO_SYSTEM = {'int': int,
                       'float': float,
                       'string': str,
                       'qname': QName,
                       'bool': bool,
                       'list': list,
                       'set': set,
                       'network': ModelRelationshipSet,
                       'decimal': decimal.Decimal,
                       'unbound': None,
                       'none': None,
                       'fact': ModelFact}

#period and unit are tuples

TYPE_SYSTEM_TO_XULE = {int: 'int',
                       float: 'float',
                       str: 'string',
                       QName: 'qname',
                       bool: 'bool',
                       list: 'list',
                       set: 'set',
                       ModelRelationshipSet: 'network',
                       decimal.Decimal: 'decimal',
                       type(None): 'unbound',
                       ModelFact: 'fact',
                       datetime.datetime: 'instant',
                       datetime.date: 'instant',
                       DateTime: 'model_date_time',
                       gYear: 'model_g_year',
                       gMonthDay: 'model_g_month_day',
                       gYearMonth: 'model_g_year_month'}

TYPE_STANDARD_CONVERSION = {'model_date_time': (model_to_xule_model_datetime, 'instant'),
                            'model_g_year': (model_to_xule_model_g_year, 'int'),
                            'model_g_month_day': (model_to_xule_model_g_month_day, 'string'),
                            'model_g_year_month': (model_to_xule_model_g_year_month, 'string')}

# TYPE_MAP = {frozenset([int, float]): ('float', float, float),
#             frozenset([int, decimal.Decimal]): ('decimal', decimal.Decimal, decimal.Decimal),
#             frozenset([float, decimal.Decimal]): ('decimal', decimal.Decimal, decimal.Decimal)
#             }
'''The TYPE_MAP shows converstions between xule types. The first entry is the common conversion when comparing
   2 values, the second entry (if present) is a reverse conversion.'''
TYPE_MAP = {frozenset(['int', 'float']): [('float', float), ('init', int)],
            frozenset(['int', 'decimal']): [('decimal', decimal.Decimal), ('int', int)],
            frozenset(['float', 'decimal']): [('decimal', decimal.Decimal), ('float', float)],
            frozenset(['balance', 'none']): [('balance', lambda x: x)], #this lambda does not convert the compute value
            frozenset(['balance', 'unbound']): [('balance', lambda x: x)],
            frozenset(['int', 'string']): [('string', str), ('int', int)],
            frozenset(['uri', 'string']): [('string', lambda x: x), ('uri', lambda x: x)],
            }

def combine_xule_types(left, right, xule_context):
    #left and right are XuleResults
    if isinstance(left.value, ModelFact):
#         left_type = TYPE_SYSTEM_TO_XULE[type(left.value.xValue)]
#         left_value = left.value.xValue       
        left_type, left_value = get_type_and_compute_value(left, xule_context)
    else:
        left_type = left.type
        left_value = left.value
        
    if isinstance(right.value, ModelFact):
#         right_type = TYPE_SYSTEM_TO_XULE[type(right.value.xValue)]
#         right_value = right.value.xValue
        
        right_type, right_value = get_type_and_compute_value(right, xule_context)
    else:
        right_type = right.type
        right_value = right.value
    
    if left_type == right_type:
        if left_type in ('instant', 'duration'):
            left_value, right_value = combine_period_values(left, right, xule_context)
        
        return (left_type, left_value, right_value)
    else:
        type_map = TYPE_MAP.get(frozenset([left_type, right_type]))
        
        if type_map is not None:
            type_map = type_map[0]
        
            if type_map[0] != left_type:
                left_compute_value = type_map[1](str(left_value))
            else:
                left_compute_value = left_value
            
            if type_map[0] != right_type:
                right_compute_value = type_map[1](str(right_value))
            else:
                right_compute_value = right_value
            
            return (type_map[0], left_compute_value, right_compute_value)
        else:
            #raise XuleProcessingError(_("Incompatable types: '%s' and '%s'" % (left_type, right_type)), xule_context)
            
            #this was 'unknown'.
            if left_type in ('unbound', 'none'):
                return (right_type, left_value, right_value)
            elif right_type in ('unbound', 'none'):
                return (left_type, left_value, right_value)
            else:
                return ('unbound', left_value, right_value)

def combine_period_values(left_result, right_result, xule_context):
    left_type, left_value = get_type_and_compute_value(left_result, xule_context)
    right_type, right_value = get_type_and_compute_value(right_result, xule_context)
    
    if left_type != right_type or left_type not in ('instant', 'duration') or right_type not in ('instant', 'duration'):
        raise XuleProcessingError(_("Internal error, combine_period_values did not get matching or appropiate date types. Recieved '%s' and '%s'" % (left_result.type, right_result.type)), xule_context)
    
    if left_result.from_model == right_result.from_model:
        return (left_result.value, right_result.value)
    else:
        if left_type == 'instant':
            if not left_result.from_model:
                return (left_value + datetime.timedelta(days=1),
                        right_value)
            else:
                return(left_value,
                       right_value + datetime.timedelta(days=1))
        else:
            #duration
            if not left_result.type.from_model:
                return ((left_value[0], left_value[1] + datetime.timedelta(days=1)),
                        right_value)
            else:
                return (left_value,
                        (right_value[0], right_value[1] + datetime.timedelta(days=1)))

def get_type_and_compute_value(result, xule_context):
    if result.type == 'fact':
        if type(result.value.xValue) in TYPE_SYSTEM_TO_XULE:
            xule_type, compute_value = TYPE_SYSTEM_TO_XULE[type(result.value.xValue)], result.value.xValue
            
            if xule_type in TYPE_STANDARD_CONVERSION:
                conversion_function = TYPE_STANDARD_CONVERSION[xule_type][0]
                xule_type = TYPE_STANDARD_CONVERSION[xule_type][1]
                compute_value = conversion_function(compute_value, xule_context)
        
            return xule_type, compute_value
        else:
            raise XuleProcessingError(_("Do not have map to convert system type '%s' to xule type." % type(result.value.xValue).__name__), xule_context)
    else:
        return result.type, result.value


def xule_castable(from_result, to_type, xule_context):
    from_type, from_value = get_type_and_compute_value(from_result, xule_context)
    
    if from_type == to_type:
        return True
    
    type_map = TYPE_MAP.get((frozenset([from_type, to_type])))
    if type_map is None:
        return False
    else:
        if type_map[0][0] == to_type:
            return True
        else:
            if len(type_map) > 1:
                if type_map[1][0] == to_type:
                    return True
                else:
                    return False
            else:
                return False

def xule_cast(from_result, to_type, xule_context):
    from_type, from_value = get_type_and_compute_value(from_result, xule_context)
    
    if from_type == to_type:
        return from_value
    
    type_map = TYPE_MAP.get((frozenset([from_type, to_type])))
    if type_map is None:
        raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_type, to_type)), xule_context)
    else:
        if type_map[0][0] == to_type:
            return type_map[0][1](from_value)
        else:
            if len(type_map) > 1:
                if type_map[1][0] == to_type:
                    return type_map[1][1](from_value)
                else:
                    raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_type, to_type)), xule_context)
            else:
                raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_type, to_type)), xule_context)

'''IMPLEMENT BIND'''        
def align_result_sets(left, right, xule_context, align_only=False, use_defaults='both', require_binding=True, trace_info=None):
    '''This function does a cartesian product of result sets but only return the combinations where
       the alignment matches.
     
       The align_only is used when only alignment is need but not type matching and compute value evalutation.
       This happens for expressions that have multiple operands that don't directly interact with each other such as
       'if' expressions where the condition needs to align witht the then/else result but the values are not combind. 
       Likewise for the 'for' expression.
       
       use_defaults indicates if the default should be used to match unmatched results on the opposite side. If it is 'left'
       then the left default can be used to match unmatched right results. Vice versa for use_defaults='right'. If 'none' then no defaults 
       will be used for matching.
       
       binding_required indicates that there must be values on both sides to combine.
       '''
    
    result = []
    combinations = []
    left_matched = []
    right_matched = []
    
    '''try and match left and right, skipping defaults.'''
#     for left_res in left.results:
#         for right_res in right.results:


#     import inspect
#     print(inspect.getframeinfo(inspect.currentframe().f_back)[2])
#     
#     print("left %i, right %i, combinations %i" % (len(left.results), len(right.results), len(left.results) * len(right.results)))

    def index_results_by_alignment(result_set):
        aligned_results = collections.defaultdict(list)
        un_unit_aligned_results = collections.defaultdict(list)
        no_unit_aligned_results = collections.defaultdict(list)
        
        for res in result_set:
            hashed_alignment = hash_alignment(res.alignment)          
            aligned_results[hashed_alignment].append(res)
            '''Handling units in alignment'''
            if res.alignment is not None:
                if ('builtin', 'unit') in res.alignment:
                    un_unit_alignment = {k:v for k, v in res.alignment.items() if k != ('builtin', 'unit')}
                    hashed_un_unit_alignment = hash_alignment(un_unit_alignment)
                    un_unit_aligned_results[hashed_un_unit_alignment].append(res)
                else:
                    no_unit_aligned_results[hashed_alignment].append(res)
            
        return aligned_results, no_unit_aligned_results, un_unit_aligned_results

    left_indexed_results, left_no_unit_indexed_results, left_un_unit_indexed_results = index_results_by_alignment(left)
    right_indexed_results, right_no_unit_indexed_results, right_un_unit_indexed_results = index_results_by_alignment(right)
    
    combined_results = collections.defaultdict(list)
    for k in left_indexed_results.keys() | right_indexed_results.keys():
        left_key = k if k in left_indexed_results else hash(None)
        right_key = k if k in right_indexed_results else hash(None)
        
        if (left_key in left_indexed_results and right_key in right_indexed_results):
            combined_results[(k,0)] += (left_indexed_results[left_key], right_indexed_results[right_key])
    '''Handling units in alignment -
       If one side has units and other side does not, then these results can match. This is handled by created indexed results by 'no_unit' and 'un_unit'. The
       'no_unit' dictionary only contains results where there is no unit in the alignment. The 'un_unit' dictionary only contains results where there is a unit
       in the alignment, however, the key is rebuilt by removing the unit portion of the alignment. This will create an aligment that does not have unit. Thee two
       dictionaries are then matched up with no_unit and un_unit for each side. This will find combinations where a result with a unit can match to a result without a unit.
    '''
    for k in left_un_unit_indexed_results.keys() & right_no_unit_indexed_results.keys():
        combined_results[(k,1)] = (left_un_unit_indexed_results[k], right_no_unit_indexed_results[k])

    for k in left_no_unit_indexed_results.keys() & right_un_unit_indexed_results.keys():
        combined_results[(k,2)] = (left_no_unit_indexed_results[k], right_un_unit_indexed_results[k])
        
#     if len(right.results) > 1:
#         print("ALINGMENT left: %i, left_indexed: %i, right: %i, right_indexed: %i, combined: %i, left has none %s, right has none %s" % (len(left.results), 
#                                                                                                            len(left_indexed_results), 
#                                                                                                            len(right.results),
#                                                                                                            len(right_indexed_results), 
#                                                                                                            len(combined_results),
#                                                                                                            str(hash(None) in left_indexed_results),
#                                                                                                            str(hash(None) in right_indexed_results)))
#                     
    for combined_left, combined_right in combined_results.values():
#         if len(right.results) > 1:
#             print("mini left: %i, mini right: %i" % (len(combined_left), len(combined_right)))
#         
        for left_result, right_result in it.product(combined_left, combined_right):
            if vars_aligned(left_result, right_result):
                combinations.append((left_result, right_result))
                left_matched.append(left_result)
                right_matched.append(right_result)
    
    '''If there is a left default match it to all the unmatched right results.'''
    if use_defaults in ('both', 'left'):
        for right_res in right.results:
            if right_res not in right_matched:
                combinations.append((left.default, right_res))
                
    '''If there is a right default match it to all the unmatched left results.'''
    if use_defaults in ('both', 'right'):
        for left_res in left.results:
            if left_res not in left_matched:
                combinations.append((left_res, right.default))
    '''if there are only defaults on each side, then match them.'''
    if ((use_defaults == 'both') and 
        (len(left.results) == 0 and len(right.results) == 0) and
        (left.default.type != 'unbound' or right.default.type != 'unbound')):
        combinations.append((left.default, right.default))
    
    for combined in combinations:
            if require_binding and (combined[0].type == 'unbound' or combined[1].type == 'unbound'):
                    continue
            if align_only:
                combined_type = (None, None, None)
            else:
                combined_type = combine_xule_types(combined[0], combined[1], xule_context)
            
            new_alignment = combine_alignment(combined[0], combined[1])

            new_meta = combine_result_meta(combined[0], combined[1], xule_context, trace_info=trace_info)
            new_alignment = new_meta[XuleResult._ALIGNMENT]
            new_tags = new_meta[XuleResult._TAGS]
            new_facts = new_meta[XuleResult._FACTS]
            new_vars = new_meta[XuleResult._VARS]

            result.append({"left": combined[0], 
                           "right": combined[1],
                           "type": combined_type[0],
                           "left_compute_value": combined_type[1],
                           "right_compute_value": combined_type[2],
                           "alignment": new_alignment,
                           "tags": new_tags,
                           "facts": new_facts,
                           "vars": new_vars,
                           "meta": new_meta})
        
    return result

def hash_alignment(alignment):
    return hash(None if alignment is None else frozenset(alignment.items()))

def vars_aligned(left_result, right_result):
    common_var_keys = set(left_result.vars.keys()) & set(right_result.vars.keys())
    return all([len(left_result.vars[common_var_key] & right_result.vars[common_var_key]) > 0 for common_var_key in common_var_keys])

def combine_tags(left_result, right_result):
    return dict(list(left_result.tags.items()) + list(right_result.tags.items()))

def combine_facts(left_result, right_result):
    def uniquify(seq): # Dave Kirby
        # Order preserving
        seen = set()
        return [x for x in seq if x not in seen and not seen.add(x)]
    
    return uniquify(left_result.facts + right_result.facts)

def combine_vars(left_result, right_result):
    var_indexes = left_result.vars.keys() | right_result.vars.keys()
    empty_set = set()
    new_vars = collections.defaultdict(set, ((k, left_result.vars.get(k, empty_set) | right_result.vars.get(k, empty_set)) for k in var_indexes))
    return new_vars

def combine_from_model(left_result, right_result):
    return left_result.from_model or right_result.from_model

def combine_trace(left_result, right_result, xule_context, trace_info=None): 
    
    if xule_context.show_trace:
        new_trace = collections.deque(left_result.trace)
        if trace_info is None:
            new_trace.extend(right_result.trace)
            return new_trace
        else:
            new_trace.extend(trace_info)
            new_trace.extend(right_result.trace)
            return new_trace
    else:
        return collections.deque()
    
    ''' 
    if trace_info is None:
        return left_result.trace + right_result.trace
    else:
        return left_result.trace + trace_info + right_result.trace
    '''
def combine_result_meta(left_result, right_result, xule_context, trace_info=None):
    return [combine_alignment(left_result, right_result),
            combine_tags(left_result, right_result), 
            combine_facts(left_result, right_result),
            combine_vars(left_result, right_result),
            combine_from_model(left_result, right_result),
            combine_trace(left_result, right_result, xule_context, trace_info=trace_info)]

def combine_alignment(left_result, right_result):
    if left_result.alignment is not None:
        return left_result.alignment
    else:
        return right_result.alignment

def combine_defaults(left_result_set, right_result_set, xule_context):

    if left_result_set.default.type in ('unbound', 'none') and right_result_set.default.type in ('unbound', 'none'):
        left_result = left_result_set.default
        right_result = right_result_set.default
    elif left_result_set.default.type in ('unbound', 'none'):
        #find a left result that can align to the right default (which is not unbound).
        try:
            left_result = next(result for result in left_result_set if result.alignment is None)
        except StopIteration:
            left_result = left_result_set.default
        right_result = right_result_set.default
    elif right_result_set.default.type in ('unbound', 'none'):
        #find a right result that can align to the left default (which is not unbound)
        try:
            right_result = next(result for result in right_result_set if result.alignment is None)
        except StopIteration:
            right_result = right_result_set.default
        left_result = left_result_set.default
    else:
        left_result = left_result_set.default
        right_result = right_result_set.default

        
    meta = combine_result_meta(left_result, right_result, xule_context)    
    combined_type = combine_xule_types(left_result, right_result, xule_context)
    
    return {"left": left_result, 
            "right": right_result,
            "type": combined_type[0],
            "left_compute_value": combined_type[1],
            "right_compute_value": combined_type[2],
            "alignment": None,
            "tags": meta[XuleResult._TAGS],
            "facts": meta[XuleResult._FACTS],
            "vars": meta[XuleResult._VARS],
            "meta": meta}
    
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
        alignment[('builtin', 'lineItem')] = model_fact.elementQname
    
    #unit
    if model_fact.isNumeric:
        if 'unit' not in non_align_builtins:
            unit_value = model_to_xule_unit(model_fact.unit.measures, xule_context)
            alignment[('builtin', 'unit')] = hash(unit_value)
            xule_context.hash_table[('unit', hash(unit_value))] = unit_value
            
    '''PERIOD AND ENTITY SHOULD FOLLOW THE MODEL FOR UNIT. THERE SHOULD BE A MODEL_TO_XULE FOR THEM.'''
    #period
    if 'period' not in non_align_builtins:
        period_value = model_to_xule_period(model_fact.context, xule_context)
        alignment[('builtin', 'period')] = hash(period_value)
        xule_context.hash_table[('period', hash(period_value))] = period_value
        
    #entity
    if 'entity' not in non_align_aspects:
        entity_value = model_to_xule_entity(model_fact.context, xule_context)
        alignment[('builtin', 'entity')] = hash(entity_value)
        xule_context.hash_table[('entity', hash(entity_value))] = entity_value
          
    #dimensional apsects
    non_align_dimensions = {aspect_info[ASPECT] for aspect_info in non_align_aspects if aspect_info[TYPE] == 'explicit_dimension'}
    for fact_dimension_qname, dimension_value in model_fact.context.qnameDims.items():
        if fact_dimension_qname not in non_align_dimensions:
            member_hash = hash((dimension_value.memberQname.namespaceURI, dimension_value.memberQname.localName))
            alignment[('explicit_dimension', fact_dimension_qname)] = member_hash
            xule_context.hash_table[('member',member_hash)] = dimension_value.memberQname
        
    return alignment

def prepare_property_args(left_rs, args, property_name, xule_context):
    '''This function creates a table of executions for a propert of the left object and the aligned arguments.'''
    
    '''A copy of the left result is created with copied results. This is so the added 'property_args' of the result are not removed by 
       a further down evalutation. This happends when an argument uses the same left_result object as the current property. For example:
                calcNetwork = ::taxonomy::summation-item-networks;
                for (c1 in $calcNetwork)
                    for (c2 in $c1::descendant-relationships(for (c3 in $c1::source-concepts()) $c3, 1)) 
                        count($c2)
                        
    '''
    left_arg_rs = XuleResultSet()
    left_arg_rs.default = left_rs.default
    for left_result in left_rs:
        #copy_left_result = XuleResult(left_result.value, left_result.type, left_result.alignment, left_result.tags, left_result.facts, left_result.vars)
        copy_left_result = left_result.dup()
        copy_left_result.property_args = tuple()
        left_arg_rs.append(copy_left_result)
    
    for arg_expr in args:
        aligned_current_arg_rs = XuleResultSet()
        
        for left_result in left_arg_rs:
            '''Add the single value left result variables'''
            single_vars = push_single_value_variables(left_result.vars, xule_context)
#             single_vars = list(left_result.vars.items())
#             for var_index, var_result_index in single_vars:
#                 var_info = xule_context.var_by_index(var_index)
#                 xule_context.add_arg(var_info['name'],
#                                       var_info['tag'],
#                                       XuleResultSet(var_info['value'].results[var_result_index]))        
            
            current_arg_rs = evaluate(arg_expr[0], xule_context)
            
            '''Remove the pushed single value left result variables.'''
            pop_single_value_variables(single_vars, current_arg_rs, xule_context)
#             for var_index, var_result_index in single_vars[::-1]:
#                 var_info = xule_context.var_by_index(var_index)
#                 var_info = xule_context.del_var(var_info['name'], current_arg_rs)

            for combined in align_result_sets(current_arg_rs, XuleResultSet(left_result), xule_context, align_only=True, use_defaults='right'):
                new_left_result = combined['right'].dup()
                new_left_result.meta = combined['meta']   
                new_left_result.property_args = combined['right'].property_args + (combined['left'], ) #this is a singleton tuple
                aligned_current_arg_rs.append(new_left_result)
            
        left_arg_rs = aligned_current_arg_rs
    
    property_table = []
    for res in left_arg_rs:
        property_args = res.property_args #this is a tuple
        #clean up the left object
        delattr(res, 'property_args')
        property_table.append((res, property_args))
    
    return property_table
    
def xule_group_to_system(in_result, xule_context):
    
    if hasattr(in_result, 'original_result') and hasattr(in_result.original_result, 'shadow_group'):
        return in_result.original_result.shadow_group
    else:
        if in_result.type == 'list':
            return_value = [item_result.value for item_result in in_result.value]
        elif in_result.type == 'set':
            return_value = {item_result.value for item_result in in_result.value}
        else:
            raise XuleProcessingError(_("Cannot convert '%s' to system list or set." % in_result.type), xule_context)

        if hasattr(in_result, 'original_result'):
            in_result.original_result.shadow_group = return_value
        return return_value
    
def print_tags(result):
    tag_strings = []
    for tag_name, value in result.tags.items():
        tag_strings.append("%s = %s" % (tag_name, value))
    
    return "\n".join(tag_strings)
    
def process_message(message_string, result, xule_context):    
    import re 
    
    common_aspects = get_common_aspects(result.facts, xule_context)
    
    for tag_name, tag_result in result.tags.items():        
        replacement_value = format_result_value(tag_result, xule_context) or ''
        
        if tag_result.type == 'fact':
            
            fact_context = get_uncommon_aspects(tag_result.value, common_aspects, xule_context)
            
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*context\s*}', format_alignment(fact_context, xule_context), message_string)
        elif tag_result.type == 'empty_fact':
            if ('builtin', 'lineItem') in result.alignment:
                tag_context = format_qname(result.alignment[('builtin', 'lineItem')], xule_context)
            else:
                tag_context = str(tag_result.value)
                
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', 'missing', message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', 'missing', message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*context\s*}', tag_context, message_string)
        else:
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*\.\s*value\s*}', replacement_value, message_string)
            message_string = re.sub('\$\s*{\s*' + tag_name + '\s*}', replacement_value, message_string)

    message_string = re.sub('\$\s*{\s*context\s*}', format_alignment(common_aspects, xule_context), message_string)
    message_string = re.sub('\$\s*{\s*value\s*}', format_result_value(result, xule_context) or '', message_string)
    if xule_context.show_trace:
        message_string = re.sub('\$\s*{\s*trace\s*}', format_trace(xule_context, result, common_aspects), message_string)
    message_string = message_string.replace('%', '%%')

    return message_string

def format_result_value(result, xule_context):

    res_type, res_value = get_type_and_compute_value(result, xule_context)

    if result.type == 'fact':
        if type(result.value.xValue) == gYear:
            return str(res_value)
    
    if res_type in ('float', 'decimal'):
        format_rounded = "{0:,.3f}".format(res_value)
        reduced_round = reduce_number(format_rounded)
        format_orig = "{0:,}".format(res_value)
        reduced_orig = reduce_number(format_orig)
        
        if reduced_round != reduced_orig:
            reduced_round += " (rounded 3d)" 
            
        return reduced_round
    
    elif res_type in ('int'):
        return "{0:,}".format(res_value)
    
    elif res_type == 'unit':
        if len(res_value[1]) == 0:
            #no denominator
            unit_string = "%s" % " * ".join([x.localName for x in res_value[0]])
        else:
            unit_string = "%s/%s" % (" * ".join([x.localName for x in res_value[0]]), 
                                             " * ".join([x.localName for x in res_value[1]]))
        return unit_string
    
    elif res_type == 'duration':
        if res_value[0] == datetime.datetime.min and res_value[1] == datetime.datetime.max:
            return "forever"
        else:
            if result.from_model == True:
                end_date = res_value[1] - datetime.timedelta(days=1)
            else:
                end_date = res_value[1]
            return"duration('%s', '%s')" % (res_value[0].strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        
    elif res_type == 'instant':
        if result.from_model == True:
            return "instant('%s')" % (res_value - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            return "instant('%s')" % res_value.strftime("%Y-%m-%d")
    
    elif res_type == 'list':
        list_value = ", ".join([format_result_value(sub_res, xule_context) for sub_res in res_value])
        return list_value
    
    elif res_type == 'set':
        set_value = "set(" + ", ".join([format_result_value(sub_res, xule_context) for sub_res in res_value]) + ")" 
        return set_value
    
    elif res_type == 'concept':
        return str(res_value.qname)
    
    elif res_type == 'taxonomy':
        if res_value is xule_context.model:
            return("instance taxonomy")
        else:
            return("rules taxonomy")
    else:
        return str(res_value)

def reduce_number(num):
    if '.' in num:
        j = 0
        for i in range(1,4):
            if num[-i] == '.':
                break
            elif num[-i] == '0':
                j = i
            else:
                break
        if j != 0:
            num = num[:-j]
        if num[-1] == '.':
            num = num[:-1]
        return num
    else:
        return num

def format_qname(qname, xule_context):
    cat_namespace = xule_context.rule_set.getNamespaceInfoByUri(qname.namespaceURI, xule_context.cat_file_num)
    if cat_namespace:
        if cat_namespace['prefix'] == '*':
            return qname.localName
        else:
            return cat_namespace['prefix'] + ":" + qname.localName
    else:
        return str(qname)
    
def format_alignment(aspects, xule_context):

    if len(aspects) == 0:
        return ''
    
    aspect_strings = []
    line_item_string = ""
    
    #built in aspects
    if ('builtin', 'lineItem') in aspects:
        line_item_string = format_qname(aspects[('builtin', 'lineItem')], xule_context)
    
    if ('builtin', 'period') in aspects:
        period_hash = aspects[('builtin', 'period')]

        period_info = xule_context.hash_table[('period', period_hash)]
        if isinstance(period_info, tuple):
            if period_info[0] == datetime.datetime.min and period_info[1] == datetime.datetime.max:
                aspect_strings.append("period=forever")
            else:
                aspect_strings.append("period=duration('%s', '%s')" % (period_info[0].strftime("%Y-%m-%d"), (period_info[1] - datetime.timedelta(days=1)).strftime("%Y-%m-%d")))
        else:
            aspect_strings.append("period=instant('%s')" % (period_info - datetime.timedelta(days=1)).strftime("%Y-%m-%d"))
    
    if ('builtin', 'unit') in aspects:
        unit_hash = aspects[('builtin', 'unit')]

        model_unit = xule_context.hash_table[('unit', unit_hash)]
        if len(model_unit[1]) == 0:
            #no denominator
            aspect_strings.append("unit=%s" % " * ".join([x.localName for x in model_unit[0]]))
        else:
            aspect_strings.append("unit=%s/%s" % (" * ".join([x.localName for x in model_unit[0]]), 
                                                  " * ".join([x.localName for x in model_unit[1]])))
            
    if ('builtin', 'entity') in aspects:
        entity_hash = aspects[('builtin', 'entity')]

        entity_info = xule_context.hash_table[('entity', entity_hash)]
        aspect_strings.append("entity={%s}%s" % (entity_info[0], entity_info[1]))      
        
    #dimensions
    dimension_aspects = [(aspect_info[ASPECT],aspect_info, aspect_member) for aspect_info, aspect_member in aspects.items() if aspect_info[TYPE] == 'explicit_dimension']
    #sort by the dimension qname
    dimension_aspects.sort(key=lambda tup: tup[0])
    
    #for aspect_info, aspect_member in aspects.items():
    for dimension_aspect in dimension_aspects:
        aspect_info = dimension_aspect[1]
        aspect_member = dimension_aspect[2]
        if aspect_info[TYPE] == 'explicit_dimension':
            member_hash = aspects[aspect_info]
            aspect_member = xule_context.hash_table['member', member_hash]
            aspect_strings.append("%s=%s" % (format_qname(aspect_info[ASPECT], xule_context), format_qname(aspect_member, xule_context)))
    
    if len(aspect_strings) > 0:
        aspect_string = "[" + "\n".join(aspect_strings) + "]"
    else:
        aspect_string = ""
        
    return line_item_string + aspect_string

def get_all_aspects(model_fact, xule_context):
    '''This function gets all the apsects of a fact'''
    return get_alignment(model_fact, {}, xule_context)

def get_common_aspects(model_facts, xule_context):
    
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

def get_uncommon_aspects(model_fact, common_aspects, xule_context):
    
    uncommon_aspects = {}
    
    fact_aspects = get_all_aspects(model_fact, xule_context)
    for aspect_info, aspect_value in fact_aspects.items():
        if aspect_info == ('builtin', 'lineItem'):
            uncommon_aspects[aspect_info] = aspect_value
        elif aspect_info not in common_aspects:
                uncommon_aspects[aspect_info] = aspect_value
    
    return uncommon_aspects
    
def get_message(rule, result, xule_context):

    if 'message' in rule:
        message_result_set = evaluate(rule.message[0], xule_context)
        if len(message_result_set.results) > 0:
            message_string = str(message_result_set.results[0].value)
        else:
            message_string = ""
            
        if len(message_result_set.results) > 1:
            xule_context.model.warning("xule:warning", "Rule '%s' produced %i message strings." % (xule_context.rule_name, len(message_result_set.results)))
    else:
        message_string = ""
    
    if message_string == "":
        #create a default message
        if rule.getName() == 'reportDeclaration':
                message_string = "${value} ${context}"
        elif rule.getName() == 'raiseDeclaration':
            if len(result.facts) > 0:
                message_string = "${default_fact.value} ${default_fact.context}${context}"
                result.add_tag('default_fact', XuleResult(result.facts[0], 'fact'))
            else:
                message_string = "${value}"
        elif rule.getName() == 'formulaDeclaration':
            message_string = "${left.value} != ${right.value} ${context}"
    
    return process_message(message_string, result, xule_context)
            
def get_element_identifier(result, xule_context):
    if len(result.facts) > 0:
        model_fact = result.facts[0]
        
        if model_fact.id is not None:
            return (model_fact.modelDocument.uri + "#" + model_fact.id, model_fact.sourceline)
        else:
            #need to build the element scheme
            location = get_tree_location(model_fact)
            return (model_fact.modelDocument.uri + "#element(" + location + ")", model_fact.sourceline)
            
def get_tree_location(model_fact):
    
    if hasattr(model_fact.parentElement, '_elementSequence'):
        prev_location = get_tree_location(model_fact.parentElement)
    else:
        prev_location = "/1"
    
    return prev_location + "/" + str(model_fact._elementSequence)

def format_trace(xule_context, result, common_aspects):
#     import pprint
#     pprint.pprint(result.trace)

    trace_string = ""
    for step in result.trace:
        trace_string += ("  " * (step[0] - 1)) + format_result_value(step[3], xule_context) + format_trace_info(step[1], step[2], result, common_aspects, xule_context) + "\n"

    trace_string += format_alignment(common_aspects, xule_context)
    return trace_string

def format_trace_info(expr_name, sugar, result, common_aspects, xule_context):
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
        if sugar[0].value is not None:
            fact_context = get_uncommon_aspects(sugar[0].value, common_aspects, xule_context)
            trace_info = 'factset '
            if ('builtin', 'lineItem') not in fact_context:
                trace_info += str(sugar[0].qname) + " "
            trace_info +=  format_alignment(fact_context, xule_context)
    else:
        trace_info += expr_name
    
    if len(trace_info) > 0:
        trace_info = " - " + trace_info
    
    return trace_info

def caller():
    import inspect
    print(inspect.stack()[2][3])