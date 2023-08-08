import collections
import copy
import decimal
import inspect
import re
import arelle.XbrlConst as xc
from lxml import etree


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
    "http://www.xbrl.org/2003/arcrole/concept-label":"any",
    "http://www.xbrl.org/2003/arcrole/concept-reference": "any",
    "http://www.xbrl.org/2003/arcrole/fact-footnote": "any",
    "http://www.xbrl.org/2003/arcrole/parent-child": "undirected",
    "http://www.xbrl.org/2003/arcrole/summation-item": "any",
    "http://www.xbrl.org/2003/arcrole/general-special": "undirected",
    "http://www.xbrl.org/2003/arcrole/essence-alias": "undirected",
    "http://www.xbrl.org/2003/arcrole/similar-tuples": "any",
    "http://www.xbrl.org/2003/arcrole/requires-element": "any",
}

_DIMENSION_ARCROLES = {
    "http://xbrl.org/int/dim/arcrole/hypercube-dimension": "none",
    "http://xbrl.org/int/dim/arcrole/dimension-domain": "none",
    "http://xbrl.org/int/dim/arcrole/domain-member": "undirected",
    "http://xbrl.org/int/dim/arcrole/all": "undirected",
    "http://xbrl.org/int/dim/arcrole/notAll": "undirected",
    "http://xbrl.org/int/dim/arcrole/dimension-default": "none"

}

_DIMENSION_SCHEMA_NAMESPACE = 'http://xbrl.org/2005/xbrldt'
_DIMENSION_SCHEMA_URL = 'http://www.xbrl.org/2005/xbrldt-2005.xsd'

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
class SXMOjbectNotCopyable(SXMException):
    pass

class _SXMBase:
    '''A base class for all SXM classes'''

    # SXM constants - attached to all classes
    DOCUMENT_TYPES = _DOCUMENT_TYPES
    DOCUMENT_CONTENT_TYPES = _DOCUMENT_CONTENT_TYPES
    ALLOWED_DOCUMENT_CONTENT = _ALLOWED_DOCUMENT_CONTENT
    STANDARD_ROLES = _STANDARD_ROLES
    STANDARD_ARCROLES = _STANDARD_ARCROLES

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
    '''Án object that has attributes with dictionary values'''
    
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

    def copy(self, original, save=True, deep=False, copy_document=True, **kwargs):
        '''Copy an exisiting object
        
           The first argument is the object to copy. All other arguments must
           be keyword arguments.
        '''

        class_bit = type(original)
        if class_bit is not None:
            try:
                new_object = original._copy(**kwargs)
            except AttributeError:
                raise SXMOjbectNotCopyable("Copy is not currently supported for {}".format(original.get_class_name()))
        else:
            new_object = None

        if new_object is not None:
            if copy_document and isinstance(new_object, _SXMDefined):
                new_object.document = original.document

        if deep:
            try:
                original._deep_copy(new_object, copy_document=copy_document, **kwargs)
            except AttributeError:
                raise SXMOjbectNotCopyable("Deep copy is not currently supported for {}".format(original.get_class_name()))
        
        # Save the object in the containing object (DTS or Concept) (if it should be save and there is an object)
        if new_object is not None and save:
            self.save(new_object.get_class_name(), new_object)

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
                    raise SXMObjectExists("{} object with key {} already exists".format(class_name, key))
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

    def copy(self, **kwargs):
        return self.dts.copy(self, **kwargs)

class SXMDocument(_SXMDTSBase):
    def __init__(self, dts, document_uri, document_type, target_namespace=None, description=None):
        _validate_init_arguments()
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

    def remove(self):
        if len(self.contents) + len(self.imports) + len(self.linkbase_refs) + len(self.arcrole_refs) + len(self.role_refs) != 0:
            return False
        else:
            # the document does not have anything in it. Need to check that it is not referenced by anything else
            for doc in self.dts.documents.values():
                if self in doc.imports or self in doc.linkbase_refs:
                    return False
            return True

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
        _validate_init_arguments()
        super().__init__(dts)
        self._namespace = namespace
        self._local_name = local_name

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

    @property # cannot be changed because it is part of the hash
    def namespace(self):
        return self._namespace

    @property # cannot be changed because it is part of the hash
    def local_name(self):
        return self._local_name

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
        _validate_init_arguments()

        self.package_base_file_name = None
        self.identifier = None
        self.default_language = None
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
        _validate_init_arguments()
        super().__init__(dts)
        self.identifier = identifier
        self.names = []
        self.description = None
        self.description_language = None
        self.version = None
        self.documents = []
        self.languages = []
        self.other_elements = dict()
        
class SXMDTS(_SXMPackageDTS, SXMAttributedBase):

    def __init__(self):
        _validate_init_arguments()
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

        self._preload_standard_roles()
        self._preload_standard_arcroles()
    
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

    def _preload_standard_roles(self):
        for role_uri, description in _STANDARD_ROLES.items():
            self.new('Role', role_uri, description)

    def _preload_standard_arcroles(self):
        for arcrole_uri, cycles_allowed in _STANDARD_ARCROLES.items():
            self.new('Arcrole', arcrole_uri, cycles_allowed)

    def remove(self, del_object):
        remove = super().remove(del_object)
        if remove:
            del_object.dts = None

    def set_default_documents(self, base_name='', base_ns='http://xbrl/'):
        '''This will assign a default document to every writable component that does not have a document
        
        The defaults will be:
            taxonomy.xsd
            presentation.xml
            defintion.xml
            calculation.xml
            generic.xml
            label.xml
            reference.xml
        '''
        if not base_ns.endswith('/'): 
            base_ns += '/'
        if self.identifier is None:
            self.identifier = 'Taxonomy Package'
        if len(self.rewrites) == 0:
            self.rewrites['../'] = 'http://xbrl/package/'
        entry_point_document = self.new('Document', base_name + '-entry-point-taxonomy.xsd', self.DOCUMENT_TYPES.SCHEMA, base_ns + 'entryPoint/taxonomy')
        
        entry_point = self.new('PackageEntryPoint', 'Taxonomy Package')
        entry_point.names.append(('Taxonomy Entry Point', 'en'))
        entry_point.documents.append(entry_point_document) 

        linkbase_documents = dict()
        other_documents = set()

        tax_items = (set(self.types.values()) | set(self.concepts.values()) | set(self.elements.values()) | 
                     set(self.roles.values()) | set(self.arcroles.values()) | set(self.part_elements.values()))

        # Each schema document for concepts, elements and types will be named 'taxonomy' followed by a number
        # This will separate the different namespaces
        tax_docs_by_namespace = {x.name.namespace: f"{base_name}-taxonomy.xsd" 
                                 for x in tax_items 
                                 if not (type(x) in (SXMRole, SXMArcrole) or
                                    (x.document is not None and x.document.is_absolute))}
        
        # Convert the document name to an acutal document
        if len(tax_docs_by_namespace) == 1:
            # There is only one taxonomy schema
            key = list(tax_docs_by_namespace.keys())[0] # get the key of the only item in the dictionary
            tax_docs_by_namespace[key] = self.new('Document', 
                                                  f"{tax_docs_by_namespace[key]}.xsd", 
                                                  self.DOCUMENT_TYPES.SCHEMA, 
                                                  key)
            entry_point_document.add(tax_docs_by_namespace[key], self.DOCUMENT_CONTENT_TYPES.IMPORT)
        else:
            # a number to each of the names 
            for num, (key, doc_name) in enumerate(tax_docs_by_namespace.items()):
                tax_docs_by_namespace[key] = self.new('Document', 
                                                  f"{tax_docs_by_namespace[key]}{num}.xsd", 
                                                  self.DOCUMENT_TYPES.SCHEMA, 
                                                  key)
                entry_point_document.add(tax_docs_by_namespace[key], self.DOCUMENT_CONTENT_TYPES.IMPORT)
        
        role_doc_name = f"{base_name}-roles.xsd"
        role_doc_ns = f"{base_ns}roles"
        arcrole_doc_name = f"{base_name}-arcroles.xsd"
        arcrole_doc_ns = f"{base_ns}arcroles"

        for tax_item in tax_items:
            if tax_item.document is None:
                tax_document = None
                if isinstance(tax_item, SXMRole):
                    if tax_item.role_uri not in _STANDARD_ROLES:
                        tax_document = self.get('Document', role_doc_name) or self.new('Document', role_doc_name, self.DOCUMENT_TYPES.SCHEMA, role_doc_ns)
                elif isinstance(tax_item, SXMArcrole):
                    if tax_item.arcrole_uri not in _STANDARD_ARCROLES:
                        tax_document = self.get('Document', arcrole_doc_name) or self.new('Document', arcrole_doc_name, self.DOCUMENT_TYPES.SCHEMA, arcrole_doc_ns)
                else:
                    tax_document = tax_docs_by_namespace[tax_item.name.namespace]
                if tax_document is not None:
                    tax_item.document = tax_document
            else:
                if tax_item.document.is_relative:
                    other_documents.add(tax_item.document)

        linkbase_items = set(self.networks.values()) | set(self.cubes)
        for linkbase_item in linkbase_items:
            if isinstance(linkbase_item, SXMNetwork):
                # go through the relationships
                for rel in linkbase_item.relationships:
                    if rel.document is None:
                        # linkbases will divided into separate files base on the type of linkbase
                        # pre, def, cal, gen, oth (other)
                        doc_type_name = rel.link_name.local_name[:3].lower()
                        doc_name = f"{base_name}-{doc_type_name}.xml"
                        linkbase_document = self.get('Document', doc_name)
                        if linkbase_document is None:
                            linkbase_document = self.new('Document', doc_name, self.DOCUMENT_TYPES.LINKBASE)
                            entry_point_document.add(linkbase_document, self.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
                        rel.document = linkbase_document

        # The taxonomy.xsd will also be the entry point. Add references to all the other doucments.
        for other_document in other_documents:
            if other_document.document_type == self.DOCUMENT_TYPES.SCHEMA:
                entry_point_document.add(other_document, self.DOCUMENT_CONTENT_TYPES.IMPORT)
            elif other_document.document_type == self.DOCUMENT_TYPES.LINKBASE:
                entry_point_document.add(other_document, self.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
            else:
                entry_point_document.add(other_document, self.DOCUMENT_CONTENT_TYPES.IMPORT)
    

class SXMArcrole(_SXMDefined):

    def __init__(self, dts, arcrole_uri, cycles_allowed, description=None, used_ons=None):
        # check if this is a standard arcrole
        if arcrole_uri in _STANDARD_ARCROLES:
            cycles_allowed = _STANDARD_ARCROLES[arcrole_uri]
            used_ons = tuple()
        else:
            _validate_init_arguments()
        super().__init__(dts)
        self._arcrole_uri = arcrole_uri
        self.description = description
        self.used_ons = used_ons
        self.cycles_allowed = cycles_allowed
    
    def _copy(self, arcrole_uri=None, cycles_allowed=None, description=None, used_ons=None):
        return self.__class__(self.dts, 
                              arcrole_uri or self._arcrole_uri,
                              cycles_allowed or self.cycles_allowed,
                              description or self.description,
                              used_ons or self.used_ons)

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
        if role_uri in _STANDARD_ROLES:
            used_ons = tuple()
            description = _STANDARD_ROLES[role_uri]
        else:
            _validate_init_arguments()
        super().__init__(dts)
        self._role_uri = role_uri
        self._description = description if not self.is_standard else None
        self.used_ons = used_ons or set()

    def _copy(self, role_uri=None, description=None, used_ons=None):
        return self.__class__(self.dts, 
                              role_uri or self._role_uri,
                              description or self._description,
                              used_ons or self.used_ons)

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
        _validate_init_arguments()
        super().__init__(dts)

        # TODO - the substitution group shold always be an element. If a qname is passed, this code should resolve it to the element
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
        _validate_init_arguments()
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

    # The original vesion of the class avoided modeling the types and relied on XML for the definition
    # of the type. Now this is being modified to properly model types. However, the old style is kept for 
    # backwards compatability.

    def __init__(self, dts, name=None, parent_type=None, xml_content=None, anonymous_element=None,
                 xml_content_target_namespace = None,
                 min_exclusive=None, min_inclusive=None, max_exclusive=None, max_inclusive=None, 
                 total_digits=None, fraction_digits=None, length=None, min_length=None, max_length=None, 
                 enumerations=None, white_space=None, pattern=None):
        _validate_init_arguments()
        super().__init__(dts)
        # TODO - Handling of anonymous types is not quite correct. The name is used to identify
        # the type, but anonymous types don't have a name. The user must create a dummy name
        # and indicate with the anonymous_element that the type is anonymous.

        # Either the xml_content is supplied or the restrictions are supplied, but not both
        restictions_test = {enumerations is None, min_inclusive is None, max_inclusive is None, min_exclusive is None, 
                            max_exclusive is None, total_digits is None, fraction_digits is None, length is None, 
                            min_length is None, max_length is None, white_space is None}
        if (xml_content is not None and False in restictions_test):
            raise SXMException("Cannot create a type with both xml content and restrictions passed separately. For type {}".format(name.clark))
        # if xml_content is supplied then xml_content_target_namespace is required
        if xml_content is not None and xml_content_target_namespace is None and name is None:
            raise SXMException("Cannot create a type based on xml content if the target namespace is not also provided. For type {}".format(name.clark))
        type_info = SXMType.extract_properties_from_xml(xml_content, xml_content_target_namespace)
        # type_name, base_name, min_exclusive, min_inclusive, max_exclusive, max_inclusive, total_digits, fraction_dictions, length, min_length, max_length, enumerations, white_space, pattern
        self._name = name or dts.new('QName', xml_content_target_namespace, type_info[0])
        if parent_type is None and type_info[1] is None:
            self._base_name = None
        else:
            self._base_name = parent_type.name if parent_type is not None else _resolve_clark_to_qname(self.dts, type_info[1])
        self.min_exclusive = min_exclusive or type_info[2]
        self.min_inclusive = min_inclusive or type_info[3]
        self.max_exclusive = max_exclusive or type_info[4]
        self.max_inclusive = max_inclusive or type_info[5]
        self.total_digits = total_digits or type_info[6]
        self.fraction_digits = fraction_digits or type_info[7]
        self.length = length or type_info[8]
        self.min_length = min_length or type_info[9]
        self.max_length = max_length or type_info[10]
        self.enumerations = enumerations or type_info[11]
        self.white_space = white_space or type_info[12]
        self.pattern = pattern or type_info[13]

        if parent_type is None:
            if self._base_name is None:
                self.parent_type = None
            else:
                parent_type = dts.get('Type', self._base_name)
                if parent_type is None:
                    raise SXMException(f"Parent type '{self._base_name.clark}' for type '{self._name.clark}' is not in the DTS")
                self.parent_type = dts.get('Type', self._base_name)
        else:
            self.parent_type = parent_type
        if self.is_base_xbrl or self.is_base_xml:
            self.content = None
        else:
            self.content = xml_content
        self.anonymous_element = anonymous_element

    @classmethod
    def extract_properties_from_xml(cls, xml_content, target_namespace):
        # Extract the restriction attributes from xml_content. Currently
        # restrictions containing assertions are not supported.
        # initialize the return values
        type_name = None
        base_name = None
        min_exclusive = None
        min_inclusive = None
        max_exclusive = None
        max_inclusive = None
        total_digits = None
        fraction_dictions = None
        length = None
        min_length = None
        max_length = None
        enumerations = list()
        white_space = None
        pattern = list()

        if xml_content is not None:
            try:
                type_node = etree.fromstring(xml_content)
            except etree.XMLSyntaxError:
                raise SXMException(f"XML content for type {type_name.clark} is not valid xml.")
        
            type_name = f'{{{target_namespace}}}{type_node.get("name")}'
            restriction_node = type_node.find('{http://www.w3.org/2001/XMLSchema}simpleContent/{http://www.w3.org/2001/XMLSchema}restriction')
            if restriction_node is not None:
                base_name = _resolve_qname_to_clark(restriction_node.get('base'), restriction_node)

                for child_node in restriction_node:
                    # These will be one of: (minExclusive | minInclusive | maxExclusive | maxInclusive | totalDigits | fractionDigits |
                    #                        length | minLength | maxLength | enumeration | whiteSpace | pattern)
                    # Anything else will be ignored
                    # TODO - Handle annotation content
                    if child_node.tag.startswith('{http://www.w3.org/2001/XMLSchema}'):
                        tag_local_name = child_node.tag.split('}', 1)[1] # This gets the part after the first }
                        # check for integer values first
                        if tag_local_name in ('minExclusive', 'minInclusive', 'maxExclusive', 'maxInclusive', 'totalDigits', 'fractionDigits',
                                              'length', 'minLength', 'maxLength'):
                            try:
                                restriction_value = int(child_node.text)
                            except ValueError:
                                raise SXMException(f'Cannot convert restriction {child_node.tag} with value {child_node.text} to an intenger. Found on type {type_name}.')
                            if tag_local_name == 'minExclusive': min_exclusive = restriction_value
                            elif tag_local_name == 'minInclusive': min_inclusive = restriction_value
                            elif tag_local_name == 'maxExclusive': max_exclusive = restriction_value
                            elif tag_local_name == 'maxInclusive': max_inclusive = restriction_value
                            elif tag_local_name == 'totalDigits': total_digits = restriction_value
                            elif tag_local_name == 'fractionDigits': fraction_dictions = restriction_value
                            elif tag_local_name == 'length': length = restriction_value
                            elif tag_local_name == 'minLength': min_length = restriction_value
                            elif tag_local_name == 'maxLength': max_length = restriction_value
                        elif tag_local_name == 'enumeration':
                            enumerations.append(child_node.get('value'))
                        elif tag_local_name == 'whiteSpace':
                            white_space = child_node.text
                        elif tag_local_name == 'pattern':
                            pattern.append(child_node.text)
                       
        return type_name, base_name, min_exclusive, min_inclusive, max_exclusive, max_inclusive, total_digits, fraction_dictions, length, min_length, max_length, enumerations, white_space, pattern

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
        if self.base_xbrl_type is None:
            return self.base_xml_type.name.clark in _NUMERIC_XML_TYPES
        else:
            return self.base_xbrl_type.name.clark in _NUMERIC_XBRL_TYPES

    @property
    def is_restricted(self):
        return bool(self.min_exclusive or
                self.min_inclusive or
                self.max_exclusive or
                self.max_inclusive or
                self.total_digits or
                self.fraction_digits or
                self.length or
                self.min_length or 
                self.max_length or
                len(self.enumerations) != 0 or
                self.white_space or
                len(self.pattern) != 0)

    def remove(self):
        # check if there are any elements using the type or a type derrived from the type
        # and that there are not types derrived from the type
        return len(self.elements(True)) == 0 and len(self.derrived_types()) == 0

class SXMPartElement(SXMElement):
    def __init__(self, dts, name, data_type, abstract, nillable=None, id=None, substitution_group=None, attributes=None):
        _validate_init_arguments()
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
    def __init__(self, dts: SXMDTS, name: SXMQName, data_type: SXMType, abstract: bool, nillable: bool, period_type: str, 
                 balance_type: str, substitution_group: SXMQName, id: str = None, attributes: list = None, typed_domain: SXMElement = None):       
        _validate_init_arguments()
        super().__init__(dts, name, data_type, abstract, nillable, id, substitution_group, attributes)

        if not (isinstance(substitution_group, SXMConcept) or
                isinstance(substitution_group, SXMQName)):
            raise SXMException("Substitution group for concept '{}'is not a concept or a base item or tuple.".format(
                                name.clark))
        
        if period_type is None:
            raise SXMException(f"For concept '{name.clark}', period type is required")
        if period_type not in ('instant', 'duration'):
            raise SXMException(f"For cocnept '{name.clark}', invalid period type '{period_type}'")
        if balance_type not in ('debit', 'credit', None):
            raise SXMException(f"For concept '{name.carlk}', invalid balance type '{balance_type}'")
        
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
        _validate_init_arguments()
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
        _validate_init_arguments()
        # Check that the parts are actual SXMParts
        if any(not isinstance(x, SXMPart) for x in parts):        
            raise SXMException("Trying to add a reference where a part is not a SXMPart")

        super().__init__(dts, concept, reference_role, None, attributes)
        self.parts = parts

    def remove(self):
        return len(self.parts) == 0

class SXMPart(_SXMDefined):
    def __init__(self, dts, part_element, part_content):
        _validate_init_arguments()
        super().__init__(dts)
        self.part_element = part_element
        self.content = part_content

    @property
    def part_name(self):
        return self.part_element.name

class SXMNetwork(_SXMDefined):
    def __init__(self, dts, link_name, arc_name, arcrole, role):
        _validate_init_arguments()
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
    
    def _copy(self, link_name=None, arc_name=None, arcrole=None, role=None):
        return self.__class__(self.dts,
                              link_name or self.link_name,
                              arc_name or self.arc_name,
                              arcrole or self.arcrole,
                              role or self.role)

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
            if child not in results: # prevents infinite loops when there is a cylce
                results.append(child)
                results += self.get_descendants(child.to_concept)

        return results

    def get_parents(self, child_concept):
        return self._to_relationships.get(child_concept, list())

    def remove(self):
        return (len(self._to_relationships) == 0 and
                len(self._from_relationships) == 0
                )

class SXMRelationship(_SXMDefined):
    def __init__(self, dts, network, from_concept, to_concept, order, weight=None, preferred_label=None, attributes=None):
        _validate_init_arguments()
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
    
    def _copy(self, network=None, from_concept=None, to_concept=None, order=None, weight=None, preferred_label=None, attributes=None):
        return (network or self.network).add_relationship(from_concept or self.from_concept,
                                                          to_concept or self.to_concept,
                                                          order or self.order,
                                                          weight or self.weight,
                                                          preferred_label or self.preferred_label,
                                                          attributes or self.attributes)

    def _deep_copy(self, new_rel, copy_document=None, **kwargs):
        for next_rel in self.network.get_descendants(self.to_concept):
            next_rel.copy(copy_document=copy_document, **kwargs)

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
        _validate_init_arguments()
        super().__init__(dts, 'cube', concept, role)
        self._primary_items = list()
        self._dimensions = list() # using list to preserve order

    def _copy(self, concept=None, role=None):
        new_copy = self.__class__(self.dts,
                                  role or self.role,
                                  concept or self.concept)
        return new_copy

    # should add _deep_copy

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
        # should make sure the usable attribute is not in the attributes
        self.attributes = attributes or dict()

    def _deep_copy(self, new_object, copy_document=None, concept=None, role=None, usable=None, attributes=None, **kwargs):
        # This will copy the children
        for child in self._children:
            new_child = child.copy(deep=True, copy_document=copy_document, role=role, usable=usable, attributes=attributes)
            new_object._children.append(new_child)

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
        _validate_init_arguments()
        super().__init__(dts, 'dimension', concept, role, None, attributes)

        self.typed_domain = typed_domain
        self._default = None

    def _copy(self, concept=None, role=None, typed_domain=None, attributes=None):
        new_copy = self.__class__(self.dts, 
                                  concept or self.concept,
                                  role or self.role,
                                  typed_domain or self.typed_domain,
                                  attributes or self.attributes)
        new_copy._default = self._default
        return new_copy

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
        _validate_init_arguments()
        super().__init__(dts, 'primary', concept, role, usable, attributes)
        self.is_all = is_all


    def _copy(self, concept=None, role=None, is_all=None, usable=None, attributes=None):
        new_copy = self.__class__(self.dts, 
                                  concept or self.concept,
                                  role or self.role,
                                  is_all or self.is_all,
                                  usable or self. usable,
                                  attributes or self.attributes)
        return new_copy

class SXMMember(_SXMCubeTreeNode):
    def __init__(self, dts, concept, role, usable=True, attributes=None):
        _validate_init_arguments()
        super().__init__(dts, 'member', concept, role, usable, attributes)

    def _copy(self, concept=None, role=None, usable=None, attributes=None):
        new_copy = self.__class__(self.dts, 
                                  concept or self.concept,
                                  role or self.role,
                                  usable or self.usable,
                                  attributes or self.attributes)
        return new_copy

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

def _resolve_qname_to_clark(name, node):
    '''This method resolves a prefix name in xml to clark notation'''
    if name is None:
        return None
    if ':' in name:
        prefix, local_name = name.split(':', 1) # split on first occurence
    else:
        prefix = None
        local_name = name
    nsmap = node.nsmap
    namespace = nsmap.get(prefix)
    if namespace is None:
        raise SXMException(f"QName cannot be resolved for name '{name}'")
    return f'{{{namespace}}}{local_name}'

def _resolve_name_in_target_to_clark(name, node):
    '''This method converts a name defined in a schema to a clark notation qname
       It uses the target namespace'''
    

def _resolve_clark_to_qname(name, dts):
    '''Convert a clark notation qname to a SXMQName'''
    match = re.match('^{([^}]+)}(.*)$', name)
    if match is None:
        raise SXMException(f"QName '{name}' is not a valid clark notation")
    return dts.new('QName', match.group(1), match.group(2))

# _SXM_ARUGMENT_TYPES is used to validate the arguments when a SXM object is created.
# The key is the name of the argument
# The value is a tuple. 
#     0 = A tuple of SXM classes that have this argument
#     1 = The type that the value of the argument must be. If None, then the type is not checked
#     2 = If the type is set or list, then this is the type that should be contained in the set or list. If this value is none, 
#         then no further type checking is done.
#         If the type is dict, then this is the expected type of the key of the dictionary
#     3 = If the type is dict, then this the exptected type of the value of the dictionary
_SXM_ARGUMENT_TYPES= {
    'abstract': ((SXMConcept, SXMElement, SXMPartElement, SXMTypedDomain), bool),
    'anonymous_element': ((SXMType, ), None),
    'arc_name': ((SXMNetwork, ), SXMQName),
    'arcrole': ((SXMNetwork, ), SXMArcrole),
    'arcrole_uri': ((SXMArcrole, ), str),
    'attributes': ((SXMConcept, SXMDimension, SXMElement, SXMMember, SXMPartElement, SXMPrimary, SXMReference, SXMRelationship, SXMResource, SXMTypedDomain), dict, (SXMQName, str), str),
    'balance_type': ((SXMConcept, ), str),
    'concept': ((SXMCube, SXMDimension, SXMMember, SXMPrimary, SXMReference, SXMResource), SXMConcept),
    'content': ((SXMResource, ), str),
    'cycles_allowed': ((SXMArcrole, ), bool),
    'data_type': ((SXMConcept, SXMElement, SXMPartElement, SXMTypedDomain), SXMType),
    'description': ((SXMArcrole, SXMDocument, SXMRole), str),
    'document_type': ((SXMDocument, ), str),
    'document_uri': ((SXMDocument, ), str),
    'enumerations': ((SXMType, ), None),
    'fraction_digits': ((SXMType, ), None),
    'from_concept': ((SXMRelationship, ), SXMConcept),
    'id': ((SXMConcept, SXMElement, SXMPartElement, SXMTypedDomain), str),
    'identifier': ((SXMPackageEntryPoint, ), None),
    'is_all': ((SXMPrimary, ), bool),
    'length': ((SXMType, ), int),
    'link_name': ((SXMNetwork, ), SXMQName),
    'local_name': ((SXMQName, ), str),
    'max_exclusive': ((SXMType, ), None),
    'max_inclusive': ((SXMType, ), None),
    'max_length': ((SXMType, ), int),
    'min_exclusive': ((SXMType, ), None),
    'min_inclusive': ((SXMType, ), None),
    'min_length': ((SXMType, ), int),
    'name': ((SXMConcept, SXMElement, SXMPartElement, SXMType, SXMTypedDomain), SXMQName),
    'namespace': ((SXMQName, ), str),
    'network': ((SXMRelationship, ), SXMNetwork),
    'nillable': ((SXMConcept, SXMElement, SXMPartElement, SXMTypedDomain), bool),
    'order': ((SXMRelationship, ), None),
    'parent_type': ((SXMType, ), SXMType),
    'part_content': ((SXMPart, ), str),
    'part_element': ((SXMPart, ), SXMElement),
    'parts': ((SXMReference, ), None),
    'pattern': ((SXMType, ), list, str),
    'period_type': ((SXMConcept, ), str),
    'preferred_label': ((SXMRelationship, ), None),
    'prefix': ((SXMQName, ), str),
    'reference_role': ((SXMReference, ), SXMRole),
    'role': ((SXMCube, SXMDimension, SXMMember, SXMNetwork, SXMPrimary, SXMResource), SXMRole),
    'role_uri': ((SXMRole, ), str),
    'substitution_group': ((SXMConcept, SXMElement, SXMPartElement, SXMTypedDomain), None),
    'target_namespace': ((SXMDocument, ), str),
    'to_concept': ((SXMRelationship, ), SXMConcept),
    'total_digits': ((SXMType, ), int),
    'typed_domain': ((SXMConcept, SXMDimension), SXMElement),
    'usable': ((SXMMember, SXMPrimary), bool),
    'used_ons': ((SXMArcrole, SXMRole), None),
    'weight': ((SXMRelationship, ), None),
    'white_space': ((SXMType, ), None),
    'xml_content': ((SXMType, ), str),
    'xml_content_target_namespace': ((SXMType, ), str),
}

def _validate_init_arguments():

    calling_frame = inspect.currentframe().f_back
    calling_class = calling_frame.f_locals.get('self', None).__class__
    args, _, _, values = inspect.getargvalues(calling_frame)
    bad_args = []
    for arg_name in args:
        if arg_name in _SXM_ARGUMENT_TYPES:
            if calling_class in _SXM_ARGUMENT_TYPES[arg_name][0]:
                # Don't bother checking if there isn't a type in the _SXM_ARGuMENT_TYPES or if the value is None
                if _SXM_ARGUMENT_TYPES[arg_name][1] is not None and values[arg_name] is not None:
                    if not isinstance(values[arg_name], _SXM_ARGUMENT_TYPES[arg_name][1]):
                        bad_args.append(f"Argument '{arg_name}' for '{calling_class.__name__}'. Expected {_SXM_ARGUMENT_TYPES[arg_name][1].__name__} but found {type(values[arg_name]).__name__}")
                    # Check contents for sets and list
                    if _SXM_ARGUMENT_TYPES[arg_name][1] in (set, list):
                        # The next item is the type that the set or list must contain.
                        if _SXM_ARGUMENT_TYPES[arg_name][2] is not None:
                            for item in values[arg_name]:
                                if not isinstance(item, _SXM_ARGUMENT_TYPES[arg_name][2]):
                                    bad_args.append(f"Argument '{arg_name}' for '{calling_class.__name__}'. Expected {_SXM_ARGUMENT_TYPES[arg_name][2].__name__} as the type of the content of the set/list but found {type(values[item]).__name__}")
                    # Check contents of dictionaries
                    if _SXM_ARGUMENT_TYPES[arg_name][1] == dict:
                        if _SXM_ARGUMENT_TYPES[arg_name][2] is not None or _SXM_ARGUMENT_TYPES[arg_name][3] is not None:
                            for key, val in values[arg_name].items():
                                # Check the key
                                if _SXM_ARGUMENT_TYPES[arg_name][2] is not None:
                                    if isinstance(_SXM_ARGUMENT_TYPES[arg_name][2], tuple):
                                        arg_types = _SXM_ARGUMENT_TYPES[arg_name][2]
                                    else:
                                        arg_types = (_SXM_ARGUMENT_TYPES[arg_name][2],)
                                    if type(key) not in arg_types:
                                        bad_args.append(f"Argument '{arg_name}' for '{calling_class.__name__}'. Expected {','.join(tuple(x.__name__ for x in arg_types))} as the type of the key of the dictionary but found {type(key).__name__}")
                                # Check the value
                                if _SXM_ARGUMENT_TYPES[arg_name][3] is not None:
                                    if not isinstance(val, _SXM_ARGUMENT_TYPES[arg_name][3]):
                                        bad_args.append(f"Argument '{arg_name}' for '{calling_class.__name__}'. Expected {_SXM_ARGUMENT_TYPES[arg_name][3].__name__} as the type of the key of the dictionary but found {type(val).__name__}")

    if len(bad_args) != 0:
        bad_list = '\n'.join(bad_args)
        raise SXMException(f"Invalid arguments for \n{bad_list}")

def verify_class_arguments():
    import inspect

    # Get the current module
    current_module = inspect.getmodule(inspect.currentframe())

    # Get all the classes defined in the current module
    classes = inspect.getmembers(current_module, inspect.isclass)

    # Dictionary to store the arguments and corresponding classes
    arguments_dict = collections.defaultdict(set)

    # Iterate over the classes
    for class_name, class_obj in classes:
        # Check if the class has an '__init__' method
        if '__init__' in class_obj.__dict__ and issubclass(class_obj, _SXMBase) and not class_name.startswith('_'):
            # Get the '__init__' method
            init_method = class_obj.__dict__['__init__']
            
            # Get the arguments of the '__init__' method
            init_signature = inspect.signature(init_method)
            init_parameters = init_signature.parameters
            
            # Iterate over the parameters
            for parameter_name, _ in list(init_parameters.items())[2:]:
                # Add the parameter to the dictionary
                arguments_dict[parameter_name].add(class_obj.__name__)
    
    for arg_name in sorted(arguments_dict.keys()):
        class_names = ', '.join(sorted(arguments_dict[arg_name]))
        print(f"'{arg_name}': (({class_names}), None),")
    