"""
Japan EDINET source
"""
import datetime
import json
import os


_document_control_number = None

def UOMString(dbLoader, unit):
    numerator = '*'.join(x.localName for x in unit.measures[0])
    denominator = '*'.join(x.localName for x in unit.measures[1])

    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator

def ConceptHash(dbLoader, elementQname):
    if elementQname.namespaceURI in dbLoader.baseNamespaces.keys():
        if dbLoader.baseNamespaces[elementQname.namespaceURI] is None:
            raise XPDBException("xpgDB:UnknownBaseNamespace",
                            _("The namespace %(ns)s is a base namespace, but the taxonomy family cannot be determined. Table 'base_namespace' needs a prefix expression for this namespace."),
                            ns=elementQname.namespaceURI)
        else:
            return 'b' + dbLoader.baseNamespaces[elementQname.namespaceURI] + ':' + elementQname.localName
    else:
        return 'e' + dbLoader.hashEntity() + ':' + elementQname.localName

def hashEntity(self):
    return self.entityScheme + "|" + self.entityIdentifier

def fiscalYearEnd(dbLoader):
    fiscalYearMonthDayEnd = dbLoader.getSimpleModelFactByQname('/jpdei/', 'CurrentFiscalYearEndDateDEI')
    if fiscalYearMonthDayEnd is not None and isinstance(fiscalYearMonthDayEnd.xValue, datetime.datetime):
        return fiscalYearMonthDayEnd.xValue.month, fiscalYearMonthDayEnd.xValue.day
    else:
        fiscalYearMonthDayEnd = None
        # get from previous filings
        results = dbLoader.execute(
            '''
                SELECT f.fact_value
                 FROM   fact f
                 JOIN element e
                   ON f.element_id = e.element_id
                 JOIN qname qe
                   ON e.qname_id = qe.qname_id
                 JOIN namespace n
                   ON qe.namespace = n.uri
                 JOIN context c
                   ON f.context_id = c.context_id
                 JOIN report r
                   ON f.accession_id = r.report_id
                 WHERE qe.local_name = 'CurrentFiscalYearEndDateDEI'
                   AND qe.namespace ilike '%%/jpdei/%%'
                   AND r.entity_id = %s
                 ORDER BY c.period_instant desc
            ''', params=(dbLoader.entityId,))
        if len(results) > 0:
            fiscalYearMonthDayEnd = results[0][0]

        fiscalYearMonthEnd = None
        fiscalYearDayEnd = None
        if fiscalYearMonthDayEnd is not None:
            fiscalYearMonthEnd = int(fiscalYearMonthDayEnd[5:7])
            fiscalYearDayEnd = int(fiscalYearMonthDayEnd[8:10])

        if fiscalYearMonthEnd is None:
            dbLoader.modelXbrl.info('info', _('Cannot determine fiscal year end month/day'))

        return fiscalYearMonthEnd, fiscalYearDayEnd

def identifyEntityAndFilingInfo(dbLoader):
    global _document_control_number
    _document_control_number = None

    info = dict()

    # Entity Name (English)
    _filingProperty(dbLoader, info, 'entityName', None, 'CompanyNameInEnglishCoverPage')
    if info.get('entityName') is None or info.get('entityName') == '':
        # Entity Name (Japanese)
        _filingProperty(dbLoader, info, 'entityName', None, 'CompanyNameCoverPage')

    # Document control number - used as identifier for the report.
    reportId = _reportIdFromUri(dbLoader.modelXbrl.modelDocument.uri)
    if reportId is not None:
        info['accessionNumber'] = reportId

    # Acceptance Date
    _filingProperty(dbLoader, info, 'acceptanceDate', None, 'FilingDateCoverPage')

    # Report period date
    _filingProperty(dbLoader, info, 'period', None, 'CurrentPeriodEndDateDEI')
    if info.get('period') == '':
        del info['period']

    # Remap the documents in the zip file. This will change the uri of the documents when they are stored in the
    # database.

    base = dbLoader.modelXbrl.modelDocument.uri
    base = base.replace('\\','/') # convert all slashes to forward slashes
    basePathParts = base.split('/')
    goodBasePathParts = basePathParts[-4:-1] # This is the last 3 directories of the path.
    if len(goodBasePathParts) == 3:
        sourceUriMap = dict()
        for uri in dbLoader.modelXbrl.urlDocs.keys():
            path, fileName = os.path.split(uri)
            path = path.replace('\\','/')
            pathParts = path.split('/')
            goodPathParts = pathParts[-3:] # The last 3 directories
            if goodPathParts == goodBasePathParts:
                # This uri should be remapped
                sourceUriMap[uri] = '/'.join(goodPathParts) + '/' + fileName
        if len(sourceUriMap) > 0:
            info['sourceUriMap'] = sourceUriMap

    return info

def _reportIdFromUri(uri):
    """Get the document control number from the directory structure of the manifest file uri.

    If the inline infoset or xbrl instance is loaded from the directory structure that is generated from the Japan
    EDINET site, the document control number will be the name of the directory that is 2 levels up (grandparent
    directory).
    """
    sep = '\\' if '\\' in uri else '/'
    pathParts = uri.split(sep)
    if len(pathParts) >= 4:
        if (pathParts[-2].lower() in ('publicdoc', 'auditdoc') and
            pathParts[-3].lower() == 'xbrl'):
            global _document_control_number
            _document_control_number = pathParts[-4]
            return '{}-{}'.format(pathParts[-4], pathParts[-2].lower())
    # document control number cannot be determined from the uri
    return None

def _filingProperty(dbLoader, info, key, partialNS, conceptName):
    """Get a piece of filing info from the model and store in the supplied dictionary."""

    infoValue = dbLoader.getSimpleFactByQname(partialNS, conceptName)
    if infoValue is not None:
        info[key] = infoValue

def reportProperties(dbLoader):
    info = dict()
    global _document_control_number
    info['document_control_number'] = _document_control_number
    _filingProperty(dbLoader, info, 'entity_name_jp', None, 'CompanyNameCoverPage')
    _filingProperty(dbLoader, info, 'entity_name_en', None, 'CompanyNameInEnglishCoverPage')
    _filingProperty(dbLoader, info, 'filing_date', None, 'FilingDateCoverPage')
    _filingProperty(dbLoader, info, 'document_title', None, 'DocumentTitleCoverPage')
    _filingProperty(dbLoader, info, 'clause_of_stipulations', None, 'ClauseOfStipulationCoverPage')
    _filingProperty(dbLoader, info, 'place_of_filing', None, 'PlaceOfFilingCoverPage')
    _filingProperty(dbLoader, info, 'quarterly_accounting_period', None, 'QuarterlyAccountingPeriodCoverPage')
    _filingProperty(dbLoader, info, 'title_and_name_of_representative', None, 'TitleAndNameOfRepresentativeCoverPage')
    _filingProperty(dbLoader, info, 'address_of_registered_headquarter', None, 'AddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'telephone_number_of_registered_headquarter', None,
                   'TelephoneNumberAddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'name_of_contact_registered_headquarter', None,
                    'NameOfContactPersonAddressOfRegisteredHeadquarterCoverPage')
    _filingProperty(dbLoader, info, 'nearest_place_of_contact', None,
                    'NearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'telephone_number_nearest_place_of_contact', None,
                    'TelephoneNumberNearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'name_of_contact_nearest_place_of_contact', None,
                    'NameOfContactPersonNearestPlaceOfContactCoverPage')
    _filingProperty(dbLoader, info, 'edinet_code', None, 'EDINETCodeDEI')
    _filingProperty(dbLoader, info, 'fund_code', None, 'FundCodeDEI')
    _filingProperty(dbLoader, info, 'security_code', None, 'SecurityCodeDEI')
    _filingProperty(dbLoader, info, 'filer_name_jp', None, 'FilerNameInJapaneseDEI')
    _filingProperty(dbLoader, info, 'filer_name_en', None, 'FilerNameInEnglishDEI')
    _filingProperty(dbLoader, info, 'fund_name_jp', None, 'FundNameInJapaneseDEI')
    _filingProperty(dbLoader, info, 'fund_name_en', None, 'FundNameInEnglishDEI')
    _filingProperty(dbLoader, info, 'cabinet_office_ordinance', None, 'CabinetOfficeOrdinanceDEI')
    _filingProperty(dbLoader, info, 'document_type', None, 'DocumentTypeDEI')
    _filingProperty(dbLoader, info, 'accounting_standards', None, 'AccountingStandardsDEI')
    _filingProperty(dbLoader, info, 'wheter_consolidated_financial_statements_are_prepared', None, 'WhetherConsolidatedFinancialStatementsArePreparedDEI')
    _filingProperty(dbLoader, info, 'industry_code_when_cosolidated_financial_statements_are_prepared_in_accordance_with_industry_specific_regulatoins', None, 'IndustryCodeWhenConsolidatedFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI')
    _filingProperty(dbLoader, info, 'industry_code_when_financial_statements_are_prepared_in_accordance_with_industry_specific_regulations', None, 'IndustryCodeWhenFinancialStatementsArePreparedInAccordanceWithIndustrySpecificRegulationsDEI')
    _filingProperty(dbLoader, info, 'current_fiscal_year_start_date', None, 'CurrentFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'current_period_end_date', None, 'CurrentPeriodEndDateDEI')
    _filingProperty(dbLoader, info, 'type_of_current_period', None, 'TypeOfCurrentPeriodDEI')
    _filingProperty(dbLoader, info, 'current_fiscal_year_end_date', None, 'CurrentFiscalYearEndDateDEI')
    _filingProperty(dbLoader, info, 'previous_fiscal_year_start_date', None, 'PreviousFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'comparative_period_end_date', None, 'ComparativePeriodEndDateDEI')
    _filingProperty(dbLoader, info, 'previous_fiscal_year_end_date', None, 'PreviousFiscalYearEndDateDEI')
    _filingProperty(dbLoader, info, 'next_fiscal_year_start_date', None, 'NextFiscalYearStartDateDEI')
    _filingProperty(dbLoader, info, 'end_date_of_quarterly_or_semi_annual_period_of_next_fiscal_year', None, 'EndDateOfQuarterlyOrSemiAnnualPeriodOfNextFiscalYearDEI')
    _filingProperty(dbLoader, info, 'amendment_flag', None, 'AmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'identification_of_document_subject_to_amendment', None, 'IdentificationOfDocumentSubjectToAmendmentDEI')
    _filingProperty(dbLoader, info, 'report_amendment_flag', None, 'ReportAmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'XBRL_amendment_flag', None, 'XBRLAmendmentFlagDEI')
    _filingProperty(dbLoader, info, 'security_code', None, 'SecurityCodeDEI')

    return json.dumps(info)

def checkLoaded(dbLoader, entry_point_name):
    if entry_point_name is None:
        return False

    report_id = _reportIdFromUri(entry_point_name)
    query = 'SELECT 1 FROM report r JOIN source s ON r.source_id = s.source_id WHERE r.source_report_identifier = %s AND s.source_name = %s'
    res = dbLoader.execute(query, params=(report_id, dbLoader.sourceName))
    if len(res) == 0:
        return False
    else:
        return True

__sourceInfo__ = {
                  "name": "SEC US GAAP Corporate Issue Filings",
                  "calculateFiscalPeriod" : True,
                  "requiresSourceReportIdentifier": True,
    "hasExtensions": True,
    "basePrefixPatterns":
        (
         (r'^http://www.xbrl.org/', None),
         (r'^http://www.xbrl.org/dtr/', r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),
         (r'^http://www.xbrl.org/2009/role/negated', r'^http://[^/]*/[^/]*/[^/]*/([^/]*)'),

         (r'^http://xbrl.org/', None),
         (r'^http://www.w3.org/', None),

         (r'^http://disclosure.edinet-fsa.go.jp/taxonomy/', r'^http://[^/]*/[^/]*/[^/]*/[^/]*/([^/]*)'),
         ),

    "overrideFunctions" : {
                      "UOMString" : UOMString,
                      "UOMHash" : UOMString, #note the hash and the string form of the unit of measure are the same
                      "identifyFiscalYearEnd": fiscalYearEnd,
                      "identifyEntityAndFilingingInfo": identifyEntityAndFilingInfo,
                      "conceptQnameHash" : ConceptHash,
                      "reportProperties": reportProperties,
                      "checkLoaded": checkLoaded,
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