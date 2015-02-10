'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved
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
                     action="store_true",
                     dest="xule_time",
                     help=_("Output timing information."))
    
    parser.add_option("--xule-trace",
                     action="store_true",
                     dest="xule_trace",
                     help=_("Output trace information."))
    
    parser.add_option("--xule-debug",
                     action="store_true",
                     dest="xule_debug",
                     help=_("Output trace information."))    
    
    parser.add_option("--xule-crash",
                     action="store_true",
                     dest="xule_crash",
                     help=_("Output trace information."))
    
    parser.add_option("--xule-server",
                     action="store",
                     dest="xule_server",
                     help=_("Launch the webserver."))

    parser.add_option("--xule-multi",
                     action="store_true",
                     dest="xule_multi",
                     help=_("Turns on multithreading"))

def xuleCmdUtilityRun(cntlr, options, **kwargs):  
    #check option combinations
    parser = OptionParser()
    
    if options.xule_add_taxonomy  is not None and (options.xule_taxonomy_entry is None or options.xule_rule_set is None):
            parser.error(_("--xule-rule-set and --xule-taxonomy-entry are required with --xule-add-taxonomy."))

    if  getattr(options, "xule_run", None) and not getattr(options, 'xule_rule_set', None):
            parser.error(_("--xule-rule-set is required with --xule-run."))

    if getattr(options, "xule_server", None) is not None and not getattr(options, 'xule_rule_set', None):
            parser.error(_("--xule-rule-set is required with --webserver."))    

    #compile rules
    if getattr(options, "xule_compile", None):
        compile_destination = getattr(options, "xule_rule_set", "xuleRules")        
        parseRules(options.xule_compile.split("|"),compile_destination)
        
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
            rule_set.open(options.xule_rule_set)
        except XuleRuleSetError:
            raise

        # Create global Context
        global_context = XuleGlobalContext(rule_set, cntlr=cntlr)
        global_context.show_timing = getattr(options, "xule_time", False)
        global_context.show_debug = getattr(options, "xule_debug", False)
        global_context.show_trace = getattr(options, "xule_trace", False)
        global_context.crash_on_error = getattr(options, "xule_crash", False)

        #xule_context = XuleRuleContext(global_context, cat_file_num=0) 

        # Start Output message queue
        t = Thread(target=output_message_queue, args=(global_context,))
        t.start()
        
        #load rules taxonomy        
        global_context.get_rules_dts()
         
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
        setattr(cntlr, "constant_list", global_context.constant_store)
        setattr(cntlr, "all_constants", global_context.all_constants)
        setattr(cntlr, "all_rules", global_context.all_rules)        


        global_context.message_queue.logging("Finished Server Initialization")
        
        # stop message_queue
        global_context.message_queue.stop()
        
     
        
def xuleCmdXbrlLoaded(cntlr, options, modelXbrl):
    
    if getattr(options, "xule_run", None):
        try:
            rule_set = XuleRuleSet()
            rule_set.open(options.xule_rule_set)
        except XuleRuleSetError:
            raise

        if getattr(options, "xule_multi", False):
            start_process(rule_set, 
                         modelXbrl, 
                         cntlr, 
                         getattr(options, "xule_time", False), 
                         getattr(options, "xule_debug", False),
                         getattr(options, "xule_trace", False),
                         getattr(options, "xule_crash", False))
        else:
            process_xule(rule_set,
                         modelXbrl, 
                         cntlr, 
                         getattr(options, "xule_time", False), 
                         getattr(options, "xule_debug", False),
                         getattr(options, "xule_trace", False),
                         getattr(options, "xule_crash", False))


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
    'name': 'Xule 1.0 Processor',
    'version': '1.0',
    'description': 'This plug-in provides a Xule 1.0 rule compiler and processor.',
    'license': 'Unknown',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2014 XBRL US Inc., All rights reserved',
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
