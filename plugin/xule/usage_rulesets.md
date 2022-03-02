# DQC Rules with Arelle - Managing Rulesets 
[return to command prompt use](usage_command_prompt.md)

### Ruleset Detection

When the DQC plugin is run without specifying the the ruleset (with the `--xule-rule-set` option), the plugin will attempt to match the correct ruleset based on the facts in the instance document. The plugin will assess the namespaces of the primary items of the facts in the instance and check the ruleset map to determine the correct ruleset. 

An initial the ruleset map is included in the "xule" plugin folder. It is named rulesetMap.json. The first time the plugin autodetects a ruleset, the ruleset map in the plugin folder is copied to the application data folder. This is the version that is used to determine which ruleset to use. 

It is recommended not to change the ruleset map in the plugin folder. The copy in the application data folder may be edited to change the ruleset map. The ruleset map is a simple JSON file mapping namespaces to a ruleset.

**Example Ruleset Map**
```
{
	"http://xbrl.ifrs.org/taxonomy/2017-03-09/ifrs-full" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc-ifrs-2017-V5-ruleset.zip?raw=true",
	"http://xbrl.ifrs.org/taxonomy/2016-03-31/ifrs-full" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc-ifrs-2016-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2017-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2017-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2016-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2016-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2015-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2015-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2014-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2014-V5-ruleset.zip?raw=true",	
	"http://fasb.org/us-gaap/2013-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2013-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2012-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2012-V5-ruleset.zip?raw=true",
	"http://fasb.org/us-gaap/2011-01-31" : "https://github.com/DataQualityCommittee/dqc_us_rules/blob/next_q1_17v5/dqc_us_rules/dqc-us-2011-V5-ruleset.zip?raw=true"
}
```
The DQC plugin reads the ruleset map in order from the top. If the namespace in the ruleset map matches a namespace used on a primary item of a fact in the instance, then the corresponding ruleset is used.

The initial copy of the ruleset map included with the plugin maps to rulesets on the DQC GitHub repository. The ruleset map can be edited to refer to local copies of the rulesets.

### Updating the ruleset map for future releases of DQC rules

When initially installed, the ruleset map of the DQC plugin corresponds to ruleset .zip files for the then currently-approved version of DQC rules.

With each new release, the ruleset map will need to be updated (even if the DQC plugin is reinstalled). This is because the working ruleset map is in the local machine's application data folder, which does not changed when re-installing the plugin.

The simplest way to update the ruleset map from the command line is to use the `--dqc-replace-rule-set-map` option followed by the URL for the new ruleset map. The URL for the new ruleset map will be indicated in the release notes

Future releases may include changes to the DQC rules and/or the DQC plugin. If the DQC plugin is **not** changed, it does not need to be re-installed, however, the ruleset map must be updated to for the plugin to use the new rulesets. If the release includes changes to the plugin, the plugin will need to be re-installed and the ruleset map updated. Instructions will be included in the release notes.
 

#### Additional options for updating the ruleset map 

The ruleset map can be reset with the copy in the plugin folder by using the `--dqc-reset-rule-set-map` option. This will overwrite any changes made to the copy of the ruleset map file in the application data folder.

**Example**

`arelleCmdLine --plugins xule --dqc-reset-rule-set-map`

Alternatively, the ruleset map can be updated from a file or URL by using `--dqc-replace-rule-set-map` followed by the file name or URL. Like the reset option, this will overwrite the ruleset map file in the application data folder.

**Example**

`arelleCmdLine --plugins xule --dqc-replace-rule-set-map myNewRulesetMap.json`

The ruleset map file can be merged by using `--dqc-update-rule-set-map` followed by the file name or URL to merge with the ruleset map file in the application data folder. Merging provides a basic means of updating the current ruleset map (the ruleset map in the application data folder). 

**Example**

`arelleCmdLine --plugins xule --dqc-update-rule-set-map myRulesetMapChanges.json`

When merging, any namespaces in the new ruleset map that are in the current ruleset map will update the current ruleset map with the location of the ruleset for that namespace. New namespaces will be added to the end of the current ruleset map. If more specific edits are needed, the current ruleset map will need be edited manually.
### Managing the Ruleset File

The ruleset file includes packages with local versions of files used by the DQC plugin. Using these resource files locally allows the plugin to be run without Internet access. These resource files are included by default in the ruleset as XBRL taxonomy packages. To ignore the packages included in the ruleset, use the option `--xule-bypass-packages`. Using the plugin this way will generally take more time to run, as the plugin will use resources referenced in the dqc_us_rules repository as raw.githubusercontent.com. 

Packages can be added or removed from a ruleset. This is managed by using the following three options:

* `--xule-show-packages`
* `--xule-add-packages`
* `--xule-remove-packages`

All these options also require the --xule-rule-set option to be used.

**Example**
`arelleCmdLine --plugins xule --xule-show-packages --xule-rule-set dqc-us-2017-V5-ruleset.zip`

Will return the following:
`
Packages in rule set:
	dqc_15_concepts.csv and dqc_0011.csv (resources.zip)
`

**Usages and switches**
* **`--xule-add-packages`** followed by a `|` separated list of package files will add the packages to the rule set. If a package is already in the rule set it will overwrite it. It will attempt to activate the package in arelle to test that the package is valid.

* **`--xule-remove-packages`** followed by a `|` separated list of package file names (this is the zip file name). If a package is not in the rule set, it will report it, but not fail. Any other packages in the list will be removed.

* **`--xule-add--packages`** and **`--xule-remove-packages`** options modify the ruleset file and can only be used on a locally stored ruleset.

The format of the package zip file is based on the XBRL packages specification. It has a single directory in the zip file. Usually, the name of this top level directory is the same as the name of the zip file, but that is not required. Inside the top level directory, there is a directory named "META-INF". Inside the META-INF directory there are two files 'catalog.xml' and "taxonomyPackages.xml".

The **catalog.xml** file contains the remapping. The `<rewriteURI>` element in this file defines the map. It can map to a directory or a file. Several `<rewriteURI>` elements can used to define multiple mappings. The one in the example is:

`
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
	<rewriteURI rewritePrefix="../" uriStartString="https://raw.githubusercontent.com/DataQualityCommittee/dqc_us_rules/master/dqc_us_rules/resources/DQC_US_0015/"/>
</catalog>
`

Note that `rewritePrefix` is mapping to the parent directory that the catalog.xml file is in.

Normally taxonomy packages are used to archive (zip) taxonomies and identity taxonomy entry points. Here the taxonomy package mechanism is used to remap csv files, which is out of scope for the taxonomy package spec. However, it does work and using taxonomy package handling built into Arelle. The XBRL spec working group is considering using taxonomy packages for other file types.

### [return to README](README.md#using)

© Copyright 2015 - 2022 XBRL US, Inc. All rights reserved.   
See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.
