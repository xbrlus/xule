"""XuleValidate

Xule is a rule processor for XBRL (X)brl r(ULE).

The XuleValidate module is used to validate rulesets

DOCSKIP
See https://xbrl.us/dqc-license for license information.
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2021 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 23204 $
DOCSKIP
"""
from arelle.ModelValue import QName
from arelle import FileSource
from arelle import ModelManager
from arelle.ValidateUtr import loadUtr
from arelle.ModelDtsObject import ModelType

from . import XuleConstants as xc
from . import XuleUtility as xu

import collections
import datetime
import logging
import re

class XuleValidate:

    xbrli_names = {'NCNameItemType',
                    'NameItemType',
                    'QNameItemType',
                    'anyURIItemType',
                    'base64BinaryItemType',
                    'booleanItemType',
                    'byteItemType',
                    'contextEntityType',
                    'contextPeriodType',
                    'contextScenarioType',
                    'dateItemType',
                    'dateTimeItemType',
                    'decimalItemType',
                    'doubleItemType',
                    'durationItemType',
                    'floatItemType',
                    'fractionItemType',
                    'gDayItemType',
                    'gMonthDayItemType',
                    'gMonthItemType',
                    'gYearItemType',
                    'gYearMonthItemType',
                    'hexBinaryItemType',
                    'intItemType',
                    'integerItemType',
                    'languageItemType',
                    'longItemType',
                    'measuresType',
                    'monetaryItemType',
                    'negativeIntegerItemType',
                    'nonNegativeIntegerItemType',
                    'nonPositiveIntegerItemType',
                    'normalizedStringItemType',
                    'positiveIntegerItemType',
                    'pureItemType',
                    'sharesItemType',
                    'shortItemType',
                    'stringItemType',
                    'timeItemType',
                    'tokenItemType',
                    'unsignedByteItemType',
                    'unsignedIntItemType',
                    'unsignedLongItemType',
                    'unsignedShortItemType'}

    def __init__(self, cntlr, rule_set, rule_set_name):
        self.cntlr = cntlr
        self.rule_set = rule_set
        self.name_models = dict()
        self.namespace_map = xu.get_rule_set_map(self.cntlr, xc.NAMESPACE_MAP)
        self.cntlr.addToLog('Using namespace map located at {}'.format(xu.get_rule_set_map_file_name(self.cntlr, xc.NAMESPACE_MAP)), 'info')
        cntlr.addToLog("Validating ruleset {}".format(rule_set_name), 'info')
        self.validate_qnames()
        
    def validate_qnames(self):
        """Validate that the qnames in a ruleset are valid for the namespace.
        """
        
        utr_namespaces = self._get_utr_namespaces()
        
        qnames_by_ns = collections.defaultdict(dict)
        qnames = self._get_qnames()
        for qname,  top_names in  qnames.items():
            qnames_by_ns[qname.namespaceURI][qname.localName] = top_names
        
        for namespace in qnames_by_ns.keys():
            if namespace in utr_namespaces:
                defined_names = utr_namespaces[namespace]
                if namespace == 'http://www.xbrl.org/2003/instance':
                    defined_names |= self.xbrli_names
            else:
                model_xbrl = self._get_entry_point(namespace)
                if model_xbrl is None or len(model_xbrl.errors) > 0:
                    self.cntlr.addToLog("No map for namespace {}.  Update {} file.".format(namespace, xc.NAMESPACE_MAP), 'NoNamespaceMap')
                    continue
                else:
                    #get the names defined in the schema
                    defined_names = set(x.localName for x in model_xbrl.qnameConcepts.keys() if x.namespaceURI == namespace)
                    defined_names |= set(x.qname.localName for x in model_xbrl.modelObjects if isinstance(x, ModelType) and x.qname.namespaceURI == namespace)
            for local_name in qnames_by_ns[namespace].keys() - defined_names:
                top_names = '\n\t'.join(qnames_by_ns[namespace][local_name])
                
                self.cntlr.addToLog('QName {{{}}}{} is not defined. Used in rules:\n\t{}'.format(namespace, local_name, top_names), 'QNameNotDefined', level=logging.ERROR)
                    
    
    def _get_utr_namespaces(self):
        # Get UTR
        modelManager = ModelManager.initialize(self.cntlr)
        modelUtr = modelManager.create()
        loadUtr(modelUtr)
        
        utr_namespaces = collections.defaultdict(set)
        for type_name, entries in modelManager.disclosureSystem.utrItemTypeEntries.items():
            for entry_name, entry in entries.items():
                if entry.isSimple:
                    utr_namespaces[entry.nsUnit].add(entry.unitId)
        
        return utr_namespaces
            
    def _get_entry_point(self, namespace):
        """Find the namespace pattern for the namespace and return the entry_point.
        """
        for namespace_pattern, entry_point_string in self.namespace_map.items():
            match = re.fullmatch(namespace_pattern, namespace)
            if match:
                return self._get_taxonomy_model(entry_point_string.format(*match.groups()), namespace)
                
        # If here, then there was no match
        return None 
    
    def _get_taxonomy_model(self, taxonomy_url, namespace):
        """Get an xbrl model of the entry_point file.
        """
        start = datetime.datetime.today()
        rules_taxonomy_filesource = FileSource.openFileSource(taxonomy_url, self.cntlr)            
        modelManager = ModelManager.initialize(self.cntlr)
        modelXbrl = modelManager.load(rules_taxonomy_filesource)
        if len({'IOerror','FileNotLoadable'} & set(modelXbrl.errors)) > 0:
            modelXbrl.error("TaxonomyLoadError","Cannot open file {} with namespace {}.".format(taxonomy_url, namespace))
        else:
            end = datetime.datetime.today()
            print("Taxonomy {namespace} loaded in {time}. {entry}".format(namespace=modelXbrl.modelDocument.targetNamespace,
                                                                         time=end - start,
                                                                         entry=taxonomy_url))
        
        return modelXbrl

    def _get_qnames(self):
        """Get all literal qnames in a ruleset.
        
        :returns: dictionary of set, keyed by qname. The set is the list of rules that use the qname
        :rtype: dict
        """         
        
        qnames = collections.defaultdict(set)
        
        for file_info in self.rule_set.catalog['files']:
            parse_tree = self.rule_set.getFile(file_info['file'])
            
            new_qnames = self._traverse(parse_tree)
            qnames = {k: qnames.get(k,set()) | new_qnames.get(k, set()) for k in qnames.keys() | new_qnames.keys()}
            #qnames |= self._traverse(parse_tree)
        
        return qnames  

    def _traverse(self, parent, depth=0,top_name=None):
        """Traverse a parse tree for qnames
        
        :returns: dictionary of set, keyed by qname. The set is the list of rules that use the qname
        :rtype: dict
        """
        qnames = collections.defaultdict(set)
        
        # When the depth is 2, we are at a top level expression (i.e. rule, constant, namespace declaration, function). Get the name of the expression.
        if depth == 2:
            top_name = "{}: {}".format(parent['exprName'], parent.get('fullName') or parent.get('constantName') or parent.get('functionName'))
        
        if isinstance(parent, dict):
            if parent.get('exprName') == 'qname':
                qnames[QName(parent['prefix'] if parent['prefix'] != '*' else None, parent['namespace_uri'], parent['localName'])].add(top_name)
                #qnames.add(QName(parent['prefix'] if parent['prefix'] != '*' else None, parent['namespace_uri'], parent['localName']))
            else:
                for k, v in parent.items():
                    # Skip 'arcrole', 'role' and 'drsRole' in navigation if it is an unprefixed qname
                    if not (parent.get('exprName') == 'navigation' and
                            k in ('arcrole', 'role', 'drsRole') and
                            v.get('exprName') == 'qname' and
                            v.get('prefix') == '*'):
                        # Remove .networks property arguments if they are unprefixed qnames
                        if (parent.get('exprName') == 'property' and
                            parent.get('propertyName') == 'networks' and
                            k == 'propertyArgs'):
                            v = [x for x in v if not (x.get('exprName') == 'qname' and x.get('prefix') == '*')]

                        new_qnames = self._traverse(v, depth+1, top_name)
                        qnames = {k: qnames.get(k,set()) | new_qnames.get(k, set()) for k in qnames.keys() | new_qnames.keys()}
                        #qnames |= self._traverse(v, depth+1, top_name)
        elif isinstance(parent, list):
            for x in parent:
                new_qnames = self._traverse(x, depth+1, top_name)
                qnames = {k: qnames.get(k,set()) | new_qnames.get(k, set()) for k in qnames.keys() | new_qnames.keys()}
                #qnames |= self._traverse(x, depth+1, top_name)
        
        return qnames             