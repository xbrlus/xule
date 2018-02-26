"""
Source definitions for SEC US GAAP filings.
"""
from ..SqlDb import XPDBException
import datetime  
import json
import os
from lxml import etree
import urllib.parse
import re

def SECExcludeReport(dbLoader):
    # don't want to process certain form types (if it is an sec filing).
    excludedForms = ['497', '485BPOS', 'N-CSR', 'N-CSRS', 'N-Q', 'N-CSR/A', 'N-CESRS/A', 'N-Q/A', 'SDR/A']
    if dbLoader.sourceData['documentType'] is not None:
        if dbLoader.sourceData['documentType'].strip() in excludedForms:
            dbLoader.modelXbrl.info("info", _("%(now)s - Skipped filing due to excluded form type:  %(formType)s"),
                formType=dbLoader.sourceData['documentType'],
                now=str(datetime.datetime.today()))
            return True
    
    return False

def SECUOMString(dbLoader, unit):
    numerator = '*'.join(x.localName for x in unit.measures[0])
    denominator = '*'.join(x.localName for x in unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator

def SECConceptHash(dbLoader, elementQname):
    if elementQname.namespaceURI in dbLoader.baseNamespaces.keys():
        if dbLoader.baseNamespaces[elementQname.namespaceURI] is None:
            raise XPDBException("xpgDB:UnknownBaseNamespace",
                            _("The namespace %(ns)s is a base namespace, but the taxonomy family cannot be determined. Table 'base_namespace' needs a prefix expression for this namespace."),
                            ns=elementQname.namespaceURI) 
        else:
            return 'b' + dbLoader.baseNamespaces[elementQname.namespaceURI] + ':' + elementQname.localName
    else:
        return 'e' + dbLoader.hashEntity() + ':' + elementQname.localName

def SECProperties(dbLoader):
    
    indexHtmlFile = dbLoader.sourceData.get("htmlFilingInfoFile", None)
    zipFile = indexHtmlFile.replace('-index.htm', '-xbrl.zip') if indexHtmlFile is not None else None
    indexHtml = dbLoader.mapDocumentUri(dbLoader.alternativeDoc) if hasattr(dbLoader,'alternativeDoc') else None
    
    return json.dumps({'zip_url': zipFile,
            'sec_html_url': indexHtmlFile,
            'document_type': dbLoader.sourceData.get("documentType", None),
            'business_phone': dbLoader.sourceData.get("entityPhone", None),
            'business_address': dbLoader.sourceData.get("entityAddress", None),
            'percent_extended': None,
            'state_of_incorporation': dbLoader.sourceData.get("stateOfIncorporation", None),
            'filing_accession_number': dbLoader.accessionNumber,
            'internal_revenue_service_number': dbLoader.sourceData.get("irsNumber", -1),
            'standard_industrial_classification': dbLoader.sourceData.get("sic", -1),
            'filing_date': dbLoader.sourceData.get("filingDate", dbLoader.acceptanceDate)
            })
    
def SECCreateAccessionRecord(dbLoader):
    
    query = '''
        INSERT INTO accession (accession_id
                              ,accepted_timestamp
                              ,is_most_current
                              ,filing_date
                              ,entity_id
                              ,entity_name
                              ,creation_software
                              ,standard_industrial_classification
                              ,sec_html_url
                              ,entry_url
                              ,filing_accession_number
                              ,internal_revenue_service_number
                              ,business_address
                              ,business_phone
                              ,document_type
                              ,state_of_incorporation
                              ,entry_type
                              ,entry_document_id
                              ,alternative_document_id
                              ,zip_url
                              ,reporting_period_end_date
                              ,is_complete
                              ,source_id
                              ,restatement_index
                              ,period_index
                              )
        SELECT report_id
              ,accepted_timestamp
              ,is_most_current
              ,(properties->>'filing_date')::timestamp
              ,entity_id
              ,entity_name
              ,creation_software
              ,(properties->>'standard_industrial_classification')::integer
              ,properties->>'sec_html_url'
              ,entry_url
              ,source_report_identifier
              ,(properties->>'internal_revenue_service_number')::integer
              ,properties->>'business_address'
              ,properties->>'business_phone'
              ,properties->>'document_type'
              ,properties->>'state_of_incorporation'
              ,entry_type
              ,entry_document_id
              ,alternative_document_id
              ,properties->>'zip_url'
              ,reporting_period_end_date
              ,True
              ,source_id
              ,restatement_index
              ,period_index
        FROM report
        WHERE report_id = %s
        ''' % dbLoader.accessionId
    
    dbLoader.execute(query, close=False, fetch=False)

    query = "INSERT INTO accession_timestamp VALUES ({})".format(dbLoader.accessionId)
    dbLoader.execute(query, close=False, fetch=False)

#         table = self.getTable('accession', 'accession_id', 
#                               ('accession_id', 'accepted_timestamp', 'is_most_current', 'filing_date','entity_id', 
#                                'entity_name', 'creation_software', 'standard_industrial_classification', 
#                                'sec_html_url', 'entry_url', 'filing_accession_number', 'internal_revenue_service_number',
#                                'business_address', 'business_phone', 'document_type', 'state_of_incorporation','entry_type',
#                                'entry_document_id', 'alternative_document_id', 'zip_url', 'reporting_period_end_date', 'is_complete', 'source_id'), 
#                               ('filing_accession_number',), 
#                               ((self.accessionId,
#                                 self.accepted_timestamp,
#                                 True,
#                                 getattr(self, "filingDate", datetime.datetime(datetime.MAXYEAR, 12, 31)),  # NOT NULL
#                                 self.entityId,  # NOT NULL
#                                 self.entityName,
#                                 creationSoftware,
#                                 getattr(self, "sic", -1),  # NOT NULL
#                                 indexHtmlFile,
#                                 getattr(self, "entryUrl", None),
#                                 self.accessionNumber,
#                                 getattr(self, "irsNumber", -1),
#                                 getattr(self, "entityAddress", None),
#                                 getattr(self, "entityPhone", None),
#                                 getattr(self, "documentType", None),
#                                 getattr(self, "stateOfIncorporation", None),
#                                 entryType,
#                                 self.documentIds[self.cleanDocumentUri(self.modelXbrl.modelDocument)],
#                                 self.documentIds[indexHtml] if indexHtml is not None else None,
#                                 zipFile,
#                                 self.period,
#                                 True,
#                                 self.sourceId
#                                 ),),
#                               checkIfExisting=True,
#                               returnExistenceStatus=True)
#         for id, filing_accession_number, existenceStatus in table:
#             self.accessionId = id
#             self.accessionPreviouslyInDB = existenceStatus            
#             break
#         
#         #add accession timestampe record
#         self.execute("INSERT INTO accession_timestamp (accession_id) VALUES ({})".format(self.accessionId), close=False, fetch=False)
#      
#     #recalculate the restatement id for all accessions for the entity.
#     query = '''UPDATE accession ua
#                     SET restatement_index = rn
#                     FROM (SELECT row_number() over(w) AS rn, entity_id, accepted_timestamp, period_end, accession_id
#                           FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end
#                             FROM accession
#                             JOIN (SELECT f.accession_id, max(c.period_end) period_end
#                                   FROM fact f
#                                   JOIN element e
#                                     ON f.element_id = e.element_id
#                                   JOIN qname q
#                                     ON e.qname_id = q.qname_id
#                                   JOIN context c
#                                     ON f.context_id = c.context_id
#                                   JOIN accession a
#                                     ON f.accession_id = a.accession_id
#                                   WHERE q.namespace like '%%%%/dei/%%%%'
#                                 AND q.local_name = 'DocumentPeriodEndDate'
#                                 AND a.entity_id = %s
#                               GROUP BY f.accession_id) accession_period_end
#                               ON accession.accession_id = accession_period_end.accession_id
#                             WHERE accession.entity_id = %s) accession_list
#             
#                     WINDOW w AS (partition BY entity_id, period_end ORDER BY accepted_timestamp DESC)) AS x
#                     WHERE ua.accession_id = x.accession_id
#                       AND coalesce(restatement_index,0) <> rn
#                     RETURNING x.accession_id, x.rn''' % (dbLoader.entityId, dbLoader.entityId)
#                     
#     dbLoader.execute(query, close=False)
#     
#     #recalculate the period index for all accessions for the entity
#     query = '''UPDATE accession ua
#                     SET period_index = rn
#                        ,is_most_current = CASE WHEN rn = 1 THEN true ELSE false END
#                     FROM (SELECT row_number() over(w) AS rn, entity_id, accepted_timestamp, period_end, accession_id, restatement_index
#                           FROM (SELECT entity_id, accepted_timestamp, accession.accession_id, period_end, restatement_index
#                             FROM accession
#                             JOIN (SELECT f.accession_id, max(c.period_end) period_end
#                                   FROM fact f
#                                   JOIN element e
#                                     ON f.element_id = e.element_id
#                                   JOIN qname q
#                                     ON e.qname_id = q.qname_id
#                                   JOIN context c
#                                     ON f.context_id = c.context_id
#                                   JOIN accession a
#                                     ON f.accession_id = a.accession_id
#                                   WHERE q.namespace like '%%%%/dei/%%%%'
#                                 AND q.local_name = 'DocumentPeriodEndDate'
#                                 AND a.entity_id = %s
#                               GROUP BY f.accession_id) accession_period_end
#                               ON accession.accession_id = accession_period_end.accession_id
#                             WHERE accession.entity_id = %s) accession_list
#             
#                     WINDOW w AS (partition BY entity_id ORDER BY period_end DESC, restatement_index ASC)) AS x
#                     WHERE ua.accession_id = x.accession_id
#                     RETURNING x.accession_id, x.rn''' % (dbLoader.entityId, dbLoader.entityId)
#                     
#     dbLoader.execute(query, close=False)
#     
#     updateList = dict()
#     for id, index in restatementResult:
#         updateList[id] = (index,)
#     

def SECFilingAndEntityInfo(dbLoader):
    
    info = dict()      
               
    info['entityName'] = dbLoader.getSimpleFactByQname('/dei/','EntityRegistrantName')
    
    info['entityIdentifier'] = dbLoader.getSimpleFactByQname('/dei/','EntityCentralIndexKey')
    if info['entityIdentifier'] is not None:
        info['entityScheme'] = 'http://www.sec.gov/CIK'
    info['documentType'] = dbLoader.getSimpleFactByQname('/dei','DocumentType')
    info['period'] = dbLoader.getSimpleFactByQname('/dei','DocumentPeriodEndDate')
    info['entryUrl'] = None
    
    indexFile = None
    rssItem = None    
    if dbLoader.supportFiles is not None:
        for fileName in dbLoader.supportFiles:
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
            if info['entityName'] is None:
                info['entityName'] = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:companyName/text()', rssNS)
            if info['entityIdentifier'] is None:
                info['entityIdentifier'] = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:cikNumber', rssNS)
                info['entityScheme'] = 'http://www.sec.gov/CIK'
            rssDocumentType = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:formType', rssNS)
            if rssDocumentType is not None and rssDocumentType != info['documentType']:
                info['documentType'] = rssDocumentType
            
            if info['period'] is None:
                reportingPeriod = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:period', rssNS)
                info['period'] = reportingPeriod[0:4] + "-" + reportingPeriod[4:6] + "-" + reportingPeriod[6:8]

            info['accessionNumber'] = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:accessionNumber', rssNS)
            info['sic'] = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:assignedSic', rssNS, -1)
            
            rssDate = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:acceptanceDatetime', rssNS)
            if rssDate is None:
                info['acceptanceDate'] = None
            else:
                info['acceptanceDate'] = rssDate[0:4] + '-' + rssDate[4:6] + '-' + rssDate[6:8] + ' ' + rssDate[8:10] + ':' + rssDate[10:12] + ':' + rssDate[14:16]
            
            info['filingDate'] = xmlFind(rssItem, 'edgar:xbrlFiling/edgar:filingDate', rssNS)
            
            info['htmlFilingInfoFile'] = xmlFind(rssItem, 'link')
            info['alternativeDoc'] = None
            info['additionalDocs'] = list()
            for fileNode in rssItem.findall('edgar:xbrlFiling/edgar:xbrlFiles/edgar:xbrlFile', rssNS):
#                 if fileNode.get('{http://www.sec.gov/Archives/edgar}type') == 'EX-101.INS':
#                     info['entryUrl'] = fileNode.get('{http://www.sec.gov/Archives/edgar}url')
#                     break
                if os.path.splitext(fileNode.get('{http://www.sec.gov/Archives/edgar}url'))[1] != '.pdf':
                    docType= fileNode.get('{http://www.sec.gov/Archives/edgar}type')
                    if docType == info['documentType']:
                        info['alternativeDoc'] = fileNode.get('{http://www.sec.gov/Archives/edgar}url')
                    #Load certain schedules
                    if re.match(r'ex-({})($|[^\d])'.format('|'.join(_ADDITIONAL_SCHEDULES)),docType.strip(),re.I) is not None:
                        info['additionalDocs'].append((fileNode.get('{http://www.sec.gov/Archives/edgar}url'), docType))
                        
            if info['alternativeDoc'] is None:
                raise XPDBException("xpgDB:cannotFindTextFiling",
                                _("Cannot identify the htm or text version of the filing. This is normally the document with the same type as the filing type.")) 
#             #Let the entry url default 
#             if info['entryUrl'] is None:
#                 info['entryUrl'] = info['alternativeDoc']
            
            if info['htmlFilingInfoFile'] is None:
                raise XPDBException("xpgDB:missingSupportFiles",
                                _("Cannot acquire filing details. Htm index file cannot be determined from the rss item."))
            indexFile = reverseMapDocumentUri(dbLoader, info['htmlFilingInfoFile'])
            filingAttributes = extractFilingDetailsFromIndex(dbLoader, indexFile, info)
            for attrName, attrValue in filingAttributes.items():
                #only populate if the value hasn't already been acquired from the rss item
                if attrName not in info:
                    info[attrName] = attrValue
        else:
            #acquire filing attributes from html index file
            if indexFile is None:
                raise XPDBException("xpgDB:missingSupportFiles",
                                _("Cannot acquire filing details. No htm index file or rss item supplied."))
            
            filingAttributes = extractFilingDetailsFromIndex(dbLoader, indexFile, info)
            #values found in the html index file override any defaults already set up.
            for attrName, attrValue in filingAttributes.items():
                info[attrName] = attrValue
        
    return info
    
def extractFilingDetailsFromIndex(dbLoader, indexFileName, info):
    
    with dbLoader.getFile(indexFileName) as indexFileHandler:
        #indexFileHandler = dbLoader.getFile(indexFileName)
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
                elif 'type:' in x.lower():
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
            
        if identInfoDict.get('entityIdentifier') == info['entityIdentifier']:
            break
    #get accession number
    secNumNodes = htmlTree.xpath("//div[@id='secNum']")
    secNumNode = secNumNodes[0] if len(secNumNodes) > 0 else None
    if secNumNode is not None:
        identInfoDict['accessionNumber'] = (getNodeText(secNumNode))[-1].strip()
        
    #filing date and accepted date
    headingDivs = htmlTree.xpath("//div[@class='infoHead']")
    for headingDiv in headingDivs:
        if 'filing date' == headingDiv.text.lower():
            identInfoDict['filingDate'] = headingDiv.getnext().text.strip()
        if 'accepted' in headingDiv.text.lower():
            identInfoDict['acceptanceDate'] = headingDiv.getnext().text.strip()
        if 'period of report' in headingDiv.text.lower():
            identInfoDict['period'] = headingDiv.getnext().text.strip()

    identInfoDict['htmlFilingInfoFile'] = dbLoader.mapDocumentUri(indexFileName)
    #identInfoDict['entryUrl'] = dbLoader.cleanDocumentUri(dbLoader.modelXbrl.modelDocument) # let it default

    #get HTML version of the filing
    identInfoDict['alternativeDoc'] = None
    identInfoDict['additionalDocs'] = list()
    docType = identInfoDict.get('documentType')
    if docType is not None:
        for fileTable in htmlTree.xpath("//table[@class='tableFile']"):
            for tr in fileTable:
                if tr[3].tag.lower() == 'td' and os.path.splitext(tr[2][0].text)[1] != '.pdf':
                    if tr[3].text == docType:
                        href = tr[2][0].get('href')
                        #if os.path.splitext(href)[1] == '.htm': #this could be a text file. Removing this constraint
                        #found the file
                        if dbLoader.isUrl(os.path.dirname(indexFileName)):
                            identInfoDict['alternativeDoc'] = urllib.parse.urljoin(indexFileName, tr[2][0].text)
                        else:
                            identInfoDict['alternativeDoc'] = os.path.join(os.path.dirname(indexFileName), tr[2][0].text)
    
                    # get additional documents
                    if re.match(r'ex-({})($|[^\d])'.format('|'.join(_ADDITIONAL_SCHEDULES)),tr[3].text.strip(),re.I) is not None:
                        href = tr[2][0].get('href')
                        if dbLoader.isUrl(os.path.dirname(indexFileName)):
                            identInfoDict['additionalDocs'].append((urllib.parse.urljoin(indexFileName, tr[2][0].text), tr[3].text))
                        else:
                            identInfoDict['additionalDocs'].append((os.path.join(os.path.dirname(indexFileName), tr[2][0].text), tr[3].text))                            

    if identInfoDict['alternativeDoc'] is None:
        raise XPDBException("xpgDB:cannotFindTextFiling",
                        _("Cannot identify the htm or text version of the filing. This is normally the document with the same type as the filing type.")) 

    return identInfoDict

def SECFiscalYearEnd(dbLoader):
    #get from the CurrentFiscalYearEndDate in the filing
    fiscalYearMonthDayEnd = dbLoader.getSimpleFactByQname('/dei/','CurrentFiscalYearEndDate')

    if fiscalYearMonthDayEnd is None and dbLoader.sourceData.get("filingDate", None) is not None:
        #get from previous filings
        results = dbLoader.execute(
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
        ''', params=(dbLoader.entityId, dbLoader.sourceData['filingDate'], dbLoader.sourceData['filingDate']))
        if len(results) > 0:
            fiscalYearMonthDayEnd = results[0][0]
            
    fiscalYearMonthEnd = None
    fiscalYearDayEnd = None
    if fiscalYearMonthDayEnd is not None:
        if fiscalYearMonthDayEnd.startswith("--"): 
            fiscalYearMonthDayEndList = fiscalYearMonthDayEnd.split('-')
            if len(fiscalYearMonthDayEndList) == 4:
                fiscalYearMonthEnd = int(fiscalYearMonthDayEndList[2])
                fiscalYearDayEnd = int(fiscalYearMonthDayEndList[3])
        else:
            fiscalYearMonthEnd = int(dbLoader.fiscalYearMonthDayEnd[:2])
            fiscalYearDayEnd = int(dbLoader.fiscalYearMonthDayEnd[2:])
    
    return fiscalYearMonthEnd, fiscalYearDayEnd
    
def getNodeText(node):
    return [x for x in etree.ElementTextIterator(node)]
        
def xmlFind(root, path, namespaces=None, default=None):
    node = root.find(path, namespaces)
    if node is None:
        return default
    else:
        return node.text        
        
def reverseMapDocumentUri(dbLoader, documentUri):
    '''Map an official uri to cache location
    '''
    if dbLoader.documentCacheLocation is not None:
        uriParts = urllib.parse.urlparse(documentUri)
        if uriParts.scheme.startswith('http'):
            cacheFile = os.path.join(dbLoader.documentCacheLocation, uriParts.netloc, uriParts.path[1:] if uriParts.path[0] == '/' else uriParts.path)
            if os.path.isfile(cacheFile):
                return cacheFile
    #Could not map to the cache
    return documentUri

_ADDITIONAL_SCHEDULES = ['13','21','23']
        
__sourceInfo__ = {
                  "name": "SEC US GAAP Corporate Issue Filings",
                  "hasExtensions" : True,
                  "basePrefixPatterns" :
                    ((r'^http://xbrl.us/',None),
                     (r'^http://xbrl.us/[^/]+/\d\d\d\d-\d\d-\d\d$',r'^http://xbrl.us/([^/]+)/\d\d\d\d-\d\d-\d\d$'),
                     (r'^http://xbrl.us/((dis)|(stm))/',r'^http://[^/]*/([^/]*)/([^/]*)/'),
                     
                     (r'^http://www.xbrl.org/',None),
                     (r'^http://www.xbrl.org/dtr/',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
                     (r'^http://www.xbrl.org/2009/role/negated',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
                     
                     (r'^http://xbrl.org/',None),
                     (r'^http://www.w3.org/',None),
                     (r'^http://ici.org/',None),
                     
                     (r'^http://fasb.org/',r'^http://[^/]*/([^/]*)/'),
                     (r'^http://fasb.org/((dis)|(stm))/',r'^http://[^/]*/([^/]*)/([^/]*)/'),
                     
                     (r'^http://xbrl.sec.gov/',r'^http://[^/]*/([^/]*)/'),
                     
                     (r'^http://xbrl.ifrs.org/',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),

                     ),                  
                  "overrideFunctions" : {
                      "excludeReport" : SECExcludeReport,
                      "UOMString" : SECUOMString,
                      "UOMHash" : SECUOMString, #note the hash and the string form of the unit of measure are the same
                      "conceptQnameHash" : SECConceptHash,
                      "reportProperties" : SECProperties,
                      #"postLoad" : SECCreateAccessionRecord,
                      "identifyEntityAndFilingingInfo" : SECFilingAndEntityInfo,
                      "identifyFiscalYearEnd" : SECFiscalYearEnd
                  },
#                   "databaseInstall": 
# '''
# CREATE OR REPLACE FUNCTION delete_report_post_sec(in_report_id bigint, in_entity_id bigint) RETURNS void AS
# $$
# BEGIN
#     DELETE FROM accession WHERE accession_id = in_report_id;
# END
# $$ LANGUAGE plpgsql;
# '''
}

'''
Notes about the source module.
The source module overrides certain defaults in the loading process. The module contains a set of settings and override functions that direct 
special handling for the source. Each override function always takes the dbLoader object. This is the database connection/loader object. Specific 
functions may take additional arguments.

Settings:
name - string - A friendly name for the source module.
hasExtensions - boolenan - 
    When true, namespaces are identified as base namespaces based on the is_base in the namespace_source tables for existing
    namespaces and on the base_namespace table for new ones. All other namespaces are identified as extensions. 
    When false, all namespaces are treated as base namespaces.
basePrefix - string - when hasExtensions is false, all namespaces will be considered base. If a canonical prefix is not defined on the base namespace table, 
    the basePrefix will be used to derive a canonical namespace.

The __sourceInfo__ dictionary contains the list of settings and override functions. These key names cannot be changed. If a name is in the 
"overrideFunctions" then when the process calls the normal version of the function, the version in the source module will be used instead. Only
the functions that need to be overridden need to be included in the source module.

Override Functions:
excludeReport(dbLoader) - boolean - The return value identifies if the report should be skipped.
reportProperties(dbLoader) - 
UOMString(dbLoader, unit) - string - Returns a string version of the unit.
UOMHash(dbLoader, unit) - string - Returns the hash version of the unit.
conceptQnameHash(dbLoader, elementQname) - string - Returns the hash of an element name
fiscalPeriod(dbLoader, context) - string - Returns the fiscal period for the period in the context.
fiscalYear(dbLoader, context) - integer - Returns the fiscal year for the period in the context.
getEntityAndFilingInfo(dbLoader) - dictionary - Returns a dictionary of entity and filing information. The common keys for the dictionary are:
    'acceptanceDate', 'accessionNumber', 'entityName', 'entityIdentifier', 'entityScheme', 'entryUrl', 'alternativeDoc', 'alternativeDocname', 'period', 'sourceUriMap'
    Any additional keys will be stored in the sourceData attribute of the dbLoader.
'''

