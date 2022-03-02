"""XuleParser

Xule is a rule processor for XBRL (X)brl r(ULE). 

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

$Change: 23280 $
DOCSKIP
"""
from pyparsing import ParseResults, lineno, ParseException, ParseSyntaxException, ParserElement
from . import XuleRuleSet as xrs
from . import XuleRuleSetBuilder as xrsb
from .xule_grammar import get_grammar
import os
import datetime
import sys
import hashlib
import threading

_options = None

def setOptions(options):
    global _options
    _options = options

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

def parseFile(dir, fileName, xuleGrammar, ruleSet):
    parse_errors = []
    try:
        full_file_name = os.path.join(dir, fileName)
        with open(full_file_name, 'rb') as xule_file:
            buffer = None
            file_hash_contents = hashlib.sha256()
            while buffer != b'':
                buffer = xule_file.read(4096)
                file_hash_contents.update(buffer)
            file_hash = file_hash_contents.hexdigest()

        #check if the file has changed
        if ruleSet.getFileHash(fileName) == file_hash and not ruleSet.recompile_all:
            #The file has not changed.
            ruleSet.markFileKeep(fileName)
        else:
            start_time = datetime.datetime.today()
            print("%s: parse start" % datetime.datetime.isoformat(start_time))

            returns = []
            def threaded_parse():
                returns.append(xuleGrammar.parseFile(full_file_name).asDict())

            t = threading.Thread(target=threaded_parse)
            t.start()
            t.join()
            parseRes = returns[0]

            # Fix parse result for later versions of PyParsing. PyParsing up to version 2.3.0 works fine. After 2.3.0 
            # the parse creates an extra layer in the hiearachy of the parse result for tagged, indexed and property
            # expressions. 
            fixForPyParsing(parseRes)


            #parseRes = xuleGrammar.parseFile(full_file_name).asDict()
            end_time = datetime.datetime.today()
            print("%s: parse end. Took %s" % (datetime.datetime.isoformat(end_time), end_time - start_time))
            ast_start = datetime.datetime.today()
            print("%s: ast start" % datetime.datetime.isoformat(ast_start))
            ruleSet.add(parseRes, os.path.getmtime(full_file_name), fileName, file_hash)
            ast_end = datetime.datetime.today()
            print("%s: ast end. Took %s" %(datetime.datetime.isoformat(ast_end), ast_end - ast_start))
        
        
    except (ParseException, ParseSyntaxException) as err:
        error_message = ("Parse error in %s \n" 
            "line: %i col: %i position: %i\n"
            "%s\n"
            "%s\n" % (full_file_name, err.lineno, err.col, err.loc, err.msg, err.line))
        parse_errors.append(error_message)
        print(error_message)
    
    return parse_errors

def fixForPyParsing(parseRes):
        if isinstance(parseRes, dict):
            if isinstance(parseRes.get('expr'), list):
                if len(parseRes['expr']) == 1:
                    parseRes['expr'] = parseRes['expr'][0]
                else:
                    raise xrs.XuleRuleSetError("Unable to parse rules. Using a version of PyParsing later than 2.3.0 and cannot correct parse result\n")
            for child in parseRes.values():
                fixForPyParsing(child)
        elif isinstance(parseRes, list) or isinstance(parseRes, set): # I don't think there will ever be a set, but this won't hurt.
            for child in parseRes:
                fixForPyParsing(child)

def parseRules(files, dest, compile_type, max_recurse_depth=None):

    parse_start = datetime.datetime.today()
    parse_errors = []

    # Set the stack size
    global _options
    if _options is None or getattr(_options, 'xule_stack_size', None) is None:
        #threading.stack_size(0x2000000)
        threading.stack_size(8 * 1048576)
    else:
        threading.stack_size(getattr(_options, 'xule_stack_size') * 1048576)
    
    #threading.stack_size(0x2000000)
    
    #Need to check the recursion limit. 1000 is too small for some rules.
    new_depth = max_recurse_depth or 5500
    orig_recursionlimit = sys.getrecursionlimit()
    if orig_recursionlimit < new_depth:
        sys.setrecursionlimit(new_depth)
    
    xuleGrammar = get_grammar()
    ruleSet = xrsb.XuleRuleSetBuilder(compile_type)
    ruleSet.append(dest)
    
    for ruleFile in sorted(files):
        processFile = ruleFile.strip()
        if os.path.isfile(processFile):
            root = os.path.dirname(processFile)
            parse_errors += parseFile(root, os.path.basename(processFile), xuleGrammar, ruleSet)

        elif os.path.isdir(processFile):
            #Remove an ending slash if there is one
            processFile = processFile[:-1] if processFile.endswith(os.sep) else processFile
            for root, dirs, files in os.walk(ruleFile.strip()):
                for name in sorted(files):
                    if os.path.splitext(name)[1] == ".xule":
                        print("Processing: %s" % os.path.basename(name))
                        relpath = os.path.relpath(root, processFile)
                        if relpath == '.': 
                            relpath = ''
                        parse_errors += parseFile(processFile, os.path.join(relpath,name), xuleGrammar, ruleSet)            
        else:
            print("Not a file or directory: %s" % processFile)
    
    #reset the recursion limit
    if orig_recursionlimit != sys.getrecursionlimit():
        sys.setrecursionlimit(orig_recursionlimit)
    
    if len(parse_errors) == 0:
        post_parse_start = datetime.datetime.today()
        print("%s: post parse start" % datetime.datetime.isoformat(post_parse_start))
        ruleSet.post_parse()
        post_parse_end = datetime.datetime.today()
        print("%s: post parse end. Took %s" %(datetime.datetime.isoformat(post_parse_end), post_parse_end - post_parse_start))
        ruleSet.close()
    else: #there are errors from parsing
        raise xrs.XuleRuleSetError("Unable to parse rules due to the following errors:\n" + "\n".join(parse_errors))

    parse_end = datetime.datetime.today()
    print("%s: Parsing finished. Took %s" %(datetime.datetime.isoformat(parse_end), parse_end - parse_start))

