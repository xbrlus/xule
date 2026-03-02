/**
 * Taxonomy Loader Module
 * Handles loading taxonomy files, merging imported taxonomies,
 * merging spec-taxonomies, and processing extensions.
 */

import { getTaxonomyData } from './main.js';
import { validateQNameReferences, validateObjectNamespacePrefixes } from './qname-validator.js';
import { setRawTaxonomyData, getRawTaxonomyData } from './json-view.js';
import { resetTaxonomyDetailsCache } from './tab-manager.js';
import { 
    BUILTIN_OBJECT_TYPES_MAP as BUILTIN_OBJECT_TYPES,
    OBJECT_TYPE_TO_ARRAY_MAP,
    getArrayNameForType
} from './object-types.js';
import { resolveFactValue } from './valueSource-resolver.js';

/**
 * Check if a URL is absolute (starts with http:// or https://)
 * @param {string} url - The URL to check
 * @returns {boolean} True if URL is absolute
 */
function isAbsoluteURL(url) {
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * Check if an object with the given name exists in the taxonomy
 * @param {Object} taxonomy - The taxonomy object to search
 * @param {string} objectName - The QName of the object to find
 * @returns {boolean} True if the object exists in the taxonomy
 */
function objectExistsInTaxonomy(xbrlModel, objectName) {
    if (!xbrlModel || !objectName) return false;
    
    // Check if it's the xbrlModel itself
    if (xbrlModel.name === objectName) return true;
    
    // List of array properties to check
    const arrayProperties = [
        'concepts', 'abstracts', 'members', 'dimensions', 'domains', 'domainClasses',
        'cubes', 'networks', 'propertyTypes', 'modelTypes', 'labelTypes', 'references', 'referenceTypes',
        'relationshipTypes', 'cubeTypes', 'dataTypes', 'units', 'entities', 'groups',
        'facts', 'transforms', 'factMaps', 'factSources', 'tableTemplates'
    ];
    
    // Search through all arrays
    for (const arrayName of arrayProperties) {
        if (Array.isArray(xbrlModel[arrayName])) {
            const found = xbrlModel[arrayName].some(item => item.name === objectName);
            if (found) return true;
        }
    }
    
    // Check facts.factValues (these define QNames)
    if (Array.isArray(xbrlModel.facts)) {
        for (const fact of xbrlModel.facts) {
            if (Array.isArray(fact.factValues)) {
                const found = fact.factValues.some(fv => fv.name === objectName);
                if (found) return true;
            }
        }
    }
    
    // Check groupTree
    if (xbrlModel.groupTree && xbrlModel.groupTree.name === objectName) {
        return true;
    }
    
    return false;
}

/**
 * Get the xbrlModel from taxonomyData, supporting both new 'xbrlModel' and legacy 'taxonomy' property names
 * @param {Object} taxonomyData - The taxonomy data object
 * @returns {Object|null} The xbrlModel object or null
 */
function getXbrlModel(taxonomyData) {
    return taxonomyData.xbrlModel || taxonomyData.taxonomy || null;
}

/**
 * Get the xbrlModelName from import spec, supporting both new 'xbrlModelName' and legacy 'taxonomyName' property names
 * @param {Object} importSpec - The import specification object
 * @returns {string|null} The xbrlModelName or null
 */
export function getXbrlModelName(importSpec) {
    return importSpec.xbrlModelName || importSpec.taxonomyName || null;
}

/**
 * Load a taxonomy from a given path and merge all imports
 * @param {string} path - Path to the taxonomy JSON file
 * @returns {Promise<Object>} The loaded and merged taxonomy data
 */
/**
 * Internal helper: process already-fetched taxonomy data through the full pipeline.
 * @param {Object} taxonomyData - Parsed taxonomy JSON
 * @param {string} path - The original path (or '' for content loaded from the local file system)
 */
async function _processTaxonomyData(taxonomyData, path) {
    // Store the base path for resolving relative URLs (like CSV files in factSources)
    const basePath = path ? path.substring(0, path.lastIndexOf('/') + 1) : '';
    if (!taxonomyData.documentInfo) {
        taxonomyData.documentInfo = {};
    }
    taxonomyData.documentInfo.basePath = basePath;
    console.log('[Taxonomy Loader] Base path set to:', basePath);

    // Store raw taxonomy data for Module View (before any merging) - deep copy to prevent mutations
    setRawTaxonomyData(JSON.parse(JSON.stringify(taxonomyData)));
    console.log('[Taxonomy Loader] Raw taxonomy data stored for Module View');

    // Reset pre-validation errors for this load cycle to avoid stale data from previous loads
    window._preQNameValidationErrors = [];

    // Note: documentNamespace and objectNamespacePrefix validation are both performed
    // inside validateQNameReferences using the rawTaxonomyData (pre-merge) documentInfo.
    // No separate pre-merge validation is needed here.

    // Sync with state module
    if (window.setTaxonomyData) {
        window.setTaxonomyData(taxonomyData);
    }

    // Merge imported taxonomies first
    console.time('[Taxonomy Loader] Merge Imports');
    await mergeImportedTaxonomies(path);
    console.timeEnd('[Taxonomy Loader] Merge Imports');

    // Merge spec-taxonomies files into the loaded taxonomy
    console.time('[Taxonomy Loader] Merge Spec Taxonomies');
    await mergeSpecTaxonomies();
    console.timeEnd('[Taxonomy Loader] Merge Spec Taxonomies');

    // Validate QName references BEFORE building the tree so errors can be displayed
    const updatedTaxonomyData = getTaxonomyData();
    const updatedXbrlModel = getXbrlModel(updatedTaxonomyData);
    if (updatedXbrlModel) {
        console.time('[Taxonomy Loader] Validate QNames');
        window.qnameValidationErrors = validateQNameReferences(
            updatedXbrlModel,
            updatedTaxonomyData.documentInfo || null,
            getRawTaxonomyData() // Pass raw taxonomy data for final taxonomy validation
        );
        console.timeEnd('[Taxonomy Loader] Validate QNames');

        // Merge namespace prefix errors from imported taxonomies
        // These are structural errors that exist in the imported taxonomies
        if (window._importedTaxonomyErrors && window._importedTaxonomyErrors.size > 0) {
            console.log(`[Taxonomy Loader] Checking ${window._importedTaxonomyErrors.size} imported taxonomies for namespace prefix errors`);

            for (const [taxonomyName, errors] of window._importedTaxonomyErrors.entries()) {
                if (errors && errors.length > 0) {
                    console.log(`[Taxonomy Loader]   - Processing ${errors.length} namespace prefix errors from ${taxonomyName}`);

                    // Filter errors for objects that were actually imported
                    const relevantErrors = errors.filter(error => {
                        // Namespace prefix errors have qname directly on the error object, not in context
                        const objectName = error.qname || error.context?.objectName || error.context?.qname;
                        if (objectName) {
                            // Check if this object exists in the merged xbrlModel
                            const exists = objectExistsInTaxonomy(updatedXbrlModel, objectName);
                            if (exists) {
                                console.log(`[Taxonomy Loader]     - Error for '${objectName}' is relevant (object imported)`);
                            } else {
                                console.log(`[Taxonomy Loader]     - Error for '${objectName}' is not relevant (object not imported)`);
                            }
                            return exists;
                        }
                        console.log(`[Taxonomy Loader]     - Error has no object name to check:`, error);
                        return false;
                    });

                    if (relevantErrors.length > 0) {
                        console.log(`[Taxonomy Loader]   - Propagating ${relevantErrors.length} relevant errors from ${taxonomyName}`);
                        window.qnameValidationErrors = window.qnameValidationErrors.concat(relevantErrors);
                    } else {
                        console.log(`[Taxonomy Loader]   - No relevant errors to propagate from ${taxonomyName}`);
                    }
                }
            }

            // Clear the imported errors after processing
            window._importedTaxonomyErrors.clear();
        }

        // Merge any pre-collected extension-time validation errors so they are visible to the UI
        if (window._preQNameValidationErrors && Array.isArray(window._preQNameValidationErrors) && window._preQNameValidationErrors.length > 0) {
            console.log(`[Taxonomy Loader] Merging ${window._preQNameValidationErrors.length} extension-time validation error(s)`);
            window.qnameValidationErrors = window.qnameValidationErrors.concat(window._preQNameValidationErrors);
            // Clear the pre-errors after merging
            window._preQNameValidationErrors = [];
        }
    }

    // Build the tree UI (this will display the validation errors)
    try {
        console.time('[Taxonomy Loader] Build Tree');
        if (window.buildTree) {
            window.buildTree();
        } else {
            console.warn('[Taxonomy Loader] buildTree function not available');
        }
        console.timeEnd('[Taxonomy Loader] Build Tree');
    } catch (error) {
        console.error('[Taxonomy Loader] Error building tree:', error);
    }

    // Show taxonomy details in right panel
    if (updatedXbrlModel && window.showDetails) {
        console.log('[Taxonomy Loader] Showing taxonomy details in right panel');
        // Reset the taxonomy details cache since we're loading a new taxonomy
        resetTaxonomyDetailsCache();
        window.showDetails(updatedXbrlModel, 'taxonomy');
    }

    // Switch to Model tab
    const taxonomyTab = document.querySelector('[data-tab="taxonomy"]');
    if (taxonomyTab) {
        taxonomyTab.click();
    }

    return taxonomyData;
}

export async function loadTaxonomy(path) {
    console.log('[Taxonomy Loader] Loading taxonomy from:', path);
    console.time('[Taxonomy Loader] Total Load Time');
    
    // Clear the taxonomy cache when loading a new top-level taxonomy
    taxonomyCache.clear();
    console.log('[Taxonomy Loader] Cleared taxonomy cache');
    
    // Clear previous QName validation errors
    window.qnameValidationErrors = [];
    
    // Clear previous factSource validation errors (not stored in model, reported separately)
    window.factSourceValidationErrors = [];
    
    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }
    
    try {
        console.time('[Taxonomy Loader] Initial Fetch');
        const response = await fetch(path);
        console.log('[Taxonomy Loader] Response status:', response.status);
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        let taxonomyData = await response.json();
        console.timeEnd('[Taxonomy Loader] Initial Fetch');
        console.log('[Taxonomy Loader] Taxonomy data loaded:', taxonomyData);

        const result = await _processTaxonomyData(taxonomyData, path);
        console.timeEnd('[Taxonomy Loader] Total Load Time');
        return result;
    } catch (error) {
        console.error('[Taxonomy Loader] Error loading taxonomy:', error);
        console.timeEnd('[Taxonomy Loader] Total Load Time');
        throw error;
    } finally {
        if (loading) {
            loading.style.display = 'none';
        }
    }
}

/**
 * Load a taxonomy from already-parsed JSON content (e.g. opened from the local file system).
 * Relative imports in the taxonomy will not be resolvable.
 * @param {Object} taxonomyData - Parsed taxonomy JSON object
 * @param {string} [fileName] - Display name for the file (used in logging only)
 */
export async function loadTaxonomyFromContent(taxonomyData, fileName) {
    console.log('[Taxonomy Loader] Loading taxonomy from content:', fileName || '(unnamed)');
    console.time('[Taxonomy Loader] Total Load Time');

    // Clear the taxonomy cache when loading a new top-level taxonomy
    taxonomyCache.clear();
    console.log('[Taxonomy Loader] Cleared taxonomy cache');

    // Clear previous QName validation errors
    window.qnameValidationErrors = [];

    // Clear previous factSource validation errors (not stored in model, reported separately)
    window.factSourceValidationErrors = [];

    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'block';
    }

    try {
        // Pass an empty path so imports are attempted (they may fail gracefully if relative)
        const result = await _processTaxonomyData(taxonomyData, '');
        console.timeEnd('[Taxonomy Loader] Total Load Time');
        return result;
    } catch (error) {
        console.error('[Taxonomy Loader] Error loading taxonomy from content:', error);
        console.timeEnd('[Taxonomy Loader] Total Load Time');
        throw error;
    } finally {
        if (loading) {
            loading.style.display = 'none';
        }
    }
}

/**
 * Merge imported taxonomies into the main taxonomy
 * @param {string} currentTaxonomyPath - Path to the current taxonomy file
 */
// Cache for loaded taxonomy files to avoid re-fetching the same file
const taxonomyCache = new Map();

// Track which taxonomies have been merged in the current loading session
// This prevents duplicate merges when a taxonomy is imported through multiple paths
// Key: taxonomy name, Value: 'full' (fully merged) or 'partial' (partially merged via selective import)
const mergedTaxonomies = new Map();

async function mergeImportedTaxonomies(currentTaxonomyPath) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    
    if (!xbrlModel || !xbrlModel.importedTaxonomies || xbrlModel.importedTaxonomies.length === 0) {
        console.log('[Taxonomy Loader] No imported taxonomies to merge');
        return;
    }
    
    console.log('[Taxonomy Loader] Starting merge of imported taxonomies...');
    
    // Clear the merged taxonomies map for this loading session
    mergedTaxonomies.clear();
    mergedTaxonomies.set(xbrlModel.name, 'full'); // Add the root xbrlModel as fully merged
    console.log('[Taxonomy Loader] Cleared merged taxonomies map');
    
    // Get the base path from the current taxonomy file (for relative path resolution)
    const basePath = currentTaxonomyPath.substring(0, currentTaxonomyPath.lastIndexOf('/') + 1);
    
    // Get the current xbrlModel name to avoid circular imports
    const currentXbrlModelName = xbrlModel.name;
    
    // Track the hierarchy of imports being processed (to detect circular imports)
    const importHierarchy = [currentXbrlModelName];
    
    // Process each import specification
    for (const importSpec of xbrlModel.importedTaxonomies) {
        const xbrlModelName = getXbrlModelName(importSpec);
        
        if (!xbrlModelName) {
            console.warn('[Taxonomy Loader] Imported taxonomy missing xbrlModelName/taxonomyName, skipping...');
            continue;
        }
        
        // Check if this would create a circular import (xbrlModel importing itself in the hierarchy)
        if (importHierarchy.includes(xbrlModelName)) {
            console.warn(`[Taxonomy Loader] Circular import detected: ${xbrlModelName} is already in the import hierarchy. Skipping to avoid infinite loop.`);
            continue;
        }
        
        try {
            // Recursively load the xbrlModel and all its nested imports
            const fullyLoadedXbrlModel = await loadTaxonomyRecursively(
                xbrlModelName, 
                basePath, 
                taxonomyData.documentInfo, 
                [...importHierarchy] // Pass a copy of the hierarchy
            );
            
            if (!fullyLoadedXbrlModel) {
                console.warn(`[Taxonomy Loader] Could not load xbrlModel ${xbrlModelName}`);
                continue;
            }
            
            // Store the nested imports in the import spec for UI display
            // This allows the Import Paths view to show the full hierarchy
            if (fullyLoadedXbrlModel.importedTaxonomies && fullyLoadedXbrlModel.importedTaxonomies.length > 0) {
                importSpec.nestedImports = fullyLoadedXbrlModel.importedTaxonomies;
                console.log(`[Taxonomy Loader] Stored ${fullyLoadedXbrlModel.importedTaxonomies.length} nested imports from ${xbrlModelName} in main xbrlModel`);
            }
            
            // Store the finalTaxonomy declaration if present
            // This MUST be preserved regardless of selective imports
            if (fullyLoadedXbrlModel.finalTaxonomy) {
                importSpec.finalTaxonomy = fullyLoadedXbrlModel.finalTaxonomy;
                // Store both old and new property names for backward compatibility
                importSpec.xbrlModelName = xbrlModelName;
                if (!importSpec.taxonomyName) {
                    importSpec.taxonomyName = xbrlModelName; // Backward compatibility
                }
                console.log(`[Taxonomy Loader] Stored finalTaxonomy declaration from ${xbrlModelName}:`, fullyLoadedXbrlModel.finalTaxonomy);
            }
            
            // Check if this xbrlModel should be skipped for merging (already merged elsewhere)
            if (fullyLoadedXbrlModel._skipMerge) {
                console.log(`[Taxonomy Loader] Skipping merge of ${xbrlModelName} (already merged in this session)`);
                continue;
            }
            
            // Now merge the fully loaded xbrlModel into the main xbrlModel
            // If selections is specified, only import objects matching the selection criteria
            if (importSpec.selections && Array.isArray(importSpec.selections) && importSpec.selections.length > 0) {
                console.log(`[Taxonomy Loader] Selective import using selections: ${importSpec.selections.length} selection criteria from ${xbrlModelName}`);
                mergeObjectsBySelection(xbrlModel, fullyLoadedXbrlModel, importSpec.selections, importSpec.excludeLabels, xbrlModelName);
                // Mark as partial merge (selective import)
                mergedTaxonomies.set(xbrlModelName, 'partial');
            }
            // If importObjectTypes is specified, import all objects of those types (and their dependencies)
            else if (importSpec.importObjectTypes && Array.isArray(importSpec.importObjectTypes) && importSpec.importObjectTypes.length > 0) {
                console.log(`[Taxonomy Loader] Selective import by object types: ${importSpec.importObjectTypes.length} object types from ${xbrlModelName}`);
                mergeObjectsByType(xbrlModel, fullyLoadedXbrlModel, importSpec.importObjectTypes, importSpec.excludeLabels, xbrlModelName);
                // Mark as partial merge (selective import)
                mergedTaxonomies.set(xbrlModelName, 'partial');
            }
            // If importObjects is specified, only merge those specific objects (and their dependencies)
            else if (importSpec.importObjects && Array.isArray(importSpec.importObjects) && importSpec.importObjects.length > 0) {
                console.log(`[Taxonomy Loader] Selective import: only importing ${importSpec.importObjects.length} specified objects from ${xbrlModelName}`);
                mergeSelectedObjects(xbrlModel, fullyLoadedXbrlModel, importSpec.importObjects, importSpec.excludeLabels, xbrlModelName);
                // Mark as partial merge (selective import)
                mergedTaxonomies.set(xbrlModelName, 'partial');
            } else {
                // Import all objects from the xbrlModel
                mergeArrayProperties(xbrlModel, fullyLoadedXbrlModel, xbrlModelName);
                // Mark as full merge (all objects imported)
                mergedTaxonomies.set(xbrlModelName, 'full');
            }

            // Merge sourceMapping from the imported taxonomy into the main documentInfo
            // so processFactSources can find CSV/XBRL files for imported factSources
            if (fullyLoadedXbrlModel._sourceMapping) {
                if (!taxonomyData.documentInfo) taxonomyData.documentInfo = {};
                if (!taxonomyData.documentInfo.sourceMapping) taxonomyData.documentInfo.sourceMapping = {};
                for (const [key, urls] of Object.entries(fullyLoadedXbrlModel._sourceMapping)) {
                    if (!taxonomyData.documentInfo.sourceMapping[key]) {
                        taxonomyData.documentInfo.sourceMapping[key] = urls;
                        console.log(`[Taxonomy Loader] Merged sourceMapping for '${key}' from ${xbrlModelName}`);
                    }
                }
            }
            
        } catch (error) {
            console.error(`[Taxonomy Loader] Error loading imported xbrlModel ${xbrlModelName}:`, error);
        }
    }
    
    console.log('[Taxonomy Loader] Imported taxonomies merge complete.');
    
    // After importing taxonomies, process extensions (domains/networks with extendTargetName)
    await processExtensions();
}

/**
 * Recursively load a taxonomy and all its nested imports
 * Returns a fully merged taxonomy object with all nested imports resolved
 * @param {string} taxonomyName - The QName of the taxonomy to load
 * @param {string} basePath - Base path for resolving relative file paths
 * @param {Object} documentInfo - Document info containing urlMapping
 * @param {Array<string>} importHierarchy - Array tracking the import hierarchy to detect circular imports
 * @returns {Promise<Object|null>} The fully loaded taxonomy object, or null if loading failed
 */
async function loadTaxonomyRecursively(taxonomyName, basePath, documentInfo, importHierarchy) {
    // Check if this would create a circular import
    if (importHierarchy.includes(taxonomyName)) {
        console.warn(`[Taxonomy Loader] Circular import detected: ${taxonomyName} is already in import hierarchy: ${importHierarchy.join(' -> ')} -> ${taxonomyName}. Skipping.`);
        return null;
    }
    
    // Check if this taxonomy has already been merged in this loading session
    // This prevents duplicate merges when a taxonomy is imported through multiple paths
    // (e.g., A imports B and C, both B and C import D - D should only be merged once)
    // However, if it was only partially merged (selective import), allow full merge later
    const mergeStatus = mergedTaxonomies.get(taxonomyName);
    const alreadyMerged = mergeStatus === 'full';
    
    // Check if we've already loaded this taxonomy file (use cache to avoid re-fetching)
    if (taxonomyCache.has(taxonomyName)) {
        console.log(`[Taxonomy Loader] Using cached taxonomy: ${taxonomyName}${alreadyMerged ? ' (already merged, returning for metadata only)' : ''}`);
        
        // Get the cached taxonomy
        const cachedTaxonomy = taxonomyCache.get(taxonomyName);
        
        // If already merged, return a special marker object with just metadata
        // This allows import paths to be preserved without duplicate merging
        if (alreadyMerged) {
            return {
                name: cachedTaxonomy.name,
                importedTaxonomies: cachedTaxonomy.importedTaxonomies,
                finalTaxonomy: cachedTaxonomy.finalTaxonomy,
                _skipMerge: true // Flag to indicate this should not be merged
            };
        }
        
        // Return a deep copy so each import can be processed independently
        // Don't mark as merged here - let the caller mark it after successful merge
        return JSON.parse(JSON.stringify(cachedTaxonomy));
    }
    
    // Extract the prefix from the taxonomyName
    const colonIndex = taxonomyName.indexOf(':');
    if (colonIndex === -1) {
        console.warn(`[Taxonomy Loader] Invalid taxonomyName format: ${taxonomyName} (expected prefix:name)`);
        return null;
    }
    
    const prefix = taxonomyName.substring(0, colonIndex);
    
    // Look up the files for this prefix in documentInfo.urlMapping
    if (!documentInfo || !documentInfo.urlMapping) {
        console.warn('[Taxonomy Loader] No urlMapping found in documentInfo');
        return null;
    }
    
    const files = documentInfo.urlMapping[prefix];
    if (!files || !Array.isArray(files) || files.length === 0) {
        console.warn(`[Taxonomy Loader] No files found in urlMapping for prefix: ${prefix}`);
        
        // ERROR SCENARIO 1: Namespace prefix in urlMapping does not match prefix in taxonomyName
        // Add oimte:taxonomyNotFound error
        if (!window._preQNameValidationErrors) window._preQNameValidationErrors = [];
        window._preQNameValidationErrors.push({
            message: `Taxonomy '${taxonomyName}' not found: no URL mapping for prefix '${prefix}' (oimte:taxonomyNotFound)`,
            errorCode: 'oimte:taxonomyNotFound',
            location: `importedTaxonomies[taxonomyName='${taxonomyName}']`,
            context: {
                taxonomyName: taxonomyName,
                prefix: prefix,
                reason: 'No URL mapping found for prefix'
            }
        });
        
        return null;
    }
    
    // Load the first file (assuming one taxonomy per prefix for now)
    const file = files[0];
    // Only prepend basePath if file is not already an absolute URL
    const filePath = isAbsoluteURL(file) ? file : basePath + file;
    
    console.log(`[Taxonomy Loader] Loading taxonomy from: ${filePath}`);
    
    const response = await fetch(filePath);
    if (!response.ok) {
        console.warn(`[Taxonomy Loader] Could not load ${filePath}`);
        
        // ERROR SCENARIO 2: URL defined in array is not found and cannot be loaded
        // Add oimte:taxonomyNotFound error
        if (!window._preQNameValidationErrors) window._preQNameValidationErrors = [];
        window._preQNameValidationErrors.push({
            message: `Taxonomy '${taxonomyName}' not found: file '${filePath}' could not be loaded (oimte:taxonomyNotFound)`,
            errorCode: 'oimte:taxonomyNotFound',
            location: `importedTaxonomies[taxonomyName='${taxonomyName}']`,
            context: {
                taxonomyName: taxonomyName,
                filePath: filePath,
                reason: 'File not found or could not be loaded'
            }
        });
        
        return null;
    }
    
    const taxonomyData = await response.json();
    const xbrlModel = getXbrlModel(taxonomyData);
    
    if (!xbrlModel) {
        console.warn(`[Taxonomy Loader] Invalid xbrlModel format in ${filePath} - missing 'xbrlModel' or 'taxonomy' property`);
        return null;
    }
    
    // Check if the xbrlModel name matches what we're looking for
    if (xbrlModel.name !== taxonomyName) {
        console.warn(`[Taxonomy Loader] XbrlModel name mismatch: expected ${taxonomyName}, found ${xbrlModel.name} in ${filePath}`);
        
        // ERROR SCENARIO 3: Name of xbrlModel in imported file does not match xbrlModelName in import statement
        // Add oimte:taxonomyNotFound error
        if (!window._preQNameValidationErrors) window._preQNameValidationErrors = [];
        window._preQNameValidationErrors.push({
            message: `Taxonomy '${taxonomyName}' not found: expected xbrlModel name '${taxonomyName}' but found '${xbrlModel.name}' in file '${filePath}' (oimte:taxonomyNotFound)`,
            errorCode: 'oimte:taxonomyNotFound',
            location: `importedTaxonomies[xbrlModelName='${taxonomyName}']`,
            context: {
                xbrlModelName: taxonomyName,
                actualXbrlModelName: xbrlModel.name,
                filePath: filePath,
                reason: 'XbrlModel name mismatch'
            }
        });
        
        return null;
    }
    
    console.log(`[Taxonomy Loader] Loaded ${xbrlModel.name}`);

    // Capture sourceMapping from this taxonomy's documentInfo, resolving relative URLs to
    // absolute paths so they remain valid when used from any importing taxonomy's context.
    if (taxonomyData.documentInfo && taxonomyData.documentInfo.sourceMapping) {
        xbrlModel._sourceMapping = {};
        for (const [factSourceName, urls] of Object.entries(taxonomyData.documentInfo.sourceMapping)) {
            xbrlModel._sourceMapping[factSourceName] = urls.map(url => {
                if (isAbsoluteURL(url)) return url;
                try { return new URL(url, filePath).href; } catch (e) { return url; }
            });
        }
        console.log(`[Taxonomy Loader] Captured ${Object.keys(xbrlModel._sourceMapping).length} sourceMapping entries from ${taxonomyName}`);
    }

    // Mark this taxonomy as being processed BEFORE processing nested imports
    // This prevents duplicate loads if nested imports reference the same taxonomy
    if (!mergedTaxonomies.has(xbrlModel.name)) {
        mergedTaxonomies.set(xbrlModel.name, 'partial');
        console.log(`[Taxonomy Loader] Marked ${xbrlModel.name} as 'partial' (being processed)`);
    }
    
    // Cache this xbrlModel immediately after loading (before processing nested imports)
    // This allows nested imports to find it if they reference the same taxonomy
    taxonomyCache.set(xbrlModel.name, JSON.parse(JSON.stringify(xbrlModel)));
    console.log(`[Taxonomy Loader] Cached ${xbrlModel.name}`);
    
    // Validate namespace prefixes for this imported xbrlModel
    // This catches structural errors (like using reserved 'xbrl' prefix) that need to be reported
    // even before merging. We don't validate QName references here because spec-taxonomies
    // haven't been merged yet.
    const namespacePrefixErrors = validateObjectNamespacePrefixes(xbrlModel, taxonomyData.documentInfo);
    
    if (namespacePrefixErrors && namespacePrefixErrors.length > 0) {
        console.log(`[Taxonomy Loader] Found ${namespacePrefixErrors.length} namespace prefix errors in imported xbrlModel ${xbrlModel.name}`);
        
        // Log the errors for debugging
        namespacePrefixErrors.forEach(err => {
            console.log(`[Taxonomy Loader]   - Error: ${err.errorCode} for '${err.qname}' at ${err.location}`);
        });
        
        // Store errors with the xbrlModel for later propagation
        if (!window._importedTaxonomyErrors) {
            window._importedTaxonomyErrors = new Map();
        }
        window._importedTaxonomyErrors.set(xbrlModel.name, namespacePrefixErrors);
    }
    
    // Add this xbrlModel to the import hierarchy for circular detection in nested imports
    const nestedHierarchy = [...importHierarchy, xbrlModel.name];
    
    // Process nested imports recursively
    if (xbrlModel.importedTaxonomies && 
        Array.isArray(xbrlModel.importedTaxonomies) && 
        xbrlModel.importedTaxonomies.length > 0) {
        
        console.log(`[Taxonomy Loader] Found ${xbrlModel.importedTaxonomies.length} nested imports in ${taxonomyName}`);
        
        // Calculate the basePath for nested imports relative to where THIS taxonomy is located
        // The filePath was basePath + file, so we need to get the directory of filePath
        const nestedBasePath = filePath.substring(0, filePath.lastIndexOf('/') + 1);
        console.log(`[Taxonomy Loader] Nested imports will use basePath: ${nestedBasePath}`);
        
        // Use this xbrlModel's documentInfo for resolving nested imports (not the parent's)
        // This allows each taxonomy to have its own urlMapping
        const nestedDocumentInfo = taxonomyData.documentInfo || documentInfo;
        
        // Load each nested import recursively and merge into this xbrlModel
        for (const nestedImportSpec of xbrlModel.importedTaxonomies) {
            const nestedXbrlModelName = getXbrlModelName(nestedImportSpec);
            
            if (!nestedXbrlModelName) {
                console.warn('[Taxonomy Loader] Nested import missing xbrlModelName/taxonomyName, skipping...');
                continue;
            }
            
            console.log(`[Taxonomy Loader]   - Processing nested import: ${nestedXbrlModelName}`);
            
            // Recursively load the nested xbrlModel (this will load all its descendants)
            // Pass the updated hierarchy to detect circular imports
            // Use nestedBasePath so paths are relative to THIS taxonomy's location
            const nestedXbrlModel = await loadTaxonomyRecursively(
                nestedXbrlModelName,
                nestedBasePath,
                nestedDocumentInfo,
                nestedHierarchy
            );
            
            if (!nestedXbrlModel) {
                console.warn(`[Taxonomy Loader]     - Could not load nested xbrlModel ${nestedXbrlModelName} (may be circular or not found)`);
                continue;
            }
            
            // Store the nested imports in the import spec for UI display
            // This allows the Import Paths view to show the full hierarchy
            if (nestedXbrlModel.importedTaxonomies && nestedXbrlModel.importedTaxonomies.length > 0) {
                nestedImportSpec.nestedImports = nestedXbrlModel.importedTaxonomies;
                console.log(`[Taxonomy Loader]     - Stored ${nestedXbrlModel.importedTaxonomies.length} nested imports from ${nestedXbrlModelName}`);
            }
            
            // Store the finalTaxonomy declaration if present
            // This MUST be preserved regardless of selective imports
            if (nestedXbrlModel.finalTaxonomy) {
                nestedImportSpec.finalTaxonomy = nestedXbrlModel.finalTaxonomy;
                console.log(`[Taxonomy Loader]     - Stored finalTaxonomy declaration from ${nestedXbrlModelName}:`, nestedXbrlModel.finalTaxonomy);
            }
            
            // Check if this xbrlModel should be skipped for merging (already merged elsewhere)
            if (nestedXbrlModel._skipMerge) {
                console.log(`[Taxonomy Loader]     - Skipping merge of ${nestedXbrlModelName} (already merged in this session)`);
                continue;
            }
            
            // Merge the nested xbrlModel into the current xbrlModel
            // Apply selections if specified
            if (nestedImportSpec.selections && Array.isArray(nestedImportSpec.selections) && nestedImportSpec.selections.length > 0) {
                console.log(`[Taxonomy Loader]     - Applying ${nestedImportSpec.selections.length} selections from ${nestedXbrlModelName}`);
                mergeObjectsBySelection(xbrlModel, nestedXbrlModel, nestedImportSpec.selections, nestedImportSpec.excludeLabels, nestedXbrlModelName);
            } else if (nestedImportSpec.importObjectTypes && Array.isArray(nestedImportSpec.importObjectTypes) && nestedImportSpec.importObjectTypes.length > 0) {
                console.log(`[Taxonomy Loader]     - Applying importObjectTypes from ${nestedXbrlModelName}`);
                mergeObjectsByType(xbrlModel, nestedXbrlModel, nestedImportSpec.importObjectTypes, nestedImportSpec.excludeLabels, nestedXbrlModelName);
            } else if (nestedImportSpec.importObjects && Array.isArray(nestedImportSpec.importObjects) && nestedImportSpec.importObjects.length > 0) {
                console.log(`[Taxonomy Loader]     - Applying importObjects from ${nestedXbrlModelName}`);
                mergeSelectedObjects(xbrlModel, nestedXbrlModel, nestedImportSpec.importObjects, nestedImportSpec.excludeLabels, nestedXbrlModelName);
            } else {
                console.log(`[Taxonomy Loader]     - Merging all objects from ${nestedXbrlModelName} (${nestedXbrlModel.concepts?.length || 0} concepts, ${nestedXbrlModel.dimensions?.length || 0} dimensions, ${nestedXbrlModel.domainClasses?.length || 0} domainClasses, ${nestedXbrlModel.members?.length || 0} members)`);
                mergeArrayProperties(xbrlModel, nestedXbrlModel, nestedXbrlModelName);
                console.log(`[Taxonomy Loader]     - After merge: xbrlModel now has ${xbrlModel.concepts?.length || 0} concepts, ${xbrlModel.dimensions?.length || 0} dimensions, ${xbrlModel.domainClasses?.length || 0} domainClasses, ${xbrlModel.members?.length || 0} members`);
            }

            // Propagate sourceMapping from nested imports so factSources from transitively
            // imported taxonomies can also be resolved when processFactSources runs on the root model
            if (nestedXbrlModel._sourceMapping) {
                if (!xbrlModel._sourceMapping) xbrlModel._sourceMapping = {};
                for (const [key, urls] of Object.entries(nestedXbrlModel._sourceMapping)) {
                    if (!xbrlModel._sourceMapping[key]) {
                        xbrlModel._sourceMapping[key] = urls;
                    }
                }
            }
        }
    }
    
    // Update the cache with the final merged xbrlModel (including nested imports)
    // This overwrites the earlier cache entry that was created before processing nested imports
    taxonomyCache.set(xbrlModel.name, JSON.parse(JSON.stringify(xbrlModel)));
    console.log(`[Taxonomy Loader] Updated cache for ${xbrlModel.name} with nested imports merged`);
    
    // The merge status was already set to 'partial' when we first loaded this taxonomy
    // The caller will update it to 'full' after successfully merging it into the main taxonomy
    
    // Return the fully merged xbrlModel
    return xbrlModel;
}

/**
 * Merge array properties from source into target taxonomy
 * @param {Object} targetTaxonomy - Target taxonomy object
 * @param {Object} sourceTaxonomy - Source taxonomy object
 * @param {string} sourceName - Name of source for logging
 */
function mergeArrayProperties(targetTaxonomy, sourceTaxonomy, sourceName) {
    const arrayProperties = [
        'dataTypes', 'units', 'propertyTypes', 'modelTypes', 'concepts', 'members',
        'dimensions', 'entities', 'groups', 'groupContents', 
        'relationshipTypes', 'cubes', 'networks', 'domains', 
        'domainClasses', 'labels', 'references', 'facts', 'footnotes',
        'cubeTypes', 'labelTypes', 'referenceTypes', 'abstracts', 'factMaps', 'factSources', 'transforms', 'layouts', 'tableTemplates'
    ];
    
    arrayProperties.forEach(prop => {
        if (Array.isArray(sourceTaxonomy[prop])) {
            // Initialize the array if it doesn't exist in target taxonomy
            if (!targetTaxonomy[prop]) {
                targetTaxonomy[prop] = [];
            }
            
            // Track QNames to detect duplicates within the source being merged
            const existingQNames = new Set();
            targetTaxonomy[prop].forEach(item => {
                if (item.qname || item.name) {
                    existingQNames.add(item.qname || item.name);
                }
            });
            
            // Merge the arrays, but skip items that already exist (by QName)
            const sourceItems = sourceTaxonomy[prop];
            let mergedCount = 0;
            let skippedCount = 0;
            
            for (let i = 0; i < sourceItems.length; i++) {
                const item = sourceItems[i];
                const itemQName = item.qname || item.name;
                
                // Skip if this item already exists in target
                if (itemQName && existingQNames.has(itemQName)) {
                    skippedCount++;
                    continue;
                }
                
                targetTaxonomy[prop].push(item);
                if (itemQName) {
                    existingQNames.add(itemQName);
                }
                mergedCount++;

                // If this is a factSource with embedded facts, also merge those facts
                // into the target model's top-level facts array
                if (prop === 'factSources' && Array.isArray(item.facts) && item.facts.length > 0) {
                    if (!targetTaxonomy.facts) {
                        targetTaxonomy.facts = [];
                    }
                    const existingFactNames = new Set(targetTaxonomy.facts.map(f => f.name).filter(Boolean));
                    let factsAdded = 0;
                    for (const fact of item.facts) {
                        if (!fact.name || !existingFactNames.has(fact.name)) {
                            targetTaxonomy.facts.push(fact);
                            if (fact.name) existingFactNames.add(fact.name);
                            factsAdded++;
                        }
                    }
                    if (factsAdded > 0) {
                        console.log(`[Taxonomy Loader] Propagated ${factsAdded} facts from factSource '${itemQName}' into top-level facts`);
                    }
                }
            }
            
            if (skippedCount > 0) {
                console.log(`[Taxonomy Loader] Merged ${mergedCount} ${prop} from ${sourceName} (skipped ${skippedCount} duplicates)`);
            } else {
                console.log(`[Taxonomy Loader] Merged ${mergedCount} ${prop} from ${sourceName}`);
            }
        }
    });
}

/**
 * Process extension objects (domains, networks, and references with extendTargetName)
 * These objects extend existing domains/networks/references by adding relationships/relatedNames to them
 */
async function processExtensions() {
    console.log('[Taxonomy Loader] Processing extensions...');
    console.time('[Taxonomy Loader] Process Extensions');
    
    const taxonomyData = getTaxonomyData();
    
    // Process domain extensions
    console.time('[Taxonomy Loader]   - Domain Extensions');
    processDomainExtensions(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Domain Extensions');
    
    // Process network extensions
    console.time('[Taxonomy Loader]   - Network Extensions');
    processNetworkExtensions(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Network Extensions');
    
    // Process reference extensions
    console.time('[Taxonomy Loader]   - Reference Extensions');
    processReferenceExtensions(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Reference Extensions');
    
    // Process cube extensions
    console.time('[Taxonomy Loader]   - Cube Extensions');
    processCubeExtensions(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Cube Extensions');
    
    // Process fact extensions
    console.time('[Taxonomy Loader]   - Fact Extensions');
    processFactExtensions(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Fact Extensions');
    
    // Resolve valueSources for all facts
    console.time('[Taxonomy Loader]   - Resolve ValueSources');
    await resolveFactValueSources(taxonomyData);
    console.timeEnd('[Taxonomy Loader]   - Resolve ValueSources');
    
    console.timeEnd('[Taxonomy Loader] Process Extensions');
    console.log('[Taxonomy Loader] Extension processing complete');
}

/**
 * Process domain extensions
 */
function processDomainExtensions(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.domains || !Array.isArray(xbrlModel.domains)) {
        return;
    }
    
    // OPTIMIZATION: Build lookup map first (O(n) instead of O(n²))
    const domainMap = new Map();
    xbrlModel.domains.forEach(domain => {
        if (domain.name) {
            domainMap.set(domain.name, domain);
        }
    });
    
    const extensionsToRemove = [];
    
    xbrlModel.domains.forEach((domain, index) => {
        // Check if this is an extension (has extendTargetName but no name)
        if (domain.extendTargetName && !domain.name) {
            const targetName = domain.extendTargetName;
            console.log(`[Taxonomy Loader] Found domain extension targeting: ${targetName}`);
            
            // Find the target domain to extend using O(1) Map lookup
            const targetDomain = domainMap.get(targetName);
            
            if (targetDomain) {
                    // If the target domain is marked completeDomain, importing taxonomy MUST NOT add relationships
                    if (targetDomain.completeDomain === true && domain.relationships && Array.isArray(domain.relationships) && domain.relationships.length > 0) {
                        // Record a clearer validation error to be merged into the QName validation errors later
                        if (!window._preQNameValidationErrors) window._preQNameValidationErrors = [];
                        const relCount = domain.relationships.length;
                        // Prepare a compact example list (first 3 relationships) to help debugging
                        const examples = domain.relationships.slice(0, 3).map(r => {
                            const s = r.source || '<no-source>';
                            const t = r.target || '<no-target>';
                            const rt = r.relationshipType || '';
                            return rt ? `${s} -[${rt}]-> ${t}` : `${s} -> ${t}`;
                        });

                        const message = `Cannot extend closed domain '${targetName}': the domain is marked \`completeDomain: true\` in the imported taxonomy. ` +
                            `The importing taxonomy attempted to add ${relCount} relationship${relCount === 1 ? '' : 's'}, which is not permitted. ` +
                            `Example(s): ${examples.join('; ')}.`;

                        window._preQNameValidationErrors.push({
                            message,
                            errorCode: 'oimte:cannotExtendCompleteDomain',
                            property: 'domains.relationships',
                            targetDomain: targetName,
                            attemptedRelationshipCount: relCount,
                            relationshipExamples: examples,
                            extension: domain
                        });
                        console.warn(`[Taxonomy Loader]   - Attempted to extend complete domain ${targetName}; recorded validation error (${relCount} relationships)`);
                    } else {
                        // Merge relationships from extension into target domain
                        if (domain.relationships && Array.isArray(domain.relationships)) {
                            if (!targetDomain.relationships) {
                                targetDomain.relationships = [];
                            }

                            // Add extension relationships to target
                            targetDomain.relationships.push(...domain.relationships);
                            console.log(`[Taxonomy Loader]   - Added ${domain.relationships.length} relationships to domain ${targetName}`);
                        }

                        // Merge properties from extension into target domain
                        if (domain.properties && Array.isArray(domain.properties)) {
                            if (!targetDomain.properties) {
                                targetDomain.properties = [];
                            }
                            targetDomain.properties.push(...domain.properties);
                            console.log(`[Taxonomy Loader]   - Added ${domain.properties.length} properties to domain ${targetName}`);
                        }
                    }
                
                // Mark this extension for removal
                extensionsToRemove.push(index);
            } else {
                console.warn(`[Taxonomy Loader]   - Target domain ${targetName} not found, extension will be kept`);
            }
        }
    });
    
    // Remove extensions (iterate backwards to avoid index shifting)
    for (let i = extensionsToRemove.length - 1; i >= 0; i--) {
        xbrlModel.domains.splice(extensionsToRemove[i], 1);
    }
    
    if (extensionsToRemove.length > 0) {
        console.log(`[Taxonomy Loader] Removed ${extensionsToRemove.length} domain extension(s)`);
    }
}

/**
 * Process network extensions
 */
function processNetworkExtensions(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.networks || !Array.isArray(xbrlModel.networks)) {
        return;
    }
    
    // OPTIMIZATION: Build lookup map first (O(n) instead of O(n²))
    const networkMap = new Map();
    xbrlModel.networks.forEach(network => {
        if (network.name) {
            networkMap.set(network.name, network);
        }
    });
    
    const extensionsToRemove = [];
    
    xbrlModel.networks.forEach((network, index) => {
        // Check if this is an extension (has extendTargetName but no name)
        if (network.extendTargetName && !network.name) {
            const targetName = network.extendTargetName;
            console.log(`[Taxonomy Loader] Found network extension targeting: ${targetName}`);
            
            // Find the target network to extend using O(1) Map lookup
            const targetNetwork = networkMap.get(targetName);
            
            if (targetNetwork) {
                // Merge relationships from extension into target network
                if (network.relationships && Array.isArray(network.relationships)) {
                    if (!targetNetwork.relationships) {
                        targetNetwork.relationships = [];
                    }
                    
                    // Add extension relationships to target
                    targetNetwork.relationships.push(...network.relationships);
                    console.log(`[Taxonomy Loader]   - Added ${network.relationships.length} relationships to network ${targetName}`);
                }
                
                // Merge other extensible properties if they exist
                if (network.roots && Array.isArray(network.roots)) {
                    if (!targetNetwork.roots) {
                        targetNetwork.roots = [];
                    }
                    targetNetwork.roots.push(...network.roots);
                    console.log(`[Taxonomy Loader]   - Added ${network.roots.length} roots to network ${targetName}`);
                }
                
                // Merge properties from extension into target network
                if (network.properties && Array.isArray(network.properties)) {
                    if (!targetNetwork.properties) {
                        targetNetwork.properties = [];
                    }
                    targetNetwork.properties.push(...network.properties);
                    console.log(`[Taxonomy Loader]   - Added ${network.properties.length} properties to network ${targetName}`);
                }
                
                // Mark this extension for removal
                extensionsToRemove.push(index);
            } else {
                console.warn(`[Taxonomy Loader]   - Target network ${targetName} not found, extension will be kept`);
            }
        }
    });
    
    // Remove extensions (iterate backwards to avoid index shifting)
    for (let i = extensionsToRemove.length - 1; i >= 0; i--) {
        xbrlModel.networks.splice(extensionsToRemove[i], 1);
    }
    
    if (extensionsToRemove.length > 0) {
        console.log(`[Taxonomy Loader] Removed ${extensionsToRemove.length} network extension(s)`);
    }
}

/**
 * Process reference extensions
 */
function processReferenceExtensions(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.references || !Array.isArray(xbrlModel.references)) {
        return;
    }
    
    // OPTIMIZATION: Build lookup map first (O(n) instead of O(n²))
    const referenceMap = new Map();
    xbrlModel.references.forEach(reference => {
        if (reference.name) {
            referenceMap.set(reference.name, reference);
        }
    });
    
    const extensionsToRemove = [];
    
    xbrlModel.references.forEach((reference, index) => {
        // Check if this is an extension (has extendTargetName but no name)
        if (reference.extendTargetName && !reference.name) {
            const targetName = reference.extendTargetName;
            console.log(`[Taxonomy Loader] Found reference extension targeting: ${targetName}`);
            
            // Find the target reference to extend using O(1) Map lookup
            const targetReference = referenceMap.get(targetName);
            
            if (targetReference) {
                // Merge relatedNames from extension into target reference
                if (reference.relatedNames && Array.isArray(reference.relatedNames)) {
                    if (!targetReference.relatedNames) {
                        targetReference.relatedNames = [];
                    }
                    
                    // Add extension relatedNames to target
                    targetReference.relatedNames.push(...reference.relatedNames);
                    console.log(`[Taxonomy Loader]   - Added ${reference.relatedNames.length} relatedNames to reference ${targetName}`);
                }
                
                // Mark this extension for removal
                extensionsToRemove.push(index);
            } else {
                console.warn(`[Taxonomy Loader]   - Target reference ${targetName} not found, extension will be kept`);
            }
        }
    });
    
    // Remove extensions (iterate backwards to avoid index shifting)
    for (let i = extensionsToRemove.length - 1; i >= 0; i--) {
        xbrlModel.references.splice(extensionsToRemove[i], 1);
    }
    
    if (extensionsToRemove.length > 0) {
        console.log(`[Taxonomy Loader] Removed ${extensionsToRemove.length} reference extension(s)`);
    }
}

/**
 * Process cube extensions
 */
function processCubeExtensions(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.cubes || !Array.isArray(xbrlModel.cubes)) {
        return;
    }
    
    // OPTIMIZATION: Build lookup map first (O(n) instead of O(n²))
    const cubeMap = new Map();
    xbrlModel.cubes.forEach(cube => {
        if (cube.name) {
            cubeMap.set(cube.name, cube);
        }
    });
    
    const extensionsToRemove = [];
    
    xbrlModel.cubes.forEach((cube, index) => {
        // Check if this is an extension (has extendTargetName but no name)
        if (cube.extendTargetName && !cube.name) {
            const targetName = cube.extendTargetName;
            console.log(`[Taxonomy Loader] Found cube extension targeting: ${targetName}`);
            
            // Find the target cube to extend using O(1) Map lookup
            const targetCube = cubeMap.get(targetName);
            
            if (targetCube) {
                // Merge cubeNetworks from extension into target cube
                if (cube.cubeNetworks && Array.isArray(cube.cubeNetworks)) {
                    if (!targetCube.cubeNetworks) {
                        targetCube.cubeNetworks = [];
                    }
                    
                    // Add extension cubeNetworks to target
                    targetCube.cubeNetworks.push(...cube.cubeNetworks);
                    console.log(`[Taxonomy Loader]   - Added ${cube.cubeNetworks.length} cubeNetworks to cube ${targetName}`);
                }
                
                // Merge excludeCubes from extension into target cube
                if (cube.excludeCubes && Array.isArray(cube.excludeCubes)) {
                    if (!targetCube.excludeCubes) {
                        targetCube.excludeCubes = [];
                    }
                    
                    // Add extension excludeCubes to target
                    targetCube.excludeCubes.push(...cube.excludeCubes);
                    console.log(`[Taxonomy Loader]   - Added ${cube.excludeCubes.length} excludeCubes to cube ${targetName}`);
                }
                
                // Set cubeComplete if not already set on target
                if (cube.cubeComplete !== undefined && targetCube.cubeComplete === undefined) {
                    targetCube.cubeComplete = cube.cubeComplete;
                    console.log(`[Taxonomy Loader]   - Set cubeComplete to ${cube.cubeComplete} on cube ${targetName}`);
                }
                
                // Merge properties from extension into target cube
                if (cube.properties && Array.isArray(cube.properties)) {
                    if (!targetCube.properties) {
                        targetCube.properties = [];
                    }
                    
                    // Add extension properties to target
                    targetCube.properties.push(...cube.properties);
                    console.log(`[Taxonomy Loader]   - Added ${cube.properties.length} properties to cube ${targetName}`);
                }
                
                // Mark this extension for removal
                extensionsToRemove.push(index);
            } else {
                console.warn(`[Taxonomy Loader]   - Target cube ${targetName} not found, extension will be kept`);
            }
        }
    });
    
    // Remove extensions (iterate backwards to avoid index shifting)
    for (let i = extensionsToRemove.length - 1; i >= 0; i--) {
        xbrlModel.cubes.splice(extensionsToRemove[i], 1);
    }
    
    if (extensionsToRemove.length > 0) {
        console.log(`[Taxonomy Loader] Removed ${extensionsToRemove.length} cube extension(s)`);
    }
}

/**
 * Process fact extensions
 */
function processFactExtensions(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.facts || !Array.isArray(xbrlModel.facts)) {
        return;
    }
    
    // OPTIMIZATION: Build lookup map first (O(n) instead of O(n²))
    const factMap = new Map();
    xbrlModel.facts.forEach(fact => {
        if (fact.name) {
            factMap.set(fact.name, fact);
        }
    });
    
    const extensionsToRemove = [];
    
    xbrlModel.facts.forEach((fact, index) => {
        // Check if this is an extension (has extendTargetName but no name)
        if (fact.extendTargetName && !fact.name) {
            const targetName = fact.extendTargetName;
            console.log(`[Taxonomy Loader] Found fact extension targeting: ${targetName}`);
            
            // Find the target fact to extend using O(1) Map lookup
            const targetFact = factMap.get(targetName);
            
            if (targetFact) {
                // Merge factValues from extension into target fact
                if (fact.factValues && Array.isArray(fact.factValues)) {
                    if (!targetFact.factValues) {
                        targetFact.factValues = [];
                    }
                    
                    // Add extension factValues to target
                    targetFact.factValues.push(...fact.factValues);
                    console.log(`[Taxonomy Loader]   - Added ${fact.factValues.length} factValues to fact ${targetName}`);
                }
                
                // Merge properties from extension into target fact
                if (fact.properties && Array.isArray(fact.properties)) {
                    if (!targetFact.properties) {
                        targetFact.properties = [];
                    }
                    
                    // Add extension properties to target
                    targetFact.properties.push(...fact.properties);
                    console.log(`[Taxonomy Loader]   - Added ${fact.properties.length} properties to fact ${targetName}`);
                }
                
                // Mark this extension for removal
                extensionsToRemove.push(index);
            } else {
                console.warn(`[Taxonomy Loader]   - Target fact ${targetName} not found, extension will be kept`);
            }
        }
    });
    
    // Remove extensions (iterate backwards to avoid index shifting)
    for (let i = extensionsToRemove.length - 1; i >= 0; i--) {
        xbrlModel.facts.splice(extensionsToRemove[i], 1);
    }
    
    if (extensionsToRemove.length > 0) {
        console.log(`[Taxonomy Loader] Removed ${extensionsToRemove.length} fact extension(s)`);
    }
}

/**
 * Resolve valueSources for all facts
 * This updates the fact values in place so resolved values are available throughout the application
 */
async function resolveFactValueSources(taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.facts || !Array.isArray(xbrlModel.facts)) {
        return;
    }
    
    let resolvedCount = 0;
    let errorCount = 0;
    
    // Process all facts
    for (const fact of xbrlModel.facts) {
        if (!fact.factValues || !Array.isArray(fact.factValues)) {
            continue;
        }
        
        // Process each factValue
        for (const factValue of fact.factValues) {
            // Skip if no valueSources or already has a value
            if (!factValue.valueSources || !Array.isArray(factValue.valueSources) || factValue.valueSources.length === 0) {
                continue;
            }
            
            // Skip if already has a value (explicit value takes precedence)
            if (factValue.value !== undefined && factValue.value !== null) {
                continue;
            }
            
            try {
                // Resolve the valueSource
                const resolved = await resolveFactValue(factValue);
                
                if (resolved.error) {
                    // Store error information but don't replace the factValue structure
                    factValue._resolveError = resolved.error;
                    factValue._resolveMessage = resolved.message;
                    errorCount++;
                } else if (resolved.value !== undefined && resolved.value !== null) {
                    // Update the factValue with the resolved value
                    factValue.value = resolved.value;
                    
                    // Store original value if transformation was applied
                    if (resolved.originalValue !== undefined) {
                        factValue._originalValue = resolved.originalValue;
                    }
                    
                    // Store transformation info
                    if (resolved.transformation) {
                        factValue._transformation = resolved.transformation;
                    }
                    
                    // Store source refs for display
                    if (resolved.sourceRefs && resolved.sourceRefs.length > 0) {
                        factValue._sourceRefs = resolved.sourceRefs;
                    }
                    
                    // Store escaped/concatenated flags
                    if (resolved.isEscaped) {
                        factValue._isEscaped = true;
                    }
                    if (resolved.concatenated) {
                        factValue._concatenated = true;
                    }
                    
                    resolvedCount++;
                }
            } catch (error) {
                console.error(`[Taxonomy Loader] Error resolving valueSource for fact ${fact.name}:`, error);
                factValue._resolveError = 'oimte:unknownFactTransformation';
                factValue._resolveMessage = error.message;
                errorCount++;
            }
        }
    }
    
    if (resolvedCount > 0 || errorCount > 0) {
        console.log(`[Taxonomy Loader] Resolved ${resolvedCount} fact value(s) from valueSources, ${errorCount} error(s)`);
    }
}

/**
 * Merge spec-taxonomy files into the main taxonomy
 */
async function mergeSpecTaxonomies() {
    const taxonomyData = getTaxonomyData();
    
    // List of spec-taxonomy files to merge (excluding transform-types)
    const specTaxonomyFiles = [
        'spec-taxonomies/types.json',
        'spec-taxonomies/xs-types.json',
        'spec-taxonomies/utr.json',
        'spec-taxonomies/iso4217.json',
        'spec-taxonomies/ref.json',
        'spec-taxonomies/xbrlSpec.json'
    ];
    
    console.log('[Taxonomy Loader] Starting merge of spec-taxonomies...');
    
    // Get the name of the currently loaded xbrlModel to avoid loading itself
    const xbrlModel = getXbrlModel(taxonomyData);
    const currentXbrlModelName = xbrlModel?.name;
    
    for (const file of specTaxonomyFiles) {
        try {
            const response = await fetch(file);
            if (!response.ok) {
                console.warn(`[Taxonomy Loader] Could not load ${file}, skipping...`);
                continue;
            }
            const specTaxonomy = await response.json();
            const specXbrlModel = getXbrlModel(specTaxonomy);
            
            if (specXbrlModel) {
                // Skip if the spec xbrlModel is the same as the currently loaded xbrlModel
                if (specXbrlModel.name === currentXbrlModelName) {
                    console.log(`[Taxonomy Loader] Skipping ${file} as it is the same as the currently loaded xbrlModel (${currentXbrlModelName})`);
                    continue;
                }
                
                // Merge all array properties from spec xbrlModel into main xbrlModel
                mergeArrayProperties(xbrlModel, specXbrlModel, file);
            }
        } catch (error) {
            console.warn(`[Taxonomy Loader] Error loading ${file}:`, error);
        }
    }
    
    console.log('[Taxonomy Loader] Spec-taxonomies merge complete');
}

/**
 * Merge only selected objects from source taxonomy (based on importObjects list)
 * Also imports dependencies and related labels (unless excludeLabels is true)
 * @param {Object} targetTaxonomy - Target taxonomy object
 * @param {Object} sourceTaxonomy - Source taxonomy object
 * @param {Array} importObjects - Array of QNames to import
 * @param {boolean} excludeLabels - If true, don't import related labels
 * @param {string} sourceName - Name of source for logging
 */
function mergeSelectedObjects(targetTaxonomy, sourceTaxonomy, importObjects, excludeLabels, sourceName) {
    console.log(`[Taxonomy Loader] Selective merge from ${sourceName}:`, importObjects);
    
    // Track which objects we've imported (to avoid duplicates when processing dependencies)
    const importedObjects = new Set(importObjects);
    const objectsToProcess = [...importObjects];
    const relatedLabels = new Set(); // Track labels related to imported objects
    
    // Map of property types to their arrays
    const propertyMap = {
        'concepts': 'concepts',
        'members': 'members',
        'dimensions': 'dimensions',
        'abstracts': 'abstracts',
        'entities': 'entities',
        'units': 'units',
        'dataTypes': 'dataTypes',
        'propertyTypes': 'propertyTypes',
        'modelTypes': 'modelTypes',
        'groups': 'groups',
        'groupContents': 'groupContents',
        'relationshipTypes': 'relationshipTypes',
        'cubes': 'cubes',
        'networks': 'networks',
        'domains': 'domains',
        'domainClasses': 'domainClasses',
        'references': 'references',
        'facts': 'facts',
        'cubeTypes': 'cubeTypes',
        'labelTypes': 'labelTypes',
        'referenceTypes': 'referenceTypes',
        'factMaps': 'factMaps',
        'factSources': 'factSources',
        'tableTemplates': 'tableTemplates'
    };
    
    // Helper function to find an object by name in a specific array
    function findObjectByName(arrayName, objectName) {
        const array = sourceTaxonomy[arrayName];
        if (!Array.isArray(array)) return null;
        return array.find(obj => obj.name === objectName);
    }
    
    // Helper function to add an object to target taxonomy
    function addObjectToTarget(arrayName, obj) {
        if (!targetTaxonomy[arrayName]) {
            targetTaxonomy[arrayName] = [];
        }
        
        // Check if object already exists (avoid duplicates)
        const exists = targetTaxonomy[arrayName].some(existing => existing.name === obj.name);
        if (!exists) {
            targetTaxonomy[arrayName].push(obj);
            console.log(`[Taxonomy Loader]   - Added ${arrayName.slice(0, -1)}: ${obj.name}`);

            // If this is a factSource with embedded facts, also propagate those facts
            // into the target model's top-level facts array
            if (arrayName === 'factSources' && Array.isArray(obj.facts) && obj.facts.length > 0) {
                if (!targetTaxonomy.facts) {
                    targetTaxonomy.facts = [];
                }
                const existingFactNames = new Set(targetTaxonomy.facts.map(f => f.name).filter(Boolean));
                let factsAdded = 0;
                for (const fact of obj.facts) {
                    if (!fact.name || !existingFactNames.has(fact.name)) {
                        targetTaxonomy.facts.push(fact);
                        if (fact.name) existingFactNames.add(fact.name);
                        factsAdded++;
                    }
                }
                if (factsAdded > 0) {
                    console.log(`[Taxonomy Loader]   - Propagated ${factsAdded} facts from factSource '${obj.name}' into top-level facts`);
                }
            }

            return true;
        }
        return false;
    }
    
    // Helper function to extract dependencies from an object
    function extractDependencies(obj) {
        const deps = new Set();
        
        // Check common dependency properties
        if (obj.dataType) deps.add(obj.dataType);
        if (obj.dimensionType) deps.add(obj.dimensionType);
        if (obj.cubeType) deps.add(obj.cubeType);
        if (obj.baseType) deps.add(obj.baseType);
        if (obj.itemType) deps.add(obj.itemType);
        if (obj.unitType) deps.add(obj.unitType);
        if (obj.propertyType) deps.add(obj.propertyType);
        if (obj.relationshipType) deps.add(obj.relationshipType);
        if (obj.referenceType) deps.add(obj.referenceType);

        // enumerationDomain: concepts and propertyTypes may reference a domain object via
        // enumerationDomain. That domain (and its transitive dependencies) must be included.
        if (obj.enumerationDomain) deps.add(obj.enumerationDomain);

        // properties[].property: each entry in a concept's (or other object's) properties
        // array references a propertyType by QName. Those propertyTypes are dependencies and
        // must be imported so that the property values can be validated and resolved.
        if (Array.isArray(obj.properties)) {
            obj.properties.forEach(p => {
                if (p.property && typeof p.property === 'string') deps.add(p.property);
            });
        }
        
        // Check allowedDomainItems array for QName references
        if (Array.isArray(obj.allowedDomainItems)) {
            obj.allowedDomainItems.forEach(item => {
                if (typeof item === 'string') deps.add(item);
            });
        }
        
        // Check array properties that might contain QName references
        if (Array.isArray(obj.dimensions)) {
            obj.dimensions.forEach(d => {
                if (typeof d === 'string') deps.add(d);
                else if (d.dimension) deps.add(d.dimension);
            });
        }
        
        if (Array.isArray(obj.members)) {
            obj.members.forEach(m => {
                if (typeof m === 'string') deps.add(m);
            });
        }
        
        if (Array.isArray(obj.relationships)) {
            obj.relationships.forEach(r => {
                if (r.source) deps.add(r.source);
                if (r.target) deps.add(r.target);
            });
        }
        
        return Array.from(deps);
    }
    
    // Built-in types that don't need to be imported from source taxonomies
    const builtInTypes = new Set([
        'xs:string', 'xs:boolean', 'xs:decimal', 'xs:float', 'xs:double',
        'xs:integer', 'xs:positiveInteger', 'xs:nonNegativeInteger',
        'xs:date', 'xs:time', 'xs:dateTime', 'xs:duration',
        'xs:QName', 'xs:anyURI', 'xs:language', 'xs:token',
        'xbrli:monetary', 'xbrli:shares', 'xbrli:pure',
        'xbrli:decimalItemType', 'xbrli:monetaryItemType',
        'xbrli:sharesItemType', 'xbrli:pureItemType',
        'xbrli:stringItemType', 'xbrli:booleanItemType',
        'xbrli:dateItemType', 'xbrli:dateTimeItemType'
    ]);
    
    // Process objects queue (including dependencies)
    let processedCount = 0;
    while (objectsToProcess.length > 0) {
        const objectName = objectsToProcess.shift();
        processedCount++;
        
        if (processedCount > 10000) {
            console.error('[Taxonomy Loader] Too many objects to process, possible circular dependency');
            break;
        }
        
        // Skip built-in types
        if (builtInTypes.has(objectName)) {
            continue;
        }
        
        // Search for the object in all property arrays
        let found = false;
        for (const [key, arrayName] of Object.entries(propertyMap)) {
            const obj = findObjectByName(arrayName, objectName);
            if (obj) {
                found = true;
                
                // Add the object to the target taxonomy
                if (addObjectToTarget(arrayName, obj)) {
                    // Track this object for label imports
                    relatedLabels.add(objectName);
                    
                    // Extract and queue dependencies
                    const deps = extractDependencies(obj);
                    deps.forEach(dep => {
                        if (!importedObjects.has(dep)) {
                            importedObjects.add(dep);
                            objectsToProcess.push(dep);
                            console.log(`[Taxonomy Loader]   - Queued dependency: ${dep}`);
                        }
                    });
                }
                break;
            }
        }
        
        if (!found) {
            console.warn(`[Taxonomy Loader] Object not found in source taxonomy: ${objectName}`);
        }
    }
    
    // Import related labels (unless excludeLabels is true)
    if (!excludeLabels && Array.isArray(sourceTaxonomy.labels)) {
        if (!targetTaxonomy.labels) {
            targetTaxonomy.labels = [];
        }
        
        let labelCount = 0;
        const labelTypesUsed = new Set(); // Track labelTypes used by imported labels
        
        sourceTaxonomy.labels.forEach(label => {
            // Check if this label is related to any imported object
            if (label.relatedName && relatedLabels.has(label.relatedName)) {
                // Check if label already exists (avoid duplicates)
                const exists = targetTaxonomy.labels.some(existing => 
                    existing.relatedName === label.relatedName &&
                    existing.language === label.language &&
                    existing.labelType === label.labelType
                );
                
                if (!exists) {
                    targetTaxonomy.labels.push(label);
                    labelCount++;
                    
                    // Track the labelType used by this label
                    if (label.labelType) {
                        labelTypesUsed.add(label.labelType);
                    }
                }
            }
        });
        
        if (labelCount > 0) {
            console.log(`[Taxonomy Loader] Imported ${labelCount} related labels from ${sourceName}`);
        }
        
        // Import labelType definitions for the labels we imported
        if (labelTypesUsed.size > 0 && Array.isArray(sourceTaxonomy.labelTypes)) {
            if (!targetTaxonomy.labelTypes) {
                targetTaxonomy.labelTypes = [];
            }
            
            let labelTypeCount = 0;
            labelTypesUsed.forEach(labelTypeName => {
                // Check if this labelType already exists in target taxonomy
                const exists = targetTaxonomy.labelTypes.some(existing => existing.name === labelTypeName);
                
                if (!exists) {
                    // Find the labelType definition in source taxonomy
                    const labelTypeDef = sourceTaxonomy.labelTypes.find(lt => lt.name === labelTypeName);
                    
                    if (labelTypeDef) {
                        targetTaxonomy.labelTypes.push(labelTypeDef);
                        labelTypeCount++;
                        console.log(`[Taxonomy Loader]   - Imported labelType definition: ${labelTypeName}`);
                    } else {
                        console.warn(`[Taxonomy Loader]   - labelType definition not found in source: ${labelTypeName}`);
                    }
                }
            });
            
            if (labelTypeCount > 0) {
                console.log(`[Taxonomy Loader] Imported ${labelTypeCount} labelType definitions from ${sourceName}`);
            }
        }
    } else if (excludeLabels) {
        console.log(`[Taxonomy Loader] Labels excluded from import (excludeLabels=true)`);
    }
    
    console.log(`[Taxonomy Loader] Selective merge complete: imported ${importedObjects.size} objects (including dependencies) from ${sourceName}`);
}

/**
 * Merge objects from source taxonomy by object type (importObjectTypes)
 * This imports all objects of the specified built-in object types and their dependencies
 * @param {Object} targetTaxonomy - The taxonomy to merge into
 * @param {Object} sourceTaxonomy - The taxonomy to merge from
 * @param {Array<string>} importObjectTypes - Array of built-in object type QNames (e.g., 'xbrl:memberObject')
 * @param {boolean} excludeLabels - Whether to exclude labels from import
 * @param {string} sourceName - Name of the source taxonomy (for logging)
 */
function mergeObjectsByType(targetTaxonomy, sourceTaxonomy, importObjectTypes, excludeLabels, sourceName) {
    console.log(`[Taxonomy Loader] Merge by object types from ${sourceName}:`, importObjectTypes);
    
    // Use the exported constant for object type mappings
    const objectTypeToProperty = BUILTIN_OBJECT_TYPES;
    
    // Collect all object names that match the specified types
    const objectsToImport = [];
    
    importObjectTypes.forEach(objectType => {
        const propertyName = objectTypeToProperty[objectType];
        
        if (!propertyName) {
            console.warn(`[Taxonomy Loader] Unknown or unsupported object type: ${objectType}`);
            return;
        }
        
        const sourceArray = sourceTaxonomy[propertyName];
        if (Array.isArray(sourceArray) && sourceArray.length > 0) {
            // Collect all object names from this array
            sourceArray.forEach(obj => {
                if (obj.name) {
                    objectsToImport.push(obj.name);
                }
            });
            console.log(`[Taxonomy Loader]   - Found ${sourceArray.length} ${propertyName} to import`);
        } else {
            console.log(`[Taxonomy Loader]   - No ${propertyName} found in source taxonomy`);
        }
    });
    
    if (objectsToImport.length === 0) {
        console.log(`[Taxonomy Loader] No objects found matching the specified object types`);
        return;
    }
    
    console.log(`[Taxonomy Loader] Total objects to import by type: ${objectsToImport.length}`);
    
    // Now use the existing mergeSelectedObjects function to import these objects and their dependencies
    mergeSelectedObjects(targetTaxonomy, sourceTaxonomy, objectsToImport, excludeLabels, sourceName);
}

/**
 * Parse a selection string into a selection object
 * Format: "objectType where property == value"
 * @param {string} selectionString - The selection string to parse
 * @returns {Object|null} Parsed selection object or null if invalid
 */
function parseSelectionString(selectionString) {
    if (typeof selectionString !== 'string') {
        return null;
    }
    
    // Match pattern: "objectType where property operator value"
    // Supported operators: ==, !=, >, <, >=, <=, contains
    const pattern = /^(\S+)\s+where\s+(\w+)\s+(==|!=|>=|<=|>|<|contains)\s+(.+)$/i;
    const match = selectionString.match(pattern);
    
    if (!match) {
        console.warn(`[Taxonomy Loader] Invalid selection string format: ${selectionString}`);
        return null;
    }
    
    return {
        objectType: match[1],
        where: [{
            property: match[2],
            operator: match[3],
            value: match[4].trim()
        }]
    };
}

/**
 * Evaluate whether an object matches a where clause
 * @param {Object} obj - The object to evaluate
 * @param {Object} whereClause - The where clause with property, operator, and value
 * @returns {boolean} True if object matches the where clause
 */
function matchesWhereClause(obj, whereClause) {
    if (!obj || !whereClause) {
        return false;
    }
    
    // For QName-style property names (containing a colon), look up the value inside
    // the object's `properties` array (e.g. [{ "property": "xbrla:balance", "value": "credit" }])
    // rather than directly on the object.
    let propertyValue = obj[whereClause.property];
    if (propertyValue === undefined && typeof whereClause.property === 'string' && whereClause.property.includes(':')) {
        if (Array.isArray(obj.properties)) {
            const entry = obj.properties.find(p => p.property === whereClause.property);
            if (entry !== undefined) {
                propertyValue = entry.value;
            }
        }
    }
    const expectedValue = whereClause.value;
    
    // Handle different data types
    let propVal = propertyValue;
    let expVal = expectedValue;
    
    // Try to parse as JSON if it looks like JSON
    if (typeof expectedValue === 'string') {
        if (expectedValue === 'true') expVal = true;
        else if (expectedValue === 'false') expVal = false;
        else if (expectedValue === 'null') expVal = null;
        else if (!isNaN(expectedValue)) expVal = Number(expectedValue);
        else if (expectedValue.startsWith('"') && expectedValue.endsWith('"')) {
            expVal = expectedValue.slice(1, -1); // Remove quotes
        } else if (expectedValue.startsWith("'") && expectedValue.endsWith("'")) {
            expVal = expectedValue.slice(1, -1); // Remove quotes
        }
    }
    
    // Evaluate based on operator
    switch (whereClause.operator) {
        case '==':
            return propVal == expVal;
        case '!=':
            return propVal != expVal;
        case '>':
            return propVal > expVal;
        case '<':
            return propVal < expVal;
        case '>=':
            return propVal >= expVal;
        case '<=':
            return propVal <= expVal;
        case 'contains':
            if (typeof propVal === 'string') {
                return propVal.includes(String(expVal));
            } else if (Array.isArray(propVal)) {
                return propVal.includes(expVal) || propVal.some(item => 
                    typeof item === 'object' && item !== null && Object.values(item).includes(expVal)
                );
            }
            return false;
        default:
            console.warn(`[Taxonomy Loader] Unknown operator: ${whereClause.operator}`);
            return false;
    }
}

/**
 * Evaluate whether an object matches a selection criteria
 * @param {Object} obj - The object to evaluate
 * @param {Object} selection - The selection criteria with objectType and where clauses
 * @returns {boolean} True if object matches all where clauses
 */
function matchesSelection(obj, selection) {
    if (!obj || !selection || !selection.where) {
        return false;
    }
    
    // Object must match ALL where clauses (AND logic)
    return selection.where.every(whereClause => matchesWhereClause(obj, whereClause));
}

/**
 * Merge objects from source taxonomy based on selection criteria
 * @param {Object} targetTaxonomy - Target taxonomy object
 * @param {Object} sourceTaxonomy - Source taxonomy object
 * @param {Array} selections - Array of selection criteria (objects or strings)
 * @param {boolean} excludeLabels - If true, don't import related labels
 * @param {string} sourceName - Name of source for logging
 */
function mergeObjectsBySelection(targetTaxonomy, sourceTaxonomy, selections, excludeLabels, sourceName) {
    console.log(`[Taxonomy Loader] Selection-based merge from ${sourceName}`);
    
    // Parse all selections (convert strings to objects)
    const parsedSelections = [];
    selections.forEach((selection, index) => {
        if (typeof selection === 'string') {
            const parsed = parseSelectionString(selection);
            if (parsed) {
                parsedSelections.push(parsed);
                console.log(`[Taxonomy Loader]   - Selection ${index + 1}: ${parsed.objectType} where ${parsed.where[0].property} ${parsed.where[0].operator} ${parsed.where[0].value}`);
            }
        } else if (typeof selection === 'object' && selection.objectType && selection.where && Array.isArray(selection.where)) {
            parsedSelections.push(selection);
            const whereClauses = selection.where.map(w => `${w.property} ${w.operator} ${w.value}`).join(' AND ');
            console.log(`[Taxonomy Loader]   - Selection ${index + 1}: ${selection.objectType} where ${whereClauses}`);
        } else {
            console.warn(`[Taxonomy Loader]   - Invalid selection format at index ${index}:`, selection);
        }
    });
    
    if (parsedSelections.length === 0) {
        console.warn(`[Taxonomy Loader] No valid selections found, skipping selective import`);
        return;
    }
    
    // Collect all matching objects
    const matchingObjectNames = [];
    const directLabels = []; // Labels selected directly via xbrl:labelObject selections
    
    parsedSelections.forEach(selection => {
        const arrayName = getArrayNameForType(selection.objectType);
        if (!arrayName) {
            console.warn(`[Taxonomy Loader] Unknown objectType: ${selection.objectType}`);
            return;
        }
        
        const sourceArray = sourceTaxonomy[arrayName];
        if (!Array.isArray(sourceArray)) {
            console.log(`[Taxonomy Loader] No ${arrayName} found in source taxonomy`);
            return;
        }
        
        // Find all objects matching this selection
        let matchCount = 0;
        sourceArray.forEach(obj => {
            if (matchesSelection(obj, selection)) {
                if (obj.name) {
                    matchingObjectNames.push(obj.name);
                    matchCount++;
                } else if (arrayName === 'labels' && obj.relatedName) {
                    // Labels don't have a 'name' property - collect them for direct import
                    directLabels.push(obj);
                    matchCount++;
                }
            }
        });
        
        console.log(`[Taxonomy Loader]   - Found ${matchCount} matching ${arrayName}`);
    });
    
    if (matchingObjectNames.length === 0 && directLabels.length === 0) {
        console.log(`[Taxonomy Loader] No objects matched selection criteria from ${sourceName}`);
        return;
    }
    
    console.log(`[Taxonomy Loader] Total matching objects: ${matchingObjectNames.length + directLabels.length}`);
    
    // Use existing mergeSelectedObjects function to import matching objects and their dependencies
    if (matchingObjectNames.length > 0) {
        mergeSelectedObjects(targetTaxonomy, sourceTaxonomy, matchingObjectNames, excludeLabels, sourceName);
    }
    
    // Directly import labels matched by xbrl:labelObject selections
    if (directLabels.length > 0 && !excludeLabels) {
        if (!targetTaxonomy.labels) {
            targetTaxonomy.labels = [];
        }
        let importedCount = 0;
        directLabels.forEach(label => {
            const exists = targetTaxonomy.labels.some(existing =>
                existing.relatedName === label.relatedName &&
                existing.language === label.language &&
                existing.labelType === label.labelType
            );
            if (!exists) {
                targetTaxonomy.labels.push(label);
                importedCount++;
            }
        });
        if (importedCount > 0) {
            console.log(`[Taxonomy Loader] Directly imported ${importedCount} labels from ${sourceName}`);
        }
    }
}
