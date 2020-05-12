# -*- coding: utf-8 -*-

'''
loadFromExcel.py is an example of a plug-in that will load an extension taxonomy from Excel
input and optionally save an (extension) DTS.

(c) Copyright 2013 Mark V Systems Limited, All rights reserved.
'''
import os, io, time, re
from collections import defaultdict
from arelle import XbrlConst
from arelle.ModelDtsObject import ModelConcept, ModelType
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import csv
import codecs
import json
from slugify import slugify

def saveXuleQNamesWinMain(cntlr, menu):
	pass

def saveXuleQNamesOptions(parser):
	# extend command line options with a save DTS option
	parser.add_option("--xule-qnames-dir", 
                      action="store", 
                      dest="saveXuleQnamesDirectory", 
                      help=_("Directory for Xule QNames files"))
	
	parser.add_option("--xule-qnames-format",
					  action="store",
					  dest="saveXuleQnamesFormat",
					  choices=('csv', 'json'),
					  default='csv',
					  help=_("csv or json"))

def saveXuleQNamesRun(cntlr, options, modelXbrl, *args, **kwargs):
	if getattr(options, "saveXuleQnamesDirectory", None):
		# extend XBRL-loaded run processing for this option
		QNameDir = getattr(options, "saveXuleQnamesDirectory", None)
		entryLocation = convertURLToPath(getattr(options, "entrypointFile", None))
		entryLocation = os.path.join(QNameDir, entryLocation)
		
		if QNameDir:
			localNames = baseItemTypes(modelXbrl)
			
			for ns, names in processDTR(cntlr).items():
				localNames[ns].update(names)
			for ns, names in processUTR(cntlr).items():
				localNames[ns].update(names)
			
			#NEED TO ADD REFERENCE PART QNAMES
			
			for concept in modelXbrl.modelObjects:
				if isinstance(concept, ModelConcept):
					if (concept.isItem or concept.isTuple): # and concept.qname.namespaceURI != 'http://www.xbrl.org/2003/instance':
						if concept.propertyView[0][0] == 'label':
							label = (concept.propertyView[0])[1]
						else:
							label = "NONE"
						localNames[concept.qname.namespaceURI].add((concept.qname.localName,
																    'Concept', 
																	label, 
																	str(concept.abstract), 
																	str(concept.typeQname), 
																	concept.periodType,
																	concept.balance))
					elif concept.isLinkPart: #reference part
						if concept.typeQname.namespaceURI == 'http://www.w3.org/2001/XMLSchema':
							conceptType = concept.typeQname.localName
						else:
							conceptType = concept.typeQname
						localNames[concept.qname.namespaceURI].add((concept.qname.localName, 
																	'Reference',
																	concept.qname.localName, 
																	str(concept.abstract), 
																	str(conceptType), 
																	None, 
																	None ))
			if options.saveXuleQnamesFormat == 'csv':		
				if not os.path.exists(entryLocation):
					os.makedirs(entryLocation)
		
				entryFile = os.path.join(entryLocation, "entryPoint.xep")
				with open(entryFile,"w") as o:
					o.write("\n".join(sorted(localNames.keys())))
		
				cntlr.addToLog("Entry point file: %s" % entryFile)
			
				for namespace, localNameList in localNames.items():
					nameLocation = os.path.join(QNameDir, convertURLToPath(namespace))
					if not os.path.exists(nameLocation):
						os.makedirs(nameLocation)
					nameFile = os.path.join(nameLocation, "names.xns")
					overwrite = os.path.isfile(nameFile)
					with codecs.open(nameFile, "w", "utf-8") as o:
						csvwriter = csv.writer(o)
						csvwriter.writerows(sorted(localNameList, key=lambda x: x[0]))
						#o.write("\n".join(y[0] for y in sorted(localNameList, key=lambda x: x[0])))
					if overwrite:
						cntlr.addToLog("Name file (overwritten): %s" % nameFile)
					else:
						cntlr.addToLog("Name file: %s" % nameFile)
			else: # json
				parts = ('type', 'label', 'isAbstract', 'dataType', 'periodType', 'balanceType')
				for namespace, localNameList in localNames.items():
					nameLocation = os.path.join(QNameDir, '{}.json'.format(slugify(namespace)))
					contentLocalNames = []
					for localNameInfo in localNameList:
						contentLocalName = {'localName': localNameInfo[0]}
						for i in range(6):
							if localNameInfo[i+1] is not None:
								contentLocalName[parts[i]] = localNameInfo[i+1]
						contentLocalNames.append(contentLocalName)
					content = {namespace: contentLocalNames}
					with open(nameLocation, 'w') as outFile:
						json.dump(content, outFile, indent=4)

def baseItemTypes(modelXbrl):
	'''This types are from the XBRL instance schema https://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd'''
	'''
	names = defaultdict(set)
	
	xbrlTypes = ['decimalItemType'
		,'floatItemType'
		,'doubleItemType'
		,'monetaryItemType'
		,'sharesItemType'
		,'pureItemType'
		,'fractionItemType'
		,'fractionItemType'
		,'integerItemType'
		,'nonPositiveIntegerItemType'
		,'negativeIntegerItemType'
		,'longItemType'
		,'intItemType'
		,'shortItemType'
		,'byteItemType'
		,'nonNegativeIntegerItemType'
		,'unsignedLongItemType'
		,'unsignedIntItemType'
		,'unsignedShortItemType'
		,'unsignedByteItemType'
		,'positiveIntegerItemType'
		,'stringItemType'
		,'booleanItemType'
		,'hexBinaryItemType'
		,'base64BinaryItemType'
		,'anyURIItemType'
		,'QNameItemType'
		,'durationItemType'
		,'dateTimeItemType'
		,'timeItemType'
		,'dateItemType'
		,'gYearMonthItemType'
		,'gYearItemType'
		,'gMonthDayItemType'
		,'gDayItemType'
		,'gMonthItemType'
		,'normalizedStringItemType'
		,'tokenItemType'
		,'languageItemType'
		,'NameItemType'
		,'NCNameItemType'
		]
	
	for name in xbrlTypes:
		names['http://www.xbrl.org/2003/instance'].add((name,'Type', name, False, None, None, None))

	return names
	'''
	typeNames = defaultdict(set)
	for typeModel in modelXbrl.qnameTypes.values():
		if isItemType(typeModel):
			typeNames[typeModel.qname.namespaceURI].add((typeModel.qname.localName, 'Type', typeModel.qname.localName, None, None, None, None))
	
	return typeNames

def isItemType(typeModel):
	xbrlTypes = ['decimalItemType'
		,'floatItemType'
		,'doubleItemType'
		,'monetaryItemType'
		,'sharesItemType'
		,'pureItemType'
		,'fractionItemType'
		,'fractionItemType'
		,'integerItemType'
		,'nonPositiveIntegerItemType'
		,'negativeIntegerItemType'
		,'longItemType'
		,'intItemType'
		,'shortItemType'
		,'byteItemType'
		,'nonNegativeIntegerItemType'
		,'unsignedLongItemType'
		,'unsignedIntItemType'
		,'unsignedShortItemType'
		,'unsignedByteItemType'
		,'positiveIntegerItemType'
		,'stringItemType'
		,'booleanItemType'
		,'hexBinaryItemType'
		,'base64BinaryItemType'
		,'anyURIItemType'
		,'QNameItemType'
		,'durationItemType'
		,'dateTimeItemType'
		,'timeItemType'
		,'dateItemType'
		,'gYearMonthItemType'
		,'gYearItemType'
		,'gMonthDayItemType'
		,'gDayItemType'
		,'gMonthItemType'
		,'normalizedStringItemType'
		,'tokenItemType'
		,'languageItemType'
		,'NameItemType'
		,'NCNameItemType'
		]
	
	if typeModel.qname.namespaceURI == "http://www.xbrl.org/2003/instance" and typeModel.qname.localName in xbrlTypes:
		# The type is or is based on an xbrl item type
		return True
	elif typeModel.typeDerivedFrom is None:
		#hit the bottom of the type derived from hierarchy, therefore the type is not a or derived from an xbrl item type
		return False
	elif not isinstance(typeModel.typeDerivedFrom, ModelType):
		#Sometimes the typeDerivedFromis a list
		return False
	else:
		#recurse the type derived from hierarchy to see if the type is based on an original xbrl item type
		return isItemType(typeModel.typeDerivedFrom)


def processDTR(cntlr):
	'''Get data types from the data type registry (DTR)'''
	cntlr.addToLog("Fetching DTR")
	dtrDict = defaultdict(set)
	try:
		with urllib.request.urlopen('http://www.xbrl.org/dtr/dtr.xml') as dtrXMLFile:
			dtrXML = dtrXMLFile.read()
		
		dtrTree = ET.fromstring(dtrXML)
		ns = {'dtr':'http://www.xbrl.org/2009/dtr'}
		for xbrlType in dtrTree.findall('dtr:types/dtr:type', ns):
			dtrNS = xbrlType.find('dtr:typeNamespace', ns)
			dtrName = xbrlType.find('dtr:typeName', ns)
			if dtrNS is not None and dtrName is not None:
				dtrDict[dtrNS.text].add((dtrName.text,'Type', dtrName.text, None, None, None, None))
				
	except urllib.error.HTTPError:
		cntlr.addToLog("DTR not found at http://www.xbrl.org/dtr/dtr.xml")
	
	cntlr.addToLog("DTR Processed")
	return dtrDict

def processUTR(cntlr):
	'''Get the units from the UTR'''
	cntlr.addToLog("Fetching UTR")
	utrDict = defaultdict(set)
	try:
		with urllib.request.urlopen('http://www.xbrl.org/utr/utr.xml') as utrXMLFile:
			utrXML = utrXMLFile.read()

		utrTree = ET.fromstring(utrXML)
		ns = {'utr':'http://www.xbrl.org/2009/utr'}
		for unit in utrTree.findall('utr:units/utr:unit', ns):
			unitNS = unit.find('utr:nsUnit', ns)
			unitName = unit.find('utr:unitId', ns)
			if unitNS is not None and unitName is not None:
				unitLabel = unit.find('utr:unitName', ns)
				if unitLabel is None:
					label = unitName.text
				else:
					label = unitLabel.text
				utrDict[unitNS.text].add((unitName.text,'Unit', label, None, None, None, None))
		
	except urllib.error.HTTPError:
		cntlr.addToLog("UTR not found at http://www.xbrl.org/utr/utr.xml")
	
	cntlr.addToLog("UTR Processed")
	return utrDict
	
def convertURLToPath(url):
	url_parts = urllib.parse.urlsplit(url)
	url_comps = [url_parts.scheme,]
	url_comps.append(url_parts.netloc.split(":")[0])
	url_comps += url_parts.path.split("/")
	url_comps = [x for x in url_comps if x]
	
	return os.sep.join(url_comps)

__pluginInfo__ = {
    'name': 'Save Xule QNames',
    'version': '0.9',
    'description': "This plug-in create QName files for the Xule Editor",
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) Copyright 2016 XBRL US Inc., All rights reserved.',
    # classes of mount points (required)
    'CntlrWinMain.Menu.Tools': saveXuleQNamesWinMain,
    'CntlrCmdLine.Options': saveXuleQNamesOptions,
    'CntlrCmdLine.Xbrl.Run': saveXuleQNamesRun,
}
