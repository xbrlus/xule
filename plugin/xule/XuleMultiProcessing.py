"""XuleMultiProcessing

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
import datetime
from math import floor
from .XuleContext import XuleGlobalContext, XuleRuleContext
from .XuleRunTime import XuleProcessingError
from .XuleRunTime import XuleProcessingError, XuleIterationStop, XuleException, XuleBuildTableError
from time import sleep
from multiprocessing import Queue, Process
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from queue import Empty
from os import getpid

# Minimum number of rules that must transitively depend on an 'frc' or 'rfrc'
# constant for it to be pre-computed before rules start.  Constants at or below
# this threshold are computed lazily the first time a rule needs them.
# Change this value to tune the pre-computation trade-off:
#   0  = pre-compute all frc/rfrc constants (old behaviour)
#   50 = only pre-compute those used by more than 50 rules
#
# Backward compatibility: if a constant has no 'rule_count' in the catalog
# (compiled before this feature was added), it is always pre-computed,
# exactly as it was before this threshold existed.
_PRECALC_MIN_RULE_COUNT = 50




def start_process(rule_set, model_xbrl, cntlr, options):
    
    global_context = XuleGlobalContext(rule_set, model_xbrl, cntlr, options=options)
    xule_context = XuleRuleContext(global_context)
    from .XuleModelIndexer import index_model
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
    sub_processes = {}
    constants_running = False

    # Convenience: prefix every debug line with timestamp and pid so concurrent
    # filings can be told apart in the log.
    def _dbg(msg):
        global_context.message_queue.logging(
            "[pid:%-6d %s] %s" % (
                getpid(),
                datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                msg))

    if getattr(global_context.options, "xule_debug", False):
        _dbg("watch_processes STARTING  num_processors=%d  total_cpus=%d  "
             "cpu_allocation=%d  running_filings=%s  pool_available=%s" % (
                 global_context.num_processors,
                 global_context.total_cpus,
                 global_context._cpu_state.get('allocation', global_context.num_processors),
                 global_context.shared_running_filings.value
                     if global_context.shared_running_filings else 'n/a',
                 global_context.shared_available_cpus.value
                     if global_context.shared_available_cpus else 'n/a'))

    while True:

        # ── TOP-OF-LOOP SNAPSHOT ──────────────────────────────────────────────
        if getattr(global_context.options, "xule_debug", False):
            alloc      = global_context._cpu_state.get('allocation', global_context.num_processors)
            pool_avail = (global_context.shared_available_cpus.value
                          if global_context.shared_available_cpus else 'n/a')
            run_fil    = (global_context.shared_running_filings.value
                          if global_context.shared_running_filings else 'n/a')
            act        = sum(1 for w in sub_processes.values() if not w['stopping'])
            stp        = sum(1 for w in sub_processes.values() if w['stopping'])
            _dbg("=" * 56)
            _dbg("LOOP TOP")
            _eff = 1 if (constants_running and not global_context.constants_done) else alloc
            _dbg("  Budget   num_processors=%-3d  cpu_allocation=%-3d  effective_rule_target=%d" % (
                     global_context.num_processors, alloc, _eff))
            _dbg("  Pool     available=%-3s  running_filings=%-3s  total=%d" % (
                     pool_avail, run_fil, global_context.total_cpus))
            _dbg("  Workers  active=%-2d  stopping=%-2d  total_sub_processes=%d" % (
                     act, stp, len(sub_processes)))
            _dbg("  Queues   rules_remaining=%-4d  rules_q=%-4d  consts_remaining=%-4d  "
                 "consts_q=%-4s" % (
                     len(global_context.all_rules),
                     global_context.rules_queue.qsize(),
                     len(global_context.all_constants),
                     global_context.calc_constants_queue.qsize()))
            _dbg("  Flags    constants_running=%-5s  constants_done=%-5s" % (
                     constants_running, global_context.constants_done))
            _dbg("=" * 56)

        # ── REBALANCE ─────────────────────────────────────────────────────────
        # Recompute this filing's fair share of the CPU budget every loop
        # iteration, woken by Condition.notify_all() or the 0.1 s timeout.
        if global_context.shared_cpu_condition is not None:
            with global_context.shared_cpu_condition:
                running = global_context.shared_running_filings.value
                if running > 0:
                    new_target = max(
                        global_context.min_cpus_per_filing,
                        floor(global_context.total_cpus / running))
                else:
                    new_target = global_context.num_processors

                current_alloc = global_context._cpu_state.get(
                    'allocation', global_context.num_processors)

                if getattr(global_context.options, "xule_debug", False):
                    formula_val = (floor(global_context.total_cpus / running)
                                   if running > 0 else 'n/a')
                    if new_target == current_alloc:
                        verdict = "NO CHANGE"
                    elif new_target < current_alloc:
                        verdict = "SHRINK %d → %d (by %d)" % (
                            current_alloc, new_target, current_alloc - new_target)
                    else:
                        verdict = "GROW %d → %d (by %d)" % (
                            current_alloc, new_target, new_target - current_alloc)
                    _dbg("REBALANCE  running_filings=%-2d  "
                         "floor(%d/%d)=%s  min_cpus=%d  "
                         "new_target=%d  current_alloc=%d  → %s" % (
                             running,
                             global_context.total_cpus, running, formula_val,
                             global_context.min_cpus_per_filing,
                             new_target, current_alloc, verdict))

                if new_target < current_alloc:
                    shrink_count = current_alloc - new_target
                    candidates   = [n for n, w in sub_processes.items()
                                    if not w['stopping']]
                    to_stop      = candidates[:shrink_count]
                    for n in to_stop:
                        sub_processes[n]['cq'].put("STOP")
                        sub_processes[n]['stopping'] = True
                    global_context.num_processors = new_target
                    if getattr(global_context.options, "xule_debug", False):
                        _dbg("  SHRINK: queued STOP for worker slots %s  "
                             "num_processors: %d → %d  "
                             "allocation stays at %d until workers exit" % (
                                 to_stop, current_alloc, new_target, current_alloc))

                elif new_target > current_alloc:
                    wanted      = new_target - current_alloc
                    before_pool = global_context.shared_available_cpus.value
                    claimable   = min(wanted, before_pool)
                    if claimable > 0:
                        before_alloc = global_context._cpu_state['allocation']
                        global_context.shared_available_cpus.value -= claimable
                        global_context._cpu_state['allocation']    += claimable
                        global_context.num_processors = global_context._cpu_state['allocation']
                        if getattr(global_context.options, "xule_debug", False):
                            _dbg("  GROW: claimed %d slots  "
                                 "pool: %d → %d  alloc: %d → %d  "
                                 "num_processors: %d → %d" % (
                                     claimable,
                                     before_pool,
                                     global_context.shared_available_cpus.value,
                                     before_alloc,
                                     global_context._cpu_state['allocation'],
                                     before_alloc,
                                     global_context.num_processors))
                    elif getattr(global_context.options, "xule_debug", False):
                        _dbg("  GROW wanted %d slots but pool empty "
                             "(available=%d); will retry next iteration" % (
                                 wanted, before_pool))

        # ── REAP DEAD WORKERS ─────────────────────────────────────────────────
        del_process = []
        for num in sub_processes:
            if not sub_processes[num]['p'].is_alive():
                del_process.append(num)
        for num in del_process:
            was_stopping = sub_processes[num]['stopping']
            worker_pid   = sub_processes[num]['p'].pid
            if was_stopping and global_context.shared_cpu_condition is not None:
                with global_context.shared_cpu_condition:
                    before_pool  = global_context.shared_available_cpus.value
                    before_alloc = global_context._cpu_state['allocation']
                    global_context.shared_available_cpus.value += 1
                    global_context._cpu_state['allocation']    -= 1
                    global_context.shared_cpu_condition.notify_all()
                if getattr(global_context.options, "xule_debug", False):
                    _dbg("WORKER EXIT [slot %-2d pid %-6s] STOP (shrink)  "
                         "pool: %d → %d  alloc: %d → %d  (notified waiters)" % (
                             num, worker_pid,
                             before_pool,
                             global_context.shared_available_cpus.value,
                             before_alloc,
                             global_context._cpu_state['allocation']))
            elif getattr(global_context.options, "xule_debug", False):
                _dbg("WORKER EXIT [slot %-2d pid %-6s] natural (queue empty)  "
                     "slot returns to filing_available  "
                     "alloc unchanged (%s)" % (
                         num, worker_pid,
                         global_context._cpu_state.get('allocation', '?')))
            del sub_processes[num]

        # ── START NEW WORKERS ─────────────────────────────────────────────────
        # active_count excludes workers already marked for stopping so their
        # vacated slots are not immediately refilled.  filing_available is the
        # number of pre-claimed CPU slots not occupied by an active worker;
        # new workers draw from this reserve without re-claiming from the pool.
        #
        # During constants computation, only 1 rule worker slot is allowed so
        # the rest of the CPU budget is reserved for the constants processes.
        # After constants finish, the full allocation is restored.
        active_count = sum(1 for w in sub_processes.values() if not w['stopping'])

        if constants_running and not global_context.constants_done:
            effective_target = 1
        elif global_context.shared_cpu_condition is not None:
            effective_target = global_context._cpu_state.get(
                'allocation', global_context.num_processors)
        else:
            effective_target = global_context.num_processors

        if global_context.shared_cpu_condition is not None:
            filing_available = global_context._cpu_state.get(
                'allocation', global_context.num_processors) - active_count
        else:
            filing_available = effective_target - active_count

        if active_count < effective_target and \
                filing_available > 0 and not global_context.rules_queue.empty():

            to_start = min(effective_target - active_count, filing_available)

            if getattr(global_context.options, "xule_debug", False):
                _dbg("START WORKERS: active=%-2d  effective_target=%-2d  "
                     "filing_available=%-2d  to_start=%d  "
                     "(constants_phase=%s)" % (
                         active_count, effective_target,
                         filing_available, to_start,
                         constants_running and not global_context.constants_done))

            for num in range(0, to_start):
                thisnum = num
                while thisnum in sub_processes.keys():
                    thisnum += 1

                process_name = "Sub-Process %d" % thisnum
                cq = Queue()
                p  = Process(target=rules_process, args=(process_name, global_context, cq))
                p.name = process_name

                c = 0
                while True:
                    try:
                        c += 1
                        if c > 3:
                            global_context.message_queue.logging(
                                "ERROR: Tried running filing 3 times: %s" % process_name)
                            break
                        p.start()
                        break
                    except Exception:
                        global_context.message_queue.logging(
                            "ERROR: Problem while starting rules_process thread: %s" % process_name)

                sub_processes[thisnum] = {'cq': cq, 'p': p, 'stopping': False}

                if getattr(global_context.options, "xule_debug", False):
                    new_active = sum(1 for w in sub_processes.values() if not w['stopping'])
                    new_fa     = global_context._cpu_state.get(
                        'allocation', global_context.num_processors) - new_active
                    _dbg("  STARTED %s (worker-pid=%s)  "
                         "active now=%-2d  filing_available now=%-2d" % (
                             process_name, p.pid, new_active, new_fa))

        # ── CONSTANT MANAGEMENT ───────────────────────────────────────────────
        # Phase A – first time all_constants is non-empty: flatten all groups
        # into a list (dependency order: c → frc → rtc → rfrc), clear
        # all_constants, and start ONE background Thread that runs a
        # ThreadPoolExecutor with (num_processors−1) worker threads.
        #
        # Using Threads (not Processes) means each worker writes computed
        # var_info objects directly into global_context._constants — no
        # pickling required, so lxml-based model references are preserved.
        # CPython's GIL makes concurrent dict writes to distinct node_id
        # keys safe without an explicit lock.
        #
        # Phase B – executor running: nothing to do here; watch_processes
        # continues its normal loop (starting 'r' rule workers in the 1-slot
        # window) while constants are computed in the background.
        #
        # Phase C – executor finished (constants_done=True): stop current rule
        # workers so they will restart next iteration and fork with the
        # now-complete _constants dict.
        if len(global_context.all_constants) > 0 and not constants_running:
            # Phase A – flatten constant groups into an ordered list.
            #
            # 'c' and 'rtc' constants have no filing dependency and are always
            # pre-computed.
            #
            # 'frc' and 'rfrc' constants need filing data; pre-computing all of
            # them in a standalone context is unsafe for many constants.
            #
            # Xule is set-oriented: expressions iterate and can produce multiple
            # values.  What constrains a result to a single value is the rule's
            # active iteration table.  When a constant is pre-computed here
            # (outside any running rule) that context is absent, so the
            # expression can return all possible values — a Xule list — where
            # downstream code (e.g. a dimension filter) expects a single qname.
            #
            # Pre-computation is only safe for constants where rule_count IS
            # known (new ruleset with counts compiled in) AND the count exceeds
            # _PRECALC_MIN_RULE_COUNT (i.e., enough rules depend on it that the
            # warm-up cost is worth paying).  In practice, constants selected for
            # pre-computation by this criterion are the "heavy" aggregations over
            # large fact sets that genuinely benefit from being computed once.
            #
            # Old rulesets (rule_count absent) and low-count constants both fall
            # through to lazy evaluation — computed the first time a rule needs
            # them, inside the rule's live iteration context.
            constants_list  = []
            skipped_lazy    = []
            has_rule_counts = None   # None = not yet determined

            for const_type in ('c', 'frc', 'rtc', 'rfrc'):
                if const_type not in global_context.all_constants:
                    continue
                for const_name in global_context.all_constants[const_type]:
                    if const_type in ('frc', 'rfrc'):
                        rule_count = (global_context.catalog['constants']
                                      .get(const_name, {})
                                      .get('rule_count', None))
                        # First constant tells us whether counts exist at all.
                        if has_rule_counts is None:
                            has_rule_counts = rule_count is not None
                        # Skip if: count unknown (old ruleset) OR count is low.
                        # Only pre-compute when count is known AND above threshold.
                        if rule_count is None or rule_count <= _PRECALC_MIN_RULE_COUNT:
                            skipped_lazy.append((const_type, const_name, rule_count))
                            continue   # compute lazily when a rule needs it
                    constants_list.append((const_type, const_name))

            global_context.all_constants = {}          # consumed; prevents re-entry

            if getattr(global_context.options, "xule_debug", False):
                _dbg("CONSTANTS Phase A: pre-compute=%d  lazy=%d  "
                     "rule_counts_available=%s  threshold=%d" % (
                         len(constants_list), len(skipped_lazy),
                         has_rule_counts, _PRECALC_MIN_RULE_COUNT))
                for (ct, cn, rc) in skipped_lazy:
                    _dbg("  LAZY [%s] %s  rule_count=%s" % (ct, cn, rc))

            if constants_list:
                # Set constants_done=False BEFORE starting the thread to
                # avoid a race where an instant-finishing executor writes True
                # and the main thread then overwrites it with False.
                global_context.constants_done = False
                num_const_workers = max(1, global_context.num_processors - 1)
                t = Thread(target=_constants_executor_thread,
                           args=(global_context, constants_list, num_const_workers))
                t.name = "Constants-Executor"
                t.daemon = True
                t.start()
                constants_running = True
                if getattr(global_context.options, "xule_debug", False):
                    _dbg("CONSTANTS: executor Thread started  "
                         "workers=%d  constants=%d  rule_slots=1" % (
                             num_const_workers, len(constants_list)))
            else:
                # Nothing to pre-compute — skip Phase B and the executor entirely.
                # Leave constants_running=False so rules start at full CPU
                # allocation immediately.  Set constants_done=True so the
                # LOAD RULE QUEUES section below loads all rule types (including
                # 'fcr') without waiting for a Phase C that will never come.
                global_context.constants_done = True
                if getattr(global_context.options, "xule_debug", False):
                    _dbg("CONSTANTS: nothing to pre-compute — "
                         "skipping Phase B; all rule types load this iteration")

        elif constants_running and global_context.constants_done:
            # Phase C
            if getattr(global_context.options, "xule_debug", False):
                _dbg("CONSTANTS: executor done; _constants=%d entries; "
                     "stopping %d rule workers for full-CPU rule phase" % (
                         len(global_context._constants), len(sub_processes)))
            for num in sub_processes:
                sub_processes[num]['cq'].put("STOP")
            constants_running = False

        elif not constants_running and not global_context.constants_done:
            # No constants to compute
            global_context.constants_done = True

        # ── LOAD RULE QUEUES ──────────────────────────────────────────────────
        if len(global_context.all_rules) > 0:
            load_rules_queue(global_context, 'r')
            if global_context.constants_done:
                load_rules_queue(global_context, 'fcr', 'rtr', 'rtfcr', 'rtcr', 'alldepr')

        # ── EXIT CHECK ────────────────────────────────────────────────────────
        if not constants_running and len(global_context.all_rules) <= 0 \
                and len(sub_processes) <= 0 \
                and global_context.rules_queue.qsize() <= 0:
            if getattr(global_context.options, "xule_debug", False):
                _dbg("EXIT: all work complete  "
                     "constants_running=%s  rules_remaining=%d  "
                     "sub_processes=%d  rules_queue=%d" % (
                         constants_running, len(global_context.all_rules),
                         len(sub_processes), global_context.rules_queue.qsize()))
            break

        # ── SLEEP ─────────────────────────────────────────────────────────────
        # Wait on the Condition so we wake immediately when another filing
        # releases CPUs (notify_all) rather than burning a CPU hot-polling.
        if global_context.shared_cpu_condition is not None:
            if getattr(global_context.options, "xule_debug", False):
                _dbg("SLEEP: waiting on condition (timeout=0.1s)")
            with global_context.shared_cpu_condition:
                global_context.shared_cpu_condition.wait(timeout=0.1)

    if getattr(global_context.options, "xule_debug", False):
        _dbg("watch_processes FINISHED  "
             "final num_processors=%d  cpu_allocation=%d" % (
                 global_context.num_processors,
                 global_context._cpu_state.get('allocation', 0)))

def _constants_executor_thread(global_context, constants_list, num_workers):
    """Background Thread: compute all constants using a ThreadPoolExecutor.

    Each worker thread inside the executor calls `calc_constant()` and writes
    the resulting var_info dict directly into `global_context._constants`.
    Because threads share the parent process's address space, no pickling is
    required — lxml model objects, XBRL facts, and any other non-serialisable
    value are stored as-is.  CPython's GIL makes individual dict key
    assignments (`d[k] = v`) atomic, so concurrent writes to distinct
    node_ids are safe without an explicit lock.

    If two threads happen to compute the same constant (e.g., one constant
    depends on another that is being concurrently computed), the last write
    wins, but both produce identical values so correctness is preserved.

    When all futures complete, `global_context.constants_done` is set to
    True so the `watch_processes` loop can advance to Phase C.
    """
    def _compute_one(args):
        _, constant_name = args
        c_name = constant_name
        try:
            if getattr(global_context.options, "xule_debug", False):
                global_context.message_queue.logging(
                    "[pid:%-6d] Computing constant: %s" % (getpid(), constant_name))

            if getattr(global_context.options, "xule_time", None) is not None:
                const_start = datetime.datetime.today()

            cat_const    = global_context.catalog['constants'].get(constant_name)
            ast_const    = global_context.rule_set.getItem(cat_const)
            node_id      = ast_const['node_id']
            file_num     = global_context.catalog['constants'][constant_name]['file']
            xule_context = XuleRuleContext(global_context, constant_name, file_num)

            if constant_name not in xule_context._BUILTIN_CONSTANTS:
                var_info = {
                    "name":       constant_name,
                    "tagged":     'tagged' in ast_const,
                    "type":       xule_context._VAR_TYPE_CONSTANT,
                    "expr":       ast_const,
                    "calculated": False,
                }
                from .XuleProcessor import calc_constant
                calc_constant(var_info, xule_context)
                # GIL makes this assignment atomic; concurrent threads writing
                # to different node_ids is safe in CPython.
                global_context._constants[node_id] = var_info

            if getattr(global_context.options, "xule_time", None) is not None:
                const_end = datetime.datetime.today()
                global_context.times.append(
                    ('constant', constant_name, const_end - const_start))

        except Exception:
            import traceback as _tb
            global_context.message_queue.logging(
                "[pid:%-6d] Error while computing constant: %s\n%s" % (
                    getpid(), c_name, _tb.format_exc()))

    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging(
            "[pid:%-6d %s] Constants executor started: %d constants / %d threads" % (
                getpid(),
                datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                len(constants_list), num_workers))

    # Run constants in phase order so that inter-phase dependencies are
    # satisfied before the next phase begins.  The original sequential code
    # computed groups in this exact order: c → frc → rtc → rfrc.  An frc
    # constant may depend on a c constant already being in _constants; running
    # all groups concurrently in one pool breaks that guarantee and causes
    # "found 'list'" errors when a filter value comes from an unresolved ref.
    # Parallelism is preserved *within* each phase.
    _PHASE_ORDER = ('c', 'frc', 'rtc', 'rfrc')
    _phases = {t: [] for t in _PHASE_ORDER}
    for item in constants_list:
        const_type = item[0]
        if const_type in _phases:
            _phases[const_type].append(item)

    for _phase in _PHASE_ORDER:
        if not _phases[_phase]:
            continue
        if getattr(global_context.options, "xule_debug", False):
            global_context.message_queue.logging(
                "[pid:%-6d %s] Constants executor: phase '%s'  %d constants" % (
                    getpid(),
                    datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    _phase, len(_phases[_phase])))
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            list(executor.map(_compute_one, _phases[_phase]))

    global_context.constants_done = True

    if getattr(global_context.options, "xule_debug", False):
        global_context.message_queue.logging(
            "[pid:%-6d %s] Constants executor done: %d entries in _constants" % (
                getpid(),
                datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                len(global_context._constants)))


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
