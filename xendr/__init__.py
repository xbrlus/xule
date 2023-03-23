"""__init__.py

Xendr is the Xbrl rENDERer. 

This is the package init file.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2023 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: $
DOCSKIP
"""
from .xendrCompile import compile_templates, list_templates, extract_templates, combine_template_sets
from .xendrRun import render_report
import optparse
import os

def cmdLineOptionExtender(parser, *args, **kwargs):
    
    # extend command line options to compile rules
    if isinstance(parser, optparse.OptionParser):
        parserGroup = optparse.OptionGroup(parser,
                                           "Xendr - XBRL Renderer")
        parser.add_option_group(parserGroup)
    else:
        parserGroup = parser
    
    parserGroup.add_option("--xendr-compile", 
                      action="store_true", 
                      dest="xendr_compile", 
                      help=_("Indicator to compile a template set. Reuires --xendr-template and --xendr-template_set options"))

    parserGroup.add_option("--xendr-render", 
                      action="store_true", 
                      dest="xendr_render", 
                      help=_("Indicator to render an instance with a template set. Reuires --xendr-template_set options and XBRL instnace (-f)"))

    parserGroup.add_option("--xendr-combine", 
                      action="store", 
                      dest="xendr_combine", 
                      help=_("Combine indicated template sets into a single template set. This argument can take a '|' separated list of "
                             "template sets or folders. Template will be added in the order this list. If a folder is indicated, then all "
                             " the template sets in the filder and its decendants will be added."))

    parserGroup.add_option("--xendr-list", 
                      action="store_true", 
                      dest="xendr_list", 
                      help=_("List the templates in a template set."))

    parserGroup.add_option("--xendr-extract", 
                      action="store", 
                      dest="xendr_extract", 
                      help=_("Extract the templates from a template set. This option identifies the folder to extract the templates to."))                      

    parserGroup.add_option("--xendr-namespace",
                      action="append",
                      dest="xendr_namespaces",
                      help=_("Create namespace mapping for prefix used in the template in the form of prefix=namespace. To map multiple "
                             "namespaces use separate --xendr-space for each one."))

    parserGroup.add_option("--xendr-template", 
                      action="append", 
                      dest="xendr_template", 
                      help=_("The HTML template file"))

    parserGroup.add_option("--xendr-template-set", 
                      action="store", 
                      dest="xendr_template_set", 
                      help=_("Compiled template set file"))

    parserGroup.add_option("--xendr-inline", 
                      action="store", 
                      dest="xendr_inline", 
                      help=_("The generated Inline XBRL file"))        

    parserGroup.add_option("--xendr-css-file", 
                      action="store", 
                      dest="xendr_css_file", 
                      help=_("Identify the CSS file that sould be used. This will overwrite the name of the CSS file that is included in the template set."))   

    parserGroup.add_option("--xendr-inline-css", 
                      action="store_true", 
                      dest="xendr_inline_css", 
                      help=_("Indicates that the CSS should be inlined in the generated HTML file. This option must be used with --frec-render-css-file."))   

    parserGroup.add_option("--xendr-title",
                      action="store",
                      dest="xendr_title",
                      help=_("Value of the <title> element in the created html"))

    parserGroup.add_option("--xendr-default-footnote-page",
                      action="store_true",
                      dest="xendr_default_footnote_page",
                      help=_("Create a default footnote page at the end of the template. This will override any footnote handling (<footnotes>) that is built into the template."))

    parserGroup.add_option("--xendr-save-xule", 
                      action="store", 
                      dest="xendr_save_xule", 
                      help=_("Name of the generated xule file to save before complining the rule set."))

    parserGroup.add_option("--xendr-show-xule-log",
                      action="store_true",
                      dest="xendr_show_xule_log",
                      help=_("Show the log messages when running the xule rules. By default these messages are not displayed."))

    parserGroup.add_option("--xendr-constants", 
                      action="store", 
                      dest="xendr_constants", 
                      help=_("Name of the constants file. This will default to render-constants.xule."))  

    parserGroup.add_option("--xendr-partial",
                      action="store_true",
                      dest="xendr_partial",
                      help=_("Indicates that this is a partial rendering such as a single schedule. This will prevent outputing unused facts in the "
                             "hidden section of the inline document."))

    parserGroup.add_option("--xendr-show-hidden",
                      action="store_true",
                      dest="xendr_show_hidden",
                      help=_("Display facts that are are written to the hidden section of the inline XBRL document."))   

    parserGroup.add_option("--xendr-show-hidden-except",
                      action="append",
                      dest="xendr_show_hidden_except",
                      help=_("Concept local name for facts that should not be displayed when showing hidden facts. To list multiples, use this option for each name."))                                                  

    parserGroup.add_option("--xendr-debug",
                      action="store_true",
                      dest="xendr_debug",
                      help=_("Run the rendered in debug mode."))

    parserGroup.add_option("--xendr-only",
                      action="store",
                      dest="xendr_only",
                      help=_("List of template names to render. All others will be skipped. Template names are separated by '|' character."))


def cmdUtilityRun(cntlr, options, **kwargs): 
    #check option combinations
    parser = optparse.OptionParser()
    
    if (options.xendr_compile is None and 
        options.xendr_render is None and 
        options.xendr_combine is None and 
        options.xendr_list is None and
        options.xendr_extract is None):
        parser.error(_("The xendr plugin requires either --xendr-compile, --xendr-render, --xendr-combine, --xendr-list and/or --xendr-extract"))

    if options.xendr_compile:
        if options.xendr_template is None and options.xendr_template_set is None:
            parser.error(_("Compiling a template set requires --xendr-template and --xendr-template-set."))
    
    if options.xendr_render:
        if options.xendr_template_set is None:
            parser.error(_("Rendering requires --xendr-template-set"))

    if options.xendr_combine is not None:
        if options.xendr_template_set is None:
            parser.error(_("Combining template sets requires --xendr-template-set"))

    if options.xendr_combine is not None:
        combine_template_sets(cntlr, options)

    if options.xendr_list and options.xendr_template_set is None:
        parser.error(_("Listing the templates in a template set requires a --ferec-render-template-set."))

    if options.xendr_extract and options.xendr_template_set is None:
        parser.error(_("Extracting the templates from a template set requires a --ferec-render-template-set."))        

    if options.xendr_inline_css and not options.xendr_css_file:
        parser.error(_("--xendr-inline-css requires the --xendr-css-file option to identify the css file."))

    if options.xendr_inline_css and options.xendr_css_file:
        # make sure the css file exists
        if not os.path.exists(options.xendr_css_file):
            parser.error(_("CSS file '{}' does not exists.".format(options.xendr_css_file)))

    validate_namespace_map(options, parser)

    if options.xendr_compile:
        compile_templates(cntlr, options)

    if options.xendr_list:
        list_templates(cntlr, options)     

    if options.xendr_extract:
        extract_templates(cntlr, options)

def validate_namespace_map(options, parser):
    options.namespace_map = dict()
    default_namespace = None
    for map in getattr(options, "xendr_namespaces") or tuple():
        map_list = map.split('=', 1)
        if len(map_list) == 1:
            if map_list[0].strip == '':
                parser.error(_("--xendr-namespace namespace without a prefix (default) must have a non space value."))
            elif None in options.namespace_map:
                parser.error(_("--xendr-namespace there can only be one default namespace"))
            else:
                options.namespace_map[None] = map_list[0].strip()
        elif len(map_list) == 2:
            prefix = map_list[0].strip()
            ns = map_list[1].strip()
            if prefix == '':
                parser.error(_("--xendr-namespace prefix must have a non space value"))
            if ns == '':
                parser.error(_("--xendr-namespace namespace must have non space value"))
            if prefix in options.namespace_map:
                parser.error(_("--xendr-namespace prefix '{}' is mapped more than once".format(prefix)))
            options.namespace_map[prefix] = ns
        else:
            parser.error(_("--xendr-namespace invalid content: {}".format(map)))

def cmdLineXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    '''Render a filing'''
    
    if options.xendr_render and options.xendr_template_set is not None:
        render_report(cntlr, options, modelXbrl, *args, **kwargs)

__pluginInfo__ = {
    'name': 'Xendr',
    'version': '0.9',
    'description': "XBRL Renderer",
    'copyright': '(c) Copyright 2023 XBRL US Inc., All rights reserved.',
    'import': 'xule',
    # classes of mount points (required)
    'CntlrCmdLine.Options': cmdLineOptionExtender,
    'CntlrCmdLine.Utility.Run': cmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': cmdLineXbrlLoaded,
    #'CntlrWinMain.Menu.Tools': fercMenuTools,
    #'CntlrWinMain.Xbrl.Loaded': cmdLineXbrlLoaded,    
}