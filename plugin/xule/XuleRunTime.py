"""XuleRuntime

Xule is a rule processor for XBRL (X)brl r(ULE). 

The XuleRuntime module contains exception classes for the xule processor

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2022 XBRL US, Inc.

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
import collections
import copy 

class XuleException(Exception):
    pass

class XuleProcessingError(XuleException):
    def __init__(self, msg, xule_context=None):
        self.msg = msg
        self.xule_context = xule_context
        
    def __str__(self):
        if hasattr(self.xule_context, 'rule_name'):
            return "Rule: %s - %s" % (self.xule_context.rule_name, self.msg)
        else:
            return self.msg

class XuleIterationStop(XuleException):
    def __init__(self, stop_value=None):
        self.stop_value = stop_value

class XuleBuildTableError(XuleException):
    def __init__(self, msg):
        self.msg = msg
        
    def __str__(self):
        return self.msg           


class XuleReEvaluate(XuleException):
    def __init__(self, alignment=None):
        self.alignment = alignment

class XuleMissingRuleSetMap(XuleException):
    pass        
