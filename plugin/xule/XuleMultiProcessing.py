"""XuleMultiProcessing

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

$Change: 23204 $
DOCSKIP
"""
import datetime
from .XuleContext import XuleGlobalContext, XuleRuleContext
from .XuleRunTime import XuleProcessingError
from .XuleRunTime import XuleProcessingError, XuleIterationStop, XuleException, XuleBuildTableError
from time import sleep
from multiprocessing import Queue, Process, Lock
from threading import Thread
from queue import Empty
from os import getpid




def start_process(rule_set, model_xbrl, cntlr, options):
    
    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, options=options)
    xule_context = XuleRuleContext(global_context)
    from .XuleProcessor import index_model
    index_model(xule_context)
    
    global_context.message_queue.logging("Processing Filing...")

    # Start message_queue monitoring thread
    t = Thread(target=output_message_queue, args=(global_context,))
    t.name = "Message Queue"
    t.start()

    
    # Start Master Process.  This runs the filing and sends the output to 
    #   the message_queue  This is in a seperate process so the information 
    #   stored on the cntlr is reset each time a filing is run
    
    try:
        master_process(global_context, rule_set)

    except Exception as ex:
        global_context.message_queue.logging("Error occuring while running start_process: %s" % (ex))
    
    finally:
        # Shutdown Message Queue
        global_context.message_queue.stop()
        global_context.message_queue.clear()
        t.join()

    global_context.message_queue.logging("Finished processing Filing...")
 
    
def debug(global_context):
    while True:
        print("*** Master Running ***")
        print("All Rules size: %d; Rules Queue: %d;  Message Queue: %d" %
              (len(global_context.all_rules), global_context.rules_queue.qsize(), global_context.message_queue.size))
        print("rule groups: %s" % (str([group for group in global_context.all_rules])))
        print("All Constants size: %d; Constant Queue: %d" %
              (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
        print("constant groups: %s" % (str([group for group in global_context.all_constants])))
        print("Constants done? %s" % (str(global_context.constants_done)))
        if len(global_context.all_rules) <=0 and global_context.rules_queue.qsize() <= 0:
            break
        #sleep(5)
 

def output_message_queue(global_context):
    c = True
    while c: 
        c = global_context.message_queue.loopoutput()

                 
def master_process(global_context, rule_set):
    
    if getattr(global_context.options, "xule_debug", False):      
        global_context.message_queue.logging("%s: Starting Master Process; pid: %d" % (datetime.datetime.now(),getpid()))

    try:
        setattr(global_context, "all_constants", global_context.cntlr.all_constants)
        delattr(global_context.cntlr, "all_constants")
    except AttributeError:
        setattr(global_context, "all_constants", rule_set.get_grouped_constants())
    
    try:
        setattr(global_context, "all_rules", global_context.cntlr.all_rules)
        delattr(global_context.cntlr, "all_rules")
    except AttributeError:
        setattr(global_context, "all_rules", rule_set.get_grouped_rules())
        
    try:
        global_context._constants = global_context.cntlr.constant_list
    except AttributeError:
        pass
    
    
    # Setting attributes needed for this run only
    setattr(global_context, "shutdown_queue", Queue())
    setattr(global_context, "constants_done", False)
    setattr(global_context, "stopped_constants", False)
#    setattr(global_context, "stop_watch", 0)


    ''' Debugging section
    print("All Constants size: %d; Constant Queue: %d" % 
          (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
    print("constant groups: %s" % (str([group for group in global_context.all_constants])))

    #run_constant_group(global_context, 'frc','rfrc')

    print("All Constants size: %d; Constant Queue: %d" % 
          (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
    print("constant groups: %s" % (str([group for group in global_context.all_constants])))
    
    print("starting all")
    '''
    
    # Load rules into queue to start calculations
#    load_rules_queue(global_context, 'r', number=(1000 * global_context.num_processors))
  
    ''' Debugging section
    while True:
        print("All Rules size: %d; Rules Queue: %d; Message Queue: %d" % 
              (len(global_context.all_rules), global_context.rules_queue.qsize(), global_context.message_queue.size))
        sleep(5)
    '''

    # Start the process to monitor the sub_process threads and the queues
    watch = Thread(target=watch_processes, args=(global_context,))
    watch.name = "Process Watcher"
    watch.start()
 
    ''' Debug Area
 
    # The following is for watching various queues and lists while the process is running
    t_debug = Thread(target=debug, args=(global_context,))
    t_debug.name = "Debug Thread"
    t_debug.start()
 
    '''
    
    '''hold thread'''
  
    watch.join()
    
    
    if getattr(global_context.options, "xule_debug", False):   
        print("*** Master Running ***")
        print("All Rules size: %d; Rules Queue: %d; Message Queue: %d" % 
              (len(global_context.all_rules), global_context.rules_queue.qsize(), global_context.message_queue.size))
        print("rule groups: %s" % (str([group for group in global_context.all_rules])))
        print("All Constants size: %d; Constant Queue: %d" % 
              (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
        print("constant groups: %s" % (str([group for group in global_context.all_constants])))
        global_context.message_queue.logging("%s: Stopping Master Process; pid: %d" % (datetime.datetime.now(), getpid()))
        sleep(5)
        
    #print out times queues
    if getattr(global_context.options, "xule_time", None) is not None:
        constants_slow = []
        constants_time = datetime.timedelta()
        rules_slow = []
        rules_time = datetime.timedelta()
        for (ttype, name, timing) in global_context.times:
            if ttype == 'constant':
                constants_time = constants_time + timing
                if timing.total_seconds() > 0.5:
                    constants_slow.append((name, timing))
            if ttype == 'rule':
                rules_time = rules_time + timing
                if timing.total_seconds() > 0.5:
                    rules_slow.append((name, timing))

        with open('data.txt', 'w') as f:
            global_context.message_queue.logging("Total Constant Calculation Time: %s seconds" % (constants_time.total_seconds()))
            global_context.message_queue.logging("Number of slow constants: %d" % (len(constants_slow)))
            for (name, timing) in sorted(constants_slow, key=lambda t:t[1]):
                global_context.message_queue.logging("Constant %s: %s" % (name, timing.total_seconds()))
            global_context.message_queue.logging("Total Rules Calculation Time: %s seconds" % (rules_time.total_seconds()))
            global_context.message_queue.logging("Number of slow rules: %d" % (len(rules_slow)))
            for (name, timing) in sorted(rules_slow, key=lambda t:t[1]):
                global_context.message_queue.logging("Rule %s: %s" % (name, timing.total_seconds()))
        
            # Write debug information to a file   
            f.write("Total rules run: %d\n" % (len(global_context.times)))
            f.write("Total Constant Calculation Time: %s seconds\n" % (constants_time.total_seconds()))
            f.write("Number of slow constants: %d\n" % (len(constants_slow)))
            for (name, timing) in sorted(constants_slow, key=lambda t:t[1]):
                f.write("Constant %s: %s\n" % (name, timing.total_seconds()))
            f.write("Total Rules Calculation Time: %s seconds\n" % (rules_time.total_seconds()))
            f.write("Number of slow rules: %d\n" % (len(rules_slow)))
            for (name, timing) in sorted(rules_slow, key=lambda t:t[1]):
                f.write("Rule %s: %s\n" % (name, timing.total_seconds()))




# Thread Processes

def rules_process(name, global_context, cq):
    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging("**************")
        global_context.message_queue.logging("** %s: %s: Start rule process" % (name, getpid()))
        global_context.message_queue.logging("Rules queue size: %d" % (global_context.rules_queue.qsize()))
        global_context.message_queue.logging("**************")
        sleep(5)
        rules_work = []

    while True:
        try:
            rule_name = global_context.rules_queue.get(False)
        except Empty:
            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.logging("**************")
                global_context.message_queue.logging("%s: %s: Empty stopping rule process" % (name, getpid()))
                global_context.message_queue.logging("Rules queue size: %d" % (global_context.rules_queue.qsize()))
                global_context.message_queue.logging("**************")
                sleep(5)
            break
            # makes sure command queue is empty when shutting down
            try:
                command = cq.get(False)
            except Empty:
                pass

        try:
            if rule_name == "":
                # skip rule if there's no name
                continue
            if getattr(global_context.options, "xule_debug", False):
                rules_work.append(rule_name)
            if getattr(global_context.options, "xule_time", None) is not None:
                rule_start = datetime.datetime.today()
  
            cat_rule = global_context.catalog['rules'][rule_name]
            rule = global_context.rule_set.getItem(cat_rule)
            file_num = cat_rule['file']
            xule_context = XuleRuleContext(global_context,
                                           rule_name,
                                           file_num)

            from .XuleProcessor import evaluate
            xule_context.iteration_table.add_table(rule['node_id'], xule_context.get_processing_id(rule['node_id']))
            evaluate(rule, xule_context)  

        except UnboundLocalError:
            continue
 
        except (XuleProcessingError, XuleBuildTableError) as e:
            if getattr(global_context.options, "xule_crash", False):
                raise
            else:
                xule_context.global_context.message_queue.error("xule:error", str(e))

        except XuleIterationStop:
            pass
        
        except Exception as e:
            if getattr(global_context.options, "xule_crash", False):
                raise
            else:
                xule_context.global_context.message_queue.error("xule:error","rule %s: %s" % (rule_name, str(e)))        
        
        if getattr(global_context.options, "xule_time", None) is not None:
            rule_end = datetime.datetime.today()
            global_context.times.append(('rule', rule_name, rule_end - rule_start))

        # clear rule name to make sure it isn't run multiple times
        rule_name = ""
    
        try:
            command = cq.get(False)
            # Stop rules_process if commanded to stop
            if command == "STOP":
                if getattr(global_context.options, "xule_debug", False):
                    global_context.message_queue.logging("** %s: Command stopping process: %s" % (name, str(command)))
                break
        except Empty:
            pass

    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging("%s: Stopping Rules Process; pid: %d" % (datetime.datetime.now(), getpid()))
        sleep(5)
        

def watch_processes(global_context):
    ''' watch constant and rules queues and load them with new groups 
            when appropriate
        watch running processes, shut them down gracefully if they've ended
            and restart them if there's more processing to do 
    '''
    #global_context.message_queue.logging("%s: Starting Watch Process; pid: %d" % (datetime.datetime.now(), getpid()))
    # Initializing variables
    sub_processes = {}
    constants_running = False
    # If constants need/are being run there is one less processor available to run rules
    processor_adjustment = 0
    
    while True:
        if getattr(global_context.options, "xule_debug", False):
            global_context.message_queue.logging("**************")
            global_context.message_queue.logging("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
                  (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
            global_context.message_queue.logging("Rule Groups: %s" % (str([group for group in global_context.all_rules])))
            global_context.message_queue.logging("All Constants size: %d; Constant Queue: %s" % 
                  (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
            global_context.message_queue.logging("Constant Groups: %s" % (str([group for group in global_context.all_constants])))
            global_context.message_queue.logging("Num Processors: %d; Num Processes - %d" % (global_context.num_processors, len(sub_processes)))
            global_context.message_queue.logging("**************")
            sleep(5)



        ''' rule start process here'''
        # if process is dead join process and remove from tracking queue
        del_process = []
        for num in sub_processes:
            if not sub_processes[num]['p'].is_alive():
                del_process.append(num)
        for num in del_process:
            del sub_processes[num]


        # If number of tracked rules processes is less than the number of processors and there's
        #   work to be done, start a rules process
        if len(sub_processes) < (global_context.num_processors + processor_adjustment) and \
            not global_context.rules_queue.empty():

            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.logging("******Adding rule processors********")
                global_context.message_queue.logging("Num Processors: %d; Sub Processes: %d" % (global_context.num_processors, len(sub_processes)))
                sleep(5)
            
            for num in range(0, global_context.num_processors - len(sub_processes) + processor_adjustment):
                # make sure there's no index collision
                thisnum = num
                while thisnum in sub_processes.keys():
                    thisnum = thisnum + 1
 
                process_name = "Sub-Process %d" % (thisnum)
                cq = Queue()
                p = Process(target=rules_process, args=(process_name, global_context, cq))
                p.name = process_name

                c = 0
                while True:
                    try:
                        c += 1
                        if c > 3:
                            global_context.message_queue.logging("ERROR: Tried running filing 3 times: %s" % (process_name))
                            break 
                        p.start()
                        break
                    except Exception as ex:
                        global_context.message_queue.logging("ERROR: Problem while starting rules_process thread: %s" % (process_name))
                        
                sub_processes[thisnum] = { 'cq': cq,
                                           'p' : p
                                         }
                #global_context.stop_watch = global_context.stop_watch + 1
                if getattr(global_context.options, "xule_debug", False):
                   # global_context.message_queue.logging("adding stop_watch: %d" % (global_context.stop_watch))
                    global_context.message_queue.logging("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
                          (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
                    global_context.message_queue.logging("rule groups: %s" % (str([group for group in global_context.all_rules])))
                    global_context.message_queue.logging("All Constants size: %d; Constant Queue: %d" % 
                          (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
                    global_context.message_queue.logging("constant groups: %s" % (str([group for group in global_context.all_constants])))       


        if len(global_context.all_constants) > 0: #and \
            #global_context.calc_constants_queue.empty():
            if 'c' in global_context.all_constants:
                load_constant_queue(global_context, 'c')
            if 'frc' in global_context.all_constants:
                load_constant_queue(global_context, 'frc')
            if 'rtc' in global_context.all_constants:
                load_constant_queue(global_context, 'rtc')
            #if 'rtc' in global_context.all_constants and \
            #    getattr(global_context.cntlr, "base_taxonomy", None) is not None:
            #    load_constant_queue(global_context, 'rtc')
            if 'rfrc' in global_context.all_constants:
                load_constant_queue(global_context, 'rtc', 'rfrc')
            #if 'rfrc' in global_context.all_constants and \
            #    getattr(global_context.cntlr, "base_taxonomy", None) is not None:
            #    load_constant_queue(global_context, 'rtc', 'rfrc')
 
            # Launch thread to calculate constants
            if not constants_running:
                calc_constants = Thread(target=process_constants, args=(global_context,))
                calc_constants.name = "Constant Calculator"
                calc_constants.start()
                constants_running = True
                global_context.constants_done = False
                processor_adjustment = -1
            else:
                processor_adjustment = 0
        
        else:
            if constants_running:
                if not global_context.stopped_constants:
                    global_context.stopped_constants = True
                    global_context.calc_constants_queue.put(("STOP", "STOP"))
                if global_context.constants_done:
                    # Send kill commands to any running threads
                    for num in sub_processes:
                        sub_processes[num]['cq'].put("STOP")
                        
                    constants_running = False
                    processor_adjustment = 0
            else:
                global_context.constants_done = True
             
        # Load Rules
        if len(global_context.all_rules) > 0:
            load_rules_queue(global_context, 'r')
            #if getattr(global_context.cntlr, "base_taxonomy", None) is not None:
            #    load_rules_queue(global_context, 'rtr', 'rtfcr')

            if global_context.constants_done:
                #load_rules_queue(global_context, 'fcr')
                load_rules_queue(global_context, 'fcr', 'rtr', 'rtfcr', 'rtcr', 'alldepr')
            #if global_context.constants_done and \
            #    getattr(global_context.cntlr, "base_taxonomy", None) is not None:
            #    load_rules_queue(global_context, 'rtcr', 'alldepr')
            # provides delay to allow rules to show up in queue
            #sleep(1)

        if not constants_running and len(global_context.all_rules) <=0 \
            and len(sub_processes) <= 0 and global_context.rules_queue.qsize() <= 0:
            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.logging("stopping watch_process")
            break       
                    
    if getattr(global_context, "xule_debug", False):
        global_context.message_queue.logging("%s: Stopping Watch Process; pid: %d" % (datetime.datetime.now(), getpid()))

def process_constants(global_context):
    ''' send stop to kill thread '''
    c_name = "None"
    
    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging("%s: Starting Constant Process; pid: %d" % (datetime.datetime.now(), getpid()))
        sleep(5)

    while True:
        try:
            const_type, constant_name = global_context.calc_constants_queue.get()
            c_name = constant_name

            if constant_name == "STOP":
                break;

            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.logging("Starting constant: %s" % (constant_name)) 
                sleep(1)

            if getattr(global_context.options, "xule_time", None) is not None:
               const_start = datetime.datetime.today() 
               
            cat_const = global_context.catalog['constants'].get(constant_name)
            ast_const = global_context.rule_set.getItem(cat_const)
            node_id = ast_const['node_id']
            file_num = global_context.catalog['constants'][constant_name]['file']
            xule_context = XuleRuleContext(global_context,
                                           constant_name,
                                           file_num)    
            if constant_name not in xule_context._BUILTIN_CONSTANTS:
                var_info = {"name": constant_name,
                            "tagged": 'tagged' in ast_const,
                            "type": xule_context._VAR_TYPE_CONSTANT,
                            "expr": ast_const,
                            "calculated": False,
                            }
                from .XuleProcessor import calc_constant
                const_values = calc_constant(var_info, xule_context)
                global_context._constants[node_id] = var_info

            if getattr(global_context.options, "xule_time", None) is not None:
                const_end = datetime.datetime.today()
                global_context.times.append(('constant', constant_name, const_end - const_start))
        except:
            global_context.message_queue.logging("error while processing constant %s" % (c_name))

    global_context.constants_done = True

    '''
    # Send kill commands to any running threads
    for num in sub_processes:
        sub_processes[num]['cq'].put("STOP")
        
    # Increases the amount of processes running rules
    global_context.num_processors = global_context.num_processors + 1
    '''
    
    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging("***** Stopping Constant Thread ******")
        #sleep(5)


# Helper Functions

def load_rules_queue(context, *args, number=None):
    ''' args are the catergories of rules that should be loaed into the queue'''
    ''' number controls the amount that's loaded during this call'''
    num = 0
    #print("begin load: %s - %s" % (str(number), str(args)))
    run_only_rules = getattr(context.options, "xule_run_only", None).split(",") if getattr(
        context.options, "xule_run_only", None) is not None else None
    
    for rules_type in args:
        if rules_type in context.all_rules:
            #print("working on: %s: %d" % (rules_type, len(context.all_rules[rules_type])))
            if number is None:
                for rule in context.all_rules[rules_type]: 
                    if not (run_only_rules is None or rule in run_only_rules):
                        continue
                    num +=1
                    context.rules_queue.put(rule)
                del context.all_rules[rules_type]
            else:
                number = number if len(context.all_rules[rules_type]) >= number \
                    else len(context.all_rules[rules_type])
                for num in range(number):
                    num += 1
                    rule = context.all_rules[rules_type].pop()
                    if not (run_only_rules is None or rule in run_only_rules):
                        continue
                    context.rules_queue.put(rule)
            
            
def load_constant_queue(context, *args):
    if getattr(context.options, "xule_debug", False):
        for const_type in args:
            context.message_queue.logging("Loading Constant group: %s" % (const_type))
    
    delete_constants = []
    for const_type in args:
        if const_type in context.all_constants:
            for constant in context.all_constants[const_type]:
                context.calc_constants_queue.put((const_type, constant))
            delete_constants.append(const_type)
    for del_const_type in delete_constants:
        del context.all_constants[del_const_type]
        

def run_constant_group(global_context, *args):
    """ list is dictionary that needs to be run, i.e. all_constants['c'] """

    
    for const_type in args:    
        global_context.message_queue.logging("Starting Constant Group: %s" % (const_type))
        if getattr(global_context.options, "xule_time", None) is not None:
            times = []
            total_start = datetime.datetime.today()

        if const_type in global_context.all_constants.keys():
            for constant_name in global_context.all_constants[const_type]:
                if getattr(global_context.options, "xule_debug", False):
                    global_context.message_queue.logging("Processing %s" % (constant_name))
                if getattr(global_context.options, "xule_time", None) is not None:
                   const_start = datetime.datetime.today()       

                cat_const = global_context.catalog['constants'].get(constant_name)
                ast_const = global_context.rule_set.getItem(cat_const)
                node_id = ast_const['node_id']
                file_num = global_context.catalog['constants'][constant_name]['file']
                xule_context = XuleRuleContext(global_context,
                                               constant_name,
                                               file_num)    
                var_info = {"name": constant_name,
                            "tagged": 'tagged' in ast_const,
                            "type": xule_context._VAR_TYPE_CONSTANT,
                            "expr": ast_const,
                            "calculated": False,
                            }
                from .XuleProcessor import calc_constant
                const_values = calc_constant(var_info, xule_context)
                global_context._constants[node_id] = var_info                
           
                '''
                try:
                    from .XuleProcessor import evaluate            
                    const_value = evaluate(const_info["expr"], xule_context)
                    xule_context.var_add_value(constant_name, const_value)
                except:
                    global_context.message_queue.logging("Error while processing: %s" % (constant_name))
                '''  
                if getattr(global_context.options, "xule_time", None) is not None:  
                    const_end = datetime.datetime.today()
                    global_context.times.append(('constant', constant_name, const_end - const_start))
             
            # remove section from constant needed to be calculated    
            del global_context.all_constants[const_type]
