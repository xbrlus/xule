'''
xbrlDB is an interface to XBRL databases.

Two implementations are provided:

(1) the XBRL Public Database schema for Postgres, published by XBRL US.

(2) an graph database, based on the XBRL Abstract Model PWD 2.

(c) Copyright 2013 Mark V Systems Limited, California US, All rights reserved.  
Mark V copyright applies to this software, which is licensed according to the terms of Arelle(r).
and does not apply to the XBRL US Database schema and description.

'''

import time, os, io, sys, logging
from arelle.Locale import format_string
from .XbrlPublicPostgresDB import insertIntoDB
from lxml import etree
from arelle import ModelManager
import optparse

def storeIntoDB(dbConnection, modelXbrl, rssItem=None, **kwargs):
    host = port = user = password = db = timeout = None
    if isinstance(dbConnection, (list, tuple)): # variable length list
        if len(dbConnection) > 0: host = dbConnection[0]
        if len(dbConnection) > 1: port = dbConnection[1]
        if len(dbConnection) > 2: user = dbConnection[2]
        if len(dbConnection) > 3: password = dbConnection[3]
        if len(dbConnection) > 4: db = dbConnection[4]
        if len(dbConnection) > 5 and dbConnection[5] and dbConnection[5].isdigit(): 
            timeout = int(dbConnection[5])

    startedAt = time.time()
#     product = None
#     if dbType in dbTypes:
#         insertIntoDB = dbTypes[dbType]
#         product = dbProduct[dbType]
#     elif isPostgresPort(host, port):
#         insertIntoDB = insertIntoPostgresDB
#     else:
#         modelXbrl.modelManager.addToLog('Server at "{0}:{1}" is not recognized to be either a Postgres or a Rexter service.'.format(host, port))
#         return
    result = insertIntoDB(modelXbrl, host=host, port=port, user=user, password=password, database=db, timeout=timeout, rssItem=rssItem, **kwargs)
    if kwargs.get("logStoredMsg", result): # if false/None result and no logStoredMsg parameter then skip the message
        modelXbrl.modelManager.addToLog(format_string(modelXbrl.modelManager.locale, 
                              _("stored to database in %.2f secs"), 
                              time.time() - startedAt), messageCode="info", file=modelXbrl.uri)
    return result

def xbrlDBcommandLineOptionExtender(parser):
    # extend command line options to store to database
    
    parserGroup = optparse.OptionGroup(parser,"XBRL US Database (xbrlusDB) Loader")
    
    parserGroup.add_option("--xbrlusDB", 
                      action="store", 
                      dest="storeIntoXbrlDb", 
                      help=_("Store into XBRL DB.  "
                             "Provides connection string: host,port,user,password,database[,timeout]."
                             "Autodetects database type unless 7th parameter is provided.  "))
    
    parserGroup.add_option("--xbrlusDB-entry",
                      action="store",
                      dest="xbrlusDBInstance",
                      help=_("Entry point file of XBRL document to load into the database. Can be an XBRL instance or inline XBRL document"))
    
    parserGroup.add_option("--xbrlusDB-file",
                      action="append",
                      dest="xbrlusDBFile",
                      help=_("Additional supporting files. Determined by source."))
    
    parserGroup.add_option("--xbrlusDB-source",
                      action="store",
                      dest="xbrlusDBSource",
                      default="SEC",
                      help=_("Filing source"))
    
    parserGroup.add_option("--xbrlusDB-document-cache",
                      action="store",
                      dest="xbrlusDBDocumentCache",
                      help=_("Map file location to official location. The map consists of two parts, the path of the file location and the path of the official " \
                             "location. The map is used to translate the file location to the path that is used to store the document uri in the database. " \
                             "This allows using local copies of a file but having the document uri in the databae indicate the official location of the document. " \
                             "The map is composed with the file location path follow by '|' and then the official location path. Multiple maps can be created " \
                             "by using multile --xblrusDB-document-map arguments."))
    parserGroup.add_option("--xbrlusDB-time",
                           action="store_true",
                           default=False,
                           dest="xbrlusDBTime",
                           help=_("Include detailed timing of the database operations. This is used for debugging and profiling."))
    
    parserGroup.add_option("--xbrlusDB-filing-id",
                           action="store",
                           dest="xbrlusDBFilingId",
                           help=_("Filing identifier to use if it cannot be acquired from the filing or supporting files."))
    
    parser.add_option_group(parserGroup)
    
    logging.getLogger("arelle").addHandler(LogToDbHandler())    

def xbrlDBcommandLineOptionChecker(cntlr, options, **kwargs):
    parser = optparse.OptionParser()
    
    if getattr(options, "xbrlusDBSource", '').lower() != 'sec':
        parser.error(_("Only supported source is SEC"))
    
def xbrlDBCommandLineXbrlRun(cntlr, options, modelXbrl, entryPoint):
    if getattr(options, "storeIntoXbrlDb", False):
        dbConnection = options.storeIntoXbrlDb.split(",")
        host = port = user = password = db = timeout = None
        
        if len(dbConnection) < 5 or len(dbConnection) > 6:
            cntlr.addToLog(_("Invalid database connection string."))
            return
        if len(dbConnection) > 0: host = dbConnection[0]
        if len(dbConnection) > 1: port = dbConnection[1]
        if len(dbConnection) > 2: user = dbConnection[2]
        if len(dbConnection) > 3: password = dbConnection[3]
        if len(dbConnection) > 4: db = dbConnection[4]
        if len(dbConnection) > 5 and dbConnection[5] and dbConnection[5].isdigit(): 
            timeout = int(dbConnection[5])

        startedAt = time.time()
        result = insertIntoDB(modelXbrl, host=host, port=port, user=user, password=password, database=db, timeout=timeout, options=options)
        if getattr(options, "logStoredMsg", False): #kwargs.get("logStoredMsg", result): # if false/None result and no logStoredMsg parameter then skip the message
            modelXbrl.modelManager.addToLog(format_string(modelXbrl.modelManager.locale, 
                                  _("stored to database in %.2f secs"), 
                                  time.time() - startedAt), messageCode="info", file=modelXbrl.uri)
        return result

class LogToDbHandler(logging.Handler):
    def __init__(self):
        super(LogToDbHandler, self).__init__()
        self.logRecordBuffer = []
        
    def flush(self):
        del self.logRecordBuffer[:]
    
    def dbHandlerLogEntries(self, clear=True):
        entries = []
        for logRec in self.logRecordBuffer:
            message = { "text": self.format(logRec) }
            if logRec.args:
                for n, v in logRec.args.items():
                    message[n] = v
            entry = {"code": logRec.messageCode,
                     "level": logRec.levelname.lower(),
                     "refs": logRec.refs,
                     "message": message}
            entries.append(entry)
        if clear:
            del self.logRecordBuffer[:]
        return entries
    
    def emit(self, logRecord):
        self.logRecordBuffer.append(logRecord)
        
 
__pluginInfo__ = {
    'name': 'XBRL US Database',
    'version': '0.9',
    'description': "This plug-in implements the XBRL US Public Postgres",
    'license': 'Apache-2 (Arelle plug-in), BSD license (pg8000 library)',
    'author': '',
    'copyright': '(c) Copyright 2016 XBRL US Inc.,\n'
                'uses: c) Copyright 2013 Mark V Systems Limited, All rights reserved,\n \n'
                ' cx_Oracle Copyright (c) 2007-2012, Anthony Tuininga. All rights reserved (Oracle DB), \n'
                '           (and)Copyright (c) 2001-2007, Computronix (Canada) Ltd., Edmonton, Alberta, Canada. All rights reserved, \n'
                '      pg8000, Copyright (c) 2007-2009, Mathieu Fenniak (Postgres DB), \n'
                '      pyodbc, no copyright, Michael Kleehammer (MS SQL), \n'
                '      PyMySQL, Copyright (c) 2010, 2013 PyMySQL contributors (MySQL DB), and\n' 
                '      rdflib, Copyright (c) 2002-2012, RDFLib Team (RDF DB)',
    # classes of mount points (required)
    #'CntlrWinMain.Menu.Tools': xbrlDBmenuEntender,
    'CntlrCmdLine.Options': xbrlDBcommandLineOptionExtender,
    'CntlrCmdLine.Utility.Run': xbrlDBcommandLineOptionChecker,
    #'CntlrCmdLine.Xbrl.Loaded': xbrlDBCommandLineXbrlLoaded,
    'CntlrCmdLine.Xbrl.Run': xbrlDBCommandLineXbrlRun,
    #'DialogRssWatch.FileChoices': xbrlDBdialogRssWatchDBconnection,
    #'DialogRssWatch.ValidateChoices': xbrlDBdialogRssWatchValidateChoices,
    #'ModelDocument.PullLoader': xbrlDBLoader,
    #'RssWatch.HasWatchAction': xbrlDBrssWatchHasWatchAction,
    #'RssWatch.DoWatchAction': xbrlDBrssDoWatchAction,
    #'Streaming.Start': xbrlDBstartStreaming,
    #'Streaming.ValidateFacts': xbrlDBvalidateStreamingFacts,
    #'Streaming.Finish': xbrlDBfinishStreaming,
    #'Validate.RssItem': xbrlDBvalidateRssItem
    'end': 'end'
}