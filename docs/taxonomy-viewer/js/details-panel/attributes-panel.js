/**
 * Attributes Panel Module
 * Handles displaying object attributes/properties in the details panel
 */

import { createPropertiesTable, createFactValuesTable, createFactDimensionsTable } from './table-builders.js';

/**
 * Populate the attributes panel with object properties
 * @param {Object} displayObj - The object to display
 * @param {Object} taxonomyData - The taxonomy data
 */
export function populateAttributesPanel(displayObj, taxonomyData) {
    const attributesContent = document.getElementById('attributes-content');
    attributesContent.innerHTML = '';
    
    if (displayObj && typeof displayObj === 'object') {
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Property', 'Value'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        const tbody = document.createElement('tbody');
        
        // Filter out 'relationships' property for network and domain objects
        const isNetworkOrDomain = displayObj.hasOwnProperty('relationships') && 
            (displayObj.hasOwnProperty('relationshipTypeName') || displayObj.hasOwnProperty('root'));
        
        // List of array properties to exclude from attributes display
        const arrayPropertiesToExclude = [
            'relationships', // Already handled above
            'concepts', 'members', 'dimensions', 'abstracts', 'entities', 'units',
            'dataTypes', 'propertyTypes', 'groups', 'groupContents', 'relationshipTypes',
            'cubes', 'networks', 'domains', 'references', 'facts',
            'cubeTypes', 'labelTypes', 'referenceTypes', 'labels', 'importedTaxonomies',
            'specTaxonomies', 'groupTree', 'finalTaxonomy', 'modelTypes', 'layouts',
            'factSource', 'factSources', 'factMaps', 'transforms'
        ];
        
        Object.keys(displayObj).forEach(key => {
            // Skip 'relationships' for networks and domains (already shown in tree view)
            if (key === 'relationships' && isNetworkOrDomain) {
                return;
            }
            
            // Skip array properties and groupTree (taxonomy object arrays/structures)
            if (arrayPropertiesToExclude.includes(key)) {
                return;
            }
            
            // Skip 'domainClasses' if it's an array of objects (taxonomy-level definition)
            // Only show it for members where it's an array of QName strings
            if (key === 'domainClasses' && Array.isArray(displayObj[key]) && 
                displayObj[key].length > 0 && typeof displayObj[key][0] === 'object') {
                return;
            }
            
            const row = document.createElement('tr');
            const keyCell = document.createElement('td');
            keyCell.textContent = key;
            const valueCell = document.createElement('td');
            const value = displayObj[key];
            
            // Special handling for 'properties' array
            if (key === 'properties' && Array.isArray(value) && value.length > 0) {
                const propsTable = createPropertiesTable(value);
                valueCell.appendChild(propsTable);
            }
            // Special handling for 'domainClasses' array (only for members, where it's an array of strings)
            else if (key === 'domainClasses' && Array.isArray(value) && value.length > 0 && typeof value[0] === 'string') {
                // Display domain classes as a comma-separated list
                valueCell.textContent = value.join(', ');
            }
            // Special handling for 'factValues' array
            else if (key === 'factValues' && Array.isArray(value) && value.length > 0) {
                const factValuesTable = createFactValuesTable(value);
                valueCell.appendChild(factValuesTable);
            }
            // Special handling for 'factDimensions' object
            else if (key === 'factDimensions' && typeof value === 'object' && value !== null) {
                const factDimensionsTable = createFactDimensionsTable(value);
                valueCell.appendChild(factDimensionsTable);
            }
            else if (Array.isArray(value) && value.length > 0) {
                // Format arrays more nicely
                if (value.every(item => typeof item === 'string')) {
                    if (value.length === 1) {
                        // For single-item arrays, display as plain text
                        valueCell.textContent = value[0];
                    } else {
                        // For multi-item arrays, display as numbered list
                        const ul = document.createElement('ul');
                        ul.style.margin = '0';
                        ul.style.paddingLeft = '20px';
                        ul.style.listStyleType = 'decimal';
                        value.forEach(item => {
                            const li = document.createElement('li');
                            li.textContent = item;
                            li.style.marginBottom = '2px';
                            ul.appendChild(li);
                        });
                        valueCell.appendChild(ul);
                    }
                } else {
                    // For complex arrays, fall back to JSON
                    valueCell.textContent = JSON.stringify(value);
                }
            }
            else if (typeof value === 'object' && value !== null) {
                valueCell.textContent = JSON.stringify(value);
            } else {
                valueCell.textContent = String(value);
            }
            row.appendChild(keyCell);
            row.appendChild(valueCell);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        attributesContent.appendChild(table);
    } else {
        attributesContent.textContent = 'No attributes available.';
    }
}
