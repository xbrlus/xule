'''
XbrlPublicPostgresDB.py implements a relational database interface for Arelle, based
on the XBRL US Public Database.  The database schema is described by "XBRL US Public Database",
published by XBRL US, 2011.  This is a syntactic representation of XBRL information. 

This module provides the execution context for saving a dts and assession in 
XBRL Public Database Tables.  It may be loaded by Arelle'sRSS feed, or by individual
DTS and instances opened by interactive or command line/web service mode.

(c) Copyright 2013 Mark V Systems Limited, California US, All rights reserved.  
Mark V copyright applies to this software, which is licensed according to the terms of Arelle(r).
and does not apply to the XBRL US Database schema and description.

The XBRL US Database schema and description is (c) Copyright XBRL US 2011, The 
resulting database may contain data from SEC interactive data filings (or any other XBRL
instance documents and DTS) in a relational model. Mark V Systems conveys neither 
rights nor license for the database schema.
 
The XBRL US Database and this code is intended for Postgres.  XBRL-US uses Postgres 8.4, 
Arelle uses 9.1, via Python DB API 2.0 interface, using the pg8000 library.

Information for the 'official' XBRL US-maintained database (this schema, containing SEC filings):
    Database Name: edgar_db 
    Database engine: Postgres version 8.4 
    \Host: public.xbrl.us 
    Port: 5432

to use from command line:

linux
   # be sure plugin is installed
   arelleCmdLine --plugin '+xbrlDB|show'
   arelleCmdLine -f http://sec.org/somewhere/some.rss -v --store-to-XBRL-DB 'myserver.com,portnumber,pguser,pgpasswd,database,timeoutseconds'
   
windows
   rem be sure plugin is installed
   arelleCmdLine --plugin "+xbrlDB|show"
   arelleCmdLine -f http://sec.org/somewhere/some.rss -v --store-to-XBRL-DB "myserver.com,portnumber,pguser,pgpasswd,database,timeoutseconds"

'''

import time
import datetime
import decimal
from arelle.ModelDocument import Type
from arelle.ModelDtsObject import ModelConcept, ModelResource
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelValue import qname
from arelle.ValidateXbrlCalcs import roundValue
from arelle.XmlUtil import elementFragmentIdentifier
from arelle import XbrlConst
from .SqlDb import XPDBException, isSqlConnection, SqlDbConnection
from contextlib import contextmanager
import re
import hashlib
from fileinput import filename
from lxml import etree
import os
import urllib.request
import urllib.parse
import collections
import importlib
import inspect
import json

def insertIntoDB(cntlr, modelXbrl, 
                 user=None, password=None, host=None, port=None, database=None, timeout=None,
                 options=None):
    
    xpgdb = None

    try:
        xpgdb = XbrlPostgresDatabaseConnection(cntlr, modelXbrl, user, password, host, port, database, timeout, 'postgres', options)
        xpgdb.execute("SET application_name TO 'xbrlusDB loader';", fetch=False)
        xpgdb.verifyTables()
        xpgdb.insertXbrl(supportFiles=getattr(options,"xbrlusDBFile",tuple()), documentCacheLocation=getattr(options,"xbrlusDBDocumentCache",None))
        xpgdb.close()
    except Exception as ex:
        if xpgdb is not None:
            try:
                xpgdb.close(rollback=True)
            except Exception as ex2:
                pass
        raise # reraise original exception with original traceback  
    
        
def isDBPort(host, port, timeout=10):
    return isSqlConnection(host, port, timeout, product="postgres")

XBRLDBTABLES = {
                "fact",
                "entity", #"entity_identifier", 
                "entity_name_history", 
                "context",  "context_dimension", "context_dimension_explicit",
                "report", "report_document", "report_element",
                "dts", "dts_element", "dts_document",
                "attribute_value",
                "custom_role_type",
                "uri",
                "document",
                "qname",
                "taxonomy", "taxonomy_version", "namespace", "base_namespace",
                "element", "element_attribute_value_association",
                "dts_network", "dts_relationship",
                "custom_arcrole_type", "custom_arcrole_used_on", "custom_role_type", "custom_role_used_on",
                "label_resource",
                "reference_part", #"reference_part_type",
                "resource",
                "footnote_resource",
                "enumeration_arcrole_cycles_allowed",
                "enumeration_element_balance",
                "enumeration_element_period_type",
                "enumeration_unit_measure_location",
                "industry", "industry_level", "industry_structure",
                "sic_code", 
                }


class XbrlPostgresDatabaseConnection(SqlDbConnection):
    
    class _QNameException(Exception):
        pass
    
    class _SourceFunctionError(Exception):
        pass
    
    def __init__(self, cntlr, modelXbrl, user, password, host, port, database, timeout, db_type, options):
        super().__init__(modelXbrl, user, password, host, port, database, timeout, db_type)
        self.options = options
        self.cntlr = cntlr
        self.startTime = datetime.datetime.today()
        
        #set up info from the options
        options.xbrlusDBInfos = {}
        for nameValue in getattr(options, 'xbrlusDBInfo', None) or tuple():
            name, value = nameValue.split('=',1) #the format was validated in the parser argument checking
            options.xbrlusDBInfos[name.strip()] = value   
        
        self.modelXbrl.info("info",_("Connected to database. Host: {}, Port: {}, Database: {}, User: {}".format(host, port, database,user)))
    
    def loadSource(self):
        #import source module
        sourceName = getattr(self.options, "xbrlusDBSource", None)
        sourceDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'source')
        
        if sourceName is None:
            #This should not happen
            raise XPDBException("xpgDB:NoSourceSpedified",
                                _("A source must be specified using --xbrlusDB-source. If the defaults are desired explicitly state this with '--xbrlusDBSource default'"))
        elif sourceName != 'default':
            self.modelXbrl.info("info", _("%(now)s - Using source %(source)s"),
                        source=sourceName,
                        now=str(datetime.datetime.today()))
            currentPackageName = __name__.split('.')[0]
            self.sourceMod = None
            try:
                self.sourceMod = importlib.import_module('arelle.plugin.' + currentPackageName + '.source.' + sourceName)
            except ImportError:
                raise XPDBException("xpgDB:InvalidSource",
                                _("Source '%s' cannot be found" % sourceName))            
        self.sourceName = sourceName.strip()    
    
    def verifyTables(self):
        missingTables = XBRLDBTABLES - self.tablesInDB()

        if missingTables:
            raise XPDBException("xpgDB:MissingTables",
                                _("The following tables are missing, suggest reinitializing database schema: %(missingTableNames)s"),
                                missingTableNames=', '.join(t for t in sorted(missingTables))) 
            
    def insertXbrl(self, supportFiles=tuple(), documentCacheLocation=None):
                        
        # must also have default dimensions loaded
        from arelle import ValidateXbrlDimensions
        ValidateXbrlDimensions.loadDimensionDefaults(self.modelXbrl)
        self.supportFiles = supportFiles
        self.documentMap = dict()
        #set up document map
        self.documentCacheLocation = documentCacheLocation
        
        if self.modelXbrl.modelDocument.type in (Type.INSTANCE, Type.INLINEXBRL):
            self.loadType = 'instance'
            if getattr(self.options, 'xbrlusDBDTSName', None) is not None:
                raise XPDBException("xpgDB:DTSNameError",
                                    _("Entry file is an instance/inline, '--xbrlusDB-dts-name' should only be used when the entry file is a taxonomy or linkbase."))
        elif self.modelXbrl.modelDocument.type in (Type.SCHEMA, Type.LINKBASE):
            self.loadType = 'dts'
        else:
            raise XPDBException("xpgDB:unknownEntryType", 
                                _("The entry file does not appear to be an instance, inline, schema or linkbase file.")) 
        
        #lock to prevent another process from updating at the same time.
        self.execute('''LOCK ONLY config 
                     IN ACCESS EXCLUSIVE MODE;''', fetch=False)

        self.loadSource()
        self.timeCall(self.insertSource)
        if self.loadType == 'instance':
            #get filing and entity info
            self.timeCall(self.identifyEntityAndFilingingInfo)
            
            #check if the filing is already in the database
            result = self.timeCall((self.execute, 'check if exists'), "SELECT 1 FROM report WHERE source_report_identifier = '%s' AND source_id = %s;" % (self.accessionNumber, self.sourceId))
            if result:
                self.modelXbrl.info("info", _("%(now)s - Skipped filing already in database. Accession filing number:  %(filingNumber)s"),
                        filingNumber=self.accessionNumber,
                        now=str(datetime.datetime.today()))
                return
            
            #exclusions - This is source dependent
            if self.excludeReport():
                #the excludeReport() method will produce the message
                return      
             
        self.timeCall(self.identifyBaseNamespaces)
        self.timeCall(self.IdentifyAndInsertDTSAndDocuments)
        if self.loadType == 'dts':
            self.timeCall(self.insertTaxonomyAndVersion)
        if self.dtsExists and self.loadType == 'dts':
            self.modelXbrl.info("info", _("%(now)s - DTS is already in the database."), now=str(datetime.datetime.today()))
        else:                        
            self.timeCall(self.identifyConceptsUsed)
            if self.loadType == 'instance':
                self.timeCall(self.insertEntity)
                self.timeCall(self.identifyFiscalYearEnd)
            
            self.timeCall(self.insertQnames)
            self.timeCall(self.insertUris)
            self.timeCall(self.insertNamespaces)
            self.timeCall(self.insertElements)
            self.timeCall(self.insertDTSElements)
            self.timeCall(self.insertCustomArcroles)
            self.timeCall(self.insertCustomRoles)
            
            
            if self.loadType == 'instance':
                self.timeCall(self.insertReport)
                self.timeCall(self.insertReportDocument)
                self.timeCall(self.insertEntityNameHistory)
                self.timeCall(self.insertReportElements)       
                self.timeCall(self.insertFacts)
                self.timeCall(self.updateReportStats)
                self.timeCall(self.postLoad)
        
            self.timeCall(self.insertNetworks)
        
        if getattr(self.options, 'xbrlusDBNoCommit', False):
            self.modelXbrl.info("info", _("%(now)s - Changes not committed"), now=str(datetime.datetime.today()))
        else:
            self.commit()

        #record the final timings
        endTime = datetime.datetime.today()
        hours, remainder = divmod((endTime - self.startTime).total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if not hasattr(self,'loadType'):
            self.modelXbrl.info("info", _("%(now)s - Load process ended %(timeTook)s"),
                timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds),
                now=str(datetime.datetime.today()))
        elif self.loadType == 'instance':
            self.modelXbrl.info("info", _("%(now)s - Loaded report into database in %(timeTook)s %(accessionNumber)s %(companyName)s %(period)s"),
                accessionNumber=self.accessionNumber, 
                companyName=self.entityName, 
                period=self.period,
                timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds),
                now=str(datetime.datetime.today()))
        else:
            self.modelXbrl.info("info", _("%(now)s - Loaded DTS into database in %(timeTook)s %(dtsNumber)s %(dtsName)s"),
                dtsNumber=self.dtsId,
                dtsName=getattr(self.options,'xbrlusDBDTSName', None) or self.entryUrl,
                timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds),
                now=str(datetime.datetime.today())) 
    
    def timeCall(self, functionInfo, *args, **kwargs):
        functionStartTime = datetime.datetime.today()
        if isinstance(functionInfo, tuple):
            function = functionInfo[0]
            note = functionInfo[1]
        else:
            function = functionInfo
            note = None
        result = function(*args, **kwargs)
        if getattr(self.options, 'xbrlusDBTime', False):
            functionEndTime = datetime.datetime.today()
            hours, remainder = divmod((functionEndTime - functionStartTime).total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            self.modelXbrl.info("info", _("%s - %s%s" % ('%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds), function.__name__, ' - ' + note if note else '')))
        return result
        
    def reportTime(self, note=None):
        if getattr(self.options, 'xbrlusDBTime', False):
            if hasattr(self, 'timerStart') and note is not None:
                endTime = datetime.datetime.now()
                hours, remainder = divmod((endTime - self.timerStart).total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.modelXbrl.info("info",_("%(timeTook)s - %(note)s "),
                                              note=note,
                                              timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds))   
            
            self.timerStart = datetime.datetime.now()

    def excludeReport(self):      
        try:
            return self.sourceCall()
        except self._SourceFunctionError:
            return False

    def identifyBaseNamespaces(self):
        self.baseNamespaces = dict()
        # use all namespace URIs
        namespaceUris = self.modelXbrl.namespaceDocs.keys() 

        #check namespace source table
        inListForQuery = '(' +  ','.join("'" + uri + "'" for uri in namespaceUris) + ')'
        results = self.execute('''
            SELECT n.uri, n.prefix, ns.is_base
            FROM namespace n
            JOIN namespace_source ns
              ON n.namespace_id = ns.namespace_id
            WHERE ns.source_id = %s
              AND n.uri in %s
            ''' % (self.sourceId, inListForQuery))
        processedUris = set()
        for uri, prefix, isBase in results:
            processedUris.add(uri)
            if isBase:
                self.baseNamespaces[uri] = prefix
            if not isBase and not self.getSourceSetting("hasExtensions"):
                self.modelXbrl.info("warning",_("For source '%s', namespace '%s' should be base because the source does not allow extensions but the namespace_source table indicates it is not a base namespace." % (self.sourceName, uri)))
        
        #check if there are new namespaces
        newUris = namespaceUris - processedUris
        if len(newUris) != 0:
            #Will be using the base namespaces table to see if there is a match.
            #Make sure the base namespace table is up to date
            self.updateBaseNamespaceTable()
            
            #get base namespace patterns
            results = self.execute("SELECT preface,  prefix_expression FROM base_namespace WHERE source_id = %s;" %self.sourceId)
            namespace_prefaces = [{'preface' :row[0], 'regex': row[1]} for row in results]
            #sort the prefaces so the longest ones are first. This will allow preface like /a/b/c/d to match to /a/b/c before /a/b.
            namespace_prefaces.sort(key=lambda x: x['preface'], reverse=True)
            
            #for each new namespace, find namespace prefixes based on the regular expression in the base_namespace table.
            for uri in newUris:
                matchFound = False
                for preface in namespace_prefaces:
                    if re.search(preface['preface'], uri) is not None:
                        matchFound = True
                        prefix = self.getPrefix(uri, preface['regex'])
                        self.baseNamespaces[uri] = prefix if prefix is not None else self.cleanNCName(uri)
                        self.modelXbrl.info("warning",_("New base namespace found. Check if the namespace should be associated with a taxonomy_version. Namespace is '%s', canonical prefix is '%s'" % (uri, prefix)))
                        #found the match, move on to the next namespace
                        break

                if not self.getSourceSetting("hasExtensions") and not matchFound:
                    #need to force a canonical prefix - use the whole namespace as the canonical prefix
                    self.baseNamespaces[uri] = self.cleanNCName(uri)
    
    def cleanNCName(self, ncname):
        #This function will replace invalid ncname characters with a dash
        if len(ncname) == 0:
            return ncname
        
        #regex for matching ncnames
        nameStart = r'A-Z_a-z\u00C0-\u00D6\u00D8-\u00F6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD'
        nameChar = nameStart + r'\-\.0-9\u00B7\u0300-\u036F\u203F-\u2040'
        nameStartPattern = '[^' + nameStart + ']'
        nameCharPattern = '[^' + nameChar + ']'
        
        cleanName = re.sub(nameStartPattern,'-', ncname[0])
        if len(ncname) > 1:
            cleanName += re.sub(nameCharPattern,'-',ncname[1:])
        
        return cleanName
    
    def updateBaseNamespaceTable(self):
        baseNamespacePatterns = self.getSourceSetting("basePrefixPatterns")
        if baseNamespacePatterns is not None:
            self.getTable('base_namespace', 'base_namespace_id', 
                      ('preface','prefix_expression', 'source_id'), 
                      ('preface','source_id',), 
                      tuple((preface, prefixExpression, self.sourceId)
                            for preface, prefixExpression in baseNamespacePatterns),
                      checkIfExisting=True) 
            
    def getPrefix(self, namespace, expression):
        if namespace is None or expression is None:
            return None
        #get the matched portion of the namespace
        matchedPrefixes = re.findall(expression, namespace)
        prefixSeparator = self.getSourceSetting("basePrefixSeparator") or '-'
        if len(matchedPrefixes) > 0:
            return prefixSeparator.join([x for x in self.getPrefixMatches(matchedPrefixes)])
        else:
            return None
    
    def getPrefixMatches(self, item):
        '''Extracts the re matches from re.findall().'''
        if isinstance(item, (tuple, list)):
            for value in item:
                for subvalue in self.getPrefixMatches(value):
                    yield subvalue
        else:
            yield item
    
    def differentiateBaseNamespaces(self):        
        # the source differentiates base and extension namespaces.       
        def getPrefix(namespace, expression):
            prefix = re.findall(expression, namespace)
            return prefix[0] if prefix else None
        
        # use all namespace URIs
        namespaceUris = self.modelXbrl.namespaceDocs.keys() 
        
        # get list of namespace prefaces that indicate the namespace is base
        results = self.execute("SELECT preface,  prefix_expression FROM base_namespace WHERE source_id = %s;" %self.sourceId)
        namespace_prefaces = [{'preface' :row[0], 'regex': row[1]} for row in results]
        #sort the prefaces so the longest ones are first. This will allow preface like /a/b/c/d to match to /a/b/c before /a/b.
        namespace_prefaces.sort(key=lambda x: x['preface'], reverse=True)
        
        #Find namespace prefixes based on the regular expression in the base_namespace table.
        for uri in namespaceUris:
            #check if the namespace is already in the database
            results = self.execute("SELECT prefix FROM namespace WHERE uri = %s AND is_base", params=(uri,))
            if len(results) > 0:
                self.baseNamespaces[uri] = results[0][0]
            else:
                prefix = None
                for preface in namespace_prefaces:
                    #if uri.startswith(preface['preface']):
                    if re.search(preface['preface'], uri) is not None:
                        self.baseNamespaces[uri] = getPrefix(uri, preface['regex']) if preface['regex'] else None
                        self.modelXbrl.info("warning",_("New base namespace found. Check if the namespace should be associated with a taxonomy_version. Namespace is '%s'" % uri))
                        #found the match, move on to the next namespace
                        break

    def insertTaxonomyAndVersion(self):
        taxonomyName = getattr(self.options, 'xbrlusDBTaxonomyName', None)
        taxonomyVersion = getattr(self.options, 'xbrlusDBTaxonomyVersion', None)
        if taxonomyName is None or taxonomyVersion is None:
            self.taxonomyId = None
            self.taxonomyVersionId = None
        else:
            #add the taxonomy row
            result = self.getTable('taxonomy', 'taxonomy_id',
                                   ('name',),
                                   ('name',),
                                   ((taxonomyName,),),
                                   checkIfExisting=True,
                                   returnExistenceStatus=True)
            self.taxonomyId = result[0][0]
            if result[0][2]: #existence status
                self.modelXbrl.info("info", _("Taxonomy %s exists" % taxonomyName))
            else:
                self.modelXbrl.info("info", _("Taxonomy %s is new" % taxonomyName))

            taxonomyVersionDocument = getattr(self.options, 'xbrlusDBTaxonomyVersionDocument', None)
            if taxonomyVersionDocument is None:
                taxonomyVersionDocumentId = None
            else:
                taxonomyVersionDocumentId = self.documentIds.get(self.mapDocumentUri(taxonomyVersionDocument))
                if taxonomyVersionDocumentId is None:
                    raise XPDBException("xpgDB:taxonomyVersionDcoumentError", 
                                    _("The taxonomy version identifying document provided is not in the DTS"))

            #add the taxonomy_version row
            result = self.getTable('taxonomy_version', 'taxonomy_version_id',
                                   ('taxonomy_id', 'version', 'identifier_document_id'),
                                   ('taxonomy_id', 'version'),
                                   ((self.taxonomyId, taxonomyVersion, taxonomyVersionDocumentId),),
                                   checkIfExisting=True,
                                   returnExistenceStatus=True)
            
            self.taxonomyVersionId = result[0][0]
            if result[0][3]: #existence status
                if taxonomyVersionDocument: #a taxonomy version document was provided
                    #check if the the taxonomy version document is the same
                    result = self.execute("SELECT identifier_document_id FROM taxonomy_version WHERE taxonomy_id = {} AND version = '{}';".format(self.taxonomyId, taxonomyVersion))
                    if len(result) != 1:
                        raise XPDBException("xpgDB:taxonomyVersionDcoumentError", 
                                    _("Querying taxonomy_version. Only expected one result but got {} for taxonomy id {} and version '{}'.".format(len(result), self.taxonomyId, taxonomyVersion)))
                    if result[0][0] != taxonomyVersionDocumentId:
                        raise XPDBException("xpgDB:taxonomyVersionDcoumentError", 
                                    _("A taxonomy version identifying document already exists for the dts but is different."))
                self.modelXbrl.info("info", _("Taxonomy version %s exists" % taxonomyVersion))
            else:
                self.modelXbrl.info("info", _("Taxonomy version %s is new" % taxonomyVersion))
            
            #add taxonomy_version_dts record for the dts
            result = self.getTable('taxonomy_version_dts', 'taxonomy_version_dts_id',
                          ('taxonomy_version_id', 'dts_id'),
                          ('taxonomy_version_id', 'dts_id'),
                          ((self.taxonomyVersionId, self.dtsId),),
                          checkIfExisting=True,
                          returnExistenceStatus=True)
            
            if result[0][3]: #taxonomy_version_dts row exists
                self.modelXbrl.info("info", _("DTS and taxonomy version combination already exists"))
            else:
                self.modelXbrl.info("info", _("DTS and taxonomy version combination added"))
            
    def identifyEntityAndFilingingInfo(self):
        
        try:
            info =  self.sourceCall()
        except self._SourceFunctionError:
            info = dict()
            
        commonInfoNames = ('acceptanceDate', 'accessionNumber', 'entityName', 'entityScheme', 'entityIdentifier', 'entryUrl', 'alternativeDoc', 'period', 'sourceUriMap')
        self.sourceData = dict()
        for k, v in info.items():
            if k in commonInfoNames:
                setattr(self, k, v)
            else:
                self.sourceData[k] = v

        #fill in defaults
        self.defaultEntityAndFilingInfo()              

    def defaultEntityAndFilingInfo(self):
        #Certain information is necessary to process a filing.
        
        #default to the file passed an an argument
        if getattr(self, 'entryUrl', None) is None:
            self.entryUrl = self.cleanDocumentUri(self.modelXbrl.modelDocument)
                
        # default the entity name
        if not self.entityName:
            self.entityName = 'UNKNOWN'
        
        if getattr(self, "accessionNumber", None) is None:
            #see if it was passed as an option
            #self.accessionNumber = getattr(self.options, "xbrlusDBFilingId", None)
            self.accessionNumber = self.options.xbrlusDBInfos.get('filing-id')
            if self.accessionNumber is None:
                raise XPDBException("xpgDB:missingFilingId", 
                                    _("Cannot determine the filing identifier"))
                
        if getattr(self, "entityIdentifier", None) is None or getattr(self, "entityScheme", None) is None:
            #get it from  a context. This assumes that every context will have the same entity scheme and identifier.
            if len(self.modelXbrl.contexts) > 0:
                #Get the first alphabetic context.
                context = self.modelXbrl.contexts[sorted(self.modelXbrl.contexts.keys())[0]]
                if getattr(self, "entityIdentifier", None) is None:
                    self.entityIdentifier = context.entityIdentifier[1] # entityIdentifier is a tuple 0 = scheme, 1 = identifier
                if getattr(self, "entityScheme", None) is None:
                    self.entityScheme = context.entityIdentifier[0]
            else:
                raise XPDBException("xpgDB:missingEntityInformation",
                                    _("Cannot determine the entity scheme and/or identifier."))
      
        if getattr(self, "acceptanceDate", None) is None:
            self.acceptanceDate = getattr(self, "acceptanceDate", datetime.datetime.now())

    @contextmanager
    def getFile(self, fileName):
        try:
            fileHandle = open(fileName, 'rb')
        except (OSError, IOError):
            #try open from web address
            fileHandle = urllib.request.urlopen(fileName)
        yield fileHandle
        fileHandle.close()
    
    def isUrl(self, url):
        if re.match('https?:', url):
            return True
        else:
            return False
    
    def insertEntity(self):
        '''
        Going to try and get the entity name and cik from the rssItem. If there is no rssItem then
        will try to get it from the facts for the filing.
        '''
        table = self.getTable('entity', 'entity_id', 
                      ('entity_name','entity_code', 'authority_scheme'), 
                      ('entity_code',), 
                      ((self.entityName,
                        self.entityIdentifier,
                        self.entityScheme
                        ),),
                      checkIfExisting=True)
        for id, x in table:
            self.entityId = id
            
        self.getTable('entity_source', 'entity_source_id',
                    ('entity_id', 'source_id'),
                    ('entity_id', 'source_id'),
                    ((self.entityId, self.sourceId),),
                    checkIfExisting=True
                    )

    def identifyFiscalYearEnd(self):
        try:
            self.fiscalYearMonthEnd, self.fiscalYearDayEnd = self.sourceCall()
        except self._SourceFunctionError:
            self.fiscalYearMonthEnd = None
            self.fiscalYearDayEnd = None

    def insertEntityNameHistory(self):
        #delete existing records that where added after this filing. This handles resetting the entity name history if the filings are processed in order.
        self.execute('''DELETE FROM entity_name_history 
                        WHERE accession_id IN
                        (SELECT report_id
                         FROM report
                         WHERE entity_id = %s
                           AND accepted_timestamp >= %s)''', params=(self.entityId, self.acceptedTimestamp),
                     fetch=False)
        #get the current entity name
        result = self.execute('''SELECT enh.entity_name
                        FROM entity_name_history enh
                        JOIN report r
                          ON enh.accession_id = r.report_id
                        WHERE r.entity_id = {0}
                        ORDER BY r.accepted_timestamp DESC
                        LIMIT 1'''.format(self.entityId))
        if len(result) == 1:
            currentEntityName = result[0][0]
        else:
            currentEntityName = None
          
        #get all the accessions after and including the processing accession.
        result = self.execute('''SELECT report_id, trim(both entity_name) 
                        FROM report
                        WHERE entity_id = %s
                          AND accepted_timestamp >= %s
                        ORDER BY accepted_timestamp''', params=(self.entityId, self.acceptedTimestamp))

        if len(result) > 0:
            rowsToAdd = []
            for accessionRow in result:
                if accessionRow[1] != currentEntityName:
                    #add an entity name history record
                    rowsToAdd.append((self.entityId, accessionRow[0], accessionRow[1]))
                    currentEntityName = accessionRow[1]
                
            if len(rowsToAdd) > 0:  
                self.getTable('entity_name_history', 'entity_name_history_id',
                              ('entity_id','accession_id','entity_name'),
                              ('entity_id','accession_id','entity_name'),
                              rowsToAdd
                              )
            #update entity with the latest name
        #if self.entityName != rowsToAdd[-1][2]:
                self.entityName = rowsToAdd[-1][2]
                self.updateTable('entity',('entity_id', 'entity_name'),((self.entityId, self.entityName),))
                
    def getSimpleFactByQname(self, partialNS, localName):
        simpleFacts = [item for item in self.modelXbrl.facts 
                                    if item.qname.localName == localName
                                    and re.search(partialNS, item.qname.namespaceURI) is not None
                                    #and partialNS in item.qname.namespaceURI
                                    and len(item.context.qnameDims) == 0]      
        if len(simpleFacts) > 0:
            return simpleFacts[0].textValue
    
    def insertReport(self):
        #defaults for accession id
        self.accessionId = "(TBD)"
        
        if (self.modelXbrl.modelDocument.creationSoftwareComment is not None and
            len(self.modelXbrl.modelDocument.creationSoftwareComment) > 0):
            creationSoftware = self.modelXbrl.modelDocument.creationSoftwareComment.splitlines()[0].strip()
        else:
            creationSoftware = None
        
        if self.modelXbrl.modelDocument.type == Type.INSTANCE:
            entryType = 'instance'
        elif self.modelXbrl.modelDocument.type == Type.INLINEXBRL:
            entryType = 'inline'
        else:
            entrytype = 'UNKNOWN'
        
        #the alternative doc is usually an html version of a report
        alternativeDoc = self.mapDocumentUri(self.alternativeDoc) if hasattr(self,'alternativeDoc') else None
        #add the alternative doc to the database
        self.insertDocuments((alternativeDoc,))

        reportProperties = self.reportProperties()

        table = self.getTable('report', 'report_id',
                            ('source_id', 'entity_id', 'dts_id', 'entry_dts_id', 'source_report_identifier', 'accepted_timestamp',
                             'entity_name', 'creation_software', 'entry_type', 'entry_url', 'entry_document_id',
                             'alternative_document_id', 'reporting_period_end_date', 'properties'),
                            ('source_id', 'source_report_identifier', 'accepted_timestamp'),
                            ((self.sourceId,
                             self.entityId,
                             self.dtsId,
                             self.entryDtsId,
                             self.accessionNumber,
                             self.acceptanceDate,
                             self.entityName,
                             creationSoftware,
                             entryType,
                             getattr(self, "entryUrl", None),
                             self.documentIds[self.cleanDocumentUri(self.modelXbrl.modelDocument)],
                             self.documentIds[alternativeDoc] if alternativeDoc is not None else None,
                             self.period,
                             reportProperties
                             ),),
                            checkIfExisting=True)
 
        for report_id, source_id, source_report_identifier, acceptedTimestamp in table:
            self.accessionId = report_id
            #The returned value is a modelBalue.DateTime, but we need it as a python datetime
            self.acceptedTimestamp = datetime.datetime(acceptedTimestamp.year, acceptedTimestamp.month, acceptedTimestamp.day, acceptedTimestamp.hour, acceptedTimestamp.minute, acceptedTimestamp.second, acceptedTimestamp.microsecond)
            break

    def reportProperties(self):
        try:
            return self.sourceCall()
        except self._SourceFunctionError:
            pass        
        
        return json.dumps({})
          
    def insertUris(self):
        uris = (_DICT_SET(self.modelXbrl.namespaceDocs.keys()) |
                _DICT_SET(self.modelXbrl.arcroleTypes.keys()) |
                _DICT_SET(XbrlConst.standardArcroleCyclesAllowed.keys()) |
                _DICT_SET(self.modelXbrl.roleTypes.keys()) |
                XbrlConst.standardRoles)
        self.showStatus("insert uris")
        table = self.getTable('uri', 'uri_id', 
                              ('uri',), 
                              ('uri',), # indexed match cols
                              tuple((uri.strip(),) 
                                    for uri in uris),
                              checkIfExisting=True)
        self.uriId = dict((uri, id)
                          for id, uri in table)
                     
    def insertQnames(self):
        #attributes
        attributeQNames = set()
        for concept in self.newDocumentConcepts | self.newNonReportingConcepts:
            for atrribName, attribValue in concept.attrib.items():
                if atrribName not in ('abstract','id','nillable','type','substitutionGroup','name'):
                    attribQName = qname(atrribName)
                    if not (attribQName.namespaceURI == 'http://www.xbrl.org/2003/instance' and attribQName.localName in ('balance','periodType')):
                        #self.attributeQNames.append((self.getQnameId(concept.qname),self.getQNameId(attribQName),attribValue))
                        attributeQNames.add(attribQName)        
            
        qnames = (_DICT_SET(self.modelXbrl.qnameTypes.keys()) |
                  set(measure
                      for unit in self.modelXbrl.units.values()
                      for measures in unit.measures
                      for measure in measures) |
                  set(concept.qname for concept in self.newDocumentConcepts | self.newNonReportingConcepts) |
                  attributeQNames 
                  )
        
        self.showStatus("insert qnames")
        table = self.getTable('qname', 'qname_id', 
                              ('namespace', 'local_name'), 
                              ('namespace', 'local_name'), # indexed match cols
                              tuple((qn.namespaceURI, qn.localName) 
                                    for qn in qnames),
                              checkIfExisting=True)

        self.qnameId = dict((qname(ns or '', ln), id)
                            for id, ns, ln in table)

        # get qnames for existing used concepts
        existingUsedQnames = self.conceptsUsed - qnames
        if len(existingUsedQnames) > 0:
            valuesClauseQnames = ("('" + x.namespaceURI + "','" + x.localName + "')" for x in existingUsedQnames)
            valuesClause = '(VALUES ' + ','.join(valuesClauseQnames) + ' ) x(namespace, local_name)'
            
            query = '''SELECT q.qname_id, q.namespace, q.local_name
                       FROM qname q
                       JOIN ''' + valuesClause + '''
                         ON q.namespace = x.namespace
                        AND q.local_name = x.local_name'''
            results = self.execute(query)
            for qnameId, namespaceURI, localName in results:
                self.qnameId[qname(namespaceURI, localName)] = qnameId        
      
    def insertNamespaces(self):
        self.showStatus("insert namespaces")
        namespaceUris = {x.namespaceURI for x in self.qnameId.keys() if x.namespaceURI is not None} | self.modelXbrl.namespaceDocs.keys()
        #namespaceUris = self.modelXbrl.namespaceDocs.keys()               

        table = self.getTable('namespace', 'namespace_id', 
                              ('uri', 'is_base', 'taxonomy_version_id', 'prefix'), 
                              ('uri',), # indexed matchcol
                              tuple((uri, 
                                     uri in self.baseNamespaces.keys() if self.loadType == 'instance' else True, #this is an assumption that if this is a dts load than the namespaces are base
                                     None, 
                                     self.baseNamespaces[uri] if uri in self.baseNamespaces.keys() else None) 
                                    for uri in namespaceUris),
                              checkIfExisting=True)
        namespaceId = {uri : id for id, uri in table}

        self.getTable('namespace_source', 'namespace_source_id',
                      ('namespace_id', 'source_id', 'is_base'),
                      ('namespace_id', 'source_id'),
                      tuple((namespaceId[uri], self.sourceId, uri in self.baseNamespaces) 
                            for uri in namespaceUris),
                      #tuple((ns['id'], self.sourceId, ns['isBase']) for ns in namespaceId.values()),
                      checkIfExisting=True)

    def insertSource(self):
        #check in database
        table = self.getTable('source', 'source_id',
                              ('source_name',),
                              ('source_name',),
                              ((self.sourceName,),),
                              checkIfExisting=True,
                              returnExistenceStatus=True)
        
        if len(table) != 1:
            raise XPDBException("xpgDB:sourceTableError",
                    _("Problem checking or adding source '%s'" % self.sourceName)) 

        self.sourceId = table[0][0]
        if table[0][2] == False: #new source
            #load the pre and post functions
            databaseInstall = self.getSourceSetting('databaseInstall')
            if databaseInstall is not None:
                self.execute(databaseInstall, fetch=False)

            #add base namespaces
            self.updateBaseNamespaceTable()
            
            self.modelXbrl.info("info", _("New source '%(source)s'"),
                        source=self.sourceName)

    def IdentifyAndInsertDTSAndDocuments(self):
        #create a map between original document uris and cleaned document uris
        self.docCleanUriMap = {self.cleanDocumentUri(modelDoc): modelDoc for modelDoc in self.modelXbrl.urlDocs.values()}
        #identify base sets for the dts and the instance
        self.instanceBaseSets = list()
        self.dtsBaseSets = list()
        for (arcrole, ELR, linkqname, arcqname), baseSet in self.modelXbrl.baseSets.items():
            isInstance = False
            if ELR and linkqname and arcqname and not arcrole.startswith("XBRL-"):
                if self.loadType == 'instance':
                    if len(baseSet) > 0:
                        if baseSet[0].modelDocument is self.modelXbrl.modelDocument:
                            isInstance = True
                if isInstance:
                    self.instanceBaseSets.append((arcrole, ELR, linkqname, arcqname))
                else:
                    self.dtsBaseSets.append((arcrole, ELR, linkqname, arcqname))

        #walk documents for dts
        #if this is an instance load, the dts are the documetns the instance points to, otherwise, the dts is the main document of the model.
        dtsDocuments = self.walkDocumentTree(self.modelXbrl.modelDocument.referencesDocument.keys() if self.loadType == 'instance' else (self.modelXbrl.modelDocument,))
        self.dtsId, self.dtsExists = self.addDTSRows(dtsDocuments)
        self.dtsDocuments = {self.docCleanUriMap[x[0]] for x in dtsDocuments}
        if self.dtsExists:
            self.documentIds = self.getDTSDocumentIds()
            self.existingDocumentIds = self.documentIds.copy()
        else:
            #add the documents
            self.insertDocuments({x[0] for x in dtsDocuments})
            self.insertDocumentRelationships(dtsDocuments)
            #add dts_documents
            self.addDTSDocuments(self.dtsId, dtsDocuments)
        #At this point the only documents in documentIds are the dts documents
        self.dtsDocumentIds = self.documentIds.copy()
        
        #add the instance document
        if self.loadType == 'instance':
            cleanInstDocumentUri = self.cleanDocumentUri(self.modelXbrl.modelDocument)
            self.insertDocuments({cleanInstDocumentUri,})
            instDocuments = ((cleanInstDocumentUri, 
                             True, 
                             tuple(self.cleanDocumentUri(x) for x in self.modelXbrl.modelDocument.referencesDocument.keys())),)
            self.insertDocumentRelationships(instDocuments)          
            #add dts record for footnotes in the instance        
            if len(self.instanceBaseSets) > 0:
                self.entryDtsId, instanceDTSExists = self.addDTSRows(instDocuments)
                #need to create a dts for these base sets. The dts will be based on the instance.
                if instanceDTSExists:
                    raise XPDBException("xpgDB:instanceDTSExists",
                            _("Instance DTS is already in the database."))
                else:
                    self.addDTSDocuments(self.entryDtsId, instDocuments)   
            else:
                self.entryDtsId = None
        
        #check that no uris were missed.
        missingUris = self.docCleanUriMap.keys() - self.documentIds.keys() 
        if len(missingUris) > 0:
#             raise XPDBException("xpgDB:missingDocuments",
#                                 _("Did not process the following documents: %s" % "\n".join(missingUris)))
            self.modelXbrl.info("info",_("Did not process the following documents: %s" % "\n".join(missingUris)))
            
    def insertDTSElements(self):
        #add dts_element records
        if not self.dtsExists:
            #find elements in relationships
            relationshipElements = set()
            for relationshipSetKey in self.dtsBaseSets:
                relationshipSet = self.modelXbrl.relationshipSet(*relationshipSetKey)
                for rel in relationshipSet.modelRelationships:
                    if isinstance(rel.fromModelObject, ModelConcept):
                        relationshipElements.add(rel.fromModelObject)
                    if isinstance(rel.toModelObject, ModelConcept):
                        relationshipElements.add(rel.toModelObject)
    
            #find elements defined in the dts but don't have relationships
#             documentElements = set()
#             for concept in self.modelXbrl.qnameConcepts.values():
#                 if concept.modelDocument in self.dtsDocuments and concept.isItem and concept.qname.namespaceURI != 'http://www.xbrl.org/2003/instance' and concept.qname.namespaceURI != 'http://xbrl.org/2005/xbrldt':
#                     documentElements.add(concept)    
            
#             for c in (relationshipElements | documentElements):
#                 print(c.qname)
#                 print(self.elementId[self.getQnameId(c.qname)])
            
            self.getTable('dts_element', 'dts_element_id',
                          ('dts_id', 'element_id', 'is_base', 'in_relationship'),
                          ('dts_id', 'element_id'),
                          tuple((self.dtsId, 
                                 self.elementId[self.getQnameId(c.qname)], 
                                 c.qname.namespaceURI in self.baseNamespaces if self.loadType == 'instance' else False, 
                                 c in relationshipElements) 
                                #for c in (relationshipElements | documentElements)))   
                                for c in relationshipElements))                       

    def walkDocumentTree(self, parents, resultDocs=None, processed=None, top=True):
        if resultDocs is None:
            resultDocs = set()
        if processed is None:
            processed = set()
        for parent in parents:
            cleanParentUri = self.cleanDocumentUri(parent)
            if cleanParentUri not in processed:
                processed.add(cleanParentUri)
                resultDocs.add((cleanParentUri, top, tuple(self.cleanDocumentUri(x) for x in parent.referencesDocument.keys())))
                resultDocs = self.walkDocumentTree(parent.referencesDocument.keys(), resultDocs, processed, False)
                    
        return resultDocs

    def addDTSRows(self, dtsDocuments):
        #only include docuemnts directly referenced from the  
        topDocs = tuple(docUri for docUri, isTop, _x in dtsDocuments if isTop)
        refDocsString = '|'.join(sorted(topDocs))
        dtshash = hashlib.sha224(refDocsString.encode()).digest()
        dtsName = getattr(self.options,'xbrlusDBDTSName',None) if self.loadType == 'dts' else None
                
        table = self.getTable('dts', 'dts_id',
                              ('dts_hash','dts_name'),
                              ('dts_hash',),
                              ((dtshash,
                                dtsName),),
                              checkIfExisting=True,
                              returnExistenceStatus=True)
        dtsId = table[0][0]
                        
        return dtsId, table[0][2] #existence

    def addDTSDocuments(self, dtsId, dtsDocuments):
        refDocIds = tuple((dtsId, self.documentIds[x[0]], x[1]) for x in dtsDocuments)
        self.getTable('dts_document', 'dts_document_id',
                      ('dts_id', 'document_id','top_level'),
                      ('dts_id', 'document_id'),
                      refDocIds)


    def insertDocumentRelationships(self, docs):
        #docs is a set of tuples. The tuples are 0 = clean parent uri, 1 = is top, 2 = clean child uri
        self.getTable('document_structure', 'document_structure_id',
                      ('parent_document_id', 'child_document_id'),
                      ('parent_document_id', 'child_document_id'),
                      tuple((self.documentIds[docInfo[0]], self.documentIds[childDoc]) for docInfo in docs for childDoc in docInfo[2]))
                      
    def insertDocuments(self, docUris):
        #Determine if the document is in the database
        query = '''
            SELECT d.document_id, a.document_uri, d.document_loaded, d.document_id IS NOT NULL AS existing
            FROM (VALUES %s) a(document_uri)
            LEFT JOIN document d
              ON a.document_uri = d.document_uri;
        ''' % ','.join(tuple("('" + x + "')" for x in docUris))
        docResults = self.execute(query)
        existingDocumentIds = dict()
        documentIds = dict()
        docsToLoad = dict()
        docsToUpdate = dict()
        for docId, docUri, docLoaded, docExisting in docResults:
            #add existing documents to the dictionary of document ids
            if docExisting:
                documentIds[docUri] = docId
                
            if docExisting and docLoaded:
                existingDocumentIds[docUri] = docId
            else:
                filePath = None
                modelDocument = self.docCleanUriMap.get(docUri)
                #modelDocument will be none for an alternative document (usually the html document) and the content for these are loaded into the database.
                if modelDocument is None:
                    filePath = docUri
                    targetNamespace = None
                else:
                    if modelDocument.type == Type.INLINEXBRL and modelDocument is self.modelXbrl.modelDocument:
                        filePath = modelDocument.filepath
                    targetNamespace = modelDocument.targetNamespace
                    
                if filePath is not None:
                    with self.getFile(filePath) as inlineFile:
                        docContent = inlineFile.read().decode()
                    #docContent = etree.tostring(doc.xmlDocument, encoding=doc.documentEncoding)
                else:                    
                    docContent = None
                if docExisting: #its in the database but not loaded.
                    docsToUpdate[docUri] = (docId, targetNamespace, docContent)
                else:
                    docsToLoad[docUri] = (targetNamespace, docContent)
        
        # At this point the documents are devided into 3 dictionaries, existing, to load, and to update.      
        # Add new docs
        if len(docsToLoad) > 0:
            table = self.getTable('document', 'document_id', 
                          ('document_uri','content', 'document_loaded', 'target_namespace', 'document_type'), 
                          ('document_uri',), 
                          tuple((uri, content, True, targetNamespace, self.determineDocumentType(uri)) for uri, (targetNamespace, content) in docsToLoad.items()),
                          checkIfExisting=True,
                          returnExistenceStatus=True)
            for docId, docUri, docExisting in table:
                if docExisting:
                    raise XPDBException("xpgDB:existingDocument",
                        _("Trying to add document that is already in the database. %s" % docUri))
                documentIds[docUri] = docId
        #update documents where there is a record in the database but it was not loaded. This can happen if a DBA adds document records for new taxonomies, but no
        #filings for that taxonomy have been added to the database. This is not common.
        if len(docsToUpdate) > 0:
            updateData = tuple((docId, docContent, True, targetNamespace) for docUrl, (docId, targetNamepace, content) in docsToUpdate.items())
            self.updateTable('document', ('document_id', 'content', 'document_loaded', 'target_namespace'), updateData)
            #the document ids are already in the documentIds dictionary.
        
        if hasattr(self,'documentIds'):
            self.documentIds.update(documentIds)
        else:
            self.documentIds = documentIds
            
        if hasattr(self, 'existingDocumentIds'):
            self.existingDocumentIds.update(existingDocumentIds)
        else:
            self.existingDocumentIds = existingDocumentIds

    def getDTSDocumentIds(self):
        query = '''
            SELECT d.document_id, d.document_uri
            FROM document d
            JOIN dts_document dd
              ON d.document_id  = dd.document_id
            WHERE dd.dts_id = %s
            ''' % self.dtsId
        
        results = self.execute(query)
        documentIds = {row[1]: row[0] for row in results}
        return documentIds
    
    def determineDocumentType(self, docUri):
        try:
            modelDoc = self.docCleanUriMap[docUri]
        except KeyError:
            #the document is not in the model
            file_ext = os.path.splitext(docUri)[1].lower()
            if file_ext in ('.htm', '.html', '.txt'):
                return 'report'
            else:
                return None
        
        if modelDoc.type == Type.SCHEMA:
            return 'schema'
        elif modelDoc.type == Type.LINKBASE:
            return 'linkbase'
        elif modelDoc.type == Type.INSTANCE:
            return 'instance'
        elif modelDoc.type == Type.INLINEXBRL:
            return 'inline'
        else:
            return None
#     def identifyAndInsertDocuments(self):
#         #Determine if the document is in the database
#         docUris = set()
#         for modelDocument in self.modelXbrl.urlDocs.values():
#             docUris.add('(' + self.dbStr(self.cleanDocumentUri(modelDocument)) + ',' + self.dbStr(modelDocument.uri) + ')')
#         query = '''
#             SELECT d.document_id, a.document_uri, a.original_uri, d.document_loaded, d.document_id IS NOT NULL AS existing
#             FROM (VALUES %s) a(document_uri, original_uri)
#             LEFT JOIN document d
#               ON a.document_uri = d.document_uri;
#         ''' % ','.join(docUris)
#         docResults = self.execute(query)
#         self.existingDocumentIds = dict()
#         self.documentIds = dict()
#         docsToLoad = dict()
#         docsToUpdate = dict()
#         for docId, docUri, docOriginalUri, docLoaded, docExisting in docResults:
#             #add existing documents to the dictionary of document ids
#             if docExisting:
#                 self.documentIds[docUri] = docId
#                 
#             if docExisting and docLoaded:
#                 self.existingDocumentIds[docUri] = docId
#             else:
#                 modelDocument = self.modelXbrl.urlDocs[docOriginalUri]
#                 if modelDocument.type == Type.INLINEXBRL and modelDocument is self.modelXbrl.modelDocument:
#                     with self.getFile(modelDocument.filepath) as inlineFile:
#                         docContent = inlineFile.read().decode()
#                     #docContent = etree.tostring(doc.xmlDocument, encoding=doc.documentEncoding)
#                 else:                    
#                     docContent = None
#                 if docExisting: #its in the database but not loaded.
#                     docsToUpdate[docUri] = (docId, docContent)
#                 else:
#                     docsToLoad[docUri] = docContent
#         
#         # At this point the documents are devided into 3 dictionaries, existing, to load, and to update.      
#         # Add new docs
#         if len(docsToLoad) > 0:
#             table = self.getTable('document', 'document_id', 
#                           ('document_uri','content', 'document_loaded'), 
#                           ('document_uri',), 
#                           tuple((uri, content, True) for uri, content in docsToLoad.items()),
#                           checkIfExisting=True,
#                           returnExistenceStatus=True)
#             for docId, docUri, docExisting in table:
#                 if docExisting:
#                     raise XPDBException("xpgDB:existingDocument",
#                         _("Trying to add document that is already in the database. %s" % docUri))
#                 self.documentIds[docUri] = docId
#         #update documents where there is a record in the database but it was not loaded. This can happen if a DBA adds document records for new taxonomies, but no
#         #filings for that taxonomy have been added to the database. This is not common.
#         if len(docsToUpdate) > 0:
#             updateData = tuple((docId, docContent, True) for docUrl, docId, content in docsToUpdate.items())
#             self.updateTable('document', ('document_id', 'content', 'document_loaded'), updateData)
#             #the document ids are already in the self.documentIds dictionary.
            
#     def identifyPreexistingDocuments(self):
#         self.existingDocumentIds = {}
#         docUris = set()
#         for modelDocument in self.modelXbrl.urlDocs.values():
#             if modelDocument.type == Type.SCHEMA:
#                 docUris.add(self.dbStr(self.cleanDocumentUri(modelDocument)))
#         if docUris:
#             results = self.execute("SELECT document_id, document_uri, document_loaded FROM document WHERE document_uri IN (" +
#                                    ', '.join(docUris) + ");")
#             self.existingDocumentIds = dict((docUri,docId) for docId, docUri, docLoaded in results if docLoaded == True)
#             self.setDocumentIdsLoaded = tuple((docId, docUri) for docId, docUri, docLoaded in results if docLoaded == False)
# 
#     def insertDocuments(self):
#         self.showStatus("insert documents")
#     
#         docsToLoad = dict()
#         for doc in self.modelXbrl.urlDocs.values():
#             docUri = self.cleanDocumentUri(doc)
#             if docUri not in self.existingDocumentIds:
#                 if doc.type == Type.INLINEXBRL and doc is self.modelXbrl.modelDocument:
#                     with self.getFile(doc.filepath) as inlineFile:
#                         docContent = inlineFile.read().decode()
#                     #docContent = etree.tostring(doc.xmlDocument, encoding=doc.documentEncoding)
#                 else:                    
#                     docContent = None
#                 docsToLoad[docUri] = docContent
#         
#         if hasattr(self, "alternativeDoc"):
#             alternativeDocUri = self.mapDocumentUri(self.alternativeDoc)
#             if alternativeDocUri not in docsToLoad:
#                 with self.getFile(self.alternativeDoc) as htmlFile:
#                     docsToLoad[alternativeDocUri] = htmlFile.read().decode()
#         '''
#         if self.modelXbrl.modelDocument.type == Type.INSTANCE and hasattr(self, "htmlInstance"):
#             with self.getFile(self.htmlInstance) as htmlFile:
#                 docsToLoad[self.htmlInstance] = htmlFile.read().decode()
#         '''
#         table = self.getTable('document', 'document_id', 
#                               ('document_uri','content', 'document_loaded'), 
#                               ('document_uri',), 
#                               tuple((uri, content, True) for uri, content in docsToLoad.items()),
#                               checkIfExisting=True,
#                               returnExistenceStatus=True)
#         self.documentIds = dict()
#         updateLoaded = set()
#         for id, uri, loaded, existed in table:
#             self.documentIds[uri] = id
#             if existed and loaded:
#                 #add to existing list. This is used to determine which concepts to load
#                 self.existingDocumentIds[uri] = id
#             if existed and not loaded:
#                 #update loaded status
#                 updateLoaded.add(id)
#         #update loaded status
#         if len(updateLoaded) > 0:
#             docIds = updateLoaded.join(',')
#             self.execute('UPDATE document SET document_loaded = true WHERE document_id in (%s)' % docIds)
# 
#         updateData = [(docId, True) for docId, docUrl in self.setDocumentIdsLoaded]
#         updateIds = self.updateTable('document', ('document_id', 'document_loaded'), updateData)
#         
#         loadedDocs = dict((docUri, docId) for docId, docUri in self.setDocumentIdsLoaded)
#         self.documentIds.update(loadedDocs)
        
    def identifyConceptsUsed(self):
        # relationshipSets are a dts property
        self.relationshipSets = [(arcrole, ELR, linkqname, arcqname)
                                 for arcrole, ELR, linkqname, arcqname in self.modelXbrl.baseSets.keys()
                                 if ELR and (arcrole.startswith("XBRL-") or (linkqname and arcqname))]
        
        conceptsUsed = set(f.qname for f in self.modelXbrl.factsInInstance)
        
        #this will contain concpets in facts
        reportElements = dict()
        
        def reportElementsIncrement(conceptQname, useType):
            if conceptQname not in reportElements:
                reportElements[conceptQname] = {'primary': 0, 'dimension': 0, 'member': 0, 'isBase': conceptQname.namespaceURI in self.baseNamespaces}
            reportElements[conceptQname][useType] += 1
        
        for f in self.modelXbrl.factsInInstance:
            reportElementsIncrement(f.qname, 'primary')
            if f.context is not None:
                for dim in f.context.qnameDims.values():
                    reportElementsIncrement(dim.dimensionQname, 'dimension')
                    if dim.isExplicit:
                        reportElementsIncrement(dim.memberQname, 'member')
        
        self.reportElements = reportElements
        
        for cntx in self.modelXbrl.contexts.values():
            for dim in cntx.qnameDims.values():
                conceptsUsed.add(dim.dimensionQname)
                if dim.isExplicit:
                    conceptsUsed.add(dim.memberQname)
                else:
                    conceptsUsed.add(dim.typedMember.qname)
                    
        for defaultDim, defaultDimMember in self.modelXbrl.qnameDimensionDefaults.items():
            conceptsUsed.add(defaultDim)
            conceptsUsed.add(defaultDimMember)
        '''
        for relationshipSetKey in self.relationshipSets:
            relationshipSet = self.modelXbrl.relationshipSet(*relationshipSetKey)
            for rel in relationshipSet.modelRelationships:
                if isinstance(rel.fromModelObject, ModelConcept):
                    conceptsUsed.add(rel.fromModelObject)
                    conceptsUsedIncrement(rel.fromModelObject.qname, None)
                if isinstance(rel.toModelObject, ModelConcept):
                    conceptsUsed.add(rel.toModelObject)
                    conceptsUsedIncrement(rel.toModelObject.qname, None)
        '''            
#         for qn in (XbrlConst.qnXbrliIdentifier, XbrlConst.qnXbrliPeriod, XbrlConst.qnXbrliUnit):
#             conceptsUsed.add(self.modelXbrl.qnameConcepts[qn])
        conceptsUsed |= {XbrlConst.qnXbrliIdentifier, XbrlConst.qnXbrliPeriod, XbrlConst.qnXbrliUnit}
        conceptsUsed -= {None}  # remove None if in conceptsUsed
        self.conceptsUsed = conceptsUsed
        
        #Determine which concepts are new. This will reduce the number of concepts and qnames to load.
        self.newDocumentConcepts = set()
#         self.existingDocumentUsedConcepts = set()
        #self.existingDocumentConcepts = set()
        self.newNonReportingConcepts = set()
        for concept in self.modelXbrl.qnameConcepts.values():
            if self.cleanDocumentUri(concept.modelDocument) not in self.existingDocumentIds:
                 #if concept.qname.namespaceURI != 'http://www.xbrl.org/2003/instance': # and concept.qname.namespaceURI != 'http://xbrl.org/2005/xbrldt':
                    if (concept.isItem or concept.isTuple) and not concept.qname.namespaceURI == 'http://www.xbrl.org/2003/instance' :
                        self.newDocumentConcepts.add(concept)
                    else:
                        self.newNonReportingConcepts.add(concept)
#                 else:
#                     if concept.qname.namespaceURI not in ('http://www.xbrl.org/2003/instance','http://www.xbrl.org/2003/XLink','http://www.xbrl.org/2003/linkbase'):
#                         self.newNonReportingConcepts.add(concept)
#                 else:
#                     #self.existingDocumentConcepts.add(concept)
#                     if concept.qname in self.conceptsUsed:
#                         self.existingDocumentUsedConcepts.add(concept)

                
    def cleanDocumentUri(self, doc):
        if doc.filepathdir.endswith('.zip'):
            pathParts = doc.filepathdir.split('/')
            pathParts.pop()
            pathParts.append(doc.basename)
            return self.mapDocumentUri('/'.join(pathParts))
        else:
            return self.mapDocumentUri(doc.uri)
    
    def mapDocumentUri(self, documentUri):
        '''Convert uri from cached location.
        '''
        #check the source uri map first.
        if hasattr(self, 'sourceUriMap'):
            if documentUri in self.sourceUriMap:
                return self.sourceUriMap[documentUri]
        
        if self.documentCacheLocation is None:
            return documentUri
        
        if documentUri.startswith(self.documentCacheLocation):
            newUri = documentUri[len(self.documentCacheLocation):].replace(os.sep, '/')
            newUri = re.sub(r'\/+', r'/', newUri)
            sep = '/' if self.documentCacheLocation[-1] != os.sep else '//'
            newUri = 'http:' + sep + newUri
            return newUri
        else:
            return documentUri

#     def insertAccessionDocumentAssociation(self):        
#         table = self.getTable('accession_document_association_migration', 'accession_document_association_id', 
#                               ('accession_id','document_id'), 
#                               ('accession_id','document_id',), 
#                               tuple((self.accessionId, docId) 
#                                     for docId in self.documentIds.values()),
#                               checkIfExisting=True)
    
    def insertReportDocument(self):
        self.getTable('report_document', 'report_document_id',
                      ('report_id', 'document_id'),
                      ('report_id', 'document_id'),
                      tuple((self.accessionId, docId)
                            for docId in set(self.documentIds.values() )- set(self.dtsDocumentIds.values())))
    
    def insertCustomArcroles(self):
        self.showStatus("insert arcrole types")
        arcroleTypesByIds = dict(((self.documentIds[self.cleanDocumentUri(arcroleType.modelDocument)],
                                   self.uriId[arcroleType.arcroleURI.strip()]), # key on docId, uriId
                                  arcroleType) # value is roleType object
                                 for arcroleTypes in self.modelXbrl.arcroleTypes.values()
                                 for arcroleType in arcroleTypes
                                 if self.cleanDocumentUri(arcroleType.modelDocument) not in self.existingDocumentIds)
        table = self.getTable('custom_arcrole_type', 'custom_arcrole_type_id', 
                              ('document_id', 'uri_id', 'definition', 'cycles_allowed'), 
                              ('document_id', 'uri_id'), 
                              tuple((arcroleTypeIDs[0], # doc Id
                                     arcroleTypeIDs[1], # uri Id
                                     arcroleType.definition, 
                                     {'any':1, 'undirected':2, 'none':3}[arcroleType.cyclesAllowed])
                                    for arcroleTypeIDs, arcroleType in arcroleTypesByIds.items()))
        table = self.getTable('custom_arcrole_used_on', 'custom_arcrole_used_on_id', 
                              ('custom_arcrole_type_id', 'qname_id'), 
                              ('custom_arcrole_type_id', 'qname_id'), 
                              tuple((idx, self.getQnameId(usedOn))
                                    for idx, docid, uriid in table
                                    for usedOn in arcroleTypesByIds[(docid,uriid)].usedOns))
        
    def insertCustomRoles(self):
        self.showStatus("insert role types")
        roleTypesByIds = dict(((self.documentIds[self.cleanDocumentUri(roleType.modelDocument)],
                                self.uriId[roleType.roleURI.strip()]), # key on docId, uriId
                               roleType) # value is roleType object
                              for roleTypes in self.modelXbrl.roleTypes.values()
                              for roleType in roleTypes
                              if self.cleanDocumentUri(roleType.modelDocument) not in self.existingDocumentIds)
        table = self.getTable('custom_role_type', 'custom_role_type_id', 
                              ('document_id', 'uri_id', 'definition'), 
                              ('document_id', 'uri_id'), 
                              tuple((roleTypeIDs[0], # doc Id
                                     roleTypeIDs[1], # uri Id
                                     roleType.definition.strip()) 
                                    for roleTypeIDs, roleType in roleTypesByIds.items()))
        table = self.getTable('custom_role_used_on', 'custom_role_used_on_id', 
                              ('custom_role_type_id', 'qname_id'), 
                              ('custom_role_type_id', 'qname_id'), 
                              tuple((id, self.getQnameId(usedOn))
                                    for id, docid, uriid in table
                                    for usedOn in roleTypesByIds[(docid,uriid)].usedOns))
        
    def insertElements(self):
        self.showStatus("insert elements")
        
        self.reportTime()
        
        newElements = list()
        newElementAttributes = list()

        for concept in self.newDocumentConcepts:
            newElements.append((self.getQnameId(concept.qname),
                                     self.getQnameId(concept.typeQname), # may be None
                                     self.getQnameId(concept.baseXbrliTypeQname
                                                      if not isinstance(concept.baseXbrliTypeQname, list)
                                                      else concept.baseXbrliTypeQname[0]
                                                      ), # may be None or may be a list for a union
                                     {'debit':1, 'credit':2, None:None}[concept.balance],
                                     {'instant':1, 'duration':2, 'forever':3, None:None}[concept.periodType],
                                     self.getQnameId(concept.substitutionGroupQname), # may be None
                                     concept.isAbstract, 
                                     concept.isNillable,
                                     self.documentIds[self.cleanDocumentUri(concept.modelDocument)],
                                     concept.isNumeric,
                                     concept.isMonetary,
                                     concept.isTuple))
            for atrribName, attribValue in concept.attrib.items():
                if atrribName not in ('abstract','id','nillable','type','substitutionGroup','name'): 
                    attribQName = qname(atrribName)
                    
                    if not (attribQName.namespaceURI == 'http://www.xbrl.org/2003/instance' and attribQName.localName in ('balance','periodType')):
                        newElementAttributes.append((self.getQnameId(concept.qname),self.getQnameId(attribQName),attribValue))
        
        self.reportTime('collected new concepts')
        
        table = self.getTable('element', 'element_id', 
                              ('qname_id', 'datatype_qname_id', 'xbrl_base_datatype_qname_id', 'balance_id',
                               'period_type_id', 'substitution_group_qname_id', 'abstract', 'nillable',
                               'document_id', 'is_numeric', 'is_monetary', 'is_tuple'), 
                              ('qname_id',), 
                              newElements)

        self.elementId = dict((qnameId, elementId)  # indexed by qnameId, not by qname value
                              for elementId, qnameId in table)
        #newDocumentConcepts.clear() # dereference
        self.reportTime('added elements')
#         # get existing element IDs
#         if self.existingDocumentUsedConcepts:
#             conceptQnameIds = []
#             for concept in self.existingDocumentUsedConcepts:
#                 conceptQnameIds.append(str(self.getQnameId(concept.qname)))
#             results = self.execute("SELECT element_id, qname_id FROM element WHERE qname_id IN (" +
#                                    ', '.join(conceptQnameIds) + ");")
#             for elementId, qnameId in results:
#                 self.elementId[qnameId] = elementId
        if len(self.existingDocumentIds) > 0:
            query = "SELECT element_id, qname_id FROM element WHERE document_id in (" + ','.join(str(x) for x in self.existingDocumentIds.values()) + ");"
            results = self.execute(query)
            self.reportTime('ran existing element query')
            for elementId, qnameId in results:
                self.elementId[qnameId] = elementId
            #existingDocumentUsedConcepts.clear() # dereference        
            self.reportTime('got existing element ids')
        #element attributes
        table = self.getTable('attribute_value', 'attribute_value_id', 
                              ('qname_id', 'text_value'),
                              ('qname_id', 'text_value'),
                              set((a[1],a[2]) for a in newElementAttributes)
                              ,checkIfExisting=True)
        
        attributeValueIds = dict(((qnameId, textValue), attributeValueId) 
                                        for attributeValueId, qnameId, textValue in table)
        
#         eava = list((self.elementId[conceptQnameId], attributeValueIds[attributeQnameId,textValue])
#                            for conceptQnameId, attributeQnameId, textValue in newElementAttributes)
        
        self.getTable('element_attribute_value_association', 'element_attribute_value_association_id',
                      ('element_id', 'attribute_value_id'),
                      ('element_id', 'attribute_value_id'),
                      list((self.elementId[conceptQnameId], attributeValueIds[attributeQnameId,textValue])
                           for conceptQnameId, attributeQnameId, textValue in newElementAttributes))
        
    def conceptElementId(self, concept):
        if isinstance(concept, ModelConcept):
            return self.elementId.get(self.getQnameId(concept.qname))
        else:
            return None
    
    def conceptElementIdByQname(self, conceptQName):
        return self.elementId.get(self.getQnameId(conceptQName))
    
    def getQnameId(self, qname):
        if qname is None:
            return None
        elif qname in self.qnameId:
            return self.qnameId[qname]
        else:
            #need to get the qname_id from the database
            result = self.execute("SELECT qname_id FROM qname WHERE namespace = '%s' AND local_name = '%s'" % (qname.namespaceURI, qname.localName))
            if result:
                self.qnameId[qname] = result[0][0]
                return result[0][0]
            else:
                return None
#                 raise XPDBException("xpgDB:MissingQname",
#                                     _("Could not retrieve the qname id for {%(namespace)s}%(localName)s"),
#                                     namespace=qname.namespaceURI, localName=qname.localName)
    
#     def insertAccessionElements(self):
#  
#         table = self.getTable('accession_element', 'accession_element_id', 
#                       ('accession_id', 'element_id', 'is_base', 'primary_count', 'dimension_count', 'member_count'), 
#                       ('accession_id', 'element_id'), 
#                       tuple((self.accessionId,
#                              self.conceptElementIdByQname(conceptQname),
#                              ae_detail['isBase'],
#                              ae_detail['primary'] if ae_detail['primary'] > 0 else None,
#                              ae_detail['dimension'] if ae_detail['dimension'] > 0 else None,
#                              ae_detail['member'] if ae_detail['member'] > 0 else None)
#                             for conceptQname, ae_detail in self.conceptsUsed2.items())
#                      )        

    def insertReportElements(self):
 
        table = self.getTable('report_element', 'report_element_id', 
                      ('report_id', 'element_id', 'is_base', 'primary_count', 'dimension_count', 'member_count'), 
                      ('report_id', 'element_id'), 
                      tuple((self.accessionId,
                             self.conceptElementIdByQname(conceptQname),
                             ae_detail['isBase'],
                             ae_detail['primary'] if ae_detail['primary'] > 0 else None,
                             ae_detail['dimension'] if ae_detail['dimension'] > 0 else None,
                             ae_detail['member'] if ae_detail['member'] > 0 else None)
                            for conceptQname, ae_detail in self.reportElements.items())
                     )        
    
    
    def insertNetworks(self):
        self.reportTime()

        if not self.dtsExists:
            self.timeCall((self.addNetworks, 'base dts network'),self.dtsId, self.dtsBaseSets)
        
        if self.loadType == 'instance' and self.entryDtsId is not None:
            self.timeCall((self.addNetworks, 'instance dts network'),self.entryDtsId, self.instanceBaseSets)
        
    def addNetworks(self, dtsId, baseSets):
#         # delete existing
#         # the load process does not load an existing filing,  so these deletes are not needed.
#         self.execute("DELETE from relationship r USING network n WHERE r.network_id = n.network_id AND n.accession_id = {0};".format(self.accessionId), 
#                       fetch=False)        
#         self.execute("DELETE from network n WHERE n.accession_id = {0};".format(self.accessionId), 
#                      fetch=False)    
#         self.reportTime('delete relationships and networks')
#         '''NEED TO DELETE EXISTING resource, label_resource, footnote_resource, reference_part'''   
        # deduplicate resources (may be on multiple arcs)
        # note that lxml has no column numbers, use elementFragmentIdentifier as unique identifier for the doucment (as pseudo-column number)
        uniqueResources = dict(((docId, xmlLoc), {'resource': resource, 'arcrole': rel.arcrole, 'document_id': docId, 'xml_location': xmlLoc})
                                for arcrole, ELR, linkqname, arcqname in baseSets
                                    for rel in self.modelXbrl.relationshipSet(arcrole, ELR, linkqname, arcqname).modelRelationships
                                        if rel.fromModelObject is not None and rel.toModelObject is not None
                                            for resource in (rel.fromModelObject, rel.toModelObject)
                                                if isinstance(resource, ModelResource)
                                                    for xmlLoc in (elementFragmentIdentifier(resource),)
                                                        for docId in (self.documentIds[self.cleanDocumentUri(resource.modelDocument)],))
        self.reportTime('dedupping resources')
        resourceData = tuple((self.uriId[resource_info['resource'].role.strip()] if resource_info['resource'].role is not None else None,
                             self.getQnameId(resource_info['resource'].qname),
                             resource_info['document_id'],
                             resource_info['resource'].sourceline,
                             0,
                             resource_info['xml_location']
                             )
                            for resource_info in uniqueResources.values())
        self.reportTime('build resource data for loading')
        #add resources
        table = self.getTable('resource', 'resource_id', 
                              ('role_uri_id', 'qname_id', 'document_id', 'document_line_number', 'document_column_number', 'xml_location'), 
                              ('document_id', 'xml_location'), 
                              resourceData,
                              checkIfExisting=True)
        self.reportTime('add resources')
        for resourceId, docId, xmlLoc in table:
            uniqueResources[(docId, xmlLoc)]['resource'].dbResourceId = resourceId
        
        #add labels
        self.getTable('label_resource', 'resource_id', 
                      ('resource_id', 'label', 'xml_lang'), 
                      ('resource_id',), 
                      tuple((resource_info['resource'].dbResourceId,
                             resource_info['resource'].textValue,
                             resource_info['resource'].xmlLang)
                            for resource_info in uniqueResources.values()
                                if resource_info['arcrole'] in (XbrlConst.conceptLabel, XbrlConst.elementLabel)),
                      checkIfExisting=True)
        self.reportTime('add label resource')
        #add footnotes
        self.getTable('footnote_resource', 'resource_id', 
                      ('resource_id', 'footnote', 'xml_lang'), 
                      ('resource_id',), 
                      tuple((resource_info['resource'].dbResourceId,
                             resource_info['resource'].textValue,
                             resource_info['resource'].xmlLang)
                            for resource_info in uniqueResources.values()
                                if resource_info['arcrole'] == XbrlConst.factFootnote),
                      checkIfExisting=True)        
        self.reportTime('add footnote resources')
        
        #references
        referenceParts = []
        for resource_info in uniqueResources.values():
            if resource_info['arcrole'] in (XbrlConst.conceptReference, XbrlConst.elementReference):
                order = 0
                for referencePart in resource_info['resource']:
                    order += 1
                    referenceParts.append((resource_info['resource'].dbResourceId, referencePart.qname, referencePart.textValue, order))
        self.reportTime('build reference part data for load. Created {} reference'.format(len(referenceParts)))

        self.getTable('reference_part', 'reference_part_id',
                      ('resource_id', 'value', 'qname_id', 'ref_order'),
                      ('resource_id', 'qname_id'),
                      tuple((rp[0], rp[2], self.getQnameId(rp[1]), rp[3])
                            for rp in referenceParts),
                      checkIfExisting=True)
        self.reportTime('add reference parts')

        table = self.getTable('dts_network', 'dts_network_id', 
                              ('dts_id', 'extended_link_qname_id', 'extended_link_role_uri_id', 
                               'arc_qname_id', 'arcrole_uri_id', 'description'), 
                              ('dts_id', 'extended_link_qname_id', 'extended_link_role_uri_id', 
                               'arc_qname_id', 'arcrole_uri_id'), 
                              tuple((dtsId,
                                     self.getQnameId(linkqname),
                                     self.uriId[ELR.strip()],
                                     self.getQnameId(arcqname),
                                     self.uriId[arcrole.strip()],
                                     None if ELR in XbrlConst.standardRoles else
                                     self.modelXbrl.roleTypes[ELR][0].definition)
                                        for arcrole, ELR, linkqname, arcqname in baseSets))
        networkIds = dict(((linkQnId, linkRoleId, arcQnId, arcRoleId), id)
                              for id, dtsId, linkQnId, linkRoleId, arcQnId, arcRoleId in table)
        
        self.reportTime('add networks')
        # do tree walk to build relationships with depth annotated, no targetRole navigation
        dbRels = []
        visited = set()
        
        def walkTree(rels, seq, depth, relationshipSet, dbRels, networkId):
            for rel in rels:
                if rel not in visited and rel.toModelObject is not None:
                    visited.add(rel)
                    dbRels.append((rel, seq, depth, networkId))
                    seq += 1
                    seq = walkTree(relationshipSet.fromModelObject(rel.toModelObject), seq, depth+1, relationshipSet, dbRels, networkId)
                    #visited.remove(rel)
            return seq
        
        for arcrole, ELR, linkqname, arcqname in baseSets:
            if ELR and linkqname and arcqname and not arcrole.startswith("XBRL-"):
                networkId = networkIds[(self.getQnameId(linkqname),
                                            self.uriId[ELR.strip()],
                                            self.getQnameId(arcqname),
                                            self.uriId[arcrole.strip()])]
                relationshipSet = self.modelXbrl.relationshipSet(arcrole, ELR, linkqname, arcqname)
                seq = 1
                visited = set()
                for rootConcept in relationshipSet.rootConcepts:
                    seq = walkTree(relationshipSet.fromModelObject(rootConcept), seq, 1, relationshipSet, dbRels, networkId)   
        
        self.reportTime('walk relationships')
        
        relsData = tuple((networkId,
                          self.conceptElementId(rel.fromModelObject), # may be None
                          self.conceptElementId(rel.toModelObject), # may be None
                          self.dbNum(rel.order),
                          rel.fromModelObject.dbResourceId if isinstance(rel.fromModelObject, ModelResource) else None,
                          rel.toModelObject.dbResourceId if isinstance(rel.toModelObject, ModelResource) else None,
                          self.dbNum(rel.weight), # none if no weight
                          sequence,
                          depth,
                          self.uriId.get(rel.preferredLabel.strip()) if rel.preferredLabel else None,
                          rel.fromModelObject.dbFactId if isinstance(rel.fromModelObject, ModelFact) else None,
                          rel.toModelObject.dbFactId if isinstance(rel.toModelObject, ModelFact) else None,
                          self.uriId[rel.targetRole] if rel.targetRole is not None else None
                          )
                         for rel, sequence, depth, networkId in dbRels
                            if rel.fromModelObject is not None and rel.toModelObject is not None)

#        copyData = "\n".join(','.join(row for row in relsData))

        self.reportTime('build relationship data for load')

        del dbRels[:]   # dererefence
        table = self.getTable('dts_relationship', 'dts_relationship_id', 
                              ('dts_network_id', 'from_element_id', 'to_element_id', 'reln_order', 
                               'from_resource_id', 'to_resource_id', 'calculation_weight', 
                               'tree_sequence', 'tree_depth', 'preferred_label_role_uri_id',
                               'from_fact_id', 'to_fact_id', 'target_role_id'), 
                              ('dts_network_id', 'tree_sequence'), 
                              relsData)
        self.reportTime('load relationships')
                                          
    def UOMString(self, unit):
        try:
            return self.sourceCall(unit)
        except self._SourceFunctionError:
            return self.UOMDefault(unit)
                
    def UOMHash(self, unit):
        try:
            return self.sourceCall(unit)
        except self._SourceFunctionError:
            return self.UOMDefault(unit)  

    def UOMDefault(self, unit):
        numerator = '*'.join(x.clarkNotation for x in unit.measures[0])
        denominator = '*'.join(x.clarkNotation for x in unit.measures[1])
        
        if numerator != '':
            if denominator != '':
                return '/'.join((numerator, denominator))
            else:
                return numerator

    def UOMDefaultString(self, unit):
        numerator = ' * '.join(x.localName for x in unit.measures[0])
        denominator = ' * '.join(x.localName for x in unit.measures[1])
        
        if numerator != '':
            if denominator != '':
                return '/'.join((numerator, denominator))
            else:
                return numerator        
                                
    def fiscalYear(self, context):
        try:
            return self.sourceCall(context)
        except self._SourceFunctionError:
            pass
        
        if self.fiscalYearMonthEnd:
            if not context.isForeverPeriod:
                cur_date = context.instantDatetime if context.isInstantPeriod else context.endDatetime
                '''
                Adjust the date back by 10 days. This is to treat year ends that fall at the very begning
                January as the previous year.
                '''
                adjusted_date = cur_date - datetime.timedelta(days=10)
                
                year_adjustment = -1 if self.fiscalYearMonthEnd == 1 and self.fiscalYearDayEnd <= 10 else 0
                
                if self.fiscalYearMonthEnd is None or self.fiscalYearDayEnd is None:
                    return base_date.year + year_adjustment
                else:
                    try:
                        #test that the month/day end combination is a valid date.
                        datetime.date(2000, self.fiscalYearMonthEnd, self.fiscalYearDayEnd)
                    except ValueError:
                        return base_date.year + year_adjustment
                    
                    if ((adjusted_date.month * 100) + adjusted_date.day) > ((self.fiscalYearMonthEnd * 100) + self.fiscalYearDayEnd):
                        #The current month/day is after the year end month/day, so add one year
                        return adjusted_date.year + 1 + year_adjustment
                    else:
                        return adjusted_date.year + year_adjustment

    def fiscalPeriod(self, context):
        try:
            return self.sourceCall(context)
        except self._SourceFunctionError:
            pass
             
        def durationString(context):
            return context.startDatetime.strftime('%Y-%m-%d') + ' - ' + context.endDatetime.strftime('%Y-%m-%d')
       
        if self.fiscalYearMonthEnd:       
            if context.isInstantPeriod:
                return self.fiscalPeriodInstant(context, context.instantDatetime.date()) or context.instantDatetime.strftime('%Y-%m-%d')
            elif context.isStartEndPeriod:
                period_length = context.endDatetime.date() - context.startDatetime.date()
                end_date_period = self.fiscalPeriodInstant(context, context.endDatetime.date())
                
                if end_date_period is None:
                    return durationString(context)
                else:
                    if period_length.days >= 81 and period_length.days <=101:
                        return '4Q' if end_date_period == 'Y' else end_date_period
                    elif period_length.days >= 172 and period_length.days <= 192:
                        if end_date_period == '2Q':
                            return '1H'
                        elif end_date_period == 'Y':
                            return '2H'
                        else:
                            return durationString(context)
                    elif period_length.days >= 263 and period_length.days <= 283 and end_date_period == '3Q':
                        return '3QCUM'
                    elif period_length.days >= 355 and period_length.days <= 375 and end_date_period == 'Y':
                        return 'Y' 
                    else:
                        return durationString(context)                     
            else:
                return 'Forever'
        
    def fiscalPeriodInstant(self, context, instant_date):
        fiscal_year = self.fiscalYear(context)  
        beginning_of_year_adjustment = -1 if self.fiscalYearMonthEnd == 1 and self.fiscalYearDayEnd <= 10 else 0
        context_fiscal_year_end = datetime.date(fiscal_year - beginning_of_year_adjustment, self.fiscalYearMonthEnd, self.fiscalYearDayEnd if not (self.fiscalYearMonthEnd == 2 and self.fiscalYearDayEnd == 29) else 28)
        
        date_diff = context_fiscal_year_end - instant_date
        if date_diff.days >= 263 and date_diff.days <= 283:
            return '1Q'
        elif date_diff.days >= 172 and date_diff.days <= 192:
            return '2Q'
        elif date_diff.days >= 81 and date_diff.days <= 101:
            return '3Q'
        elif date_diff.days >= -10 and date_diff.days <= 10:
            return 'Y'
    
    def calendarYearAndPeriod(self, context):
        if context.isInstantPeriod:
            return self.calendarYearAndPeriodInstant(context)
        elif context.isStartEndPeriod:
            return self.calendarYearAndPeriodDuration(context)
                
                
    def calendarYearAndPeriodInstant(self, context):
        calendarYear = context.instantDatetime.year
        calendarEndOffset = datetime.datetime(calendarYear, 4, 1) - context.instantDatetime
        calendarPeriod = '1Q'
        
        #check if June 30th is closer (q2)
        nextOffset = datetime.datetime(calendarYear, 7, 1) - context.instantDatetime
        if abs(calendarEndOffset) > abs(nextOffset):
            calendarEndOffset = nextOffset
            calendarPeriod = '2Q'
        
        #check if September 30th is closer(q3)
        nextOffset = datetime.datetime(calendarYear, 10, 1) - context.instantDatetime
        if abs(calendarEndOffset) > abs(nextOffset):
            calendarEndOffset = nextOffset
            calendarPeriod = '3Q'
        
        #check if the year end is closer (y)
        nextOffset = datetime.datetime(calendarYear + 1, 1, 1) - context.instantDatetime
        if abs(calendarEndOffset) > abs(nextOffset):
            calendarEndOffset = nextOffset
            calendarPeriod = 'Y'
            
        #check if the previous year end is closer (y)
        nextOffset = datetime.datetime(calendarYear, 1, 1) - context.instantDatetime
        if abs(calendarEndOffset) > abs(nextOffset):
            calendarEndOffset = nextOffset
            calendarPeriod = 'Y'
            calendarYear = calendarYear - 1        
        
        return calendarYear, calendarPeriod, None, calendarEndOffset.days, None
    
    def calendarYearAndPeriodDuration(self, context):
        periodLength = (context.endDatetime - context.startDatetime).days
        yearOffset = 0
        found_period = True
        specialYear = False
        
        calendarYear = None
        calendarPeriod = None
        startOffset = None
        endOffset = None
        sizePercentage = None

        if periodLength >= 81 and periodLength <= 101:
            #quarter
            periodRanges = (('1Q',(1,1),(3,31)), ('2Q',(4,1),(6,30)), ('3Q',(7,1),(9,30)), ('4Q',(10,1),(12,31)))
        elif periodLength >= 172 and periodLength <=192:
            #half year
            periodRanges = (('1H',(1,1),(6,30)), ('2H',(7,1),(12,31)))
        elif periodLength >= 263 and periodLength <= 283:
            #3QCum
            periodRanges = (('3QCUM',(1,1),(9,30)),)
        elif periodLength >= 355 and periodLength <= 375:
            #year
            if context.endDatetime.year - context.startDatetime.year == 2:
                #special case. If the start to end year is over three years, the calendar year should be the middle year. For example 2008-12-28 to 2010-01-04.
                calendarPeriod = 'Y'
                calendarYear = context.endDatetime.year - 1
                periodRanges = tuple()
            else:
                periodRanges = (('Y',(1,1),(12,31)),)
        else:
            #unknown period
            calendarPeriod = context.startDatetime.date().isoformat() + " - " + context.endDatetime.date().isoformat()
            if context.startDatetime.year == context.endDatetime.year:
                calendarYear = context.startDatetime.year
            else:
                #determine which year has the most overlap.
                if (self.periodOverlap(context.startDatetime, context.endDatetime, datetime.datetime(context.startDatetime.year, 1, 1), datetime.datetime(context.startDatetime.year, 12, 31)) >=
                   self.periodOverlap(context.startDatetime, context.endDatetime, datetime.datetime(context.endDatetime.year, 1, 1), datetime.datetime(context.endDatetime.year, 12, 31))):
                    calendarYear = context.startDatetime.year
                else:
                    calendarYear = context.endDatetime.year
            periodRanges = tuple()
            
        currentOverlap = 0
        for periodName, periodStart, periodEnd in periodRanges:
            #check the overlap using the end date year
            overlapDays = self.periodOverlap(context.startDatetime, context.endDatetime, datetime.datetime(context.startDatetime.year, periodStart[0], periodStart[1]), datetime.datetime(context.startDatetime.year, periodEnd[0], periodEnd[1]))
            if overlapDays > currentOverlap:
                calendarPeriod = periodName
                calendarYear = context.startDatetime.year
                currentOverlap = overlapDays
            if context.startDatetime.year != context.endDatetime.year:
                #if the start and end date years are different, then check the overlap using the start date year
                overlapDays = self.periodOverlap(context.startDatetime, context.endDatetime, datetime.datetime(context.endDatetime.year, periodStart[0], periodStart[1]), datetime.datetime(context.endDatetime.year, periodEnd[0], periodEnd[1]))
                if overlapDays > currentOverlap:
                    calendarPeriod = periodName
                    calendarYear = context.endDatetime.year
                    currentOverlap = overlapDays

        #determine the difference between the calendar period and the context period.
        periodStartAndEnds = {'1Q': ((1,1), (3,31)),
                      '2Q': ((4,1), (6,30)),
                      '3Q': ((7,1), (9,30)),
                      '4Q': ((10,1), (12,31)),
                      '1H': ((1,1), (6,30)),
                      '2H': ((7,1), (12,31)),
                      '3QCUM': ((1,1), (9,30)),
                      'Y': ((1,1), (12,31))
                      }
        
        if calendarPeriod in periodStartAndEnds:
            calendarStart = datetime.date(calendarYear, *periodStartAndEnds[calendarPeriod][0])
            calendarEnd = datetime.date(calendarYear, *periodStartAndEnds[calendarPeriod][1])
            startOffset = (calendarStart - context.startDatetime.date()).days
            endOffset = (calendarEnd - context.endDatetime.date()).days + 1
            sizePercentage = 1.0 - (((calendarEnd - calendarStart).days + 1) / periodLength)
            
            
        return calendarYear, calendarPeriod, startOffset, endOffset, sizePercentage

    def periodOverlap(self, startDateA, endDateA, startDateB, endDateB):
        if not ((startDateA < endDateB) and (endDateA > startDateB)):
            #there is no overlap
            return 0
        else:
            return (min(endDateA, endDateB) - max(startDateA, startDateB)).days
        
    def hashPeriod(self, context):
        if context.isStartEndPeriod:
            return context.startDatetime.strftime('%Y%m%d') + '-' + context.endDatetime.strftime('%Y%m%d')
        elif context.isInstantPeriod:
            return context.instantDatetime.strftime('%Y%m%d')
        else:
            return 'F'
    
    def hashCalendarPeriod(self, context, calendarYear, calendarPeriod):
        if calendarPeriod is None:
            return None
        
        if context.isStartEndPeriod or context.isInstantPeriod:
            if '-' in calendarPeriod:
                #unknown period
                return None
            else:
                return calendarPeriod + str(calendarYear)
        else:
            #forever period
            return None
    
    def hashDimensions(self, context):
        normalized_dimensions = [self.conceptQnameHash(context.qnameDims[dim].dimensionQname) + '=' + self.hashMember(context.qnameDims[dim]) for dim in context.qnameDims.keys()]
        normalized_dimensions.sort()
        if normalized_dimensions is not None:
            return '|'.join(normalized_dimensions)
    
    def hashMember(self, modelDimension):
        if modelDimension.isExplicit:
            return self.conceptQnameHash(modelDimension.memberQname)
        elif modelDimension.isTyped:
            return self.canonicalizeTypedDimensionMember(modelDimension.typedMember)
        else:
            raise XPDBException("xpgDB:UnknownMemberType",
                                _("Dimension member is not explicit or typed"))
            
    def hashContext(self, context):
        hash_list = [
                     self.hashEntity(),
                     self.hashPeriod(context)
                     ]

        if bool(context.qnameDims): #has dimensions
            hash_list.append(self.hashDimensions(context))
        
        hash = '|'.join(hash_list)        
    
        return hashlib.sha224(hash.encode()).digest()
    
    def conceptQnameHash(self, elementQname):
        try:
            return self.sourceCall(elementQname)
        except self._SourceFunctionError:
            return elementQname.clarkNotation
            
    def hashPrimary(self, fact):
        return self.conceptQnameHash(fact.qname)
    
    def hashEntity(self):
        return self.entityScheme + "|" + self.entityIdentifier
     
    def hashUnit(self, fact):
        #self.unitHash.get((self.accessionId,fact.unitID))
        unitInfo = self.unitsbyXmlId.get(fact.unitID)
        if unitInfo is None:
            return None
        else:
            return unitInfo['unitHash']

    def hashFact(self, fact):

        if fact.isTuple:
            hash = self.hashTuple(fact)
        else:
            hash_list = [self.hashPrimary(fact),
                         self.hashEntity(),
                         self.cntxInfo.get((self.accessionId,fact.contextID))['period_hash'],
                         self.hashUnit(fact) or ''
                         #self.unitHash.get((self.accessionId,fact.unitID)) or ''
                         ]
    
            if self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash']:
                hash_list.append(self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash'])
            
            hash = '|'.join(hash_list)

        return hash    
    
    def hashFactCalendar(self, fact):

        if fact.isTuple:
            hash = self.hashTuple(fact)
        else:
            if self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_period_hash'] is None:
                hash = None
            else:
                hash_list = [self.hashPrimary(fact),
                             self.hashEntity(),
                             self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_period_hash'],
                             self.hashUnit(fact) or ''
                             #self.unitHash.get((self.accessionId,fact.unitID)) or ''
                             ]
        
                if self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash']:
                    hash_list.append(self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash'])
                
                hash = '|'.join(hash_list)
        
        return hash    
    
    def hashFactFiscal(self, fact):
        if fact.isTuple:
            hash = self.hashTuple(fact)
        else:
            if self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_period_hash'] is None:
                hash = None     
            else:       
                hash_list = [self.hashPrimary(fact),
                             self.hashEntity(),
                             self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_period_hash'],
                             self.hashUnit(fact) or ''
                             #self.unitHash.get((self.accessionId,fact.unitID)) or ''
                             ]
        
                if self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash']:
                    hash_list.append(self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash'])
                
                hash = '|'.join(hash_list)
    
        return hash

    def hashTuple(self, fact):
        hash_list = ['t' + self.hashPrimary(fact)]  + [self.hashFact(subFact) for subFact in fact.modelTupleFacts]
        return '|'.join(hash_list)

    def insertFacts(self):
        self.reportTime()
        accsId = self.accessionId

        self.showStatus("insert facts")
        
        # units        
#         table = self.getTable('unit', 'unit_id', 
#                               ('accession_id', 'unit_xml_id'), 
#                               ('accession_id', 'unit_xml_id'), 
#                               tuple((accsId,
#                                      unitId)
#                                     for unitId in self.modelXbrl.units.keys()))
#         
#         self.unitId = dict(((_accsId, xmlId), id)
#                            for id, _accsId, xmlId in table)
#         
#         self.unitString = dict(((_accsId, xmlId), self.UOMString(self.modelXbrl.units[xmlId]))
#                            for id, _accsId, xmlId in table)
#         
#         self.unitHash = dict(((_accsId, xmlId), self.UOMHash(self.modelXbrl.units[xmlId]))
#                            for id, _accsId, xmlId in table)
#         
#         # measures
#         table = self.getTable('unit_measure', 'unit_measure_id', 
#                               ('unit_id', 'qname_id', 'location_id'), 
#                               ('qname_id', 'location_id'), 
#                               tuple((self.unitId[(accsId,unit.id)],
#                                      self.getQnameId(measure),
#                                      1 if (len(unit.measures[1]) == 0) else (i + 2))
#                                     for unit in self.modelXbrl.units.values()
#                                     for i in range(2)
#                                     for measure in unit.measures[i]))
        self.insertUnit()
        self.reportTime('units')
        
        self.cntxInfo = dict()
        for c in self.modelXbrl.contexts.values():
            calendarValues = self.calendarYearAndPeriod(c)
            fiscalPeriod = self.fiscalPeriod(c)
            fiscalYear = self.fiscalYear(c)
            self.cntxInfo[(accsId, c.id)] = {'period_start': c.startDatetime if c.isStartEndPeriod else None,
                                             'period_end': c.endDatetime if c.isStartEndPeriod else None,
                                             'period_instant': c.instantDatetime if c.isInstantPeriod else None,
                                             'specifies_dimensions': bool(c.qnameDims),
                                             'entity_scheme': c.entityIdentifier[0],
                                             'entity_identifier': c.entityIdentifier[1],
                                             'fiscal_year': fiscalYear,
                                             'fiscal_period': fiscalPeriod,
                                             'fiscal_period_hash': self.hashCalendarPeriod(c, fiscalYear, fiscalPeriod),
                                             'period_hash': self.hashPeriod(c),
                                             'dim_hash': self.hashDimensions(c),
                                             'context_hash': self.hashContext(c),
                                             'calendar_period_hash': self.hashCalendarPeriod(c, calendarValues[0], calendarValues[1]),
                                             'calendar_year': calendarValues[0],
                                             'calendar_period': calendarValues[1],
                                             'calendar_start_offset': calendarValues[2],
                                             'calendar_end_offset': calendarValues[3],
                                             'calendar_period_size_diff_percentage': calendarValues[4]                                           
                                             }

        '''
        tuple((accsId,
               cntx.startDatetime if cntx.isStartEndPeriod else None,
               cntx.endDatetime if cntx.isStartEndPeriod else None,
               cntx.instantDatetime if cntx.isInstantPeriod else None,
               bool(cntx.qnameDims),
               cntx.id,
               cntx.entityIdentifier[0],
               cntx.entityIdentifier[1])
              for cntx in self.modelXbrl.contexts.values()))
        '''
        table = self.getTable('context', 'context_id', 
                              ('accession_id', 'period_start', 'period_end', 'period_instant', 'specifies_dimensions', 'context_xml_id', 
                               'entity_scheme', 'entity_identifier','context_hash',
                               'fiscal_year', 'fiscal_period', 'calendar_year', 'calendar_period', 'calendar_start_offset', 'calendar_end_offset', 'calendar_period_size_diff_percentage'), 
                              ('accession_id', 'context_xml_id'), 
                              tuple((c_key[0],
                                     c_val['period_start'],
                                     c_val['period_end'],
                                     c_val['period_instant'],
                                     c_val['specifies_dimensions'],
                                     c_key[1],
                                     c_val['entity_scheme'],
                                     c_val['entity_identifier'],
                                     c_val['context_hash'],
                                     c_val['fiscal_year'],
                                     c_val['fiscal_period'],
                                     c_val['calendar_year'],
                                     c_val['calendar_period'],
                                     c_val['calendar_start_offset'],
                                     c_val['calendar_end_offset'],
                                     c_val['calendar_period_size_diff_percentage'],
                                     )
                                    for c_key, c_val in self.cntxInfo.items()))
        self.cntxId = dict(((_accsId, xmlId), id)
                           for id, _accsId, xmlId in table)
        self.reportTime('context')
        '''
        self.cntxInfo = dict()
        for c in self.modelXbrl.contexts.values():
            calendarValues = self.calendarYearAndPeriod(c)
            self.cntxInfo[(accsId, c.id)] = {'fiscal_year': self.fiscalYear(c),
                                             'fiscal_period': self.fiscalPeriod(c),
                                             'period_hash': self.hashPeriod(c),
                                             'dim_hash': self.hashDimensions(c),
                                             'calendar_period_hash': self.hashCalendarPeriod(c, calendarValues[0], calendarValues[1]),
                                             'calendar_year': calendarValues[0],
                                             'calendar_period': calendarValues[1],
                                             'calendar_start_offset': calendarValues[2],
                                             'calendar_end_offset': calendarValues[3],
                                             'calendar_size_percentage': calendarValues[4]                                             
                                             }
        '''
        '''
        # context_aug
        table = self.getTable('context_aug', 'context_id',
                              ('context_id', 'fiscal_year', 'fiscal_period', #'context_hash', 'dimension_hash', 
                               'calendar_year', 'calendar_period', 'calendar_start_offset', 'calendar_end_offset', 'calendar_period_size_diff_percentage'),
                              ('context_id',),
                              tuple((self.cntxId[c_key],
                                     c_val['fiscal_year'],
                                     c_val['fiscal_period'],
                                     #c_val['period_hash'],
                                     #c_val['dim_hash'],
                                     c_val['calendar_year'],
                                     c_val['calendar_period'],
                                     c_val['calendar_start_offset'],
                                     c_val['calendar_end_offset'],
                                     c_val['calendar_period_size_diff_percentage'])
                                    for c_key, c_val in self.cntxInfo.items()))
        '''
        # context_dimension
        values = []
        explicitValues = []
        for cntx in self.modelXbrl.contexts.values():
            for dim in cntx.qnameDims.values():
                values.append((self.cntxId[(accsId,cntx.id)],
                               self.getQnameId(dim.dimensionQname),
                               self.getQnameId(dim.memberQname), # may be None
                               self.getQnameId(dim.typedMember.qname) if dim.isTyped else None,
                               False, # not default
                               dim.contextElement == "segment",
                               self.canonicalizeTypedDimensionMember(dim.typedMember) if dim.isTyped else None))
#                 explicitValues.append((self.cntxId[(accsId,cntx.id)],
#                                self.getQnameId(dim.dimensionQname),
#                                self.getQnameId(dim.memberQname), # may be None
#                                self.getQnameId(dim.typedMember.qname) if dim.isTyped else None,
#                                False, # not default
#                                dim.contextElement == "segment",
#                                dim.typedMember.stringValue if dim.isTyped else None))
            for dimQname, memQname in self.modelXbrl.qnameDimensionDefaults.items():
                if dimQname not in cntx.qnameDims:
                    values.append((self.cntxId[(accsId,cntx.id)],
                                   self.getQnameId(dimQname),
                                   self.getQnameId(memQname),
                                   None,
                                   True, # is default
                                   None, # ambiguous and irrelevant for the XDT model
                                   None))
        
        if values:
            table = self.getTable('context_dimension', 'context_dimension_id', 
                                  ('context_id', 'dimension_qname_id', 'member_qname_id', 'typed_qname_id', 'is_default', 'is_segment', 'typed_text_content'), 
                                  ('context_id', 'dimension_qname_id', 'member_qname_id'), # shouldn't typed_qname_id be here?  not good idea because it's not indexed in XBRL-US DDL
                                  values)
            
        self.reportTime('context dimension')
        for i, val in enumerate(values):
            if not val[4]:
                explicitValues.append((table[i][0],) + val)
                
        if explicitValues:
            table = self.getTable('context_dimension_explicit', 'context_dimension_id', 
                                  ('context_dimension_id', 'context_id', 'dimension_qname_id', 'member_qname_id', 'typed_qname_id', 'is_default', 'is_segment', 'typed_text_content'), 
                                  ('context_id', 'dimension_qname_id', 'member_qname_id'), # shouldn't typed_qname_id be here?  not good idea because it's not indexed in XBRL-US DDL
                                  explicitValues)
        self.reportTime('context dimension explicit')
        
        
        
        self.timeCall(self.insertFactSet, self.modelXbrl.facts, None)

        self.timeCall((self.updateUltimus, 'calc normal ultimus'),'normal')
        self.timeCall((self.updateUltimus, 'calc calendar ultimus'),'calendar')
        self.timeCall((self.updateUltimus, 'calc fiscal ultimus'),'fiscal')        

    def insertUnit(self):
        
        unitBase = dict()
        unitMeasureBase = dict()
        
        for unit in self.modelXbrl.units.values():
            unitHashString = self.UOMDefault(unit)
            unitHash = hashlib.sha224(unitHashString.encode()).digest()
            unitString = self.UOMDefaultString(unit)
            if str(unitHash) not in unitBase:
                unitBase[str(unitHash)] = {'hash':unitHash, 'hashString':unitHashString, 'string':unitString, 'modelUnits':list()}
            unitBase[str(unitHash)]['modelUnits'].append(unit)
        
        table = self.getTable('unit_base', 'unit_base_id',
                              ('unit_hash', 'unit_hash_string', 'unit_string'),
                              ('unit_hash',),
                              tuple((unitValue['hash'], unitValue['hashString'], unitValue['string'])
                                    for unitValue in unitBase.values()),
                              checkIfExisting=True,
                              returnExistenceStatus=True)
        
        for row in table:
            unitBase[row[1]]['unitBaseId'] = row[0]
        
        #unit_measure_base
        table = self.getTable('unit_measure_base', 'unit_measure_base_id',
                              ('unit_base_id', 'qname_id', 'location_id'),
                              ('unit_base_id', 'qname_id', 'location_id'),
                              tuple((unitValue['unitBaseId'], 
                                     self.getQnameId(measure), 
                                     1 if (len(unitValue['modelUnits'][0].measures[1]) == 0) else (i + 2))
                                    for unitValue in unitBase.values()
                                    for i in range(2)
                                    for measure in unitValue['modelUnits'][0].measures[i]),
                              checkIfExisting=True)
        
        #unit report
        table = self.getTable('unit_report', 'unit_report_id',
                              ('report_id', 'unit_base_id', 'unit_xml_id'),
                              ('report_id', 'unit_base_id', 'unit_xml_id'),
                              tuple((self.accessionId, unitValue['unitBaseId'], unit.id)
                                    for unitValue in unitBase.values()
                                    for unit in unitValue['modelUnits']))
        
        self.unitsbyXmlId = dict((xmlId, {'unitReportId':id, 'unitBaseId': unitBaseId, 'unitString':self.UOMString(self.modelXbrl.units[xmlId]), 'unitHash':self.UOMHash(self.modelXbrl.units[xmlId])})
                          for id, _x, unitBaseId, xmlId in table)        


    
    def canonicalizeTypedDimensionMember(self, typedMember):
        typedElement = self.modelXbrl.qnameConcepts[typedMember.qname]
        
        if typedElement.baseXsdType == 'duration':
            return self.canonicalizeDuration(typedMember.xValue)
        elif typedElement.baseXsdType == 'QName':
            #qnames are cononicalized by using clark notation
            try:
                typedMemberQname = qname(typedMember.xValue, castException=self._QNameException, prefixException=self._QNameException)
            except self._QNameException:
                raise XPDBException("xpgDB:TypedMemberQnameError",
                                    _("Cannot resolve qname in typed member for dimension %s and member %s" % (typedMember.qname, typedMember.xValue)))
            if typedMemberQname.namespaceURI is None and None not in typedMember.nsmap:
                raise XPDBException("xpgDB:TypedMemberQnameError",
                                    _("Typed member is a qname without a prefix and there is no default namespace for the element. Dimension is %s and member is %s." % ( typedMember.qname, typedMember.xValue)))
            return typedMemberQname.clarkNotation
        else:
            return str(typedMember.xValue)
    
    def canonicalizeDuration(self, duration):
        #durations are cononicalzied by the method described in XML Schema  Datatypes https://www.w3.org/TR/xmlschema11-2/#f-durationCanMap
        #first gather the parts in the duration
        ''' The following pattern checks for valid combinations of parts. There is a problem wiht it, PT30000S failed to match. However, the data is 
            already validated at this point. So instead using a simplified pattern that extracts the parts but doesn't validate that the right parts
            are there (i.e. PT would match but is not a valid duration). 
        
        #pattern = "-?P((((?P<year1>[0-9]+)Y((?P<month1>[0-9]+)M)?((?P<day1>[0-9]+)D)?|((?P<month2>[0-9]+)M)((?P<day2>[0-9]+)D)?|((?P<day3>[0-9]+)D))(T(((?P<hour1>[0-9]+)H)((?P<minute1>[0-9]+)M)?((?P<second1>[0-9]+(\.[0-9]+))?S)?|((?P<minute2>[0-9]+)M)((?P<second2>[0-9]+(\.[0-9]+))?S)?|((?P<second3>[0-9]+(\.[0-9]+))?S)))?)|(T(((?P<hour2>[0-9]+)H)((?P<minute3>[0-9]+)M)?((?P<second4>[0-9]+(\.[0-9]+))?S)?|((?P<minute4>[0-9]+)M)((?P<second5>[0-9]+(\.[0-9]+))?S)?|((?P<second6>[0-9]+(\.[0-9]+))?S))))$"
        '''
        pattern = "-?P((?P<year>[0-9]+)Y)?((?P<month>[0-9]+)M)?((?P<day>[0-9]+)D)?(T((?P<hour>[0-9]+)H)?((?P<minute>[0-9]+)M)?((?P<second>[0-9]+(\.[0-9]+)?)S)?)?"
        partsRaw = re.match(pattern, duration)
        parts = dict()
        months = 0
        seconds = decimal.Decimal(0)
        sign = ''
        multiplier = {'year':12, 'month':1, 'day':86400, 'hour':3600, 'minute':60}
        monthParts = ('year', 'month')
        secondParts = ('day', 'hour', 'minute', 'second')
        for rawName, rawValue in partsRaw.groupdict().items():
            for name in ('year','month','day','hour','minute','second','sign'):
                if rawValue is not None and name in rawName:
                    if name == 'sign':
                        parts['sign'] = rawValue
                    elif name == 'second':
                        partValue = decimal.Decimal(rawValue)
                    else:
                        partValue = int(rawValue) * multiplier[name]
                        
                    if name in monthParts:
                        months += partValue   
                    else:
                        seconds += partValue 
                    break
                
        if months != 0 and seconds != 0:
            return parts.get('sign','') + 'P' + self.canonicalizeYearMonth(months) + self.canonicalizeDayTime(seconds)
        elif months is not 0:
            return parts.get('sign', '') + 'P' + self.canonicalizeYearMonth(months)
        else:
            return parts.get('sign','') + 'P' + self.canonicalizeDayTime(seconds)
    
    def canonicalizeYearMonth(self, months):       
        y = months // 12 # // drops the remainder
        m = months % 12 

        returnValue = ''
        if y != 0:
            returnValue += str(y) + 'Y'
        if m != 0:
            returnValue += str(m) + 'M'
        
        return returnValue

    def canonicalizeDayTime(self, seconds):
        
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        
        returnValue = ''
        if d != 0:
            returnValue += str(d) + 'D'
        if h + m + s != 0:
            returnValue += 'T'
        if h != 0:
            returnValue += str(h) + 'H'
        if m != 0:
            returnValue += str(m) + 'M'
        if s != 0:
            returnValue += str(s) + 'S'
    
        return returnValue
    
    def updateUltimus(self, ultimusType):
        if ultimusType == 'normal':
            indexName = 'ultimus_index'
            hashName = 'fact_hash'
            factsByHash = self.factsByHashString
            contextJoin = ''
            orderBy = 'r.accepted_timestamp DESC, r.report_id DESC, f.xml_id, f.fact_id DESC'
        elif ultimusType == 'calendar':
            #calendar
            indexName = 'calendar_ultimus_index'
            hashName = 'calendar_hash'
            factsByHash = self.factsByCalendarHashString
            contextJoin = 'JOIN context c ON f.context_id = c.context_id'
            orderBy = 'r.accepted_timestamp DESC, r.report_id DESC, abs(c.calendar_period_size_diff_percentage), abs(c.calendar_end_offset), f.xml_id, f.fact_id DESC'
        elif ultimusType == 'fiscal':
            indexName = 'fiscal_ultimus_index'
            hashName = 'fiscal_hash'
            factsByHash = self.factsByFiscalHashString
            contextJoin = ''
            orderBy = 'r.accepted_timestamp DESC, r.report_id DESC, f.xml_id, f.fact_id DESC'            
        
        self.reportTime()
        updateFacts = []
        self.reportTime()
        
        hashQuery = '''
            WITH ultimus_calc AS (
                SELECT f.fact_id
                      ,{indexName} as old_index
                      ,row_number() OVER (PARTITION BY {hashName} ORDER BY {orderBy}) AS new_index
                FROM report r
                JOIN fact f
                  ON r.report_id = f.accession_id
                {contextJoin}
                WHERE f.{hashName} in (SELECT {hashName} FROM fact WHERE accession_id = {reportId})
            )
            UPDATE fact f
            SET {indexName} = ultimus_calc.new_index
            FROM ultimus_calc
            WHERE f.fact_id = ultimus_calc.fact_id
              AND COALESCE(ultimus_calc.old_index, 0) <> ultimus_calc.new_index
            '''.format(indexName=indexName, hashName=hashName, orderBy=orderBy, reportId=self.accessionId, contextJoin=contextJoin)
        
#         self.reportTime()
        self.execute(hashQuery, fetch=False)
#         self.reportTime('biq query run')
        
#         
#         
#         t = datetime.timedelta()
#         pt = datetime.timedelta()
#         c = 0
#         for hashString, factIds in factsByHash.items():
#             c += 1
#             #get facts to update
#             hashQuery = '''
#                 SELECT f.fact_id, {indexName} as hash_index
#                 FROM report r
#                 JOIN fact f
#                   ON r.report_id = f.accession_id
#                 {contextAugJoin}
#                 WHERE f.{hashName} = decode('{hash}', 'hex')
#                 ORDER BY {orderBy};
#                 '''.format(indexName=indexName, contextAugJoin=contextAugJoin, hashName=hashName, hash=hashlib.sha224(hashString.encode()).hexdigest(), orderBy=orderBy)
#             
#             s = datetime.datetime.now()
#             results = self.execute(hashQuery)
#             e = datetime.datetime.now()
#             t += e - s
#             if (c % 100) == 0:
#                 phours, premainder = divmod((t - pt).total_seconds(), 3600)
#                 pminutes, pseconds = divmod(premainder, 60)
#                 thours, tremainder = divmod(t.total_seconds(), 3600)
#                 tminutes, tseconds = divmod(tremainder, 60)
#                 self.modelXbrl.info("info",_("count: %(c)s - 100: %(pt)s - total: %(t)s"),
#                                               c=str(c),
#                                               pt='%02.0f:%02.0f:%02.4f' % (phours, pminutes, pseconds),
#                                               t='%02.0f:%02.0f:%02.4f' % (thours, tminutes, tseconds))  
#                 pt = t
#             new_ultimus = 1
#             for row in results:
#                 if row[1] != new_ultimus:
#                     updateFacts.append((row[0], new_ultimus))
# #                     #update the values for fact_aug
# #                     if row[0] in self.factsForFactAug:
# #                         self.factsForFactAug[row[0]][indexName] = new_ultimus
#                 new_ultimus += 1
#                 
#                 
#         thours, tremainder = divmod(t.total_seconds(), 3600)
#         tminutes, tseconds = divmod(tremainder, 60)
#         self.modelXbrl.info("info",_("final count: %(c)s - total: %(t)s"),
#                                       c=str(c),
#                                       t='%02.0f:%02.0f:%02.4f' % (thours, tminutes, tseconds)) 
#                 
#         self.reportTime('calc ultimus')
#         self.updateTable('fact',('fact_id', indexName), updateFacts)
#         #self.updateTable('fact_aug',('fact_id', indexName), updateFacts)
#         self.reportTime('update ultimus')
        
    def isExtendedFact(self, fact):
        '''
        This funciton determines if the fact has an extended component (primary or dimension or member).
        '''
        
        #primary_extended = not self.namespaceId.get(fact.qname.namespaceURI).get("isBase")
        primary_extended = not self.isBaseNamespace(fact.qname.namespaceURI)
        if fact.isTuple:
            dimension_extended = False
        else:
#             dimension_extended = (any(not self.namespaceId.get(fact.context.qnameDims[dim].dimensionQname.namespaceURI).get("isBase") or                                  
#                                       not (
#                                            self.namespaceId.get(fact.context.qnameDims[dim].memberQname.namespaceURI).get("isBase") if fact.context.qnameDims[dim].isExplicit 
#                                            else 
#                                            self.namespaceId.get(fact.context.qnameDims[dim].typedMember.qname.namespaceURI).get("isBase")
#                                            )
#                                       for dim in fact.context.qnameDims.keys()
#                                   ))
            dimension_extended = (any(not self.isBaseNamespace(fact.context.qnameDims[dim].dimensionQname.namespaceURI) or                                  
                                      not (
                                           self.isBaseNamespace(fact.context.qnameDims[dim].memberQname.namespaceURI) if fact.context.qnameDims[dim].isExplicit 
                                           else self.isBaseNamespace(fact.context.qnameDims[dim].typedMember.qname.namespaceURI)
                                           )
                                      for dim in fact.context.qnameDims.keys()
                                  ))    
        
        return primary_extended or dimension_extended
    
    def isBaseNamespace(self, uri):
        return uri in self.baseNamespaces
    
    # facts
    def insertFactSet(self, modelFacts, tupleFactId):
        insertForFact, results = self.getFactsForTuple(modelFacts, tupleFactId)

        self.factsByHashString = collections.defaultdict(list)
        self.factsByCalendarHashString = collections.defaultdict(list)
        self.factsByFiscalHashString = collections.defaultdict(list)
        #self.factsForFactAug = dict()
        for id, _accsId, xmlId, uom, isExtended in results:
            self.factsByHashString[insertForFact[xmlId]['fact_hash_string']].append(id)
            if insertForFact[xmlId]['fiscal_hash_string'] is not None:
                self.factsByFiscalHashString[insertForFact[xmlId]['fiscal_hash_string']].append(id)
            if insertForFact[xmlId]['calendar_hash_string'] is not None:
                self.factsByCalendarHashString[insertForFact[xmlId]['calendar_hash_string']].append(id)            

    def getFactsForTuple(self, modelFacts, tupleFactId):
        insertForFact = dict()
        tuples = []
        
        for fact in modelFacts:
            if fact.isTuple:
                tuples.append(fact)
                
            calendarHashString = self.hashFactCalendar(fact)
            calendarHash = hashlib.sha224(calendarHashString.encode()).digest() if calendarHashString is not None else None
            fiscalHashString = self.hashFactFiscal(fact)
            fiscalHash = hashlib.sha224(fiscalHashString.encode()).digest() if fiscalHashString is not None else None
            factHashString = self.hashFact(fact)
            factXMLId = elementFragmentIdentifier(fact)
            
            if fact.isNil or not fact.isNumeric:
                effectiveValue = None
            else:
                effectiveValue = roundValue(fact.value, fact.precision, fact.decimals)
                if effectiveValue == 0:
                    effectiveValue = int(effectiveValue)
            
            if fact.isNil:
                factValue = None
            elif fact.isNumeric:
                factValue = fact.value
            else:
                if len(fact.value) == 0:
                    factValue = None
                else:
                    factValue = fact.value

            insertForFact[factXMLId] = {'model_fact': fact,
                 'accession_id': self.accessionId,
                 'tuple_fact_id': tupleFactId,
                 'context_id': self.cntxId.get((self.accessionId,fact.contextID)),
                 'unit_id': self.unitsbyXmlId[fact.unitID]['unitReportId'] if fact.unitID in self.unitsbyXmlId else None, #self.unitId.get((self.accessionId,fact.unitID)),
                 'unit_base_id': self.unitsbyXmlId[fact.unitID]['unitBaseId'] if fact.unitID in self.unitsbyXmlId else None,
                 'element_id': self.conceptElementId(fact.concept),
                 'effective_value': effectiveValue,
                 'fact_value': factValue,
                 'xml_id': factXMLId,
                 'precision_value': fact.xAttributes['precision'].xValue if ('precision' in fact.xAttributes and isinstance(fact.xAttributes['precision'].xValue,int)) else None,
                 'decimals_value': fact.xAttributes['decimals'].xValue if ('decimals' in fact.xAttributes and isinstance(fact.xAttributes['decimals'].xValue,int)) else None,
                 'is_precision_infinity': 'precision' in fact.xAttributes and fact.xAttributes['precision'].xValue == 'INF',
                 'is_decimals_infinity': 'decimals' in fact.xAttributes and fact.xAttributes['decimals'].xValue == 'INF',
                 'uom': self.unitsbyXmlId[fact.unitID]['unitString'] if fact.unitID in self.unitsbyXmlId else None, #self.unitString.get((self.accessionId,fact.unitID)),
                 'fiscal_year': self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_year'] if not fact.isTuple else None,
                 'fiscal_period': self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_period'] if not fact.isTuple else None,
                 'fiscal_hash': fiscalHash,
                 'fiscal_hash_string': fiscalHashString,
                 'fact_hash': hashlib.sha224(factHashString.encode()).digest(),
                 'fact_hash_string': factHashString,
                 'calendar_year': self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_year'] if not fact.isTuple else None,
                 'calendar_period': self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_period']if not fact.isTuple else None,
                 'calendar_hash': calendarHash,
                 'calendar_hash_string': calendarHashString,
                 'is_extended': self.isExtendedFact(fact),
                 'is_tuple': fact.isTuple
                 }

        table = self.getTable('fact', 'fact_id', 
                              ('accession_id', 'tuple_fact_id', 'context_id', 'unit_id', 'unit_base_id', 'element_id', 'effective_value', 'fact_value', 
                               'xml_id', 'precision_value', 'decimals_value', 
                               'is_precision_infinity', 'is_decimals_infinity','uom', 
                               'fiscal_year', 'fiscal_period', 'fiscal_hash', 'fact_hash',
                               'calendar_year', 'calendar_period', 'calendar_hash', 
                               'is_extended'), 
                              ('accession_id', 'xml_id', 'uom', 'is_extended'),
                              tuple((f['accession_id'], f['tuple_fact_id'], f['context_id'], f['unit_id'], f['unit_base_id'], f['element_id'], f['effective_value'], f['fact_value'], 
                               f['xml_id'], f['precision_value'], f['decimals_value'], 
                               f['is_precision_infinity'], f['is_decimals_infinity'], f['uom'], 
                               f['fiscal_year'], f['fiscal_period'], f['fiscal_hash'], f['fact_hash'],
                               f['calendar_year'], f['calendar_period'], f['calendar_hash'], 
                               f['is_extended'])
                              for f in insertForFact.values()))
        
        for id, _accsId, xmlId, uom, isExtended in table:
            #put the database id of the fact on the ModelFact object
            insertForFact[xmlId]['model_fact'].dbFactId = id
        #recurse for the tuple facts. The sub facts of a tuple are not included in modelFacts.
        for tupleFact in tuples:
            tupleInserts, tupleResults = self.getFactsForTuple(tupleFact.modelTupleFacts, tupleFact.dbFactId)
            insertForFact.update(tupleInserts)
            table += tupleResults

        return insertForFact, table
    
    def postLoad(self):
        try:
            self.sourceCall()
        except self._SourceFunctionError:
            pass

    def updateReportStats(self):
         
        #recalculate the restatement index for all reports for the entity.
        query = '''
            UPDATE report r
            SET restatement_index = rn
            FROM (
                SELECT row_number() over(w) AS rn, report_id
                FROM report
                WHERE entity_id = %s
                WINDOW w AS (partition BY entity_id, reporting_period_end_date ORDER BY accepted_timestamp DESC)) x
            WHERE r.report_id = x.report_id 
              AND x.rn <> coalesce(r.restatement_index,0)''' % (self.entityId)
        self.execute(query, fetch=False)
        
        #recalculate the period index for all reports for the entity
        query = '''
            UPDATE report r
            SET period_index = rn
            FROM (
                SELECT row_number() over(w) AS rn, report_id
                FROM report
                WHERE entity_id = %s
                WINDOW w AS (partition BY entity_id ORDER BY reporting_period_end_date DESC, restatement_index ASC)) x
            WHERE r.report_id = x.report_id
              AND x.rn <> coalesce(r.period_index, 0)''' % (self.entityId)
        self.execute(query, fetch=False)
        
        #update is most current
        query = '''
            UPDATE report r
            SET is_most_current = x.is_most_current
            FROM (
                SELECT row_number() over (w) = 1 AS is_most_current, report_id
                FROM report
                WHERE entity_id = %s
                WINDOW w AS (ORDER BY accepted_timestamp DESC, source_report_identifier)) x
            WHERE r.report_id = x.report_id
              AND r.is_most_current != x.is_most_current''' % (self.entityId)
        self.execute(query, fetch=False)

    def getSourceSetting(self, name):
        if self.sourceMod is not None:
            if hasattr(self.sourceMod, '__sourceInfo__'):
                if name in self.sourceMod.__sourceInfo__:
                    return self.sourceMod.__sourceInfo__[name]
        return None

    def sourceCall(self, *args, **kwargs):
        callFunctionName = inspect.stack()[1][3]
        callFunction = None
        #check if there is a source module being used
        if self.sourceMod is not None and hasattr(self.sourceMod, '__sourceInfo__') and "overrideFunctions" in self.sourceMod.__sourceInfo__:
            #check if the function is in the source module
            callFunction = self.sourceMod.__sourceInfo__['overrideFunctions'].get(callFunctionName)
        
        if callFunction is None:
            raise self._SourceFunctionError
        else:           
            return callFunction(self, *args, **kwargs)

         