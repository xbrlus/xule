#Get Data


#Concepts
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPABYWGsJm3yv2EAczrEBPqcuxoo-fqst1a_t3Itd6toOBcsBLt_XrhVuCudYzePYJOSSu36NbKKXo/pub?gid=2076321437&single=true&output=csv" --output x1.csv
sed -e "s/\"//g" x1.csv > concepts.xule
rm x1.csv


#constants
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPABYWGsJm3yv2EAczrEBPqcuxoo-fqst1a_t3Itd6toOBcsBLt_XrhVuCudYzePYJOSSu36NbKKXo/pub?gid=251701975&single=true&output=csv" --output x6.csv

sed -e "s/\"//g" x6.csv > constants.xule
rm x6.csv

#outputAttributes
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPABYWGsJm3yv2EAczrEBPqcuxoo-fqst1a_t3Itd6toOBcsBLt_XrhVuCudYzePYJOSSu36NbKKXo/pub?gid=1525264930&single=true&output=csv" --output x7.csv

sed -e "s/\"//g" x7.csv > outputAttributes.xule
rm x7.csv

#taxonomy
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPABYWGsJm3yv2EAczrEBPqcuxoo-fqst1a_t3Itd6toOBcsBLt_XrhVuCudYzePYJOSSu36NbKKXo/pub?gid=1848360043&single=true&output=csv" --output x8.csv

sed -e "s/\"//g" x8.csv > taxonomy.xule
rm x8.csv



python3.9 ~/arelle/Arelle-master/arellecmdline.py --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/xodel  --plugins "xule" --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-xodel-ruleset.zip --xule-max-recurse-depth=2500

rm /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/xodel/xodel-output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-xodel-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/xodel/xodel-output.txt