"""
default source
"""

def excludeReport(dbLoader):
    return False

def UOMString(dbLoader, unit):
    numerator = '*'.join(x.clarkNotation for x in unit.measures[0])
    denominator = '*'.join(x.clarkNotation for x in unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator
        
def SECConceptHash(dbLoader, elementQname):
    return elementQname.clarkNotation        

__sourceInfo__ = {
                  "name": "SEC US GAAP Corporate Issue Filings",
                  "calculateFiscalPeriod" : True,
                  "overrideFunctions" : {
                      "excludeReport" : excludeReport,
                      "UOMString" : UOMString,
                      "UOMHash" : UOMString, #note the hash and the string form of the unit of measure are the same
                      "ConceptQnameHash" : SECConceptHash
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
UOMString(dbLoader, unit) - string - Returns a string version of the unit.
hashUOM(dbLoader, unit) - string - Returns the hash version of the unit.

'''