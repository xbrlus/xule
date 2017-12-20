'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change$
'''
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
