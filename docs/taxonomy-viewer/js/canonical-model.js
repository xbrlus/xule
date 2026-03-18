/**
 * Canonical Model Representation
 * 
 * This module provides functionality to create canonical representations of XBRL models
 * for comparison and hashing purposes.
 */

/**
 * Properties to exclude from canonical form (non-semantic properties)
 */
const EXCLUDED_PROPERTIES = new Set([
    'basePath',
    'sourceMapping',
    'importMapping',
    'documentNamespace',
    'importedTaxonomies',
    'extendTargetName'
]);

/**
 * Properties to exclude from factSource objects in canonical form
 * - 'metadata' is operational information for lazy evaluation (includes validationTimestamp)
 * - 'facts' is the internal materialized-facts cache; the same facts appear in xbrlModel.facts
 */
const EXCLUDED_FACTSOURCE_PROPERTIES = new Set([
    'metadata',           // Operational summary (includes validationTimestamp which changes)
    'facts'               // Internal cache — materialized facts are already in xbrlModel.facts
]);

/**
 * Properties that should always appear first in their objects
 */
const FIRST_PROPERTIES = {
    'default': ['name'],
    'documentInfo': ['documentType']
};

/**
 * Array properties that contain objects to be sorted
 */
const SORTABLE_ARRAYS = new Set([
    'abstracts', 'concepts', 'cubes', 'cubeTypes', 'dataTypes', 'dimensions',
    'domains', 'domainClasses', 'entities', 'facts', 'footnotes', 'factMaps',
    'factSources', 'groups', 'groupContents', 'labels', 'members', 'modelTypes', 
    'networks', 'propertyTypes', 'references', 'referenceTypes', 'relationshipTypes',
    'units', 'transforms', 'layouts', 'properties', 'relationships',
    'cubeDimensions', 'axisHeaders', 'factValues', 'relatedNames'
]);

/**
 * Create a canonical form of an XBRL model
 * @param {Object} model - The model object containing documentInfo and xbrlModel
 * @returns {Object} The canonical form of the model
 * @throws {Error} If model is not in compiled form
 */
export function createCanonicalForm(model) {
    if (!model || !model.xbrlModel) {
        throw new Error('Invalid model: missing xbrlModel');
    }
    
    const modelForm = model.xbrlModel.modelForm || 'module';
    if (modelForm !== 'compiled') {
        throw new Error('Canonical form requires compiled model (modelForm="compiled")');
    }
    
    // Deep clone to avoid mutation
    const cloned = JSON.parse(JSON.stringify(model));
    
    // Process the model
    const canonical = {
        documentInfo: processDocumentInfo(cloned.documentInfo),
        xbrlModel: processXbrlModel(cloned.xbrlModel)
    };
    
    return canonical;
}

/**
 * Process documentInfo object for canonical form
 */
function processDocumentInfo(documentInfo) {
    if (!documentInfo) return null;
    
    const processed = {};
    
    // Get keys and filter out excluded properties
    const keys = Object.keys(documentInfo).filter(key => 
        !EXCLUDED_PROPERTIES.has(key) && 
        !isEmptyValue(documentInfo[key])
    );
    
    // Sort keys with documentType first
    const sortedKeys = sortObjectKeys(keys, 'documentInfo');
    
    // Build processed object
    for (const key of sortedKeys) {
        processed[key] = normalizeValue(documentInfo[key], key);
    }
    
    return processed;
}

/**
 * Process xbrlModel object for canonical form
 */
function processXbrlModel(xbrlModel) {
    if (!xbrlModel) return null;
    
    const processed = {};
    
    // Get keys and filter out excluded properties
    const keys = Object.keys(xbrlModel).filter(key => 
        !EXCLUDED_PROPERTIES.has(key) && 
        !isEmptyValue(xbrlModel[key])
    );
    
    // Sort keys with name first
    const sortedKeys = sortObjectKeys(keys, 'default');
    
    // Build processed object
    for (const key of sortedKeys) {
        let value = xbrlModel[key];
        
        // Special handling for factSources: include all factSources, but strip
        // operational properties (metadata, internal facts cache)
        if (key === 'factSources' && Array.isArray(value)) {
            value = processFactSources(value);
            if (value.length === 0) continue;
        }
        
        // Sort arrays if they contain objects
        if (Array.isArray(value) && SORTABLE_ARRAYS.has(key)) {
            value = sortObjectArray(value, key);
        }
        
        processed[key] = normalizeValue(value, key);
    }
    
    return processed;
}

/**
 * Process factSources array for canonical form
 * Includes all factSources (both materialized and hash-based).
 * Excludes operational properties: 'metadata' (contains validationTimestamp) and
 * 'facts' (internal cache; materialized facts already appear in xbrlModel.facts).
 */
function processFactSources(factSources) {
    if (!Array.isArray(factSources)) return [];
    
    // Process each factSource to remove operational properties
    return factSources.map(fs => {
        const processed = {};
        
        // Get keys excluding operational properties
        const keys = Object.keys(fs).filter(key => 
            !EXCLUDED_FACTSOURCE_PROPERTIES.has(key) && 
            !isEmptyValue(fs[key])
        );
        
        // Sort keys with name first
        const sortedKeys = sortObjectKeys(keys, 'default');
        
        // Build processed factSource
        for (const key of sortedKeys) {
            let value = fs[key];
            // factNames is a set (unordered) in the spec — sort it so insertion order
            // does not affect the model hash
            if (key === 'factNames' && Array.isArray(value)) {
                value = [...value].sort((a, b) => a.localeCompare(b));
            }
            processed[key] = normalizeValue(value, key);
        }
        
        return processed;
    });
}

/**
 * Sort an array of objects according to canonical rules
 */
function sortObjectArray(array, arrayName) {
    if (!array || array.length === 0) return array;
    
    // Make a copy to avoid mutation
    const sorted = [...array];
    
    // Determine sort strategy based on array type
    if (arrayName === 'labels') {
        sorted.sort((a, b) => {
            // Sort by relatedName, labelType, then language
            const relatedNameCompare = compareStrings(a.relatedName, b.relatedName);
            if (relatedNameCompare !== 0) return relatedNameCompare;
            
            const labelTypeCompare = compareStrings(a.labelType, b.labelType);
            if (labelTypeCompare !== 0) return labelTypeCompare;
            
            return compareStrings(a.language, b.language);
        });
    } else if (arrayName === 'references') {
        sorted.sort((a, b) => {
            // Sort by name, then concatenated relatedNames
            const nameCompare = compareStrings(a.name, b.name);
            if (nameCompare !== 0) return nameCompare;
            
            const relatedNamesA = (a.relatedNames || []).join('|');
            const relatedNamesB = (b.relatedNames || []).join('|');
            return compareStrings(relatedNamesA, relatedNamesB);
        });
    } else if (arrayName === 'relationships') {
        sorted.sort((a, b) => {
            // Sort by source, target, then order
            const sourceCompare = compareStrings(a.source, b.source);
            if (sourceCompare !== 0) return sourceCompare;
            
            const targetCompare = compareStrings(a.target, b.target);
            if (targetCompare !== 0) return targetCompare;
            
            return (a.order || 0) - (b.order || 0);
        });
    } else if (arrayName === 'properties') {
        sorted.sort((a, b) => {
            // Sort by property, then value
            const propertyCompare = compareStrings(a.property, b.property);
            if (propertyCompare !== 0) return propertyCompare;
            
            return compareValues(a.value, b.value);
        });
    } else if (arrayName === 'factValues') {
        sorted.sort((a, b) => compareStrings(a.name, b.name));
    } else {
        // Default: sort by name property if it exists
        sorted.sort((a, b) => compareStrings(a.name, b.name));
    }
    
    // Recursively process each object in the array
    return sorted.map(item => processObject(item));
}

/**
 * Process a single object recursively
 */
function processObject(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    
    if (Array.isArray(obj)) {
        return obj.map(item => processObject(item));
    }
    
    const processed = {};
    
    // Get keys and filter out excluded properties
    const keys = Object.keys(obj).filter(key => 
        !EXCLUDED_PROPERTIES.has(key) && 
        !isEmptyValue(obj[key])
    );
    
    // Sort keys
    const sortedKeys = sortObjectKeys(keys, 'default');
    
    // Build processed object
    for (const key of sortedKeys) {
        let value = obj[key];
        
        // Sort arrays if needed
        if (Array.isArray(value) && SORTABLE_ARRAYS.has(key)) {
            value = sortObjectArray(value, key);
        } else {
            value = normalizeValue(value, key);
        }
        
        processed[key] = value;
    }
    
    return processed;
}

/**
 * Sort object keys according to canonical rules
 */
function sortObjectKeys(keys, objectType) {
    const firstProps = FIRST_PROPERTIES[objectType] || FIRST_PROPERTIES['default'];
    
    const first = [];
    const rest = [];
    
    for (const key of keys) {
        if (firstProps.includes(key)) {
            first.push(key);
        } else {
            rest.push(key);
        }
    }
    
    // Sort first properties in their defined order
    first.sort((a, b) => firstProps.indexOf(a) - firstProps.indexOf(b));
    
    // Sort rest alphabetically
    rest.sort();
    
    return [...first, ...rest];
}

/**
 * Normalize a value according to canonical rules
 */
function normalizeValue(value, key) {
    if (value === null || value === undefined) {
        return value;
    }
    
    if (typeof value === 'string') {
        // Trim and normalize whitespace
        return value.trim().replace(/\s+/g, ' ');
    }
    
    if (typeof value === 'number') {
        // Use canonical number representation
        return value;
    }
    
    if (typeof value === 'boolean') {
        return value;
    }
    
    if (Array.isArray(value)) {
        // Filter out empty values and process each item
        const items = value
            .filter(item => !isEmptyValue(item))
            .map(item => normalizeValue(item, key));
        // Per canonical spec: sort primitive (string/number) arrays lexicographically
        // so that insertion order does not affect the model hash
        if (items.length > 0 && typeof items[0] !== 'object') {
            items.sort((a, b) => String(a).localeCompare(String(b)));
        }
        return items;
    }
    
    if (typeof value === 'object') {
        return processObject(value);
    }
    
    return value;
}

/**
 * Check if a value is considered empty for canonical form
 */
function isEmptyValue(value) {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string' && value.trim() === '') return true;
    if (Array.isArray(value) && value.length === 0) return true;
    if (typeof value === 'object' && Object.keys(value).length === 0) return true;
    return false;
}

/**
 * Compare two strings lexicographically
 */
function compareStrings(a, b) {
    const strA = String(a || '');
    const strB = String(b || '');
    return strA.localeCompare(strB);
}

/**
 * Compare two values of any type
 */
function compareValues(a, b) {
    if (typeof a === 'string' && typeof b === 'string') {
        return compareStrings(a, b);
    }
    if (typeof a === 'number' && typeof b === 'number') {
        return a - b;
    }
    // Convert to string for comparison
    return compareStrings(String(a), String(b));
}

/**
 * Generate a SHA-256 hash of the canonical model
 * @param {Object} model - The model to hash
 * @returns {Promise<string>} The hash string prefixed with version (e.g., "v1:abc123...")
 */
export async function generateModelHash(model) {
    const canonical = createCanonicalForm(model);
    const json = JSON.stringify(canonical);
    
    // Convert string to UTF-8 bytes
    const encoder = new TextEncoder();
    const data = encoder.encode(json);
    
    // Generate SHA-256 hash
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    
    // Convert to hex string
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    
    return 'v1:' + hashHex;
}

/**
 * Compare two models and check if they are semantically equivalent
 * @param {Object} model1 - First model
 * @param {Object} model2 - Second model
 * @returns {Promise<boolean>} True if models are semantically equivalent
 */
export async function areModelsEquivalent(model1, model2) {
    try {
        const hash1 = await generateModelHash(model1);
        const hash2 = await generateModelHash(model2);
        return hash1 === hash2;
    } catch (error) {
        console.error('Error comparing models:', error);
        return false;
    }
}
