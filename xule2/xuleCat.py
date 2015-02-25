import pprint
import sys
from XuleRuleSet import XuleRuleSet
from pyparsing import ParseResults

def print_catalog(rule_set_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)

    pprint.pprint(rule_set.catalog)
            
def xml_rule(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    print(rule.asXML())
    
def dict_rule(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    pprint.pprint(rule.asDict())       
    
def xml_file(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    file = rule_set.getFile(int(rule_name))
    
    print(file.asXML())        
    
def xml_const(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    cat_const = rule_set.catalog['constants'][rule_name]
    rule = rule_set.getItem(cat_const)
    
    print(rule.asXML())  
    
def xml_func(rule_set_name, rule_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    cat_func = rule_set.catalog['functions'][rule_name]
    
    print(cat_func)
    
    rule = rule_set.getItem(cat_func)
    
    print(rule.asXML())   

def id_files(rule_set_name):
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    for file_info in rule_set.catalog['files']:
        parse_res = rule_set.getFile(file_info['file'])
        print("File: %s" % file_info['name'])
        print(_display_ids(parse_res))
        
def _display_ids(parse_res, level=0, display_string=''):
    if isinstance(parse_res, ParseResults):
        additional = ''
        if parse_res.getName() == 'varRef':
            if parse_res.is_constant:
                additional =  " ($" + parse_res.varName + " - constant)"
            else:
                additional = " ($" + parse_res.varName + " declaration: " + str(parse_res.var_declaration) + ")"
        elif parse_res.getName() == 'varAssign':
            additional = " (" + parse_res.varName + ")"
        elif parse_res.getName() == 'forExpr':
            additional = " (" + parse_res.forVar + ")"
        elif parse_res.getName() == 'reportDeclaration':
            additional = " (" + parse_res.reportName + ")"
        elif parse_res.getName() == 'raiseDeclaration':
            additional = " (" + parse_res.raiseName + ")"  
        elif parse_res.getName() == 'formulaDeclaration':
            additional = " (" + parse_res.formulaName + ")"                      
        elif parse_res.getName() in ('functionDeclaration', 'functionReference'):
            additional = " (" + parse_res.functionName + ")"   
    
        
        if parse_res.number != '':
            additional += (" [" + 
                           ('1' if parse_res.number == 'single' else "*")  + 
                           ", " + str(parse_res.has_alignment) + 
                           ((", " + ("D" if parse_res.is_dependant else "I")) if 'is_dependant' in parse_res else "") +
                           ((", " + str(parse_res.var_refs)) if len(parse_res.var_refs) > 0 else "") + 
                           "]")
        
        display_string += ("  " * level) + str(parse_res.node_id) + ":" + parse_res.getName() + additional + "\n"
        for next_part in parse_res:
            display_string = _display_ids(next_part, level + 1, display_string)
    return display_string

def id_rule(rule_set_name, rule_name): 
    rule_set = XuleRuleSet()
    rule_set.open(rule_set_name)
    
    cat_rule = rule_set.catalog['rules'][rule_name]
    rule = rule_set.getItem(cat_rule)
    
    print(_display_ids(rule))  
        
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
        elif command == 'xml-file':
            xml_file(rule_set_name, sys.argv[3])
        elif command == 'ids':
            id_files(rule_set_name)
        else:
            print("Unknown command: %s" % command)
    else:
        print("No command supplied.")
