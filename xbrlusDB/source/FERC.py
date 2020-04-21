"""
Source definitions for SEC US GAAP filings.
"""
from arelle import FileSource
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.plugin.xbrlusDB.SqlDb import XDBException
import datetime  
import json
import os
from lxml import etree
import urllib.parse
import re

def UOMString(dbLoader, unit):
    numerator = '*'.join(x.localName for x in unit.measures[0])
    denominator = '*'.join(x.localName for x in unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator

def conceptHash(dbLoader, elementQname):
    return elementQname.localName

def FERCProperties(dbLoader):

    return json.dumps({'cid': dbLoader.getSimpleFactByQname(None, 'CompanyIdentifier'),
                       'submission_type': dbLoader.getSimpleFactByQname(None, 'SubmissionType'),
                       'form_type': dbLoader.getSimpleFactByQname(None, 'FormType'),
                       'report_year': dbLoader.getSimpleFactByQname(None, 'ReportYear'),
                       'report_period': dbLoader.getSimpleFactByQname(None, 'ReportPeriod'),
            })

def FERCFilingAndEntityInfo(dbLoader):
    
    info = dict()      
               
    info['entityName'] = dbLoader.getSimpleFactByQname(None, 'RespondentLegalName')
    return info

def FiscalYearEnd(dbLoader):
    # FERC filings are on calendar year. The Fiscal year end is alwasy 12/31

    return 12, 31

def factAccessLevel(dbLoader, modelFact):
    if fact_is_marked(modelFact, 'http://www.ferc.gov/arcrole/Confidential') :
        return 100
    else:
        return None

def fact_is_marked(modelFact, arcrole):
    '''Check if the fact is marked as redacted or confdential based on the special footnote relationships'''
    network = get_relationshipset(modelFact.modelXbrl, arcrole)
    rels = network.fromModelObject(modelFact)
    if len(rels) > 0:
        return True
    else:
        return False

def get_relationshipset(model_xbrl, arcrole, linkrole=None, linkqname=None, arcqname=None, includeProhibits=False):
    # This checks if the relationship set is already built. If not it will build it. The ModelRelationshipSet class
    # stores the relationship set in the model at .relationshipSets.
    relationship_key = (arcrole, linkrole, linkqname, arcqname, includeProhibits)
    return model_xbrl.relationshipSets[relationship_key] if relationship_key in model_xbrl.relationshipSets else ModelRelationshipSet(model_xbrl, *relationship_key)


_ADDITIONAL_SCHEDULES = ['13','21','23']
        
__sourceInfo__ = {
                  "name": "FERC Forms",
                  "doNotAllowUnnamedDTS": True,
                  "hasExtensions" : False,
                  "basePrefixSeparator" : "-",
                  "basePrefixPatterns" :
                    ((r'^http://xbrl.us/',r'[^\/]+$'),
                     (r'^http://xbrl.us/[^/]+/\d\d\d\d-\d\d-\d\d$',r'^http://xbrl.us/([^/]+)/\d\d\d\d-\d\d-\d\d$'),
                     (r'^http://xbrl.us/((dis)|(stm))/',r'^http://[^/]*/([^/]*)/([^/]*)/'),
                     
                     (r'^http://www.xbrl.org/',r'.*(xbrl).*/([^\/]+$)'),
                     (r'^http://www.xbrl.org/dtr/',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
                     (r'^http://www.xbrl.org/2009/role/negated',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
                     
                     (r'^http://xbrl.org/',r'.*(xbrl).*/([^\/]+$)'),
                     (r'^http://www.w3.org/',r'[^\/]+$'),
                     (r'^http://ici.org/',None),
                     
                     (r'^http://fasb.org/',r'^http://[^/]*/([^/]*)/'),
                     (r'^http://fasb.org/srt/',"'us-gaap'"), # srt concepts where originally us-gaap
                     (r'^http://fasb.org/((dis)|(stm))/',r'^http://[^/]*/([^/]*)/([^/]*)/'),
                     
                     (r'^http://xbrl.sec.gov/',r'^http://[^/]*/([^/]*)/'),
                     
                     (r'^http://xbrl.ifrs.org/',r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
                     
                     (r'^https?://[^/]*ferc.gov/.*/roles/',r'.*(ferc).*/(roles)/([^\\/]+)'),
                     (r'^https?://[^/]*ferc.gov/',r'.*(ferc).*/([^\/]+$)'), # Takes the text after the last slash

                     ),                  
                  "overrideFunctions" : {
                      "UOMString" : UOMString,
                      "UOMHash" : UOMString, #note the hash and the string form of the unit of measure are the same
                      "conceptQnameHash": conceptHash,
                      "reportProperties" : FERCProperties,
                      #"postLoad" : SECCreateAccessionRecord,
                      "identifyEntityAndFilingingInfo" : FERCFilingAndEntityInfo,
                      "identifyFiscalYearEnd" : FiscalYearEnd,
                      "getAccessLevelForFact" : factAccessLevel,
                  },

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

