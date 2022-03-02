"""XuleServer

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
import sys, os, gettext, shlex, signal

# Change path to base arelle directory (3 paths down)
sep = "\\" if os.getcwd().find("\\") != -1 else "/"
directory = os.getcwd().split(sep)
sys.path.append(sep.join(directory[:(len(directory)-3)]))
 
from arelle import CntlrCmdLine
from multiprocessing import Manager

def set_exit_handler(func):
    signal.signal(signal.SIGTERM, func)
    
def on_exit(sig, func=None):
    print("exit handler triggered")
    sys.exit(1)
    
if __name__ == '__main__':
    set_exit_handler(on_exit)
    options = None
    # grab options, setup
    envArgs = os.getenv("ARELLE_ARGS")
    manager = Manager()
    output = manager.dict()
    
    if envArgs:
        args = shlex.split(envArgs)
    else:
        args = sys.argv[1:]
    try:
        numthreads = int(args[args.index('--xule-numthreads')+1])
    except ValueError:
        numthreads = 1
    gettext.install("arelle") # needed for options messages

    print("Initializing Server")
    cntlr = CntlrCmdLine.parseAndRun(args)
    cntlr.startLogging(logFileName='logToBuffer')
    # get generated options from controller
    options = getattr(cntlr, "xule_options", None)
    setattr(options, "webserver", options.xule_server)
    # Clear options to reduce size of cntlr object
    setattr(cntlr, "xule_options", None)
    setattr(options, "xule_server", None)

    # Clean up
    import gc
    gc.collect()

    # start web server
    if options is not None:
        '''
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)
        '''

        print("starting webserver")
        from arelle import CntlrWebMain
        app = CntlrWebMain.startWebserver(cntlr, options, output=output)
        print("ending webserver")
    else:
        print("Error! Options don't exist!")
