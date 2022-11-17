'''
Reivision number: $Change: 23365 $
'''

from arelle import FileSource
from arelle import ModelManager
from arelle import PluginManager

import collections
import copy
import datetime
import io
import json
import logging
import optparse
import os
import re
import tempfile


# This will hold the xule plugin module
_xule_plugin_info = None

_XBRLI_NAMESPACE = 'http://www.xbrl.org/2003/instance'
_INSTANCE_OUTPUT_ATTRIBUTES = {'instance-name', 'instance-taxonomy'}
_FACT_OUTPUT_ATTRIBUTES = {'fact-value', 
                           'fact-concept',
                           'fact-unit',
                           'fact-entity',
                           'fact-period',
                           'fact-decimals',
                           'fact-dimensions',
                           'fact-instance',
                           'fact-alignment'
}
_INSTANCE_BASE_STRING = '''{
    "documentInfo": {
        "documentType": "https://xbrl.org/2021/xbrl-json",
        "features": {
            "xbrl:canonicalValues": true
        },
        "namespaces": {
            "iso4217": "http://www.xbrl.org/2003/iso4217",
            "utr": "http://www.xbrl.org/2009/utr",
            "xbrl": "https://xbrl.org/2021",
            "xbrli": "http://www.xbrl.org/2003/instance"
        },
        "linkGroups": {
            "_": "http://www.xbrl.org/2003/role/link"
        },
        "taxonomy": []
    },
    "facts": {}
}
'''

_TAXONOMY_MODEL_START = '''
    <xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:link="http://www.xbrl.org/2003/linkbase" 
                xmlns:xlink="http://www.w3.org/1999/xlink" 
                xmlns:xml="http://www.w3.org/XML/1998/namespace">
'''

_QNAME_MATCH = re.compile('^{(.+)}(.+)$')
# This unit_match will contain the numerator in group(1) and the denominator in group(4)
_UNIT_MATCH = re.compile('({[^}]+}[^{]+(\*{[^}]+}[^{]+)*)(/({[^}]+}[^{]+(\*{[^}]+}[^{]+)*))?')

class XinceException(Exception):
    pass

class XinceNSMap:
    def __init__(self):
        self._map_by_ns = dict()
        self._map_by_prefix = dict()
        self._last_ns_number = collections.defaultdict(int)
        self._used_ns = set()

    @property
    def map_by_namespace(self):
        return copy.copy(self._map_by_ns)

    @property
    def map_by_prefix(self):
        return copy.copy(self._map_by_prefix)

    @property
    def used_map_by_namespace(self):
        return {k: v for k, v in self._map_by_ns.items() if k in self._used_ns}
    
    @property
    def used_map_by_prefix(self):
        return {k: v for k, v in self._map_by_prefix.items() if v in self._used_ns}

    def add(self, prefix, namespace):
        if self._map_by_prefix.get(prefix) == namespace:
            return # there is nothing to do, the prefix and namespace are already in the map
        elif prefix in self._map_by_prefix or namespace in self._map_by_ns:
            raise XinceException(f"{prefix}:{namespace} are already in the XinceNSMap")
        else:
            self._map_by_ns[namespace] = prefix
            self._map_by_prefix[prefix] = namespace

    def add_or_get_namespace(self, namespace, prefix='ns'):
        if self.get_prefix(namespace) is None:
            while f"{prefix}{self._last_ns_number[prefix] if self._last_ns_number[prefix] > 0 else ''}" in self._map_by_prefix:
                self._last_ns_number[prefix] += 1
            new_prefix = f"{prefix}{self._last_ns_number[prefix] if self._last_ns_number[prefix] > 0 else ''}"
            self._map_by_ns[namespace] = new_prefix
            self._map_by_prefix[new_prefix] = namespace

        return self.get_prefix(namespace)
 
    def get_namespace(self, prefix):
        return self._map_by_prefix.get(prefix)

    def get_prefix(self, namespace):
        return self._map_by_ns.get(namespace)

    def mark_namespace_as_used(self, namespace):
        if namespace in self._map_by_ns:
            self._used_ns.add(namespace)

class XinceQname:
    def __init__(self, ns, local_name):
        self.namespace = ns
        self.local_name = local_name

    @property
    def clark(self):
        return f"{{{self.namespace}}}{self.local_name}"

    def __repr__(self):
        return self.clark

    def prefix(self, nsmap, mark=False):
        '''nsmap is a dictionary of namespaces to prefixes'''
        if mark:
            self.mark_as_used(nsmap)
        return f'{nsmap.add_or_get_namespace(self.namespace)}'

    def serialize(self, nsmap, mark=False, format='json'):
        if mark:
            self.mark_as_used(nsmap)
        return f'{self.prefix(nsmap)}:{self.local_name}'

    def mark_as_used(self, nsmap):
        nsmap.mark_namespace_as_used(self.namespace)

class XinceEntity:
    def __init__(self, scheme, identifier):
        self.scheme = scheme
        self.identifier = identifier

    def __repr__(self):
        return self.serialize()

class XinceUnit:
    def __init__(self, numerators, denominators):
        '''numerators and denominators must be lists of XinceQnames'''
        if not (isinstance(numerators, list) and all((isinstance(x, XinceQname) for x in numerators))):
            raise XinceException("Numerators must be XinceQnames")
        if denominators is not None and not(isinstance(denominators, list) and all((isinstance(x, XinceQname) for x in denominators))):
            raise XinceException("Denominators must be XinceQnames")

        self.numerators = numerators
        self.denominators = denominators

    @property
    def is_pure(self):
        return self.denominators is None and len(self.numerators) == 1 and self.numerators[0].clark == '{http://www.xbrl.org/2003/instance}pure'

    def serialize(self, nsmap, format='json'):
        result = None
        if format == 'json':
            result = '*'.join((x.serialize(nsmap, mark=True) for x in self.numerators))
            if self.denominators is not None:
                result += '/' + '*'.join((x.serialize(nsmap, mark=True)) for x in self.denominators)

        return result

    def __repr__(self):
        result = '*'.join((x.clark for x in self.numerators))
        if self.denominators is not None:
            result += '/' + '*'.join((x.clark for x in self.denominators)) 

class XincePeriod:
    def __init__(self, start=None, end=None):
        '''If there is only a start, it is an instance. If both start and end it is a duration. If neither start or end it is forever'''
        if start is not None:
            if not isinstance(start, datetime.datetime):
                raise XinceException(f"Start date for a period must be a datetime, found {type(start).__name__}")
        if end is not None:
            if not isinstance(end, datetime.datetime):
                raise XinceException(f"End date for a period must be a datetime, found {type(end).__name__}")
        self._start = start
        self._end = end
    
    @property
    def is_instance(self):
        return self._start is not None and self._end is None

    @property
    def is_duration(self):
        return not self.is_instance

    @property
    def is_forever(self):
        return self._start is None and self._end is None
    
    def serialize(self, format='json'):
        result = None
        if format == 'json':
            if self.is_instance:
                result = self._start.isoformat()
            elif self.is_forever:
                result = None
            else: # non forever duration
                result = f'{self._start.isoformat()}/{self._end.isoformat()}'
        
        return result

    def __repr__(self):
        return self.serialize()

def getXulePlugin(cntlr):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
    """
    global _xule_plugin_info
    if _xule_plugin_info is None:
        for _plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == 'xule':
                _xule_plugin_info = plugin_info
                break
        else:
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run DQC rules. This plugin should be automatically loaded."), "XinceError", level=logging.ERROR)
    
    return _xule_plugin_info

def getXuleMethod(cntlr, method_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(method_name)

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, optparse.OptionParser):
        parserGroup = optparse.OptionGroup(parser,
                                           "Xule to Instance")
        parser.add_option_group(parserGroup)
    else:
        parserGroup = parser
    
    parserGroup.add_option("--xince-location",
                            action="store",
                            help=_("Directory where files are create"))

    parserGroup.add_option("--xince-file-type",
                            action="store",
                            default="json",
                            help=_("type of output. values are 'json', 'xml'"))

    parserGroup.add_option("--xince-show-xule-log",
                            action="store_true",
                            help=_("Indicates to output the xule log"))

def cmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()

    if options.xince_location is not None and options.xule_rule_set is None:
        parser.error("Xule to instance requires a xule rule set (--xule-rule-set)")

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    # Model is create (file loaded) now ready to create an instance

    if options.xince_location is None:
        # nothing to do
        modelXbrl.info("Xule to Instance plugin is installed but the --xule-to-instance option was not provided. Not creating instances.")
    else:
        create_instance(cntlr, options, modelXbrl)

def create_instance(cntlr, options, modelXbrl):

    # Run Xule rules
    log_capture = run_xule(cntlr, options, modelXbrl)

    # Find instances and facts
    instances, instance_facts = organize_instances_and_facts(log_capture, cntlr)

    for instance_name, taxonomies in instances.items():
        process_instance(instance_name, taxonomies, instance_facts[instance_name], cntlr, options)

def organize_instances_and_facts(log_capture, cntlr):
    '''Arrange the captured log into instances
    
    The return is a dictionary of instances keyed by name and the value is the list of taxonomies for the instance,
    and a dictionary of facts keyed by instance name and the value is a list of the captured log entries that
    belong to that instance'''
    instances = collections.defaultdict(list)
    instance_facts = collections.defaultdict(list)

    issues = []

    for rule_name, log_recs in log_capture.items():
        for log_rec in log_recs:
            inst_keys = set(log_rec.args.keys()).intersection(_INSTANCE_OUTPUT_ATTRIBUTES)
            fact_keys = set(log_rec.args.keys()).intersection(_FACT_OUTPUT_ATTRIBUTES)
            # rules creating instances = add to the instances dictionary
            if len(inst_keys) > 0: 
                # This record creates an instance documents
                # There must be an instance-name and an instance-taxonomy
                good = True
                if 'instance-name' not in inst_keys:
                    issues.append(f"A rule that creates an instance must have an 'instance-name' output attribute. Error found in rule {rule_name}")
                    good = False
                if 'instance-taxonomy' not in inst_keys:
                    issues.append(f"A rule that creates an instance must have an 'instance-taxonomy' output attribute. Error found in rule{rule_name})")
                    good = False
                if good:
                    taxonomies = json.loads(log_rec.args['instance-taxonomy'])
                    if type(taxonomies) not in (str, list):
                        issues.append(f"instance-taxonomies must be a single uri indicating the schema reference or a list of uris. Error found in rule {rule_name}")
                    else:
                        if isinstance(taxonomies, str):
                            taxonomies = [taxonomies,]
                        instances[log_rec.args['instance-name']] = taxonomies

            # rules creating facts. Add to the instance_facts dictionary
            if len(fact_keys) > 0:
                # There must be a fact-instance. Other problems like missing concept name will be checked when creating the fact.
                if 'fact-instance' not in fact_keys:
                    issues.append(f"A rule that creates a fact must have a 'fact-instance' output attribute. Error found in rule {rule_name}")
                else:

                    instance_facts[log_rec.args['fact-instance']].append({k: v for k, v in log_rec.args.items() if k in fact_keys} | {'message': log_rec.msg, 'rule-name': rule_name})# just take the fact output attributes

    # Check that there are not facts for an instance that was not created with an instance rule.
    fact_bad_instances = set(instance_facts.keys()) - set(instances.keys())
    for  bad_instance in fact_bad_instances:
        issues.append(f"There are {len(instance_facts[bad_instance])} facts in instance {bad_instance} but there is not a rule defining this instance")

    for message in issues:
        cntlr.addToLog(message, 'XinceError', level=logging.ERROR)

    return instances, instance_facts

def process_instance(instance_name, taxonomies, facts, cntlr, options):

    fact_id = id_generator()
    instance = json.loads(_INSTANCE_BASE_STRING)
    # Create an Arelle model of the taxonomy. This is done by adding the taxonomies 
    # as schema refs and loading the file. The model is used to validate as facts are created
    # (i.e. the concept name is valid)
    taxonomy_model = get_taxonomy_model(instance_name, taxonomies, cntlr)
    nsmap = get_initial_nsmap(instance, taxonomy_model)
    # Always keep the 'xbrl' namespace
    nsmap.mark_namespace_as_used('https://xbrl.org/2021')
    # Add the schema refs
    # TODO this could also be role and arcrole refs
    for taxonomy in taxonomies:
        instance['documentInfo']['taxonomy'].append(taxonomy)

    # Add facts
    for fact in facts:
        add_fact(fact, instance, taxonomy_model, fact_id, nsmap, cntlr)

    # Clean up the namespaces
    #nsmap.remove_unused_namespaces()
    #unused_prefixes =set(instance['namespaces'].keys()) - set(nsmap.map_by_prefix.keys())
    instance['documentInfo']['namespaces'] = nsmap.used_map_by_prefix
    
    
    # Write the file
    output_file_name = os.path.join(options.xince_location, f'{instance_name}.json')
    with open(output_file_name, 'w') as f:
        json.dump(instance, f, indent=2)
    cntlr.addToLog(f"Writing instance file {output_file_name}", "XinceInfo")
    

def get_initial_nsmap(instance, taxonomy_model):
    '''This will add namespaces and their prefixes'''

    # first add the namespaces in the instance. These are the basic ones
    nsmap = XinceNSMap()
    for prefix, ns in instance['documentInfo']['namespaces'].items():
        nsmap.add_or_get_namespace(ns, prefix)
    # Then add namespaces defined in the the taxonomy
    for prefix, ns in taxonomy_model.prefixedNamespaces.items():
        nsmap.add_or_get_namespace(ns, prefix)
    
    return nsmap

def id_generator():
    i = 0
    while True:
        yield(f'f{i}')
        i += 1

def get_taxonomy_model(tax_name, taxonomies, cntlr):

    cntlr.addToLog(f"Start loading taxonomy model for instance {tax_name}", "XinceInfo")
    entry_point = _TAXONOMY_MODEL_START
    for taxonomy in taxonomies:
        # TODO - This assumes that the taxonomies are all schema refs, but they could be rolerefs and arcrole refs.
        entry_point += f'<link:schemaRef xlink:href="{taxonomy}" xlink:type="simple"/>'
    entry_point += '</xbrli:xbrl>'

    entry_point_file_object, entry_point_file_name = tempfile.mkstemp('.xml', text=True)
    try:
        with os.fdopen(entry_point_file_object, 'w') as ep:
            ep.write(entry_point)
        entry_point_file_source = FileSource.openFileSource(entry_point_file_name, cntlr)            
        modelManager = ModelManager.initialize(cntlr)
        tax_model = modelManager.load(entry_point_file_source)
    finally:
        # Delete the temp file
        os.unlink(entry_point_file_name)

    if 'IOerror' in tax_model.errors:
        raise XinceException(_(f"Error creating taxonomy for instance {tax_name}"))                

    cntlr.addToLog(f"Loaded taxonomy model for instance {tax_name}", "XinceInfo")

    return tax_model

def add_fact(fact_info, instance, taxonomy, fact_id, nsmap, cntlr):
    errors = False
    # default aspects are from fact-alignment
    alignment_string = fact_info.get('fact-alignment', '{}')
    try:
        merged_info = json.loads(alignment_string)
        # Fix the keys. Alignment uses 'concept' but the key should be 'fact-concept'to match the Xince output attribute
        merged_info ={f'fact-{k}': v for k, v in merged_info.items()}
    except json.decoder.JSONDecodeError:
        cntlr.addToLog(f"Invalid fact-alignment '{alignment_string}' for rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
        errors = True

    for k, v in fact_info.items():
        if k != 'fact-alignment':
            merged_info[k] = v
    if 'fact-value' not in merged_info:
        # Get the fact value from the rule result
        merged_info['fact-value'] = merged_info['message']

    is_valid, fact_value, concept, entity, period, unit, dimensions, decimals, language = verify_fact(merged_info, taxonomy, cntlr)

    if is_valid or errors:
        fact_dict = dict()
        # TODO if the value is qname, then need to mark in the nsmap
        fact_dict['value'] = fact_value
        if concept.isNumeric and decimals != 'INF':
            fact_dict['decimals'] = decimals
        fact_dict['dimensions'] = dict()
        concept_qname = XinceQname(concept.qname.namespaceURI, concept.qname.localName)
        fact_dict['dimensions']['concept'] = concept_qname.serialize(nsmap, mark=True)
        if language is not None:
            fact_dict['dimensions']['language'] = language
        # entities are treated like qnames even though they are clearly not
        entity_qname = XinceQname(entity.scheme, entity.identifier)
        fact_dict['dimensions']['entity'] = entity_qname.serialize(nsmap, mark=True)
        fact_dict['dimensions']['period'] = period.serialize()
        if concept.isNumeric and not unit.is_pure:
            fact_dict['dimensions']['unit'] = unit.serialize(nsmap)
        if dimensions is not None and len(dimensions) > 0:
            for dim, mem in dimensions.items():
                # dim is a concept
                dim_qname = XinceQname(dim.qname.namespaceURI, dim.qname.localName)
                if dim.isExplicitDimension:
                    mem_qname = XinceQname(mem.qname.namespaceURI, mem.qname.localName)
                    fact_dict['dimensions'][dim_qname.serialize(nsmap, mark=True)] = mem_qname.serialize(nsmap, mark=True)
                else: # typed dimension
                    fact_dict['dimensions'][dim_qname.serialize(nsmap, mark=True)] = mem

        instance['facts'][next(fact_id)] = fact_dict
                
def verify_fact(fact_info, taxonomy, cntlr):
    errors = False

    fact_value = None
    model_concept = None
    entity = None
    period = None
    unit = None
    dimensions = None 
    decimals = None
    language = None

    # Check concept, entity and period exists. These are always required
    for aspect in ('fact-concept', 'fact-entity', 'fact-period'):
        if aspect not in fact_info:
            cntlr.addToLog(f"Fact is missing {aspect} which is required. Rule: {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check concept
    model_concept = get_concept(fact_info.get('fact-concept'), taxonomy)
    if model_concept is None:
        cntlr.addToLog(f"Concept {fact_info['fact-concept']} is not in the taxonomy for the instance. Rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
        errors = True

    # Check entity - it should look like a clark notation qname where the namespace is the scheme and the local part is the identifier
    if 'fact-entity' in fact_info:
        try:
            entity_info = json.loads(fact_info['fact-entity'])
            if len(entity_info) != 2:
                raise json.decoder.JSONDecodeError
            entity = XinceEntity(entity_info[0], entity_info[1])
        except json.decoder.JSONDecodeError:
            cntlr.addToLog(f"fact-entity '{fact_info['fact-entity']}' is not valid for rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True

    # Check period
    if 'fact-period' in fact_info:
        period = get_period(fact_info['fact-period'], fact_info['rule-name'], cntlr)
        if period is None:
            errors = True

    if model_concept is not None and model_concept.isNumeric:
        # Check units
        if 'fact-unit' not in fact_info:
            cntlr.addToLog(f"fact-unit is required for numeric facts. Concept is '{model_concept.qname.clarkNotation}' from rule '{fact_info['rule-name']}", "XinceError", level=logging.ERROR)
            errors = True
        unit = get_unit(fact_info['fact-unit'], fact_info['rule-name'], cntlr)
        if unit is None:
            errors = True

        # Check decimals
        if 'fact-decimals' in fact_info and fact_info['fact-decimals'].strip().lower() != 'none':
            if fact_info['fact-decimals'].lower().strip() == 'inf':
                decimals = 'INF'
            else:
                try:
                    decimals = int(fact_info['fact-decimals'])
                except ValueError:
                    cntlr.addToLog(f"Invalid decimals of {fact_info['fact-decimals']} for rule {fact_info['rule-name']}", "XinceError", level=logging.ERROR)
                    errors = True
        else: # default to infinity when not provided
            decimals = 'INF'

    # Check language
    if model_concept is not None and model_concept.baseXbrliType == 'stringItemType':
        if 'fact-language' in fact_info and fact_info['fact-language'].strip().lower() != 'none':
            language = fact_info['fact-language'].strip()

    # Check dimensions
    if 'fact-dimensions' in fact_info:
        dimensions = get_dimensions(fact_info['fact-dimensions'], taxonomy, fact_info['rule-name'], cntlr)
        if dimensions is None:
            errors = True

    # TODO fix fact value based on type
    if 'fact-value' in fact_info:
        fact_value = fact_info['fact-value']

    return not errors, fact_value, model_concept, entity, period, unit, dimensions, decimals, language

def get_concept(clark, taxonomy):
    if not hasattr(taxonomy, 'clarkConcepts'):
        # Create a dictionary keyed by qname in clark notation.
        clark_concepts = {k.clarkNotation: v for k, v in taxonomy.qnameConcepts.items()}
        taxonomy.clarkConcepts = clark_concepts
    return taxonomy.clarkConcepts.get(clark)
    
def get_unit(unit_string, rule_name, cntlr):
    # The unit_string uses clark notation for the individual units
    numerators = None
    denominators = None

    def break_up_units(units):
        if units is None:
            return None

        errors = False
        result = []
        for unit_part in units.split('*'):
            qname_match = _QNAME_MATCH.fullmatch(unit_part.strip())
            if unit_match is None:
                cntlr.addToLog(f"Unit '{unit_part}' is not in clark notation. Rule is '{rule_name}'", "XinceError", level=logging.ERROR)
                errors = True
            else:
                unit_qname = XinceQname(qname_match.group(1), qname_match.group(2))
                result.append(unit_qname)
        return result if not errors else None

    unit_match = _UNIT_MATCH.fullmatch(unit_string.strip())
    if unit_match is None:
        cntlr.addToLog(f"Unit '{unit_string}' is not a valid xince unit. Rule is '{rule_name}'", "XinceError", level=logging.ERROR)
    else:
        numerators = break_up_units(unit_match.group(1))
        if unit_match.group(4) is not None:
            denominators = break_up_units(unit_match.group(4))
            if denominators is None:
                return None

    if numerators is None:
        # The unit match must have failed, so the unit is not valid.
        return None
    else:
        return XinceUnit(numerators, denominators)

def get_period(period_string, rule_name, cntlr):
    start = None
    end = None
    if period_string.lower().strip() == 'forever':
        return XincePeriod() # no start or end date, this is a forever period
    elif '/' in period_string:
        # this is a duration
        start_string, end_string = period_string.strip().split('/')
        try:
            start = datetime.datetime.fromisoformat(start_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid start date format (must be ios format). Start date is '{start_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        try:
            end = datetime.datetime.fromisoformat(end_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid end date format (must be ios format). Start date is '{end_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        if start is not None and end is not None:
            return XincePeriod(start, end)
    else:
        # this is an instant
        try:
            start = datetime.datetime.fromisoformat(period_string.strip())
        except ValueError:
            cntlr.addToLog(f"Invalid instant date format (must be ios format). Start date is '{period_string}'. Rule is {rule_name}", "XinceError", level=logging.ERROR)
        if start is not None:
            return XincePeriod(start)
    
    return None # the period could not be created

def get_dimensions(dim_string, taxonomy, rule_name, cntlr):
    try:
        dimensions = json.loads(dim_string.strip())
    except json.decoder.JSONDecodeError:
        cntlr.addToLog(f"Dimensions string '{dim_string.strip()}' is not value for rule {rule_name}", "XinceError", level=logging.ERROR)
        return

    if not isinstance(dimensions, dict):
        cntlr.addToLog(f"Dimensions string '{dim_string.strip()}' is not value for rule {rule_name}", "XinceError", level=logging.ERROR)
        return
    
    error = False
    result = dict()
    for dim, member in dimensions.items():
        # check dimension is valid
        dim_concept = get_concept(dim, taxonomy)
        if dim_concept is None:
            cntlr.addToLog(f"Dimension concept {dim} is not in the taxonomy. Rule {rule_name}", "XinceError", level=logging.ERROR)
            error = True
        elif not dim_concept.isDimensionItem:
            cntlr.addToLog(f"Dimension concept {dim_concept.qname.clarkNotation} is not a dimension item. Rule {rule_name}", "XinceError", level=logging.ERROR)
            error = True

        else: # all is good
            if dim_concept.isExplicitDimension:
                # the member is a qname for the member concept
                mem_concept = get_concept(member, taxonomy)
                if mem_concept is None:
                    cntlr.addToLog(f"Member concept {member} is not in the taxonomy. Rule {rule_name}", "XinceError", level=logging.ERROR)
                    error = True
                elif not mem_concept.isDomainMember:
                    cntlr.addToLog(f"Member concept {mem_concept.qname.clarkNotation} is not a member of a dimension. Rule {rule_name}", "XinceError", level=logging.ERROR)
                    error = True
                else:
                    result[dim_concept] = mem_concept
                # TODO - should check that the member is valid for the dimension. This would require building all the cubes and checking
                # the member for the fact concept. 
                # TODO - should also check that the member is not the default
            else: # this is a typed dimension
                # TODO convert the typed dimenson value like fact values
                result[dim_concept] = member
        
    return result



def run_xule(cntlr, options, modelXbrl):

    # Create a log handler that will capture the messages when the rules are run.
    log_capture_handler = _logCaptureHandler()
    if not options.xince_show_xule_log:
        cntlr.logger.removeHandler(cntlr.logHandler)
    cntlr.logger.addHandler(log_capture_handler)

    # Call the xule processor to run the rules
    call_xule_method = getXuleMethod(cntlr, 'Xule.callXuleProcessor')
    run_options = copy.deepcopy(options)
            
    #xule_args = getattr(run_options, 'xule_arg', []) or []
    #xule_args += list(xule_date_args)
    #setattr(run_options, 'xule_arg', xule_args)
        # Get xule rule set
    # with ts.open(catalog_item['xule-rule-set']) as rule_set_file:
    call_xule_method(cntlr, modelXbrl, options.xule_rule_set, run_options)
    
    # Remove the handler from the logger. This will stop the capture of messages
    cntlr.logger.removeHandler(log_capture_handler)
    if not options.xince_show_xule_log:
        cntlr.logger.addHandler(cntlr.logHandler)

    return log_capture_handler.captured

class _logCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self._captured = collections.defaultdict(list)

    def emit(self, record):
        self._captured[record.messageCode].append(record)
    
    @property
    def captured(self):
        return self._captured


__pluginInfo__ = {
    'name': 'FERC Renderer',
    'version': '0.9',
    'description': "FERC Tools",
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}