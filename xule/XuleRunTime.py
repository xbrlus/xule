'''
Xule is rule processor for XBRL (X)brl r(ULE). 

Copyright (c) 2014 XBRL US Inc. All rights reserved

$Change$
'''
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
