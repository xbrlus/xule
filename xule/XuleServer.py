import sys, os, gettext, shlex

# Change path to base arelle directory (3 paths down)
sep = "\\" if os.getcwd().find("\\") != -1 else "/"
directory = os.getcwd().split(sep)
sys.path.append(sep.join(directory[:(len(directory)-3)]))

from arelle import CntlrCmdLine


if __name__ == '__main__':
    # grab options, setup
    envArgs = os.getenv("ARELLE_ARGS")
    if envArgs:
        args = shlex.split(envArgs)
    else:
        args = sys.argv[1:]
    gettext.install("arelle") # needed for options messages

    print("Initializing Server")
    cntlr = CntlrCmdLine.parseAndRun(args)

    # get generated options from controller
    options = getattr(cntlr, "xule_options", None)
    if options is not None:
        setattr(options, "webserver", options.xule_server)
    
        # Clear options to reduce size of cntlr object
        setattr(cntlr, "xule_options", None)
        setattr(options, "xule_server", None)
    
        # start web server
        cntlr.startLogging(logFileName='logToBuffer')
        from arelle import CntlrWebMain
        app = CntlrWebMain.startWebserver(cntlr, options)

