
import argparse
import collections
import importlib.util
import io
import json
import logging
import optparse
import os
import re
import zipfile

from lxml import etree

from arelle import FileSource, PackageManager, PluginManager
from arelle.CntlrWebMain import Options
from arelle.ModelDocument import ModelDocument
from arelle.ModelDtsObject import ModelResource

_CONFIG = None
_OPTIONS = None
_PLUGINS = {}
_SXM = None
_METHOD_MODULE = None

class PackageException(Exception):
    pass

# Utility to find another plugin
def getserizlierPlugins(cntlr):
    '''Serializer plugins have a 'serializer.serialize' entry in the _PLUGIN dictionary.'''
    serializer_plugins = []
    for _x, plugin_info in PluginManager.modulePluginInfos.items():
        if 'serializer.serialize' in plugin_info:
            serializer_plugins.append(plugin_info)
    
    return serializer_plugins

def getPlugin(cntlr, plugin_name):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
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
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getPlugin(cntlr, plugin_name).get(object_name)


def error(code, msg, model_xbrl):
    global _OPTIONS

    model_xbrl.error(code, msg)
    if not getattr(_OPTIONS, 'serializer_package_allow_errors', False):
        raise PackageException

def cmdLineOptionExtender(parser, *args, **kwargs):
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "Serializer",
                                           "This plugin will create a Taxonomy Package. ")
        parser.add_option_group(parserGroup)

    parserGroup.add_option('--serializer-package-name',
                           help="The name of the taxonomy package file to create.")

    parserGroup.add_option('--serializer-package-version',
                         help="The version to create in the pacakge.")
    parserGroup.add_option('--serializer-package-revision',
                         help="The revision number of the taxonomy.")
    parserGroup.add_option('--serializer-package-meta-inf',
                            action='store',
                            help="The name of the META-INF template folder. The default is 'META-INF-' plus the form name.")
    parserGroup.add_option('--serializer-package-catalog',
                            action='store',
                            help="The name of the catalog.xml file to use in the package.")  
    parserGroup.add_option('--serializer-package-taxonomy-package',
                            action='store',
                            help="The name of the taxonomyPackage.xml file to use in the package.")                                                       
    parserGroup.add_option('--serializer-package-cur-version',
                             action='store',
                             help="The version currently in the taxonomy. This version will be replaced.")

    parserGroup.add_option('--serializer-package-allow-errors',
                           action='store_true',
                           help='Allow errors and continue processing')

    parserGroup.add_option('--serializer-method', 
                            action='store',
                            help="Identifies the code for hte method of serialization.")

def  cmdUtilityRun(cntlr, options, **kwargs): 
    '''
    The entrypoint file (-f option) will be a directory of the taxonomy files.
    '''
    global taxonomy_package_file_name
    global catalog_file_name
    global cur_version
    global new_version

    # Get the Simple XBRL Model Module.
    global _SXM
    _SXM = getPluginObject(cntlr, 'SimpleXBRLModel', 'SXM.getModule')()

    parser = optparse.OptionParser()

    cur_version = options.serializer_package_cur_version
    new_version = options.serializer_package_version

    # Check if a serializer method is supplied
    # if options.serializer_method is None:
    #     parser.error("--serializer-method is required. This supplies the code for how the serializer will organize the taxonomy.")
    # else:
    #     # Load the serializer method code
    #     global _METHOD_MODULE
    #     module_name = os.path.splitext(os.path.basename(options.serializer_method))[0]
    #     module_spec = importlib.util.spec_from_file_location(module_name, options.serializer_method)
    #     if module_spec is None:
    #         cntlr.addToLog("Serializer method {} cannot load.".format(options.serializer_method), "Error", level=logging.ERROR)
    #     else:
    #         try:
    #             _METHOD_MODULE = importlib.util.module_from_spec(module_spec)
    #             module_spec.loader.exec_module(_METHOD_MODULE)
    #         except Exception as e:
    #             cntlr.addToLog("Serializer method {} loads with errors. {}".format(module_spec, str(e)), "Error", level=logging.ERROR)
    #         else:
    #             cntlr.addToLog("Serializer method {} loaded".format(module_name),"Info")
    #             _METHOD_MODULE.x(cntlr)

    # Check if a name is supplied.
    if options.serializer_package_name is None:
        parser.error("--serializer-package-name is required. This is the name of the taxonomy package to create.")

    # --serializer-package-meta-inf is mutually exclusive with --serializer-package-catalog and --serializer-pacakge-taxonomy-package
    if options.serializer_package_meta_inf is not None and options.serializer_package_taxonomy_package is not None:
        parser.error("--serializer-package-meta-inf cannot be used with --serializer-package-taxonomy-package.")

    if options.serializer_package_meta_inf is not None and options.serializer_package_catalog is not None:
        parser.error("--serializer-package-meta-inf cannot be used with --serializer-package-catalog.")

    # Check if supplied files exist:
    if options.serializer_package_meta_inf is not None:
        if os.path.isdir(options.serializer_package_meta_inf):
            if os.path.isfile(os.path.join(options.serializer_package_meta_inf, 'taxonomyPackage.xml')):
                taxonomy_package_file_name = os.path.join(options.serializer_package_meta_inf, 'taxonomyPackage.xml')
            else:
                parser.error("taxonomyPackage.xml does not exist in the supplied meta info folder '{}'.".format(options.serializer_package_meta_inf))
            if os.path.isfile(os.path.join(options.serializer_package_meta_inf, 'catalog.xml')):
                catalog_file_name = os.path.join(options.serializer_package_meta_inf, 'catalog.xml')
        else: # supplied meta-inf folder does not exist
            parser.error("Supplied meta info folder (--serializer-package-meta-inf) does not exist '{}'".format(options.serializer_package_meta_inf))

    # Check if supplied taxonomy package exists
    if options.serializer_package_taxonomy_package is not None:
        if os.path.isfile(options.serializer_package_taxonomy_package):
            taxonomy_package_file_name = os.path.join(options.serializer_package_taxonomy_package)
        else:
            parser.error("Supplied taxonomy package file name (--serializer-package-taxonomy-package) does not exist '{}'".format(options.serializer_package_taxonomy_package))
    
    # Check if supplied catalog file exists
    if options.serializer_package_catalog is not None:
        if os.path.isfile(options.serializer_package_catalog):
            catalog_file_name = os.path.join(options.serializer_package_catalog)
        else:
            parser.error("Supplied catalog file name (--serializer-package-catalog) does not exist '{}'".format(options.serializer_package_catalog))
    
    # Check if an entry point file is supplied, if not get it from the package
    if options.entrypointFile is None:
        # Find the taxonomyPackage.xml file and get the entry point from there.
        if len(PackageManager.packagesConfig['packages']) > 0:
            # open up the taxonomy package 
            package_fs = FileSource.openFileSource(PackageManager.packagesConfig['packages'][0]['URL'], cntlr)
            metadataFiles = package_fs.taxonomyPackageMetadataFiles
            metadataFile = metadataFiles[0]
            metadata = package_fs.url + os.sep + metadataFile
            taxonomy_package = PackageManager.parsePackage(cntlr, package_fs, metadata,
                                            os.sep.join(os.path.split(metadata)[:-1]) + os.sep)
            
            if taxonomy_package['entryPoints'] and len(taxonomy_package['entryPoints']) > 0:
                # Get the first entry point, there really should only be one
                first_key = list(taxonomy_package['entryPoints'].keys())[0]
                entry_point = taxonomy_package['entryPoints'][first_key][0][1] # the [1] is the url of the entry point
                options.entrypointFile = entry_point
                cntlr.addToLog("Using entry point {}".format(entry_point), "info")
            else:
                cntlr.addToLog("Cannot determine entry point for supplied package", "error")
                raise PackageException
        else:
            cntlr.addToLog("Cannot determine entry point for supplied package", "error")
            raise PackageException

def cmndLineXbrlRun(cntlr, options, model_xbrl, entryPoint, *args, **kwargs):

    #map = organize_taxonomy(model_xbrl, options)

    #serialize_taxonomy(map, model_xbrl, options)

    # Multiple serializer methods may be used. Serialize for each one. Find them by looking at the plugins that
    # have been used. Look for the 'serializer.serialize' entry.



    # Call the serialize method in the serializer method module. This will return a dictionary
    # of documents to create
    documents = getattr(_METHOD_MODULE, 'serialize', lambda *_x: dict())(model_xbrl, options, _SXM.SXMDTS())

    for serializer_method in getserizlierPlugins(cntlr):
        documents = serializer_method['serializer.serialize'](model_xbrl, options, _SXM)

    return

    global cur_version, new_version
    # Get filesource - this is the file source of the file that loaded the model
    model_xbrl = cntlr.modelManager.filesource
    # Get the taxonomy package zip file that the file source came from
    package_zip = None
    entry_mapped_url = PackageManager.mappedUrl(model_xbrl.url)
    for potential_package_zip in model_xbrl.referencedFileSources.values():
        if potential_package_zip.isInArchive(entry_mapped_url):
            package_zip = potential_package_zip
            break
    if package_zip is None:
        error("PackageError", "Cannot find the taxonomy package.", model_xbrl)
        raise Exception
    
   
    # Get the new package name
    _package_dir, package_file_name = os.path.split(package_zip.basefile)
    input_package_name = os.path.splitext(package_file_name)[0]
    new_package_name = '{}_package'.format(input_package_name)
    
    if cur_version is None:
        # Get the current version from the first xsd file in the package
        with zipfile.ZipFile(package_zip.basefile, 'r') as p:
            xsds = [x for x in p.namelist() if os.path.splitext(x)[1] == '.xsd']
            if len(xsds) > 0:
                first_xsd = xsds[0]
                _xsd_dir, xsd_name = os.path.split(first_xsd)
                xsd_name = os.path.splitext(xsd_name)[0]
                xsd_name_parts = xsd_name.split('_')
                cur_version = xsd_name_parts[-1]
            else:
                error("PackagerError", "Cannot determing the current version from the package files.", model_xbrl)
                raise PackageException
    if cur_version is None:
        error("PackagerError", "Current version not provided or cannot be detrmined from the package.", model_xbrl)  
        raise PackageException
    if new_version is None:
        error("PackagerError", "New version not provided or cannot be detrmined from the package.", model_xbrl) 
        raise PackageException     

    new_package_file_name = process_input_zip(package_zip.basefile, 
                                              os.path.dirname(package_zip.basefile), 
                                              new_package_name, 
                                              cur_version, 
                                              new_version,
                                              options.serializer_package_revision)

    model_xbrl.info("info", "Created taxonomy package: {}".format(os.path.realpath(new_package_file_name)))

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
