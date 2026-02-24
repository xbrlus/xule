/**
 * Labels Panel Module
 * Handles displaying label information for taxonomy objects
 */

import { getXbrlModel } from '../utils.js';

/**
 * Populate the labels panel
 * @param {Array} labels - Array of label objects
 * @param {Object} taxonomyData - The taxonomy data
 */
export function populateLabelsPanel(labels, taxonomyData) {
    const labelsContent = document.getElementById('labels-content');
    labelsContent.innerHTML = '';
    
    if (labels.length > 0) {
        console.log('[Details Panel] First label:', labels[0]);
        
        // Helper function to check if a label type should be rendered as HTML
        const isLabelTypeTextBlock = (labelTypeName) => {
            // All xbrl:xxx label types are strings (defined in xbrlSpec.json)
            if (labelTypeName && labelTypeName.startsWith('xbrl:')) {
                return false;
            }
            
            // Check if the label type has xbrli:textBlock dataType
            const xbrlModel = getXbrlModel(taxonomyData);
            if (xbrlModel && xbrlModel.labelTypes) {
                const labelTypeObj = xbrlModel.labelTypes.find(lt => lt.name === labelTypeName);
                if (labelTypeObj && labelTypeObj.dataType === 'xbrli:textBlock') {
                    return true;
                }
            }
            
            return false;
        };
        
        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Label Type', 'Language', 'Value'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        labels.forEach(label => {
            const row = document.createElement('tr');
            
            // Label Type cell
            const labelTypeCell = document.createElement('td');
            labelTypeCell.textContent = label.labelType || label.role || '';
            row.appendChild(labelTypeCell);
            
            // Language cell
            const languageCell = document.createElement('td');
            languageCell.textContent = label.language || '';
            row.appendChild(languageCell);
            
            // Value cell - render as HTML if the label type is textBlock
            const valueCell = document.createElement('td');
            if (isLabelTypeTextBlock(label.labelType) && label.value) {
                // Render as HTML
                valueCell.innerHTML = label.value;
                valueCell.style.maxHeight = '300px';
                valueCell.style.overflow = 'auto';
            } else {
                valueCell.textContent = label.value || '';
            }
            row.appendChild(valueCell);
            
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        labelsContent.appendChild(table);
    } else {
        labelsContent.textContent = 'No labels found.';
    }
}
