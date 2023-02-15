# XULE Editor 
*_A language syntax highlighter and code completion extension for editing [Xule](https://xbrl.us/xule) with Visual Studio Code._*
<br /><br /><div style="text-align:center; vertical-align:middle"><img width="600" src="https://github.com/xbrlus/xule-editor/raw/master/src/xule-editor.gif" /></div>

### Workspace, Settings and Taxonomy Files
The settings .zip file below includes a Visual Studio Code .code-workspace and settings files corresponding to the reference implementation code (```source``` folder) included in every [Data Quality Committee Rules release (DQC)](https://github.com/DataQualityCommittee/dqc_us_rules/releases).  

The files in the .zip linked below include: 
  1. a **DQC.code-workspace** file defining folders corresponding to the reference implementation 
  1. **settings.json files** that define imports and namespaces required by the Xule Editor in each workspace folder, and 
  1. US GAAP (2014 - 2023) and IFRS (2018 - 2022) **Taxonomies in .json format** called by the settings.json files. 

Together, these resources enable highlighting and code completion in the Xule Editor. 

### Getting Started (<a href="https://youtu.be/LQtbUBjx0qQ" target="_blank">Watch video</a>)
  1. Install the latest [Xule Editor](https://marketplace.visualstudio.com/items?itemName=XBRLUS.xule).
  1. Download and **extract all folders and files from the [dqc-xule-settings.zip](https://github.com/xbrlus/xule-editor/raw/master/dqc-xule-settings.zip)** archive into the ```dqc_us_rules``` subdirectory of the release, so that the **```taxonomy``` folder is at the same level as the existing ```source``` folder**.
<br /><div style="text-align:center"><img src="https://github.com/xbrlus/xule-editor/raw/master/src/taxonomy-folder.png" /></div><br /><br />
**Proceed with caution** - the extract process will create **_or replace_** existing workspace, settings and taxonomy files in the DQC reference implementation ```source``` folder structure. If you are not sure how to proceed safely, consider manually copying from the files in the .zip into the appropriate settings file.  **XBRL US is not responsible for overwritten settings.**

### Confirming the Xule Editor extension
Once the DQC.code-workspace and .json files are extracted, **open the DQC.code-workspace file from Visual Studio Code's "Open Workspace..." prompt** under the program's File menu. Browse the folders by year (US GAAP above IFRS, separated by a common ```lib``` folder), and open a .xule file for one of the DQC Rules.  If the Visual Studio Code view includes underlined text in the body of the editor, warnings or errors listed for the file (like the image at left below), try the following steps:

  * Check the location of the settings.json file(s) and the contents of the file itself against the corresponding file(s) in the .zip, to be sure the xule.autoImports and xule.namespaces.definitions are correct.
  * Check the location of the ```taxonomy``` folder and its contents, to be sure it matches the contents of the .zip archive.
  * MacOS users might need to remove the '../../lib/' string from the *_functions.xule_* and *_version.xule_* entries in the settings.json files.
  * Check that the settings.json file is being read properly by the Xule Editor extension - open the settings for the extension, then browse to the corresponding folder(s) using the dropdown, to confirm that the Auto Imports and Namespaces: Definitions are listed (like the image at right below).  If not, try uninstalling and reinstalling the Xule Editor extension.
 
<div style="text-align:center"><img align=center width="300" src="https://github.com/xbrlus/xule-editor/raw/master/src/problem-xule-editor.png" /> &nbsp; <img align=center width="300" src="https://github.com/xbrlus/xule-editor/raw/master/src/xule-folder-settings.png" /> 

<a href="https://github.com/xbrlus/xule-editor/raw/master/src/problem-xule-editor.png">full size - problem</a> &nbsp; <a href="https://github.com/xbrlus/xule-editor/raw/master/src/xule-folder-settings.png">full size - settings</a></div>