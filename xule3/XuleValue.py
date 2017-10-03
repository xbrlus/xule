'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change: 21757 $
'''
from .XuleRunTime import XuleProcessingError
from arelle.ModelValue import QName, dayTimeDuration, DateTime, gYear, gMonthDay, gYearMonth, InvalidValue, IsoDuration
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelRelationshipSet import ModelRelationshipSet
import datetime
import decimal
from aniso8601.__init__ import parse_duration, parse_datetime, parse_date
import collections
import copy
import pprint

class XuleValueSet:
    def __init__(self, values=None):
        self.values = collections.defaultdict(list)
        
        if values is not None:
            self.append(values)
            
    def __iter__(self):
        for val in self.values:
            yield val

    def append(self, values):
        if hasattr(values, '__iter__'):
            for val in values:
                self._append_check(val)
        else:
            self._append_check(values)
            
    def _append_check(self, value):
        if isinstance(value, XuleValue):
            self.values[value.alignment].append(value)
        else:
            raise XuleProcessingError(_("Internal error: XuleValueSet can only append a XuleValue, found '%s'" % type(value)))
        
    def __copy__(self):
        new_value_set = XuleValueSet()
        new_value_set.values = copy.copy(self.values)
        return new_value_set
        
class XuleValue:
    def __init__(self, xule_context, orig_value, orig_type, alignment=None, from_model=False, shadow_collection=None, tag=None):
        xule_type, xule_value, fact = self._get_type_and_value(xule_context, orig_value, orig_type)
        
        #self.xule_context = xule_context
        self.value = xule_value
        self.type = xule_type
        self.fact = fact
        self.from_model = from_model
        self.alignment = alignment
        self.facts = None
        self.tags = None
        self.aligned_result_only = False
        self.used_vars = None
        self.used_expressions = None
        self.shadow_collection = shadow_collection
        self.tag = tag if tag is not None else self
        
        if self.type in ('list', 'set') and self.shadow_collection is None:
        #if self.type in ('list', 'set'):            
            shadow = [x.shadow_collection if x.type in ('set','list') else x.value for x in self.value]
            if self.type == 'list':
                self.shadow_collection = tuple(shadow)
            else:
                self.shadow_collection = frozenset(shadow)
    ''' 
    import traceback
    def __eq__(self, other):
#         print("EQUAL")
#         print(traceback.format_stack())
        if type(other) is type(self):
            return self.value == other.value
        else:
            return False
    
    def __ne__(self, other):
#         print("NOT EQUAL")
#         print(traceback.format_stack())
        return not self.__eq__(other)
    
    def __hash__(self):
#         print("HASH")
#         print(traceback.format_stack())        
        return hash(self.value)
    '''
    def clone(self):       
        new_value = copy.copy(self)
        #new_value.value = copy.copy(self.value)
        new_value.alignment = copy.copy(self.alignment)
        new_value.facts = copy.copy(self.facts)
        new_value.tags = copy.copy(self.tags)
        new_value.shadow_collection = copy.copy(self.shadow_collection)
        new_value.used_vars = copy.copy(self.used_vars)
        new_value.used_expressions = copy.copy(self.used_expressions)
    
        return new_value

    def _get_type_and_value(self, xule_context, orig_value, orig_type):
        #set value, type, fact on the XuleValue
        if orig_type == 'fact':
            #get the underlying value and determine the type
            xule_type, compute_value = model_to_xule_type(xule_context, orig_value.xValue)
            return xule_type, compute_value, orig_value
        else:
            return orig_type, orig_value, None

    @property
    def is_fact(self):
        return self.fact is not None
    
    def format_value(self):
            
        if self.type in ('float', 'decimal'):
            format_rounded = "{0:,.4f}".format(self.value)
            reduced_round = self._reduce_number(format_rounded)
            format_orig = "{0:,}".format(self.value)
            reduced_orig = self._reduce_number(format_orig)
            
            if reduced_round != reduced_orig:
                reduced_round += " (rounded 4d)" 
                
            return reduced_round
        
        elif self.type == 'int':
            if self.fact is not None:
                if type(self.fact.xValue) == gYear:
                    return str(self.value)
                
            return "{0:,}".format(self.value)
        
        elif self.type == 'unit':
            if len(self.value[1]) == 0:
                #no denominator
                unit_string = "%s" % " * ".join([x.localName for x in self.value[0]])
            else:
                unit_string = "%s/%s" % (" * ".join([x.localName for x in self.value[0]]), 
                                                 " * ".join([x.localName for x in self.value[1]]))
            return unit_string
        
        elif self.type == 'duration':
            if self.value[0] == datetime.datetime.min and self.value[1] == datetime.datetime.max:
                return "forever"
            else:
                if self.from_model == True:
                    end_date = self.value[1] - datetime.timedelta(days=1)
                else:
                    end_date = self.value[1]
                return"duration('%s', '%s')" % (self.value[0].strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            
        elif self.type == 'instant':
            if self.from_model == True:
                return "instant('%s')" % (self.value - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                return "instant('%s')" % self.value.strftime("%Y-%m-%d")
        
        elif self.type == 'list':
            list_value = ", ".join([sub_value.format_value() for sub_value in self.value])
            return list_value
        
        elif self.type == 'set':
            set_value = "set(" + ", ".join([sub_value.format_value() for sub_value in self.value]) + ")" 
            return set_value
        
        elif self.type == 'dictionary':
            new_dict_value = {k_value.format_value(): v_value.format_value() for k_value, v_value in self.value}
            
            return pprint.pformat(new_dict_value)
        
        elif self.type == 'concept':
            return str(self.value.qname)
        
        elif self.type == 'taxonomy':
            if self.value.xule_taxonomy_type == 'taxonomy':
                return("instance taxonomy")
            else:
                return("rules taxonomy")
            
        elif self.type == 'network':
            return "\n" + "\n".join([str(x) for x in self.value[0]]) + "\n# of relationships: " + str(len(self.value[1].modelRelationships)) + "\n"
        
        elif self.type == 'unbound':
            return "missing"
        
        elif self.type == 'roll_forward_set':
            s = []
            for pattern in self.value:
                #s.append("Network: " + xule_context.model.roleTypes[pattern['pres_net'].linkrole][0].definition + " (" + pattern['pres_net'].linkrole + ")")
                s.append("Netowrk: " + pattern['pres_net'].linkrole)
                if pattern['dimension_info'] is not None:
                    if len(pattern['dimension_info']) == 0:
                        s.append("\t" + "Dimenions: NO PAIRS")
                    for dim, dim_info in pattern['dimension_info'].items():
                        s.append("\t" + "Dimension: " + str(dim) + " (" + str(dim_info['has_default']) + ")")
                        for mem in dim_info['members']:
                            s.append("\t\t" + str(mem))
                else:
                    s.append("\t" + "Dimensions: NONE")
                s.append("\t" + "balance_concept: " + str(pattern['balance_concept'].qname))
                for contrib in pattern['contributing_concepts']:
                    weight = '+' if contrib in pattern['addins'] else '-' if contrib in pattern['subouts'] else 'UNKNOWN'
                    s.append("\t\t" + weight + " " + str(contrib.qname))
                for base_total_concept in pattern['base_total_concepts']:
                    matches_total = " (no)"
                    if pattern['total_concept'] is not None:
                        if base_total_concept.qname == pattern['total_concept'].qname:
                            matches_total = " (yes)"
                    s.append("\t" + "total: " + str(base_total_concept.qname) + matches_total)
                
            return "\n".join(s)
        
        elif self.type == 'label':
            return "(" + self.value.role + ")(" + self.value.xmlLang + ") " +self.value.textValue
        else:
            return str(self.value)

    def _reduce_number(self, num):
        if '.' in num:
            j = 0
            #for i in range(1,4):
            i = 1
            while True:
                if num[-i] == '.':
                    break
                elif num[-i] == '0':
                    j = i
                else:
                    break
                i += 1
            if j != 0:
                num = num[:-j]
            if num[-1] == '.':
                num = num[:-1]
            return num
        else:
            return num

class XulePeriodComp:
    '''
    This class is used to compare periods.
    '''
    def __init__(self, period):
        if isinstance(period, tuple):
            #this is a duration
            self.start = period[0]
            self.end = period[1]
            self.instant = None
            self.type = 'duration'
        elif isinstance(period, datetime.datetime):
            #this is an instance
            self.start = None
            self.end = None
            self.instant = period
            self.type = 'instant'
        else:
            raise XuleProcessingError(_("XulePeriodComp can only be initailzied with a single datetime or a tuple of two datetimes. Found '%s'" % period))
        
    def __eq__(self, other):
        return (self.start == other.start  and
                self.end == other.end and
                self.instant == other.instant)
    
    def __ne__(self, other):
        return (self.start != other.start or
                self.end != other.end or
                self.instant != other.instant)

    def __lt__(self, other):
        if self.type != other.type:
            return NotImplemented
        else:
            if self.type == 'instant':
                return self.instant < other.instant
            else:
                return (self.start < other.start or
                    self.start == other.start and self.end < other.end)
    '''
        if self.type ==  'instant' and other.type == 'instant':
            return self.instant < other.instant
        elif self.type == 'duration' and other.type == 'duration':
            return (self.start < other.start or
                    self.start == other.start and self.end < other.end)
        elif self.type == 'instant' and other.type == 'duration':
            return self.instant < other.start
        elif self.type == 'duration' and other.type == 'instant':
            return self.start < other.instant
        else:
            raise XuleProcessingError(_("Internal error: XulePeriodComp has bad types: '%s' and '%s'" % (self.type, other.type)))
    '''
    def __gt__(self, other):
        if self.type != other.type:
            return NotImplemented
        else:
            if self.type == 'instant':
                return self.instant > other.instant
            else:
                return (self.end > other.end or
                        self.end == other.end and self.start > other.start)
    '''
        if self.type ==  'instant' and other.type == 'instant':
            return self.instant > other.instant
        elif self.type == 'duration' and other.type == 'duration':
            return (self.end > other.end or
                    self.end == other.end and self.start > other.start)
        elif self.type == 'instant' and other.type == 'duration':
            return self.instant > other.start
        elif self.type == 'duration' and other.type == 'instant':
            return self.start > other.instant
        else:
            raise XuleProcessingError(_("Internal error: XulePeriodComp has bad types: '%s' and '%s'" % (self.type, other.type)))
    '''
    def __le__(self, other):
        if self.type != other.type:
            return NotImplemented
        else:      
            return self.__eq__(other) or self.__lt__(other)
        
    def __ge__(self, other):
        if self.type != other.type:
            return NotImplemented
        else:
            return self.__eq__(other) or self.__gt__(other)

class XuleRole:
    def __init__(self, role_uri):
        self._role_uri = role_uri
    
    def __str__(self):
        return self._role_uri
    
    @property
    def roleURI(self):
        return self._role_uri
    
    @property
    def definition(self):
        return STANDARD_ROLE_DEFINITIONS.get(self._role_uri)
    
    @property
    def usedOns(self):
        if self._role_uri in STANDARD_ROLE_USEDON:
            return {STANDARD_ROLE_USEDON[self._role_uri],}
        else:
            return set()

STANDARD_ROLE_USEDON = {
    'http://www.xbrl.org/2003/role/label':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/terseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/verboseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/positiveLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/positiveTerseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/positiveVerboseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/negativeLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/negativeTerseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/negativeVerboseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/zeroLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/zeroTerseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/zeroVerboseLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/totalLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/periodStartLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/periodEndLabel':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/documentation':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/definitionGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/disclosureGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/presentationGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/measurementGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/commentaryGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/exampleGuidance':QName('link','http://www.xbrl.org/2003/linkbase','label'),
    'http://www.xbrl.org/2003/role/reference':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/definitionRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/disclosureRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/mandatoryDisclosureRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/recommendedDisclosureRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/unspecifiedDisclosureRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/presentationRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/measurementRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/commentaryRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/exampleRef':QName('link','http://www.xbrl.org/2003/linkbase','reference'),
    'http://www.xbrl.org/2003/role/footnote':QName('link','http://www.xbrl.org/2003/linkbase','footnote')
                        }

STANDARD_ROLE_DEFINITIONS = {'http://www.xbrl.org/2003/role/link':'Standard extended link role',
                    'http://www.xbrl.org/2003/role/label':    'Standard label for a Concept.',
                    'http://www.xbrl.org/2003/role/terseLabel': 'Short label for a Concept, often omitting text that should be inferable when the concept is reported in the context of other related concepts.',
                    'http://www.xbrl.org/2003/role/verboseLabel': 'Extended label for a Concept, making sure not to omit text that is required to enable the label to be understood on a stand alone basis.',
                    'http://www.xbrl.org/2003/role/positiveLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/positiveTerseLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/positiveVerboseLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/negativeLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/negativeTerseLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/negativeVerboseLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/zeroLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/zeroTerseLabel': 'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/zeroVerboseLabel':'Label for a Concept, when the value being presented is positive (negative, zero). For example, the standard and standard positive labels might be "profit after tax" and the standard negative labels "loss after tax", the terse label and terse positive labels might both be "profit", while the negative terse label might be "loss".',
                    'http://www.xbrl.org/2003/role/totalLabel': 'The label for a Concept for use in presenting values associated with the concept when it is being reported as the total of a set of other values.',
                    'http://www.xbrl.org/2003/role/periodStartLabel': 'The label for a Concept with periodType="instant" for use in presenting values associated with the concept when it is being reported as a start (end) of period value.',
                    'http://www.xbrl.org/2003/role/periodEndLabel': 'The label for a Concept with periodType="instant" for use in presenting values associated with the concept when it is being reported as a start (end) of period value.',
                    'http://www.xbrl.org/2003/role/documentation':    'Documentation of a Concept, providing an explanation of its meaning and its appropriate usage and any other documentation deemed necessary.',
                    'http://www.xbrl.org/2003/role/definitionGuidance':    'A precise definition of a Concept, providing an explanation of its meaning and its appropriate usage.',
                    'http://www.xbrl.org/2003/role/disclosureGuidance':    '''An explanation of the disclosure requirements relating to the Concept. Indicates whether the disclosure is,
mandatory (i.e. prescribed by authoritative literature);,
recommended (i.e. encouraged by authoritative literature;,
common practice (i.e. not prescribed by authoritative literature, but disclosure is common);,
structural completeness (i.e., included to complete the structure of the taxonomy).''',
                    'http://www.xbrl.org/2003/role/presentationGuidance': 'An explanation of the rules guiding presentation (placement and/or labelling) of this Concept in the context of other concepts in one or more specific types of business reports. For example, "Net Surplus should be disclosed on the face of the Profit and Loss statement".',
                    'http://www.xbrl.org/2003/role/measurementGuidance': 'An explanation of the method(s) required to be used when measuring values associated with this Concept in business reports.',
                    'http://www.xbrl.org/2003/role/commentaryGuidance':    'Any other general commentary on the Concept that assists in determining definition, disclosure, measurement, presentation or usage.',
                    'http://www.xbrl.org/2003/role/exampleGuidance': 'An example of the type of information intended to be captured by the Concept.',

                    'http://www.xbrl.org/2003/role/reference': 'Standard reference for a Concept',
                    'http://www.xbrl.org/2003/role/definitionRef':'Reference to documentation that details a precise definition of the Concept.',
                    'http://www.xbrl.org/2003/role/disclosureRef':'''Reference to documentation that details an explanation of the disclosure requirements relating to the Concept. Specified categories include:
mandatory
recommended''',
                    'http://www.xbrl.org/2003/role/mandatoryDisclosureRef':'''Reference to documentation that details an explanation of the disclosure requirements relating to the Concept. Specified categories include:
mandatory
recommended''',
                    'http://www.xbrl.org/2003/role/recommendedDisclosureRef':'''Reference to documentation that details an explanation of the disclosure requirements relating to the Concept. Specified categories include:
mandatory
recommended''',
                    'http://www.xbrl.org/2003/role/unspecifiedDisclosureRef':'''Reference to documentation that details an explanation of the disclosure requirements relating to the Concept. Unspecified categories include, but are not limited to:
common practice
structural completeness
The latter categories do not reference documentation but are indicated in the link role to indicate why the Concept has been included in the taxonomy.''',
                    'http://www.xbrl.org/2003/role/presentationRef':'Reference to documentation which details an explanation of the presentation, placement or labelling of this Concept in the context of other Concepts in one or more specific types of business reports',
                    'http://www.xbrl.org/2003/role/measurementRef':'Reference concerning the method(s) required to be used when measuring values associated with this Concept in business reports',
                    'http://www.xbrl.org/2003/role/commentaryRef':'Any other general commentary on the Concept that assists in determining appropriate usage',
                    'http://www.xbrl.org/2003/role/exampleRef':'Reference to documentation that illustrates by example the application of the Concept that assists in determining appropriate usage.',
                    'http://www.xbrl.org/2003/role/footnote':'Standard footnote role'
}

def model_to_xule_unit(model_unit_measures, xule_context):
    numerator = tuple(sorted(model_unit_measures[0]))
    denominator = tuple(sorted(model_unit_measures[1]))
    
    model_unit = (numerator, denominator)
    
    #this is done to force the unit to be normalized. This will convert something like USD/pure to just USD.
    normalized_unit = unit_multiply(model_unit, ((XBRL_PURE,),()))
    
    return normalized_unit

def model_to_xule_model_datetime(model_date_time, xule_context):
    '''This is used for datetimes that are stored as values of facts. These use arelle.ModelValue.DateTime type.'''
    return iso_to_date(xule_context, str(model_date_time))

def model_to_xule_model_g_year(model_g_year, xule_context):
    return model_g_year.year

def model_to_xule_model_g_month_day(model_g_month_day, xule_context):
    return "--%s-%s" % (str(model_g_month_day.month).zfill(2),str(model_g_month_day.day).zfill(2))

def model_to_xule_model_g_year_month(model_g_year_month, xule_context):
    return str(model_g_year_month)

def model_to_xule_period(model_context, xule_context):
    if model_context.isStartEndPeriod:
        return (model_context.startDatetime, model_context.endDatetime)# - datetime.timedelta(days=1))
    elif model_context.isInstantPeriod:
        return model_context.endDatetime # - datetime.timedelta(days=1)
    elif model_context.isForeverPeriod:
        return (datetime.datetime.min, datetime.datetime.max)
    else:
        raise XuleProcessingError(_("Period is not duration, instant or forever"), xule_context)

def model_to_xule_entity(model_context, xule_context):
    return (model_context.entityIdentifier[0], model_context.entityIdentifier[1])

def iso_to_date(xule_context, date_string):
        try:
            '''THIS COULD USE A BETTER METHOD FOR CONVERTING THE ISO FORMATTED DATE TO A DATETIME.'''
            if len(date_string) == 10:
                return date_to_datetime(parse_date(date_string))
                #return datetime.datetime.strptime(date_string,'%Y-%m-%d')
            else:
                return parse_datetime(date_string)
                #return datetime.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S')
        except NameError:
            raise XuleProcessingError(_("'%s' could not be converted to a date." % date_string), xule_context)
        except Exception:
            raise XuleProcessingError(_("Error converting date: '%s'" % date_string), xule_context)    

def date_to_datetime(date_value):
    if isinstance(date_value, datetime.datetime):
        return date_value
    else:
        return datetime.datetime.combine(date_value, datetime.datetime.min.time())

def unit_multiply(left_unit, right_unit):
    
    left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
    left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
                  
    right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
    right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
    
    #new nuemrator and denominator before (pre) canceling
    new_num_pre = tuple(sorted(left_num + right_num))
    new_denom_pre = tuple(sorted(left_denom + right_denom))
    
    new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
    
    if len(new_num) == 0:
        new_num = (XBRL_PURE,)   
    
    return (new_num, new_denom)

def unit_cancel(left, right):
    #need mutable structure
    left_list = list(left)
    right_list = list(right)
    
    for l in range(len(left_list)):
        for r in range(len(right_list)):
            if left_list[l] == right_list[r]:
                left_list[l] = None
                right_list[r] = None
    
    return tuple(x for x in left_list if x is not None), tuple(x for x in right_list if x is not None)
    
def unit_divide(left_unit, right_unit):
    
    left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
    left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
                  
    right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
    right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
    
    #new nuemrator and denominator before (pre) canceling
    new_num_pre = tuple(sorted(left_num + right_denom))
    new_denom_pre = tuple(sorted(left_denom + right_num))
    
    new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
    
    if len(new_num) == 0:
        new_num = (XBRL_PURE,)   
    
    return (new_num, new_denom)

XBRL_PURE = QName(None, 'http://www.xbrl.org/2003/instance', 'pure')

TYPE_XULE_TO_SYSTEM = {'int': int,
                       'float': float,
                       'string': str,
                       'qname': QName,
                       'bool': bool,
                       'list': list,
                       'set': set,
                       'network': ModelRelationshipSet,
                       'decimal': decimal.Decimal,
                       'unbound': None,
                       'none': None,
                       'fact': ModelFact}

#period and unit are tuples

TYPE_SYSTEM_TO_XULE = {int: 'int',
                       float: 'float',
                       str: 'string',
                       QName: 'qname',
                       bool: 'bool',
                       list: 'list',
                       set: 'set',
                       ModelRelationshipSet: 'network',
                       decimal.Decimal: 'decimal',
                       type(None): 'unbound',
                       InvalidValue: 'unbound',
                       ModelFact: 'fact',
                       datetime.datetime: 'instant',
                       datetime.date: 'instant',
                       DateTime: 'model_date_time',
                       IsoDuration: 'iso_duration',
                       gYear: 'model_g_year',
                       gMonthDay: 'model_g_month_day',
                       gYearMonth: 'model_g_year_month'}

TYPE_STANDARD_CONVERSION = {'model_date_time': (model_to_xule_model_datetime, 'instant'),
                            'model_g_year': (model_to_xule_model_g_year, 'int'),
                            'model_g_month_day': (model_to_xule_model_g_month_day, 'string'),
                            'model_g_year_month': (model_to_xule_model_g_year_month, 'string'),
                            'iso_duration': (lambda x,c: x.sourceValue, 'string')}

'''The TYPE_MAP shows conversions between xule types. The first entry is the common conversion when comparing
   2 values, the second entry (if present) is a reverse conversion.
   
   When converting float values, the str() function is used to handle difficult floats.
'''
TYPE_MAP = {frozenset(['int', 'float']): [('float', float), ('int', lambda x: int(str(x)))],
            frozenset(['int', 'decimal']): [('decimal', decimal.Decimal), ('int', lambda x: int(str(x)))],
            frozenset(['float', 'decimal']): [('decimal', lambda x: decimal.Decimal(str(x))), ('float', float)],
            frozenset(['balance', 'none']): [('balance', lambda x: x)], #this lambda does not convert the compute value
            frozenset(['balance', 'unbound']): [('balance', lambda x: x)],
            frozenset(['int', 'string']): [('string', str), ('int', int)],
            frozenset(['decimal', 'string']): [('string', str), ('decimal', decimal.Decimal)],
            frozenset(['uri', 'string']): [('string', lambda x: x), ('uri', lambda x: x)],
            #frozenset(['none', 'string']): [('string', lambda x: x if x is not None else '')],
            }

def model_to_xule_type(xule_context, model_value):

    if type(model_value) in TYPE_SYSTEM_TO_XULE:
        xule_type, compute_value = TYPE_SYSTEM_TO_XULE[type(model_value)], model_value
        
        if xule_type in TYPE_STANDARD_CONVERSION:
            conversion_function = TYPE_STANDARD_CONVERSION[xule_type][0]
            xule_type = TYPE_STANDARD_CONVERSION[xule_type][1]
            compute_value = conversion_function(compute_value, xule_context)
            
# This was implement to see if integer math was more efficient. However, it did not prove to improve performance                
#                 if xule_type == 'decimal' and compute_value.as_tuple()[2] == 0:
#                     xule_type = 'int'
#                     compute_value = int(compute_value)
    else:
        raise XuleProcessingError(_("Do not have map to convert system type '%s' to xule type." % type(model_value).__name__), xule_context)

    return xule_type, compute_value

def xule_castable(from_value, to_type, xule_context):
    if from_value.type == to_type:
        return True
    
    type_map = TYPE_MAP.get((frozenset([from_value.type, to_type])))
    if type_map is None:
        return False
    else:
        if type_map[0][0] == to_type:
            return True
        else:
            if len(type_map) > 1:
                if type_map[1][0] == to_type:
                    return True
                else:
                    return False
            else:
                return False

def xule_cast(from_value, to_type, xule_context):
    #from_type, from_value = get_type_and_compute_value(from_result, xule_context)
    
    if from_value.type == to_type:
        return from_value.value
    
    type_map = TYPE_MAP.get((frozenset([from_value.type, to_type])))
    if type_map is None:
        raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_value.type, to_type)), xule_context)
    else:
        if type_map[0][0] == to_type:
            return type_map[0][1](from_value.value)
        else:
            if len(type_map) > 1:
                if type_map[1][0] == to_type:
                    return type_map[1][1](from_value.value)
                else:
                    raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_value.type, to_type)), xule_context)
            else:
                raise XuleProcessingError(_("Type '%s' is not castable to '%s'" % (from_value.type, to_type)), xule_context)

def combine_xule_types(left, right, xule_context):
    #left and right are XuleValues   
    
    left_value = left.value
    right_value = right.value
    
    if left.type == right.type:
        if left.type in ('instant', 'duration'):
            left_value, right_value = combine_period_values(left, right, xule_context)
        return (left.type, left_value, right_value)
    else:
        type_map = TYPE_MAP.get(frozenset([left.type, right.type]))
        
        if type_map is not None:
            type_map = type_map[0]
        
            if type_map[0] != left.type:
                left_compute_value = type_map[1](left_value)
            else:
                left_compute_value = left_value
            
            if type_map[0] != right.type:
                right_compute_value = type_map[1](right_value)
            else:
                right_compute_value = right_value
            
            return (type_map[0], left_compute_value, right_compute_value)
        else:
            if left.type in ('unbound', 'none'):
                return (right.type, left_value, right_value)
            elif right.type in ('unbound', 'none'):
                return (left.type, left_value, right_value)
            else:
                return ('unbound', left_value, right_value)

def combine_period_values(left, right, xule_context):    
    if left.type != right.type or left.type not in ('instant', 'duration') or right.type not in ('instant', 'duration'):
        raise XuleProcessingError(_("Internal error, combine_period_values did not get matching or appropiate date types. Recieved '%s' and '%s'" % (left.type, right.type)), xule_context)
    
    if left.from_model == right.from_model:
        return (left.value, right.value)
    else:
        if left.type == 'instant':
            if not left.from_model:
                return (left.value + datetime.timedelta(days=1),
                        right.value)
            else:
                return(left.value,
                       right.value + datetime.timedelta(days=1))
        else:
            #duration
            if not left.from_model:
                return ((left.value[0], left.value[1] + datetime.timedelta(days=1)),
                        right.value)
            else:
                return (left.value,
                        (right.value[0], right.value[1] + datetime.timedelta(days=1)))

        
