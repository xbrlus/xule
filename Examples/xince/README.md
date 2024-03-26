# XINCE Examples
## Overview
The XINCE syntax is a domain specific language used to define and create XBRL instances. The XINCE language uses the XULE syntax to manipulate facts prior to outputting XBRL instances in a JSON or XML format.

The XINCE Examples have the following folder structure:

* Source: Source files defined using XINCE that create XBRL instance documents.
* Compiled: Compiled xule zip models (ruleset files) that create the instance when run.
* Output: Folder with the generated Instance Documents

## Example 1. - Create Single Fact Instance
This example creates a single fact instance using the US-GAAP taxonomy.

To create the model.zip file run the following command to compile the file:

```sh
python3.12 ~/arelle/Arelle-master/arellecmdline.py --xule-compile ./source/example1  --plugins "xule" --xule-rule-set ./model/example1/xince-example1-model.zip  --xule-max-recurse-depth=25000
```

To create the instance run the following command:

```sh
python ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|xodel' --xule-time .005 --xule-debug --noCertificateCheck --logFile ./log/example1/xince-example1-log.xml --xule-rule-set ./model/example1/xince-example1-model.zip --logNoRefObjectProperties --xodel-location ./output/example1 --xodel-show-xule-log
```

This will create a json instance. To create an xml instance the following argument can be added:
```sh
--xince-file-type=xml
```



## License and Patent

See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.

Copyright 2015 - 2023 XBRL US, Inc. All rights reserved.
