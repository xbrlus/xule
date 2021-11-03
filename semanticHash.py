'''Semantic Hasher

The semantic hasher will create a canonical string of an XBRL instance document and create a hex digest from it.
'''
from arelle.ModelDtsObject import ModelResource
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelValue import qname
from lxml import etree
import datetime
import decimal
import hashlib
import isodate
import optparse
import numpy
import re 

_CNTLR = None
_OPTIONS = None
_HASHES = set()

class SemanticHashException(Exception):
    def __init__(self, code, message, **kwargs ):
        self.code = code
        self.message = message
        self.kwargs = kwargs
        self.args = ( self.__repr__(), )
    def __repr__(self):
        return _('[{0}] exception: {1}').format(self.code, self.message % self.kwargs)

def semanticHashOptions(parser):
	# extend command line options with a save DTS option
    parserGroup = optparse.OptionGroup(parser,
                                    "Semantic Hash",
                                    "Calculates the semantic hash of an XBRL document. Currently only supports instance documents.")
    
    parserGroup.add_option("--semantic-hash",
					  action="store_true",
					  help=_("Flag to return the semantic hash as a hex digest"))

    parserGroup.add_option("--semantic-hash-string", 
                       action="store", 
                       help=_("File name to save the canonicalized string"))

def semanticHashUtilityRun(cntlr, options, *arg, **kwargs):
    # save the controller and the options for use later.
    global _CNTLR, _OPTIONS
    _CNTLR = cntlr
    _OPTIONS = options

def semanticHashRun(cntlr, options, modelXbrl, *args, **kwargs):

    # if the semantic hash options are used, then get the canonical string
    if getattr(options, "semantic_hash", False) or getattr(options, "semantic_hash_string") is not None:
        semanticHashDocument(modelXbrl)

def semanticHashDocument(model_xbrl):

    report_string = semanticHashDocumentString(model_xbrl)
    return hashlib.sha256(report_string.encode())

def semanticHashDocumentString(model_xbrl):
    """Create a hash to uniquely identify the report.

    The semantic hash is based on hashing the facts in the model and digesting the string with the sha256
    algorithm.
    """
    # This is a list of tuples which contain the string of the fact and the original model fact.
    fact_string_map_hashes = [(semanticStringHashFact(fact), fact) for fact in model_xbrl.facts]
    # dedup
    fact_string_map_hashes_dedup = []
    previous_fact_string = ''
    for fact_item in sorted(fact_string_map_hashes, key=lambda x:x[0]):
        if fact_item[0] == previous_fact_string:
            # this is a dup
            fact_string_map_hashes_dedup[-1][1].append(fact_item[1])
        else:
            fact_string_map_hashes_dedup.append((fact_item[0], [fact_item[1],]))
        previous_fact_string = fact_item[0]
    # Get the facts sorted by the hash string. The map will be keyed by the model fact and the value will be the position
    # of the fact after the INSTANCEnum.
    fact_map = dict()
    cur_len = 1
    fact_string_hashes = []
    for fact_item in fact_string_map_hashes_dedup:
        for fact in fact_item[1]:
            fact_map[fact] = cur_len
        cur_len += len(fact_item[0])
        fact_string_hashes.append(fact_item[0])

    footnote_string_hashes = [semanticStringHashFootnote(x, fact_map) for x in model_xbrl.relationshipSet("XBRL-footnotes").modelRelationships]

    report_string = semanticFormat('INSTANCE', '{}{}'.format(''.join(sorted(fact_string_hashes)), ''.join(sorted(footnote_string_hashes))))

    # Check the options if the hashstring should be outputted
    report_hash = hashlib.sha256(report_string.encode()).hexdigest()
    if report_hash not in _HASHES:
        # This is only called the first time.
        _HASHES.add(report_hash)
        if getattr(_OPTIONS, "semantic_hash"):
            # output the hexdigest of the canonical string to the log
            model_xbrl.info("SemanticHash", format(hashlib.sha256(report_string.encode()).hexdigest()))

        if getattr(_OPTIONS, "semantic_hash_string") is not None:
            # write the canonical strint to the file
            with open(_OPTIONS.semantic_hash_string, 'wb') as o:
                o.write(report_string.encode()) 

    return report_string

def semanticStringHashFact(fact):

    if fact.isTuple:
        return semanticHashTuple(fact)
    else:
        fact_name = semanticFormat('QNAME', fact.elementQname.clarkNotation)
        entity = semanticFormat('ENTITY', '{}{}'.format(semanticFormat('ENTITYSCHEME', fact.context.entityIdentifier[0]),
                                                        semanticFormat('ENTITYIDENTIFER', fact.context.entityIdentifier[1])))
        period = semanticHashPeriod(fact.context)
        unit = semanticFormat('UNIT', UOMDefault(fact.unit)) if fact.unit is not None else ''
        dimensions = semanticHashDimensions(fact.context) if len(fact.context.qnameDims) > 0 else ''
        decimals = semanticHashDecimals(fact)
        fact_val = semanticHashFactValue(fact)

        hash_string = '{}{}{}{}{}{}{}'.format(fact_name, entity, period, unit, decimals, dimensions, fact_val)

        return semanticFormat('FACT', hash_string)

def semanticHashTuple(fact):
    tuple = semanticFormat('QNAME', fact.qname.clarkNotation)
    tuple_facts = [semanticStringHashFact(x) for x in fact.modelTypleFacts].sort()
    return semanticFormat('TUPLE', '{}{}'.format(tuple, ''.join(tuple_facts)))

def semanticHashPeriod(context):
    if context.isStartEndPeriod:
        if (context.endDatetime.time().hour == 0 and 
            context.endDatetime.time().minute == 0 and
            context.endDatetime.time().second == 0 and
            context.endDatetime.time().microsecond == 0):
            end = (context.endDatetime - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            end = context.endDatetime.isoformat()

        period = semanticFormat('DURATION', '{}{}'.format(semanticFormat('START', context.startDatetime.strftime('%Y-%m-%d')),
                                                            semanticFormat('END', end)))
    elif context.isInstantPeriod:
        if (context.instantDatetime.time().hour == 0 and
            context.instantDatetime.time().minute == 0 and
            context.instantDatetime.time().second == 0 and
            context.instantDatetime.time().microsecond == 0):
            period = semanticFormat('INSTANT', (context.instantDatetime - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
        else:
            period = semanticFormat('INSTANT', context.instantDatetime.isoformat())
    else:
        period = semanticFormat('FOREVER', '')

    return semanticFormat('PERIOD', period)

def semanticHashDimensions(context):

    normalized_dimensions = [
        semanticFormat('DIMVALUE', '{}{}'.format(semanticFormat('DIM', dim.clarkNotation), 
                                                 semanticHashMember(context.qnameDims[dim])))
                        for dim in context.qnameDims.keys()]

    return semanticFormat('DIMS', ''.join(sorted(normalized_dimensions)))

def semanticHashMember(modelDimension):
    if modelDimension.isExplicit:
        return semanticFormat('MEMBER', modelDimension.memberQname.clarkNotation)
    elif modelDimension.isTyped:
        return semanticFormat('MEMBER', canonicalizeTypedDimensionMember(modelDimension.typedMember))
    else:
        raise SemanticHashException("sh:UnknownMemberType",
                            _("Dimension member is not explicit or typed"))

def semanticHashDecimals(fact):
    if not fact.isNumeric:
        return ''
    else:
        if fact.precision is not None:
            raise SemanticHashException("sh:PrecisionNotSupported",
                            _("The precision attribute of a fact is not supported"))
        if fact.decimals is None:
            return ''
        else:
            return semanticFormat('DECIMALS', 'INF' if fact.decimals == 'INF' else str(int(fact.decimals)))

def semanticStringHashFootnote(footnote_rel, obj_map):
    from_hash_string = semanticHashObject(footnote_rel.fromModelObject, obj_map)
    to_hash_string = semanticHashObject(footnote_rel.toModelObject, obj_map)

    arc_element = semanticFormat('ARC', footnote_rel.qname.clarkNotation)
    el_role = semanticFormat('ROLE', footnote_rel.linkrole)
    arc_role = semanticFormat('ARCROLE', footnote_rel.arcrole)
    from_obj= from_hash_string
    to_obj = to_hash_string

    return semanticFormat('FOOTNOTE', '{}{}{}{}{}'.format(arc_element, el_role, arc_role, from_obj, to_obj))

def semanticHashObject(model_obj, obj_map):
    if isinstance(model_obj, ModelFact):
        return semanticFormat('LOCATOR', '{}'.format(obj_map[model_obj]))
    elif isinstance(model_obj, ModelResource):
        return semanticStringHashResource(model_obj)
    else:
        raise SemanticHashException("sh:UnknownResourceType",
                            _("Found resource of unknown type: {}".format(type(model_obj).__name__)))

def semanticStringHashResource(resource):
    res_element = semanticFormat('QNAME', resource.qname.clarkNotation)
    role = semanticFormat('ROLE', resource.role or "http://www.xbrl.org/2003/role/footnote")
    lang = semanticFormat('LANGUAGE', resource.xmlLang.lower()) if resource.xmlLang is not None else ""

    if resource.elementQname.clarkNotation == "{http://www.xbrl.org/2003/linkbase}footnote":
        # This could be a string, XHTML or a combination of both. 
        if len(resource) == 0: # This does not have any XHTML content
            res_text = resource.textValue or ''
        else: # there is XHTML content
            res_text = canonicalizeXML(resource, include_node_tag=False)

    res_value = semanticFormat('VALUE', res_text)

    return semanticFormat('RESOURCE', '{}{}{}{}'.format(res_element, role, lang, res_value))

def semanticHashFactValue(fact):
    if fact.isNil: #empty value
        return semanticFormat('VALUE', '')

    # Textblocks are special because they can contain xml. This will capture if the typed is
    # derived from a textBlock
    original_text_block_qname = qname('http://www.xbrl.org/dtr/type/non-numeric', 'textBlockItemType')
    new_text_block_qname = qname('http://www.xbrl.org/dtr/type/2020-01-21', 'textBlockItemType')
    fraction_qname = qname('http://www.xbrl.org/2003/instance', 'fractionItemType')
    if fact.concept.instanceOfType(original_text_block_qname) or fact.concept.instanceOfType(new_text_block_qname):
        base_type = 'textBlock'
    elif fact.concept.instanceOfType(fraction_qname):
        base_type = 'fraction'
    else:
        base_type = fact.concept.baseXsdType

    if base_type == 'QName':
        string_value = (fact.xValue.namespaceURI, fact.xValue.localName)
    elif base_type == 'textBlock':
        string_value = fact
    elif base_type == 'fraction':
        string_value = fact
    else:
        string_value = fact.value

    return semanticFormat('VALUE', canonicalizeValue(base_type, string_value))

def canonicalizeValue(base_type, string_value):
    if base_type == 'XBRLI_DATEUNION':
        # This could be a date or a datetime.
        if 'T' in string_value:
            base_type = 'dateTime'
        else:
            base_type = 'date'
    value_string_hasher = _CANONICAL_METHODS.get(base_type)
    if value_string_hasher is None:
        raise SemanticHashException("sh", _("Do not have a canonicalizer for type {}".format(base_type)))
    if base_type == 'QName':
        return_value = value_string_hasher(*string_value)
    elif base_type == 'textBlock':
        return_value = value_string_hasher(string_value)
    elif base_type == 'normalizedString':
        return_value = value_string_hasher(string_value)
    elif base_type == 'fraction':
        return_value = value_string_hasher(string_value)
    else:
        # This re will collapse whitespaces
        return_value = value_string_hasher(re.sub(r"[ \t\n\r]+", ' ', string_value).strip(' '))

    return return_value

def semanticFormat(name, str_val):
    return "{}{}.{}".format(name.upper(), len(str_val), str_val)

def UOMDefault(unit):
    numerator = '*'.join(x.clarkNotation for x in unit.measures[0])
    denominator = '*'.join(x.clarkNotation for x in unit.measures[1])
    
    if numerator != '':
        if denominator != '':
            return '/'.join((numerator, denominator))
        else:
            return numerator

def canonicalizeTypedDimensionMember(member):
    element = member.modelXbrl.qnameConcepts.get(member.elementQname)
    base_type = element.baseXsdType
    if base_type == 'QName':
        string_value = (member.xValue.namespaceURI, member.xValue.localName)
    else:
        string_value = member.textValue

    return canonicalizeValue(base_type, string_value)

def canonicalizeDecimal(string_value):
    try:
        internal = decimal.Decimal(string_value).normalize().as_tuple()
    except:
        raise SemanticHashException("sh", _("Cannot convert decimal value '{}'".format(string_value)))
    
    if internal[2] < 0:
        whole = internal[1][:internal[2]]
        fraction = tuple(0 for x in range(internal[2] * -1 - len(internal[1][internal[2]:]))) + internal[1][internal[2]:]
    else:
        whole = internal[1] + tuple(0 for x in range(internal[2]))
        fraction = (0,)
    if len(whole) == 0:
        whole = (0,)
    if len(fraction) == 0:
        fraction = (0,)

    return '{}{}.{}'.format('-' if internal[0] == 1 else '',
                            ''.join((str(x) for x in whole)),
                            ''.join((str(x) for x in fraction)))
    
def canonicalizeFloat(string_value):
    internal = float(string_value)
    almost = numpy.format_float_scientific(internal, exp_digits=1, trim='0')
    return almost.replace('e+', 'E')

def canonicalizeInteger(string_value):
    internal = int(string_value)
    return '{}{}'.format('-' if internal < 0 else '', abs(internal))

def canonicalizeFraction(fact):
    numerator = None
    denominator = None
    for child in fact:
        if child.tag == '{http://www.xbrl.org/2003/instance}numerator':
            numerator = child.text
        if child.tag == '{http://www.xbrl.org/2003/instance}denominator':
            denominator = child.text

    if numerator is None or denominator is None:
        raise SemanticHashException("sh", _("Found a fractio without a numerator or denominator"))

    return '{}/{}'.format(canonicalizeDecimal(numerator), canonicalizeDecimal(denominator))

def canonicalizeDuration(string_value):
    internal = isodate.parse_duration(string_value)
    return isodate.duration_isoformat(internal)

def canonicalizeLanguage(string_value):
    return string_value.lower()

def canonicalizeQName(namespace, local_part):
    return '{{{}}}{}'.format(namespace, local_part)

def canonicalizeBoolean(string_value):
    if string_value.strip().lower() == 'true' or string_value.strip().lower() == 1:
        return 'true'
    else:
        return 'false'

def canonicalizeString(string_value):
    return re.sub(r"[ \t\n\r]+", ' ', string_value).strip(' ') # collapse multiple spaces, tabs, line feeds and returns to single space

def canonicalizeNormalizedString(string_value):
    return re.sub(r"[\t\n\r]", ' ', string_value) # replace tab, line feed, return with space (XML Schema Rules, note: does not include NBSP)

def canonicalizeTime(string_value, date_shift=False):
    day_offset = 0
    re_match = re.fullmatch('(?P<hour>\d\d):(?P<minute>\d\d):(?P<second>\d+(\.\d*)?)((?P<tz_direction>[-+])(?P<tz_time>\d\d:\d\d)|(?P<utc>Z))?', string_value)
    if re_match is None:
        raise SemanticHashException("sh", _("Cannot canonicalize time {}".format(string_value)))
    time_dict = re_match.groupdict()

    internal = isodate.parse_time(string_value)
    offset = internal.utcoffset()
    if offset is not None:
        offset_multiplier = -1 if offset.days >= 0 else 1
        seconds = decimal.Decimal((internal.hour * 60 * 60) + (internal.minute * 60) + internal.second + (decimal.Decimal(internal.microsecond)/1000000))
        new_total_seconds = seconds + (((offset.days * 24 * 60 * 60) + offset.seconds) * offset_multiplier)
        day_offset = new_total_seconds // 86400
        day_offset += -1 if day_offset.is_signed() else 0
        new_total_seconds %= 86400 # Number of seconds in a day
        if new_total_seconds < 0:
            new_total_seconds += 86400
    else:
        new_total_seconds = decimal.Decimal((internal.hour * 60 * 60) + (internal.minute * 60) + internal.second)

    new_hour = new_total_seconds // (60 * 60)
    new_minute = (new_total_seconds - (new_hour * 60 * 60)) // 60
    new_second = new_total_seconds - (new_hour * 60 * 60) - (new_minute * 60)
    return_string = '{:02g}:{:02g}:{:02.100g}{}'.format(new_hour, new_minute, new_second, '' if offset is None else 'Z') 

    if date_shift:
        return return_string, int(day_offset)
    else:
        return return_string

def canonicalizeDateTime(string_value):
    re_match = re.fullmatch('(?P<year>-?\d\d\d\d\d*)-(?P<month>\d\d)-(?P<day>\d\d)(T(?P<time>.*))?', string_value)
    if re_match is None:
        raise SemanticHashException("sh", _("Cannot canonicalize dateTime {}".format(string_value)))
    day_offset = 0
    t = re_match.groupdict()['time']
    if t is not None:
        # Check if the time is 24:00:00. This is a special time indicating end of day
        if t.startswith('24:00:00'):
            day_offset += 1
            time_zone = t[8:]
            time_string = '00:00:00{}'.format(time_zone)
        else:
            time_string = t
        time_part, day_shift = canonicalizeTime(time_string, date_shift=True)
        day_offset += day_shift
    else:
        time_part = ''

    # This can only handle years between 1 and 9999 (this is a limitation of the datetime.date class)
    internal_date = datetime.date(year=int(re_match.groupdict()['year']), month=int(re_match.groupdict()['month']), day=int(re_match.groupdict()['day']))
    shifted_date = internal_date + datetime.timedelta(days=day_offset)
    return '{}{}{}'.format(shifted_date.isoformat(), '' if time_part == '' else 'T', time_part)

def canonicalizeQName(ns, local_name):
    return '{{{}}}{}'.format(ns, local_name)

def canonicalizeTextBlock(content):
    # The wrapper allows fragments that don't start with a tag to be parsed. i.e. "abc <div>this is in the div</div>". This
    # example would not parse becasue it starts with text and not a tag.
    wrapper = '<top xmlns="http://www.w3.org/1999/xhtml">{}</top>'.format(content.value.strip())
    xml_content = etree.fromstring(wrapper)
    
    return_value =  canonicalizeXML(xml_content, include_node_tag=False)
    return return_value

def canonicalizeXML(node, include_node_tag=True):
    string_value = ''
    if include_node_tag:
        string_value = semanticFormat('TAG', node.tag)
        if len(node.attrib) > 0:
            attributes = []
            for att_name, att_value in node.attrib.items():
                att_name_string = semanticFormat('ATT_NAME', att_name)
                att_value_string = semanticFormat('ATT_VALUE', att_value)
                attributes.append(att_name_string + att_value_string)
            string_value += semanticFormat('ATTRIBUTES', ''.join(sorted(attributes)))

    if node.text is not None and len(canonicalizeString(node.text)) > 0:
        string_value += semanticFormat('T', canonicalizeString(node.text))
    for child in node:
        string_value += canonicalizeXML(child)

    if include_node_tag and node.tail is not None and len(canonicalizeString(node.tail)) > 0:
        string_value += semanticFormat('T', canonicalizeString(node.tail))
    
    if include_node_tag:
        return semanticFormat('NODE', string_value)
    else:
        return string_value # the calling function will handle the semantic format

_CANONICAL_METHODS = {

'decimal': canonicalizeDecimal,
'float': canonicalizeFloat,
'double': canonicalizeFloat,
'integer': canonicalizeInteger,
'nonPositiveInteger': canonicalizeInteger,
'negativeInteger': canonicalizeInteger,
'long': canonicalizeInteger,
'int': canonicalizeInteger,
'short': canonicalizeInteger,
'byte': canonicalizeInteger,
'nonNegativeInteger': canonicalizeInteger,
'unsignedLong': canonicalizeInteger,
'unsignedInt': canonicalizeInteger,
'unsignedShort': canonicalizeInteger,
'unsignedByte': canonicalizeInteger,
'positiveInteger': canonicalizeInteger,

'monetary': canonicalizeDecimal,
'shares': canonicalizeDecimal,
'pure': canonicalizeDecimal,
'fraction': canonicalizeFraction,
'string': canonicalizeString,
'boolean': canonicalizeBoolean,
'hexBinary': canonicalizeString,
'base64Binary': canonicalizeString,
'anyURI': canonicalizeString,
'QName': canonicalizeQName, # This will never be used.

'duration': canonicalizeDuration,
'dateTime': canonicalizeDateTime,
'time': canonicalizeTime,
'date': canonicalizeString,
'gYearMonth': canonicalizeString,
'gYear': canonicalizeString,
'gMonthDay': canonicalizeString,
'gDay': canonicalizeString,
'gMonth': canonicalizeString,
'normalizedString': canonicalizeNormalizedString,
'token': canonicalizeString,
'language': canonicalizeLanguage,
'Name': canonicalizeString,
'NCName': canonicalizeString,

'textBlock': canonicalizeTextBlock

}

__pluginInfo__ = {
    'name': 'Semantic Hasher',
    'version': '0.1',
    'description': 'Creates a semantic hash of an XBRL document',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2021',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None,
    'semanticHash.hashDocument': semanticHashDocument,
    'semanticHash.hashDocumentString': semanticHashDocumentString,
    'CntlrCmdLine.Options': semanticHashOptions,
    'CntlrCmdLine.Utility.Run': semanticHashUtilityRun,
    'CntlrCmdLine.Xbrl.Run': semanticHashRun
    }