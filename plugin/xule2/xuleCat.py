'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change$
'''
import pprint 
import sys
from XuleRuleSet import XuleRuleSet
from pyparsing import ParseResults
from lxml import etree



def print_catalog(rule_set_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
#     print_pre_calcs = []
#     for pre_calc in rule_set.catalog['pre_calc_expressions']:
#         print_pre_calcs.append((pre_calc.node_id, 'r' if pre_calc.get('rules-taxonomy') else ''))
#         
#     rule_set.catalog['pre_calc_expressions'] = sorted(print_pre_calcs, key=lambda x: x[0])
        
    pprint.pprint(rule_set.catalog)
            
def xml_rule(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    print(etree.tostring(rule_part_to_xml(rule), encoding="unicode", pretty_print=True))

    
def rule_part_to_xml(rule_part):     
    atts = dict()
    sub_parts = []
    
    for k, v in rule_part.items():
        if k not in ('var_refs', 'dependent_vars', 
                     'downstream_iterables', 'dependent_iterables',
                     'is_dependent', 'node_id',
                     'has_alignment', 'number',
                     'cacheable', 'is_iterable',
                     'instance', 'table_id', 'is_constant', 'var_declaration'):
            if isinstance(v, ParseResults):
                sub_parts.append(v)
            else:
                atts[k] = v
                
    node = etree.Element(rule_part.getName())
    if len(sub_parts) == 0:
        if rule_part.getName() in ('integer', 'float', 'string', 'void'):  
            node.text = rule_part.value
        else:
            for att_name, att in atts.items():
                node.set(att_name, att)
    else:
        for att_name, att in atts.items():
            node.set(att_name, att)
        for sub_part in rule_part:
            if isinstance(sub_part, ParseResults):
                if not (sub_part.getName() == 'forControl' and rule_part.getName() == 'forBodyExpr'):
                    node.append(rule_part_to_xml(sub_part))
            
    return node
        
        
    
    
    
    
    '''
    if len(sub_parts) == 0:
        if rule_part.getName() in ('integer', 'float', 'string', 'void'):
            o = "<" + rule_part.getName() + ">"
            o += rule_part.value
            o += "<" + rule_part.getName() + "/>"
        else:
            o = "<" + rule_part.getName()
            for att_name, att in atts.items():
                o += " " + att_name + "=" + str(att)
            o += "/>"
    else:
        o = "<" + rule_part.getName()
        for att_name, att in atts.items():
            o += " " + att_name + "=" + att
        o += ">"
        for sub_part in sub_parts:
            o += rule_part_to_xml(sub_part)
        o += "<" + rule_part.getName() + "/>"

    return o
    '''
    
def dict_rule(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    pprint.pprint(rule.asDict())       
    
def xml_file(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    file = rule_set.getFile(int(rule_name))
    
    #print(file.asXML()) 
    print(etree.tostring(rule_part_to_xml(file), encoding="unicode", pretty_print=True))       
    
def xml_const(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_const = rule_set.catalog['constants'][rule_name]
    rule = rule_set.getItem(cat_const)
    
    print(etree.tostring(rule_part_to_xml(rule), encoding="unicode", pretty_print=True))  
    
def xml_func(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_func = rule_set.catalog['functions'][rule_name]
    
    print(cat_func)
    
    rule = rule_set.getItem(cat_func)
    
    print(etree.tostring(rule_part_to_xml(rule), encoding="unicode", pretty_print=True))   

def id_files(rule_set_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    for file_info in rule_set.catalog['files']:
        parse_res = rule_set.getFile(file_info['file'])
        print("File: %s" % file_info['name'])
        print(_display_ids(parse_res))
        
def _display_ids(parse_res, level=0, display_string=''):
    if isinstance(parse_res, ParseResults):
        additional = ''
        if parse_res.getName() == 'varRef':
            if parse_res.is_constant:
                additional =  " ($" + parse_res.varName + " declaration: " + str(parse_res.var_declaration) + ") - constant)"
            else:
                additional = " ($" + parse_res.varName + " declaration: " + str(parse_res.var_declaration) + ")"
        elif parse_res.getName() == 'varAssign':
            additional = " (" + parse_res.varName + ")" + (" NOT USED" if parse_res.get('not_used') == True else "")
        elif parse_res.getName() == 'constantAssign':
            additional = " (" + parse_res.constantName + ")"
        elif parse_res.getName() == 'functionArg':
            additional = " (" + parse_res.argName + ")"
        elif parse_res.getName() == 'forExpr':
            additional = " (" + parse_res.forControl.forVar + ")"
        elif parse_res.getName() == 'reportDeclaration':
            additional = " (" + parse_res.reportName + ")"
        elif parse_res.getName() == 'raiseDeclaration':
            additional = " (" + parse_res.raiseName + ")"  
        elif parse_res.getName() == 'formulaDeclaration':
            additional = " (" + parse_res.formulaName + ")"                      
        elif parse_res.getName() in ('functionDeclaration', 'functionReference'):
            additional = " (" + parse_res.functionName + ")"  + (" CACHEABLE" if parse_res.get('cacheable') == True else "") 
        elif parse_res.getName() == 'preconditionDeclaration':
            additional = " ({})".format(parse_res.preconditionName)
        elif parse_res.getName() == 'preconditionNames':
            additional = " ({})".format(", ".join(parse_res))
        
        iterable_additions = []
        if parse_res.is_iterable != '':
            #uses the instance taxonomy
            if parse_res.get('instance'):
                iterable_additions.append('i')
            #uses the rules-taxonomy
            if parse_res.get('rules-taxonomy'):
                iterable_additions.append('r')
            #number
            if parse_res.get('number') == 'single':
                iterable_additions.append('1')
            if parse_res.get('number') == 'multi':
                iterable_additions.append('*')
            #has alignment
            if parse_res.get('has_alignment'):
                iterable_additions.append('Align')
            else:
                iterable_additions.append('NoAlign')
            #dependent vars
            if hasattr(parse_res, 'dependent_vars') and len(parse_res.dependent_vars) > 0:
                iterable_additions.append("v" + str({(x[0], x[1]) for x in parse_res.dependent_vars}))
            #var refs
            if hasattr(parse_res, 'var_refs') and len(parse_res.var_refs) > 0:
                iterable_additions.append("V" + str({(x[0], x[1]) for x in parse_res.var_refs}))
            #dependent iterables
            if hasattr(parse_res, 'dependent_iterables') and len(parse_res.dependent_iterables) > 0:
                iterable_additions.append("i" + str({dep.node_id for dep in parse_res.dependent_iterables}))
            #downstream iterables
            if hasattr(parse_res, 'downstream_iterables') and len(parse_res.downstream_iterables) > 0:
                iterable_additions.append("di" + str({dep.node_id for dep in parse_res.downstream_iterables}))
            #values expression
            if parse_res.get('values_expression'):
                iterable_additions.append("Values")
            #Table id
            if parse_res.get('table_id'):
                iterable_additions.append('Table {}'.format(parse_res.table_id))
            
            additional += ", ".join(iterable_additions)
#             additional += (" [" + 
#                            ('i, ' if parse_res.get('instance') else '') +
#                            ('r, ' if parse_res.get('rules-taxonomy') else '') +
#                            (('1' if parse_res.number == 'single' else "*") if 'number' in parse_res else '')  + 
#                            (", Align" if parse_res.has_alignment else ", NoAlign") + 
#                            ((", " + ("D" if parse_res.is_dependent else "I")) if 'is_dependent' in parse_res else "") +
#                            #((", " + str(parse_res.var_refs)) if len(parse_res.var_refs) > 0 else "") + 
#                            ((", v" + str({(x[0], x[1]) for x in parse_res.dependent_vars})) if len(parse_res.dependent_vars) > 0 else "") +
#                            ((", V" + str({(x[0], x[1]) for x in parse_res.var_refs})) if len(parse_res.var_refs) > 0 else "") +
#                            #((", VIds" + str(parse_res.var_ref_ids)) if 'var_ref_ids' in parse_res else "")  +
#                            ((", i" + str({dep.node_id for dep in parse_res.dependent_iterables})) if len(parse_res.dependent_iterables) > 0 else "") +         
#                            ((", di" + str({dep.node_id for dep in parse_res.downstream_iterables})) if len(parse_res.downstream_iterables) > 0 else "") +                    
#                            (", Values" if parse_res.get('values_expression') == True else "") +
#                            (", Table %i" % parse_res.table_id if parse_res.get('table_id') is not None else "") +
#                            "]")
        
        if 'is_iterable' in parse_res:
            additional += " iterable"
        if 'in_loop' in parse_res:
            additional += " LOOP"
        display_string += ("  " * level) + str(parse_res.node_id) + ":" + parse_res.getName() + additional + "\n"
        for next_part in parse_res:
            display_string = _display_ids(next_part, level + 1, display_string)
    return display_string

def id_rule(rule_set_name, rule_name): 
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    print(_display_ids(rule))  

def id_func(rule_set_name, func_name): 
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    
    cat_func = rule_set.catalog['functions'][func_name]
    func = rule_set.getItem(cat_func)
    
    print(_display_ids(func))  

def check_node_index(rule_set_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name, open_for_add=False)
    mismatch_found = False
    node_count = 0
    
    for node_id in rule_set.catalog['node_index']:
        node_count += 1
        node = rule_set.getNodeById(node_id)
        if node_id != node.node_id:
            mismatch_found = True
            print("Mismatch",node_id, node.node_id)

    if not mismatch_found:
        print("Node index verified. Checked %i nodes." % node_count)

if __name__ == "__main__":
    rule_set_name = sys.argv[1]
    command = sys.argv[2]
    
    if len(sys.argv) > 1:
        if command == 'cat':
            print_catalog(rule_set_name)
        elif command == 'xml-rule':
            xml_rule(rule_set_name, sys.argv[3])
        elif command == 'id-rule':
            id_rule(rule_set_name, sys.argv[3])            
        elif command == 'dict-rule':
            dict_rule(rule_set_name, sys.argv[3])            
        elif command == 'xml-const':
            xml_const(rule_set_name, sys.argv[3])
        elif command == 'xml-func':
            xml_func(rule_set_name, sys.argv[3])
        elif command == 'id-func':
            id_func(rule_set_name, sys.argv[3])             
        elif command == 'xml-file':
            xml_file(rule_set_name, sys.argv[3])
        elif command == 'ids':
            id_files(rule_set_name)
        elif command == 'check-node-index':
            check_node_index(rule_set_name)
        else:
            print("Unknown command: %s" % command)
    else:
        print("No command supplied.")
