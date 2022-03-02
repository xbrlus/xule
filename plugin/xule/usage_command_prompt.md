# Using DQC Rules with Arelle - from a command prompt 
[return to README](README.md#using) | [managing rulesets from the command prompt](usage_rulesets.md)

### Confirm the DQC Arelle plugin is installed by running `arelleCmdLine --plugin validate/DQC`.

You should see an activation message for the plugin:
`
[info] Activation of plug-in DQC Rules Validator successful, version Check version using Tools->DQC->Version on the GUI or --dqc-version on the command line. - validate/DQC
`  

The minimum parameters that need to be passed are the following:
* **`--plugins validate/DQC`** : Loads the DQC plugin. When running with an SEC filing, the SEC transformations are also needed for Inline XBRL filings. Both plugins can be specified using **--plugins "validate/DQC|transforms/SEC"**. The pipe character `|` separates the plugins. Specifying the SEC transforms plugins will have no affect on traditional XBRL filings, so it can be included for all SEC filings.
* **`-f`** : The location of the instance file to be evaluated. This will take a zip file, XML instance or inline XBRL file.
* **`-v`**: Instructs the processor to validate the filing including running the DQC rules.

A typical command line syntax for Arelle is as follows (including optional parameters defined below:

`
arelleCmdLine --plugins "validate/DQC|transforms/SEC" -f {instance file or zip file} -v --noCertificateCheck --logFile {log file name}
`

**Example:**  
`
arelleCmdLine --plugins "validate/DQC|transforms/SEC" -f https://www.sec.gov/Archives/edgar/data/xxx-20170930.xml  -v --noCertificateCheck --logFile DQC-output.xml
`   

In addition the following optional parameters can be passed:

* **`--logFile`** : Specifies where the output of running the rules should be sent. To get an XML file the file needs to end with .xml. To get a json file it needs to end with .json. If a log file is not specified, output will be displayed in the command window.
* **`--noCertificateCheck`** : This is used to ensure that files from the internet are not rejected if there is no SSL certificate on the machine running the DQC plugin.
* **`--xule-bypass-packages`** : This option will ignore packages included in the ruleset. (See *Managing the Ruleset File* below)  
* **`--packages`** : This option will accept additional taxonomy packages
* **`--xule-rule-set`** : The location of the compiled ruleset to use. 

To get additional options use the option `--help` (eg. `arelleCmdLine --plugins validate/DQC --help`)

The DQC plugin options will be displayed at the bottom of the list under the title "DQC validation plugin". All DQC specific options start with `--DQC` or `--xule`.

[return to README](README.md#using) | [managing rulesets from the command prompt](usage_rulesets.md)
 
© Copyright 2015 - 2022 XBRL US, Inc. All rights reserved.   
See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.
