"""
Source definitions for Solare filings.
"""

__sourceInfo__ = {
                  "name": "Solar Taxonomy Filings"
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

