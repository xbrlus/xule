'''
Reivision number: $Change: 23365 $
'''

from arelle import FileSource
from arelle import ModelManager
from arelle import PluginManager

import base64
import collections
import copy
import datetime
import decimal
import io
import isodate
import json
import logging
import optparse
import os
import re
import tempfile


# This will hold the xule plugin module
_xule_plugin_info = None

_XBRLI_NAMESPACE = 'http://www.xbrl.org/2003/instance'
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
_INSTANCE_BASE_STRING = '''{
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

class XinceException(Exception):
    pass

class XinceNSMap:
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
        result = f'{nsmap.add_or_get_namespace(self.namespace)}'
        if mark:
            self.mark_as_used(nsmap)
        return result

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

    def serialize(self, nsmap, format='json'):
        result = None
        if format == 'json':
            result = '*'.join((x.serialize(nsmap, mark=True) for x in self.numerators))
            if self.denominators is not None:
                result += '/' + '*'.join((x.serialize(nsmap, mark=True)) for x in self.denominators)

        return result

    def __repr__(self):
        result = '*'.join((x.clark for x in self.numerators))
        if self.denominators is not None:
            result += '/' + '*'.join((x.clark for x in self.denominators)) 

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
    _used_ids = set()
    _last_values = collections.defaultdict(int) # this will default the initial value to 0
    _generators = dict()

    @classmethod
    def get_id_generator(cls, prefix='f'):
        if prefix not in cls._generators:
            def id_generator():
                while True:
                    if cls._last_values[prefix] == 0:
                        # The first time, the id will just be the prefix.
                        next_id = prefix
                    else:
                        next_id =f'{prefix}{cls._last_values[prefix]}'
                    if next_id not in cls._used_ids:
                        # make sure there isn't already an id created that is the same. This can happen if the prefix ends with a number. ie
                        cls._used_ids.add(next_id)
                        yield(next_id)
                    cls._last_values[prefix] += 1
            cls._generators[prefix] = id_generator()

        return cls._generators[prefix]

def getXulePlugin(cntlr):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
    """
    global _xule_plugin_info
    if _xule_plugin_info is None:
        for _plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == 'xule':
                _xule_plugin_info = plugin_info
                break
        else:
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run DQC rules. This plugin should be automatically loaded."), "XinceError", level=logging.ERROR)
    
    return _xule_plugin_info

def getXuleMethod(cntlr, method_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(method_name)

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, optparse.OptionParser):
        parserGroup = optparse.OptionGroup(parser,
                                           "Xule to Instance")
        parser.add_option_group(parserGroup)
    else:
        parserGroup = parser
    
    parserGroup.add_option("--xince-location",
                            action="store",
                            help=_("Directory where files are create"))

    parserGroup.add_option("--xince-file-type",
                            action="store",
                            default="json",
                            help=_("type of output. values are 'json', 'xml'"))

    parserGroup.add_option("--xince-show-xule-log",
                            action="store_true",
                            help=_("Indicates to output the xule log"))

def cmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()

    if options.xince_location is not None and options.xule_rule_set is None:
        parser.error("Xule to instance requires a xule rule set (--xule-rule-set)")

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    # Model is create (file loaded) now ready to create an instance

    if options.xince_location is None:
        # nothing to do
        modelXbrl.info("Xule to Instance plugin is installed but the --xince-location option was not provided. Not creating instances.")
    else:
        create_instance(cntlr, options, modelXbrl)

def create_instance(cntlr, options, modelXbrl):

    # Run Xule rules
    log_capture = run_xule(cntlr, options, modelXbrl)

    # Find instances and facts
    instances, instance_facts = organize_instances_and_facts(log_capture, cntlr)

    for instance_name, taxonomies in instances.items():
        process_instance(instance_name, taxonomies, instance_facts[instance_name], cntlr, options)

def organize_instances_and_facts(log_capture, cntlr):
    '''Arrange the captured log into instances
    
    The return is a dictionary of instances keyed by name and the value is the list of taxonomies for the instance,
    and a dictionary of facts keyed by instance name and the value is a list of the captured log entries that
    belong to that instance'''
    instances = collections.defaultdict(list)
    instance_facts = collections.defaultdict(list)

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
                    instance_facts[log_rec.args['fact-instance']].append({k: v for k, v in log_rec.args.items() if k in fact_keys} | {'message': log_rec.msg, 'rule-name': rule_name})# just take the fact output attributes

    # Check that there are not facts for an instance that was not created with an instance rule.
    fact_bad_instances = set(instance_facts.keys()) - set(instances.keys())
    for  bad_instance in fact_bad_instances:
        issues.append(f"There are {len(instance_facts[bad_instance])} facts in instance {bad_instance} but there is not a rule defining this instance")

    for message in issues:
        cntlr.addToLog(message, 'XinceError', level=logging.ERROR)

    return instances, instance_facts

def process_instance(instance_name, taxonomies, facts, cntlr, options):

    instance = json.loads(_INSTANCE_BASE_STRING)
    # Create an Arelle model of the taxonomy. This is done by adding the taxonomies 
    # as schema refs and loading the file. The model is used to validate as facts are created
    # (i.e. the concept name is valid)
    taxonomy_model = get_taxonomy_model(instance_name, taxonomies, cntlr)
    nsmap = get_initial_nsmap(instance, taxonomy_model)
    # Always keep the 'xbrl' namespace
    nsmap.mark_namespace_as_used('https://xbrl.org/2021')
    # Add the schema refs
    # TODO this could also be role and arcrole refs
    for taxonomy in taxonomies:
        instance['documentInfo']['taxonomy'].append(taxonomy)

    # Add facts
    for fact in facts:
        add_fact(fact, instance, taxonomy_model, nsmap, cntlr)

    # Clean up the namespaces
    #nsmap.remove_unused_namespaces()
    #unused_prefixes =set(instance['namespaces'].keys()) - set(nsmap.map_by_prefix.keys())
    instance['documentInfo']['namespaces'] = nsmap.used_map_by_prefix
    
    
    # Write the file
    output_file_name = os.path.join(options.xince_location, f'{instance_name}.json')
    with open(output_file_name, 'w') as f:
        json.dump(instance, f, indent=2)
    cntlr.addToLog(f"Writing instance file {output_file_name}", "XinceInfo")
    

def get_initial_nsmap(instance, taxonomy_model):
    '''This will add namespaces and their prefixes'''

    # first add the namespaces in the instance. These are the basic ones
    nsmap = XinceNSMap()
    for prefix, ns in instance['documentInfo']['namespaces'].items():
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

def add_fact(fact_info, instance, taxonomy, nsmap, cntlr):
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

    is_valid, fact_value, concept, entity, period, unit, dimensions, decimals, language, footnotes = verify_fact(merged_info, taxonomy, cntlr)

    if is_valid and not errors:
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
        if 'fact-id' in fact_info:
            next_id = next(IDGenerator.get_id_generator(''.join(fact_info['fact-id'].split())))
        else:
            next_id = next(IDGenerator.get_id_generator())
        
        if footnotes is not None:
            process_footnotes(fact_dict, instance, footnotes, fact_info['rule-name'], cntlr)

        instance['facts'][next_id] = fact_dict

def process_footnotes(fact_dict, instance, footnotes, rule_name, cntlr):
    if isinstance(footnotes, dict):
        footnotes = [footnotes,]
    
    for footnote in footnotes:
        if not isinstance(footnote, dict):
            cntlr.addToLog(f"Footnote must be a dictionary, found {type(footnote).__name__}. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
            continue
        if 'arcrole' not in footnote:
            cntlr.addToLog(f"Footnote requires an arcrole. Found in {rule_name}", "XinceError", level=logging.ERROR)
            continue
        if 'content' in footnote and 'fact-id' in footnote:
            cntlr.addToLog(f"Footnote cannot have both 'content' and 'fact-id'. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
            continue
        if 'content' in footnote:
            if 'lang' not in footnote:
                cntlr.addToLog(f"Footnote with text content must also have a 'lang'. Found in rule {rule_name}", "XinceError", level=logging.ERROR)
                continue

            # create the footnote pseudo fact
            footnote_id = next(IDGenerator.get_id_generator('fn'))
            footnote_node = {'value': footnote['content'],
                             'dimensions': {
                                'concept': 'xbrl:note',
                                'noteId': footnote_id,
                                'language': footnote['lang']
                                }}
            instance['facts'][footnote_id] = footnote_node
        elif 'fact-id' in footnote:
            footnote_id = footnote['fact-id']
        # Add the link to the fact
        if 'links' not in fact_dict:
            fact_dict['links'] = dict()

        alias = get_alias(instance, 'linkTypes', footnote['arcrole'])
        if alias not in fact_dict['links']:
            fact_dict['links'][alias] = dict()
        if _STANDARD_ROLE_ALIAS not in fact_dict['links'][alias]:
            fact_dict['links'][alias][_STANDARD_ROLE_ALIAS] = list()

        fact_dict['links'][alias][_STANDARD_ROLE_ALIAS].append(footnote_id)

            

                
    '''
        "links": {
      "footnote": {
        "_": [ "f123", "f456" ]
       }
    }
  },
  "f123": {
    "value": "This is an <b>important</b> footnote",
    "dimensions": {
      "concept": "xbrl:note",
      "noteId": "f123",
      "language": "en"
    },
    '''

def get_alias(instance, alias_type, link_value):
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
    alias = _LINK_ALIASES_BY_URI.get(link_value, next(IDGenerator.get_id_generator(link_value.rsplit('/', 1)[-1])))
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
    footnotes = None

    # Check concept, entity and period exists. These are always required
    for aspect in ('fact-concept', 'fact-entity', 'fact-period'):
        if aspect not in fact_info:
            cntlr.addToLog(f"Fact is missing {aspect} which is required. Rule: {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check concept
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
            fact_value = get_fact_value(fact_info['fact-value'], model_concept, cntlr)
            if fact_value is None:
                # There was a problem with the value
                cntlr.addToLog(f"Fact value '{fact_info['fact-value']}' is not valid for concept '{model_concept.qname.localName}' with type '{model_concept.typeQname.localName}'. Found in rule '{fact_info['rule-name']}'", "XinceError", level=logging.ERROR)
                errors = True
    # check footnotes
    if 'fact-footnote' in fact_info:
        try:
            footnotes = json.loads(fact_info['fact-footnote'])
            if type(footnotes) not in (list, dict):
                cntlr.addToLog(f"Footnotes for fact should be a list or a dictionary, but found {type(footnotes).__name__}. Found in rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
                errors = True
        except json.decoder.JSONDecodeError:
            cntlr.addToLog(f"Footnotes for fact are not a json string. Probably missing 'to-xince'. Found in rule '{fact_info['rule-name']}'", "XinceError", level=logging.ERROR)
            errors = True

    return not errors, fact_value, model_concept, entity, period, unit, dimensions, decimals, language, footnotes

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
    elif val.string().lower() in ('0', 'false'):
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

def run_xule(cntlr, options, modelXbrl):

    # Create a log handler that will capture the messages when the rules are run.
    log_capture_handler = _logCaptureHandler()
    if not options.xince_show_xule_log:
        cntlr.logger.removeHandler(cntlr.logHandler)
    cntlr.logger.addHandler(log_capture_handler)

    # Call the xule processor to run the rules
    call_xule_method = getXuleMethod(cntlr, 'Xule.callXuleProcessor')
    run_options = copy.deepcopy(options)
            
    #xule_args = getattr(run_options, 'xule_arg', []) or []
    #xule_args += list(xule_date_args)
    #setattr(run_options, 'xule_arg', xule_args)
        # Get xule rule set
    # with ts.open(catalog_item['xule-rule-set']) as rule_set_file:
    call_xule_method(cntlr, modelXbrl, options.xule_rule_set, run_options)
    
    # Remove the handler from the logger. This will stop the capture of messages
    cntlr.logger.removeHandler(log_capture_handler)
    if not options.xince_show_xule_log:
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


__pluginInfo__ = {
    'name': 'FERC Renderer',
    'version': '0.9',
    'description': "FERC Tools",
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}