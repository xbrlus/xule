/**
 * Table Builders Module
 * Functions for creating various table structures in the details panel
 */

import { getTaxonomyData } from '../main.js';
import { getXbrlModel } from '../utils.js';
import { resolveFactValue } from '../valueSource-resolver.js';

/**
 * Check if a dataType derives from a base dataType by following the baseType chain
 * @param {string} dataType - The dataType to check
 * @param {string} baseDataType - The base dataType to check against
 * @param {Object} xbrlModel - The taxonomy xbrlModel
 * @param {Set} visited - Set of already visited dataTypes (to prevent infinite recursion)
 * @returns {boolean} True if dataType derives from baseDataType
 */
function dataTypeDerivedFrom(dataType, baseDataType, xbrlModel, visited = new Set()) {
    if (!dataType || !baseDataType || !xbrlModel) return false;
    
    // Direct match
    if (dataType === baseDataType) return true;
    
    // Check if we've already visited this dataType (circular reference protection)
    if (visited.has(dataType)) return false;
    visited.add(dataType);
    
    // Look up the dataType definition
    const dataTypeDef = xbrlModel.dataTypes?.find(dt => dt.name === dataType);
    if (!dataTypeDef) return false;
    
    // Check if baseType matches
    if (dataTypeDef.baseType === baseDataType) return true;
    
    // Recursively check the baseType
    if (dataTypeDef.baseType) {
        return dataTypeDerivedFrom(dataTypeDef.baseType, baseDataType, xbrlModel, visited);
    }
    
    return false;
}

/**
 * Create a properties table
 * @param {Array} properties - Array of property objects with {property, value}
 * @returns {HTMLElement} The properties table element
 */
export function createPropertiesTable(properties) {
    const propsTable = document.createElement('table');
    propsTable.style.width = '100%';
    propsTable.style.fontSize = '0.9em';
    propsTable.style.marginTop = '5px';
    propsTable.style.border = '1px solid #ddd';
    
    const propsThead = document.createElement('thead');
    const propsHeaderRow = document.createElement('tr');
    propsHeaderRow.style.backgroundColor = '#f0f0f0';
    ['Property', 'Value'].forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.border = '1px solid #ddd';
        th.style.padding = '5px';
        th.style.fontWeight = 'bold';
        propsHeaderRow.appendChild(th);
    });
    propsThead.appendChild(propsHeaderRow);
    propsTable.appendChild(propsThead);
    
    // Build a map of property names to their dataTypes
    const propertyTypeDataTypes = new Map();
    const taxonomyData = getTaxonomyData();
    if (taxonomyData) {
        const xbrlModel = getXbrlModel(taxonomyData);
        if (xbrlModel && xbrlModel.propertyTypes) {
            xbrlModel.propertyTypes.forEach(propType => {
                if (propType.name && propType.dataType) {
                    propertyTypeDataTypes.set(propType.name, propType.dataType);
                }
            });
        }
    }
    
    const propsTbody = document.createElement('tbody');
    properties.forEach(prop => {
        const propRow = document.createElement('tr');
        
        const propNameCell = document.createElement('td');
        propNameCell.textContent = prop.property || '-';
        propNameCell.style.border = '1px solid #ddd';
        propNameCell.style.padding = '5px';
        propNameCell.style.fontWeight = 'bold';
        propRow.appendChild(propNameCell);
        
        const propValueCell = document.createElement('td');
        propValueCell.style.border = '1px solid #ddd';
        propValueCell.style.padding = '5px';
        
        // Check if this property has a dataType derived from xbrli:realURL
        const dataType = propertyTypeDataTypes.get(prop.property);
        const xbrlModel = getXbrlModel(taxonomyData);
        if (dataType && xbrlModel && dataTypeDerivedFrom(dataType, 'xbrli:realURL', xbrlModel) && prop.value && typeof prop.value === 'string') {
            // Render as a clickable link
            const link = document.createElement('a');
            link.href = prop.value;
            link.textContent = prop.value;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.style.color = '#0066cc';
            link.style.textDecoration = 'underline';
            propValueCell.appendChild(link);
        } else if (Array.isArray(prop.value) && prop.value.length > 0) {
            // Format arrays more nicely
            if (prop.value.every(item => typeof item === 'string')) {
                if (prop.value.length === 1) {
                    // For single-item arrays, display as plain text
                    propValueCell.textContent = prop.value[0];
                } else {
                    // For multi-item arrays, display as numbered list
                    const ul = document.createElement('ul');
                    ul.style.margin = '0';
                    ul.style.paddingLeft = '20px';
                    ul.style.listStyleType = 'decimal';
                    prop.value.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        li.style.marginBottom = '2px';
                        ul.appendChild(li);
                    });
                    propValueCell.appendChild(ul);
                }
            } else {
                // For complex arrays, fall back to JSON
                propValueCell.textContent = JSON.stringify(prop.value);
            }
        } else {
            // Render as plain text
            propValueCell.textContent = typeof prop.value === 'object' ? JSON.stringify(prop.value) : (prop.value || '-');
        }
        
        propRow.appendChild(propValueCell);
        
        propsTbody.appendChild(propRow);
    });
    propsTable.appendChild(propsTbody);
    
    return propsTable;
}

/**
 * Create a nested table for factValues array
 * @param {Array} factValues - Array of fact value objects
 * @returns {HTMLElement} The factValues table element
 */
export function createFactValuesTable(factValues) {
    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.fontSize = '0.9em';
    table.style.marginTop = '5px';
    table.style.border = '1px solid #ddd';
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.style.backgroundColor = '#f0f0f0';
    ['Name', 'Value', 'Decimals', 'Source'].forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.border = '1px solid #ddd';
        th.style.padding = '5px';
        th.style.fontWeight = 'bold';
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    
    // Process fact values and resolve value sources asynchronously
    factValues.forEach(async (fv) => {
        const row = document.createElement('tr');
        
        const nameCell = document.createElement('td');
        // Add fact icon before the fact name
        if (fv.name && fv.name !== '-') {
            nameCell.textContent = `💠 ${fv.name}`;
        } else {
            nameCell.textContent = fv.name || '-';
        }
        nameCell.style.border = '1px solid #ddd';
        nameCell.style.padding = '5px';
        nameCell.style.fontWeight = 'bold';
        row.appendChild(nameCell);
        
        const valueCell = document.createElement('td');
        valueCell.style.border = '1px solid #ddd';
        valueCell.style.padding = '5px';
        valueCell.style.maxWidth = '500px';
        valueCell.style.overflow = 'auto';
        
        const decimalsCell = document.createElement('td');
        decimalsCell.style.border = '1px solid #ddd';
        decimalsCell.style.padding = '5px';
        
        const sourceCell = document.createElement('td');
        sourceCell.style.border = '1px solid #ddd';
        sourceCell.style.padding = '5px';
        sourceCell.style.fontSize = '0.85em';
        sourceCell.style.color = '#666';
        
        // Initially show loading or existing value
        if (fv.valueSources && fv.valueSources.length > 0) {
            // Check if value was already resolved during taxonomy loading
            if (fv.value !== undefined && fv.value !== null) {
                // Value already resolved - display it
                if (fv._isEscaped) {
                    // Render as HTML for escaped content - wrap in container to preserve styles
                    const htmlContainer = document.createElement('div');
                    htmlContainer.innerHTML = fv.value;
                    // Let the inner HTML control all styling
                    valueCell.appendChild(htmlContainer);
                } else {
                    valueCell.textContent = fv.value;
                }
                
                // Show all source refs
                if (fv._sourceRefs && fv._sourceRefs.length > 0) {
                    sourceCell.textContent = fv._sourceRefs.join(', ');
                    
                    // Show concatenated indicator if multiple sources
                    if (fv._concatenated) {
                        const concatSpan = document.createElement('span');
                        concatSpan.textContent = ' 🔗';
                        concatSpan.title = 'Concatenated from multiple sources';
                        concatSpan.style.cursor = 'help';
                        sourceCell.appendChild(concatSpan);
                    }
                } else {
                    sourceCell.textContent = fv.valueSources[0].id || '';
                }
                
                // Show transformation info if present
                if (fv._transformation) {
                    const transformSpan = document.createElement('span');
                    transformSpan.textContent = ` (${fv._transformation})`;
                    transformSpan.style.fontSize = '0.85em';
                    transformSpan.style.color = '#666';
                    sourceCell.appendChild(transformSpan);
                }
                
                // Show escaped indicator
                if (fv._isEscaped) {
                    const escapedSpan = document.createElement('span');
                    escapedSpan.textContent = ' ⚡';
                    escapedSpan.title = 'Escaped HTML markup';
                    escapedSpan.style.cursor = 'help';
                    sourceCell.appendChild(escapedSpan);
                }
                
                // Show original value tooltip if transformation was applied
                if (fv._originalValue && fv._originalValue !== fv.value) {
                    const originalSpan = document.createElement('span');
                    originalSpan.textContent = ' 📄';
                    originalSpan.title = `Original: ${fv._originalValue}`;
                    originalSpan.style.cursor = 'help';
                    valueCell.appendChild(originalSpan);
                }
                
                // Show error if resolution failed
                if (fv._resolveError) {
                    valueCell.innerHTML = `<span style="color: #d00;" title="${fv._resolveMessage || fv._resolveError}">⚠️ ${fv._resolveError}</span>`;
                }
            } else {
                // Value not yet resolved - resolve asynchronously
                valueCell.textContent = 'Loading...';
                
                // Show all source refs if available
                if (fv._sourceRefs && fv._sourceRefs.length > 0) {
                    sourceCell.textContent = fv._sourceRefs.join(', ');
                } else {
                    // Fallback to first id
                    sourceCell.textContent = fv.valueSources[0].id || '';
                }
                
                // Resolve the value asynchronously
                resolveFactValue(fv).then(resolved => {
                    if (resolved.error) {
                        valueCell.innerHTML = `<span style="color: #d00;" title="${resolved.message || resolved.error}">⚠️ ${resolved.error}</span>`;
                    } else if (resolved.value !== null) {
                        // Render as HTML if escaped, otherwise as text
                        if (resolved.isEscaped) {
                            const htmlContainer = document.createElement('div');
                            htmlContainer.innerHTML = resolved.value;
                            // Let the inner HTML control all styling
                            valueCell.appendChild(htmlContainer);
                        } else {
                            valueCell.textContent = resolved.value;
                        }
                        
                        // Update source cell with all refs
                        if (resolved.sourceRefs && resolved.sourceRefs.length > 0) {
                            sourceCell.textContent = resolved.sourceRefs.join(', ');
                        }
                        
                        // Add transformation info if present
                        if (resolved.transformation) {
                            sourceCell.textContent += ` (${resolved.transformation})`;
                        }
                        
                        // Show concatenated indicator if multiple sources were concatenated
                        if (resolved.concatenated) {
                            const concatSpan = document.createElement('span');
                            concatSpan.textContent = ' 🔗';
                            concatSpan.title = 'Concatenated from multiple sources';
                            concatSpan.style.cursor = 'help';
                            sourceCell.appendChild(concatSpan);
                        }
                        
                        // Show original value tooltip if transformation was applied
                        if (resolved.originalValue && resolved.originalValue !== resolved.value) {
                            const originalSpan = document.createElement('span');
                            originalSpan.textContent = ' 📄';
                            originalSpan.title = `Original: ${resolved.originalValue}`;
                            originalSpan.style.cursor = 'help';
                            valueCell.appendChild(originalSpan);
                        }
                    }
                }).catch(err => {
                    console.error('[Table Builder] Error resolving fact value:', err);
                    valueCell.innerHTML = `<span style="color: #d00;">⚠️ Error</span>`;
                });
            }
        } else {
            valueCell.textContent = fv.value || '-';
        }
        
        decimalsCell.textContent = fv.decimals !== undefined ? fv.decimals : '-';
        
        row.appendChild(valueCell);
        row.appendChild(decimalsCell);
        row.appendChild(sourceCell);
        
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    
    return table;
}

/**
 * Create a nested table for factDimensions object
 * @param {Object} factDimensions - Object containing dimension name-value pairs
 * @returns {HTMLElement} The factDimensions table element
 */
export function createFactDimensionsTable(factDimensions) {
    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.fontSize = '0.9em';
    table.style.marginTop = '5px';
    table.style.border = '1px solid #ddd';
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.style.backgroundColor = '#f0f0f0';
    ['Dimension', 'Value'].forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.border = '1px solid #ddd';
        th.style.padding = '5px';
        th.style.fontWeight = 'bold';
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    Object.entries(factDimensions).forEach(([dimension, value]) => {
        const row = document.createElement('tr');
        
        const dimensionCell = document.createElement('td');
        dimensionCell.textContent = dimension;
        dimensionCell.style.border = '1px solid #ddd';
        dimensionCell.style.padding = '5px';
        dimensionCell.style.fontWeight = 'bold';
        row.appendChild(dimensionCell);
        
        const valueCell = document.createElement('td');
        valueCell.textContent = value || '-';
        valueCell.style.border = '1px solid #ddd';
        valueCell.style.padding = '5px';
        row.appendChild(valueCell);
        
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    
    return table;
}
