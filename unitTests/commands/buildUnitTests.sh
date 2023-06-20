#Get Data


#BasicMath
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1632854119&single=true&output=csv" --output x1.csv
sed -e "s/\"//g" x1.csv > basicMathOperators.xule
rm x1.csv

#BlockExpression

curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=485840780&single=true&output=csv" --output x2.csv
sed -e "s/\"//g" x2.csv > blockExpression.xule
rm x2.csv

#Boolean
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1884744869&single=true&output=csv" --output x3.csv

sed -e "s/\"//g" x3.csv > boolean.xule
rm x3.csv

#collectionFunctions
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=300797703&single=true&output=csv" --output x4.csv

sed -e "s/\"//g" x4.csv > collectionFunctions.xule
rm x4.csv

#collections
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=20466746&single=true&output=csv" --output x5.csv

sed -e "s/\"//g" x5.csv > collections.xule
rm x5.csv

#constants
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=886281383&single=true&output=csv" --output x6.csv

sed -e "s/\"//g" x6.csv > constants.xule
rm x6.csv

#dateFunctions
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1944785008&single=true&output=csv" --output x7.csv

sed -e "s/\"//g" x7.csv > dateFunctions.xule
rm x7.csv

#dates
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=2058348852&single=true&output=csv" --output x8.csv

sed -e "s/\"//g" x8.csv > dates.xule
rm x8.csv

#factFilters
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=725944600&single=true&output=csv" --output x8.csv

sed -e "s/\"//g" x8.csv > factFilters.xule
rm x8.csv

#filterFunction
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=651122003&single=true&output=csv" --output x9.csv

sed -e "s/\"//g" x9.csv > filterFunction.xule
rm x9.csv

#forLoop
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=35734832&single=true&output=csv" --output x10.csv

sed -e "s/\"//g" x10.csv > forLoop.xule
rm x10.csv

#functions
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=2054126147&single=true&output=csv" --output x11.csv

sed -e "s/\"//g" x11.csv > functions.xule
rm x11.csv

#ifThenElse
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1331165840&single=true&output=csv" --output x12.csv

sed -e "s/\"//g" x12.csv > ifThenElse.xule
rm x12.csv

#index
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=622332123&single=true&output=csv" --output x12.csv

sed -e "s/\"//g" x12.csv > index.xule
rm x12.csv

#keywords
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=710919262&single=true&output=csv" --output x13.csv

sed -e "s/\"//g" x13.csv > keywords.xule
rm x13.csv

#lists
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=217291961&single=true&output=csv" --output x14.csv

sed -e "s/\"//g" x14.csv > lists.xule
rm x14.csv

#literals
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=295511920&single=true&output=csv" --output x15.csv

sed -e "s/\"//g" x15.csv > literals.xule
rm x15.csv

#mathErrors
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1609548581&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > mathErrors.xule
rm x.csv

#messages
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=882948626&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > messages.xule
rm x.csv

#navigate
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1047083069&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > navigate.xule
rm x.csv

#none
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=549451599&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > none.xule
rm x.csv

#numericalFunctions
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=401650722&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > numericalFunctions.xule
rm x.csv

#precedance
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1392803541&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > precedance.xule
rm x.csv

#resources
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=729551048&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > resources.xule
rm x.csv

#sets
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1617878270&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > sets.xule
rm x.csv


#skip
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=480354327&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > skip.xule
rm x.csv


#strings
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1890555522&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > strings.xule
rm x.csv

#taxonomyFunctions
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1273110033&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > taxonomyFunctions.xule
rm x.csv

#valueExists
curl -L "https://docs.google.com/spreadsheets/d/e/2PACX-1vSEtUfyuj8X_KCiptdgLOmx0RmtIakd9raP59ydC_CLzITTNH5CiSNnW5uVPH6gxSFEx8hs2L7UKVv6/pub?gid=1419652766&single=true&output=csv" --output x.csv

sed -e "s/\"//g" x.csv > valueExists.xule
rm x.csv

python3.9 ~/arelle/Arelle-master/arellecmdline.py --xule-compile /Users/campbellpryde/Documents/GitHub/xule/unitTests/source/base  --plugins "xule" --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --xule-max-recurse-depth=2500

rm /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt

python3.9 ~/arelle/Arelle-master/arellecmdline.py --plugins 'xule|transforms/SEC|validate/EFM|inlineXbrlDocumentSet' --xule-run --noCertificateCheck --xule-rule-set /Users/campbellpryde/Documents/GitHub/xule/unitTests/compiled/ut-ruleset.zip --logNoRefObjectProperties --logFormat "[%(messageCode)s] %(message)s" >> /Users/campbellpryde/Documents/GitHub/xule/unitTests/output/output.txt