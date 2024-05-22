
import os
import re

def commandLineFilingStart(cntlr, options, filesource, entrypointFiles, *args, **kwargs):
    '''Identify manifest files in Japan EDINET Archive (zip) files.'''

    if filesource.isArchive and filesource.fs is not None: # The .fs will ensure that the file exists
        # Need to check if the archive has the expected directory structure for Japan EDINET archive.

        entryFiles = []
        # Find the manifest files
        for fullFileName in filesource.fs.namelist():
            path, fileName = os.path.split(fullFileName)
            fileNamePart, extPart = os.path.splitext(fileName)
            # Check if this is a manifest file
            fileMatch = re.match(r'^manifest_(.+)\.xml$', fileName)
            if fileMatch is not None and len(fileMatch.groups()) == 1:
                docType = fileMatch.group(1) # This is the portion matched in the parens in the re
            else:
                continue # this is not a manifest file
            # Check if the directory structure seems ok. The strucutre should be:
            # top level / document control number / XBRL / PublicDoc or AuditDoc
            pathParts = path.split('/')
            pathParts.reverse()
            if len(pathParts) >= 3:
                docControlNumber = pathParts[2]
                if pathParts[:3] == [docType, 'XBRL', docControlNumber]:
                    # tuple with the file name first and then a sort key
                    entryFiles.append((os.path.join(filesource.baseurl, fullFileName),
                                       (pathParts[2], 0 if docType.lower() == 'publicdoc' else 2 if  docType.lower() == 'auditdoc' else 3, docType)))

        if len(entryFiles) > 0:
            # Files were found.

            # Sort the entryFiles so that the public doc is loaded before the audit doc.
            # The audit doc does not have period information. If the public doc is loaded first, the fiscal
            # period information can be extracted from the database from the public doc data.
            sortedEntryFiles = sorted(entryFiles, key=lambda x: x[1])
            # Delete the xbrl files in the entryPointFiles. These are files that were found in the archive that
            # are not JapanEDINET manifest files.
            for removeFileName in [x for x in entrypointFiles if x['file'].startswith(filesource.baseurl)]:
                entrypointFiles.remove(removeFileName)
            entrypointFiles.extend({'file': x[0]} for x in sortedEntryFiles)
            cntlr.addToLog("Identified {} manifest files".format(str(len(entryFiles))), messageCode="info")

__pluginInfo__ = {
    'name': 'Japan EDINET Archive File Loader',
    'version': '0.9',
    'description': "This plug-in adds a feature to identify the manifest files used in Japan EDINET zip files.",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'inlineXbrlDocumentSet',
    # classes of mount points (required)
    'CntlrCmdLine.Filing.Start': commandLineFilingStart,
}