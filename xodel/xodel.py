'''
Reivision number: $Change: 23365 $
'''

from arelle import FileSource
from arelle import ModelManager
from arelle.ModelXbrl import ModelXbrl
from .arelleHelper import *
from .xodelXuleExtensions import property_to_xodel
from .XodelVars import get_arelle_model
from .XodelException import XodelException

import base64
import collections
import copy
import datetime
import decimal
import io
import isodate
import json
import logging
from lxml import etree as et
import optparse
import os
import re
import string
import tempfile
from typing import Dict

# XINCE Constants
_XBRLI_NAMESPACE = 'http://www.xbrl.org/2003/instance'
_LINK_NAMESPACE = 'http://www.xbrl.org/2003/linkbase'
_XLINK_NAMESPACE = 'http://www.w3.org/1999/xlink'
_LINKROLE_REGISTRY_URI = 'http://www.xbrl.org/lrr/lrr.xml'
_LINKROLE_REGISTRY = None
_LINKROLE_REGISTRY_NAMESPACE = 'http://www.xbrl.org/2005/lrr'
_DIMENSION_NAMESPACE = 'http://xbrl.org/2006/xbrldi'
_INSTANCE_OUTPUT_ATTRIBUTES = {'instance-name', 'instance-taxonomy'}
_FACT_OUTPUT_ATTRIBUTES = {'fact-value', 
                           'fact-concept',
                           'fact-unit',
                           'fact-entity',
                           'fact-period',
                           'fact-decimals',
                           'fact-dimensions',
                           'fact-instance',
                           'fact-alignment',
                           'fact-is-nil',
                           'fact-id',
                           'fact-footnote'
}
_INSTANCE_BASE_JSON_STRING = '''{
    "documentInfo": {
        "documentType": "https://xbrl.org/2021/xbrl-json",
        "features": {
            "xbrl:canonicalValues": true
        },
        "namespaces": {
            "iso4217": "http://www.xbrl.org/2003/iso4217",
            "utr": "http://www.xbrl.org/2009/utr",
            "xbrl": "https://xbrl.org/2021",
            "xbrli": "http://www.xbrl.org/2003/instance"
        },
        "linkGroups": {
            "_": "http://www.xbrl.org/2003/role/link"
        },
        "taxonomy": []
    },
    "facts": {}
}
'''

_INSTANCE_BASE_XML_STRING = '''<!-- Created by Xince -->
<xbrli:xbrl
  xmlns:xbrli="http://www.xbrl.org/2003/instance"
  xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:link="http://www.xbrl.org/2003/linkbase" 
  xmlns:utr="http://www.xbrl.org/2009/utr"
  xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>'''

_TAXONOMY_MODEL_START = '''
    <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:link="http://www.xbrl.org/2003/linkbase" 
                xmlns:xlink="http://www.w3.org/1999/xlink" 
                xmlns:xml="http://www.w3.org/XML/1998/namespace">
'''

_QNAME_MATCH = re.compile('^{(.+)}(.+)$')
# This unit_match will contain the numerator in group(1) and the denominator in group(4)
_UNIT_MATCH = re.compile('({[^}]+}[^{]+(\*{[^}]+}[^{]+)*)(/({[^}]+}[^{]+(\*{[^}]+}[^{]+)*))?')
_HEX_MATCH = re.compile('^[0-9a-fA-F]*$')
_G_YEAR_MONTH = re.compile('^(\d{4,})-(\d\d)$')
_G_YEAR = re.compile('^\d{4,}$')
_G_MONTH_DAY = re.compile('^--\d\d-\d\d((\+|-)\d\d:\d\d)?$')
_G_DAY = re.compile('^---\d\d((\+|-)\d\d:\d\d)?$')
_G_MONTH = re.compile('^--\d\d((\+|-)\d\d:\d\d)?$')
_LANGUAGE = re.compile('^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$')

# These are for validation of Name and NCName
_BaseChar ='[\u0041-\u005A]|[\u0061-\u007A]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u00FF]|[\u0100-\u0131]|[\u0134-\u013E]|[\u0141-\u0148]|[\u014A-\u017E]|'
'[\u0180-\u01C3]|[\u01CD-\u01F0]|[\u01F4-\u01F5]|[\u01FA-\u0217]|[\u0250-\u02A8]|[\u02BB-\u02C1]|\u0386|[\u0388-\u038A]|\u038C|[\u038E-\u03A1]|'
'[\u03A3-\u03CE]|[\u03D0-\u03D6]|\u03DA|\u03DC|\u03DE|\u03E0|[\u03E2-\u03F3]|[\u0401-\u040C]|[\u040E-\u044F]|[\u0451-\u045C]|[\u045E-\u0481]|[\u0490-\u04C4]|'
'[\u04C7-\u04C8]|[\u04CB-\u04CC]|[\u04D0-\u04EB]|[\u04EE-\u04F5]|[\u04F8-\u04F9]|[\u0531-\u0556]|\u0559|[\u0561-\u0586]|[\u05D0-\u05EA]|[\u05F0-\u05F2]|[\u0621-\u063A]|'
'[\u0641-\u064A]|[\u0671-\u06B7]|[\u06BA-\u06BE]|[\u06C0-\u06CE]|[\u06D0-\u06D3]|\u06D5|[\u06E5-\u06E6]|[\u0905-\u0939]|\u093D|[\u0958-\u0961]|[\u0985-\u098C]|[\u098F-\u0990]|'
'[\u0993-\u09A8]|[\u09AA-\u09B0]|\u09B2|[\u09B6-\u09B9]|[\u09DC-\u09DD]|[\u09DF-\u09E1]|[\u09F0-\u09F1]|[\u0A05-\u0A0A]|[\u0A0F-\u0A10]|[\u0A13-\u0A28]|[\u0A2A-\u0A30]|[\u0A32-\u0A33]|'
'[\u0A35-\u0A36]|[\u0A38-\u0A39]|[\u0A59-\u0A5C]|\u0A5E|[\u0A72-\u0A74]|[\u0A85-\u0A8B]|\u0A8D|[\u0A8F-\u0A91]|[\u0A93-\u0AA8]|[\u0AAA-\u0AB0]|[\u0AB2-\u0AB3]|[\u0AB5-\u0AB9]|\u0ABD|\u0AE0|'
'[\u0B05-\u0B0C]|[\u0B0F-\u0B10]|[\u0B13-\u0B28]|[\u0B2A-\u0B30]|[\u0B32-\u0B33]|[\u0B36-\u0B39]|\u0B3D|[\u0B5C-\u0B5D]|[\u0B5F-\u0B61]|[\u0B85-\u0B8A]|[\u0B8E-\u0B90]|[\u0B92-\u0B95]|[\u0B99-\u0B9A]|'
'\u0B9C|[\u0B9E-\u0B9F]|[\u0BA3-\u0BA4]|[\u0BA8-\u0BAA]|[\u0BAE-\u0BB5]|[\u0BB7-\u0BB9]|[\u0C05-\u0C0C]|[\u0C0E-\u0C10]|[\u0C12-\u0C28]|[\u0C2A-\u0C33]|[\u0C35-\u0C39]|[\u0C60-\u0C61]|[\u0C85-\u0C8C]|'
'[\u0C8E-\u0C90]|[\u0C92-\u0CA8]|[\u0CAA-\u0CB3]|[\u0CB5-\u0CB9]|\u0CDE|[\u0CE0-\u0CE1]|[\u0D05-\u0D0C]|[\u0D0E-\u0D10]|[\u0D12-\u0D28]|[\u0D2A-\u0D39]|[\u0D60-\u0D61]|[\u0E01-\u0E2E]|\u0E30|'
'[\u0E32-\u0E33]|[\u0E40-\u0E45]|[\u0E81-\u0E82]|\u0E84|[\u0E87-\u0E88]|\u0E8A|\u0E8D|[\u0E94-\u0E97]|[\u0E99-\u0E9F]|[\u0EA1-\u0EA3]|\u0EA5|\u0EA7|[\u0EAA-\u0EAB]|[\u0EAD-\u0EAE]|\u0EB0|'
'[\u0EB2-\u0EB3]|\u0EBD|[\u0EC0-\u0EC4]|[\u0F40-\u0F47]|[\u0F49-\u0F69]|[\u10A0-\u10C5]|[\u10D0-\u10F6]|\u1100|[\u1102-\u1103]|[\u1105-\u1107]|\u1109|[\u110B-\u110C]|[\u110E-\u1112]|'
'\u113C|\u113E|\u1140|\u114C|\u114E|\u1150|[\u1154-\u1155]|\u1159|[\u115F-\u1161]|\u1163|\u1165|\u1167|\u1169|[\u116D-\u116E]|[\u1172-\u1173]|\u1175|\u119E|\u11A8|\u11AB|[\u11AE-\u11AF]|'
'[\u11B7-\u11B8]|\u11BA|[\u11BC-\u11C2]|\u11EB|\u11F0|\u11F9|[\u1E00-\u1E9B]|[\u1EA0-\u1EF9]|[\u1F00-\u1F15]|[\u1F18-\u1F1D]|[\u1F20-\u1F45]|[\u1F48-\u1F4D]|[\u1F50-\u1F57]|\u1F59|\u1F5B|\u1F5D|'
'[\u1F5F-\u1F7D]|[\u1F80-\u1FB4]|[\u1FB6-\u1FBC]|\u1FBE|[\u1FC2-\u1FC4]|[\u1FC6-\u1FCC]|[\u1FD0-\u1FD3]|[\u1FD6-\u1FDB]|[\u1FE0-\u1FEC]|[\u1FF2-\u1FF4]|[\u1FF6-\u1FFC]|\u2126|[\u212A-\u212B]|\u212E|'
'[\u2180-\u2182]|[\u3041-\u3094]|[\u30A1-\u30FA]|[\u3105-\u312C]|[\uAC00-\uD7A3]'
_Ideographic = '[\u4E00-\u9FA5]|\u3007|[\u3021-\u3029]'
_CombiningChar = '[\u0300-\u0345]|[\u0360-\u0361]|[\u0483-\u0486]|[\u0591-\u05A1]|[\u05A3-\u05B9]|[\u05BB-\u05BD]|\u05BF|[\u05C1-\u05C2]|\u05C4|[\u064B-\u0652]|'
'\u0670|[\u06D6-\u06DC]|[\u06DD-\u06DF]|[\u06E0-\u06E4]|[\u06E7-\u06E8]|[\u06EA-\u06ED]|[\u0901-\u0903]|\u093C|[\u093E-\u094C]|\u094D|'
'[\u0951-\u0954]|[\u0962-\u0963]|[\u0981-\u0983]|\u09BC|\u09BE|\u09BF|[\u09C0-\u09C4]|[\u09C7-\u09C8]|[\u09CB-\u09CD]|\u09D7|[\u09E2-\u09E3]|'
'\u0A02|\u0A3C|\u0A3E|\u0A3F|[\u0A40-\u0A42]|[\u0A47-\u0A48]|[\u0A4B-\u0A4D]|[\u0A70-\u0A71]|[\u0A81-\u0A83]|\u0ABC|[\u0ABE-\u0AC5]|'
'[\u0AC7-\u0AC9]|[\u0ACB-\u0ACD]|[\u0B01-\u0B03]|\u0B3C|[\u0B3E-\u0B43]|[\u0B47-\u0B48]|[\u0B4B-\u0B4D]|[\u0B56-\u0B57]|[\u0B82-\u0B83]|'
'[\u0BBE-\u0BC2]|[\u0BC6-\u0BC8]|[\u0BCA-\u0BCD]|\u0BD7|[\u0C01-\u0C03]|[\u0C3E-\u0C44]|[\u0C46-\u0C48]|[\u0C4A-\u0C4D]|[\u0C55-\u0C56]|'
'[\u0C82-\u0C83]|[\u0CBE-\u0CC4]|[\u0CC6-\u0CC8]|[\u0CCA-\u0CCD]|[\u0CD5-\u0CD6]|[\u0D02-\u0D03]|[\u0D3E-\u0D43]|[\u0D46-\u0D48]|[\u0D4A-\u0D4D]|'
'\u0D57|\u0E31|[\u0E34-\u0E3A]|[\u0E47-\u0E4E]|\u0EB1|[\u0EB4-\u0EB9]|[\u0EBB-\u0EBC]|[\u0EC8-\u0ECD]|[\u0F18-\u0F19]|\u0F35|\u0F37|\u0F39|'
'\u0F3E|\u0F3F|[\u0F71-\u0F84]|[\u0F86-\u0F8B]|[\u0F90-\u0F95]|\u0F97|[\u0F99-\u0FAD]|[\u0FB1-\u0FB7]|\u0FB9|[\u20D0-\u20DC]|\u20E1|'
'[\u302A-\u302F]|\u3099|\u309A'
_Digit = '[\u0030-\u0039]|[\u0660-\u0669]|[\u06F0-\u06F9]|[\u0966-\u096F]|[\u09E6-\u09EF]|[\u0A66-\u0A6F]|[\u0AE6-\u0AEF]|[\u0B66-\u0B6F]|[\u0BE7-\u0BEF]|'
'[\u0C66-\u0C6F]|[\u0CE6-\u0CEF]|[\u0D66-\u0D6F]|[\u0E50-\u0E59]|[\u0ED0-\u0ED9]|[\u0F20-\u0F29]'
_Extender ='\u00B7|\u02D0|\u02D1|\u0387|\u0640|\u0E46|\u0EC6|\u3005|[\u3031-\u3035]|[\u309D-\u309E]|[\u30FC-\u30FE]'
_Letter	=	f'{_BaseChar}|{_Ideographic}'

_NameChar = f"{_Letter}|{_Digit}|\.|-|_|:|{_CombiningChar}|{_Extender}"
_Name = f"^({_Letter}|_|:)({_NameChar})*$"
_NAME_MATCH = re.compile(_Name)

_NCNameChar = f"{_Letter}|{_Digit}|\.|-|_|{_CombiningChar}|{_Extender}"
_NCName = f"^({_Letter}|_)({_NCNameChar})*$"
_NCNAME_MATCH = re.compile(_NCName)


_LINK_ALIASES_BY_URI = {'http://www.xbrl.org/2003/arcrole/fact-footnote': 'footnote',
                 'http://www.xbrl.org/2009/arcrole/fact-explanatoryFact': 'explanatoryFact',
                 'http://www.xbrl.org/2003/role/link': '_'}

_LINK_ALIASES_BY_ALIAS = {v.lower(): k for k, v in _LINK_ALIASES_BY_URI.items()}
_STANDARD_ROLE_ALIAS = '_'



# Starting point
def process_xodel(cntlr, options, modelXbrl):
    # register the controller (cntlr and the default model)
    global _CNTLR
    _CNTLR = cntlr
    global _ARELLE_MODEL
    _ARELLE_MODEL = modelXbrl
    from .xule.XuleProperties import add_property
    add_property('to-xodel', property_to_xodel, 0, tuple() )
    # Run Xule rules
    log_capture = run_xule(cntlr, options, modelXbrl)

    #build taxonomy model
    # buile_taxonomy_model will add the taxonomies to the XodelModelManager
    build_taxonomy_model(log_capture, options, cntlr, modelXbrl)
    from . import serializer
    serializer._OPTIONS = options
    for name, dts in XodelModelManager.get_all_models().items():
        dts.set_default_documents(name)
        serializer.write(dts, os.path.join(options.xodel_location, 'package.zip'), cntlr)

    # Find instances and facts
    instances, instance_facts = organize_instances_and_facts(log_capture, cntlr)

    for instance_name, taxonomies in instances.items():
        process_instance(instance_name, taxonomies, instance_facts[instance_name], cntlr, options)

# XULE Call
def run_xule(cntlr, options, modelXbrl):

    # Create a log handler that will capture the messages when the rules are run.
    log_capture_handler = _logCaptureHandler()
    if not options.xodel_show_xule_log:
        cntlr.logger.removeHandler(cntlr.logHandler)
    cntlr.logger.addHandler(log_capture_handler)

    # Call the xule processor to run the rules
    from .xule import __pluginInfo__ as xule_plugin_info
    call_xule_method = xule_plugin_info['Xule.callXuleProcessor']

    run_options = copy.deepcopy(options)
            
    #xule_args = getattr(run_options, 'xule_arg', []) or []
    #xule_args += list(xule_date_args)
    #setattr(run_options, 'xule_arg', xule_args)
        # Get xule rule set
    # with ts.open(catalog_item['xule-rule-set']) as rule_set_file:
    setattr(run_options, 'logRefObjectProperties', False)
    call_xule_method(cntlr, modelXbrl, options.xule_rule_set, run_options)
    
    # Remove the handler from the logger. This will stop the capture of messages
    cntlr.logger.removeHandler(log_capture_handler)
    if not options.xodel_show_xule_log:
        cntlr.logger.addHandler(cntlr.logHandler)

    return log_capture_handler.captured

class _logCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._captured = collections.defaultdict(list)

    def emit(self, record):
        self._captured[record.messageCode].append(record)
    
    @property
    def captured(self):
        return self._captured

# XINCE code
class XinceException(Exception):
    pass

class XinceNSMap:
    # Note: This class will never allow default namespaces
    def __init__(self):
        self._map_by_ns = dict()
        self._map_by_prefix = dict()
        self._last_ns_number = collections.defaultdict(int)
        self._used_ns = set()

    @property
    def map_by_namespace(self):
        return copy.copy(self._map_by_ns)

    @property
    def map_by_prefix(self):
        return copy.copy(self._map_by_prefix)

    @property
    def used_map_by_namespace(self):
        return {k: v for k, v in self._map_by_ns.items() if k in self._used_ns}
    
    @property
    def used_map_by_prefix(self):
        return {k: v for k, v in self._map_by_prefix.items() if v in self._used_ns}

    def add(self, prefix, namespace):
        if self._map_by_prefix.get(prefix) == namespace:
            return # there is nothing to do, the prefix and namespace are already in the map
        elif prefix in self._map_by_prefix or namespace in self._map_by_ns:
            raise XinceException(f"{prefix}:{namespace} are already in the XinceNSMap")
        else:
            self._map_by_ns[namespace] = prefix
            self._map_by_prefix[prefix] = namespace

    def add_or_get_namespace(self, namespace, prefix='ns'):
        if self.get_prefix(namespace) is None:
            while f"{prefix}{self._last_ns_number[prefix] if self._last_ns_number[prefix] > 0 else ''}" in self._map_by_prefix:
                self._last_ns_number[prefix] += 1
            new_prefix = f"{prefix}{self._last_ns_number[prefix] if self._last_ns_number[prefix] > 0 else ''}"
            self._map_by_ns[namespace] = new_prefix
            self._map_by_prefix[new_prefix] = namespace

        return self.get_prefix(namespace)
 
    def get_namespace(self, prefix):
        return self._map_by_prefix.get(prefix)

    def get_prefix(self, namespace):
        return self._map_by_ns.get(namespace)

    def mark_namespace_as_used(self, namespace):
        if namespace in self._map_by_ns:
            self._used_ns.add(namespace)

class XinceQname:
    def __init__(self, ns, local_name):
        self.namespace = ns
        self.local_name = local_name

    @property
    def clark(self):
        return f"{{{self.namespace}}}{self.local_name}"

    def __repr__(self):
        return self.clark

    def prefix(self, nsmap, mark=False):
        '''nsmap is a dictionary of namespaces to prefixes'''
        result = nsmap.add_or_get_namespace(self.namespace)
        if mark:
            self.mark_as_used(nsmap)
        return result

    def prefixed(self, nsmap, mark=False):
        # Return a prefixed verison of the qname
        prefix = nsmap.add_or_get_namespace(self.namespace)
        if mark:
            self.mark_as_used(nsmap)
        return f'{prefix}:{self.local_name}'

    def serialize(self, nsmap, mark=False, format='json'):
        result = f'{self.prefix(nsmap, mark)}:{self.local_name}'
        return result

    def mark_as_used(self, nsmap):
        nsmap.mark_namespace_as_used(self.namespace)

class XinceEntity:
    def __init__(self, scheme, identifier):
        self.scheme = scheme
        self.identifier = identifier

    def __repr__(self):
        return self.serialize()

class XinceUnit:
    def __init__(self, numerators, denominators):
        '''numerators and denominators must be lists of XinceQnames'''
        if not (isinstance(numerators, list) and all((isinstance(x, XinceQname) for x in numerators))):
            raise XinceException("Numerators must be XinceQnames")
        if denominators is not None and not(isinstance(denominators, list) and all((isinstance(x, XinceQname) for x in denominators))):
            raise XinceException("Denominators must be XinceQnames")

        self.numerators = numerators
        self.denominators = denominators

    @property
    def is_pure(self):
        return self.denominators is None and len(self.numerators) == 1 and self.numerators[0].clark == '{http://www.xbrl.org/2003/instance}pure'

    def serialize(self, nsmap, format='json', instance_name=None):
        if format == 'json':
            result = None
            if format == 'json':
                result = '*'.join((x.serialize(nsmap, mark=True) for x in self.numerators))
                if self.denominators is not None:
                    result += '/' + '*'.join((x.serialize(nsmap, mark=True)) for x in self.denominators)

            return result
        elif format == 'xml':
            if instance_name is None:
                raise XinceException(f'Serializing an XML unit requires an instance name')
            unit_id = next(IDGenerator.get_id_generator(instance_name, self.numerators[0].local_name.lower()))
            unit_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}unit')
            unit_node.set('id', unit_id)
            if self.denominators is None:
                for num in self.numerators:
                    measure_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}measure')
                    measure_node.text = num.prefixed(nsmap, mark=True)
                    unit_node.append(measure_node)
            else: # there are denominators
                if len(self.numerators) == 0:
                    raise XinceException(f'Unit has no numerators')
                if len(self.numerators) != 1:
                    raise XinceException(f'Unit has more than one numerator and a denonminator. This cannot be serialized in XML')
                divide_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}divide')
                unit_node.append(divide_node)
                num_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}unitNumerator')
                num_mes_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}measure')
                num_mes_node.text = self.numerators[0].prefixed(nsmap, mark=True)
                num_node.append(num_mes_node)
                divide_node.append(num_node)
                den_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}unitDenominator')
                den_mes_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}measure')
                den_mes_node.text = self.denominators[0].prefixed(nsmap, mark=True)
                den_node.append(den_mes_node)
                divide_node.append(den_node)
            return unit_node
        else:
            raise XinceException(f'Trying to serialize a XinceUnit, but unknown format of "{format}" found')

    def __repr__(self):
        result = '*'.join((x.clark for x in sorted(self.numerators)))
        if self.denominators is not None:
            result += '/' + '*'.join((x.clark for x in sorted(self.denominators))) 
        return result

class XincePeriod:
    def __init__(self, start=None, end=None):
        '''If there is only a start, it is an instance. If both start and end it is a duration. If neither start or end it is forever'''
        if start is not None:
            if not isinstance(start, datetime.datetime):
                raise XinceException(f"Start date for a period must be a datetime, found {type(start).__name__}")
        if end is not None:
            if not isinstance(end, datetime.datetime):
                raise XinceException(f"End date for a period must be a datetime, found {type(end).__name__}")
        self._start = start
        self._end = end
    
    @property
    def is_instance(self):
        return self._start is not None and self._end is None

    @property
    def is_duration(self):
        return not self.is_instance

    @property
    def is_forever(self):
        return self._start is None and self._end is None
    
    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    def serialize(self, format='json'):
        result = None
        if format == 'json':
            if self.is_instance:
                result = self._start.isoformat()
            elif self.is_forever:
                result = None
            else: # non forever duration
                result = f'{self._start.isoformat()}/{self._end.isoformat()}'
        
        return result

    def __repr__(self):
        return self.serialize()

class IDGenerator:
    _used_ids = collections.defaultdict(set)
    _last_values = collections.defaultdict(int) # this will default the initial value to 0
    _generators = dict()

    @classmethod
    def get_id_generator(cls, inst_name, prefix='f'):
        if (inst_name, prefix) not in cls._generators:
            def id_generator():
                while True:
                    if cls._last_values[(inst_name, prefix)] == 0:
                        # The first time, the id will just be the prefix.
                        next_id = prefix
                    else:
                        next_id =f'{prefix}{cls._last_values[(inst_name, prefix)]}'
                    if next_id not in cls._used_ids[inst_name]:
                        # make sure there isn't already an id created that is the same. This can happen if the prefix ends with a number. ie
                        cls._used_ids[inst_name].add(next_id)
                        yield(next_id)
                    cls._last_values[(inst_name, prefix)] += 1
            cls._generators[(inst_name, prefix)] = id_generator()

        return cls._generators[(inst_name, prefix)]

def organize_instances_and_facts(log_capture, cntlr):
    '''Arrange the captured log into instances
    
    The return is a dictionary of instances keyed by name and the value is the list of taxonomies for the instance,
    and a dictionary of facts keyed by instance name and the value is a list of the captured log entries that
    belong to that instance'''
    instances = collections.defaultdict(list)
    instance_facts = collections.defaultdict(list)
    footnotes = collections.defaultdict(dict) # dictionary of footnotes by instance
    fact_footnotes = collections.defaultdict(dict) # 
    issues = []

    for rule_name, log_recs in log_capture.items():
        for log_rec in log_recs:
            inst_keys = set(log_rec.args.keys()).intersection(_INSTANCE_OUTPUT_ATTRIBUTES)
            fact_keys = set(log_rec.args.keys()).intersection(_FACT_OUTPUT_ATTRIBUTES)
            # rules creating instances = add to the instances dictionary
            if len(inst_keys) > 0: 
                # This record creates an instance documents
                # There must be an instance-name and an instance-taxonomy
                good = True
                if 'instance-name' not in inst_keys:
                    issues.append(f"A rule that creates an instance must have an 'instance-name' output attribute. Error found in rule {rule_name}")
                    good = False
                if 'instance-taxonomy' not in inst_keys:
                    issues.append(f"A rule that creates an instance must have an 'instance-taxonomy' output attribute. Error found in rule{rule_name})")
                    good = False
                if good:
                    try: # the instance-taxonomy may be a a list (as a json array) or a string of a single uri
                        taxonomies = json.loads(log_rec.args['instance-taxonomy'])
                    except json.decoder.JSONDecodeError:
                        # a regular string will cause this error, so this must be simple string oa single uri
                        taxonomies = [log_rec.args['instance-taxonomy'],]

                    if type(taxonomies) not in (str, list):
                        issues.append(f"instance-taxonomies must be a single uri indicating the schema reference or a list of uris. Error found in rule {rule_name}")
                    else:
                        if log_rec.args['instance-name'] in instances:
                            issues.append(f"There is more than one instance rule for {log_rec.args['instance-name']}. Found in rule {rule_name}")
                        if isinstance(taxonomies, str):
                            taxonomies = [taxonomies,]
                        instances[log_rec.args['instance-name']] = taxonomies

            # rules creating facts. Add to the instance_facts dictionary
            if len(fact_keys) > 0:
                # There must be a fact-instance. Other problems like missing concept name will be checked when creating the fact.
                if 'fact-instance' not in fact_keys:
                    issues.append(f"A rule that creates a fact must have a 'fact-instance' output attribute. Error found in rule {rule_name}")
                else:
                    fact_info = {k: v for k, v in log_rec.args.items() if k in fact_keys} | {'message': log_rec.msg, 'rule-name': rule_name}# just take the fact output attributes
                    # Assign fact_id - this will prevent duplicate fact ids
                    if 'fact-id' in log_rec.args:
                        next_id = next(IDGenerator.get_id_generator(log_rec.args['fact-instance'], ''.join(log_rec.args['fact-id'].split())))
                    else:
                        next_id = next(IDGenerator.get_id_generator(log_rec.args['fact-instance']))
                    fact_info['fact-id'] = next_id
                    instance_facts[log_rec.args['fact-instance']].append(fact_info)

                    # organize footnotes
                    if 'fact-footnote' in fact_keys:
                        footnotes = json.loads(log_rec.args['fact-footnote'])
                        if not isinstance(footnotes, list):
                            issues.append(f'The fact-footnote must be a list, found "{type(footnote).__name__}". Error found in rule {rule_name}')
                        # else:
                        #     for footnote in footnotes:
                        #         # a footnote is a dictionary
                        #         if not isinstance(footnote, dict):
                        #             issues.append(f'The footnote in a fact-footnote must be a dictionary, found "{type(footnote).__name__}". Error found in rule { rule_name}')
                        #             continue
                        #         if 'content' in footnote:
                        #             footnote_id = next(IDGenerator.get_id_generator(log_rec.args['fact-instance'], 'fn'))
                        #             footnotes[log_rec.args['fact-instance']][footnote_id] = footnote

                    
    # Check that there are not facts for an instance that was not created with an instance rule.
    fact_bad_instances = set(instance_facts.keys()) - set(instances.keys())
    for  bad_instance in fact_bad_instances:
        issues.append(f"There are {len(instance_facts[bad_instance])} facts in instance {bad_instance} but there is not a rule defining this instance")

    # Check if a fact is related to another fact (as a fact footnote) that the other fact exists
    for instance_name, facts in instance_facts.items():
        fact_ids = {x['fact-id'] for x in facts}
        for fact in facts:
            if 'fact-footnote' in fact:
                for footnote in json.loads(fact['fact-footnote']):
                    if 'fact-id' in footnote:
                        if footnote['fact-id'] not in fact_ids:
                            issues.append(f"A fact is pointing to another fact (fact footnote) with ID {footnote['fact-id']} but the fact footnote does not existing in the {instance_name} instance")

    for message in issues:
        cntlr.addToLog(message, 'XinceError', level=logging.ERROR)

    return instances, instance_facts

def process_instance(instance_name, taxonomies, facts, cntlr, options):

    used_footnotes, fact_footnotes = organize_footnotes(instance_name, facts, cntlr)

    if options.xodel_file_type == 'json':
        process_json(instance_name, taxonomies, facts, used_footnotes, fact_footnotes, cntlr, options)
    else:
        process_xml(instance_name, taxonomies, facts, used_footnotes, fact_footnotes, cntlr, options)

def organize_footnotes(instance_name, facts, cntlr):
    '''This fucntion dedups the footnotes and assigns footnote ids'''
    used_footnotes = dict()
    fact_footnotes = collections.defaultdict(list)

    for fact in facts:
        if 'fact-footnote' in fact:
            footnotes = json.loads(fact['fact-footnote'])
            if not isinstance(footnotes, list) and not (isinstance(footnotes, dict)):
                cntlr.addToLog(f"fact-footnote is not in the right format. Found in rule {fact['ruile-name']}", "XinceError", level=logging.ERROR)
                continue
            if isinstance(footnotes, dict):
                footnotes = (footnotes,)
            for footnote in footnotes:
                if not isinstance(footnote, dict):
                    cntlr.addToLog(f"footnotd of a fact-footnote is not in the right format. Found in rule {fact['ruile-name']}", "XinceError", level=logging.ERROR)
                    continue
                
                hash = footnote_hash(footnote, fact['rule-name'], cntlr)
                if hash is None:
                    continue
                fact_footnotes[fact['fact-id']].append(hash)
                if hash not in used_footnotes:
                    footnote_id = next(IDGenerator.get_id_generator(instance_name, 'fn'))
                    footnote['id'] = footnote_id
                    used_footnotes[hash] = footnote
    return used_footnotes, fact_footnotes
          
def footnote_hash(footnote, rule_name, cntlr):
    ''''
    lang
    arcrole
    content
    fact-id'''

    if 'content' not in footnote and 'fact-id' not in footnote:
        cntlr.addToLog(f"footnote does not contain content or a reference to another fact. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
        return None
    if 'content'in footnote and 'lang' not in footnote:
        cntlr.addToLog(f"Footnote with content requires a language. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
        return None
    if 'arcrole' not in footnote:
        cntlr.addToLog(f"Footnote requires and arcrole. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
        return None
    if 'content' in footnote and 'fact-id' in footnote:
        cntlr.addToLog(f"Footnote can eihter have content or a fact-id (reference to anther fact) but not both. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
        return None
    
    arcrole = _LINK_ALIASES_BY_ALIAS.get(footnote['arcrole'], footnote['arcrole'])

    hash_dict = copy.copy(footnote)
    hash_dict['arcrole'] = arcrole
    return hash(frozenset(hash_dict.items()))

def process_json(instance_name, taxonomies, facts, used_footnotes, fact_footnotes, cntlr, options):

    instance = json.loads(_INSTANCE_BASE_JSON_STRING)
    # Create an Arelle model of the taxonomy. This is done by adding the taxonomies 
    # as schema refs and loading the file. The model is used to validate as facts are created
    # (i.e. the concept name is valid)
    taxonomy_model = get_taxonomy_model(instance_name, taxonomies, cntlr)
    nsmap = get_initial_nsmap(instance, taxonomy_model, instance['documentInfo']['namespaces'])
    # Always keep the 'xbrl' namespace
    nsmap.mark_namespace_as_used('https://xbrl.org/2021')
    # Add the schema refs
    # TODO this could also be role and arcrole refs
    for taxonomy in taxonomies:
        instance['documentInfo']['taxonomy'].append(taxonomy)

    # Add facts
    for fact in facts:
        is_valid, fact_value, concept, entity, period, unit, dimensions, decimals, language = get_fact_data(fact, taxonomy_model, cntlr)
        if is_valid:
            footnotes = (used_footnotes[h] for h in fact_footnotes[fact['fact-id']])
            create_json_fact(instance, instance_name, nsmap, cntlr, fact.get('rule-name'), fact.get('fact-id'), fact_value, concept, entity, period, unit, dimensions, decimals, language, footnotes)

    # Add footnotes
    for footnote in used_footnotes.values():
        # create the footnote pseudo fact
        if 'content' in footnote:
            footnote_id = footnote['id']
            footnote_node = {'value': footnote['content'],
                                'dimensions': {
                                'concept': 'xbrl:note',
                                'noteId': footnote_id,
                                'language': footnote['lang']
                                }}
            instance['facts'][footnote_id] = footnote_node

    # Clean up the namespaces
    #nsmap.remove_unused_namespaces()
    #unused_prefixes =set(instance['namespaces'].keys()) - set(nsmap.map_by_prefix.keys())
    instance['documentInfo']['namespaces'] = nsmap.used_map_by_prefix
    
    # Write the file
    output_file_name = os.path.join(options.xodel_location, f'{instance_name}.json')
    with open(output_file_name, 'w') as f:
        json.dump(instance, f, indent=2)
    cntlr.addToLog(f"Writing instance file {output_file_name}", "XinceInfo")

def process_xml(instance_name, taxonomies, facts, used_footnotes, fact_footnotes, cntlr, options):

    instance = et.fromstring(_INSTANCE_BASE_XML_STRING)
    # Create an Arelle model of the taxonomy. This is done by adding the taxonomies 
    # as schema refs and loading the file. The model is used to validate as facts are created
    # (i.e. the concept name is valid)
    taxonomy_model = get_taxonomy_model(instance_name, taxonomies, cntlr)
    nsmap = get_initial_nsmap(instance, taxonomy_model, instance.nsmap)
    # Add the schema refs
    for taxonomy in taxonomies:
        schema_ref = et.Element(f'{{{_LINK_NAMESPACE}}}schemaRef')
        schema_ref.set(f'{{{nsmap.get_namespace("xlink")}}}href', taxonomy)
        schema_ref.set(f'{{{nsmap.get_namespace("xlink")}}}type', 'simple')
        instance.append(schema_ref)

    contexts = dict()
    units = dict()
    footnote_rels = []
    # Add facts
    fact_nodes = []
    for fact in facts:
        is_valid, fact_value, concept, entity, period, unit, dimensions, decimals, language = get_fact_data(fact, taxonomy_model, cntlr)
        if is_valid:
            xml_fact = create_xml_fact(contexts, units, taxonomy_model, instance_name, nsmap, cntlr, fact.get('rule-name'), fact.get('fact-id'), fact_value, concept, entity, period, unit, dimensions, decimals, language)
            fact_nodes.append(xml_fact)
    
    # add arcrole refs for footnotes
    add_arcrole_refs(instance, used_footnotes.values(), taxonomy_model, cntlr)
    # Add contexts
    for context in contexts.values():
        instance.append(context)
    # Add units
    for unit in units.values():
        instance.append(unit)    
    # Attach facts
    for fact in fact_nodes:
        instance.append(fact)
    # Add footnotes
    add_xml_footnotes(instance_name, instance, fact_footnotes, used_footnotes, cntlr)
    
    # #TODO - Add schema refs for role and arcroles that are used in the instance. 
    # Clean up namespaces
    et.cleanup_namespaces(instance, top_nsmap=nsmap.used_map_by_prefix, keep_ns_prefixes=nsmap.used_map_by_prefix)
    # Write the file
    output_file_name = os.path.join(options.xodel_location, f'{instance_name}.xml')
    with open(output_file_name, 'wb') as f:
        tree = et.ElementTree(instance)
        tree.write(f, encoding="utf-8", pretty_print=True, xml_declaration=True)
    cntlr.addToLog(f"Writing instance file {output_file_name}", "XinceInfo")

def get_initial_nsmap(instance, taxonomy_model, namespaces):
    '''This will add namespaces and their prefixes'''

    # first add the namespaces in the instance. These are the basic ones
    nsmap = XinceNSMap()
    for prefix, ns in namespaces.items():
        nsmap.add_or_get_namespace(ns, prefix)
    # Then add namespaces defined in the the taxonomy
    for prefix, ns in taxonomy_model.prefixedNamespaces.items():
        nsmap.add_or_get_namespace(ns, prefix)
    
    return nsmap

def get_taxonomy_model(tax_name, taxonomies, cntlr):

    cntlr.addToLog(f"Start loading taxonomy model for instance {tax_name}", "XinceInfo")
    entry_point = _TAXONOMY_MODEL_START
    for taxonomy in taxonomies:
        # TODO - This assumes that the taxonomies are all schema refs, but they could be rolerefs and arcrole refs.
        entry_point += f'<link:schemaRef xlink:href="{taxonomy}" xlink:type="simple"/>'
    entry_point += '</xbrli:xbrl>'

    entry_point_file_object, entry_point_file_name = tempfile.mkstemp('.xml', text=True)
    try:
        with os.fdopen(entry_point_file_object, 'w') as ep:
            ep.write(entry_point)
        entry_point_file_source = FileSource.openFileSource(entry_point_file_name, cntlr)            
        modelManager = ModelManager.initialize(cntlr)
        tax_model = modelManager.load(entry_point_file_source)
    finally:
        # Delete the temp file
        os.unlink(entry_point_file_name)

    if 'IOerror' in tax_model.errors:
        raise XinceException(_(f"Error creating taxonomy for instance {tax_name}"))                

    cntlr.addToLog(f"Loaded taxonomy model for instance {tax_name}", "XinceInfo")

    return tax_model

def get_fact_data(fact_info, taxonomy, cntlr):
    errors = False
    # default aspects are from fact-alignment
    dimensions = dict()
    merged_info = dict()
    alignment_string = fact_info.get('fact-alignment', '{}')
    try:
        alignment_info = json.loads(alignment_string)
        # Fix the keys. Alignment uses 'concept' but the key should be 'fact-concept'to match the Xince output attribute
        for info_item, info_value in alignment_info.items():
            if info_item in ('concept', 'period', 'entity', 'unit'):
                merged_info[f'fact-{info_item}'] = info_value
            else: # this is a dimension
                dimensions[info_item] = info_value
        if len(dimensions) > 0:
            merged_info['fact-dimensions'] = json.dumps(dimensions)
    except json.decoder.JSONDecodeError:
        cntlr.addToLog(f"Invalid fact-alignment '{alignment_string}' for rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
        errors = True

    # Override the alignment information with any of the fact-... outputs.
    # TODO - Should fact-dimensions override all dimensions in the alignment? currently it will.
    for k, v in fact_info.items():
        if k != 'fact-alignment':
            merged_info[k] = v

    return verify_fact(merged_info, taxonomy, cntlr)

def create_json_fact(instance, instance_name, nsmap, cntlr, rule_name, fact_id, fact_value, concept, entity, period, unit, dimensions, decimals, language, footnotes):

    fact_dict = dict()
    # TODO if the value is qname, then need to mark in the nsmap
    fact_dict['value'] = fact_value
    if concept.isNumeric and decimals != 'infinity' and fact_value is not None:
        fact_dict['decimals'] = decimals
    fact_dict['dimensions'] = dict()
    concept_qname = XinceQname(concept.qname.namespaceURI, concept.qname.localName)
    fact_dict['dimensions']['concept'] = concept_qname.serialize(nsmap, mark=True)
    if language is not None:
        fact_dict['dimensions']['language'] = language
    # entities are treated like qnames even though they are clearly not
    entity_qname = XinceQname(entity.scheme, entity.identifier)
    fact_dict['dimensions']['entity'] = entity_qname.serialize(nsmap, mark=True)
    fact_dict['dimensions']['period'] = period.serialize()
    if concept.isNumeric and not unit.is_pure:
        fact_dict['dimensions']['unit'] = unit.serialize(nsmap)
    if dimensions is not None and len(dimensions) > 0:
        for dim, mem in dimensions.items():
            # dim is a concept
            dim_qname = XinceQname(dim.qname.namespaceURI, dim.qname.localName)
            if dim.isExplicitDimension:
                mem_qname = XinceQname(mem.qname.namespaceURI, mem.qname.localName)
                fact_dict['dimensions'][dim_qname.serialize(nsmap, mark=True)] = mem_qname.serialize(nsmap, mark=True)
            else: # typed dimension
                fact_dict['dimensions'][dim_qname.serialize(nsmap, mark=True)] = mem
    
    if footnotes is not None:
        process_json_footnotes(fact_dict, instance, instance_name, footnotes)

    instance['facts'][fact_id] = fact_dict

def process_json_footnotes(fact_dict, instance, instance_name, footnotes):
    if isinstance(footnotes, dict):
        footnotes = [footnotes,]
    
    for footnote in footnotes:
 
        if 'content' in footnote:
            footnote_id = footnote['id']
        elif 'fact-id' in footnote:
            footnote_id = footnote['fact-id']
        # Add the link to the fact
        if 'links' not in fact_dict:
            fact_dict['links'] = dict()

        alias = get_alias(instance,instance_name, 'linkTypes', footnote['arcrole'])
        if alias not in fact_dict['links']:
            fact_dict['links'][alias] = dict()
        if _STANDARD_ROLE_ALIAS not in fact_dict['links'][alias]:
            fact_dict['links'][alias][_STANDARD_ROLE_ALIAS] = list()

        fact_dict['links'][alias][_STANDARD_ROLE_ALIAS].append(footnote_id)

def create_xml_fact(contexts, units, taxonomy, instance_name, nsmap, cntlr, rule_name, fact_id, fact_value, concept, entity, period, unit, dimensions, decimals, language):

    concept_qname = XinceQname(concept.qname.namespaceURI, concept.qname.localName)
    concept_qname.mark_as_used(nsmap)
    fact = et.Element(concept_qname.clark)
    # TODO if fact_value is a qname, need to make sure the nsmap has the namespace
    fact.set('id', fact_id)
    if fact_value is None or fact_value == '':
        fact.set(f'{{http://www.w3.org/2001/XMLSchema-instance}}nil', 'true')
    else:
        fact.text = fact_value
    
        if decimals is not None:
            if decimals == 'infinity':
                fact.set('decimals', 'INF')
            else:
                fact.set('decimals', str(decimals))
        if language is not None:
            fact.set('xmlns:lang', language)

    context_id = get_context(instance_name, contexts, taxonomy, nsmap, entity, period, dimensions)
    fact.set('contextRef', context_id)
    if unit is not None:
        unit_id = get_xml_unit(instance_name, units, nsmap, unit)
        fact.set('unitRef', unit_id)
    
    return fact

def get_context(instance_name, contexts, taxonomy, nsmap, entity, period, dimensions):
    hash = context_hash(entity, period, dimensions)
    if hash not in contexts:
        # Create the context
        context_id = next(IDGenerator.get_id_generator(instance_name, 'c'))
        context_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}context')
        context_node.set('id', context_id)
        # Entity
        entity_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}entity')
        ident_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}identifier')
        ident_node.set('scheme', entity.scheme)
        ident_node.text = entity.identifier
        entity_node.append(ident_node)
        context_node.append(entity_node)
        # Period
        period_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}period')
        if period.is_forever:
            forever_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}forever')
            period_node.append(forever_node)
        elif period.is_instance:
            instant_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}instant')
            period_node.append(instant_node)
            if period.start.hour + period.start.minute + period.start.second + period.start.microsecond == 0:
                # the time is midnight the end of day
                instant_node.text = (period.start + datetime.timedelta(days=1)).date().isoformat()
            else:
                instant_node.text = period.start.isoformat()
        else: # duration
            start_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}startDate')
            if period.start.hour + period.start.minute + period.start.second + period.start.microsecond == 0:
                start_node.text = period.start.date().isoformat()
            else:
                start_node.text = period.start.isoformat()
            period_node.append(start_node)
        
            end_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}endDate')
            if period.end.hour + period.end.minute + period.end.second + period.end.microsecond == 0:
                end_node.text = (period.end + datetime.timedelta(days=1)).date().isoformat()
            else:
                end_node.text = period.end.isoformat()
            period_node.append(end_node)
        context_node.append(period_node)
        # Dimensions
        if dimensions is not None and len(dimensions) > 0:
            # create segment to contain the dimensions
            segment_node = et.Element(f'{{{_XBRLI_NAMESPACE}}}segment')
            entity_node.append(segment_node)
            for dim, mem in dimensions.items():
                # dim is a concept
                dim_qname = XinceQname(dim.qname.namespaceURI, dim.qname.localName)
                if dim.isExplicitDimension:
                    dim_node = et.Element(f'{{{_DIMENSION_NAMESPACE}}}explicitMember')
                    segment_node.append(dim_node)
                    dim_node.set('dimension', dim_qname.prefixed(nsmap, mark=True))
                    mem_qname = XinceQname(mem.qname.namespaceURI, mem.qname.localName)
                    dim_node.text = mem_qname.prefixed(nsmap, mark=True)
                else: # typed dimension
                    dim_node = et.Element(f'{{{_DIMENSION_NAMESPACE}}}typedMember')
                    segment_node.append(dim_node)
                    dim_node.set('dimension', dim_qname.prefixed(nsmap, mark=True))
                    # Need to get the typed domain
                    dim_concept = get_concept(dim_qname.clark, taxonomy)
                    typed_qname = XinceQname(dim_concept.typedDomainElement.qname.namespaceURI, dim_concept.typedDomainElement.qname.localName)
                    typed_qname.mark_as_used(nsmap)
                    typed_domain_node = et.Element(typed_qname.clark)
                    dim_node.append(typed_domain_node)
                    typed_domain_node.text = mem
            
        contexts[hash] = context_node
    
    return contexts[hash].get('id')

def context_hash(entity, period, dimensions):
    dims = []
    if dimensions is not None:
        for dim, mem in dimensions.items():
            dims.append( (dim.qname.clarkNotation, mem.qname.clarkNotation if dim.isExplicitDimension else mem) )

    return hash( (entity.scheme, entity.identifier, repr(period), tuple(dims)) )

def get_xml_unit(instance_name, units, nsmap, unit):
    if repr(unit) not in units:
        units[repr(unit)] = unit.serialize(nsmap, 'xml', instance_name)
    return units[repr(unit)].get('id')

def add_arcrole_refs(instance, footnotes, taxonomy, cntlr):
    for footnote in footnotes:
         arcroles = {_LINK_ALIASES_BY_ALIAS.get(footnote['arcrole'], footnote['arcrole']) for x in footnotes}
         for arcrole in arcroles:
            if arcrole != 'http://www.xbrl.org/2003/arcrole/fact-footnote':
                if arcrole in taxonomy.arcroleTypes:
                    arcrole_doc = taxonomy.arcroleTypes[arcrole].document.uri
                    arcrole_href = f'{arcrole_doc}#{taxonomy.arcroleTypes[arcrole].id}'
                else:
                    # check the linkrole registry
                    arcrole_href = get_uri_from_lrr(arcrole, cntlr)
                if arcrole_href is None:
                    cntlr.addToLog(f"Cannot determine the location for arcrole '{arcrole}' to add an arcroleRef", "XinceError", level=logging.ERROR)
                    continue
                # otherwise write the arcroleRef element
                arcrole_ref = et.Element(f'{{{_LINK_NAMESPACE}}}arcroleRef')
                arcrole_ref.set(f'{{{_XLINK_NAMESPACE}}}type', 'simple')
                arcrole_ref.set('arcroleURI', arcrole)
                arcrole_ref.set(f'{{{_XLINK_NAMESPACE}}}href', arcrole_href)
                instance.append(arcrole_ref)

def get_uri_from_lrr(role, cntlr):
    global _LINKROLE_REGISTRY
    if _LINKROLE_REGISTRY is None:
        _LINKROLE_REGISTRY = et.parse(FileSource.openFileStream(cntlr, _LINKROLE_REGISTRY_URI))
    
    # find arcrole in lrr
    for entry in _LINKROLE_REGISTRY.xpath(f"lrr:arcroles/lrr:arcrole[normalize-space(lrr:roleURI) = '{role}']", namespaces={'lrr': _LINKROLE_REGISTRY_NAMESPACE}):
        href_node = entry.find("lrr:authoritativeHref", namespaces={'lrr': _LINKROLE_REGISTRY_NAMESPACE})
        if href_node is not None:
            return href_node.text.strip()

def add_xml_footnotes(instance_name, instance, fact_footnotes, used_footnotes, cntlr):
    if len(fact_footnotes) == 0:
        return # there are no footnotes so, just go back
    footnote_link = et.Element(f'{{{_LINK_NAMESPACE}}}footnoteLink')
    footnote_link.set(f'{{{_XLINK_NAMESPACE}}}role', 'http://www.xbrl.org/2003/role/link')
    footnote_link.set(f'{{{_XLINK_NAMESPACE}}}type', 'extended')
    instance.append(footnote_link)
    # create the arcs
    locators = dict()
    for fact_id, footnotes in fact_footnotes.items():
        for footnote_hash in footnotes:
            footnote = used_footnotes[footnote_hash]
            arcrole = _LINK_ALIASES_BY_ALIAS.get(footnote['arcrole'], footnote['arcrole'])
            fact_loc = get_locator(footnote_link, locators, fact_id)
            if 'fact-id' in footnote: # this is fact to fact (explanatoryFact) footnote
                footnote_res = get_locator(footnote_link, locators, footnote['fact-id'])
            else: # This is a resource
                footnote_res = get_resource(footnote_link, locators, footnote)
            arc = et.Element(f'{{{_LINK_NAMESPACE}}}footnoteArc')
            arc.set(f'{{{_XLINK_NAMESPACE}}}type', 'arc')
            arc.set(f'{{{_XLINK_NAMESPACE}}}arcrole', arcrole)
            arc.set(f'{{{_XLINK_NAMESPACE}}}from', fact_loc.get(f'{{{_XLINK_NAMESPACE}}}label'))
            arc.set(f'{{{_XLINK_NAMESPACE}}}to', footnote_res.get(f'{{{_XLINK_NAMESPACE}}}label'))
            footnote_link.append(arc)

def get_locator(parent, locators, id):
    if id not in locators:
        loc = et.Element(f'{{{_LINK_NAMESPACE}}}loc')
        loc.set(f'{{{_XLINK_NAMESPACE}}}type', 'locator')
        loc.set(f'{{{_XLINK_NAMESPACE}}}label', f'{id}_lab')
        loc.set(f'{{{_XLINK_NAMESPACE}}}href', f'#{id}')
        locators[id] = loc
        parent.append(loc)
    return locators[id]

def get_resource(parent, locators, footnote):
    if footnote['id'] not in locators:
        res = et.Element(f'{{{_LINK_NAMESPACE}}}footnote')
        res.set(f'{{{_XLINK_NAMESPACE}}}type', 'resource')
        res.set(f'{{{_XLINK_NAMESPACE}}}label', f'{footnote["id"]}_lab')
        res.set(f'{{{_XLINK_NAMESPACE}}}role', 'http://www.xbrl.org/2003/role/footnote')
        res.set('{http://www.w3.org/XML/1998/namespace}lang', footnote['lang'])
        res.text = footnote['content']
        locators[footnote['id']] = res
        parent.append(res)

    return locators[footnote['id']]


def get_alias(instance, instance_name, alias_type, link_value):
    # if a standard shortcut is used. I.e just 'foootnote'
    link_value = _LINK_ALIASES_BY_ALIAS.get(link_value.lower(), link_value)
    # See if the alias and role are already in the document
    if alias_type in instance['documentInfo']:
        for alias, alias_value in instance['documentInfo'][alias_type].items():
            if alias_value == link_value:
                return alias
    else:
        instance['documentInfo'][alias_type] = dict()
    # if here, then there was not an existing arcrole
    alias = _LINK_ALIASES_BY_URI.get(link_value, next(IDGenerator.get_id_generator(instance_name, link_value.rsplit('/', 1)[-1])))
    instance['documentInfo'][alias_type][alias] = link_value

    return alias
 
def verify_fact(fact_info, taxonomy, cntlr):
    errors = False

    fact_value = None
    model_concept = None
    entity = None
    period = None
    unit = None
    dimensions = None 
    decimals = None
    language = None
    #footnotes = None

    # Check concept, entity and period exists. These are always required
    for aspect in ('fact-concept', 'fact-entity', 'fact-period'):
        if aspect not in fact_info:
            cntlr.addToLog(f"Fact is missing {aspect} which is required. Rule: {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check concept
    if 'fact-concept' in fact_info:
        model_concept = get_concept(fact_info.get('fact-concept'), taxonomy)
        if model_concept is None:
            cntlr.addToLog(f"Concept {fact_info['fact-concept']} is not in the taxonomy for the instance. Rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check entity - it should look like a clark notation qname where the namespace is the scheme and the local part is the identifier
    if 'fact-entity' in fact_info:
        try:
            entity_info = json.loads(fact_info['fact-entity'])
            if len(entity_info) != 2:
                raise json.decoder.JSONDecodeError
            entity = XinceEntity(entity_info[0], entity_info[1])
        except json.decoder.JSONDecodeError:
            cntlr.addToLog(f"fact-entity '{fact_info['fact-entity']}' is not valid for rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check period
    if 'fact-period' in fact_info:
        period = get_period(fact_info['fact-period'], fact_info['rule-name'], cntlr)
        if period is None:
            errors = True

    if model_concept is not None and model_concept.isNumeric:
        # Check units
        if 'fact-unit' not in fact_info:
            cntlr.addToLog(f"fact-unit is required for numeric facts. Concept is '{model_concept.qname.clarkNotation}' from rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True
        unit = get_unit(fact_info['fact-unit'], fact_info['rule-name'], cntlr)
        if unit is None:
            errors = True

        # Check decimals
        if 'fact-decimals' in fact_info and fact_info['fact-decimals'].strip().lower() != 'none':
            if fact_info['fact-decimals'].lower().strip() == 'inf':
                decimals = 'infinity'
            else:
                try:
                    decimals = int(decimal.Decimal(fact_info['fact-decimals']))
                except ValueError:
                    cntlr.addToLog(f"Invalid decimals of {fact_info['fact-decimals']} for rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
                    errors = True
        else: # default to infinity when not provided
            decimals = 'infinity'

    # Check language
    if model_concept is not None and model_concept.baseXbrliType == 'stringItemType':
        if 'fact-language' in fact_info and fact_info['fact-language'].strip().lower() != 'none':
            language = fact_info['fact-language'].strip()

    # Check dimensions
    if 'fact-dimensions' in fact_info:
        dimensions = get_dimensions(fact_info['fact-dimensions'], taxonomy, fact_info['rule-name'], cntlr)
        if dimensions is None:
            errors = True

    if model_concept is not None:
        if fact_info.get('fact-is-nil', 'false').lower() in ('true', '1'):
            fact_value = None
        else:
            if 'fact-value' not in fact_info:
                cntlr.addToLog(f"'fact-value' is missing from the rule. This is required if 'fact-is-nil' is false or not present. Found in rule '{fact_info['rule-name']}'", "XinceError", level=logging.ERROR)
                errors = True
            else:
                fact_value = get_fact_value(fact_info['fact-value'], model_concept, cntlr)
                if fact_value is None:
                    # There was a problem with the value
                    cntlr.addToLog(f"Fact value '{fact_info['fact-value']}' is not valid for concept '{model_concept.qname.localName}' with type '{model_concept.typeQname.localName}'. Found in rule '{fact_info['rule-name']}'", "XinceError", level=logging.ERROR)
                    errors = True
    # # check footnotes
    # if 'fact-footnote' in fact_info:
    #     try:
    #         footnotes = json.loads(fact_info['fact-footnote'])
    #         if type(footnotes) not in (list, dict):
    #             cntlr.addToLog(f"Footnotes for fact should be a list or a dictionary, but found {type(footnotes).__name__}. Found in rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
    #             errors = True
    #     except json.decoder.JSONDecodeError:
    #         cntlr.addToLog(f"Footnotes for fact are not a json string. Probably missing 'to-xince'. Found in rule '{fact_info['rule-name']}'", "XinceError", level=logging.ERROR)
    #         errors = True

    return not errors, fact_value, model_concept, entity, period, unit, dimensions, decimals, language,# footnotes

def get_concept(clark, taxonomy):
    if not hasattr(taxonomy, 'clarkConcepts'):
        # Create a dictionary keyed by qname in clark notation.
        clark_concepts = {k.clarkNotation: v for k, v in taxonomy.qnameConcepts.items()}
        taxonomy.clarkConcepts = clark_concepts
    return taxonomy.clarkConcepts.get(clark)
    
def get_unit(unit_string, rule_name, cntlr):
    # The unit_string uses clark notation for the individual units
    numerators = None
    denominators = None

    def break_up_units(units):
        if units is None:
            return None

        errors = False
        result = []
        for unit_part in units.split('*'):
            qname_match = _QNAME_MATCH.fullmatch(unit_part.strip())
            if unit_match is None:
                cntlr.addToLog(f"Unit '{unit_part}' is not in clark notation. Rule is '{rule_name}'", "XinceError", level=logging.ERROR)
                errors = True
            else:
                unit_qname = XinceQname(qname_match.group(1), qname_match.group(2))
                result.append(unit_qname)
        return result if not errors else None

    unit_match = _UNIT_MATCH.fullmatch(unit_string.strip())
    if unit_match is None:
        cntlr.addToLog(f"Unit '{unit_string}' is not a valid xince unit. Rule is '{rule_name}'", "XinceError", level=logging.ERROR)
    else:
        numerators = break_up_units(unit_match.group(1))
        if unit_match.group(4) is not None:
            denominators = break_up_units(unit_match.group(4))
            if denominators is None:
                return None

    if numerators is None:
        # The unit match must have failed, so the unit is not valid.
        return None
    else:
        return XinceUnit(numerators, denominators)

def get_period(period_string, rule_name, cntlr):
    start = None
    end = None
    if period_string.lower().strip() == 'forever':
        return XincePeriod() # no start or end date, this is a forever period
    elif '/' in period_string:
        # this is a duration
        start_string, end_string = period_string.strip().split('/')
        try:
            start = datetime.datetime.fromisoformat(start_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid start date format (must be ios format). Start date is '{start_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        try:
            end = datetime.datetime.fromisoformat(end_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid end date format (must be ios format). Start date is '{end_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        if start is not None and end is not None:
            return XincePeriod(start, end)
    else:
        # this is an instant
        try:
            start = datetime.datetime.fromisoformat(period_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid instant date format (must be ios format). Start date is '{period_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        if start is not None:
            return XincePeriod(start)
    
    return None # the period could not be created

def get_dimensions(dim_string, taxonomy, rule_name, cntlr):
    try:
        dimensions = json.loads(dim_string.strip())
    except json.decoder.JSONDecodeError:
        cntlr.addToLog(f"Dimensions string '{dim_string.strip()}' is not value for rule {rule_name}", "XinceError", level=logging.ERROR)
        return

    if not isinstance(dimensions, dict):
        cntlr.addToLog(f"Dimensions string '{dim_string.strip()}' is not value for rule {rule_name}", "XinceError", level=logging.ERROR)
        return
    
    error = False
    result = dict()
    for dim, member in dimensions.items():
        # check dimension is valid
        dim_concept = get_concept(dim, taxonomy)
        if dim_concept is None:
            cntlr.addToLog(f"Dimension concept {dim} is not in the taxonomy. Rule {rule_name}", "XinceError", level=logging.ERROR)
            error = True
        elif not dim_concept.isDimensionItem:
            cntlr.addToLog(f"Dimension concept {dim_concept.qname.clarkNotation} is not a dimension item. Rule {rule_name}", "XinceError", level=logging.ERROR)
            error = True

        else: # all is good
            if dim_concept.isExplicitDimension:
                # the member is a qname for the member concept
                mem_concept = get_concept(member, taxonomy)
                if mem_concept is None:
                    cntlr.addToLog(f"Member concept {member} is not in the taxonomy. Rule {rule_name}", "XinceError", level=logging.ERROR)
                    error = True
                elif not mem_concept.isDomainMember:
                    cntlr.addToLog(f"Member concept {mem_concept.qname.clarkNotation} is not a member of a dimension. Rule {rule_name}", "XinceError", level=logging.ERROR)
                    error = True
                else:
                    result[dim_concept] = mem_concept
                # TODO - should check that the member is valid for the dimension. This would require building all the cubes and checking
                # the member for the fact concept. 
                # TODO - should also check that the member is not the default
            else: # this is a typed dimension
                # TODO convert the typed dimenson value like fact values
                result[dim_concept] = get_fact_value(member, dim_concept.typedDomainElement, cntlr)
        
    return result

def get_fact_value(fact_value, model_concept, cntlr):
    if model_concept.baseXsdType not in _TYPE_VERIFICATION_FUNCTION:
        cntlr.addToLog(f"Data type '{model_concept.baseXsdType}' is not supported)")
        return None
    else:
        # All XuleValue dates are datetimes. This is a problem if the new fact is a date (not a datetime)
        if model_concept.baseXsdType == 'date':
            fact_value = fact_value[:10] # this will take the date portion ignoring the time component
        return _TYPE_VERIFICATION_FUNCTION[model_concept.baseXsdType](fact_value)

def canonical_decimal(val):
    try:
        num = decimal.Decimal(val)
    except decimal.InvalidOperation:
        return None
    num_string = str(num)
    if '.' in num_string:
        num_string = num_string.rstrip('0') # remove trailing 0s
        if num_string[-1] == '.':
            num_string += '0'
    else:
        num_string += '.0'

    num_string = num_string.lstrip('0')
    if num_string[0] == '.':
        num_string = '0' + num_string
    return num_string

def canonical_float(val):
    # this works for double also. Python doesn't really have a float, the float is a double.
    try:
        num = float(val)
    except ValueError:
        return None
    num_string = str(num)
    num_string.replace('e', 'E')
    if 'E' not in num_string:
        num_string += 'E0'
    return num_string

def canonical_integer(val):
    try:
        num = int(val)
    except ValueError:
        return None
    return str(num)

def canonical_non_positive_integer(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if result.startswith('-') or result == '0':
        return result
    else:
        return None

def canonical_negative_integer(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if result.startswith('-'):
        return result
    else:
        return None

def canonical_long(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 9223372036854775807 and int(result) >= -9223372036854775808:
        return result
    else:
        return None  

def canonical_int(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 2147483647 and int(result) >= -2147483648:
        return result
    else:
        return None

def canonical_short(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 32767 and int(result) >= -32768:
        return result
    else:
        return None

def canonical_byte(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 127 and int(result) >= -128:
        return result
    else:
        return None

def canonical_non_negative_integer(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if result == '0' and not result.startswith('-'):
        return result
    else:
        return None

def canonical_unsigned_long(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 18446744073709551615 and int(result) >= 0:
        return result
    else:
        return None

def canonical_unsigned_int(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 4294967295 and int(result) >= 0:
        return result
    else:
        return None

def canonical_unsigned_short(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 65535 and int(result) >= 0:
        return result
    else:
        return None

def canonical_unsigned_byte(val):
    result = canonical_integer(val)
    if result is None:
        return None
    if int(result) <= 255 and int(result) >= 0:
        return result
    else:
        return None

def canonical_positive_integer(val):
    result = canonical_non_negative_integer(val)
    if result is None or result == '1':
        return None
    else:
        return result

def canonical_fraction(val):
    return None # fraction is not supported.

def canonical_string(val):
    return val

def canonical_boolean(val):
    if val.strip().lower() in ('1', 'true'):
        return 'true'
    elif val.strip().lower() in ('0', 'false'):
        return 'false'
    else:
        return None

def canonical_hex_binary(val):
    if _HEX_MATCH.fullmatch(val):
        return val.upper()
    else:
        return None

def canonical_base64_binary(val):
    try:
        bin = base64.b64encode(val)
    except TypeError:
        return None
    return base64.standard_b64encode(val).encode('ascii')

def canonical_qname(val):
    if _QNAME_MATCH.fullmatch(val):
        return val
    else:
        return None

def canonical_duration(val):
    try:
        result = isodate.parse_duration(val)
    except isodate.isoerror.ISO8601Error:
        return None
    return val

def canonical_date_time(val):
    try:
        datetime.datetime.fromisoformat(val)
    except ValueError:
        return None
    return val

def canonical_time(val):
    try:
        datetime.time.fromisoformat(val)
    except ValueError:
        return None
    return val

def canonical_date(val):
    try:
        datetime.date.fromisoformat(val)
    except ValueError:
        return None
    return val

def canonical_g_year_month(val):
    match = _G_YEAR_MONTH.fullmatch(val.strip())
    if match:
        if int(match.group(2)) >= 1 and int(match.group(2)) <= 12:
            return f'{match.group(1)}-{match.group(2)}'
    return None

def canonical_g_year(val):
    if _G_YEAR.fullmatch(val.strip()):
        return val.strip()
    else:
        return None

def canonical_g_month_day(val):
    if _G_MONTH_DAY.fullmatch(val.strip()):
        return val.strip()
    else:
        return None

def canonical_g_day(val):
    if _G_DAY.fullmatch(val.strip()):
        return val.strip()
    else:
        return None

def canonical_g_month(val):
    if _G_MONTH.fullmatch(val.strip()):
        return val.strip()
    else:
        return None

def canonical_normalized_string(val):
    for bad_char in ('\r\n\t'):
        if bad_char in val:
            return None
    return val

def canonical_token(val):
    normalized_string = canonical_normalized_string(val)
    if normalized_string is None:
        return None
    if normalized_string.startswith(' ') or normalized_string.endswith(' '):
        return None
    if '  ' in normalized_string: # 2 spaces
        return None
    else:
        return val

def canonical_language(val):
    if _LANGUAGE.fullmatch(val.strip()):
        return val.strip()
    else:
        return None

def canonical_name(val):
    if _NAME_MATCH(val):
        return val
    else:
        return None

def canonical_NCName(val):
    if _NCNAME_MATCH(val):
        return val
    else:
        return None

_TYPE_XBRL_TO_SCHEMA= {
    'decimalItemType': 'decimal',
    'floatItemType': 'float',
    'doubleItemType': 'double',
    'integerItemType': 'integer',
    'nonPositiveIntegerItemType': 'nonPositiveInteger',
    'negativeIntegerItemType': 'negativeInteger',
    'longItemType': 'long',
    'intItemType': 'int',
    'shortItemType': 'short',
    'byteItemType': 'byte',
    'nonNegativeIntegerItemType': 'nonNegativeInteger',
    'unsignedLongItemType': 'unsignedLong',
    'unsignedIntItemType': 'unsignedInt',
    'unsignedShortItemType': 'unsignedShort',
    'unsignedByteItemType': 'unsignedByte',
    'positiveIntegerItemType': 'positiveInteger',
    'monetaryItemType': 'decimal',
    'sharesItemType': 'decimal',
    'pureItemType': 'decimal',
    'stringItemType': 'string',
    'booleanItemType': 'boolean',
    'hexBinaryItemType': 'hexBinary',
    'base64BinaryItemType': 'base64Binary',
    'anyURIItemType': 'anyURI',
    'QNameItemType': 'QName',
    'durationItemType': 'duration',
    'dateTimeItemType': 'dateTime',
    'timeItemType': 'time',
    'dateItemType': 'date',
    'gYearMonthItemType': 'gYearMonth',
    'gYearItemType': 'gYear',
    'gMonthDayItemType': 'gMonthDay',
    'gDayItemType': 'gDay',
    'gMonthItemType': 'gMonth',
    'normalizedStringItemType': 'normalizedString',
    'tokenItemType': 'token',
    'languageItemType': 'language',
    'NameItemType': 'Name',
    'NCNameItemType': 'NCName'
}
_TYPE_VERIFICATION_FUNCTION = {
    'decimal':  canonical_decimal,
    'float':  canonical_float,
    'double':  canonical_float,
    'integer':  canonical_integer,
    'nonPositiveInteger':  canonical_non_positive_integer,
    'negativeInteger':  canonical_negative_integer,
    'long':  canonical_long,
    'int':  canonical_int,
    'short':  canonical_short,
    'byte':  canonical_byte,
    'nonNegativeInteger':  canonical_non_negative_integer,
    'unsignedLong':  canonical_unsigned_long,
    'unsignedInt':  canonical_unsigned_int,
    'unsignedShort':  canonical_unsigned_short,
    'unsignedByte':  canonical_unsigned_byte,
    'positiveInteger':  canonical_positive_integer,
    'string':  canonical_string,
    'boolean':  canonical_boolean,
    'hexBinary':  canonical_hex_binary,
    'base64Binary':  canonical_base64_binary,
    'anyURI':  canonical_string,
    'QName':  canonical_qname,
    'duration':  canonical_duration,
    'dateTime':  canonical_date_time,
    'time':  canonical_time,
    'date':  canonical_date,
    'gYearMonth':  canonical_g_year_month,
    'gYear':  canonical_g_year,
    'gMonthDay':  canonical_g_month_day,
    'gDay':  canonical_g_day,
    'gMonth':  canonical_g_month,
    'normalizedString':  canonical_normalized_string,
    'token':  canonical_token,
    'language':  canonical_language,
    'Name':  canonical_name,
    'NCName':  canonical_NCName
}






# XODEL Constants
_CNTLR = None
_ARELLE_MODEL=None

_STANDARD_LINK_NAMES = {'presentation': '{http://www.xbrl.org/2003/linkbase}presentationLink',
                        'definition': '{http://www.xbrl.org/2003/linkbase}definitionLink',
                        'calculation': '{http://www.xbrl.org/2003/linkbase}calculationLink',
                        'generic': '{http://xbrl.org/2008/generic}link'}
_STANDARD_ARC_NAME = {'{http://www.xbrl.org/2003/linkbase}presentationLink': '{http://www.xbrl.org/2003/linkbase}presentationArc',
                        '{http://www.xbrl.org/2003/linkbase}definitionLink': '{http://www.xbrl.org/2003/linkbase}definitionArc',
                        '{http://www.xbrl.org/2003/linkbase}calculationLink': '{http://www.xbrl.org/2003/linkbase}calculationArc',
                        '{http://xbrl.org/2008/generic}link': '{http://xbrl.org/2008/generic}arc'}

_STANDARD_EXTENDED_LINK_ROLE = 'http://www.xbrl.org/2003/role/link'

_STANDARD_ARCROLES = {
    "http://www.xbrl.org/2003/arcrole/concept-label",
    "http://www.xbrl.org/2003/arcrole/concept-reference",
    "http://www.xbrl.org/2003/arcrole/fact-footnote",
    "http://www.xbrl.org/2003/arcrole/parent-child",
    "http://www.xbrl.org/2003/arcrole/summation-item",
    "http://www.xbrl.org/2003/arcrole/general-special",
    "http://www.xbrl.org/2003/arcrole/essence-alias",
    "http://www.xbrl.org/2003/arcrole/similar-tuples",
    "http://www.xbrl.org/2003/arcrole/requires-element"
}

# output attribute validators
def string_validator(val):
    return True
def object_validator(val):
    try:
        get_model_object(val, _CNTLR)
    except:
        return False
    return True
def qname_validator(val):
    try:
        match_clark(val)
    except:
        return False
    return True
def integer_validator(val):
    try:
        int(val)
    except:
        return False
    return True
def decimal_validator(val):
    try: 
        decimal.Decimal(val)
    except:
        return False
    return True
def list_validator(val):
    try:
        py_list = json.loads(val)
        return isinstance(py_list, list)
    except:
        return False
def boolean_validator(val):
    return val.lower() in ('true', 'false')
def white_space_validator(val):
    return val in ('collapse', 'preserve', 'replace')
def enumerations_validator(val):
    try:
        enum_values = json.loads(val)
    except:
        return False
    if not isinstance(enum_values, list):
        return False
    for enum_value in enum_values:
        if not isinstance(enum_value, str):
            return False
    return True
def period_type_validator(val):
    return val in ('duration', 'instant')
def balance_type_validator(val):
    return val in ('debit', 'credit')
def attribute_validator(val):
    # Attributes a dictionary of qnames
    try:
        attr_dict = json.loads(val)
    except:
        return False
    if not isinstance(attr_dict, dict):
        return False
    for attr_name in attr_dict.keys():
        if not isinstance(attr_name, str):
            return False
        if match_clark(attr_name) is None:
            return False
    # Made it to the end, so everything should be good
    return True
def relationship_type_validator(val):
    return qname_validator(val) or val.lower() in ('presentation', 'calculation', 'definition', 'generic')


_VALIDATOR_FORMAT_MESSAGE = {
    qname_validator: 'QName must be formatted in clark notation (is {namespace-uri}local-name). Did you use the .to-xodel property',
    object_validator: 'Cannot find arelle model object. Did you use the .to-xodel property',
    list_validator: 'Expecting a list. Lists must be formatted as JSON arrays. Did you use the .to-xodel property', 
    boolean_validator: 'Boolean values must be either "ture" or "false". Did you use the .to-xodel property',
    white_space_validator: "Valid values for the type-white-space attribute are 'collapse', 'preserve', 'replace'",
    enumerations_validator: "type-enumerations must be a JSON list of strings. Did you use the .to-xodel property",
    period_type_validator: "concept-period-type must be either 'duration' or 'instant'",
    balance_type_validator: "concept-balance-type must be either 'credit' or 'debit'",
    attribute_validator: "attributes must be a dictionary keyed by qnames (attribute name)"
}

_COMPONENT_NAME = 0
_ATTRIBUTE_VALIDATOR= 1
_XODEL_OUTPUT_ATTRIBUTES = {
    'taxonomy-name': (None, string_validator),
    'taxonomy-namespace': ('taxonomy', string_validator),
    'Taxonomy-import': ('taxonomy', string_validator),
    'taxonomy-entry-point': ('taxonomy', string_validator),
    'type': ('type', object_validator),
    'type-name': ('type', qname_validator),
    'type-parent': ('type', object_validator),
    'type-parent-name': ('type', qname_validator),
    'type-min-inclusive': ('type', integer_validator),
    'type-max-inclusive': ('type', integer_validator),
    'type-min-exclusive': ('type', integer_validator),
    'type-max-exclusive': ('type', integer_validator),
    'type-total-digits': ('type', integer_validator),
    'type-fraction-digits': ('type', integer_validator),
    'type-length': ('type', integer_validator),
    'type-min-length': ('type', integer_validator),
    'type-max-length': ('type', integer_validator),
    'type-enumerations': ('type', enumerations_validator),
    'type-white-space': ('type', white_space_validator),
    'type-pattern': ('type', string_validator),
    'concept': ('concept', object_validator),
    'concept-name': ('concept', qname_validator),
    'concept-data-type': ('concept', qname_validator),
    'concept-abstract': ('concept', boolean_validator),
    'concept-nillable': ('concept', boolean_validator),
    'concept-period-type': ('concept', period_type_validator),
    'concept-balance-type': ('concept',balance_type_validator),
    'concept-substitution-group': ('concept', qname_validator),
    'concept-attributes': ('concept', attribute_validator),
    'role': ('role', object_validator),
    'role-uri': ('role', string_validator),
    'role-definition': ('role', string_validator),
    'role-used-on': ('role', list_validator),
    'relationship': ('relationship', object_validator),
    'relationship-source': ('relationship', qname_validator),
    'relationship-target': ('relationship', qname_validator),
    'relationship-order': ('relationship', decimal_validator),
    'relationship-weight': ('relationships', decimal_validator),
    'relationship-preferred-label': ('relationship', string_validator),
    'relationship-linkrole-uri': ('relationship', string_validator),
    'relationship-type': ('relationship', relationship_type_validator),
    'relationship-arcrole': ('relationship', string_validator),
    'relationship-attribute': ('relationship', attribute_validator),
    'relationship-id': ('relationship', string_validator),
}

# The _Tree class is used to sort components that are hierarchical so the parents are processed before the children.
class _TreeException(Exception):
    pass

class _Tree:
    # This is tree is just for sorting hierarchical things like type hiearchy and concpet substitution groups
    def __init__(self):
        self.nodes = dict()
        self._children = collections.defaultdict(set)
        self.parent = dict()

    def add(self, name, parent, node):
        if name in self.nodes:
            raise _TreeException(f"Node {name} already exists in the tree")
        self._children[parent].add(name)
        self.parent[name] = parent
        self.nodes[name] = node

    @property
    def roots(self):
        # This tree struction is unusally in that every node has a parent, but the parent
        # may not be in the tree. In this case, the node is a root.
        return {x for x in self.nodes if self.parent[x] not in self.nodes}

    def children(self, parent):
        return self._children[parent] 

    def walk(self, nodes=None):
        # Returns the keys in walking the tree order
        if nodes is None:
            parents = self.roots
        else:
            parents = nodes
        result = []
        for parent in parents:
            result +=  [parent, ] + [x for x in self.walk(self.children(parent))]
        return result
    
    def walk_nodes(self):
        return [self.nodes[x] for x in self.walk()]



def xodel_warning(message):
    if _CNTLR is not None:
        _CNTLR.addToLog(message, "XodelWarning")

def process_taxonomy(rule_name, log_rec, taxonomy, options, cntlr, arelle_model):
    # The SXM DTS will already have been created.
    pass


def type_sort(log_infos, cntlr):
    # Types need to be sorted so that base types are processed before derrived types
    type_tree = _Tree()
    for log_info in log_infos:
        log_rec = log_info[1]
        # find the type name and the type parent name
        type_name = None
        type_parent_name = None
        if 'type-name' in log_rec.args:
            type_name = log_rec.args['type-name'] # This should be a clark notation
        elif 'type' in log_rec.args:
            type_object = get_model_object(log_rec.args['type'], cntlr)
            type_name = type_object.qname.clarkNotation
        if 'type-parent-name' in log_rec.args:
            type_parent_name = log_rec.args['type-parent-name']
        elif 'type-parent' in log_rec.args:
            type_parent_object = get_model_object(log_rec.args['type-parent'], cntlr)
        elif 'type' in log_rec.args:
            type_object = get_model_object(log_rec.args['type'], cntlr)
            if type_object.typeDerivedFrom is not None:
                type_parent_name = type_object.typeDerivedFrom.qnameDerivedFrom.clarkNotation
        try:
            type_tree.add(type_name, type_parent_name, log_info)
        except _TreeException:
            raise XodelException(f"Duplicate type found {type_name}")

    return type_tree.walk_nodes()

def process_type(rule_name, log_rec, taxonomy, options, cntlr, arelle_model):
    '''Create a type. 
    
       Type type system is limited to types derived from xbrl types and simple types (i.e. for reference parts).'''

    type_name = None
    parent_name = None
    min_exclusive = None
    min_inclusive = None
    max_exclusive = None
    max_inclusive = None
    total_digits = None
    fraction_digits = None
    length = None
    min_length = None
    max_length = None
    enumerations = None
    white_space = None
    pattern = None

    if 'type' in log_rec.args:
        # This type will be copied and then any additional output attributes will be applied
        arelle_type = get_model_object(log_rec.args['type'], _CNTLR)
        type_info = taxonomy.get_class('Type').extract_properties_from_xml(etree.tostring(arelle_type), get_target_namespace(arelle_type))
        (type_name, parent_name, min_exclusive, min_inclusive, max_exclusive, max_inclusive, total_digits, fraction_digits, length, min_length, max_length, enumerations, white_space, pattern) = type_info

    type_name_clark = log_rec.args.get('type-name') or type_name
    type_name = resolve_clark_to_qname(type_name_clark, taxonomy)

    # check if the type is already create. It might have been created as a parent type
    if taxonomy.get('Type', type_name) is not None:
        # There is nothing to do, the type is already there
        return

    if 'type-parent-name' in log_rec.args:
        type_parent_clark_name = log_rec.args['type-parent-name']
    elif 'type-parent' in log_rec.args:
        type_parent_arelle = get_model_object(log_rec.args['type-parent'], _CNTLR)
        if type_parent_arelle is None:
            raise XodelException(f"'type-parent' not found in Arelle model'")
        type_parent_clark_name = type_parent_arelle.qname.clarkNotation
    else:
        type_parent_clark_name = parent_name

    if type_parent_clark_name is None:
        type_parent_name = None
    else:
        type_parent_name = resolve_clark_to_qname(type_parent_clark_name, taxonomy)
    parent_type = taxonomy.get('Type', type_parent_name)
    if parent_type is None and type_parent_name is not None:
        parent_type = find_type(taxonomy, type_parent_name, _CNTLR)
        if parent_type is None:
            # cannot find the type.
            raise XodelException(f"Cannot not find definition for a parent type of '{type_parent_name.clark}'")
    if 'type-min-exclusive' in log_rec.args:
        min_exclusive = int(log_rec.args['type-min-exclusive'])
    if 'type-min-inclusive' in log_rec.args:
        min_inclusive = int(log_rec.args['type-min-inclusive'])
    if 'type-max-exclusive' in log_rec.args:
        max_exclusive = int(log_rec.args[ 'type-max-exclusive'])
    if 'type-max-inclusive' in log_rec.args:
        max_inclusive = int(log_rec.args[ 'type-max-inclusive'])
    if 'type-total-digits' in log_rec.args:
        total_digits = int(log_rec.args[ 'type-total-digits'])
    if 'type-fraction-digits' in log_rec.args:
        fraction_digits = int(log_rec.args['type-fraction-digits'])
    if 'type-length' in log_rec.args:
        length = int(log_rec.args['type-length'])
    if 'type-min-length' in log_rec.args:
        min_length = int(log_rec.args['type-min-length'])
    if 'type-max-length' in log_rec.args:
        max_length = int(log_rec.args['type-max-length'])
    if 'type-enumerations' in log_rec.args:
        enumerations = json.loads(log_rec.args['type-enumerations'])
    if 'type-white-space' in log_rec.args:
        white_space = log_rec.args['type-white-space']
    if 'type-patern' in log_rec.args:
        pattern = log_rec.args['type-patern']

        taxonomy.new('Type', type_name, parent_type, min_exclusive=min_exclusive, min_inclusive=min_inclusive,
                    max_inclusive=max_inclusive, max_exclusive=max_exclusive, total_digits=total_digits,
                    fraction_digits=fraction_digits, length=length, min_length=min_length, max_length=max_length,
                    enumerations=enumerations, white_space=white_space, pattern=pattern)

def process_concept(rule_name, log_rec, taxonomy, options, cntlr, arelle_model):
    
    '''
    concept
    concept-name
    concept-data-type
    concept-abstract
    concept-nillable
    concept-period-type
    concept-balance-type
    concept-substitution-group
    concept-attributes
    '''

    # Check if there is a concept that is being copied (output attribute 'concept')
    if 'concept'in log_rec.args:
        arelle_concept = get_model_object(log_rec.args['concept'], cntlr)
        concept_info = extract_concept_info(arelle_concept, taxonomy)
    else:
        concept_info = dict()
    
    if 'concept-name' in log_rec.args:
        concept_info['concept-name'] = resolve_clark_to_qname(log_rec.args['concept-name'], taxonomy)
    if 'concept-data-type' in log_rec.args:
        concept_info['type-name'] = resolve_clark_to_qname(log_rec.args['concept-data-type'], taxonomy)
    if 'concept-abstract' in log_rec.args:
        concept_info['is-abstract'] = json.loads(log_rec.args['concept-abstract'])
    if 'concept-nillable' in log_rec.args:
        concept_info['nillable'] = log_rec.args['concept-nillable'].lower()
    if 'concept-period-type' in log_rec.args:
        concept_info['period-type'] = log_rec.args['concept-period-type']
    if 'concept-balance-type' in log_rec.args:
        concept_info['balance'] = log_rec.args['concept-balance-type']
    if 'concept-substitution-group' in log_rec.args:
        concept_info['substitution-group'] = resolve_clark_to_qname(log_rec.args['concept-substitution-group'], taxonomy)
    if 'concept-attributes' in log_rec.args:
        concept_info['attributes'].update(json.loads(log_rec.args['concept-attributes']))

    # Check concept name
    if 'concept-name' not in concept_info:
        raise XodelException(f"Cannot create a concept without a name. Need to copy from an existing concept or use the 'concept-name' output")
    # Check type
    if 'type-name' not in concept_info:
        raise XodelException(f"For concept '{concept_info['concept-name'].clark}', type '{concept_info['type-name'].clark}' is not found.")
    # The type needs to be a SXMType, currently we have a qname
    concept_type = find_type(taxonomy, concept_info['type-name'], _CNTLR)
    if concept_type is None:
            raise XodelException(f"For concept '{concept_info['concept-name'].clark}', do not have the type definition for '{concept_info['type-name'].clark}'")
    taxonomy.new('Concept', concept_info.get('concept-name'), concept_type, concept_info.get('abstract'),
                            concept_info.get('nillable'), concept_info.get('period-type'), concept_info.get('balance'),
                            concept_info.get('substitution-group-name'), concept_info.get('id'), concept_info.get('attributes'))


def process_role(rule_name, log_rec, taxonomy, options, cntlr, arelle_model):
    ''''
    role
    role-name
    role-uri
    role-definition
    role-used-on
    '''

    # Check if there is a role output attribute. This will copy an existing role
    if 'role' in log_rec.args:
        arelle_role = get_model_object(log_rec.args['role'], cntlr)
        role_info = extract_role_info(arelle_role, taxonomy)
    else:
        role_info = dict()

    if 'role-uri' in log_rec.args:
        role_info['uri'] = log_rec.args['role-uri']
    if 'role-definition' in log_rec.args:
        role_info['definition'] = log_rec.args['role-definition']
    if 'role-used-on' in log_rec.args:
        used_ons = []
        # This is a list of qnames or one of the standard links
        for used_on in json.loads(log_rec.args['role-used-on']):
            if used_on.lower() in _STANDARD_LINK_NAMES:
                used_ons.append(resolve_clark_to_qname(_STANDARD_LINK_NAMES[used_on.lower()], taxonomy))
            else:
                used_ons.append(resolve_clark_to_qname(used_on, taxonomy))
        role_info['used-on'] = used_ons
    
    # a role uri is required
    if 'uri' not in role_info or len(role_info['uri']) == 0 or role_info['uri'] is None:
        raise XodelException(f"Duplicate role. Role {role_info['uri']} is already in the taxonomy")
    if taxonomy.get('Role', role_info['uri']) is None:
        taxonomy.new('Role', role_info['uri'], role_info.get('definition'), role_info.get('used-on'))

def process_relationship(rule_name, log_rec, taxonomy, options, cntlr, arelle_model):
    ''''
    relationship
    relationship-source
    relationship-target
    relationship-order
    relationship-weight
    relationship-preferred-label
    relationship-linkrole-uri
    relationship-role
    relationship-arcrole
    relationship-attribute
    relationship-id
    '''
    # Check if there is a relationship output attribute. This will copy an existing role
    if 'relationship' in log_rec.args:
        arelle_rel = get_model_object(log_rec.args['relationship'], cntlr)
        rel_info = extract_rel_info(arelle_rel, taxonomy)
    else:
        rel_info = dict()
    
    # get source and target concepts
    source_concept = taxonomy.get('Concept', rel_info['source'])
    if source_concept is None:
        raise XodelException(f"While createing a relationship, concept {rel_info['source'].clark} is not in the taxonomy")
    
    target_concept = taxonomy.get('Concept', rel_info['target'])
    if target_concept is None:
        raise XodelException(f"While createing a relationship, concept {rel_info['target'].clark} is not in the taxonomy")
    
    # Get the extended link element
    if rel_info['type'] in _STANDARD_LINK_NAMES:
        link_name = resolve_clark_to_qname(_STANDARD_LINK_NAMES[rel_info['type']], taxonomy)
    else:
        link_name = rel_info['type']

    # Get the arc element
    arc_name = resolve_clark_to_qname(_STANDARD_ARC_NAME.get(link_name.clark), taxonomy)
    if arc_name is None:
        raise XodelException(f"Cannot determine the correct arc name for a relationship in {link_name.clark} extended link")

    # Convert the role and arcrole to SXM objects
    role = taxonomy.get('Role', rel_info['role-uri'])
    if role is None and rel_info['role-uri'] == _STANDARD_EXTENDED_LINK_ROLE:
        role = taxonomy.new('Role', _STANDARD_EXTENDED_LINK_ROLE)
    
    arcrole = taxonomy.get('Arcrole', rel_info['arcrole'])
    if arcrole is None:
        if rel_info['arcrole'] in _STANDARD_ARCROLES:
            arcrole = taxonomy.new('Arcrole', rel_info['arcrole'], None, None, None)
        else:
            raise XodelException(f"Arcrole {rel_info['arcrole']} is not defined in the taxonomy")

    # Need to get or create the SXMNetwork
    network = taxonomy.get('Network', link_name, arc_name, arcrole, role) or \
              taxonomy.new('Network', link_name, arc_name, arcrole, role)
    # Add the relationship
    taxonomy.new('Relationship', network, source_concept, target_concept, rel_info.get('order', 1),
                                 rel_info.get('weight'), rel_info.get('preferred-label'), rel_info.get('attribute', dict()))

def get_model_object(object_string, cntlr):
    arelle_model_id, object_id = json.loads(object_string)
    arelle_model = get_arelle_model(cntlr, arelle_model_id)
    return arelle_model.modelObject(object_id)

def no_sort(log_infos, _cntlr):
    # really - don't do anything - sort order doesn't matter
    return log_infos

def role_uri_sort(log_infos, cntlr):
    uris = dict()
    for log_info in log_infos:
        if 'role-uri' in log_info[1].args:
            uri = log_info[1].args['role-uri']
        elif 'role' in log_info[1].args:
            model_role = get_model_object(log_info[1].args['role'], cntlr)
            if model_role is None:
                raise XodelException(f"Cannot find arelle role")
            else:
                uri = model_role.roleURI
        if uri in uris:
            raise XodelException(f"Duplicate role {uri}")
        uris[uri] = log_info

    result = []
    for key in sorted(uris.keys()):
        result.append(uris[key])
    
    return result

def uri_sort(log_rec):
    if 'role-uri' in log_rec.args:
        return log_rec.args['role-uri']
    elif 'role' in log_rec.args:
        model_role = get_model_object(log_rec)

# XODAL Processing Order
_XODEL_COMPONENT_ORDER = collections.OrderedDict({
    'taxonomy': (process_taxonomy, no_sort),
    'type': (process_type, type_sort),
    'concept': (process_concept, no_sort),
    'role': (process_role, role_uri_sort),
    'relationship': (process_relationship, no_sort),
})


def build_taxonomy_model(log, options, cntlr, arelle_model):

    # Create the model manager. This will contain all the taxonomies that are created
    models = XodelModelManager

    # organize the rule results
    results_by_component = collections.defaultdict(list)
    for rule_name, log_recs in log.items():
        for log_rec in log_recs:
            # get the output attributes that are in the log rec - see if they are a xodal output attribute and translate to a taxonomy components
            tax_components = {_XODEL_OUTPUT_ATTRIBUTES[x][_COMPONENT_NAME] for x in set(log_rec.args.keys()).intersection(_XODEL_OUTPUT_ATTRIBUTES.keys())}
            for tax_component in tax_components:
                if tax_component is not None:
                    results_by_component[tax_component].append((rule_name, log_rec))
            # Validate the output attibutes. This is just doing some basic type checking.
            for arg_name, arg_value in log_rec.args.items():
                if arg_name in _XODEL_OUTPUT_ATTRIBUTES:
                    validator = _XODEL_OUTPUT_ATTRIBUTES[arg_name][_ATTRIBUTE_VALIDATOR]
                    if not validator(arg_value):
                        attribute_message = _VALIDATOR_FORMAT_MESSAGE.get(validator) or ''
                        if len(attribute_message) > 0:
                            attribute_message += ' '
                        xodel_warning(f"Output Attribute '{arg_name}' is not valid for value '{arg_value[:40]}'. {attribute_message}Found in rule {rule_name}")

    # Process the components in order
    for component, (builder, sorter) in _XODEL_COMPONENT_ORDER.items():
        log_recs = results_by_component.get(component, tuple())
        if len(log_recs) == 0:
            continue # there is nothing to do
        for rule_name, log_rec in sorter(log_recs, cntlr):
            if 'taxonomy-name' not in log_rec.args.keys():
                raise XodelException(f"Rule {rule_name} does not have a 'taxonomy-name' output attribute.")
            if component == 'taxonomy':
                taxonomy = XodelModelManager.create_model(log_rec.args['taxonomy-name'])
                taxonomy.package_base_file_name = make_filename(log_rec.args['taxonomy-name'])
            else:
                taxonomy = XodelModelManager.get_model(log_rec.args['taxonomy-name'])
            
            builder(rule_name, log_rec, taxonomy, options, cntlr, arelle_model)

def make_filename(filename):
    filename = ' '.join(filename.split()) # this normalizes the whitespace
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = (c for c in filename if c in valid_chars)
    return f'{filename}.zip'

def get_target_namespace(node):
    '''Find the <schema> element and get the target namespace'''
    root = node.getroottree().getroot()
    return root.get('targetNamespace')          

class XodelModelManager:
    # This class is just to manage the created taxonomies. It is a class only, never instantiated.
    _models: Dict[str, ModelXbrl] = dict()

    @classmethod
    def get_model(cls: type, model_name: str) -> ModelXbrl:
        if model_name in XodelModelManager._models:
            return XodelModelManager._models[model_name]
        else:
            raise XodelException(f"Taxonomy {model_name} has not been created")
    
    @classmethod
    def get_all_models(cls: type):
        return copy.copy(XodelModelManager._models)

    @classmethod
    def create_model(cls: type, model_name: str) -> ModelXbrl:

        if model_name in XodelModelManager._models:
            raise XodelException(f"Cannot create taxonomy {model_name} because it alreay exists")
        else:
            # Get new model
            from .SimpleXBRLModel import SXM

            new_model: SXM.SXMDTS = SXM.SXMDTS()
            XodelModelManager._models[model_name]: SXM.SXMDTS = new_model
            return new_model

    