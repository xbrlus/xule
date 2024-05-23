"""
Danish Business Authority source
"""
import json

def UOMString(dbLoader, unit):
    numerator = '*'.join(x.localName for x in unit.measures[0])
    denominator = '*'.join(x.localName for x in unit.measures[1])

    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator

def identifyEntityAndFilingInfo(dbLoader):
    info = dict()

    # Entity Name (Japanese)
    _filingProperty(dbLoader, info, 'entityName', 'http://xbrl.dcca.dk/gsd', 'NameOfReportingEntity')

    return info

def _filingProperty(dbLoader, info, key, partialNS, conceptName):
    """Get a piece of filing info from the model and store in the supplied dictionary."""

    infoValue = dbLoader.getSimpleFactByQname(partialNS, conceptName)
    if infoValue is not None:
        info[key] = infoValue

def reportProperties(dbLoader):
    info = dict()

    _filingProperty(dbLoader, info, 'ReportingPeriodStartDate', 'http://xbrl.dcca.dk/gsd', 'ReportingPeriodStartDate')
    _filingProperty(dbLoader, info, 'ReportingPeriodEndDate', 'http://xbrl.dcca.dk/gsd', 'ReportingPeriodEndDate')
    _filingProperty(dbLoader, info, 'NameOfReportingEntity', 'http://xbrl.dcca.dk/gsd', 'NameOfReportingEntity')
    _filingProperty(dbLoader, info, 'AddressOfReportingEntityStreetName', 'http://xbrl.dcca.dk/gsd', 'AddressOfReportingEntityStreetName')
    _filingProperty(dbLoader, info, 'AddressOfReportingEntityStreetBuildingIdentifier', 'http://xbrl.dcca.dk/gsd', 'AddressOfReportingEntityStreetBuildingIdentifier')
    _filingProperty(dbLoader, info, 'AddressOfReportingEntityPostCodeIdentifier', 'http://xbrl.dcca.dk/gsd', 'AddressOfReportingEntityPostCodeIdentifier')
    _filingProperty(dbLoader, info, 'AddressOfReportingEntityDistrictName', 'http://xbrl.dcca.dk/gsd', 'AddressOfReportingEntityDistrictName')
    _filingProperty(dbLoader, info, 'AddressOfReportingEntityCountry', 'http://xbrl.dcca.dk/gsd', 'AddressOfReportingEntityCountry')
    _filingProperty(dbLoader, info, 'DateOfFoundationOfReportingEntity', 'http://xbrl.dcca.dk/gsd', 'DateOfFoundationOfReportingEntity')
    _filingProperty(dbLoader, info, 'TelephoneNumberOfReportingEntity', 'http://xbrl.dcca.dk/gsd', 'TelephoneNumberOfReportingEntity')
    _filingProperty(dbLoader, info, 'HomepageOfReportingEntity', 'http://xbrl.dcca.dk/gsd', 'HomepageOfReportingEntity')
    _filingProperty(dbLoader, info, 'RegisteredOfficeOfReportingEntity', 'http://xbrl.dcca.dk/gsd', 'RegisteredOfficeOfReportingEntity')
    _filingProperty(dbLoader, info, 'NameAndSurnameOfChairmanOfGeneralMeeting', 'http://xbrl.dcca.dk/gsd', 'NameAndSurnameOfChairmanOfGeneralMeeting')
    _filingProperty(dbLoader, info, 'DateOfGeneralMeeting', 'http://xbrl.dcca.dk/gsd', 'DateOfGeneralMeeting')

    return json.dumps(info)

__sourceInfo__ = {
                  "name": "SEC US GAAP Corporate Issue Filings",
                  "calculateFiscalPeriod" : True,
                  "overrideFunctions" : {
                      "UOMString" : UOMString,
                      "UOMHash" : UOMString, #note the hash and the string form of the unit of measure are the same
                      "identifyEntityAndFilingingInfo": identifyEntityAndFilingInfo,
                      "reportProperties": reportProperties,
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