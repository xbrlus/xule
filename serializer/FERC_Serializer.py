'''Serializer for FERC'''

from ast import Index
import collections
from curses.ascii import BEL
import optparse
import re
from tkinter import NUMERIC

from arelle.ModelDtsObject import ModelConcept, ModelType
from arelle.ModelValue import QName
from arelle.CntlrWebMain import Options
import arelle.XbrlConst as xc
from lxml import etree

_OPTIONS = None
_OLD_MODEL = None
_CORE_NAME = 'ferc'
_NAMESPACE_START = 'http://ferc.gov/form/'  # the rest of the namespace is version / taxonomy part (i.e. form1, ferc, sched-bla-bla)
_NEW_FORM_TYPE = None
_NEW_SCHEDULE_TYPE =  None
_PARENT_CHILD = 'http://www.xbrl.org/2003/arcrole/parent-child'
_SUMMATION_ITEM = 'http://www.xbrl.org/2003/arcrole/summation-item'
_PRESENTATION_LINK_ELEMENT = '{http://www.xbrl.org/2003/linkbase}presentationLink'
_PRESENTATION_ARC_ELEMENT = '{http://www.xbrl.org/2003/linkbase}presentationArc'
_FOOTNOTE_ARC_NAME = '{http://www.xbrl.org/2003/linkbase}footnoteArc'
_STANDARD_LABEL = 'http://www.xbrl.org/2003/role/label'
_TERSE_LABEL = 'http://www.xbrl.org/2003/role/terseLabel'
_ITEM = '{http://www.xbrl.org/2003/instance}item'
_TUPLE = '{http://www.xbrl.org/2003/instance}tuple'
_XBRLI_NS = 'http://www.xbrl.org/2003/instance'
_LINK_NS = 'http://www.xbrl.org/2003/linkbase'
_GEN_NS = 'http://xbrl.org/2008/generic'
_DIMENSION_NAMESPACE = 'http://xbrl.org/2005/xbrldt'
_LINK_PART_CLARK = '{http://www.xbrl.org/2003/linkbase}part'
_DOCUMENT_MAP = dict()
_NEW_VERSION = None
_CORE_NAMESPACE = None
_TYPE_NAMESPACE = None
_ARCROLE_NAMESPACE = None
_PART_NAMESPACE = None
_OLD_NAMESPACE = ''
_OLD_TYPE_NAMESPACE = ''
_OLD_NS_MATCH = re.compile("^http://([^/]+\\.)?ferc\\.gov/(.*)$")
_OLD_ARCROLE_MATCH = re.compile("^http://(?P<pre>[^\\.]+)\\.?ferc\\.gov/(?:form)/(?P<old_version>[^/]+)/arcroles/(?P<name>[^/]+)$")
_OLD_ROLE_MATCH = re.compile("^http://(?:(?P<pre>[^\\.]+)\\.)?ferc\\.gov/(?:form)/(?P<old_version>[^/]+)/roles/(?P<role_type>[^/]+)/(?P<rest>.*)$")
_NEW_NS_MATCH = None
_NEW_ARCROLE_MATCH = None
_NEW_ROLE_MATCH = None
_NEW_SCHEDULE_ROLE_MATCH = None
_SCHEDULE_FORM_ARCROLE = 'http://eforms.ferc.gov/form/2020-01-01/arcroles/schedule-form'
_SCHEDULE_FORM_DEFINITION = 'Links schedules to forms'
# Document descriptions
_CORE_DESCRIPTION = 'This schema contains core elements for the FERC taxonomy.'
_TYPE_DESCRIPTION = 'This schema contains ferc types.'
_PART_DESCRIPTION = 'This schema contains ferc reference parts.'
_ARCROLE_DESCRIPTION = 'This schema contains ferc arcrole role definitions'
_FOOTNOTE_ARC_DESCRIPTION = 'This schema contains ferc footnote arcrole defintions.'
_REFERENCE_ROLE_DESCRIPTION = 'This schema contains roles for references.'
_LABEL_ROLE_DESCRIPTION = 'This schema contains roles for labels.'

_ENTRY_POINT_LABEL_ROLE = 'http://ferc.gov/form/2020-01-01/roles/label/EntryPoint'
_EFORMS_LABEL_ROLE = 'http://ferc.gov/form/2020-01-01/roles/label/eForm'
_ENTRY_POINT_PATH_LABEL_ROLE= 'http://ferc.gov/form/2020-01-01/roles/label/EntryPointPath'

_DEFAULT_TABLE_STANDARD_LABEL = 'Default [Table]'
_DEFAULT_TABLE_TERSE_LABEL = 'This [Table] abastract element is used for creating table for "Total" line items without dimension assignment. The element is used in "Default" group.'
_DEFAULT_LINE_ITEMS_STANDARD_LABEL = 'Default [Line Items]'
_DEFAULT_LINE_ITEMS_TERSE_LABEL = 'This [Line Items] abastract element is used for creating table for "Total" line items without dimension assignment. The element is used in "Default" group.'
_DEFAULT_ABSTRACT_STANDARD_LABEL = 'Default [Abstract]'
_DEFAULT_ABSTRACT_TERSE_LABEL = 'This abastract element is used for creating table for "Total" line items without dimension assignment. The element is used in "Default" group.'
_DEFAULT_ROLE_DEFINITION = 'Default'

class FERCSerialzierException(Exception):
    pass

def serialize(model_xbrl, options, sxm):
    global _OPTIONS
    _OPTIONS = options

    global _OLD_MODEL
    _OLD_MODEL = model_xbrl

    set_configuration(options, model_xbrl)

    new_model = sxm.SXMDTS()
    new_model = organize_taxonomy(model_xbrl, new_model, options)

    return new_model

def error(code, msg):

    _OLD_MODEL.error(code, msg)
    if not getattr(_OPTIONS, 'serializer_package_allow_errors', False):
        raise FERCSerialzierException

def warning(code, msg):
    _OLD_MODEL.warning(code, msg)

def set_configuration(options, old_model):
    global _NEW_VERSION 
    _NEW_VERSION = getattr(options, 'serializer_package_version')

    global _NEW_NS_MATCH
    _NEW_NS_MATCH = re.compile("{}{}/(.*)$".format(re.escape(_NAMESPACE_START), re.escape(_NEW_VERSION)))

    global _NEW_ARCROLE_MATCH
    # for old_arcrole in old_model.arcroleTypes.keys():
    #     match = _OLD_ARCROLE_MATCH.fullmatch(old_arcrole)
    #     if match is not None:
    #         ns_prefix = match.group(1)
    #         _NEW_ARCROLE_MATCH = re.compile("http://{}\.ferc\.gov/form/{}/arcroles/.*".format(re.escape(ns_prefix), re.compile(_NEW_VERSION)))
    #         break
    _NEW_ARCROLE_MATCH = _OLD_ARCROLE_MATCH

    global _NEW_ROLE_MATCH
    #_NEW_ROLE_MATCH = re.compile('{}{}/roles/.*$'.format(re.escape(_NAMESPACE_START), re.escape(_NEW_VERSION)))
    _NEW_ROLE_MATCH = _OLD_ROLE_MATCH

    global _NEW_SCHEDULE_ROLE_MATCH
    _NEW_SCHEDULE_ROLE_MATCH = re.compile('(.*)/roles/Schedule/([^/]+)/(.*)')
    global _DOCUMENT_MAP

    global _CORE_NAMESPACE 
    _CORE_NAMESPACE = '{}{}/{}'.format(_NAMESPACE_START, _NEW_VERSION, _CORE_NAME)  
    _DOCUMENT_MAP[_CORE_NAMESPACE] = '{}-{}_{}.xsd'.format(_CORE_NAME, 'core', _NEW_VERSION)

    global _TYPE_NAMESPACE
    _TYPE_NAMESPACE = '{}{}/{}'.format(_NAMESPACE_START, _NEW_VERSION, 'types')
    _DOCUMENT_MAP[_TYPE_NAMESPACE] = '{}-{}_{}.xsd'.format(_CORE_NAME, 'core-types', _NEW_VERSION)

    global _ARCROLE_NAMESPACE
    _ARCROLE_NAMESPACE = '{}{}/arcroles/core'.format(_NAMESPACE_START, _NEW_VERSION)
    _DOCUMENT_MAP[_ARCROLE_NAMESPACE] = '{}-core-arcroles_{}.xsd'.format(_CORE_NAME, _NEW_VERSION)
    
    global _OLD_PART_NAMESPACE
    for old_part_element in old_model.qnameConcepts.values():
        if (_LINK_PART_CLARK in [x.clarkNotation for x in old_part_element.substitutionGroupQnames] and
            _OLD_NS_MATCH.fullmatch(old_part_element.qname.namespaceURI)):
            #_PART_NAMESPACE = old_part_element.name.namespaceURI
            _OLD_PART_NAMESPACE = old_part_element.qname.namespaceURI
            break

    global _PART_NAMESPACE
    #_PART_NAMESPACE = '{}{}/parts'.format(_NAMESPACE_START, _NEW_VERSION)
    # Use the original namespace for the parts
    _PART_NAMESPACE = _OLD_PART_NAMESPACE
    _DOCUMENT_MAP[_PART_NAMESPACE] = '{}-core-ref-parts_{}.xsd'.format(_CORE_NAME, _NEW_VERSION)
    
    global _OLD_TYPE_NAMESPACE
    for old_type_name in old_model.qnameTypes.keys():
        if _OLD_NS_MATCH.fullmatch(old_type_name.namespaceURI) is not None and old_type_name.localName == 'formItemType':
            _OLD_TYPE_NAMESPACE = old_type_name.namespaceURI
            break

    global _OLD_NAMESPACE
    for old_concept_name in old_model.qnameConcepts.keys():
        if old_model.qnameConcepts[old_concept_name].typeQname.localName == 'formItemType' and _OLD_NS_MATCH.fullmatch(old_concept_name.namespaceURI) is not None:
            _OLD_NAMESPACE = old_concept_name.namespaceURI
            break
    if _OLD_NAMESPACE is None:
        raise FERCSerialzierException("Cannot determine the namespace of the working taxonomy concepts. "
                                      "The FERC Serializer uses the first concept that has a datatype with local name "
                                      "of 'formItemType'. Did not find a concept with a 'formItemType' data type.")
 

    global _NEW_FORM_TYPE
    _NEW_FORM_TYPE = '{{{}{}/types}}formItemType'.format(_NAMESPACE_START, _NEW_VERSION)
    
    global _NEW_SCHEDULE_TYPE
    _NEW_SCHEDULE_TYPE = '{{{}{}/types}}scheduleItemType'.format(_NAMESPACE_START, _NEW_VERSION)

def add_package_defaults(new_model, forms):

    if len(forms) == 0:
        raise FERCSerialzierException("No forms were found")

    # form_names = []
    # for form in forms:
    #     form_dir = form.name.local_name.lower().split('abstract')[0]
    #     form_names.append('form{}'.format(form_dir[4:]))

    main_form = sorted(forms, key=lambda x: x.name.local_name)[0]
    try:
        form_name = list(main_form.labels.get((_EFORMS_LABEL_ROLE, 'en'), []))[0].content
    except IndexError:
        raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_EFORMS_LABEL_ROLE, main_form.name.clark))

    form_name_no_space = form_name.replace(' ','').lower()
    new_model.identifier = 'http://xbrl.ferc.gov/taxonomy/{}/{}'.format(form_name_no_space, _NEW_VERSION)
    new_model.name = 'FERC {} Taxonomy'.format(form_name)
    new_model.name_language = 'en'
    new_model.description = 'This taxonomy packacge contains the taxonomies used for FERC {}'.format(form_name)
    new_model.description_language = 'en-US'
    new_model.version = _NEW_VERSION
    new_model.license_href = 'https://eCollection.ferc.gov/taxonomy/terms/TaxonomiesTermsConditions.html'
    new_model.license_name = 'Taxonomies Terms and Conditions'
    new_model.publisher = 'Federal Energy Regulatory Commission (FERC)'
    new_model.publisher_url = 'http://www.ferc.gov/'
    new_model.publisher_country = 'US'
    new_model.publication_date = _NEW_VERSION
    new_model.rewrites['../'] = 'https://eCollection.ferc.gov/taxonomy/{}/{}/'.format(form_name_no_space, _NEW_VERSION)

def organize_taxonomy(model_xbrl, new_model, options):
    global _OPTIONS
    _OPTIONS = options

    # get all relationships
    for arcrole, ELR, linkqname, arcqname in model_xbrl.baseSets.keys():
        if ELR and linkqname and arcqname and arcrole and not arcrole.startswith("XBRL-"):
            # This is an individual base set
            #relationship_set = model_xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname)
            #map['rels'][(arcrole, ELR, linkqname, arcqname)]['relationship-set'] = relationship_set
            organize_networks(model_xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname), new_model)

    organize_labels(model_xbrl, new_model)
    organize_references(model_xbrl, new_model)

    # Find forms and the schedules that make up the form
    forms, schedule_role_map  = find_forms(new_model)
    # Remove networks that are not part of a form.
    clean_up_networks(new_model, schedule_role_map)
    # Add schedule form relationships
    schedule_form_networks(new_model, forms, schedule_role_map)
    # Build cubes
    organize_cubes(new_model)
    # assign documents to networks and cubes
    schedule_documents = assign_documents_to_networks(new_model, schedule_role_map)
    # Add arcroles for footnote instances.
    add_footnote_arcroles(model_xbrl, new_model)
    #count_docs(new_model)
    # Build entry points for forms and ferc-all
    form_entry_documents = add_form_entry_points(new_model, forms, schedule_documents)
    # Add the default table
    create_default_table(new_model, form_entry_documents, forms, schedule_role_map)
    # fill in the package meta data information
    add_package_defaults(new_model, forms)

    return new_model

def organize_networks(relationship_set, new_model):

    # Skip dimensional relatonships. These will be recreated based on the presentation.
    if (( # presentation
        (relationship_set.linkqname.localName == 'presentationLink' and
          relationship_set.linkqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
          relationship_set.arcqname.localName == 'presentationArc' and
          relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
          relationship_set.arcrole == _PARENT_CHILD) or 
          # calculation
         (relationship_set.linkqname.localName == 'calculationLink' and
          relationship_set.linkqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
          relationship_set.arcqname.localName == 'calculationArc' and
          relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
          relationship_set.arcrole == _SUMMATION_ITEM)) and
        is_concept_to_concept_network(relationship_set)):

        # Create the new network
        link_name = new_qname(new_model, relationship_set.linkqname)
        arc_name = new_qname(new_model, relationship_set.arcqname)
        # Get or create the arcrole
        arcrole= new_arcrole(new_model, relationship_set.modelXbrl, relationship_set.arcrole)
        elrole = (new_model.get('Role', get_new_role_uri(relationship_set.linkrole)) or
                  new_role(new_model, relationship_set.modelXbrl, relationship_set.linkrole))
        network = new_model.new('Network', link_name, arc_name, arcrole, elrole)

        # Add the relationships and also create the concepts
        for relationship in sorted(relationship_set.modelRelationships, key=lambda x: x.order or 1):
            # Make sure the concepts of the relationship are created
            from_concept = new_concept(new_model, relationship.fromModelObject)
            to_concept = new_concept(new_model, relationship.toModelObject)
            rel_atts = {new_qname_from_clark(new_model, k): v
                        for k, v in relationship.arcElement.attrib.items()
                        if not k.startswith('{http://www.w3.org/1999/xlink}')
                        and not k in ('order', 'weight', 'preferredLabel')}
            if relationship.preferredLabel is None:
                preferred_label = None
            else:
                preferred_label = new_label_role(new_model, relationship.modelXbrl, relationship.preferredLabel)
            network.add_relationship(from_concept, to_concept, 'calc', relationship.weight, preferred_label, rel_atts)

def is_concept_to_concept_network(relationship_set):
    for rel in relationship_set.modelRelationships:
        if not is_concept_to_concept_relationship(rel):
            return False
    return True

def is_concept_to_concept_relationship(relationship):
    return isinstance(relationship.fromModelObject, ModelConcept) and isinstance(relationship.toModelObject, ModelConcept)

def new_qname(new_model, model_qname):

    if model_qname.namespaceURI == _OLD_NAMESPACE:
        override_namespace = _CORE_NAMESPACE
    elif model_qname.namespaceURI == _OLD_TYPE_NAMESPACE:
        override_namespace = _TYPE_NAMESPACE
    elif model_qname.namespaceURI == _OLD_PART_NAMESPACE:
        override_namespace = _PART_NAMESPACE
    else:
        override_namespace = model_qname.namespaceURI

    return new_model.new('QName', override_namespace, model_qname.localName)

def new_concept(new_model, model_concept):
    concept_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_concept, True)

    if new_model.get('Concept', concept_name) is not None:
        # The concept is already in the model
        return new_model.get('Concept', concept_name)

    period_type = model_concept.periodType
    balance_type = model_concept.balance

    if model_concept.isTypedDimension:
        typed_domain_name = new_qname(new_model, model_concept.typedDomainElement.qname)
        typed_domain = new_model.get('TypedDomain', typed_domain_name) or new_typed_domain(new_model, model_concept.typedDomainElement) 
    else:
        typed_domain = None

    concept = new_model.new('Concept',
                          concept_name,
                          data_type,
                          abstract,
                          nillable,
                          period_type,
                          balance_type,
                          substitution_group,
                          id,
                          attributes,
                          typed_domain)

    # Assign document
    if concept_name.namespace == _CORE_NAMESPACE:
        document = new_document(new_model, _DOCUMENT_MAP[_CORE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _CORE_NAMESPACE, _CORE_DESCRIPTION)
    else:
        document = new_document(new_model, model_concept.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_concept.modelDocument.targetNamespace)

    document.add(concept)

    return concept

def get_element_info(new_model, model_element, is_concept=False):

    name = new_qname(new_model, model_element.qname)

    new_type_qname = fix_type_qname(new_model, model_element.typeQname)
    # determine if this is a type that is defined in this taxonomy or an external data type (i.e. DTR)
    data_type = (new_model.get('Type', new_type_qname) or 
                    new_type(new_model, model_element.type if model_element.type is not None else model_element.typeQname, new_type_qname))
    if model_element.substitutionGroup is None:
        substitution_group = None
    else:
        if model_element.substitutionGroupQname.clarkNotation in (_ITEM, _TUPLE):
            substitution_group = new_qname(new_model, model_element.substitutionGroupQname)
        else:
            # This is a derrived substitution group
            sub_group_qname = new_qname(new_model, model_element.substitutionGroupQname)
            if is_concept:
                substitution_group = (new_model.get('Concept', sub_group_qname) or
                                    new_concept(new_model, model_element.substitutionGroup))
            else: # the substitution group is an element
                substitution_group = (new_model.get('Element', sub_group_qname) or
                                    new_element(new_model, model_element.substitutionGroup))

    abstract = model_element.isAbstract
    nillable = model_element.isNillable
    id = model_element.id
    attributes = get_element_attributes(new_model, model_element.attrib.items())

    return (name,
            data_type,
            abstract,
            nillable,
            id,
            substitution_group,
            attributes)

def fix_type_qname(new_model, old_qname):
    if old_qname.namespaceURI == _OLD_TYPE_NAMESPACE:
        type_namespace = _TYPE_NAMESPACE
    else:
        type_namespace = old_qname.namespaceURI

    return new_model.new('QName', type_namespace, old_qname.localName)


def get_element_attributes(new_model, attributes):
    '''Convert lxml attribute dictionary to SXM attribute dictionary'''
    return {new_qname_from_clark(new_model, n): v for n, v in attributes}

def new_qname_from_clark(new_model, name):
    '''Separate the namespace and local name in a clark notation qname'''
    res = re.match('({(.*)})?(.*)', name.strip())
    # There will be 3 items in the groups. [1] is the namespace and [2] is the local name
    return new_model.new('QName', res.groups()[1], res.groups()[2])

def new_typed_domain(new_model, model_element):
    name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element)
    typed_domain = new_model.new('TypedDomain', name, data_type, abstract, nillable, id, substitution_group, attributes)

    # Assign document
    if typed_domain.name.namespace == _CORE_NAMESPACE:
        document = new_document(new_model, _DOCUMENT_MAP[_CORE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _TYPE_NAMESPACE, _TYPE_DESCRIPTION)
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(typed_domain)

    return typed_domain

def new_type(new_model, model_type, new_type_qname):
    # model_type may be an arelle ModelType or a qname. If it is a qname it is a base xbrl type
    if new_model.get('Type', new_type_qname) is not None:
        return new_model.get('Type', new_type_qname)

    if isinstance(model_type, QName):
        # This is base XML type.
        type_parent = None
        type_content = None
    else:
        if model_type.typeDerivedFrom is not None:
            type_parent_qname = fix_type_qname(new_model, model_type.typeDerivedFrom.qname)
            type_parent = new_model.get('Type', type_parent_qname) or new_type(new_model, model_type.typeDerivedFrom, type_parent_qname)
        else:
            type_parent = None

        type_content = etree.tostring(model_type)

    new_data_type = new_model.new('Type', new_type_qname, type_parent, type_content)

    if not new_data_type.is_base_xml: # otherwise this is a base xml type and there is not document
        if new_data_type.name.namespace == _TYPE_NAMESPACE:
            type_document = new_document(new_model, _DOCUMENT_MAP[_TYPE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _TYPE_NAMESPACE, _TYPE_DESCRIPTION)
        else:
            if isinstance(model_type, ModelType) and model_type.qname.localName.endswith('@anonymousType'):
                type_document = None
            else:
                type_document = new_document(new_model, model_type.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_type.modelDocument.targetNamespace)
        if type_document is not None:
            type_document.add(new_data_type)

    return new_data_type

def new_element(new_model, model_element):

    element_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element)
    new_element =  new_model.new('Element',
                                element_name,
                                data_type,
                                abstract,
                                nillable,
                                id,
                                substitution_group,
                                attributes)

    # Assign document
    if new_element.name.namespace == _CORE_NAMESPACE:
        document = new_document(new_model, _DOCUMENT_MAP[_CORE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _TYPE_NAMESPACE, _TYPE_DESCRIPTION)
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(new_element)

    return new_element

def new_part_element(new_model, model_element):

    element_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element)
    new_part_element =  new_model.new('PartElement',
                          element_name,
                          data_type,
                          abstract,
                          nillable,
                          id,
                          substitution_group,
                          attributes)
    
    # Assign document
    if new_part_element.name.namespace == _PART_NAMESPACE:
        document = new_document(new_model, _DOCUMENT_MAP[_PART_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _PART_NAMESPACE, _PART_DESCRIPTION)
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(new_part_element)

    return new_part_element

def new_arcrole(new_model, model_xbrl, arcrole_uri):

    document_uri = None
    is_ferc = False
    # Convert arcrole uri for new version
    ferc_match = _OLD_ARCROLE_MATCH.fullmatch(arcrole_uri)
    if ferc_match is not None:
        # Convert arcrle uri to lastest version
        #new_arcrole_uri = 'http://{}.ferc.gov/forms/{}/arcroles/{}'.format(ferc_match.group('pre'), _NEW_VERSION, ferc_match.group('name'))
        new_arcrole_uri = arcrole_uri
        document_uri = '{}-core-arcroles_{}.xsd'.format(_CORE_NAME, _NEW_VERSION)
        is_ferc = True
    else: # not defined by the ferc taxonomy
        new_arcrole_uri = arcrole_uri

    # Check if it already exits
    if new_model.get('Arcrole', new_arcrole_uri):
        return new_model.get('Arcrole', new_arcrole_uri)

    '''convert an arelle arcrole to a sxm arcrole'''
    old_arcrole = model_xbrl.arcroleTypes[arcrole_uri]
    if len(old_arcrole) == 0:
        if arcrole_uri in xc.standardArcroleCyclesAllowed:
            usedons = (new_model.new('QName', 'http://www.xbrl.org/2003/linkbase' ,xc.standardArcroleArcElement(arcrole_uri)),)
            definition = ''
            cycles_allowed = xc.standardArcroleCyclesAllowed[arcrole_uri][0] # this is the cycles allowed value
        else: 
            error('FERCSerializerError', 'arcrole {} not found in source DTS'.format(new_arcrole_uri))
    else:
        usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_arcrole[0].usedOns)
        cycles_allowed = old_arcrole[0].cyclesAllowed
        definition = old_arcrole[0].definition
        document_uri = document_uri or old_arcrole[0].modelDocument.uri
        document_namespace = old_arcrole[0].modelDocument.targetNamespace

    new_arcrole =  new_model.new('Arcrole', new_arcrole_uri, cycles_allowed, definition, usedons)

    # assign document
    if document_uri is not None:
        if is_ferc:
            document = new_document(new_model, _DOCUMENT_MAP[_ARCROLE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _ARCROLE_NAMESPACE, _ARCROLE_DESCRIPTION)
        else:
            # This code is untested with FERC taxonomies
            document = new_document(new_model, document_uri, new_model.DOCUMENT_TYPES.SCHEMA, document_namespace)
        document.add(new_arcrole)

    return new_arcrole

def get_new_role_uri(uri):
    return uri

    # # Convert role uri for new version
    # ferc_match = _OLD_ROLE_MATCH.fullmatch(uri)
    # if ferc_match is not None:
    #     # Convert arcrole uri to lastest version
    #     return 'http://{}ferc.gov/form/{}/roles/{}/{}'.format('{}.'.format(ferc_match.group('pre')) if ferc_match.group('pre') is not None else '', 
    #                                                                    _NEW_VERSION, 
    #                                                                    ferc_match.group('role_type'),
    #                                                                    ferc_match.group('rest'))
    # else: # not defined by the ferc taxonomy
    #     return uri

def new_role(new_model, model_xbrl, role_uri):

    new_role_uri = get_new_role_uri(role_uri)

    # Check if it already exists
    if new_model.get('Role', new_role_uri):
        return new_model.get('Role', new_role_uri)

    '''convert an arelle role to a sxm role'''
    old_role = model_xbrl.roleTypes[role_uri]
    if len(old_role) == 0:
        if role_uri in xc.standardRoles:
            usedons = tuple()
            definition = None
        else:
            error('FERCSerializerError', 'role {} not found in source DTS'.format(role_uri))
    else:
        usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_role[0].usedOns)
        definition = old_role[0].definition

    # The documents for the role definitions will be assigned later
    return new_model.new('Role', new_role_uri, definition, usedons)

def organize_labels(model_xbrl, new_model):
    '''Get the labels for the concepts that are in the new model'''

    # need the core document to add imports for label roles and the label linkbase
    core_document = new_model.documents.get(_DOCUMENT_MAP[_CORE_NAMESPACE])
    if core_document is None:
        raise FERCSerialzierException("Cannot find the core xsd while adding labels")

    label_network = model_xbrl.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-label')
    for label_rel in label_network.modelRelationships:
        new_concept = new_model.get('Concept', new_qname(new_model, label_rel.fromModelObject.qname))
        if new_concept is not None:
            old_label = label_rel.toModelObject
            label_role = new_label_role(new_model, model_xbrl, old_label.role)
            # label_role = new_model.get('Role', get_new_role_uri(old_label.role)) 
            # if label_role is None:
            #     label_role = new_role(new_model, label_rel.modelXbrl, old_label.role)
            #     assign_role_document(label_role)
            #     # add import to core file
            #     if label_role.document is not None: # if its none it is a core xbrl role
            #         core_document.add(label_role.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
            fix = lambda x: x.strip() if label_role == _STANDARD_LABEL else x
            new_label = new_concept.add_label(label_role, old_label.xmlLang.lower(), fix(old_label.textValue))
            label_document_name = '{}-core_{}_lab.xml'.format(_CORE_NAME, _NEW_VERSION)
            label_document = new_document(new_model, label_document_name, new_model.DOCUMENT_TYPES.LINKBASE)
            label_document.add(new_label)
            # add the label document as an import to the core file
            core_document.add(label_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)

def new_label_role(new_model, old_model, old_role):
    core_document = new_model.documents.get(_DOCUMENT_MAP[_CORE_NAMESPACE])
    label_role = new_model.get('Role', get_new_role_uri(old_role)) 
    if label_role is None:
        label_role = new_role(new_model, old_model, old_role)
        assign_role_document(label_role)
        # add import to core file
        if label_role.document is not None: # if its none it is a core xbrl role
            core_document.add(label_role.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
    return label_role

def organize_references(model_xbrl, new_model):
    '''Get the references for the concepts that are in the new model'''

    # need the core document to add imports for reference roles, part elements and the reference linkbases
    core_document = new_model.documents.get(_DOCUMENT_MAP[_CORE_NAMESPACE])
    if core_document is None:
        raise FERCSerialzierException("Cannot find the core xsd while adding references")

    ref_network = model_xbrl.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-reference')
    for ref_rel in ref_network.modelRelationships:
        new_concept = new_model.get('Concept', new_qname(new_model, ref_rel.fromModelObject.qname))
        if new_concept is not None:
            old_ref = ref_rel.toModelObject
            ref_role = new_model.get('Role', get_new_role_uri(old_ref.role)) 
            if ref_role is None:
                  ref_role = new_role(new_model, old_ref.modelXbrl, old_ref.role)
                  assign_role_document(ref_role)
            # add import to core file
            if ref_role.document is None: # if it is none it is an xbrl core role
                core_document.add(ref_role.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
            # Get the parts
            new_parts = []
            for old_part in old_ref:
                part_name = new_qname(new_model, old_part.qname)
                part_element = new_model.get('PartElement', part_name)
                if part_element is None:
                    old_part_element = model_xbrl.qnameConcepts.get(old_part.qname)
                    if old_part_element is None:
                        raise FERCSerialzierException("Cannot find refernce part element definition for {}".format(old_part.qname.clarkNotation))
                    part_element = new_part_element(new_model, old_part_element)
                new_parts.append(new_model.new('Part', part_element, old_part.textValue))
                # add import to core file
                core_document.add(part_element.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

            role_match = _NEW_ROLE_MATCH.fullmatch(ref_role.role_uri)
            if role_match is None:
                FERCSerialzierException("Cannot determine type of role from role reference '{}'".format(ref_role.role_uri))
            new_ref = new_concept.add_reference(ref_role, new_parts)
            ref_type = '-'.join(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', role_match.group('rest'))).lower() # splits camel case and joins with a dash
            ref_document_name = '{}-core-ref-{}_{}_ref.xml'.format(_CORE_NAME, ref_type, _NEW_VERSION)
            ref_document = new_document(new_model, ref_document_name, new_model.DOCUMENT_TYPES.LINKBASE)
            ref_document.add(new_ref)
            # add the ref linkbase as a linkbase ref in the core
            core_document.add(ref_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)

def assign_role_document(role):
    ferc_match = _NEW_ROLE_MATCH.fullmatch(role.role_uri)
    if ferc_match is None:
        return None
    document_name = '{}-{}-{}-roles_{}.xsd'.format(_CORE_NAME, 'core', ferc_match.group('role_type')[:3], _NEW_VERSION)
    namespace = 'http://www.ferc.gov/form/roles/{}'.format(ferc_match.group('role_type'))


    description = None
    if ferc_match.group('role_type') == 'label':
        description = _LABEL_ROLE_DESCRIPTION
    elif ferc_match.group('role_type') == 'reference':
        description = _REFERENCE_ROLE_DESCRIPTION
    role_document = new_document(role.dts, document_name, role.DOCUMENT_TYPES.SCHEMA, namespace, description)
    role_document.add(role)

def organize_cubes(new_model):
    ''' Build the cubes
    
    The cubes are built from the presentation relationships. The existing dimension relationships are ignored.
    '''
    # need utility function for building networks of members
    build_from_network = new_model.get_utility('Member', 'build_from_network') # This is a class method to create member nodes

    cubes = []
    # Go through the presentation relationships and find the cubes
    for network in new_model.get_match('Network', (None, None, _PARENT_CHILD)):
        tables = find_dim_parts(network, 'TABLE')
        for table in tables:
            cube_node = new_model.new('Cube', network.role, table)
            cubes.append(cube_node)
            # Find the primary items
            primaries = find_dim_parts(network, 'LINE ITEMS', table)
            for primary in primaries:
                primary_node = new_model.new('Primary', primary, network.role)
                cube_node.add_primary_node(primary_node)
                top_members = build_from_network(network, primary)
                for top_member in top_members:
                    primary_node.add_child_node(top_member)

            # Get each of the dimensions
            dimensions = find_dim_parts(network, 'AXIS', table)
            for dimension in dimensions:
                dimension_node = new_model.new('Dimension', dimension, network.role, dimension.typed_domain)
                cube_node.add_dimension_node(dimension_node)
                # Get the domains for the dimension
                domains = find_dim_parts(network, 'DOMAIN', dimension)
                if len(domains) > 1:
                    raise FERCSerialzierException("Dimension {} has more than one domain. Only 1 is allowed".foramt(dimension.name.clark,
                                                                                                                    '\n'.join([x.name.clark for x in domains])))
                elif len(domains) == 1:
                    domain = list(domains)[0]
                    domain_node = new_model.new('Member', domain, network.role)
                    dimension_node.add_child_node(domain_node)
                    top_members = build_from_network(network, domain)
                    for top_member in top_members:
                        domain_node.add_child_node(top_member)
                    # Add the default
                    if dimension_node.is_explicit:
                        dimension_node.default = domain_node
            
    return cubes

def find_dim_parts(network, part_name, root=None):
    dim_parts = set()
    if root is None:
        concepts = network.concepts
    else:
        # Get all the concepts under the root concept
        concepts = [x.to_concept for x in network.get_descendants(root)]

    for concept in concepts:
        for standard_labels in concept.get_match('Label', (_STANDARD_LABEL,)):
            for standard_label in standard_labels:
                if standard_label.content.upper().endswith('[{}]'.format(part_name.upper())):
                    dim_parts.add(concept)
                    break
    return dim_parts

def is_dimensional(concept, dimension_type):
    for standard_label in concept.get_match('Label', (_STANDARD_LABEL,)):
        if standard_label.content.endswith('[{}]'.format(dimension_type.uppercase())):
            return True
    return False

def create_default_table(new_model, form_entry_documents, forms, schedule_role_map):
    ''''
    The default table is a table of only line items (no dimensions) for line items that only exist in 
    a tables with at least one typed dimension. Because of the typed dimension, facts for these
    concepts cannot be reported without dimensions (typed dimensions don't have a default). So the default
    table is created to allow these facts to be valid in the default table.
    '''

    # Reverse the schedule_role_map so I can look up by role. This will identify the document
    # for the schedule
    role_schedule_map = dict()
    for schedule_concept, roles in schedule_role_map.items():
        for role in roles:
            role_schedule_map[role] = schedule_concept
    
    # Find the line items
    typed_cubes = set()
    for cube in new_model.cubes.values():
        for dim in cube.dimensions:
            if dim.is_typed:
                typed_cubes.add(cube)
                break

    # Go through the cubes with typed dimensions. Find the cooresponding presentation network and
    # look for siblings of the table that are total elements
    for cube in typed_cubes:
        typed_total_concepts = set()
        network = new_model.get('Network', new_qname_from_clark(new_model, _PRESENTATION_LINK_ELEMENT), 
                                           new_qname_from_clark(new_model, _PRESENTATION_ARC_ELEMENT),
                                           _PARENT_CHILD,
                                           cube.role)
        if network is None:
            raise FERCSerialzierException("Cannot find cooresponding network for cube {} in role {}".format(cube.concept.name, cube.role.role_uri))
        parent_rels = network.get_parents(cube.concept)
        if len(parent_rels) != 1:
            raise FERCSerialzierException("Cube {} is in a presentation network more than once in role {}.".find(cube.concept.name.clark, cube.role.role_uri))
        for child_rel in network.get_children(parent_rels[0].from_concept):
            if (child_rel.order >= parent_rels[0].order and # This indicates the child is a following sibling of the table
                child_rel.to_concept.type.is_numeric and
                child_rel.to_concept is not cube.concept):
                typed_total_concepts.add(child_rel.to_concept)
        
        if len(typed_total_concepts) > 0:
            # Create a new role for the totals. This will be based on the exiting cube role
            i = 0
            while True:
                new_role_uri = '{}Total{}'.format(cube.role.role_uri, '' if i == 0 else str(i))
                if new_role_uri not in new_model.roles:
                    break
                else:
                    i += 1
                if i > 1000000:
                    raise FERCSerialzierException("In a terrible loop trying to create the total role for role {}".format(cube.role.role_uri))
            new_role = new_model.new('Role', new_role_uri, '{} - Totals'.format(cube.role.description), cube.role.used_ons)
            cube.role.document.add(new_role)
            # Create the new cube
            new_cube = new_model.new('Cube', new_role, cube.concept)
            new_cube.document = cube.document
            new_primary = new_model.new('Primary', cube.primary_items[0].concept, new_role)
            new_cube.add_primary_node(new_primary)
            # create the new presentation network
            new_network = new_model.new('Network', network.link_name, 
                                                   network.arc_name,
                                                   network.arcrole,
                                                   new_role)
            presentation_document = network.from_relationships[network.roots[0]][0].document
            presentation_document.add(new_network.add_relationship(parent_rels[0].from_concept, new_cube.concept))
            presentation_document.add(new_network.add_relationship(new_cube.concept, new_primary.concept))

            for concept in typed_total_concepts:
                # add to the cube
                new_primary.add_child(concept.get_class('Member'), concept, new_role)
                # add to the presentation network
                new_rel = new_network.add_relationship(new_primary.concept, concept)
                presentation_document.add(new_rel)

    # # remove concepts that are in tables that only have explicit dimensions that all have defaults
    # default_concepts = typed_total_concepts - defaulted_cube_concepts
    
    # if len(default_concepts)> 0:
    #     # Create the default concepts (table, line items, abastract)
    #     string_item_type_name = new_model.new('QName', _XBRLI_NS, 'stringItemType')
    #     string_item_type = new_model.get('Type', string_item_type_name) or new_model.new('Type', string_item_type_name)
    #     substitution_group_name = new_model.new('QName', _XBRLI_NS, 'item')
    #     table_substitution_group_name = new_model.new('QName', _DIMENSION_NAMESPACE, 'hypercubeItem')
    #     standard_label_role = new_model.get('Role', _STANDARD_LABEL) or new_model.new('Role', _STANDARD_LABEL)
    #     terse_label_role = new_model.get('Role', _TERSE_LABEL) or new_model.new('Role', _TERSE_LABEL)

    #     core_document = new_document(new_model, _DOCUMENT_MAP[_CORE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _CORE_NAMESPACE, _CORE_DESCRIPTION)
    #     #Create the default extended link role
    #     used_ons = (new_model.new('QName', _LINK_NS, 'definitionLink'),
    #                 new_model.new('QName', _LINK_NS, 'presentationLink'))
    #     default_role = new_model.new('Role', 'http://ferc.gov/form/{}/roles/default'.format(_NEW_VERSION), _DEFAULT_ROLE_DEFINITION, used_ons)

    #     # Create the documents 
    #     default_linkbase = new_document(new_model, 'default/default_{}_def.xml'.format(_NEW_VERSION), new_model.DOCUMENT_TYPES.LINKBASE)
    #     default_labels = new_document(new_model, 'default/default_{}_lab.xml'.format(_NEW_VERSION), new_model.DOCUMENT_TYPES.LINKBASE)
    #     default_schema = new_document(new_model, 'default/default_{}.xsd'.format(_NEW_VERSION), 
    #                                   new_model.DOCUMENT_TYPES.SCHEMA, '{}default'.format(_NAMESPACE_START))
    #     default_schema.add(default_linkbase, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
    #     default_schema.add(default_labels, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
    #     default_presentation = new_document(new_model, 'default/default_{}_pre.xml'.format(_NEW_VERSION), new_model.DOCUMENT_TYPES.LINKBASE)
    #     default_schema.add(default_presentation, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
    #     default_role.document = default_schema

    #     # add the default schema to each of the form entry points
    #     for form_document in form_entry_documents:
    #         form_document.add(default_schema, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
        

    #     default_table = new_model.new('Concept', new_model.new('QName', _CORE_NAMESPACE, 'DefaultTable'),
    #                                             string_item_type,
    #                                             True, # abstract
    #                                             True, # nillable
    #                                             'duration',
    #                                             None, # id
    #                                             table_substitution_group_name)
    #     lab = default_table.add_label(standard_label_role, 'en', _DEFAULT_TABLE_STANDARD_LABEL)
    #     lab.document = default_labels
    #     lab = default_table.add_label(terse_label_role, 'en', _DEFAULT_TABLE_TERSE_LABEL)
    #     lab.document = default_labels
    #     default_table.document = core_document
    #     default_line_items = new_model.new('Concept', new_model.new('QName', _CORE_NAMESPACE, 'DefaultLineItems'),
    #                                             string_item_type,
    #                                             True, # abstract
    #                                             True, # nillable
    #                                             'duration',
    #                                             None, # id
    #                                             substitution_group_name)
    #     lab = default_line_items.add_label(standard_label_role, 'en', _DEFAULT_LINE_ITEMS_STANDARD_LABEL)
    #     lab.document = default_labels
    #     lab = default_line_items.add_label(terse_label_role, 'en', _DEFAULT_LINE_ITEMS_TERSE_LABEL)
    #     lab.document = default_labels
    #     default_line_items.document = core_document
    #     default_abstract = new_model.new('Concept', new_model.new('QName', _CORE_NAMESPACE, 'DefaultAbstract'),
    #                                             string_item_type,
    #                                             True, # abstract
    #                                             True, # nillable
    #                                             'duration',
    #                                             None, # id
    #                                             substitution_group_name)
    #     lab = default_abstract.add_label(standard_label_role, 'en', _DEFAULT_ABSTRACT_STANDARD_LABEL)
    #     lab.document = default_labels 
    #     lab = default_abstract.add_label(terse_label_role, 'en', _DEFAULT_ABSTRACT_TERSE_LABEL)
    #     lab.document = default_labels
    #     default_abstract.document = core_document 

    #     # Create the default cube
    #     default_cube = new_model.new('Cube', default_role, default_table)
    #     default_primary = new_model.new('Primary', default_line_items, default_role)
    #     default_cube.add_primary_node(default_primary)
    #     default_cube.document = default_linkbase
    #     default_primary.document = default_linkbase

    #     # Create presentation the network
    #     network_key = (new_qname_from_clark(new_model, _PRESENTATION_LINK_ELEMENT),
    #                 new_qname_from_clark(new_model, _PRESENTATION_ARC_ELEMENT),
    #                 new_model.get('Arcrole', _PARENT_CHILD) or new_model.new('Arcrole', _PARENT_CHILD),
    #                 default_role)
    #     network = new_model.get('Network', *network_key) or new_model.new('Network', *network_key)
    #     default_presentation.add(network.add_relationship(default_abstract, default_table))
    #     default_presentation.add(network.add_relationship(default_table, default_line_items))

    #     # Add to the default cube
    #     for concept in sorted(default_concepts, key=lambda x: x.name.clark):
    #         child = default_primary.add_child(new_model.get_class('Member'), concept)
    #         child.document = default_linkbase
    #         default_presentation.add(network.add_relationship(default_line_items, concept))

def new_document(new_model, uri, document_type, target_namespace=None, description=None):
    return new_model.get('Document', uri) or new_model.new('Document', uri, document_type, target_namespace, description)

def clean_up_networks(new_model, schedule_role_map):
    '''Remove networks that are not part of the forms'''
    # Get all the roles that will be outputed from the schedule map
    schedule_roles = {x for y in schedule_role_map.values() for x in y}
    # Go through all the networks and delete the ones that are not in the schedule roles
    for network in list(new_model.networks.values()): # Using a list so we can delete netowrks in the new_model.networks dictionary
        if network.role not in schedule_roles:
            # this network will be deleted
            delete_network(new_model, network)

    # Next need to clean up left over orphans
    clean_up_orphans(new_model)

def delete_network(new_model, network):
    for rel in network.relationships:
        rel.remove()
    new_model.remove(network)

def count_docs(new_model):
    counts = collections.defaultdict(lambda: [0,0])
    for component in (list(new_model.networks.values()) +
                      list(new_model.concepts.values()) +
                      list(new_model.part_elements.values()) +
                      list(new_model.typed_domains.values()) +
                      list(new_model.elements.values()) +
                      list(new_model.types.values()) +
                      list(new_model.arcroles.values()) +
                      list(new_model.roles.values()) +
                      list(new_model.cubes.values())):
        if component.document is None:
            counts[component.get_class_name()][0] += 1
        else:
            counts[component.get_class_name()][1] += 1

        if component.get_class_name() == 'Concept':
            for labels in component.labels.values():
                for label in labels:
                    if label.document is None:
                        counts[label.get_class_name()][0] += 1
                    else:
                        counts[label.get_class_name()][1] += 1
            for refs in component.references.values():
                for ref in refs:
                    if ref.document is None:
                        counts[ref.get_class_name()][0] += 1
                    else:
                        counts[ref.get_class_name()][1] += 1

    print('class', 'no doc', 'doc')
    for k, v in counts.items():
        print(k, v[0], v[1])

    return counts

def clean_up_orphans(new_model):

    for component in (list(new_model.networks.values()) +
                      list(new_model.concepts.values()) +
                      list(new_model.part_elements.values()) +
                      list(new_model.typed_domains.values()) +
                      list(new_model.elements.values()) +
                      list(new_model.types.values()) +
                      list(new_model.arcroles.values()) +
                      list(new_model.roles.values())):
        clean_up_model_component(component)

def clean_up_model_component(component):
    
    remove = False
    if component.dts.component_exists(component):
        # Network
        if isinstance(component, component.get_class('Network')):
            if len(component.relationships) == 0:
                remove = True
        # Concept
        elif isinstance(component, component.get_class('Concept')):
            if _NEW_NS_MATCH.fullmatch(component.name.namespace)and (len(component.to_concept_relationships) + len(component.from_concept_relationships)) == 0:
                remove =  all([clean_up_model_component(x) for x in component.derrived_concepts()])
        # Part Element
        elif isinstance(component, component.get_class('PartElement')):
            if _NEW_NS_MATCH.fullmatch(component.name.namespace) and len(component.parts) == 0:
                remove = all([clean_up_model_component(x) for x in component.derrived_substitution_groups()])
        # Typed Domain
        elif isinstance(component, component.get_class('TypedDomain')):
            if _NEW_NS_MATCH.fullmatch(component.name.namespace) and len(component.concepts) == 0:
                remove = all([clean_up_model_component(x) for x in component.derrived_substitution_groups()])
        # Element
        elif isinstance(component, component.get_class('Element')):
            if _NEW_NS_MATCH.fullmatch(component.name.namespace):
                remove = all([clean_up_model_component(x) for x in component.derrived_substitution_groups()])
        # Type
        elif isinstance(component, component.get_class('Type')):
            if _NEW_NS_MATCH.fullmatch(component.name.namespace) and len(component.elements(True)) == 0:
                remove = all([clean_up_model_component(x) for x in component.derrived_types()])
        # Arcrole
        elif isinstance(component, component.get_class('Arcrole')):
            if (_NEW_ARCROLE_MATCH.fullmatch(component.arcrole_uri) is not None and 
                len(component.networks) == 0):
                remove = True
        # Role
        elif isinstance(component, component.get_class('Role')):
            if (_NEW_ROLE_MATCH.fullmatch(component.role_uri) is not None and 
                len(component.networks) == 0 and
                len(component.resources) == 0):
                remove = True
        else:
            raise FERCSerialzierException("Do not have a clean up method for '{}'".format(type(component).__name__))

        if remove:
            remove = component.dts.remove(component)

    return remove

def assign_documents_to_networks(new_model, schedule_role_map):
    schedule_documents = dict()
    for schedule, roles in schedule_role_map.items():
        if len(roles) == 0:
            continue
        # The folder for the schedule is the schedule element name
        schedule_name = schedule.name.local_name.split('Abstract')[0]
        if schedule.type.name.local_name == 'formItemType': # This is the list of schedules
            schedule_name = 'ScheduleListOfSchedules{}'.format(schedule_name)
        # The file name will be the page number
        file_name = None
        for label_info in sorted(schedule.labels, key=lambda x: x[0].role_uri):
            if label_info[0].role_uri.lower().endswith('page'):
                file_name = 'sched-{}'.format(sorted(schedule.labels[label_info], key=lambda x: x.content)[0].content)
                break
        if file_name is None: # no page number was found
            file_name = 'sched-0'
        document_start = 'schedules/{schedule_name}/{file_name}_{version}'.format(schedule_name=schedule_name, file_name=file_name, version=_NEW_VERSION)
        schema_document = new_document(new_model, 
            '{}.xsd'.format(document_start),
            new_model.DOCUMENT_TYPES.SCHEMA,
            '{}{}/sched-{}'.format(_NAMESPACE_START, _NEW_VERSION, schedule_name))
        schedule_documents[schedule] = schema_document

        for role in roles:
            for network in new_model.get_match('Network', (None, None, None, role)):
                if len(network.relationships) > 0:
                    linkbase_type = network.link_name.local_name[:3].lower()
                    linkbase_document = new_document(new_model,
                                                    '{}_{}.xml'.format(document_start, linkbase_type),
                                                    new_model.DOCUMENT_TYPES.LINKBASE)
                    for rel in network.relationships:
                        linkbase_document.add(rel)
                    # add the linkbase ref to the schema document
                    schema_document.add(role)
                    schema_document.add(linkbase_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
                    if not network.arcrole.is_standard:
                        schema_document.add(network.arcrole, new_model.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
            
            for cube in new_model.get_match('Cube', role):
                cube_tops = cube.primary_items + cube.dimensions 
                if len(cube_tops) != 0:
                    linkbase_document = new_document(new_model,
                                                     '{}_def.xml'.format(document_start),
                                                     new_model.DOCUMENT_TYPES.LINKBASE)
                    linkbase_document.add(cube)
                    for cube_top in cube_tops:
                        linkbase_document.add(cube_top) # This is either a primary or dimension
                        for cube_node in cube_top.all_descendants:
                            linkbase_document.add(cube_node)
                    # Add the linkbase ref to the schema document
                    schema_document.add(linkbase_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)

    return schedule_documents
                                        
def schedule_form_networks(new_model, forms, schedule_role_map):
    # Create the schedule-form arcrole
    schedule_form_arcrole = new_model.new('Arcrole', 
                                          _SCHEDULE_FORM_ARCROLE,
                                          'none',
                                          _SCHEDULE_FORM_DEFINITION,
                                          (new_model.new('QName', _LINK_NS, 'presentationArc'),
                                           new_model.new('QName', _LINK_NS, 'definitionArc'),
                                           new_model.new('QName', _GEN_NS, 'arc')
                                           )
                                          )
    document = new_document(new_model, _DOCUMENT_MAP[_ARCROLE_NAMESPACE], new_model.DOCUMENT_TYPES.SCHEMA, _ARCROLE_NAMESPACE, _ARCROLE_DESCRIPTION)
    document.add(schedule_form_arcrole)

    # network = new_model.new('Network', link_name, arc_name, arcrole, elrole)
    for form, schedules in forms.items():
        for schedule in schedules:
            if schedule.type.name.clark == _NEW_FORM_TYPE:
                # This is the list of schedules where the form is a child of the list of schedules. So skip
                continue
            # Get the extended link role
            elroles = schedule_role_map.get(schedule)
            if elroles is None or len(elroles) == 0:
                continue
            elrole = sorted(elroles)[0]
            # Get or create the network
            network_key = (new_qname_from_clark(new_model, _PRESENTATION_LINK_ELEMENT),
                           new_qname_from_clark(new_model, _PRESENTATION_ARC_ELEMENT),
                           schedule_form_arcrole,
                           elrole)
            network = new_model.get('Network', *network_key)
            if network is None:
                network = new_model.new('Network', *network_key)
            # Add the relationship.
            network.add_relationship(schedule, form, 1)

def add_footnote_arcroles(old_model, new_model):
    for arcroles in old_model.arcroleTypes.values():
        document_name = '{}-core-footnote-roles_{}.xsd'.format(_CORE_NAME, _NEW_VERSION)
        document_namespace = 'http://www.ferc.gov/form/roles/footnote'
        for old_arcrole in arcroles:
            if _FOOTNOTE_ARC_NAME in [x.clarkNotation for x in old_arcrole.usedOns]:
                usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_arcrole.usedOns)
                definition = old_arcrole.definition
                new_arcrole = new_model.new('Arcrole', old_arcrole.arcroleURI, old_arcrole.cyclesAllowed, definition, usedons)
                arcrole_document = new_document(new_model, document_name, new_model.DOCUMENT_TYPES.SCHEMA, document_namespace, _FOOTNOTE_ARC_DESCRIPTION)
                arcrole_document.add(new_arcrole)

def add_form_entry_points(new_model, forms, schedule_documents):
    form_entry_documents = set() # This will save all the form entry points for the all entry point
    first_form = None
    first_name = None
    all_form_names = []
    for form, schedules in sorted(forms.items(), key=lambda x: x[0].name.local_name):
        # first form (in sorted order) is used for the 'all' entry point
        if first_form is None:
            first_form = form
        try:
            entry_point_name = list(form.labels.get((_ENTRY_POINT_PATH_LABEL_ROLE, 'en'), []))[0].content
        except IndexError:
            raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_ENTRY_POINT_PATH_LABEL_ROLE, form.name.clark))
        try:
            form_name = list(form.labels.get((_EFORMS_LABEL_ROLE, 'en'), []))[0].content
        except IndexError:
            raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_EFORMS_LABEL_ROLE, form.name.clark))

        if first_form is form:
            first_name = form_name
        all_form_names.append(form_name)

        # Create form document
        document_name = 'form/{}_{}.xsd'.format(entry_point_name, _NEW_VERSION)
        document_namespace = '{}{}/ferc-{}'.format(_NAMESPACE_START, _NEW_VERSION, form_name.lower().replace(' ', '-'))
        form_document = new_document(new_model, document_name, new_model.DOCUMENT_TYPES.SCHEMA, document_namespace)
        form_entry_documents.add(form_document)
        for schedule in schedules:
            try:
                form_document.add(schedule_documents[schedule], new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
            except KeyError:
                pass # This is a schedule in the list of schedules that isn't really schedule.

        # Create entry point
        entry_point = new_model.new('PackageEntryPoint', entry_point_name)
        entry_point.names.append((form_name, 'en'))
        try:
            entry_point.description = list(form.labels.get((_ENTRY_POINT_LABEL_ROLE, 'en'), []))[0].content
        except IndexError:
            raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_ENTRY_POINT_PATH_LABEL_ROLE, form.name.clark))
        entry_point.description_language = 'en'
        entry_point.version = _NEW_VERSION
        entry_point.documents.append(form_document)
        other_element_qname = new_model.new('QName', 'http://www.ferc.gov/form/taxonomy-package', 'entryPoint', 'tp')
        entry_point.other_elements[other_element_qname] = form_name

    # Add the all forms document and entry point
    if len(form_entry_documents) > 0:
        # Add 'all' document
        all_document_name = '{}-all_{}.xsd'.format(_CORE_NAME, _NEW_VERSION)
        all_namespace = '{}{}/{}-all'.format(_NAMESPACE_START, _NEW_VERSION, _CORE_NAME)
        all_document = new_document(new_model, all_document_name, new_model.DOCUMENT_TYPES.SCHEMA, all_namespace)
        for form_doc in sorted(form_entry_documents, key=lambda x: x.uri):
            all_document.add(form_doc, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

        # Add 'all' entry point
        all_name = '{} - All'.format(first_name)
        entry_point = new_model.new('PackageEntryPoint', 'All')
        entry_point.names.append((all_name, 'en'))
        entry_point.description = 'This entry point contains the FERC {} taxonomies'.format(', '.join(sorted(all_form_names)))
        entry_point.description_language = 'en'
        entry_point.version = _NEW_VERSION
        entry_point.documents.append(all_document)

    return form_entry_documents

def get_schedule_role(schedule_concept):
    '''Find the role that cooresponds to the schedule concept'''
    possible_roles = set()
    for rels in schedule_concept.from_concept_relationships.values():
        for rel in rels:
            if rel.arcrole == _PARENT_CHILD and rel.is_root:
                possible_roles.add(rel.role) # the 4th item inthe key is the role
    if len(possible_roles) > 1:
        # Have more than one option. Check if the abstract is used in different schedules. This is a little tricky as a schedule can have
        # more than one role (i.e. retained earnings). In this case the roles will all have the same starting URI.
        possible_roles = sorted(possible_roles)
        base_roles = {possible_roles[0],} # this should be the basic role for a set of roles
        for role in possible_roles:
            if not any([role.role_uri.startswith(x.role_uri) for x in base_roles]):
                base_roles.add(role)
        if len(base_roles) > 1: # then the schedule abstract is being used in more than one schedule
            warning('FERCSerializerWarning', 'Found multiple roles for schedule {}\nRoles are:\n{}'.format(schedule_concept.name.clark,
                                                '\n'.join([x.role_uri for x in sorted(base_roles)])))
    return possible_roles

def find_forms(new_model):
    '''Get the form concepts and the list of schedules for each form

    This method finds all the form concepts and the schedules that belong to each form. It also identifies a definitive
    page number for each schedule. This page number will be used for the file names for the schedule schemas and related
    linkbases. A schedule can be used in more than one form and so have different page numbers for each form. The page number
    associated with the alphabetically first form name is used.
    '''
    # find form concepts that are in a presentation and they are the root. This should only happen
    # in the list of schedules/Table of concepts.
    form_concepts = dict()
    schedule_map = dict()
    for concept in new_model.concepts.values():
        if concept.type.name.clark == _NEW_FORM_TYPE:
            form_concepts[concept] = set()

    for form_concept in form_concepts.keys(): # this must be keys() as if the form has no schedules, it 
                                              # will be removed from the dictionary during the iteration.
                                              # By using keys, the dictionary can change size.
        for potential_rels in form_concept.from_concept_relationships.values():
            # Get all the root rels in the presentation
            rels = [x for x in potential_rels if (x.is_root and 
                                                  x.arcrole == _PARENT_CHILD and
                                                  x.to_concept.type.name.clark == _NEW_SCHEDULE_TYPE)]
            # Check that there is only one network, this should be the list of schedules network
            networks = {x.network for x in rels}
            if len(networks) > 1:
                raise FERCSerialzierException("Found form concept {} as root in more than network. The form concept should only "
                                              "be the root in the list of schedules.".format(form_concept.name.clark))
            # Add the form_concept as a schedule for the list of schedules which has the form concept at the root
            # instead of a schedule concewpt.
            form_concepts[form_concept].add(form_concept)
            schedule_map[form_concept] = {next(iter(networks)).role,}
            for rel in next(iter(networks)).relationships:
                if rel.to_concept.type.name.clark == _NEW_SCHEDULE_TYPE:
                    schedule_roles = get_schedule_role(rel.to_concept)
                    if schedule_roles is not None: # if it is none then this element is just header but there is no real schedule
                        schedule_map[rel.to_concept] = schedule_roles
                    form_concepts[form_concept].add(rel.to_concept)

    # remove forms that are not used
    for form in list(form_concepts):
        if len(form_concepts[form]) == 0:
            del form_concepts[form]

    return form_concepts, schedule_map

def dummy(*args, **kwargs):
    pass

__pluginInfo__ = {
    'name': 'XBRL FERC Serializer',
    'version': '01.0',
    'description': "This plug-in organizes the taxonomy files and creates a Taxonomy Package for FERC taxonomies",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'serializer',
    # classes of mount points (required)
    'CntlrCmdLine.Options': dummy,
    'CntlrCmdLine.Utility.Run': dummy,
    'CntlrCmdLine.Xbrl.Run': dummy,
    'serializer.serialize': serialize,
}