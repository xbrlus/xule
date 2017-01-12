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

def insertIntoDB(modelXbrl, 
                 user=None, password=None, host=None, port=None, database=None, timeout=None,
                 options=None):
    
    xpgdb = None

    try:
        xpgdb = XbrlPostgresDatabaseConnection(modelXbrl, user, password, host, port, database, timeout, 'postgres', options)
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
                "unit", "unit_measure", 
                "context",  "context_dimension", "context_dimension_explicit",
                "accession", "accession_document_association", "accession_element", "accession_timestamp",
                "attribute_value",
                "custom_role_type",
                "uri",
                "document",
                "qname",
                "taxonomy", "taxonomy_version", "namespace", "base_namespace",
                "element", "element_attribute", "element_attribute_value_association",
                "network", "relationship",
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
    
    def __init__(self, modelXbrl, user, password, host, port, database, timeout, db_type, options):
        super().__init__(modelXbrl, user, password, host, port, database, timeout, db_type)
        self.options = options
        self.startTime = datetime.datetime.today()
    
    def verifyTables(self):
        missingTables = XBRLDBTABLES - self.tablesInDB()
#         # if no tables, initialize database
#         if missingTables == XBRLDBTABLES:
#             self.create("xbrlPublicPostgresDB.ddl")
#             
#             # load fixed tables
#             self.getTable('enumeration_arcrole_cycles_allowed', 'enumeration_arcrole_cycles_allowed_id', 
#                           ('description',), ('description',),
#                           (('any',), ('undirected',), ('none',)))
#             self.getTable('enumeration_element_balance', 'enumeration_element_balance_id', 
#                           ('description',), ('description',),
#                           (('credit',), ('debit',)))
#             self.getTable('enumeration_element_period_type', 'enumeration_element_period_type_id', 
#                           ('description',), ('description',),
#                           (('instant',), ('duration',), ('forever',)))
#             missingTables = XBRLDBTABLES - self.tablesInDB()
        if missingTables:
            raise XPDBException("xpgDB:MissingTables",
                                _("The following tables are missing, suggest reinitializing database schema: %(missingTableNames)s"),
                                missingTableNames=', '.join(t for t in sorted(missingTables))) 
            
    def insertXbrl(self, supportFiles=tuple(), documentCacheLocation=None):
        try:            
            
            # must also have default dimensions loaded
            from arelle import ValidateXbrlDimensions

            ValidateXbrlDimensions.loadDimensionDefaults(self.modelXbrl)
            
            self.documentMap = dict()
            #set up document map
            self.documentCacheLocation = documentCacheLocation
            
            # find pre-existing documents in server database
            self.timeCall(self.identifyEntityAndFilingingInfo, supportFiles)

            #check if the filing is already in the database
            result = self.timeCall(self.execute, "SELECT 1 FROM accession WHERE filing_accession_number = '%s';" % self.accessionNumber)
            if result:
                self.modelXbrl.info("info", _("%(now)s - Skipped filing already in database. Accession filing number:  %(filingNumber)s"),
                        filingNumber=self.accessionNumber,
                        now=str(datetime.datetime.today()))
                return
            
            # don't want to process certain form types (if it is an sec filing).
            excludedForms = ['497', '485BPOS', 'N-CSR', 'N-CSRS', 'N-Q', 'N-CSR/A', 'N-CESRS/A', 'N-Q/A']
            if self.documentType is not None:
                if self.documentType.strip() in excludedForms:
                    self.modelXbrl.info("info", _("%(now)s - Skipped filing due to excluded form type:  %(formType)s"),
                        formType=self.documentType,
                        now=str(datetime.datetime.today()))
                    return            

#             self.execute('''LOCK ONLY document, qname, uri, namespace, element, custom_arcrole_type, custom_arcrole_used_on, custom_role_type, custom_role_used_on, entity 
#                         IN ACCESS EXCLUSIVE MODE;''', fetch=False)
            self.execute('''LOCK ONLY config 
                         IN ACCESS EXCLUSIVE MODE;''', fetch=False)
            self.identifyPreexistingDocuments()
            self.identifyBaseNamespaces()
            self.identifyConceptsUsed()
            self.insertEntity()
            self.identifyFiscalYearEnd()
            self.insertDocuments()
            self.insertQnames()
            self.insertUris()
            self.insertNamespaces()
            self.insertElements()
            self.insertCustomArcroles()
            self.insertCustomRoles()
            
            #self.commit()
            self.insertAccession()
            self.insertAccessionDocumentAssociation()
            self.insertEntityNameHistory()
            self.insertAccessionElements()            
            self.insertFacts()
            self.insertNetworks()
            self.updateAccessionStats()
            
#             self.modelXbrl.profileStat(_("XbrlPublicDB: DTS insertion"), time.time() - startedAt)
#             startedAt = time.time()
#             self.modelXbrl.profileStat(_("XbrlPublicDB: instance insertion"), time.time() - startedAt)
#             startedAt = time.time()
            self.showStatus("Committing entries")
            self.commit()
#             self.modelXbrl.profileStat(_("XbrlPublicDB: insertion committed"), time.time() - startedAt)
            self.showStatus("DB insertion completed", clearAfter=5000)
            
            endTime = datetime.datetime.today()
            hours, remainder = divmod((endTime - self.startTime).total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            self.modelXbrl.info("info", _("%(now)s - Loaded into database in %(timeTook)s %(accessionNumber)s %(formType)s %(companyName)s %(period)s"),
                accessionNumber=self.accessionNumber, 
                formType=self.documentType, 
                companyName=self.entityName, 
                period=self.period,
                timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds),
                now=str(datetime.datetime.today()))
    
        except Exception as ex:
            self.showStatus("DB insertion failed due to exception", clearAfter=5000)
            raise
    
    def timeCall(self, function=None, *args, **kwargs):
        functionStartTime = datetime.datetime.today()
        function(*args, **kwargs)
        if getattr(self.options, 'xbrlusDBTime', False):
            functionEndTime = datetime.datetime.today()
            hours, remainder = divmod((functionEndTime - functionStartTime).total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            self.modelXbrl.info("info", _("Function: %s - took %s" % (function.__name__, '%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds))))

    def identifyBaseNamespaces(self):
        def getPrefix(namespace, expression):
            prefix = re.findall(expression, namespace)
            return prefix[0] if prefix else None
        
        # use all namespace URIs
        namespaceUris = self.modelXbrl.namespaceDocs.keys() 
        
        
        
        
        # get list of namespace prefaces that indicate the namespace is base
        results = self.execute("SELECT preface,  prefix_expression FROM base_namespace;")
        namespace_prefaces = [{'preface' :row[0], 'regex': row[1]} for row in results]
        #sort the prefaces so the longest ones are first. This will allow preface like /a/b/c/d to match to /a/b/c before /a/b.
        namespace_prefaces.sort(key=lambda x: x['preface'], reverse=True)
        
        #Find namespace prefixes based on the regular expression in the base_namespace table.
        self.baseNamespaces = {}
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
        
    def identifyEntityAndFilingingInfo(self, supportFiles):        
        self.entityName = self.getSimpleFactByQname('/dei/','EntityRegistrantName')
        
        self.entityIdentifier = self.getSimpleFactByQname('/dei','EntityCentralIndexKey')
        if self.entityIdentifier:
            self.entityScheme = 'http://www.sec.gov/CIK'
        self.documentType = self.getSimpleFactByQname('/dei','DocumentType')
        self.period = self.getSimpleFactByQname('/dei','DocumentPeriodEndDate')
        
        indexFile = None
        rssItem = None
        
        if supportFiles is not None:
            for fileName in supportFiles:
                if os.path.splitext(fileName)[1] == '.htm':
                        indexFile = fileName
                else:
                    #open the file and see if it is an rss item
                    try:
                        rssItemTree = etree.parse(fileName)
                        rssItem = rssItemTree.getroot()
                        if rssItem.tag != 'item':
                            raise XPDBException("xpgDB:rssItemSupportFileError",
                                    _("Expecting support file to be an rss item file, but the root tag is not 'item'. File '%s'." % fileName))
                    except etree.XMLSyntaxError:
                        pass
                    except:
                        raise XPDBException("xpgDB:badSupportFile",
                                    _("Problem opening supporting file '%s'." % fileName))
                    
            #acquire filing attributes from the rss feed
            if rssItem is not None:
                rssNS = {'edgar': 'http://www.sec.gov/Archives/edgar'}
                if not self.entityName:
                    self.entityName = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:companyName/text()', rssNS)
                if not self.entityIdentifier:
                    self.entityIdentifier = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:cikNumber', rssNS)
                    self.entityScheme = 'http://www.sec.gov/CIK'
                rssDocumentType = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:formType', rssNS)
                if rssDocumentType is not None and rssDocumentType != self.documentType:
                    self.documentType = rssDocumentType
                
                if not self.period:
                    reportingPeriod = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:period', rssNS)
                    self.period = reportingPeriod[0:4] + "-" + reportingPeriod[4:6] + "-" + reportingPeriod[6:8]
                '''
                # only do this if it is not found in the filing as a fact. The fact is more reliable than the rss feed data.
                if not (bool(self.fiscalYearMonthEnd) and bool(self.fiscalYearDayEnd)):
                    fiscalYearEnd = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:filscalYearEnd', rssNS)
                    self.fiscalYearMonthEnd = int(fiscalYearEnd[:2])
                    self.fiscalYearDayEnd = int(fiscalYearEnd[:2])
                '''    
                self.accessionNumber = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:accessionNumber', rssNS)
                self.sic = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:assignedSic', rssNS, -1)
                
                rssDate = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:acceptanceDatetime', rssNS)
                if rssDate is None:
                    self.acceptanceDate = None
                else:
                    self.acceptanceDate = rssDate[0:4] + '-' + rssDate[4:6] + '-' + rssDate[6:8] + ' ' + rssDate[8:10] + ':' + rssDate[10:12] + ':' + rssDate[14:16]
                
                self.filingDate = self.xmlFind(rssItem, 'edgar:xbrlFiling/edgar:filingDate', rssNS)
                
                self.htmlFilingInfoFile = self.xmlFind(rssItem, 'link')
                self.entryUrl = None
                self.htmlInstance = None
                for fileNode in rssItem.findall('edgar:xbrlFiling/edgar:xbrlFiles/edgar:xbrlFile', rssNS):
                    if fileNode.get('{http://www.sec.gov/Archives/edgar}type') == 'EX-101.INS':
                        self.entryUrl = fileNode.get('{http://www.sec.gov/Archives/edgar}url')
                        break
                    elif fileNode.get('{http://www.sec.gov/Archives/edgar}type') == self.documentType:
                        if os.path.splitext(fileNode.get('{http://www.sec.gov/Archives/edgar}url'))[1] != '.pdf':
                            self.htmlInstance = fileNode.get('{http://www.sec.gov/Archives/edgar}url')
                            
                if self.htmlInstance is None:
                    raise XPDBException("xpgDB:cannotFindTextFiling",
                                    _("Cannot identify the htm or text version of the filing. This is normally the document with the same type as the filing type.")) 
                if self.entryUrl is None:
                    self.entryUrl = self.htmlInstance
                
                if self.htmlFilingInfoFile is None:
                    raise XPDBException("xpgDB:missingSupportFiles",
                                    _("Cannot acquire filing details. Htm index file cannot be determined from the rss item."))
                indexFile = self.reverseMapDocumentUri(self.htmlFilingInfoFile)
                filingAttributes = self.extractFilingDetailsFromIndex(indexFile)
                for attrName, attrValue in filingAttributes.items():
                    #only populate if the value hasn't already been acquired from the rss item
                    if not hasattr(self, attrName):
                        setattr(self, attrName, attrValue)
            else:
                #acquire filing attributes from html index file
                if indexFile is None:
                    raise XPDBException("xpgDB:missingSupportFiles",
                                    _("Cannot acquire filing details. No htm index file or rss item supplied."))
                
                filingAttributes = self.extractFilingDetailsFromIndex(indexFile)
                for attrName, attrValue in filingAttributes.items():
                    setattr(self, attrName, attrValue)
                
        # default the entity identifier
#         if not self.entityIdentifier:
#             self.entityIdentifier = 'UNKNOWN'
#             self.entityScheme = 'http://www.sec.gov/CIK'
        if not self.entityName:
            self.entityName = 'UNKNOWN'
            
        self.collectionSource = 'SEC'
        
        #fill in defaults
        self.defaultEntityAndFilingInfo()

    def defaultEntityAndFilingInfo(self):
        #Certain information is necessary to process a filing.
        if getattr(self, "accessionNumber", None) is None:
            #see if it was passed as an option
            self.accessionNumber = getattr(self.options, "xbrlusDBFilingId", None)
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
                
    def xmlFind(self, root, path, namespaces=None, default=None):
        node = root.find(path, namespaces)
        if node is None:
            return default
        else:
            return node.text

    def identifyFiscalYearEnd(self):
        #get from the CurrentFiscalYearEndDate in the filing
        self.fiscalYearMonthDayEnd = self.getSimpleFactByQname('/dei','CurrentFiscalYearEndDate')
        
        if self.fiscalYearMonthDayEnd is None and getattr(self, "filingDate", None) is not None:
            #get from previous filings
            results = self.execute(
            '''
                SELECT f.fact_value
                 FROM   fact f
                 JOIN element e
                   ON f.element_id = e.element_id
                 JOIN qname qe
                   ON e.qname_id = qe.qname_id
                 JOIN accession a
                   ON f.accession_id = a.accession_id
                 JOIN namespace n
                   ON qe.namespace = n.uri
                 WHERE qe.local_name = 'CurrentFiscalYearEndDate'
                   AND n.prefix = 'dei'
                   AND a.entity_id = %s
                 ORDER BY CASE WHEN %s >= a.filing_date THEN 0 ELSE 1 END
                          ,abs(%s - a.filing_date);
            ''', params=(self.entityId, self.filingDate, self.filingDate))
            if len(results) > 0:
                self.fiscalYearMonthDayEnd = results[0][0]
                
        self.fiscalYearMonthEnd = None
        self.fiscalYearDayEnd = None
        if self.fiscalYearMonthDayEnd is not None:
            if self.fiscalYearMonthDayEnd.startswith("--"): 
                fiscalYearMonthDayEndList = self.fiscalYearMonthDayEnd.split('-')
                if len(fiscalYearMonthDayEndList) == 4:
                    self.fiscalYearMonthEnd = int(fiscalYearMonthDayEndList[2])
                    self.fiscalYearDayEnd = int(fiscalYearMonthDayEndList[3])
            else:
                self.fiscalYearMonthEnd = int(self.fiscalYearMonthDayEnd[:2])
                self.fiscalYearDayEnd = int(self.fiscalYearMonthDayEnd[2:])

    def extractFilingDetailsFromIndex(self, indexFileName):
        with self.getFile(indexFileName) as indexFileHandler:
            #indexFileHandler = self.getFile(indexFileName)
            htmlParser = etree.HTMLParser()
            htmlTree = etree.parse(indexFileHandler, htmlParser)
        identInfoNodes = htmlTree.xpath("//div[@class='companyInfo']")
        #There may be multiple nodes. Find the one that has the matching cik.
        for identInfoNode in identInfoNodes:
            identInfoDict = dict()
            nextKey = None
            for x in etree.ElementTextIterator(identInfoNode):
                if nextKey is None:
                    #only getting this from the CurrentFiscalYearEndDate fact in the filing
#                     if 'fiscal year end' in x.lower():
#                         nextKey = 'fiscalYearMonthDayEnd'
                    if 'irs no' in x.lower():
                        nextKey = 'irsNumber'
                    elif 'state of incorp' in x.lower():
                        nextKey = 'stateOfIncorporation'
                    elif 'type' in x.lower():
                        nextKey = 'documentType'
                    elif 'sic' in x.lower():
                        nextKey = 'sic'
                    elif 'cik' in x.lower():
                        nextKey = 'entityIdentifier'
                    if nextKey in identInfoDict:
                        #the key was already found.
                        nextKey = None
                else:
                    if not x.replace(':','').strip() == '':
                        if nextKey == 'entityIdentifier':
                            identInfoDict[nextKey] = x.strip()[:10]
                        else:
                            identInfoDict[nextKey] = x.strip()
                        nextKey = None
                        
            #getting mailing address. This is in a sibling element
            for mailer in identInfoNode.getparent().xpath("div[@class='mailer']"):
                if 'business address' in mailer.text.lower():
                    addressParts = [a.text.strip() for a in mailer.getchildren()] 
                    #the last part is the phone number
                    if len(addressParts) > 1:
                        identInfoDict['entityAddress'] = ", ".join(addressParts[:-1])
                        identInfoDict['entityPhone'] = addressParts[-1]
                
            if identInfoDict.get('entityIdentifier') == self.entityIdentifier:
                break
        #get accession number
        secNumNodes = htmlTree.xpath("//div[@id='secNum']")
        secNumNode = secNumNodes[0] if len(secNumNodes) > 0 else None
        if secNumNode is not None:
            identInfoDict['accessionNumber'] = self.getNodeText(secNumNode)[-1].strip()
            
        #filing date and accepted date
        headingDivs = htmlTree.xpath("//div[@class='infoHead']")
        for headingDiv in headingDivs:
            if 'filing date' == headingDiv.text.lower():
                identInfoDict['filingDate'] = headingDiv.getnext().text.strip()
            if 'accepted' in headingDiv.text.lower():
                identInfoDict['acceptanceDate'] = headingDiv.getnext().text.strip()
            if 'period of report' in headingDiv.text.lower():
                identInfoDict['period'] = headingDiv.getnext().text.strip()

        identInfoDict['htmlFilingInfoFile'] = self.mapDocumentUri(indexFileName)
        identInfoDict['entryUrl'] = self.cleanDocumentUri(self.modelXbrl.modelDocument)

        #get HTML version of the filing
        docType = identInfoDict.get('documentType')
        if docType is not None:
            for fileTable in htmlTree.xpath("//table[@class='tableFile']"):
                for tr in fileTable:
                    if tr[3].tag.lower() == 'td' and tr[3].text == docType:
                        href = tr[2][0].get('href')
                        if os.path.splitext(href)[1] == '.htm':
                            #found the file
                            if self.isUrl(os.path.dirname(indexFileName)):
                                identInfoDict['htmlInstance'] = urllib.parse.urljoin(indexFileName, tr[2][0].text)
                            else:
                                identInfoDict['htmlInstance'] = os.path.join(os.path.dirname(indexFileName), tr[2][0].text)
                            


        return identInfoDict
        
    def getNodeText(self, node):
        return [x for x in etree.ElementTextIterator(node)]
    
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
    
    def reportTime(self, startTime, endTime, note):

        hours, remainder = divmod((endTime - startTime).total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.modelXbrl.info("info",_("%(now)s - %(note)s loaded in %(timeTook)s"),
                                      now=str(datetime.datetime.today()),
                                      note=note,
                                      timeTook='%02.0f:%02.0f:%02.4f' % (hours, minutes, seconds))         
    def insertEntity(self):
        
        self.showStatus("insert entity")
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

    def insertEntityNameHistory(self):
        #delete existing records that where added after this filing. This handles resetting the entity name history if the filings are processed in order.
        self.execute('''DELETE FROM entity_name_history 
                        WHERE accession_id IN
                        (SELECT accession_id
                         FROM accession
                         WHERE entity_id = %s
                           AND accepted_timestamp >= %s)''', params=(self.entityId, self.accepted_timestamp),
                     close=False, fetch=False)
        #get the current entity name
        result = self.execute('''SELECT enh.entity_name
                        FROM entity_name_history enh
                        JOIN accession a
                          ON enh.accession_id = a.accession_id
                        WHERE a.entity_id = {0}
                        ORDER BY a.accepted_timestamp DESC
                        LIMIT 1'''.format(self.entityId))
        if len(result) == 1:
            currentEntityName = result[0][0]
        else:
            currentEntityName = None
          
        #get all the accessions after and including the processing accession.
        result = self.execute('''SELECT accession_id, trim(both entity_name) 
                        FROM accession
                        WHERE entity_id = %s
                          AND accepted_timestamp >= %s
                        ORDER BY accepted_timestamp''', params=(self.entityId, self.accepted_timestamp))

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
                                    and partialNS in item.qname.namespaceURI
                                    and len(item.context.qnameDims) == 0]      
        if len(simpleFacts) > 0:
            return simpleFacts[0].textValue

    def insertAccession(self):
        self.accessionId = "(TBD)"
        self.showStatus("insert accession")
        
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
        
        
        indexHtmlFile = getattr(self, "htmlFilingInfoFile", None)
        zipFile = indexHtmlFile.replace('-index.htm', '-xbrl.zip') if indexHtmlFile is not None else None
        
        indexHtml = self.mapDocumentUri(self.htmlInstance) if hasattr(self,'htmlInstance') else None
        indexHtmlId = self.documentIds[self.mapDocumentUri(self.htmlInstance)] if hasattr(self,'htmlInstance') else None
        
        table = self.getTable('accession', 'accession_id', 
                              ('accepted_timestamp', 'is_most_current', 'filing_date','entity_id', 
                               'entity_name', 'creation_software', 'standard_industrial_classification', 
                               'sec_html_url', 'entry_url', 'filing_accession_number', 'internal_revenue_service_number',
                               'business_address', 'business_phone', 'document_type', 'state_of_incorporation','entry_type',
                               'entry_document_id', 'alternative_document_id', 'zip_url', 'reporting_period_end_date'), 
                              ('filing_accession_number',), 
                              ((getattr(self, "acceptanceDate",  datetime.date(datetime.MAXYEAR, 12, 31)),
                                True,
                                getattr(self, "filingDate", datetime.datetime(datetime.MAXYEAR, 12, 31)),  # NOT NULL
                                self.entityId,  # NOT NULL
                                self.entityName,
                                creationSoftware,
                                getattr(self, "sic", -1),  # NOT NULL
                                indexHtmlFile,
                                getattr(self, "entryUrl", None),
                                self.accessionNumber,
                                getattr(self, "irsNumber", -1),
                                getattr(self, "entityAddress", None),
                                getattr(self, "entityPhone", None),
                                getattr(self, "documentType", None),
                                getattr(self, "stateOfIncorporation", None),
                                entryType,
                                self.documentIds[self.cleanDocumentUri(self.modelXbrl.modelDocument)],
                                self.documentIds[indexHtml] if indexHtml is not None else None,
                                zipFile,
                                self.period
                                ),),
                              checkIfExisting=True,
                              returnExistenceStatus=True)
        for id, filing_accession_number, existenceStatus in table:
            self.accessionId = id
            self.accessionPreviouslyInDB = existenceStatus            
            break
        
        result = self.execute("SELECT accepted_timestamp FROM accession WHERE accession_id = %i" % self.accessionId)
        if result:
            self.accepted_timestamp = result[0][0]
        else:
            raise XPDBException("xpgDB:AcceptedTimestampError",
                                _("Could not retrieve the accepted_timestamp for accession_id %(accessionId)s"),
                                accessionId=self.accessionId)
        
        #add accession timestampe record
        self.execute("INSERT INTO accession_timestamp (accession_id) VALUES ({})".format(self.accessionId), close=False, fetch=False)
        
          
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
        
        '''
        Took out the attributes in the qname list because some attributes don't have a namespace. The getTable function
        doesn't quite handle nulls in a good way.
        '''
        
        #attributes
        attributeQNames = set()
        for concept in self.filingDocumentConcepts:
            for atrribName, attribValue in concept.attrib.items():
                if atrribName not in ('abstract','id','nillable','type','substitutionGroup','name'):
                    attribQName = qname(atrribName)
                    if not (attribQName.namespaceURI == 'http://www.xbrl.org/2003/instance' and attribQName.localName in ('balance','periodType')):
                        #self.attributeQNames.append((self.getQnameId(concept.qname),self.getQNameId(attribQName),attribValue))
                        attributeQNames.add(attribQName)        
        
        qnames = (#_DICT_SET(self.modelXbrl.qnameConcepts.keys()) |
                  #_DICT_SET(self.modelXbrl.qnameAttributes.keys()) |
                  _DICT_SET(self.modelXbrl.qnameTypes.keys()) |
                  set(measure
                      for unit in self.modelXbrl.units.values()
                      for measures in unit.measures
                      for measure in measures) |
                  self.modelXbrl.qnameConcepts.keys() |
                  #set(concept.qname for concept in self.filingDocumentConcepts | self.nonReportingConcepts) |
                  attributeQNames 
                  )
        
        self.showStatus("insert qnames")
        table = self.getTable('qname', 'qname_id', 
                              ('namespace', 'local_name'), 
                              ('namespace', 'local_name'), # indexed match cols
                              tuple((qn.namespaceURI, qn.localName) 
                                    for qn in qnames),
                              checkIfExisting=True)

        self.qnameId = dict((qname(ns, ln), id)
                            for id, ns, ln in table)

        # get qname IDs for existing concepts
#         if self.existingDocumentIds:
#             results = self.execute("SELECT q.qname_id, q.namespace, q.local_name " +
#                                            "FROM qname q " +
#                                            "JOIN element e " +
#                                            "  ON q.qname_id = e.qname_id " +
#                                            "JOIN document d " +
#                                            "  ON e.document_id = d.document_id " +
#                                            "WHERE d.document_uri IN (" +
#                                            ','.join("'%s'" % docId for docId in self.existingDocumentIds) +
#                                            ");") 
#             for qnameId, namespaceURI, localName in results:
#                 self.qnameId[qname(namespaceURI, localName)] = qnameId
#             
        #get qname_ids for existing concepts
#         if self.existingDocumentUsedConcepts:
#             qnamesClause = []
#             for concept in self.existingDocumentUsedConcepts:
#                 qnamesClause.append("(namespace = '%s' and local_name = '%s')" % (concept.qname.namespaceURI, concept.qname.localName))
#                 
#                 
#             results = self.execute("SELECT qname_id, namespace, local_name FROM qname WHERE " + ' OR '.join(qnamesClause) + ";")
#             for qnameId, namespaceURI, localName in results:
#                 self.qnameId[qname(namespaceURI, localName)] = qnameId
                
   
#             qnamesClause.append("(namespace = '%s' and local_name = '%s')" % (concept.qname.namespaceURI, concept.qname.localName))
#             results = self.execute("SELECT qname_id, namespace, local_name FROM qname WHERE " + ' OR '.join(qnamesClause) + ";")
#             for qnameId, namespaceURI, localName in results:
#                 self.qnameId[qname(namespaceURI, localName)] = qnameId
   

      
    def insertNamespaces(self):
        self.showStatus("insert namespaces")
        namespaceUris = self.modelXbrl.namespaceDocs.keys()               

        table = self.getTable('namespace', 'namespace_id', 
                              ('uri', 'is_base', 'taxonomy_version_id', 'prefix'), 
                              ('uri','is_base'), # indexed matchcol
                              tuple((uri, uri in self.baseNamespaces.keys(), None, self.baseNamespaces[uri] if uri in self.baseNamespaces.keys() else None) 
                                    for uri in namespaceUris),
                              checkIfExisting=True)
        self.namespaceId = dict((uri, {"id": id, "isBase": isBase})
                                for id, uri, isBase in table)

        
    def identifyPreexistingDocuments(self):
        self.existingDocumentIds = {}
        docUris = set()
        for modelDocument in self.modelXbrl.urlDocs.values():
            if modelDocument.type == Type.SCHEMA:
                docUris.add(self.dbStr(self.cleanDocumentUri(modelDocument)))
        if docUris:
            results = self.execute("SELECT document_id, document_uri, document_loaded FROM document WHERE document_uri IN (" +
                                   ', '.join(docUris) + ");")
            self.existingDocumentIds = dict((docUri,docId) for docId, docUri, docLoaded in results if docLoaded == True)
            self.setDocumentIdsLoaded = tuple((docId, docUri) for docId, docUri, docLoaded in results if docLoaded == False)
        
    def identifyConceptsUsed(self):
        # relationshipSets are a dts property
        self.relationshipSets = [(arcrole, ELR, linkqname, arcqname)
                                 for arcrole, ELR, linkqname, arcqname in self.modelXbrl.baseSets.keys()
                                 if ELR and (arcrole.startswith("XBRL-") or (linkqname and arcqname))]
        
        conceptsUsed = set(f.qname for f in self.modelXbrl.factsInInstance)
        
        #this will contain concpets in facts and relationships
        conceptsUsed2 = dict()
        
        def conceptsUsedIncrement(conceptQname, useType):
            if conceptQname not in conceptsUsed2:
                conceptsUsed2[conceptQname] = {'primary': 0, 'dimension': 0, 'member': 0, 'isBase': conceptQname.namespaceURI in self.baseNamespaces}
            
            if useType:
                conceptsUsed2[conceptQname][useType] += 1
            
        
        for f in self.modelXbrl.factsInInstance:
            conceptsUsedIncrement(f.qname, 'primary')
#             if f.context is not None:
#                 for dim in f.context.qnameDims.values():
#                     conceptsUsedIncrement(dim.dimensionQname, 'dimension')
#                     if dim.isExplicit:
#                         conceptsUsedIncrement(dim.memberQname, 'member')
        
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
            
        for relationshipSetKey in self.relationshipSets:
            relationshipSet = self.modelXbrl.relationshipSet(*relationshipSetKey)
            for rel in relationshipSet.modelRelationships:
                if isinstance(rel.fromModelObject, ModelConcept):
                    conceptsUsed.add(rel.fromModelObject)
                    conceptsUsedIncrement(rel.fromModelObject.qname, None)
                if isinstance(rel.toModelObject, ModelConcept):
                    conceptsUsed.add(rel.toModelObject)
                    conceptsUsedIncrement(rel.toModelObject.qname, None)
                    
        for qn in (XbrlConst.qnXbrliIdentifier, XbrlConst.qnXbrliPeriod, XbrlConst.qnXbrliUnit):
            conceptsUsed.add(self.modelXbrl.qnameConcepts[qn])
        
        conceptsUsed -= {None}  # remove None if in conceptsUsed
        self.conceptsUsed = conceptsUsed
        self.conceptsUsed2 = conceptsUsed2
        
        #Determine which concepts are new. This will reduce the number of concepts and qnames to load.
        self.filingDocumentConcepts = set()
        self.existingDocumentUsedConcepts = set()
        self.existingDocumentConcepts = set()
        self.nonReportingConcepts = set()
        for concept in self.modelXbrl.qnameConcepts.values():
            if self.cleanDocumentUri(concept.modelDocument) not in self.existingDocumentIds:
                if concept.isItem or concept.isTuple:
                    self.filingDocumentConcepts.add(concept)
                else:
                    self.nonReportingConcepts.add(concept)
            else:
                self.existingDocumentConcepts.add(concept)
                if concept in self.conceptsUsed:
                    self.existingDocumentUsedConcepts.add(concept)
                
        
    def insertDocuments(self):
        self.showStatus("insert documents")
    
        docsToLoad = dict()
        for doc in self.modelXbrl.urlDocs.values():
            docUri = self.cleanDocumentUri(doc)
            if docUri not in self.existingDocumentIds:
                if doc.type == Type.INLINEXBRL and doc is self.modelXbrl.modelDocument:
                    with self.getFile(doc.filepath) as inlineFile:
                        docContent = inlineFile.read().decode()
                    #docContent = etree.tostring(doc.xmlDocument, encoding=doc.documentEncoding)
                else:                    
                    docContent = None
                docsToLoad[docUri] = docContent
        
        if hasattr(self, "htmlInstance"):
            htmlInstanceUri = self.mapDocumentUri(self.htmlInstance)
            if htmlInstanceUri not in docsToLoad:
                with self.getFile(self.htmlInstance) as htmlFile:
                    docsToLoad[htmlInstanceUri] = htmlFile.read().decode()
        '''
        if self.modelXbrl.modelDocument.type == Type.INSTANCE and hasattr(self, "htmlInstance"):
            with self.getFile(self.htmlInstance) as htmlFile:
                docsToLoad[self.htmlInstance] = htmlFile.read().decode()
        '''
        table = self.getTable('document', 'document_id', 
                              ('document_uri','content'), 
                              ('document_uri',), 
                              docsToLoad.items(),
                              checkIfExisting=True)
        self.documentIds = dict((uri, id)
                                for id, uri in table)
        self.documentIds.update(self.existingDocumentIds)
        
        updateData = [(docId, True) for docId, docUrl in self.setDocumentIdsLoaded]
        updateIds = self.updateTable('document', ('document_id', 'document_loaded'), updateData)
        
        loadedDocs = dict((docUri, docId) for docId, docUri in self.setDocumentIdsLoaded)
        self.documentIds.update(loadedDocs)
        
        

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
        
    def reverseMapDocumentUri(self, documentUri):
        '''Map an official uri to cache location
        '''
        if self.documentCacheLocation is not None:
            uriParts = urllib.parse.urlparse(documentUri)
            if uriParts.scheme.startswith('http'):
                cacheFile = os.path.join(self.documentCacheLocation, uriParts.netloc, uriParts.path[1:] if uriParts.path[0] == '/' else uriParts.path)
                if os.path.isfile(cacheFile):
                    return cacheFile
        #Could not map to the cache
        return documentUri

    def insertAccessionDocumentAssociation(self):        
        table = self.getTable('accession_document_association', 'accession_document_association_id', 
                              ('accession_id','document_id'), 
                              ('accession_id','document_id',), 
                              tuple((self.accessionId, docId) 
                                    for docId in self.documentIds.values()),
                              checkIfExisting=True)
        
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

        newElements = list()
        newElementAttributes = list()

        for concept in self.filingDocumentConcepts:
            newElements.append((self.getQnameId(concept.qname),
                                     self.getQnameId(concept.typeQname), # may be None
                                     self.getQnameId(concept.baseXbrliTypeQname
                                                      if not isinstance(concept.baseXbrliTypeQname, list)
                                                      else concept.baseXbrliTypeQname[0]
                                                      ), # may be None or may be a list for a union
                                     {'debit':1, 'credit':2, None:None}[concept.balance],
                                     {'instant':1, 'duration':2, 'forever':3, None:0}[concept.periodType],
                                     self.getQnameId(concept.substitutionGroupQname), # may be None
                                     concept.isAbstract, 
                                     concept.isNillable,
                                     self.documentIds[self.cleanDocumentUri(concept.modelDocument)],
                                     concept.isNumeric,
                                     concept.isMonetary))
            for atrribName, attribValue in concept.attrib.items():
                if atrribName not in ('abstract','id','nillable','type','substitutionGroup','name'): 
                    attribQName = qname(atrribName)
                    
                    if not (attribQName.namespaceURI == 'http://www.xbrl.org/2003/instance' and attribQName.localName in ('balance','periodType')):
                        newElementAttributes.append((self.getQnameId(concept.qname),self.getQnameId(attribQName),attribValue))
                    
        table = self.getTable('element', 'element_id', 
                              ('qname_id', 'datatype_qname_id', 'xbrl_base_datatype_qname_id', 'balance_id',
                               'period_type_id', 'substitution_group_qname_id', 'abstract', 'nillable',
                               'document_id', 'is_numeric', 'is_monetary'), 
                              ('qname_id',), 
                              newElements)

        self.elementId = dict((qnameId, elementId)  # indexed by qnameId, not by qname value
                              for elementId, qnameId in table)
        #filingDocumentConcepts.clear() # dereference
        
        # get existing element IDs
        if self.existingDocumentUsedConcepts:
            conceptQnameIds = []
            for concept in self.existingDocumentUsedConcepts:
                conceptQnameIds.append(str(self.getQnameId(concept.qname)))
            results = self.execute("SELECT element_id, qname_id FROM element WHERE qname_id IN (" +
                                   ', '.join(conceptQnameIds) + ");")
            for elementId, qnameId in results:
                self.elementId[qnameId] = elementId
        #existingDocumentUsedConcepts.clear() # dereference        
        
        #element attributes
        table = self.getTable('attribute_value', 'attribute_value_id', 
                              ('qname_id', 'text_value'),
                              ('qname_id', 'text_value'),
                              set((a[1],a[2]) for a in newElementAttributes)
                              ,checkIfExisting=True)
        
        attributeValueIds = dict(((qnameId, textValue), attributeValueId) 
                                        for attributeValueId, qnameId, textValue in table)
        
        eava = list((self.elementId[conceptQnameId], attributeValueIds[attributeQnameId,textValue])
                           for conceptQnameId, attributeQnameId, textValue in newElementAttributes)
        
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
                return result[0][0]
            else:
                return None
#                 raise XPDBException("xpgDB:MissingQname",
#                                     _("Could not retrieve the qname id for {%(namespace)s}%(localName)s"),
#                                     namespace=qname.namespaceURI, localName=qname.localName)
    
    def insertAccessionElements(self):
 
        table = self.getTable('accession_element', 'accession_element_id', 
                      ('accession_id', 'element_id', 'is_base', 'primary_count', 'dimension_count', 'member_count'), 
                      ('accession_id', 'element_id'), 
                      tuple((self.accessionId,
                             self.conceptElementIdByQname(conceptQname),
                             ae_detail['isBase'],
                             ae_detail['primary'] if ae_detail['primary'] > 0 else None,
                             ae_detail['dimension'] if ae_detail['dimension'] > 0 else None,
                             ae_detail['member'] if ae_detail['member'] > 0 else None)
                            for conceptQname, ae_detail in self.conceptsUsed2.items()),
                      checkIfExisting=True
                     )        
                   
    def insertNetworks(self):
        self.showStatus("insert resources")
        
        # delete existing
        self.execute("DELETE from relationship r USING network n WHERE r.network_id = n.network_id AND n.accession_id = {0};".format(self.accessionId), 
                     close=False, fetch=False)        
        self.execute("DELETE from network n WHERE n.accession_id = {0};".format(self.accessionId), 
                     close=False, fetch=False)    
        
        '''NEED TO DELETE EXISTING resource, label_resource'''    
        
        # deduplicate resources (may be on multiple arcs)
        # note that lxml has no column numbers, use elementFragmentIdentifier as unique identifier for the doucment (as pseudo-column number)
        uniqueResources = dict(((docId, xmlLoc), {'resource': resource, 'arcrole': rel.arcrole, 'document_id': docId, 'xml_location': xmlLoc})
                                for arcrole, ELR, linkqname, arcqname in self.modelXbrl.baseSets.keys()
                                    for rel in self.modelXbrl.relationshipSet(arcrole, ELR, linkqname, arcqname).modelRelationships
                                        if rel.fromModelObject is not None and rel.toModelObject is not None
                                            for resource in (rel.fromModelObject, rel.toModelObject)
                                                if isinstance(resource, ModelResource)
                                                    for xmlLoc in (elementFragmentIdentifier(resource),)
                                                        for docId in (self.documentIds[self.cleanDocumentUri(resource.modelDocument)],))
        
        resourceData = tuple((self.uriId[resource_info['resource'].role.strip()],
                             self.getQnameId(resource_info['resource'].qname),
                             resource_info['document_id'],
                             resource_info['resource'].sourceline,
                             0,
                             resource_info['xml_location']
                             )
                            for resource_info in uniqueResources.values())
        #add resources
        table = self.getTable('resource', 'resource_id', 
                              ('role_uri_id', 'qname_id', 'document_id', 'document_line_number', 'document_column_number', 'xml_location'), 
                              ('document_id', 'xml_location'), 
                              resourceData,
                              checkIfExisting=True)
        for resourceId, docId, xmlLoc in table:
            uniqueResources[(docId, xmlLoc)]['resource'].dbResourceId = resourceId
        
        #add labels
        self.showStatus("insert labels")
        self.getTable('label_resource', 'resource_id', 
                      ('resource_id', 'label', 'xml_lang'), 
                      ('resource_id',), 
                      tuple((resource_info['resource'].dbResourceId,
                             resource_info['resource'].textValue,
                             resource_info['resource'].xmlLang)
                            for resource_info in uniqueResources.values()
                                if resource_info['arcrole'] in (XbrlConst.conceptLabel, XbrlConst.elementLabel)),
                      checkIfExisting=True)

        #add footnotes
        self.showStatus("insert footnotes")
        self.getTable('footnote_resource', 'resource_id', 
                      ('resource_id', 'footnote', 'xml_lang'), 
                      ('resource_id',), 
                      tuple((resource_info['resource'].dbResourceId,
                             resource_info['resource'].textValue,
                             resource_info['resource'].xmlLang)
                            for resource_info in uniqueResources.values()
                                if resource_info['arcrole'] == XbrlConst.factFootnote),
                      checkIfExisting=True)        
        
        '''NEED TO ADD REFERENCES'''
        
        #references
        referenceParts = []
        for resource_info in uniqueResources.values():
            if resource_info['arcrole'] in (XbrlConst.conceptReference, XbrlConst.elementReference):
                order = 0
                for referencePart in resource_info['resource']:
                    order += 1
                    referenceParts.append((resource_info['resource'].dbResourceId, referencePart.qname, referencePart.textValue, order))
        
        self.showStatus("insert reference parts")
        self.getTable('reference_part', 'reference_part_id',
                      ('resource_id', 'value', 'qname_id', 'ref_order'),
                      ('resource_id', 'qname_id'),
                      tuple((rp[0], rp[2], self.qnameId[rp[1]], rp[3])
                            for rp in referenceParts),
                      checkIfExisting=True)
        
        self.showStatus("insert networks")
        table = self.getTable('network', 'network_id', 
                              ('accession_id', 'extended_link_qname_id', 'extended_link_role_uri_id', 
                               'arc_qname_id', 'arcrole_uri_id', 'description'), 
                              ('accession_id', 'extended_link_qname_id', 'extended_link_role_uri_id', 
                               'arc_qname_id', 'arcrole_uri_id'), 
                              tuple((self.accessionId,
                                     self.getQnameId(linkqname),
                                     self.uriId[ELR.strip()],
                                     self.getQnameId(arcqname),
                                     self.uriId[arcrole.strip()],
                                     None if ELR in XbrlConst.standardRoles else
                                     self.modelXbrl.roleTypes[ELR][0].definition)
                                    for arcrole, ELR, linkqname, arcqname in self.modelXbrl.baseSets.keys()
                                    if ELR and linkqname and arcqname and not arcrole.startswith("XBRL-")))
        self.networkId = dict(((accId, linkQnId, linkRoleId, arcQnId, arcRoleId), id)
                              for id, accId, linkQnId, linkRoleId, arcQnId, arcRoleId in table)
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
        
        for arcrole, ELR, linkqname, arcqname in self.modelXbrl.baseSets.keys():
            if ELR and linkqname and arcqname and not arcrole.startswith("XBRL-"):
                networkId = self.networkId[(self.accessionId,
                                            self.getQnameId(linkqname),
                                            self.uriId[ELR.strip()],
                                            self.getQnameId(arcqname),
                                            self.uriId[arcrole.strip()])]
                relationshipSet = self.modelXbrl.relationshipSet(arcrole, ELR, linkqname, arcqname)
                seq = 1
                visited = set()
                for rootConcept in relationshipSet.rootConcepts:
                    seq = walkTree(relationshipSet.fromModelObject(rootConcept), seq, 1, relationshipSet, dbRels, networkId)   
        
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

        del dbRels[:]   # dererefence
        table = self.getTable('relationship', 'relationship_id', 
                              ('network_id', 'from_element_id', 'to_element_id', 'reln_order', 
                               'from_resource_id', 'to_resource_id', 'calculation_weight', 
                               'tree_sequence', 'tree_depth', 'preferred_label_role_uri_id',
                               'from_fact_id', 'to_fact_id', 'target_role_id'), 
                              ('network_id', 'tree_sequence'), 
                              relsData)

    def unitString(self, unit):
        numerator = '*'.join(x.localName for x in unit.measures[0])
        denominator = '*'.join(x.localName for x in unit.measures[1])
        
        if numerator != '':
            if denominator != '':
                return '/'.join((numerator, denominator))
            else:
                return numerator
    
    def fiscalYear(self, context):
        
#         if self.fiscalYearMonthEnd:
#             if not context.isForeverPeriod:
#                 base_date = context.instantDatetime if context.isInstantPeriod else context.endDatetime
#                 '''
#                 Adjust the date back by 10 days. This is to treat year ends that fall at the very begning
#                 January as the previous year.
#                 '''
#                 base_date = base_date - timedelta(days=10)
#                 
#                 if self.fiscalYearMonthEnd and self.fiscalYearDayEnd:                        
#                     #adjust if the fiscal month/day end is the beginning of the year. These fiscal year ends are treated as if they happen in the previous year.
#                     year_adjustment = -1 if self.fiscalYearMonthEnd == 1 and self.fiscalYearDayEnd <= 10 else 0
#                     #adjust if the date is after the fiscal month/day end. In this case we are in the next fiscal yesar.
#                     year_adjustment += 1 if (base_date.month == self.fiscalYearMonthEnd and base_date.day > self.fiscalYearDayEnd) or base_date.month > self.fiscalYearMonthEnd else 0
#                 
#                     return base_date.year + year_adjustment
                
                
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
        
        def durationString(context):
            return context.startDatetime.strftime('%Y-%m-%d') + ' - ' + context.endDatetime.strftime('%Y-%m-%d')
       
        if self.fiscalYearMonthEnd:       
            if context.isInstantPeriod:
                return self.fiscalPeriodInstant(context, context.instantDatetime.date()) or context.instantDatetime.date() 
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
        normalized_dimensions = [self.hashConceptQname(context.qnameDims[dim].dimensionQname) + '=' + self.hashMember(context.qnameDims[dim]) for dim in context.qnameDims.keys()]
        normalized_dimensions.sort()
        if normalized_dimensions is not None:
            return '|'.join(normalized_dimensions)
    
    def hashMember(self, modelDimension):
        if modelDimension.isExplicit:
            return self.hashConceptQname(modelDimension.memberQname)
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
    
    def hashConceptQname(self, elementQname):
        if elementQname.namespaceURI in self.baseNamespaces.keys():
            if self.baseNamespaces[elementQname.namespaceURI] is None:
                raise XPDBException("xpgDB:UnknownBaseNamespace",
                                _("The namespace %(ns)s is a base namespace, but the taxonomy family cannot be determined. Table 'base_namespace' needs a prefix expression for this namespace."),
                                ns=elementQname.namespaceURI) 
            else:
                return 'b' + self.baseNamespaces[elementQname.namespaceURI] + ':' + elementQname.localName
        else:
            return 'e' + self.hashEntity() + ':' + elementQname.localName

    def hashPrimary(self, fact):
        return self.hashConceptQname(fact.qname)
    
    def hashEntity(self):
        return self.entityScheme + "|" + self.entityIdentifier
     
    def hashUnit(self, fact):
        self.unitString.get((self.accessionId,fact.unitID))

    def hashFact(self, fact):

        if fact.isTuple:
            hash = self.hashTuple(fact)
        else:
            hash_list = [self.hashPrimary(fact),
                         self.hashEntity(),
                         self.cntxInfo.get((self.accessionId,fact.contextID))['period_hash'],
                         self.unitString.get((self.accessionId,fact.unitID)) or ''
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
                             self.unitString.get((self.accessionId,fact.unitID)) or ''
                             ]
        
                if self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash']:
                    hash_list.append(self.cntxInfo.get((self.accessionId,fact.contextID))['dim_hash'])
                
                hash = '|'.join(hash_list)
        
        return hash    
    
    def hashTuple(self, fact):
        hash_list = ['t' + self.hashPrimary(fact)]  + [self.hashFact(subFact) for subFact in fact.modelTupleFacts]
        return '|'.join(hash_list)

    def insertFacts(self):
        accsId = self.accessionId
        if self.accessionPreviouslyInDB:
            self.showStatus("deleting prior facts of this accession")
            # remove prior facts
            self.execute("DELETE from unit_measure "
                         "USING unit "
                         "WHERE unit.accession_id = {0} AND unit_measure.unit_id = unit.unit_id;".format(accsId), 
                         close=False, fetch=False)
            self.execute("DELETE from unit WHERE unit.accession_id = {0};".format(accsId), 
                         close=False, fetch=False)
            self.execute("DELETE FROM context_dimension cd USING context c WHERE cd.context_id = c.context_id AND c.accession_id = {0};".format(accsId),
                         close=False, fetch=False)
            self.execute("DELETE FROM context_dimension_explicit cd USING context c WHERE cd.context_id = c.context_id AND c.accession_id = {0};".format(accsId),
                         close=False, fetch=False)            
            self.execute("DELETE from context WHERE context.accession_id = {0};".format(accsId), 
                         close=False, fetch=False)            
            self.execute("DELETE FROM fact WHERE fact.accession_id = {0};".format(accsId), 
                         close=False, fetch=False)

        self.showStatus("insert facts")
        
        # units        
        table = self.getTable('unit', 'unit_id', 
                              ('accession_id', 'unit_xml_id'), 
                              ('accession_id', 'unit_xml_id'), 
                              tuple((accsId,
                                     unitId)
                                    for unitId in self.modelXbrl.units.keys()))
        self.unitId = dict(((_accsId, xmlId), id)
                           for id, _accsId, xmlId in table)
        
        self.unitString = dict(((_accsId, xmlId), self.unitString(self.modelXbrl.units[xmlId]))
                           for id, _accsId, xmlId in table)
        
        # measures
        table = self.getTable('unit_measure', 'unit_measure_id', 
                              ('unit_id', 'qname_id', 'location_id'), 
                              ('qname_id', 'location_id'), 
                              tuple((self.unitId[(accsId,unit.id)],
                                     self.getQnameId(measure),
                                     1 if (len(unit.measures[1]) == 0) else (i + 2))
                                    for unit in self.modelXbrl.units.values()
                                    for i in range(2)
                                    for measure in unit.measures[i]))


        self.cntxInfo = dict()
        for c in self.modelXbrl.contexts.values():
            calendarValues = self.calendarYearAndPeriod(c)
            self.cntxInfo[(accsId, c.id)] = {'period_start': c.startDatetime if c.isStartEndPeriod else None,
                                             'period_end': c.endDatetime if c.isStartEndPeriod else None,
                                             'period_instant': c.instantDatetime if c.isInstantPeriod else None,
                                             'specifies_dimensions': bool(c.qnameDims),
                                             'entity_scheme': c.entityIdentifier[0],
                                             'entity_identifier': c.entityIdentifier[1],
                                             'fiscal_year': self.fiscalYear(c),
                                             'fiscal_period': self.fiscalPeriod(c),
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
            
        
        for i, val in enumerate(values):
            if not val[4]:
                explicitValues.append((table[i][0],) + val)
                
        if explicitValues:
            table = self.getTable('context_dimension_explicit', 'context_dimension_id', 
                                  ('context_dimension_id', 'context_id', 'dimension_qname_id', 'member_qname_id', 'typed_qname_id', 'is_default', 'is_segment', 'typed_text_content'), 
                                  ('context_id', 'dimension_qname_id', 'member_qname_id'), # shouldn't typed_qname_id be here?  not good idea because it's not indexed in XBRL-US DDL
                                  explicitValues)
        
        self.insertFactSet(self.modelXbrl.facts, None)

        s = datetime.datetime.today()
        self.updateUltimus('normal')
        e1 = datetime.datetime.today()
        self.reportTime(s,e1,'normal ultimus')
        
        self.updateUltimus('calendar')
        e2 = datetime.datetime.today()
        self.reportTime(e1, e2,'calendar ultimus')
        
        #self.insertFactAug()
    
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
            contextAugJoin = ''
            orderBy = 'a.accepted_timestamp DESC, a.accession_id DESC, f.fact_id DESC'
        else:
            #calendar
            indexName = 'calendar_ultimus_index'
            hashName = 'calendar_hash'
            factsByHash = self.factsByCalendarHashString
            contextAugJoin = 'JOIN context_aug ca ON f.context_id = ca.context_id'
            orderBy = 'a.accepted_timestamp DESC, a.accession_id DESC, abs(ca.calendar_period_size_diff_percentage), abs(ca.calendar_end_offset), f.fact_id DESC'
        
        updateFacts = []
        for hashString, factIds in factsByHash.items():
            #get facts to update
            hashQuery = '''
                SELECT f.fact_id, {indexName} as hash_index
                FROM accession a
                JOIN fact f
                  ON a.accession_id = f.accession_id
                {contextAugJoin}
                WHERE f.{hashName} = decode('{hash}', 'hex')
                ORDER BY {orderBy};
                '''.format(indexName=indexName, contextAugJoin=contextAugJoin, hashName=hashName, hash=hashlib.sha224(hashString.encode()).hexdigest(), orderBy=orderBy)
            results = self.execute(hashQuery)
            
            new_ultimus = 1
            for row in results:
                if row[1] != new_ultimus:
                    updateFacts.append((row[0], new_ultimus))
#                     #update the values for fact_aug
#                     if row[0] in self.factsForFactAug:
#                         self.factsForFactAug[row[0]][indexName] = new_ultimus
                new_ultimus += 1
        
        self.updateTable('fact',('fact_id', indexName), updateFacts)
        #self.updateTable('fact_aug',('fact_id', indexName), updateFacts)
    
    def isExtendedFact(self, fact):
        '''
        This funciton determines if the fact has an extended component (primary or dimension or member).
        '''
        
        primary_extended = not self.namespaceId.get(fact.qname.namespaceURI).get("isBase")
        dimension_extended = (any(not self.namespaceId.get(fact.context.qnameDims[dim].dimensionQname.namespaceURI).get("isBase") or                                  
                                  not (
                                       self.namespaceId.get(fact.context.qnameDims[dim].memberQname.namespaceURI).get("isBase") if fact.context.qnameDims[dim].isExplicit 
                                       else 
                                       self.namespaceId.get(fact.context.qnameDims[dim].typedMember.qname.namespaceURI).get("isBase")
                                       )
                                  for dim in fact.context.qnameDims.keys()
                              ))
        
        return primary_extended or dimension_extended
        
    # facts
    def insertFactSet(self, modelFacts, tupleFactId):
        insertForFact = dict()
        
        factsByXMLId = dict()
        for fact in modelFacts:
            calendarHashString = self.hashFactCalendar(fact)
            calendarHash = hashlib.sha224(calendarHashString.encode()).digest() if calendarHashString is not None else None
            factHashString = self.hashFact(fact)
            
            factXMLId = elementFragmentIdentifier(fact)
            factsByXMLId[factXMLId] = fact
            
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
            
            insertForFact[factXMLId] = {'accession_id': self.accessionId,
                 'tuple_fact_id': tupleFactId,
                 'context_id': self.cntxId.get((self.accessionId,fact.contextID)),
                 'unit_id': self.unitId.get((self.accessionId,fact.unitID)),
                 'element_id': self.conceptElementId(fact.concept),
                 'effective_value': effectiveValue,
                 'fact_value': factValue,
                 'xml_id': factXMLId,
                 'precision_value': fact.xAttributes['precision'].xValue if ('precision' in fact.xAttributes and isinstance(fact.xAttributes['precision'].xValue,int)) else None,
                 'decimals_value': fact.xAttributes['decimals'].xValue if ('decimals' in fact.xAttributes and isinstance(fact.xAttributes['decimals'].xValue,int)) else None,
                 'is_precision_infinity': 'precision' in fact.xAttributes and fact.xAttributes['precision'].xValue == 'INF',
                 'is_decimals_infinity': 'decimals' in fact.xAttributes and fact.xAttributes['decimals'].xValue == 'INF',
                 'uom': self.unitString.get((self.accessionId,fact.unitID)),
                 'fiscal_year': self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_year'],
                 'fiscal_period': self.cntxInfo.get((self.accessionId,fact.contextID))['fiscal_period'],
                 'fact_hash': hashlib.sha224(factHashString.encode()).digest(),
                 'fact_hash_string': factHashString,
                 'calendar_year': self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_year'],
                 'calendar_period': self.cntxInfo.get((self.accessionId,fact.contextID))['calendar_period'],
                 'calendar_hash': calendarHash,
                 'calendar_hash_string': calendarHashString,
                 'is_extended': self.isExtendedFact(fact)
                 }

        table = self.getTable('fact', 'fact_id', 
                              ('accession_id', 'tuple_fact_id', 'context_id', 'unit_id', 'element_id', 'effective_value', 'fact_value', 
                               'xml_id', 'precision_value', 'decimals_value', 
                               'is_precision_infinity', 'is_decimals_infinity','uom', 
                               'fiscal_year', 'fiscal_period', 'fact_hash',
                               'calendar_year', 'calendar_period', 'calendar_hash', 
                               'is_extended'), 
                              ('accession_id', 'xml_id', 'uom', 'is_extended'),
                              tuple((f['accession_id'], f['tuple_fact_id'], f['context_id'], f['unit_id'], f['element_id'], f['effective_value'], f['fact_value'], 
                               f['xml_id'], f['precision_value'], f['decimals_value'], 
                               f['is_precision_infinity'], f['is_decimals_infinity'], f['uom'], 
                               f['fiscal_year'], f['fiscal_period'], f['fact_hash'],
                               f['calendar_year'], f['calendar_period'], f['calendar_hash'], 
                               f['is_extended'])
                              for f in insertForFact.values()))

        #factId = dict()
        self.factsByHashString = collections.defaultdict(list)
        self.factsByCalendarHashString = collections.defaultdict(list)
        #self.factsForFactAug = dict()
        for id, _accsId, xmlId, uom, isExtended in table:
            #put the database id of the fact on the ModelFact object
            factsByXMLId[xmlId].dbFactId = id
#             self.factsForFactAug[id] = {'fact_hash': hashlib.sha224(insertForFact[xmlId]['fact_hash_string'].encode()).digest(),
#                                         'calendar_hash': hashlib.sha224(insertForFact[xmlId]['calendar_hash_string'].encode()).digest() if insertForFact[xmlId]['calendar_hash_string'] is not None else None,
#                                         'uom': uom,
#                                         'is_extended': isExtended,
#                                         'ultimus_index': None,
#                                         'calendar_ultimus_index': None}
            self.factsByHashString[insertForFact[xmlId]['fact_hash_string']].append(id)
            if insertForFact[xmlId]['calendar_hash_string'] is not None:
                self.factsByCalendarHashString[insertForFact[xmlId]['calendar_hash_string']].append(id)            
  
    def insertFactAug(self):
        self.getTable('fact_aug', 'fact_id',
                      ('fact_id', 'fact_hash', 'ultimus_index', 'calendar_hash', 'calendar_ultimus_index', 'uom', 'is_extended'),
                      ('fact_id',),
                      tuple((factId, factCols['fact_hash'], factCols['ultimus_index'], factCols['calendar_hash'], factCols['calendar_ultimus_index'], factCols['uom'], factCols['is_extended'])
                            for factId, factCols in self.factsForFactAug.items()),
                      returnMatches=False)

    def updateAccessionStats(self):
         
        #recalculate the restatement id for all accessions for the entity.
        query = '''UPDATE accession ua
                        SET restatement_index = rn
                        FROM (SELECT row_number() over(w) AS rn, entity_id, accepted_timestamp, period_end, accession_id
                              FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end
                                FROM accession
                                JOIN (SELECT f.accession_id, max(c.period_end) period_end
                                      FROM fact f
                                      JOIN element e
                                        ON f.element_id = e.element_id
                                      JOIN qname q
                                        ON e.qname_id = q.qname_id
                                      JOIN context c
                                        ON f.context_id = c.context_id
                                      JOIN accession a
                                        ON f.accession_id = a.accession_id
                                      WHERE q.namespace like '%%%%/dei/%%%%'
                                    AND q.local_name = 'DocumentPeriodEndDate'
                                    AND a.entity_id = %s
                                  GROUP BY f.accession_id) accession_period_end
                                  ON accession.accession_id = accession_period_end.accession_id
                                WHERE accession.entity_id = %s) accession_list
                
                        WINDOW w AS (partition BY entity_id, period_end ORDER BY accepted_timestamp DESC)) AS x
                        WHERE ua.accession_id = x.accession_id
                          AND coalesce(restatement_index,0) <> rn''' % (self.entityId, self.entityId)
        self.execute(query, close=False, fetch=False)
        
        #recalculate the period index for all accessions for the entity
        self.execute('''UPDATE accession ua
                        SET period_index = rn
                           ,is_most_current = CASE WHEN rn = 1 THEN true ELSE false END
                        FROM (SELECT row_number() over(w) AS rn, entity_id, accepted_timestamp, period_end, accession_id, restatement_index
                              FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end, restatement_index
                                FROM accession
                                JOIN (SELECT f.accession_id, max(c.period_end) period_end
                                      FROM fact f
                                      JOIN element e
                                        ON f.element_id = e.element_id
                                      JOIN qname q
                                        ON e.qname_id = q.qname_id
                                      JOIN context c
                                        ON f.context_id = c.context_id
                                      JOIN accession a
                                        ON f.accession_id = a.accession_id
                                      WHERE q.namespace like '%%%%/dei/%%%%'
                                    AND q.local_name = 'DocumentPeriodEndDate'
                                    AND a.entity_id = %s
                                  GROUP BY f.accession_id) accession_period_end
                                  ON accession.accession_id = accession_period_end.accession_id
                                WHERE accession.entity_id = %s) accession_list
                
                        WINDOW w AS (partition BY entity_id ORDER BY period_end DESC, restatement_index ASC)) AS x
                        WHERE ua.accession_id = x.accession_id;
                        ''' % (self.entityId, self.entityId), close=False, fetch=False)
    

         
         