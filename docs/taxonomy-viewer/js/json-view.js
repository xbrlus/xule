/**
 * JSON View Module
 * Displays a truncated view of the taxonomy JSON structure
 */

import { getTaxonomyData } from './main.js';
import { getPropertyDescription } from './spec-parser.js';
import { getXbrlModel } from './utils.js';
import { generateModelHash } from './canonical-model.js';
import { compareModels, formatDifferencesForDisplay } from './model-diff.js';

// Store the pagination state for each array
const paginationState = new Map();

// Store the collapse state for each object/array
const collapseState = new Map();

// Cache current taxonomy and documentInfo for rebuilds
let cachedTaxonomy = null;
let cachedDocumentInfo = null;

/**
 * Get the scrollable container for the current view
 * @returns {HTMLElement|null} The scrollable container element
 */
function getScrollContainer() {
    // The model and module content divs are scrollable
    const modelContent = document.querySelector('#model-view-container > div');
    const moduleContent = document.querySelector('#module-view-container > div');
    
    // Check which one is currently visible/active
    if (modelContent && modelContent.offsetParent !== null) {
        return modelContent;
    }
    if (moduleContent && moduleContent.offsetParent !== null) {
        return moduleContent;
    }
    
    return null;
}

/**
 * Rebuild the current view and restore scroll position
 * @param {string} viewType - 'model' or 'module'
 * @param {number} scrollTop - The scroll position to restore
 */
function rebuildCurrentView(viewType, scrollTop) {
    if (viewType === 'model' && cachedTaxonomy && cachedDocumentInfo) {
        const container = document.getElementById('model-view-container');
        if (container) {
            buildModelView(cachedTaxonomy, cachedDocumentInfo, container);
        }
    } else if (viewType === 'module') {
        const container = document.getElementById('module-view-container');
        if (container) {
            buildModuleView(container);
        }
    }
    
    // Restore scroll position after a short delay to allow DOM update
    setTimeout(() => {
        const container = getScrollContainer();
        if (container) {
            container.scrollTop = scrollTop;
        }
    }, 0);
}



// Store the raw taxonomy file data
let rawTaxonomyData = null;

/**
 * Set the raw taxonomy data (called when file is loaded)
 * @param {Object} data - The raw taxonomy data from the file
 */
export function setRawTaxonomyData(data) {
    rawTaxonomyData = data;
}

/**
 * Get the raw taxonomy data (before imports are merged)
 * @returns {Object|null} The raw taxonomy data
 */
export function getRawTaxonomyData() {
    return rawTaxonomyData;
}

/**
 * Copy JSON to clipboard
 * @param {Object} documentInfo - The documentInfo object
 * @param {Object} taxonomy - The taxonomy object
 * @param {string} viewType - 'model' or 'module'
 * @param {HTMLElement} button - The button element
 */
function copyJSONToClipboard(documentInfo, taxonomy, viewType, button) {
    try {
        // Build the JSON object based on view type
        let jsonObject = {};
        
        if (documentInfo) {
            // Clone documentInfo and apply filters
            const docInfoClone = { ...documentInfo };
            
            if (viewType === 'model') {
                // Filter out non-semantic properties from documentInfo in Model View
                // (matches the display filter in buildObjectDisplay)
                // NOTE: sourceMapping is retained — it is required for fact value source resolution
                // in compiled models (see spec sec-canonical-model for the distinction between
                // "excluded from canonical hash" and "absent from compiled file").
                delete docInfoClone.basePath;
                delete docInfoClone.importMapping;
                delete docInfoClone.documentNamespace;
            } else {
                // Filter out basePath in Module View
                delete docInfoClone.basePath;
            }
            
            jsonObject.documentInfo = docInfoClone;
        }
        
        if (taxonomy) {
            // Clone taxonomy and apply filters
            const taxonomyClone = { ...taxonomy };
            
            // Always filter out basePath
            delete taxonomyClone.basePath;
            
            if (viewType === 'model') {
                // Filter out importedTaxonomies in Model View
                delete taxonomyClone.importedTaxonomies;
                
                // For factSources in Model View, include all factSources but strip the internal
                // 'facts' array. Materialized sources show 'factNames'; hash-based show 'hash'/'metadata'.
                if (taxonomyClone.factSources) {
                    taxonomyClone.factSources = taxonomyClone.factSources
                        .map(fs => {
                            const fsClone = { ...fs };
                            // Remove internal materialized facts array (not part of the model schema)
                            delete fsClone.facts;
                            return fsClone;
                        });
                    
                    if (taxonomyClone.factSources.length === 0) {
                        delete taxonomyClone.factSources;
                    }
                }
                
                // Add or override modelForm to "compiled" in Model View
                taxonomyClone.modelForm = 'compiled';
            }
            
            jsonObject.xbrlModel = taxonomyClone;
        }
        
        // Convert to formatted JSON string
        const jsonString = JSON.stringify(jsonObject, null, 2);
        
        // Copy to clipboard
        navigator.clipboard.writeText(jsonString).then(() => {
            // Show success feedback
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            button.style.backgroundColor = '#51cf66';
            setTimeout(() => {
                button.textContent = originalText;
                button.style.backgroundColor = '#228be6';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy JSON:', err);
            button.textContent = 'Copy Failed';
            button.style.backgroundColor = '#ff6b6b';
            setTimeout(() => {
                button.textContent = 'Copy JSON';
                button.style.backgroundColor = '#228be6';
            }, 2000);
        });
    } catch (error) {
        console.error('Error building JSON for clipboard:', error);
        button.textContent = 'Error';
        button.style.backgroundColor = '#ff6b6b';
        setTimeout(() => {
            button.textContent = 'Copy JSON';
            button.style.backgroundColor = '#228be6';
        }, 2000);
    }
}

/**
 * Build the JSON view for a taxonomy
 * @param {Object} taxonomy - The taxonomy object to display
 * @param {Object} documentInfo - The documentInfo object
 */
export function buildJSONView(taxonomy, documentInfo) {
    console.log('[buildJSONView] Building JSON view');
    
    // Cache the data for rebuilds
    cachedTaxonomy = taxonomy;
    cachedDocumentInfo = documentInfo;
    
    const container = document.getElementById('json-view-content');
    if (!container) {
        console.error('[buildJSONView] JSON view container not found');
        return;
    }
    
    container.innerHTML = '';
    paginationState.clear();
    collapseState.clear(); // Clear collapse state when switching files
    
    // Initialize collapsed state for all top-level xbrlModel properties
    if (taxonomy) {
        Object.keys(taxonomy).forEach(key => {
            // Collapse all arrays and objects under xbrlModel by default
            const value = taxonomy[key];
            if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
                collapseState.set(`model.obj.xbrlModel.${key}`, true);
                collapseState.set(`model.arr.model.xbrlModel.${key}`, true);
            }
        });
    }

    // Initialize collapsed state for Module View top-level properties (same as Model View)
    const rawModel = rawTaxonomyData ? getXbrlModel(rawTaxonomyData) : null;
    if (rawModel) {
        Object.keys(rawModel).forEach(key => {
            const value = rawModel[key];
            if (Array.isArray(value) || (typeof value === 'object' && value !== null)) {
                collapseState.set(`module.obj.xbrlModel.${key}`, true);
                collapseState.set(`module.arr.module.xbrlModel.${key}`, true);
            }
        });
    }
    
    // Create sub-tabs for Model View and Module View
    const subTabsContainer = document.createElement('div');
    subTabsContainer.style.display = 'flex';
    subTabsContainer.style.gap = '10px';
    subTabsContainer.style.marginBottom = '15px';
    subTabsContainer.style.borderBottom = '2px solid #dee2e6';
    subTabsContainer.style.paddingBottom = '5px';
    
    const modelViewButton = document.createElement('button');
    modelViewButton.textContent = 'Model View';
    modelViewButton.className = 'json-sub-tab active';
    modelViewButton.style.padding = '8px 16px';
    modelViewButton.style.border = 'none';
    modelViewButton.style.backgroundColor = '#228be6';
    modelViewButton.style.color = 'white';
    modelViewButton.style.borderRadius = '4px 4px 0 0';
    modelViewButton.style.cursor = 'pointer';
    modelViewButton.style.fontSize = '14px';
    modelViewButton.style.fontWeight = 'bold';
    
    const moduleViewButton = document.createElement('button');
    moduleViewButton.textContent = 'Module View';
    moduleViewButton.className = 'json-sub-tab';
    moduleViewButton.style.padding = '8px 16px';
    moduleViewButton.style.border = 'none';
    moduleViewButton.style.backgroundColor = '#e9ecef';
    moduleViewButton.style.color = '#495057';
    moduleViewButton.style.borderRadius = '4px 4px 0 0';
    moduleViewButton.style.cursor = 'pointer';
    moduleViewButton.style.fontSize = '14px';
    
    subTabsContainer.appendChild(modelViewButton);
    subTabsContainer.appendChild(moduleViewButton);
    container.appendChild(subTabsContainer);
    
    // Create containers for each view
    const modelViewContainer = document.createElement('div');
    modelViewContainer.id = 'model-view-container';
    modelViewContainer.style.display = 'block';
    
    const moduleViewContainer = document.createElement('div');
    moduleViewContainer.id = 'module-view-container';
    moduleViewContainer.style.display = 'none';
    
    container.appendChild(modelViewContainer);
    container.appendChild(moduleViewContainer);
    
    // Build Model View (merged taxonomy)
    buildModelView(taxonomy, documentInfo, modelViewContainer);
    
    // Build Module View (raw file)
    buildModuleView(moduleViewContainer);
    
    // Add click handlers for sub-tabs
    modelViewButton.addEventListener('click', () => {
        modelViewButton.style.backgroundColor = '#228be6';
        modelViewButton.style.color = 'white';
        moduleViewButton.style.backgroundColor = '#e9ecef';
        moduleViewButton.style.color = '#495057';
        modelViewContainer.style.display = 'block';
        moduleViewContainer.style.display = 'none';
    });
    
    moduleViewButton.addEventListener('click', () => {
        moduleViewButton.style.backgroundColor = '#228be6';
        moduleViewButton.style.color = 'white';
        modelViewButton.style.backgroundColor = '#e9ecef';
        modelViewButton.style.color = '#495057';
        moduleViewContainer.style.display = 'block';
        modelViewContainer.style.display = 'none';
    });
}

/**
 * Build the Model View (merged taxonomy)
 * @param {Object} taxonomy - The taxonomy object to display
 * @param {Object} documentInfo - The documentInfo object
 * @param {HTMLElement} container - The container element
 */
function buildModelView(taxonomy, documentInfo, container) {
    container.innerHTML = '';
    
    // Create wrapper with styling
    const wrapper = document.createElement('div');
    wrapper.style.fontFamily = 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace';
    wrapper.style.fontSize = '13px';
    wrapper.style.lineHeight = '1.6';
    wrapper.style.padding = '15px';
    wrapper.style.backgroundColor = '#f8f9fa';
    wrapper.style.borderRadius = '4px';
    wrapper.style.overflow = 'auto';
    wrapper.style.maxHeight = 'calc(100vh - 250px)';
    wrapper.style.height = '100%';
    
    // Title
    const title = document.createElement('h3');
    title.textContent = 'Model View - Complete Merged Taxonomy';
    title.style.marginTop = '0';
    title.style.marginBottom = '15px';
    title.style.color = '#228be6';
    wrapper.appendChild(title);
    
    // Description
    const description = document.createElement('p');
    description.textContent = 'This view shows the complete merged taxonomy model including all imported taxonomies and spec-taxonomies. Arrays are limited to 5 items initially. Use "Show Next 5" buttons to load more.';
    description.style.color = '#495057';
    description.style.marginBottom = '20px';
    wrapper.appendChild(description);
    
    // Model Comparison Controls
    const comparisonControls = createModelComparisonControls(taxonomy, documentInfo);
    wrapper.appendChild(comparisonControls);
    
    // Build the JSON structure
    const jsonDisplay = document.createElement('pre');
    jsonDisplay.style.margin = '0';
    jsonDisplay.style.whiteSpace = 'pre-wrap';
    jsonDisplay.style.wordBreak = 'break-word';
    
    // Build the content
    const content = buildJSONStructure(documentInfo, taxonomy, 'model');
    jsonDisplay.appendChild(content);
    
    wrapper.appendChild(jsonDisplay);
    
    // Add copy button
    const copyButton = document.createElement('button');
    copyButton.textContent = 'Copy JSON';
    copyButton.style.marginTop = '15px';
    copyButton.style.padding = '8px 16px';
    copyButton.style.backgroundColor = '#228be6';
    copyButton.style.color = 'white';
    copyButton.style.border = 'none';
    copyButton.style.borderRadius = '4px';
    copyButton.style.cursor = 'pointer';
    copyButton.style.fontSize = '13px';
    copyButton.addEventListener('click', () => copyJSONToClipboard(documentInfo, taxonomy, 'model', copyButton));
    wrapper.appendChild(copyButton);
    
    container.appendChild(wrapper);
}

/**
 * Build the Module View (raw file)
 * @param {HTMLElement} container - The container element
 */
function buildModuleView(container) {
    container.innerHTML = '';
    
    // Create wrapper with styling
    const wrapper = document.createElement('div');
    wrapper.style.fontFamily = 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace';
    wrapper.style.fontSize = '13px';
    wrapper.style.lineHeight = '1.6';
    wrapper.style.padding = '15px';
    wrapper.style.backgroundColor = '#f8f9fa';
    wrapper.style.borderRadius = '4px';
    wrapper.style.overflow = 'auto';
    wrapper.style.maxHeight = 'calc(100vh - 250px)';
    wrapper.style.height = '100%';
    
    // Title
    const title = document.createElement('h3');
    title.textContent = 'Module View - Source File';
    title.style.marginTop = '0';
    title.style.marginBottom = '15px';
    title.style.color = '#228be6';
    wrapper.appendChild(title);
    
    // Description
    const description = document.createElement('p');
    description.textContent = 'This view shows the raw JSON from the source taxonomy file (without merged imports). Arrays are limited to 5 items initially. Use "Show Next 5" buttons to load more.';
    description.style.color = '#495057';
    description.style.marginBottom = '20px';
    wrapper.appendChild(description);
    
    if (!rawTaxonomyData) {
        const noDataMsg = document.createElement('p');
        noDataMsg.textContent = 'No raw taxonomy data available.';
        noDataMsg.style.color = '#868e96';
        noDataMsg.style.fontStyle = 'italic';
        wrapper.appendChild(noDataMsg);
        container.appendChild(wrapper);
        return;
    }
    
    // Build the JSON structure
    const jsonDisplay = document.createElement('pre');
    jsonDisplay.style.margin = '0';
    jsonDisplay.style.whiteSpace = 'pre-wrap';
    jsonDisplay.style.wordBreak = 'break-word';
    
    // Build the content from raw data
    const content = buildJSONStructure(
        rawTaxonomyData.documentInfo, 
        getXbrlModel(rawTaxonomyData),
        'module'
    );
    jsonDisplay.appendChild(content);
    
    wrapper.appendChild(jsonDisplay);
    
    // Add copy button
    const copyButton = document.createElement('button');
    copyButton.textContent = 'Copy JSON';
    copyButton.style.marginTop = '15px';
    copyButton.style.padding = '8px 16px';
    copyButton.style.backgroundColor = '#228be6';
    copyButton.style.color = 'white';
    copyButton.style.border = 'none';
    copyButton.style.borderRadius = '4px';
    copyButton.style.cursor = 'pointer';
    copyButton.style.fontSize = '13px';
    copyButton.addEventListener('click', () => copyJSONToClipboard(rawTaxonomyData.documentInfo, getXbrlModel(rawTaxonomyData), 'module', copyButton));
    wrapper.appendChild(copyButton);
    
    container.appendChild(wrapper);
}

/**
 * Build the JSON structure display
 * @param {Object} documentInfo - The documentInfo object
 * @param {Object} taxonomy - The taxonomy object
 * @param {string} viewType - 'model' or 'module' to namespace pagination keys
 * @returns {DocumentFragment} The built structure
 */
function buildJSONStructure(documentInfo, taxonomy, viewType = 'model') {
    const fragment = document.createDocumentFragment();
    
    // Opening brace
    fragment.appendChild(createTextNode('{\n'));
    
    // DocumentInfo section
    if (documentInfo) {
        fragment.appendChild(createTextNode('  ', '#868e96'));
        fragment.appendChild(createPropertyName('documentInfo'));
        fragment.appendChild(createTextNode(': '));
        fragment.appendChild(buildObjectDisplay(documentInfo, 2, viewType, '', 'documentInfo'));
        fragment.appendChild(createTextNode(',\n'));
    }
    
    // xbrlModel section
    if (taxonomy) {
        fragment.appendChild(createTextNode('  ', '#868e96'));
        fragment.appendChild(createPropertyName('xbrlModel'));
        fragment.appendChild(createTextNode(': '));
        fragment.appendChild(buildTaxonomyDisplay(taxonomy, 2, viewType));
        fragment.appendChild(createTextNode('\n'));
    }
    
    // Closing brace
    fragment.appendChild(createTextNode('}'));
    
    return fragment;
}

/**
 * Build display for the xbrlModel object
 * @param {Object} taxonomy - The xbrlModel object
 * @param {number} indent - Current indentation level
 * @param {string} viewType - 'model' or 'module' to namespace pagination keys
 * @returns {DocumentFragment} The built structure
 */
function buildTaxonomyDisplay(taxonomy, indent, viewType) {
    const fragment = document.createDocumentFragment();
    const indentStr = '  '.repeat(indent);
    
    fragment.appendChild(createTextNode('{\n'));
    
    // Filter out properties based on view type:
    // Model View: basePath (internal), importedTaxonomies (merged), facts property from factSources
    // Module View: basePath only (show raw source including factSources)
    let keys = Object.keys(taxonomy);
    if (viewType === 'model') {
        keys = keys.filter(key => key !== 'basePath' && key !== 'importedTaxonomies');
        // Add modelForm if not present
        if (!keys.includes('modelForm')) {
            keys.push('modelForm');
        }
    } else {
        // Module View - only filter out basePath
        keys = keys.filter(key => key !== 'basePath');
    }
    keys.forEach((key, index) => {
        let value = taxonomy[key];
        const isLast = index === keys.length - 1;
        
        // In Model View, set modelForm to "compiled" (either override existing value or provide default)
        if (viewType === 'model' && key === 'modelForm') {
            value = 'compiled';
        }
        
        // In Model View, filter factSources: remove internal 'facts' array (keep factNames for
        // materialized sources, or hash/metadata for hash-based sources)
        if (viewType === 'model' && key === 'factSources' && Array.isArray(value)) {
            // Skip rendering if no factSources exist
            if (value.length === 0) {
                return;
            }
        }
        
        fragment.appendChild(createTextNode(indentStr, '#868e96'));
        fragment.appendChild(createPropertyName(key));
        fragment.appendChild(createTextNode(': '));
        
        if (Array.isArray(value)) {
            const arrayKey = `${viewType}.xbrlModel.${key}`;
            fragment.appendChild(buildArrayDisplay(value, arrayKey, indent, viewType, `xbrlModel.${key}`));
        } else if (typeof value === 'object' && value !== null) {
            fragment.appendChild(buildObjectDisplay(value, indent, viewType, `xbrlModel.${key}`));
        } else {
            fragment.appendChild(buildPrimitiveValue(value));
        }
        
        if (!isLast) {
            fragment.appendChild(createTextNode(','));
        }
        fragment.appendChild(createTextNode('\n'));
    });
    
    fragment.appendChild(createTextNode('  '.repeat(indent - 1) + '}'));
    
    return fragment;
}

/**
 * Build display for an object
 * @param {Object} obj - The object to display
 * @param {number} indent - Current indentation level
 * @param {string} viewType - 'model' or 'module' to namespace pagination keys
 * @param {string} parentKey - Parent key for collapse tracking
 * @param {string} objectType - Type of object ('documentInfo', etc.) for conditional filtering
 * @returns {DocumentFragment} The built structure
 */
function buildObjectDisplay(obj, indent, viewType, parentKey = '', objectType = '') {
    const fragment = document.createDocumentFragment();
    const indentStr = '  '.repeat(indent);
    
    // Filter properties based on context
    let keys = Object.keys(obj);
    if (viewType === 'model' && objectType === 'documentInfo') {
        // Filter out basePath, importMapping, and documentNamespace from documentInfo in Model View
        // (these are resolved during model composition and are non-semantic)
        // NOTE: sourceMapping is intentionally retained — it is required for fact value source
        // resolution in compiled models (see spec sec-canonical-model).
        keys = keys.filter(key => key !== 'basePath' && key !== 'importMapping' && key !== 'documentNamespace');
    } else if (viewType === 'module' && objectType === 'documentInfo') {
        // Filter out basePath from documentInfo in Module View
        keys = keys.filter(key => key !== 'basePath');
    } else if (viewType === 'model' && parentKey.includes('factSources[')) {
        // In Model View, filter out materialized facts from factSource objects (keep hash/metadata)
        keys = keys.filter(key => key !== 'facts');
    }
    const collapseKey = `${viewType}.obj.${parentKey}`;
    const isCollapsed = collapseState.get(collapseKey) || false;
    
    // Create collapse arrow
    const collapseArrow = document.createElement('span');
    collapseArrow.textContent = isCollapsed ? '▶ ' : '▼ ';
    collapseArrow.style.cursor = 'pointer';
    collapseArrow.style.color = '#868e96';
    collapseArrow.style.userSelect = 'none';
    collapseArrow.style.marginRight = '4px';
    
    collapseArrow.addEventListener('click', () => {
        const currentScrollTop = getScrollContainer()?.scrollTop || 0;
        collapseState.set(collapseKey, !isCollapsed);
        rebuildCurrentView(viewType, currentScrollTop);
    });
    
    fragment.appendChild(collapseArrow);
    fragment.appendChild(createTextNode('{'));
    
    if (isCollapsed) {
        fragment.appendChild(createTextNode('...}'));
        return fragment;
    }
    
    fragment.appendChild(createTextNode('\n'));
    
    keys.forEach((key, index) => {
        const value = obj[key];
        const isLast = index === keys.length - 1;
        
        fragment.appendChild(createTextNode(indentStr, '#868e96'));
        fragment.appendChild(createPropertyName(key));
        fragment.appendChild(createTextNode(': '));
        
        if (Array.isArray(value)) {
            // For nested arrays (like relationships), also paginate
            const arrayKey = `${parentKey}.${key}`;
            fragment.appendChild(buildArrayDisplay(value, arrayKey, indent, viewType, arrayKey));
        } else if (typeof value === 'object' && value !== null) {
            fragment.appendChild(buildObjectDisplay(value, indent + 1, viewType, `${parentKey}.${key}`, objectType));
        } else {
            fragment.appendChild(buildPrimitiveValue(value));
        }
        
        if (!isLast) {
            fragment.appendChild(createTextNode(','));
        }
        fragment.appendChild(createTextNode('\n'));
    });
    
    fragment.appendChild(createTextNode('  '.repeat(indent - 1) + '}'));
    
    return fragment;
}

/**
 * Build display for an array with pagination
 * @param {Array} array - The array to display
 * @param {string} arrayKey - Unique key for this array
 * @param {number} indent - Current indentation level
 * @param {string} viewType - 'model' or 'module' to namespace pagination keys
 * @param {string} parentKey - Parent key for collapse tracking
 * @returns {DocumentFragment} The built structure
 */
function buildArrayDisplay(array, arrayKey, indent, viewType, parentKey = '') {
    const fragment = document.createDocumentFragment();
    
    if (array.length === 0) {
        fragment.appendChild(createTextNode('[]'));
        return fragment;
    }
    
    const collapseKey = `${viewType}.arr.${arrayKey}`;
    const isCollapsed = collapseState.get(collapseKey) || false;
    
    // Create collapse arrow
    const collapseArrow = document.createElement('span');
    collapseArrow.textContent = isCollapsed ? '▶ ' : '▼ ';
    collapseArrow.style.cursor = 'pointer';
    collapseArrow.style.color = '#868e96';
    collapseArrow.style.userSelect = 'none';
    collapseArrow.style.marginRight = '4px';
    
    collapseArrow.addEventListener('click', () => {
        const currentScrollTop = getScrollContainer()?.scrollTop || 0;
        collapseState.set(collapseKey, !isCollapsed);
        rebuildCurrentView(viewType, currentScrollTop);
    });
    
    fragment.appendChild(collapseArrow);
    fragment.appendChild(createTextNode('['));
    
    if (isCollapsed) {
        fragment.appendChild(createTextNode(`...] // ${array.length} items`));
        return fragment;
    }
    
    // Initialize pagination state
    if (!paginationState.has(arrayKey)) {
        paginationState.set(arrayKey, { offset: 0, pageSize: 5 });
    }
    
    const state = paginationState.get(arrayKey);
    const visibleItems = array.slice(0, state.offset + state.pageSize);
    const hasMore = visibleItems.length < array.length;
    
    fragment.appendChild(createTextNode('\n'));
    
    const indentStr = '  '.repeat(indent);
    visibleItems.forEach((item, index) => {
        const isLast = index === visibleItems.length - 1 && !hasMore;
        
        fragment.appendChild(createTextNode(indentStr, '#868e96'));
        
        if (typeof item === 'object' && item !== null) {
            fragment.appendChild(buildObjectDisplay(item, indent + 1, viewType, `${parentKey}[${index}]`));
        } else {
            fragment.appendChild(buildPrimitiveValue(item));
        }
        
        if (!isLast) {
            fragment.appendChild(createTextNode(','));
        }
        fragment.appendChild(createTextNode('\n'));
    });
    
    // Add "Show Next 5" button if there are more items
    if (hasMore) {
        fragment.appendChild(createTextNode(indentStr, '#868e96'));
        const button = createLoadMoreButton(arrayKey, array, indent, viewType);
        fragment.appendChild(button);
        fragment.appendChild(createTextNode('\n'));
    }
    
    fragment.appendChild(createTextNode('  '.repeat(indent - 1) + ']'));
    
    return fragment;
}

/**
 * Create a "Show Next 5" button
 * @param {string} arrayKey - The array key
 * @param {Array} array - The full array
 * @param {number} indent - Current indentation level
 * @param {string} viewType - 'model' or 'module' to determine which view to rebuild
 * @returns {HTMLElement} The button element
 */
function createLoadMoreButton(arrayKey, array, indent, viewType) {
    const state = paginationState.get(arrayKey);
    const remaining = array.length - (state.offset + state.pageSize);
    const toLoad = Math.min(5, remaining);
    
    const button = document.createElement('button');
    button.textContent = `▼ Show Next ${toLoad} (${remaining} remaining)`;
    button.style.backgroundColor = '#228be6';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '3px';
    button.style.padding = '4px 8px';
    button.style.fontSize = '11px';
    button.style.cursor = 'pointer';
    button.style.marginTop = '2px';
    button.style.marginBottom = '2px';
    
    button.addEventListener('click', () => {
        // Capture scroll position before updating
        const currentScrollTop = getScrollContainer()?.scrollTop || 0;
        
        state.offset += state.pageSize;
        paginationState.set(arrayKey, state);
        
        // Rebuild the view and restore scroll position
        rebuildCurrentView(viewType, currentScrollTop);
    });
    
    button.addEventListener('mouseenter', () => {
        button.style.backgroundColor = '#1c7ed6';
    });
    
    button.addEventListener('mouseleave', () => {
        button.style.backgroundColor = '#228be6';
    });
    
    return button;
}

/**
 * Build display for a primitive value
 * @param {*} value - The primitive value
 * @returns {HTMLElement} The span element
 */
function buildPrimitiveValue(value) {
    const span = document.createElement('span');
    
    if (typeof value === 'string') {
        span.textContent = `"${value}"`;
        span.style.color = '#099268';
    } else if (typeof value === 'number') {
        span.textContent = String(value);
        span.style.color = '#e8590c';
    } else if (typeof value === 'boolean') {
        span.textContent = String(value);
        span.style.color = '#d9480f';
    } else if (value === null) {
        span.textContent = 'null';
        span.style.color = '#868e96';
    } else {
        span.textContent = String(value);
    }
    
    return span;
}

/**
 * Create a property name element with tooltip
 * @param {string} name - The property name
 * @returns {HTMLElement} The span element
 */
function createPropertyName(name) {
    const span = document.createElement('span');
    span.textContent = `"${name}"`;
    span.style.color = '#1971c2';
    span.style.fontWeight = 'bold';
    
    // Add tooltip if description is available
    const description = getPropertyDescription(name);
    if (description) {
        span.style.cursor = 'help';
        span.title = description;
        span.style.textDecoration = 'underline';
        span.style.textDecorationStyle = 'dotted';
        span.style.textDecorationColor = '#1971c2';
        span.style.textUnderlineOffset = '2px';
    }
    
    return span;
}

/**
 * Create a text node with optional color
 * @param {string} text - The text content
 * @param {string} color - Optional text color
 * @returns {HTMLElement|Text} The text element
 */
function createTextNode(text, color = null) {
    if (color) {
        const span = document.createElement('span');
        span.textContent = text;
        span.style.color = color;
        return span;
    }
    return document.createTextNode(text);
}

/**
 * Create model comparison controls (hash generation and model comparison)
 * @param {Object} taxonomy - The taxonomy object (xbrlModel)
 * @param {Object} documentInfo - The document info object
 * @returns {HTMLElement} The controls container
 */
function createModelComparisonControls(taxonomy, documentInfo) {
    const container = document.createElement('div');
    container.id = 'modelComparisonContainer';
    container.style.marginBottom = '20px';
    container.style.padding = '15px';
    container.style.backgroundColor = '#fff';
    container.style.borderRadius = '4px';
    container.style.border = '1px solid #dee2e6';
    
    // Title
    const title = document.createElement('h4');
    title.textContent = 'Model Comparison Tools';
    title.style.marginTop = '0';
    title.style.marginBottom = '12px';
    title.style.color = '#228be6';
    container.appendChild(title);
    
    // Buttons container
    const buttonsContainer = document.createElement('div');
    buttonsContainer.id = 'modelComparisonButtons';
    
    // Generate Hash button
    const hashButton = document.createElement('button');
    hashButton.textContent = 'Generate Model Hash';
    hashButton.id = 'generateHashButton';
    hashButton.onclick = async () => {
        try {
            hashButton.disabled = true;
            hashButton.textContent = 'Generating...';
            
            // Create proper model structure
            // Ensure modelForm is set to 'compiled' for the Model View (which shows merged/compiled model)
            const model = {
                xbrlModel: {
                    ...taxonomy,
                    modelForm: 'compiled'
                },
                documentInfo: documentInfo
            };
            
            const hash = await generateModelHash(model);
            
            // Display the hash
            let hashDisplay = document.getElementById('modelHashDisplay');
            if (!hashDisplay) {
                hashDisplay = document.createElement('div');
                hashDisplay.id = 'modelHashDisplay';
                container.appendChild(hashDisplay);
            }
            
            hashDisplay.innerHTML = `
                <p style="margin: 10px 0 5px 0;"><strong>Model Hash:</strong></p>
                <code style="display: block; padding: 10px; background-color: #e3f2fd; border-radius: 3px; word-break: break-all; font-family: 'Courier New', monospace;">${hash}</code>
                <p style="margin: 5px 0 0 0; font-size: 0.85em; color: #666;">This cryptographic hash uniquely identifies the semantic content of this model.</p>
            `;
            
            hashButton.disabled = false;
            hashButton.textContent = 'Generate Model Hash';
        } catch (error) {
            alert('Error generating hash: ' + error.message);
            hashButton.disabled = false;
            hashButton.textContent = 'Generate Model Hash';
        }
    };
    buttonsContainer.appendChild(hashButton);
    
    // File input for comparison (hidden)
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.id = 'compareModelFile';
    fileInput.accept = '.json';
    fileInput.style.display = 'none';
    fileInput.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        try {
            const compareLabel = document.querySelector('label[for="compareModelFile"]');
            if (compareLabel) {
                compareLabel.textContent = 'Comparing...';
                compareLabel.style.cursor = 'wait';
            }
            
            const text = await file.text();
            const model2 = JSON.parse(text);
            
            // Create proper model structure for current taxonomy
            // Ensure modelForm is set to 'compiled' for the Model View (which shows merged/compiled model)
            const model1 = {
                xbrlModel: {
                    ...taxonomy,
                    modelForm: 'compiled'
                },
                documentInfo: documentInfo
            };
            
            // Compare models
            const diffReport = await compareModels(model1, model2);
            
            // Display results
            let resultsDisplay = document.getElementById('diffResultsDisplay');
            if (!resultsDisplay) {
                resultsDisplay = document.createElement('div');
                resultsDisplay.id = 'diffResultsDisplay';
                container.appendChild(resultsDisplay);
            }
            
            resultsDisplay.innerHTML = formatDifferencesForDisplay(diffReport);
            
            if (compareLabel) {
                compareLabel.textContent = 'Compare with Model...';
                compareLabel.style.cursor = 'pointer';
            }
            
            // Reset file input
            fileInput.value = '';
        } catch (error) {
            alert('Error comparing models: ' + error.message);
            const compareLabel = document.querySelector('label[for="compareModelFile"]');
            if (compareLabel) {
                compareLabel.textContent = 'Compare with Model...';
                compareLabel.style.cursor = 'pointer';
            }
            fileInput.value = '';
        }
    };
    buttonsContainer.appendChild(fileInput);
    
    // Label for file input (styled as button)
    const fileLabel = document.createElement('label');
    fileLabel.setAttribute('for', 'compareModelFile');
    fileLabel.textContent = 'Compare with Model...';
    buttonsContainer.appendChild(fileLabel);
    
    container.appendChild(buttonsContainer);
    
    return container;
}
