'''Package taxonomy

This script creates a taxonomy package from a folder containing a taxonomy. It requires a template
for the META-INF folder. If the template for the META-INF folder is named as META-INF-{taxonomy name}
this script will use that folder as the template. 
'''
import argparse
from lxml import etree
import os
import re
import zipfile

file_count = 0

def reversion(in_file, out_file, zip_file, version, package_name, zip_tms=None):
    global file_count
    file_count += 1
    print('{:03d} Processing file: {}'.format(file_count, in_file))

    with open(in_file, 'r', encoding="utf8") as f:
        content = f.read()

    def sub_version(matchobj):
        replacement = "{pre}{date}-{version}{post}".format(
            pre=matchobj.group(1),
            date=matchobj.group(2),
            version=version,
            post=matchobj.group(3)
        )
        return replacement

    def sub_sub_replace(matchobj):
        content = matchobj.group()
        # replace each 2020-01-01
        content = re.sub('2020-01-01', '2020-01-01-{}'.format(version), content)

        return content

    # replace namespace declarations:  xmlns:prefix="namespace"
    content = re.sub('''(xmlns:?[^=]+=[\'\"][^\'\"]*)(2020-01-01)([^\'\"]*[\'\"])''', sub_version, content).replace('\\', '/')
    # replace @hrefs
    content = re.sub('''(href=[\'\"][^\'\"#]*)(2020-01-01)([^\'\"#]*[\'\"#])''', sub_sub_replace, content).replace('\\', '/')
    # replace namespace (in imports)
    content = re.sub('''(namespace=[\'\"][^\'\"#]*)(2020-01-01)([^\'\"#]*[\'\"#])''', sub_version, content).replace('\\', '/')
    # replace targetNamespace
    content = re.sub('''(targetNamespace=[\'\"][^\'\"#]*)(2020-01-01)([^\'\"#]*[\'\"#])''', sub_version, content).replace('\\', '/')   
    # replace uriStartString (in context.xml file of META_INF)
    content = re.sub('''(uriStartString=[\'\"][^\'\"#]*)(2020-01-01)([^\'\"#]*[\'\"#])''', sub_version, content).replace('\\', '/')
    # replace schemaLocation (in imports)
    content = re.sub('''(?<=[^:])(schemaLocation=[\'\"][^\'\"#]*)(2020-01-01)([^\'\"#]*[\'\"#])''', sub_version, content).replace('\\', '/')
    # replace xsi:schemaLocation
    content = re.sub('''xsi:schemaLocation=[\'\"][^\'\"]*[\'\"]''', sub_sub_replace, content).replace('\\', '/')
    # replace <tp:version>
    content = re.sub('''(<tp:version>)(2020-01-01)(</tp:version>)''', sub_version, content)
    # replace <tp:identifier>
    content = re.sub('''(<tp:identifier>).*(</tp:identifier>)''', sub_sub_replace, content)  

    zip_file.writestr(os.path.join(package_name, out_file.replace('2020-01-01', '2020-01-01-{}'.format(version))).replace('\\','/'), 
                      content)
    if zip_tms is not None:
        zip_tms.writestr(out_file.replace('2020-01-01', '2020-01-01-{}'.format(version)), 
                      content)                      

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create FERC Taxonomy Package')
    parser.add_argument('form',
                         help="The name of the folder containing the taxonomy.")
    parser.add_argument('version',
                         help="The version to create in the pacakge.")
    parser.add_argument('meta_inf',
                         nargs="?", # This makes the argument optional
                         help="(Optional) The name of the META-INF template folder.")

    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.realpath(__file__))

    package_name = '{}_2020-01-01-{}'.format(args.form, args.version)
    tms_name = '{}_2020-01-01-{}-TMS'.format(args.form, args.version)
    meta_dir = args.meta_inf or 'META-INF-{}'.format(args.form)
    if not os.path.exists(meta_dir):
        print("META-INF folder is missing. Looking for '{}'".format(meta_dir))
        exit(1)

    #create zipfile
    with zipfile.ZipFile('{}.zip'.format(package_name), 'w', zipfile.ZIP_DEFLATED) as zip:
        # Make a copy of the taxonomy package for TMS. This version does not have the root folder nor the META-INF File
        with zipfile.ZipFile('{}.zip'.format(tms_name), 'w', zipfile.ZIP_DEFLATED) as zip_tms:
            # copy the meta inf folder
            for dirname, dirnames, filenames in os.walk(meta_dir):
                for filename in filenames:
                    if filename == 'desktop.ini': continue
                    file_path = '/'.join((dirname, filename)) #os.path.join(dirname, filename)
                    #zip.write(file_path, os.path.join(package_name, 'META-INF', filename))
                    reversion(file_path, os.path.join('META-INF', filename).replace('\\','/'), zip, args.version, package_name)

            for dirname, dirnames, filenames in os.walk(args.form):
                for filename in filenames:
                    if filename == 'desktop.ini': continue
                    file_path = os.path.join(dirname, filename)
                    new_path = file_path.split(os.sep)[1:]
                    new_path = os.path.join(*file_path.split(os.sep)[1:])
                    new_path.replace('\\', '/')
                    #zip.write(file_path, new_path)
                    reversion(file_path, new_path, zip, args.version, package_name, zip_tms)


    
