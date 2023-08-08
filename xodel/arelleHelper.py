
from arelle import FileSource
from arelle.ModelDtsObject import ModelConcept, ModelType
from arelle.ModelValue import qname, QName
import arelle.XbrlConst as xc

from lxml import etree
from .XodelException import XodelException
from .XodelVars import *
import re


_DTR_LOCATION = 'https://www.xbrl.org/dtr/dtr.xml'

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


def extract_element_info(model_element, dts):



    return {'element-name': resolve_clark_to_qname(model_element.qname.clarkNotation, dts),
            'type-name': resolve_clark_to_qname(model_element.typeQname.clarkNotation, dts),
            'is-abstract': model_element.isAbstract,
            'nillable': model_element.isNillable,
            'id': model_element.id,
            'substitution-group-name': resolve_clark_to_qname(model_element.substitutionGroupQname.clarkNotation, dts),
            'attributes': {k:v for k, v in model_element.attrib.items()
                               if k not in ('name', 'id', 'type', 'substitutionGroup', 'abstract',
                                            '{http://www.xbrl.org/2003/instance}periodType',
                                            '{http://www.xbrl.org/2003/instance}balance')},
            # Save the namespace map to resolve qname values in attributes
            'nsmap': model_element.nsmap
    }

def extract_concept_info(model_concept, dts):
    concept_info = extract_element_info(model_concept, dts)
    concept_info['concept-name'] = concept_info['element-name']
    del concept_info['element-name']
    concept_info['balance'] = model_concept.balance
    concept_info['period-type'] = model_concept.periodType
    if model_concept.isTypedDimension:
        concept_info['typed-domain-name'] = resolve_clark_to_qname(model_concept.TypedDomainElement.qname.clarkNotation, dts)
    else:
        concept_info['typed-domain-name'] = None
    
    return concept_info

def extract_role_info(model_role, dts):
    role_info = {
        'uri': model_role.roleURI,
        'definition': model_role.definition,
        'used-on': [resolve_clark_to_qname(x.clarkNotation, dts) for x in model_role.usedOns]
    }

    return role_info

def extract_rel_info(model_rel, dts):
    ''''
    relationship
    relationship-source
    relationship-target
    relationship-order
    relationship-weight
    relationship-preferred-label
    relationship-linkrole-uri
    relationship-type
    relationship-arcrole
    relationship-attribute
    relationship-id
    '''
    rel_info = dict()
    rel_info['source-name'] = resolve_clark_to_qname(model_rel.fromModelObject.qname.clarkNotation, dts)
    rel_info['target-name'] = resolve_clark_to_qname(model_rel.toModelObject.qname.clarkNotation, dts)
    if model_rel.orderDecimal is not None:
        rel_info['order'] = model_rel.orderDecimal
    if model_rel.preferredLabel is not None:
        rel_info['preferred-label'] = model_rel.preferredLabel
    if model_rel.weightDecimal is not None:
        rel_info['weight'] = model_rel.weightDecimal
    rel_info['role'] = model_rel.linkrole
    rel_info['type'] = resolve_clark_to_qname(model_rel.linkQname.clarkNotation, dts)
    rel_info['arcrole'] = model_rel.arcrole
    rel_info['attriubtes'] = {k:v for k, v in model_rel.arcElement.attrib.items()
                               if k not in ('order', 'weight', 'preferredLabel',
                                            '{http://www.w3.org/1999/xlink}arcrole',
                                            '{http://www.w3.org/1999/xlink}from',
                                            '{http://www.w3.org/1999/xlink}to',
                                            '{http://www.w3.org/1999/xlink}type',
                                            )}

    return rel_info









def sxm_qname_to_arelle_qname(sxm_qname):
    return qname(sxm_qname.namespace, sxm_qname.local_name)

def model_qname_index(arelle_model):
    if not hasattr(arelle_model, 'xodel_index'):
        index = dict()
        for arelle_object in arelle_model.modelObjects:
            object_name = getattr(arelle_object, 'qname', None)
            if object_name is not None:
                index[object_name.clarkNotation] = arelle_object
        arelle_model.xodel_index = index

    return arelle_model.xodel_index

def get_arelle_object_by_qname(object_qname, cntlr):
    # Search the arelle models for an object with a specifict qname.
    # The search will use the default taxonomy first, then look in taxonomies
    # added by xule rules that returned model Objects.
    for arelle_model in (cntlr.modelManager.modelXbrl,) + tuple(XodelVars.get(cntlr, 'arelle-models').values()):
        if object_qname in model_qname_index(arelle_model):
            return model_qname_index(arelle_model)[object_qname]
    
    return None

def find_type(new_model, type_name, cntlr):
    '''Find a type based on the type name
       new_model is a SXMDTS
       type_name is is an SXMQname
       
       The type may already be in the model. 
       If not, then try a loaded arelle model
       If not see if it is a base xbrli type
       If not see if it is in the DTR'''
    concept_type = new_model.get('Type', type_name)
    if concept_type is None:
        # Get the type from the arelle model
        arelle_type = get_arelle_object_by_qname(type_name.clark, cntlr)

        concept_type = (new_type_from_arelle(new_model, arelle_type) or
                        new_type_from_dtr(new_model, type_name, cntlr) or
                        new_type_from_xbrli(new_model, type_name, cntlr))
    
    return concept_type

def new_type_from_arelle(new_model, model_type):
    # model_type may be an arelle ModelType or a qname. If it is a qname it is a base xbrl type
    if model_type is None:
        return None
    if isinstance(model_type, QName):
        new_type_qname = resolve_clark_to_qname(model_type.clarkNotation, new_model)
    else:
        new_type_qname = resolve_clark_to_qname(model_type.qname.clarkNotation, new_model)
    if new_model.get('Type', new_type_qname) is not None:
        return new_model.get('Type', new_type_qname)

    if model_type.qname.namespaceURI == 'http://www.xbrl.org/2003/instance':
        # This is base XML type.
        type_parent = None
        type_content = None
    else:
        if model_type.typeDerivedFrom is not None:
            type_parent = new_model.get('Type', model_type.typeDerivedFrom.qname) or new_type_from_arelle(new_model, model_type.typeDerivedFrom)
        else:
            type_parent = None

        type_content = etree.tostring(model_type).decode()

    new_data_type = new_model.new('Type', new_type_qname, type_parent, type_content)
    # Assign the document
    if model_type.modelDocument.uri.startswith('http:') or model_type.modelDocument.uri.startswith('https:'):
        new_data_type.document = get_or_make_document(new_model, model_type.modelDocument.uri, new_model.DOCUMENT_TYPES.SCHEMA, model_type.modelDocument.targetNamespace)

    return new_data_type

def open_file(url, cntlr, as_text=True):
    contents = XodelVars.get(cntlr, f'FILE-{url}')
    if contents is None:
        # Using the FileSource object in arelle. This will open the file and handle taxonomy package mappings.
        file_source = FileSource.openFileSource(url, cntlr)
        file = file_source.file(url, binary=True)
        # file is  tuple of one item as a BytesIO stream. Since this is in bytes, it needs to be converted to text via a decoder.
        # Assuming the file is in utf-8. 
        if as_text:
            contents = ''.join([x.decode('utf-8') for x in file[0].readlines()])
        else:
            contents = file[0].read()
        XodelVars.set(cntlr, f'FILE-{url}', contents)
    return contents

def new_type_from_dtr(new_model, type_qname, cntlr):
    # See if the DTR is already open
    dtr_tree = XodelVars.get(cntlr, 'DTR-TREE')
    if dtr_tree is None:
        # open the DTR
        try:
            dtr_string = open_file(_DTR_LOCATION, cntlr, as_text=False)
        except OSError:
            raise XodelException(f'Unable to open Data Type Registry (DTR) at {_DTR_LOCATION}')
        dtr_tree = etree.fromstring(dtr_string)
        XodelVars.set(cntlr, 'DTR-TREE', dtr_tree)
    # Find the type in the DTR
    if '{' in dtr_tree.tag:
        nsmap = {'dtr': dtr_tree.tag[1:dtr_tree.tag.find('}')]}
    else:
        # The default is the namespace
        nsmap = {'dtr': dtr_tree.nsmap.get(None)}
    dtr_type = dtr_tree.xpath(f"dtr:types/dtr:type[dtr:typeNamespace='{type_qname.namespace}' and dtr:typeName='{type_qname.local_name}']", namespaces=nsmap)
    if len(dtr_type) == 0: # There really should only be one or xero
        return None
    # Now load the taxonomy that the type is in
    dtr_taxonomy_file_location = dtr_type[0].find('dtr:authoritativeHref', namespaces=nsmap).text
    # remove the id of the type from the authoritative href.
    dtr_taxonomy_file_location = dtr_taxonomy_file_location.split('#')[0]
    dtr_arelle_model = XodelVars.get(cntlr, f'DTR-arelle-model-{dtr_taxonomy_file_location}')
    if dtr_arelle_model is None:
        # Get the taxonomy that defines the DTR type
        dtr_taxonomy_file_source = FileSource.openFileSource(dtr_taxonomy_file_location, cntlr)            
        dtr_arelle_model = cntlr.modelManager.load(dtr_taxonomy_file_source)
        if len(dtr_arelle_model.errors) > 0:
            raise XodelException(f'Cannot open Taxonomy for type {type_qname.clark}. Taxonomy location from the Data Type Registry (DTR) is {dtr_taxonomy_file_location}')
        XodelVars.set(cntlr, f'DTR-arelle-model-{dtr_taxonomy_file_location}', dtr_arelle_model)
    
    # get the arelle type
    arelle_type = dtr_arelle_model.qnameTypes.get(qname(type_qname.clark))
    if arelle_type is None:
        return None
    else:
        return new_type_from_arelle(new_model, arelle_type)

def new_type_from_xbrli(new_model, type_qname, cntlr):
    pass

def get_or_make_document(model, uri, doc_type, namespace=None):
    if model.get('Document', uri) is None:
        model.new('Document', uri, doc_type, namespace)
    return model.get('Document', uri)

def type_from_dtr(namespace, name, cntlr):
    try:
        dtr_file = FileSource.openFileSource(_DTR_LOCATION, cntlr)
    except:
        raise XodelException(f"Cannot find Data Type Registry (DTR) at {_DTR_LOCATION}")

def resolve_clark_to_qname(name, dts):
    '''Convert a clark notation qname to a SXMQName'''
    match = re.match('^{([^}]+)}(.*)$', name)
    if match is None:
        raise XodelException(f"QName '{name}' is not a valid clark notation")
    return dts.new('QName', match.group(1), match.group(2))

def match_clark(clark):
    match = re.match('^{([^}]+)}(.*)$', clark)
    if match is None:
        raise XodelException(f"QName '{clark}' is not a valid clark notation")
    return match

def resolve_qname_to_clark(name, node, is_attribute=False):
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
    if is_attribute and namespace is None:
        return local_name
    else:
        if namespace is None:
            raise XodelException(f"QName cannot be resolved for name '{name}'")
        return f'{{{namespace}}}{local_name}'