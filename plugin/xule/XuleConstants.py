"""XuleConstants

Xule is a rule processor for XBRL (X)brl r(ULE). 

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
# Dimension navigation psuedo arc roles
DIMENSION_PSEDDO_ARCROLES = {'hypercube-primary': ('all',{'http://xbrl.org/int/dim/arcrole/all',}),
                             'dimension-member': ('dimension', {'http://xbrl.org/int/dim/arcrole/dimension-domain', 'http://xbrl.org/int/dim/arcrole/domain-member'}),
                             'primary-member': ('primary', {'http://xbrl.org/int/dim/arcrole/all', 'http://xbrl.org/int/dim/arcrole/domain-member'})}

DIMENSION_PSEUD0_SIDE = 0
DIMENSION_PSEUD0_ARCROLE_PART = 1

# Rule set mapping 
NAMESPACE_MAP = 'namespaceMap.json'
RULE_SET_COMPATIBILITY_FILE = 'rulesetCompatibility.json'
