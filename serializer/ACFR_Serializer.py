'''Serializer for ACFR Taxonomy'''

import collections
import re
from tkinter import E

from arelle.ModelDtsObject import ModelConcept, ModelType
from arelle.ModelValue import QName
import arelle.XbrlConst as xc
from lxml import etree

_OPTIONS = None
_OLD_MODEL = None


_NEW_FORM_TYPE = None
_NEW_SCHEDULE_TYPE =  None
_PARENT_CHILD = 'http://www.xbrl.org/2003/arcrole/parent-child'
_SUMMATION_ITEM = 'http://www.xbrl.org/2003/arcrole/summation-item'

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
_OLD_PART_NAMESPACE = ''
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
# TODO remove items above

_CORE_NAME = 'acfr'
_NAMESPACE_START = 'http://taxonomies.xbrl.us/'  # the rest of the namespace is version / taxonomy part (i.e. form1, ferc, sched-bla-bla)
_DOCUMENTATION_LABEL_ROLE = 'http://www.xbrl.org/2003/role/documentation'

_BASE_NAMESPACES = re.compile(r'^http://(www\.)?((w3)|(xbrl))\.org/')

_GRANTS_MATCH = re.compile(r"^http://.*/roles/(?P<role_name>grantsmanagement[^/]*).*$", re.IGNORECASE)
_SINGLE_AUDIT_MATCH = re.compile(r"^http://.*/roles/(?P<role_name>singleaudit[^/]*).*$", re.IGNORECASE)

_GRANTS_NAMESPACE = None
_SINGLE_AUDIT_NAMESPACE =  None
_ACFR_NAMESPACE = None
_COMBO_NAMESPACE = None

_CORE_NAMESPACES = None

_STATE_ROLES = dict() # key by new role value is state namespace
_STATE_CONCEPTS = dict() # key by concept local name, value is state namespace
_STATE_PARTS = dict() # key is by part local name, value is the state namespace

_CONCEPT_MAP = dict() # key = old model_concept, value = new concept
#_ROLE_MAP = dict() # key = old role uri, value = new role uri



# http://xbrl.us/grants
# http://xbrl.us/singleaudit
# http://xbrl.us/acfr-grants-singleaudit

_VALID_DOCUMENT_LOCATIONS = ('disclosure', 'singleaudit', 'state', 'statement', 'grants', 'document', 'meta')
_DEFINITION_ROLES_IGNORE = (
    'http://xbrl.org/int/dim/arcrole/all',	
    'http://xbrl.org/int/dim/arcrole/dimension-default',
    'http://xbrl.org/int/dim/arcrole/dimension-domain',	
    'http://xbrl.org/int/dim/arcrole/domain-member',
    'http://xbrl.org/int/dim/arcrole/hypercube-dimension',
    'http://xbrl.org/int/dim/arcrole/notAll',
    'http://xbrl.us/acfr/v0.3/2021-05-01/acfr/arcroles/entity-report',
    'http://www.xbrl.org/2021/arcrole/class-subclass',
    'http://www.xbrl.org/2021/arcrole/trait-concept'
)

_PRESENTATION_LINK_ELEMENT = '{http://www.xbrl.org/2003/linkbase}presentationLink'
_PRESENTATION_ARC_ELEMENT = '{http://www.xbrl.org/2003/linkbase}presentationArc'
_DEFINITION_LINK_ELEMENT = '{http://www.xbrl.org/2003/linkbase}definitionLink'
_DEFINITION_ARC_ELEMENT = '{http://www.xbrl.org/2003/linkbase}definitionArc'

class ACFRSerialzierException(Exception):
    pass

class FERCSerialzierException(Exception):
    # TODO Remove this class
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
        raise FERCSerialzierException(msg)

def warning(msg):
    _OLD_MODEL.warning('ACFRSerializationWarning', msg)

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

    global _NEW_SCHEDULE_ROLE_MATCH
    _NEW_SCHEDULE_ROLE_MATCH = re.compile('(.*)/roles/Schedule/([^/]+)/(.*)')
    global _DOCUMENT_MAP

    global _CORE_NAMESPACE 
    _CORE_NAMESPACE = '{}{}/{}'.format(_NAMESPACE_START, _NEW_VERSION, _CORE_NAME)  
    _DOCUMENT_MAP[_CORE_NAMESPACE] = '{}-{}_{}.xsd'.format(_CORE_NAME, 'core', _NEW_VERSION)



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

    # TODO - remove all above

    global _GRANTS_NAMESPACE
    _GRANTS_NAMESPACE = f'{_NAMESPACE_START}grants/{_NEW_VERSION}'
    global _SINGLE_AUDIT_NAMESPACE
    _SINGLE_AUDIT_NAMESPACE =  f'{_NAMESPACE_START}singleAudit/{_NEW_VERSION}'
    global _ACFR_NAMESPACE
    _ACFR_NAMESPACE = f'{_NAMESPACE_START}acfr/{_NEW_VERSION}'
    global _COMBO_NAMESPACE
    _COMBO_NAMESPACE = f'{_NAMESPACE_START}grip/{_NEW_VERSION}'
    global _CORE_NAMESPACES
    _CORE_NAMESPACES = {_GRANTS_NAMESPACE: {'taxonomy': 'grants',
                                            'name': 'Grants',
                                            'description': 'Grants Taxonomy'},
                        _SINGLE_AUDIT_NAMESPACE: {'taxonomy': 'singleaudit', 
                                                'name': 'Single Audit',
                                                'description': 'Single Audit Taxonomy'},
                        _ACFR_NAMESPACE: {'taxonomy': 'acfr',
                                        'name': 'ACFR',
                                        'description': 'ACFR Taxonomy'},
                        _COMBO_NAMESPACE: {'taxonomy': 'grip',
                                        'name': 'GRIP',
                                        'description': 'Government Reporting Information Package Taxonomy'}
    }

    for tax_namespace, info in _CORE_NAMESPACES.items():
        #TODO add version to namespaces
        tax_name = info['taxonomy']
        info['type'] = 'core',
        info['network-location'] = f'{tax_name}/'
        info['uri'] = f'{tax_name}/elts/{tax_name}_{_NEW_VERSION}.xsd'
        #info['description'] = f'{info["name"]} taxonomy'
        info['all-uri'] = f'{tax_name}/{tax_name}-all_{_NEW_VERSION}.xsd'
        info['all-namespace'] = f'{_NAMESPACE_START}{tax_name}/all/{_NEW_VERSION}'
        info['type-uri'] = f'{tax_name}/elts/{tax_name}_types_{_NEW_VERSION}.xsd'
        info['type-namespace'] = f'{_NAMESPACE_START}{tax_name}/type/{_NEW_VERSION}'
        info['type-description'] = f'This schema contains types for the {info["name"]} taxonomy'
        info['role-start-uri'] = f'{_NAMESPACE_START}{tax_name}/roles/'
        info['role-doc-uri'] = f'{tax_name}/elts/{tax_name}_roles_{_NEW_VERSION}.xsd'
        info['role-namespace'] = f'{_NAMESPACE_START}{tax_name}/roles/{_NEW_VERSION}'
        info['role-description'] = f'This schema contains roles for the {info["name"]} taxonomy'
        info['arcrole-start-uri'] = f'{tax_namespace}/arcroles/'
        info['arcrole-doc-uri'] = f'{tax_name}/elts/{tax_name}_arcroles_{_NEW_VERSION}.xsd'
        info['arcrole-namespace'] = f'{_NAMESPACE_START}{tax_name}/arcoles/{_NEW_VERSION}'
        info['arcrole-description'] = f'This schema contains arcroles for the {info["name"]} taxonomy'
        info['label-standard-uri'] = f'{tax_name}/elts/{tax_name}_lab_{_NEW_VERSION}.xml'
        info['label-doc-uri'] = f'{tax_name}/elts/{tax_name}_doc_{_NEW_VERSION}.xml'
        info['ref-uri'] = f'{tax_name}/elts/{tax_name}_ref_{_NEW_VERSION}.xml'

    # Add the state taxonomy info
    states = get_state_concepts(old_model)
    for state, (labels, refs, parts, abstracts) in states.items():
        state_namespace = f'{_NAMESPACE_START}acfr/state/{state.qname.localName}'
        tax_name = state.qname.localName
        _CORE_NAMESPACES[state_namespace] = {
            'name': tax_name,
            'type': 'state',
            'taxonomy': state.qname.localName,
            'network-location': f'acfr/state/{tax_name}',
            'uri': f'acfr/state/{tax_name}/elts/{tax_name}_{_NEW_VERSION}.xsd',
            'description': f'{tax_name} taxonomy',
            'all-uri': f'acfr/state/{tax_name}/{tax_name}-all_{_NEW_VERSION}.xsd',
            'all-namespace': f'acfr/state/{tax_name}/all/{_NEW_VERSION}',
            'type-uri': f'acfr/state/{tax_name}/elts/{tax_name}_types_{_NEW_VERSION}.xsd',
            'type-namespace': f'{_NAMESPACE_START}{tax_name}/type/{_NEW_VERSION}',
            'type-description': f'This schema contains types for the {tax_name} taxonomy',
            'role-start-uri': f'{_NAMESPACE_START}acfr/state/{state.qname.localName}/roles/',
            'role-doc-uri': f'acfr/state/{tax_name}/elts/{tax_name}_roles_{_NEW_VERSION}.xsd',
            'role-namespace': f'{_NAMESPACE_START}acfr/state/{tax_name}/roles/{_NEW_VERSION}',
            'role-description': f'This schema contains roles for the {info["name"]} taxonomy',
            'arcrole-start-uri': f'{_NAMESPACE_START}acfr/state/{state.qname.localName}/arcroles/',
            'arcrole-doc-uri': f'acfr/state/{tax_name}/elts/{tax_name}_arcroles_{_NEW_VERSION}.xsd',
            'arcrole-namespace': f'{_NAMESPACE_START}acfr/state/{tax_name}/arcoles/{_NEW_VERSION}',
            'arcrole-description': f'This schema contains arcroles for the {tax_name} taxonomy',
            'label-standard-uri': f'acfr/state/{tax_name}/elts/{tax_name}_lab_{_NEW_VERSION}.xml',
            'label-doc-uri': f'acfr/state/{tax_name}/elts/{tax_name}_doc_{_NEW_VERSION}.xml',
            'ref-uri': f'acfr/state/{tax_name}/elts/{tax_name}_ref_{_NEW_VERSION}.xml',
            'old-label-roles': [x.role for x in labels],
            'old-ref-roles': [x.role for x in refs]
        }
        # Add state roles
        for resource in tuple(labels) + tuple(refs):
            role_name = get_new_role_uri(resource.role, state_namespace, old_model).split("/")[-1]
            _STATE_ROLES[role_name] = state_namespace
        # Add state concepts
            _STATE_CONCEPTS[state.qname.localName] = state_namespace
        for state_abstract in abstracts:
            _STATE_CONCEPTS[state_abstract.qname.localName] = state_namespace
        # add state parts
        for part in parts:
            _STATE_PARTS[part.qname.localName] = state_namespace

# NS  http://taxonomies.xbrl.us/acfr/2022/stmt/netposition
# URI http://taxonomies.xbrl.us/acfr/2022/stmt/netposition/netposition_2022.xsd


# NS  http://taxonomies.xbrl.us/acfr/2022
# URI http://taxonomies.xbrl.us/acfr/2022/elts/acfr_2022.xsd

# NS  http://taxonomies.xbrl.us/acfr/2022/acfr-all
# URI http://taxonomies.xbrl.us/acfr/2022/acfr-all_2022.xsd

# NS  http://taxonomies.xbrl.us/acfr/2022/roles/name of role
# URI http://taxonomies.xbrl.us/acfr/2022/elts/acfr-roles_2022.xsd

def get_state_concepts(old_model):
    states = dict()
    meta_gov_network = get_single_network('GovernmentOrganization', old_model)
    if meta_gov_network is None:
        warning('Cannot find the Government Activity network. Cannot not determine states')
        return states
    # The root is the government entities abstract. The children are the states
    if len(meta_gov_network.rootConcepts) != 1:
        warning('There is more than one root in the Meta Government Activies network')
        return states
    
    for state in meta_gov_network.fromModelObject(meta_gov_network.rootConcepts[0]):
        labels = get_labels(state.toModelObject)
        if 'DocumentLocation' not in labels:
            warning(f'State concept {state.name.clarkNotation} does not have document location label of "State"')
        empty_labels = [x for x in labels.values() if x.text is None]
        refs, parts = get_references(state.toModelObject)

        # get the abstracts in the entity-report. These elements will be defined in the state xsd
        entity_report_network = get_single_network('entity-report', old_model)
        if entity_report_network is None:
            warning(f'Cannot find entity-report relationships for state {state.toModelObject.qname.localName}')
            state_abstracts = []
        else:
            state_abstracts = [x.toModelObject for x in entity_report_network.fromModelObject(state.toModelObject)]
        states[state.toModelObject] = (empty_labels, refs, parts, state_abstracts)

    return states

def get_single_network(end_name, old_model):

   for arcrole, ELR, linkqname, arcqname in old_model.baseSets.keys():
        if ELR and linkqname and arcqname and arcrole and not arcrole.startswith("XBRL-"):
            if arcrole == _PARENT_CHILD and ELR.endswith(end_name):
                return old_model.relationshipSet(arcrole, ELR, linkqname, arcqname)

def get_labels(old_concept):
    labels = dict()
    old_model = old_concept.modelXbrl
    label_network = old_model.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-label')
    for label_rel in label_network.fromModelObject(old_concept):
        labels[label_rel.toModelObject.role.split("/")[-1]] = label_rel.toModelObject
    return labels

def get_references(old_concept):
    refs = set()
    parts = set()
    old_model = old_concept.modelXbrl
    ref_network = old_model.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-reference')
    for ref_rel in ref_network.fromModelObject(old_concept):
        refs.add(ref_rel.toModelObject)
        for part in ref_rel.toModelObject:
            parts.add(part)

    return refs, parts

def add_package_defaults(new_model):

    new_model.identifier = f'{_NAMESPACE_START}/taxonomy/acfr/{_NEW_VERSION}'
    new_model.name = 'ACFR Taxonomy'
    new_model.name_language = 'en-US'
    new_model.description = 'This taxonomy packacge contains the taxonomies used government reporting'
    new_model.description_language = 'en-US'
    new_model.version = _NEW_VERSION
    # TODO add license and publisher
    #new_model.license_href = 'https: LICENSE LOCATION GOES HERE'
    new_model.license_name = 'Taxonomies Terms and Conditions'
    #new_model.publisher = 'PUBLISHER'
    #new_model.publisher_url = 'https: PUBLISHER URL'
    new_model.publisher_country = 'US'
    # TODO where to get pubication date
    #new_model.publication_date = f'{_NEW_VERSION}-01-01'
    # TODO offical lcoations
    new_model.rewrites['../'] = f'{_NAMESPACE_START}'

def organize_taxonomy(model_xbrl, new_model, options):
    global _OPTIONS
    _OPTIONS = options


    concept_map = organize_networks(model_xbrl, new_model)
    # get all relationships
    # for arcrole, ELR, linkqname, arcqname in model_xbrl.baseSets.keys():
    #     if ELR and linkqname and arcqname and arcrole and not arcrole.startswith("XBRL-"):
    #         # This is an individual base set
    #         #relationship_set = model_xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname)
    #         #map['rels'][(arcrole, ELR, linkqname, arcqname)]['relationship-set'] = relationship_set
    #         organize_networks(model _xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname), new_model)

    #Build cubes from presentation
    organize_cubes(new_model)
    # Create entity-report relationships
    add_defintion_from_presentation(new_model, 'entity-report', 'entity-report', 'Entity Report')
    add_defintion_from_presentation(new_model, 'GovernmentActivity', 'domain-member')
    # fill in the package meta data information
    add_package_defaults(new_model)
    # Build entry points for forms and ferc-all
    add_entry_points(new_model)

    assign_network_documents(new_model)
    # Add states to acfr
    add_states_to_acfr(new_model)



    # TODO create entity-report relationships in the definition


    return new_model

    
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

    # Add the default table
    create_default_table(new_model, schedule_role_map)


    return new_model

def organize_networks(old_model, new_model):
    
    concept_map = dict() # key is old qname, value is new concept
    old_presentations = {'grants': list(), 'singleaudit': list(), 'acfr': list()}
    old_calculations = []
    old_definitions = []
    # get all relationships
    for arcrole, ELR, linkqname, arcqname in old_model.baseSets.keys():
        if ELR and linkqname and arcqname and arcrole and not arcrole.startswith("XBRL-"):
            relationship_set = old_model.relationshipSet(arcrole, ELR, linkqname, arcqname)
        else:
            continue

        # only include concept to concept networks
        if not is_concept_to_concept_network(relationship_set):
            continue

        # Skip dimensional relatonships. These will be recreated based on the presentation.

        if (# presentation
            relationship_set.linkqname.localName == 'presentationLink' and
            relationship_set.linkqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcqname.localName == 'presentationArc' and
            relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcrole == _PARENT_CHILD):
            # determine if this is grants, single audit or acfr (which is the default)
            if _GRANTS_MATCH.match(relationship_set.linkrole):
                old_presentations['grants'].append(relationship_set)
            elif _SINGLE_AUDIT_MATCH.match(relationship_set.linkrole):
                old_presentations['singleaudit'].append(relationship_set)
            else:
                old_presentations['acfr'].append(relationship_set)

        if (# calculation
            relationship_set.linkqname.localName == 'calculationLink' and
            relationship_set.linkqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcqname.localName == 'calculationArc' and
            relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcrole == _SUMMATION_ITEM):
            old_calculations.append(relationship_set)

        if (# definition
            relationship_set.linkqname.localName == 'definitionLink' and
            relationship_set.linkqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcqname.localName == 'definitionArc' and
            relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
            relationship_set.arcrole not in _DEFINITION_ROLES_IGNORE):
            old_definitions.append(relationship_set)
    # Order is important in the list of relationship sets. This will determine which schema file the concept will end up in.
    # If a concept is in a "grants" presentation it will be in the grants. If not "grants", then if it is in "single audit" it will
    # be in the single audit schema and if not, then it is acfr.
    for old_relationship_sets in (old_presentations['grants'],
                                  old_presentations['singleaudit'],
                                  old_presentations['acfr'],
                                  old_calculations,
                                  old_definitions
                                  ):
        for relationship_set in old_relationship_sets:
            if relationship_set.linkqname.localName == 'calculationLink':
                if not all_in_presentation(relationship_set, new_model):
                    #pass
                    continue # skip if the calculation includes concepts that are not in the presentation
                else: 
                    x = 0
            # Determine which taxonomy the concepts will be in
            if _GRANTS_MATCH.match(relationship_set.linkrole):
                taxonomy_ns = _GRANTS_NAMESPACE
            elif _SINGLE_AUDIT_MATCH.match(relationship_set.linkrole):
                taxonomy_ns = _SINGLE_AUDIT_NAMESPACE
            else:
                taxonomy_ns = _ACFR_NAMESPACE


            # Create the new network
            link_name = new_qname(new_model, relationship_set.linkqname)
            arc_name = new_qname(new_model, relationship_set.arcqname)
            # Get or create the arcrole
            arcrole=(new_model.get('Arcrole', get_new_arcrole_uri(relationship_set.arcrole, taxonomy_ns, old_model)) or
                     new_arcrole(new_model, relationship_set.modelXbrl, relationship_set.arcrole, taxonomy_ns))
            elrole = (new_model.get('Role', get_new_role_uri(relationship_set.linkrole, taxonomy_ns, old_model)) or
                    new_role(new_model, relationship_set.modelXbrl, relationship_set.linkrole, taxonomy_ns))
            network = new_model.new('Network', link_name, arc_name, arcrole, elrole)

            # Add the relationships and also create the concepts
            for relationship in sorted(relationship_set.modelRelationships, key=lambda x: x.order or 1):
                # Make sure the concepts of the relationship are created
                from_concept = new_concept(new_model, 
                                        relationship.fromModelObject, 
                                        determine_taxonomy_for_existing_concept(new_model, relationship.fromModelObject.qname, concept_map) or taxonomy_ns)
                concept_map[relationship.fromModelObject.qname] = from_concept
                to_concept = new_concept(new_model, 
                                        relationship.toModelObject, 
                                        determine_taxonomy_for_existing_concept(new_model, relationship.toModelObject.qname, concept_map) or taxonomy_ns)
                concept_map[relationship.toModelObject.qname] = to_concept
                rel_atts = {new_qname_from_clark(new_model, k): v
                            for k, v in relationship.arcElement.attrib.items()
                            if not k.startswith('{http://www.w3.org/1999/xlink}')
                            and not k in ('order', 'weight', 'preferredLabel')}
                if relationship.preferredLabel is None:
                    preferred_label = None
                else:
                    preferred_label = new_label_role(new_model, relationship.modelXbrl, relationship.preferredLabel)
                network.add_relationship(from_concept, to_concept, 'calc', relationship.weight, preferred_label, rel_atts)

    return concept_map

def determine_taxonomy_for_existing_concept(new_model, old_qname, concept_map):

    # TODO - move state concepts to state

    return concept_map.get(old_qname).name.namespace if concept_map.get(old_qname) is not None else None

    if new_model.get('Concept', new_model.new('QName', _GRANTS_NAMESPACE, local_name)):
        return _GRANTS_NAMESPACE
    elif new_model.get('Concept', new_model.new('QName', _SINGLE_AUDIT_NAMESPACE, local_name)):
        return _SINGLE_AUDIT_NAMESPACE
    elif new_model.get('Concept', new_model.new('QName', _ACFR_NAMESPACE, local_name)):
        return _ACFR_NAMESPACE
    else:
        return None

def is_concept_to_concept_network(relationship_set):
    for rel in relationship_set.modelRelationships:
        if not is_concept_to_concept_relationship(rel):
            return False
    return True

def is_concept_to_concept_relationship(relationship):
    return isinstance(relationship.fromModelObject, ModelConcept) and isinstance(relationship.toModelObject, ModelConcept)

def all_in_presentation(relationship_set, new_model):

    bad_concepts = set()
    for rel in relationship_set.modelRelationships:
        for old_concept in [rel.fromModelObject, rel.toModelObject]:
            if _CONCEPT_MAP.get(old_concept) is None or  not _CONCEPT_MAP.get(old_concept) not in new_model.concepts:
                bad_concepts.add(old_concept.qname.clarkNotation)

    for name in bad_concepts:
        warning(f'Concept {name} is in a calculation {relationship_set.linkrole} but is not in a presentation')
    
    return len(bad_concepts) == 0


def new_qname(new_model, model_qname, namespace=None):

    return new_model.new('QName', namespace or model_qname.namespaceURI, model_qname.localName)

def new_concept(new_model, model_concept, namespace=None):

    # override the namespace for state concepts
    namespace = _STATE_CONCEPTS.get(model_concept.qname.localName, namespace)

    concept_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_concept, True, namespace)

    if new_model.get('Concept', concept_name) is not None:
        # The concept is already in the model
        return new_model.get('Concept', concept_name)

    period_type = model_concept.periodType
    balance_type = model_concept.balance

    if model_concept.isTypedDimension:
        typed_domain_name = new_qname(new_model, model_concept.typedDomainElement.qname, namespace)
        typed_domain = new_model.get('TypedDomain', typed_domain_name) or new_typed_domain(new_model, model_concept.typedDomainElement, namespace) 
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
    if concept_name.namespace in _CORE_NAMESPACES:
        # TODO add descriptions to the core documents
        document = new_document(new_model, _CORE_NAMESPACES[concept_name.namespace]['uri'], new_model.DOCUMENT_TYPES.SCHEMA, concept_name.namespace, '')
    else:
        document = new_document(new_model, model_concept.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_concept.modelDocument.targetNamespace)

    document.add(concept)

    # add concept to concept map
    _CONCEPT_MAP[model_concept] = concept

    organize_labels_for_concept(concept, model_concept)
    organize_references_for_concept(concept, model_concept)

    return concept

def get_element_info(new_model, model_element, is_concept=False, namespace=None):

    name = new_qname(new_model, model_element.qname, namespace)

    new_type_qname = fix_type_qname(new_model, model_element.typeQname, namespace)
    # determine if this is a type that is defined in this taxonomy or an external data type (i.e. DTR)
    data_type = (new_model.get('Type', new_type_qname) or 
                    new_type(new_model, model_element.type if model_element.type is not None else model_element.typeQname, 
                             new_type_qname, 
                             namespace))
    if model_element.substitutionGroup is None:
        substitution_group = None
    else:
        if model_element.substitutionGroupQname.clarkNotation in (_ITEM, _TUPLE):
            substitution_group = new_qname(new_model, model_element.substitutionGroupQname)
        else:
            # Determine if the element of the substitution group is defined in the acfr taxonomy or is
            # an xbrl base concept (i.e. stringItemType)
            if _BASE_NAMESPACES.match(model_element.substitutionGroupQname.namespaceURI) is None:
                # This is a derrived substitution group
                sub_group_namespace = namespace
            else:
                sub_group_namespace = model_element.substitutionGroupQname.namespaceURI

            sub_group_qname = new_qname(new_model, model_element.substitutionGroupQname, sub_group_namespace)
            if is_concept:
                substitution_group = (new_model.get('Concept', sub_group_qname) or
                                    new_concept(new_model, model_element.substitutionGroup, sub_group_namespace))
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

def fix_type_qname(new_model, old_qname, element_namespace=None):

    if _BASE_NAMESPACES.match(old_qname.namespaceURI) is None:
        if element_namespace is None:
            raise ACFRSerialzierException(f"Don't know where to put this type: {old_qname.namespaceURI}:{old_qname.localName}")
        try:
            type_namespace = _CORE_NAMESPACES[element_namespace]['type-namespace']
        except:
            x = 0

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

def new_typed_domain(new_model, model_element, namespace=None):
    name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element, False, namespace)
    typed_domain = new_model.get('TypedDomain', name) or new_model.new('TypedDomain', name, data_type, abstract, nillable, id, substitution_group, attributes)

    # Assign document
    if typed_domain.name.namespace in _CORE_NAMESPACES:
        document = new_document(new_model, 
                                _CORE_NAMESPACES[typed_domain.name.namespace]['uri'], 
                                new_model.DOCUMENT_TYPES.SCHEMA, 
                                typed_domain.name.namespace,
                                _CORE_NAMESPACES[typed_domain.name.namespace]['description'])
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(typed_domain)
    return typed_domain

def new_type(new_model, model_type, new_type_qname, element_namespace=None):
    # model_type may be an arelle ModelType or a qname. If it is a qname it is a base xbrl type
    if new_model.get('Type', new_type_qname) is not None:
        return new_model.get('Type', new_type_qname)

    if isinstance(model_type, QName):
        # This is base XML type.
        type_parent = None
        type_content = None
    else:
        if model_type.typeDerivedFrom is not None:
            type_parent_qname = fix_type_qname(new_model, model_type.typeDerivedFrom.qname, element_namespace)
            type_parent = new_model.get('Type', type_parent_qname) or new_type(new_model, model_type.typeDerivedFrom, type_parent_qname, element_namespace)
        else:
            type_parent = None

        type_content = etree.tostring(model_type)

    new_data_type = new_model.new('Type', new_type_qname, type_parent, type_content)

    if not new_data_type.is_base_xml: # otherwise this is a base xml type and there is no document
        if new_data_type.name.namespace in (x['type-namespace'] for x in _CORE_NAMESPACES.values()):
            type_document = new_document(new_model, 
                                         _CORE_NAMESPACES[element_namespace]['type-uri'], 
                                         new_model.DOCUMENT_TYPES.SCHEMA, 
                                         new_data_type.name.namespace, 
                                         _CORE_NAMESPACES[element_namespace]['type-description'])
        else:
            if isinstance(model_type, ModelType) and model_type.qname.localName.endswith('@anonymousType'):
                type_document = None
            else: # probably in the DTR (Data Type Registry) or some other referenced type from an external taxonomy
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
        document = new_document(new_model, _CORE_NAMESPACES[new_element.name.namespace]['uri'], new_model.DOCUMENT_TYPES.SCHEMA, _TYPE_NAMESPACE, _TYPE_DESCRIPTION)
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(new_element)

    return new_element

def new_part_element(new_model, model_element, tax_namespace):

    # if _BASE_NAMESPACES.match(model_element.qname.namespaceURI) is not None:
    #     tax_namespace = None
    # else:
    tax_namespace = _STATE_PARTS.get(model_element.qname.localName, tax_namespace)

    element_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element, False, tax_namespace)
    
    new_part_element =  new_model.get('PartElement', element_name) or \
                        new_model.new('PartElement',
                          element_name,
                          data_type,
                          abstract,
                          nillable,
                          id,
                          substitution_group,
                          attributes)
    
    # Assign document
    if new_part_element.name.namespace in _CORE_NAMESPACES:
        document = new_document(new_model, _CORE_NAMESPACES[tax_namespace]['uri'], new_model.DOCUMENT_TYPES.SCHEMA, tax_namespace, _CORE_NAMESPACES[tax_namespace]['description'])
    else:
        document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

    document.add(new_part_element)

    return new_part_element

def get_new_arcrole_uri(uri, tax_namespace, old_model):
    
    if xc.isStandardArcrole(uri):
        return uri
    else:
        old_arcroles = old_model.arcroleTypes.get(uri)
        if old_arcroles is None or len(old_arcroles) == 0:
            arcrole_name = uri.split("/")[-1]
        else:
            old_arcrole = old_arcroles[0]
            used_ons = (x.clarkNotation for x in old_arcrole.usedOns)
            arcrole_name = uri.split("/")[-1]

        return f"{_CORE_NAMESPACES[tax_namespace]['role-start-uri']}{arcrole_name}" #TODO should _NEW_VERSION GO ON THE END

def new_arcrole(new_model, model_xbrl, arcrole_uri, tax_namespace):

    if xc.isStandardArcrole(arcrole_uri):
        new_arcrole_uri = arcrole_uri
    else: 
        new_arcrole_uri = get_new_arcrole_uri(arcrole_uri, tax_namespace, model_xbrl)

    # Check if it already exists
    if new_model.get('Arcole', new_arcrole_uri):
        return new_model.get('Arcrole', new_arcrole_uri)

    '''convert an arelle role to a sxm role'''
    old_arcrole = model_xbrl.arcroleTypes[arcrole_uri]
    if len(old_arcrole) == 0:
        if xc.isStandardArcrole(arcrole_uri):
            usedons = tuple()
            definition = None
            cycles_allowed = xc.standardArcroleCyclesAllowed[arcrole_uri][0] # this is the cycles allowed value
        else:
            error('ACFRSerializerError', 'arcrole {} not found in source DTS'.format(arcrole_uri))
    else:
        usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_arcrole[0].usedOns)
        definition = old_arcrole[0].definition
        cycles_allowed = old_arcrole[0].cyclesAllowed

    # The documents for the role definitions will be assigned later
    arcrole =  new_model.new('Arcrole', new_arcrole_uri, cycles_allowed, definition, usedons)

    assign_arcrole_document(arcrole, tax_namespace)

    return arcrole

def get_new_role_uri(uri, tax_namespace, old_model):
    
    if uri in xc.standardRoles:
        return uri
    else:
        old_roles = old_model.roleTypes.get(uri)
        if old_roles is None or len(old_roles) == 0:
            role_name = uri.split("/")[-1]
        else:
            old_role = old_roles[0]
            used_ons = tuple(x.clarkNotation for x in old_role.usedOns)
            # if '{http://www.xbrl.org/2003/linkbase}label' in used_ons or '{http://www.xbrl.org/2003/linkbase}reference' in used_ons:
            #     # for label and reference roles the role name is composed from the descripton
            #     role_name = re.sub(r'\W+', '', old_role.definition) # this eliminates all non alpha or numeric characters
            # else:
            #     role_name = uri.split("/")[-1]
            role_name = uri.split("/")[-1]

        # Get the last part of the old role uri
        # if the role is for a state, the namespace needs to be the state namespace
        tax_namespace = _STATE_ROLES.get(role_name, tax_namespace)
        return f"{_CORE_NAMESPACES[tax_namespace]['role-start-uri']}{role_name}" #TODO should _NEW_VERSION GO ON THE END

def new_role(new_model, model_xbrl, role_uri, tax_namespace):

    if role_uri in xc.standardRoles:
        new_role_uri = role_uri
    else: 
        new_role_uri = get_new_role_uri(role_uri, tax_namespace, model_xbrl)

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
    role =  new_model.new('Role', new_role_uri, definition, set(usedons))

    assign_role_document(role, tax_namespace)

    return role

#def organize_labels_for_concept(new_concept, new_model, concept_map):

def organize_labels_for_concept(new_concept, old_concept):
    '''Get the labels for the concepts that are in the new model'''

    new_model = new_concept.dts
    label_network = old_concept.modelXbrl.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-label')
    for label_rel in label_network.fromModelObject(old_concept):
        # need the core document to add imports for label roles and the label linkbase
        core_document = new_concept.document
        if core_document is None:
            raise ACFRSerialzierException("Cannot find the core xsd while adding labels")
        
        old_label = label_rel.toModelObject
        label_role = new_label_role(new_model, old_concept.modelXbrl, old_label.role)

        fix = lambda x: x.strip() if label_role == _STANDARD_LABEL else x
        new_label = new_concept.add_label(label_role, 'en-US', fix(old_label.textValue))
        if label_role == _DOCUMENTATION_LABEL_ROLE:
            label_document_name = _CORE_NAMESPACES[new_concept.name.namespace]['label-doc-uri']
        else:
            label_document_name = _CORE_NAMESPACES[new_concept.name.namespace]['label-standard-uri']
        label_document = new_document(new_model, label_document_name, new_model.DOCUMENT_TYPES.LINKBASE)
        label_document.add(new_label)
        # add the label document as an import to the core file
        core_document.add(label_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)

def new_label_role(new_model, old_model, old_role):
    #core_document = new_model.documents.get(_CORE_NAMESPACES[_COMBO_NAMESPACE]['uri'])
    label_role = new_model.get('Role', get_new_role_uri(old_role, _COMBO_NAMESPACE, old_model)) 
    if label_role is None:
        label_role = new_role(new_model, old_model, old_role, _COMBO_NAMESPACE)
        assign_role_document(label_role, _COMBO_NAMESPACE)
        # add import to core file
        # if label_role.document is not None: # if its none it is a core xbrl role
        #     core_document = new_document(new_model, 
        #                         _CORE_NAMESPACES[_COMBO_NAMESPACE]['uri'], 
        #                         new_model.DOCUMENT_TYPES.SCHEMA, 
        #                         _COMBO_NAMESPACE, 
        #                         _CORE_NAMESPACES[_COMBO_NAMESPACE]['description'])
        #     core_document.add(label_role.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

    return label_role

def organize_references_for_concept(new_concept, old_concept):
    '''Get the references for the concepts that are in the new model'''
    new_model = new_concept.dts
    old_model = old_concept.modelXbrl

    ref_network = old_model.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-reference')
    for ref_rel in ref_network.fromModelObject(old_concept):
         # need the core document to add imports for reference roles, part elements and the reference linkbases
        core_document = new_concept.document
        if core_document is None:
            raise ACFRSerialzierException("Cannot find the core xsd while adding references")

        old_ref = ref_rel.toModelObject
        ref_role = new_model.get('Role', get_new_role_uri(old_ref.role, _COMBO_NAMESPACE, old_concept.modelXbrl)) 
        if ref_role is None:
            ref_role = new_role(new_model, old_ref.modelXbrl, old_ref.role, _COMBO_NAMESPACE)
        # find the core taxonomy for the reference. If this is a state reference, then the ref core is
        # is the state schema.
        role_name = ref_role.role_uri.split("/")[-1]
        ref_core_namespace = _STATE_ROLES.get(role_name, new_concept.name.namespace)
        # Get the parts
        new_parts = []
        for old_part in old_ref:
            part_name = new_qname(new_model, old_part.qname)
            part_element = new_model.get('PartElement', part_name)
            if part_element is None:
                old_part_element = old_model.qnameConcepts.get(old_part.qname)
                if old_part_element is None:
                    raise ACFRSerialzierException("Cannot find refernce part element definition for {}".format(old_part.qname.clarkNotation))
                part_element = new_part_element(new_model, old_part_element, _COMBO_NAMESPACE)
            new_parts.append(new_model.new('Part', part_element, old_part.textValue))
            # add import to core file
            core_document.add(part_element.document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

        new_ref = new_concept.add_reference(ref_role, new_parts)

        ref_document_name = _CORE_NAMESPACES[ref_core_namespace]['ref-uri']
        ref_document = new_document(new_model, ref_document_name, new_model.DOCUMENT_TYPES.LINKBASE)
        ref_document.add(new_ref)
        # add the ref linkbase as a linkbase ref in the core
        core_document.add(ref_document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)

def assign_role_document(role, tax_namespace):

    tax_namespace = _STATE_ROLES.get(role.role_uri.split("/")[-1], tax_namespace)
    if not role.is_standard and role.document is None:
        role_document = new_document(role.dts, 
                                     _CORE_NAMESPACES[tax_namespace]['role-doc-uri'], 
                                     role.dts.DOCUMENT_TYPES.SCHEMA, 
                                     _CORE_NAMESPACES[tax_namespace]['role-namespace'],
                                     _CORE_NAMESPACES[tax_namespace]['role-description'])
        role_document.add(role)

def assign_arcrole_document(arcrole, tax_namespace):

    if not arcrole.is_standard and arcrole.document is None:
        arcrole_document = new_document(arcrole.dts, 
                                     _CORE_NAMESPACES[tax_namespace]['arcrole-doc-uri'], 
                                     arcrole.dts.DOCUMENT_TYPES.SCHEMA, 
                                     _CORE_NAMESPACES[tax_namespace]['arcrole-namespace'],
                                     _CORE_NAMESPACES[tax_namespace]['arcrole-description'])
        arcrole_document.add(arcrole)

def add_defintion_from_presentation(new_model, old_role_name, arcrole_name, arcrole_description=None):

    pres_role = find_role(old_role_name, 'role', new_model)
    if pres_role is None:
        warning(f'Cannot create entity-report relationships becasue cannot find presentation role that ends with "{old_role_name}"')
        return
    pres_networks = new_model.get_match('Network', (new_qname_from_clark(new_model, _PRESENTATION_LINK_ELEMENT), None, None, pres_role.role_uri))
    if len(pres_networks) != 1:
        warning(f'Expected only 1 presentation network for {old_role_name} but found {len(pres_networks)}')
        return
    pres_network = pres_networks[0]

    # Create the new network
    link_name = new_qname_from_clark(new_model, _DEFINITION_LINK_ELEMENT)
    arc_name = new_qname_from_clark(new_model, _DEFINITION_ARC_ELEMENT)
    # make sure definition link is in the used on for the link role
    if link_name not in pres_role.used_ons:
        pres_role.used_ons.add(link_name)
    # Get or create the arcrole
    # See if there is already an arcrole
    arcrole = find_role(arcrole_name, 'arcrole', new_model)
    if arcrole is None:
        if arcrole_name == 'domain-member':
            usedon = (new_model.new('QName', 'http://www.xbrl.org/2003/linkbase', 'defintionArc', 'link'))
            arcrole = new_model.new('Arcrole', 'http://xbrl.org/int/dim/arcrole/domain-member', 'undirected', 'Source (a domain) contains the target (a member).', usedon)
            dimension_document = new_model.get('Document', 'http://www.xbrl.org/2005/xbrldt-2005.xsd') or \
                                new_model.new('Document', 'http://www.xbrl.org/2005/xbrldt-2005.xsd', new_model.DOCUMENT_TYPES.SCHEMA, 'http://xbrl.org/2005/xbrldt')                    
            arcrole.document = dimension_document
        else:
            arcrole_uri = f"{_CORE_NAMESPACES[_ACFR_NAMESPACE]['role-start-uri']}{arcrole_name}" #TODO should _NEW_VERSION GO ON THE END
            arcrole = new_model.new('Arcrole', arcrole_uri, 'undirected', arcrole_description, {arc_name,})
    else:
        if link_name not in arcrole.used_ons:
            arcrole.used_ons.add(link_name)
    elrole = pres_role 
    network = new_model.new('Network', link_name, arc_name, arcrole, elrole)

    for pres_rel in pres_network.relationships:
        network.add_relationship(pres_rel.from_concept, pres_rel.to_concept, pres_rel.order, pres_rel.weight, None, pres_rel.attributes)

def find_role(role_name, role_type, new_model):
    roles = new_model.roles if role_type == 'role' else new_model.arcroles
    found_roles = [x for x in roles.keys() if x.endswith(f'/{role_name}')]
    if len(found_roles) != 1:
        return None
    else:
        return roles[found_roles[0]]

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
                    raise ACFRSerialzierException("Dimension {} has more than one domain. Only 1 is allowed".foramt(dimension.name.clark,
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
                else: # There is no domain
                    if not dimension_node.is_typed:
                        has_members = len(find_dim_parts(network, 'MEMBER', dimension)) > 0
                        if has_members:
                            warning(f'Axis {dimension_node.concept.name.clark} has no domains but has members')
                        else:
                            warning(f'Axis {dimension_node.concept.name.clark} has no domains')
            
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

def create_default_table(new_model, schedule_role_map):
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
                for descendant in network.get_descendants(child_rel.to_concept):
                    if descendant.to_concept.type.is_nuemric:
                        typed_total_concepts.add(descendant.to_concept)
        
        if len(typed_total_concepts) > 0: # This indicates a total table needs to be created
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
            new_role = cube.role.copy(role_uri=new_role_uri, description='{} - Totals'.format(cube.role.description))
            # Create the new cube
            new_cube = cube.copy(role=new_role)
            for dimension in cube.dimensions:
                if dimension.is_explicit and dimension.default is not None:
                    # Copy this defaulted dimension to the total table
                    new_dimension = dimension.copy(deep=True, role=new_role)
                    new_cube.add_dimension_node(new_dimension)
            if len(cube.primary_items) == 0:
                raise FERCSerialzierException("There are no primary items for table concept {}".format(cube.concept.name.clark))
            new_primary = cube.primary_items[0].copy(role=new_role)
            new_cube.add_primary_node(new_primary)
            # create the new presentation network
            new_network = network.copy(role=new_role)
            presentation_document = parent_rels[0].document
            new_network.add_relationship(parent_rels[0].from_concept, new_cube.concept)
            presentation_document.add(new_network.add_relationship(parent_rels[0].from_concept, new_cube.concept))
            presentation_document.add(new_network.add_relationship(new_cube.concept, new_primary.concept))

            for concept in typed_total_concepts:
                # add to the cube
                new_member = new_primary.add_child(concept.get_class('Member'), concept)
                new_member.document = new_primary.document
                # add to the presentation network
                new_rel = new_network.add_relationship(new_primary.concept, concept)
                presentation_document.add(new_rel)

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

def assign_network_documents(new_model):

    grouped_by_root = group_network_roles(new_model)

    for network in new_model.networks.values():

        root = grouped_by_root[network.role.role_uri]['root']
        role_name = grouped_by_root[network.role.role_uri]['role-name']
        document_name = "{start}/{doc_type}/{doc}_{link_type}_{version}.xml".format(
                                                             start=_CORE_NAMESPACES[root.name.namespace]['network-location'],
                                                             doc_type=role_document_type(root).lower(),
                                                             doc=role_name,
                                                             link_type=network.link_name.local_name[:3],
                                                             version=_NEW_VERSION)

        document = new_document(new_model, document_name, new_model.DOCUMENT_TYPES.LINKBASE)
        schema_document = new_model.documents[_CORE_NAMESPACES[root.name.namespace]['all-uri']]
        schema_document.add(document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)
        for rel in network.relationships:
            document.add(rel)

        # make sure role is assigned a document
        if not network.arcrole.is_standard and network.arcrole.document is None:
            arcrole_document = new_document(new_model, 
                                            _CORE_NAMESPACES[root.name.namespace]['arcrole-doc-uri'], 
                                            new_model.DOCUMENT_TYPES.SCHEMA, 
                                            _CORE_NAMESPACES[root.name.namespace]['arcrole-namespace'],
                                            _CORE_NAMESPACES[root.name.namespace]['arcrole-description'])
            arcrole_document.add(network.arcrole) 

    for cube in new_model.cubes.values():
        cube_tops = cube.primary_items + cube.dimensions 
        pres_root = grouped_by_root[network.role.role_uri]['root']
        if len(cube_tops) != 0:
            role_name = grouped_by_root[cube.role.role_uri]['role-name']
            document_name = "{start}/{doc_type}/{doc}_{link_type}_{version}.xml".format(
                                start=_CORE_NAMESPACES[cube.concept.name.namespace]['network-location'],
                                doc_type=role_document_type(pres_root).lower(),
                                doc=role_name,
                                link_type='def',
                                version=_NEW_VERSION)
            document = new_document(new_model, document_name, new_model.DOCUMENT_TYPES.LINKBASE)
            document.add(cube)
            for cube_top in cube_tops:
                document.add(cube_top) # This is either a primary or dimension
                for cube_node in cube_top.all_descendants:
                    document.add(cube_node)
            # Add the linkbase ref to the schema document
            schema_document = new_model.documents[_CORE_NAMESPACES[cube.concept.name.namespace]['all-uri']]
            schema_document.add(document, new_model.DOCUMENT_CONTENT_TYPES.LINKBASE_REF)


def group_network_roles(new_model):

    grouped_calcs = dict() # this is keyed by role uri and the value will be the primary role
    grouped_by_root = dict()

    # Organize the presentation networks by the root abstract
    for network in new_model.networks.values():
        if network.link_name.local_name == 'presentationLink':
            if len(network.roots) != 1:
                warning(f'{network.link_name.local_name} Network {network.role.description} has {len(network.roots)}. It can only have 1')
            else:
                root_name = remove_abstract(network.roots[0].name.local_name)
                grouped_by_root[network.role.role_uri] = {'root': network.roots[0], 'role-name': root_name}

    # organize the calcs by primary role.
    sorted_networks = sorted(new_model.networks.values(), key=lambda x: x.role.role_uri)
    primary_role_uri = None
    for network in sorted_networks:
        if network.link_name.local_name == 'calculationLink':
            if primary_role_uri is None or not network.role.role_uri.startswith(primary_role_uri):
                primary_role_uri = network.role.role_uri
            if network.role.role_uri not in grouped_by_root:
                grouped_calcs[network.role.role_uri] = primary_role_uri

    for role_uri, primary_role_uri in grouped_calcs.items():
        if primary_role_uri not in grouped_by_root:
            warning('xxx', f'Primary role for calc is not in the presentation: {primary_role_uri}')
        grouped_by_root[role_uri] = grouped_by_root[primary_role_uri]

        # if network.link_name.local_name == 'presentationLink':
        #     if len(network.roots) != 1:
        #             warning('ACFRSerializationException', f'{network.link_name.local_name} Network {network.role.description} has {len(network.roots)}. It can only have 1')
        #     else:
        #         root = network.roots[0]
        #         root_name = remove_abstract(root.name.local_name.lower())
        #         if root.name.namespace == _GRANTS_NAMESPACE:    
        #             root_tax = 'grants'
        #         elif root.name.namespace == _SINGLE_AUDIT_NAMESPACE:
        #             root_tax = 'singleaudit'
        #         else:
        #             root_tax = 'acfr'

        #         grouped_by_root[network.link_name.local_name[:3]][network.role.role_uri] = {'root-name': root_name, 
        #                                                 'tax': root_tax, 
        #                                                 'root-namespace': root.name.namespace}

    return grouped_by_root

def remove_abstract(name):
    if name.lower().endswith('abstract'):
        return name[:-8]
    else:
        return name

def role_document_type(concept):
    
    # this is in the documentLocation label
    for label_key in concept.labels: # the key is a tuple of role uri and language
        if label_key[0].role_uri.lower().endswith('documentlocation'): # This is the label_role_uri
            if len(concept.labels[label_key]) > 0:
                document_location = list(concept.labels[label_key])[0].content
                if document_location.lower() not in _VALID_DOCUMENT_LOCATIONS:
                    warning(f'Unexpected document location for concept {concept.name.clark} location is {document_location}')
                if document_location.lower() == 'state': # find the state in the entity-report relationship
                    pass
                return document_location
    # the document location was not found
    warning(f'Document location for {concept.name.clark} was not found. This is a root concept of a network and should have document location lable.')
    return None

def add_states_to_acfr(new_model):

    # add the state schemas to the acfr-all schema
    acfr_document = new_document(new_model, _CORE_NAMESPACES[_ACFR_NAMESPACE]['all-uri'], new_model.DOCUMENT_TYPES.SCHEMA, _CORE_NAMESPACES[_ACFR_NAMESPACE]['all-namespace'], '')

    for state_namespace, info in _CORE_NAMESPACES.items():
        if info['type'] == 'state':
            state_document = new_document(new_model, info['all-uri'], new_model.DOCUMENT_TYPES.SCHEMA, info['all-namespace'], '')
            acfr_document.add(state_document, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

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

def add_entry_points(new_model):
    sub_taxonomy_documents = set() # This will save all the form entry points for the all entry point

    for tax_ns, tax_info in sorted(_CORE_NAMESPACES.items(), key=lambda x: x[1]['name']):
        # sub taxonomy all file
        sub_taxonomy_document = new_document(new_model, 
                                             tax_info['all-uri'], 
                                             new_model.DOCUMENT_TYPES.SCHEMA, 
                                             tax_info['all-namespace'])
        # TODO fix handling of combo. This "if" is just to prevent a key error.
        if tax_info['uri'] in new_model.documents:
            sub_taxonomy_document.add(new_model.documents[tax_info['uri']], new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
            sub_taxonomy_documents.add(sub_taxonomy_document)
            #sub_taxonomy_documents.add(new_model.documents[tax_info['uri']])
            # Create entry point
            entry_point = new_model.new('PackageEntryPoint', f"{tax_info['name']} taxonomy entry point")
            entry_point.names.append((tax_info['name'], 'en-US'))
            entry_point.description = tax_info['description']
            entry_point.description_language = 'en-US'
            entry_point.version = _NEW_VERSION
            entry_point.documents.append(sub_taxonomy_document)


    # for form, schedules in sorted(forms.items(), key=lambda x: (len(x[0].name.local_name), x[0].name.local_name)):
    #     # first form (in sorted order) is used for the 'all' entry point
    #     if first_form is None:
    #         first_form = form
    #     try:
    #         entry_point_name = list(form.labels.get((_ENTRY_POINT_PATH_LABEL_ROLE, 'en'), []))[0].content
    #     except IndexError:
    #         raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_ENTRY_POINT_PATH_LABEL_ROLE, form.name.clark))
    #     try:
    #         form_name = list(form.labels.get((_EFORMS_LABEL_ROLE, 'en'), []))[0].content
    #     except IndexError:
    #         raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_EFORMS_LABEL_ROLE, form.name.clark))

    #     if first_form is form:
    #         first_name = form_name
    #     all_form_names.append(form_name)

    #     # Create form document
    #     document_name = 'form/{}_{}.xsd'.format(entry_point_name, _NEW_VERSION)
    #     document_namespace = '{}{}/ferc-{}'.format(_NAMESPACE_START, _NEW_VERSION, form_name.lower().replace(' ', '-'))
    #     form_document = new_document(new_model, document_name, new_model.DOCUMENT_TYPES.SCHEMA, document_namespace)
    #     form_entry_documents.add(form_document)
    #     for schedule in schedules:
    #         try:
    #             form_document.add(schedule_documents[schedule], new_model.DOCUMENT_CONTENT_TYPES.IMPORT)
    #         except KeyError:
    #             pass # This is a schedule in the list of schedules that isn't really schedule.

    #     # Create entry point
    #     entry_point = new_model.new('PackageEntryPoint', entry_point_name)
    #     entry_point.names.append((form_name, 'en'))
    #     try:
    #         entry_point.description = list(form.labels.get((_ENTRY_POINT_LABEL_ROLE, 'en'), []))[0].content
    #     except IndexError:
    #         raise FERCSerialzierException("Cannot get {} label for form concept {}".format(_ENTRY_POINT_PATH_LABEL_ROLE, form.name.clark))
    #     entry_point.description_language = 'en'
    #     entry_point.version = _NEW_VERSION
    #     entry_point.documents.append(form_document)
    #     other_element_qname = new_model.new('QName', 'http://www.ferc.gov/form/taxonomy-package', 'entryPoint', 'tp')
    #     entry_point.other_elements[other_element_qname] = form_name


        # Add 'all' document
    all_document_name = f'grip-all_{_NEW_VERSION}.xsd'
    all_namespace = f'{_NAMESPACE_START}{_NEW_VERSION}/grip-all'
    all_document = new_document(new_model, all_document_name, new_model.DOCUMENT_TYPES.SCHEMA, all_namespace)
    for sub_doc in sub_taxonomy_documents:
        all_document.add(sub_doc, new_model.DOCUMENT_CONTENT_TYPES.IMPORT)

    # Add 'all' entry point
    entry_point = new_model.new('PackageEntryPoint', 'All')
    entry_point.names.append(('ACFR - All', 'en'))
    entry_point.description = 'This entry point contains the {} taxonomies'.format(', '.join(sorted( (x['name'] for x in _CORE_NAMESPACES.values()) )))
    entry_point.description_language = 'en'
    entry_point.version = _NEW_VERSION
    entry_point.documents.append(all_document)

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
            warning('Found multiple roles for schedule {}\nRoles are:\n{}'.format(schedule_concept.name.clark,
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
    'name': 'XBRL ACFR Serializer',
    'version': '01.0',
    'description': "This plug-in organizes the taxonomy files and creates a Taxonomy Package for ACFR taxonomies",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2022 XBRL US Inc., All rights reserved.',
    'import': 'serializer',
    # classes of mount points (required)
    'CntlrCmdLine.Options': dummy,
    'CntlrCmdLine.Utility.Run': dummy,
    'CntlrCmdLine.Xbrl.Run': dummy,
    'serializer.serialize': serialize,
}