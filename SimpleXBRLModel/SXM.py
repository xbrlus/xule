import collections
import copy
import decimal
import re
from weakref import KeyedRef

# Used to map where to save new objects. The key is the name of the SXM object that is being saved.
_SAVE_LOCATIONS = {
    'Concept': {'attribute': 'concepts',
                'key': ('name',)},
    'Element': {'attribute': 'elements', 
                'key': ('name',)},
    'Network': {'attribute': 'networks', 
                'key': ('link_name', 'arc_name', 'arcrole', 'role')},
    'Arcrole': {'attribute':'arcroles', 
                'key': ('arcrole_uri',)},
    'Role' : {'attribute': 'roles', 
              'key': ('role_uri',)},
    'Type': {'attribute': 'types',
             'key': ('name',)},
    'Cube': {'attribute': 'cubes',
             'key': ('role', 'concept')},
    'TypedDomain': {'attribute': 'typed_domains',
                    'key': ('name',)},
    'Label': {'attribute': '_labels',
              'key': ('role', 'language'),
              'dups': True},
    'Reference': {'attribute': '_references',
                  'key': ('role',),
                  'dups': True},
    'PartElement': {'attribute': 'part_elements',
              'key': ('name',)},
    'Document': {'attribute': 'documents',
                 'key': ('uri',)},
    'PackageEntryPoint': {'attribute': 'entry_points',
                          'key': ('identifier',)}
}

_STANDARD_ARCROLES = {
    "http://www.w3.org/1999/xlink/properties/linkbase",
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

# _STANDARD_ROLES = {
#     'http://www.xbrl.org/2003/role/label',
#     'http://www.xbrl.org/2003/role/terseLabel',
#     'http://www.xbrl.org/2003/role/verboseLabel',
#     'http://www.xbrl.org/2003/role/totalLabel',
#     'http://www.xbrl.org/2003/role/periodStartLabel',
#     'http://www.xbrl.org/2003/role/periodEndLabel',
#     'http://www.xbrl.org/2003/role/documentation',
#     'http://www.xbrl.org/2003/role/definitionGuidance',
#     'http://www.xbrl.org/2003/role/disclosureGuidance',
#     'http://www.xbrl.org/2003/role/presentationGuidance',
#     'http://www.xbrl.org/2003/role/measurementGuidance',
#     'http://www.xbrl.org/2003/role/commentaryGuidance',
#     'http://www.xbrl.org/2003/role/exampleGuidance',
#     'http://www.xbrl.org/2003/role/positiveLabel',
#     'http://www.xbrl.org/2003/role/positiveTerseLabel',
#     'http://www.xbrl.org/2003/role/positiveVerboseLabel',
#     'http://www.xbrl.org/2003/role/negativeLabel',
#     'http://www.xbrl.org/2003/role/negativeTerseLabel',
#     'http://www.xbrl.org/2003/role/negativeVerboseLabel',
#     'http://www.xbrl.org/2003/role/zeroLabel',
#     'http://www.xbrl.org/2003/role/zeroTerseLabel',
#     'http://www.xbrl.org/2003/role/zeroVerboseLabel',
#     'http://www.xbrl.org/2003/role/link'
# }

_STANDARD_ROLES = {'http://www.xbrl.org/2003/role/link':'Standard extended link role',
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

_DOCUMENT_TYPES = collections.namedtuple('DocumentTypes',
                                        ('SCHEMA', 'LINKBASE', 'OTHER'))('taxonomy-schema',
                                                                    'taxonomy-linkbase',
                                                                    'other')
_DOCUMENT_CONTENT_TYPES = collections.namedtuple('DocumentContentTypes',
                                                ('CONTENT', 
                                                'ARCROLE_REF', 
                                                'ROLE_REF', 
                                                'IMPORT', 
                                                'LINKBASE_REF'))('content',
                                                                    'arcrole_ref',
                                                                    'role_ref',
                                                                    'import',
                                                                    'linbase_ref')

_ALLOWED_DOCUMENT_CONTENT = {
    'Concept': {_DOCUMENT_TYPES.SCHEMA},
    'Element' : {_DOCUMENT_TYPES.SCHEMA},
    'Arcrole' : {_DOCUMENT_TYPES.SCHEMA}, 
    'Role': {_DOCUMENT_TYPES.SCHEMA}, 
    'Type': {_DOCUMENT_TYPES.SCHEMA},  
    'PartElement': {_DOCUMENT_TYPES.SCHEMA}, 
    'TypedDomain': {_DOCUMENT_TYPES.SCHEMA},
    'Label': {_DOCUMENT_TYPES.LINKBASE}, 
    'Reference': {_DOCUMENT_TYPES.LINKBASE}, 
    'Cube': {_DOCUMENT_TYPES.LINKBASE}, 
    'Primary': {_DOCUMENT_TYPES.LINKBASE},
    'Dimension': {_DOCUMENT_TYPES.LINKBASE},
    'Member': {_DOCUMENT_TYPES.LINKBASE}, 
    'Relationship': {_DOCUMENT_TYPES.LINKBASE}, 
}

_TYPED_DOMAIN_REF_ATTRIBUTE = '{http://xbrl.org/2005/xbrldt}typedDomainRef'
_PERIOD_ATTRIBUTE = '{http://www.xbrl.org/2003/instance}periodType'
_BALANCE_ATTRIBUTE = '{http://www.xbrl.org/2003/instance}balance'

_NUMERIC_XBRL_TYPES = {'{http://www.xbrl.org/2003/instance}decimalItemType': '{http://www.w3.org/2001/XMLSchema}decimal',
                       '{http://www.xbrl.org/2003/instance}floatItemType': '{http://www.w3.org/2001/XMLSchema}float',
                       '{http://www.xbrl.org/2003/instance}doubleItemType': '{http://www.w3.org/2001/XMLSchema}double',
                       '{http://www.xbrl.org/2003/instance}integerItemType': '{http://www.w3.org/2001/XMLSchema}integer',
                       '{http://www.xbrl.org/2003/instance}nonPositiveIntegerItemType': '{http://www.w3.org/2001/XMLSchema}nonPostiveInteger',
                       '{http://www.xbrl.org/2003/instance}negativeIntegerItemType': '{http://www.w3.org/2001/XMLSchema}negativeInteger',
                       '{http://www.xbrl.org/2003/instance}longItemType': '{http://www.w3.org/2001/XMLSchema}long',
                       '{http://www.xbrl.org/2003/instance}intItemType': '{http://www.w3.org/2001/XMLSchema}int',
                       '{http://www.xbrl.org/2003/instance}shortItemType': '{http://www.w3.org/2001/XMLSchema}short',
                       '{http://www.xbrl.org/2003/instance}byteItemType': '{http://www.w3.org/2001/XMLSchema}byte',
                       '{http://www.xbrl.org/2003/instance}nonNegativeIntegerItemType': '{http://www.w3.org/2001/XMLSchema}nonNegativeInteger',
                       '{http://www.xbrl.org/2003/instance}unsignedLongItemType': '{http://www.w3.org/2001/XMLSchema}unsignedLong',
                       '{http://www.xbrl.org/2003/instance}unsignedIntItemType': '{http://www.w3.org/2001/XMLSchema}unsignedInt',
                       '{http://www.xbrl.org/2003/instance}unsignedShortItemType': '{http://www.w3.org/2001/XMLSchema}unsignedShort',
                       '{http://www.xbrl.org/2003/instance}unsignedByteItemType': '{http://www.w3.org/2001/XMLSchema}unsignedByte',
                       '{http://www.xbrl.org/2003/instance}positiveIntegerItemType': '{http://www.w3.org/2001/XMLSchema}positiveInteger',
                       '{http://www.xbrl.org/2003/instance}monetaryItemType': '{http://www.w3.org/2001/XMLSchema}decimal',
                       '{http://www.xbrl.org/2003/instance}sharesItemType': '{http://www.w3.org/2001/XMLSchema}decimal',
                       '{http://www.xbrl.org/2003/instance}pureItemType': '{http://www.w3.org/2001/XMLSchema}decimal',
                       '{http://www.xbrl.org/2003/instance}fractionItemType': None}

_NUMERIC_XML_TYPES = {'{http://www.w3.org/2001/XMLSchema}float',
                      '{http://www.w3.org/2001/XMLSchema}decimal',
                      '{http://www.w3.org/2001/XMLSchema}double',
                      '{http://www.w3.org/2001/XMLSchema}integer',
                      '{http://www.w3.org/2001/XMLSchema}nonPostiveInteger',
                      '{http://www.w3.org/2001/XMLSchema}long',
                      '{http://www.w3.org/2001/XMLSchema}nonNegativeInteger',
                      '{http://www.w3.org/2001/XMLSchema}negativeInteger',
                      '{http://www.w3.org/2001/XMLSchema}int',
                      '{http://www.w3.org/2001/XMLSchema}unsignedLong',
                      '{http://www.w3.org/2001/XMLSchema}positiveInteger',
                      '{http://www.w3.org/2001/XMLSchema}short',
                      '{http://www.w3.org/2001/XMLSchema}unsignedInt',
                      '{http://www.w3.org/2001/XMLSchema}byte',
                      '{http://www.w3.org/2001/XMLSchema}unsignedShort',
                      '{http://www.w3.org/2001/XMLSchema}unsignedByte',
                      


}

class SXMException(Exception):
    pass
class SXMObjectExists(SXMException):
    pass

class _SXMBase:
    '''A base class for all SXM classes'''

    # SXM constants - attached to all classes
    DOCUMENT_TYPES = _DOCUMENT_TYPES
    DOCUMENT_CONTENT_TYPES = _DOCUMENT_CONTENT_TYPES
    ALLOWED_DOCUMENT_CONTENT = _ALLOWED_DOCUMENT_CONTENT

    def __init__(self):
        pass
    
    @staticmethod
    def get_class(class_name):
        full_name = 'SXM{}'.format(class_name)
        if full_name in globals():
            return globals()[full_name]

    @classmethod
    def get_class_name(cls):
        return cls.__name__[3:]

class SXMAttributedBase(_SXMBase):
    '''Án object that has attributes with ditionary values'''
    
    def new(self, class_name, *args, **kwargs):
        '''Create a new Simple XBRL Model object. 

        The *args and **kwargs are the arguments for the object being created.
        '''

        # If save=True is in the arguments, then the value will be saved in the DTS.
        save = bool(kwargs.get('save', True))
        # remove the "save" argument if it is there
        try:
            del kwargs['save']
        except KeyError:
            pass

        class_bit = self.get_class(class_name)
        if class_bit is not None:
            new_object = class_bit(self if isinstance(self, SXMDTS) else self.dts, *args, **kwargs)
        else:
            new_object = None

        # Save the object in the containing object (DTS or Concept) (if it should be save and there is an object)
        if new_object and save:
            self.save(class_name, new_object)

        return new_object

    @staticmethod
    def component_key(component):
        save_info = _SAVE_LOCATIONS.get(component.get_class_name())
        if save_info is None:
            raise SXMException("Component type '{}' does not exist".format(type(component).__name__))
        if len(save_info['key']) == 1:
            key = getattr(component, save_info['key'][0])
        else:
            key = tuple(getattr(component, x) for x in save_info['key'])
        
        return key

    @staticmethod
    def component_attribute_name(component):
        '''This is the name of the dictionary on this object'''
        save_info = _SAVE_LOCATIONS.get(component.get_class_name())
        if save_info is None:
            raise SXMException("Component type '{}' does not exist".format(type(component).__name__))
        return save_info['attribute']

    def component_exists(self, component):
        key = self.component_key(component)
        if key is None:
            raise SXMException("Component type '{}' does not exist".format(type(component).__name__))
        component_dict = getattr(self, self.component_attribute_name(component))
        return key in component_dict

    def save(self, class_name, new_object):
        save_info = _SAVE_LOCATIONS.get(class_name)
        if save_info is not None:
    
            if len(save_info['key']) == 1:
                key = getattr(new_object, save_info['key'][0])
            else:
                key = tuple(getattr(new_object, x) for x in save_info['key'])

            # Check if the object is already created.
            list_of_objects = getattr(self, save_info['attribute'])
            if save_info.get('dups', False):
                if key not in list_of_objects:
                    list_of_objects[key] = set()
                list_of_objects[key].add(new_object)
            else:
                if key in list_of_objects:
                    raise SXMException("{} object with key {} already exists".format(class_name, key))
                list_of_objects[key] = new_object

    def remove(self, del_object):
        class_name = type(del_object).__name__[3:] # This gets the class name by ignoring the SXM as the begining
        try:
            removable = del_object.remove()
        except AttributeError:
            removable = True
        if removable:
            info = _SAVE_LOCATIONS.get(class_name)
            if info is not None:
                if len(info['key']) == 1:
                    key = getattr(del_object, info['key'][0])
                else:
                    key = tuple(getattr(del_object, x) for x in info['key'])
                list_of_objects = getattr(self, info['attribute'])
                if key in list_of_objects:
                    if info.get('dups', False):
                        remove_all_from_list(list_of_objects[key]. del_object)
                        if len(list_of_objects[key]) == 0:
                            del list_of_objects[key]
                    else: # dups not allowed
                        del list_of_objects[key]

        if removable and isinstance(del_object, _SXMDefined) and del_object.document is not None:
            del_object.document.remove_from_document(del_object)

        return removable

    def get(self, class_name, *key):
        save_info = _SAVE_LOCATIONS.get(class_name)
        if save_info is None:
            return None
        else:
            if len(key) == 1:
                key = key[0]
            return getattr(self, save_info['attribute'], dict()).get(key)

    def get_match(self, class_name, match_key):
        ''' Return dts attributes with partial key match.'''
        save_info = _SAVE_LOCATIONS.get(class_name)
        if save_info is None:
            return None
        else:
            results = []
            # allow match_key to be a single item
            if not (isinstance(match_key, list) or isinstance(match_key, tuple)):
                match_key = (match_key,)
            for key, val in getattr(self, save_info['attribute'], dict()).items():
                keep = True
                if len(match_key) > len(key):
                    # a shorter key is ok. It will only require matching on what is provided.
                    raise SXMException("Searching {} with wrong size key".format(class_name))
                for i in range(len(match_key)):
                    if match_key[i] is not None:
                        if match_key[i] != key[i]:
                            keep = False
                if keep:
                    results.append(val)

            return results
    
    def get_utility(self, class_name, class_method):
        try:
            class_bit = globals()['SXM{}'.format(class_name)]
            return getattr(class_bit, class_method)
        except:
            raise SXMException("Unable to get utiltiy class method {} from class {}".format(class_name, class_method))

class _SXMDTSBase(_SXMBase):
    '''An object that is part of a DTS'''
    def __init__(self, dts):
        super().__init__()
        self.dts = dts

class SXMDocument(_SXMDTSBase):
    def __init__(self, dts, document_uri, document_type, target_namespace=None, description=None):
        super().__init__(dts)

        self.uri = document_uri
        self._document_type = document_type
        self.description = description
        self.target_namespace = target_namespace
        self._contents = set()
        self._role_refs = set()
        self._arcrole_refs = set()
        self._imports = set()
        self._linkbase_refs = set()
        # Keeping track of ids by seed
        self._seeds = collections.defaultdict(lambda: 0)
        self._ids = dict() # keyed by content object value is id. 
    
    def __repr__(self):
        return 'Document: {}'.format(str(self))

    def __str__(self):
        return self.uri

    @property
    def document_type(self):
        return self._document_type

    @document_type.setter
    def document_type(self, val):
        if val is not None and val not in self.DOCUMENT_TYPES:
            raise SXMException("Invalid document type: {}".format(val))
        self._document_type = val

    @property 
    def contents(self):
        return frozenset(self._contents)

    @property
    def is_relative(self):
        return not self.is_absolute

    @property
    def is_absolute(self):
        # this is a rather simplified view of what it means to be 'absolute'
        return self.uri.lower().startswith('http:') or self.uri.lower().startswith('https:')

    @property
    def role_refs(self):
        return frozenset(self._role_refs)
    
    @property
    def arcrole_refs(self):
        return frozenset(self._arcrole_refs)
    
    @property
    def imports(self):
        return frozenset(self._imports)

    @property
    def linkbase_refs(self):
        return frozenset(self._linkbase_refs)

    def get_id(self, sxm_object):
        if sxm_object not in self._contents:
            return None
        
        if sxm_object not in self._ids:
            self._ids[sxm_object] = self._next_id(getattr(sxm_object, '_seed_id', None) or sxm_object.get_class_name())
        return self._ids[sxm_object]

    def add(self, sxm_object, content_type='content'):

        if content_type not in _DOCUMENT_CONTENT_TYPES:
            raise SXMException("Invalid content type for adding to a document: {}".format(content_type))

        if content_type == self.DOCUMENT_CONTENT_TYPES.CONTENT and isinstance(sxm_object, _SXMDefined):
            self._contents.add(sxm_object)
            sxm_object._document = self
        elif content_type == self.DOCUMENT_CONTENT_TYPES.ARCROLE_REF and isinstance(sxm_object, SXMArcrole):
            if not sxm_object.is_standard:
                self._arcrole_refs.add(sxm_object)
        elif content_type == self.DOCUMENT_CONTENT_TYPES.ROLE_REF and isinstance(sxm_object, SXMRole):
            if not sxm_object.is_standard:
                self._role_refs.add(sxm_object)
        elif content_type == self.DOCUMENT_CONTENT_TYPES.IMPORT and isinstance(sxm_object, SXMDocument):
            self._imports.add(sxm_object)
        elif content_type == self.DOCUMENT_CONTENT_TYPES.LINKBASE_REF and isinstance(sxm_object, SXMDocument):
            self._linkbase_refs.add(sxm_object)
        else:
            raise SXMException("Simple XBRL Object '{}' cannot be added to a document as a {}.".format(type(sxm_object).__name__, content_type))
    
    def remove_from_document(self, sxm_object, content_type='content'):

        if content_type not in self.DOCUMENT_CONTENT_TYPES:
            raise SXMException("Invalid content type for deleting from document: {}".format(content_type))
        try:
            if content_type == self.DOCUMENT_CONTENT_TYPES.CONTENT and isinstance(sxm_object, _SXMDefined):
                self._contents.remove(sxm_object)
                sxm_object._document = None
                if sxm_object in self._ids:
                    del self._ids[sxm_object]
            elif content_type == self.DOCUMENT_CONTENT_TYPES.ARCROLE_REF and isinstance(sxm_object, SXMArcrole):
                self._arcrole_refs.remove(sxm_object)
            elif content_type == self.DOCUMENT_CONTENT_TYPES.ROLE_REF and isinstance(sxm_object, SXMRole):
                self._role_refs.remove(sxm_object)
            elif content_type == self.DOCUMENT_CONTENT_TYPES.IMPORT and isinstance(sxm_object, SXMDocument):
                self._imports.remove(sxm_object)
            elif content_type == self.DOCUMENT_CONTENT_TYPES.LINKBASE_REF and isinstance(sxm_object, SXMDocument):
                self._linkbase_refs.remove(sxm_object)
            else:
                raise SXMException("Simple XBRL Object '{}' cannot be deleted from a document as a {}.".format(type(sxm_object).__name__, content_type))
        except KeyError:
            pass

    def _next_id(self, seed):
        if len(seed) == 0:
            seed = 'id'
        elif re.match('^[0-9-\.]', seed) is not None: # ids cannot start with a number - or . This should be more robust matching for NCNAME
            seed = 'id_{}'.format(seed)
        if self._seeds[seed] == 0:
            self._seeds[seed] += 1
            return seed
        else:
            id = '{}_{}'.format(seed, str(self._seeds[seed]))
            self._seeds[seed] += 1
            return id

class _SXMDefined(_SXMDTSBase):
    '''Defined objects are defined in a document'''

    def __init__(self, dts, *args, **kwargs):
        super().__init__(dts)
        self._document = None

    @property
    def document(self):
        return self._document

    @document.setter
    def document(self, val):
        if val is not None and not isinstance(val, SXMDocument):
            raise SXMException("Trying to add a {} to a {} instead of a document".format(self.get_class_name), val.get_class_name if isinstance(val, _SXMBase) else type(val).__name__)
        if self._document is not None:
            self._document.remove_from_document(self)
        if val is not None:
            val.add(self)

    @property
    def id(self):
        if self._document is None:
            return None # An id can only be created when the object is in a document
        else:
            return self._document.get_id(self)

class SXMQName(_SXMDTSBase):
    def __init__(self, dts, namespace, local_name, prefix=None):
        super().__init__(dts)
        self.namespace = namespace
        self.local_name = local_name

        if namespace is not None:
            if namespace not in dts.namespaces:
                if prefix is None:
                    # create a new prefix
                    i = 1
                    while 'ns{}'.format(str(i)) in dts.namespaces.values():
                        i += 1
                    prefix = 'ns{}'.format(str(i))
                dts.namespaces[namespace] = prefix
        
    def __repr__(self):
        return "QName: {}".format(str(self))

    def __str__(self):
        return self.clark

    def __hash__(self):
        return hash((self.namespace, self.local_name))

    def __eq__(self, other):
        if isinstance(other, SXMQName):
            return self.namespace == other.namespace and self.local_name == other.local_name
        else:
            return self.clark == other
    
    def __lt__(self, other):
        return str(self) < str(other)

    @property
    def prefix(self):
        return self.dts.namespaces.get(self.namespace)

    @property
    def clark(self):
        if self.namespace is None:
            return self.local_name
        else:
            return '{{{}}}{}'.format(self.namespace, self.local_name)

    @property
    def name_pair(self):
        return self.namespace, self.local_name

class _SXMPackageDTS(_SXMBase):
    # This class just adds package properties to the SXMDTS
    # This is done as a separate class just to separate these properties out
    # for organizational purposes
    def __init__(self):
        self.identifier = None
        self.name = None
        self.name_language = None
        self.description = None
        self.description_language = None
        self.version = None
        self.license_href = None
        self.license_name = None
        self.publisher = None
        self.publisher_language = None
        self.publisher_url = None
        self.publisher_country = None
        self.publication_date = None
        self.entry_points = dict()
        # superceded taxonomies and version reports are not currently supported
        self.rewrites = dict()
        self.other_elements = dict()

class SXMPackageEntryPoint(_SXMDTSBase):
    def __init__(self, dts, identifier):
        super().__init__(dts)
        self.identifier = identifier
        self.names = []
        self.description = None
        self.version = None
        self.documents = []
        self.languages = []
        self.other_elements = dict()
        
class SXMDTS(_SXMPackageDTS, SXMAttributedBase):

    def __init__(self):
        super().__init__()
        self.concepts = dict()
        self.elements = dict()
        self.networks = dict()
        self.arcroles = dict()
        self.roles = dict()
        self.types = dict()
        self.cubes = dict()
        self.typed_domains = dict()
        self.part_elements = dict()
        self.documents = dict()
        self.namespaces = dict()
    
    def __contains__(self, value):
        if isinstance(value, tuple) or isinstance(value, list):
            if len(value) == 2:
                # This is a qname and need to check if it is a concept or element
                qname = SXMQName(self, *value)
                return qname in self.concepts
        elif isinstance(value, SXMConcept):
            return value.name in self.concepts
        elif isinstance(value, SXMArcrole):
            return value in self.arcroles
        elif isinstance(value, SXMRole):
            return value in self.roles

    @property
    def all_elements(self):
        '''Returns all elements (elements, concepts, typed_domains, part_elements'''
        for concept in self.concepts.values():
            yield concept
        for element in self.elements.values():
            yield element
        for typed_domain in self.typed_domains.values():
            yield typed_domain
        for part_element in self.part_elements.values():
            yield part_element

    def remove(self, del_object):
        remove = super().remove(del_object)
        if remove:
            del_object.dts = None

class SXMArcrole(_SXMDefined):

    def __init__(self, dts, arcrole_uri, cycles_allowed, description, used_ons):
        super().__init__(dts)
        self._arcrole_uri = arcrole_uri
        self.description = description
        self.used_ons = used_ons
        self.cycles_allowed = cycles_allowed
    
    @property # make this property immutable because it is used for the hash
    def arcrole_uri(self):
        return copy.copy(self._arcrole_uri)

    @property
    def _seed_id(self):
        return self._arcrole_uri.split('/')[-1]

    def __repr__(self):
        return 'Arcrole: {}'.format(str(self))

    def __str__(self):
        return self.arcrole_uri

    def __hash__(self):
        return hash(self._arcrole_uri)

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    @property
    def networks(self):
        return frozenset(x for x in self.dts.networks.values() if self is x.arcrole)

    @property
    def is_standard(self):
        return self._arcrole_uri in _STANDARD_ARCROLES

    def remove(self):
        return len(self.networks) == 0

class SXMRole(_SXMDefined):
    def __init__(self, dts, role_uri, description=None, used_ons=None):
        super().__init__(dts)
        self._role_uri = role_uri
        self._description = description if not self.is_standard else None
        self.used_ons = used_ons or set()

    @property
    def role_uri(self): # make this property immutable because it is used for the hash
        return copy.copy(self._role_uri)

    @property
    def _seed_id(self):
        return self._role_uri.split('/')[-1]

    @property
    def description(self):
        if self.is_standard:
            return _STANDARD_ROLES[self._role_uri]
        else:
            return self._description

    @description.setter
    def description(self, val):
        if not self.is_standard:
            self._description = val

    def __repr__(self):
        return 'Role: {}'.format(str(self))

    def __str__(self):
        return self.role_uri

    def __hash__(self):
        return hash(self._role_uri)

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    @property
    def networks(self):
        return frozenset(x for x in self.dts.networks.values() if self is x.role)

    @property
    def is_standard(self):
        return self._role_uri in _STANDARD_ROLES

    @property
    def resources(self):
        result = set()
        for concept in self.dts.concepts.values():
            for label_key in concept.labels:
                if label_key[0] == self.role_uri:
                    result |= concept.labels[label_key]
            for ref_key in concept.references:
                if ref_key == self.role_uri:
                    result |= concept.references[ref_key]
    
        return result

    def remove(self):
        return len(self.networks) == 0 and len(self.resources) == 0

class SXMElement(_SXMDefined):
    def __init__(self, dts, name, data_type, abstract, nillable=None, id=None, substitution_group=None, attributes=None):
        super().__init__(dts)

        if substitution_group is not None:
            if not (isinstance(substitution_group, SXMElement) or
                    isinstance(substitution_group, SXMQName)):
                raise SXMException("Substitution group for element '{}' is not an element.".format(
                                    name.clark))
        # calculate
        self._seed_id = id
        self._name = name
        self.type = data_type
        self.is_abstract = abstract
        self.nillable = nillable
        self.substitution_group = substitution_group
        
        self.attributes = dict()
        if attributes is not None:
            for att_name, att_value in attributes.items():
                # these attributes are captured as properties
                if att_name.clark not in ('name', 'type', 'id', 'nillable', 'substitutionGroup', 'abstract', _PERIOD_ATTRIBUTE, _BALANCE_ATTRIBUTE):
                    self.attributes[att_name] = att_value
            
        # elements with anonymous types will have @anonymousType at the end of the type local name. These
        # are types that are inside the <element> tag. The type has to be created before the element. When
        # the element is created, the type is update to indicate the element the type is for.
        if self.type.name.local_name.endswith('@anonymousType'):
            # update the type
            self.type.anonymous_element = self

        if not isinstance(data_type, SXMType):
            raise SXMException("Adding element {} but type is not an SXMType, found '{}'".format(name, type(data_type).__name__))

    def __repr__(self):
        return 'Element: {}'.format(str(self))

    def __str__(self):
        return self._name.clark

    def __hash__(self):
        return hash(self._name.clark)

    def __eq__(self, other):
        if isinstance(other, SXMElement):
            return self.name == other.name
        else:
            return self.name.clark == other

    @property # make this property immutable because it is used for the hash
    def name(self):
        return copy.copy(self._name)

    @property
    def substitution_group_name(self):
        # this returns the qname of the substitution group. The self.substitution_group can be
        # either a qname or another element.
        if self.substitution_group is None:
            return None
        elif isinstance(self.substitution_group, SXMQName):
            return self.substitution_group
        else:
            return self.substitution_group.name

    def derrived_substitution_groups(self, direct_only=True):
        '''Return substitution groups derrived from current element.
        
        If direct_only is true, only go one level down. If fasle, then recurse.'''
        # directly derived types
        results = {x for x in self.dts.elements.values() if x.substitution_group is self}
        results |= {x for x in self.dts.concepts.values() if x.substitution_group is self}
        results |= {x for x in self.dts.part_elements.values() if x.substitution_group is self}
        if not direct_only:
            for derrived in copy.copy(results):
                results |= derrived.derrived_types(False)
        return results

    @property
    def ancestor_substitution_groups(self):
        if self.substitution_group is None:
            return []
        elif isinstance(self.substitution_group, SXMQName):
            return [self.substitution_group,]
        else:
            for element in self.dts.all_elements:
                if element is self.substitution_group:
                    return [self.substitution_group,] + element.ancestor_substitution_groups
            raise SXMException("Cannot find substituion group element '{}'".format(self.substitution_group.name.clark))

    def remove(self):
        if self.type.is_anonymous:
            self.type.anonymous = None
            self.dts.remove(self.type)
        
        return True

class SXMTypedDomain(SXMElement):
    def __init__(self, dts, name, data_type, abstract, nillable, id, substitution_group, attributes):
        super().__init__(dts, name, data_type, abstract, nillable, id, substitution_group, attributes)

    def __repr__(self):
        return 'Typed Domain: {}'.format(str(self))

    @property
    def concepts(self):
        results = set()
        for concept in self.dts.concepts.values():
            if concept.typed_domain is self:
                results.add(concept)
        return results

    def remove(self):
        # Its removeable as long there are no concepts using it
        return len(self.concepts) == 0

class SXMType(_SXMDefined):

    def __init__(self, dts, name, parent_type=None, xml_content=None, anonymous_element=None):
        super().__init__(dts)

        # the xml_content is None when it is a base xbrli item type or a base xml type. Should consider checking this

        self._name = name
        self.parent_type = parent_type
        if self.is_base_xbrl or self.is_base_xml:
            self.content = None
        else:
            self.content = xml_content
        self.anonymous_element = anonymous_element

    @property # make this property immutable because it is used for the hash
    def name(self):
        return copy.copy(self._name)
    
    @property
    def _seed_id(self):
        return self.name.local_name

    def __repr__(self):
        return 'Type: {}'.format(str(self))

    def __str__(self):
        return self._name.clark

    def __hash__(self):
        return hash(self._name.clark)

    def __eq__(self, other):
        return str(self) == str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def elements(self, include_derrived=False):
        # The list of elements that use this type
        results =  {x for x in self.dts.all_elements if x.type is self}
        # Check any derrived types
        if include_derrived:
            for derrived_type in self.derrived_types(False):
                results |= derrived_type.elements
        
        return results

    def derrived_types(self, direct_only=True):
        '''Return types derrived from current type.
        
        If direct_only is true, only go one level down. If fasle, then recurse.'''
        # directly derived types
        results = {x for x in self.dts.types.values() if x.parent_type is self}
        if not direct_only:
            for derrived in copy.copy(results):
                results |= derrived.derrived_types(False)
        return results

    @property
    def base_xbrl_type(self):
        if self.is_base_xbrl:
            return self
        elif self.parent_type is None:
            # This is not an xbrl Type
            return None
        else:
            return self.parent_type.base_xbrl_type

    @property
    def base_xml_type(self):
        # Should add translating the XBRL type into the xml type.
        # For now XBRL types will return None
        if self.is_base_xml:
            return self
        elif self.parent_type is None:
            return None
        else:
            return self.parent_type.base_xml_type

    @property
    def ancestor_types(self):
        if self.parent_type is None:
            return [self,]
        return [self,] + self.parent_type.ancestor_types

    @property 
    def is_xbrl(self):
        return self.base_xbrl_type is not None

    @property
    def is_base_xbrl(self):
        return self._name.namespace == 'http://www.xbrl.org/2003/instance'

    @property
    def is_base_xml(self):
        return self._name.namespace == 'http://www.w3.org/2001/XMLSchema'

    @property
    def is_anonymous(self):
        return self.anonymous_element is not None

    @property
    def is_numeric(self):
        return self.base_xbrl_type in _NUMERIC_XBRL_TYPES or self.base_xml_type in _NUMERIC_XML_TYPES

    def remove(self):
        # check if there are any elements using the type or a type derrived from the type
        # and that there are not types derrived from the type
        return len(self.elements(True)) == 0 and len(self.derrived_types()) == 0

class SXMPartElement(SXMElement):
    def __init__(self, dts, name, data_type, abstract, nillable=None, id=None, substitution_group=None, attributes=None):
        super().__init__(dts, name, data_type, abstract, nillable, id, substitution_group, attributes)

    def __repr__(self):
        return 'Part Element: {}'.format(str(self))
    
    @property
    def parts(self):
        '''Return the parts that use this part element'''
        result = set()
        for concept in self.dts.concepts.values():
            for references in concept.references.values():
                for reference in references:
                    for part in reference.parts:
                        if part.part_element is self:
                            result.add(part)
        
        return result
        
    def remove(self):
        return super().remove and len(self.parts) == 0
    
class SXMConcept(SXMElement, SXMAttributedBase):
    def __init__(self, dts, name, data_type, abstract, nillable, period_type, balance_type, substitution_group, id=None, attributes=None, typed_domain=None):
        super().__init__(dts, name, data_type, abstract, nillable, id, substitution_group, attributes)
        
        if not (isinstance(substitution_group, SXMConcept) or
                isinstance(substitution_group, SXMQName)):
            raise SXMException("Substitution group for concept '{}'is not a concept or a base item or tuple.".format(
                                name.clark))
                
        self.period_type = period_type
        self.balance_type = balance_type
        self.typed_domain = typed_domain

        self._from_concept_relationships = collections.defaultdict(set)
        self._to_concept_relationships = collections.defaultdict(set)
        self._labels = dict()
        self._references = dict()

        # remove typed domain ref if is in the attributes
        for att_name in list(self.attributes.keys()):
            if att_name.clark == _TYPED_DOMAIN_REF_ATTRIBUTE:    
                try:
                    del self.attributes[att_name]
                except KeyError:
                    pass
                break # don't need to finish only deleting one attribute

    def __repr__(self):
        return 'Concept: {}'.format(str(self))

    @property
    def from_concept_relationships(self):
        return copy.copy(self._from_concept_relationships)

    @property
    def to_concept_relationships(self):
        return copy.copy(self._to_concept_relationships)
    
    @property
    def labels(self):
        return copy.copy(self._labels)
    
    @property
    def references(self):
        return copy.copy(self._references)

    def add_label(self, label_role, language, text):
        label = self.new('Label', self, label_role, language, text)
        return label

    def add_reference(self, reference_role, parts):
        ref = self.new('Reference', self, reference_role, parts)
        return ref

    def derrived_concepts(self, direct_only=True):
        '''Return concepts derrived from current concept (based on the substitution group).
        
        If direct_only is true, only go one level down. If fasle, then recurse.'''
        # directly derived types
        results = {x for x in self.dts.concepts.values() if x.substitution_group is self}
        if not direct_only:
            for derrived in copy.copy(results):
                results |= derrived.derrived_types(False)
        return results

    def remove(self):
        remove = (super().remove and 
                len(self._to_concept_relationships) == 0 and 
                len(self._from_concept_relationships) == 0 and
                len(self.derrived_concepts()) == 0
                )
        if remove:
            for resources in self.references.values():
                for resource in resources:
                    resource.document = None
            for resources in self.labels.values():
                for resource in resources:
                    resource.document = None

class SXMResource(_SXMDefined):
    def __init__(self, dts, concept, role, content=None, attributes=None):
        if not isinstance(role, SXMRole):
            raise SXMException("Trying to add resource with an invalid role. Found {}: {}".format(type(role).__name__, str(role)))
        super().__init__(dts)
        self.concept = concept
        self.role = role
        self.content = content
        # Should ensure that role is not in the attributes.
        self.attributes = attributes

class _SXMLabelBase(SXMResource):
    def __init__(self, dts, concept, label_role, language, content, attributes=None):
        super().__init__(dts, concept, label_role, content, attributes)
        self.language = language

class SXMLabel(_SXMLabelBase):
    pass

class _SXMReferenceBase(SXMResource):
    pass

# Future - add generic label and generic reference resources.

class SXMReference(_SXMReferenceBase):
    def __init__(self, dts, concept, reference_role, parts, attributes=None):
        # Check that the parts are actual SXMParts
        if any(not isinstance(x, SXMPart) for x in parts):        
            raise SXMException("Trying to add a reference where a part is not a SXMPart")

        super().__init__(dts, concept, reference_role, None, attributes)
        self.parts = parts

    def remove(self):
        return len(self.parts) == 0

class SXMPart(_SXMDefined):
    def __init__(self, dts, part_element, part_content):
        super().__init__(dts)
        self.part_element = part_element
        self.content = part_content

    @property
    def part_name(self):
        return self.part_element.name

class SXMNetwork(_SXMDefined):
    def __init__(self, dts, link_name, arc_name, arcrole, role):
        if not isinstance(role, SXMRole):
            raise SXMException("Trying to add a network with an invalid role. Found {}: {}".format(type(role).__name__, str(role)))
        if not isinstance(arcrole, SXMArcrole):
            raise SXMException("Trying to add a network with an invalice arc role. Found {}: {}".format(type(arcrole).__name__, str(arcrole)))
        
        super().__init__(dts)
        self.link_name = link_name
        self.arc_name = arc_name
        self.arcrole = arcrole
        self.role = role
        self._from_relationships = collections.defaultdict(list)
        self._to_relationships = collections.defaultdict(list)
    
    def __contains__(self, concept):
        # Determines if the concept is in the network
        return self in (concept.from_concept_relationships.keys() | concept.to_concept_relationships.keys())

    @property
    def from_relationships(self):
        # protect the relationships, send a copy
        return copy.copy(self._from_relationships)
    
    @property
    def to_relationships(self):
        # protect the relationships, send a copy
        return copy.copy(self._to_relationships)

    @property
    def relationships(self):
        return {y for x in self._from_relationships.values() for y in x} |  {y for x in self._to_relationships.values() for y in x}

    @property
    def roots(self):
        return tuple(self._from_relationships.keys() - self._to_relationships.keys())

    @property
    def concepts(self):
        return tuple(self._from_relationships.keys() | self._to_relationships.keys())

    def add_relationship(self, from_concept, to_concept, order='calc', weight=None, preferred_label=None, attributes=None):
        if order == 'calc':
            # Calculate the order based on the order of the last child
            order = max([0,] + [x.order or 0 for x in self.get_children(from_concept)]) + 1
        return self.dts.new('Relationship', self, from_concept, to_concept, order, weight, preferred_label, attributes)

    def get_children(self, parent_concept):
        return sorted(self._from_relationships.get(parent_concept, list()), key=lambda x: x.order)

    def get_descendants(self, parent_concept):
        results = []
        for child in self.get_children(parent_concept):
            if child not in results:
                results.append(child)
                results += self.get_descendants(child)

        return results

    def get_parents(self, child_concept):
        return self._to_relationships.get(child_concept, list())

    def remove(self):
        return (len(self._to_relationships) == 0 and
                len(self._from_relationships) == 0
                )

class SXMRelationship(_SXMDefined):
    def __init__(self, dts, network, from_concept, to_concept, order, weight=None, preferred_label=None, attributes=None):
        # Check that the from and to concept are already in the DTS
        if from_concept.name not in dts.concepts:
            raise SXMException("Cannot add relationship for concept '{}' that does not exist in the DTS".format(from_concept.name))
        if to_concept.name not in dts.concepts:
            raise SXMException("Cannot add relationship for concept '{}' that does not exist in the DTS".format(to_concept.name))

        super().__init__(dts)
        self._network = network
        self.from_concept = from_concept
        self.to_concept = to_concept
        self.order = decimal.Decimal(order)
        self.weight = weight
        self.preferred_label = preferred_label
        # Should check that from, to, order, calc, weight, preferred label attributes are not in the attributes dict
        self.attributes = attributes if attributes else dict()

        # Save the relationships in the network
        self.network._from_relationships[from_concept].append(self)
        self.network._to_relationships[to_concept].append(self)

        # Save the relationships in the concept
        from_concept._from_concept_relationships[self.network].add(self)
        to_concept._to_concept_relationships[self.network].add(self)
    
    def remove(self):
        # remove the reationship from the network
        remove_all_from_list(self.network._from_relationships[self.from_concept], self)
        if len(self.network._from_relationships[self.from_concept]) == 0:
            del self.network._from_relationships[self.from_concept]
        remove_all_from_list(self.network._to_relationships[self.to_concept], self)
        if len(self.network._to_relationships[self.to_concept]) == 0:
            del self.network._to_relationships[self.to_concept]
        # remove the relationship from the concepts
        self.from_concept._from_concept_relationships[self.network].remove(self)
        if len(self.from_concept._from_concept_relationships[self.network]) == 0:
            del self.from_concept._from_concept_relationships[self.network]
        self.to_concept._to_concept_relationships[self.network].remove(self)
        if len(self.to_concept._to_concept_relationships[self.network]) == 0:
            del self.to_concept._to_concept_relationships[self.network]

        return True

    @property
    def network(self):
        return self._network 

    @property
    def perferred_label(self):
        return self.attributes.get(self.dts.new('QName', None, 'preferredLabel'))

    @property
    def link_name(self):
        return self.network.link_name
    @property
    def arc_name(self):
        return self.network.arc_name
    @property
    def arcrole(self):
        return self.network.arcrole
    @property
    def role(self):
        return self.network.role

    @property
    def is_root(self):
        return self.from_concept in self.network.roots

class _SXMCubePart(_SXMDefined):
    def __init__(self, dts, dim_type, concept, role):
        super().__init__(dts)
        self.dim_type = dim_type
        self.concept = concept
        self.role = role
    
    def __repr__(self):
        return '{}: {}'.format(self.dim_type, str(self))

    def __str__(self):
        return str(self.concept)

    def __hash__(self):
        return hash((self.concept, self.dim_type, self.role))

    def __eq__(self, other):
        return self.concept == other.concept
    
class SXMCube(_SXMCubePart):

    def __init__(self, dts, role, concept):
        super().__init__(dts, 'cube', concept, role)
        self._primary_items = list()
        self._dimensions = list() # using list to preserve order

    @property
    def primary_items(self):
        return copy.copy(self. _primary_items)

    @property
    def line_item_concepts(self):
        # Returns the concepts
        result = set()
        for primary in self._primary_items:
            result.add(primary.concept)
            result |= {x.concept for x in primary.all_descendants}
        return result
    
    @property
    def dimensions(self):
        return copy.copy(self._dimensions)

    def add_primary_node(self, primary_node):
        self._primary_items.append(primary_node)

    def add_dimension_node(self, dimension_node):
        self._dimensions.append(dimension_node)

class _SXMCubeTreeNode(_SXMCubePart):
    def __init__(self, dts, dim_type, concept, role, usable=True, attributes=None):
        super().__init__(dts, dim_type, concept, role)
        self.usable = usable
        self._children = []
        self.usable = usable
        # should make sure the usable attribute is not in the attributes
        self.attributes = attributes or dict()

    @property
    def children(self):
        return copy.copy(self._children)

    @property
    def all_descendants(self):
        result = self.children
        for child in self._children:
            result += child.all_descendants
        return result

    _ALLOWED_CHILDREN = {
        'dimension': {'domain', 'member'},
        'domain': {'member',},
        'member': {'member',}, 
        'primary': {'member'}
    }

    def add_child_node(self, child_node, sibling=None, direction='after'):
        # check if the child is allowed
        if child_node.dim_type not in _SXMCubeTreeNode._ALLOWED_CHILDREN.get(self.dim_type, set()):
            raise SXMException("Not allowed to add {} as a child of a {} in a cube".format(child_node.dim_type, self.dim_type))

        # This adds a _SXMCubeTreeNode to the children
        if sibling is None:
            # child is added to the end
            self._children.append(child_node)
        else: # find the sibling
            i = None
            for i in enumerate(self._children):
                if self._children[i] == sibling:
                    break
            else: # the sibling was not found
                raise SXMException("Cannot insert member {mem} {dir} {sib} because {sib} is not in {par}".format(mem=child_node.concept.localName,
                                                                                                                 dir=direction,
                                                                                                                 sib=sibling.concept.localName,
                                                                                                                 par=self.concept.localName))
            if direction == 'after':
                self._children.insert(i+1, child_node) # insert inserts before the indexed item
            else:
                self._children.insert(i, child_node) 

    def add_child(self, cls, child, role=None, usable=True, attributes=None, sibling=None, direction='after'):
        # This adds a concept as a child (a _SXMCubeTreeNode is created from the concept)
        child_node = cls(self.dts, child, role or self.role, usable, attributes) # default role is the same as the parent
        self.add_child_node(child_node, sibling, direction)
        return child_node

    # When creating a remove node. Verify that if the node is a member of a dimension and it is the default, that it cannot be remove.
    # The default must be handled first.

class SXMDimension(_SXMCubeTreeNode):
    def __init__(self, dts, concept, role, typed_domain=None, attributes=None):
        super().__init__(dts, 'dimension', concept, role, None, attributes)

        self.typed_domain = typed_domain
        self._default = None

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, val):
        if val is None:
            self._default = None
        else:
            if not isinstance(val, _SXMCubeTreeNode):
                raise SXMException("Cannot add default of type {} to dimension {} because it is the wrong type".format(type(val).__name__, self.concept.name.clark))
            if val in self.all_descendants:
                self._default = val
            else:
                raise SXMException("Cannot add default {} to dimension {} because it is not a member of the dimension".format(val.concept.name.clark), self.concept.name.clark)

    @property
    def typed_domain(self):
        return self._typed_domain

    @typed_domain.setter
    def typed_domain(self, val):
        if val is None:
            self._typed_domain = val
        else:
            if not isinstance(val, SXMElement):
                raise SXMException("Cannot add typed domain of type {} to dimension {}. It must be an element".format(type(val).__name__, self.concept.name.clark))
            self._typed_domain = val 

    @property
    def is_typed(self):
        return self.typed_domain is not None
    
    @property
    def is_explicit(self):
        return self.typed_domain is None

class SXMPrimary(_SXMCubeTreeNode):
    def __init__(self, dts, concept, role, is_all=True, usable=True, attributes=None):
        super().__init__(dts, 'primary', concept, role, usable, attributes)
        self.is_all = is_all

class SXMMember(_SXMCubeTreeNode):
    def __init__(self, dts, concept, role, usable=True, attributes=None):
        super().__init__(dts, 'member', concept, role, usable, attributes)

    @classmethod
    def build_from_network(cls, network, root=None, role=None, include_root=False):
        ''' Build membership tree from a network'''
        root_nodes = set()
        processed = set()

        def add_child_rels(parent_node, rel):
            if rel.to_concept not in processed:
                child_node = parent_node.add_child(SXMMember, rel.to_concept)
                processed.add(rel.to_concept)
                for grand_child_rel in network.get_children(rel.to_concept):
                    add_child_rels(child_node, grand_child_rel)

        if root is None:
            roots = network.roots
        else:
            roots = [root,]

        for root in roots:
            if root not in processed:
                root_node = SXMMember(network.dts, root, role or network.role)
                root_nodes.add(root_node)
                processed.add(root)
                for child_rel in network.get_children(root):
                    add_child_rels(root_node, child_rel)
        
        if include_root:
            results = root_nodes
        else:
            # remove the roots from the trees.
            results = []
            for root_node in root_nodes:
                for child in root_node.children:
                    results.append(child)

        return results

def remove_all_from_list(the_list, the_item):
    '''Remove all occurences of the item from the list'''
    try:
        while True:
            the_list.remove(the_item)
    except ValueError:
        pass
