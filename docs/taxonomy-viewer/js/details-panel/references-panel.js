/**
 * References Panel Module
 * Handles displaying reference information for taxonomy objects
 */

import { getTaxonomyData } from '../main.js';
import { getXbrlModel } from '../utils.js';

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
 * Populate the references panel
 * @param {Array} references - Array of reference objects
 */
export function populateReferencesPanel(references) {
    const referencesContent = document.getElementById('references-content');
    referencesContent.innerHTML = '';
    
    // Get taxonomy data for label lookup
    const taxonomyData = getTaxonomyData();
    
    if (references.length > 0) {
        // Group by referenceType
        const grouped = {};
        references.forEach(ref => {
            const type = ref.referenceType || 'Unknown';
            if (!grouped[type]) grouped[type] = [];
            grouped[type].push(ref);
        });

        Object.keys(grouped).forEach(type => {
            const typeDiv = document.createElement('div');
            const typeHeader = document.createElement('h4');
            // Look up label for referenceType, fall back to QName if no label exists
            const referenceTypeLabel = getReferenceTypeLabel(type, taxonomyData);
            typeHeader.textContent = `Reference Type: ${referenceTypeLabel}`;
            typeDiv.appendChild(typeHeader);

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
            grouped[type].forEach((ref, refIndex) => {
                if (ref.properties) {
                    // Alternate colors: even indices get light blue, odd indices get white/default
                    const backgroundColor = refIndex % 2 === 0 ? '#e3f2fd' : '#ffffff';
                    
                    ref.properties.forEach(prop => {
                        const row = document.createElement('tr');
                        row.style.backgroundColor = backgroundColor;
                        
                        const propCell = document.createElement('td');
                        // Look up label for property QName, fall back to QName if no label exists
                        const propertyLabel = getPropertyLabelForReference(prop.property, taxonomyData);
                        propCell.textContent = propertyLabel;
                        const valueCell = document.createElement('td');
                        
                        // Check if this property has dataType derived from xbrli:realURL and render as link
                        const propertyType = getPropertyType(prop.property, taxonomyData);
                        const xbrlModel = getXbrlModel(taxonomyData);
                        if (propertyType && propertyType.dataType && xbrlModel && 
                            dataTypeDerivedFrom(propertyType.dataType, 'xbrli:realURL', xbrlModel) && prop.value) {
                            
                            // Check if it's a markdown link specifically
                            const isMarkdownLink = dataTypeDerivedFrom(propertyType.dataType, 'xbrli:linkToMarkdownFormat', xbrlModel);
                            
                            const link = document.createElement('a');
                            link.href = prop.value;
                            link.target = '_blank';
                            link.rel = 'noopener noreferrer';
                            link.textContent = prop.value;
                            link.style.color = '#0066cc';
                            link.style.textDecoration = 'underline';
                            valueCell.appendChild(link);
                            
                            // Add preview icon for markdown links
                            if (isMarkdownLink) {
                                const previewIcon = document.createElement('span');
                                previewIcon.textContent = ' 📄';
                                previewIcon.title = 'Preview markdown in application';
                                previewIcon.style.cursor = 'pointer';
                                previewIcon.style.marginLeft = '8px';
                                previewIcon.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    showMarkdownPreview(prop.value, prop.property);
                                });
                                valueCell.appendChild(previewIcon);
                            }
                        } else {
                            valueCell.textContent = prop.value;
                        }
                        
                        row.appendChild(propCell);
                        row.appendChild(valueCell);
                        tbody.appendChild(row);
                    });
                }
            });
            table.appendChild(tbody);
            typeDiv.appendChild(table);
            referencesContent.appendChild(typeDiv);
        });
    } else {
        referencesContent.textContent = 'No references found.';
    }
}

/**
 * Helper function to get label for a referenceType QName
 * @param {string} referenceTypeQName - The referenceType QName to look up
 * @param {Object} taxonomyData - The taxonomy data object
 * @returns {string} The label value if found, otherwise the QName
 */
function getReferenceTypeLabel(referenceTypeQName, taxonomyData) {
    if (!referenceTypeQName) return referenceTypeQName;
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.labels) {
        return referenceTypeQName;
    }
    
    // Look for a label with matching relatedName and labelType of 'xbrl:label'
    const labels = xbrlModel.labels.filter(l => 
        l.relatedName === referenceTypeQName && l.labelType === 'xbrl:label'
    );
    
    // Return the label value if found, otherwise return the QName
    return labels.length > 0 ? labels[0].value : referenceTypeQName;
}

/**
 * Helper function to get label for a property QName in references
 * @param {string} propertyQName - The property QName to look up
 * @param {Object} taxonomyData - The taxonomy data object
 * @returns {string} The label value if found, otherwise the QName
 */
function getPropertyLabelForReference(propertyQName, taxonomyData) {
    if (!propertyQName) return propertyQName;
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.labels) {
        return propertyQName;
    }
    
    // Look for a label with matching relatedName and labelType of 'xbrl:label'
    const labels = xbrlModel.labels.filter(l => 
        l.relatedName === propertyQName && l.labelType === 'xbrl:label'
    );
    
    // Return the label value if found, otherwise return the QName
    return labels.length > 0 ? labels[0].value : propertyQName;
}

/**
 * Helper function to get the propertyType definition for a property QName
 * @param {string} propertyQName - The property QName to look up
 * @param {Object} taxonomyData - The taxonomy data object
 * @returns {Object|null} The propertyType object if found, otherwise null
 */
function getPropertyType(propertyQName, taxonomyData) {
    if (!propertyQName) return null;
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.propertyTypes) {
        return null;
    }
    
    const propertyType = xbrlModel.propertyTypes.find(pt => 
        pt.name === propertyQName
    );
    
    return propertyType || null;
}

/**
 * Show markdown view in the application
 * @param {string} markdownUrl - The URL to the markdown file
 * @param {string} propertyName - The property name for display
 */
async function showMarkdownPreview(markdownUrl, propertyName) {
    console.log('[Markdown View] Loading:', markdownUrl);
    
    // Show the markdown view tab
    const detailsTabs = document.getElementById('details-tabs');
    const markdownTab = document.getElementById('markdown-preview-tab');
    const markdownButton = document.querySelector('[data-details-tab="markdown-preview"]');
    
    if (!markdownTab || !markdownButton) {
        console.error('[Markdown View] Tab elements not found');
        return;
    }
    
    // Show and activate the tab
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    markdownButton.style.display = 'block';
    
    // Activate the tab
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    markdownTab.classList.add('active');
    markdownButton.classList.add('active');
    
    // Load and render the markdown
    const container = document.getElementById('markdown-preview-content');
    if (!container) {
        console.error('[Markdown View] Content container not found');
        return;
    }
    
    container.innerHTML = '<div style="padding: 20px;">Loading markdown...</div>';
    
    try {
        // Fetch the markdown file
        const response = await fetch(markdownUrl);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const markdownText = await response.text();
        
        // Convert markdown to HTML
        if (typeof marked === 'undefined') {
            throw new Error('Marked library not loaded');
        }
        
        const htmlContent = marked.parse(markdownText);
        
        // Display the rendered HTML
        container.innerHTML = `
            <div style="padding: 20px; max-width: 900px; margin: 0 auto;">
                <div style="margin-bottom: 20px; padding: 10px; background-color: #f5f5f5; border-left: 4px solid #2196f3;">
                    <strong>Source:</strong> ${markdownUrl}
                </div>
                <div class="markdown-content" style="line-height: 1.6; color: #333;">
                    ${htmlContent}
                </div>
            </div>
        `;
        
        console.log('[Markdown View] Rendered successfully');
    } catch (error) {
        console.error('[Markdown View] Error loading markdown:', error);
        container.innerHTML = `
            <div style="padding: 20px;">
                <div style="color: #d32f2f; padding: 15px; background-color: #ffebee; border-radius: 4px;">
                    <strong>Error loading markdown:</strong> ${error.message}
                    <br><br>
                    <strong>URL:</strong> ${markdownUrl}
                </div>
            </div>
        `;
    }
}
