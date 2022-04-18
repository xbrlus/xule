"""
Data Quality Consortium validation (DQC) processor

This validation module runs FERC rules. It uses the Xule rule processor

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2019 XBRL US, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

$Change: 22782 $
DOCSKIP
"""
import optparse
from arelle import PluginManager

""" Xule validator specific variables."""
_short_name = 'eForms'
_name = 'FERC eForms Rules Validator'
_version = 'Check version using Tools->FERC->Version on the GUI or --ferc-version on the command line'
_version_prefix = '3.0.'
_description = 'FERC eForms rules validator.'
_license = 'Apache-2'
_author = 'XBRL US Inc.'
_copyright = '(c) 2017-2022'
_rule_set_map_name = 'fercRulesetMap.json'
_latest_map_name = 'https://github.com/xbrlus/ferc-renderer/raw/master/fercRulesetMap.json' 

"""Do not change anything below this line."""
_xule_plugin_info = None

def cmdOptions(parser):
    """Extend command line options for xule validator
    
    This is called by the Arelle controller.
    """
    if isinstance(parser, optparse.OptionParser):
        # This is the normal optparse.OptionsParser object.
        parserGroup = optparse.OptionGroup(parser,
                                           "{} validation plugin (Also see --xule options)".format(_short_name))
        parser.add_option_group(parserGroup)
    else:
        # This is a fake parser object (which does not support option groups). This is sent when arelle is in GUI
        # mode or running as a webserver
        parserGroup = parser

    # Show version of validator
    parserGroup.add_option("--{}-version".format(_short_name).lower(),
                      action="store_true",
                      dest="{}_version".format(_short_name),
                      help=_("Display version number of the {} validation plugin.".format(_short_name)))

    # Display validator rule set map
    parserGroup.add_option("--{}-display-rule-set-map".format(_short_name).lower(),
                           action="store_true",
                           dest="{}_display_rule_set_map".format(_short_name),
                           help=_("Display the rule set map currently used."))   

    # Update validator rule set map
    parserGroup.add_option("--{}-update-rule-set-map".format(_short_name).lower(),
                           action="store",
                           dest="{}_update_rule_set_map".format(_short_name),
                           help=_("Update the rule set map currently used. The supplied file will be merged with the current rule set map."))
    
    # Replace validator rule set map
    parserGroup.add_option("--{}-replace-rule-set-map".format(_short_name).lower(),
                           action="store",
                           dest="{}_replace_rule_set_map".format(_short_name),
                           help=_("Replace the rule set map currently used."))

    # Update validator rule set map with latest
    parserGroup.add_option("--{}-update-rule-set-map-latest".format(_short_name).lower(),
                           action="store_true",
                           dest="{}_update_rule_set_map_latest".format(_short_name),
                           help=_(
                               "Update the rule set map currently used with the latest version."))

    # Replace validator rule set map
    parserGroup.add_option("--{}-replace-rule-set-map-latest".format(_short_name).lower(),
                           action="store_true",
                           dest="{}_replace_rule_set_map_latest".format(_short_name),
                           help=_("Replace the rule set map currently used with the latest version."))


def cntrlrCmdLineUtilityRun(cntlr, options, **kwargs):
    """Validator run utility.
    
    This is invoked by the Arelle controler after Arelle is fully up but before a filing is loaded.
    """
    # Save options in xule
    save_options_method = getXuleMethod(cntlr, 'Xule.CntrlCmdLine.Utility.Run.Init')
    save_options_method(cntlr, options, **kwargs)

    parser = optparse.OptionParser()
    
    # Check that both update an replace rule set map are not used together.
    replace_update_rule_set_map_options = [x.lower().replace('_','-') for x in ('{}_update_rule_set_map'.format(_short_name),
                                                       '{}_replace_rule_set_map'.format(_short_name),
                                                       '{}_update_rule_set_map_latest'.format(_short_name),
                                                       '{}_replace_rule_set_map_latest'.format(_short_name)
                                                       )
                                             if getattr(options, x, False)]
    if len(replace_update_rule_set_map_options) > 1:
        parser.error(_("Cannot use the following options at the same time: --{}".format(', '.join(replace_update_rule_set_map_options))))


    #if len([x for x in (getattr(options, "{}_update_rule_set_map".format(_short_name), False),
    #                   getattr(options, "{}_replace_rule_set_map".format(_short_name), False)) if x]) > 1:
    #    parser.error(_("Cannot use --{short_name}-update-rule-set-map and --{short_name}-replace-rule-set-map the same time.".format(short_name=_short_name)))
    
    # Show validator version
    if getattr(options, '{}_version'.format(_short_name), False):
        version_method = getXuleMethod(cntlr, 'Xule.ValidatorVersion')
        version_method(cntlr, _short_name, _rule_set_map_name, _version_prefix, __file__)

        #cntlr.addToLog("{} validator version: {}".format(_short_name,  _version_prefix + version_method(__file__)), _short_name)
        #cntlr.close()
    
    # Update the rule set map
    if getattr(options, "{}_update_rule_set_map".format(_short_name), False):
        update_method = getXuleMethod(cntlr, 'Xule.RulesetMap.Update')
        update_method(cntlr, getattr(options,"{}_update_rule_set_map".format(_short_name)), _rule_set_map_name)
    
    # Replace the rule set map
    if getattr(options, "{}_replace_rule_set_map".format(_short_name), False):
        update_method = getXuleMethod(cntlr, 'Xule.RulesetMap.Replace')
        update_method(cntlr, getattr(options,"{}_replace_rule_set_map".format(_short_name)), _rule_set_map_name)
    
    # Display the rule set map
    if getattr(options, "{}_display_rule_set_map".format(_short_name), False):
        update_method = getXuleMethod(cntlr, 'Xule.RulesetMap.Display')
        update_method(cntlr, _short_name, _rule_set_map_name)

    # Update the rule set map with the latest
    if getattr(options, "{}_update_rule_set_map_latest".format(_short_name), False):
        update_method = getXuleMethod(cntlr, 'Xule.RulesetMap.Update')
        update_method(cntlr, _latest_map_name, _rule_set_map_name)

    # Replace the rule set map with the latest
    if getattr(options, "{}_replace_rule_set_map_latest".format(_short_name), False):
        update_method = getXuleMethod(cntlr, 'Xule.RulesetMap.Replace')
        update_method(cntlr, _latest_map_name, _rule_set_map_name)

    # Register the xule validator
    registerMethod = getXuleMethod(cntlr, 'Xule.RegisterValidator')
    registerMethod(_short_name, _rule_set_map_name)
    
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
            cntlr.addToLog(_("Xule plugin is not loaded. Xule plugin is required to run FERC rules. This plugin should be automatically loaded."))
    
    return _xule_plugin_info

def getXuleMethod(cntlr, class_name):
    """Get method from Xule
    
    Get a method/function from the Xule plugin. This is how this validator calls functions in the Xule plugin.
    """
    return getXulePlugin(cntlr).get(class_name)

def menuTools(cntlr, menu):
    """Add validator menu the Tools menu in the Arelle GUI
    
    This is invoked by the Arelle controller
    """
    menu_method = getXuleMethod(cntlr, 'Xule.AddMenuTools')
    version_method = getXuleMethod(cntlr, 'Xule.ValidatorVersion')
    menu_method(cntlr, menu, _short_name, _version_prefix, __file__, _rule_set_map_name, _latest_map_name)

def validateMenuTools(cntlr, validateMenu, *args, **kwargs):
    """Add validator checkbutton to the Arelle Validate menu (under Tools).
    
    This is invoked by the Arelle controller.
    """
    menu_method = getXuleMethod(cntlr, 'Xule.AddValidationMenuTools')
    menu_method(cntlr, validateMenu, _short_name, _rule_set_map_name)
    
__pluginInfo__ = {
    'name': _name,
    'version': _version,
    'description': _description,
    'license': _license,
    'author': _author,
    'copyright': _copyright,
    'import': 'xule',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None,
    'CntlrWinMain.Menu.Tools': menuTools,
    'CntlrWinMain.Menu.Validation': validateMenuTools,
    'CntlrCmdLine.Utility.Run': cntrlrCmdLineUtilityRun,
    'CntlrCmdLine.Options': cmdOptions
    }
