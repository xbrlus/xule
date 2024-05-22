import datetime
import decimal
import json
import numpy
from .XodelVars import save_arelle_model
from arelle.ModelObject import ModelObject
from arelle.ModelValue import QName

class JSONEncoder(json.JSONEncoder):

    # overload method default
    def default(self, obj):

        # Match all the types you want to handle in your converter
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        # Call the default method for other types
        return json.JSONEncoder.default(self, obj)

def property_to_xodel(xule_context, object_value, *args, _intermediate=False):
    # _intermediate is used when recursing. The final value will be a string. But if there are collections
    # (sets, list or dictionaries) then there needs to be recursion. The value passed up should be a
    # python collection (list or dictionary) until the final value is sent to the original caller, which
    # will be a string.
    try:
        from .xule import XuleValue as xv
    except (ModuleNotFoundError, ImportError):
        from xule import XuleValue as xv

    basic = True
    if object_value.type == 'entity':
        #basic = False
        working_val = f'["{object_value.value[0]}", "{object_value.value[1]}"]'
    elif object_value.type == 'unit':
        working_val =  repr(object_value.value)
    elif object_value.type == 'duration':
        if object_value.value[0] == datetime.datetime.min and object_value.value[1] == datetime.datetime.max:
            working_val = 'forever'
        else:
            working_val = f'{object_value.value[0].isoformat()}/{object_value.value[1].isoformat()}'
    elif object_value.type == 'instant':
        working_val = object_value.value.isoformat()
    elif object_value.type == 'qname':
        working_val = object_value.value.clarkNotation
    elif object_value.type in ('set', 'list'):
        basic = False
        working_val = tuple(property_to_xodel(xule_context, x, _intermediate=True) for x in object_value.value)
    elif object_value.type == 'dictionary':
        basic = False
        working_val = {property_to_xodel(xule_context, k, _intermediate=True): property_to_xodel(xule_context, v, _intermediate=True) for k, v in object_value.value}
    elif object_value.type== 'bool':
        if _intermediate:
            working_val = object_value.value
        else:
            if object_value.value == True:
                working_val = 'true'
            else:
                working_val = 'false'
    # elif object_value.type == 'concept':
    #     # Need to save the arelle model and the concept
    #     save_arelle_model(object_value.value.modelXbrl)
    #     working_val = json.dumps((id(object_value.value.modelXbrl), object_value.value.objectId()))
    elif object_value.type in ('none', 'unbound'):
        if _intermediate:
            working_val = None 
        else:
            working_val = '' # empty string for None
    # elif isinstance(object_value.value, decimal.Decimal):
    #     working_val = str(object_value.value)
    elif isinstance(object_value.value, datetime.datetime):
        working_val =  object_value.value.isoformat()
    elif type(object_value.value) in (float, decimal.Decimal):
        if _intermediate:
            working_val = object_value.value
        else:
            working_val = numpy.format_float_positional(object_value.value, trim='0')
        #working_val = str(object_value.value)
    elif type(object_value.value) == int:
        if _intermediate:
            working_val = object_value.value
        else:
            working_val = str(object_value.value)
    elif isinstance(object_value.value, ModelObject):
        # Need to save the arelle model and the concept
        save_arelle_model(object_value.value.modelXbrl)
        if _intermediate:
            working_val = (id(object_value.value.modelXbrl), object_value.value.objectId())
        else:
            working_val = json.dumps((id(object_value.value.modelXbrl), object_value.value.objectId()))
    else:
        working_val = object_value.format_value()

    if _intermediate:
        return working_val
    elif basic:
        return xv.XuleValue(xule_context, working_val, 'string')
    else:
        return xv.XuleValue(xule_context, json.dumps(working_val, cls=JSONEncoder), 'string')
    
def property_reprefix(xule_context, object_value, *args):
    '''
    This property will generate a new qname by applying the prefix that is passed. The prefix will match a prefix in the rule set
    '''
    try:
        from .xule.XuleRunTime import XuleProcessingError
    except (ModuleNotFoundError, ImportError):
        from xule.XuleRunTime import XuleProcessingError
    try:
        from .xule import XuleValue as xv
    except (ModuleNotFoundError, ImportError):
        from xule import XuleValue as xv

    if len(args) == 0:
        prefix = '*' # this is the default prefix
    else:
        if args[0].type != 'string':
            raise XuleProcessingError(_(f"Property .reprefix request a string argumnet, found {args[0].type}"), xule_context)
        prefix = args[0].value
    
    namespace = xule_context.rule_set.getNamespaceUri(prefix)

    new_qname = QName(prefix if prefix != '*' else None, namespace, object_value.value.localName)

    return xv.XuleValue(xule_context, new_qname, 'qname')
