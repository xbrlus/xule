<<<<<<< HEAD
"""XuleParser

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - present XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23663 $
DOCSKIP
"""
from pyparsing import ParseResults, lineno, ParseException, ParseSyntaxException
from . import XuleRuleSet as xrs
from . import XuleRuleSetBuilder as xrsb
from .XuleParseFile import parseFile
import os
import datetime
import json
import sys
import hashlib
from dataclasses import dataclass
from pathlib import Path

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

@dataclass(frozen=True)
class CompileJob:
    fullFileName: str
    fileName: str
    fileHash: str

def add_location(src, loc, toks):
    #adds location information to the parse results
    '''NEEDS TO BE ADDED TO EACH OF THE ParserElements'''
    toks['char_loc'] = loc
    toks['line'] = lineno(loc, src)
    
    return toks

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

def parseRules(files, dest, compile_type, max_recurse_depth=None, xule_compile_workers=1):

    parse_start = datetime.datetime.today()
    parse_errors = []

    # Set the stack size
    global _options
    save_pyparsing_result_location = getattr(_options, 'xule_compile_save_pyparsing_result_location', None)
    stack_size = getattr(_options, 'xule_stack_size', 8) * 1048576

    #Need to check the recursion limit. 1000 is too small for some rules.
    new_depth = max_recurse_depth or 5500
    orig_recursionlimit = sys.getrecursionlimit()
    if orig_recursionlimit < new_depth:
        sys.setrecursionlimit(new_depth)
    
    ruleSet = xrsb.XuleRuleSetBuilder(compile_type)
    ruleSet.append(dest)
    
    compileJobs = []
    for ruleFile in sorted(files):
        processFile = ruleFile.strip()
        if os.path.isfile(processFile):
            root = os.path.dirname(processFile)
            fileName = os.path.basename(processFile)
            fullFileName = os.path.join(root, fileName)
            fileHash = getFileHash(fullFileName)
            if ruleSet.recompile_all or fileHash != ruleSet.getFileHash(fileName):
                compileJobs.append(CompileJob(fullFileName, fileName, fileHash))
            else:
                ruleSet.markFileKeep(fileName)

        elif os.path.isdir(processFile):
            #Remove an ending slash if there is one
            processFile = processFile[:-1] if processFile.endswith(os.sep) else processFile
            for root, dirs, files in os.walk(ruleFile.strip()):
                for name in sorted(files):
                    if os.path.splitext(name)[1] == ".xule":
                        relpath = os.path.relpath(root, processFile)
                        if relpath == '.': 
                            relpath = ''
                        relativeFileName = os.path.join(relpath, name)
                        fullFileName = os.path.join(processFile, relativeFileName)
                        fileHash = getFileHash(fullFileName)
                        if ruleSet.recompile_all or fileHash != ruleSet.getFileHash(relativeFileName):
                            compileJobs.append(CompileJob(fullFileName, relativeFileName, fileHash))
                        else:
                            ruleSet.markFileKeep(relativeFileName)
        else:
            print("Not a file or directory: %s" % processFile)

    if xule_compile_workers == 1:
        for job in compileJobs:
            try:
                parseRes = parseFile(job.fullFileName, stack_size=stack_size, recursion_limit=new_depth)
            except (ParseException, ParseSyntaxException) as err:
                handleParsingException(job, err, parse_errors)
            else:
                handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location)
    else:
        from arelle.PluginUtils import PluginProcessPoolExecutor
        xule_plugin_module = sys.modules["xule"]
        max_workers = None if xule_compile_workers <= 0 else xule_compile_workers
        with PluginProcessPoolExecutor(xule_plugin_module, max_workers) as pool:
            jobFutures = {
                job: pool.submit(parseFile, full_file_name=job.fullFileName, stack_size=stack_size, recursion_limit=new_depth)
                for job in compileJobs
            }
            for job, future in jobFutures.items():
                try:
                    parseRes = future.result()
                except (ParseException, ParseSyntaxException) as err:
                    handleParsingException(job, err, parse_errors)
                else:
                    handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location)

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

def getFileHash(fullFileName):
    with open(fullFileName, 'rb') as xule_file:
        buffer = None
        file_hash_contents = hashlib.sha256()
        while buffer != b'':
            buffer = xule_file.read(4096)
            file_hash_contents.update(buffer)
        return file_hash_contents.hexdigest()

def handleParsingException(job, err, parse_errors):
    error_message = ("Parse error in %s \n"
                     "line: %i col: %i position: %i\n"
                     "%s\n"
                     "%s\n" % (job.fullFileName, err.lineno, err.col, err.loc, err.msg, err.line))
    parse_errors.append(error_message)
    print(error_message)

def handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location):
    # Write the parse results as a json file
    if save_pyparsing_result_location:
        pyparsing_result_file_name = f'{os.path.join(save_pyparsing_result_location, job.fileName)}.pyparsed.json'
        Path(os.path.dirname(pyparsing_result_file_name)).mkdir(parents=True, exist_ok=True)
        with open(pyparsing_result_file_name, 'w') as py_write:
            py_write.write(json.dumps(parseRes, indent=2))

    # Fix parse result for later versions of PyParsing. PyParsing up to version 2.3.0 works fine. After 2.3.0
    # the parse creates an extra layer in the hierarchy of the parse result for tagged, indexed and property
    # expressions.
    fixForPyParsing(parseRes)

    ast_start = datetime.datetime.today()
    print("%s: %s ast start" % (datetime.datetime.isoformat(ast_start), job.fileName))
    ruleSet.add(parseRes, os.path.getmtime(job.fullFileName), job.fileName, job.fileHash)
    ast_end = datetime.datetime.today()
    print("%s: %s ast end. Took %s" % (datetime.datetime.isoformat(ast_end), job.fileName, ast_end - ast_start))
=======
"""XuleParser

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - present XBRL US, Inc.

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
from pyparsing import ParseResults, lineno, ParseException, ParseSyntaxException
from . import XuleRuleSet as xrs
from . import XuleRuleSetBuilder as xrsb
from .XuleParseFile import parseFile
import os
import datetime
import json
import sys
import hashlib
from dataclasses import dataclass
from pathlib import Path

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

@dataclass(frozen=True)
class CompileJob:
    fullFileName: str
    fileName: str
    fileHash: str

def add_location(src, loc, toks):
    #adds location information to the parse results
    '''NEEDS TO BE ADDED TO EACH OF THE ParserElements'''
    toks['char_loc'] = loc
    toks['line'] = lineno(loc, src)
    
    return toks

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

def parseRules(files, dest, compile_type, max_recurse_depth=None, xule_compile_workers=1):

    parse_start = datetime.datetime.today()
    parse_errors = []

    # Set the stack size
    global _options
    save_pyparsing_result_location = getattr(_options, 'xule_compile_save_pyparsing_result_location', None)
    stack_size = getattr(_options, 'xule_stack_size', 8) * 1048576

    #Need to check the recursion limit. 1000 is too small for some rules.
    new_depth = max_recurse_depth or 5500
    orig_recursionlimit = sys.getrecursionlimit()
    if orig_recursionlimit < new_depth:
        sys.setrecursionlimit(new_depth)
    
    ruleSet = xrsb.XuleRuleSetBuilder(compile_type)
    ruleSet.append(dest)
    
    compileJobs = []
    for ruleFile in sorted(files):
        processFile = ruleFile.strip()
        if os.path.isfile(processFile):
            root = os.path.dirname(processFile)
            fileName = os.path.basename(processFile)
            fullFileName = os.path.join(root, fileName)
            fileHash = getFileHash(fullFileName)
            if ruleSet.recompile_all or fileHash != ruleSet.getFileHash(fileName):
                compileJobs.append(CompileJob(fullFileName, fileName, fileHash))
            else:
                ruleSet.markFileKeep(fileName)

        elif os.path.isdir(processFile):
            #Remove an ending slash if there is one
            processFile = processFile[:-1] if processFile.endswith(os.sep) else processFile
            for root, dirs, files in os.walk(ruleFile.strip()):
                for name in sorted(files):
                    if os.path.splitext(name)[1] == ".xule":
                        relpath = os.path.relpath(root, processFile)
                        if relpath == '.': 
                            relpath = ''
                        relativeFileName = os.path.join(relpath, name)
                        fullFileName = os.path.join(processFile, relativeFileName)
                        fileHash = getFileHash(fullFileName)
                        if ruleSet.recompile_all or fileHash != ruleSet.getFileHash(relativeFileName):
                            compileJobs.append(CompileJob(fullFileName, relativeFileName, fileHash))
                        else:
                            ruleSet.markFileKeep(relativeFileName)
        else:
            print("Not a file or directory: %s" % processFile)

    if xule_compile_workers == 1:
        for job in compileJobs:
            try:
                parseRes = parseFile(job.fullFileName, stack_size=stack_size, recursion_limit=new_depth)
            except (ParseException, ParseSyntaxException) as err:
                handleParsingException(job, err, parse_errors)
            else:
                handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location)
    else:
        from arelle.PluginUtils import PluginProcessPoolExecutor
        xule_plugin_module = sys.modules["xule"]
        max_workers = None if xule_compile_workers <= 0 else xule_compile_workers
        with PluginProcessPoolExecutor(xule_plugin_module, max_workers) as pool:
            jobFutures = {
                job: pool.submit(parseFile, full_file_name=job.fullFileName, stack_size=stack_size, recursion_limit=new_depth)
                for job in compileJobs
            }
            for job, future in jobFutures.items():
                try:
                    parseRes = future.result()
                except (ParseException, ParseSyntaxException) as err:
                    handleParsingException(job, err, parse_errors)
                else:
                    handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location)

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

def getFileHash(fullFileName):
    with open(fullFileName, 'rb') as xule_file:
        buffer = None
        file_hash_contents = hashlib.sha256()
        while buffer != b'':
            buffer = xule_file.read(4096)
            file_hash_contents.update(buffer)
        return file_hash_contents.hexdigest()

def handleParsingException(job, err, parse_errors):
    error_message = ("Parse error in %s \n"
                     "line: %i col: %i position: %i\n"
                     "%s\n"
                     "%s\n" % (job.fullFileName, err.lineno, err.col, err.loc, err.msg, err.line))
    parse_errors.append(error_message)
    print(error_message)

def handleParsedFile(parseRes, job, ruleSet, save_pyparsing_result_location):
    # Write the parse results as a json file
    if save_pyparsing_result_location:
        pyparsing_result_file_name = f'{os.path.join(save_pyparsing_result_location, job.fileName)}.pyparsed.json'
        Path(os.path.dirname(pyparsing_result_file_name)).mkdir(parents=True, exist_ok=True)
        with open(pyparsing_result_file_name, 'w') as py_write:
            py_write.write(json.dumps(parseRes, indent=2))

    # Fix parse result for later versions of PyParsing. PyParsing up to version 2.3.0 works fine. After 2.3.0
    # the parse creates an extra layer in the hierarchy of the parse result for tagged, indexed and property
    # expressions.
    fixForPyParsing(parseRes)

    ast_start = datetime.datetime.today()
    print("%s: %s ast start" % (datetime.datetime.isoformat(ast_start), job.fileName))
    ruleSet.add(parseRes, os.path.getmtime(job.fullFileName), job.fileName, job.fileHash)
    ast_end = datetime.datetime.today()
    print("%s: %s ast end. Took %s" % (datetime.datetime.isoformat(ast_end), job.fileName, ast_end - ast_start))
>>>>>>> old/main
