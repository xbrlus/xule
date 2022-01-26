import collections
import logging
import optparse
import os
import re
import zipfile

from lxml import etree

from arelle import FileSource, PackageManager, PluginManager
from arelle.CntlrWebMain import Options

_CNTLR = None
_OPTIONS = None
_PLUGINS = {}
_SXM = None
_PACKAGE_FOLDER = None

_SCHEMA_NAMESPACE = 'http://www.w3.org/2001/XMLSchema'
_SCHEMA = '{http://www.w3.org/2001/XMLSchema}schema'
_IMPORT = '{http://www.w3.org/2001/XMLSchema}import'
_ELEMENT = '{http://www.w3.org/2001/XMLSchema}element'
_LINKBASE = '{http://www.xbrl.org/2003/linkbase}linkbase'
_ROLE_REF = '{http://www.xbrl.org/2003/linkbase}roleRef'
_ARCROLE_REF = '{http://www.xbrl.org/2003/linkbase}arcroleRef'
_DEFINITION_ARC = '{http://www.xbrl.org/2003/linkbase}definitionArc'
_DEFINITION_LINKBASE = '{http://www.xbrl.org/2003/linkbase}definitionLink'
_PERIOD_ATTRIBUTE = '{http://www.xbrl.org/2003/instance}periodType'
_BALANCE_ATTRIBUTE = '{http://www.xbrl.org/2003/instance}balance'
_TYPED_DOMAIN_REF_ATTRIBUTE = '{http://xbrl.org/2005/xbrldt}typedDomainRef'
_CONTEXT_ELEMENT_ATTRIBUTE = '{http://xbrl.org/2005/xbrldt}contextElement'
_ARCROLE_TYPE = '{http://www.xbrl.org/2003/linkbase}arcroleType'
_ROLE_TYPE = '{http://www.xbrl.org/2003/linkbase}roleType'
_ROLE_DEFINITION = '{http://www.xbrl.org/2003/linkbase}definition'
_APP_INFO_ELEMENT = '{http://www.w3.org/2001/XMLSchema}appinfo'
_ANNOTATION_ELEMENT = '{http://www.w3.org/2001/XMLSchema}annotation'
_DOCUMENTATION_ELEMENT = '{http://www.w3.org/2001/XMLSchema}documentation'
_LINKBASE_REF_ELEMENT = '{http://www.xbrl.org/2003/linkbase}linkbaseRef'
_USEDON_ELEMENT = '{http://www.xbrl.org/2003/linkbase}usedOn'

_DIMENSION_ARCROLES = {'all': ('http://xbrl.org/int/dim/arcrole/all', 'undirected',
                            'Source (a primary item declaration) requires a combination of dimension members of the target (hypercube) to appear in the context of the primary item.'),
                       'notAll': ('http://xbrl.org/int/dim/arcrole/notAll', 'undirecte',
                            'Source (a primary item declaration) requires a combination of dimension members of the target (hypercube) not to appear in the context of the primary item.'),
                       'hypercube-dimension': ('http://xbrl.org/int/dim/arcrole/hypercube-dimension', 'none',
                            'Source (a hypercube) contains the target (a dimension) among others.'),
                       'dimension-domain': ('http://xbrl.org/int/dim/arcrole/dimension-domain', 'none',
                            'Source (a dimension) has only the target (a domain) as its domain.'),
                       'dimension-default': ('http://xbrl.org/int/dim/arcrole/dimension-default', 'none',
                            'Source (a dimension) declares that there is a default member that is the target of the arc (a member).'),
                       'domain-member': ('http://xbrl.org/int/dim/arcrole/domain-member', 'undirected',
                            'Source (a domain) contains the target (a member).')
                       }
_DIMENSION_ARC_BY_ENDS = {('Cube', 'Primary'): 'all',
                          ('Cube', 'Dimension'): 'hypercube-dimension',
                          ('Dimension', 'Member'): 'dimension-domain',
                          ('Dimension', 'Default'): 'dimension-default',
                          ('Primary', 'Member'): 'domain-member',
                          ('Member', 'Member'): 'domain-member'}

_DIMENSION_URI = 'http://www.xbrl.org/2005/xbrldt-2005.xsd'
_DIMENSION_NAMESPACE = 'http://xbrl.org/2005/xbrldt'
_DIMENSION_ARC_COMPONENTS = dict()
_SERIALIZATION_TYPES = ('xml',)
_RESOURCE_LINKBASES = {'Label': {'extended_link': '{http://www.xbrl.org/2003/linkbase}labelLink', 
                                 'arc': '{http://www.xbrl.org/2003/linkbase}labelArc', 
                                 'resource': '{http://www.xbrl.org/2003/linkbase}label',
                                 'arcrole': 'http://www.xbrl.org/2003/arcrole/concept-label'},
                       'Reference': {'extended_link': '{http://www.xbrl.org/2003/linkbase}referenceLink', 
                                     'arc': '{http://www.xbrl.org/2003/linkbase}referenceArc',  
                                     'resource': '{http://www.xbrl.org/2003/linkbase}reference',
                                     'arcrole': 'http://www.xbrl.org/2003/arcrole/concept-reference'}}

class SerializerException(Exception):
    pass

class NSMap:
    def __init__(self, init_map):
        # init_map must be a dictionary keyed by prefix. The value
        self.map = init_map.copy() # make a copy so changes to the orignal dont affect this object

    @property
    def ns_by_prefix(self):
        return {k: v['ns'] for k, v in self.map.items()}

    @property
    def prefix_by_ns(self):
        return {v['ns']: k for k, v in self.map.items()}

    def copy(self):
        return NSMap(self.map) # the initiator makes a copy of the map

    def get_or_add_prefix(self, ns, location=None):
        if self.prefix(ns) is None:
            # need to add the namespace and assign a prefix
            # first option for a prefix is to take the last part of the namespace
            # that doesn't look like a date
            url_parts = ns.lower().split('/')
            prefix = None
            for part in reversed(url_parts):
                if re.fullmatch('\d{4}-\d{2}-\d{2}', part): # This looks like a date
                    continue
                if ':' in part: # this might be the http: or https:. In any case it is not a good prefix
                    continue
                if part in ('', 'cr'):
                    continue
                prefix = part
                break
            if prefix is None:
                # no prefix candidate was found
                prefix = 'ns'
            if prefix in self.map: # the potential prefix needs to be numbered
                for i in range(1,1000000): # if there are over a million this is a very complicated taxonomy
                    if prefix + str(i) not in self.map:
                        prefix += str(i)
                        break
                else:
                    raise SerializerException("Too many namespaces tried 1 million times for prefix {} and namespace {}".format(prefix, ns))
            self.map[prefix] = {'ns': ns}
            if location is not None:
                self.map[prefix]['location'] = location
            return prefix
        else:
            return self.prefix(ns)

    def schema_locations(self, start_document):
        # Returns a space separated list of namespaces and locations. Used for the schemaLocation attribute
        result = []
        for namespace_info in self.map.values():
            if 'location'in namespace_info:
                if namespace_info['location'].lower().startswith('http:') or namespace_info['location'].lower().startswith('http:s'):
                    href = namespace_info['location']
                else:
                    href = os.path.relpath(namespace_info['location'], start=os.path.dirname(start_document.uri))
                result.append(namespace_info['ns'])
                result.append(href)

        return ' '.join(result)

    def location(self, prefix):
        if prefix in self.map:
            return self.map[prefix].get('location')
        else:
            return None

    def namespace(self, prefix):
        if prefix in self.map:
            return self.map[prefix]['ns']
        else:
            return None

    def prefix(self, ns):
        for k, v in self.map.items():
            if v['ns'] == ns:
                return k
        # no namespace was found in the map
        return None

    def get_qname(self, namespace, local_name):
        prefix = self.get_or_add_prefix(namespace)
        if prefix is None:
            return local_name
        else:
            return '{}:{}'.format(prefix, local_name)


_STANDARD_NS = NSMap({'xs': {'ns': 'http://www.w3.org/2001/XMLSchema'},
                      'xbrli': {'ns': 'http://www.xbrl.org/2003/instance', 'location': 'http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd'},
                      'xbrldt': {'ns': 'http://xbrl.org/2005/xbrldt', 'location': 'http://www.xbrl.org/2005/xbrldt-2005.xsd'},
                      'xsi': {'ns': 'http://www.w3.org/2001/XMLSchema-instance'}
                      })

_STANDARD_LINKBASE_NS = NSMap({'link': {'ns': 'http://www.xbrl.org/2003/linkbase', 'location': 'http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd'},
                              'xlink': {'ns': 'http://www.w3.org/1999/xlink'},
                              'xsi': {'ns': 'http://www.w3.org/2001/XMLSchema-instance'}
                              })

_TAXONOMY_PACKAGE_NS = NSMap({'tp': {'ns': 'http://xbrl.org/2016/taxonomy-package'}})

_CATALOG_NS = NSMap({'ct': {'ns': 'urn:oasis:names:tc:entity:xmlns:xml:catalog'}})

# Utility to find another plugin
def getSerizlierPlugins(cntlr):
    '''Serializer plugins have a 'serializer.serialize' entry in the _PLUGIN dictionary.'''
    serializer_plugins = []
    for _x, plugin_info in PluginManager.modulePluginInfos.items():
        if 'serializer.serialize' in plugin_info:
            serializer_plugins.append(plugin_info)
    
    return serializer_plugins

def getPlugin(cntlr, plugin_name):
    """Find the  plugin
    
    This will locate the plugin module.
    """
    global _PLUGINS
    if plugin_name not in _PLUGINS:
        for _x, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == plugin_name:
                _PLUGINS[plugin_name] = plugin_info
                break
        else:
            cntlr.addToLog(_("'{plugin_name}'' plugin is not loaded. '{plugin_name}' plugin is required. "
                             "This plugin should be automatically loaded.".format(plugin_name=plugin_name)))
    
    return _PLUGINS[plugin_name]

def getPluginObject(cntlr, plugin_name, object_name):
    """Get method from a plugin
    
    Get a method/function from a plugin.
    """
    return getPlugin(cntlr, plugin_name).get(object_name)


def error(msg, code='Serializer'):
    _CNTLR.addToLog(msg, code, level=logging.ERROR)
    if not getattr(_OPTIONS, 'serializer_package_allow_errors', False):
        raise SerializerException

def warning(msg, code='Serializer'):
    _CNTLR.addToLog(msg, code, level=logging.WARNING)

def info(msg, code='Serializer'):
    _CNTLR.addToLog(msg, code, level=logging.INFO)

def cmdLineOptionExtender(parser, *args, **kwargs):
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "Serializer",
                                           "This plugin will create a Taxonomy Package. ")
        parser.add_option_group(parserGroup)
    
    parserGroup.add_option('--serializer-package-taxonomy-package',
                            action='store',
                            help="The name of the taxonomyPackage.xml file to use in the package.")

    parserGroup.add_option('--serializer-package-identifier',
                           help='Package identifier')
    
    parserGroup.add_option('--serializer-package-name',
                           help="The name of the taxonomy package file to create.")
    
    parserGroup.add_option('--serializer-package-meta-name',
                           help="The name of the taxonomy in the taxonomy package meta inf.")

    parserGroup.add_option('--serializer-package-meta-name_language',
                           help="The language of the taxonomy name in the taxonomy package meta inf.")

    parserGroup.add_option('--serializer-package-version',
                         help="The version to create in the pacakge.")

    parserGroup.add_option('--serializer-package-description',
                           help='Package description')

    parserGroup.add_option('--serializer-package-description-language',
                           help='Package description language')

    parserGroup.add_option('--serializer-package-license-href',
                           help='Package license href')

    parserGroup.add_option('--serializer-package-license-name',
                           help='Package license name')

    parserGroup.add_option('--serializer-package-publisher',
                           help='Package publisher')
    
    parserGroup.add_option('--serializer-package-publisher-language',
                           help='Package publisher language')

    parserGroup.add_option('--serializer-package-publisher-url',
                           help='Package publisher url')

    parserGroup.add_option('--serializer-package-country',
                           help='Package publisher country')

    parserGroup.add_option('--serializer-package-date',
                           help='Package publisher date')

    parserGroup.add_option('--serializer-package-rewrite',
                           action='append', 
                           help='Package rewrite in the form of "{prefix} {start string}". '
                                'There can be multiple.')

    parserGroup.add_option('--serializer-has-relationship-location',
                            type="choice",
                            choices=("segment", "scenario"),
                            default="segment", 
                            help="Either segment or scenario. Segment is the default. Identifies the location for all and notAll dimensonal relationships")
    
    parserGroup.add_option('--serializer-package-allow-errors',
                           action='store_true',
                           help='Allow errors and continue processing')


def  cmdUtilityRun(cntlr, options, **kwargs): 
    '''
    The entrypoint file (-f option) will be a directory of the taxonomy files.
    '''
    global taxonomy_package_file_name
    global catalog_file_name
    global new_version

    global _CNTLR
    _CNTLR = cntlr

    # Get the Simple XBRL Model Module.
    global _SXM
    _SXM = getPluginObject(cntlr, 'SimpleXBRLModel', 'SXM.getModule')()

    parser = optparse.OptionParser()

    new_version = options.serializer_package_version

    # Check if a name is supplied.
    if options.serializer_package_name is None:
        parser.error("--serializer-package-name is required. This is the name of the taxonomy package to create.")

    # Check if supplied taxonomy package exists
    if options.serializer_package_taxonomy_package is not None:
        if os.path.isfile(options.serializer_package_taxonomy_package):
            taxonomy_package_file_name = os.path.join(options.serializer_package_taxonomy_package)
        else:
            parser.error("Supplied taxonomy package file name (--serializer-package-taxonomy-package) does not exist '{}'".format(options.serializer_package_taxonomy_package))
    
    # # Check if an entry point file is supplied, if not get it from the package
    # if options.entrypointFile is None:
    #     # Find the taxonomyPackage.xml file and get the entry point from there.
    #     if len(PackageManager.packagesConfig['packages']) > 0:
    #         # open up the taxonomy package 
    #         package_fs = FileSource.openFileSource(PackageManager.packagesConfig['packages'][0]['URL'], cntlr)
    #         metadataFiles = package_fs.taxonomyPackageMetadataFiles
    #         metadataFile = metadataFiles[0]
    #         metadata = package_fs.url + os.sep + metadataFile
    #         taxonomy_package = PackageManager.parsePackage(cntlr, package_fs, metadata,
    #                                         os.sep.join(os.path.split(metadata)[:-1]) + os.sep)
            
    #         if taxonomy_package['entryPoints'] and len(taxonomy_package['entryPoints']) > 0:
    #             # Get the first entry point, there really should only be one
    #             first_key = list(taxonomy_package['entryPoints'].keys())[0]
    #             entry_point = taxonomy_package['entryPoints'][first_key][0][1] # the [1] is the url of the entry point
    #             options.entrypointFile = entry_point
    #             cntlr.addToLog("Using entry point {}".format(entry_point), "info")
    #         else:
    #             cntlr.addToLog("Cannot determine entry point for supplied package", "error")
    #             raise SerializerException
    #     else:
    #         cntlr.addToLog("Cannot determine entry point for supplied package", "error")
    #         raise SerializerException

def cmndLineXbrlRun(cntlr, options, model_xbrl, entryPoint, *args, **kwargs):
    # Multiple serializer methods may be used. Serialize for each one. Find them by looking at the plugins that
    # have been used. Look for the 'serializer.serialize' entry.
    # Call the serialize method in the serializer method module. This will return a dictionary
    # of documents to create
    global _OPTIONS
    _OPTIONS = options
    global _PACKAGE_FOLDER
    _PACKAGE_FOLDER = os.path.splitext(os.path.basename(options.serializer_package_name))[0]

    for serializer in getSerizlierPlugins(cntlr):
        dts = serializer['serializer.serialize'](model_xbrl, options, _SXM)
        write(dts, options.serializer_package_name or 'taxonomy_package.zip', cntlr)

def write(dts, package_name, cntlr):

    with zipfile.ZipFile(package_name, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for document in dts.documents.values():
            if document.is_relative:
                contents = serialize_document(document)
                z.writestr(os.path.join(_PACKAGE_FOLDER, document.uri), contents)
        serialize_package_files(z, dts)
    info("Writing package {}".format(package_name))

def verify(document):
    '''Verify that the contents are allowed for the type of the document'''
    # save the messages for debugging
    has_errors = False
    if document.document_type == document.DOCUMENT_TYPES.LINKBASE:
        for schema_import in document._imports:
            warning("Import {} is not allowed in a linkbase".format(schema_import.document_uri))
            has_errors = True
    if document.document_type == document.DOCUMENT_TYPES.SCHEMA:
        if document.target_namespace is None:
            warning("Schema documents need a target namespace")
            has_errors = True
    for content in document.contents:
        try:
            if not document.document_type in document.ALLOWED_DOCUMENT_CONTENT[content.get_class_name()]:
                warning("Component of type {} is not allowed in a {} document".format(content.get_class_name(), document.document_type))
                has_errors = True
        except KeyError:
            warning("Component of type {} is not allowed in a {} document".format(content.get_class_name(), document.document_type))
            has_errors = True

    return not has_errors

def serialize_document(document, serialization_type='xml'):
    if serialization_type not in _SERIALIZATION_TYPES:
        raise SerializerException("Invalid serialization type. Found '{}'".format(serialization_type))

    if not verify(document):
        raise SerializerException("Document contains invalid content")

    # there is only a serialization type of xml, so don't need to check
    if document.document_type == document.DOCUMENT_TYPES.LINKBASE:
        return serialize_linkbase(document)
    elif document.document_type == document.DOCUMENT_TYPES.SCHEMA:
        return serialize_schema(document)
    else:
        return '' # there is nothing serialization

def serialize_linkbase(document):
    namespaces = _STANDARD_LINKBASE_NS.copy()

    linkbase = etree.Element(_LINKBASE,
                             nsmap=namespaces.ns_by_prefix)
    # There can be 2 kinds of content, resource (labels and references) and relationships
    # Organize the relationships by network
    networks = dict()
    resources = dict()
    cubes = dict()

    for content in document.contents:
        # Add any role refs or arcrole refs that are needed
        if isinstance(content, _SXM.SXMRelationship):
            if content.network not in networks:
                extended_link = etree.Element(content.network.link_name.clark, 
                                    {'{{{}}}role'.format(namespaces.namespace('xlink')): content.network.role.role_uri,
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'extended'},
                                    nsmap=namespaces.ns_by_prefix)
                networks[content.network] = (extended_link, collections.defaultdict(list),)
            extended_link, locators = networks[content.network]
            serialize_relationship(extended_link, locators, content, namespaces, document)
            # Make sure the role has a roleref
            document.add(content.network.role, content.DOCUMENT_CONTENT_TYPES.ROLE_REF)
            # Make sure the preferred label role has a role ref
            if content.preferred_label is not None:
                document.add(content.preferred_label)
            # Make sure the arcrole has an arcroleref
            document.add(content.network.arcrole, content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
        if isinstance(content, _SXM.SXMResource):
            if content.get_class_name() not in resources:
                extended_link_name = _RESOURCE_LINKBASES[content.get_class_name()]['extended_link']

                extended_link = etree.Element(extended_link_name,
                                    {'{{{}}}role'.format(namespaces.namespace('xlink')): 'http://www.xbrl.org/2003/role/link',
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'extended'},
                                    nsmap=namespaces.ns_by_prefix)
                resources[content.get_class_name()] = (extended_link, dict(), set())
            extended_link, locators, arcs = resources[content.get_class_name()]
            serialize_resource(extended_link, locators, arcs, content, namespaces, document)
            # Make sure the resource role and arcrole has a reference
            document.add(content.role, content.DOCUMENT_CONTENT_TYPES.ROLE_REF)
        if isinstance(content, _SXM._SXMCubePart):
            if content.role not in cubes:
                extended_link = etree.Element(_DEFINITION_LINKBASE, 
                                    {'{{{}}}role'.format(namespaces.namespace('xlink')): content.role.role_uri,
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'extended'},
                                    nsmap=namespaces.ns_by_prefix)
                cubes[content.role] = (extended_link, collections.defaultdict(list))
            extended_link, locators = cubes[content.role]
            serialize_cube(extended_link, locators, content, namespaces, document)
            # Primaries have to be handled differently because of their roles. They are processed when the cube is processed
            if isinstance(content, _SXM.SXMCube):
                for primary in content.primary_items:
                    if primary.role != content.role: 
                        # the primary is target-role into the cube role. Also put the cube in the role of the primary
                        extended_link = etree.Element(_DEFINITION_LINKBASE, 
                                    {'{{{}}}role'.format(namespaces.namespace('xlink')): primary.role,
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'extended'},
                                    nsmap=namespaces.ns_by_prefix)
                        cubes[primary.role] = (extended_link, dict())
                        # add role ref
                        document.add(primary.role, primary.DOCUMENT_CONTENT_TYPES.ROLE_REF)
                    # else (primary.role == content.role) The extended link is already created when the cube was created.
                    extended_link, locators = cubes[primary.role]
                    serialize_cube(extended_link, locators, content, namespaces, document, primary_role=primary.role)
            # Make sure the role has a ref
            document.add(content.role, content.DOCUMENT_CONTENT_TYPES.ROLE_REF)

        # Add arcrole refs for dimensions
        if isinstance(content, _SXM.SXMCube):
            if len(content.dimensions) > 0:
                document.add(get_dimension_arc(content.dts, 'hypercube-dimension'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
            if len(content.primary_items) > 0:
                document.add(get_dimension_arc(content.dts, 'all'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
        if isinstance(content, _SXM.SXMPrimary):
            if len(content.children) > 0:
                document.add(get_dimension_arc(content.dts, 'domain-member'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
        if isinstance(content, _SXM.SXMDimension):
            if len(content.children) > 0:
                document.add(get_dimension_arc(content.dts, 'dimension-domain'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
            if content.default is not None:
                document.add(get_dimension_arc(content.dts, 'dimension-default'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)
        if isinstance(content, _SXM.SXMMember):
            if len(content.children) > 0 :
                document.add(get_dimension_arc(content.dts, 'domain-member'), content.DOCUMENT_CONTENT_TYPES.ARCROLE_REF)

    # Add role and arcrole refs
    for role in document.role_refs:
        if not role.is_standard:
            href = create_href(role, document)
            role_ref = etree.Element(_ROLE_REF,
                                    {'roleURI': role.role_uri,
                                    '{{{}}}href'.format(namespaces.namespace('xlink')): href,
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'simple'},
                                    nsmap=namespaces.ns_by_prefix)
            linkbase.append(role_ref)
    for arcrole in document.arcrole_refs:
        if not arcrole.is_standard:
            href = create_href(arcrole, document)
            arcrole_ref = etree.Element(_ARCROLE_REF,
                                    {'arcroleURI': arcrole.arcrole_uri,
                                    '{{{}}}href'.format(namespaces.namespace('xlink')): href,
                                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'simple'},
                                    nsmap=namespaces.ns_by_prefix)
            linkbase.append(arcrole_ref)

    # Add all the extended links
    for extended_link, _locators in networks.values():
        linkbase.append(extended_link)
    for extended_link, _locators, _arcs in resources.values():
        linkbase.append(extended_link)
    for extended_link, _locators in cubes.values():
        linkbase.append(extended_link)

    # Add schemaLocation to the linkbase. This is done at the end because reference parts
    # may have added namespaces to inlcude
    linkbase.set('{{{}}}schemaLocation'.format(namespaces.namespace('xsi')), namespaces.schema_locations(document))

    etree.cleanup_namespaces(linkbase, namespaces.ns_by_prefix, namespaces.ns_by_prefix.keys())
    return etree.tostring(linkbase, pretty_print=True)

def serialize_relationship(extended_link, locators, rel, namespaces, document):
    
    if rel.from_concept not in locators:
        from_locator, from_label = create_locator(rel.from_concept, document, namespaces)
        locators[rel.from_concept].append(from_label)
        extended_link.append(from_locator)
    else:
        from_label = locators[rel.from_concept][0]

    if rel.to_concept not in locators:
        suffix = None
    else:
        suffix = len(locators[rel.to_concept])
    to_locator, to_label = create_locator(rel.to_concept, document, namespaces, suffix)
    locators[rel.to_concept].append(to_label)
    extended_link.append(to_locator)
    
    arc_attributes = {'{{{}}}arcrole'.format(namespaces.namespace('xlink')): rel.network.arcrole.arcrole_uri,
                    '{{{}}}type'.format(namespaces.namespace('xlink')): 'arc',
                    '{{{}}}from'.format(namespaces.namespace('xlink')): from_label,
                    '{{{}}}to'.format(namespaces.namespace('xlink')): to_label
                    }
    if rel.order is not None:
        arc_attributes['order'] = str(rel.order)
    if rel.weight is not None:
        arc_attributes['weight'] = str(rel.weight)
    if rel.preferred_label is not None:
        arc_attributes['preferredLabel'] = rel.preferred_label.role_uri
    if rel.attributes is not None:
        arc_attributes.update({k.clark: v for k, v in rel.attributes.items()})
        
    arc = etree.Element(rel.network.arc_name.clark,
                        arc_attributes,
                        nsmap=namespaces.ns_by_prefix)
    
    extended_link.append(arc)

def serialize_resource(extended_link, locators, arcs, resource, namespaces, document):
    resource_type = resource.get_class_name()

    resource_xlink_label = 'lbl_{}_{}_{}'.format(resource_type[:3].lower(),
                                        resource.concept.name.prefix, 
                                        resource.concept.name.local_name)
    # Create the resource
    resource_attributes = {'{{{}}}role'.format(namespaces.namespace('xlink')): resource.role.role_uri,
                            '{{{}}}type'.format(namespaces.namespace('xlink')): 'resource',
                            '{{{}}}label'.format(namespaces.namespace('xlink')): resource_xlink_label}
    if resource_type == 'Label':
        resource_attributes['{http://www.w3.org/XML/1998/namespace}lang'] = resource.language
    if resource.attributes is not None:
        resource_attributes.update(resource.attributes)

    resource_node = etree.Element(_RESOURCE_LINKBASES[resource_type]['resource'],
                                    resource_attributes,
                                    nsmap=namespaces.ns_by_prefix)
                                    
    #content
    if resource_type == 'Label':
        resource_node.text = resource.content
    elif resource_type == 'Reference':
        for part in resource.parts:
            # Make sure the part namespace is in the document
            namespaces.get_or_add_prefix(part.part_element.name.namespace, part.part_element.document.uri)
            part_node = etree.Element(part.part_element.name.clark, nsmap=namespaces.ns_by_prefix)
            part_node.text = part.content
            resource_node.append(part_node)

    # locator if needed
    if resource.concept not in locators:
        locator, from_label = create_locator(resource.concept, document, namespaces)
        locators[resource.concept] = from_label
        extended_link.append(locator)
        # create arc. All the resources for the same concept will have the same resource label, so only one arc is needed
    else:
        from_label = locators[resource.concept]
    
    # arc
    if resource.concept not in arcs:
        # The arc only has to be outputted once because the xlink:label for the resource is reused for each resource
        arc_attributes = {'{{{}}}arcrole'.format(namespaces.namespace('xlink')): _RESOURCE_LINKBASES[resource_type]['arcrole'],
                '{{{}}}type'.format(namespaces.namespace('xlink')): 'arc',
                '{{{}}}from'.format(namespaces.namespace('xlink')): from_label,
                '{{{}}}to'.format(namespaces.namespace('xlink')): resource_xlink_label
                }

        arc = etree.Element(_RESOURCE_LINKBASES[resource_type]['arc'],
                            arc_attributes,
                            nsmap=namespaces.ns_by_prefix)
        extended_link.append(arc)
        arcs.add(resource.concept)

    extended_link.append(resource_node)

def serialize_cube(extended_link, locators, cube_part, namespaces, document, primary_role=None):
    # The primary_role indicates that the all relationship of the primary is in a different role
    # than the role of the cube. This is processing the cube in the alternate role and the relationship
    # will have a target role that matches the cube role.

    if isinstance(cube_part, _SXM.SXMCube):
        if primary_role is None: # if not, the dimension are added in this role
            children_by_arc = (cube_part.dimensions,[])
        else:
            children_by_arc = ([],)
        # primaries in a different role than the cube, will be in a different extended link.
        for primary in cube_part.primary_items:
            if primary_role is None and cube_part.role == primary.role:
                children_by_arc[1].append(primary)
            elif cube_part.role != primary.role and primary.role == primary_role:
                children_by_arc[0].append(primary)
    else:
        children_by_arc = (cube_part.children,)
    
    for children in children_by_arc:
        for count, child in enumerate(children, start=1):
            if cube_part.concept not in locators:
                from_locator, from_label = create_locator(cube_part.concept, document, namespaces)
                locators[cube_part.concept].append(from_label)
                extended_link.append(from_locator)
            else:
                from_label = locators[cube_part.concept][0]

            if child.concept not in locators:
                suffix = None
            else:
                suffix = len(locators[child.concept])
            to_locator, to_label = create_locator(child.concept, document, namespaces, suffix)
            locators[child.concept].append(to_label)
            extended_link.append(to_locator)
            
            arc_role = _DIMENSION_ARCROLES[_DIMENSION_ARC_BY_ENDS[(cube_part.get_class_name(), child.get_class_name())]][0]

            arc_attributes = {'{{{}}}arcrole'.format(namespaces.namespace('xlink')): arc_role,
                            '{{{}}}type'.format(namespaces.namespace('xlink')): 'arc',
                            '{{{}}}from'.format(namespaces.namespace('xlink')): from_label if child.get_class_name() != 'Primary' else to_label,
                            '{{{}}}to'.format(namespaces.namespace('xlink')): to_label if child.get_class_name() != 'Primary' else from_label,
                            'order': str(count)
                            }
            if arc_role == 'http://xbrl.org/int/dim/arcrole/all':
                # add the contextElement attribute
                arc_attributes[_CONTEXT_ELEMENT_ATTRIBUTE] = _OPTIONS.serializer_has_relationship_location
                namespaces.get_or_add_prefix(_DIMENSION_NAMESPACE)

            if child.attributes is not None:
                arc_attributes.update({k.clark: v for k, v in child.attributes.items()})
                
            arc = etree.Element(_DEFINITION_ARC,
                                arc_attributes,
                                nsmap=namespaces.ns_by_prefix)

            extended_link.append(arc)

            # Add the dimension default
            if cube_part.get_class_name() == 'Dimension' and cube_part.default is not None:
                if cube_part.default.concept not in locators:
                    suffix = None
                else:
                    suffix = len(locators[cube_part.default.concept])
                to_locator, to_label = create_locator(cube_part.default.concept, document, namespaces, suffix)
                locators[cube_part.default.concept].append(to_label)
                extended_link.append(to_locator)

                arc_role = _DIMENSION_ARCROLES['dimension-default'][0]

                arc_attributes = {'{{{}}}arcrole'.format(namespaces.namespace('xlink')): arc_role,
                                '{{{}}}type'.format(namespaces.namespace('xlink')): 'arc',
                                '{{{}}}from'.format(namespaces.namespace('xlink')): from_label,
                                '{{{}}}to'.format(namespaces.namespace('xlink')): to_label,
                                'order': '1'
                                }

                arc = etree.Element(_DEFINITION_ARC,
                                    arc_attributes,
                                    nsmap=namespaces.ns_by_prefix)
            
                extended_link.append(arc)
         
def create_locator(concept, document, namespaces, suffix=None):
    label = '{}_{}{}'.format(concept.name.prefix, concept.name.local_name, '' if suffix is None else '_{}'.format(str(suffix)))
    href = create_href(concept, document)
    locator = etree.Element('{{{}}}loc'.format(namespaces.namespace('link')),
                            {'{{{}}}label'.format(namespaces.namespace('xlink')): label,
                            '{{{}}}href'.format(namespaces.namespace('xlink')): href, 
                             '{{{}}}type'.format(namespaces.namespace('xlink')): 'locator'},
                            nsmap=namespaces.ns_by_prefix)

    return locator, label

def create_href(component, start_document):
    if component.document is start_document:
        href_base = ''
    elif component.document.is_absolute:
        href_base = component.document.uri
    else:
        href_base = os.path.relpath(component.document.uri, start=os.path.dirname(start_document.uri))
    
    return '{}#{}'.format(href_base, component.id)

def get_dimension_arc(dts, name):
    if name not in _DIMENSION_ARC_COMPONENTS:
        usedon = (dts.new('QName', 'http://www.xbrl.org/2003/linkbase', 'defintionArc', 'xbrldt'),)
        arc = dts.new('Arcrole', _DIMENSION_ARCROLES[name][0], _DIMENSION_ARCROLES[name][1], _DIMENSION_ARCROLES[name][2], usedon)
        _DIMENSION_ARC_COMPONENTS[name] = arc
        dimension_document = dts.get('Document', _DIMENSION_URI) or dts.new('Document', _DIMENSION_URI, dts.DOCUMENT_TYPES.SCHEMA, _DIMENSION_NAMESPACE)
        dimension_document.add(arc)
    return _DIMENSION_ARC_COMPONENTS[name]

def serialize_schema(document):
    namespaces = _STANDARD_NS.copy()
    namespaces.get_or_add_prefix(document.target_namespace)

    schema_attributes = {'targetNamespace': document.target_namespace,
                         'elementFormDefault': 'qualified',
                         'attributeFormDefault': 'unqualified'}

    schema = etree.Element(_SCHEMA,
                           schema_attributes,
                           nsmap=namespaces.ns_by_prefix)

    needed_namespaces = set() # tracks namespaces that will need to be imported or schemaLocation

    arcroles = set()
    roles = set()
    types = set()
    concepts = set()
    elements = set()

    # Go through the contents
    for content in document.contents:
        if isinstance(content, _SXM.SXMType):
            if not content.is_anonymous:
                type_node, add_namespaces = serialize_xml_content(content, namespaces)
                types.add(type_node)
                needed_namespaces |= add_namespaces
        elif isinstance(content, _SXM.SXMConcept):
            concept_node, add_namespaces = serialize_concept(content, namespaces)
            concepts.add(concept_node)
            needed_namespaces |= add_namespaces
        elif isinstance(content, _SXM.SXMElement): # This will pick up PartElements and TypedDomains because they inherit from Element
            element_node, add_namespaces = serialize_element(content, namespaces)
            elements.add(element_node)
            needed_namespaces |= add_namespaces
        elif isinstance(content, _SXM.SXMArcrole):
            arcrole_element, add_namespaces = serialize_arcrole(content, namespaces)
            arcroles.add(arcrole_element)
            needed_namespaces |= add_namespaces
        elif isinstance(content, _SXM.SXMRole):
            role_element, add_namespaces = serialize_role(content, namespaces)
            roles.add(role_element)
            needed_namespaces |= add_namespaces

    if (len(document.linkbase_refs) + len(roles) + len(arcroles) > 0) or document.description is not None:
        annotation_element = etree.Element(_ANNOTATION_ELEMENT, nsmap=namespaces.ns_by_prefix)
        schema.append(annotation_element)
        if document.description is not None:
            description_element = etree.Element(_DOCUMENTATION_ELEMENT, nsmap=namespaces.ns_by_prefix)
            description_element.text = document.description
            annotation_element.append(description_element)
        if (len(document.linkbase_refs) + len(roles) + len(arcroles) > 0):
            app_info_element = etree.Element(_APP_INFO_ELEMENT, nsmap=namespaces.ns_by_prefix)
            annotation_element.append(app_info_element)
            for linkbase in sorted(document.linkbase_refs, key=lambda x: x.uri):
                app_info_element.append(serialize_linkbase_ref(linkbase, document, namespaces))
            for arcrole in sorted(arcroles, key=lambda x: x.get('arcroleURI')):
                app_info_element.append(arcrole)
            for role in sorted(roles, key=lambda x: x.get('roleURI')):
                app_info_element.append(role)

    # add imports for namespaces that were added from the contents
    for namespace in needed_namespaces:
        namespaces.get_or_add_prefix(namespace)
        for potential_import in document.dts.documents.values():
            if potential_import.target_namespace == namespace:
                document.add(potential_import, document.DOCUMENT_CONTENT_TYPES.IMPORT)
                break
    
    # Add imports
    for import_ref in sorted(document.imports, key=lambda x: x.uri):
        if import_ref is not document:
            schema.append(serialize_import(import_ref, document, namespaces))

    for concept_node in sorted(concepts, key=lambda x: x.get('name')):
        schema.append(concept_node)
    for element_node in sorted(elements, key=lambda x: x.get('name')):
        schema.append(element_node)
    for type_node in sorted(types, key=lambda x: x.get('name')):
        schema.append(type_node)

    etree.cleanup_namespaces(schema, namespaces.ns_by_prefix, namespaces.ns_by_prefix.keys())
    return etree.tostring(schema, pretty_print=True)

def serialize_xml_content(new_type, namespaces):
    type_element = etree.fromstring(new_type.content)
    #etree.cleanup_namespaces(type_element)
    # Find needed namespaces
    if not new_type.is_anonymous: # anonymous types don't have ids
        type_element.set('id', new_type.document.get_id(new_type))
    return type_element, find_needed_namespaces(type_element)

def serialize_element(new_element, namespaces):
    needed_namespaces = set()
    element_node = etree.Element(_ELEMENT, nsmap=namespaces.ns_by_prefix)
    element_node.set('name', new_element.name.local_name)
    element_node.set('id', new_element.document.get_id(new_element))

    if not new_element.type.is_anonymous:
        element_node.set('type', namespaces.get_qname(*new_element.type.name.name_pair))
        needed_namespaces.add(new_element.type.name.namespace)
    else:
        # the type is anonymous. It should be added as a child of the element
        type_element, add_namespaces = serialize_xml_content(new_element.type, namespaces)
        element_node.append(type_element)
        needed_namespaces |= add_namespaces
    if new_element.is_abstract:
        element_node.set('abstract', 'true')
    if new_element.nillable:
        element_node.set('nillable', 'true')
    if new_element.substitution_group is not None:
        element_node.set('substitutionGroup', namespaces.get_qname(*new_element.substitution_group_name.name_pair))
        needed_namespaces.add(new_element.substitution_group_name.namespace)
    for att_name, att_value in new_element.attributes.items():
        if att_name.clark in (_PERIOD_ATTRIBUTE, _BALANCE_ATTRIBUTE, _TYPED_DOMAIN_REF_ATTRIBUTE):
            continue # Skip these
        if att_name.namespace is not None:
            # This will be problematic for attribute names that have a namespace prefix. Throwing a warning for now
            warning('Attribute {} has a prefix, but the serializer may not be able to create the namespace properly'.format(att_name))
        element_node.set(att_name.clark, att_value)
    
    return element_node, needed_namespaces

def serialize_concept(new_concept, namespaces):
    concept_node, needed_namespaces = serialize_element(new_concept, namespaces)
    # now add the concept attributes
    concept_node.set(_PERIOD_ATTRIBUTE, new_concept.period_type)
    if new_concept.balance_type is not None:
        concept_node.set(_BALANCE_ATTRIBUTE, new_concept.balance_type)
    if new_concept.typed_domain is not None:
        href = create_href(new_concept.typed_domain, new_concept.document)
        concept_node.set(_TYPED_DOMAIN_REF_ATTRIBUTE, href)
        needed_namespaces.add(_DIMENSION_NAMESPACE)
        needed_namespaces.add(new_concept.typed_domain.name.namespace)

    return concept_node, needed_namespaces

def find_needed_namespaces(node):
    '''Find and attributes that reference a namespace that is needed in an xml node or its descendents'''
    namespaces = set()
    for n in node.iter():
        if etree.QName(n.tag).namespace == _SCHEMA_NAMESPACE:
            for att_name, att_value in n.items():
                if att_name in ('ref', 'type', 'base', 'substitutionGroup', 'refer'): # These attributes are qnames in schema
                    namespace_to_add = namespace_from_text_qname(n, att_value)
                    if namespace_to_add is None:
                        raise SerializerException("Cannot get namespace for {}".format(att_value))
                    else:
                        namespaces.add(namespace_to_add)
                    
    return namespaces

def namespace_from_text_qname(node, val):
    if ':' in val:
        prefix, _local_name = val.split(':')
    else:
        prefix = None

    for ns_prefix, namespace in node.nsmap.items():
        if ns_prefix == prefix:
            return namespace

def serialize_arcrole(new_arcrole, namespaces):
    needed_namespaces = set()
    arcrole_element = etree.Element(_ARCROLE_TYPE,
                                    {'arcroleURI': new_arcrole.arcrole_uri,
                                     'cyclesAllowed': new_arcrole.cycles_allowed,
                                     'id': new_arcrole.id},
                                    nsmap=namespaces.ns_by_prefix)
    if new_arcrole.description is not None:
        definition = etree.Element(_ROLE_DEFINITION, nsmap=namespaces.ns_by_prefix)
        definition.text = new_arcrole.description
        arcrole_element.append(definition)
    for usedon in new_arcrole.used_ons:
        usedon_element = etree.Element(_USEDON_ELEMENT, nsmap=namespaces.ns_by_prefix)
        usedon_element.text = '{}:{}'.format(namespaces.get_or_add_prefix(usedon.namespace), usedon.local_name)
        arcrole_element.append(usedon_element)
        needed_namespaces.add(usedon.namespace)
    
    return arcrole_element, needed_namespaces

def serialize_role(new_role, namespaces):
    needed_namespaces = set()
    role_element = etree.Element(_ROLE_TYPE,
                                 {'roleURI': new_role.role_uri,
                                  'id': new_role.id},
                                  nsmap=namespaces.ns_by_prefix)
    if new_role.description is not None:
        definition = etree.Element(_ROLE_DEFINITION, nsmap=namespaces.ns_by_prefix)
        definition.text = new_role.description
        role_element.append(definition)
    for usedon in new_role.used_ons:
        usedon_element = etree.Element(_USEDON_ELEMENT, nsmap=namespaces.ns_by_prefix)
        usedon_element.text = '{}:{}'.format(namespaces.get_or_add_prefix(usedon.namespace), usedon.local_name)
        role_element.append(usedon_element)
        needed_namespaces.add(usedon.namespace)
    
    return role_element, needed_namespaces

def serialize_linkbase_ref(new_linkbase, document, namespaces):
    if new_linkbase.is_absolute:
        href = new_linkbase.uri
    else:
        href = os.path.relpath(new_linkbase.uri, start=os.path.dirname(document.uri))
    linkbase_ref_element = etree.Element(_LINKBASE_REF_ELEMENT,
                           {'{http://www.w3.org/1999/xlink}href': href,
                            '{http://www.w3.org/1999/xlink}arcrole': 'http://www.w3.org/1999/xlink/properties/linkbase',
                            '{http://www.w3.org/1999/xlink}type': 'simple'},
                            nsmap=namespaces.ns_by_prefix)
    return linkbase_ref_element

def serialize_import(new_import_document, document, namespaces):
    if new_import_document.is_absolute:
        href = new_import_document.uri
    else:
        href = os.path.relpath(new_import_document.uri, start=os.path.dirname(document.uri))
    import_element = etree.Element(_IMPORT,
                                   {'namespace': new_import_document.target_namespace,
                                    'schemaLocation': href},
                                    nsmap=namespaces.ns_by_prefix)
    return import_element

def serialize_package_files(zip_file, dts):
    folder_name = 'META-INF'
    # taxonomy_package
    namespaces = _TAXONOMY_PACKAGE_NS.copy()

    package = etree.Element('{http://xbrl.org/2016/taxonomy-package}taxonomyPackage', nsmap=namespaces.ns_by_prefix)
    add_package_element(package, dts, 'identifier', 'serializer_package_identifier', 
                        '{http://xbrl.org/2016/taxonomy-package}identifier', namespaces)
    name_element = add_package_element(package, dts, 'name', 'serializer_package_meta_name', 
                        '{http://xbrl.org/2016/taxonomy-package}name', namespaces)
    if name_element is not None:
        # add the language
        # english is the default. 
        name_element.set('{http://www.w3.org/XML/1998/namespace}lang', _OPTIONS.serializer_package_meta_name_language or dts.name_language or 'en')

    description_element = add_package_element(package, dts, 'description', 'serializer_package_description', 
                        '{http://xbrl.org/2016/taxonomy-package}description', namespaces)
    # add description language
    if (description_element is not None and
        (_OPTIONS.serializer_package_description_language is not None or dts.description_language is not None)):
        description_element.set('{http://www.w3.org/XML/1998/namespace}lang', _OPTIONS.serializer_package_description_language or dts.description_language or 'en')

    add_package_element(package, dts, 'version', 'serializer_package_version', 
                        '{http://xbrl.org/2016/taxonomy-package}version', namespaces)
    # License
    if (_OPTIONS.serializer_package_license_href is not None or 
        dts.license_href is not None or
        _OPTIONS.serializer_package_license_name is not None or
        dts.license_name is not None):
        license_element = etree.Element('{http://xbrl.org/2016/taxonomy-package}license', nsmap=namespaces.ns_by_prefix)
        if (_OPTIONS.serializer_package_license_href is not None or 
            dts.license_href is not None):
            license_element.set('href', _OPTIONS.serializer_package_license_href or dts.license_href)
        if (_OPTIONS.serializer_package_license_name is not None or
            dts.license_name is not None):
            license_element.set('name', _OPTIONS.serializer_package_license_name or dts.license_name)

    publisher_element = add_package_element(package, dts, 'publisher', 'serializer_package_publisher', 
                        '{http://xbrl.org/2016/taxonomy-package}publisher', namespaces)
    if publisher_element is not None:
            publisher_element.set('{http://www.w3.org/XML/1998/namespace}lang', _OPTIONS.serializer_package_publisher_language or dts.publisher_language or 'en')

    add_package_element(package, dts, 'publisher_url', 'serializer_package_publisher_url', 
                        '{http://xbrl.org/2016/taxonomy-package}publisherURL', namespaces)
    add_package_element(package, dts, 'publisherCountry', 'serializer_package_publisher_country', 
                        '{http://xbrl.org/2016/taxonomy-package}publisherCountry', namespaces)
    add_package_element(package, dts, 'publication_date', 'serializer_package_publication_date', 
                        '{http://xbrl.org/2016/taxonomy-package}publicationDate', namespaces)

    # entry points
    if len(dts.entry_points) > 0:
        entry_points_element = etree.Element('{http://xbrl.org/2016/taxonomy-package}entryPoints', nsmap=namespaces.ns_by_prefix)
        package.append(entry_points_element)
        for entry_point in dts.entry_points.values():
            entry_point_element = etree.Element('{http://xbrl.org/2016/taxonomy-package}entryPoint', nsmap=namespaces.ns_by_prefix)
            entry_points_element.append(entry_point_element)
            for name, lang in entry_point.names:
                name_element = add_entry_point_detail(entry_point_element, name, 'name', namespaces, lang)
            add_entry_point_detail(entry_point_element, entry_point.description, 'description', namespaces, entry_point.description_language)
            add_entry_point_detail(entry_point_element, entry_point.version, 'version', namespaces)
            for document in entry_point.documents:
                if document.is_absolute:
                    document_uri = document.uri
                else:
                    document_start = dts.rewrites.get('../')
                    if document_start is None:
                        document_start = ''
                    document_uri = os.path.join(document_start, document.uri)
                doc_element = add_entry_point_detail(entry_point_element, '', 'entryPointDocument', namespaces)
                doc_element.set('href', document_uri)

            for name, val in entry_point.other_elements.items():
                namespaces.get_or_add_prefix(name.namespace)
                child_element = etree.Element(name.clark, nsmap=namespaces.ns_by_prefix) 
                child_element.text = val
                entry_point_element.append(child_element)

    # Write the taxonomy package file
    etree.cleanup_namespaces(package, namespaces.ns_by_prefix, namespaces.ns_by_prefix.keys())
    taxonomy_package_file_name = '{}/{}/{}'.format(_PACKAGE_FOLDER, folder_name, 'taxonomyPackage.xml')
    zip_file.writestr(taxonomy_package_file_name, etree.tostring(package, pretty_print=True))

    # Catalog file
    if len(dts.rewrites) > 0:
        namespaces = _CATALOG_NS.copy()
        catalog_element = etree.Element('{urn:oasis:names:tc:entity:xmlns:xml:catalog}catalog', nsmap=namespaces.ns_by_prefix)
        for prefix, start_string in dts.rewrites.items():
            child_element = etree.Element('{urn:oasis:names:tc:entity:xmlns:xml:catalog}rewriteURI', nsmap=namespaces.ns_by_prefix)
            child_element.set('rewritePrefix', prefix)
            child_element.set('uriStartString', start_string)
            catalog_element.append(child_element)
        
        etree.cleanup_namespaces(catalog_element, namespaces.ns_by_prefix, namespaces.ns_by_prefix.keys())
        taxonomy_package_file_name = '{}/{}/{}'.format(_PACKAGE_FOLDER, folder_name, 'catalog.xml')
        zip_file.writestr(taxonomy_package_file_name, etree.tostring(catalog_element, pretty_print=True))

def add_entry_point_detail(entry_point_element, val, detail_name, namespaces, language=None):
    if val is not None:
        if detail_name in ('description', 'name') and language is None:
            raise SerializerException("The description element in the taxonomyPagckage.xml requires a language")
        child_element = etree.Element('{{http://xbrl.org/2016/taxonomy-package}}{}'.format(detail_name), nsmap=namespaces.ns_by_prefix)
        child_element.text = val
        if language is not None:
            child_element.set('{http://www.w3.org/XML/1998/namespace}lang', language)
        entry_point_element.append(child_element)
        return child_element

def add_package_element(package, dts, property_name, option_name, element_name, namespaces):
    if getattr(_OPTIONS, option_name, None) is not None or getattr(dts, property_name, None) is not None:
        element = etree.Element(element_name, nsmap=namespaces.ns_by_prefix)
        element.text = getattr(_OPTIONS, option_name, None) or getattr(dts, property_name, None)
        package.append(element)
        return element

__pluginInfo__ = {
    'name': 'XBRL Serializer',
    'version': '01.0',
    'description': "This plug-in organizes the taxonomy files and creates a Taxonomy Package",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'SimpleXBRLModel',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    'CntlrCmdLine.Xbrl.Run': cmndLineXbrlRun,
}
