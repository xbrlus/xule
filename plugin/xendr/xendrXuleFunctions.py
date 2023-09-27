'''
xendrXuleFunctions

This file contains xule functions that are added to the xule processor to support xendr

Reivision number: $Change: $
'''
from arelle.ModelInstanceObject import ModelFact
from arelle.ModelInstanceObject import ModelResource
import json

def get_footnotes_from_fact_ids(xule_context, *args):
    from .xule import XuleValue as xv
    from .xule.XuleRunTime import XuleProcessingError
    # This function will take a string containing object ids and convert them to a list of 
    # footnote objects. the object ids are separated by whitespace
    # This is used for Xendr when processing footnotes
    if args[0].type != 'string':
        raise XuleProcessingError(_("Function xendr-get-footnotes-from-fact-ids() requires a string argument, found {}".format(args[0].type)))
    
    fact_ids = args[0].value.split(',')
    # Get the facts from the ids that were passed in
    model_facts = [xule_context.model.modelObject(x.strip()) for x in fact_ids] # split by whitespace
    xule_facts = tuple(xv.XuleValue(xule_context, x, 'fact') for x in model_facts if x is not None) 
    return xv.XuleValue(xule_context, xule_facts, 'list')


    # Get the footnote base sets
    rel_sets = [xule_context.model.relationshipSet(x) for x in xule_context.model.baseSets.keys() if x[2] is not None 
                                                               and x[2].clarkNotation == '{http://www.xbrl.org/2003/linkbase}footnoteLink' 
                                                               and None not in x]

    # Go through the facts and get the footnotes
    footnotes = []
    shadow = []
    for fact in model_facts:
        for rel_set in rel_sets:
            for rel in rel_set.fromModelObject(fact):
                footnote_resource = rel.toModelObject
                footnote_value = [
                    rel.arcrole,
                    getattr(footnote_resource, 'role', None), # if the to object is a fact, it won't have a role
                    footnote_resource.get('{http://www.w3.org/XML/1998/namespace}lang')
                ]
                if isinstance(footnote_resource, ModelFact):
                    footnote_value.append('fact')
                elif isinstance(footnote_resource, ModelResource):
                    footnote_value.append('resource')
                else:
                    raise XuleProcessingError(_("Found enxpected type of footnote (not a footnote resource nor a fact)."), xule_context)
                
                footnote_value.append(footnote_resource)
                footnotes.append(xv.XuleValue(xule_context, tuple(footnote_value), 'footnote'))
                shadow.append(tuple(footnote_value))

    return xv.XuleValue(xule_context, tuple(footnotes), 'list', shadow_collection=shadow)

def get_internal_model_id(xule_context, *args):
    from .xule import XuleValue as xv
    from .xule.XuleRunTime import XuleProcessingError
    if args[0].fact is None:
        return xv.XuleValue(xule_context, None, 'none')
    else:
        return xv.XuleValue(xule_context, args[0].fact.objectId(), 'string')
    
def format_footnote_info(xule_context, *args):
    from .xule import XuleValue as xv
    if args[0].type != 'footnote':
        raise XuleProcessingError(_(f"Function xendr-format-footnote() requires a footnote object as the argument, but found {args[0].type}"), xule_context)
    footnote_info = {'type': args[0].value[xv.FOOTNOTE_TYPE],
                     'content': args[0].value[xv.FOOTNOTE_CONTENT].objectId(),
                     'fact': args[0].value[xv.FOOTNOTE_FACT].objectId(),
                     'arcrole': args[0].value[xv.FOOTNOTE_ARCROLE]}
    return xv.XuleValue(xule_context, json.dumps(footnote_info), 'string')
    