'''Serializer for FERC'''

import collections
import json
import os
import re

from arelle.ModelDocument import ModelDocument
from arelle.ModelDtsObject import ModelResource, ModelConcept
from arelle.ModelValue import QName
import arelle.XbrlConst as xc
from lxml import etree


_OPTIONS = None

_CONFIG = {
    "short-name": "ferc",
    "core-name": "core",
    "form-type": "{http://www.ferc.gov/form/types}formItemType",
    "schedule-type": "{http://www.ferc.gov/form/types}scheduleItemType",
    "keep-document-namespaces": ["^http://([^/]+\\.)?ferc\\.gov/.*$"],
    "roles": [["default", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/form/[^/]+/roles/Default$"],
              ["schedule", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/form/[^/]+/roles/Schedule/([^/]+)/(.*)$"],
              ["label", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/form/[^/]+/roles/label/(f[0-9]+)(.*)$"],
              ["label", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/form/[^/]*/roles/label/(.*)$"],
              ["reference", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/form/[^/]*/roles/reference/(.*)$"],
              ["core", "^http://(?:(?:eforms\\.)|(?:www\\.))?ferc\\.gov/(?:form/[^/]*/)?arcroles?/(.*)$"]

    ],
    "locations": [
        {"core": "core"},
        {"form": "form"},
        {"schedule": "schedule"}
    ],
}

_DIMENSION_RELATIONSHIP_TYPES = ("http://xbrl.org/int/dim/arcrole/hypercube-dimension",
                                 "http://xbrl.org/int/dim/arcrole/dimension-domain",
                                 "http://xbrl.org/int/dim/arcrole/domain-member",
                                 "http://xbrl.org/int/dim/arcrole/all",
                                 "http://xbrl.org/int/dim/arcrole/notAll",
                                 "http://xbrl.org/int/dim/arcrole/dimension-default"
)
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

class FERCSerialzierException(Exception):
    pass

def serialize(model_xbrl, options, sxm):
    global _OPTIONS
    _OPTIONS = options

    new_model = sxm.SXMDTS()

    x = organize_taxonomy(model_xbrl, new_model, options)

    return dict()


def error(code, msg, model_xbrl):
    global _OPTIONS

    model_xbrl.error(code, msg)
    if not getattr(_OPTIONS, 'serializer_package_allow_errors', False):
        raise FERCSerialzierException

def config(model_object):
    global _CONFIG

    # cntlr = model_object.modelXbrl.modelManager.cntlr

    # if _CONFIG is None:
    #     try:
    #         with open(os.path.join(os.path.dirname(__file__), 'package.json'), 'r') as config_file:
    #             _CONFIG = json.load(config_file)
    #     except FileNotFoundError:
    #         cntlr.addToLog("Packager config file 'package.json' is not found", "error")
    #         raise
    #     except json.JSONDecodeError:
    #         cntlr.addToLog("Packager config file 'package.json' is not a valid json file", "error")
    #         raise

    return _CONFIG

def organize_taxonomy(model_xbrl, new_model, options):
    global _OPTIONS
    _OPTIONS = options

    map = {
           'arcroles': collections.defaultdict(list),
           'concepts': dict(),
           'entries': [],
           'forms': dict(),
           'imports': [],
           'keep-documents': [],
           'label': [],
           'references':[],
           'ref-parts': set(),
           'rels': collections.defaultdict(dict),
           'roles': collections.defaultdict(list),
           'schedule-role-pages': dict(),
           'typed-domains': set(),
           'types': [],
    }

    # Determine which documents to use
    map['keep-documents'], map['imports'] = keep_documents(model_xbrl)

    # get all relationships
    for arcrole, ELR, linkqname, arcqname in model_xbrl.baseSets.keys():
        if ELR and linkqname and arcqname and arcrole and not arcrole.startswith("XBRL-"):
            # This is an individual base set
            relationship_set = model_xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname)
            map['rels'][(arcrole, ELR, linkqname, arcqname)]['relationship-set'] = relationship_set
            organize_networks(model_xbrl.relationshipSet(arcrole, ELR, linkqname, arcqname), new_model)

    organize_labels(model_xbrl, new_model)
    organize_references(model_xbrl, new_model)


    # Find concepts, types, roles, arcroles, typed dimension domains, and reference parts.
    for model_object in model_xbrl.modelObjects:
        # Only need to go through model objects that are in the keep documents. The rest are in imported docs.
        if model_object.modelDocument in map['keep-documents']:
            handler = _ORGANIZER.get(type(model_object).__name__)
            if handler is not None:
                handler(model_object, map)

    # find labels
    map['labels'] = find_labels(model_xbrl, map)

    # find form elements - used to create form entry points
    map['forms'], map['schedule-role-pages'] = find_forms(model_xbrl, map)

    return map

    # DELETE BELOW
    object_by_type = collections.defaultdict(list)
    for x in model_xbrl.modelObjects:
        object_by_type[type(x).__name__].append(x)

    for x in sorted(object_by_type.keys()):
        print(x, len(object_by_type[x]))


    concept_docs = set()
    for model_object in model_xbrl.modelObjects:
        if type(model_object).__name__ == 'ModelConcept':
            concept_docs.add(model_object.modelDocument.uri)

    print('\n'.join(sorted(concept_docs)))
    for name in ('type', 'role', 'arcrole'):
        for k, v in map[name].items():
            print(name, k, len(v))
            #if name == 'role':
            #    for r in sorted(v, key=lambda x: x['role'].roleURI):
            #        print(r['role'].roleURI, *r['location-info'])

def organize_networks(relationship_set, new_model):
    
    #map['rels'][(arcrole, ELR, linkqname, arcqname)]['relationship-set'] = relationship_set

    # Skip demensional relatonships. These will be recreated based on the presentation.
    if (not (relationship_set.linkqname.localName == 'definitionLink' and
             relationship_set.linkqname .namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
             relationship_set.arcqname.localName == 'definitionArc' and
             relationship_set.arcqname.namespaceURI == 'http://www.xbrl.org/2003/linkbase' and
             relationship_set.arcrole in _DIMENSION_RELATIONSHIP_TYPES) and
        is_concept_to_concept_network(relationship_set)):

        # Create the new network
        link_name = new_qname(new_model, relationship_set.linkqname)
        arc_name = new_qname(new_model, relationship_set.arcqname)
        # Get or create the arcrole
        arcrole= (new_model.get('Arcrole', relationship_set.arcrole) or
                  new_arcrole(new_model, relationship_set.modelXbrl, relationship_set.arcrole))
        elrole = (new_model.get('Role', relationship_set.linkrole) or
                  new_role(new_model, relationship_set.modelXbrl, relationship_set.linkrole))
        network = new_model.new('Network', link_name, arc_name, arcrole, elrole)

        # Add the relationships and also create the concepts
        for relationship in relationship_set.modelRelationships:
            # Make sure the concepts of the relationship are created
            from_concept = (new_model.get('Concept', new_qname(new_model, relationship.fromModelObject.qname)) or
                            new_concept(new_model, relationship.fromModelObject))
            to_concept = (new_model.get('Concept', new_qname(new_model, relationship.toModelObject.qname)) or
                          new_concept(new_model, relationship.toModelObject))
            rel_atts = {new_qname_from_clark(new_model, k): v
                        for k, v in relationship.arcElement.attrib.items()
                        if not k.startswith('{http://www.w3.org/1999/xlink}')
                        and not k in ('order', 'weight')}
            network.add_relationship(from_concept, to_concept, relationship.order, relationship.weight, rel_atts)

def is_concept_to_concept_network(relationship_set):
    for rel in relationship_set.modelRelationships:
        if not is_concept_to_concept_relationship(rel):
            return False
    return True

def is_concept_to_concept_relationship(relationship):
    return isinstance(relationship.fromModelObject, ModelConcept) and isinstance(relationship.toModelObject, ModelConcept)

def new_qname(new_model, model_qname):
    return new_model.new('QName', model_qname.namespaceURI, model_qname.localName)

def new_concept(new_model, model_concept):
    
    concept_name, data_type, abstract, nillable, id, attributes = get_element_info(new_model, model_concept)
    period_type = model_concept.periodType
    balance_type = model_concept.balance
    # Really, this could be a chain of substitution groups. 
    substitution_group = new_qname(new_model, model_concept.substitutionGroupQname)
    if model_concept.isTypedDimension:
        typed_domain_name = new_qname(new_model, model_concept.typedDomainElement.qname)
        typed_domain = new_model.get('TypedDomain', typed_domain_name) or new_typed_domain(new_model, model_concept.typedDomainElement) 
    else:
        typed_domain = None

    return new_model.new('Concept',
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

def get_element_info(new_model, model_element):
    name = new_qname(new_model, model_element.qname)
    data_type = new_model.get('Type', new_qname(new_model, model_element.typeQname)) or new_type(new_model, model_element.type if model_element.type is not None else model_element.typeQname)
    abstract = model_element.isAbstract
    nillable = model_element.isNillable
    id = model_element.id
    attributes = get_element_attributes(new_model, model_element.attrib.items())

    return (name,
            data_type,
            abstract,
            nillable,
            id,
            attributes)

def get_element_attributes(new_model, attributes):
    '''Convert lxml attribute dictionary to SXM attribute dictionary'''
    return {new_qname_from_clark(new_model, n): v for n, v in attributes}

def new_qname_from_clark(new_model, name):
    '''Separate the namespace and local name in a clark notation qname'''
    res = re.match('({(.*)})?(.*)', name.strip())
    # There will be 3 items in the groups. [1] is the namespace and [2] is the local name
    new_model.new('QName', res.groups()[1], res.groups()[2])

def new_typed_domain(new_model, model_element):
    name, data_type, abstract, nillable, id, attributes = get_element_info(new_model, model_element)
    return new_model.new('TypedDomain', name, data_type, abstract, nillable, id, attributes, etree.tostring(model_element))

def new_type(new_model, model_type):
    # model_type may be an arelle ModelType or a qname.
    if isinstance(model_type, QName):
        type_name = new_qname(new_model, model_type)
        type_parent = None
        type_content = None
    else:
        if model_type.typeDerivedFrom is not None:
            type_parent_name = new_qname(new_model, model_type.typeDerivedFrom.qname)
            type_parent = new_model.get('Type', type_parent_name) or new_type(new_model, model_type.typeDerivedFrom)
        else:
            type_parent = None

        type_name = new_qname(new_model, model_type.qname)
        type_content = etree.tostring(model_type)
    return new_model.new('Type', type_name, type_parent, type_content)

def new_element(new_model, model_element):

    element_name, data_type, abstract, nillable, id, attributes = get_element_info(new_model, model_element)
    return new_model.new('Element',
                          element_name,
                          id,
                          data_type,
                          abstract,
                          nillable,
                          attributes)

def new_arcrole(new_model, model_xbrl, arcrole_uri):
    '''convert an arelle arcrole to a sxm arcrole'''
    old_arcrole = model_xbrl.arcroleTypes[arcrole_uri]
    if len(old_arcrole) == 0:
        if arcrole_uri in xc.standardArcroleCyclesAllowed:
            usedons = (new_model.new('QName', 'http://www.xbrl.org/2003/linkbase' ,xc.standardArcroleArcElement(arcrole_uri)),)
            definition = ''
        else: 
            error('FERCSerializerError', 'arcrole {} not found in source DTS'.format(arcrole_uri), model_xbrl)
    else:
        usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_arcrole[0].usedOns)
        definition = old_arcrole[0].definition
    return new_model.new('Arcrole', arcrole_uri, definition, usedons)

def new_role(new_model, model_xbrl, role_uri):
    '''convert an arelle role to a sxm role'''
    old_role = model_xbrl.roleTypes[role_uri]
    if len(old_role) == 0:
        if role_uri in xc.standardRoles:
            usedons = tuple()
            definition = _STANDARD_ROLE_DEFINITIONS[role_uri]
        else:
            error('FERCSerializerError', 'role {} not found in source DTS'.format(role_uri), model_xbrl)
    else:
        usedons = tuple(new_model.new('QName', x.namespaceURI, x.localName) for x in old_role[0].usedOns)
        definition = old_role[0].definition
    return new_model.new('Role', role_uri, definition, usedons)

def organize_labels(model_xbrl, new_model):
    '''Get the labels for the concepts that are in the new model'''

    label_network = model_xbrl.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-label')
    for label_rel in label_network.modelRelationships:
        new_concept = new_model.get('Concept', new_qname(new_model, label_rel.fromModelObject.qname))
        if new_concept is not None:
            old_label = label_rel.toModelObject
            label_role = (new_model.get('Role', old_label.role) or
                  new_role(new_model, label_rel.modelXbrl, old_label.role))
            new_concept.add_label(label_role, old_label.xmlLang.lower(), old_label.textValue)

def organize_references(model_xbrl, new_model):
    '''Get the references for the concepts that are in the new model'''

    ref_network = model_xbrl.relationshipSet('http://www.xbrl.org/2003/arcrole/concept-reference')
    for ref_rel in ref_network.modelRelationships:
        new_concept = new_model.get('Concept', new_qname(new_model, ref_rel.fromModelObject.qname))
        if new_concept is not None:
            old_ref = ref_rel.toModelObject
            ref_role = (new_model.get('Role', old_ref.role) or
                  new_role(new_model, old_ref.modelXbrl, old_ref.role))
            # Get the parts
            new_parts = []
            for old_part in old_ref:
                part_name = new_qname(new_model, old_part.qname)
                part_element = new_model.get('Element', part_name) 
                if part_element is None:
                    old_part_element = model_xbrl.qnameConcepts.get(old_part.qname)
                    if old_part_element is None:
                        raise FERCSerialzierException("Cannot find refernce part element definition for {}".format(old_part.qname.clarkNotation))
                    part_element = new_element(new_model, old_part_element)
                new_parts.append(new_model.new('Part', part_element, old_part.textValue))
            new_concept.add_reference(ref_role, new_parts)

                



            #new_concept.add_label(label_role, old_label.xmlLang.lower(), old_label.textValue)








def organize_concept(model_concept, map):

    if model_concept.isItem or model_concept.isTuple:
        concept_rels = get_concept_relationships(model_concept, map)
        keep = any([x.arcrole == 'http://www.xbrl.org/2003/arcrole/parent-child' for x in (concept_rels['froms'] + concept_rels['tos'])])
        labels = []
        references = []
        if keep:
            for rel in concept_rels['froms']:
                if rel.arcrole == 'http://www.xbrl.org/2003/arcrole/concept-label':
                    labels.append(rel)
                if rel.arcrole == 'http://www.xbrl.org/2003/arcrole/concept-reference':
                    references.append(rel)

        map['concepts'][model_concept] = {'concept':model_concept,
                               'rels': concept_rels,
                               'label-rels': labels,
                               'reference-rels': references,
                               'keep': keep}
        # Typed dimension domain
        if model_concept.isTypedDimension:
            map['typed-domains'].add(model_concept.typedDomainElement)      

        # Reference parts
        for ref_rel in references:
            reference = ref_rel.toModelObject
            for ref_part in reference:
                map['ref-parts'].add(ref_part)

def organize_type(model_type, map):
    map['types'].append({'type':model_type})

def organize_role(model_role, map):

    role_uri = model_role.arcroleURI if model_role.isArcrole else model_role.roleURI
    role_map = map['arcroles'] if model_role.isArcrole else map['roles']
    role_info = determine_role_location(role_uri, model_role.modelXbrl)
    if role_info is None:
        model_role.modelXbrl.warning("PackageError","Role '{}' is format. Could not match to a role model".format(role_uri))
    else:
        role_map[role_info[0]].append({'arcrole' if model_role.isArcrole else 'role':model_role, 'location-info':role_info[1]})

def keep_documents(model_xbrl):
    '''Determine which documents to process.

    Keep all non xsd documents.
    Keep xsd documents where the target namespace matches the config for keep-document-namespaces.
    '''
    keep_documents = []
    imports = dict()
    for model_object in model_xbrl.modelObjects:
        if isinstance(model_object, ModelDocument):
            if getattr(model_object, 'noTargetNamespace', True):
                keep_documents.append(model_object)
            else:
                for keep_expression in config(model_object).get('keep-document-namespaces'):
                    if re.fullmatch(keep_expression, model_object.targetNamespace) is not None:
                        keep_documents.append(model_object)
                    else:
                        imports[model_object.targetNamespace] = model_object.uri
    
    return keep_documents, imports

def determine_role_location(role_uri, model_xbrl):
    if role_uri is None:
        return
    
    for role_info in config(model_xbrl).get('roles', tuple()):
        role_type = role_info[0]
        role_expression = role_info[1]
        match = re.fullmatch(role_expression, role_uri)
        if match is not None:
            return (role_type, match.groups())
    
    # If here, no match was found
    return
'''
def determine_namespace_location(namespace_uri, model_xbrl):
    if namespace_uri is None:
        return

    for imported_namespace in config(model_xbrl.modelManager.cntlr).get('imported-namespaces', tuple()):
        if imported_namespace[0] == 'regex':
            if re.match(imported_namespace[1], namespace_uri):
                return 'import'
        elif imported_namespace[0] == 'name':
            if imported_namespace[2] == namespace_uri:
                return 'import'
    # If here then there were no imported namespace matches, so the concept goes to the core
    return 'core'
'''
def get_chained_attr(left, *props, default=None):
    for prop in props:
        prop_value = getattr(left, prop)
        if prop_value is None:
            return default
        else:
            left = prop_value
    return left

def get_concept_relationships(model_concept, map):
    concept_rels = {'froms':[], 'tos': []}
    for v in map['rels'].values():
        concept_rels['froms'].extend(v['relationship-set'].fromModelObject(model_concept))
        concept_rels['tos'].extend(v['relationship-set'].toModelObject(model_concept))
    return concept_rels

def find_forms(model_xbrl, map):
    '''Get the form concepts and the list of schedules for each form

    This method finds all the form concepts and the schedules that belong to each form. It also identifies a definitive
    page number for each schedule. This page number will be used for the file names for the schedule schemas and related
    linkbases. A schedule can be used in more than one form and so have different page numbers for each form. to get to 
    definitive page number, the forms are ranked by the number of schedules in the form and the page number for the highest
    ranked form is used.
    '''
    form_and_schedule = collections.defaultdict(list)
    missing_page_number = 0
    # find form concepts
    form_concepts = tuple(x for x in map['concepts'].values() 
                                if x['concept'].typeQname.clarkNotation == config(model_xbrl).get('form-type') and
                                x['keep'])
    # Get the page label role for the form
    form_page_label_roles = dict()
    for form_concept_info in form_concepts:
        try:
            form_page_label_role = next((x.toModelObject.role for x in form_concept_info['label-rels'] if x.toModelObject.role.endswith('Page')))
        except StopIteration:
            # There are no labels for this concpet.
            form_page_lable_role = tuple()
        
        if form_page_label_role is None:
            error("PackageError", "Form concept '{}' does not have a page label.".format(form_concept_info['concept'].qname.localName), model_xbrl)
        else:
            form_page_label_roles[form_concept_info['concept']] = form_page_label_role

    # get the schedule concepts for each form
    for form_concept_info in form_concepts:
        # Get the label role for the form page numbers
        form_page_label_role = form_page_label_roles.get(form_concept_info['concept'])
        if form_page_label_role is None:
            continue

        for rel in form_concept_info['rels']['tos']:
            if rel.arcrole == 'http://eforms.ferc.gov/form/2020-01-01/arcroles/schedule-form':
                schedule_concept = rel.fromModelObject
                schedule_concept_info = get_concept_info(schedule_concept, map)
                if schedule_concept.typeQname.clarkNotation == config(model_xbrl).get('schedule-type'):
                    # Get page number for the schedule
                    schedule_page_number = get_resource(schedule_concept_info, 'label', form_page_label_role)
                    form_and_schedule[form_concept_info['concept']].append({'schedule_concept': schedule_concept,
                                                                            'page': None if schedule_page_number is None else schedule_page_number.stringValue,
                                                                            'role': rel.linkrole}) 
    # A schedule may be in multiple forms with different page numbers. We want to get a single page number for each schedule.
    # This single page number will be used to name the folder/files for the schedule to shorten the name.
    # Rank the forms by the number of schedules in each form. The for each schedule pick the page number form the highest
    # ranked form. The ranking uses the form concept name as a secondary sort key incase there are forms with the same number of schedules.
    ranked_forms = sorted(form_and_schedule.keys(), key=lambda x: (len(form_and_schedule[x]), x.qname.clarkNotation))
    schedule_role_page_numbers = dict()
    for form_concept in ranked_forms:
        for schedule in form_and_schedule[form_concept]:
            if (schedule['page'] is not None or 
                (schedule['page'] is None and schedule['role'] not in schedule_role_page_numbers)
               ):
                schedule_role_page_numbers[schedule['role']] = schedule['page']
            del schedule['page']
    # Check if any schedule is missing a page number. If so one will be assigned.
    for role in sorted(schedule_role_page_numbers.keys()):
        if schedule_role_page_numbers[role] is None:
            schedule_concepts = set()
            for schedules in form_and_schedule.values():
                for schedule in schedules:
                    if schedule['role'] == role:
                        schedule_concepts.add(schedule['schedule_concept'])
            schedule_list = ', '.join([x.qname.localName for x in schedule_concepts])
            error("PackageError", "Cannot get a definitive page number for role '{}'"
                                  " used with the following schedule concepts: {}".format(role, schedule_list), model_xbrl)
            schedule_role_page_numbers[role] = '0-{}'.format(str(missing_page_number))
            missing_page_number +=1 
    # There will be duplicate page numbers because a schedule concept may be in multiple roles (i.e. retained earings is made up of several roles).
    # Assign a sub page number where there are dups.
    by_page = collections.defaultdict(list)
    for role, page in schedule_role_page_numbers.items():
        by_page[page].append(role)
    # Go through all the page numbers that have multiple roles and assign a sub-page number in alphabetical role order
    for page, roles in by_page.items():
        if len(roles) > 1:
            sub_page = 0
            for role in sorted(roles):
                if sub_page > 0: # This will leave the first one without the sub page number
                    schedule_role_page_numbers[role] = '{}-{}'.format(schedule_role_page_numbers[role], str(sub_page))
                sub_page += 1

    return form_and_schedule, schedule_role_page_numbers

def get_resource(concept_info, resource_type, role, first=True):
    resources = []
    key = 'label-rels' if resource_type == 'label' else 'reference-rels'
    for rel in concept_info[key]:
        if isinstance(rel.toModelObject, ModelResource):
            if rel.toModelObject.role == role:
                if first:
                    return rel.toModelObject
                else:
                    resources.append(rel.toModelObject)
    if first:
        return None
    else:
        return resources

def get_concept_info(model_concept, map):
    return map['concepts'].get(model_concept)

_ORGANIZER = {'ModelConcept': organize_concept,
              'ModelType': organize_type,
              'ModelRoleType': organize_role,
              }

def find_labels(model_xbrl, map):
    '''Find labels for all the concepts'''

    label_relationship_sets = {map['rels'][x]['relationship-set'] for x in map['rels'].keys() if x[0] == 'http://www.xbrl.org/2003/arcrole/concept-label'}

    for concept in map['concepts']:
        for label_rs in label_relationship_sets:
            for rel in label_rs.fromModelObject(concept):
                pass
                

def serialize_taxonomy(map, model_xbrl, options):
    
    # Determine all the files and namespaces
    file_map = determine_files(map, model_xbrl, options)
    
    # Create the taxonomy Package zip file

def determine_files(map, model_xbrl, options):
    '''Figure out what is going in each file. 
    '''

    file_map = dict()

    # Core
    # The contains all acrrole, all concepts, reference parts, default roles, label roles, reference roles, type domains, types
    



'''
List of model object types
ModelAny
ModelAnyAttribute
ModelAttribute
ModelAttributeGroup
ModelChoice
ModelConcept
ModelDocument
ModelEnumeration
ModelLink
ModelLocator
ModelObject
ModelResource
ModelRoleType
ModelSequence
ModelType
'''

'''
List of tags in a taxonomy
{http://www.ferc.gov/form/parts}Account
{http://www.ferc.gov/form/parts}Column
{http://www.ferc.gov/form/parts}ColumnName
{http://www.ferc.gov/form/parts}Dimension
{http://www.ferc.gov/form/parts}DoNotConvert
{http://www.ferc.gov/form/parts}ElementName
{http://www.ferc.gov/form/parts}FixedMember
{http://www.ferc.gov/form/parts}Form
{http://www.ferc.gov/form/parts}MemberValue
{http://www.ferc.gov/form/parts}Period
{http://www.ferc.gov/form/parts}Row
{http://www.ferc.gov/form/parts}RowEnd
{http://www.ferc.gov/form/parts}RowStart
{http://www.ferc.gov/form/parts}RuleDescription
{http://www.ferc.gov/form/parts}RuleFocus
{http://www.ferc.gov/form/parts}RuleIdentifier
{http://www.ferc.gov/form/parts}RuleLogic
{http://www.ferc.gov/form/parts}RuleMessage
{http://www.ferc.gov/form/parts}RuleSeverity
{http://www.ferc.gov/form/parts}Schedule
{http://www.ferc.gov/form/parts}ScheduleRole
{http://www.ferc.gov/form/parts}SequenceDimension
{http://www.ferc.gov/form/parts}SequenceRole
{http://www.ferc.gov/form/parts}Sign
{http://www.ferc.gov/form/parts}ValueType
{http://www.ferc.gov/form/taxonomy-pacckage}form
{http://www.w3.org/2001/XMLSchema}annotation
{http://www.w3.org/2001/XMLSchema}appinfo
{http://www.w3.org/2001/XMLSchema}complexType
{http://www.w3.org/2001/XMLSchema}documentation
{http://www.w3.org/2001/XMLSchema}element
{http://www.w3.org/2001/XMLSchema}enumeration
{http://www.w3.org/2001/XMLSchema}import
{http://www.w3.org/2001/XMLSchema}length
{http://www.w3.org/2001/XMLSchema}restriction
{http://www.w3.org/2001/XMLSchema}simpleContent
{http://www.w3.org/2001/XMLSchema}simpleType
{http://www.xbrl.org/2003/linkbase}arcroleRef
{http://www.xbrl.org/2003/linkbase}arcroleType
{http://www.xbrl.org/2003/linkbase}calculationArc
{http://www.xbrl.org/2003/linkbase}calculationLink
{http://www.xbrl.org/2003/linkbase}definition
{http://www.xbrl.org/2003/linkbase}definitionArc
{http://www.xbrl.org/2003/linkbase}definitionLink
{http://www.xbrl.org/2003/linkbase}label
{http://www.xbrl.org/2003/linkbase}labelArc
{http://www.xbrl.org/2003/linkbase}labelLink
{http://www.xbrl.org/2003/linkbase}linkbaseRef
{http://www.xbrl.org/2003/linkbase}loc
{http://www.xbrl.org/2003/linkbase}presentationArc
{http://www.xbrl.org/2003/linkbase}presentationLink
{http://www.xbrl.org/2003/linkbase}reference
{http://www.xbrl.org/2003/linkbase}referenceArc
{http://www.xbrl.org/2003/linkbase}referenceLink
{http://www.xbrl.org/2003/linkbase}roleRef
{http://www.xbrl.org/2003/linkbase}roleType
{http://www.xbrl.org/2003/linkbase}usedOn
{http://xbrl.org/2016/taxonomy-package}description
{http://xbrl.org/2016/taxonomy-package}entryPoint
{http://xbrl.org/2016/taxonomy-package}entryPointDocument
{http://xbrl.org/2016/taxonomy-package}entryPoints
{http://xbrl.org/2016/taxonomy-package}identifier
{http://xbrl.org/2016/taxonomy-package}license
{http://xbrl.org/2016/taxonomy-package}name
{http://xbrl.org/2016/taxonomy-package}publicationDate
{http://xbrl.org/2016/taxonomy-package}publisher
{http://xbrl.org/2016/taxonomy-package}publisherCountry
{http://xbrl.org/2016/taxonomy-package}publisherURL
{http://xbrl.org/2016/taxonomy-package}version
{urn:oasis:names:tc:entity:xmlns:xml:catalog}rewriteURI
'''
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
    'serializer.serialize': serialize
}