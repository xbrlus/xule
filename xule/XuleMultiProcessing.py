import datetime
#from .XuleProcessor import index_model, assign_severity
from .XuleContext import XuleGlobalContext, XuleRuleContext
from .XuleRunTime import XuleProcessingError
from time import sleep
from multiprocessing import Queue, Process, Lock
from threading import Thread
from queue import Empty


def start_process(rule_set, model_xbrl, cntlr, show_timing=False, show_debug=False, show_trace=False, crash_on_error=False,
                  multi=False, async=False, cpunum=None):
    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, 
                                       multi=multi, async=async,
                                       cpunum=cpunum) 
    global_context.show_timing = show_timing
    global_context.show_debug = show_debug
    global_context.show_trace = show_trace
    global_context.crash_on_error = crash_on_error
    
    xule_context = XuleRuleContext(global_context)
    from .XuleProcessor import index_model
    global_context.fact_index = index_model(xule_context)

    global_context.message_queue.logging("Processing Filing...")

    # Start message_queue monitoring thread
    t = Thread(target=output_message_queue, args=(global_context,))
    t.name = "Message Queue"
    t.start()

    
    # Start Master Process.  This runs the filing and sends the output to 
    #   the message_queue  This is in a seperate process so the information 
    #   stored on the cntlr is reset each time a filing is run
    master = Process(target=master_process, args=(global_context, rule_set,))
    master.name = "Master Process"
    master.start()
    
    # Wait until filing as been evaluated
    master.join()
    
    # Shutdown Message Queue
    global_context.message_queue.stop()

    global_context.message_queue.clear()
    

def output_message_queue(global_context):
    c = True
    while c: 
        c = global_context.message_queue.loopoutput()

                 
def master_process(global_context, rule_set):
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
        global_context.constant_store = global_context.cntlr.constant_list
    except AttributeError:
        pass
    
    setattr(global_context, "shutdown_queue", Queue())
    setattr(global_context, "stop_watch", 0)


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
    load_rules_queue(global_context, 'r', number=(1000 * global_context.num_processors))
    
    ''' Debugging section
    print("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
          (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
    sleep(5)
    '''

    # Start initial queues based on the number of processes indicated    
    sub_processes = {}
    global_context.message_queue.print("numproc: %d" % (global_context.num_processors))
    for num in range(global_context.num_processors):
        cq = Queue()
        p = Process(target=rules_process, args=(str(num), global_context, cq))
        p.name = "Sub-Process %d" % (num)
        p.start()
        #print("masterProcess - Process: %d, pid: %d" % (num, p.pid))
        sub_processes[num] = { 'cq': cq,
                                 'p' : p
                               }

    # Start the process to monitor the sub_process threads and the queues
    watch = Thread(target=watch_processes, args=(global_context, sub_processes,))
    watch.name = "Process Watcher"
    watch.start()
 
    ''' Debug Area
    for const_type in xule_context.all_constants:
        print("Constant type: %s: %d" % (const_type, len(xule_context.all_constants[const_type])))
    print("C")
    for rule_type in xule_context.all_rules:
        print("Rule type: %s: %d" % (rule_type, len(xule_context.all_rules[rule_type])))
    print("D")
    '''
    
    # Launch thread to calculate constants
    calc_constants = Thread(target=process_constants, args=(global_context, sub_processes,))
    calc_constants.name = "Constant Calculator"
    calc_constants.start()
      

    '''hold thread'''
  
    checks = global_context.num_processors + 1
    for num in range(checks):
        global_context.shutdown_queue.get()

    # Cleans up subprocesses
    for num in sub_processes:
        print("Before Joining %s process(pid %d" % (num, sub_processes[num]['p'].pid))
        #while sub_processes[num]['p'].is_alive():
        #    pass
        sub_processes[num]['p'].join()
        print("After Joining %s process(pid %d" % (num, sub_processes[num]['p'].pid))
        
    if global_context.show_debug:
        print("*** Master Running ***")
        print("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
              (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
        print("rule groups: %s" % (str([group for group in global_context.all_rules])))
        print("All Constants size: %d; Constant Queue: %d" % 
              (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
        print("constant groups: %s" % (str([group for group in global_context.all_constants])))

        
    #print out times queues
    if global_context.show_timing:
        constants_slow = []
        constants_time = datetime.timedelta()
        rules_slow = []
        rules_time = datetime.timedelta()
        for (ttype, name, timing) in global_context.times:
            if ttype == 'constant':
                constants_time = constants_time + timing
                if timing.total_seconds() > 1:
                    constants_slow.append((name, timing))
            if ttype == 'rule':
                rules_time = rules_time + timing
                if timing.total_seconds() > 1:
                    rules_slow.append((name, timing))

        with open('data.txt', 'w') as f:
            global_context.message_queue.logging("Total Constant Calculation Time: %s seconds" % (constants_time.total_seconds()))
            global_context.message_queue.logging("Number of slow constants: %d" % (len(constants_slow)))
            for (name, timing) in constants_slow:
                global_context.message_queue.logging("Constant %s: %s" % (name, timing.total_seconds()))
            global_context.message_queue.logging("Total Rules Calculation Time: %s seconds" % (rules_time.total_seconds()))
            global_context.message_queue.logging("Number of slow rules: %d" % (len(rules_slow)))
            for (name, timing) in rules_slow:
                global_context.message_queue.logging("Rule %s: %s" % (name, timing.total_seconds()))
        
            # Write debug information to a file   
            f.write("Total Constant Calculation Time: %s seconds\n" % (constants_time.total_seconds()))
            f.write("Number of slow constants: %d\n" % (len(constants_slow)))
            for (name, timing) in constants_slow:
                f.write("Constant %s: %s\n" % (name, timing.total_seconds()))
            f.write("Total Rules Calculation Time: %s seconds\n" % (rules_time.total_seconds()))
            f.write("Number of slow rules: %d\n" % (len(rules_slow)))
            for (name, timing) in rules_slow:
                f.write("Rule %s: %s\n" % (name, timing.total_seconds()))
            



# Thread Processes

def rules_process(name, global_context, cq):
    if global_context.show_debug:
        global_context.message_queue.logging("** %s: Start rule process" % (name))
    while True:
        #print("** %s: Start loop" % (name))
        #print("Number in queue: %d" % (global_context.rules_queue.qsize()))
        try:
            rule_name = global_context.rules_queue.get(False)
        except Empty:
            if global_context.show_debug:
                global_context.message_queue.logging("** %s: Empty stopping rule process" % (name))
                global_context.message_queue.logging("*rules queue size: %d" % (global_context.rules_queue.qsize()))
            if len(global_context.all_rules) <= 0 and global_context.rules_queue.qsize() <= 0:
                global_context.shutdown_queue.put("stop")
                #print("%s: Entering Shutdown Queue" % (name))
                break
            else:
                if global_context.show_debug:
                    global_context.message_queue.logging("** %s: Aborting rule process stop" % (name))
        try:
            command = cq.get(False)
            if command == "STOP":
                if global_context.show_debug:
                    global_context.message_queue.logging("** %s: Command stopping process: %s" % (name, str(command)))
                break
        except Empty:
            pass

        try:
            if global_context.show_timing:
                rule_start = datetime.datetime.today()
                
            cat_rule = global_context.catalog['rules'][rule_name]
            file_num = cat_rule['file']
            xule_context = XuleRuleContext(global_context,
                                           rule_name,
                                           file_num)            
            # create xule_context now
            rule = global_context.rule_set.getItem(cat_rule)
            from .XuleProcessor import evaluate, assign_severity
            assign_severity(rule, xule_context)
            evaluate(rule, xule_context)
        
        except XuleProcessingError as e:
            global_context.message_queue.error("xule:error", str(e))
        
        except Exception as e:
            if global_context.crash_on_error:
                raise
            else:
                global_context.message_queue.error("xule:error","rule %s: %s" % (rule_name, str(e)))        

        if global_context.show_timing:
            rule_end = datetime.datetime.today()
            global_context.times.append(('rule', rule_name, rule_end - rule_start))
    
    if global_context.show_debug:
        global_context.message_queue.logging("** %s: Stopping rule process" % (name))

def watch_processes(global_context, sub_processes):
    ''' watch constant and rules queues and load them with new groups 
            when appropriate
        watch running processes, shut them down gracefully if they've ended
            and restart them if there's more processing to do 
    '''
    while True:
        if global_context.show_debug:
            global_context.message_queue.logging("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
                  (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
            global_context.message_queue.logging("rule groups: %s" % (str([group for group in global_context.all_rules])))
            global_context.message_queue.logging("All Constants size: %d; Constant Queue: %d" % 
                  (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
            global_context.message_queue.logging("constant groups: %s" % (str([group for group in global_context.all_constants])))
            global_context.message_queue.logging("Stop Watch: %d; Num Processes - %d" % (global_context.stop_watch, global_context.num_processors))
            sleep(5)

        if global_context.constants_done and global_context.stop_watch >= global_context.num_processors:
            #global_context.message_queue.logging("stopping watch_process")
            break

        #global_context.message_queue.logging("watch-process- constant groups: %s" % (str([group for group in global_context.all_constants])))

        if len(global_context.all_constants) > 0: #and \
            #global_context.calc_constants_queue.empty():
            if 'c' in global_context.all_constants:
                load_constant_queue(global_context, 'c')
            if 'frc' in global_context.all_constants:
                load_constant_queue(global_context, 'frc')
            if 'rtc' in global_context.all_constants and \
                getattr(global_context.cntlr, "base_taxonomy", None) is not None:
                load_constant_queue(global_context, 'rtc')
            if 'rfrc' in global_context.all_constants and \
                getattr(global_context.cntlr, "base_taxonomy", None) is not None:
                load_constant_queue(global_context, 'rtc', 'rfrc')
        else:
            if not global_context.stopped_constants:
                global_context.stopped_constants = True
                global_context.calc_constants_queue.put(("STOP", "STOP"))
   
        # Rules
        if len(global_context.all_rules) > 0:
            load_rules_queue(global_context, 'r')
            if global_context.constants_done:
                load_rules_queue(global_context, 'fcr')
            if getattr(global_context.cntlr, "base_taxonomy", None) is not None:
                load_rules_queue(global_context, 'rtr', 'rtfcr')
            if global_context.constants_done and \
                getattr(global_context.cntlr, "base_taxonomy", None) is not None:
                load_rules_queue(global_context, 'rtcr', 'alldepr')

        
        # if process is dead join process and remove from tracking queue
        del_process = []
        for num in sub_processes:
            if not sub_processes[num]['p'].is_alive():
                del_process.append(num)
        for i in del_process:
            del sub_processes[i]

        if len(sub_processes) < global_context.num_processors and \
            not global_context.rules_queue.empty():
            for num in range(0, global_context.num_processors - len(sub_processes)):
                # make sure there's no index collision
                thisnum = num
                while thisnum in sub_processes.keys():
                    thisnum = thisnum + 1
 
                cq = Queue()
                p = Process(target=rules_process, args=(str(thisnum), global_context, cq))
                p.name = "Sub-Process %d" % (thisnum)
                p.start()
                #print("watchProcess - Process: %d, pid: %d" % (thisnum, p.pid))
                sub_processes[thisnum] = { 'cq': cq,
                                           'p' : p
                                         }
                global_context.stop_watch = global_context.stop_watch + 1
                if global_context.show_debug:
                    global_context.message_queue.logging("adding stop_watch: %d" % (global_context.stop_watch))
    
                    global_context.message_queue.logging("All Rules size: %d; Rules Queue: %d; Sub_processes: %d; Message Queue: %d" % 
                          (len(global_context.all_rules), global_context.rules_queue.qsize(), len(sub_processes), global_context.message_queue.size))
                    global_context.message_queue.logging("rule groups: %s" % (str([group for group in global_context.all_rules])))
                    global_context.message_queue.logging("All Constants size: %d; Constant Queue: %d" % 
                          (len(global_context.all_constants), global_context.calc_constants_queue.qsize()))
                    global_context.message_queue.logging("constant groups: %s" % (str([group for group in global_context.all_constants])))       
                

def process_constants(global_context, sub_processes):
    ''' send stop to kill thread '''
    c_name = "None"
    while True:
        try:
            const_type, constant_name = global_context.calc_constants_queue.get()
            c_name = constant_name

            if constant_name == "STOP":
                break;

            if global_context.show_debug:     
                global_context.message_queue.logging("Starting constant: %s" % (constant_name)) 

            if global_context.show_timing:
               const_start = datetime.datetime.today() 

            file_num = global_context.catalog['constants'][constant_name]['file']
            xule_context = XuleRuleContext(global_context,
                                           constant_name,
                                           file_num)            
            const_info = xule_context.find_var(constant_name)
            from .XuleProcessor import evaluate            
            const_value = evaluate(const_info["expr"], xule_context)
            xule_context.var_add_value(constant_name, const_value)
 
            if global_context.show_timing:
                const_end = datetime.datetime.today()
                global_context.times.append(('constant', constant_name, const_end - const_start))
        except:
            global_context.message_queue.logging("error while processing constant %s" % (c_name))

    global_context.constants_done = True

    # Send kill commands to any running threads
    for num in sub_processes:
        sub_processes[num]['cq'].put("STOP")
        
    # Increases the amount of processes running rules
    global_context.num_processors = global_context.num_processors + 1
    
    if global_context.show_debug:
        global_context.message_queue.logging("***** Stopping Constant Thread ******")


# Helper Functions

def load_rules_queue(context, *args, number=None):
    ''' args are the catergories of rules that should be loaed into the queue'''
    ''' number controls the amount that's loaded during this call'''

    for rules_type in args:
        if rules_type in context.all_rules:
            if number is None:
                for rule in context.all_rules[rules_type]:
                    context.rules_queue.put(rule)
                del context.all_rules[rules_type]
            else:
                number = number if len(context.all_rules[rules_type]) >= number \
                    else len(context.all_rules[rules_type])
                for num in range(number):
                    context.rules_queue.put(context.all_rules[rules_type].pop())
                    
                
            
            
def load_constant_queue(global_context, *args):
    for const_type in args:
        if const_type in global_context.all_constants:
            for constant in global_context.all_constants[const_type]:
                global_context.calc_constants_queue.put((const_type, constant))
            del global_context.all_constants[const_type]

def run_constant_group(global_context, *args):
    """ list is dictionary that needs to be run, i.e. all_constants['c'] """

    
    for const_type in args:    
        global_context.message_queue.logging("Starting Constant Group: %s" % (const_type))
        if global_context.show_timing:
            times = []
            total_start = datetime.datetime.today()

        if const_type in global_context.all_constants.keys():
            for constant_name in global_context.all_constants[const_type]:
                if global_context.show_debug:
                    global_context.message_queue.logging("Processing %s" % (constant_name))
                if global_context.show_timing:
                   const_start = datetime.datetime.today()       
    
                file_num = global_context.catalog['constants'][constant_name]['file']
                xule_context = XuleRuleContext(global_context,
                                               constant_name,
                                               file_num)            
                const_info = xule_context.find_var(constant_name)
                try:
                    from .XuleProcessor import evaluate            
                    const_value = evaluate(const_info["expr"], xule_context)
                    xule_context.var_add_value(constant_name, const_value)
                except:
                    global_context.message_queue.logging("Error while processing: %s" % (constant_name))
                if global_context.show_timing:
                    const_end = datetime.datetime.today()
                    global_context.times.append(('constant', constant_name, const_end - const_start))
             
            # remove section from constant needed to be calculated    
            del global_context.all_constants[const_type]


