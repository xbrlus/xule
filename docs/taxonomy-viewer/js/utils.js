// Utility functions for icons, labels, and UI helpers
import { getTaxonomyData, registerCacheClearFunction } from './state.js';
import { BUILTIN_OBJECT_TYPES_MAP as BUILTIN_OBJECT_TYPES } from './object-types.js';

/**
 * Get the xbrlModel from taxonomyData, supporting both new 'xbrlModel' and legacy 'taxonomy' property names
 * @param {Object} taxonomyData - The taxonomy data object
 * @returns {Object|null} The xbrlModel object or null
 */
export function getXbrlModel(taxonomyData) {
    if (!taxonomyData) return null;
    return taxonomyData.xbrlModel || taxonomyData.taxonomy || null;
}

// OPTIMIZATION: Cache for icon labels to avoid repeated array searches
let iconLabelCache = null;
let hasIconLabels = null; // null = not checked yet, true = has icons, false = no icons
let iconLabelCacheTaxonomyId = null;

/**
 * Build icon label cache from taxonomy labels
 * This is called once per taxonomy load and creates a fast lookup Map
 */
function buildIconLabelCache() {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    
    // Check if we need to rebuild cache (new taxonomy loaded)
    const currentTaxonomyId = xbrlModel?.name || null;
    if (iconLabelCacheTaxonomyId === currentTaxonomyId && iconLabelCache !== null) {
        return; // Cache is still valid
    }
    
    // Reset cache
    iconLabelCache = new Map();
    hasIconLabels = false; // Will be set to true if we find any
    iconLabelCacheTaxonomyId = currentTaxonomyId;
    
    if (!xbrlModel || !xbrlModel.labels) {
        return;
    }
    
    // Build Map of objectName -> icon value for all xbrl:iconLabel labels
    // This is O(n) once, instead of O(n) per icon lookup
    xbrlModel.labels.forEach(label => {
        if (label.labelType === 'xbrl:iconLabel' && label.relatedName) {
            iconLabelCache.set(label.relatedName, label.value);
            hasIconLabels = true;
        }
    });
    
    console.log(`[Utils] Icon label cache built: ${iconLabelCache.size} custom icons`);
}

/**
 * Clear icon label cache (call when taxonomy changes)
 */
export function clearIconLabelCache() {
    iconLabelCache = null;
    hasIconLabels = null; // Reset to "not checked yet"
    iconLabelCacheTaxonomyId = null;
}

// Register cache clearing function with state module
registerCacheClearFunction(clearIconLabelCache);

/**
 * Helper function to get icon label for a specific object name
 * Uses cached Map for O(1) lookup instead of O(n) array search
 */
function getIconLabel(objectName) {
    // Build cache if not already built
    if (iconLabelCache === null) {
        buildIconLabelCache();
    }
    
    // Fast O(1) lookup from Map
    return iconLabelCache.get(objectName) || null;
}

/**
 * Check if an object name is a built-in OBJECT TYPE using the authoritative list
 * from BUILTIN_OBJECT_TYPES constant (e.g., xbrl:conceptObject, xbrl:memberObject)
 * These are the actual object type definitions, not objects defined in taxonomies
 * Built-in object types get a star icon to distinguish them
 */
export function isBuiltInObjectType(objectName) {
    if (!objectName || typeof objectName !== 'string') {
        return false;
    }
    
    // Check if the objectName exists as a key in BUILTIN_OBJECT_TYPES
    // This is the authoritative list of built-in object types
    return objectName in BUILTIN_OBJECT_TYPES;
}

/**
 * Create a display object for a built-in object type
 * Extracts the simple name from the QName (e.g., "conceptObject" from "xbrl:conceptObject")
 * @param {string} qname - The QName of the built-in object type
 * @returns {Object} Display object with name property
 */
export function createBuiltInObjectDisplay(qname) {
    // Extract the simple name after the colon
    const colonIndex = qname.indexOf(':');
    const simpleName = colonIndex >= 0 ? qname.substring(colonIndex + 1) : qname;
    
    return {
        name: simpleName,
        qname: qname
    };
}

/**
 * Get icon for a specific object type or object name
 * If objectName is provided, checks for xbrl:iconLabel first, then checks if it's a built-in object type
 * For members without an icon label, checks if any of their domainClasses have an icon label
 * OPTIMIZED: Early exit if taxonomy has no icon labels
 */
export function getIconForType(type, objectName = null) {
    // OPTIMIZATION: Check for custom icons if objectName is provided
    if (objectName) {
        // If we haven't checked yet (hasIconLabels === null), or if we know there are icons
        if (hasIconLabels === null || hasIconLabels === true) {
            const customIcon = getIconLabel(objectName);
            if (customIcon) {
                return customIcon;
            }
            
            // NEW: If this is a member without an icon label, check its domainClasses for icons
            if (type === 'member') {
                const taxonomyData = getTaxonomyData();
                const xbrlModel = getXbrlModel(taxonomyData);
                if (xbrlModel && xbrlModel.members) {
                    const member = xbrlModel.members.find(m => m.name === objectName);
                    if (member && Array.isArray(member.domainClasses) && member.domainClasses.length > 0) {
                        // Check each domainClass for an icon label
                        for (const domainClass of member.domainClasses) {
                            const domainClassIcon = getIconLabel(domainClass);
                            if (domainClassIcon) {
                                return domainClassIcon;
                            }
                        }
                    }
                }
            }
        }
        // After first lookup, hasIconLabels will be true or false
        // If false, skip lookups for this taxonomy (performance optimization)
        
        // Check if this is a built-in object TYPE (meta-object like xbrl:conceptObject)
        if (isBuiltInObjectType(objectName)) {
            return '⭐'; // Star icon for built-in object types only
        }
    }

    const icons = {
        'concept': '📊',
        'abstract': '📁',
        'member': '🏷️',
        'dimension': '📐',
        'domain': '🌐',
        'domainClass': '🪐',
        'network': '🕸️',
        'cube': '📦',
        'unit': '⚖️',
        'entity': '🏢',
        'transform': '🔄',
        'propertyType': '🔧',
        'modelType': '🎯',
        'dataType': '🔤',
        'cubeType': '📮',
        'labelType': '🏷',
        'referenceType': '📎',
        'relationshipType': '🔗',
        'group': '👥',
        'taxonomy': '📚',
        'footnote': '📝',
        'fact': '💠',
        'layout': '⊞',
        'default': '•'
    };
    return icons[type] || icons['default'];
}

// Determine the type of a node by looking it up in taxonomy data
export function getNodeType(nodeName) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) return 'default';
    
    const typeArrays = [
        { array: 'concepts', type: 'concept' },
        { array: 'abstracts', type: 'abstract' },
        { array: 'members', type: 'member' },
        { array: 'dimensions', type: 'dimension' },
        { array: 'domainClasses', type: 'domainClass' },
        { array: 'domains', type: 'domain' },
        { array: 'units', type: 'unit' },
        { array: 'entities', type: 'entity' },
        { array: 'transforms', type: 'transform' },
        { array: 'cubes', type: 'cube' },
        { array: 'footnotes', type: 'footnote' },
        { array: 'facts', type: 'fact' },
        { array: 'layouts', type: 'layout' }
    ];
    
    for (const { array, type } of typeArrays) {
        if (xbrlModel[array]) {
            const found = xbrlModel[array].find(item => item.name === nodeName);
            if (found) return type;
        }
    }
    
    return 'default';
}

// Helper function to get the label for a node (element name)
export function getNodeLabel(nodeName, displayMode) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (displayMode === 'name' || !xbrlModel || !xbrlModel.labels) {
        return nodeName;
    }

    const label = xbrlModel.labels.find(l => 
        l.relatedName === nodeName && 
        (l.labelType === 'xbrl:label' || !l.labelType) &&
        l.language && l.language.startsWith('en')
    );

    return label ? label.value : nodeName;
}

/**
 * Format a QName for display, optionally showing its label
 * @param {string} qname - The QName to format
 * @param {boolean} showLabel - Whether to show the label (if available)
 * @returns {string} Formatted QName with optional label
 */
export function formatQNameWithLabel(qname, showLabel = true) {
    if (!showLabel) {
        return qname;
    }
    
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.labels) {
        return qname;
    }
    
    // Try to find a label for this QName
    const label = xbrlModel.labels.find(l => 
        l.relatedName === qname && 
        (l.labelType === 'xbrl:label' || !l.labelType) &&
        l.language && l.language.startsWith('en')
    );
    
    // If we have a label, show "Label (qname)", otherwise just the qname
    return label ? `${label.value} (${qname})` : qname;
}

/**
 * Format an array of QNames for display, optionally showing labels
 * @param {Array<string>} qnames - Array of QNames to format
 * @param {boolean} showLabels - Whether to show labels (if available)
 * @returns {string} Comma-separated list of formatted QNames
 */
export function formatQNameArrayWithLabels(qnames, showLabels = true) {
    if (!Array.isArray(qnames) || qnames.length === 0) {
        return '';
    }
    
    return qnames.map(qname => formatQNameWithLabel(qname, showLabels)).join(', ');
}
