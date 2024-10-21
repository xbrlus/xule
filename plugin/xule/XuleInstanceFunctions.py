"""XuleInstanceFunctions

Xule is a rule processor for XBRL (X)brl r(ULE). 

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2024 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change$
DOCSKIP
"""

from . import XuleValue as xv
from .XuleRunTime import XuleProcessingError
from .XuleModelIndexer import index_model
from .XuleUtility import get_model_manager_for_import
from arelle import ModelXbrl, ModelDocument, FileSource, ModelValue
from arelle.PrototypeInstanceObject import DimValuePrototype
import datetime
import os.path
import tempfile

BUILT_IN_ASPECTS = ('concept', 'entity', 'unit', 'period', 'language')

def func_instance(xule_context, *args):
    if len(args) == 0:
        # Return the default instance which is the instance loaded by Arelle
        if xule_context.model is None:
            # There is no instance doucment
            return xv.XuleValue(xule_context, None, 'none')
        else:
            return xv.XuleValue(xule_context, xule_context.model, 'instance')
    elif len(args) == 1:
        instance_url = args[0]
        if instance_url.type not in ('string', 'uri'):
            raise XuleProcessingError(_("The instance() function takes a string or uri, found {}.".format(instance_url.type)), xule_context)
        
        start = datetime.datetime.today()
        instance_filesource = FileSource.openFileSource(instance_url.value, xule_context.global_context.cntlr)            
        #modelManager = ModelManager.initialize(xule_context.global_context.cntlr)
        #modelManager = xule_context.global_context.cntlr.modelManager
        import_model_manager = get_model_manager_for_import(xule_context.global_context.cntlr)
        instance_model = import_model_manager.load(instance_filesource)
        if 'IOerror' in instance_model.errors:
            raise XuleProcessingError(_("Instance {} not found.".format(instance_url)))
        end = datetime.datetime.today()
        
        xule_context.global_context.cntlr.addToLog("Instance Loaded. Load time %s from '%s' " % (end - start, instance_url.value))            
        
        index_model(xule_context, instance_model)

        return xv.XuleValue(xule_context, instance_model, 'instance')
    else:
        raise XuleProcessingError(_("The instance() function takes at most 1 argument, found {}".format(len(args))))

def func_new_instance(xule_context, *args):
    '''Create a new instance
    
    There are 3 arguments:
    Name (required)
    List/set of schema refs (required)
    list/set of arcrole or role refs'''

    if len(args) == 0:
        raise XuleProcessingError(_("new_instance() function requires at lease 2 arguments, name and list/set of schema refs. Found no arguments"), xule_context)
    elif len(args) == 1:
        raise XuleProcessingError(_("missing list/set of schema refs for new_instance() function"), xule_context)

    if args[0].type in ('string', 'uri'):
        inst_name = args[0].value
    else:
        raise XuleProcessingError(_("name of new_instance() function must be a string or uri, found {}".format(args[0].type)), xule_context)

    
    if args[1].type in ('set', 'list'):
        schema_refs = list(args[1].shadow_collection)
    elif args[1].type in ('string', 'uri'):
        schema_refs = [args[1].value,] # list of one
    else: 
        raise XuleProcessingError(_("list of schema references for new_instance() function must be a set, list, string or uri, found {}".format(args[1].type)), xule_context)

    if len(args) == 3:
        # There are arcrole/role refs
        if args[2].type in ('set', 'list'):
            schema_refs.extend(list(args[2].shadow_collection))
        elif args[2].type in ('string', 'uri'):
            schema_refs.apend(args[2].value)
        else:
            raise XuleProcessingError(_("List of arcrole/role refs for new_instance() fucntion must be a set, list, string or uri, found{}".format(args[2].type)), xule_context)

    # Create the model
    #model_manager = xule_context.model.modelManager
    model_manager = get_model_manager_for_import(xule_context.global_context.cntlr)
    # Need a filesource for the new instance document. Creating a temporary directory to put the file in
    temp_directory = tempfile.TemporaryDirectory()
    inst_file_name = os.path.join(temp_directory.name, f'{inst_name}.json')
    file_source = FileSource.FileSource(inst_file_name)
    new_model = ModelXbrl.ModelXbrl(model_manager, file_source)
    # Attach the file source to the model
    new_model.fileSource = file_source
    # Attached the temp direcory to the model to keep it from being destroyed. When garbage collection happens, the directory and its
    # contents will be removed.
    new_model.xule_temp_instance_directory = temp_directory
    inst_doc = ModelDocument.create(new_model, ModelDocument.Type.INSTANCE, inst_file_name, schema_refs, isEntry=True)
    new_model.modelDocument = inst_doc
    # # test that a fact can be created
    # from arelle.ModelValue import qname
    # import datetime
    # q = qname('http://fasb.org/us-gaap/2022', 'Assets')
    # _cntx = new_model.createContext(
    #                     'http://test',
    #                     'PhillipCompany',
    #                     'instant',
    #                     datetime.datetime(2021,12,31),
    #                     datetime.datetime(2022,12,31),
    #                     None, # no dimensional validity checking (like formula does)
    #                     [], [], [],
    #                     id='c01')
    # _unit = new_model.createUnit([qname('http://www.xbrl.org/2003/iso4217', 'usd')], [], id='u01')

    # atts = {'id': 'f01',
    #         'contextRef': 'c01',
    #         'unitRef': 'u01'}
    
    # fact = new_model.createFact(q, atts, '200')

    return xv.XuleValue(xule_context, new_model, 'instance')

def func_fact(xule_context, *args):
    '''Create a fact
    
    Arguments:
        Instance - instance object
        Value
        Aspects - dictionary
        Footnotes - list/set of footnotes
    '''

    if len(args) not in (3,4):
        raise XuleProcessingError(_("fact() fucntion requires at least 3 arguments but no more than 4, found {}."
                                    "Arguments are instance, value, aspects, footnotes(optional).".format(len(args))), xule_context)

    if args[0].type != 'instance':
        raise XuleProcessingError(_("the first argument of the fact() function must be an instance, found {}".format(args[0].type)), xule_context)
    else:
        instance = args[0]
    
    value = args[1]

    if args[2].type!= 'dictionary':
        raise XuleProcessingError(_("The 3rd argument of the fact() function must be a dictionary, found {}".format(args[2].type)), xule_context)
    else:
        aspects = args[2]

    if len(args) == 4:
        raise XuleProcessingError(_("fact() function currenlty does not support footnotes"), xule_context)

    concept_qname = get_concept_qname(aspects, instance, xule_context)
    fact_attrs = {}
    fact_id = get_fact_id(aspects, instance, xule_context)
    if fact_id is not None:
        fact_attrs['id'] = fact_id
    context_id = get_context(aspects, instance, xule_context)
    fact_attrs['contextRef'] = context_id
    unit_id = get_unit(aspects, instance, concept_qname, xule_context)
    if unit_id is not None:
        fact_attrs['unitRef'] = unit_id

    model_fact = instance.value.createFact(concept_qname, fact_attrs, str(value.value))

    # TODO the value should be convered based on the data type of the concept. For example if it is a decimal concept and the value is an intenger, it should be converted and the type shoulde be 'decimal'
    fact_value =  xv.XuleValue(xule_context, value.value, value.type)
    fact_value.fact = model_fact

    return fact_value

    # # test that a fact can be created
    # from arelle.ModelValue import qname
    # import datetime
    # q = qname('http://fasb.org/us-gaap/2022', 'Assets')
    # _cntx = new_model.createContext(
    #                     'http://test',
    #                     'PhillipCompany',
    #                     'instant',
    #                     datetime.datetime(2021,12,31),
    #                     datetime.datetime(2022,12,31),
    #                     None, # no dimensional validity checking (like formula does)
    #                     [], [], [],
    #                     id='c01')
    # _unit = new_model.createUnit([qname('http://www.xbrl.org/2003/iso4217', 'usd')], [], id='u01')

    # atts = {'id': 'f01',
    #         'contextRef': 'c01',
    #         'unitRef': 'u01'}
    
    # fact = new_model.createFact(q, atts, '200')


def get_concept_qname(aspects, instance, xule_context):
    if 'concept' not in aspects.shadow_keys:
        raise XuleProcessingError(_("fact() function requires a 'concept' aspect"), xule_context)
    else:
        concept_value = aspects.value_dictionary[aspects.shadow_keys['concept']]

    if concept_value.type == 'concept':
        concept_qname = concept_value.value.qname
    elif concept_value.type == 'qname':
        concept_qname =  concept_value.value
    else:
        raise XuleProcessingError(_("Concept for fact() fucntion is not the right type. Expecting 'concept' or 'qname', found '{}'".format(concept_value.type)), xule_context)

    # check the concept name is in the taxonomy
    if concept_qname not in instance.value.qnameConcepts:
        raise XuleProcessingError(_("Trying to create fact for concpet {} but it is not in the dts for the instance".format(concept_qname.clarkNotation)), xule_context)
    
    return concept_qname

def get_fact_id(aspects, instance, xule_context):
    if 'id' in aspects.shadow_keys:
        fact_id = aspects.value_dictionary[aspects.shadow_keys['id']]
        # should check that the fact id is not already used
    else:
        # TODO should a fact id be auto generated
        fact_id = None

    return fact_id

def get_context(aspects, instance, xule_context):
    if 'period' not in aspects.shadow_keys:
        raise XuleProcessingError(_("Fact requires a period"), xule_context)
    else:
        period_value = aspects.value_dictionary[aspects.shadow_keys['period']]

    if 'entity' not in aspects.shadow_keys:
        raise XuleProcessingError(_("Fact requires an entity"), xule_context)
    else:
        entity_value = aspects.value_dictionary[aspects.shadow_keys['entity']]

    context_key = [entity_value.value[0], entity_value.value[1]]
    if period_value.type == 'forever':
        context_key.append('forever')
        context_key.append(None)
        context_key.append(None)
    elif period_value.type == 'instant':
        context_key.append('instant')
        context_key.append(None)
        context_key.append(period_value.value)
    elif period_value.type == 'duration':
        context_key.append('duration')
        context_key.append(period_value.value[0])
        context_key.append(period_value.value[1])
    
    #context_key.append(None) #priItems - not sure what this is
    context_dims = get_context_dimensions(aspects, instance, xule_context)
    context_key.append(context_dims)
    context_key.append([]) # non dim segment
    context_key.append([]) # non dim scenario
    # see if there is an exsiting context
    model_context = instance.value.matchContext(*context_key)
    if model_context is None:
        create_key = context_key[:5] + [None,] + context_key[5:]
        model_context = instance.value.createContext(*create_key)

    return model_context.id

def get_context_dimensions(aspects, instance, xule_context):
    result = dict()
    for dim_name in aspects.shadow_keys:
        if dim_name not in BUILT_IN_ASPECTS:
            # The dim_name must be a dimension concept in the taxonomy
            dim_concept = instance.value.qnameConcepts.get(dim_name)
            if dim_concept is None:
                raise XuleProcessingError(_("Dimension {} for fact() function is not in the taxonommy".format(dim_name.clarkNotation)), xule_context)
            if ModelValue.qname('http://xbrl.org/2005/xbrldt', 'dimensionItem') not in dim_concept.substitutionGroupQnames:
                raise XuleProcessingError(_("Dimension {} for fact() fucntion is not a xbrldt:dimensionItem".format(dim_concept.substitutionGroupQname)), xule_context)
            # TODO could verify that the dimension is valid for the table
            
            dim_value = aspects.value_dictionary[aspects.shadow_keys[dim_name]]
            # TODO need to check for typed dimensions
            # Copied from loadFromOIM.py line 2354
            #nameDims[dimQname] = DimValuePrototype(modelXbrl, None, dimQname, mem, "segment")
            result[dim_name] = DimValuePrototype(instance.value, None, dim_name, dim_value.value, "segment")
            
    return result

def get_unit(aspects, instance, concept_qname, xule_context):

    concept = instance.value.qnameConcepts[concept_qname]
    if not concept.isNumeric:
        return None # non numerics don't get a unit

    if 'unit' not in aspects.shadow_keys:
        raise XuleProcessingError(_("Numeric fact requires a unit"), xule_context)
    else:
        unit_value = aspects.value_dictionary[aspects.shadow_keys['unit']]

    unit_key = (unit_value.value.numerator, unit_value.value.denominator)
    model_unit = instance.value.matchUnit(*unit_key)
    if model_unit is None:
        model_unit = instance.value.createUnit(*unit_key)
    
    return model_unit.id

def built_in_functions():
    funcs = {'fact': ('regular', func_fact, -4, False, 'single'),
             'new_instance':('regular', func_new_instance, -3, False, 'single'),
             'instance': ('regular', func_instance, -1, False, 'single')}
    
    return funcs

BUILTIN_FUNCTIONS = built_in_functions()