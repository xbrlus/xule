/**
 * QName Validator Module
 * Validates QName references in taxonomy objects according to OIM Taxonomy Schema
 * 
 * This module validates ALL QName references defined in the oim-taxonomy-schema.json.
 * 
 * VALIDATED PROPERTIES:
 * 
 * XBRL MODEL LEVEL:
 * - xbrlModel.name (or taxonomy.name for backward compatibility)
 * - importedTaxonomies[].xbrlModelName (or taxonomyName for backward compatibility)
 * - importedTaxonomies[].importObjects[]
 * - importedTaxonomies[].importObjectTypes[]
 * 
 * PROPERTY TYPES:
 * - propertyTypes[].name
 * - propertyTypes[].dataType (accepts dataType or collection QNames)
 * - propertyTypes[].enumerationDomain (must reference a domain object)
 * - propertyTypes[].allowedObjects[]
 * 
 * ABSTRACTS & MEMBERS:
 * - abstracts[].name
 * - members[].name
 * 
 * CONCEPTS:
 * - concepts[].name
 * - concepts[].dataType (accepts dataType or collection QNames)
 * - concepts[].enumerationDomain (must reference a domain object)
 * 
 * CUBES:
 * - cubes[].name
 * - cubes[].cubeType
 * - cubes[].cubeDimensions[].dimensionName
 * - cubes[].cubeDimensions[].domainName
 * - cubes[].cubeDimensions[].domainDataType
 * - cubes[].cubeNetworks[]
 * - cubes[].excludeCubes[]
 * - cubes[].requiredCubes[]
 * 
 * DIMENSIONS:
 * - dimensions[].name
 * - dimensions[].domainClass
 * - dimensions[].cubeTypes[]
 * 
 * DOMAINS:
 * - domains[].name
 * - domains[].root
 * - domains[].extendTargetName
 * - domains[].relationships[].source
 * - domains[].relationships[].target
 * 
 * DOMAIN CLASSES:
 * - domainClasses[].name
 * - domainClasses[].allowedDomainItems[]
 * 
 * NETWORKS:
 * - networks[].name
 * - networks[].relationshipTypeName
 * - networks[].extendTargetName
 * - networks[].roots[]
 * - networks[].relationships[].source
 * - networks[].relationships[].target
 * 
 * ENTITIES:
 * - entities[].name (SQName)
 * 
 * UNITS:
 * - units[].name
 * - units[].dataType
 * 
 * GROUPS:
 * - groups[].name
 * 
 * GROUP CONTENTS:
 * - groupContents[].groupName
 * - groupContents[].relatedNames[]
 * 
 * GROUP TREE:
 * - groupTree.name
 * - groupTree.relationships[].source
 * - groupTree.relationships[].target
 * 
 * RELATIONSHIP TYPES:
 * - relationshipTypes[].name
 * - relationshipTypes[].allowedLinkProperties[]
 * - relationshipTypes[].requiredLinkProperties[]
 * - relationshipTypes[].sourceObjects[]
 * - relationshipTypes[].targetObjects[]
 * 
 * LABELS:
 * - labels[].relatedName
 * - labels[].labelType
 * 
 * REFERENCES:
 * - references[].name
 * - references[].extendTargetName
 * - references[].relatedNames[]
 * - references[].referenceType
 * 
 * FACTSPACES:
 * - facts[].name (SQName)
 * - facts[].factDimensions['xbrl:concept']
 * - facts[].factDimensions['xbrl:unit'] (if QName format)
 * - facts[].factValues[].name (DEFINES new QName - not validated)
 * 
 * FOOTNOTES:
 * - footnotes[].name
 * 
 * LABEL TYPES:
 * - labelTypes[].name
 * - labelTypes[].dataType
 * - labelTypes[].allowedObjects[]
 * 
 * REFERENCE TYPES:
 * - referenceTypes[].name
 * - referenceTypes[].allowedObjects[]
 * - referenceTypes[].orderedProperties[]
 * - referenceTypes[].requiredProperties[]
 * 
 * CUBE TYPES:
 * - cubeTypes[].name
 * - cubeTypes[].baseCubeType
 * - cubeTypes[].allowedCubeDimensions[].dimensionName
 * - cubeTypes[].allowedCubeDimensions[].dimensionDataType
 * - cubeTypes[].allowedCubeDimensions[].allowedDimensionProperties[]
 * - cubeTypes[].allowedCubeDimensions[].requiredDimensionProperties[]
 * - cubeTypes[].requiredCubeRelationships[].relationshipTypeName
 * - cubeTypes[].requiredCubeRelationships[].source
 * - cubeTypes[].requiredCubeRelationships[].sourceDataType
 * - cubeTypes[].requiredCubeRelationships[].sourceObject
 * - cubeTypes[].requiredCubeRelationships[].target
 * - cubeTypes[].requiredCubeRelationships[].targetDataType
 * - cubeTypes[].requiredCubeRelationships[].targetObject
 * - cubeTypes[].requiredCubeProperties[]
 * 
 * DATA TYPES:
 * - dataTypes[].name
 * - dataTypes[].baseType
 * - dataTypes[].unitType.dataTypeNumerator
 * - dataTypes[].unitType.dataTypeDenominator
 * - dataTypes[].unitType.dataTypeMultiplier
 * - dataTypes[].mapType.keyType
 * - dataTypes[].mapType.valueType
 * 
 * TRANSFORMS:
 * - transforms[].name
 * - transforms[].inputDataType
 * - transforms[].outputDataType
 * 
 * PROPERTIES (generic):
 * - All objects with properties[].property
 * - All properties[].value where propertyType has dataType xs:QName
 * 
 * LAYOUTS (if provided in xbrlModel):
 * - layouts[].name
 * - layouts[].dataTables[].name (DEFINES new QName - not validated)
 * - layouts[].dataTables[].cubeName
 * 
 * TAXONOMY:
 * - taxonomy.factMaps[].name (DEFINES new QName - not validated)
 * - taxonomy.factMaps[].templateName (references tableTemplate, jsonTemplateMap, or xmlTemplateMap)
 * - taxonomy.factMaps[].cubeName (optional - references cube)
 * - taxonomy.factSources[].name (DEFINES new QName - not validated)
 * - taxonomy.factSources[].factMapName (references factMap)
 * - taxonomy.tableTemplates[].name (DEFINES new QName - not validated)
 * - taxonomy.jsonTemplates[].name (DEFINES new QName - not validated)
 * - taxonomy.xmlTemplates[].name (DEFINES new QName - not validated)
 */

import { getTaxonomyData } from './main.js';
import { BUILTIN_OBJECT_TYPES_SET as BUILTIN_OBJECT_TYPES, NON_IMPORTABLE_OBJECT_TYPES_SET } from './object-types.js';
import { validateCalculations, validateSummationItemRelationshipProperties, validateDuplicateCalculationRelationships } from './calculation-validator.js';

// Store validation errors
let validationErrors = [];

/**
 * Get all validation errors
 * @returns {Array<Object>} Array of validation error objects
 */
export function getValidationErrors() {
    return validationErrors;
}

/**
 * Clear all validation errors
 */
export function clearValidationErrors() {
    validationErrors = [];
}

/**
 * Add a validation error
 * @param {string} message - Error message
 * @param {Object} context - Context information (object name, property, etc.)
 */
function addValidationError(message, context) {
    const entry = {
        message,
        errorCode: 'oimte:invalidQNameReference',
        ...context
    };
    validationErrors.push(entry);
    // Errors flagged as persistent must survive the processFactSources re-validation
    // overwrite in taxonomy-builder.js (which calls validateQNameReferences again on
    // the already-processed model where extendTargetName entries have been removed).
    // Write directly to _persistentValidationErrors (not _preQNameValidationErrors) to
    // avoid the duplicate that would occur if we went through the _preQName merge block.
    if (context && context.persistent) {
        if (!window._persistentValidationErrors) window._persistentValidationErrors = [];
        const persistEntry = { ...entry };
        delete persistEntry.persistent; // remove internal flag before storing
        window._persistentValidationErrors.push(persistEntry);
    }
    console.error(`[QName Validator] ${message}`, context);
}

/**
 * Check if a QName is a built-in object type
 * @param {string} qname - The QName to check
 * @returns {boolean} True if it's a built-in object type
 */
function isBuiltinObjectType(qname) {
    return BUILTIN_OBJECT_TYPES.has(qname);
}

/**
 * Get the namespace prefix from documentInfo
 * @param {Object} documentInfo - The documentInfo object
 * @returns {string|null} The namespace prefix or null if not found
 */
function getDocumentNamespacePrefix(documentInfo) {
    if (!documentInfo || !documentInfo.documentNamespace) {
        return null;
    }
    
    const documentNamespace = documentInfo.documentNamespace;
    
    // documentNamespace must be a prefix string (a key in the namespaces map).
    // If found, return it directly.
    if (documentInfo.namespaces && documentInfo.namespaces[documentNamespace]) {
        return documentNamespace;
    }
    
    // If documentNamespace is not in the namespaces map but looks like a plain
    // prefix (no URI scheme or path separator), return it as-is so that
    // objectNamespaceMismatch can still fire for objects using a different prefix.
    // validateDocumentNamespace will separately report the missing declaration.
    if (!documentNamespace.includes('://') && !documentNamespace.includes('/')) {
        return documentNamespace;
    }
    
    return null;
}

/**
 * Validate that all objects defined in the taxonomy use the correct namespace prefix
 * This only validates objects that should be defined in the current taxonomy module,
 * not objects from imported taxonomies or spec-taxonomies.
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} documentInfo - The documentInfo object
 * @returns {Array<Object>} Array of namespace validation errors
 */
export function validateObjectNamespacePrefixes(taxonomy, documentInfo) {
    const errors = [];
    const expectedPrefix = getDocumentNamespacePrefix(documentInfo);
    
    if (expectedPrefix) {
        console.log(`[QName Validator] Expected namespace prefix: ${expectedPrefix}`);
    } else {
        console.log('[QName Validator] No documentNamespace defined - allowing any prefix except reserved ones');
    }
    
    // Reserved prefixes that are NOT allowed for object definitions in non-system taxonomies
    // These are reserved for built-in types and cannot be used to define new objects
    // UNLESS the taxonomy itself declares one of these as its documentNamespace
    const reservedPrefixes = new Set(['xbrl', 'xbrli', 'xs', 'iso4217', 'utr', 'enum2', 'xbrli-2003', 'oimce', 'oime', 'oimte', 'ref', 'xbrltt']);
    
    /**
     * Check if a QName uses the correct prefix
     * Only validates objects that should belong to this taxonomy module
     * @param {string} qname - The QName to check
     * @param {string} location - Where the QName is defined (for error reporting)
     */
    function checkQNamePrefix(qname, location) {
        if (!qname || typeof qname !== 'string') return;
        
        const colonIndex = qname.indexOf(':');
        if (colonIndex === -1) {
            // No prefix - this is an error
            errors.push({
                message: `Object name '${qname}' does not have a namespace prefix (oimce:invalidURIForReservedAlias)`,
                errorCode: 'oimce:invalidURIForReservedAlias',
                qname: qname,
                location: location,
                expectedPrefix: expectedPrefix || 'any'
            });
            return;
        }
        
        const prefix = qname.substring(0, colonIndex);
        
        // FIRST: Check if the prefix is defined in namespaces
        // This is oimte:objectNamespacePrefixNotDefined
        if (!documentInfo.namespaces || !documentInfo.namespaces[prefix]) {
            errors.push({
                message: `Object name '${qname}' uses undefined namespace prefix '${prefix}' (oimte:objectNamespacePrefixNotDefined)`,
                errorCode: 'oimte:objectNamespacePrefixNotDefined',
                qname: qname,
                location: location,
                actualPrefix: prefix,
                expectedPrefix: expectedPrefix || 'any',
                note: 'Prefix not found in documentInfo.namespaces'
            });
            return;
        }
        
        // SECOND: If expectedPrefix is defined, check if the prefix matches
        if (expectedPrefix && prefix === expectedPrefix) {
            // This object is in this module's namespace - this is correct
            return;
        }
        
        // THIRD: Check if using a reserved prefix that is NOT the document's namespace
        // This is oimce:invalidURIForReservedAlias
        // Compiled models are permitted to reference any prefix defined in namespaces
        // (reserved prefixes are legitimate references in a compiled/merged model)
        if (reservedPrefixes.has(prefix) && taxonomy.modelForm !== 'compiled') {
            errors.push({
                message: `Object name '${qname}' uses reserved namespace prefix '${prefix}' (oimce:invalidURIForReservedAlias)`,
                errorCode: 'oimce:invalidURIForReservedAlias',
                qname: qname,
                location: location,
                actualPrefix: prefix,
                expectedPrefix: expectedPrefix || 'any',
                note: `Reserved prefix '${prefix}' cannot be used to define objects unless it is the document namespace`
            });
            return;
        }
        
        // FOURTH: Check for namespace mismatch when modelForm is "module" or not defined
        // This is oimte:objectNamespaceMismatch
        // Only applies when expectedPrefix is defined (documentNamespace exists)
        if (expectedPrefix && prefix !== expectedPrefix) {
            // Check if modelForm is "module" or not defined
            const modelForm = documentInfo.modelForm;
            if (!modelForm || modelForm === 'module') {
                // In module form, objects must use the documentNamespace prefix
                errors.push({
                    message: `Object name '${qname}' uses prefix '${prefix}' which does not match documentNamespace prefix '${expectedPrefix}' (oimte:objectNamespaceMismatch)`,
                    errorCode: 'oimte:objectNamespaceMismatch',
                    qname: qname,
                    location: location,
                    actualPrefix: prefix,
                    expectedPrefix: expectedPrefix,
                    note: `When modelForm is 'module' or undefined, objects must use the documentNamespace prefix`
                });
                return;
            }
        }
        
        // If we reach here, the prefix is defined in namespaces and not reserved
        // This is valid - objects can use any defined namespace prefix
    }
    
    // Array properties that contain objects with 'name' property
    const arrayProperties = [
        'concepts',
        'abstracts',
        'members',
        'dimensions',
        'domains',
        'domainClasses',
        'dataTypes',
        'propertyTypes',
        'groups',
        'cubes',
        'networks',
        'entities',
        'units',
        'cubeTypes',
        'labelTypes',
        'referenceTypes',
        'relationshipTypes',
        'facts',
        'references',
        'transforms',
        'footnotes',
        'factSources',
        'factMaps',
        'tableTemplates',
        'layouts'
    ];
    
    arrayProperties.forEach(prop => {
        if (Array.isArray(taxonomy[prop])) {
            taxonomy[prop].forEach((obj, index) => {
                if (obj.name) {
                    checkQNamePrefix(obj.name, `${prop}[${index}].name`);
                }
            });
        }
    });
    
    // Check facts.factValues.name (these define new QNames)
    if (Array.isArray(taxonomy.facts)) {
        taxonomy.facts.forEach((fs, fsIndex) => {
            if (Array.isArray(fs.factValues)) {
                fs.factValues.forEach((fv, fvIndex) => {
                    if (fv.name) {
                        checkQNamePrefix(fv.name, `facts[${fsIndex}].factValues[${fvIndex}].name`);
                    }
                });
            }
        });
    }
    
    // Check groupTree.name if it exists
    if (taxonomy.groupTree && taxonomy.groupTree.name) {
        checkQNamePrefix(taxonomy.groupTree.name, 'groupTree.name');
    }
    
    // Check the taxonomy name itself
    if (taxonomy.name) {
        checkQNamePrefix(taxonomy.name, 'taxonomy.name');
    }

    // Check finalTaxonomy.name if it exists
    if (taxonomy.finalTaxonomy && taxonomy.finalTaxonomy.name) {
        checkQNamePrefix(taxonomy.finalTaxonomy.name, 'finalTaxonomy.name');
    }
    
    return errors;
}

/**
 * Validate that all URIs in the namespaces object are unique.
 * No two prefix keys may map to the same namespace URI.
 * @param {Object} documentInfo - The documentInfo object
 * @returns {Array<Object>} Array of validation errors
 */
function validateNamespaceURIUniqueness(documentInfo) {
    const errors = [];
    if (!documentInfo || !documentInfo.namespaces) {
        return errors;
    }
    const uriToPrefix = new Map();
    for (const [prefix, uri] of Object.entries(documentInfo.namespaces)) {
        if (uriToPrefix.has(uri)) {
            const firstPrefix = uriToPrefix.get(uri);
            errors.push({
                message: `Prefixes '${firstPrefix}' and '${prefix}' both map to the same namespace URI '${uri}' (oimce:multipleAliasesForURI)`,
                errorCode: 'oimce:multipleAliasesForURI',
                prefix1: firstPrefix,
                prefix2: prefix,
                uri: uri,
                location: 'documentInfo.namespaces'
            });
        } else {
            uriToPrefix.set(uri, prefix);
        }
    }
    return errors;
}

/**
 * Validate that the documentNamespace is properly defined in the namespaces.
 * Also checks that documentNamespace is present when modelForm is 'module' or not defined.
 * @param {Object} documentInfo - The documentInfo object
 * @param {Object|null} xbrlModel - The raw (pre-merge) xbrlModel object, used to read modelForm
 * @returns {Array<Object>} Array of validation errors
 */
export function validateDocumentNamespace(documentInfo, xbrlModel = null) {
    const errors = [];
    
    if (!documentInfo) {
        return errors;
    }
    
    // Determine whether the module constraint applies:
    // modelForm of 'module' (or absent, which defaults to module) requires documentNamespace.
    const modelForm = xbrlModel ? xbrlModel.modelForm : undefined;
    const isModuleForm = !modelForm || modelForm === 'module';
    
    // If documentNamespace is absent and module form applies, report the missing property.
    if (!documentInfo.documentNamespace) {
        if (isModuleForm) {
            errors.push({
                message: `The documentNamespace property is required when modelForm is 'module' or not defined (oimte:documentNamespaceNotDefined)`,
                errorCode: 'oimte:documentNamespaceNotDefined',
                location: 'documentInfo.documentNamespace',
                note: 'Modules must declare a documentNamespace prefix'
            });
        }
        return errors;
    }
    
    const documentNamespace = documentInfo.documentNamespace;
    
    // documentNamespace must be a prefix string that is defined as a key in the namespaces map
    if (documentInfo.namespaces && documentInfo.namespaces[documentNamespace]) {
        // Valid: documentNamespace is a prefix defined in namespaces
        return errors;
    }
    
    // If we reach here, documentNamespace is not a valid prefix in the namespaces map
    errors.push({
        message: `The documentNamespace '${documentNamespace}' is not defined as a prefix key in the namespaces declaration (oimte:documentNamespacePrefixNotDefined)`,
        errorCode: 'oimte:documentNamespacePrefixNotDefined',
        documentNamespace: documentNamespace,
        location: 'documentInfo.documentNamespace',
        note: 'The documentNamespace must be a prefix string defined as a key in the namespaces map'
    });
    
    return errors;
}

/**
 * Build an index of all defined names in the taxonomy
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Set<string>} Set of all defined QNames
 */
function buildDefinedNamesIndex(taxonomy) {
    const definedNames = new Set();
    const nameToLocation = new Map(); // Track where each name is defined for better error messages
    
    // Helper function to add a name and check for duplicates
    function addName(name, location) {
        if (definedNames.has(name)) {
            const firstLocation = nameToLocation.get(name);
            addValidationError(
                `Duplicate QName '${name}' found`,
                {
                    errorCode: 'oimte:duplicateObjects',
                    qname: name,
                    firstDefinedIn: firstLocation,
                    alsoFoundIn: location
                }
            );
        } else {
            definedNames.add(name);
            nameToLocation.set(name, location);
        }
    }
    
    // Add built-in object type names as valid objects that can be referenced
    // These are the meta-objects that define object types in the taxonomy model
    BUILTIN_OBJECT_TYPES.forEach(objectType => {
        definedNames.add(objectType);
        nameToLocation.set(objectType, 'built-in object type');
    });
    
    // Add the taxonomy name itself as a defined QName
    if (taxonomy.name) {
        addName(taxonomy.name, 'taxonomy.name');
    }
    
    // Array properties that contain objects with 'name' property
    const arrayProperties = [
        'concepts',
        'abstracts',
        'members',
        'dimensions',
        'domains',
        'domainClasses',
        'dataTypes',
        'propertyTypes',
        'groups',
        'cubes',
        'networks',
        'entities',
        'units',
        'cubeTypes',
        'labelTypes',
        'referenceTypes',
        'relationshipTypes',
        'modelTypes',  // Added modelTypes to define allowed model types
        'facts',  // Added facts to check for duplicate fact names
        'references',  // References also have name property
        'transforms',  // Transforms have name property
        'footnotes',   // Footnotes have name property
        'factMaps',    // Fact maps have name property (e.g., xbrl:OIM-JSON, xbrl:XBRL21XML)
        'factSources',     // Fact sets have name property
        'tableTemplates',  // Table templates have name property
        'jsonTemplates',   // JSON templates have name property
        'xmlTemplates',    // XML templates have name property
        'layouts',     // Layouts have name property
        'collections'  // Collections have name property
    ];
    
    arrayProperties.forEach(prop => {
        if (Array.isArray(taxonomy[prop])) {
            taxonomy[prop].forEach((obj, index) => {
                if (obj.name) {
                    addName(obj.name, `${prop}[${index}].name`);
                }
            });
        }
    });
    
    // Add layouts.dataTables.name (these define new QNames)
    if (Array.isArray(taxonomy.layouts)) {
        taxonomy.layouts.forEach((layout, layoutIndex) => {
            if (Array.isArray(layout.dataTables)) {
                layout.dataTables.forEach((dt, dtIndex) => {
                    if (dt.name) {
                        addName(dt.name, `layouts[${layoutIndex}].dataTables[${dtIndex}].name`);
                    }
                });
            }
        });
    }
    
    // Add facts.factValues.name (these define new QNames)
    if (Array.isArray(taxonomy.facts)) {
        taxonomy.facts.forEach((fs, fsIndex) => {
            if (Array.isArray(fs.factValues)) {
                fs.factValues.forEach((fv, fvIndex) => {
                    if (fv.name) {
                        addName(fv.name, `facts[${fsIndex}].factValues[${fvIndex}].name`);
                    }
                });
            }
        });
    }
    
    // Add groupTree.name if it exists
    if (taxonomy.groupTree && taxonomy.groupTree.name) {
        addName(taxonomy.groupTree.name, 'groupTree.name');
    }
    
    return definedNames;
}

/**
 * Check if a language code is a valid BCP 47 language code
 * Pattern: ^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$
 * Examples: en, en-US, fr, de-DE, zh-Hans-CN
 * @param {string} languageCode - The language code to validate
 * @returns {boolean} True if the language code is valid BCP 47 format
 */
function isValidBCP47LanguageCode(languageCode) {
    if (!languageCode || typeof languageCode !== 'string') {
        return false;
    }
    
    // BCP 47 language code pattern from oim-taxonomy-schema.json
    const bcp47Pattern = /^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{2,8})*$/;
    return bcp47Pattern.test(languageCode);
}

/**
 * Check if a QName is valid (either built-in or defined in taxonomy)
 * @param {string} qname - The QName to check
 * @param {Set<string>} definedNames - Set of defined QNames in taxonomy
 * @returns {boolean} True if the QName is valid
 */
function isValidQName(qname, definedNames) {
    // Check if it's a built-in object type
    if (isBuiltinObjectType(qname)) {
        return true;
    }
    
    // Check if it's defined in the taxonomy
    if (definedNames.has(qname)) {
        return true;
    }
    
    // Check if it's a built-in XSD type (common ones)
    const xsdTypes = [
        'xs:string', 'xs:boolean', 'xs:decimal', 'xs:float', 'xs:double',
        'xs:integer', 'xs:positiveInteger', 'xs:nonNegativeInteger',
        'xs:date', 'xs:dateTime', 'xs:time', 'xs:duration',
        'xs:token', 'xs:normalizedString', 'xs:anyURI', 'xs:QName',
        'xs:NCName', 'xs:language', 'xs:NMTOKEN', 'xs:NMTOKENS',
        'xs:ID', 'xs:IDREF', 'xs:IDREFS', 'xs:ENTITY', 'xs:ENTITIES',
        'xs:long', 'xs:int', 'xs:short', 'xs:byte',
        'xs:unsignedLong', 'xs:unsignedInt', 'xs:unsignedShort', 'xs:unsignedByte',
        'xs:base64Binary', 'xs:hexBinary'
    ];
    
    if (xsdTypes.includes(qname)) {
        return true;
    }
    
    // Check for XBRL/XBRLI built-in types
    const xbrlPrefix = qname.split(':')[0];
    if (xbrlPrefix === 'xbrli' || xbrlPrefix === 'xbrl') {
        // Allow common XBRL types that might be defined elsewhere
        const xbrlTypes = [
            'xbrli:stringItemType', 'xbrli:monetaryItemType', 'xbrli:decimalItemType',
            'xbrli:dateItemType', 'xbrli:positiveIntegerItemType', 'xbrli:integerItemType',
            'xbrli:monetary', 'xbrli:shares', 'xbrli:pure',
            'xbrli:balanceType', 'xbrli:periodType', 'xbrli:aggregationType',
            'xbrli:reportAttributeType', 'xbrli:timeSeriesDataType', 'xbrli:intervalConventionType',
            'xbrli:startEndDates', 'xbrli:periodString', 'xbrli:unitString', 'xbrli:emoji'
        ];
        
        if (xbrlTypes.includes(qname)) {
            return true;
        }
    }
    
    return false;
}

/**
 * Get the object type QName for a given defined object name in the taxonomy.
 * Searches common arrays (concepts, members, abstracts, entities, units, etc.)
 * and returns the corresponding built-in object type QName (e.g. 'xbrl:conceptObject')
 * or null if not found.
 * @param {Object} taxonomy
 * @param {string} qname
 * @returns {string|null}
 */
export function getObjectTypeForQName(taxonomy, qname) {
    if (!taxonomy || !qname) return null;

    const mapping = [
        { array: 'concepts', type: 'xbrl:conceptObject' },
        { array: 'members', type: 'xbrl:memberObject' },
        { array: 'abstracts', type: 'xbrl:abstractObject' },
        { array: 'entities', type: 'xbrl:entityObject' },
        { array: 'units', type: 'xbrl:unitObject' },
        { array: 'groups', type: 'xbrl:groupObject' },
        { array: 'domains', type: 'xbrl:domainObject' },
        { array: 'domainClasses', type: 'xbrl:domainClassObject' },
        { array: 'dimensions', type: 'xbrl:dimensionObject' },
        { array: 'labels', type: 'xbrl:labelObject' },
        { array: 'networks', type: 'xbrl:networkObject' },
        { array: 'cubes', type: 'xbrl:cubeObject' },
        { array: 'references', type: 'xbrl:referenceObject' },
        { array: 'footnotes', type: 'xbrl:footnoteObject' },
        { array: 'factMaps', type: 'xbrl:factMapObject' },
        { array: 'factSources', type: 'xbrl:factSourceObject' },
        { array: 'tableTemplates', type: 'xbrl:tableTemplateObject' },
        { array: 'jsonTemplates', type: 'xbrl:jsonTemplateObject' },
        { array: 'xmlTemplates', type: 'xbrl:xmlTemplateObject' },
        { array: 'dataTypes', type: 'xbrl:dataTypeObject' },
        { array: 'collections', type: 'xbrl:collectionObject' },
        { array: 'relationshipTypes', type: 'xbrl:relationshipTypeObject' },
        { array: 'propertyTypes', type: 'xbrl:propertyTypeObject' },
        { array: 'modelTypes', type: 'xbrl:modelTypeObject' },
        { array: 'labelTypes', type: 'xbrl:labelTypeObject' },
        { array: 'referenceTypes', type: 'xbrl:referenceTypeObject' },
        { array: 'cubeTypes', type: 'xbrl:cubeTypeObject' }
    ];

    for (const m of mapping) {
        const arr = taxonomy[m.array];
        if (!Array.isArray(arr)) continue;
        for (const obj of arr) {
            if (obj && obj.name === qname) return m.type;
            // Some arrays store QName references directly (e.g. relationship targets as strings) - skip
        }
    }

    // If not found, check built-in object type names
    if (BUILTIN_OBJECT_TYPES.has(qname)) return qname;

    return null;
}

/**
 * Check if a QName is a valid reference for a dataType property on concept, propertyType, or labelType objects.
 * Valid references are: built-in XSD types (xs: prefix), xbrli:/xbrl: built-in types,
 * dataType objects, and collection objects.
 * @param {string} qname - The QName to check
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set<string>} definedNames - Set of defined QNames
 * @returns {boolean} True if the QName is a valid dataType reference
 */
function isValidDataTypeRef(qname, taxonomy, definedNames) {
    if (!qname) return false;

    // Built-in XSD types (xs: prefix) are always valid data type references
    const prefix = qname.split(':')[0];
    if (prefix === 'xs') return true;

    // xbrli:/xbrl: built-in types are valid if recognised
    if (prefix === 'xbrli' || prefix === 'xbrl') {
        return isValidQName(qname, definedNames);
    }

    // For taxonomy-defined names, resolve to the object type
    const objType = getObjectTypeForQName(taxonomy, qname);
    return objType === 'xbrl:dataTypeObject' ||
           objType === 'xbrl:collectionObject';
}

/**
 * Validate allowedDomainItems in domainClass objects
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set<string>} definedNames - Set of defined QNames
 */
function validateAllowedDomainItems(taxonomy, definedNames) {
    if (!Array.isArray(taxonomy.domainClasses)) {
        return;
    }
    
    taxonomy.domainClasses.forEach(domainClass => {
        if (Array.isArray(domainClass.allowedDomainItems)) {
            domainClass.allowedDomainItems.forEach(qname => {
                if (!isValidQName(qname, definedNames)) {
                    addValidationError(
                        `Invalid QName '${qname}' in allowedDomainItems`,
                        {
                            domainClass: domainClass.name,
                            property: 'allowedDomainItems',
                            invalidQName: qname
                        }
                    );
                } else {
                    // Each entry must be a built-in object type, an XS/xbrli type,
                    // a dataType object, a collection object, or a domain object
                    const objType = getObjectTypeForQName(taxonomy, qname);
                    const isAllowed = isBuiltinObjectType(qname) ||
                        isValidDataTypeRef(qname, taxonomy, definedNames) ||
                        objType === 'xbrl:dataTypeObject' ||
                        objType === 'xbrl:collectionObject' ||
                        objType === 'xbrl:domainObject';
                    if (!isAllowed) {
                        addValidationError(
                            `allowedDomainItems entry '${qname}' in domainClass '${domainClass.name}' must be a built-in object type, a dataType, a collection, a domain, or a built-in XML Schema type`,
                            {
                                domainClass: domainClass.name,
                                property: 'allowedDomainItems',
                                invalidQName: qname,
                                errorCode: 'oimte:invalidQNameType'
                            }
                        );
                    }
                }
            });
        }
    });
}

/**
 * Validate QName references in cubeDimensions
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set<string>} definedNames - Set of defined QNames
 */
function validateCubeDimensions(taxonomy, definedNames) {
    if (!Array.isArray(taxonomy.cubes)) {
        return;
    }
    
    taxonomy.cubes.forEach(cube => {
        if (Array.isArray(cube.cubeDimensions)) {
            // Check for duplicate dimensions
            const dimensionNames = new Map(); // Map to track dimensionName -> first occurrence index
            
            cube.cubeDimensions.forEach((cubeDim, idx) => {
                // Validate dimensionName
                if (cubeDim.dimensionName && !isValidQName(cubeDim.dimensionName, definedNames)) {
                    addValidationError(
                        `Invalid dimensionName '${cubeDim.dimensionName}' in cube`,
                        {
                            cube: cube.name,
                            property: 'cubeDimensions.dimensionName',
                            invalidQName: cubeDim.dimensionName
                        }
                    );
                }
                
                // Check for duplicate dimensionName
                if (cubeDim.dimensionName) {
                    if (dimensionNames.has(cubeDim.dimensionName)) {
                        const firstIdx = dimensionNames.get(cubeDim.dimensionName);
                        addValidationError(
                            `Duplicate dimension '${cubeDim.dimensionName}' in cube '${cube.name}'`,
                            {
                                cube: cube.name,
                                property: `cubeDimensions[${idx}].dimensionName`,
                                dimensionName: cubeDim.dimensionName,
                                firstOccurrence: `cubeDimensions[${firstIdx}]`,
                                errorCode: 'oimte:duplicateDimensionsInCube',
                                cubeName: cube.name
                            }
                        );
                    } else {
                        dimensionNames.set(cubeDim.dimensionName, idx);
                    }
                }
                
                // Validate domainName if present
                if (cubeDim.domainName && !isValidQName(cubeDim.domainName, definedNames)) {
                    addValidationError(
                        `Invalid domainName '${cubeDim.domainName}' in cube`,
                        {
                            cube: cube.name,
                            property: 'cubeDimensions.domainName',
                            invalidQName: cubeDim.domainName
                        }
                    );
                }
            });
        }
    });
}

/**
 * Validate QName references in other taxonomy arrays
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set<string>} definedNames - Set of defined QNames
 */
function validateOtherQNameReferences(taxonomy, definedNames) {
    // ========== TAXONOMY LEVEL ==========
    // Validate importedTaxonomies
    if (Array.isArray(taxonomy.importedTaxonomies)) {
        taxonomy.importedTaxonomies.forEach(imp => {
            // NOTE: imp.taxonomyName references an external taxonomy file and should not be validated here
            // It will be validated when that taxonomy is loaded
            
            if (Array.isArray(imp.importObjects)) {
                imp.importObjects.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in importObjects`,
                            { property: 'importedTaxonomies.importObjects', invalidQName: qname, errorCode: 'oimte:invalidQNameReference' }
                        );
                    }
                });
            }
            if (Array.isArray(imp.importObjectTypes)) {
                imp.importObjectTypes.forEach(qname => {
                    // importObjectTypes must only contain known built-in object types
                    if (!isBuiltinObjectType(qname)) {
                        addValidationError(
                            `Invalid object type '${qname}' in importObjectTypes - must be a built-in object type`,
                            { property: 'importedTaxonomies.importObjectTypes', invalidQName: qname }
                        );
                    }
                    // xbrl:importTaxonomyObject has its own specific error
                    else if (qname === 'xbrl:importTaxonomyObject') {
                        addValidationError(
                            `Invalid object type 'xbrl:importTaxonomyObject' in importObjectTypes - importTaxonomy objects cannot be imported`,
                            { property: 'importedTaxonomies.importObjectTypes', invalidQName: qname, errorCode: 'oimte:invalidReferenceToImportTaxonomyObject' }
                        );
                    }
                    // Non-importable types: nested sub-objects, singletons, and xbrl:labelObject
                    // (xbrl:cubeDimensionObject, xbrl:propertyObject, xbrl:finalTaxonomyObject,
                    //  xbrl:groupTreeObject, xbrl:xbrlModelObject, xbrl:labelObject)
                    else if (NON_IMPORTABLE_OBJECT_TYPES_SET.has(qname)) {
                        addValidationError(
                            `Invalid object type '${qname}' in importObjectTypes - this object type is a nested, singleton, or non-importable type`,
                            { property: 'importedTaxonomies.importObjectTypes', invalidQName: qname, errorCode: 'oimte:invalidImportObjectType' }
                        );
                    }
                });
            }
            
            // Validate selections array (if present)
            // Implements all constraints from the Selection Expression Grammar appendix
            if (Array.isArray(imp.selections)) {
                // ── Selection Expression Grammar – operator/type constants ──────────────
                // §5: the full enumerated set of recognised operators
                const VALID_SEL_OPERATORS = new Set([
                    '==', '!=', 'in', 'not in', 'contains', 'not contains',
                    '>', '<', '>=', '<='
                ]);
                // §7: operators whose value MUST be a non-empty array
                const ARRAY_VALUE_OPERATORS = new Set(['in', 'not in']);
                // §6: operators that are only valid on string properties
                const STRING_ONLY_OPERATORS = new Set(['contains', 'not contains']);
                // §6: ordering operators – not permitted on boolean properties
                const ORDERING_OPERATORS = new Set(['>', '<', '>=', '<=']);

                // §6: known built-in properties that have an effective type of xs:boolean.
                // Boolean properties only support == and != (all other operators are incompatible).
                const BOOLEAN_PROPERTIES = new Set([
                    'nillable', 'definitional', 'allowedAsLinkProperty', 'completeDomain',
                    'excludeLabels', 'finalTaxonomyFlag', 'allowedAsLinkProperty'
                ]);

                const selModelName = imp.xbrlModelName || imp.taxonomyName || 'unknown';

                imp.selections.forEach((selection, selIndex) => {
                    const selPath = `importedTaxonomies[xbrlModelName='${selModelName}'].selections[${selIndex}]`;

                    // ── §1: objectType is required for object-format selections ────────
                    if (typeof selection === 'object' && selection !== null && !selection.objectType) {
                        addValidationError(
                            `Invalid selection expression at ${selPath}: the required 'objectType' property is missing (constraint §1)`,
                            {
                                property: 'importedTaxonomies.selections',
                                selectionIndex: selIndex,
                                errorCode: 'oimte:invalidSelectionExpression',
                                constraint: '§1'
                            }
                        );
                        return; // Cannot validate further without objectType
                    }

                    // Extract objectType from either string or object format
                    let objectType = null;
                    if (typeof selection === 'string') {
                        const match = selection.match(/^([^\s]+)\s+where\s+/i);
                        if (match) objectType = match[1];
                    } else if (typeof selection === 'object' && selection.objectType) {
                        objectType = selection.objectType;
                    }

                    // ── §2: objectType must be a recognised model component object type ─
                    if (objectType && !isBuiltinObjectType(objectType)) {
                        addValidationError(
                            `Invalid selection expression at ${selPath}: objectType '${objectType}' is not a recognised model component object type (constraint §2). See sec-taxonomy-object for the list of valid object types.`,
                            {
                                property: 'importedTaxonomies.selections',
                                selectionIndex: selIndex,
                                objectType: objectType,
                                errorCode: 'oimte:invalidSelectionExpression',
                                constraint: '§2'
                            }
                        );
                    }

                    // ── Existing specific-type constraints ────────────────────────────
                    // xbrl:importTaxonomyObject is never importable via selections
                    if (objectType === 'xbrl:importTaxonomyObject') {
                        addValidationError(
                            `Invalid object type 'xbrl:importTaxonomyObject' in selections - importTaxonomy objects cannot be imported`,
                            {
                                property: 'importedTaxonomies.selections',
                                selectionIndex: selIndex,
                                objectType: objectType,
                                errorCode: 'oimte:invalidReferenceToImportTaxonomyObject'
                            }
                        );
                    }

                    // excludeLabels=true + xbrl:labelObject in selections is a conflict
                    if (objectType === 'xbrl:labelObject' && imp.excludeLabels === true) {
                        addValidationError(
                            `Conflicting import properties: 'excludeLabels' is true but selections[${selIndex}] specifies objectType 'xbrl:labelObject'`,
                            {
                                property: 'importedTaxonomies.selections',
                                selectionIndex: selIndex,
                                objectType: objectType,
                                errorCode: 'oimte:conflictingImportProperties'
                            }
                        );
                    }

                    // ── Validate each where clause ─────────────────────────────────────
                    const whereClauses = (typeof selection === 'object' && Array.isArray(selection.where))
                        ? selection.where
                        : [];

                    whereClauses.forEach((clause, clauseIdx) => {
                        if (!clause || typeof clause !== 'object') return;

                        const { property: propName, operator, value } = clause;
                        const clausePath = `${selPath}.where[${clauseIdx}]`;

                        // ── §5: operator must be in the enumerated set ───────────────
                        if (operator !== undefined && !VALID_SEL_OPERATORS.has(operator)) {
                            addValidationError(
                                `Invalid selection expression at ${clausePath}: operator '${operator}' is not a recognised operator (constraint §5). Valid operators are: ==, !=, in, not in, contains, not contains, >, <, >=, <=`,
                                {
                                    property: 'importedTaxonomies.selections.where.operator',
                                    selectionIndex: selIndex,
                                    clauseIndex: clauseIdx,
                                    invalidOperator: operator,
                                    errorCode: 'oimte:invalidSelectionExpression',
                                    constraint: '§5'
                                }
                            );
                        }

                        // ── §6: operator must be compatible with the property's effective type ──
                        if (operator && propName && BOOLEAN_PROPERTIES.has(propName)) {
                            // Boolean properties only support == and !=
                            if (ORDERING_OPERATORS.has(operator) || ARRAY_VALUE_OPERATORS.has(operator) || STRING_ONLY_OPERATORS.has(operator)) {
                                addValidationError(
                                    `Invalid selection expression at ${clausePath}: operator '${operator}' is not compatible with boolean property '${propName}' (constraint §6). Boolean properties only support '==' and '!='`,
                                    {
                                        property: 'importedTaxonomies.selections.where',
                                        selectionIndex: selIndex,
                                        clauseIndex: clauseIdx,
                                        invalidOperator: operator,
                                        propertyName: propName,
                                        effectiveType: 'boolean',
                                        errorCode: 'oimte:invalidSelectionExpression',
                                        constraint: '§6'
                                    }
                                );
                            }
                        }

                        // ── §7: 'in' / 'not in' value must be a non-empty array ──────
                        if (operator && ARRAY_VALUE_OPERATORS.has(operator)) {
                            if (!Array.isArray(value)) {
                                addValidationError(
                                    `Invalid selection expression at ${clausePath}: operator '${operator}' requires a JSON array as its value but received ${typeof value === 'string' ? `string '${value}'` : `a ${typeof value}`} (constraint §7)`,
                                    {
                                        property: 'importedTaxonomies.selections.where.value',
                                        selectionIndex: selIndex,
                                        clauseIndex: clauseIdx,
                                        invalidOperator: operator,
                                        errorCode: 'oimte:invalidSelectionExpression',
                                        constraint: '§7'
                                    }
                                );
                            } else if (value.length === 0) {
                                addValidationError(
                                    `Invalid selection expression at ${clausePath}: operator '${operator}' requires a non-empty array but an empty array [] was provided (constraint §7)`,
                                    {
                                        property: 'importedTaxonomies.selections.where.value',
                                        selectionIndex: selIndex,
                                        clauseIndex: clauseIdx,
                                        invalidOperator: operator,
                                        errorCode: 'oimte:invalidSelectionExpression',
                                        constraint: '§7'
                                    }
                                );
                            }
                        }
                    });
                });
            }
        });
    }
    
    // ========== PROPERTY TYPES ==========
    if (Array.isArray(taxonomy.propertyTypes)) {
        taxonomy.propertyTypes.forEach(propType => {
            if (propType.dataType) {
                if (!isValidQName(propType.dataType, definedNames)) {
                    addValidationError(
                        `Invalid dataType '${propType.dataType}' in propertyType`,
                        { propertyType: propType.name, property: 'dataType', invalidQName: propType.dataType }
                    );
                } else if (!isValidDataTypeRef(propType.dataType, taxonomy, definedNames)) {
                    addValidationError(
                        `dataType '${propType.dataType}' in propertyType must reference a dataType object, collection object, or built-in XML Schema type`,
                        { propertyType: propType.name, property: 'dataType', invalidQName: propType.dataType, errorCode: 'oimte:invalidQNameType' }
                    );
                }
            }
            if (propType.enumerationDomain) {
                if (!isValidQName(propType.enumerationDomain, definedNames)) {
                    addValidationError(
                        `Invalid enumerationDomain '${propType.enumerationDomain}' in propertyType`,
                        { propertyType: propType.name, property: 'enumerationDomain', invalidQName: propType.enumerationDomain }
                    );
                } else {
                    const objType = getObjectTypeForQName(taxonomy, propType.enumerationDomain);
                    if (objType !== 'xbrl:domainObject') {
                        addValidationError(
                            `enumerationDomain '${propType.enumerationDomain}' in propertyType must reference a domain object`,
                            { propertyType: propType.name, property: 'enumerationDomain', invalidQName: propType.enumerationDomain, errorCode: 'oimte:invalidQNameType' }
                        );
                    }
                }
            }
            if (Array.isArray(propType.allowedObjects)) {
                propType.allowedObjects.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in propertyType allowedObjects`,
                            { propertyType: propType.name, property: 'allowedObjects', invalidQName: qname }
                        );
                    }
                });
            }
        });
    }
    
    // ========== CONCEPTS ==========
    if (Array.isArray(taxonomy.concepts)) {
        taxonomy.concepts.forEach(concept => {
            if (concept.dataType) {
                if (!isValidQName(concept.dataType, definedNames)) {
                    addValidationError(
                        `Invalid dataType '${concept.dataType}' in concept`,
                        { concept: concept.name, property: 'dataType', invalidQName: concept.dataType }
                    );
                } else if (!isValidDataTypeRef(concept.dataType, taxonomy, definedNames)) {
                    addValidationError(
                        `dataType '${concept.dataType}' in concept must reference a dataType object, collection object, or built-in XML Schema type`,
                        { concept: concept.name, property: 'dataType', invalidQName: concept.dataType, errorCode: 'oimte:invalidQNameType' }
                    );
                }
            }
            if (concept.enumerationDomain) {
                if (!isValidQName(concept.enumerationDomain, definedNames)) {
                    addValidationError(
                        `Invalid enumerationDomain '${concept.enumerationDomain}' in concept`,
                        { concept: concept.name, property: 'enumerationDomain', invalidQName: concept.enumerationDomain }
                    );
                } else {
                    const objType = getObjectTypeForQName(taxonomy, concept.enumerationDomain);
                    if (objType !== 'xbrl:domainObject') {
                        addValidationError(
                            `enumerationDomain '${concept.enumerationDomain}' in concept must reference a domain object`,
                            { concept: concept.name, property: 'enumerationDomain', invalidQName: concept.enumerationDomain, errorCode: 'oimte:invalidQNameType' }
                        );
                    }
                }
            }
        });
    }
    
    // ========== MEMBERS ==========
    if (Array.isArray(taxonomy.members)) {
        taxonomy.members.forEach(member => {
            if (Array.isArray(member.domainClasses)) {
                member.domainClasses.forEach(domainClass => {
                    if (!isValidQName(domainClass, definedNames)) {
                        addValidationError(
                            `Invalid domainClass '${domainClass}' in member`,
                            { member: member.name, property: 'domainClasses', invalidQName: domainClass, errorCode: 'oimte:invalidQNameReference' }
                        );
                    }
                });
            }
        });
    }
    
    // ========== CUBES ==========
    if (Array.isArray(taxonomy.cubes)) {
        // Build a name→cube lookup for cross-cube validation
        const cubeMap = Object.create(null);
        taxonomy.cubes.forEach(c => { if (c.name) cubeMap[c.name] = c; });

        taxonomy.cubes.forEach(cube => {
            if (cube.extendTargetName && !isValidQName(cube.extendTargetName, definedNames)) {
                addValidationError(
                    `Invalid extendTargetName '${cube.extendTargetName}' in cube`,
                    { cube: cube.extendTargetName, property: 'extendTargetName', invalidQName: cube.extendTargetName, persistent: true }
                );
            } else if (cube.extendTargetName && isValidQName(cube.extendTargetName, definedNames)) {
                const extendType = getObjectTypeForQName(taxonomy, cube.extendTargetName);
                if (extendType !== 'xbrl:cubeObject') {
                    addValidationError(
                        `extendTargetName '${cube.extendTargetName}' in cube must reference a cube object, but references a '${extendType || 'unknown'}' object`,
                        {
                            cube: cube.extendTargetName,
                            property: 'extendTargetName',
                            invalidQName: cube.extendTargetName,
                            errorCode: 'oimte:invalidQNameType',
                            persistent: true
                        }
                    );
                }
            }
            if (cube.cubeType && !isValidQName(cube.cubeType, definedNames)) {
                addValidationError(
                    `Invalid cubeType '${cube.cubeType}' in cube`,
                    { cube: cube.name, property: 'cubeType', invalidQName: cube.cubeType }
                );
            } else if (cube.cubeType) {
                const cubeTypeObjType = getObjectTypeForQName(taxonomy, cube.cubeType);
                if (cubeTypeObjType !== 'xbrl:cubeTypeObject') {
                    addValidationError(
                        `cubeType '${cube.cubeType}' in cube must reference a cubeType object, but references a '${cubeTypeObjType || 'unknown'}' object`,
                        { cube: cube.name, property: 'cubeType', invalidQName: cube.cubeType, errorCode: 'oimte:invalidQNameType' }
                    );
                }
            }
            if (Array.isArray(cube.cubeDimensions)) {
                cube.cubeDimensions.forEach(cd => {
                    if (cd.domainDataType && !isValidQName(cd.domainDataType, definedNames)) {
                        addValidationError(
                            `Invalid domainDataType '${cd.domainDataType}' in cubeDimensions`,
                            { cube: cube.name, property: 'cubeDimensions.domainDataType', invalidQName: cd.domainDataType }
                        );
                    }
                    // Validate periodConstraints conceptName and context references
                    if (Array.isArray(cd.periodConstraints)) {
                        cd.periodConstraints.forEach((pc, pcIdx) => {
                            ['startDate', 'endDate'].forEach(dateField => {
                                if (pc[dateField]) {
                                    const dateConstraint = pc[dateField];
                                    if (dateConstraint.conceptName) {
                                        if (!isValidQName(dateConstraint.conceptName, definedNames)) {
                                            addValidationError(
                                                `Invalid conceptName '${dateConstraint.conceptName}' in periodConstraints[${pcIdx}].${dateField}`,
                                                { cube: cube.name, property: `cubeDimensions.periodConstraints[${pcIdx}].${dateField}.conceptName`, invalidQName: dateConstraint.conceptName }
                                            );
                                        } else {
                                            const conceptObjType = getObjectTypeForQName(taxonomy, dateConstraint.conceptName);
                                            if (conceptObjType !== 'xbrl:conceptObject') {
                                                addValidationError(
                                                    `conceptName '${dateConstraint.conceptName}' in periodConstraints[${pcIdx}].${dateField} must reference a concept object, but references a '${conceptObjType || 'unknown'}' object`,
                                                    { cube: cube.name, property: `cubeDimensions.periodConstraints[${pcIdx}].${dateField}.conceptName`, invalidQName: dateConstraint.conceptName, errorCode: 'oimte:invalidQNameType' }
                                                );
                                            }
                                        }
                                    }
                                    if (dateConstraint.context) {
                                        // context value is 'prefix:localName@suffix' — extract the QName before '@'
                                        const atIdx = dateConstraint.context.indexOf('@');
                                        const contextQName = atIdx >= 0 ? dateConstraint.context.slice(0, atIdx) : dateConstraint.context;
                                        if (!isValidQName(contextQName, definedNames)) {
                                            addValidationError(
                                                `Invalid context QName '${contextQName}' in periodConstraints[${pcIdx}].${dateField}`,
                                                { cube: cube.name, property: `cubeDimensions.periodConstraints[${pcIdx}].${dateField}.context`, invalidQName: contextQName }
                                            );
                                        } else {
                                            const ctxObjType = getObjectTypeForQName(taxonomy, contextQName);
                                            if (ctxObjType !== 'xbrl:conceptObject') {
                                                addValidationError(
                                                    `context '${contextQName}' in periodConstraints[${pcIdx}].${dateField} must reference a concept object, but references a '${ctxObjType || 'unknown'}' object`,
                                                    { cube: cube.name, property: `cubeDimensions.periodConstraints[${pcIdx}].${dateField}.context`, invalidQName: contextQName, errorCode: 'oimte:invalidQNameType' }
                                                );
                                            }
                                        }
                                    }
                                }
                            });
                        });
                    }
                });
            }
            if (Array.isArray(cube.cubeNetworks)) {
                cube.cubeNetworks.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in cube cubeNetworks`,
                            { cube: cube.name, property: 'cubeNetworks', invalidQName: qname }
                        );
                    } else {
                        const networkObjType = getObjectTypeForQName(taxonomy, qname);
                        if (networkObjType !== 'xbrl:networkObject') {
                            addValidationError(
                                `QName '${qname}' in cube cubeNetworks must reference a network object, but references a '${networkObjType || 'unknown'}' object`,
                                { cube: cube.name, property: 'cubeNetworks', invalidQName: qname, errorCode: 'oimte:invalidQNameType' }
                            );
                        }
                    }
                });
            }
            if (Array.isArray(cube.excludeCubes)) {
                cube.excludeCubes.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in cube excludeCubes`,
                            { cube: cube.name, property: 'excludeCubes', invalidQName: qname }
                        );
                    }
                });
            }
            if (Array.isArray(cube.requiredCubes)) {
                cube.requiredCubes.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in cube requiredCubes`,
                            { cube: cube.name, property: 'requiredCubes', invalidQName: qname }
                        );
                    }
                });
            }
            // Check if any excludeCube and requiredCube share the same dimensional space
            if (Array.isArray(cube.excludeCubes) && cube.excludeCubes.length > 0 &&
                Array.isArray(cube.requiredCubes) && cube.requiredCubes.length > 0) {
                // Helper: get the set of dimensionNames for a cube object
                const getDimNames = c => new Set(
                    Array.isArray(c.cubeDimensions)
                        ? c.cubeDimensions.map(cd => cd.dimensionName).filter(Boolean)
                        : []
                );
                for (const excludedQName of cube.excludeCubes) {
                    const excludedCube = cubeMap[excludedQName];
                    if (!excludedCube) continue;
                    const excludedDims = getDimNames(excludedCube);
                    for (const requiredQName of cube.requiredCubes) {
                        const requiredCube = cubeMap[requiredQName];
                        if (!requiredCube) continue;
                        const requiredDims = getDimNames(requiredCube);
                        // Two cubes share the same dimensional space when they have
                        // an identical set of dimension names.
                        const sameDimSpace =
                            excludedDims.size === requiredDims.size &&
                            [...excludedDims].every(d => requiredDims.has(d));
                        if (sameDimSpace) {
                            addValidationError(
                                `Cube '${cube.name}' has excludeCube '${excludedQName}' and requiredCube '${requiredQName}' that share the same dimensional space`,
                                {
                                    cube: cube.name,
                                    property: 'excludeCubes',
                                    excludedCube: excludedQName,
                                    requiredCube: requiredQName,
                                    errorCode: 'oimte:excludeCubeSharesDimensionalSpaceWithRequiredCube'
                                }
                            );
                        }
                    }
                }
            }
        });
    }
    
    // ========== DIMENSIONS ==========
    if (Array.isArray(taxonomy.dimensions)) {
        taxonomy.dimensions.forEach(dimension => {
            if (dimension.domainClass && !isValidQName(dimension.domainClass, definedNames)) {
                addValidationError(
                    `Invalid domainClass '${dimension.domainClass}' in dimension`,
                    { dimension: dimension.name, property: 'domainClass', invalidQName: dimension.domainClass }
                );
            }
            
            // Check if xbrl:conceptDomain is used on a dimension that is not xbrl:concept
            if (dimension.domainClass === 'xbrl:conceptDomain' && dimension.name !== 'xbrl:concept') {
                addValidationError(
                    `Concept domain class 'xbrl:conceptDomain' cannot be used on dimension '${dimension.name}'`,
                    { 
                        dimension: dimension.name, 
                        property: 'domainClass', 
                        domainClass: dimension.domainClass,
                        dimensionName: dimension.name,
                        errorCode: 'oimte:invalidConceptDomainClass'
                    }
                );
            }
            
            // Check if xbrl:unitDomain is used on a dimension that is not xbrl:unit
            if (dimension.domainClass === 'xbrl:unitDomain' && dimension.name !== 'xbrl:unit') {
                addValidationError(
                    `Unit domain class 'xbrl:unitDomain' cannot be used on dimension '${dimension.name}'`,
                    { 
                        dimension: dimension.name, 
                        property: 'domainClass', 
                        domainClass: dimension.domainClass,
                        dimensionName: dimension.name,
                        errorCode: 'oimte:invalidUnitDomainClass'
                    }
                );
            }
            
            // Check if xbrl:languageDomain is used on a dimension that is not xbrl:language
            if (dimension.domainClass === 'xbrl:languageDomain' && dimension.name !== 'xbrl:language') {
                addValidationError(
                    `Language domain class 'xbrl:languageDomain' cannot be used on dimension '${dimension.name}'`,
                    { 
                        dimension: dimension.name, 
                        property: 'domainClass', 
                        domainClass: dimension.domainClass,
                        dimensionName: dimension.name,
                        errorCode: 'oimte:invalidLanguageDomainClass'
                    }
                );
            }
            
            if (Array.isArray(dimension.cubeTypes)) {
                dimension.cubeTypes.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in dimension cubeTypes`,
                            { dimension: dimension.name, property: 'cubeTypes', invalidQName: qname }
                        );
                    } else {
                        const cubeTypeRefType = getObjectTypeForQName(taxonomy, qname);
                        if (cubeTypeRefType !== 'xbrl:cubeTypeObject') {
                            addValidationError(
                                `QName '${qname}' in dimension cubeTypes must reference a cubeType object, but references a '${cubeTypeRefType || 'unknown'}' object`,
                                { dimension: dimension.name, property: 'cubeTypes', invalidQName: qname, errorCode: 'oimte:invalidQNameType' }
                            );
                        }
                    }
                });
            }
        });
    }
    
    // ========== CUBE TYPES ==========
    if (Array.isArray(taxonomy.cubeTypes)) {
        taxonomy.cubeTypes.forEach(cubeType => {
            if (cubeType.baseCubeType && !isValidQName(cubeType.baseCubeType, definedNames)) {
                addValidationError(
                    `Invalid baseCubeType '${cubeType.baseCubeType}' in cubeType`,
                    { cubeType: cubeType.name, property: 'baseCubeType', invalidQName: cubeType.baseCubeType }
                );
            } else if (cubeType.baseCubeType) {
                const baseCubeTypeObjType = getObjectTypeForQName(taxonomy, cubeType.baseCubeType);
                if (baseCubeTypeObjType !== 'xbrl:cubeTypeObject') {
                    addValidationError(
                        `baseCubeType '${cubeType.baseCubeType}' in cubeType must reference a cubeType object, but references a '${baseCubeTypeObjType || 'unknown'}' object`,
                        { cubeType: cubeType.name, property: 'baseCubeType', invalidQName: cubeType.baseCubeType, errorCode: 'oimte:invalidQNameType' }
                    );
                }
            }
            
            // Validate cubeDimensionConstraints.allowed array
            if (cubeType.cubeDimensionConstraints && Array.isArray(cubeType.cubeDimensionConstraints.allowed)) {
                cubeType.cubeDimensionConstraints.allowed.forEach((constraint, idx) => {
                    if (constraint.dimensionName && !isValidQName(constraint.dimensionName, definedNames)) {
                        addValidationError(
                            `Invalid dimensionName '${constraint.dimensionName}' in cubeType cubeDimensionConstraints`,
                            { cubeType: cubeType.name, property: `cubeDimensionConstraints.allowed[${idx}].dimensionName`, invalidQName: constraint.dimensionName }
                        );
                    } else if (constraint.dimensionName) {
                        // QName exists — but it must resolve specifically to a dimension object
                        const dimRefType = getObjectTypeForQName(taxonomy, constraint.dimensionName);
                        if (dimRefType && dimRefType !== 'xbrl:dimensionObject') {
                            addValidationError(
                                `dimensionName '${constraint.dimensionName}' in cubeType '${cubeType.name}' cubeDimensionConstraints must reference a dimension object, but references a '${dimRefType}' object`,
                                { cubeType: cubeType.name, property: `cubeDimensionConstraints.allowed[${idx}].dimensionName`, invalidQName: constraint.dimensionName, errorCode: 'oimte:invalidQNameType' }
                            );
                        }
                    }
                    if (constraint.dataType && !isValidQName(constraint.dataType, definedNames)) {
                        addValidationError(
                            `Invalid dataType '${constraint.dataType}' in cubeType cubeDimensionConstraints`,
                            { cubeType: cubeType.name, property: `cubeDimensionConstraints.allowed[${idx}].dataType`, invalidQName: constraint.dataType }
                        );
                    }
                    
                    // Validate dimensionProperties arrays
                    if (constraint.dimensionProperties) {
                        if (Array.isArray(constraint.dimensionProperties.allowed)) {
                            constraint.dimensionProperties.allowed.forEach((propQName, propIdx) => {
                                if (!isValidQName(propQName, definedNames)) {
                                    addValidationError(
                                        `Invalid property QName '${propQName}' in cubeType dimension properties`,
                                        { cubeType: cubeType.name, property: `cubeDimensionConstraints.allowed[${idx}].dimensionProperties.allowed[${propIdx}]`, invalidQName: propQName }
                                    );
                                }
                            });
                        }
                        if (Array.isArray(constraint.dimensionProperties.required)) {
                            constraint.dimensionProperties.required.forEach((propQName, propIdx) => {
                                if (!isValidQName(propQName, definedNames)) {
                                    addValidationError(
                                        `Invalid property QName '${propQName}' in cubeType dimension properties`,
                                        { cubeType: cubeType.name, property: `cubeDimensionConstraints.allowed[${idx}].dimensionProperties.required[${propIdx}]`, invalidQName: propQName }
                                    );
                                }
                            });
                        }
                    }
                });
            }
            
            // Validate cubeRelationships arrays
            if (cubeType.cubeRelationships) {
                if (Array.isArray(cubeType.cubeRelationships.required)) {
                    cubeType.cubeRelationships.required.forEach((relConstraint, idx) => {
                        if (relConstraint.type && !isValidQName(relConstraint.type, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${relConstraint.type}' in cubeType cubeRelationships`,
                                { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].type`, invalidQName: relConstraint.type }
                            );
                        }
                        // Validate source and target constraints
                        if (relConstraint.source) {
                            if (relConstraint.source.qname && !isValidQName(relConstraint.source.qname, definedNames)) {
                                addValidationError(
                                    `Invalid source QName '${relConstraint.source.qname}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].source.qname`, invalidQName: relConstraint.source.qname }
                                );
                            }
                            if (relConstraint.source.objectType && !isValidQName(relConstraint.source.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid source objectType '${relConstraint.source.objectType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].source.objectType`, invalidQName: relConstraint.source.objectType }
                                );
                            }
                            if (relConstraint.source.dataType && !isValidQName(relConstraint.source.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid source dataType '${relConstraint.source.dataType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].source.dataType`, invalidQName: relConstraint.source.dataType }
                                );
                            }
                        }
                        if (relConstraint.target) {
                            if (relConstraint.target.qname && !isValidQName(relConstraint.target.qname, definedNames)) {
                                addValidationError(
                                    `Invalid target QName '${relConstraint.target.qname}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].target.qname`, invalidQName: relConstraint.target.qname }
                                );
                            }
                            if (relConstraint.target.objectType && !isValidQName(relConstraint.target.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid target objectType '${relConstraint.target.objectType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].target.objectType`, invalidQName: relConstraint.target.objectType }
                                );
                            }
                            if (relConstraint.target.dataType && !isValidQName(relConstraint.target.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid target dataType '${relConstraint.target.dataType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.required[${idx}].target.dataType`, invalidQName: relConstraint.target.dataType }
                                );
                            }
                        }
                    });
                }
                if (Array.isArray(cubeType.cubeRelationships.allowed)) {
                    cubeType.cubeRelationships.allowed.forEach((relConstraint, idx) => {
                        if (relConstraint.type && !isValidQName(relConstraint.type, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${relConstraint.type}' in cubeType cubeRelationships`,
                                { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].type`, invalidQName: relConstraint.type }
                            );
                        }
                        // Similar validation for allowed relationships source/target as above
                        if (relConstraint.source) {
                            if (relConstraint.source.qname && !isValidQName(relConstraint.source.qname, definedNames)) {
                                addValidationError(
                                    `Invalid source QName '${relConstraint.source.qname}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].source.qname`, invalidQName: relConstraint.source.qname }
                                );
                            }
                            if (relConstraint.source.objectType && !isValidQName(relConstraint.source.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid source objectType '${relConstraint.source.objectType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].source.objectType`, invalidQName: relConstraint.source.objectType }
                                );
                            }
                            if (relConstraint.source.dataType && !isValidQName(relConstraint.source.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid source dataType '${relConstraint.source.dataType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].source.dataType`, invalidQName: relConstraint.source.dataType }
                                );
                            }
                        }
                        if (relConstraint.target) {
                            if (relConstraint.target.qname && !isValidQName(relConstraint.target.qname, definedNames)) {
                                addValidationError(
                                    `Invalid target QName '${relConstraint.target.qname}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].target.qname`, invalidQName: relConstraint.target.qname }
                                );
                            }
                            if (relConstraint.target.objectType && !isValidQName(relConstraint.target.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid target objectType '${relConstraint.target.objectType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].target.objectType`, invalidQName: relConstraint.target.objectType }
                                );
                            }
                            if (relConstraint.target.dataType && !isValidQName(relConstraint.target.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid target dataType '${relConstraint.target.dataType}' in cubeType relationship constraint`,
                                    { cubeType: cubeType.name, property: `cubeRelationships.allowed[${idx}].target.dataType`, invalidQName: relConstraint.target.dataType }
                                );
                            }
                        }
                    });
                }
            }
            
            // Validate cubeProperties arrays
            if (cubeType.cubeProperties) {
                if (Array.isArray(cubeType.cubeProperties.required)) {
                    cubeType.cubeProperties.required.forEach((propQName, propIdx) => {
                        if (!isValidQName(propQName, definedNames)) {
                            addValidationError(
                                `Invalid property QName '${propQName}' in cubeType properties`,
                                { cubeType: cubeType.name, property: `cubeProperties.required[${propIdx}]`, invalidQName: propQName }
                            );
                        }
                    });
                }
                if (Array.isArray(cubeType.cubeProperties.allowed)) {
                    cubeType.cubeProperties.allowed.forEach((propQName, propIdx) => {
                        if (!isValidQName(propQName, definedNames)) {
                            addValidationError(
                                `Invalid property QName '${propQName}' in cubeType properties`,
                                { cubeType: cubeType.name, property: `cubeProperties.allowed[${propIdx}]`, invalidQName: propQName }
                            );
                        }
                    });
                }
            }
        });
    }
    
    // ========== DOMAINS ==========
    if (Array.isArray(taxonomy.domains)) {
        taxonomy.domains.forEach(domain => {
            if (domain.root && !isValidQName(domain.root, definedNames)) {
                addValidationError(
                    `Invalid root '${domain.root}' in domain`,
                    { domain: domain.name, property: 'root', invalidQName: domain.root }
                );
            }
            if (domain.extendTargetName && !isValidQName(domain.extendTargetName, definedNames)) {
                addValidationError(
                    `Invalid extendTargetName '${domain.extendTargetName}' in domain`,
                    { domain: domain.name, property: 'extendTargetName', invalidQName: domain.extendTargetName, persistent: true }
                );
            } else if (domain.extendTargetName && isValidQName(domain.extendTargetName, definedNames)) {
                const extendType = getObjectTypeForQName(taxonomy, domain.extendTargetName);
                if (extendType !== 'xbrl:domainObject') {
                    addValidationError(
                        `extendTargetName '${domain.extendTargetName}' in domain must reference a domain object, but references a '${extendType || 'unknown'}' object`,
                        {
                            domain: domain.extendTargetName,
                            property: 'extendTargetName',
                            invalidQName: domain.extendTargetName,
                            errorCode: 'oimte:invalidQNameType',
                            persistent: true
                        }
                    );
                }
            }
            if (Array.isArray(domain.relationships)) {
                domain.relationships.forEach((rel, idx) => {
                    if (rel.source && !isValidQName(rel.source, definedNames)) {
                        addValidationError(
                            `Invalid source '${rel.source}' in domain relationship`,
                            { domain: domain.name, property: `relationships[${idx}].source`, invalidQName: rel.source }
                        );
                    }
                    if (rel.target && !isValidQName(rel.target, definedNames)) {
                        addValidationError(
                            `Invalid target '${rel.target}' in domain relationship`,
                            { domain: domain.name, property: `relationships[${idx}].target`, invalidQName: rel.target }
                        );
                    }
                    // Validate that the target object resolves to an allowed object type for domain relationships
                    if (rel.target && isValidQName(rel.target, definedNames)) {
                        const targetType = getObjectTypeForQName(taxonomy, rel.target);
                        const allowedTargetTypes = new Set([
                            'xbrl:conceptObject',
                            'xbrl:memberObject',
                            'xbrl:abstractObject',
                            'xbrl:entityObject',
                            'xbrl:unitObject'
                        ]);

                        if (!targetType || !allowedTargetTypes.has(targetType)) {
                            addValidationError(
                                `Invalid domain relationship target '${rel.target}' — target must be a concept, member, abstract, entity or unit object`,
                                {
                                    domain: domain.name,
                                    property: `relationships[${idx}].target`,
                                    invalidQName: rel.target,
                                    resolvedObjectType: targetType || null,
                                    errorCode: 'oimte:invalidDomainRelationshipTarget'
                                }
                            );
                        }
                    }
                });
            }
        });
    }
    
    // ========== REQUIRED PROPERTY VALIDATION ==========
    // Check for missing required properties on taxonomy objects
    const requiredProperties = {
        documentInfo: ['documentType', 'namespaces'],
        taxonomy: ['name'],
        concepts: ['name', 'dataType', 'periodType'],
        dimensions: ['name', 'domainClass'],
        members: ['name'],
        abstracts: ['name'],
        domainClasses: ['name'],
        units: ['name'],
        entities: ['name'],
        cubes: ['name', 'cubeDimensions'],
        cubeDimensions: ['dimensionName'],
        domains: ['name', 'root'],
        relationships: ['source', 'target'],
        networks: ['name', 'relationshipTypeName'],
        groups: ['name'],
        groupContents: ['groupName', 'relatedNames'],
        groupTree: ['name'],
        dataTypes: ['name', 'baseType'],
        collections: ['name', 'dataTypesAllowed'],
        propertyTypes: ['name', 'dataType'],
        labelTypes: ['name'],
        referenceTypes: ['name'],
        relationshipTypes: ['name', 'cycles'],
        cubeTypes: ['name'],
        labels: ['relatedName', 'language', 'labelType', 'value'],
        references: ['name', 'referenceType'],
        facts: ['name', 'factDimensions'],
        footnotes: ['name', 'content', 'language'],
        properties: ['property', 'value']
    };
    
    // Validate documentInfo
    if (taxonomy.documentInfo) {
        requiredProperties.documentInfo.forEach(prop => {
            if (!taxonomy.documentInfo.hasOwnProperty(prop)) {
                addValidationError(
                    `Missing required property '${prop}' in documentInfo`,
                    { 
                        objectType: 'documentInfo',
                        property: prop,
                        errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                        propertyName: prop
                    }
                );
            }
        });
    }
    
    // Validate taxonomy object
    if (taxonomy) {
        requiredProperties.taxonomy.forEach(prop => {
            if (!taxonomy.hasOwnProperty(prop)) {
                addValidationError(
                    `Missing required property '${prop}' in taxonomy object`,
                    { 
                        objectType: 'taxonomy',
                        property: prop,
                        errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                        propertyName: prop
                    }
                );
            }
        });
    }
    
    // Validate groupTree (single object, not array)
    if (taxonomy.groupTree) {
        requiredProperties.groupTree.forEach(prop => {
            if (!taxonomy.groupTree.hasOwnProperty(prop)) {
                addValidationError(
                    `Missing required property '${prop}' in groupTree`,
                    { 
                        objectType: 'groupTree',
                        property: prop,
                        errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                        propertyName: prop
                    }
                );
            }
        });
    }
    
    // Validate array-based objects
    Object.keys(requiredProperties).forEach(arrayName => {
        if (arrayName === 'documentInfo' || arrayName === 'taxonomy' || arrayName === 'groupTree' || arrayName === 'cubeDimensions' || arrayName === 'relationships' || arrayName === 'properties') {
            return; // Skip documentInfo, taxonomy, groupTree (handled above), cubeDimensions, relationships, and properties (nested arrays)
        }
        
        if (Array.isArray(taxonomy[arrayName])) {
            taxonomy[arrayName].forEach((obj, idx) => {
                requiredProperties[arrayName].forEach(prop => {
                    // Special handling for objects that can use either 'name' or 'extendTargetName'
                    // When extendTargetName is present, several properties become non-required.
                    // This mirrors the oneOf pattern in the JSON schema for each object type.
                    const extendTargetNameExemptions = {
                        domains:        ['name', 'root'],
                        networks:       ['name', 'relationshipTypeName'],
                        facts:          ['name', 'factDimensions'],
                        references:     ['name'],
                        cubes:          ['name'],
                        tableTemplates: ['name'],
                    };
                    if (obj.hasOwnProperty('extendTargetName') &&
                        extendTargetNameExemptions[arrayName] &&
                        extendTargetNameExemptions[arrayName].includes(prop)) {
                        return;
                    }
                    
                    if (!obj.hasOwnProperty(prop)) {
                        const objectIdentifier = obj.name || obj.extendTargetName || obj.relatedName || `${arrayName}[${idx}]`;
                        addValidationError(
                            `Missing required property '${prop}' in ${arrayName} object '${objectIdentifier}'`,
                            { 
                                objectType: arrayName,
                                objectIndex: idx,
                                objectName: objectIdentifier,
                                property: prop,
                                errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                                propertyName: prop
                            }
                        );
                    }
                });
            });
        }
    });
    
    // Validate cubeDimensions (nested in cubes)
    if (Array.isArray(taxonomy.cubes)) {
        taxonomy.cubes.forEach((cube, cubeIdx) => {
            if (Array.isArray(cube.cubeDimensions)) {
                cube.cubeDimensions.forEach((cubeDim, dimIdx) => {
                    requiredProperties.cubeDimensions.forEach(prop => {
                        if (!cubeDim.hasOwnProperty(prop)) {
                            const cubeName = cube.name || `cubes[${cubeIdx}]`;
                            const dimensionIdentifier = cubeDim.dimensionName || `cubeDimensions[${dimIdx}]`;
                            addValidationError(
                                `Missing required property '${prop}' in cube '${cubeName}' dimension '${dimensionIdentifier}'`,
                                { 
                                    objectType: 'cubeDimensions',
                                    cube: cubeName,
                                    dimensionIndex: dimIdx,
                                    dimensionName: dimensionIdentifier,
                                    property: prop,
                                    errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                                    propertyName: prop
                                }
                            );
                        }
                    });
                });
            }
        });
    }
    
    // Validate relationships (nested in domains and networks)
    if (Array.isArray(taxonomy.domains)) {
        taxonomy.domains.forEach((domain, domainIdx) => {
            if (Array.isArray(domain.relationships)) {
                domain.relationships.forEach((rel, relIdx) => {
                    requiredProperties.relationships.forEach(prop => {
                        if (!rel.hasOwnProperty(prop)) {
                            const domainName = domain.name || `domains[${domainIdx}]`;
                            const relIdentifier = rel.source || rel.target || `relationships[${relIdx}]`;
                            addValidationError(
                                `Missing required property '${prop}' in domain '${domainName}' relationship '${relIdentifier}'`,
                                { 
                                    objectType: 'relationships',
                                    domain: domainName,
                                    relationshipIndex: relIdx,
                                    relationshipIdentifier: relIdentifier,
                                    property: prop,
                                    errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                                    propertyName: prop
                                }
                            );
                        }
                    });
                });
            }
        });
    }
    
    if (Array.isArray(taxonomy.networks)) {
        taxonomy.networks.forEach((network, networkIdx) => {
            if (Array.isArray(network.relationships)) {
                network.relationships.forEach((rel, relIdx) => {
                    requiredProperties.relationships.forEach(prop => {
                        if (!rel.hasOwnProperty(prop)) {
                            const networkName = network.name || `networks[${networkIdx}]`;
                            const relIdentifier = rel.source || rel.target || `relationships[${relIdx}]`;
                            addValidationError(
                                `Missing required property '${prop}' in network '${networkName}' relationship '${relIdentifier}'`,
                                { 
                                    objectType: 'relationships',
                                    network: networkName,
                                    relationshipIndex: relIdx,
                                    relationshipIdentifier: relIdentifier,
                                    property: prop,
                                    errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                                    propertyName: prop
                                }
                            );
                        }
                    });
                });
            }
        });
    }
    
    // ========== INVALID PROPERTY VALIDATION ==========
    // Check for properties that are not defined in the OIM Taxonomy schema
    const allowedProperties = {
        documentInfo: ['documentType', 'namespaces', 'documentNamespace', 'importMapping', 'description', 'sourceMapping'],
        taxonomy: ['name', 'frameworkName', 'version', 'modelForm', 'modelType', 'importedTaxonomies', 'finalTaxonomy', 'propertyTypes', 'modelTypes', 'abstracts', 'members', 'concepts', 'cubes', 'dimensions', 'domains', 'domainClasses', 'networks', 'entities', 'units', 'groups', 'groupContents', 'groupTree', 'relationshipTypes', 'labels', 'references', 'facts', 'footnotes', 'dataTypes', 'collections', 'cubeTypes', 'labelTypes', 'referenceTypes', 'transforms', 'properties', 'layouts', 'factMaps', 'factSources', 'tableTemplates', 'jsonTemplates', 'xmlTemplates'],
        concepts: ['name', 'dataType', 'periodType', 'nillable', 'enumerationDomain', 'properties'],
        dimensions: ['name', 'domainClass', 'cubeTypes', 'properties'],
        members: ['name', 'domainClasses', 'properties'],
        abstracts: ['name', 'properties'],
        domainClasses: ['name', 'allowedDomainItems', 'properties'],
        units: ['name', 'dataType', 'compositeUnitRepresentation', 'properties'],
        entities: ['name', 'properties'],
        cubes: ['name', 'cubeDimensions', 'cubeType', 'cubeNetworks', 'excludeCubes', 'requiredCubes', 'properties', 'extendTargetName'],
        cubeDimensions: ['dimensionName', 'domainName', 'domainDataType', 'typedSort', 'allowDomainFacts', 'periodConstraints'],
        domains: ['name', 'root', 'relationships', 'extendTargetName', 'completeDomain', 'properties'],
        relationships: ['source', 'target', 'order', 'properties'],
        networks: ['name', 'relationshipTypeName', 'roots', 'relationships', 'extendTargetName', 'properties'],
        groups: ['name', 'groupURI', 'properties'],
        groupContents: ['groupName', 'relatedNames'],
        groupTree: ['name', 'relationships'],
        dataTypes: ['name', 'baseType', 'enumeration', 'openEnumeration', 'minInclusive', 'maxInclusive', 'minExclusive', 'maxExclusive', 'totalDigits', 'fractionDigits', 'length', 'minLength', 'maxLength', 'whiteSpace', 'patterns', 'unitType', 'mapType', 'allowedObjects'],
        collections: ['name', 'dataTypesAllowed', 'uniqueValues', 'orderedValues', 'maxItems', 'minItems', 'properties'],
        propertyTypes: ['name', 'dataType', 'enumerationDomain', 'definitional', 'allowedObjects', 'allowedAsLinkProperty'],
        labelTypes: ['name', 'uri', 'dataType', 'allowedObjects'],
        referenceTypes: ['name', 'uri', 'allowedObjects', 'orderedProperties', 'requiredProperties'],
        relationshipTypes: ['name', 'uri', 'cycles', 'allowedLinkProperties', 'requiredLinkProperties', 'sourceObjects', 'targetObjects', 'constraints'],
        cubeTypes: ['name', 'baseCubeType', 'coreDimensions', 'cubeDimensionConstraints', 'cubeRelationships', 'cubeProperties'],
        labels: ['relatedName', 'language', 'labelType', 'value'],
        references: ['name', 'extendTargetName', 'relatedNames', 'referenceType', 'language', 'properties'],
        facts: ['name', 'extendTargetName', 'factValues', 'factDimensions', 'properties'],
        footnotes: ['name', 'content', 'language'],
        transforms: ['name', 'inputDataType', 'outputDataType'],
        factMaps: ['name', 'templateName', 'cubeName'],
        factSources: ['name', 'factMapName', 'namespaceMaps', 'factNames', 'hash', 'metadata', 'urlModelRedirect', 'facts', 'properties'],
        tableTemplates: ['name', 'rowIdColumn', 'columns', 'factDimensions', 'decimals', 'extendTargetName'],
        jsonTemplates: ['name', 'factDimensions', 'valuePath', 'decimals'],
        xmlTemplates: ['name', 'factDimensions', 'valuePath', 'decimals'],
        urlModelRedirect: ['fromModel', 'toModel'],
        jsonTemplateMap: ['factDimensions', 'valuePath', 'decimals'],
        xmlTemplateMap: ['factDimensions', 'valuePath', 'decimals'],
        columns: ['columnName', 'factDimensions', 'propertyGroups', 'decimals', 'transformation', 'order'],
        properties: ['property', 'value'],
        cubeDimensionConstraints: ['allowed', 'closed'],
        dimensionConstraint: ['dimensionName', 'type', 'dataType', 'required', 'dimensionProperties'],
        dimensionProperties: ['allowed', 'required'],
        cubeRelationships: ['required', 'allowed'],
        relationshipConstraint: ['type', 'source', 'target'],
        relationshipSource: ['qname', 'objectType', 'dataType'],
        relationshipTarget: ['qname', 'objectType', 'dataType'],
        cubeProperties: ['required', 'allowed'],
        layouts: ['name', 'xbrlModelName', 'dataTables', 'tableConstruction'],
        dataTables: ['name', 'tableType', 'cubeName', 'xAxis', 'yAxis', 'zAxis', 'showRefs', 'tablePoints']
    };
    
    // Validate documentInfo
    if (taxonomy.documentInfo) {
        const allowedProps = new Set(allowedProperties.documentInfo);
        Object.keys(taxonomy.documentInfo).forEach(prop => {
            if (!allowedProps.has(prop)) {
                addValidationError(
                    `Invalid property '${prop}' defined in documentInfo`,
                    { 
                        objectType: 'documentInfo',
                        objectName: 'documentInfo',
                        propertyName: prop,
                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                    }
                );
            }
        });
    }
    
    // Validate taxonomy object
    if (taxonomy) {
        const allowedProps = new Set(allowedProperties.taxonomy);
        Object.keys(taxonomy).forEach(prop => {
            if (!allowedProps.has(prop)) {
                addValidationError(
                    `Invalid property '${prop}' defined in taxonomy object`,
                    { 
                        objectType: 'taxonomy',
                        objectName: taxonomy.name || 'taxonomy',
                        propertyName: prop,
                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                    }
                );
            }
        });
    }
    
    // Validate groupTree (single object, not array)
    if (taxonomy.groupTree) {
        const allowedProps = new Set(allowedProperties.groupTree);
        Object.keys(taxonomy.groupTree).forEach(prop => {
            if (!allowedProps.has(prop)) {
                addValidationError(
                    `Invalid property '${prop}' defined in groupTree`,
                    { 
                        objectType: 'groupTree',
                        objectName: taxonomy.groupTree.name || 'groupTree',
                        propertyName: prop,
                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                    }
                );
            }
        });
    }
    
    // Validate array-based objects
    Object.keys(allowedProperties).forEach(arrayName => {
        if (arrayName === 'documentInfo' || arrayName === 'taxonomy' || arrayName === 'groupTree' || arrayName === 'cubeDimensions' || arrayName === 'relationships' || arrayName === 'properties' || arrayName === 'columns' || arrayName === 'cubeDimensionConstraints' || arrayName === 'dimensionConstraint' || arrayName === 'dimensionProperties' || arrayName === 'cubeRelationships' || arrayName === 'relationshipConstraint' || arrayName === 'relationshipSource' || arrayName === 'relationshipTarget' || arrayName === 'cubeProperties') {
            return; // Skip documentInfo, taxonomy, groupTree (handled above), and nested structures (handled separately)
        }
        
        if (Array.isArray(taxonomy[arrayName])) {
            const allowedProps = new Set(allowedProperties[arrayName]);
            taxonomy[arrayName].forEach((obj, idx) => {
                Object.keys(obj).forEach(prop => {
                    if (!allowedProps.has(prop)) {
                        const objectIdentifier = obj.name || obj.relatedName || `${arrayName}[${idx}]`;
                        addValidationError(
                            `Invalid property '${prop}' defined in ${arrayName} object '${objectIdentifier}'`,
                            { 
                                objectType: arrayName,
                                objectName: objectIdentifier,
                                propertyName: prop,
                                errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                            }
                        );
                    }
                });
            });
        }
    });
    
    // Validate cubeDimensions (nested in cubes)
    if (Array.isArray(taxonomy.cubes)) {
        const allowedProps = new Set(allowedProperties.cubeDimensions);
        taxonomy.cubes.forEach((cube, cubeIdx) => {
            if (Array.isArray(cube.cubeDimensions)) {
                cube.cubeDimensions.forEach((cubeDim, dimIdx) => {
                    Object.keys(cubeDim).forEach(prop => {
                        if (!allowedProps.has(prop)) {
                            const cubeName = cube.name || `cubes[${cubeIdx}]`;
                            const dimensionIdentifier = cubeDim.dimensionName || `cubeDimensions[${dimIdx}]`;
                            addValidationError(
                                `Invalid property '${prop}' defined in cube '${cubeName}' dimension '${dimensionIdentifier}'`,
                                { 
                                    objectType: 'cubeDimensions',
                                    objectName: `${cubeName}.${dimensionIdentifier}`,
                                    propertyName: prop,
                                    errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                }
                            );
                        }
                    });
                });
            }
        });
    }

    // Validate factMaps array
    if (Array.isArray(taxonomy.factMaps)) {
        const allowedFactMapProps = new Set(allowedProperties.factMaps);
        taxonomy.factMaps.forEach((factMap, mapIdx) => {
            Object.keys(factMap).forEach(prop => {
                if (!allowedFactMapProps.has(prop)) {
                    const mapName = factMap.name || `factMaps[${mapIdx}]`;
                    addValidationError(
                        `Invalid property '${prop}' defined in factMap '${mapName}'`,
                        { 
                            objectType: 'factMaps',
                            objectName: mapName,
                            propertyName: prop,
                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                        }
                    );
                }
            });
        });
    }

    // Validate tableTemplates array
    if (Array.isArray(taxonomy.tableTemplates)) {
        const allowedTemplateProps = new Set(allowedProperties.tableTemplates);
        taxonomy.tableTemplates.forEach((template, templateIdx) => {
            Object.keys(template).forEach(prop => {
                if (!allowedTemplateProps.has(prop)) {
                    const templateName = template.name || `tableTemplates[${templateIdx}]`;
                    addValidationError(
                        `Invalid property '${prop}' defined in tableTemplate '${templateName}'`,
                        { 
                            objectType: 'tableTemplates',
                            objectName: templateName,
                            propertyName: prop,
                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                        }
                    );
                }
            });
            
            // Validate columns (nested in tableTemplates)
            if (Array.isArray(template.columns)) {
                const allowedColProps = new Set(allowedProperties.columns);
                template.columns.forEach((col, colIdx) => {
                    Object.keys(col).forEach(prop => {
                        if (!allowedColProps.has(prop)) {
                            const templateName = template.name || `tableTemplates[${templateIdx}]`;
                            const colIdentifier = col.columnName || `columns[${colIdx}]`;
                            addValidationError(
                                `Invalid property '${prop}' defined in tableTemplate '${templateName}' column '${colIdentifier}'`,
                                { 
                                    objectType: 'columns',
                                    objectName: `${templateName}.${colIdentifier}`,
                                    propertyName: prop,
                                    errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                }
                            );
                        }
                    });
                });
            }
            // Validate extendTargetName reference
            if (template.extendTargetName && !isValidQName(template.extendTargetName, definedNames)) {
                addValidationError(
                    `Invalid extendTargetName '${template.extendTargetName}' in tableTemplate`,
                    { property: `tableTemplates[${templateIdx}].extendTargetName`, invalidQName: template.extendTargetName, persistent: true }
                );
            } else if (template.extendTargetName && isValidQName(template.extendTargetName, definedNames)) {
                const extendType = getObjectTypeForQName(taxonomy, template.extendTargetName);
                if (extendType !== 'xbrl:tableTemplateObject') {
                    addValidationError(
                        `extendTargetName '${template.extendTargetName}' in tableTemplate must reference a tableTemplate object, but references a '${extendType || 'unknown'}' object`,
                        {
                            property: `tableTemplates[${templateIdx}].extendTargetName`,
                            invalidQName: template.extendTargetName,
                            errorCode: 'oimte:invalidQNameType',
                            persistent: true
                        }
                    );
                }
            }
        });
    }
    
    // Validate factSources array
    if (Array.isArray(taxonomy.factSources)) {
        const allowedFactSourceProps = new Set(allowedProperties.factSources);
        taxonomy.factSources.forEach((factSource, sourceIdx) => {
            Object.keys(factSource).forEach(prop => {
                if (!allowedFactSourceProps.has(prop)) {
                    const sourceName = factSource.name || `factSources[${sourceIdx}]`;
                    addValidationError(
                        `Invalid property '${prop}' defined in factSource '${sourceName}'`,
                        { 
                            objectType: 'factSources',
                            objectName: sourceName,
                            propertyName: prop,
                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                        }
                    );
                }
            });
        });
    }
    
    // Validate cubeTypes nested structures
    if (Array.isArray(taxonomy.cubeTypes)) {
        taxonomy.cubeTypes.forEach((cubeType, cubeTypeIdx) => {
            const cubeTypeName = cubeType.name || `cubeTypes[${cubeTypeIdx}]`;
            
            // Validate cubeDimensionConstraints properties
            if (cubeType.cubeDimensionConstraints) {
                const allowedConstraintsProps = new Set(allowedProperties.cubeDimensionConstraints);
                Object.keys(cubeType.cubeDimensionConstraints).forEach(prop => {
                    if (!allowedConstraintsProps.has(prop)) {
                        addValidationError(
                            `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeDimensionConstraints`,
                            { 
                                objectType: 'cubeDimensionConstraints',
                                objectName: `${cubeTypeName}.cubeDimensionConstraints`,
                                propertyName: prop,
                                errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                            }
                        );
                    }
                });
                
                // Validate cubeDimensionConstraints.allowed items
                if (Array.isArray(cubeType.cubeDimensionConstraints.allowed)) {
                    const allowedDimConstraintProps = new Set(allowedProperties.dimensionConstraint);
                    cubeType.cubeDimensionConstraints.allowed.forEach((dimConstraint, dimIdx) => {
                        Object.keys(dimConstraint).forEach(prop => {
                            if (!allowedDimConstraintProps.has(prop)) {
                                const dimName = dimConstraint.dimensionName || `allowed[${dimIdx}]`;
                                addValidationError(
                                    `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeDimensionConstraints.allowed item '${dimName}'`,
                                    { 
                                        objectType: 'dimensionConstraint',
                                        objectName: `${cubeTypeName}.cubeDimensionConstraints.allowed.${dimName}`,
                                        propertyName: prop,
                                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                    }
                                );
                            }
                        });
                        
                        // Validate dimensionProperties if present
                        if (dimConstraint.dimensionProperties) {
                            const allowedDimPropsProps = new Set(allowedProperties.dimensionProperties);
                            Object.keys(dimConstraint.dimensionProperties).forEach(prop => {
                                if (!allowedDimPropsProps.has(prop)) {
                                    const dimName = dimConstraint.dimensionName || `allowed[${dimIdx}]`;
                                    addValidationError(
                                        `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' dimension '${dimName}' dimensionProperties`,
                                        { 
                                            objectType: 'dimensionProperties',
                                            objectName: `${cubeTypeName}.cubeDimensionConstraints.allowed.${dimName}.dimensionProperties`,
                                            propertyName: prop,
                                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                        }
                                    );
                                }
                            });
                        }
                    });
                }
            }
            
            // Validate cubeRelationships properties
            if (cubeType.cubeRelationships) {
                const allowedRelProps = new Set(allowedProperties.cubeRelationships);
                Object.keys(cubeType.cubeRelationships).forEach(prop => {
                    if (!allowedRelProps.has(prop)) {
                        addValidationError(
                            `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships`,
                            { 
                                objectType: 'cubeRelationships',
                                objectName: `${cubeTypeName}.cubeRelationships`,
                                propertyName: prop,
                                errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                            }
                        );
                    }
                });
                
                // Validate cubeRelationships.required items
                if (Array.isArray(cubeType.cubeRelationships.required)) {
                    const allowedRelConstraintProps = new Set(allowedProperties.relationshipConstraint);
                    const allowedSourceProps = new Set(allowedProperties.relationshipSource);
                    const allowedTargetProps = new Set(allowedProperties.relationshipTarget);
                    
                    cubeType.cubeRelationships.required.forEach((relConstraint, relIdx) => {
                        Object.keys(relConstraint).forEach(prop => {
                            if (!allowedRelConstraintProps.has(prop)) {
                                const relType = relConstraint.type || `required[${relIdx}]`;
                                addValidationError(
                                    `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.required item '${relType}'`,
                                    { 
                                        objectType: 'relationshipConstraint',
                                        objectName: `${cubeTypeName}.cubeRelationships.required.${relType}`,
                                        propertyName: prop,
                                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                    }
                                );
                            }
                        });
                        
                        // Validate source object if present
                        if (relConstraint.source) {
                            Object.keys(relConstraint.source).forEach(prop => {
                                if (!allowedSourceProps.has(prop)) {
                                    const relType = relConstraint.type || `required[${relIdx}]`;
                                    addValidationError(
                                        `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.required '${relType}' source`,
                                        { 
                                            objectType: 'relationshipSource',
                                            objectName: `${cubeTypeName}.cubeRelationships.required.${relType}.source`,
                                            propertyName: prop,
                                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                        }
                                    );
                                }
                            });
                        }
                        
                        // Validate target object if present
                        if (relConstraint.target) {
                            Object.keys(relConstraint.target).forEach(prop => {
                                if (!allowedTargetProps.has(prop)) {
                                    const relType = relConstraint.type || `required[${relIdx}]`;
                                    addValidationError(
                                        `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.required '${relType}' target`,
                                        { 
                                            objectType: 'relationshipTarget',
                                            objectName: `${cubeTypeName}.cubeRelationships.required.${relType}.target`,
                                            propertyName: prop,
                                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                        }
                                    );
                                }
                            });
                        }
                    });
                }
                
                // Validate cubeRelationships.allowed items
                if (Array.isArray(cubeType.cubeRelationships.allowed)) {
                    const allowedRelConstraintProps = new Set(allowedProperties.relationshipConstraint);
                    const allowedSourceProps = new Set(allowedProperties.relationshipSource);
                    const allowedTargetProps = new Set(allowedProperties.relationshipTarget);
                    
                    cubeType.cubeRelationships.allowed.forEach((relConstraint, relIdx) => {
                        Object.keys(relConstraint).forEach(prop => {
                            if (!allowedRelConstraintProps.has(prop)) {
                                const relType = relConstraint.type || `allowed[${relIdx}]`;
                                addValidationError(
                                    `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.allowed item '${relType}'`,
                                    { 
                                        objectType: 'relationshipConstraint',
                                        objectName: `${cubeTypeName}.cubeRelationships.allowed.${relType}`,
                                        propertyName: prop,
                                        errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                    }
                                );
                            }
                        });
                        
                        // Validate source object if present
                        if (relConstraint.source) {
                            Object.keys(relConstraint.source).forEach(prop => {
                                if (!allowedSourceProps.has(prop)) {
                                    const relType = relConstraint.type || `allowed[${relIdx}]`;
                                    addValidationError(
                                        `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.allowed '${relType}' source`,
                                        { 
                                            objectType: 'relationshipSource',
                                            objectName: `${cubeTypeName}.cubeRelationships.allowed.${relType}.source`,
                                            propertyName: prop,
                                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                        }
                                    );
                                }
                            });
                        }
                        
                        // Validate target object if present
                        if (relConstraint.target) {
                            Object.keys(relConstraint.target).forEach(prop => {
                                if (!allowedTargetProps.has(prop)) {
                                    const relType = relConstraint.type || `allowed[${relIdx}]`;
                                    addValidationError(
                                        `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeRelationships.allowed '${relType}' target`,
                                        { 
                                            objectType: 'relationshipTarget',
                                            objectName: `${cubeTypeName}.cubeRelationships.allowed.${relType}.target`,
                                            propertyName: prop,
                                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                        }
                                    );
                                }
                            });
                        }
                    });
                }
            }
            
            // Validate cubeProperties properties
            if (cubeType.cubeProperties) {
                const allowedCubePropsProps = new Set(allowedProperties.cubeProperties);
                Object.keys(cubeType.cubeProperties).forEach(prop => {
                    if (!allowedCubePropsProps.has(prop)) {
                        addValidationError(
                            `Invalid property '${prop}' defined in cubeType '${cubeTypeName}' cubeProperties`,
                            { 
                                objectType: 'cubeProperties',
                                objectName: `${cubeTypeName}.cubeProperties`,
                                propertyName: prop,
                                errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                            }
                        );
                    }
                });
            }
        });
    }
    
    // Validate relationships (nested in domains and networks)
    if (Array.isArray(taxonomy.domains)) {
        const allowedProps = new Set(allowedProperties.relationships);
        taxonomy.domains.forEach((domain, domainIdx) => {
            if (Array.isArray(domain.relationships)) {
                domain.relationships.forEach((rel, relIdx) => {
                    Object.keys(rel).forEach(prop => {
                        if (!allowedProps.has(prop)) {
                            const domainName = domain.name || `domains[${domainIdx}]`;
                            const relIdentifier = rel.source || rel.target || `relationships[${relIdx}]`;
                            addValidationError(
                                `Invalid property '${prop}' defined in domain '${domainName}' relationship '${relIdentifier}'`,
                                { 
                                    objectType: 'relationships',
                                    objectName: `${domainName}.${relIdentifier}`,
                                    propertyName: prop,
                                    errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                }
                            );
                        }
                    });
                });
            }
        });
    }
    
    if (Array.isArray(taxonomy.networks)) {
        const allowedProps = new Set(allowedProperties.relationships);
        taxonomy.networks.forEach((network, networkIdx) => {
            if (Array.isArray(network.relationships)) {
                network.relationships.forEach((rel, relIdx) => {
                    Object.keys(rel).forEach(prop => {
                        if (!allowedProps.has(prop)) {
                            const networkName = network.name || `networks[${networkIdx}]`;
                            const relIdentifier = rel.source || rel.target || `relationships[${relIdx}]`;
                            addValidationError(
                                `Invalid property '${prop}' defined in network '${networkName}' relationship '${relIdentifier}'`,
                                { 
                                    objectType: 'relationships',
                                    objectName: `${networkName}.${relIdentifier}`,
                                    propertyName: prop,
                                    errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                }
                            );
                        }
                    });
                });
            }
        });
    }

    // Validate layouts (array at taxonomy level)
    if (Array.isArray(taxonomy.layouts)) {
        const allowedLayoutProps = new Set(allowedProperties.layouts);
        taxonomy.layouts.forEach((layout, layoutIdx) => {
            Object.keys(layout).forEach(prop => {
                if (!allowedLayoutProps.has(prop)) {
                    const layoutName = layout.name || `layouts[${layoutIdx}]`;
                    addValidationError(
                        `Invalid property '${prop}' defined in layout '${layoutName}'`,
                        { 
                            objectType: 'layouts',
                            objectName: layoutName,
                            propertyName: prop,
                            errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                        }
                    );
                }
            });
            
            // Validate dataTables (nested in layouts)
            if (Array.isArray(layout.dataTables)) {
                const allowedDataTableProps = new Set(allowedProperties.dataTables);
                layout.dataTables.forEach((dataTable, dtIdx) => {
                    Object.keys(dataTable).forEach(prop => {
                        if (!allowedDataTableProps.has(prop)) {
                            const layoutName = layout.name || `layouts[${layoutIdx}]`;
                            const dtName = dataTable.name || `dataTables[${dtIdx}]`;
                            addValidationError(
                                `Invalid property '${prop}' defined in layout '${layoutName}' dataTable '${dtName}'`,
                                { 
                                    objectType: 'dataTables',
                                    objectName: `${layoutName}.${dtName}`,
                                    propertyName: prop,
                                    errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                                }
                            );
                        }
                    });
                });
            }
        });
    }

    // ========== DOMAIN CLASS TARGET VALIDATION ==========
    // Check if any domainClass is used as a target in domain relationships
    if (Array.isArray(taxonomy.domainClasses) && Array.isArray(taxonomy.domains)) {
        const domainClassNames = new Set(taxonomy.domainClasses.map(dr => dr.name));
        
        taxonomy.domains.forEach(domain => {
            if (Array.isArray(domain.relationships)) {
                domain.relationships.forEach((rel, idx) => {
                    if (rel.target && domainClassNames.has(rel.target)) {
                        addValidationError(
                            `Domain class '${rel.target}' cannot be used as a target in domain relationship`,
                            { 
                                domain: domain.name, 
                                property: `relationships[${idx}].target`, 
                                invalidQName: rel.target,
                                errorCode: 'oimte:invalidDomainClassTarget',
                                domainClass: rel.target
                            }
                        );
                    }
                });
            }
        });
    }
    
    // ========== NETWORKS ==========
    // Build a map of relationship type name -> { sourceObjects: Set, targetObjects: Set }
    // covering both built-in types (merged from xbrlSpec.json) and user-defined types.
    const relationshipTypeConstraints = new Map();
    if (Array.isArray(taxonomy.relationshipTypes)) {
        taxonomy.relationshipTypes.forEach(rt => {
            if (rt.name) {
                const src = Array.isArray(rt.sourceObjects) && rt.sourceObjects.length > 0
                    ? new Set(rt.sourceObjects) : null;
                const tgt = Array.isArray(rt.targetObjects) && rt.targetObjects.length > 0
                    ? new Set(rt.targetObjects) : null;
                if (src || tgt) {
                    relationshipTypeConstraints.set(rt.name, { sourceObjects: src, targetObjects: tgt });
                }
            }
        });
    }

    if (Array.isArray(taxonomy.networks)) {
        taxonomy.networks.forEach(network => {
            if (network.relationshipTypeName && !isValidQName(network.relationshipTypeName, definedNames)) {
                addValidationError(
                    `Invalid relationshipTypeName '${network.relationshipTypeName}' in network`,
                    { network: network.name, property: 'relationshipTypeName', invalidQName: network.relationshipTypeName }
                );
            }
            if (network.extendTargetName && !isValidQName(network.extendTargetName, definedNames)) {
                addValidationError(
                    `Invalid extendTargetName '${network.extendTargetName}' in network`,
                    { network: network.name, property: 'extendTargetName', invalidQName: network.extendTargetName, persistent: true }
                );
            } else if (network.extendTargetName && isValidQName(network.extendTargetName, definedNames)) {
                const extendType = getObjectTypeForQName(taxonomy, network.extendTargetName);
                if (extendType !== 'xbrl:networkObject') {
                    addValidationError(
                        `extendTargetName '${network.extendTargetName}' in network must reference a network object, but references a '${extendType || 'unknown'}' object`,
                        {
                            network: network.extendTargetName,
                            property: 'extendTargetName',
                            invalidQName: network.extendTargetName,
                            errorCode: 'oimte:invalidQNameType',
                            persistent: true
                        }
                    );
                }
            }
            if (Array.isArray(network.roots)) {
                network.roots.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in network roots`,
                            { network: network.name, property: 'roots', invalidQName: qname }
                        );
                    }
                });

                // ---- Duplicate root check (oimte:duplicateRoots) ----
                const seenRoots = new Set();
                network.roots.forEach((qname) => {
                    if (seenRoots.has(qname)) {
                        const networkName = network.name || network.extendTargetName || `networks[?]`;
                        addValidationError(
                            `Duplicate root '${qname}' in network '${networkName}' (oimte:duplicateRoots)`,
                            {
                                errorCode: 'oimte:duplicateRoots',
                                network: networkName,
                                property: 'roots',
                                root: qname
                            }
                        );
                    } else {
                        seenRoots.add(qname);
                    }
                });
            }
            if (Array.isArray(network.relationships)) {
                const relTypeConstraint = network.relationshipTypeName
                    ? relationshipTypeConstraints.get(network.relationshipTypeName) : null;

                network.relationships.forEach((rel, idx) => {
                    if (rel.source && !isValidQName(rel.source, definedNames)) {
                        addValidationError(
                            `Invalid source '${rel.source}' in network relationship`,
                            { network: network.name, property: `relationships[${idx}].source`, invalidQName: rel.source }
                        );
                    }
                    if (rel.target && !isValidQName(rel.target, definedNames)) {
                        addValidationError(
                            `Invalid target '${rel.target}' in network relationship`,
                            { network: network.name, property: `relationships[${idx}].target`, invalidQName: rel.target }
                        );
                    }

                    // Check source/target object type constraints for the relationship type
                    if (relTypeConstraint) {
                        if (rel.source && relTypeConstraint.sourceObjects) {
                            const sourceObjType = getObjectTypeForQName(taxonomy, rel.source);
                            if (sourceObjType && !relTypeConstraint.sourceObjects.has(sourceObjType)) {
                                addValidationError(
                                    `Source '${rel.source}' has object type '${sourceObjType}' which is not an allowed source object type for relationship type '${network.relationshipTypeName}'`,
                                    {
                                        network: network.name,
                                        property: `relationships[${idx}].source`,
                                        invalidQName: rel.source,
                                        errorCode: 'oimte:invalidRelationshipSourceObject',
                                        relationshipTypeName: network.relationshipTypeName,
                                        allowedObjectTypes: [...relTypeConstraint.sourceObjects]
                                    }
                                );
                            }
                        }
                        if (rel.target && relTypeConstraint.targetObjects) {
                            const targetObjType = getObjectTypeForQName(taxonomy, rel.target);
                            if (targetObjType && !relTypeConstraint.targetObjects.has(targetObjType)) {
                                addValidationError(
                                    `Target '${rel.target}' has object type '${targetObjType}' which is not an allowed target object type for relationship type '${network.relationshipTypeName}'`,
                                    {
                                        network: network.name,
                                        property: `relationships[${idx}].target`,
                                        invalidQName: rel.target,
                                        errorCode: 'oimte:invalidRelationshipTargetObject',
                                        relationshipTypeName: network.relationshipTypeName,
                                        allowedObjectTypes: [...relTypeConstraint.targetObjects]
                                    }
                                );
                            }
                        }
                    }
                });

                // ---- Duplicate relationship check (oimte:duplicateRelationships) ----
                // Two relationships are duplicates when source, target, order, and every
                // additional property all have identical values.
                // The order default is 0 when the property is absent (spec §network-object).
                const seenRelKeys = new Set();
                network.relationships.forEach((rel, idx) => {
                    // Normalise properties array: sort by property QName so order doesn't matter
                    const normProps = Array.isArray(rel.properties)
                        ? [...rel.properties]
                              .map(p => ({ property: p.property ?? null, value: p.value ?? null }))
                              .sort((a, b) => String(a.property).localeCompare(String(b.property)))
                        : [];
                    const key = JSON.stringify({
                        source: rel.source ?? null,
                        target: rel.target ?? null,
                        order:  rel.order  ?? 0,
                        properties: normProps
                    });
                    if (seenRelKeys.has(key)) {
                        const networkName = network.name || network.extendTargetName || `networks[?]`;
                        addValidationError(
                            `Duplicate relationship in network '${networkName}': source='${rel.source}', target='${rel.target}', order=${rel.order ?? 0} (oimte:duplicateRelationships)`,
                            {
                                errorCode: 'oimte:duplicateRelationships',
                                network: networkName,
                                property: `relationships[${idx}]`,
                                source: rel.source,
                                target: rel.target,
                                order:  rel.order ?? 0
                            }
                        );
                    } else {
                        seenRelKeys.add(key);
                    }
                });
            }
        });
    }
    
    // ========== UNITS ==========
    if (Array.isArray(taxonomy.units)) {
        // Build a set of all unit object names for compositeUnitRepresentation checks
        const unitObjectNames = new Set(taxonomy.units.map(u => u.name).filter(Boolean));

        // Unit string representation syntax pattern (OIM Common §3.4).
        // Valid forms:
        //   Alt 1 (numerators only):   Q(*Q)*
        //   Alt 2 (numerator/denom):   (Q|\(Q(\*Q)+\)) / (Q|\(Q(\*Q)+\))
        // where Q = prefix:localname (NCName : NCName-like), no whitespace anywhere.
        const UNIT_STR_PATTERN = /^([A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*)(\*[A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*)*$|^([A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*|\([A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*(\*[A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*)+\))\/([A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*|\([A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*(\*[A-Za-z_][A-Za-z0-9_.-]*:[A-Za-z_][A-Za-z0-9_.-]*)+\))$/;

        // Extract all QNames from a syntactically valid unit string representation.
        // Splits on *, /, (, ) and discards empty tokens.
        function extractUnitQNames(str) {
            return str.split(/[*()/]/).filter(s => s.length > 0);
        }

        taxonomy.units.forEach(unit => {
            if (unit.dataType && !isValidQName(unit.dataType, definedNames)) {
                addValidationError(
                    `Invalid dataType '${unit.dataType}' in unit`,
                    { unit: unit.name, property: 'dataType', invalidQName: unit.dataType }
                );
            }

            // Validate compositeUnitRepresentation entries (oimce:invalidUnitStringRepresentation)
            if (Array.isArray(unit.compositeUnitRepresentation)) {
                unit.compositeUnitRepresentation.forEach(str => {
                    // 1. Syntax check — only QNames, *, /, () and no whitespace
                    if (!UNIT_STR_PATTERN.test(str)) {
                        addValidationError(
                            `Unit '${unit.name}' has invalid compositeUnitRepresentation '${str}': does not conform to the unit string representation syntax defined in OIM Common §3.4 (only QNames, '*', '/', and '()' are permitted; no whitespace allowed)`,
                            {
                                objectName: unit.name,
                                objectType: 'xbrl:unitObject',
                                property: 'compositeUnitRepresentation',
                                invalidValue: str,
                                errorCode: 'oimce:invalidUnitStringRepresentation',
                                reason: 'string contains invalid characters or does not conform to unit string representation syntax'
                            }
                        );
                        return; // skip QName resolution check when syntax is already invalid
                    }

                    // 2. Per-QName checks: self-reference and resolution
                    extractUnitQNames(str).forEach(qname => {
                        // 2a. Self-reference check — a unit MUST NOT appear in its own compositeUnitRepresentation
                        //     (oimte:unitDataTypeUsedInDefinition)
                        if (qname === unit.name) {
                            addValidationError(
                                `Unit '${unit.name}' has compositeUnitRepresentation '${str}' that references the unit itself — a unit MUST NOT appear in its own unit string representation`,
                                {
                                    objectName: unit.name,
                                    objectType: 'xbrl:unitObject',
                                    property: 'compositeUnitRepresentation',
                                    invalidValue: str,
                                    invalidQName: qname,
                                    errorCode: 'oimte:unitDataTypeUsedInDefinition'
                                }
                            );
                            return; // self-reference is the primary error; skip the resolution check for this QName
                        }

                        // 2b. QName resolution check — each QName must reference a unit object in the model
                        if (!unitObjectNames.has(qname)) {
                            addValidationError(
                                `Unit '${unit.name}' has compositeUnitRepresentation '${str}' referencing '${qname}' which is not a unit object defined in the model`,
                                {
                                    objectName: unit.name,
                                    objectType: 'xbrl:unitObject',
                                    property: 'compositeUnitRepresentation',
                                    invalidValue: str,
                                    invalidQName: qname,
                                    errorCode: 'oimce:invalidUnitStringRepresentation',
                                    reason: `'${qname}' does not resolve to a unit object`
                                }
                            );
                        }
                    });
                });
            }
        });
    }
    
    // ========== GROUP CONTENTS ==========
    if (Array.isArray(taxonomy.groupContents)) {
        taxonomy.groupContents.forEach(gc => {
            if (gc.groupName && !isValidQName(gc.groupName, definedNames)) {
                addValidationError(
                    `Invalid groupName '${gc.groupName}' in groupContents`,
                    { property: 'groupContents.groupName', invalidQName: gc.groupName }
                );
            }
            if (Array.isArray(gc.relatedNames)) {
                gc.relatedNames.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in groupContents relatedNames`,
                            { groupName: gc.groupName, property: 'relatedNames', invalidQName: qname }
                        );
                    }
                });
            }
        });
    }
    
    // ========== GROUP TREE ==========
    if (taxonomy.groupTree && Array.isArray(taxonomy.groupTree.relationships)) {
        taxonomy.groupTree.relationships.forEach((rel, idx) => {
            if (rel.source && !isValidQName(rel.source, definedNames)) {
                addValidationError(
                    `Invalid source '${rel.source}' in groupTree relationship`,
                    { property: `groupTree.relationships[${idx}].source`, invalidQName: rel.source }
                );
            }
            if (rel.target && !isValidQName(rel.target, definedNames)) {
                addValidationError(
                    `Invalid target '${rel.target}' in groupTree relationship`,
                    { property: `groupTree.relationships[${idx}].target`, invalidQName: rel.target }
                );
            }
        });
    }
    
    // ========== RELATIONSHIP TYPES ==========
    if (Array.isArray(taxonomy.relationshipTypes)) {
        taxonomy.relationshipTypes.forEach(relType => {
            if (Array.isArray(relType.allowedLinkProperties)) {
                relType.allowedLinkProperties.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in relationshipType allowedLinkProperties`,
                            { relationshipType: relType.name, property: 'allowedLinkProperties', invalidQName: qname }
                        );
                    }
                });
            }
            if (Array.isArray(relType.requiredLinkProperties)) {
                relType.requiredLinkProperties.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in relationshipType requiredLinkProperties`,
                            { relationshipType: relType.name, property: 'requiredLinkProperties', invalidQName: qname }
                        );
                    }
                });
            }
        });
    }
    
    // ========== LABELS ==========
    if (Array.isArray(taxonomy.labels)) {
        taxonomy.labels.forEach((label, idx) => {
            if (label.relatedName && !isValidQName(label.relatedName, definedNames)) {
                addValidationError(
                    `Invalid relatedName '${label.relatedName}' in label`,
                    { property: `labels[${idx}].relatedName`, invalidQName: label.relatedName }
                );
            }
            if (label.labelType && !isValidQName(label.labelType, definedNames)) {
                addValidationError(
                    `Invalid labelType '${label.labelType}' in label`,
                    { property: `labels[${idx}].labelType`, invalidQName: label.labelType }
                );
            }
            // Validate BCP47 language code
            if (label.language && !isValidBCP47LanguageCode(label.language)) {
                addValidationError(
                    `Invalid language code '${label.language}' in label for '${label.relatedName}'. Must be a valid BCP 47 language code.`,
                    { 
                        property: `labels[${idx}].language`, 
                        invalidValue: label.language,
                        errorCode: 'oimte:invalidLanguage',
                        relatedName: label.relatedName
                    }
                );
            }
        });
    }
    
    // ========== REFERENCES ==========
    if (Array.isArray(taxonomy.references)) {
        taxonomy.references.forEach((ref, idx) => {
            if (ref.extendTargetName && !isValidQName(ref.extendTargetName, definedNames)) {
                addValidationError(
                    `Invalid extendTargetName '${ref.extendTargetName}' in reference`,
                    { property: `references[${idx}].extendTargetName`, invalidQName: ref.extendTargetName, persistent: true }
                );
            } else if (ref.extendTargetName && isValidQName(ref.extendTargetName, definedNames)) {
                const extendType = getObjectTypeForQName(taxonomy, ref.extendTargetName);
                if (extendType !== 'xbrl:referenceObject') {
                    addValidationError(
                        `extendTargetName '${ref.extendTargetName}' in reference must reference a reference object, but references a '${extendType || 'unknown'}' object`,
                        {
                            property: `references[${idx}].extendTargetName`,
                            invalidQName: ref.extendTargetName,
                            errorCode: 'oimte:invalidQNameType',
                            persistent: true
                        }
                    );
                }
            }
            if (ref.referenceType && !isValidQName(ref.referenceType, definedNames)) {
                addValidationError(
                    `Invalid referenceType '${ref.referenceType}' in reference`,
                    { property: `references[${idx}].referenceType`, invalidQName: ref.referenceType }
                );
            }
            if (Array.isArray(ref.relatedNames)) {
                ref.relatedNames.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in reference relatedNames`,
                            { property: `references[${idx}].relatedNames`, invalidQName: qname }
                        );
                    }
                });
            }
            // Validate BCP47 language code
            if (ref.language && !isValidBCP47LanguageCode(ref.language)) {
                addValidationError(
                    `Invalid language code '${ref.language}' in reference '${ref.name || ref.extendTargetName}'. Must be a valid BCP 47 language code.`,
                    { 
                        property: `references[${idx}].language`, 
                        invalidValue: ref.language,
                        errorCode: 'oimte:invalidLanguage',
                        referenceName: ref.name || ref.extendTargetName
                    }
                );
            }
        });
    }
    
    // ========== FACTSPACES ==========
    // QName pattern: prefix starts with letter/underscore, local name starts with letter/underscore
    // This distinguishes QNames from typed values like dateTime ("2025-01-01T00:00:00"),
    // template variables ("$column"), LEI identifiers ("lei:00EH..."), etc.
    const qnameValuePattern = /^[A-Za-z_][A-Za-z0-9._-]*:[A-Za-z_][A-Za-z0-9._-]*$/;
    // The set of valid built-in (core) dimension keys that may appear in factDimensions.
    // Any other key must be a QName that resolves to a taxonomy-defined dimension.
    const coreDimensionKeys = new Set(['xbrl:concept', 'xbrl:unit', 'xbrl:period', 'xbrl:entity', 'xbrl:language']);

    if (Array.isArray(taxonomy.facts)) {
        taxonomy.facts.forEach((fs, idx) => {
            if (fs.factDimensions) {
                // Validate that every dimension KEY is either a known core dimension or a
                // taxonomy-defined name. Keys like 'xbrl:unit1' or 'xbrl:entity1' are not valid.
                for (const dimKey of Object.keys(fs.factDimensions)) {
                    if (coreDimensionKeys.has(dimKey)) continue;  // valid core dimension key
                    if (isValidQName(dimKey, definedNames)) continue;  // valid taxonomy dimension
                    addValidationError(
                        `Invalid dimension key '${dimKey}' in fact '${fs.name || idx}': not a core dimension (xbrl:concept, xbrl:period, xbrl:entity, xbrl:unit, xbrl:language) or a defined taxonomy dimension`,
                        { property: `facts[${idx}].factDimensions`, invalidQName: dimKey, errorCode: 'oimte:invalidQNameReference' }
                    );
                }
                if (fs.factDimensions['xbrl:concept'] && !isValidQName(fs.factDimensions['xbrl:concept'], definedNames)) {
                    addValidationError(
                        `Invalid xbrl:concept '${fs.factDimensions['xbrl:concept']}' in fact`,
                        { property: `facts[${idx}].factDimensions['xbrl:concept']`, invalidQName: fs.factDimensions['xbrl:concept'], errorCode: 'oimte:invalidQNameReference' }
                    );
                }
                // xbrl:unit must be a QName (prefix:localName) or a compound unit expression
                // containing '*' or '/'. A bare string with no colon and no operator is never valid.
                if (fs.factDimensions['xbrl:unit'] && typeof fs.factDimensions['xbrl:unit'] === 'string') {
                    const unitVal = fs.factDimensions['xbrl:unit'];
                    const isCompoundExpr = unitVal.includes('*') || unitVal.includes('/');
                    if (!isCompoundExpr) {
                        if (!unitVal.includes(':')) {
                            // Bare string without namespace prefix — never a valid unit QName
                            addValidationError(
                                `Invalid xbrl:unit '${unitVal}' in fact '${fs.name || idx}': unit must be a QName (e.g. utr:${unitVal}) or a compound expression`,
                                { property: `facts[${idx}].factDimensions['xbrl:unit']`, invalidQName: unitVal, errorCode: 'oimte:invalidQNameReference' }
                            );
                        } else if (!isValidQName(unitVal, definedNames)) {
                            // Looks like a QName but the referenced name is not defined
                            addValidationError(
                                `Invalid xbrl:unit '${unitVal}' in fact '${fs.name || idx}'`,
                                { property: `facts[${idx}].factDimensions['xbrl:unit']`, invalidQName: unitVal, errorCode: 'oimte:invalidQNameReference' }
                            );
                        }
                    }
                }
                // Validate custom dimension member values — any dimension whose value looks like a
                // QName (prefix:localName) and is not one of the core dimension keys
                for (const [dimKey, dimValue] of Object.entries(fs.factDimensions)) {
                    if (coreDimensionKeys.has(dimKey)) continue;
                    if (typeof dimValue !== 'string') continue;
                    if (!qnameValuePattern.test(dimValue)) continue; // not a QName-shaped value
                    if (!isValidQName(dimValue, definedNames)) {
                        addValidationError(
                            `Invalid dimension member '${dimValue}' for dimension '${dimKey}' in fact '${fs.name || idx}'`,
                            { property: `facts[${idx}].factDimensions['${dimKey}']`, invalidQName: dimValue, errorCode: 'oimte:invalidQNameReference' }
                        );
                    }
                }
            }
            // NOTE: fs.factValues[].name defines new QNames and should not be validated
        });
    }
    
    // ========== FACT MAPS ==========
    if (Array.isArray(taxonomy.factMaps)) {
        taxonomy.factMaps.forEach(factMap => {
            // Validate templateName reference (required)
            if (factMap.templateName && !isValidQName(factMap.templateName, definedNames)) {
                addValidationError(
                    `Invalid templateName '${factMap.templateName}' in factMap`,
                    { factMap: factMap.name, property: 'templateName', invalidQName: factMap.templateName, errorCode: 'oimte:invalidQNameReference' }
                );
            }
            // Validate cubeName reference (optional)
            if (factMap.cubeName && !isValidQName(factMap.cubeName, definedNames)) {
                addValidationError(
                    `Invalid cubeName '${factMap.cubeName}' in factMap`,
                    { factMap: factMap.name, property: 'cubeName', invalidQName: factMap.cubeName, errorCode: 'oimte:invalidQNameReference' }
                );
            }
        });
    }
    
    // ========== FACT SOURCES ==========
    if (Array.isArray(taxonomy.factSources)) {
        taxonomy.factSources.forEach(factSource => {
            // Validate factMapName reference
            if (factSource.factMapName && !isValidQName(factSource.factMapName, definedNames)) {
                addValidationError(
                    `Invalid factMapName '${factSource.factMapName}' in factSource`,
                    { factSource: factSource.name, property: 'factMapName', invalidQName: factSource.factMapName, errorCode: 'oimte:invalidQNameReference' }
                );
            }
        });
    }
    
    // ========== LABEL TYPES ==========
    if (Array.isArray(taxonomy.labelTypes)) {
        taxonomy.labelTypes.forEach(lt => {
            if (lt.dataType) {
                if (!isValidQName(lt.dataType, definedNames)) {
                    addValidationError(
                        `Invalid dataType '${lt.dataType}' in labelType`,
                        { labelType: lt.name, property: 'dataType', invalidQName: lt.dataType }
                    );
                } else if (!isValidDataTypeRef(lt.dataType, taxonomy, definedNames)) {
                    addValidationError(
                        `dataType '${lt.dataType}' in labelType must reference a dataType object, collection object, or built-in XML Schema type`,
                        { labelType: lt.name, property: 'dataType', invalidQName: lt.dataType, errorCode: 'oimte:invalidQNameType' }
                    );
                }
            }
            if (Array.isArray(lt.allowedObjects)) {
                lt.allowedObjects.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in labelType allowedObjects`,
                            { labelType: lt.name, property: 'allowedObjects', invalidQName: qname }
                        );
                    }
                });
            }
        });
    }
    
    // ========== REFERENCE TYPES ==========
    if (Array.isArray(taxonomy.referenceTypes)) {
        taxonomy.referenceTypes.forEach(rt => {
            if (Array.isArray(rt.allowedObjects)) {
                rt.allowedObjects.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in referenceType allowedObjects`,
                            { referenceType: rt.name, property: 'allowedObjects', invalidQName: qname }
                        );
                    }
                });
            }
            if (Array.isArray(rt.orderedProperties)) {
                rt.orderedProperties.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in referenceType orderedProperties`,
                            { referenceType: rt.name, property: 'orderedProperties', invalidQName: qname }
                        );
                    }
                });
            }
            if (Array.isArray(rt.requiredProperties)) {
                rt.requiredProperties.forEach(qname => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid QName '${qname}' in referenceType requiredProperties`,
                            { referenceType: rt.name, property: 'requiredProperties', invalidQName: qname }
                        );
                    }
                });
            }
        });
    }
    
    // ========== CUBE TYPES ==========
    // NOTE: QName validation for cubeTypes is handled by taxonomy-builder.js
    // to avoid duplicate error reporting
    /*
    if (Array.isArray(taxonomy.cubeTypes)) {
        taxonomy.cubeTypes.forEach(ct => {
            if (ct.baseCubeType && !isValidQName(ct.baseCubeType, definedNames)) {
                addValidationError(
                    `Invalid baseCubeType '${ct.baseCubeType}' in cubeType`,
                    { cubeType: ct.name, property: 'baseCubeType', invalidQName: ct.baseCubeType }
                );
            }
            
            // Validate coreDimensions
            if (Array.isArray(ct.coreDimensions)) {
                ct.coreDimensions.forEach((dim, idx) => {
                    if (!isValidQName(dim, definedNames)) {
                        addValidationError(
                            `Invalid core dimension '${dim}' in cubeType coreDimensions`,
                            { cubeType: ct.name, property: `coreDimensions[${idx}]`, invalidQName: dim }
                        );
                    }
                });
            }
            
            // Validate dimensions.allowed
            if (ct.dimensions && Array.isArray(ct.dimensions.allowed)) {
                ct.dimensions.allowed.forEach((dim, idx) => {
                    // Can be either a simple QName or an object
                    if (typeof dim === 'string') {
                        if (!isValidQName(dim, definedNames)) {
                            addValidationError(
                                `Invalid dimension QName '${dim}' in cubeType dimensions.allowed`,
                                { cubeType: ct.name, property: `dimensions.allowed[${idx}]`, invalidQName: dim }
                            );
                        }
                    } else if (typeof dim === 'object') {
                        if (dim.name && !isValidQName(dim.name, definedNames)) {
                            addValidationError(
                                `Invalid dimension name '${dim.name}' in cubeType dimensions.allowed`,
                                { cubeType: ct.name, property: `dimensions.allowed[${idx}].name`, invalidQName: dim.name }
                            );
                        }
                        if (dim.dataType && !isValidQName(dim.dataType, definedNames)) {
                            addValidationError(
                                `Invalid dataType '${dim.dataType}' in cubeType dimensions.allowed`,
                                { cubeType: ct.name, property: `dimensions.allowed[${idx}].dataType`, invalidQName: dim.dataType }
                            );
                        }
                        if (dim.properties) {
                            if (Array.isArray(dim.properties.allowed)) {
                                dim.properties.allowed.forEach((prop, propIdx) => {
                                    if (!isValidQName(prop, definedNames)) {
                                        addValidationError(
                                            `Invalid property '${prop}' in cubeType dimensions.allowed properties.allowed`,
                                            { cubeType: ct.name, property: `dimensions.allowed[${idx}].properties.allowed[${propIdx}]`, invalidQName: prop }
                                        );
                                    }
                                });
                            }
                            if (Array.isArray(dim.properties.required)) {
                                dim.properties.required.forEach((prop, propIdx) => {
                                    if (!isValidQName(prop, definedNames)) {
                                        addValidationError(
                                            `Invalid property '${prop}' in cubeType dimensions.allowed properties.required`,
                                            { cubeType: ct.name, property: `dimensions.allowed[${idx}].properties.required[${propIdx}]`, invalidQName: prop }
                                        );
                                    }
                                });
                            }
                        }
                    }
                });
            }
            
            // Validate relationships.required
            if (ct.relationships && Array.isArray(ct.relationships.required)) {
                ct.relationships.required.forEach((rel, idx) => {
                    if (typeof rel === 'string') {
                        if (!isValidQName(rel, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${rel}' in cubeType relationships.required`,
                                { cubeType: ct.name, property: `relationships.required[${idx}]`, invalidQName: rel }
                            );
                        }
                    } else if (typeof rel === 'object') {
                        if (rel.type && !isValidQName(rel.type, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${rel.type}' in cubeType relationships.required`,
                                { cubeType: ct.name, property: `relationships.required[${idx}].type`, invalidQName: rel.type }
                            );
                        }
                        if (rel.source) {
                            if (rel.source.qname && !isValidQName(rel.source.qname, definedNames)) {
                                addValidationError(
                                    `Invalid source qname '${rel.source.qname}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].source.qname`, invalidQName: rel.source.qname }
                                );
                            }
                            if (rel.source.objectType && !isValidQName(rel.source.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid source objectType '${rel.source.objectType}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].source.objectType`, invalidQName: rel.source.objectType }
                                );
                            }
                            if (rel.source.dataType && !isValidQName(rel.source.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid source dataType '${rel.source.dataType}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].source.dataType`, invalidQName: rel.source.dataType }
                                );
                            }
                        }
                        if (rel.target) {
                            if (rel.target.qname && !isValidQName(rel.target.qname, definedNames)) {
                                addValidationError(
                                    `Invalid target qname '${rel.target.qname}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].target.qname`, invalidQName: rel.target.qname }
                                );
                            }
                            if (rel.target.objectType && !isValidQName(rel.target.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid target objectType '${rel.target.objectType}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].target.objectType`, invalidQName: rel.target.objectType }
                                );
                            }
                            if (rel.target.dataType && !isValidQName(rel.target.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid target dataType '${rel.target.dataType}' in cubeType relationships.required`,
                                    { cubeType: ct.name, property: `relationships.required[${idx}].target.dataType`, invalidQName: rel.target.dataType }
                                );
                            }
                        }
                    }
                });
            }
            
            // Validate relationships.allowed
            if (ct.relationships && Array.isArray(ct.relationships.allowed)) {
                ct.relationships.allowed.forEach((rel, idx) => {
                    if (typeof rel === 'string') {
                        if (!isValidQName(rel, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${rel}' in cubeType relationships.allowed`,
                                { cubeType: ct.name, property: `relationships.allowed[${idx}]`, invalidQName: rel }
                            );
                        }
                    } else if (typeof rel === 'object') {
                        if (rel.type && !isValidQName(rel.type, definedNames)) {
                            addValidationError(
                                `Invalid relationship type '${rel.type}' in cubeType relationships.allowed`,
                                { cubeType: ct.name, property: `relationships.allowed[${idx}].type`, invalidQName: rel.type }
                            );
                        }
                        if (rel.source) {
                            if (rel.source.qname && !isValidQName(rel.source.qname, definedNames)) {
                                addValidationError(
                                    `Invalid source qname '${rel.source.qname}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].source.qname`, invalidQName: rel.source.qname }
                                );
                            }
                            if (rel.source.objectType && !isValidQName(rel.source.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid source objectType '${rel.source.objectType}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].source.objectType`, invalidQName: rel.source.objectType }
                                );
                            }
                            if (rel.source.dataType && !isValidQName(rel.source.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid source dataType '${rel.source.dataType}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].source.dataType`, invalidQName: rel.source.dataType }
                                );
                            }
                        }
                        if (rel.target) {
                            if (rel.target.qname && !isValidQName(rel.target.qname, definedNames)) {
                                addValidationError(
                                    `Invalid target qname '${rel.target.qname}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].target.qname`, invalidQName: rel.target.qname }
                                );
                            }
                            if (rel.target.objectType && !isValidQName(rel.target.objectType, definedNames)) {
                                addValidationError(
                                    `Invalid target objectType '${rel.target.objectType}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].target.objectType`, invalidQName: rel.target.objectType }
                                );
                            }
                            if (rel.target.dataType && !isValidQName(rel.target.dataType, definedNames)) {
                                addValidationError(
                                    `Invalid target dataType '${rel.target.dataType}' in cubeType relationships.allowed`,
                                    { cubeType: ct.name, property: `relationships.allowed[${idx}].target.dataType`, invalidQName: rel.target.dataType }
                                );
                            }
                        }
                    }
                });
            }
            
            // Validate properties.required
            if (ct.properties && Array.isArray(ct.properties.required)) {
                ct.properties.required.forEach((prop, idx) => {
                    if (!isValidQName(prop, definedNames)) {
                        addValidationError(
                            `Invalid property '${prop}' in cubeType properties.required`,
                            { cubeType: ct.name, property: `properties.required[${idx}]`, invalidQName: prop }
                        );
                    }
                });
            }
            
            // Validate properties.allowed
            if (ct.properties && Array.isArray(ct.properties.allowed)) {
                ct.properties.allowed.forEach((prop, idx) => {
                    if (!isValidQName(prop, definedNames)) {
                        addValidationError(
                            `Invalid property '${prop}' in cubeType properties.allowed`,
                            { cubeType: ct.name, property: `properties.allowed[${idx}]`, invalidQName: prop }
                        );
                    }
                });
            }
        });
    }
    */
    
    // ========== DATA TYPES ==========
    if (Array.isArray(taxonomy.dataTypes)) {
        taxonomy.dataTypes.forEach(dt => {
            if (dt.baseType && !isValidQName(dt.baseType, definedNames)) {
                addValidationError(
                    `Invalid baseType '${dt.baseType}' in dataType`,
                    { dataType: dt.name, property: 'baseType', invalidQName: dt.baseType }
                );
            }
            if (dt.unitType) {
                if (dt.unitType.dataTypeNumerator && !isValidQName(dt.unitType.dataTypeNumerator, definedNames)) {
                    addValidationError(
                        `Invalid dataTypeNumerator '${dt.unitType.dataTypeNumerator}' in dataType unitType`,
                        { dataType: dt.name, property: 'unitType.dataTypeNumerator', invalidQName: dt.unitType.dataTypeNumerator }
                    );
                }
                if (dt.unitType.dataTypeDenominator && !isValidQName(dt.unitType.dataTypeDenominator, definedNames)) {
                    addValidationError(
                        `Invalid dataTypeDenominator '${dt.unitType.dataTypeDenominator}' in dataType unitType`,
                        { dataType: dt.name, property: 'unitType.dataTypeDenominator', invalidQName: dt.unitType.dataTypeDenominator }
                    );
                }
                if (dt.unitType.dataTypeMultiplier && !isValidQName(dt.unitType.dataTypeMultiplier, definedNames)) {
                    addValidationError(
                        `Invalid dataTypeMultiplier '${dt.unitType.dataTypeMultiplier}' in dataType unitType`,
                        { dataType: dt.name, property: 'unitType.dataTypeMultiplier', invalidQName: dt.unitType.dataTypeMultiplier }
                    );
                }
            }
            
            // collectionType MUST NOT appear inside a dataType — collections are now top-level objects
            if (dt.collectionType) {
                addValidationError(
                    `DataType '${dt.name}' defines a collectionType property. Collections must be defined in the top-level collections array, not inside a dataType object.`,
                    {
                        dataType: dt.name,
                        property: 'collectionType',
                        errorCode: 'oimte:collectionTypeWithoutCollectionBaseType'
                    }
                );
            }

            // Validate that mapType is only used with baseType xbrli:map
            if (dt.mapType && dt.baseType !== 'xbrli:map') {
                addValidationError(
                    `DataType '${dt.name}' defines mapType but baseType is '${dt.baseType}' instead of 'xbrli:map'`,
                    {
                        dataType: dt.name,
                        property: 'mapType',
                        baseType: dt.baseType,
                        errorCode: 'oimte:mapTypeWithoutMapBaseType'
                    }
                );
            }

            // Validate mapType QName fields
            if (dt.mapType) {
                if (dt.mapType.keyType && !isValidQName(dt.mapType.keyType, definedNames)) {
                    addValidationError(
                        `Invalid keyType '${dt.mapType.keyType}' in dataType mapType`,
                        { dataType: dt.name, property: 'mapType.keyType', invalidQName: dt.mapType.keyType }
                    );
                }
                if (dt.mapType.valueType && !isValidQName(dt.mapType.valueType, definedNames)) {
                    addValidationError(
                        `Invalid valueType '${dt.mapType.valueType}' in dataType mapType`,
                        { dataType: dt.name, property: 'mapType.valueType', invalidQName: dt.mapType.valueType }
                    );
                }
            }
        });
    }
    
    // ========== COLLECTIONS ==========
    if (Array.isArray(taxonomy.collections)) {
        taxonomy.collections.forEach(col => {
            if (Array.isArray(col.dataTypesAllowed)) {
                col.dataTypesAllowed.forEach((qname, idx) => {
                    if (!isValidQName(qname, definedNames)) {
                        addValidationError(
                            `Invalid dataTypesAllowed QName '${qname}' in collection '${col.name}'`,
                            { collection: col.name, property: `dataTypesAllowed[${idx}]`, invalidQName: qname }
                        );
                    }
                });
            }
        });
    }

    // ========== TRANSFORMS ==========
    if (Array.isArray(taxonomy.transforms)) {
        taxonomy.transforms.forEach(transform => {
            if (transform.inputDataType && !isValidQName(transform.inputDataType, definedNames)) {
                addValidationError(
                    `Invalid inputDataType '${transform.inputDataType}' in transform`,
                    { transform: transform.name, property: 'inputDataType', invalidQName: transform.inputDataType }
                );
            }
            if (transform.outputDataType && !isValidQName(transform.outputDataType, definedNames)) {
                addValidationError(
                    `Invalid outputDataType '${transform.outputDataType}' in transform`,
                    { transform: transform.name, property: 'outputDataType', invalidQName: transform.outputDataType }
                );
            }
        });
    }
    
    // ========== PROPERTIES (generic property objects) ==========
    // Build a map of propertyType names to their dataTypes for validation
    const propertyTypeDataTypes = new Map();
    if (Array.isArray(taxonomy.propertyTypes)) {
        taxonomy.propertyTypes.forEach(pt => {
            if (pt.name && pt.dataType) {
                propertyTypeDataTypes.set(pt.name, pt.dataType);
            }
        });
    }

    // Build a map of custom dataType definitions (for use in property value validation)
    const propertyDataTypeMap = new Map();
    if (Array.isArray(taxonomy.dataTypes)) {
        taxonomy.dataTypes.forEach(dt => {
            if (dt.name) {
                propertyDataTypeMap.set(dt.name, dt);
            }
        });
    }
    
    // Validate property.property references in any object with a properties array
    // Also validate that if a propertyType has dataType xs:QName, the value is a valid QName
    // Also validate required and allowed properties within property objects
    const validateProperties = (obj, context) => {
        if (Array.isArray(obj.properties)) {
            obj.properties.forEach((prop, idx) => {
                // Validate required properties in property objects
                requiredProperties.properties.forEach(reqProp => {
                    if (!prop.hasOwnProperty(reqProp)) {
                        addValidationError(
                            `Missing required property '${reqProp}' in property object at ${context}.properties[${idx}]`,
                            { 
                                objectType: 'properties',
                                property: `${context}.properties[${idx}].${reqProp}`,
                                errorCode: 'oimte:invalidJSONStructureMissingRequiredProperty',
                                propertyName: reqProp
                            }
                        );
                    }
                });
                
                // Validate allowed properties in property objects
                const allowedProps = new Set(allowedProperties.properties);
                Object.keys(prop).forEach(propKey => {
                    if (!allowedProps.has(propKey)) {
                        addValidationError(
                            `Invalid property '${propKey}' defined in property object at ${context}.properties[${idx}]`,
                            { 
                                objectType: 'properties',
                                objectName: `${context}.properties[${idx}]`,
                                propertyName: propKey,
                                errorCode: 'oimte:invalidJSONStructureInvalidPropertyDefined'
                            }
                        );
                    }
                });
                
                // Validate that prop.property is a valid QName
                if (prop.property && !isValidQName(prop.property, definedNames)) {
                    addValidationError(
                        `Invalid property '${prop.property}' in ${context}`,
                        { property: `${context}.properties[${idx}].property`, invalidQName: prop.property }
                    );
                }
                
                // If the propertyType has a dataType, validate the value against it
                if (prop.property && prop.value !== undefined && prop.value !== null) {
                    const dataType = propertyTypeDataTypes.get(prop.property);
                    if (dataType === 'xs:QName') {
                        // The value should be a QName, so validate it
                        if (!isValidQName(prop.value, definedNames)) {
                            addValidationError(
                                `Invalid QName value '${prop.value}' for property '${prop.property}' in ${context}`,
                                { 
                                    property: `${context}.properties[${idx}].value`, 
                                    invalidQName: prop.value,
                                    propertyType: prop.property,
                                    expectedDataType: 'xs:QName'
                                }
                            );
                        } else {
                            // Additional semantic type checks for specific xs:QName properties
                            if (prop.property === 'xbrl:preferredLabel') {
                                const labelRefType = getObjectTypeForQName(taxonomy, prop.value);
                                if (labelRefType && labelRefType !== 'xbrl:labelTypeObject') {
                                    addValidationError(
                                        `preferredLabel value '${prop.value}' in ${context} must reference a labelType object, but references a '${labelRefType}' object`,
                                        {
                                            property: `${context}.properties[${idx}].value`,
                                            invalidQName: prop.value,
                                            errorCode: 'oimte:invalidQNameType'
                                        }
                                    );
                                }
                            }
                        }
                    } else if (dataType) {
                        // General data type validation for all other declared types
                        const isValid = isValueValidForDataType(prop.value, dataType, propertyDataTypeMap);
                        if (!isValid) {
                            addValidationError(
                                `Property '${prop.property}' in ${context} has value '${prop.value}' which does not match its declared data type '${dataType}'`,
                                {
                                    property: `${context}.properties[${idx}].value`,
                                    propertyType: prop.property,
                                    declaredDataType: dataType,
                                    value: prop.value,
                                    errorCode: 'oimte:propertyValueDataTypeMismatch'
                                }
                            );
                        }
                    }
                }
            });
        }
    };
    
    // Apply property validation to all objects that can have properties
    ['concepts', 'abstracts', 'members', 'cubes', 'dimensions', 'domains', 'domainClasses', 'networks', 'entities', 'groups', 'labels', 'references'].forEach(arrayProp => {
        if (Array.isArray(taxonomy[arrayProp])) {
            taxonomy[arrayProp].forEach((obj, idx) => {
                validateProperties(obj, `${arrayProp}[${idx}]`);
            });
        }
    });
    
    // Validate properties on the xbrlModel itself
    if (taxonomy.properties) {
        validateProperties(taxonomy, 'xbrlModel');
    }
    
    // Validate properties on domain and network relationships
    if (Array.isArray(taxonomy.domains)) {
        taxonomy.domains.forEach((domain, dIdx) => {
            if (Array.isArray(domain.relationships)) {
                domain.relationships.forEach((rel, rIdx) => {
                    validateProperties(rel, `domains[${dIdx}].relationships[${rIdx}]`);
                });
            }
        });
    }
    if (Array.isArray(taxonomy.networks)) {
        taxonomy.networks.forEach((network, nIdx) => {
            if (Array.isArray(network.relationships)) {
                network.relationships.forEach((rel, rIdx) => {
                    validateProperties(rel, `networks[${nIdx}].relationships[${rIdx}]`);
                });
            }
        });
    }
}

/**
 * Validate QName references in relationshipTypes
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set<string>} definedNames - Set of defined QNames
 */
function validateRelationshipTypes(taxonomy, definedNames) {
    if (!Array.isArray(taxonomy.relationshipTypes)) {
        return;
    }
    
    taxonomy.relationshipTypes.forEach(relType => {
        // Validate sourceObjects
        if (Array.isArray(relType.sourceObjects)) {
            relType.sourceObjects.forEach(qname => {
                if (!isValidQName(qname, definedNames)) {
                    addValidationError(
                        `Invalid QName '${qname}' in relationshipType sourceObjects`,
                        {
                            relationshipType: relType.name,
                            property: 'sourceObjects',
                            invalidQName: qname
                        }
                    );
                }
            });
        }
        
        // Validate targetObjects
        if (Array.isArray(relType.targetObjects)) {
            relType.targetObjects.forEach(qname => {
                if (!isValidQName(qname, definedNames)) {
                    addValidationError(
                        `Invalid QName '${qname}' in relationshipType targetObjects`,
                        {
                            relationshipType: relType.name,
                            property: 'targetObjects',
                            invalidQName: qname
                        }
                    );
                }
            });
        }
    });
}

/**
 * Validate QName references in layouts array
 * @param {Array} layouts - Array of layout objects from xbrlModel
 * @param {Set<string>} definedNames - Set of defined QNames
 */
function validateLayoutsReferences(layouts, definedNames) {
    if (!layouts || !Array.isArray(layouts)) {
        return;
    }
    
    layouts.forEach((layout, layoutIdx) => {
        // NOTE: taxonomy.factMaps[].name and taxonomy.factSources[].name define new QNames and should not be validated
        
        // Validate dataTables
        if (Array.isArray(layout.dataTables)) {
            layout.dataTables.forEach((dt, idx) => {
                // NOTE: dt.name defines a new QName and should not be validated
                
                if (dt.cubeName && !isValidQName(dt.cubeName, definedNames)) {
                    addValidationError(
                        `Invalid cubeName '${dt.cubeName}' in dataTable`,
                        { property: `layouts[${layoutIdx}].dataTables[${idx}].cubeName`, invalidQName: dt.cubeName }
                    );
                }
            });
        }
    });
}

/**
 * Validate that objects using dataTypes respect the allowedObjects restrictions
 * @param {Object} taxonomy - The taxonomy object
 */
function validateDataTypeAllowedObjects(taxonomy) {
    if (!Array.isArray(taxonomy.dataTypes)) {
        return;
    }
    
    // Build a map of dataType names to their allowedObjects arrays
    const dataTypeAllowedObjects = new Map();
    taxonomy.dataTypes.forEach(dt => {
        if (dt.name && Array.isArray(dt.allowedObjects) && dt.allowedObjects.length > 0) {
            dataTypeAllowedObjects.set(dt.name, dt.allowedObjects);
        }
    });
    
    if (dataTypeAllowedObjects.size === 0) {
        return; // No restricted dataTypes
    }
    
    // Check concepts
    if (Array.isArray(taxonomy.concepts)) {
        taxonomy.concepts.forEach(concept => {
            if (concept.dataType && dataTypeAllowedObjects.has(concept.dataType)) {
                const allowedObjects = dataTypeAllowedObjects.get(concept.dataType);
                if (!allowedObjects.includes('xbrl:conceptObject')) {
                    addValidationError(
                        `Concept '${concept.name}' uses dataType '${concept.dataType}' which does not allow xbrl:conceptObject in its allowedObjects`,
                        {
                            objectName: concept.name,
                            objectType: 'concept',
                            dataType: concept.dataType,
                            allowedObjects: allowedObjects,
                            errorCode: 'oimte:unallowedDatatypeObject'
                        }
                    );
                }
            }
        });
    }
    
    // Check members
    if (Array.isArray(taxonomy.members)) {
        taxonomy.members.forEach(member => {
            if (member.dataType && dataTypeAllowedObjects.has(member.dataType)) {
                const allowedObjects = dataTypeAllowedObjects.get(member.dataType);
                if (!allowedObjects.includes('xbrl:memberObject')) {
                    addValidationError(
                        `Member '${member.name}' uses dataType '${member.dataType}' which does not allow xbrl:memberObject in its allowedObjects`,
                        {
                            objectName: member.name,
                            objectType: 'member',
                            dataType: member.dataType,
                            allowedObjects: allowedObjects,
                            errorCode: 'oimte:unallowedDatatypeObject'
                        }
                    );
                }
            }
        });
    }
    
    // Check dimensions
    if (Array.isArray(taxonomy.dimensions)) {
        taxonomy.dimensions.forEach(dimension => {
            if (dimension.dataType && dataTypeAllowedObjects.has(dimension.dataType)) {
                const allowedObjects = dataTypeAllowedObjects.get(dimension.dataType);
                if (!allowedObjects.includes('xbrl:dimensionObject')) {
                    addValidationError(
                        `Dimension '${dimension.name}' uses dataType '${dimension.dataType}' which does not allow xbrl:dimensionObject in its allowedObjects`,
                        {
                            objectName: dimension.name,
                            objectType: 'dimension',
                            dataType: dimension.dataType,
                            allowedObjects: allowedObjects,
                            errorCode: 'oimte:unallowedDatatypeObject'
                        }
                    );
                }
            }
        });
    }
    
    // Check units
    if (Array.isArray(taxonomy.units)) {
        taxonomy.units.forEach(unit => {
            if (unit.dataType && dataTypeAllowedObjects.has(unit.dataType)) {
                const allowedObjects = dataTypeAllowedObjects.get(unit.dataType);
                if (!allowedObjects.includes('xbrl:unitObject')) {
                    addValidationError(
                        `Unit '${unit.name}' uses dataType '${unit.dataType}' which does not allow xbrl:unitObject in its allowedObjects`,
                        {
                            objectName: unit.name,
                            objectType: 'unit',
                            dataType: unit.dataType,
                            allowedObjects: allowedObjects,
                            errorCode: 'oimte:unallowedDatatypeObject'
                        }
                    );
                }
            }
        });
    }
    
    // Check entities
    if (Array.isArray(taxonomy.entities)) {
        taxonomy.entities.forEach(entity => {
            if (entity.dataType && dataTypeAllowedObjects.has(entity.dataType)) {
                const allowedObjects = dataTypeAllowedObjects.get(entity.dataType);
                if (!allowedObjects.includes('xbrl:entityObject')) {
                    addValidationError(
                        `Entity '${entity.name}' uses dataType '${entity.dataType}' which does not allow xbrl:entityObject in its allowedObjects`,
                        {
                            objectName: entity.name,
                            objectType: 'entity',
                            dataType: entity.dataType,
                            allowedObjects: allowedObjects,
                            errorCode: 'oimte:unallowedDatatypeObject'
                        }
                    );
                }
            }
        });
    }
}

/**
 * Validate that fact values match the data type of their associated concept
 * @param {Object} taxonomy - The taxonomy object
 */
function validateFactValueDataTypes(taxonomy) {
    if (!Array.isArray(taxonomy.facts) || !Array.isArray(taxonomy.concepts)) {
        return;
    }
    
    // Build a map of concept names to their data types
    const conceptDataTypes = new Map();
    taxonomy.concepts.forEach(concept => {
        if (concept.name && concept.dataType) {
            conceptDataTypes.set(concept.name, concept.dataType);
        }
    });
    
    // Build a map of data type names to their base types for validation
    const dataTypeMap = new Map();
    if (Array.isArray(taxonomy.dataTypes)) {
        taxonomy.dataTypes.forEach(dt => {
            if (dt.name) {
                dataTypeMap.set(dt.name, dt);
            }
        });
    }
    
    // Check each fact's values against the concept's data type
    taxonomy.facts.forEach((fact, factIdx) => {
        // Get the concept referenced by this fact
        const conceptName = fact.factDimensions?.['xbrl:concept'];
        if (!conceptName) {
            return; // No concept specified, skip validation
        }
        
        const dataType = conceptDataTypes.get(conceptName);
        if (!dataType) {
            return; // No data type specified for concept, skip validation
        }
        
        // Check each fact value
        if (Array.isArray(fact.factValues)) {
            fact.factValues.forEach((factValue, valueIdx) => {
                if (factValue.value === undefined || factValue.value === null) {
                    return; // No value to validate
                }
                
                const value = factValue.value;
                const isValid = isValueValidForDataType(value, dataType, dataTypeMap);
                
                if (!isValid) {
                    addValidationError(
                        `Fact '${fact.name}' has value '${value}' which does not match the data type '${dataType}' of concept '${conceptName}'`,
                        {
                            factName: fact.name,
                            conceptName: conceptName,
                            dataType: dataType,
                            value: value,
                            property: `facts[${factIdx}].factValues[${valueIdx}].value`,
                            errorCode: 'oimte:factValueDataTypeMismatch'
                        }
                    );
                }
            });
        }
    });
}

/**
 * Check if a value is valid for a given data type
 * @param {*} value - The value to check
 * @param {string} dataType - The data type QName
 * @param {Map} dataTypeMap - Map of data type definitions
 * @returns {boolean} True if value is valid for the data type
 */
function isValueValidForDataType(value, dataType, dataTypeMap) {
    // Get the base type - handle both custom types and XSD types
    let baseType = dataType;
    let dtDefinition = null;
    
    // If it's a custom type, get its definition
    if (dataTypeMap.has(dataType)) {
        dtDefinition = dataTypeMap.get(dataType);
        
        // Check enumeration constraint if present and not open
        if (dtDefinition.enumeration && Array.isArray(dtDefinition.enumeration) && !dtDefinition.openEnumeration) {
            // Value must be one of the enumerated values
            const valueStr = String(value);
            const isEnumerated = dtDefinition.enumeration.some(enumVal => String(enumVal) === valueStr);
            if (!isEnumerated) {
                return false; // Value not in closed enumeration
            }
            // If enumeration check passes, continue with other validations
        }
        
        if (dtDefinition.baseType) {
            baseType = dtDefinition.baseType;
        } else if (dtDefinition.baseDataType) {
            baseType = dtDefinition.baseDataType;
        }
    }
    
    // Handle common XSD and XBRL types
    const typeChecks = {
        // Numeric types
        'xbrli:monetary': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        'xbrli:sharesType': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        'xbrli:pureType': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        'xs:decimal': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        'xs:integer': (v) => typeof v === 'number' ? Number.isInteger(v) : /^-?\d+$/.test(String(v)),
        'xs:int': (v) => typeof v === 'number' ? Number.isInteger(v) : /^-?\d+$/.test(String(v)),
        'xs:long': (v) => typeof v === 'number' ? Number.isInteger(v) : /^-?\d+$/.test(String(v)),
        'xs:double': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        'xs:float': (v) => typeof v === 'number' || (!isNaN(parseFloat(v)) && isFinite(v)),
        
        // Date/time types - validate both format and actual date validity
        'xs:date': (v) => {
            const str = String(v);
            // Check format first
            if (!/^\d{4}-\d{2}-\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            // Extract date part - match just the date portion (YYYY-MM-DD)
            const match = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
            if (!match) return false;
            
            const year = parseInt(match[1], 10);
            const month = parseInt(match[2], 10);
            const day = parseInt(match[3], 10);
            
            // Validate month range
            if (month < 1 || month > 12) return false;
            
            // Validate day range for the given month
            if (day < 1) return false;
            
            // Days in month (accounting for leap years)
            const isLeapYear = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
            const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
            const maxDay = daysInMonth[month - 1];
            
            return day <= maxDay;
        },
        'xs:dateTime': (v) => {
            const str = String(v);
            // Check format first
            if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            // Extract datetime part (before timezone) using match
            const match = str.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
            if (!match) return false;
            
            const year = parseInt(match[1], 10);
            const month = parseInt(match[2], 10);
            const day = parseInt(match[3], 10);
            const hour = parseInt(match[4], 10);
            const minute = parseInt(match[5], 10);
            const second = parseInt(match[6], 10);
            
            // Validate ranges
            if (month < 1 || month > 12) return false;
            if (hour > 23 || minute > 59 || second > 59) return false;
            
            // Validate day for the month
            if (day < 1) return false;
            const isLeapYear = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
            const daysInMonth = [31, isLeapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
            const maxDay = daysInMonth[month - 1];
            
            return day <= maxDay;
        },
        'xs:time': (v) => /^\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/.test(String(v)),
        'xs:gYear': (v) => /^-?\d{4}(Z|[+-]\d{2}:\d{2})?$/.test(String(v)),
        'xs:gYearMonth': (v) => {
            const str = String(v);
            // Check format first
            if (!/^-?\d{4}-\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            // Extract year-month part using match
            const match = str.match(/^(-?\d{4})-(\d{2})/);
            if (!match) return false;
            const month = parseInt(match[2], 10);
            // Validate month is 1-12
            return month >= 1 && month <= 12;
        },
        'xs:gMonthDay': (v) => {
            const str = String(v);
            // Check format first
            if (!/^--\d{2}-\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            // Extract month-day part using match
            const match = str.match(/^--(\d{2})-(\d{2})/);
            if (!match) return false;
            const month = parseInt(match[1], 10);
            const day = parseInt(match[2], 10);
            // Validate month and day ranges (use 2020 as leap year for Feb 29)
            if (month < 1 || month > 12) return false;
            if (day < 1) return false;
            const daysInMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
            return day <= daysInMonth[month - 1];
        },
        'xs:gDay': (v) => {
            const str = String(v);
            if (!/^---\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            const dayPart = str.match(/^---(\d{2})/);
            if (!dayPart) return false;
            const day = parseInt(dayPart[1], 10);
            return day >= 1 && day <= 31;
        },
        'xs:gMonth': (v) => {
            const str = String(v);
            if (!/^--\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) {
                return false;
            }
            const monthPart = str.match(/^--(\d{2})/);
            if (!monthPart) return false;
            const month = parseInt(monthPart[1], 10);
            return month >= 1 && month <= 12;
        },
        'xs:duration': (v) => /^-?P(\d+Y)?(\d+M)?(\d+D)?(T(\d+H)?(\d+M)?(\d+(\.\d+)?S)?)?$/.test(String(v)),
        
        // Boolean
        'xs:boolean': (v) => v === true || v === false || v === 'true' || v === 'false' || v === '1' || v === '0',
        
        // String types (always valid unless restricted by pattern/enumeration)
        'xs:string': (v) => true,
        'xs:normalizedString': (v) => true,
        'xs:token': (v) => true,
        'xs:anyURI': (v) => true,
        
        // QName (basic check - just verify it has a colon)
        'xs:QName': (v) => typeof v === 'string' && v.includes(':')
    };
    
    // Check against the original dataType first (e.g., xs:date)
    // Then fall through to apply dataType constraints — do NOT return early here.
    if (typeChecks[dataType]) {
        if (!typeChecks[dataType](value)) return false;
    } else if (typeChecks[baseType]) {
        // If original dataType doesn't have a validator, check the baseType
        if (!typeChecks[baseType](value)) return false;
    }
    // If we don't have a specific validator for this type, allow the base format
    // and fall through to apply any dataType constraints below.

    // ---- Apply structural constraints from the dataType definition ----
    if (dtDefinition) {
        const valueStr = String(value);

        // --- String length constraints ---
        // xs:length: value length must equal exactly this number
        if (dtDefinition.length !== undefined && valueStr.length !== dtDefinition.length) {
            return false;
        }
        // xs:minLength: value length must be >= this number
        if (dtDefinition.minLength !== undefined && valueStr.length < dtDefinition.minLength) {
            return false;
        }
        // xs:maxLength: value length must be <= this number
        if (dtDefinition.maxLength !== undefined && valueStr.length > dtDefinition.maxLength) {
            return false;
        }

        // --- Pattern constraints (XML regex, at least one must match) ---
        if (dtDefinition.patterns && Array.isArray(dtDefinition.patterns) && dtDefinition.patterns.length > 0) {
            const matchesAny = dtDefinition.patterns.some(p => {
                try { return new RegExp(p).test(valueStr); } catch (e) { return true; }
            });
            if (!matchesAny) return false;
        }

        // --- Numeric range/precision constraints ---
        const numValue = parseFloat(value);
        if (!isNaN(numValue)) {
            // xs:minInclusive: value must be >= this
            if (dtDefinition.minInclusive !== undefined && numValue < dtDefinition.minInclusive) {
                return false;
            }
            // xs:maxInclusive: value must be <= this
            if (dtDefinition.maxInclusive !== undefined && numValue > dtDefinition.maxInclusive) {
                return false;
            }
            // xs:minExclusive: value must be > this
            if (dtDefinition.minExclusive !== undefined && numValue <= dtDefinition.minExclusive) {
                return false;
            }
            // xs:maxExclusive: value must be < this
            if (dtDefinition.maxExclusive !== undefined && numValue >= dtDefinition.maxExclusive) {
                return false;
            }
            // xs:fractionDigits: digits after decimal point must be <= this
            if (dtDefinition.fractionDigits !== undefined) {
                const dotIndex = valueStr.indexOf('.');
                const fractionLen = dotIndex >= 0 ? valueStr.length - dotIndex - 1 : 0;
                if (fractionLen > dtDefinition.fractionDigits) return false;
            }
            // xs:totalDigits: total significant digits must be <= this
            if (dtDefinition.totalDigits !== undefined) {
                const digits = valueStr.replace(/[^0-9]/g, '');
                if (digits.length > dtDefinition.totalDigits) return false;
            }
        }
    }

    return true;
}

/**
 * Validate that if an imported taxonomy has finalTaxonomy flag set,
 * the extending taxonomy only adds facts, footnotes, and entities
 * OR if finalObjectTypes is specified, only those object types are restricted
 * @param {Object} mergedXbrlModel - The fully merged xbrlModel
 * @param {Object} rawTaxonomyData - The raw taxonomy data before merging
 */
function validateFinalTaxonomyExtensions(mergedXbrlModel, rawTaxonomyData) {
    // Get xbrlModel from rawTaxonomyData, supporting both new and old property names
    const currentXbrlModel = rawTaxonomyData?.xbrlModel || rawTaxonomyData?.taxonomy;
    
    if (!currentXbrlModel) {
        return;
    }
    
    // Check if any imported taxonomies have finalTaxonomy object
    if (!Array.isArray(currentXbrlModel.importedTaxonomies)) {
        return;
    }
    
    // Check each imported xbrlModel for finalTaxonomy restrictions
    let hasFinalTaxonomyFlag = false;
    let restrictedObjectTypes = new Set();
    
    if (Array.isArray(mergedXbrlModel.importedTaxonomies)) {
        for (const imp of mergedXbrlModel.importedTaxonomies) {
            if (imp.finalTaxonomy) {
                // Check if finalTaxonomyFlag is set to true
                if (imp.finalTaxonomy.finalTaxonomyFlag === true) {
                    hasFinalTaxonomyFlag = true;
                    break; // Full restriction applies
                }
                // Check if finalObjectTypes is specified
                else if (Array.isArray(imp.finalTaxonomy.finalObjectTypes)) {
                    imp.finalTaxonomy.finalObjectTypes.forEach(objType => {
                        restrictedObjectTypes.add(objType);
                    });
                }
            }
        }
    }
    
    // Map object type QNames to property names
    const objectTypeToProperty = {
        'xbrl:conceptObject': 'concepts',
        'xbrl:abstractObject': 'abstracts',
        'xbrl:memberObject': 'members',
        'xbrl:dimensionObject': 'dimensions',
        'xbrl:domainObject': 'domains',
        'xbrl:domainClassObject': 'domainClasses',
        'xbrl:cubeObject': 'cubes',
        'xbrl:networkObject': 'networks',
        'xbrl:groupObject': 'groups',
        'xbrl:labelObject': 'labels',
        'xbrl:referenceObject': 'references',
        'xbrl:propertyTypeObject': 'propertyTypes',
        'xbrl:dataTypeObject': 'dataTypes',
        'xbrl:cubeTypeObject': 'cubeTypes',
        'xbrl:labelTypeObject': 'labelTypes',
        'xbrl:referenceTypeObject': 'referenceTypes',
        'xbrl:relationshipObject': 'relationshipTypes',
        'xbrl:unitObject': 'units',
        'xbrl:entityObject': 'entities',
        'xbrl:factObject': 'facts'
    };
    
    // If finalTaxonomyFlag is true, restrict all objects except facts, footnotes, and entities
    if (hasFinalTaxonomyFlag) {
        const restrictedProperties = [
            'concepts', 'abstracts', 'members', 'dimensions', 'domains', 'domainClasses',
            'cubes', 'networks', 'groups', 'groupContents', 'groupTree', 'labels', 'references',
            'propertyTypes', 'dataTypes', 'cubeTypes', 'labelTypes', 'referenceTypes',
            'relationshipTypes', 'units', 'transforms', 'properties'
        ];
        
        for (const prop of restrictedProperties) {
            if (currentXbrlModel[prop] && Array.isArray(currentXbrlModel[prop]) && currentXbrlModel[prop].length > 0) {
                addValidationError(
                    `Cannot extend final taxonomy with '${prop}' - only facts, footnotes, and entities are allowed`,
                    {
                        property: prop,
                        errorCode: 'oimte:invalidFinalTaxonomyModification',
                        objectCount: currentXbrlModel[prop].length
                    }
                );
            } else if (currentXbrlModel[prop] && typeof currentXbrlModel[prop] === 'object' && !Array.isArray(currentXbrlModel[prop])) {
                // Handle single object properties like groupTree
                addValidationError(
                    `Cannot extend final taxonomy with '${prop}' - only facts, footnotes, and entities are allowed`,
                    {
                        property: prop,
                        errorCode: 'oimte:invalidFinalTaxonomyModification'
                    }
                );
            }
        }
    }
    // If specific object types are restricted via finalObjectTypes
    else if (restrictedObjectTypes.size > 0) {
        for (const objectType of restrictedObjectTypes) {
            const propertyName = objectTypeToProperty[objectType];
            if (propertyName && currentXbrlModel[propertyName] && 
                Array.isArray(currentXbrlModel[propertyName]) && 
                currentXbrlModel[propertyName].length > 0) {
                addValidationError(
                    `Cannot extend taxonomy with '${propertyName}' - object type '${objectType}' is restricted by finalObjectTypes`,
                    {
                        property: propertyName,
                        restrictedObjectType: objectType,
                        errorCode: 'oimte:invalidFinalTaxonomyObjectType',
                        objectCount: currentXbrlModel[propertyName].length
                    }
                );
            }
        }
    }
    
    // Check for finalObjects restrictions (specific objects that cannot be extended)
    validateFinalObjectExtensions(mergedXbrlModel, currentXbrlModel);
}

/**
 * Validate that objects listed in finalObjects are not extended using extendTargetName
 * @param {Object} mergedXbrlModel - The fully merged xbrlModel
 * @param {Object} currentXbrlModel - The current xbrlModel being validated
 */
function validateFinalObjectExtensions(mergedXbrlModel, currentXbrlModel) {
    // Collect all finalObjects from imported taxonomies
    const finalObjects = new Set();
    
    if (Array.isArray(mergedXbrlModel.importedTaxonomies)) {
        for (const imp of mergedXbrlModel.importedTaxonomies) {
            if (imp.finalTaxonomy && Array.isArray(imp.finalTaxonomy.finalObjects)) {
                imp.finalTaxonomy.finalObjects.forEach(objName => {
                    finalObjects.add(objName);
                });
            }
        }
    }
    
    if (finalObjects.size === 0) {
        return; // No final objects to check
    }
    
    // Check networks for extendTargetName violations
    if (Array.isArray(currentXbrlModel.networks)) {
        for (const network of currentXbrlModel.networks) {
            if (network.extendTargetName && finalObjects.has(network.extendTargetName)) {
                addValidationError(
                    `Cannot extend final object '${network.extendTargetName}' - object is marked as final in imported taxonomy`,
                    {
                        objectName: network.extendTargetName,
                        objectType: 'network',
                        errorCode: 'oimte:invalidFinalTaxonomyObject'
                    }
                );
            }
        }
    }
    
    // Check domains for extendTargetName violations
    if (Array.isArray(currentXbrlModel.domains)) {
        for (const domain of currentXbrlModel.domains) {
            if (domain.extendTargetName && finalObjects.has(domain.extendTargetName)) {
                addValidationError(
                    `Cannot extend final object '${domain.extendTargetName}' - object is marked as final in imported taxonomy`,
                    {
                        objectName: domain.extendTargetName,
                        objectType: 'domain',
                        errorCode: 'oimte:invalidFinalTaxonomyObject'
                    }
                );
            }
        }
    }
    
    // Check references for extendTargetName violations
    if (Array.isArray(currentXbrlModel.references)) {
        for (const reference of currentXbrlModel.references) {
            if (reference.extendTargetName && finalObjects.has(reference.extendTargetName)) {
                addValidationError(
                    `Cannot extend final object '${reference.extendTargetName}' - object is marked as final in imported taxonomy`,
                    {
                        objectName: reference.extendTargetName,
                        objectType: 'reference',
                        errorCode: 'oimte:invalidFinalTaxonomyObject'
                    }
                );
            }
        }
    }
    
    // Check cubes for extendTargetName violations
    if (Array.isArray(currentXbrlModel.cubes)) {
        for (const cube of currentXbrlModel.cubes) {
            if (cube.extendTargetName && finalObjects.has(cube.extendTargetName)) {
                addValidationError(
                    `Cannot extend final object '${cube.extendTargetName}' - object is marked as final in imported taxonomy`,
                    {
                        objectName: cube.extendTargetName,
                        objectType: 'cube',
                        errorCode: 'oimte:invalidFinalTaxonomyObject'
                    }
                );
            }
        }
    }
}

/**
 * Validate modelType constraints on xbrlModel
 * Checks that:
 * 1. The modelType attribute references a valid modelType object
 * 2. Only allowed object types are present for the specified modelType
 * 3. Required properties for the modelType are present
 * Note: The allowedObjects constraint only applies to objects in the same namespace
 *       when modelForm is "module" or undefined. Imported objects are not validated.
 * @param {Object} taxonomy - The taxonomy object to validate
 * @param {Set<string>} definedNames - Set of defined names including modelType names
 * @param {Object} documentInfo - The documentInfo object containing namespace and modelForm
 */
function validateModelType(taxonomy, definedNames, documentInfo) {
    if (!taxonomy.modelType) {
        // modelType is optional, so no error if not specified
        return;
    }
    
    // Validate that the modelType references a valid modelType object
    if (!isValidQName(taxonomy.modelType, definedNames)) {
        addValidationError(
            `Invalid modelType '${taxonomy.modelType}' - modelType does not exist`,
            {
                errorCode: 'oimte:invalidQNameReference',
                property: 'xbrlModel.modelType',
                invalidQName: taxonomy.modelType
            }
        );
        return; // Can't continue validation if modelType is invalid
    }
    
    // Find the modelType definition
    const modelTypeDef = taxonomy.modelTypes?.find(mt => mt.name === taxonomy.modelType);
    if (!modelTypeDef) {
        // If not in this taxonomy, it might be in an imported taxonomy
        // For now, we can only validate if it's in the current taxonomy
        return;
    }
    
    // Helper function to get the namespace prefix from a QName
    function getQNamePrefix(qname) {
        if (!qname || typeof qname !== 'string') return null;
        const colonIndex = qname.indexOf(':');
        if (colonIndex === -1) return null;
        return qname.substring(0, colonIndex);
    }
    
    // Get the document namespace prefix
    const documentPrefix = documentInfo ? getDocumentNamespacePrefix(documentInfo) : null;
    
    // Check if we should validate based on modelForm
    // The allowedObjects constraint only applies when:
    // 1. modelForm is "module" or undefined, AND
    // 2. The object is in the same namespace as the document
    const shouldValidateObject = (objectName) => {
        if (!documentInfo) return false; // No documentInfo, can't validate
        
        const modelForm = documentInfo.modelForm;
        if (modelForm && modelForm !== 'module') {
            // modelForm is defined and not "module", so constraint doesn't apply
            return false;
        }
        
        if (!documentPrefix) {
            // No document namespace defined, can't determine if object is in same namespace
            return false;
        }
        
        // Check if object is in the same namespace as the document
        const objectPrefix = getQNamePrefix(objectName);
        return objectPrefix === documentPrefix;
    };
    
    // Check that all objects in the xbrlModel are allowed by the modelType
    if (modelTypeDef.allowedObjects && Array.isArray(modelTypeDef.allowedObjects)) {
        const allowedObjectTypes = new Set(modelTypeDef.allowedObjects);
        
        // Map of array names to their object types
        const objectTypeMap = [
            { array: 'concepts', objectType: 'xbrl:conceptObject' },
            { array: 'abstracts', objectType: 'xbrl:abstractObject' },
            { array: 'members', objectType: 'xbrl:memberObject' },
            { array: 'dimensions', objectType: 'xbrl:dimensionObject' },
            { array: 'domains', objectType: 'xbrl:domainObject' },
            { array: 'domainClasses', objectType: 'xbrl:domainClassObject' },
            { array: 'cubes', objectType: 'xbrl:cubeObject' },
            { array: 'networks', objectType: 'xbrl:networkObject' },
            { array: 'groups', objectType: 'xbrl:groupObject' },
            { array: 'entities', objectType: 'xbrl:entityObject' },
            { array: 'units', objectType: 'xbrl:unitObject' },
            { array: 'propertyTypes', objectType: 'xbrl:propertyTypeObject' },
            { array: 'dataTypes', objectType: 'xbrl:dataTypeObject' },
            { array: 'collections', objectType: 'xbrl:collectionObject' },
            { array: 'cubeTypes', objectType: 'xbrl:cubeTypeObject' },
            { array: 'labelTypes', objectType: 'xbrl:labelTypeObject' },
            { array: 'referenceTypes', objectType: 'xbrl:referenceTypeObject' },
            { array: 'relationshipTypes', objectType: 'xbrl:relationshipTypeObject' },
            { array: 'facts', objectType: 'xbrl:factObject' },
            { array: 'footnotes', objectType: 'xbrl:footnoteObject' },
            { array: 'labels', objectType: 'xbrl:labelObject' },
            { array: 'references', objectType: 'xbrl:referenceObject' },
            { array: 'groupTree', objectType: 'xbrl:groupTreeObject' },
            { array: 'groupContents', objectType: 'xbrl:groupContentObject' },
            { array: 'layouts', objectType: 'xbrl:layoutObject' },
            { array: 'importedTaxonomies', objectType: 'xbrl:importTaxonomyObject' },
            { array: 'finalTaxonomy', objectType: 'xbrl:finalTaxonomyObject' }
        ];
        
        objectTypeMap.forEach(({ array, objectType }) => {
            if (taxonomy[array]) {
                const isArray = Array.isArray(taxonomy[array]);
                const hasItems = isArray ? taxonomy[array].length > 0 : (typeof taxonomy[array] === 'object');
                
                if (hasItems && !allowedObjectTypes.has(objectType)) {
                    // Get the items to validate
                    const items = isArray ? taxonomy[array] : [taxonomy[array]];
                    
                    // Filter to only objects in the document namespace (when modelForm is module)
                    const itemsToValidate = items.filter(item => {
                        // Skip items without a name (imported taxonomies, etc.)
                        if (!item || !item.name) return false;
                        // Only validate if object is in document namespace
                        return shouldValidateObject(item.name);
                    });
                    
                    // Only report error if there are objects in the document namespace that violate the constraint
                    if (itemsToValidate.length > 0) {
                        const firstItem = itemsToValidate[0];
                        const itemName = firstItem?.name || 'unnamed';
                        
                        addValidationError(
                            `Object type '${objectType}' is not allowed in modelType '${taxonomy.modelType}' (only applies to objects in document namespace when modelForm is 'module')`,
                            {
                                errorCode: 'oimte:disallowedObjectModelType',
                                modelType: taxonomy.modelType,
                                objectType: objectType,
                                arrayName: array,
                                firstObjectName: itemName,
                                objectCount: itemsToValidate.length,
                                allowedObjects: Array.from(allowedObjectTypes)
                            }
                        );
                    }
                }
            }
        });
    }
    
    // Check for required properties (if modelType defines them)
    if (modelTypeDef.requiredProperties && Array.isArray(modelTypeDef.requiredProperties)) {
        modelTypeDef.requiredProperties.forEach(requiredProp => {
            const hasProperty = taxonomy.properties?.some(p => p.property === requiredProp);
            if (!hasProperty) {
                addValidationError(
                    `Missing required property '${requiredProp}' for modelType '${taxonomy.modelType}'`,
                    {
                        errorCode: 'oimte:missingRequiredModelTypeProperty',
                        modelType: taxonomy.modelType,
                        requiredProperty: requiredProp
                    }
                );
            }
        });
    }
    
    // Check for empty allowedObjects (if that's invalid)
    if (modelTypeDef.allowedObjects && Array.isArray(modelTypeDef.allowedObjects) && modelTypeDef.allowedObjects.length === 0) {
        addValidationError(
            `ModelType '${taxonomy.modelType}' has empty allowedObjects array`,
            {
                errorCode: 'oimte:invalidEmptySet',
                modelType: taxonomy.modelType,
                property: 'allowedObjects'
            }
        );
    }
}

/**
 * Validate all QName references in the taxonomy
 * @param {Object} taxonomy - The taxonomy object to validate
 * @param {Object} layout - Optional layout object to validate
 * @param {Object} documentInfo - Optional documentInfo object for namespace validation
 * @param {Object} rawTaxonomyData - Optional raw taxonomy data (before imports) for final taxonomy validation
 * @returns {Array<Object>} Array of validation errors
 */
export function validateQNameReferences(taxonomy, documentInfo = null, rawTaxonomyData = null) {
    clearValidationErrors();
    
    if (!taxonomy) {
        console.warn('[QName Validator] No taxonomy provided for validation');
        return [];
    }
    
    // All namespace validation runs against the raw (pre-merge) module using its own documentInfo.
    // The merged model's documentInfo is not used here because documentNamespace and namespaces
    // are module-level properties that disappear at the compiled-model level.
    const rawDocumentInfo = rawTaxonomyData
        ? rawTaxonomyData.documentInfo
        : documentInfo;
    const rawModel = rawTaxonomyData
        ? (rawTaxonomyData.xbrlModel || rawTaxonomyData.taxonomy)
        : taxonomy;

    if (rawDocumentInfo) {
        // Validate that documentNamespace is present (for modules) and is a defined prefix key.
        // This must run against raw documentInfo and raw model — after merging, documentNamespace
        // and modelForm may be absent from the compiled documentInfo.
        console.log('[QName Validator] Validating documentNamespace...');
        const docNsErrors = validateDocumentNamespace(rawDocumentInfo, rawModel);
        if (docNsErrors) {
            docNsErrors.forEach(e => addValidationError(e.message, e));
        }

        // Validate that no two prefixes in the namespaces map share the same URI.
        console.log('[QName Validator] Validating namespace URI uniqueness...');
        const nsUriErrors = validateNamespaceURIUniqueness(rawDocumentInfo);
        if (nsUriErrors) {
            nsUriErrors.forEach(e => addValidationError(e.message, e));
        }
    }

    if (rawModel && rawDocumentInfo) {
        // Validate that all objects in the raw module use a namespace prefix that:
        //  (a) is defined in the namespaces map, and
        //  (b) matches the documentNamespace prefix (when module-form).
        // Objects from imported taxonomies were validated against their own documentInfo
        // when those files were loaded, so checking the compiled merged model would
        // flag legitimately-imported objects as mismatches.
        console.log('[QName Validator] Validating object namespace prefixes...');
        const prefixErrors = validateObjectNamespacePrefixes(rawModel, rawDocumentInfo);
        if (prefixErrors) {
            prefixErrors.forEach(e => addValidationError(e.message, e));
        }
    }
    
    console.log('[QName Validator] Building index of defined names...');
    const definedNames = buildDefinedNamesIndex(taxonomy);
    console.log(`[QName Validator] Found ${definedNames.size} defined names`);
    
    console.log('[QName Validator] Validating allowedDomainItems...');
    validateAllowedDomainItems(taxonomy, definedNames);
    
    console.log('[QName Validator] Validating cubeDimensions...');
    validateCubeDimensions(taxonomy, definedNames);
    
    console.log('[QName Validator] Validating other QName references...');
    validateOtherQNameReferences(taxonomy, definedNames);
    
    console.log('[QName Validator] Validating relationshipTypes...');
    validateRelationshipTypes(taxonomy, definedNames);
    
    console.log('[QName Validator] Validating dataType allowedObjects...');
    validateDataTypeAllowedObjects(taxonomy);
    
    // Validate modelType constraints
    console.log('[QName Validator] Validating modelType constraints...');
    validateModelType(taxonomy, definedNames, documentInfo);
    
    // Validate final taxonomy extensions if raw taxonomy data is provided
    if (rawTaxonomyData) {
        console.log('[QName Validator] Validating final taxonomy extensions...');
        validateFinalTaxonomyExtensions(taxonomy, rawTaxonomyData);
    }
    
    // Validate layouts if provided in taxonomy
    if (taxonomy.layouts) {
        console.log('[QName Validator] Validating layouts references...');
        validateLayoutsReferences(taxonomy.layouts, definedNames);
    }
    
    // Validate fact values against concept data types
    console.log('[QName Validator] Validating fact value data types...');
    validateFactValueDataTypes(taxonomy);
    
    // Validate calculation consistency per Calculation 1.1 spec, restricted to cube-valid facts
    console.log('[QName Validator] Validating calculations (Calculation 1.1)...');
    validateCalculations(taxonomy, addValidationError);

    // Validate summation-item relationship concept property consistency (periodType + balance/weight/reconciliation)
    console.log('[QName Validator] Validating summation-item relationship concept properties...');
    validateSummationItemRelationshipProperties(taxonomy, addValidationError);

    // Validate no summation-item network contains duplicate (source, target) relationships
    console.log('[QName Validator] Validating for duplicate summation-item relationships...');
    validateDuplicateCalculationRelationships(taxonomy, addValidationError);

    console.log(`[QName Validator] Validation complete. Found ${validationErrors.length} errors.`);
    
    return validationErrors;
}
