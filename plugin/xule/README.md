# Deployment and Usage

#### On this page: [Deploying the DQC Arelle Plugin](#deploying) || [Usage and Results - DQC Rules with Arelle](#using) || [License and Patent](#licensing)

## <a name="deploying"></a>Deploying the DQC Arelle Plugin
### Windows/Mac/Linux Application Install
1. Download the latest version of [Arelle](http://arelle.org/pub/) to your environment and install. 
2. Download the latest release of the [DQC plugin](https://github.com/DataQualityCommittee/dqc_us_rules/releases) 
3. Extract the DQC archive and copy the ```plugin/xule``` folder and files to the plugin directory of Arelle in your environment (if prompted, overwrite files in the existing xule subfolder). In a Windows environment, this would be located on a path similar to C:\Program Files\Arelle\plugin; on a Mac, the location would be at /Applications/Arelle.app/Contents/MacOS/plugin. 
**Also copy the DQC.py file** (located in the ```plugin/validate``` folder of the DQC release) to the ```plugin/validate``` directory of Arelle in your environoment. In a Windows environment, this would be located on a path similar to C:\Program Files\Arelle\plugin\validate; on a Mac, the location would be at /Applications/Arelle.app/Contents/MacOS/plugin/validate.
4. Copy the "aniso8601" folder to the root of the Arelle install in your environment. In a Windows environment, this would be located on a path similar to C:\Program FIles\Arelle; on a Mac, the location would be at /Applications/Arelle.app/Contents/MacOS/.

### Source Install
* Download the latest [Arelle source code](https://github.com/Arelle/Arelle/) from GitHub to your environment and run setup.py to install. 
* Install the following modules to python:
  * isodate
  * aniso8601
  * numpy
* Follow steps 2 and 3 from the **Windows/Mac/Linux Application Install** section above to add the DQC plugin to the source copy of Arelle. The Arelle location is where the Arelle source code from GitHub was extracted on the local machine or server. The Arelle plugin foler is at ```arelle/plugin``` in the source distribution. For *step 2*, add the xule folder and files to the ```arelle/plugin``` folder. For *step 3*, add the **DQC.py** file from the DQC release's ```plugin/validate``` subfolder to the ```arelle/plugin/validate``` folder.

The DQC plugin requires **Python 3.5** or later and is **not compatible with earlier versions of Python**.

### Updating the ruleset map file
After the installation, the ruleset map file needs to be updated for the latest version. The latest ruleset map is "plugin/xule/rulesetMap.json" in the GitHub distribution. Use the following command to update the ruleset map:

`
arelleCmdLine --plugin validate/DQC --dqc-replace-rule-set-map *{location of rulesetMap.json file from the GitHub distribution}*
`

## <a name="using"></a>Usage and Results - DQC Rules with Arelle

*  [from the graphic user interface (GUI)](usage_Arelle_GUI.md) - **version 5.2.0 or later**
*  [from a command prompt](usage_command_prompt.md)
	*  [managing rulesets](usage_rulesets.md)

### Results
The DQC Arelle plugin produces validation messages using standard Arelle output. In the GUI, results will appear in the bottom window as the filing is processed and can be exported to text for review. From a command prompt, the option `--logFile` specifies the output location of the file. The format of the output is specified by the extension of the file. For example ```--logFile DQC-output.```**xml** will create an xml formatted file whereas ```--logFile DQC-output.```**json** will create a json formatted file. **Output to a file is appended** to an existing file - the existing file is not overwritten. An example of an XML output is shown below:

```
<entry code="DQC.US.0001.75" level="error">
<message severity="error" cid="4508053008" filing_url="https://www.sec.gov/Archives/edgar/data/1606698/000109690617000244/0001096906-17-000244-xbrl.zip/alpine-20161231.xml">[DQC.US.0001.75] The concept SharesIssued with a value of 21,474,481 is dimensionally qualified with the StatementEquityComponentsAxis and the base taxonomy member CommonClassAMember. Only extension members and the elements defined as children of this axis in the US GAAP taxonomy should be used with the axis StatementEquityComponentsAxis.
The properties of the fact for SharesIssued are:
Period: 2016-12-31
Dimensions: us-gaap:StatementEquityComponentsAxis=us-gaap:CommonClassAMember
Unit: shares

Rule Element Id:75
Rule Version: 2.0 'https://www.sec.gov/Archives/edgar/data/1606698/000109690617000244/0001096906-17-000244-xbrl.zip/alpine-20161231.xml’, 320</message>
<ref href="('https://www.sec.gov/Archives/edgar/data/1606698/000109690617000244/0001096906-17-000244-xbrl.zip/alpine-20161231.xml#element(/1/317)', 320)"/></entry>
```

In the XML example above, **the message portion starts with *[DQC.US.0001.75]* and ends with the instance filename and line number at the end of the message**. 

The message portion of the log file output can be controlled by using the `--logFormat` option. The default format is specified as the following:

`"[%(messageCode)s] %(message)s - %(file)s"`

To *exclude the rule number, filename and line number from the message*, use the command prompt `--logFormat  "%(message)s"`.

## <a name="licensing"></a>License and Patent

See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.

Copyright 2015 - 2022 XBRL US, Inc. All rights reserved.
