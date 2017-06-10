'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change$
'''
from .XuleParser import parseRules
from .XuleProcessor import process_xule, XuleProcessingError
from .XuleRuleSet import XuleRuleSet, XuleRuleSetError
from .XuleContext import XuleGlobalContext, XuleRuleContext
from .XuleMultiProcessing import run_constant_group, output_message_queue, start_process
from optparse import OptionParser, SUPPRESS_HELP
from multiprocessing import Queue
from threading import Thread
from time import sleep
from arelle import FileSource
from arelle import ModelManager

__version__ = '2.0.' + '$Change$'[9:-2]

def xuleMenuOpen(cntlr, menu):
    pass

def xuleMenuTools(cntlr, menu):
    pass

def xuleCmdOptions(parser):
    # extend command line options to compile rules
    parser.add_option("--xule-compile", 
                      action="store", 
                      dest="xule_compile", 
                      help=_("Xule files to be compiled.  "
                             "This may be a file or directory.  When a directory is provided, all files in the directory will be processed.  "
                             "Multiple file and directory names are separated by a '|' character. "))
    
    parser.add_option("--xule-rule-set",
                      action="store",
                      dest="xule_rule_set",
                      help=_("RULESET to use (this is the directory where compile rules are stored."))

    parser.add_option("--xule-grammar",
                      action="store",
                      dest="xule_grammar",
                      choices=['xule2', 'xule3'],
                      default="xule2",
                      help=_("Grammar version of the Xule rule file. Default is xule2")) 
    
    parser.add_option("--xule-run",
                      action="store_true",
                      dest="xule_run",
                      help=_("Indicates that the rules should be processed."))
    
    parser.add_option("--xule-add-taxonomy",
                      action="store",
                      dest="xule_add_taxonomy",
                      help=_("Add the taxonomy location specified to the rule set."))

    parser.add_option("--xule-taxonomy-entry", 
                      action="store", 
                      dest="xule_taxonomy_entry", 
                      help=_("Taxonomy entry point."))
        
    parser.add_option("--xule-time",
                     action="store",
                     type="float",
                     dest="xule_time",
                     help=_("Output timing information. Supply the minimum threshold in seconds for displaying timing information for a rule."))
    
    parser.add_option("--xule-trace",
                     action="store_true",
                     dest="xule_trace",
                     help=_("Output trace information."))
    
    parser.add_option("--xule-trace-count",
                      action="store",
                      dest="xule_trace_count",
                      help=_("Name of the file to write a trace count."))
    
    parser.add_option("--xule-debug",
                     action="store_true",
                     dest="xule_debug",
                     help=_("Output trace information."))    

    parser.add_option("--xule-debug-table",
                     action="store_true",
                     dest="xule_debug_table",
                     help=_("Output trace information."))    
    
    parser.add_option("--xule-crash",
                     action="store_true",
                     dest="xule_crash",
                     help=_("Output trace information."))
    
    parser.add_option("--xule-pre-calc",
                      action="store_true",
                      dest="xule_pre_calc",
                      help=_("Pre-calc expressions"))
    
    parser.add_option("--xule-filing-list",
                      action="store",
                      dest="xule_filing_list",
                      help=_("File name of file that contains a list of filings to process"))
    
    parser.add_option("--xule-server",
                     action="store",
                     dest="xule_server",
                     help=_("Launch the webserver."))

    parser.add_option("--xule-multi",
                     action="store_true",
                     dest="xule_multi",
                     help=_("Turns on multithreading"))
    
    parser.add_option("--xule-cpu",
                     action="store",
                     dest="xule_cpu",
                     help=_("overrides number of cpus per processing to use"))
    
    parser.add_option("--xule-async",
                     action="store_true",
                     dest="xule_async",
                     help=_("Outputs onscreen output as the filing is being processed"))

    parser.add_option("--xule-numthreads",
                     action="store",
                     dest="xule_numthreads",
                     help=_("Indicates number of concurrents threads will run while the Xule Server is active"))
    
    parser.add_option("--xule-skip",
                      action="store",
                      dest="xule_skip",
                      help=_("List of rules to skip"))
    
    parser.add_option("--xule-no-cache",
                      action="store_true",
                      dest="xule_no_cache",
                      help=_("Turns off local caching for a rule."))
    
    parser.add_option("--xule-precalc-constants",
                      action="store_true",
                      dest="xule_precalc_constants",
                      help=_("Pre-calculate constants that do not depend on the instance."))

    parser.add_option("--xule-include-nils",
                      action="store_true",
                      dest="xule_include_nils",
                      help=_("Indicates that the processor should include nil facts. By default, nils are ignored."))
    
    parser.add_option("--xule-include-dups",
                      action="store_true",
                      dest="xule_include_dups",
                      help=_("Indicates that the processor should include duplicate facts. By default, duplicate facts are ignored."))    

def xuleCmdUtilityRun(cntlr, options, **kwargs):  
    #check option combinations
    parser = OptionParser()
    
    if getattr(options, "xule_filing_list", None) is not None and options.entrypointFile is not None:
        parser.error(_("--xule-filing-list and -f option cannot be used together"))
    
    if getattr(options, "xule_add_taxonomy", None) is not None and (options.xule_taxonomy_entry is None or options.xule_rule_set is None):
            parser.error(_("--xule-rule-set and --xule-taxonomy-entry are required with --xule-add-taxonomy."))

    if  getattr(options, "xule_run", None) is not None and not getattr(options, 'xule_rule_set', None):
            parser.error(_("--xule-rule-set is required with --xule-run."))
    
    if getattr(options, "xule_server", None) is not None and not getattr(options, 'xule_rule_set', None):
            parser.error(_("--xule-rule-set is required with --xule_server."))
            
    if getattr(options, "xule-numthreads", None) == None:
        setattr(options, "xule-numthreads", 1)    

    from os import name
    if getattr(options, "xule_multi", False) and name == 'nt':
            parser.error(_("--xule-multi can't be used in Windows"))    

    if not getattr(options, "xule_multi", False) and getattr(options, "xule_cpu", None) is not None:
            parser.error(_("--xule-cpu can only be used with --xule-multi enabled"))    

    #compile rules
    if getattr(options, "xule_compile", None):
        compile_destination = getattr(options, "xule_rule_set", "xuleRules")        
        parseRules(options.xule_compile.split("|"),compile_destination, grammar=options.xule_grammar)
        
    #add taxonomy to rule set
    if getattr(options, "xule_add_taxonomy", None):
        try:
            rule_set = XuleRuleSet()
            rule_set.open(options.xule_rule_set)
        except XuleRuleSetError:
            raise

        rule_set.addTaxonomy(options.xule_add_taxonomy, options.xule_taxonomy_entry)

        rule_set.close()
        
    if getattr(options, "xule_server", None):
        try:
            rule_set = XuleRuleSet()
            rule_set.open(options.xule_rule_set, False)
        except XuleRuleSetError:
            raise

        # Create global Context
        global_context = XuleGlobalContext(rule_set, cntlr=cntlr, options=options#,
                                           #multi=getattr(options, "xule_multi", False), 
                                           #async=getattr(options, "xule_async", False),
                                           #cpunum=getattr(options, "xule_cpu", None))
                                           )
        #global_context.show_timing = getattr(options, "xule_time", None)
        #global_context.show_debug = getattr(options, "xule_debug", False)
        #global_context.show_debug_table = getattr(options, "xule_debug_table", False)
        #global_context.show_trace = getattr(options, "xule_trace", None)
        #global_context.crash_on_error = getattr(options, "xule_crash", False)

        global_context.message_queue.print("Using %d processors" % (global_context.num_processors)) 

        # Start Output message queue
        if getattr(options, "xule_multi", False):
            t = Thread(target=output_message_queue, args=(global_context,))
            t.start()
        
        #load rules taxonomy
        global_context.message_queue.logging("Loading rules taxonomy")
        global_context.get_rules_dts()        
#        rules_dts = global_context.get_rules_dts()
#        from .XuleProcessor import load_networks
#        load_networks(rules_dts)
         
        global_context.message_queue.logging("Building Constant and Rule Groups")
        global_context.all_constants = rule_set.get_grouped_constants()
        global_context.all_rules = rule_set.get_grouped_rules()        

        
        for g in global_context.all_constants:
            global_context.message_queue.logging("Constants: %s - %d" % (g, len(global_context.all_constants[g])))
        #    for c in global_context.all_constants[g]:
        #        print(" -- %s" % (c))

        for g in global_context.all_rules:
            global_context.message_queue.logging("Rules: %s - %d" % (g, len(global_context.all_rules[g])))
            #for c in global_context.all_rules[g]:
            #    print(" -- %s" % (c))


        # evaluate valid constants (no dependency, rules taxonomy)
        global_context.message_queue.logging("Calculating and Storing Constants")
        run_constant_group(global_context, 'c', 'rtc')

                                   
        # Add precalculated information to the cntlr to pass to XuleServer
        setattr(cntlr, "xule_options", options)
        setattr(cntlr, "rule_set", global_context.rule_set)        
        setattr(cntlr, "constant_list", global_context._constants)
        setattr(cntlr, "all_constants", global_context.all_constants)
        setattr(cntlr, "all_rules", global_context.all_rules)        


        global_context.message_queue.logging("Finished Server Initialization")
        
        # stop message_queue
        global_context.message_queue.stop()
        
        if getattr(options, "xule_multi", False):
            t.join()

    #process filing list
    if getattr(options, "xule_filing_list", None):
        try:
            with open(options.xule_filing_list, "r") as filing_list:
                for line in filing_list:

                    filing = line.strip()
                    print("Processing filing", filing)
                    filing_filesource = FileSource.openFileSource(filing, cntlr)            
                    modelManager = ModelManager.initialize(cntlr)
                    modelXbrl = modelManager.load(filing_filesource) 
                    xuleCmdXbrlLoaded(cntlr, options, modelXbrl)
                    modelXbrl.close()

        except FileNotFoundError:
            print("Filing listing file '%s' is not found" % options.xule_filing_list)
        
def xuleCmdXbrlLoaded(cntlr, options, modelXbrl, entryPoint=None):
    if getattr(options, "xule_run", None):
        try:
            if getattr(options, "xule_multi", True) and \
                getattr(cntlr, "rule_set", None) is not None:
                rule_set =  getattr(cntlr, "rule_set")
            else:
                rule_set = XuleRuleSet()              
                rule_set.open(options.xule_rule_set, False)
        except XuleRuleSetError:
            raise

        if getattr(options, "xule_multi", False):
            start_process(rule_set, 
                         modelXbrl, 
                         cntlr, 
                         options
                         #getattr(options, "xule_time", None), 
                         #getattr(options, "xule_debug", False),
                         #getattr(options, "xule_trace", None),
                         #getattr(options, "xule_trace_count", None),
                         #getattr(options, "xule_crash", False),
                         #multi=getattr(options, "xule_multi", False), 
                         #async=getattr(options, "xule_async", False),
                         #cpunum=getattr(options, "xule_cpu", None))#,
                         #skip=getattr(options, "xule_skip", None))
                         )
        else:
            process_xule(rule_set,
                         modelXbrl, 
                         cntlr, 
                         options,
                         #getattr(options, "xule_time", None), 
                         #getattr(options, "xule_debug", False),
                         #getattr(options, "xule_debug_table", False),
                         #getattr(options, "xule_trace", None),
                         #getattr(options, "xule_trace_count", None),
                         #getattr(options, "xule_crash", False),
                         #getattr(options, "xule_pre_calc", False),
                         #multi=getattr(options, "xule_multi", False), 
                         #async=getattr(options, "xule_async", False),
                         #cpunum=getattr(options, "xule_cpu", None)
                         #skip=getattr(options, "xule_skip", None),
                         #no_cache=getattr(options, "xule_no_cache", False),
                         #precalc_constants=getattr(options, "xule_precalc_constants", False))
                         )
def xuleValidate(val):
    pass

def xuleTestStart(modelTestcaseVariation):        
    pass

def xuleTestXbrlLoaded(modelTestcaseVariation):
    pass

def xuleModelTestVariationReadMe(modelTestcaseVariation):
    pass

def xuleModelTestVariationExpectedResult(modelTestcaseVariation):
    pass

def xuleModelTestVariationExpectedSeverity(modelTestcaseVariation):
    pass

def xuleDialogRssWatchFileChoices(dialog, frame, row, options, cntlr, openFileImage, openDatabaseImage):
    pass

def xuleRssWatchHasWatchAction(rssWatchOptions):
    pass

def xuleRssDoWatchAction(modelXbrl, rssWatchOptions, rssItem):
    pass

__pluginInfo__ = {
    'name': 'Xule Processor',
    'version': '2.0',
    'description': 'This plug-in provides a Xule 2.0 rule compiler and processor.',
    'license': 'Unknown',
    'author': '',
    'copyright': '(c) 2014',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None, 
    'CntlrWinMain.Menu.File.Open': xuleMenuOpen,
    'CntlrWinMain.Menu.Tools': xuleMenuTools,
    'CntlrCmdLine.Options': xuleCmdOptions,
    'CntlrCmdLine.Utility.Run': xuleCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': xuleCmdXbrlLoaded,
    'Validate.Finally': xuleValidate,
    'Testcases.Start': xuleTestStart,
    'TestcaseVariation.Xbrl.Loaded': xuleTestXbrlLoaded,
    'ModelTestcaseVariation.ReadMeFirstUris': xuleModelTestVariationReadMe,
    'ModelTestcaseVariation.ExpectedResult': xuleModelTestVariationExpectedResult,
    'ModelTestcaseVariation.ExpectedSeverity': xuleModelTestVariationExpectedSeverity,
    'DialogRssWatch.FileChoices': xuleDialogRssWatchFileChoices,
    'DialogRssWatch.ValidateChoices': xuleRssWatchHasWatchAction,
    'RssWatch.HasWatchAction': xuleRssWatchHasWatchAction,
    'RssWatch.DoWatchAction': xuleRssDoWatchAction
    }
