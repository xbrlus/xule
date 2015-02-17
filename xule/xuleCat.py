import pprint 
import sys
from XuleRuleSet import XuleRuleSet

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

if __name__ == "__main__":
    rule_set_name = sys.argv[1]
    command = sys.argv[2]
    
    if len(sys.argv) > 1:
        if command == 'cat':
            print_catalog(rule_set_name)
        elif command == 'xml-rule':
            xml_rule(rule_set_name, sys.argv[3])
        elif command == 'dict-rule':
            dict_rule(rule_set_name, sys.argv[3])            
        elif command == 'xml-const':
            xml_const(rule_set_name, sys.argv[3])
        elif command == 'xml-func':
            xml_func(rule_set_name, sys.argv[3])
        elif command == 'xml-file':
            xml_file(rule_set_name, sys.argv[3])
        else:
            print("Unknown command: %s" % command)
    else:
        print("No command supplied.")
