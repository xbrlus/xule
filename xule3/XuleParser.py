'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21535 $
'''
from pyparsing import ParseResults, lineno, ParseException, ParseSyntaxException, ParserElement

import os
import datetime
import sys
from .xule_grammar import get_grammar

def printRes(pr, level=0):
    level = level + 1
    print("level: " + str(level))
    if isinstance(pr, ParseResults):
        print("name: " + pr.name)
        
        for child in pr:
            printRes(child, level)

def add_location(src, loc, toks):
    #adds location information to the parse results
    '''NEEDS TO BE ADDED TO EACH OF THE ParserElements'''
    toks['char_loc'] = loc
    toks['line'] = lineno(loc, src)
    
    return toks

def parseFile(fileName, xuleGrammar, ruleSet, xml_dir=None):
    try:
        '''WOULD LIKE TO CHECK IF THE FILE IS ALREADY IN THE RULE SET AND IF IT HAS CHANGED.
           IF IT HASN'T CAN SKIP THE PARSING AND USE THE EXISTING PICKLED FILE. HOWEVER,
           NEED TO CHANGE THE WAY 'NEW' IS DONE IN THE XULERULESET, SO THAT IT PRESERVES THE 
           EXISTING FILES AND CATALOGS AND THEN CLEANS EVERYTHING UP WHEN THE RULESET IS CLOSED.
        '''
        start_time = datetime.datetime.today()
        print("%s: parse start %s" % (datetime.datetime.isoformat(start_time), fileName))
        
        parseRes = xuleGrammar.parseFile(fileName).asDict()
        
        if xml_dir:
            xml_file = xml_dir + "/" + os.path.basename(fileName) + ".xml"
            
            if not os.path.exists(xml_dir):
                os.makedirs(xml_dir)
            
            with open(xml_file,"w") as o:
                o.write(parseRes.asXML())

        end_time = datetime.datetime.today()
        print("%s: parse end. Took %s" % (datetime.datetime.isoformat(end_time), end_time - start_time))
#         import pprint
#         pprint.pprint(parseRes)
        ast_start = datetime.datetime.today()
        print("%s: ast start" % datetime.datetime.isoformat(ast_start))
        ruleSet.add(parseRes, os.path.getmtime(fileName), os.path.basename(fileName))
        ast_end = datetime.datetime.today()
        print("%s: ast end. Took %s" %(datetime.datetime.isoformat(ast_end), ast_end - ast_start))
        
        
    except (ParseException, ParseSyntaxException) as err:
        print("Parse error in %s \n" 
            "line: %i col: %i position: %i\n"
            "%s\n"
            "%s" % (sys.argv[1], err.lineno, err.col, err.loc, err.msg, err.line))



def parseRulesDetails(grammar_function, files, dest, xml_dir=None):
    
    parse_start = datetime.datetime.today()
    
    #Need to check the recursion limit. 1000 is too small for some rules.
    new_depth = 2500
    orig_recursionlimit = sys.getrecursionlimit()
    if orig_recursionlimit < new_depth:
        sys.setrecursionlimit(new_depth)
    
    xuleGrammar = grammar_function()
    ruleSet = XuleRuleSet()
    ruleSet.new(dest)
    
    for ruleFile in files:
        processFile = ruleFile.strip()
        if os.path.isfile(processFile):
            parseFile(processFile, xuleGrammar, ruleSet, xml_dir)

        elif os.path.isdir(ruleFile.strip()):
            for root, dirs, files in os.walk(ruleFile.strip()):
                for name in files:
                    if os.path.splitext(name)[1] == ".xule":
                        print("Processing: %s" % os.path.basename(name))
                        parseFile(os.path.join(root, name), xuleGrammar, ruleSet, xml_dir)            
        else:
            print("Not a file or directory: %s" % processFile)
    
    
    post_parse_start = datetime.datetime.today()
    print("%s: post parse start" % datetime.datetime.isoformat(post_parse_start))
    ruleSet.build_dependencies()
    post_parse_end = datetime.datetime.today()
    print("%s: post parse end. Took %s" %(datetime.datetime.isoformat(post_parse_end), post_parse_end - post_parse_start))
      
    ruleSet.close()
    
    #reset the recursion limit
    if orig_recursionlimit != sys.getrecursionlimit():
        sys.setrecursionlimit(orig_recursionlimit)    

    parse_end = datetime.datetime.today()
    print("%s: Parsing finished. Took %s" %(datetime.datetime.isoformat(parse_end), parse_end - parse_start))

def parseRules(files, dest, xml_dir=None, grammar=None):
    
    parseRulesDetails(get_grammar, files, dest, xml_dir)
    
if __name__ == "__main__":
    from XuleRuleSet import XuleRuleSet
    import argparse
    
    aparser = argparse.ArgumentParser()
    aparser.add_argument("source", help="Xule rule file or directory of rule files.")
    aparser.add_argument("target", help="Xule rul set directory. Location where the rule set will be created. Existing rule set files in this directory will be deleted")
    aparser.add_argument("--xml-dir", dest="xml_dir", help="Directory of where to put xml version of the parsed files.")
    aparser.add_argument("--xule-grammar", dest="xule_grammar", choices=['xule2', 'xule3'], default="xule2", help="Grammar version of the Xule rule file. Default is xule2")
    args = aparser.parse_args()
    
    print("%s: Using grammar %s" % (datetime.datetime.isoformat(datetime.datetime.today()), args.xule_grammar))
    if args.xule_grammar == "xule3":
        from xule_grammar3 import *
    else:
        from xule_grammar2 import *
    
#     if len(sys.argv) > 1:
#         dest = sys.argv[2].strip() if len(sys.argv) > 2 else "xuleRules"
#         if len(sys.argv) > 3:
#             parseRules([sys.argv[1]], dest, xml_dir = sys.argv[3])
#         else:
#             parseRules([sys.argv[1]], dest)

    parseRulesDetails(get_grammar, [args.source], args.target, xml_dir = args.xml_dir)      
else:
    from .XuleRuleSet import XuleRuleSet
