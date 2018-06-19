"""__init__.py

Xule is a rule processor for XBRL (X)brl r(ULE). 

This is the package init file.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - 2018 XBRL US, Inc.

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
from .XuleProcessor import process_xule
from . import XuleRunTime as xrt
from . import XuleRuleSet as xr
from . import XuleUtility as xu
from . import XuleConstants as xc
from .XuleContext import XuleGlobalContext, XuleRuleContext

try:
    from . import XuleValidate as xv
except ImportError:
    xv = None

try:
    from . import XuleParser as xp
except ImportError:
    xp = None
    
try:
    from . import XuleMultiProcessing as xm
except ImportError:
    xm = None    


from optparse import OptionParser, SUPPRESS_HELP
from arelle import FileSource
from arelle import ModelManager
from arelle import PluginManager
from arelle.CntlrWebMain import Options
import optparse
import os 
import datetime
import json

__version__ = '3.0.' + (xu.version() or '')

_cntlr = None
_options = None
_is_xule_direct = None
_saved_taxonomies = dict()
_test_start = None
_test_variation_name = None
_latest_map_name = None
_xule_validators = []
_xule_rule_set_map_name = 'xuleRulesetMap.json'

class EmptyOptions:
    pass

class XuleVars:
    
    class XuleVarContainer:
        pass

    @classmethod
    def set(cls, cntlr, name, value):
        if not hasattr(cntlr, 'xule_vars'):
            cntlr.xule_vars = dict()
        
        cntlr.xule_vars[name] = value
    
    @classmethod
    def get(cls, cntlr, name):
        if hasattr(cntlr, 'xule_vars'):
            return cntlr.xule_vars.get(name)
        else:
            return None

def xuleMenuTools(cntlr, menu):
    import tkinter
    
    global _cntlr
    _cntlr = cntlr
    
    attr_name = 'xule_is_on'
    setattr(cntlr.modelManager, attr_name, cntlr.config.setdefault(attr_name,False))

    if getattr(cntlr.modelManager, attr_name):
        addMenuTools(cntlr, menu, 'Xule', __version__, _xule_rule_set_map_name, _latest_map_name)
    else:
        activate_xule_label = "Activate"
        def turnOnXule():
            # The validation menu hook is hit before the tools menu hook. the XuleVars for 'validate_menu' is set in the validation menu hook.
            validate_menu = XuleVars.get(cntlr, 'validate_menu')
            addValidateMenuTools(cntlr, validate_menu, 'Xule', _xule_rule_set_map_name)
            menu.delete('Xule')
            xule_menu = addMenuTools(cntlr, menu, 'Xule', __version__, _xule_rule_set_map_name, _latest_map_name)
            
            def turnOffXule():
                validate_menu.delete('Xule Rules')
                menu.delete('Xule')
                new_xule_menu = tkinter.Menu(menu, tearoff=0)
                new_xule_menu.add_command(label=activate_xule_label, underline=0, command=XuleVars.get(cntlr, 'activate_xule_function'))
                menu.add_cascade(label=_("Xule"), menu=new_xule_menu, underline=0)
                cntlr.config['xule_activated'] = False
                
            xule_menu.add_command(label='Deactivate Xule', underline=0, command=turnOffXule)
            cntlr.config['xule_activated'] = True
        
        xule_menu = tkinter.Menu(menu, tearoff=0)
        xule_menu.add_command(label=activate_xule_label, underline=0, command=turnOnXule)
        XuleVars.set(cntlr, 'activate_xule_function', turnOnXule)
    
        menu.add_cascade(label=_("Xule"), menu=xule_menu, underline=0)
        
        if cntlr.config.get('xule_activated', False):
            turnOnXule()

def addMenuTools(cntlr, menu, name, version, map_name, cloud_map_location):
    import tkinter
    import tkinter.ttk as ttk
    import tkinter.font as tkFont
    
    def showVersion():
        if name == 'Xule':
            version_text = version
        else:
            version_text = '{}: {}\n\nXule: {}'.format(name, version, __version__)
        tkinter.messagebox.showinfo("{} Version".format(name), version_text)

    def showRuleSetMap():
        try:
            map = xu.get_rule_set_map(cntlr, map_name)
            map_file_name = xu.get_rule_set_map_file_name(cntlr, map_name)
        except xrt.XuleMissingRuleSetMap:
            tkinter.messagebox.showinfo(_("Cannot find rule set map"), _("Rule set map for '{}' does not exist. Rule set map file name is '{}'".format(name, xu.get_rule_set_map_file_name(cntlr, map_name))))
        else:
            headers = ['Namespace', 'Rule Set']
            # Set the value of the map dictionary to be a list.
            displayRuleSetMap(map.items(), headers, '{} Rule Set Map - {}'.format(name, map_file_name))
    
    def checkRuleSetMap():
        # Get the current rule set map
        current_map = xu.get_rule_set_map(cntlr, map_name)
        # Get the latest map
        # Open the new map
        latest_map = xu.open_json_file(cntlr, cloud_map_location)
        
        match = True
        for namespace, rule_set in latest_map.items():
            if current_map.get(namespace) != rule_set:
                match = False
        
        if match:
            tkinter.messagebox.showinfo("{} Rule Set Check".format(name), _("You have the latest rule set map."))
        else:
            compare_map = []
            for cur_key in current_map:
                cur_row = [cur_key, current_map[cur_key]]
                latest_value = latest_map.get(cur_key)
                cur_row.append(latest_value or '')
                cur_row.append('Yes' if current_map[cur_key] == latest_value else 'No' if cur_key in latest_map else 'Current Map Only')
                compare_map.append(cur_row)
            for latest_key in latest_map.keys() - current_map.keys():
                # These keys are not in the current map
                compare_map.append([latest_key,'',latest_map[latest_key], 'Latest Map Only'])
            headers = ('Namespace', 'Current Rule Set', 'Latest Rule Set', 'Match')
            displayRuleSetMap(compare_map, headers, 'Current rule set map does not match latest DQC rule set map')

            #tkinter.messagebox.showinfo("DQC Rule Set Check", _("The rule set map you have does match the latest DQC rule set map."))
            
    def displayRuleSetMap(map, headers, title=''):
        # Get the top level container
        root = tkinter.Toplevel()
        # Create a tree view. This will be a multi column list box
        tree_box = ttk.Treeview(root, columns=headers, show="headings")
        tree_box.winfo_toplevel().title(title)
        # Set the headers and the initial column widths based on the length of the each headers
        for col in headers:
            tree_box.heading(col, text=col.title())
            tree_box.column(col, width=tkFont.Font().measure(col.title()))
        # Add the values to the tree box
        for current_value in map:
            item = tree_box.insert('', 'end', values=current_value, tag=current_value[3].replace(' ','') if len(current_value) >= 4 else 'Yes')
        # Set rows tht don't match to red
        tree_box.tag_configure('No', foreground='red')
        tree_box.tag_configure('LatestMapOnly', foreground='red')
        tree_box.tag_configure('CurrentMapOnly', foreground='blue')
        
        # Reset the column widths based on the values in the columns
        max_w = tkFont.Font().measure('X'*30)
        for col_index in range(len(headers)):
            col_id = headers[col_index]
            col_w = tree_box.column(col_id, width=None)
            for row in map:
                x = list(row)[col_index]
                new_w = tkFont.Font().measure(x)
                if new_w > max_w:
                    col_w = max_w
                    break
                if new_w > col_w:
                    col_w = new_w
            tree_box.column(col_id, width=col_w)
        # Place the tree box
        tree_box.grid(column=0, row=0, sticky='nsew')
        # Create the scroll bars
        vsb = ttk.Scrollbar(root, orient='vertical', command=tree_box.yview)
        hsb = ttk.Scrollbar(root, orient='horizontal', command=tree_box.xview)
        # Set the feedback from the tree box to the scroll bars
        tree_box.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        # Place the scroll bars
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        # Set the feedback from the scroll bars to the text_box
        vsb.config(command=tree_box.yview)
        hsb.config(command=tree_box.xview)
        # This makes the tree box stretchy
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        
        
    def getLatestRuleSetMap():
        
        def updateRuleSetMap(main_window, file_name, replace):
            try:
                xu.update_rule_set_map(cntlr, file_name, map_name, overwrite=bool(replace))
                main_window.destroy()
            except OSError:
                tkinter.messagebox.showinfo("File does not exists", "File '{}' does not exist".format(file_name))
            except xrt.XuleProcessingError:
                tkinter.messagebox.showinfo("Invalid Rule Set Map File", "{} is not a valid rule set map file".format(file_name))            
        
        def selectRuleSetMap(main_window, replace):
            filename = cntlr.uiFileDialog("open",
                                title=_("{} - Select Rule Set Map File".format(name)),
                                initialdir=cntlr.config.setdefault("fileOpenDir","."),
                                filetypes=[(_("Map files"), "*.*")],
                                defaultextension=".json")

            if os.sep == "\\":
                filename = filename.replace("/", "\\")
            
            if filename != '':
                updateRuleSetMap(main_window, filename, replace)
            else:
                main_window.destroy()
        
        def useLatestRuleSetMap(main_window, replace):
            updateRuleSetMap(main_window, _latest_map_name, replace)
            
        def useEnteredValue(main_window, entry_value, replace):
            updateRuleSetMap(main_window, entry_value.get(), replace)
        
        root = tkinter.Toplevel()
        # Frame for text at the top
        window_text =_("To update the {name} rule set map using the latest {name} map, click on ".format(name=name) +
                       "\"Use latest {name} rule set map\"\n".format(name=name) +
                       "You can also select a rule set map by pasting/typing the file name or URL and pressing the Enter key or\n" +
                       "using the file selector.\n\n" +
                       "Check the \"Overwrite rule set map\" if you want to completely overwrite the existing rule set map. \n" +
                       "Otherwise the new rule set map will be merged with your current rule set map. When merging, where namespaces are \n" +
                       "the same, the rule set from the new rule set map will be used. Namespaces in the current namespace map that are not \n" + 
                       "in the new namespace map will be left in the rule set map.")
        frame1 = tkinter.Frame(root, borderwidth=2)
        frame1.pack()
        frame1_label = tkinter.Label(frame1, text=window_text, justify=tkinter.LEFT)
        frame1_label.pack()
        
        frame1.winfo_toplevel().title("Update {} Rule Set Map".format(name))
        
        # Main frame
        frame = tkinter.Frame(root, borderwidth=2)
        frame.pack(anchor="w")
        
        # Replace check box
        frame2 = tkinter.Frame(root, borderwidth=2)
        frame2.pack(anchor="w")
        replace_var = tkinter.IntVar()
        replace_var.set(1)
        replace_check = tkinter.Checkbutton(frame2, text="Overwrite {} rule set map".format(name), variable=replace_var)
        replace_check.pack(side=tkinter.LEFT)
        
        latest_button = tkinter.Button(frame, command=lambda: useLatestRuleSetMap(root, replace_var), text="Use latest {} rule set map".format(name))
        latest_button.pack(side=tkinter.LEFT)
        or_label = tkinter.Label(frame, text="  or  ")
        or_label.pack(side=tkinter.LEFT)
        entry_value = tkinter.StringVar()
        entry = tkinter.Entry(frame, width=60, textvariable=entry_value)
        entry.bind('<Return>', lambda e: useEnteredValue(root, entry_value, replace_var))        
        entry.pack(side=tkinter.LEFT)
        frame.image = tkinter.PhotoImage(file=os.path.join(cntlr.imagesDir, "toolbarOpenFile.gif"))

        select_button = tkinter.Button(frame, command=lambda: selectRuleSetMap(root, replace_var))
        select_button.config(image=frame.image)
        select_button.pack(side=tkinter.LEFT)

    xuleMenu = tkinter.Menu(menu, tearoff=0)
    xuleMenu.add_command(label=_("Version..."), underline=0, command=showVersion)
    xuleMenu.add_command(label=_("Display {} rule set map...".format(name)), underline=0, command=showRuleSetMap)
    if cloud_map_location is not None:
        xuleMenu.add_command(label=_("Check {} rule set map".format(name)), underline=0, command=checkRuleSetMap)
        xuleMenu.add_command(label=_("Update {} rule set map...".format(name)), underline=0, command=getLatestRuleSetMap)

    menu.add_cascade(label=_("{}".format(name)), menu=xuleMenu, underline=0)
    return xuleMenu

def xuleValidateMenuTools(cntlr, validateMenu, *args, **kwargs):
    # Save the validationMenu object. 
    XuleVars.set(cntlr, 'validate_menu', validateMenu)
    
def addValidateMenuTools(cntlr, validateMenu, name, map_name):
    # Extend menu with an item for the save infoset plugin
    attr_name = 'validate{}'.format(name.strip())
    attr_value = cntlr.config.setdefault(attr_name, False)
    setattr(cntlr.modelManager, attr_name, attr_value)
    #cntlr.modelManager.validateDQC = cntlr.config.setdefault("validateDQC",False)
    from tkinter import BooleanVar
    validate_var = BooleanVar(value=getattr(cntlr.modelManager, attr_name))
    
    def setValidateXuleOption(*args):
        setattr(cntlr.modelManager, attr_name, validate_var.get())
        cntlr.config[attr_name] = getattr(cntlr.modelManager, attr_name)
        
    validate_var.trace("w", setValidateXuleOption)
    validateMenu.add_checkbutton(label=_("{} Rules".format(name)), 
                                 underline=0, 
                                 variable=validate_var, onvalue=True, offvalue=False)


    xuleRegisterValidators(name, map_name, validate_var)

def isXuleDirect():
    """Determines if xule was loaded as a direct plugin"""
    
    global _is_xule_direct
    if _is_xule_direct is None:
        global _options
        _is_xule_direct = False
        for plugin_command in getattr(_options, 'plugins', '').split('|'):
            if plugin_command.lower().endswith('xule'):
                _is_xule_direct = True

    return _is_xule_direct

def xuleRegisterValidators(name, map_name, validate_var=None):

    # Registers the validator
    global _xule_validators
    if validate_var is None:
        _xule_validators.append({'name':name, 'map_name': map_name})
    else:
        _xule_validators.append({'name':name, 'validate_flag': validate_var, 'map_name': map_name})

def xuleCmdOptions(parser):
    # extend command line options to compile rules
    if isinstance(parser, Options):
        parserGroup = parser
    else:
        parserGroup = optparse.OptionGroup(parser,
                                           "Xule Business Rule")
        parser.add_option_group(parserGroup)
    
    if xp is not None: # The XuleParser is imported
        parserGroup.add_option("--xule-compile",
                          action="store",
                          dest="xule_compile",
                          help=_("Xule files to be compiled.  "
                                 "This may be a file or directory.  When a directory is provided, all files in the directory will be processed.  "
                                 "Multiple file and directory names are separated by a '|' character. "))
    
    parserGroup.add_option("--xule-rule-set",
                      action="store",
                      dest="xule_rule_set",
                      help=_("RULESET to use (this is the directory where compile rules are stored."))
    
    parserGroup.add_option("--xule-run",
                      action="store_true",
                      dest="xule_run",
                      help=_("Indicates that the rules should be processed."))
    
    parserGroup.add_option("--xule-add-packages",
                           action="store",
                           dest="xule_add_packages",
                           help=_("Add packages to a xule rule set. Multiple package files are separated with a |."))

    parserGroup.add_option("--xule-remove-packages",
                           action="store",
                           dest="xule_remove_packages",
                           help=_("Remove packages from a xule rule set. Multiple package files are separated with a |."))
    
    parserGroup.add_option("--xule-show-packages",
                     action="store_true",
                     dest="xule_show_packages",
                     help=_("Show list of packages in the rule set."))    

    parserGroup.add_option("--xule-bypass-packages",
                     action="store_true",
                     dest="xule_bypass_packages",
                     help=_("Indicates that the packages in the rule set will not be activated."))  
    
    parserGroup.add_option("--xule-time",
                     action="store",
                     type="float",
                     dest="xule_time",
                     help=_("Output timing information. Supply the minimum threshold in seconds for displaying timing information for a rule."))
    
    parserGroup.add_option("--xule-trace",
                     action="store_true",
                     dest="xule_trace",
                     help=_("Output trace information."))
    
    parserGroup.add_option("--xule-trace-count",
                      action="store",
                      dest="xule_trace_count",
                      help=_("Name of the file to write a trace count."))
    
    parserGroup.add_option("--xule-debug",
                     action="store_true",
                     dest="xule_debug",
                     help=_("Output trace information."))    

    parserGroup.add_option("--xule-debug-table",
                     action="store_true",
                     dest="xule_debug_table",
                     help=_("Output trace information."))  
    
    parserGroup.add_option("--xule-debug-table-style",
                       action="store",
                       dest="xule_debug_table_style",
                       help=_("The table format. The valid values are tabulate table formats: plain, simple, grid, fancy_gri, pipe, orgtbl, jira, psql, rst, mediawiki, moinmoin, html, latex, latex_booktabs, textile."))  

    parserGroup.add_option("--xule-test-debug",
                     action="store_true",
                     dest="xule_test_debug",
                     help=_("Output testcase information."))   
    
    parserGroup.add_option("--xule-crash",
                     action="store_true",
                     dest="xule_crash",
                     help=_("Output trace information."))
    
    parserGroup.add_option("--xule-pre-calc",
                      action="store_true",
                      dest="xule_pre_calc",
                      help=_("Pre-calc expressions"))
    
    parserGroup.add_option("--xule-filing-list",
                      action="store",
                      dest="xule_filing_list",
                      help=_("File name of file that contains a list of filings to process"))
    
    if xm is not None:
        parserGroup.add_option("--xule-server",
                         action="store",
                         dest="xule_server",
                         help=_("Launch the webserver."))
    
        parserGroup.add_option("--xule-multi",
                         action="store_true",
                         dest="xule_multi",
                         help=_("Turns on multithreading"))
        
        parserGroup.add_option("--xule-cpu",
                         action="store",
                         dest="xule_cpu",
                         help=_("overrides number of cpus per processing to use"))
        
        parserGroup.add_option("--xule-async",
                         action="store_true",
                         dest="xule_async",
                         help=_("Outputs onscreen output as the filing is being processed"))
    
        parserGroup.add_option("--xule-numthreads",
                         action="store",
                         dest="xule_numthreads",
                         help=_("Indicates number of concurrents threads will run while the Xule Server is active"))
        
        parserGroup.add_option("--xule-skip",
                          action="store",
                          dest="xule_skip",
                          help=_("List of rules to skip"))
        
        parserGroup.add_option("--xule-run-only",
                          action="store",
                          dest="xule_run_only",
                          help=_("List of rules to run"))    
        
        parserGroup.add_option("--xule-no-cache",
                          action="store_true",
                          dest="xule_no_cache",
                          help=_("Turns off local caching for a rule."))
        
        parserGroup.add_option("--xule-precalc-constants",
                          action="store_true",
                          dest="xule_precalc_constants",
                          help=_("Pre-calculate constants that do not depend on the instance."))
    
        parserGroup.add_option("--xule-exclude-nils",
                          action="store_true",
                          dest="xule_exclude_nils",
                          help=_("Indicates that the processor should exclude nil facts. By default, nils are included."))
        
        parserGroup.add_option("--xule-include-dups",
                          action="store_true",
                          dest="xule_include_dups",
                          help=_("Indicates that the processor should include duplicate facts. By default, duplicate facts are ignored."))    
        
        parserGroup.add_option("--xule-version",
                          action="store_true",
                          dest="xule_version",
                          help=_("Display version number of the xule module."))
        
        parserGroup.add_option("--xule-display-rule-set-map",
                               action="store_true",
                               dest="xule_display_rule_set_map",
                               help=_("Display the rule set map currently used."))

        parserGroup.add_option("--xule-update-rule-set-map",
                               action="store",
                               dest="xule_update_rule_set_map",
                               help=_("Update the rule set map currently used. The supplied file will be merged with the current rule set map."))
    
        parserGroup.add_option("--xule-replace-rule-set-map",
                               action="store",
                               dest="xule_replace_rule_set_map",
                               help=_("Replace the rule set map currently used."))
        
        parserGroup.add_option("--xule-reset-rule-set-map",
                               action="store_true",
                               dest=("xule_reset_rule_set_map"),
                               help=_("Reset the rule set map to the default."))
    
    if xv is not None: # The XuleValidate module is imported
        parserGroup.add_option("--xule-validate",
                               action="store_true",
                               dest="xule_validate",
                               help=_("Validate ruleset"))
    
def xuleCmdUtilityRun(cntlr, options, **kwargs): 
    # Save the controller and options in the module global variable
    global _cntlr
    _cntlr = cntlr
    global _options
    _options = options 
    
    # check option combinations
    parser = OptionParser()
    
    if getattr(options, "xule_version", False):
        cntlr.addToLog("Xule version: %s" % __version__, 'xule')
        cntlr.close()

    if getattr(options, "xule_cpu", None) is not None and not getattr(options, 'xule_multi', None):
            parser.error(_("--xule-multi is required with --xule_cpu."))

    if getattr(options, "xule_server", None) is not None and not getattr(options, 'xule_rule_set', None):
            parser.error(_("--xule-rule-set is required with --xule_server."))

    from os import name
    if getattr(options, "xule_multi", False) and name == 'nt':
        parser.error(_("--xule-multi can't be used in Windows"))    

            
    if getattr(options, "xule-numthreads", None) == None:
        setattr(options, "xule-numthreads", 1)   
    
    if getattr(options, 'xule_add_packages', None) is not None and not getattr(options, 'xule_rule_set', None):
        parser.error(_("--xule-rule-set is required with --xule-add-packages.")) 

    if getattr(options, 'xule_remove_packages', None) is not None and not getattr(options, 'xule_rule_set', None):
        parser.error(_("--xule-rule-set is required with --xule-remove-packages.")) 

    if getattr(options, 'xule_show_packages', None) is not None and not getattr(options, 'xule_rule_set', None):
        parser.error(_("--xule-rule-set is required with --xule-show-packages."))    

    if len([x for x in (getattr(options, "xule_update_rule_set_map", False),
                       getattr(options, "xule_replace_rule_set_map", False),
                       getattr(options, "xule_reset_rule_set_map", False)) if x]) > 1:
        parser.error(_("Cannot use --xule-update-rule-set-map or --xule-replace-rule-set-map or --xule-reset-rule-set-map the same time."))
    
    if getattr(options, 'xule_validate', None) is not None and getattr(options, 'xule_rule_set', None) is None:
        parser.error(_("--xule-validate requires a Xule ruleset. Use option --xule-rule-set."))
    
    # compile rules
    if getattr(options, "xule_compile", None):
        compile_destination = getattr(options, "xule_rule_set", "xuleRules") 
        xp.parseRules(options.xule_compile.split("|"), compile_destination)
    
    # add packages
    if getattr(options, "xule_add_packages", None):
        rule_set = xr.XuleRuleSet(cntlr)
        rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
        packages = options.xule_add_packages.split('|')
        rule_set.manage_packages(packages, 'add')

    # remove packages
    if getattr(options, "xule_remove_packages", None):
        rule_set = xr.XuleRuleSet(cntlr)
        rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
        packages = options.xule_remove_packages.split('|')
        rule_set.manage_packages(packages, 'del')
    
    # show packages
    if getattr(options, "xule_show_packages", False):
        rule_set = xr.XuleRuleSet(cntlr)
        rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
        print("Packages in rule set:")
        for package_info in rule_set.get_packages_info():
            print('\t' + package_info.get('name') + ' (' + os.path.basename(package_info.get('URL')) + ')')
        
    # update rule set map
    if getattr(options, 'xule_update_rule_set_map', None):
        xu.update_rule_set_map(cntlr, getattr(options, 'xule_update_rule_set_map'), _xule_rule_set_map_name)
    
    # replace rule set map
    if getattr(options, 'xule_replace_rule_set_map', None):
        xu.update_rule_set_map(cntlr, getattr(options, 'xule_replace_rule_set_map'), _xule_rule_set_map_name, overwrite=True)
    
    # reset rule set map
    if getattr(options, 'xule_reset_rule_set_map', False):
        xu.reset_rule_set_map(cntlr, _xule_rule_set_map_name)

    # display the rule set map
    if getattr(options, 'xule_display_rule_set_map', False):
        displayValidatorRulesetMap(cntlr, 'Xule', _xule_rule_set_map_name)
        
    # validate ruleset
    if getattr(options, 'xule_validate', False):
        rule_set = xr.XuleRuleSet(cntlr)
        rule_set.open(options.xule_rule_set, open_packages=not getattr(options, 'xule_bypass_packages', False))
        xv.XuleValidate(cntlr, rule_set, options.xule_rule_set)
    
    if getattr(options, "xule_server", None):
        from threading import Thread
        
        try:
            rule_set = xr.XuleRuleSet()
            rule_set.open(options.xule_rule_set, False)
        except xr.XuleRuleSetError:
            raise

        # Create global Context
        global_context = XuleGlobalContext(rule_set, cntlr=cntlr, options=options)

        global_context.message_queue.print("Using %d processors" % (global_context.num_processors)) 

        # Start Output message queue
        if getattr(options, "xule_multi", False):
            t = Thread(target=xm.output_message_queue, args=(global_context,))
            t.start()
        
        global_context.message_queue.logging("Building Constant and Rule Groups")
        global_context.all_constants = rule_set.get_grouped_constants()
        global_context.all_rules = rule_set.get_grouped_rules()        

        
        for g in global_context.all_constants:
            global_context.message_queue.logging("Constants: %s - %d" % (g, len(global_context.all_constants[g])))

        for g in global_context.all_rules:
            global_context.message_queue.logging("Rules: %s - %d" % (g, len(global_context.all_rules[g])))

        # evaluate valid constants (no dependency, rules taxonomy)
        global_context.message_queue.logging("Calculating and Storing Constants")
        xm.run_constant_group(global_context, 'c', 'rtc')

                                   
        # Add precalculated information to the cntlr to pass to XuleServer
        setattr(cntlr, "xule_options", options)
        setattr(cntlr, "rule_set", global_context.rule_set)        
        setattr(cntlr, "constant_list", global_context._constants)
        setattr(cntlr, "all_constants", global_context.all_constants)
        setattr(cntlr, "all_rules", global_context.all_rules)        


        global_context.message_queue.logging("Finished Server Initialization")
        
        # stop message_queue
        global_context.message_queue.stop()
        
        if getattr(options, "xule_multi", False):
            t.join()
    else:
        if options.entrypointFile is None:
            # try running the xule processor
            xuleCmdXbrlLoaded(cntlr, options, None)
    # process filing list
    if getattr(options, "xule_filing_list", None):
        try:
            with open(options.xule_filing_list, "r") as filing_list:
                for line in filing_list:

                    filing = line.strip()
                    print("Processing filing", filing)
                    filing_filesource = FileSource.openFileSource(filing, cntlr)            
                    modelManager = ModelManager.initialize(cntlr)
                    modelXbrl = modelManager.load(filing_filesource) 
                    xuleCmdXbrlLoaded(cntlr, options, modelXbrl)
                    modelXbrl.close()

        except FileNotFoundError:
            cntlr.addToLog(_("Filing listing file '%s' is not found" % options.xule_filing_list), 'xule')
    
    # Only register xule as a validator if the xule plugin was directly added in the --plugin optins.
    if isXuleDirect():
        xuleRegisterValidators('Xule', _xule_rule_set_map_name)
    
def xuleCmdXbrlLoaded(cntlr, options, modelXbrl, entryPoint=None):   
    if getattr(options, "xule_run", None):
        runXule(cntlr, options, modelXbrl)
        
def runXule(cntlr, options, modelXbrl, rule_set_map=_xule_rule_set_map_name):
        try:
            if getattr(options, "xule_multi", True) and \
                getattr(cntlr, "rule_set", None) is not None:
                rule_set = getattr(cntlr, "rule_set")
            else:
                if getattr(options, 'xule_rule_set', None) is not None:
                    rule_set_location = options.xule_rule_set
                else:
                    # Determine the rule set from the model.
                    rule_set_location = xu.determine_rule_set(modelXbrl, cntlr, rule_set_map)
                    modelXbrl.log('INFO', 'info', 'Using ruleset {}'.format(rule_set_location))
                    if rule_set_location is None:
                        # The rule set could not be determined.
                        modelXbrl.log('ERROR', 'xule', "Cannot determine which rule set to use for the filing. Check the rule set map at '{}'.".format(xu.get_rule_set_map_file_name(cntlr, rule_set_map)))
                        raise xr.XuleRuleSetError('The rule set to used could not be determined. Check that there is a rule set map at {} and verify that there is an appropiate mapping for the filing.'.format(xu.get_rule_set_map_file_name(cntlr, rule_set_map)))
                    
                rule_set = xr.XuleRuleSet(cntlr)              
                rule_set.open(rule_set_location, open_packages=not getattr(options, 'xule_bypass_packages', False))
        except xr.XuleRuleSetError:
            raise

        if getattr(options, "xule_multi", False):
            xm.start_process(rule_set,
                         modelXbrl,
                         cntlr,
                         options
                         )
        else:
            if modelXbrl is None:
                # check if there are any rules that need a model
                for rule in rule_set.catalog['rules'].values():
                    if rule['dependencies']['instance'] == True and rule['dependencies']['rules-taxonomy'] != False:
                        raise xr.XuleRuleSetError('Need instance to process rules')
                    
            global _saved_taxonomies        
            used_taxonomies = process_xule(rule_set,
                                           modelXbrl,
                                           cntlr,
                                           options,
                                           _saved_taxonomies
                                           )
            # Save one loaded taxonomy
            new_taxonomy_keys = used_taxonomies.keys() - _saved_taxonomies.keys()
            if len(new_taxonomy_keys) > 0:
                for tax_key in list(new_taxonomy_keys)[:2]: # This take at most 2 taxonomies.
                    tax_key = next(iter(new_taxonomy_keys)) # randomly get one key
                    _saved_taxonomies[tax_key] = used_taxonomies[tax_key]
            
def xuleValidate(val):
    global _cntlr
    global _options
    global _xule_validators
    
#     #This will only run from command line
#     # _options will not be EmptyOptions when run from command line.
#     if _cntlr is not None and not isinstance(_options, EmptyOptions):
#         if not getattr(_options, "xule_run", False):
#             # Only run on validate if the --xule-run option was not supplied. If --xule-run is supplied, it has already been run
#             for xule_validator in _xule_validators:
#                 runXule(_cntlr, _options, val.modelXbrl, xule_validator['map_name'])
# 
#     # This will only run from gui
#     for xule_validator in _xule_validators:
#         # The 'validate_flag' is only registered when run from the GUI
#         if 'validate_flag' in xule_validator and xule_validator['validate_flag'].get():
#             val.modelXbrl.modelManager.showStatus(_("Starting {} validation".format(xule_validator['name'])))
#             val.modelXbrl.info("DQC",_("Starting {} validation".format(xule_validator['name'])))
#             runXule(_cntlr, _options, val.modelXbrl, xule_validator['map_name'])
#             val.modelXbrl.info(xule_validator['name'],_("Finished {} validation".format(xule_validator['name'])))
#             val.modelXbrl.modelManager.showStatus(_("Finished {} validation".format(xule_validator['name'])))

    for xule_validator in _xule_validators:
        if 'validate_flag' in xule_validator:
            # This is run in the GUI. The 'validate_flag' is only in the xule_validator when invoked from the GUI
            if xule_validator['validate_flag'].get():
                # Only run if the validate_flag variable is ture (checked off in the validate menu)
                val.modelXbrl.modelManager.showStatus(_("Starting {} validation".format(xule_validator['name'])))
                val.modelXbrl.info("DQC",_("Starting {} validation".format(xule_validator['name'])))
                runXule(_cntlr, _options, val.modelXbrl, xule_validator['map_name'])
                val.modelXbrl.info(xule_validator['name'],_("Finished {} validation".format(xule_validator['name'])))
                val.modelXbrl.modelManager.showStatus(_("Finished {} validation".format(xule_validator['name']))) 
        else:
            # This is run on the command line or web server
            # Only run on validate if the --xule-run option was not supplied. If --xule-run is supplied, it has already been run
            if not getattr(_options, "xule_run", False):
                runXule(_cntlr, _options, val.modelXbrl, xule_validator['map_name'])            

    if _cntlr.hasWebServer:
        # When arelle is running as a webserver, it will register the xule_validators on each request to the web server. 
        # The _xule_validators is emptied. On the next request, the xule_validators for that request will be re-register.
        _xule_validators = []

def xuleTestXbrlLoaded(modelTestcase, modelXbrl, testVariation):
    global _options
    global _test_start
    global _test_variation_name
    
    if getattr(_options, 'xule_test_debug', False):
        _test_start = datetime.datetime.today()
        _test_variation_name = testVariation.id
        print('{}: Testcase variation {} started'.format(_test_start.isoformat(sep=' '), testVariation.id))

def xuleTestValidated(modelTestcase, modelXbrl):
    global _options
    global _test_start
    global _test_variation_name
    
    if getattr(_options, 'xule_test_debug', False):
        if _test_start is not None:            
            test_end = datetime.datetime.today()
            print("{}: Test variation {} finished. in {} ".format(test_end.isoformat(sep=' '), _test_variation_name, (test_end - _test_start)))

def updateValidatorRulesetMap(cntlr, new_map, map_name):
    xu.update_rule_set_map(cntlr, new_map, map_name)
    
def replaceValidatorRulesetMap(cntlr, new_map, map_name):
    xu.update_rule_set_map(cntlr, new_map, map_name, overwrite=True)    

def displayValidatorRulesetMap(cntlr, validator_name, map_name):
    map = xu.get_rule_set_map(cntlr, map_name)
    map_file_name = xu.get_rule_set_map_file_name(cntlr, map_name)
    display_map = json.dumps(map, indent=4)
    cntlr.addToLog("{} Rule Set map {} - {}\n{}".format(validator_name,  map_name, map_file_name, display_map ), validator_name)    
    
__pluginInfo__ = {
    'name': 'XBRL rule processor (xule)',
    'version': 'Check version using Tools->DQC->Version on the GUI or --xule-version on the command line',
    'description': 'This plug-in provides a DQC processor.',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017-2018',
    # classes of mount points (required)
    'ModelObjectFactory.ElementSubstitutionClasses': None,
    'CntlrWinMain.Menu.Tools': xuleMenuTools,
    'CntlrWinMain.Menu.Validation':xuleValidateMenuTools,
    'CntlrCmdLine.Options': xuleCmdOptions,
    'CntlrCmdLine.Utility.Run': xuleCmdUtilityRun,
    'CntlrCmdLine.Xbrl.Loaded': xuleCmdXbrlLoaded,
    'Validate.Finally': xuleValidate,
    'TestcaseVariation.Xbrl.Loaded': xuleTestXbrlLoaded,
    'TestcaseVariation.Xbrl.Validated': xuleTestValidated,
    'Xule.AddMenuTools': addMenuTools,
    'Xule.AddValidationMenuTools': addValidateMenuTools,
    'Xule.ValidatorVersion': xu.version,
    'Xule.RegisterValidator': xuleRegisterValidators,
    'Xule.RulesetMap.Update': updateValidatorRulesetMap,
    'Xule.RulesetMap.Replace': replaceValidatorRulesetMap,
    'Xule.RulesetMap.Display': displayValidatorRulesetMap    
    }
