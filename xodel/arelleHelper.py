
from arelle.ModelDtsObject import ModelConcept, ModelType
from arelle.ModelValue import QName
import arelle.XbrlConst as xc

from lxml import etree
from .xodel import XodelException
import re

_BASE_NAMESPACES = re.compile(r'^http://(www\.)?((w3)|(xbrl))\.org/')
# def new_concept(new_model, model_concept, namespace=None):

#     # override the namespace for state concepts
#     namespace = _STATE_CONCEPTS.get(model_concept.qname.localName, namespace)

#     concept_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_concept, True, namespace)

#     if new_model.get('Concept', concept_name) is not None:
#         # The concept is already in the model
#         return new_model.get('Concept', concept_name)

#     period_type = model_concept.periodType
#     balance_type = model_concept.balance

#     if model_concept.isTypedDimension:
#         typed_domain_name = new_qname(new_model, model_concept.typedDomainElement.qname, namespace)
#         typed_domain = new_model.get('TypedDomain', typed_domain_name) or new_typed_domain(new_model, model_concept.typedDomainElement, namespace) 
#     else:
#         typed_domain = None

#     concept = new_model.new('Concept',
#                           concept_name,
#                           data_type,
#                           abstract,
#                           nillable,
#                           period_type,
#                           balance_type,
#                           substitution_group,
#                           id,
#                           attributes,
#                           typed_domain)

#     # Assign document
#     if concept_name.namespace in _CORE_NAMESPACES:
#         # TODO add descriptions to the core documents
#         document = new_document(new_model, _CORE_NAMESPACES[concept_name.namespace]['uri'], new_model.DOCUMENT_TYPES.SCHEMA, concept_name.namespace, '')
#     else:
#         document = new_document(new_model, model_concept.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_concept.modelDocument.targetNamespace)

#     document.add(concept)

#     # add concept to concept map
#     _CONCEPT_MAP[model_concept] = concept

#     organize_labels_for_concept(concept, model_concept)
#     organize_references_for_concept(concept, model_concept)

#     return concept

# def new_element(new_model, model_element):

#     element_name, data_type, abstract, nillable, id, substitution_group, attributes = get_element_info(new_model, model_element)
#     new_element =  new_model.new('Element',
#                                 element_name,
#                                 data_type,
#                                 abstract,
#                                 nillable,
#                                 id,
#                                 substitution_group,
#                                 attributes)

#     # Assign document
#     if new_element.name.namespace == _CORE_NAMESPACE:
#         document = new_document(new_model, _CORE_NAMESPACES[new_element.name.namespace]['uri'], new_model.DOCUMENT_TYPES.SCHEMA, _TYPE_NAMESPACE, _TYPE_DESCRIPTION)
#     else:
#         document = new_document(new_model, model_element.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_element.modelDocument.targetNamespace)

#     document.add(new_element)

#     return new_element

# def new_type(new_model, model_type, new_type_qname, element_namespace=None):
#     # model_type may be an arelle ModelType or a qname. If it is a qname it is a base xbrl type
#     if new_model.get('Type', new_type_qname) is not None:
#         return new_model.get('Type', new_type_qname)

#     if isinstance(model_type, QName):
#         # This is base XML type.
#         type_parent = None
#         type_content = None
#     else:
#         if model_type.typeDerivedFrom is not None:
#             type_parent_qname = fix_type_qname(new_model, model_type.typeDerivedFrom.qname, element_namespace)
#             type_parent = new_model.get('Type', type_parent_qname) or new_type(new_model, model_type.typeDerivedFrom, type_parent_qname, element_namespace)
#         else:
#             type_parent = None

#         type_content = etree.tostring(model_type)

#     new_data_type = new_model.new('Type', new_type_qname, type_parent, type_content)

#     # if not new_data_type.is_base_xml: # otherwise this is a base xml type and there is no document
#     #     if new_data_type.name.namespace in (x['type-namespace'] for x in _CORE_NAMESPACES.values()):
#     #         type_document = new_document(new_model, 
#     #                                      _CORE_NAMESPACES[element_namespace]['type-uri'], 
#     #                                      new_model.DOCUMENT_TYPES.SCHEMA, 
#     #                                      new_data_type.name.namespace, 
#     #                                      _CORE_NAMESPACES[element_namespace]['type-description'])
#     #     else:
#     #         if isinstance(model_type, ModelType) and model_type.qname.localName.endswith('@anonymousType'):
#     #             type_document = None
#     #         else: # probably in the DTR (Data Type Registry) or some other referenced type from an external taxonomy
#     #             type_document = new_document(new_model, model_type.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_type.modelDocument.targetNamespace)
#     #     if type_document is not None:
#     #         type_document.add(new_data_type)

#     return new_data_type


# def new_qname(new_model, model_qname, namespace=None):

#     return new_model.new('QName', namespace or model_qname.namespaceURI, model_qname.localName)






# def get_element_info(new_model, model_element, is_concept=False, namespace=None):

#     name = new_qname(new_model, model_element.qname, namespace)

#     new_type_qname = fix_type_qname(new_model, model_element.typeQname, namespace)
#     # determine if this is a type that is defined in this taxonomy or an external data type (i.e. DTR)
#     data_type = (new_model.get('Type', new_type_qname) or 
#                     new_type(new_model, model_element.type if model_element.type is not None else model_element.typeQname, 
#                              new_type_qname, 
#                              namespace))
#     if model_element.substitutionGroup is None:
#         substitution_group = None
#     else:
#         if model_element.substitutionGroupQname.clarkNotation in (_ITEM, _TUPLE):
#             substitution_group = new_qname(new_model, model_element.substitutionGroupQname)
#         else:
#             # Determine if the element of the substitution group is defined in the acfr taxonomy or is
#             # an xbrl base concept (i.e. stringItemType)
#             if _BASE_NAMESPACES.match(model_element.substitutionGroupQname.namespaceURI) is None:
#                 # This is a derrived substitution group
#                 sub_group_namespace = namespace
#             else:
#                 sub_group_namespace = model_element.substitutionGroupQname.namespaceURI

#             sub_group_qname = new_qname(new_model, model_element.substitutionGroupQname, sub_group_namespace)
#             if is_concept:
#                 substitution_group = (new_model.get('Concept', sub_group_qname) or
#                                     new_concept(new_model, model_element.substitutionGroup, sub_group_namespace))
#             else: # the substitution group is an element
#                 substitution_group = (new_model.get('Element', sub_group_qname) or
#                                     new_element(new_model, model_element.substitutionGroup))

#     abstract = model_element.isAbstract
#     nillable = model_element.isNillable
#     id = model_element.id
#     attributes = get_element_attributes(new_model, model_element.attrib.items())

#     return (name,
#             data_type,
#             abstract,
#             nillable,
#             id,
#             substitution_group,
#             attributes)

# def fix_type_qname(new_model, old_qname, element_namespace=None):

#     if _BASE_NAMESPACES.match(old_qname.namespaceURI) is None:
#         if element_namespace is None:
#             raise ACFRSerialzierException(f"Don't know where to put this type: {old_qname.namespaceURI}:{old_qname.localName}")
#         try:
#             type_namespace = _CORE_NAMESPACES[element_namespace]['type-namespace']
#         except:
#             x = 0

#     else:
#         type_namespace = old_qname.namespaceURI

#     return new_model.new('QName', type_namespace, old_qname.localName)


def extract_element_info(model_element):

    return {'name': model_element.qname,
            'type-name': model_element.typeQname,
            'is-abstract': model_element.isAbstract,
            'nillable': model_element.isNillable,
            'id': model_element.id,
            'substitution-group-name': model_element.substitutionGroupQname,
            'attributes': model_element.attrib.items()}

def extract_concept_info(model_concept):
    concept_info = extract_element_info(model_concept)
    concept_info['balance'] = model_concept.balance
    concept_info['period-type'] = model_concept.periodType
    if model_concept.isTypedDimension:
        concept_info['typed-domain-name'] = model_concept.TypedDomainElement.qname
    else:
        concept_info['typed-domain-name'] = None
    
    return concept_info

def new_type_from_arelle(new_model, model_type):
    # model_type may be an arelle ModelType or a qname. If it is a qname it is a base xbrl type
    new_type_qname = resolve_clark_to_qname(model_type.qname.clarkNotation, new_model)
    if new_model.get('Type', new_type_qname) is not None:
        return new_model.get('Type', new_type_qname)

    if isinstance(model_type, QName):
        # This is base XML type.
        type_parent = None
        type_content = None
    else:
        if model_type.typeDerivedFrom is not None:
            type_parent = new_model.get('Type', model_type.typeDerivedFrom.qname) or new_type_from_arelle(new_model, model_type.typeDerivedFrom)
        else:
            type_parent = None

        type_content = etree.tostring(model_type)

    new_data_type = new_model.new('Type', new_type_qname, type_parent, type_content)

    return new_data_type

def resolve_clark_to_qname(name, dts):
    '''Convert a clark notation qname to a SXMQName'''
    match = re.match('^{([^}]+)}(.*)$', name)
    if match is None:
        raise XodelException(f"QName '{name}' is not a valid clark notation")
    return dts.new('QName', match.group(1), match.group(2))