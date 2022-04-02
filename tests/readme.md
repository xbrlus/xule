# Test Suite

## Overview

This suite contains a number of individual XBRL filings which represent pass and fail cases for each of the rules published by the Data Quality Committee.

A pass case specifies an XBRL instance document for a given rule that will pass the rule without raising any DQC error.

A fail case is expected to raise the error condition of the  rule and return the specified error message (or equivalent) to the user.

A user can take a given test case XBRL file and run it in a DQC rules-aware XBRL processor and compare the result against the expected result.

#### The test suite includes URLs to instance files (xml) with data matching the files listed in the "matrix" section of the .travis.yml for this branch or release. For each DQC Release, each test case listed has been instantiated by Travis-CI to: 

  1.  run xule with the corresponding ruleset.zip for a specified rule (or rules) for the instance file
  2.  produce messaging that is captured to environment's log.xml file
  3.  run a specific second file from the release's tests/output folder which contains identical data and **includes the error messaging**
  4.  invoke the compare.py routine to confirm both files produce identcal results
  5.  generate a 'failing' test message when the two results are not identical.  

This process indicates is that the first (live) instance produces the output expected - error messaging for the data in the instance - when the rule is fired.

#### Sample file couples (from the "matrix" of `.travis.yml` in the root of this archive)

  matrix:
    - INFILES='[{"file":"https://www.sec.gov/Archives/edgar/data/1004156/000119312518157677/arauco-20171231.xml", "xule_run_only":"DQC.IFRS.0080"},{"file":"http://www.sec.gov/Archives/edgar/data/1716586/000114036118040208/est-20181005.xml", "xule_run_only":"DQC.IFRS.0080"}]' EXFILES=$EXPECTED/DQC.IFRS.0080_arauco-2017.xml,$EXPECTED/DQC.IFRS.0080_est-2018.xml

#### Shell commands for the tests/output (from `travis-run.sh` in the root of this archive)

python3.5 -m arelle.CntlrCmdLine --plugin "validate/DQC|transforms/SEC" -v --xule-filing-list infiles.json --logFile log.xml -v --xule-debug
python3.5 compare.py --compare-file report.txt --test-files log.xml --expected-results $EXFILES --html-file report.html  

#### See also `compare.py` in the root of this archive  

© Copyright 2015 - 2022 XBRL US, Inc. All rights reserved.   
See [License](https://xbrl.us/dqc-license) for license information.  
See [Patent Notice](https://xbrl.us/dqc-patent) for patent infringement notice.
