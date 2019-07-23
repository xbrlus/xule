from arelle import PluginManager
from arelle.CntlrWebMain import Options
from lxml import etree

import logging
import optparse

# This will hold the xule plugin module
_xule_plugin_info = None

# xule namespace used in the template
_xule_namespace_map = {'xule': 'http://xbrl.us/xule/2.0/template'}
_rule_name_prefix = 'xule-'

def getXulePlugin(cntlr):
    """Find the Xule plugin
    
    This will locate the Xule plugin module.
    """
    global _xule_plugin_info
    if _xule_plugin_info is None:
        for plugin_name, plugin_info in PluginManager.modulePluginInfos.items():
            if plugin_info.get('moduleURL') == 'xule':
                _xule_plugin_info = plugin_info
                break
        else:
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run DQC rules. This plugin should be automatically loaded."))
    
    return _xule_plugin_info

def getXuleMethod(cntlr, method_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(method_name)


def process_template(cntlr, template_file_name):
    '''Prepare the template to substitute values

    1. build the xule rules from the template
    2. identify where in the template to substitution caluldated values
    '''

    # Open the template
    try:
        with open(template_file_name) as fp:
            template_tree = etree.parse(fp)
    except FileNotFoundError:
        cntlr.addToLog("Template file '{}' is not found.".format(template_file_name), 'error', level=logging.ERROR)
        raise

    except etree.XMLSchemaValidateError:
        cntlr.addToLog("Template file '{}' is not a valid XHTML file.".format(template_file_name), 'error', level=logging.ERROR)
        raise    

    # build the namespace declaration for xule
    xule_namespaces = build_xule_namespaces(template_tree)
    # create the rules for xule and retrieve the update template with the substitutions identified.
    xule_rules, substitutions = build_xule_rules(template_tree)

    return None, template_tree

def build_xule_namespaces(template_tree):
    '''build the namespace declarations for xule

    Convert the namespaces on the template to namespace declarations for xule. This will only use the 
    namespaces that are declared on the root element of the template.
    '''
    namespaces = ['namespace {}={}'.format(k, v) if k is not None else 'namespace {}'.format(v) for k, v in template_tree.getroot().nsmap.items()]
    return '\n'.join(namespaces)

def build_xule_rules(template_tree):
    '''Extract the rules and identify the subsititions in the template

    1. Create the xule rules
    2. Identify where the subsitutions will be
    '''
    
    substitutions = dict()
    xule_rules = []
    next_rule_number = 1

    # Go through each of the xule expressions in the template
    for xule_frag in template_tree.findall('//xule:frag', _xule_namespace_map):
        xule_expression = xule_frag.find('xule:expression', _xule_namespace_map)
        if xule_expression is not None:
            rule_name = _rule_name_prefix + str(next_rule_number)
            next_rule_number += 1
            substitutions[rule_name] = (0, xule_frag)
            rule_text = 'output {}\n{}'.format(rule_name, xule_expression.text)
            xule_rules.append(rule_text)
        
    return '\n'.join(xule_rules), substitutions

def fercMenuTools(cntlr, menu):
    import tkinter
  
    def fercRender():
        global _INSTANCE_MODEL
        if _INSTANCE_MODEL is None:
            tkinter.messagebox.showinfo("FERC Renderer", "Need to load an instance document in order to render")
        elif _INSTANCE_MODEL.modelDocument.type not in (Type.INSTANCE, Type.INLINEXBRL):
            tkinter.messagebox.showinfo("FERC Renderer", "Loaded document is not an instance")
        else:
            # Extract the formLocation references from the Arelle model
            refs = get_references(_INSTANCE_MODEL, _CONCEPT_REFERENCE)
            
            if _INSTANCE_MODEL.modelManager.cntlr.userAppDir is None:
                raise Exception(_("Arelle does not have a user application data directory. Cannot save rendered file"))            
            render_file_name = os.path.join(cntlr.userAppDir, 'plugin', 'ferc',  os.path.splitext(_INSTANCE_MODEL.modelDocument.basename)[0] + '.html')            
            
            render(render_file_name, _INSTANCE_MODEL, refs)        
            webbrowser.open(render_file_name)

    fercMenu = tkinter.Menu(menu, tearoff=0)
    fercMenu.add_command(label=_("Render"), underline=0, command=fercRender)

    menu.add_cascade(label=_("FERC"), menu=fercMenu, underline=0)

def cmdLineXbrlLoaded(cntlr, model, *Args, **kwargs):
    pass

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "FERC Renderer")
        parser.add_option_group(parserGroup)
    
    parserGroup.add_option("--ferc-render-template", 
                      action="store", 
                      dest="ferc_render_template", 
                      help=_("The HTML template file"))   

def fercCmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()
    
    if options.ferc_render_template is None:
        parser.error(_("--ferc-render-template is required."))

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):

    if options.ferc_render_template is not None:
        xule_rule_text, template = process_template(cntlr, options.ferc_render_template)

__pluginInfo__ = {
    'name': 'FERC Tools',
    'version': '0.9',
    'description': "FERC Tools",
    'copyright': '(c) Copyright 2018 XBRL US Inc., All rights reserved.',
    'import': 'xule'
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': fercCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    'CntlrWinMain.Menu.Tools': fercMenuTools,
    'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}