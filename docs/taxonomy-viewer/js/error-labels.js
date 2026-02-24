/**
 * Error Labels Module
 * Handles loading and accessing error labels from the error taxonomies
 */

let errorTaxonomies = [];
let errorLabelsCache = new Map();

/**
 * Load the error taxonomies (oimte.json and oime.json)
 * @returns {Promise<Array<Object>>} The loaded error taxonomies
 */
async function loadErrorTaxonomies() {
    if (errorTaxonomies.length > 0) {
        return errorTaxonomies;
    }

    const taxonomyFiles = ['spec-taxonomies/oimte.json', 'spec-taxonomies/oime.json'];
    
    try {
        const responses = await Promise.all(
            taxonomyFiles.map(file => fetch(file))
        );
        
        const taxonomies = await Promise.all(
            responses.map(async (response, index) => {
                if (!response.ok) {
                    console.warn(`Failed to load ${taxonomyFiles[index]}:`, response.statusText);
                    return null;
                }
                return await response.json();
            })
        );
        
        errorTaxonomies = taxonomies.filter(t => t !== null);
        
        // Build the labels cache from all taxonomies
        errorTaxonomies.forEach(taxonomy => {
            if (taxonomy?.taxonomy?.labels) {
                taxonomy.taxonomy.labels.forEach(label => {
                    if (label.labelType === 'xbrl:label' && label.language === 'en') {
                        errorLabelsCache.set(label.relatedName, label.value);
                    }
                });
            }
        });
        
        console.log(`Loaded ${errorLabelsCache.size} error labels from ${errorTaxonomies.length} error taxonomies`);
        return errorTaxonomies;
    } catch (error) {
        console.error('Error loading error taxonomies:', error);
        return [];
    }
}

/**
 * Get the label for an error code
 * @param {string} errorCode - The error code (e.g., 'oimte:disallowedObjectProperty')
 * @returns {string} The label for the error code, or the error code itself if not found
 */
export function getErrorLabel(errorCode) {
    // If labels haven't been loaded yet, return the error code
    if (errorLabelsCache.size === 0) {
        return errorCode;
    }
    
    return errorLabelsCache.get(errorCode) || errorCode;
}

/**
 * Get the error message template for an error code
 * @param {string} errorCode - The error code
 * @returns {string|null} The error message template, or null if not found
 */
export function getErrorMessage(errorCode) {
    if (errorTaxonomies.length === 0) {
        return null;
    }
    
    // Search through all loaded taxonomies
    for (const taxonomy of errorTaxonomies) {
        if (!taxonomy?.taxonomy?.labels) continue;
        
        const messageLabel = taxonomy.taxonomy.labels.find(
            label => label.relatedName === errorCode && 
                     label.labelType === 'oimte:errorMessage' && 
                     label.language === 'en'
        );
        
        if (messageLabel) {
            return messageLabel.value;
        }
    }
    
    return null;
}

/**
 * Initialize the error labels module
 * Should be called on page load
 */
export async function initErrorLabels() {
    await loadErrorTaxonomies();
}

/**
 * Get all error labels as a Map
 * @returns {Map<string, string>} Map of error codes to labels
 */
export function getAllErrorLabels() {
    return new Map(errorLabelsCache);
}
