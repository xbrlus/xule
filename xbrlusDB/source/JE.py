"""
Japan EDINET source
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

def fiscalYearEnd(dbLoader):
    fiscalYearMonthDayEnd = dbLoader.getSimpleModelFactByQname('/jpdei/', 'CurrentFiscalYearEndDateDEI')
    if fiscalYearMonthDayEnd is not None:
        return fiscalYearMonthDayEnd.xValue.month, fiscalYearMonthDayEnd.xValue.day
    else:
        return None, None

def identifyEntityAndFilingInfo(dbLoader):
    info = dict()

    # Entity Name (Japanese)
    _filingProperty(dbLoader, info, 'entityName', '/jpcrp/', 'CompanyNameCoverPage')

    return info

def _filingProperty(dbLoader, info, key, partialNS, conceptName):
    """Get a piece of filing info from the model and store in the supplied dictionary."""

    infoValue = dbLoader.getSimpleFactByQname(partialNS, conceptName)
    if infoValue is not None:
        info[key] = infoValue

def reportProperties(dbLoader):
    info = dict()
    _filingProperty(dbLoader, info, 'entityNameJP', '/jpcrp/', 'CompanyNameCoverPage')
    _filingProperty(dbLoader, info, 'entityNameEN', '/jpcrp/', 'CompanyNameInEnglishCoverPage')
    _filingProperty(dbLoader, info, 'filingDate', '/jpcrp/', 'FilingDateCoverPage')
    _filingProperty(dbLoader, info, 'documentTitle', '/jpcrp/', 'DocumentTitleCoverPage')
    _filingProperty(dbLoader, info, 'clauseOfStipulation', '/jpcrp/', 'ClauseOfStipulationCoverPage')
    _filingProperty(dbLoader, info, 'placeOfFiling', '/jpcrp/', 'PlaceOfFilingCoverPage')
    _filingProperty(dbLoader, info, 'QuarterlyAccountingPeriod', '/jpcrp/', 'QuarterlyAccountingPeriodCoverPage')
    _filingProperty(dbLoader, info, 'titleAndNameOfRepresentative', '/jpcrp/', 'TitleAndNameOfRepresentativeCoverPage')
    _filingProperty(dbLoader, info, 'AddressOfRegisteredHeadquarter', '/jpcrp/', 'AddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'telephoneNumberOFRegisteredHeadquarter', '/jpcrp/',
                   'TelephoneNumberAddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'nameOfContactPersionAddressOfRegisteredHeadquarter', '/jpcrp/',
                    'NameOfContactPersonAddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'nearestPlaceOfContact', '/jpcrp/',
                    'NearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'telephoneNumberNeraestPlaceOfContact', '/jpcrp/',
                    'TelephoneNumberNearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'nameOfContactPersonNearestPlaceOfContact', '/jpcrp/',
                    'NameOfContactPersonNearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'EDINETCode', '/jpdei/', 'EDINETCodeDEI')
    _filingProperty(dbLoader, info, 'fundCode', '/jpdei/', 'FundCodeDEI')
    _filingProperty(dbLoader, info, 'securityCode', '/jpdei/', 'SecurityCodeDEI')
    _filingProperty(dbLoader, info, 'filerNameJP', '/jpdei/', 'FilerNameInJapaneseDEI')
    _filingProperty(dbLoader, info, 'filerNameEN', '/jpdei/', 'FilerNameInEnglishDEI')
    _filingProperty(dbLoader, info, 'fundNameJP', '/jpdei/', 'FundNameInJapaneseDEI')
    _filingProperty(dbLoader, info, 'fundNameEN', '/jpdei/', 'FundNameInEnglishDEI')
    _filingProperty(dbLoader, info, 'cabinetOfficeOrdinance', '/jpdei/', 'CabinetOfficeOrdinanceDEI')
    _filingProperty(dbLoader, info, 'documentType', '/jpdei/', 'DocumentTypeDEI')
    _filingProperty(dbLoader, info, 'accountingStandards', '/jpdei/', 'AccountingStandardsDEI')
    _filingProperty(dbLoader, info, 'whetherConsolidatedFinancialStaementsArePrepared', '/jpdei/', 'WhetherConsolidatedFinancialStatementsArePreparedDEI')
    _filingProperty(dbLoader, info, 'industryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulations', '/jpdei/', 'IndustryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI')
    _filingProperty(dbLoader, info, 'industryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulations', '/jpdei/', 'IndustryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI')
    _filingProperty(dbLoader, info, 'currentFiscalYearStartDate', '/jpdei/', 'CurrentFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'currentPeriodEndDate', '/jpdei/', 'CurrentPeriodEndDateDEI')
    _filingProperty(dbLoader, info, 'typeOfCurrentPeriod', '/jpdei/', 'TypeOfCurrentPeriodDEI')
    _filingProperty(dbLoader, info, 'currentFiscalYearEndDate', '/jpdei/', 'CurrentFiscalYearEndDateDEI')
    _filingProperty(dbLoader, info, 'previousFiscalYearStartDate', '/jpdei/', 'PreviousFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'ComparativePeriodEndDate', '/jpdei/', 'ComparativePeriodEndDateDEI')
    _filingProperty(dbLoader, info, 'previousFiscalYearEndDate', '/jpdei/', 'PreviousFiscalYearEndDateDEI')
    _filingProperty(dbLoader, info, 'nextFiscalYearStartDate', '/jpdei/', 'NextFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'endDateOfQuarterlyOrSemiAnnualPeriodOfNextFiscalYear', '/jpdei/', 'EndDateOfQuarterlyOrSemiAnnualPeriodOfNextFiscalYearDEI')
    _filingProperty(dbLoader, info, 'amendmentFlag', '/jpdei/', 'AmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'identificationOfDocumentSubjectToAmendment', '/jpdei/', 'IdentificationOfDocumentSubjectToAmendmentDEI')
    _filingProperty(dbLoader, info, 'reportAmendmentFlag', '/jpdei/', 'ReportAmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'XBRLAmendmentFlag', '/jpdei/', 'XBRLAmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'securityCode', '/jpdei/', 'SecurityCodeDEI')

    return json.dumps(info)

__sourceInfo__ = {
                  "name": "SEC US GAAP Corporate Issue Filings",
                  "calculateFiscalPeriod" : True,
                  "overrideFunctions" : {
                      "UOMString" : UOMString,
                      "UOMHash" : UOMString, #note the hash and the string form of the unit of measure are the same
                      "identifyFiscalYearEnd": fiscalYearEnd,
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