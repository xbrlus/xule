python3.9 ~/arelle/Arelle-master/arellecmdline.py --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/base  --plugins "xule" --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-max-recurse-depth=2500

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' -f https://www.sec.gov/Archives/edgar/data/831259/000083125921000029/0000831259-21-000029-xbrl.zip --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" --xule-run-only TAXPROP011,TAXPROP012,TAXPROP013,TAXPROP014,TAXPROP015 >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" --xule-run-only UNITFILT001,UNITFILT002,UNITFILT003,UNITFILT004,UNITFILT005,UNITFILT006,UNITFILT007,UNITFILT008,UNITFILT009,UNITFILT010,UNITFILT011 >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

/Users/campbellpryde/Documents/GitHub/xule/unitTests/commands/buildUnitTests.sh


python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-run-only CFILT123 --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

