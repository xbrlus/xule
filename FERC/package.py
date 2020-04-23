'''
Reivision number: $Change$
'''
'''Package taxonomy

This script creates a taxonomy package from a folder containing a taxonomy. It requires a template
for the META-INF folder. If the template for the META-INF folder is named as META-INF-{taxonomy name}
this script will use that folder as the template. 
'''

from arelle.CntlrWebMain import Options
from arelle import FileSource
from arelle import PackageManager
from lxml import etree
import io
import optparse
import os
import re
import zipfile

file_count = 0
taxonomy_package_file_name = None
catalog_file_name = None
cur_version = None
new_version = None
form_name = None

def reversion(in_file, out_file, zip_file, cur_version, version, package_name):
    global file_count
    file_count += 1
    print('{:03d} Processing file: {}'.format(file_count, in_file.name if isinstance(in_file, io.IOBase) else in_file))

    if isinstance(in_file, io.IOBase):
        content = in_file.read().decode()
    else:
        with open(in_file, 'r', encoding="utf8") as f:
            content = f.read()

    def sub_version(matchobj):
        replacement = "{pre}{version}{post}".format(
            pre=matchobj.group(1),
            date=matchobj.group(2)[:10],
            version=version,
            post=matchobj.group(3)
        )
        return replacement

    def sub_sub_replace(matchobj):
        content = matchobj.group()
        # replace each 2020-01-01
        content = re.sub(cur_version, version, content)

        return content

    # replace namespace declarations:  xmlns:prefix="namespace"
    content = re.sub('''(xmlns:?[^=]+=[\'\"][^\'\"]*)({})([^\'\"]*[\'\"])'''.format(cur_version), sub_version, content).replace('\\', '/')
    # replace @hrefs
    content = re.sub('''(href=[\'\"][^\'\"#]*)({})([^\'\"#]*[\'\"#])'''.format(cur_version), sub_sub_replace, content).replace('\\', '/')
    # replace namespace (in imports)
    content = re.sub('''(namespace=[\'\"][^\'\"#]*)({})([^\'\"#]*[\'\"#])'''.format(cur_version), sub_version, content).replace('\\', '/')
    # replace targetNamespace
    content = re.sub('''(targetNamespace=[\'\"][^\'\"#]*)({})([^\'\"#]*[\'\"#])'''.format(cur_version), sub_version, content).replace('\\', '/')   
    # replace uriStartString (in context.xml file of META_INF)
    content = re.sub('''(uriStartString=[\'\"][^\'\"#]*)({})([^\'\"#]*[\'\"#])'''.format(cur_version), sub_version, content).replace('\\', '/')
    # replace schemaLocation (in imports)
    content = re.sub('''(?<=[^:])(schemaLocation=[\'\"][^\'\"#]*)({})([^\'\"#]*[\'\"#])'''.format(cur_version), sub_version, content).replace('\\', '/')
    # replace xsi:schemaLocation
    content = re.sub('''xsi:schemaLocation=[\'\"][^\'\"]*[\'\"]''', sub_sub_replace, content).replace('\\', '/')
    # replace <tp:version>
    content = re.sub('''(<tp:version>)({})(</tp:version>)'''.format(cur_version), sub_version, content)
    # replace <tp:identifier>
    content = re.sub('''(<tp:identifier>).*(</tp:identifier>)''', sub_sub_replace, content)  

    zip_file.writestr(os.path.join(package_name, out_file.replace(cur_version, '{}'.format(version))).replace('\\','/'), 
                      content)                     

def process_input_zip(input_zip, package_dir, form_name, cur_version, new_version):

    global taxonomy_package_file_name
    global catalog_file_name

    package_name = '{}_{}'.format(form_name, new_version)
    new_package_file_name = os.path.join(package_dir, '{}.zip'.format(package_name))
    #create zipfile
    with zipfile.ZipFile(new_package_file_name, 'w', zipfile.ZIP_DEFLATED) as zip:
        # copy the taxonomyPackage.xml file
        reversion(taxonomy_package_file_name, 
                    os.path.join('META-INF', 'taxonomyPackage.xml').replace('\\','/'), 
                    zip, 
                    '2020-01-01',
                    new_version,
                    package_name)
        # catalog file, if it exists
        if catalog_file_name is not None:
            reversion(catalog_file_name, 
                    os.path.join('META-INF', 'catalog.xml').replace('\\','/'), 
                    zip, 
                    '2020-01-01',
                    new_version,
                    package_name)
        
        with zipfile.ZipFile(input_zip, 'r') as in_zip:
            for file_path in in_zip.namelist():
                # check if there is a hidden directory, if so, skip the file.
                if not('/.' in file_path or '\\.' in file_path or 'META-INF' in file_path):
                    with in_zip.open(file_path) as in_file_object:
                        new_path = file_path.split('/')[1:]
                        new_path = os.path.join(*new_path)
                        new_path.replace('\\', '/')
                        reversion(in_file_object, 
                                new_path, 
                                zip,
                                cur_version, 
                                new_version, 
                                package_name)

    return new_package_file_name

def cmdLineOptionExtender(parser, *args, **kwargs):
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "FERC Taxonomy Packager",
                                           "This plugin will create a FERC Taxonomy Package. The -f options should point to the folder tht contains the taxonomy.")
        parser.add_option_group(parserGroup)

    parserGroup.add_option('--ferc-package-dir',
                         default='.',
                         help="The directory of the package file to create.")
    parserGroup.add_option('--ferc-package-version',
                         help="The version to create in the pacakge.")
    parserGroup.add_option('--ferc-package-form',
                             action='store',
                             help="The name of the form. The default is the last part of the taxonomy path.")
    parserGroup.add_option('--ferc-package-meta-inf',
                            action='store',
                            help="The name of the META-INF template folder. The default is 'META-INF-' plus the form name.")
    parserGroup.add_option('--ferc-package-catalog',
                            action='store',
                            help="The name of the catalog.xml file to use in the package.")  
    parserGroup.add_option('--ferc-package-taxonomy-package',
                            action='store',
                            help="The name of the taxonomyPackage.xml file to use in the package.")                                                       
    parserGroup.add_option('--ferc-package-cur-version',
                             action='store',
                             help="The version currently in the taxonomy. This version will be replaced.")


def fercCmdUtilityRun(cntlr, options, **kwargs): 
    '''
    The entrypoint file (-f option) will be a directory of the taxonomy files.
    '''
    global taxonomy_package_file_name
    global catalog_file_name
    global cur_version
    global new_version
    global form_name

    parser = optparse.OptionParser()

    form_name = options.ferc_package_form
    cur_version = options.ferc_package_cur_version
    new_version = options.ferc_package_version

    # --ferc-package-meta-inf is mutually exclusive with --ferc-package-catalog and --ferc-pacakge-taxonomy-package
    if options.ferc_package_meta_inf is not None and options.ferc_package_taxonomy_package is not None:
        parser.error("--ferc-package-meta-inf cannot be used with --ferc-package-taxonomy-package.")

    if options.ferc_package_meta_inf is not None and options.ferc_package_catalog is not None:
        parser.error("--ferc-package-meta-inf cannot be used with --ferc-package-catalog.")

    # Check if supplied files exist:
    if options.ferc_package_meta_inf is not None:
        if os.path.isdir(options.ferc_package_meta_inf):
            if os.path.isfile(os.path.join(options.ferc_package_meta_inf, 'taxonomyPackage.xml')):
                taxonomy_package_file_name = os.path.join(options.ferc_package_meta_inf, 'taxonomyPackage.xml')
            else:
                parser.error("taxonomyPackage.xml does not exist in the supplied meta info folder '{}'.".format(options.ferc_package_meta_inf))
            if os.path.isfile(os.path.join(options.ferc_package_meta_inf, 'catalog.xml')):
                catalog_file_name = os.path.join(options.ferc_package_meta_inf, 'catalog.xml')
        else: # supplied meta-inf folder does not exist
            parser.error("Supplied meta info folder (--ferc-package-meta-inf) does not exist '{}'".format(options.ferc_package_meta_inf))

    # Check if supplied taxonomy package exists
    if options.ferc_package_taxonomy_package is not None:
        if os.path.isfile(options.ferc_package_taxonomy_package):
            taxonomy_package_file_nmae = os.path.join(options.ferc_package_taxonomy_package)
        else:
            parser.error("Supplied taxonomy package file name (--ferc-package-taxonomy-package) does not exist '{}'".format(options.ferc_package_taxonomy_package))
    
    # Check if supplied catalog file exists
    if options.ferc_package_catalog is not None:
        if os.path.isfile(options.ferc_package_catalog):
            catalog_file_name = os.path.join(options.ferc_package_catalog)
        else:
            parser.error("Supplied catalog file name (--ferc-package-catalog) does not exist '{}'".format(options.ferc_package_catalog))
    
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

def cmndLineXbrlRun(cntlr, options, modelXbrl, entryPoint, **kwargs):

    global form_name, cur_version, new_version
    # Get filesource - this is the file source of the file that loaded the model
    cur_file_source = cntlr.modelManager.filesource
    # Get the taxonomy package zip file that the file source came from
    package_zip = None
    entry_mapped_url = PackageManager.mappedUrl(cur_file_source.url)
    for potential_package_zip in cur_file_source.referencedFileSources.values():
        if potential_package_zip.isInArchive(entry_mapped_url):
            package_zip = potential_package_zip
            break
    if package_zip is None:
        modelXbrl.error("Cannot find the taxonomy package.")
    
    if form_name is None  or new_version is None:
        # Get these from the package file name
        package_dir, package_file_name = os.path.split(package_zip.basefile)
        package_full_name = os.path.splitext(package_file_name)[0]
        package_name_parts = package_full_name.split('-')
        if len(package_name_parts) != 3:
            modelXbrl.error("PackagerError", "Cannot determime form name and version from package name.")
            raise Exception
        package_form_name, package_new_version, revision = package_name_parts
        form_name = form_name or package_form_name
        new_version = new_version or package_new_version
    
    if cur_version is None:
        # Get the current version from the first xsd file in the package
        with zipfile.ZipFile(package_zip.basefile, 'r') as p:
            xsds = [x for x in p.namelist() if os.path.splitext(x)[1] == '.xsd']
            if len(xsds) > 0:
                first_xsd = xsds[0]
                xsd_dir, xsd_name = os.path.split(first_xsd)
                xsd_name = os.path.splitext(xsd_name)[0]
                xsd_name_parts = xsd_name.split('_')
                cur_version = xsd_name_parts[-1]
            else:
                modelXbrl.error("PackagerError", "Cannot determing the current version from the package files.")
                raise Exception

    if form_name is None:
        modelXbrl.error("PackagerError", "Form name not provided or cannot be detrmined from the package.")
        raise Exception
    if cur_version is None:
        modelXbrl.error("PackagerError", "Current version not provided or cannot be detrmined from the package.")  
        raise Exception
    if new_version is None:
        modelXbrl.error("PackagerError", "New version not provided or cannot be detrmined from the package.") 
        raise Exception     

    new_package_file_name = process_input_zip(package_zip.basefile, options.ferc_package_dir, form_name, cur_version, new_version)

    modelXbrl.info("info", "Created taxonomy package: {}".format(os.path.realpath(new_package_file_name)))

__pluginInfo__ = {
    'name': 'FERC Taxonomy Packager',
    'version': '0.9',
    'description': "This plug-in organizes the taxonomy files and creates a Taxonomy Package",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': '',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': fercCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Run': cmndLineXbrlRun,
}
    
