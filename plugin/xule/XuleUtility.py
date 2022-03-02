"""XuleUtility

Xule is a rule processor for XBRL (X)brl r(ULE). 

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

$Change: 23339 $
DOCSKIP
"""
from arelle.ModelRelationshipSet import ModelRelationshipSet
import collections
import json 
import os
import inspect
import glob
import re
import shutil
from contextlib import contextmanager
from . import XuleConstants as xc
from . import XuleRunTime as xrt
from .XuleRunTime import XuleProcessingError
# XuleValue is a module. It is imported in the _imports() function to avoid a circular relative import error.
XuleValue = None
XuleProperties = None


def version(plugin_init_files=__file__):
    change_numbers = set()

    if plugin_init_files == __file__:
        xule_mod_pattern = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(plugin_init_files), '*.py'))
        files_to_check = glob.glob(xule_mod_pattern)
    elif isinstance(plugin_init_files, str):
        files_to_check = (plugin_init_files,) # change the string to a tuple
    else:
        files_to_check = plugin_init_files

    for mod_file_name in files_to_check:
        with open(mod_file_name, 'r') as mod_file:
            file_text = mod_file.read()
            match = re.search(r'\$' + r'Change:\s*(\d+)\s*\$', file_text)
            if match is not None:
                change_numbers.add(int(match.group(1)))
    
    if len(change_numbers) == 0:
        return ''
    else:
        return str(max(change_numbers))
    
    return ''

def _imports():
    """Imports
    
    This function handles the imports. These imports are here to prevent circular relative import errors which happens in version prior to 3.5.
    """
    global XuleValue
    if XuleValue is None:
        from . import XuleValue
        
    global XuleProperties
    if XuleProperties is None:
        from . import XuleProperties

def add_sets(xule_context, left, right):
    _imports()
    new_set_values = list(left.value)
    new_shadow = list(left.shadow_collection)

    for item in right.value:
        if item.value not in new_shadow:
            new_shadow.append(item.shadow_collection if item.type in ('set','list','dictionary') else item.value)
            new_set_values.append(item)
    
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def subtract_sets(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in left.value:
        left_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if left_compute_value not in right.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
            
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def symetric_difference(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in left.value:
        compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if compute_value not in right.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
            
    for item in right.value:
        compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if compute_value not in left.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)                    

    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def intersect_sets(xule_context, left, right):
    _imports()
    new_set_values = set()
    new_shadow = set()
    
    for item in right.value:
        right_compute_value = item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value
        if right_compute_value in left.shadow_collection:
            new_set_values.add(item)
            new_shadow.add(item.shadow_collection if item.type in ('set', 'list', 'dictionary') else item.value)
    
    return XuleValue.XuleValue(xule_context, frozenset(new_set_values), 'set', shadow_collection=frozenset(new_shadow))

def resolve_role(role_value, role_type, dts, xule_context):
    """Resolve a role.
    
    A role is either a string, uri or a non prefixed qname. If it is a string or uri, it is a full arcrole. If it is
    a non prefixed qname, than the local name of the qname is used to match an arcrole that ends in 'localName'. If more than one arcrole is found then
    and error is raise. This allows short form of an arcrole i.e parent-child.
    """
    _imports()
    if role_value.value.prefix is not None:
        raise XuleProcessingError(_("Invalid {}. {} should be a string, uri or short role name. Found qname with value of {}".format(role_type, role_type.capitalize(), role_value.format_value())))
    else:
        if role_type == 'arcrole' and role_value.value.localName in xc.DIMENSION_PSEDDO_ARCROLES:
            return role_value.value.localName
        # Check that the dictionary of short arcroles is in the context. If not, build the diction are arcrole short names
        short_attribute_name = 'xule_{}_short'.format(role_type)
        if not hasattr(dts, short_attribute_name):
            if role_type == 'arcrole':
                setattr(dts, short_attribute_name, XuleProperties.CORE_ARCROLES.copy())
                dts_roles = dts.arcroleTypes
            else:
                setattr(dts, short_attribute_name, {'link': 'http://www.xbrl.org/2003/role/link'})
                dts_roles = dts.roleTypes
            
            short_role_dict = getattr(dts, short_attribute_name)
            for role in dts_roles:
                short_name = role.split('/')[-1] if '/' in role else role
                if short_name in short_role_dict:
                    short_role_dict[short_name] = None # indicates that there is a dup shortname
                else:
                    short_role_dict[short_name] = role
        
        short_role_dict = getattr(dts, short_attribute_name)
        short_name = role_value.value.localName
        if short_name not in short_role_dict:
            return None
            #raise XuleProcessingError(_("The {} short name '{}' does not match any arcrole.".format(role_type, short_name)))
        if short_name in (XuleProperties.CORE_ARCROLES if role_type == 'arcrole' else {'link': 'http://www.xbrl.org/2003/role/link'}) and short_role_dict[short_name] is None:
            raise XuleProcessingError(_("A taxonomy defined {role} has the same short name (last portion of the {role}) as a core specification {role}. " 
                                        "Taxonomy defined {role} is '{tax_role}'. Core specification {role} is '{core_role}'."
                                        .format(role=role_type, 
                                                tax_role=getattr(dts, short_attribute_name)[short_name], 
                                                core_role=XuleProperties.CORE_ARCROLES[short_name] if role_type == 'arcrole' else 'http://www.xbrl.org/2003/role/link')))
        if short_name in short_role_dict and short_role_dict[short_name] is None:
            raise XuleProcessingError(_("The {} short name '{}' resolves to more than one arcrole in the taxonomy.".format(role_type, short_name)))
        
        return short_role_dict[short_name]

def role_uri_to_model_role(model_xbrl, role_uri):
    _imports()
    if role_uri in model_xbrl.roleTypes:
        return model_xbrl.roleTypes[role_uri][0]
    else:
        return XuleValue.XuleRole(role_uri)

def arcrole_uri_to_model_role(model_xbrl, arcrole_uri):
    _imports()
    if arcrole_uri in model_xbrl.arcroleTypes:
        return model_xbrl.arcroleTypes[arcrole_uri][0]
    else:
        return XuleValue.XuleArcrole(arcrole_uri)

# def base_dimension_sets(dts):
#     """Get the Xule base dimension sets.
#     
#     This is like the baseSets dictionary of a model. The base dimension set is a dictionary keyed by the drs role and hypercube. The drs role is the role of the initial 'all' relationship or the target role of the initial
#     'all' relationship if there is a target role. The value of the dictionary is a set of the 'all' relationships.
#     """
#     _imports() 
#     if not hasattr(dts, 'xuleBaseDimensionSets'):
#         dts.xuleBaseDimensionSets = collections.defaultdict(set)
#         for base_set in dts.baseSets:
#             if (base_set[XuleProperties.NETWORK_ARCROLE] in('http://xbrl.org/int/dim/arcrole/all', 
#                                                             'http://xbrl.org/int/dim/arcrole/notAll') and 
#                 base_set[XuleProperties.NETWORK_ROLE] is not None and 
#                 base_set[XuleProperties.NETWORK_LINK] is not None and 
#                 base_set[XuleProperties.NETWORK_ARC] is not None):
#                 # This is an 'all' dimension base set find the hypercubes
#                 relationship_set =dts.relationshipSets.get(base_set,
#                                                             ModelRelationshipSet(dts, 
#                                                                                base_set[XuleProperties.NETWORK_ARCROLE],
#                                                                                base_set[XuleProperties.NETWORK_ROLE],
#                                                                                base_set[XuleProperties.NETWORK_LINK],
#                                                                                base_set[XuleProperties.NETWORK_ARC]))
#                 
#                 for rel in relationship_set.modelRelationships:
#                     drs_role = rel.targetRole or base_set[XuleProperties.NETWORK_ROLE]
#                     hypercube = rel.toModelObject
#                     dts.xuleBaseDimensionSets[(drs_role, hypercube)].add(rel)
# 
#     return dts.xuleBaseDimensionSets
#
# def dimension_sets(dts):
#     """The dimension sets in a dts.
#     
#     A dimension set is identified by a drs role and hypercube. 
#     """
#     _imports()
#     if not hasattr(dts, 'xuleDimensionSets'):
#         dts.xuleDimensionSets = dict()
#     
#     return dts.xuleDimensionSets
# 
# def dimension_set(dts, dimension_set_info):
#     _imports()
#     if dimension_set_info not in dimension_sets(dts):
#         dimension_sets(dts)[dimension_set_info] = XuleValue.XuleDimensionCube(dts, *dimension_set_info)
# 
#     return dimension_sets(dts)[dimension_set_info]                                                         
                                                                                        

def determine_rule_set(model_xbrl, cntlr, rule_set_map_name):
    """Determine which rule set to use based on the instance.
    
    :param model_xbrl: Arelle model of the instance
    :type model_xbrl: ModelXbrl
    :param cntlr: Arelle controller
    :type cntlr: Cntlr
    """
    # Open the rule set map file. This is a json file that maps namespace uris to a location for a rule set.
    rule_set_map = get_rule_set_map(cntlr, rule_set_map_name)

    if rule_set_map is not None:
        # Go through the list of namespaces in the rule set map
        for mapped_namespace, rule_set_location in rule_set_map.items():
            if mapped_namespace in model_xbrl.namespaceDocs:
                return rule_set_location
    
#     # This is only reached if a rule set location was not found in the map.
#     rule_set_map_file_name = get_rule_set_map_file_name(cntlr, xc.RULE_SET_MAP)
#     model_xbrl.log('ERROR', 'xule', "Cannot determine which rule set to use for the filing. Check the rule set map at '{}'.".format(rule_set_map_file_name))
#     #raise XuleProcessingError(_("Cannot determine which rule set to use for the filing. Check the rule set map at '{}'.".format(rule_set_map_file_name)))

def get_rule_set_map(cntlr, map_name):
    try:
        with get_rule_set_map_file(cntlr, map_name) as rule_set_map_file:
            # An ordered dict is used to keep the order of the key/value pairs in the json object.
            return json.load(rule_set_map_file, object_pairs_hook=collections.OrderedDict)
    except ValueError:
        rule_set_map_file_name = get_rule_set_map_file_name(cntlr, map_name)
        raise XuleProcessingError(_("Map file does not appear to be a valid JSON file. File: {}".format(rule_set_map_file_name)))

@contextmanager
def get_rule_set_map_file(cntlr, map_name, mode='r'):
    """Get the location of the rule set map
    
    The rule set map will be in the application data folder for the xule plugin. An initial copy is in the
    plugin folder for xule. If the map is not found in the application data folder, the initial copy is copied
    to the application folder.
    
    :param cntlr: Arelle controler
    :type cntlr: Cntlr
    :returns: Rule set map file location
    :rtype: string
    """
    rule_set_map_file_name = get_rule_set_map_file_name(cntlr, map_name)
    if not os.path.isfile(rule_set_map_file_name):
        # See if there is an initial copy in the plugin folder
        if os.path.isabs(map_name):
            initial_copy_file_name = map_name
        else:
            current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
            initial_copy_file_name = os.path.join(current_dir, map_name)        
            if not os.path.isfile(initial_copy_file_name):
                raise xrt.XuleMissingRuleSetMap("Cannot find rule set map file for '{}'. This file is needed to determine which rule set to use.".format(map_name))
            os.makedirs(os.path.dirname(rule_set_map_file_name), exist_ok=True)
            shutil.copyfile(initial_copy_file_name, rule_set_map_file_name)
    
    # Open the rule set map file
    try:
        rule_set_map_file_object = open(rule_set_map_file_name, mode)
    except:
        raise XuleProcessingError(_("Unable to open map file at {}".format(rule_set_map_file_name)))
    
    yield rule_set_map_file_object
    # Clean up
    rule_set_map_file_object.close()

def get_rule_set_map_file_name(cntlr, map_name):
    if cntlr.userAppDir is None:
        raise XuleProcessingError(_("Arelle does not have a user application data directory. Cannot locate map file"))            
    return os.path.join(cntlr.userAppDir, 'plugin', 'xule', map_name)

def update_rule_set_map(cntlr, new_map_name, map_name, overwrite=False):
    
    new_map = open_json_file(cntlr, new_map_name)
    
    if overwrite:
        rule_set_map = new_map
    else:
        # update
        rule_set_map = get_rule_set_map(cntlr, map_name)
        rule_set_map.update(new_map)

    #update the rule set map
    with get_rule_set_map_file(cntlr, map_name, 'w') as rule_set_file: 
        json.dump(rule_set_map, rule_set_file)
    if overwrite:
        cntlr.addToLog(_("Map file replaced - {}".format(get_rule_set_map_file_name(cntlr, map_name))), "xule")
    else:
        cntlr.addToLog(_("Map file updated - {}".format(get_rule_set_map_file_name(cntlr, map_name))), "xule")

def open_json_file(cntlr, file_name):
    # Open the new map
    from arelle import FileSource
    file_source = FileSource.openFileSource(file_name, cntlr)
    # FileSource does not handle reading JSPON files. If the file is not binary, FileSource assumes it is XML
    # Read the file as binary and then decode.
    file_object = file_source.file(file_name, binary=True)[0] 
    
    file_content = file_object.read().decode()
    try:
        return json.loads(file_content, object_pairs_hook=collections.OrderedDict)
    except ValueError:
        raise XuleProcessingError(_("New map file does not appear to be a valid JSON file. File: {}".format(file_name)))

def reset_rule_set_map(cntlr, map_name):
    rule_set_map_file_name = get_rule_set_map_file_name(cntlr, map_name)
    # delete the rule set map file
    try:
        os.remove(rule_set_map_file_name)
    except OSError:
        pass
    
    # get the rule set map. This will copy the default file when it doesn't exist in the
    # users appdata (which was just deleted)
    with get_rule_set_map_file(cntlr):
        pass
    
    cntlr.addToLog(_("Map file reset"), "xule")

def get_element_identifier(model_object):
    if model_object is not None:
        if model_object.id is not None:
            return (model_object.modelDocument.uri + "#" + model_object.id, model_object.sourceline)
        else:
            #need to build the element scheme
            location = get_tree_location(model_object)
            return (model_object.modelDocument.uri + "#element(" + location + ")", model_object.sourceline)
            
def get_tree_location(model_object):
    
    parent = model_object.getparent()
    if parent is None:
        return "/1"
    else:
        prev_location = get_tree_location(parent)
        return prev_location + "/" + str(parent.index(model_object) + 1)

def get_rule_set_compatibility_version():

    current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    compatibility_file_name = os.path.join(current_dir, xc.RULE_SET_COMPATIBILITY_FILE)        
    if not os.path.isfile(compatibility_file_name):
        raise xrt.XuleProcessingError("Cannot find rule set compatibility file for '{}'. This file is needed to determine which rule set to use.".format(compatibility_file_name))
    try:
        with open(compatibility_file_name, 'r') as compatibility_file:
            compatibility_json =  json.load(compatibility_file)
            return compatibility_json.get('versionControl')
    except ValueError:
        raise XuleProcessingError(_("Rule set compatibility file does not appear to be a valid JSON file. File: {}".format(xc.RULE_SET_COMPATIBILITY_FILE))) 