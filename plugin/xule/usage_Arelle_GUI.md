# Using DQC Rules with Arelle - from the GUI 
[return to README](README.md#using)

## Initial setup for the DQC Rules xule plugin

* Open the Arelle program.
* Choose the "Help" menu and select "Manage plug-ins" to verify the "DQC Rules Validator" is listed.
* ***If DQC Rules Validator is not listed:***
    * Use the "Select" button to bring up teh "Select Plug-in Module" dialog. 
    * Select the **DQC.py** file (under "Validate"). Next to the file, the name will appear as "DQC Rules Validator". Click on "OK". 
    * Also select the **EdgarRenderer** file and click "OK".
    * The "Select Plug-in Module" will close. On the "Plug-in Manager" dialog click on "Close".
	* When the dialogue box appears requesting a program restart, choose "Yes".
* Choose the "Tools" menu and "Validation" and confirm there is a check mark for "DQC Rules". If not, select this item from the menu.

## Checking version and rule set map

* Arelle caches the default rulesetMap.json file when the program restarts after the DQC plugin is installed. There are several functions available to manage this file, as noted below.
* Choose the "Tools" menu and mouse-over the DQC option to see four options:
    * "Version ..." displays the current xule version installed to Arelle's plugin/xule subfolder (recommended as 3.0.22730 or higher).
    * "Display DQC rule set map ..." shows the current rule sets targeted. By default, the GitHub URLs should correspond to the **current release version** (ie. `https://github.com/DataQualityCommittee/dqc_us_rules/dqc_us_rules/blob/` **v8** `/dqc_us_rules/`... would indicate Version 8 ruleset.zip files).
    * "Check DQC rule set map ..." verifies the cached rulesetMap.json file references the most-current approved ruleset.zip files.
    * "Update DQC rule set map ..." provides an interface for either appending or overwriting the cached rulesetMap.json file.

## Checking a filing with DQC Rules

* Choose the "File" menu and either "Open file" or "Open Web" to select an XBRL .zip file from local computer or SEC EDGAR system.
* Select the .xml file (instance document) from the view of the contents of the .zip.
* After the instance has rendered in Arelle, choose the "Tools" >> "Validation" menu and select "Validate".
* Monitor the "messages" window at the bottom of Arelle, to see _[DQC] Starting DQC validation - xxx.xml_ appears.
* After the message _[DQC] Finished DQC validation - xxx.xml_ appears, review any error messages. The results can be saved by selecting the messages window (right-click on a Windows PC) and choosing "Save to file".

See also [from a command prompt](usage_command_prompt.md) for advanced configuration options. 

### [return to README](README.md#using)
 
© Copyright 2015 - 2021 XBRL US, Inc. All rights reserved.   
See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.
