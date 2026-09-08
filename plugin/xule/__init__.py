"""__init__.py

Xule is a rule processor for XBRL (X)brl r(ULE). 

This is the package init file.

DOCSKIP
See https://xbrl.us/dqc-license for license information.  
See https://xbrl.us/dqc-patent for patent infringement notice.
Copyright (c) 2017 - present XBRL US, Inc.

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
import sys

from .XuleProcessor import process_xule
from . import XuleRunTime as xrt
from . import XuleRuleSet as xr
from . import XuleUtility as xu
from . import XuleConstants as xc
from .XuleContext import XuleGlobalContext, XuleRuleContext
import collections
import copy
import logging

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

try:
    import tabulate as tab
except ImportError:
    tab = None

from arelle import FileSource
from arelle import ModelManager
from arelle import PluginManager
import optparse
import os 
import datetime
import json

_MIN_CPUS_PER_FILING = 2  # minimum rule-worker slots required to start processing a filing

# Global variables are set for the Xule package. However, Arelle may import the package multiple times, which causes
# these variables to reset each time. This try block checks if the package global variables are already defined, if
# not then they are defined/initialized. The __version__ variable is used as a proxy for all the other variables.
try:
    __version__
except NameError:
    __version__ = '3.0.' + (xu.version() or '')
    _cntlr = None
    #_options = None
    _is_xule_direct = None
    _saved_taxonomies = dict()
    _test_start = None
    _test_variation_name = None
    _latest_map_name = None
    _xule_validators = []
    _xule_rule_set_map_name = 'xuleRulesetMap.json'
    _server_mode = False
    _shared_cntlr = None

def _xule_request_worker(child_conn, options, sourceZipStream, media):
    """Runs in a per-request forked process.  _shared_cntlr is inherited via fork (not pickled).
    The process exits after one request so no state bleeds between requests.  Results are sent
    back to the parent through a one-way Pipe connection, avoiding the Manager dict overhead and
    the inherited-connection issues that a multiprocessing.Pool would introduce.

    CPU budget protocol (server mode only):
      Step 1 – Claim a filing slot immediately (bounded by max_concurrent_filings).
               Incrementing shared_running_filings HERE, before waiting for CPU slots,
               causes watch_processes in every already-running filing to wake up
               (via notify_all) and rebalance their allocations downward.  This is
               what allows a newly-arrived filing to actually obtain CPUs instead of
               sitting blocked while filing-1 holds everything.
      Step 2 – Wait until _MIN_CPUS_PER_FILING slots are free, then claim them.
               The rebalance triggered by Step 1 will have released slots into the
               pool by the time this wait resolves.
      Step 3 – Greedily claim up to this filing's fair share of the total budget.
      Finally – Return all still-held slots and decrement shared_running_filings.
    """
    from math import floor
    cond = getattr(_shared_cntlr, 'shared_cpu_condition', None)

    if cond is not None:
        # ── Step 1: claim a filing slot ───────────────────────────────────────
        # Increment shared_running_filings BEFORE waiting for CPU slots so the
        # rebalance formula (floor(total/running)) in every already-running
        # filing's watch_processes immediately sees the new demand and sheds CPUs
        # into the shared pool for us to claim in Step 2.
        # The cap (max_concurrent_filings = total / MIN_CPUS) prevents the
        # denominator from growing so large that each share falls below MIN_CPUS.
        # Requests beyond the cap wait here until a slot frees at filing exit.
        max_concurrent = getattr(_shared_cntlr, 'max_concurrent_filings', 4)
        with cond:
            cond.wait_for(
                lambda: _shared_cntlr.shared_running_filings.value < max_concurrent
            )
            _shared_cntlr.shared_running_filings.value += 1
            cond.notify_all()   # wake watch_processes in all running filings

        # ── Step 2: wait for minimum CPU slots then claim them ────────────────
        # The notify_all above causes running filings to rebalance (shed CPUs),
        # so this wait should resolve quickly once they shed their surplus.
        with cond:
            cond.wait_for(
                lambda: _shared_cntlr.shared_available_cpus.value >= _MIN_CPUS_PER_FILING
            )
            _shared_cntlr.shared_available_cpus.value -= _MIN_CPUS_PER_FILING
            running = _shared_cntlr.shared_running_filings.value

        # ── Step 3: claim additional slots up to this filing's fair share ──────
        initial_target = max(_MIN_CPUS_PER_FILING,
                             floor(_shared_cntlr.total_cpus / running))
        additional = initial_target - _MIN_CPUS_PER_FILING
        if additional > 0:
            with cond:
                additional = min(additional, _shared_cntlr.shared_available_cpus.value)
                _shared_cntlr.shared_available_cpus.value -= additional
        allocation = _MIN_CPUS_PER_FILING + additional

        # _cpu_state is a mutable dict shared between this thread and watch_processes so that
        # watch_processes can adjust the allocation during processing and the finally block
        # can return exactly the right number of slots to the pool.
        _shared_cntlr._cpu_state = {'allocation': allocation}
        setattr(options, 'xule_cpu', allocation)

    try:
        _shared_cntlr.logHandler.clearLogBuffer()
        success = _shared_cntlr.run(options, sourceZipStream)
        if media == "xml":
            result = _shared_cntlr.logHandler.getXml()
        elif media == "json":
            result = _shared_cntlr.logHandler.getJson()
        elif media == "text":
            result = _shared_cntlr.logHandler.getText()
        else:
            result = list(_shared_cntlr.logHandler.getLines())
        child_conn.send((success, result))
    except Exception as e:
        child_conn.send((False, [str(e)]))
    finally:
        if cond is not None:
            # Return all pre-claimed slots still held by this filing.  Slots consumed by
            # 'stopping' (shrink) workers are returned to the pool as those workers die
            # inside watch_processes; slots that cycled through natural worker deaths remain
            # in cpu_allocation and are returned here.
            remaining = _shared_cntlr._cpu_state.get('allocation', 0)
            with cond:
                if remaining > 0:
                    _shared_cntlr.shared_available_cpus.value += remaining
                _shared_cntlr.shared_running_filings.value -= 1
                cond.notify_all()
        child_conn.close()


def _warm_up_taxonomy_cache(cntlr, rule_set_path, message_queue=None):
    """Load the sample filing that matches the active rule set's taxonomy type and year.

    Inspects *rule_set_path* (e.g. "dqc-us-2025-V31", "dqc-ifrs-2025-V31") to
    determine both the taxonomy family and the target year, then looks for a
    matching file in /code/filings.

    Taxonomy type detection (first match wins, case-insensitive):
      dqc-us   → usgaap   (e.g. usgaap-2025.zip)
      dqc-ifrs → ifrs     (e.g. ifrs-2025.zip)
      dqc-esef → esef     (e.g. esef-2025.zip)

    Files are tried in extension order: .zip, .htm, .xml.  Only the one file
    matching the detected taxonomy+year is loaded; if no match is found the
    warm-up is skipped silently.

    The loaded ModelXbrl is intentionally kept open so the parent web-server process
    retains the parsed schema objects in memory.  Forked request workers inherit
    those objects via copy-on-write, cutting cold-start filing load time from
    10–15 seconds to under a second.

    Sample filings should be placed in /code/filings inside the container, named
    as {taxonomy}-{year}.{ext}, e.g. usgaap-2025.zip, ifrs-2025.zip, esef-2025.zip.
    See support_files/filings/README.md for details.
    """
    import os
    import re

    warmup_dir = '/code/filings'

    # Ordered list of (substring-in-rule-set-path, warm-up-file-prefix).
    # Checked case-insensitively against the rule set basename; first match wins.
    _TAXONOMY_PREFIXES = [
        ('dqc-us',   'usgaap'),
        ('dqc-ifrs', 'ifrs'),
        ('dqc-esef', 'esef'),
    ]

    def _log(msg):
        if message_queue is not None:
            message_queue.logging(msg)
        else:
            cntlr.addToLog(msg, 'xule')

    base = os.path.basename(rule_set_path or '').lower()

    # Detect taxonomy family.
    taxonomy_prefix = None
    for key, prefix in _TAXONOMY_PREFIXES:
        if key in base:
            taxonomy_prefix = prefix
            break

    if taxonomy_prefix is None:
        _log("Taxonomy warm-up: unrecognised taxonomy in rule set path '%s' — skipping"
             % rule_set_path)
        return

    # Extract the first four-digit year-like number (20xx) from the rule set path.
    match = re.search(r'20\d{2}', base)
    if not match:
        _log("Taxonomy warm-up: no year found in rule set path '%s' — skipping"
             % rule_set_path)
        return

    year = match.group(0)
    stem = '%s-%s' % (taxonomy_prefix, year)   # e.g. "usgaap-2025"

    if not os.path.isdir(warmup_dir):
        _log("Taxonomy warm-up: directory %s not found — skipping" % warmup_dir)
        return

    # Try each supported extension in preference order.
    filing_path = None
    for ext in ('.zip', '.htm', '.xml'):
        candidate = os.path.join(warmup_dir, stem + ext)
        if os.path.isfile(candidate):
            filing_path = candidate
            break

    if filing_path is None:
        _log("Taxonomy warm-up: no filing found for '%s' in %s — skipping"
             % (stem, warmup_dir))
        return

    from arelle import FileSource

    name = os.path.basename(filing_path)
    _log("Taxonomy warm-up: loading %s (taxonomy %s, year %s)" % (name, taxonomy_prefix, year))
    try:
        # Arelle expects the entry-point document, not the ZIP container itself.
        # For a ZIP file, append the main HTM/XML filename so Arelle receives a
        # path of the form  /code/filings/2025.zip/report.htm  rather than
        # /code/filings/2025.zip  (which it would try to read as plain text and
        # fail with a UTF-8 decode error).
        load_url = filing_path
        if filing_path.endswith('.zip'):
            entry = _find_zip_entry(filing_path)
            if entry is None:
                _log("Taxonomy warm-up: no HTM/XML entry point found inside %s — skipping"
                     % name)
                return
            load_url = filing_path + '/' + entry
            _log("Taxonomy warm-up: entry point is %s" % entry)

        file_source = FileSource.openFileSource(load_url, cntlr)
        cntlr.modelManager.load(file_source, "Taxonomy warm-up: %s" % name)
        # Intentionally NOT calling modelXbrl.close() — keeping the model open
        # retains the parsed DTS in the parent's memory so forked request workers
        # inherit it via copy-on-write rather than re-parsing from disk.
        _log("Taxonomy warm-up complete: %s" % name)
    except Exception as e:
        _log("Taxonomy warm-up failed (%s): %s — continuing" % (name, str(e)))


def _find_zip_entry(zip_path):
    """Return the filename of the main iXBRL document inside an EDGAR filing ZIP.

    Strategy 1 — filing-summary.xml (EDGAR standard):
        EDGAR submission ZIPs include a filing-summary.xml whose <InputFiles>
        section lists the primary instance document first.  We parse it and return
        the first .htm/.html file found there.

    Strategy 2 — largest non-exhibit HTM:
        If no filing-summary.xml exists (older or non-EDGAR ZIPs), we pick the
        top-level HTM file with the largest uncompressed size, excluding files
        that look like exhibit attachments or EDGAR viewer report pages:
          - exhibit pattern:  ex<digits>, _ex<digits>, exhibit (case-insensitive)
          - viewer pages:     R<digits>.htm  (EDGAR interactive viewer)
          - linkbase XML:     files with label/calc/def/pre/ref suffixes

    Returns None if no suitable document is found.
    """
    import re
    import zipfile
    import xml.etree.ElementTree as ET

    def _is_exhibit(filename):
        """True if the filename looks like an EDGAR exhibit or viewer page."""
        base = filename.lower().rsplit('.', 1)[0]
        # Viewer report pages: R1.htm, R2.htm, …
        if re.match(r'^r\d+$', base):
            return True
        # Exhibit files: ex31.htm, bstx_ex31z1.htm, exhibit32.htm, …
        if re.search(r'(?:^|[_\-])ex\d', base):
            return True
        if 'exhibit' in base:
            return True
        return False

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            # Top-level files only (no sub-directory paths)
            top_level = [n for n in names if '/' not in n and '\\' not in n]

            # ── Strategy 1: filing-summary.xml ──────────────────────────────
            if 'filing-summary.xml' in top_level:
                try:
                    with zf.open('filing-summary.xml') as f:
                        root = ET.parse(f).getroot()
                    # <InputFiles><File>primary.htm</File>...</InputFiles>
                    for elem in root.iter('File'):
                        fname = (elem.text or '').strip()
                        if fname.lower().endswith(('.htm', '.html')) and fname in top_level:
                            return fname
                except Exception:
                    pass  # fall through to strategy 2

            # ── Strategy 2: largest non-exhibit HTM ──────────────────────────
            candidates = []
            for n in top_level:
                if not n.lower().endswith(('.htm', '.html')):
                    continue
                if _is_exhibit(n):
                    continue
                try:
                    size = zf.getinfo(n).file_size
                except Exception:
                    size = 0
                candidates.append((size, n))

            if candidates:
                # The main iXBRL filing is almost always the largest HTM in the ZIP
                candidates.sort(reverse=True)
                return candidates[0][1]

            # ── Strategy 3: any top-level XML that isn't a linkbase/summary ──
            linkbase_suffixes = ('_lab.xml', '_cal.xml', '_def.xml',
                                 '_pre.xml', '_ref.xml', 'summary.xml')
            for n in top_level:
                if n.lower().endswith('.xml') and not any(
                        n.lower().endswith(s) for s in linkbase_suffixes):
                    return n

    except Exception:
        pass

    return None


def xuleCntlrWebMainStartWebServer(app, cntlr, host, port, server):
    """CntlrWebMain.StartWebServer hook: records the fully-initialised cntlr for worker forks
    and creates the shared multiprocessing primitives for cross-filing CPU budget tracking.

    This fires after cntlr.startLogging() has run (so logHandler is ready) but before the
    HTTP server accepts its first request.  Storing cntlr here means each per-request fork
    inherits a complete cntlr — constants loaded, logHandler configured — via copy-on-write.
    The shared Value/Condition objects are also inherited by every fork and are backed by
    OS shared memory, so all concurrent filing processes see the same pool state.
    Returns None so arelle still registers all default routes and starts the server normally.
    """
    from multiprocessing import Value, Lock, Condition
    from os import cpu_count as _cpu_count
    global _server_mode, _shared_cntlr

    total = _cpu_count() or 1
    cpu_lock = Lock()
    cpu_condition = Condition(cpu_lock)

    cntlr.total_cpus = total
    cntlr.min_cpus_per_filing = _MIN_CPUS_PER_FILING
    # Maximum number of filings counted toward the rebalance formula at once.
    # Derived from the CPU budget: floor(total / MIN_CPUS) gives the most filings
    # that can each receive at least MIN_CPUS_PER_FILING slots simultaneously.
    # Step 1 of _xule_request_worker waits until running_filings < this cap before
    # joining the active pool, so excess requests queue naturally.
    cntlr.max_concurrent_filings = max(1, total // _MIN_CPUS_PER_FILING)
    cntlr.shared_available_cpus = Value('i', total)
    cntlr.shared_running_filings = Value('i', 0)
    cntlr.shared_cpu_condition = cpu_condition

    _server_mode = True
    _shared_cntlr = cntlr
    return None


def xuleCntlrWebMainRunOptions(cntlr, options, sourceZipStream, responseZipStream, media, viewFile):
    """CntlrWebMain.RunOptions hook: isolates each HTTP request in its own forked process.

    Uses Process + Pipe rather than a Pool so there are no pool-management threads in the
    parent that could deadlock a forked child, and no shared Pool connections that xule's
    own rule-worker subprocesses would inherit and corrupt.
    Falls back to None (default arelle path) for zip / view requests that depend on
    in-process file objects.
    """
    if not _server_mode or responseZipStream is not None or viewFile is not None:
        return None

    from multiprocessing import Process, Pipe

    parent_conn, child_conn = Pipe(duplex=False)
    p = Process(target=_xule_request_worker,
                args=(child_conn, options, sourceZipStream, media))
    p.start()
    child_conn.close()
    try:
        result_tuple = parent_conn.recv()
    finally:
        parent_conn.close()
    p.join()
    return result_tuple


class EmptyOptions:
    pass

def xuleMenuTools(cntlr, menu):
    import tkinter
    
    global _cntlr
    _cntlr = cntlr
    
    attr_name = 'xule_is_on'
    setattr(cntlr.modelManager, attr_name, cntlr.config.setdefault(attr_name,False))

    if getattr(cntlr.modelManager, attr_name):
        addMenuTools(cntlr, menu, 'Xule', '', __file__, _xule_rule_set_map_name, _latest_map_name)
    else:
        activate_xule_label = "Activate"
        def turnOnXule():
            # The validation menu hook is hit before the tools menu hook. the XuleVars for 'validate_menu' is set in the validation menu hook.
            validate_menu = xu.XuleVars.get(cntlr, 'validate_menu')
            addValidateMenuTools(cntlr, validate_menu, 'Xule', _xule_rule_set_map_name)
            menu.delete('Xule')
            xule_menu = addMenuTools(cntlr, menu, 'Xule', '', __file__, _xule_rule_set_map_name, _latest_map_name)
            
            def turnOffXule():
                validate_menu.delete('Xule Rules')
                menu.delete('Xule')
                new_xule_menu = tkinter.Menu(menu, tearoff=0)
                new_xule_menu.add_command(label=activate_xule_label, underline=0, command=xu.XuleVars.get(cntlr, 'activate_xule_function'))
                menu.add_cascade(label=_("Xule"), menu=new_xule_menu, underline=0)
                cntlr.config['xule_activated'] = False
                
            xule_menu.add_command(label='Deactivate Xule', underline=0, command=turnOffXule)
            cntlr.config['xule_activated'] = True
        
        xule_menu = tkinter.Menu(menu, tearoff=0)
        xule_menu.add_command(label=activate_xule_label, underline=0, command=turnOnXule)
        xu.XuleVars.set(cntlr, 'activate_xule_function', turnOnXule)
    
        menu.add_cascade(label=_("Xule"), menu=xule_menu, underline=0)
        
        if cntlr.config.get('xule_activated', False):
            turnOnXule()

def addMenuTools(cntlr, menu, name, version_prefix, version_file, map_name, cloud_map_location):
                #cntlr, menu, 'Xule', '', __file__, _xule_rule_set_map_name, _latest_map_name
    import tkinter
    import tkinter.ttk as ttk
    import tkinter.font as tkFont
    
    def showVersion():
        if name == 'Xule':
            version_text = "{}".format(versionText(cntlr, name, map_name, version_prefix, version_file))
        else:
            version_text = "{}\n{}".format(versionText(cntlr, name, map_name, version_prefix, version_file),
                                           versionText(cntlr, 'Xule', _xule_rule_set_map_name, '', __file__))

        tkinter.messagebox.showinfo("{} Version".format(name), version_text)

    def showRuleSetMap():
        #try:
        #    map = xu.get_rule_set_map(cntlr, map_name)
            map_file_name = xu.get_rule_set_map_file_name(cntlr, map_name)
        #except xrt.XuleMissingRuleSetMap:
        #    tkinter.messagebox.showinfo(_("Cannot find rule set map"), _("Rule set map for '{}' does not exist. Rule set map file name is '{}'".format(name, xu.get_rule_set_map_file_name(cntlr, map_name))))
        #else:

            cntlr.showStatus(_("Loading rule set map data..."))
            headers = ['Namespace', 'Rule Set', 'Version']
            # Set the value of the map dictionary to be a list.
            displayRuleSetMap(rulesetMapData(cntlr, map_name), headers, '{} Rule Set Map - {}'.format(name, map_file_name))
            # Reset the status message at the bottom of the main window
            cntlr.showStatus(_("Ready..."))

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
                x = list(row)[col_index] or ''
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
            updateRuleSetMap(main_window, cloud_map_location, replace)
            
        def useEnteredValue(main_window, entry_value, replace):
            updateRuleSetMap(main_window, entry_value.get(), replace)
        
        root = tkinter.Toplevel()
        # Frame for text at the top
        window_text =_("To update the {name} rule set map using the latest {name} map, click on ".format(name=name) +
                       "\"Use latest approved {name} rule set map\"\n".format(name=name) +
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
        
        latest_button = tkinter.Button(frame, command=lambda: useLatestRuleSetMap(root, replace_var), text="Use latest approved {} rule set map".format(name))
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
    xu.XuleVars.set(cntlr, 'validate_menu', validateMenu)
    
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
        
    validate_var.trace_add("write", setValidateXuleOption)
    validateMenu.add_checkbutton(label=_("{} Rules".format(name)), 
                                 underline=0, 
                                 variable=validate_var, onvalue=True, offvalue=False)


    xuleRegisterValidators(name, map_name, validate_var)

def isXuleDirect(cntlr):
    """Determines if xule was loaded as a direct plugin"""
    
    global _is_xule_direct
    if _is_xule_direct is None:
        _is_xule_direct = False
        for plugin_command in getattr(xu.XuleVars.get(cntlr, 'options'), 'plugins', '').split('|'):
            if plugin_command.lower().strip().endswith('xule'):
                _is_xule_direct = True

    return _is_xule_direct

def xuleRegisterValidators(name, map_name, validate_var=None):

    # Registers the validator
    global _xule_validators
    if validate_var is None:
        _xule_validators.append({'name':name, 'map_name': map_name})
    else:
        _xule_validators.append({'name':name, 'validate_flag': validate_var, 'map_name': map_name})

def validatorVersion(cntlr, validator_name, map_name, version_prefix, validator_file):
    '''Log the version text'''
    version_text = versionText(cntlr, validator_name, map_name, version_prefix, validator_file)

    cntlr.addToLog(version_text, 'info')

def versionText(cntlr, validator_name, map_name, version_prefix, validator_file):
    '''Get the version information and format it as text'''
    version = version_prefix + xu.version(validator_file)
    if validator_name == 'Xule':
        version_text = 'Xule processor version : {}'.format(__version__)
    else:
        version_text = '{} validator version: {}'.format(validator_name, version)

    return version_text

    # The following code is not currently being used. It will read each of the rule sets and report the version.
    # However, this does not perform well be cause each ruleset has to be downloaded and read.
    if map_name is not None:
        try:
            map_data = rulesetMapData(cntlr, map_name)[1:]
        except:
            pass #ignore problems reading the rule set map
        else:
            map_by_version = collections.defaultdict(list)
            for map_line in map_data:
                map_by_version[map_line[2]].append(map_line)
            version_text += '\n\n'
            for rule_set_version in map_by_version:
                version_text += 'Rule set version {}:\n'.format(rule_set_version)
                version_text += '\n'.join('  {}'.format(x[0]) for x in map_by_version[rule_set_version])

    return version_text
def xuleCmdOptions(parser):
    # extend command line options to compile rules
    if isinstance(parser, optparse.OptionParser):
        # This is the normal optparse.OptionsParser object.
        parserGroup = optparse.OptionGroup(parser,
                                           "Xule Business Rule")
        parser.add_option_group(parserGroup)
    else:
        # This is a fake parser object (which does not support option groups). This is sent when arelle is in GUI
        # mode or running as a webserver
        parserGroup = parser
    
    if xp is not None: # The XuleParser is imported
        parserGroup.add_option("--xule-compile",
                          action="store",
                          dest="xule_compile",
                          help=_("Xule files to be compiled.  "
                                 "This may be a file or directory.  When a directory is provided, all files in the directory will be processed.  "
                                 "Multiple file and directory names are separated by a '|' character. "))
        
        parserGroup.add_option("--xule-compile-type",
                              action="store",
                              dest="xule_compile_type",
                              default="pickle",
                              help=_("Determines how the compiled rules are stored. Options are 'pickle', 'json'."))
    
        parserGroup.add_option("--xule-compile-save-pyparsing-result-location",
                               action="store",
                               help=_("This will save the result from pyparsing as a json file. This is the raw parse results before post parsing. Used for debugging purpsoses."))

        parserGroup.add_option("--xule-compile-workers",
                               action="store",
                               dest="xule_compile_workers",
                               default=1,
                               type="int",
                               help=_("Controls the number of worker processes used to compile XULE rule files in parallel. A value of 0 will use the number of machine processors."))

    parserGroup.add_option("--xule-rule-set",
                      action="store",
                      dest="xule_rule_set",
                      help=_("RULESET to use (this is the directory where compile rules are stored."))
    
    parserGroup.add_option("--xule-run",
                      action="store_true",
                      dest="xule_run",
                      help=_("Indicates that the rules should be processed."))
    
    parserGroup.add_option("--xule-cache-size-bytes",
                        action="store",
                        dest="xule_cache_size_bytes",
                        default=1_000_000_000,
                        type="int",
                        help=_("The maximum size of the per-rule expression cache in bytes."))

    parserGroup.add_option("--xule-max-rule-iterations",
                        action="store",
                        dest="xule_max_rule_iterations",
                        default=10000,
                        type="int",
                        help=_("The maximum amount of iterations any xule rule should be allowed to run.")
                    )
    
    parserGroup.add_option("--xule-round-to-decimals",
                           action="store",
                           default="4",
                           help=_("The number of deimal places numbers should be rounded when displaying. 'inf' indicates not rounding. Otherwise must be an integer"))
    
    parserGroup.add_option("--xule-arg",
                          action="append",
                          dest="xule_arg",
                          help=_("Creates a constant. In the form of 'name=value'"))

    parserGroup.add_option("--xule-args-file",
                          action="store",
                          dest="xule_args_file",
                          help=_("Loads constants from a json file prepared by --xule-output-constants-file"))

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
    
    parserGroup.add_option("--xule-ordered-iterations",
                      action="store_true",
                      dest="xule_ordered_iterations",
                      help=_("Indicates that the iterations should be ordered consistently. This may affect performance"))

    parserGroup.add_option("--xule-rule-stats-file",
                        action="store",
                        dest="xule_rule_stats_file",
                        help=_("Name of file to store rule run statistics. The file will be a JSON file"))
    
    parserGroup.add_option("--xule-rule-stats-log",
                        action="store_true",
                        dest="xule_rule_stats_log",
                        help=_("Output rule run statistics to the log."))

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
                      help=_("File name of file that contains a list of filings to process. The filing list can be a text file or a JSON file. "
                             "If it is a text file, the file names are on separate lines. If the file is a JSON file, the JSON must be an "
                             "array. Each item in the array is a JSON object. The file name is specified with 'file' key. Additional keys can "
                             "be used to specific --xule options to use. These options will override options specified on the command line. "
                             "Example: [{'file' : 'example_1.xml}, {'file' : 'example_2.xml', 'xule_rule_set' "))

    parserGroup.add_option("--xule-max-recurse-depth",
                            action="store",
                            type="int",
                            dest="xule_max_recurse_depth",
                            default=10000,
                            help=_("The recurse depth for python. If there is a 'RecursionError: maximum recursion depth exceeded' "
                                   "error this argument can be used to increase the max recursion depth."))
    parserGroup.add_option("--xule-stack-size",
                          type="int",
                          action="store",
                          dest="xule_stack_size",
                          default="2",
                          help=_("Stack size to use when parsing rules. The default stack size is 8Mb. Use 0 to indicate that the operating "
                                 "system default stack size should be used. Otherwise indicate the stack size in megabytes (i.e. 10 for 10 Mb)."))

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

    parserGroup.add_option("--xule-run-only-pattern",
                        action="store",
                        dest="xule_run_only_pattern",
                        help=_("Regex of rules to run"))

    parserGroup.add_option("--xule-no-cache",
                        action="store_true",
                        dest="xule_no_cache",
                        help=_("Turns off local caching for a rule."))
    
    parserGroup.add_option("--xule-precalc-constants",
                        action="store_true",
                        dest="xule_precalc_constants",
                        help=_("Pre-calculate constants that do not depend on the instance."))
    
    parserGroup.add_option("--xule-output-constants",
                           action="store",
                           dest="xule_output_constants",
                           help=_("Comma separated list of constant names to output."))

    parserGroup.add_option("--xule-output-constants-file",
                           action="store",
                           dest="xule_output_constants_file",
                           help=_("File path to contain reloadable output constants, or write to log if absent."))

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
                            dest="xule_reset_rule_set_map",
                            help=_("Reset the rule set map to the default."))
    
    parserGroup.add_option("--xule-max-excel-files",
                           action="store",
                           type="int",
                           default=5,
                           dest="xule_max_excel_files",
                           help=_("The maximun number of excel files that can open at the same time. The default is 5."))

    if xv is not None: # The XuleValidate module is imported
        parserGroup.add_option("--xule-validate",
                               action="store_true",
                               dest="xule_validate",
                               help=_("Validate ruleset"))

def saveOptions(cntlr, options, **kwargs):
    xu.XuleVars.set(cntlr, 'options', options)
    # Save the options in the xuleparser
    if xp is not None:
        xp.setOptions(options)

def xuleCmdUtilityRun(cntlr, options, **kwargs): 
    # Save the controller and options in the module global variable
    global _cntlr
    _cntlr = cntlr
    saveOptions(cntlr, options, **kwargs)

    cntlr.addToLog("Xule version: %s" % __version__, 'info')

    # check option combinations
    parser = optparse.OptionParser()

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

    if getattr(options, 'xule_filing_list', None) is not None and getattr(options, 'entrypointFile', None) is not None:
        parser.error(_("--xule-filing-list cannot be used with -f"))

    if getattr(options, 'xule_max_excel_files') < 1:
        parser.error(_("--xule-max-excel-files must be greater than 0, found {}".format(getattr(options, 'xule_max_excel_files'))))

    if getattr(options, 'xule_compile_workers') < 0:
        parser.error(_("Workers (--xule-compile-workers) value must be a positive number or 0 (uses number of CPUs)."))
    elif getattr(options, 'xule_compile_workers') != 1:
        if getattr(sys, "frozen", False):
            parser.error(_("Multiple workers (--xule-compile-workers) requires running Arelle from source."))
        try:
            from arelle.PluginUtils import PluginProcessPoolExecutor
        except ModuleNotFoundError:
            parser.error(_("Multiprocessing plugin support was introduced in Arelle 2.17.3. Update to a newer version of Arelle to use multiple workers (--xule-compile-workers)."))

    round_to_decimals = getattr(options, 'xule_round_to_decimals', None)
    if round_to_decimals is not None:
        if round_to_decimals.lower() != 'inf':
            try:
                int(round_to_decimals)
            except ValueError:
                parser.error(_(f"--xule-round-to-decimals must be 'inf' or and integer, found {round_to_decimals}"))

    # compile rules
    if getattr(options, "xule_compile", None):
        compile_destination = getattr(options, "xule_rule_set", "xuleRules") 
        xuleCompile(options.xule_compile, compile_destination, getattr(options, "xule_compile_type"), getattr(options, "xule_max_recurse_depth"), getattr(options, "xule_compile_workers"))
        #xp.parseRules(options.xule_compile.split("|"), compile_destination, getattr(options, "xule_compile_type"))
    
    # add packages
    if getattr(options, "xule_add_packages", None):
        try:
            rule_set = xr.XuleRuleSet(cntlr)
            rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
            packages = options.xule_add_packages.split('|')
            rule_set.manage_packages(packages, 'add')
        except xr.XuleRuleCompatibilityError as err:
            # output the message to the log and NOT raise an exception
            cntlr.addToLog(err.args[0] if len(err.args)>0 else 'Unknown rule compatibility error', 'xule', level=logging.ERROR)
    # remove packages
    if getattr(options, "xule_remove_packages", None):
        try:
            rule_set = xr.XuleRuleSet(cntlr)
            rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
            packages = options.xule_remove_packages.split('|')
            rule_set.manage_packages(packages, 'del')
        except xr.XuleRuleCompatibilityError as err:
            # output the message to the log and NOT raise an exception
            cntlr.addToLog(err.args[0] if len(err.args)>0 else 'Unknown rule compatibility error', 'xule', level=logging.ERROR)
    
    # show packages
    if getattr(options, "xule_show_packages", False):
        try:
            rule_set = xr.XuleRuleSet(cntlr)
            rule_set.open(getattr(options, "xule_rule_set"), open_packages=False, open_files=False)
            print("Packages in rule set:")
            for package_info in rule_set.get_packages_info():
                print('\t' + package_info.get('name') + ' (' + os.path.basename(package_info.get('URL')) + ')')
        except xr.XuleRuleCompatibilityError as err:
            # output the message to the log and NOT raise an exception
            cntlr.addToLog(err.args[0] if len(err.args)>0 else 'Unknown rule compatibility error', 'xule', level=logging.ERROR)
        
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
            rule_set = xr.XuleRuleSet(cntlr)
            rule_set.open(options.xule_rule_set, False)
        except xr.XuleRuleSetError:
            raise
        except xr.XuleRuleCompatibilityError as err:
            # output the message to the log and NOT raise an exception
            cntlr.addToLog(err.args[0] if len(err.args)>0 else 'Unknown rule compatibility error', 'xule', level=logging.ERROR)
        else:
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

            
            # Category labels for the log.
            _CONST_CATEGORY_LABELS = {
                'c':    'c    (no dependencies)',
                'rtc':  'rtc  (rules taxonomy only)',
                'frc':  'frc  (filing instance only)',
                'rfrc': 'rfrc (filing instance + rules taxonomy)',
            }

            for g in global_context.all_constants:
                global_context.message_queue.logging(
                    "Constants: %s - %d" % (g, len(global_context.all_constants[g])))

            for g in global_context.all_rules:
                global_context.message_queue.logging(
                    "Rules: %s - %d" % (g, len(global_context.all_rules[g])))

            # In debug mode, emit a detailed breakdown: each category's constants
            # sorted by rule_count descending so the most-used constants are visible
            # at a glance.  rule_count is stored in the compiled catalog by
            # XuleRuleSetBuilder.post_parse(); constants compiled before this change
            # will show 0.
            if getattr(options, 'xule_debug', False):
                global_context.message_queue.logging(
                    "--- Constants by category (sorted by rule usage) ---")
                for g in ('c', 'rtc', 'frc', 'rfrc'):
                    if g not in global_context.all_constants:
                        continue
                    label = _CONST_CATEGORY_LABELS.get(g, g)
                    const_names = global_context.all_constants[g]
                    # Sort by rule_count descending; constants without a count
                    # (compiled before this feature) fall to the bottom.
                    sorted_consts = sorted(
                        const_names,
                        key=lambda n: rule_set.catalog['constants'][n].get('rule_count', 0),
                        reverse=True,
                    )
                    global_context.message_queue.logging(
                        "  [%s] — %d constants" % (label, len(sorted_consts)))
                    for const_name in sorted_consts:
                        count = rule_set.catalog['constants'][const_name].get('rule_count', 0)
                        global_context.message_queue.logging(
                            "    %-50s  %d rules" % (const_name, count))
                global_context.message_queue.logging(
                    "--- End constants breakdown ---")

            # evaluate valid constants (no dependency, rules taxonomy)
            global_context.message_queue.logging("Calculating and Storing Constants")
            xm.run_constant_group(global_context, 'c', 'rtc')

                                    
            # Add precalculated information to the cntlr to pass to XuleServer
            setattr(cntlr, "xule_options", options)
            setattr(cntlr, "rule_set", global_context.rule_set)
            setattr(cntlr, "constant_list", global_context._constants)
            setattr(cntlr, "all_constants", global_context.all_constants)
            setattr(cntlr, "all_rules", global_context.all_rules)

            # Pre-load the sample filing for this rule set's taxonomy year to warm
            # the parent process's taxonomy cache.  Forked request workers inherit
            # the parsed DTS objects via copy-on-write, avoiding 10-15 second
            # taxonomy parse time on every cold request.
            _warm_up_taxonomy_cache(cntlr, options.xule_rule_set,
                                    global_context.message_queue)

            global_context.message_queue.logging("Finished Server Initialization")
            
            # stop message_queue
            global_context.message_queue.stop()
            
            if getattr(options, "xule_multi", False):
                t.join()
    else:
        if getattr(options, 'xule_filing_list', None) is not None:
            # process filing list
            if getattr(options, "xule_filing_list", None):
                try:
                    with open(options.xule_filing_list, 'r') as filing_list_file:
                        # Try json
                        try:
                            filing_list = json.load(filing_list_file, object_pairs_hook=collections.OrderedDict)
                        except:
                            # Try a flat list of file names
                            try:
                                # reset the file pointer
                                filing_list_file.seek(0)
                                filing_list = [{"file": file_name} for file_name in filing_list_file]
                            except:
                                cntlr.addToLog(_("Unable to open Filing listing file '%s'." % options.xule_filing_list), 'xule')
                                raise
                except FileNotFoundError:
                    cntlr.addToLog(_("Filing listing file '%s' is not found" % options.xule_filing_list), 'xule')
                    raise

                if isinstance(filing_list, list):
                    for file_info in filing_list:
                        if isinstance(file_info, dict):
                            input_file_name = file_info.get('file')
                            if input_file_name is not None:
                                input_file_name = input_file_name.strip()
                                print("Processing filing", input_file_name)
                                filing_filesource = FileSource.openFileSource(input_file_name, cntlr)
                                # TODO - #29 
                                #modelManager = ModelManager.initialize(cntlr)
                                #modelManager = cntlr.modelManager
                                modelManager = xu.get_model_manager_for_import(cntlr)
                                modelXbrl = modelManager.load(filing_filesource)
                                # Update options
                                new_options = copy.copy(options)
                                delattr(new_options, 'xule_filing_list')
                                for k, v in file_info.items():
                                    if k != 'file' and k.strip().lower().startswith('xule'): # Only change xule options
                                        setattr(new_options, k.strip().lower(), v)
                                if getattr(new_options, 'xule_run', None) or getattr(new_options, 'xule_output_constants', None) is not None:
                                    xuleCmdXbrlLoaded(cntlr, new_options, modelXbrl)
                                elif getattr(new_options, 'validate'):
                                    for xule_validator in _xule_validators:
                                        runXule(_cntlr, new_options, modelXbrl, xule_validator['map_name'], True)
                                modelXbrl.close()
        else:
            if options.entrypointFile is None:
                # try running the xule processor - This is when rules are run without an instance document
                xuleCmdXbrlLoaded(cntlr, options, None)

    # Only register xule as a validator if the xule plugin was directly added in the --plugin options.
    if isXuleDirect(cntlr):
        xuleRegisterValidators('Xule', _xule_rule_set_map_name)
    
def xuleCmdXbrlLoaded(cntlr, options, modelXbrl, *args, **kwargs):
    if getattr(options, "xule_run", None) or getattr(options, "xule_output_constants", None) is not None:
        runXule(cntlr, options, modelXbrl)

def xuleCompile(xule_file_names, ruleset_file_name, compile_type, max_recurse_depth=None, xule_compile_workers=1):
    xp.parseRules(xule_file_names.split("|"), ruleset_file_name, compile_type, max_recurse_depth, xule_compile_workers)

def runXule(cntlr, options, modelXbrl, rule_set_map=_xule_rule_set_map_name, is_validator=False):
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
                        raise xr.XuleRuleSetError(
                            "Cannot determine which rule set to use for the filing. Check the rule set map at '{}'.".format(
                                xu.get_rule_set_map_file_name(cntlr, rule_set_map)
                            )
                        )
                rule_set = xr.XuleRuleSet(cntlr)              
                rule_set.open(rule_set_location, open_packages=not getattr(options, 'xule_bypass_packages', False))
        except xr.XuleRuleCompatibilityError as err:
            modelXbrl.error(
                'xule:RulesetCompatabilityError',
                'Rule compatibility error: {}'.format(err),
            )
        except xr.XuleRuleSetError as rse:
            modelXbrl.error(
                'xule:RulesetError',
                'An issue occurred with the xule ruleset: {}'.format(rse)
            )
        else:
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
                            raise xr.XuleRuleSetError(f'Need instance to process rule {rule["full_name"]}')
                        
                global _saved_taxonomies        
                used_taxonomies = process_xule(rule_set,
                                            modelXbrl,
                                            cntlr,
                                            options,
                                            _saved_taxonomies,
                                            is_validator
                                            )
                # Save one loaded taxonomy
                new_taxonomy_keys = used_taxonomies.keys() - _saved_taxonomies.keys()
                if len(new_taxonomy_keys) > 0:
                    for tax_key in list(new_taxonomy_keys)[:2]: # This take at most 2 taxonomies.
                        tax_key = next(iter(new_taxonomy_keys)) # randomly get one key
                        _saved_taxonomies[tax_key] = used_taxonomies[tax_key]

def callXuleProcessor(cntlr, modelXbrl, rule_set_location, options):
    '''Call xule from other plugins

    This is an entry point for other plugins to call xule.
    '''
    try:
        rule_set = xr.XuleRuleSet(cntlr)              
        rule_set.open(rule_set_location)

        global _saved_taxonomies        
        used_taxonomies = process_xule(rule_set,
                                        modelXbrl,
                                        cntlr,
                                        options,
                                        _saved_taxonomies,
                                        is_validator=True # This will run xule if there is not a --xule-run option
                                        )
        # Save one loaded taxonomy
        new_taxonomy_keys = used_taxonomies.keys() - _saved_taxonomies.keys()
        if len(new_taxonomy_keys) > 0:
            for tax_key in list(new_taxonomy_keys)[:2]: # This take at most 2 taxonomies.
                tax_key = next(iter(new_taxonomy_keys)) # randomly get one key
                _saved_taxonomies[tax_key] = used_taxonomies[tax_key]
    except xr.XuleRuleCompatibilityError as err:
        # output the message to the log and NOT raise an exception
        cntlr.addToLog(err.args[0] if len(err.args)>0 else 'Unknown rule compatibility error', 'xule', level=logging.ERROR)

def xuleValidate(val, extra_options=None):
    global _cntlr
    global _xule_validators

    # If the controller is not there, pull it from the model. this happens when running as a web service in multi processing mode.
    _cntlr = _cntlr or val.modelXbrl.modelManager.cntlr
    options = xu.XuleVars.get(_cntlr, 'options')
    if options is None:
        options = EmptyOptions()
    if extra_options:
        for n, v in extra_options.items():
            setattr(options, n, v)
            if n == "block_Validate.Finally" and v:
                setattr(val, "block_Validate.Finally", True)

    for xule_validator in _xule_validators:
        if getattr(val, "block_Validate.Finally", False):
            # running under extraOptions control
            if extra_options is None: # Validate.Finally which is blocked
                return
            if extra_options.get("block_runXule", False): # runXule is blocked
                return
            elif len(val.modelXbrl.facts) > 0 and len(val.modelXbrl.qnameConcepts) > 0:
                runXule(_cntlr, options, val.modelXbrl, xule_validator['map_name'], is_validator=True)
        elif 'validate_flag' in xule_validator:
            # This is run in the GUI. The 'validate_flag' is only in the xule_validator when invoked from the GUI
            if xule_validator['validate_flag'].get():
                # Only run if the validate_flag variable is ture (checked off in the validate menu)
                if  len(val.modelXbrl.facts) > 0 and len(val.modelXbrl.qnameConcepts) > 0:
                    # Only run if there is something in the model. Sometimes arelle creates an empty model and runs the validation.
                    # This happens in the case of the transforms/tester plugin. Arelle creates an empty model to run a formula
                    # valiation. In this case, there really wasn't a model to validate.
                    val.modelXbrl.modelManager.showStatus(_("Starting {} validation".format(xule_validator['name'])))
                    val.modelXbrl.info("DQC",_("Starting {} validation".format(xule_validator['name'])))
                    runXule(_cntlr, options, val.modelXbrl, xule_validator['map_name'], True)
                    val.modelXbrl.info(xule_validator['name'],_("Finished {} validation".format(xule_validator['name'])))
                    val.modelXbrl.modelManager.showStatus(_("Finished {} validation".format(xule_validator['name']))) 
        else:
            # This is run on the command line or web server
            # Only run on validate if the --xule-run option was not supplied. If --xule-run is supplied, it has already been run
            if not getattr(options, "xule_run", False) and len(val.modelXbrl.facts) > 0 and len(val.modelXbrl.qnameConcepts) > 0:
                runXule(_cntlr, options, val.modelXbrl, xule_validator['map_name'], is_validator=True)

    if getattr(_cntlr, 'hasWebServer', False) and not getattr(_cntlr, 'hasGui', False) and not getattr(options, "block_deregister", False):
        # When arelle is running as a webserver, it will register the xule_validators on each request to the web server. 
        # The _xule_validators is emptied. On the next request, the xule_validators for that request will be re-register.
        _xule_validators = []

def xuleTestXbrlLoaded(modelTestcase, modelXbrl, testVariation):
    global _cntlr
    global _test_start
    global _test_variation_name
    
    if getattr(xu.XuleVars.get(_cntlr,'options'), 'xule_test_debug', False):
        _test_start = datetime.datetime.today()
        _test_variation_name = testVariation.id
        print('{}: Testcase variation {} started'.format(_test_start.isoformat(sep=' '), testVariation.id))

def xuleTestValidated(modelTestcase, modelXbrl):
    global _cntlr
    global _test_start
    global _test_variation_name
    
    if getattr(xu.XuleVars.get(_cntlr, 'options'), 'xule_test_debug', False):
        if _test_start is not None:            
            test_end = datetime.datetime.today()
            print("{}: Test variation {} finished. in {} ".format(test_end.isoformat(sep=' '), _test_variation_name, (test_end - _test_start)))

def updateValidatorRulesetMap(cntlr, new_map, map_name):
    xu.update_rule_set_map(cntlr, new_map, map_name)
    
def replaceValidatorRulesetMap(cntlr, new_map, map_name):
    xu.update_rule_set_map(cntlr, new_map, map_name, overwrite=True)    

def rulesetMapData(cntlr, map_name):
    '''Get the rule set map data.

    Gets the namespace and rule set file name from the map and then opens each ruleset to get the rule set version number.'''

    map_data = [('Namespace', 'Rule Set File', 'Version')]

    if map_name is not None:
        map = xu.get_rule_set_map(cntlr, map_name)
        for k, v in map.items():
            rule_set = xr.XuleRuleSet(cntlr)
            try:
                rule_set.open(v, open_packages=False, open_files=False)
                version = rule_set.catalog.get('xule_compiled_version') or 'not versioned'
            except xr.XuleRuleCompatibilityError as err:
                version = err.args[0] if len(err.args)>0 else 'incompatible rule set version'
            except FileNotFoundError:
                version = 'Rule set not found'
            map_data.append((k, v, version))
    return map_data

def displayValidatorRulesetMap(cntlr, validator_name, map_name):

    if map_name is not None:
        map_file_name = xu.get_rule_set_map_file_name(cntlr, map_name)
        map_data = rulesetMapData(cntlr, map_name)

        if tab is None:
            display_map = '\n'.join(['{}\t{}\t{}'.format(*x) for x in map_data])
        else:
            display_map = tab.tabulate(map_data, headers='firstrow')

        cntlr.addToLog("{} Rule Set map {} - {}\n{}".format(validator_name,  map_name, map_file_name, display_map ), validator_name)
    
__pluginInfo__ = {
    'name': 'XBRL rule processor (xule)',
    'version': 'Check version using Tools->Xule->Version on the GUI or --xule-version on the command line',
    'description': 'This plug-in provides a DQC processor.',
    'license': 'Apache-2',
    'author': 'XBRL US Inc.',
    'copyright': '(c) 2017-2018',
    'import': 'semanticHash',
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
    'Xule.ValidatorVersion': validatorVersion,
    'Xule.RegisterValidator': xuleRegisterValidators,
    'Xule.RulesetMap.Update': updateValidatorRulesetMap,
    'Xule.RulesetMap.Replace': replaceValidatorRulesetMap,
    'Xule.RulesetMap.Display': displayValidatorRulesetMap,
    'Xule.CntrlCmdLine.Utility.Run.Init': saveOptions,
    'Xule.compile': xuleCompile,
    'Xule.callXuleProcessor': callXuleProcessor,
    'CntlrWebMain.StartWebServer': xuleCntlrWebMainStartWebServer,
    'CntlrWebMain.RunOptions': xuleCntlrWebMainRunOptions,
    }
