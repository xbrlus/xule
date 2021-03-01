"""XuleFunctions

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

$Change: 23066 $
DOCSKIP
"""

from aniso8601 import parse_duration
from arelle.ModelValue import qname, QName
import collections
import datetime
import decimal
import json

from .XuleRunTime import XuleProcessingError
from . import XuleValue as xv
from . import XuleRollForward as xrf
from . import XuleUtility as xu


def func_exists(xule_context, *args):   
    #return xv.xv.XuleValue(xule_context, args[0].type not in ('unbound', 'none'), 'bool')
    return xv.XuleValue(xule_context, args[0].type != 'unbound', 'bool')

def func_missing(xule_context, *args):
    #return xv.XuleValue(xule_context, args[0].type in ('unbound', 'none'), 'bool')
    return xv.XuleValue(xule_context, args[0].type == 'unbound', 'bool')

def func_date(xule_context, *args):
    arg = args[0]

    if arg.type == 'instant':
        return arg
    elif arg.type == 'string':
        return xv.XuleValue(xule_context, xv.iso_to_date(xule_context, arg.value), 'instant')
    else:
        raise XuleProcessingError(_("function 'date' requires a string argument, found '%s'" % arg.type), xule_context)

def func_duration(xule_context, *args):
    start = args[0]
    end = args[1]
    
    start_instant = func_date(xule_context, start)
    end_instant = func_date(xule_context, end)
    
    if end_instant.value < start_instant.value:
        return xv.XuleValue(xule_context, None, 'unbound')
    else:
        return xv.XuleValue(xule_context, (start_instant.value, end_instant.value), 'duration', from_model=start.from_model or end.from_model)

def func_forever(xule_context, *args):
    return xv.XuleValue(xule_context, (datetime.datetime.min, datetime.datetime.max), 'duration')

def func_unit(xule_context, *args):
    
    if len(args) == 0 or len(args) > 2:
        raise XuleProcessingError(_("The unit() function takes 1 or 2 arguments, found {}".format(len(args))), xule_context)
    
    return xv.XuleValue(xule_context, xv.XuleUnit(*args), 'unit')

def func_entity(xule_context, *args):
    scheme = args[0]
    identifier = args[1]
    
    if scheme.type != 'string' or identifier.type != 'string':
        raise XuleProcessingError(_("The entity scheme and identifier must be strings. Found '%s' and '%s'" % (scheme.type, identifier.type)), xule_context)
    
    return xv.XuleValue(xule_context, (scheme.value, identifier.value), 'entity')

def func_qname(xule_context, *args):
    namespace_uri_arg = args[0]
    local_name_arg = args[1]
    
    if namespace_uri_arg.type not in ('string', 'uri', 'unbound', 'none'):
        raise XuleProcessingError(_("Function 'qname' requires the namespace_uri argument to be a string, uri or none, found '%s'" % namespace_uri_arg.type), xule_context)
    if local_name_arg.type != 'string':
        raise XuleProcessingError(_("Function 'qname' requires the local_part argument to be a string, found '%s'" % local_name_arg.type), xule_context)

    if namespace_uri_arg.type == 'unbound':
        return xv.XuleValue(xule_context, qname(local_name_arg.value, noPrefixIsNoNamespace=True), 'qname')
    else:
        # get the prefix from the rule file
        prefix = get_prefix(xule_context, namespace_uri_arg.value)
        return xv.XuleValue(xule_context, QName(prefix, namespace_uri_arg.value, local_name_arg.value), 'qname')

def get_prefix(xule_context, uri):
    for k, v in xule_context.global_context.catalog['namespaces'].items():
        if v['uri'] == uri:
            if k == '*':
                return None
            else:
                return k
    return None

def func_uri(xule_context, *args):
    arg = args[0]

    if arg.type == 'string':
        return xv.XuleValue(xule_context, arg.value, 'uri')
    elif arg.type == 'uri':
        return arg
    else:
        raise XuleProcessingError(_("The 'uri' function requires a string argument, found '%s'." % arg.type), xule_context) 

def func_time_span(xule_context, *args):
    arg = args[0]
    
    if arg.type != 'string':
        raise XuleProcessingError(_("Function 'time-span' expects a string, fount '%s'." % arg.type), xule_context)
    
    try:
        return xv.XuleValue(xule_context, parse_duration(arg.value.upper()), 'time-period')
    except:
        raise XuleProcessingError(_("Could not convert '%s' into a time-period." % arg.value), xule_context)

def func_schema_type(xule_context, *args):
    arg = args[0]
    
    if arg.type == 'qname':
        if arg.value in xule_context.model.qnameTypes:
            return xv.XuleValue(xule_context, xule_context.model.qnameTypes[arg.value], 'type')
        else:
            return xv.XuleValue(xule_context, None, 'none')
    else:
        raise XuleProcessingError(_("Function 'schema' expects a qname argument, found '%s'" % arg.type), xule_context)

def func_num_to_string(xule_context, *args):
    arg = args[0]
    
    if arg.type in ('int', 'float', 'decimal'):
        return xv.XuleValue(xule_context, format(arg.value, ","), 'string')
    else:
        raise XuleProcessingError(_("function 'num_to_string' requires a numeric argument, found '%s'" % arg.type), xule_context)
        
def func_mod(xule_context, *args):
    numerator = args[0]
    denominator = args[1]
    
    if numerator.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The numerator for the 'mod' function must be numeric, found '%s'" % numerator.type), xule_context) 
    if denominator.type not in ('int', 'float', 'decimal'):
        raise XuleProcessingError(_("The denominator for the 'mod' function must be numeric, found '%s'" % denominator.type), xule_context)
    
    combined_type, numerator_compute_value, denominator_compute_value = xv.combine_xule_types(numerator, denominator, xule_context)
    return xv.XuleValue(xule_context, numerator_compute_value % denominator_compute_value, combined_type)

def func_extension_concept(xule_context, *args):   
    extension_ns_value_set = xule_context._const_extension_ns()
    if len(extension_ns_value_set.values) > 0:
        extension_ns = extension_ns_value_set.values[None][0].value
    else:
        raise XuleProcessingError(_("Cannot determine extension namespace."), xule_context)
    
    concepts = set(xv.XuleValue(xule_context, x, 'concept') for x in xule_context.model.qnameConcepts.values() if (x.isItem or x.isTuple) and x.qname.namespaceURI == extension_ns)
    
    return xv.XuleValue(xule_context, frozenset(concepts), 'set')

def agg_count(xule_context, values):
    alignment = values[0].alignment if len(values) > 0 else None
    return_value = xv.XuleValue(xule_context, len(values), 'int', alignment=alignment)
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #xv.XuleValue(xule_context, len(values), 'int', alignment=alignment)

def agg_sum(xule_context, values):
    agg_value = values[0].clone()
    tags = {} if agg_value.tags is None else agg_value.tags
    facts = collections.OrderedDict() if agg_value.facts is None else agg_value.facts
    
    for current_value in values[1:]:
        combined_types = xv.combine_xule_types(agg_value, current_value, xule_context)
        if combined_types[0] == 'set':
            agg_value = xv.XuleValue(xule_context, combined_types[1] | combined_types[2], combined_types[0], alignment=agg_value.alignment)
        else:
            agg_value = xv.XuleValue(xule_context, combined_types[1] + combined_types[2], combined_types[0], alignment=agg_value.alignment)
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
            
    if len(tags) > 0:
        agg_value.tags = tags
    if len(facts) > 0:
        agg_value.facts = facts
    
    return agg_value 

def agg_all(xule_context, values):
    all_value = True
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type != 'bool':
            raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % current_value.type), xule_context)
        if current_value.value and current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.value and current_value.facts is not None:
            facts.update(current_value.facts)      
        all_value = all_value and current_value.value
        if not all_value:
            break
    
    return_value = xv.XuleValue(xule_context, all_value, 'bool')
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
        
    return return_value #xv.XuleValue(xule_context, all_value, 'bool')

def agg_any(xule_context, values):
    any_value = False
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type != 'bool':
            raise XuleProcessingError(_("Function all can only operator on booleans, but found '%s'." % current_value.type), xule_context)
        if current_value.value and current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.value and current_value.facts is not None:
            facts.update(current_value.facts)
                    
        any_value = any_value or current_value.value
        if any_value:
            break
    return_value = xv.XuleValue(xule_context, any_value, 'bool')
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0 :
        return_value.facts = facts
    return return_value #xv.XuleValue(xule_context, any_value, 'bool')

def agg_first(xule_context, values):
    return values[0].clone()

def agg_max(xule_context, values):
    agg_value = values[0].clone()
    
    for current_value in values[1:]:
        if agg_value.value < current_value.value:
            agg_value = current_value.clone()
            
    return agg_value

def agg_min(xule_context, values):
    agg_value = values[0].clone()
    
    for current_value in values[1:]:
        if agg_value.value > current_value.value:
            agg_value = current_value.clone()
            
    return agg_value    
    
def agg_list(xule_context, values):
#Commented out for elimination of the shadow_collection
#     list_values = []
#     shadow = []
#     
#     for current_value in values:
#         list_values.append(current_value)
#         shadow.append(current_value.shadow_collection if current_value.type in ('list','set') else current_value.value)
#         
#     return xv.XuleValue(xule_context, tuple(list_values), 'list', shadow_collection=tuple(shadow))

    list_values = []
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        list_values.append(current_value)
        shadow.append(current_value.shadow_collection if current_value.type in ('list','set', 'dictionary') else current_value.value)
        if current_value.tags is not None:
            tags.update(current_value.tags)
        if current_value.facts is not None:
            facts.update(current_value.facts)
    
    return_value = xv.XuleValue(xule_context, tuple(list_values), 'list', shadow_collection=tuple(shadow))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #xv.XuleValue(xule_context, tuple(list_values), 'list')

def agg_set(xule_context, values):
    set_values = []
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    for current_value in values:
        if current_value.type in ('set', 'list', 'dictionary'):
            if current_value.shadow_collection not in shadow:
                set_values.append(current_value)
                shadow.append(current_value.shadow_collection)
                if current_value.tags is not None:
                    tags.update(current_value.tags)
                if current_value.facts is not None:
                    facts.update(current_value.facts)
        else:
            if current_value.value not in shadow:
                set_values.append(current_value)
                shadow.append(current_value.value)
                if current_value.tags is not None:
                    tags.update(current_value.tags)
                if current_value.facts is not None:
                    facts.update(current_value.facts)
    
    return_value = xv.XuleValue(xule_context, frozenset(set_values), 'set', shadow_collection=frozenset(shadow))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value #xv.XuleValue(xule_context, frozenset(set_values), 'set')

def agg_dict(xule_context, values):
    shadow = []
    tags = {}
    facts = collections.OrderedDict()
    
    dict_values = dict()
    shadow = dict()
    
    for current_value in values:
        if current_value.type != 'list':
            raise XuleProcessingError(_("Arguments for the dict() function must be lists of key/value pairs, found %s" % current_value.type),
                                      xule_context)
        if len(current_value.value) != 2:
            raise XuleProcessingError(_("Arguments for the dict() function must be lists of length 2 (key/value pair). Found list of length %i" % len(current_value.value)))
    
        key = current_value.value[0]
        if key.type == 'dictionary':
            raise XuleProcessingError(_("Key to a dictionary cannot be a dictionary."), xule_context)
        
        value = current_value.value[1]
        
        # A dictionary can only have one value for a key. If the key is already in the dicitionary then the current set of values can be skipped.
        # This is determined by the shadow (the underlying value of the XuleValue) as it is done for agg_set.
        if key.type in ('set', 'list'):
            if key.shadow_collection in shadow:
                continue
        else:
            if key.value in shadow:
                continue
        
        if key.tags is not None:
            tags.update(key.tags)
        if value.tags is not None:
            tags.update(value.tags)
        if key.facts is not None:
            facts.update(key.facts)     
        if value.facts is not None:
            facts.update(value.facts)                       
        
        dict_values[key] = value
  
        shadow[key.shadow_collection if key.type in ('list', 'set') else key.value] = value.shadow_collection if value.type in ('list', 'set', 'dictionary') else value.value

    return_value = xv.XuleValue(xule_context, frozenset(dict_values.items()), 'dictionary', shadow_collection=frozenset(shadow.items()))
    if len(tags) > 0:
        return_value.tags = tags
    if len(facts) > 0:
        return_value.facts = facts
    return return_value  

def func_taxonomy(xule_context, *args):
    if len(args) == 0:
        if xule_context.model is None:
            # There is no instance doucment
            return xv.XuleValue(xule_context, None, 'none')
        else:
            setattr(xule_context.model, 'taxonomy_name', 'instance')
            return xv.XuleValue(xule_context, xule_context.model, 'taxonomy')
    elif len(args) == 1:
        taxonomy_url = args[0]
        if taxonomy_url.type not in ('string', 'uri'):
            raise XuleProcessingError(_("The taxonomy() function takes a string or uri, found {}.".format(taxonomy_url.type)), xule_context)
        
        other_taxonomy = xule_context.get_other_taxonomies(taxonomy_url.value)
        setattr(other_taxonomy, 'taxonomy_name', taxonomy_url.value)
        return xv.XuleValue(xule_context, other_taxonomy , 'taxonomy')
    else:
        raise XuleProcessingError(_("The taxonomy() function takes at most 1 argument, found {}".format(len(args))))
 
def func_csv_data(xule_context, *args):
    """Read a csv file/url.
    
    Arguments:
        file_url (string or url)
        has_header (boolean) - determines if the first line of the csv file has headers
        type list (list) - list of xule types in the order of the columns of the csv file. This is optional. If not provided, then all the data will be
                           treated as stirngs.
        as_dictionary (boolean) - return the row as a dictionary instead of a list. This is optional.
    """
    if len(args) < 2:
        raise XuleProcessingError(_("The csv-data() function requires at least 2 arguments (file url, has headers), found {} arguments.".format(len(args))), xule_context)
    if len(args) > 4:
        raise XuleProcessingError(_("The csv-data() function takes no more than 3 arguments (file url, has headers, column types, as dictionary), found {} arguments.".format(len(args))), xule_context)

    file_url = args[0]
    has_headers = args[1]

    if file_url.type not in ('string', 'uri'):
        raise XuleProcessingError(_("The file url argument (1st argument) of the csv-dta() function must be a string or uri, found '{}'.".format(file_url.value)), xule_context)
    
    if has_headers.type != 'bool':
        raise XuleProcessingError(_("The has headers argument (2nd argument) of the csv-data() function muset be a boolean, found '{}'.".format(has_headers.type)), xule_context)
    
    if len(args) >= 3:    
        column_types = args[2]
        if column_types.type == 'none':
            ordered_cols = None
        elif column_types.type == 'list':
            ordered_cols = list()
            for col in column_types.value:
                if col.type != 'string':
                    raise XuleProcessingError(_("The type list argument (3rd argument) of the csv-data() function must be a list of strings, found '{}'.".format(col.type)), xule_context)
                ordered_cols.append(col.value)
        else:
            raise XuleProcessingError(_("The type list argument (3rd argument) of the csv-data() fucntion must be list, found '{}'.".format(column_types.type)), xule_context)
    else:
        ordered_cols = None
    
    if len(args) == 4:
        if args[3].type != 'bool':
            raise XuleProcessingError(_("The as dictionary argument (4th argument) of the csv-data() function must be a boolean, found '{}'.".format(args[3].type)), xule_context)
        if args[3].value:
            return_row_type = 'dictionary'
        else:
            return_row_type = 'list'
    else:
        return_row_type = 'list'
        
    if return_row_type == 'dictionary' and not has_headers.value:
        raise XuleProcessingError(_("When the csv-data() function is returning the rows as dictionaries (4th argument), the has headers argument (2nd argument) must be true."), xule_context)
        
    result = list()
    result_shadow = list()
    
    from arelle import PackageManager
    mapped_file_url = PackageManager.mappedUrl(file_url.value)

    # Using the FileSource object in arelle. This will open the file and handle taxonomy package mappings.
    from arelle import FileSource
    file_source = FileSource.openFileSource(file_url.value, xule_context.global_context.cntlr)
    file = file_source.file(file_url.value, binary=True)
    # file is  tuple of one item as a BytesIO stream. Since this is in bytes, it needs to be converted to text via a decoder.
    # Assuming the file is in utf-8. 
    data_source = [x.decode('utf-8') for x in file[0].readlines()]
 
    import csv
    reader = csv.reader(data_source)
    first_line = True
    row_num = 0
    for line in reader:
        row_num += 1
        if first_line and has_headers.value:
            first_line = False
            #skip the headers line
            if return_row_type == 'dictionary':
                # Need to get the names from the first row
                column_names = [x for x in line]
                if len(column_names) != len(set(column_names)):
                    raise XuleProcessingError(_("There are duplicate column names in the csv file. This is not allowed when return rows as dictionaries. File: {}".format(file_url.value)), xule_context)
                
            continue
        
        if return_row_type == 'list':
            result_line = list()
            result_line_shadow = list()
        else: #dictionary
            result_line = dict()
            result_line_shadow = dict()
            
        for col_num, item in enumerate(line):
            if ordered_cols is not None and col_num >= len(ordered_cols):
                raise XuleProcessingError(_("The nubmer of columns on row {} is greater than the number of column types provided in the third argument of the csv-data() function. File: {}".format(row_num, file_url.value)), xule_context)
            
            item_value = convert_file_data_item(item, ordered_cols[col_num] if ordered_cols is not None else None, xule_context)

            if return_row_type == 'list':
                result_line.append(item_value)
                result_line_shadow.append(item_value.value)
            else: #dictonary
                if col_num >= len(column_names):
                    raise xule_context(_("The number of columns on row {} is greater than the number of headers in the csv file. File: {}".format(row_num, 
                                                                                                                                                  mappedUrl if mapped_file_url == file_url.value else file_url.value + ' --> ' + mapped_file_url)), xule_context)

                result_line[xv.XuleValue(xule_context, column_names[col_num], 'string')] = item_value
                result_line_shadow[column_names[col_num]] = item_value.value
                
        if return_row_type == 'list':
            result.append(xv.XuleValue(xule_context, tuple(result_line), 'list', shadow_collection=tuple(result_line_shadow)))
            result_shadow.append(tuple(result_line_shadow))
        else: #dictionary
            result.append(xv.XuleValue(xule_context, frozenset(result_line.items()), 'dictionary', shadow_collection=frozenset(result_line_shadow.items())))
            result_shadow.append(frozenset(result_line_shadow.items()))
          
    return xv.XuleValue(xule_context, tuple(result), 'list', shadow_collection=tuple(result_shadow))
                
def convert_file_data_item(item, type, xule_context):
    
    if type is None:
        return xv.XuleValue(xule_context, item, 'string')
    elif type == 'qname':
        if item.count(':') == 0:
            prefix = '*' # This indicates the default namespace
            local_name = item
        elif item.count(':') == 1:
            prefix, local_name = item.split(':')
        else:
            raise XuleProcessingError(_("While processing a data file, QName in a file can only have one ':', found {} ':'s".format(item.count(':'))), xule_context)
        
        namespace = xule_context.rule_set.getNamespaceUri(prefix)
        
        return xv.XuleValue(xule_context, QName(prefix if prefix != '*' else None, namespace, local_name), 'qname')
    elif type == 'int':
        try:
            return xv.XuleValue(xule_context, int(item), 'int')
        except ValueError:
            raise XuleProcessingError(_("While processing a data file, cannot convert '{}' to an {}.".format(item, type)), xule_context)
    elif type == 'float':
        try:
            return xv.XuleValue(xule_context, float(item), 'float')
        except ValueError:
            raise XuleProcessingError(_("While processing a data file, cannot convert '{}' to a {}.".format(item, type)), xule_context)
    elif type == 'decimal':
        try:
            return xv.XuleValue(xule_context, decimal.Decimal(item), 'decimal')
        except decimal.InvalidOperation:
            raise XuleProcessingError(_("While processing a data file, cannot convert '{}' to a {}.".format(item, type)), xule_context)
    elif type == 'string':
        return xv.XuleValue(xule_context, item, type)        
    else:
        raise XuleProcessingError(_("While processing a data file, {} is not implemented.".format(type)), xule_context)

def func_json_data(xule_context, *args):
    """Read a json file/url.
    
    Arguments:
        file_url (string or url)

    Returns a dictionary/list of the json data.
    """
    
    file_url = args[0]

    if file_url.type not in ('string', 'uri'):
        raise XuleProcessingError(_("The file url argument of the json-dta() function must be a string or uri, found '{}'.".format(file_url.value)), xule_context)

    from arelle import PackageManager
    mapped_file_url = PackageManager.mappedUrl(file_url.value)

    # Using the FileSource object in arelle. This will open the file and handle taxonomy package mappings.
    from arelle import FileSource
    file_source = FileSource.openFileSource(file_url.value, xule_context.global_context.cntlr)
    file = file_source.file(file_url.value, binary=True)
    # file is  tuple of one item as a BytesIO stream. Since this is in bytes, it needs to be converted to text via a decoder.
    # Assuming the file is in utf-8. 
    data_source = [x.decode('utf-8') for x in file[0].readlines()]
    try:
        json_source = json.loads(''.join(data_source))
    #except JSONDecodeError:
    except ValueError:
        raise XuleProcessingError(_("The file '{}' is not a valid JSON file.".format(file_url.value)), xule_context)
    
    x = xv.system_collection_to_xule(json_source, xule_context)
    return xv.system_collection_to_xule(json_source, xule_context)

def func_first_value(xule_context, *args):
    """Return the first non None value.

    This function can take any number of arguments. It will return the first argument that is not None
    """
    for arg in args:
        if arg.value is not None:
            return arg.clone()
    # If here, either there were no arguments, or they were all none
    return xv.XuleValue(xule_context, None, 'unbound')

def func_range(xule_context, *args):
    """Return a list of numbers.

    If there is one argument it is the stop value of the range with the start value of 1.
    If there are 2 arguments, the first is the start and the second is the stop.
    If there are 3 argument, the first is the start, the second the stop and the third is the step.
    All the arguments must be convertible to an integer

    """
    # Check all arguments are numbers.
    for position, arg in enumerate(args, 1):
        if arg.type not in ('int', 'float', 'decimal'):
            ordinal = "%d%s" % (position,"tsnrhtdd"[(position/10%10!=1)*(position%10<4)*position%10::4])
            raise XuleProcessingError(
                _("The {} argument of the 'range' function must be a number, found '{}'".format(ordinal, arg.type)), xule_context)
        if not xv.xule_castable(arg, 'int', xule_context):
            ordinal = "%d%s" % (position, "tsnrhtdd"[(position / 10 % 10 != 1) * (position % 10 < 4) * position % 10::4])
            raise XuleProcessingError(
                _("The {} argument of the 'range' function must be an integer, found '{}'".format(ordinal, arg.value)),
                xule_context)


    if len(args) == 0:
        raise XuleProcessingError(_("The 'range' function requires at least one argument."), xule_context)
    elif len(args) == 1:
        start_num = 1
        stop_num = int(args[0].value) + 1
        step = 1
    elif len(args) == 2:
        start_num = int(args[0].value)
        stop_num = int(args[1].value) + 1
        step = 1
    else:
        start_num = int(args[0].value)
        stop_num = int(args[1].value) + 1
        step = int(args[2].value)

    # Check that the
    number_list = list(range(start_num, stop_num, step))
    number_list_values = tuple(xv.XuleValue(xule_context, x, 'int') for x in number_list)
    return xv.XuleValue(xule_context, number_list_values, 'list', shadow_collection=tuple(number_list))

def func_difference(xule_context, *args):
    '''Difference between 2 sets'''

    if args[0].type != 'set':
        raise XuleProcessingError(
            _("The first argument to the difference() fucntion must be a set, found '{}'".format(args[0].type)),
            xule_context)
    if args[1].type != 'set':
        raise XuleProcessingError(
            _("The second argument to the difference() fucntion must be a set, found '{}'".format(args[1].type)),
            xule_context)

    return xu.subtract_sets(xule_context, args[0], args[1])

def func_symmetric_difference(xule_context, *args):
    '''Symmetric difference between 2 sets'''

    if args[0].type != 'set':
        raise XuleProcessingError(
            _("The first argument to the symmetric_difference() fucntion must be a set, found '{}'".format(args[0].type)),
            xule_context)
    if args[1].type != 'set':
        raise XuleProcessingError(
            _("The second argument to the symmetric_difference() fucntion must be a set, found '{}'".format(args[1].type)),
            xule_context)

    return xu.symetric_difference(xule_context, args[0], args[1])

def func_version(xule_context, *args):
    '''Get the version number of the rule set'''
    version = xule_context.global_context.catalog.get('version', None)
    if version is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, version, 'string')

def func_rule_name(xule_context, *args):
    '''Get the name of the current executing rule'''
    if xule_context.rule_name is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, xule_context.rule_name, 'string')

#the position of the function information
FUNCTION_TYPE = 0
FUNCTION_EVALUATOR = 1
FUNCTION_ARG_NUM = 2
#aggregate only 
FUNCTION_DEFAULT_VALUE = 3
FUNCTION_DEFAULT_TYPE = 4
#non aggregate only
FUNCTION_ALLOW_UNBOUND_ARGS = 3
FUNCTION_RESULT_NUMBER = 4

def built_in_functions():
    funcs = {
#              'all': ('aggregate', agg_all, 1, True, 'bool'),
#              'any': ('aggregate', agg_any, 1, False, 'bool'),
#              'first': ('aggregate', agg_first, 1, None, None),
#              'count': ('aggregate', agg_count, 1, 0, 'int'),
#              'sum': ('aggregate', agg_sum, 1, None, None),
#              'max': ('aggregate', agg_max, 1, None, None), 
#              'min': ('aggregate', agg_min, 1, None, None),
             'list': ('aggregate', agg_list, 1, tuple(), 'list'),
             #'list': ('aggregate', agg_list, 1, None, None),
             'set': ('aggregate', agg_set, 1, frozenset(), 'set'),
             #'set': ('aggregate', agg_set, 1, None, None),
             'dict': ('aggregate', agg_dict, 1, frozenset(), 'dictionary'),
             
             'exists': ('regular', func_exists, 1, True, 'single'),
             'missing': ('regular', func_missing, 1, True, 'single'),
             #'instant': ('regular', func_instant, 1, False, 'single'),
             'date': ('regular', func_date, 1, False, 'single'),
             'duration': ('regular', func_duration, 2, False, 'single'),
             'forever': ('regular', func_forever, 0, False, 'single'),
             'unit': ('regular', func_unit, -2, False, 'single'),
             'entity': ('regular', func_entity, 2, False, 'single'),
             'qname': ('regular', func_qname, 2, True, 'single'),
             'uri': ('regular', func_uri, 1, False, 'single'),
             'time-span': ('regular', func_time_span, 1, False, 'single'),
             'schema-type': ('regular', func_schema_type, 1, False, 'single'),
             'num-to-string': ('regular', func_num_to_string, 1, False, 'single'),
             'mod': ('regular', func_mod, 2, False, 'single'),
             'extension-concepts': ('regular', func_extension_concept, 0, False, 'single'),
             'taxonomy': ('regular', func_taxonomy, -1, False, 'single'),
             'csv-data': ('regular', func_csv_data, -4, False, 'single'),
             'json-data': ('regular', func_json_data, 1, False, 'single'),
             'first-value': ('regular', func_first_value, None, True, 'single'),
             'range': ('regular', func_range, -3, False, 'single'),
             'difference': ('regular', func_difference, 2, False, 'single'),
             'symmetric_difference': ('regular', func_symmetric_difference, 2, False, 'single'),
             'version': ('regular', func_version, 0, False, 'single'),
             'rule-name': ('regular', func_rule_name, 0, False, 'single')
             }    

    try:
        funcs.update(xrf.BUILTIN_FUNCTIONS)
    except NameError:
        pass
    
    return funcs

BUILTIN_FUNCTIONS = built_in_functions()



#BUILTIN_FUNCTIONS = {}
