python3.9 ~/arelle/Arelle-master/arellecmdline.py --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/base  --plugins "xule" --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-max-recurse-depth=2500

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' -f https://www.sec.gov/Archives/edgar/data/831259/000083125921000029/0000831259-21-000029-xbrl.zip --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" --xule-run-only TAXPROP011,TAXPROP012,TAXPROP013,TAXPROP014,TAXPROP015 >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" --xule-run-only UNITFILT001,UNITFILT002,UNITFILT003,UNITFILT004,UNITFILT005,UNITFILT006,UNITFILT007,UNITFILT008,UNITFILT009,UNITFILT010,UNITFILT011 >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

/Users/campbellpryde/Documents/GitHub/xule/unitTests/commands/buildUnitTests.sh


python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-run-only CFILT123 --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

/Applications/Arelle.app/Contents/MacOS/arelleCmdLine --plugins "xule|xule/xulecat" 

/Applications/Arelle.app/Contents/MacOS/arelleCmdLine --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/base  --plugins "xule" --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-max-recurse-depth=2500


/Applications/Arelle.app/Contents/MacOS/arelleCmdLine --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt


#xodel
python3.9 ~/arelle/Arelle-master/arellecmdline.py  --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/xodel  --plugins 'xule|xodel' --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/xodel-ruleset.zip --xule-max-recurse-depth=2500

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xodel|serializer' -f https://www.sec.gov/Archives/edgar/data/831259/000083125921000029/0000831259-21-000029-xbrl.zip --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/xodel-ruleset.zip --logNoRefObjectProperties  --xule-run-only create_base_taxonomy,create_extension_concepts,create_extension_labels,create_presentation_role,create_presentation --xodel-location '/Users/campbellpryde/Documents/GitHub/xule/unitTests/output'

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|xodel|serializer' -f https://www.sec.gov/Archives/edgar/data/831259/000083125921000029/0000831259-21-000029-xbrl.zip --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/xodel-ruleset.zip --logNoRefObjectProperties  --xule-run-only create_base_taxonomy,create_extension_concepts,create_extension_labels,create_presentation_role,create_presentation --xodel-location '/Users/campbellpryde/Documents/GitHub/xule/unitTests/output'

-f '/Users/campbellpryde/Downloads/0001109357-23-000067-xbrl.zip'

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' -f '/Users/campbellpryde/Downloads/0001109357-23-000067-xbrl.zip'  -v --xule-time .005 --xule-debug --noCertificateCheck   --logFile  /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/unit.xml --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/xodel-ruleset.zip --xule-run-only units_xml --xule-crash

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|xodel|serializer|transforms/SEC' -f https://www.sec.gov/Archives/edgar/data/831259/000083125921000029/0000831259-21-000029-xbrl.zip  --xule-run  --xule-time .005 --xule-debug --noCertificateCheck   --logFile  /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/unit.xml --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/xodel-ruleset.zip --xule-run-only create_base_unit_taxonomy,create_label_roles,create_label_roles_versionDate,create_utr_concepts,create_datatype_unit_concepts,create_alt_iso_concepts,create_scale_concepts,import_currency_taxonomy,create_labels_standard,add_alt_currency_labels,add_datatype_unit_labels,create_magnatude_labels,create_magnatude_documentation,create_domain_header_concepts,create_domain_labels,create_utr_presentation,create_utr_presentation_role,create_magnitude_presentation_role,create_magnitude_presentation,create_currency_presentation_role,create_currency_presentation,create_datatype_presentation_role,create_datatype_presentation,link_unit_to_builtIndatatype,create_dtr_concepts,create_base_ItemType_concepts,create_data_type_labels,create_inbuilt_data_type_labels,link_unit_to_datatype,link_currency_to_datatype,create_operator_arcroles,create_utr_definition_role,link_unit_to_unit,add_reference_qname,add_reference_qname_datatype,add_reference_qname_alt,add_reference_qname_si   --xodel-location '/Users/campbellpryde/Documents/GitHub/xule/unitTests/output'
