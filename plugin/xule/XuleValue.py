"""XuleValue

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2022 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23303 $
DOCSKIP
"""
from .XuleRunTime import XuleProcessingError
from . import XuleProperties
from . import XuleUtility
from arelle.ModelValue import AnyURI, QName, dayTimeDuration, DateTime, gYear, gMonthDay, gYearMonth, InvalidValue, IsoDuration
from arelle.ModelInstanceObject import ModelFact, ModelUnit
from arelle.ModelRelationshipSet import ModelRelationshipSet
from arelle.ModelDtsObject import ModelRelationship
from arelle.ValidateXbrlDimensions import loadDimensionDefaults
from arelle.Validate import validate
import datetime
import decimal
from aniso8601.__init__ import parse_duration, parse_datetime, parse_date
import collections
import copy
from fractions import Fraction
import pprint
import re
import textwrap


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
    def __init__(self, xule_context, orig_value, orig_type, alignment=None, from_model=False, shadow_collection=None, tag=None, orig_fact=None):
        #convert all python strings to XuleString.
        if isinstance(orig_value, str):
            orig_value = XuleString(orig_value)
        
        xule_type, xule_value, fact = self._get_type_and_value(xule_context, orig_value, orig_type)
        
        #self.xule_context = xule_context
        self.value = xule_value
        self.type = xule_type
        self.fact = orig_fact or fact
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
            shadow = [x.shadow_collection if x.type in ('set', 'list', 'dictionary') else x.value for x in self.value]
            if self.type == 'list':
                self.shadow_collection = tuple(shadow)
            else:
                self.shadow_collection = frozenset(shadow)
        elif self.type == 'dictionary' and self.shadow_collection is None:
            shadow = self.shadow_dictionary
            self.shadow_collection = frozenset(shadow.items())
        elif self.type == 'string': # make all strings XuleStrings
            self.value = XuleString(self.value)
    @property
    def shadow_dictionary(self):
        if self.type == 'dictionary':
            if not hasattr(self, '_shadow_dictionary'):
                self._shadow_dictionary = {k.shadow_collection if k.type in ('set', 'list') else k.value: v.shadow_collection if v.type in ('set', 'list', 'dictionary') else v.value for k, v in self.value}
            return self._shadow_dictionary
        else:
            return None
    @property
    def value_dictionary(self):
        if self.type == 'dictionary':
            if not hasattr(self, '_value_dictionary'):
                self._value_dictionary = {k: v for k, v in self.value}
            return self._value_dictionary
        else:
            return None
        
    @property
    def key_search_dictionary(self):
        if self.type == 'dictionary':
            if not hasattr(self, '_key_search_dictionary'):
                self._key_search_dictionary = {k.shadow_collection if k.type in ('set', 'list') else k.value: v for k, v in self.value}
            return self._key_search_dictionary
        else:
            return None      
        
        
    @property
    def sort_value(self):
        if not hasattr(self, '_sort_value'):
            if self.type == 'list':
                self._sort_value = [x.sort_value for x in self.value]
            elif self.type == 'set':
                self._sort_value = {x.sort_value for x in self.value}
            elif self.type == 'dictonary':
                self._sort_value = [[k.sort_value, v.sort_value] for k, v in self.value]
            elif self.type == 'concept':
                self._sort_value = self.value.qname.clarkNotation
            elif self.type == 'qname':
                self._sort_value = self.value.clarkNotation
            else:
                self._sort_value = self.value
        
        return self._sort_value
        
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
       
    def __str__(self):
        return self.format_value()
       
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
            if "{http://xbrl.org/2020/extensible-enumerations-2.0}enumerationSetItemType" in self._type_ancestry(orig_value.concept.type):
                # This is concept that is an extensibile enumeration set. Arelle will pass the valueas
                # a list of QNames. Need to convert to a set of XuleValues where each Xulevalue is a
                # "qname" xule type.
                # The orig_value should be a list or set of qname values
                if not (isinstance(orig_value.xValue, list) or isinstance(orig_value.xValue, set)):
                    raise XuleProcessingError(_("Encountered a extensible enumeration. Expected the fact value to be a set or list, but found '{}'.".format(type(orig_value.xValue).__name__)))
                enum_set = set()
                for enum in orig_value.xValue:
                    enum_value_type, enum_compute_value = model_to_xule_type(xule_context, enum)
                    enum_set.add(XuleValue(xule_context, enum_compute_value, enum_value_type))
                return 'set', enum_set, orig_value
            elif "{http://xbrl.org/2020/extensible-enumerations-2.0}enumerationItemType" in self._type_ancestry(orig_value.concept.type):
                # This should be a single qname, but Arelle puts it in a list
                if isinstance(orig_value.xValue, list):
                    if len(orig_value.xValue) == 1:
                        xule_type, compute_value = model_to_xule_type(xule_context, orig_value.xValue[0]) 
                    else:
                        raise XuleProcessingError(_("Encountered an enumerationItemType that contains more than one value. This type of fact can only have one fact. Concept is '{}' with value of '{}'".format(orig_value.concept.qname.clarkNotation, orig_value.text)))
                else:
                    xule_type, compute_value = model_to_xule_type(xule_context, orig_value.xValue)
                return xule_type, compute_value, orig_value
            else:
                xule_type, compute_value = model_to_xule_type(xule_context, orig_value.xValue)
                return xule_type, compute_value, orig_value
        else:
            return orig_type, orig_value, None

    def _type_ancestry(self, model_type):
        if model_type.typeDerivedFrom is None:
            return [model_type.qname.clarkNotation]
        else:
            return [model_type.qname.clarkNotation] + self._type_ancestry(model_type.typeDerivedFrom)

    @property
    def is_fact(self):
        return self.fact is not None

    @property
    def system_value(self):
        if self.type == 'set':
            return {x.system_value for x in self.value}
        elif self.type == 'list':
            return [x.system_value for x in self.value]
        elif self.type == 'dictionary':
            return {n.system_value: v.system_value for n, v in self.value}
        else:
            return self.value
    
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
            
            return str(self.value)
#             if len(self.value[1]) == 0:
#                 #no denominator
#                 unit_string = "%s" % " * ".join([x.localName for x in self.value[0]])
#             else:
#                 unit_string = "%s/%s" % (" * ".join([x.localName for x in self.value[0]]), 
#                                                  " * ".join([x.localName for x in self.value[1]]))
#             return unit_string
        
        elif self.type == 'duration':
            if self.value[0] == datetime.datetime.min and self.value[1] == datetime.datetime.max:
                return "forever"
            else:
                if self.from_model == True:
                    end_date = self.value[1] - datetime.timedelta(days=1)
                else:
                    end_date = self.value[1]
                return"%s to %s" % (self.value[0].strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
            
        elif self.type == 'instant':
            if self.from_model == True:
                return "%s" % (self.value - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                return "%s" % self.value.strftime("%Y-%m-%d")
        
        elif self.type == 'list':
            #list_value = ", ".join([sub_value.format_value() for sub_value in self.value])
            list_value = "list(" + ", ".join([sub_value.format_value() for sub_value in self.value]) + ")" 
            return list_value
        
        elif self.type == 'set':
            set_value = "set(" + ", ".join([sub_value.format_value() for sub_value in self.value]) + ")" 
            return set_value
        
        elif self.type == 'dictionary': 
            return pprint.pformat(self.system_value)
        
        elif self.type == 'concept':
            return str(self.value.qname)
        
        elif self.type == 'taxonomy':
            return self.value.taxonomy_name
            
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
            return "(" + self.value.role + ") (" + self.value.xmlLang + ") " +self.value.textValue
        
        elif self.type == 'relationship':
            return "relationship from " + str(self.value.fromModelObject.qname) + " to " + str(self.value.toModelObject.qname)
        
        elif self.type == 'reference':
            reference_string = self.value.role + '\n'
            for part in self.value:
                reference_string += '\t' + str(part.qname) + ': ' + part.textValue + '\n'
            return reference_string
        elif self.type == 'role':
            role_string = getattr(self.value, 'roleURI', None) or getattr(self.value, 'arcroleURI', None)
            role_string += ' - ' + self.value.definition
            return role_string
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

class XuleRoleBase:
    def __init__(self, uri, role_type):
        self._uri = uri
        self._role_type = role_type

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.isArcrole == other.isArcrole and self._uri == other.arcroleURI if other.isArcrole else other.roleURI

    def __hash__(self):
        return hash(self._uri)

    @property
    def isArcrole(self):
        return self._role_type == 'arcrole'

class XuleArcrole(XuleRoleBase):
    def __init__(self, arcrole_uri):
        super().__init__(arcrole_uri, 'arcrole')
        
    def __str__(self):
        return self._uri
    
    @property
    def arcroleURI(self):
        return self._uri
    
    @property
    def definition(self):
        return self._STANDARD_ARCROLE_DEFINITIONS.get(self._uri)
    
    @property
    def usedOns(self):
        if self._uri in self._STANDARD_ARCROLE_USEDONS:
            return {self._STANDARD_ARCROLE_USEDONS[self._uri],}
        else:
            return set()
    
    @property
    def cyclesAllowed(self):
        return self._STANDARD_ARCROLE_CYCLES_ALLOWED.get(self._uri)
    
    _STANDARD_ARCROLE_DEFINITIONS = {
            'http://www.xbrl.org/2003/arcrole/fact-footnote': 'Footnote relationship',
            'http://www.xbrl.org/2003/arcrole/concept-label': 'Label relationship',
            'http://www.xbrl.org/2003/arcrole/concept-reference': 'Reference relationship',
            'http://www.xbrl.org/2003/arcrole/parent-child': 'Parent/Child relationship',
            'http://www.xbrl.org/2003/arcrole/summation-item': 'Summation/item relationship',
            'http://www.xbrl.org/2003/arcrole/general-special': 'General/special relationships',
            'http://www.xbrl.org/2003/arcrole/essence-alias': 'Essence/alias relatinoship',
            'http://www.xbrl.org/2003/arcrole/similar-tuples': 'Similar tuples relationship',
            'http://www.xbrl.org/2003/arcrole/requires-element': 'Requires element relationship'}
    
    _STANDARD_ARCROLE_USEDONS = {
            'http://www.xbrl.org/2003/arcrole/fact-footnote': QName('link','http://www.xbrl.org/2003/linkbase','footnoteArc'),
            'http://www.xbrl.org/2003/arcrole/concept-label': QName('link','http://www.xbrl.org/2003/linkbase','labelArc'),
            'http://www.xbrl.org/2003/arcrole/concept-reference': QName('link','http://www.xbrl.org/2003/linkbase','refernceArc'),
            'http://www.xbrl.org/2003/arcrole/parent-child': QName('link','http://www.xbrl.org/2003/linkbase','presentationArc'),
            'http://www.xbrl.org/2003/arcrole/summation-item': QName('link','http://www.xbrl.org/2003/linkbase','calculationArc'),
            'http://www.xbrl.org/2003/arcrole/general-special': QName('link','http://www.xbrl.org/2003/linkbase','definitionArc'),
            'http://www.xbrl.org/2003/arcrole/essence-alias': QName('link','http://www.xbrl.org/2003/linkbase','definitionArc'),
            'http://www.xbrl.org/2003/arcrole/similar-tuples': QName('link','http://www.xbrl.org/2003/linkbase','definitionArc'),
            'http://www.xbrl.org/2003/arcrole/requires-element': QName('link','http://www.xbrl.org/2003/linkbase','definitionArc'),}
    
    _STANDARD_ARCROLE_CYCLES_ALLOWED = {
            'http://www.xbrl.org/2003/arcrole/fact-footnote': 'any',
            'http://www.xbrl.org/2003/arcrole/concept-label': 'any',
            'http://www.xbrl.org/2003/arcrole/concept-reference': 'any',
            'http://www.xbrl.org/2003/arcrole/parent-child': 'undirected',
            'http://www.xbrl.org/2003/arcrole/summation-item': 'any',
            'http://www.xbrl.org/2003/arcrole/general-special': 'undirected',
            'http://www.xbrl.org/2003/arcrole/essence-alias': 'undirected',
            'http://www.xbrl.org/2003/arcrole/similar-tuples': 'any',
            'http://www.xbrl.org/2003/arcrole/requires-element': 'any'}

class XuleRole(XuleRoleBase):
    def __init__(self, role_uri):
        super().__init__(role_uri, 'role')
    
    def __str__(self):
        return self._uri
    
    @property
    def roleURI(self):
        return self._uri
    
    @property
    def arcroleURI(self):
        return self._uri
    
    @property
    def definition(self):
        return self._STANDARD_ROLE_DEFINITIONS.get(self._uri)
    
    @property
    def usedOns(self):
        if self._uri in self._STANDARD_ROLE_USEDON:
            return {self._STANDARD_ROLE_USEDON[self._uri],}
        else:
            return set()

    _STANDARD_ROLE_USEDON = {
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

    _STANDARD_ROLE_DEFINITIONS = {'http://www.xbrl.org/2003/role/link':'Standard extended link role',
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
    
class XuleString(str):
    """Xule string
    
    A string literal in xule can contain a combination of 3 components: a string of character, and escape character or an expression.
    A xule string will keep track of the expression components and create a format string, with the expression components as substitutions.
    It will also provide a dictionary of the substitutions and their values.
    """
    def __new__(cls, format_string, substitutions=None):
        """Constructor
        
        :param format_string: The format string
        :type format_string: str
        :param substitutions: List of 3 part tuples: 0=location in format string, 1=substitution name, 2=substitution value
        :type substituions: list
        :returns: Formatted string
        :rtype: str
        
        The constructor will save the formatted string as the underlying string
        """

        if substitutions is None or len(substitutions) == 0:
            # In this case there are no substitutions so the the XuleString is just a plain string
            if format_string is not None:
                format_string = format_string.replace('%', '%%')
                string_inst = super().__new__(cls, format_string % dict())
                string_inst._format_string = format_string
                string_inst._substitutions = dict()
            else:
                #string_inst = super().__new__(cls, format_string)
                string_inst = None
        else:
            # The format string is not a real python format string. It is a string without the substitutions in it.
            # The substitutions is a list of 3 part tuples: 0=location in format string, 1=substitution name, 2=substitution value.
            # The substitutions are applied to the format string to create a real python %-style format string.
            
            # Find all the '%' signs in the string. Thees wil need to be escaped.
            percent_locations = [m.start() for m in re.finditer('%', format_string)]
            #sub_locations = {x[0]:(x[1], x[2]) for x in substitutions or []}
            sub_locations = collections.defaultdict(list)
            for location, sub_name, sub_value in substitutions or []:
                sub_locations[location].append((sub_name, sub_value))
            
            for i in sorted(percent_locations + list(sub_locations.keys()), reverse=True):
                if i in percent_locations:
                    format_string = format_string[:i] + '%' + format_string[i:]
                else:
                    # i must be in sub_locations
                    sub_value = ''
                    for sub in sub_locations[i]:
                        sub_value += '%({})s'.format(sub[0])
                    format_string = format_string[:i] + sub_value + format_string[i:]
                    #format_string = format_string[:i] + '%({})s'.format(sub_locations[i][0]) + format_string[i:]
            
            format_subs = {x[1]:x[2] for x in substitutions or []}
            
            string_inst = super().__new__(cls, format_string % format_subs)
            
            if len(format_subs) == 0 and len(percent_locations) == 0:
                # In this case the format string is already stored as the base class string. There is no need to duplicate it in the
                # _format_string.
                string_inst._format_string = None
            else:
                string_inst._format_string = format_string
            string_inst._substitutions = format_subs
        
        return string_inst
    
    
    @property
    def format_string(self):
        return getattr(self, '_format_string', None) or self
    
    @property
    def substitutions(self):
        return getattr(self, '_substitutions', None) or dict()
class XuleUnit:
    def __init__(self, *args):
        if len(args) == 1:
            if isinstance(args[0], ModelUnit):
                # the argument is a model unit
                self._numerator = tuple(sorted(args[0].measures[0]))
                #eliminate pure from the denominator.
                denoms = tuple(x for x in args[0].measures[1] if x != XBRL_PURE)
                self._denominator= tuple(sorted(denoms))
                self._unit_xml_id = args[0].id
                self._unit_cancel()
            elif isinstance(args[0], XuleValue) and args[0].type == 'qname':
                self._numerator = (args[0].value,)
                self._denominator = tuple()
                self._unit_xml_id = None
            elif isinstance(args[0], XuleValue) and args[0].type in ('set', 'list'):
                nums = []
                for x in args[0].value:
                    if x.type == 'qname':
                        nums.append(x.value)
                    else:
                        raise XuleProcessingError(_("Unit must be created from qnames, found '{}'".format(x.type)), None)
                self._numerator = tuple(sorted(nums))
                self._denominator = tuple()
                self._unit_xml_id = None
            elif isinstance(args[0], XuleValue) and args[0].type == 'unit': 
                self._numerator = args[0].value.numerator
                self._denominator = args[0].value.denominator
                self._unit_xml_id = args[0].value.xml_id
            else:
                raise XuleProcessingError(_("Cannot create a XuleUnit from a '{}'.".format(type(args[0]))), None)
        elif len(args) == 2:
            #In this case the first argument is a collection of numerators or a single numerator and the second is a collection of denominators or a single denominator
            nums = []
            denums = []
            
            if isinstance(args[0], XuleValue) and args[0].type in ('set', 'list'):
                for part in args[0].value:
                    sub_nums, sub_denums = self._unit_extract_parts(part)
                    nums += sub_nums
                    denums += sub_denums
            else:
                nums.append(self._unit_extract_parts(args[0])[0][0])
            
            if isinstance(args[1], XuleValue) and args[1].type in ('set', 'list'):
                for part in args[1].value:
                    sub_nums, sub_denums = self._unit_extract_parts(part)
                    nums += sub_denums
                    denums += sub_nums
            else:
                denums.append(self._unit_extract_parts(args[1])[0][0])
            
            self._numerator = sorted(nums)
            self._denominator = sorted(denums)
                        
            self._unit_cancel()
        else:
            raise XuleProcessingError(_("Cannot create a XuleUnit. Expecting 1 or 2 arguments but found {}".format(len(args))), None)
    
    def _unit_extract_parts(self, part):
        if part.type == 'unit':
            return part.value.numerator, part.value.denominator
        elif part.type == 'qname':
            return (part.value,), tuple()
        else:
            raise XuleProcessingError(_("Cannot create a unit from '{}'.".format(part.type)), None)
    
        
        
    def _unit_cancel(self):
        #need mutable structure
        num_list = list(self._numerator)
        denom_list = list(self._denominator)
         
        for n in range(len(num_list)):
            for d in range(len(denom_list)):
                if num_list[n] == denom_list[d]:
                    num_list[n] = None
                    denom_list[d] = None
        
        self._numerator = tuple(x for x in num_list if x is not None)
        self._denominator = tuple(x for x in denom_list if x is not None)                
    
    @property
    def numerator(self):
        return self._numerator
    
    @property
    def denominator(self):
        return self._denominator
    
    @property
    def xml_id(self):
        return self._unit_xml_id
    
    def __repr__(self):   
        if len(self._denominator) == 0:
            #no denominator
            return "%s" % " * ".join([x.clarkNotation for x in self._numerator])
        else:
            return "%s/%s" % (" * ".join([x.clarkNotation for x in self._numerator]), 
                                                  " * ".join([x.clarkNotation for x in self._denominator]))
    
    def __str__(self):
        if len(self._denominator) == 0:
            #no denominator
            return "%s" % " * ".join([x.localName for x in self._numerator])
        else:
            return "%s/%s" % (" * ".join([x.localName for x in self._numerator]), 
                                                  " * ".join([x.localName for x in self._denominator]))       

    def __eq__(self, other):
        return self._numerator == other._numerator and self._denominator == other._denominator

    def __hash__(self):
        return hash((self._numerator, self._denominator))

DIMENSION_TYPE = 0
DIMENSION_SUB_TYPE = 1
DIMENSION_USABLE = 2
HYPERCUBE_CLOSED = 3
_HAS_HYPERCUBE_RELATIONSHIPS = ('http://xbrl.org/int/dim/arcrole/all', 'http://xbrl.org/int/dim/arcrole/notAll')

class DimensionRelationship(ModelRelationship):
    def __init__(self, modelRelationship, dimension_set, side=None):
        self.__class__ = type(modelRelationship.__class__.__name__,
                              (self.__class__, modelRelationship.__class__),
                              {})
        self.__dict__ = modelRelationship.__dict__     
        
        self.modelRelationship = modelRelationship
        self.dimension_set = dimension_set
        self.dimension_type = None
        self.dimension_sub_type = None
        if modelRelationship.arcrole in ('http://xbrl.org/int/dim/arcrole/domain-member', 'http://xbrl.org/int/dim/arcrole/dimension-domain'):
            self.side = side
        else:
            self.side = None

    #override from and to methods
    @property
    def toModelObject(self):
        if self.arcrole in _HAS_HYPERCUBE_RELATIONSHIPS: # 'http://xbrl.org/int/dim/arcrole/all':
            return self.modelRelationship.fromModelObject
        else:
            return self.modelRelationship.toModelObject

    @property        
    def fromModelObject(self):
        if self.arcrole in _HAS_HYPERCUBE_RELATIONSHIPS: # 'http://xbrl.org/int/dim/arcrole/all':
            return self.modelRelationship.toModelObject
        else:
            return self.modelRelationship.fromModelObject
    
    @property
    def fromDimensionType(self):
        return self.dimension_set.dimensionType(self.fromModelObject)[DIMENSION_TYPE]
    
    @property
    def toDimensionType(self):
        return self.dimension_set.dimensionType(self.toModelObject)[DIMENSION_TYPE]

    @property
    def fromDimensionSubType(self):
        return self.dimension_set.dimensionType(self.fromModelObject)[DIMENSION_SUB_TYPE]
    
    @property
    def toDimensionSubType(self):
        return self.dimension_set.dimensionType(self.toModelObject)[DIMENSION_SUB_TYPE]    

class XuleDimensionCube:
    """This class represents an XBRL cube.
    
    The main purpose of the dimension relationship set is to identify all the relationships that make up a hypercube.
    """

    _consecutive_arcroles = {'http://xbrl.org/int/dim/arcrole/all': 'http://xbrl.org/int/dim/arcrole/hypercube-dimension',
                            'http://xbrl.org/int/dim/arcrole/notAll': 'http://xbrl.org/int/dim/arcrole/hypercube-dimension',
                            'http://xbrl.org/int/dim/arcrole/hypercube-dimension': 'http://xbrl.org/int/dim/arcrole/dimension-domain',
                            'http://xbrl.org/int/dim/arcrole/dimension-domain': 'http://xbrl.org/int/dim/arcrole/domain-member',
                            'http://xbrl.org/int/dim/arcrole/domain-member': 'http://xbrl.org/int/dim/arcrole/domain-member'}

    DIMENSION_SET_ROLE = 0
    DIMENSION_SET_HYPERCUBE = 1

    @classmethod
    def base_dimension_sets(cls, dts):
        cls._establish_dimension_base_sets(dts)
        return dts.xuleBaseDimensionSets

    @classmethod
    def dimension_sets(cls, dts):
        cls._establish_cubes(dts)
        return dts.xuleDimensionSets

    @classmethod
    def dimension_defaults(cls, dts):
        cls._establish_dimension_defaults(dts)
        return dts.xuleDimensionDefaults

    @classmethod
    def dimension_defaults_by_name(cls, dts):
        cls._establish_dimension_defaults(dts)
        return {k.qname: v.qname for k, v in dts.xuleDimensionDefaults.items()}

    @classmethod
    def _establish_cubes(cls, dts):
        cls._establish_dimension_base_sets(dts)
        # Establish the dimension sets dictionary for the dts
        if not hasattr(dts, 'xuleDimensionSets'):
            dts.xuleDimensionSets = dict()

    @classmethod
    def _establish_dimension_base_sets(cls, dts):
        if not hasattr(dts, 'xuleBaseDimensionSets'):
            dts.xuleBaseDimensionSets = collections.defaultdict(set)

            for base_set in dts.baseSets:
                if (base_set[XuleProperties.NETWORK_ARCROLE] in ('http://xbrl.org/int/dim/arcrole/all',
                                                                 'http://xbrl.org/int/dim/arcrole/notAll') and
                        base_set[XuleProperties.NETWORK_ROLE] is not None and
                        base_set[XuleProperties.NETWORK_LINK] is not None and
                        base_set[XuleProperties.NETWORK_ARC] is not None):
                    # This is an 'all' dimension base set find the hypercubes
                    relationship_set = dts.relationshipSets.get(base_set,
                                                                ModelRelationshipSet(dts,
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ARCROLE],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ROLE],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_LINK],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ARC]))

                    for rel in relationship_set.modelRelationships:
                        if rel.toModelObject is not None:
                            drs_role = base_set[XuleProperties.NETWORK_ROLE]
                            dts.xuleBaseDimensionSets[(drs_role, rel.toModelObject)].add(rel)

    @classmethod
    def _establish_dimension_defaults(cls, dts):
        if not hasattr(dts, 'xuleDimensionDefaults'):
            dts.xuleDimensionDefaults = dict()

            for base_set in dts.baseSets:
                if (base_set[XuleProperties.NETWORK_ARCROLE] == 'http://xbrl.org/int/dim/arcrole/dimension-default' and
                        base_set[XuleProperties.NETWORK_ROLE] is not None and
                        base_set[XuleProperties.NETWORK_LINK] is not None and
                        base_set[XuleProperties.NETWORK_ARC] is not None):
                    relationship_set = dts.relationshipSets.get(base_set,
                                                                ModelRelationshipSet(dts,
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ARCROLE],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ROLE],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_LINK],
                                                                                     base_set[
                                                                                         XuleProperties.NETWORK_ARC]))

                    for rel in relationship_set.modelRelationships:
                        dts.xuleDimensionDefaults[rel.fromModelObject] = rel.toModelObject


    def __new__(cls, dts, drs_role_uri, hypercube, include_facts=False):
        # if (drs_role_uri, hypercube) not in cls.base_dimension_sets(dts):
        #     raise XuleProcessingError(_(
        #         "Dimension base set for drs role '{}' and hypercube '{}' does not exists.".format(drs_role, str(
        #             hypercube.qname))))
        if (drs_role_uri, hypercube) not in cls.base_dimension_sets(dts):
            return None
        # See if the cube is already created.
        new_cube = cls.dimension_sets(dts).get((drs_role_uri, hypercube))
        # If not, create an empty cube
        if new_cube is None:
            new_cube = super().__new__(cls)
            cls.dimension_sets(dts)[(drs_role_uri, hypercube)] = new_cube
        # This will cause the init to be called.
        return new_cube

    def __init__(self, dts, drs_role_uri, hypercube, include_facts=False):

        if self is not None:
            # Check if the cube is already created. If it is, do nothing, the created cube will be returned.
            if not hasattr(self, '_hypercube'):
                self._establish_dimension_defaults(dts) # Get list of dimension-defaults across all DRSs
                # Create the cube
                self.has_facts = False
                self._dts = dts
                self._drs_role_uri = drs_role_uri
                self._hypercube = hypercube
                self._from_relationships = collections.defaultdict(list)
                self._to_relationships = collections.defaultdict(list)
                #self._from_concepts = collections.defaultdict(set)
                #self._to_concepts = collections.defaultdict(set)
                self._relationships = set()
                #self._primaries = set()
                self._primaries_all = set() # primary concepts that are attached with an 'all' has-hypercube relationship
                self._primaries_not_all = set() # primary concepts that are attached with a 'notAll' has-hypercube3 relationship
                #self._root_primaries = set()
                self._root_primaries_all = set()
                self._root_primaries_not_all = set()
                self._dimensions = set()
                self._dimension_members = collections.defaultdict(set)
                self._dimension_domains = collections.defaultdict(set)
                self._dimension_default = dict()
                self._concept_types = collections.defaultdict(lambda: [None, None, None, None]) # This is a dictionary keyed by concept with a value of a list of 2 items, the dimension type and the dimension sub type

                for model_has_rel in self.base_dimension_sets(dts).get((drs_role_uri, hypercube), set()):
                    has_rel = DimensionRelationship(model_has_rel, self)
                    # Determine if this primary is an all or notAll relationship.
                    primary_all = True if model_has_rel.arcrole == 'http://xbrl.org/int/dim/arcrole/all' else False
                    if primary_all:
                        self._root_primaries_all.add(has_rel.toModelObject)
                        self._primaries_all.add(has_rel.toModelObject)
                    else:
                        self._root_primaries_not_all.add(has_rel.toModelObject)
                        self._primaries_not_all.add(has_rel.toModelObject)
                    #self._root_primaries.add(has_rel.toModelObject)
                    #self._primaries.add(has_rel.toModelObject)
                    self._relationships.add(has_rel)
                    # The xbrl direction of the 'all' relationship is from primary to hypercube, but in the xule model, the hypercube is the top, so the direction is the opposite. This is
                    # handled by the DimensionRelationship() object.
                    self._from_relationships[has_rel.fromModelObject].append(has_rel)
                    self._to_relationships[has_rel.toModelObject].append(has_rel)

                    #identify concepts
                    self._concept_types[has_rel.fromModelObject][DIMENSION_TYPE] = 'hypercube'
                    self._concept_types[has_rel.toModelObject][DIMENSION_TYPE] = 'primary-member'
                    self._concept_types[has_rel.toModelObject][DIMENSION_SUB_TYPE] = 'primary'
                    self._concept_types[has_rel.toModelObject][HYPERCUBE_CLOSED] = (self._concept_types[has_rel.toModelObject][HYPERCUBE_CLOSED] or True) and bool(has_rel.arcElement.get('{http://xbrl.org/2005/xbrldt}closed', False))
                    #traverse the primary domain-member
                    self._traverse_dimension_relationships(
                        dts, 'primary', has_rel.toModelObject, 'http://xbrl.org/int/dim/arcrole/domain-member',
                        has_rel.linkrole, has_rel.linkQname, has_rel.qname, set(),
                        primary_all=primary_all,
                        closed=has_rel.arcElement.get('{http://xbrl.org/2005/xbrldt}closed', False)
                    )
                    #traverse the dimensions
                    self._traverse_dimension_relationships(
                        dts, 'dimension', has_rel.fromModelObject,
                        'http://xbrl.org/int/dim/arcrole/hypercube-dimension', has_rel.targetRole or has_rel.linkrole,
                        has_rel.linkQname, has_rel.qname, set()
                    )

            if include_facts:
                self.add_facts()

    def _traverse_dimension_relationships(self, dts, side, parent, arcrole, role, link_name, arc_name, seen_concepts,
                                          dimension_concept=None, primary_all=None, closed=False):
        relationship_set = dts.relationshipSet(arcrole, role, link_name, arc_name)
        rels_to_process = [
            rel for rel in relationship_set.fromModelObject(parent) if rel.toModelObject not in seen_concepts
        ]
        for model_child_rel in rels_to_process:
            # Reset the seen concepts for each iteration of the dimension in the cube.
            if arcrole == 'http://xbrl.org/int/dim/arcrole/hypercube-dimension':
                seen_concepts = set()
            seen_concepts.add(model_child_rel.toModelObject)
            child_rel = DimensionRelationship(model_child_rel, self, side)
            self._from_relationships[child_rel.fromModelObject].append(child_rel)
            self._to_relationships[child_rel.toModelObject].append(child_rel)

            child_concept = child_rel.toModelObject
            if side == 'primary':
                if primary_all:
                    self._primaries_all.add(child_concept)
                else:
                    self._primaries_not_all.add(child_concept)
            else:  # 'dimension'
                if child_rel.arcrole.endswith('dimension'):
                    dimension_concept = child_concept
                    self._dimensions.add(dimension_concept)
                    # Check for dimension default.
                    self._dimension_default[dimension_concept] = dts.xuleDimensionDefaults.get(dimension_concept)
                elif child_rel.arcrole.endswith('member'):
                    self._dimension_members[dimension_concept].add(child_concept)
                elif child_rel.arcrole.endswith('domain'):
                    self._dimension_members[dimension_concept].add(child_concept)
                    self._dimension_domains[dimension_concept].add(child_concept)

            # Identify type of child concept
            if arcrole.endswith('dimension'):
                self._concept_types[child_concept][DIMENSION_TYPE] = 'dimension'
                if child_concept.isExplicitDimension:
                    self._concept_types[child_concept][DIMENSION_SUB_TYPE] = 'explicit'
                if child_concept.isTypedDimension:
                    self._concept_types[child_concept][DIMENSION_SUB_TYPE] = 'typed'
            else:  # this is a member of some kind
                if side == 'primary':
                    self._concept_types[child_concept][DIMENSION_TYPE] = 'primary-member'
                    # This handles the odd case if a concept is both in a closed and open relationship to the
                    # hypercube, basically, the open wins.
                    self._concept_types[child_concept][HYPERCUBE_CLOSED] = closed and (
                            self._concept_types[child_concept][HYPERCUBE_CLOSED] or True
                    )
                else:
                    self._concept_types[child_concept][DIMENSION_USABLE] = child_rel.isUsable
                    self._concept_types[child_concept][DIMENSION_TYPE] = 'dimension-member'
                    if child_concept is self._dimension_default.get(dimension_concept):
                        self._concept_types[child_concept][DIMENSION_SUB_TYPE] = 'default'

            self._traverse_dimension_relationships(
                dts, side, child_rel.toModelObject, self._consecutive_arcroles[arcrole],
                child_rel.targetRole or role, link_name, arc_name, seen_concepts,
                dimension_concept=dimension_concept,
                primary_all=primary_all,
                closed=closed
            )

    def add_facts(self):
        """This method adds facts to the cube

        :rtype: None
        """
        if self.has_facts:
            return # The facts are already here

        if not hasattr(self._dts, 'xuleFactIndex'):
            # This dts has not been indexed. For now will treat as if there are no facts. But probably should
            # consider building the fact index for the DTS
            return

        # get all facts for the concepts in the cube
        self._facts_all = self._find_facts(self._primaries_all)
        self._facts_not_all = self._find_facts(self._primaries_not_all)

        self.has_facts = True

    def _find_facts(self, primaries):

        facts = set()
        for concept in primaries:
            if concept.qname in self._dts.xuleFactIndex[('builtin', 'concept')]:
                facts |= self._dts.xuleFactIndex[('builtin', 'concept')][concept.qname]

        # Dimensions
        for dimension_concept in self._dimensions:
            if len(facts) > 0: # If there are no facts, then the facts for the dimension does not need to be checked.
                dimension_index_key = ('explicit_dimension', dimension_concept.qname)
                if dimension_concept.isTypedDimension:
                    # For typed dimensions all the facts will match
                    dimension_facts = set()
                    for type_member in self._dts.xuleFactIndex.get(dimension_index_key, dict()).keys():
                        if type_member is not None:
                            dimension_facts |= self._dts.xuleFactIndex.get(dimension_index_key, dict()).get(type_member, set())
                    #dimension_facts = self._dts.xuleFactIndex.get(dimension_index_key, dict()).get('all', set())
                else:
                    dimension_facts = set()
                    for dimension_member in self._dimension_members[dimension_concept]:
                        if self.isUsable(dimension_member):
                            dimension_facts |= self._dts.xuleFactIndex.get(dimension_index_key, dict()).get(dimension_member.qname, set())
                    # default member
                    default_member = self._dimension_default.get(dimension_concept)
                    if default_member in self._dimension_members[dimension_concept] and self.isUsable(default_member):
                        # Note the defaults on the get(). The first one for dimension_index_key returns an empty
                        # dictionary. This happens when the dimension is not in the fact index which happens when
                        # there are no facts that use this dimension. In this case, all  the facts match the default
                        # for the dimension. This is in the second get() for the None value of the dimension. The None
                        # value of the dimension represents all facts that do not have the dimension explicitly. The
                        # 'all' on the fact index is used in this case. The 'all' is every fact in the instance. If the
                        # dimension is not used in the instance at all, then the first get() returns an empty dict. The
                        # second get() will not find a key of None (since the dict is empty) and will return all facts.
                        dimension_facts |= self._dts.xuleFactIndex.get(dimension_index_key, dict()).get(None, self._dts.xuleFactIndex.get('all', set()))

                facts &= dimension_facts

        # Check facts for closed/open cubes
        closed_facts = set()
        dimension_qnames = {x.qname for x in self._dimensions}
        for fact in facts:
            if self._concept_types[fact.concept][HYPERCUBE_CLOSED]:
                if len(fact.context.qnameDims.keys() - dimension_qnames) > 0:
                    # This fact has dimension that are not part of the cube
                    closed_facts.add(fact)
        #remove closed facts
        facts -= closed_facts

        return facts

    def __str__(self):
        output = str(self._hypercube.qname) + ' - ' + self.drs_role.roleURI + ' - ' + (XuleUtility.role_uri_to_model_role(self._dts, self._drs_role_uri).definition or "") + '\n'
        # Stats
        output += '\tNumber of dimenions: ' + str(len(self._dimensions)) + '\n'
        output += '\tNumber of primaries: ' + str(len(self._primaries_all | self._primaries_not_all)) + '\n'
        if self.has_facts:
            output += '\tNumber of facts: ' + str(len(getattr(self, 'facts', tuple()))) + '\n'
        else:
            output += '\tFacts have not been added to the cube\n'
        # Primaries
        output += '\tPrimary Concepts:\n'
        for prim in self._primaries_all | self._primaries_not_all:
            output += '\t\t' + str(prim.qname)
            if prim in self._primaries_all:
                output += ' (all)'
            else:
                output += ' (not all)'
            if self._concept_types[prim][HYPERCUBE_CLOSED] or False:
                output += ' (Closed)'
            else:
                output += ' (Open)'
            if prim in self._root_primaries_all:
                output += ' (ROOT PRIMARY)'
            output += '\n'
        # Dimensions
        for dim in self._dimensions:
            # Add a tab to each of the lines
            output += textwrap.indent(XuleDimensionDimension(self, dim).dimension_str, '\t')


        """
        # Facts
        if self.has_facts:
            output += '\tFacts:\n'
            for fact in self.facts:
                output += '\t\t' + str(fact) + '\n'
        """
        return output

    @property
    def drs_role(self):
        return XuleUtility.role_uri_to_model_role(self._dts, self._drs_role_uri)

    @property
    def hypercube(self):
        return self._hypercube

    @property
    def dimensions(self):
        return {XuleDimensionDimension(self, x) for x in self._dimensions}

    @property
    def primaries(self):
        return self._primaries_all | self._primaries_not_all

    def dimension_default(self, dim_concept):
        self._establish_dimension_defaults(self._dts)
        return self._dts.xuleDimensionDefaults.get(dim_concept)

    def dimension_members(self, dim_concept):
        return self._dimension_members.get(dim_concept, set())

    def dimension_domains(self, dim_concept):
        return self._dimension_domains.get(dim_concept, set())

    @property
    def facts(self):
        if getattr(self, 'has_facts', False): # This prevents differences when debugging. See note below
            if not hasattr(self, '_facts'):
                facts = getattr(self, '_facts_all', set())
                if len(facts) > 0: # This only needs to be done if there are facts to eliminate
                    # Need to eliminate facts in negative cubes within the same drs
                    for base_dimension in self.base_dimension_sets(self._dts):
                        if base_dimension[0] == self.drs_role.roleURI: # This cube is in the same drs
                            facts -= getattr(XuleDimensionCube(self._dts, *base_dimension, include_facts=True), '_facts_not_all', set())
                self._facts = facts

            return self._facts
        else:
            # The check on self having has_facts strickly speaking is not needed. However, when debugging and
            # breaking at a point before the facts are gather and assigned to self._facts, the debugger
            # runs this property. When this happens, this will return None and not try to gather the facts from
            # self._facts_all and self._facts_not_all which may not have been populated yet. This prevents differences
            # when running in the debugger and breaking vs just running.
            return None

    def fromModelObject(self, concept):
        return self._from_relationships.get(concept, [])

    @property
    def fromModelObjects(self):
        return set(x for x in self._from_relationships.values())

    def toModelObject(self, concept):
        return self._to_relationships.get(concept, [])
    
    @property
    def toModelObjects(self):
        return set(x for x in self._to_relationships.values())
    
#     def modelRelationships(self):
#         return self._relationships
    
    @property
    def rootConcepts(self):
        return [self._hypercube,]
    
    def dimensionType(self, concept):
        return self._concept_types.get(concept)

    def isUsable(self, concept):
        return self._concept_types[concept][DIMENSION_USABLE]

class XuleDimensionDimension:
    def __init__(self, cube, dimension_concept):
        self.cube = cube
        self.dimension_concept = dimension_concept

    @property
    def default(self):
        return self.cube.dimension_default(self.dimension_concept)

    @property
    def members(self):
        return self.cube.dimension_members(self.dimension_concept)

    @property
    def domains(self):
        return self.cube.dimension_domains(self.dimension_concept)

    @property
    def dimension_type(self):
        return self.cube.dimensionType(self.dimension_concept)

    @property
    def dimension_str(self):
        """converts dimensions into a string"""
        output = str(self.dimension_concept.qname) + ' (DIMENSION) \n'
        output += self.member_str
        return output

    @property
    def member_str(self):
        output = ''
        for mem in self.members:
            output += str(mem.qname)
            if mem in self.domains:
                output += ' (DOMAIN)'
            if mem is self.default:
                output += ' (DEFAULT)'
            output += '\n'
        return output

    def __str__(self):
        dim_string = 'Dimension: {dim_name}\n' \
                     'Cube: {cube_name}\n' \
                     'DRS Role: {drs_role}'.format(dim_name=self.dimension_concept.qname,
                                                   cube_name=self.cube.hypercube.qname,
                                                   drs_role=self.cube.drs_role.roleURI)
        dim_string += '\nMembers:\n'
        dim_string += textwrap.indent(self.member_str, '\t')
        return dim_string

def model_to_xule_unit(model_unit, xule_context):
    return XuleUnit(model_unit)

#     numerator = tuple(sorted(model_unit.measures[0]))
#     denominator = tuple(sorted(model_unit_measures[1]))
#     
#     model_unit = (numerator, denominator)
#     
#     #this is done to force the unit to be normalized. This will convert something like USD/pure to just USD.
#     normalized_unit = unit_multiply(model_unit, ((XBRL_PURE,),()))
#     
#     return normalized_unit

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

# def unit_multiply(left_unit, right_unit):
#     
#     left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
#     left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
#                   
#     right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
#     right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
#     
#     #new nuemrator and denominator before (pre) canceling
#     new_num_pre = tuple(sorted(left_num + right_num))
#     new_denom_pre = tuple(sorted(left_denom + right_denom))
#     
#     new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
#     
#     if len(new_num) == 0:
#         new_num = (XBRL_PURE,)   
#     
#     return (new_num, new_denom)
# 
# def unit_cancel(left, right):
#     #need mutable structure
#     left_list = list(left)
#     right_list = list(right)
#     
#     for l in range(len(left_list)):
#         for r in range(len(right_list)):
#             if left_list[l] == right_list[r]:
#                 left_list[l] = None
#                 right_list[r] = None
#     
#     return tuple(x for x in left_list if x is not None), tuple(x for x in right_list if x is not None)
#     
# def unit_divide(left_unit, right_unit):
#     
#     left_num = tuple(x for x in left_unit[0] if x != XBRL_PURE)
#     left_denom = tuple(x for x in left_unit[1] if x != XBRL_PURE)
#                   
#     right_num = tuple(x for x in right_unit[0] if x != XBRL_PURE)
#     right_denom = tuple(x for x in right_unit[1] if x != XBRL_PURE)
#     
#     #new nuemrator and denominator before (pre) canceling
#     new_num_pre = tuple(sorted(left_num + right_denom))
#     new_denom_pre = tuple(sorted(left_denom + right_num))
#     
#     new_num, new_denom = unit_cancel(new_num_pre, new_denom_pre)
#     
#     if len(new_num) == 0:
#         new_num = (XBRL_PURE,)   
#     
#     return (new_num, new_denom)

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
                       type(None): 'none',
                       InvalidValue: 'unbound',
                       ModelFact: 'fact',
                       datetime.datetime: 'instant',
                       datetime.date: 'instant',
                       DateTime: 'model_date_time',
                       IsoDuration: 'iso_duration',
                       gYear: 'model_g_year',
                       gMonthDay: 'model_g_month_day',
                       gYearMonth: 'model_g_year_month',
                       AnyURI: 'uri',
                       Fraction: 'fraction'}

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
            frozenset(['qname', 'unit']): [('unit', lambda x: XuleUnit(x))],
            frozenset(['instant', 'time-period']): [('instant', lambda x:x)]
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

def system_collection_to_xule(col, xule_context):
    """Convert a python dictionary or list to xule value
    
    :param col: native collection
    :type col: collectin (dict or list)
    :param xule_context: The rule context
    :type xule_context: XuleRuleContext
    :returns: A XuleValue of the the collection
    :rtype: XuleValue
        
    """
    if isinstance(col, dict):
        return system_dict_to_xule(col, xule_context)
    elif isinstance(col, list):
        return system_list_to_xule(col, xule_context)
    else:
        raise XuleProcessingError(_("Cannot convert native type {} into a XuleValue collection.".format(type(col))), xule_context )

def system_dict_to_xule(col, xule_context):
    result = dict()
    shadow = dict()
    for n, v in col.items():
        xule_name = XuleValue(xule_context, n, 'string')
        if isinstance(v, dict) or isinstance(v, list) or isinstance(v, set):
            xule_value = system_collection_to_xule(v, xule_context)
        else:
            xule_type, compute_value = model_to_xule_type(xule_context, v)
            xule_value = XuleValue(xule_context, compute_value, xule_type)
        result[xule_name] = xule_value
        shadow[n] = xule_value.shadow_collection if xule_value.type in ('set', 'list', 'dictionary') else xule_value.value

    return XuleValue(xule_context, frozenset(result.items()), 'dictionary', shadow_collection=frozenset(shadow.items()))

def system_list_to_xule(col, xule_context):
    result = list()
    shadow = list()
    for v in col:
        if isinstance(v, dict) or isinstance(v, list) or isinstance(v, set):
            xule_value = system_collection_to_xule(v, xule_context)
        else:
            xule_type, compute_value = model_to_xule_type(xule_context, v)
            xule_value = XuleValue(xule_context, compute_value, xule_type)
        result.append(xule_value)
        shadow.append(xule_value.shadow_collection if xule_value.type in ('set', 'list', 'dictionary') else xule_value.value)
    
    return XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(shadow))

DEFAULT_VALUES_BY_TYPE = {'int': 0,
                          'float': 0.0,
                          'decimal': decimal.Decimal(0),
                          'list': tuple(),
                          'set': frozenset(set()),
                          'string': ''}

def default_value_by_type(system_type):
    return DEFAULT_VALUES_BY_TYPE.get(system_type, None)