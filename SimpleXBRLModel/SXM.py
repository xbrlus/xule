import collections
import copy

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
    'TypeDomain': {'attribute': 'type_domains',
                    'key': ('name',)}
}

class SXMException(Exception):
    pass
class SXMObjectExists(SXMException):
    pass

class SXMBase:
    '''A base class for all SXM classes'''
    def __init__(self):
        pass

class SXMDTSBase(SXMBase):
    '''An object that is part of a DTS'''
    def __init__(self, dts):
        super().__init__()
        self.dts = dts

class SXMDocument(SXMBase):
    def __init__(self, document_uri=None, document_name=None):
        super().__init__()
        self.document_uri = document_uri
        self.document_name = document_name
        self._sxm_objects = set()
    
    @property 
    def document_contents(self):
        return frozenset(self._sxm_objects)

    def add(self, sxm_object):
        if isinstance(sxm_object, SXMDefined):
            if sxm_object not in self._sxm_objects:
                self._sxm_objects.add(sxm_object)
                sxm_object.document = self
        else:
            raise SXMException("Simple XBRL Object '{}' cannot be added to a document.".format(type(sxm_object).__name__))
    
    def remove(self, sxm_object):
        if isinstance(sxm_object, SXMDefined):
            if sxm_object in self._sxm_objects:
                self._sxm_objects.remove(sxm_object)
                sxm_object.document = None
        else:
            raise SXMException("Simple XBRL Object '{}' cannot be removed from a document.".format(type(sxm_object).__name__))

class SXMDefined(SXMBase):
    '''Defined objects are defined in a document'''
    def __init__(self, document=None):
        super().__init__()
        self.document = document
        if document is not None:
            document.add(self)

class SXMQName(SXMDTSBase):
    def __init__(self, dts, namespace, local_name):
        super().__init__(dts)
        self.namespace = namespace
        self.local_name = local_name
    
    def __repr__(self):
        return "{{{}}}{}".format(self.namespace, self.local_name)

    def __hash__(self):
        return hash((self.namespace, self.local_name))

    def __eq__(self, other):
        if not isinstance(other, SXMQName):
            return NotImplemented
        return self.namespace == other.namespace and self.local_name == other.local_name

class SXMDTS(SXMBase):

    def __init__(self):
        super().__init__()
        self.concepts = dict()
        self.elements = dict()
        self.networks = dict()
        self.arcroles = dict()
        self.roles = dict()
        self.types = dict()
        self.type_domains = dict()
    
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

        full_name = 'SXM{}'.format(class_name)
        if full_name in globals():
            class_bit = globals()[full_name]
            new_object = class_bit(self, *args, **kwargs)
        else:
            new_object = None

        # Save the object in the DTS (if it should be save and there is an object)
        if new_object and save:
            save_info = _SAVE_LOCATIONS.get(class_name)
            if save_info is not None:
                if len(save_info['key']) == 1:
                    key = getattr(new_object, save_info['key'][0])
                else:
                    key = tuple(getattr(new_object, x) for x in save_info['key'])
                # Check if the object is already created.
                list_of_objects = getattr(self, save_info['attribute'])
                if key in list_of_objects:
                    raise SXMException("{} object with key {} already exists".format(class_name, key))
                list_of_objects[key] = new_object

        return new_object

    def get(self, class_name, key):
        save_info = _SAVE_LOCATIONS.get(class_name)
        if save_info is None:
            return None
        else:
            return getattr(self, save_info['attribute'], dict()).get(key)

class SXMArcrole(SXMDTSBase, SXMDefined):
    def __new__(cls, dts, arcrole_uri, description, used_ons):
        if arcrole_uri in dts.arcroles:
            raise SXMObjectExists('Arcrole {}'.format(arcrole_uri))
        return super().__new__(cls)

    def __init__(self, dts, arcrole_uri, description, used_ons):
        super().__init__(dts)
        self.arcrole_uri = arcrole_uri
        self.description = description
        self.used_ons = used_ons
    
    def __repr__(self):
        return self.arcrole_uri
    
    def __hash__(self):
        return hash(self.arcrole_uri)

    def __eq__(self, other):
        if not isinstance(other, SXMArcrole):
            return NotImplemented
        return self.arcrole_uri == other.arcrole_uri

    @property
    def networks(self):
        return frozenset(x for x in self.dts.newtorks if self is x.arcrole)

class SXMRole(SXMDTSBase, SXMDefined):
    def __init__(self, dts, role_uri, description, used_ons):
        super().__init__(dts)
        self.role_uri = role_uri
        self.description = description
        self.used_ons = used_ons

    def __repr__(self):
        return self.role_uri
    
    def __hash__(self):
        return hash(self.role_uri)

    def __eq__(self, other):
        if not isinstance(other, SXMRole):
            return NotImplemented
        return self.role_uri == other.role_uri

    @property
    def networks(self):
        return frozenset(x for x in self.dts.networks if self is x.role)

class SXMElement(SXMDTSBase, SXMDefined):

    def __init__(self, dts, name, data_type, abstract, nillable=None, id=None, attributes=None):
        super().__init__(dts)
        self.id = id
        self.name = name
        self.type = type
        self.is_abstract = abstract
        self.nillable = nillable
        self.attributes = attributes or dict()

class SXMTypedDomain(SXMElement):
    def __init__(self, dts, name, data_type, abstract, nillable, id, attributes,  xml_content):
        super().__init__(dts, name, data_type, abstract, nillable, id, attributes)
        self.content = xml_content

class SXMType(SXMDTSBase):

    def __init__(self, dts, name, parent_type, xml_content):
        super().__init__(dts)
        self.name = name
        self.parent_type = parent_type
        self.content = xml_content

    @property
    def base_xbrl_type(self):
        if self.parent_type is None:
            return self
        else:
            return self.parent_type.base_xbrl_type
        
class SXMConcept(SXMElement):
    def __init__(self, dts, name, data_type, abstract, nillable, period_type, balance_type, substitution_group, id, attributes, typed_domain=None):
        super().__init__(dts, name, data_type, abstract, nillable, id, attributes)
        self.substitution_group = substitution_group
        self.period_type = period_type
        self.balance_type = balance_type
        self.attributes = attributes or dict()
        self.typed_domain = typed_domain

        self._from_concept_relationships = collections.defaultdict(set)
        self._to_concept_relationships = collections.defaultdict(set)
        self._labels = list()
        self._references = list()

    def __repr__(self):
        return repr(self.name)

    @property
    def from_concept_relationships(self):
        return self._from_concept_relationships.copy()

    @property
    def to_concept_relationships(self):
        return self._to_concept_relationships.copy()
    
    @property
    def labels(self):
        return self._labels.copy()
    
    @property
    def references(self):
        return self._references.copy()

    def add_label(self, label_role, language, text):
        label = self.dts.new('Label', label_role, language, text)
        self._labels.append(label)

    def add_reference(self, reference_role, parts):
        ref = self.dts.new('Reference', reference_role, parts)
        self._references.append(ref)

class SXMLabel(SXMDTSBase, SXMDefined):
    def __init__(self, dts, label_role, language, text):
        super().__init__(dts)
        self.label_role = label_role
        self.language = language
        self.text = text

class SXMReference(SXMDTSBase, SXMDefined):
    def __init__(self, dts, reference_role, parts):
        # Check that the parts are actual SXMParts
        if any(not isinstance(x, SXMPart) for x in parts):        
            raise SXMException("Trying to add a reference where a part is not a SXMPart")

        super().__init__(dts)
        self.reference_role = reference_role
        self.parts = parts

class SXMPart(SXMDTSBase, SXMDefined):
    def __init__(self, dts, part_element, part_value):
        super().__init__(dts)
        self.part_element = part_element
        self.value = part_value

    def part_name(self):
        return self.part_element.name

class SXMNetwork(SXMDTSBase, SXMDefined):
    def __init__(self, dts, link_name, arc_name, arcrole, role, attributes=None):
        super().__init__(dts)
        self.link_name = link_name
        self.arc_name = arc_name
        self.arcrole = arcrole
        self.role = role
        self.attributes = attributes or dict()
        self._from_relationships = collections.defaultdict(list)
        self._to_relationships = collections.defaultdict(list)
    
    def __contains__(self, concept):
        # Determines if the concept is in the network
        rel_key = (self.link_name, self.arc_name, self.arcrole, self.role)
        return rel_key in (concept.from_concept_relationships.keys() | concept.to_concept_relationships.keys())

    @property
    def from_relationships(self):
        # protect the relationships, send a copy
        return self._from_relationships.copy()
    
    @property
    def to_relationships(self):
        # protect the relationships, send a copy
        return self._to_relationships.copy()

    @property
    def relationships(self):
        return {y for x in self._from_relationships.values() for y in x} |  {y for x in self._to_relationships.values() for y in x}

    @property
    def roots(self):
        return tuple(self._from_relationships.keys() - self._to_relationships.keys())

    def add_relationship(self, from_concept, to_concept, order, weight, attributes):

        rel = self.dts.new('Relationship', self, from_concept, to_concept, order, weight, attributes)
        self._from_relationships[from_concept].append(rel)
        self._to_relationships[to_concept].append(rel)


class SXMRelationship(SXMDTSBase):
    def __init__(self, dts, network, from_concept, to_concept, order, weight, attributes):

        # Check that the from and to concpets are already in the DTS
        if from_concept.name not in dts.concepts:
            raise SXMException("Cannot add relationship for concept '{}' that does not exist in the DTS".format(from_concept.name))
        if to_concept.name not in dts.concepts:
            raise SXMException("Cannot add relationship for concept '{}' that does not exist in the DTS".format(to_concept.name))

        super().__init__(dts)
        self.network = network
        self.from_concept = from_concept
        self.to_concept = to_concept
        self.order = order
        self.weight = weight
        self.attributes = attributes if attributes else dict()

        # Save the relationships in the concept
        rel_key = (self.network.link_name, self.network.arc_name, self.network.arcrole, self.network.role)
        from_concept._from_concept_relationships[rel_key].add(self)
        to_concept._to_concept_relationships[rel_key].add(self)
    
    @property
    def perferred_lable(self):
        return self.attributes.get(self.dts.new('QName', None, 'preferredLable'))

    @property
    def target_role(self):
        return self.attributes.get(self.dts.new('QName', 'http://xbrl.org/2005/xbrldt', 'targetRole'))

    @property
    def link_name(self):
        return self.network.link_name
    @property
    def arc_name(self):
        return self.network.arc_name
    @property
    def relationship_type(self):
        return self.network.relationship_type
    @property
    def group(self):
        return self.network.group

class SXMCube(SXMDTSBase):

    def __init__(self, dts, role, cube_concept):
        super().__init__(dts)
        self.role = role
        self.cube_concept = cube_concept
        self._primary_items = list()
        self.dimensions = list() # using list to prserve order
        self.negative_cubes = set()

    @property
    def primary_items(self):
        return copy.copy(self. _primary_items)

    def add_primary_item(self, primary_member):
        self._primary_items.add(primary_member)

class SXMDimensionrelationships(SXMRelationship):
    def __init__(self, dts, network, from_concept, to_concept, order, weight, attributes):
        super().__init__(dts, network, from_concept, to_concept, order, weight, attributes)

    @property

class SXMMember(SXMDTSBase):
    def __init__(self, dts, member_concept, role, target_role=None, usable=True, attributes=None):
        super().__init__(dts)
        self.member_concept = member_concept
        self.role = role
        self.target_role = target_role
        self.usable = usable
        self.attributes = attributes or dict()





