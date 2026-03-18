// Utility functions for icons, labels, and UI helpers
import { getTaxonomyData, registerCacheClearFunction } from './state.js';
import { BUILTIN_OBJECT_TYPES_MAP as BUILTIN_OBJECT_TYPES } from './object-types.js';

// ---------------------------------------------------------------------------
// Module-level constant: maps taxonomy array names to the UI type string used
// by getIconForType / getNodeType. Defined once here so getNodeType doesn't
// re-allocate the array on every call.
// ---------------------------------------------------------------------------
const _NODE_TYPE_ARRAYS = [
    { array: 'concepts',         type: 'concept' },
    { array: 'abstracts',        type: 'abstract' },
    { array: 'members',          type: 'member' },
    { array: 'dimensions',       type: 'dimension' },
    { array: 'domainClasses',    type: 'domainClass' },
    { array: 'domains',          type: 'domain' },
    { array: 'units',            type: 'unit' },
    { array: 'entities',         type: 'entity' },
    { array: 'transforms',       type: 'transform' },
    { array: 'cubes',            type: 'cube' },
    { array: 'footnotes',        type: 'footnote' },
    { array: 'facts',            type: 'fact' },
    { array: 'layouts',          type: 'layout' },
    { array: 'dataTypes',        type: 'dataType' },
    { array: 'relationshipTypes',type: 'relationshipType' },
    { array: 'propertyTypes',    type: 'propertyType' },
    { array: 'cubeTypes',        type: 'cubeType' },
    { array: 'labelTypes',       type: 'labelType' },
    { array: 'referenceTypes',   type: 'referenceType' },
    { array: 'networks',         type: 'network' },
    { array: 'groups',           type: 'group' }
];

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

// ---------------------------------------------------------------------------
// Node-type cache: Map<objectName, uiTypeString> built once per taxonomy load
// so getNodeType() is O(1) instead of O(n * numArrays) on every call.
// ---------------------------------------------------------------------------
let nodeTypeCache = null;
let nodeTypeCacheTaxonomyId = null;

function buildNodeTypeCache(xbrlModel) {
    nodeTypeCache = new Map();
    nodeTypeCacheTaxonomyId = xbrlModel?.name || null;
    if (!xbrlModel) return;
    for (const { array, type } of _NODE_TYPE_ARRAYS) {
        if (Array.isArray(xbrlModel[array])) {
            for (const item of xbrlModel[array]) {
                if (item.name && !nodeTypeCache.has(item.name)) {
                    nodeTypeCache.set(item.name, type);
                }
            }
        }
    }
    console.log(`[Utils] Node type cache built: ${nodeTypeCache.size} entries`);
}

function clearNodeTypeCache() {
    nodeTypeCache = null;
    nodeTypeCacheTaxonomyId = null;
}

// ---------------------------------------------------------------------------
// Label cache: Map<relatedName, labelValue> for English xbrl:label lookups.
// Shared by getNodeLabel() and formatQNameWithLabel() so neither runs
// labels.find() (O(n)) more than once per unique name per taxonomy load.
// ---------------------------------------------------------------------------
let labelCache = null;
let labelCacheTaxonomyId = null;

function buildLabelCache(xbrlModel) {
    labelCache = new Map();
    labelCacheTaxonomyId = xbrlModel?.name || null;
    if (!xbrlModel?.labels) return;
    // Iterate once, storing the first English xbrl:label (or unlabelled label)
    // found for each relatedName — matching the predicate used by the old find() calls.
    for (const l of xbrlModel.labels) {
        if (
            !labelCache.has(l.relatedName) &&
            (l.labelType === 'xbrl:label' || !l.labelType) &&
            l.language?.startsWith('en')
        ) {
            labelCache.set(l.relatedName, l.value);
        }
    }
    console.log(`[Utils] Label cache built: ${labelCache.size} entries`);
}

function clearLabelCache() {
    labelCache = null;
    labelCacheTaxonomyId = null;
}

/**
 * Return the cached English label for a relatedName, or null if not found.
 * Builds the cache on first call for the current taxonomy.
 */
function getCachedLabel(xbrlModel, relatedName) {
    if (labelCache === null || labelCacheTaxonomyId !== (xbrlModel?.name || null)) {
        buildLabelCache(xbrlModel);
    }
    return labelCache.get(relatedName) ?? null;
}

// Register all cache clearing functions with state module
registerCacheClearFunction(clearIconLabelCache);
registerCacheClearFunction(clearNodeTypeCache);
registerCacheClearFunction(clearLabelCache);

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

// Determine the type of a node by looking it up in taxonomy data.
// OPTIMIZED: result is cached in nodeTypeCache (Map) built once per taxonomy load.
export function getNodeType(nodeName) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) return 'default';

    // Rebuild cache if taxonomy has changed or cache hasn't been built yet
    if (nodeTypeCache === null || nodeTypeCacheTaxonomyId !== (xbrlModel.name || null)) {
        buildNodeTypeCache(xbrlModel);
    }

    return nodeTypeCache.get(nodeName) ?? 'default';
}

// Helper function to get the label for a node (element name).
// OPTIMIZED: uses labelCache (built once per taxonomy load) for O(1) lookup.
export function getNodeLabel(nodeName, displayMode) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (displayMode === 'name' || !xbrlModel || !xbrlModel.labels) {
        return nodeName;
    }

    return getCachedLabel(xbrlModel, nodeName) ?? nodeName;
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
    
    // Try to find a label for this QName (O(1) via shared label cache)
    const labelValue = getCachedLabel(xbrlModel, qname);

    // If we have a label, show "Label (qname)", otherwise just the qname
    return labelValue ? `${labelValue} (${qname})` : qname;
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
