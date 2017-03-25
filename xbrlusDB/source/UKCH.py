"""
Source definitions for SEC US GAAP filings.
"""
from ..SqlDb import XPDBException
import datetime  
import json
import os
from lxml import etree
import urllib.parse
from arelle.ModelDocument import Type

def UKCHUOMString(dbLoader, unit):
    numerator = '*'.join(x.localName for x in unit.measures[0])
    denominator = '*'.join(x.localName for x in unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator


def UKCHFilingAndEntityInfo(dbLoader):
    
    info = dict()      
    nsPattern = '/cd/.*business'
    info['entityName'] = dbLoader.getSimpleFactByQname(nsPattern, 'EntityCurrentLegalOrRegisteredName')
    
    info['entityIdentifier'] = dbLoader.getSimpleFactByQname(nsPattern, 'UKCompaniesHouseRegisteredNumber')
    info['period'] = dbLoader.getSimpleFactByQname(nsPattern,'EndDateForPeriodCoveredByReport')
    if info['entityIdentifier'] is None or info['period'] is None:
        raise XPDBException("xpgDB:missingReportInfo", 
                                    _("Cannot get the registered number or the period of the report."))
    info['accessionNumber'] = ','.join((info['entityIdentifier'], info['period']))
    
    fullFileName = dbLoader.options.entrypointFile
    baseFileName = os.path.basename(fullFileName)
    info['entryUrl'] = baseFileName
    
    if dbLoader.modelXbrl.modelDocument.type == Type.INLINEXBRL:
        info['alternativeDocName'] = baseFileName
        info['alternativeDoc'] = dbLoader.modelXbrl.modelDocument.uri

    return info

def UKCHFiscalYearEnd(dbLoader):
    #get from the CurrentFiscalYearEndDate in the filing
    nsPattern = '/cd/.*business'
    balanceSheetDate = dbLoader.getSimpleFactByQname(nsPattern,'BalanceSheetDate')
    if balanceSheetDate is None:
        fiscalYearMonthEnd = None
        fiscalYearDayEnd = None
    else:
        fiscalYearMonthEnd = int(balanceSheetDate.strip()[5:7])
        fiscalYearDayEnd = int(balanceSheetDate.strip()[8:10])

    return fiscalYearMonthEnd, fiscalYearDayEnd
    
        
__sourceInfo__ = {
                  "name": "UK Companies House filings",
                  "hashExtensions" : False,
                  "basePrefix" : "ukch-",
                  "basePrefixSeparator" : "-",
                  "basePrefixPatterns" :
                    ((r'^http://www.xbrl.org/uk/',r'^http://www\.xbrl\.org/([^/]+)/([^/]+)/([^/]+)/'),
                     (r'^http://xbrl.frc.org.uk/', r'^http://xbrl\.frc\.org\.(uk)/([^/]+)/[^/]+/(.*)')
                     ),
                  "overrideFunctions" : {
                      "UOMString" : UKCHUOMString,
                      "UOMHash" : UKCHUOMString, #note the hash and the string form of the unit of measure are the same
                      "identifyEntityAndFilingingInfo" : UKCHFilingAndEntityInfo,
                      "identifyFiscalYearEnd" : UKCHFiscalYearEnd
                  }
}

'''
Notes about the source module.
The source module overrides certain defaults in the loading process. The module contains a set of settings and override functions that direct 
special handling for the source. Each override function always takes the dbLoader object. This is the database connection/loader object. Specific 
functions may take additional arguments.

Settings:
name - string - A friendly name for the source module.
calculateFiscalPeriod - boolean - Indicates that fiscal period calculations should be done. This requires that the source can identify the
                                  fiscal year month and day end.

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
    'acceptanceDate', 'accessionNumber', 'entityName', 'entityIdentifier', 'entityScheme', 'entryUrl', 'htmlInstance', 'period'
    Any additional keys will be stored in the sourceData attribute of the dbLoader.
'''

