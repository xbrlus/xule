/**
 * Details Panel Module
 * Handles displaying details for taxonomy objects in the details panel
 */

import { getTaxonomyData } from './main.js';
import { getIconForType, getNodeType, getNodeLabel, formatQNameArrayWithLabels, isBuiltInObjectType, createBuiltInObjectDisplay, getXbrlModel } from './utils.js';
import { attachNodeHandlers } from './tree-handlers.js';
import { renderDataTableForLayout } from './layout-builder.js';
import { buildNetworkTree, buildChildrenMap, checkRootMismatch } from './networks-builder.js';
import { buildImportPathsView, buildFinalTaxonomyView, populateTaxonomyPropertiesTab } from './taxonomy-imports.js';
import { buildJSONView } from './json-view.js';
import { setCurrentDisplayedObject } from './tab-manager.js';

// Import modularized panel functions
import { manageTabVisibility as _manageTabVisibility, resetPanelTitles as _resetPanelTitles, adjustPanelSizesForCube as _adjustPanelSizesForCube } from './details-panel/tab-management.js';
import { populateAttributesPanel as _populateAttributesPanel } from './details-panel/attributes-panel.js';
import { populateLabelsPanel as _populateLabelsPanel } from './details-panel/labels-panel.js';
import { populateReferencesPanel as _populateReferencesPanel } from './details-panel/references-panel.js';
import { populateLocationsPanel as _populateLocationsPanel } from './details-panel/locations-panel.js';
import { createPropertiesTable, createFactValuesTable, createFactDimensionsTable } from './details-panel/table-builders.js';

// Re-export modularized functions
export const manageTabVisibility = _manageTabVisibility;
export const resetPanelTitles = _resetPanelTitles;
export const adjustPanelSizesForCube = _adjustPanelSizesForCube;
export const populateAttributesPanel = _populateAttributesPanel;
export const populateLabelsPanel = _populateLabelsPanel;
export const populateReferencesPanel = _populateReferencesPanel;
export const populateLocationsPanel = _populateLocationsPanel;

/**
 * Show details for a taxonomy object
 * @param {Object|string} obj - The object or name to show details for
 * @param {string} type - The type of object (concept, dimension, cube, etc.)
 */
export async function showDetails(obj, type) {
    // Track what type of object is currently displayed
    setCurrentDisplayedObject(type);
    
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Details Panel] No taxonomy data available for showing details');
        return;
    }
    
    let displayObj = obj;
    let name;
    
    // Handle different component types
    if (type === 'concept') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (typeof obj === 'string') {
            // If obj is a string, look up the full object
            if (xbrlModel.concepts) {
                displayObj = xbrlModel.concepts.find(c => c.name === name);
            }
            if (!displayObj) displayObj = { name };
        } else {
            // If obj is already an object, use it directly
            displayObj = obj;
        }
    } else if (type === 'dimension') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.dimensions) {
            displayObj = xbrlModel.dimensions.find(d => d.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'unit') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.units) {
            displayObj = xbrlModel.units.find(u => u.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'member') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.members) {
            displayObj = xbrlModel.members.find(m => m.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'abstract') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.abstracts) {
            displayObj = xbrlModel.abstracts.find(a => a.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'domainClass') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.domainClasses) {
            displayObj = xbrlModel.domainClasses.find(dr => dr.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'entity') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.entities) {
            displayObj = xbrlModel.entities.find(e => e.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'transform') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.transforms) {
            displayObj = xbrlModel.transforms.find(t => t.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'cube') {
        name = obj.name;
        displayObj = obj;
        // Special handling for cubes - show in a custom format
        await showCubeDetails(displayObj);
        return;
    } else if (type === 'domain') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.domains) {
            displayObj = xbrlModel.domains.find(d => d.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'network') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.networks) {
            displayObj = xbrlModel.networks.find(n => n.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'propertyType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.propertyTypes) {
            displayObj = xbrlModel.propertyTypes.find(pt => pt.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'dataType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.dataTypes) {
            displayObj = xbrlModel.dataTypes.find(dt => dt.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'cubeType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.cubeTypes) {
            displayObj = xbrlModel.cubeTypes.find(ct => ct.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'labelType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.labelTypes) {
            displayObj = xbrlModel.labelTypes.find(lt => lt.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'referenceType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.referenceTypes) {
            displayObj = xbrlModel.referenceTypes.find(rt => rt.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'relationshipType') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.relationshipTypes) {
            displayObj = xbrlModel.relationshipTypes.find(rt => rt.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'group') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.groups) {
            displayObj = xbrlModel.groups.find(g => g.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
        // Special handling for groups - show group contents
        showGroupDetails(displayObj);
        return;
    } else if (type === 'fact') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.facts) {
            displayObj = xbrlModel.facts.find(f => f.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
        
        // Show the details tabs for facts
        const detailsTabs = document.getElementById('details-tabs');
        if (detailsTabs) {
            detailsTabs.style.display = 'flex';
        }
        
        // Manage tab visibility - show only Properties and Grid View for facts
        manageTabVisibility('fact');
        
        // Make sure Properties tab is active by default
        document.querySelectorAll('.details-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.querySelectorAll('.details-tab-button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.detailsTab === 'properties') {
                btn.classList.add('active');
            }
        });
        document.getElementById('properties-tab').classList.add('active');
        
    } else if (type === 'footnote') {
        name = typeof obj === 'string' ? obj : obj.name;
        if (xbrlModel.footnotes) {
            displayObj = xbrlModel.footnotes.find(f => f.name === name);
        }
        if (!displayObj) displayObj = typeof obj === 'object' ? obj : { name };
    } else if (type === 'taxonomy') {
        name = typeof obj === 'string' ? obj : obj.name;
        // For taxonomy type, show the taxonomy object itself
        // Exclude factMaps from the display object as they are shown in Fact Maps tab
        const xbrlModel = getXbrlModel(taxonomyData);
        if (xbrlModel) {
            const { factMaps, ...taxonomyWithoutFactMaps } = xbrlModel;
            displayObj = {
                name: xbrlModel.name || name,
                version: xbrlModel.version,
                ...taxonomyWithoutFactMaps
            };
        } else {
            displayObj = { name };
        }
        
        // Show details tabs and manage visibility
        const detailsTabs = document.getElementById('details-tabs');
        if (detailsTabs) {
            detailsTabs.style.display = 'flex';
        }
        
        // Manage tab visibility for taxonomy context
        manageTabVisibility('taxonomy');
        
        // Show JSON in details content
        const details = document.getElementById('details-content');
        details.textContent = JSON.stringify(displayObj, null, 2);
        
        // Populate attributes panel with taxonomy info
        populateAttributesPanel(displayObj, taxonomyData);
        
        // Find labels and references for taxonomy
        const labels = xbrlModel.labels ? xbrlModel.labels.filter(l => l.relatedName === displayObj.name) : [];
        const references = xbrlModel.references ? xbrlModel.references.filter(r => r.relatedNames && r.relatedNames.includes(displayObj.name)) : [];
        
        // Populate labels and references
        populateLabelsPanel(labels, taxonomyData);
        populateReferencesPanel(references);
        
        // Populate QName locations
        populateLocationsPanel(displayObj.name, taxonomyData);
        
        // Build import paths view
        buildImportPathsView(displayObj);
        
        // Build final taxonomy view
        buildFinalTaxonomyView(displayObj);
        
        // Build JSON view
        buildJSONView(displayObj, taxonomyData.documentInfo);
        
        // Make properties tab active by default
        document.querySelectorAll('.details-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById('properties-tab').classList.add('active');
        
        // Return early since we've handled everything
        return;
    } else {
        // Check if this is a built-in object type (e.g., xbrl:conceptObject)
        const objName = typeof obj === 'string' ? obj : obj.name;
        if (isBuiltInObjectType(objName)) {
            // This is a built-in object type, create a display object for it
            displayObj = createBuiltInObjectDisplay(objName);
            name = objName; // Use the full QName for label lookups
        } else {
            name = obj.name;
            displayObj = obj;
        }
    }

    // Reset panel titles for non-cube/non-fact objects
    if (type !== 'fact') {
        resetPanelTitles();
    }

    // Show JSON in details content
    const details = document.getElementById('details-content');
    details.textContent = JSON.stringify(displayObj, null, 2);

    // Populate attributes table
    populateAttributesPanel(displayObj, taxonomyData);

    // Find labels and references
    const labels = xbrlModel.labels ? xbrlModel.labels.filter(l => l.relatedName === name) : [];
    const references = xbrlModel.references ? xbrlModel.references.filter(r => r.relatedNames && r.relatedNames.includes(name)) : [];

    // Populate labels and references
    populateLabelsPanel(labels, taxonomyData);
    populateReferencesPanel(references);
    
    // Populate locations (networks and domains where this QName appears)
    populateLocationsPanel(name, taxonomyData);
}

/**
 * Show details for a cube with specialized layout
 * @param {Object} cube - The cube object to display
 */
export async function showCubeDetails(cube) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Details Panel] No taxonomy data available for cube details');
        return;
    }
    
    const name = cube.name;

    // Show the details tabs for cubes
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    
    // Manage tab visibility - show only Properties and Grid View for cubes
    manageTabVisibility('cube');

    // Make sure Properties tab is active by default
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('properties-tab').classList.add('active');
    document.querySelector('[data-details-tab="properties"]').classList.add('active');

    // Build the grid view (use modular version if available)
    if (window.buildCubeGrid && typeof window.buildCubeGrid === 'function') {
        window.buildCubeGrid(cube);
    } else {
        console.warn('[Details Panel] buildCubeGrid function not available - cube grid will not be displayed');
        const gridContent = document.getElementById('cube-grid-content');
        if (gridContent) {
            gridContent.innerHTML = '<p style="padding: 20px; color: #888;">Cube grid visualization not available.</p>';
        }
    }

    // Build the fact view (use modular version if available)
    if (window.buildCubeFactView && typeof window.buildCubeFactView === 'function') {
        await window.buildCubeFactView(cube);
    } else {
        console.warn('[Details Panel] buildCubeFactView function not available - cube fact view will not be displayed');
        const factViewContent = document.getElementById('cube-fact-view-content');
        if (factViewContent) {
            factViewContent.innerHTML = '<p style="padding: 20px; color: #888;">Cube fact view not available.</p>';
        }
    }

    // Clear all panels and show cube-specific content
    const details = document.getElementById('details-content');
    details.textContent = JSON.stringify(cube, null, 2);

    // Update panel titles for cube-specific content
    document.querySelector('#attributes-panel h3').textContent = 'Cube Dimensions';
    document.querySelector('#labels-panel h3').textContent = 'Labels';
    document.querySelector('#labels-panel h3').style.display = 'none'; // Hide labels title for cubes
    document.querySelector('#references-panel h3').textContent = 'Cube Networks';
    
    // Adjust panel sizes for cubes
    adjustPanelSizesForCube();

    // Show Cube Dimensions in Attributes panel
    populateCubeDimensionsPanel(cube, taxonomyData);

    // Find labels for the cube
    const labels = xbrlModel.labels ? xbrlModel.labels.filter(l => l.relatedName === name) : [];
    
    // Populate labels
    populateLabelsPanel(labels, taxonomyData);

    // Populate Cube Networks in references panel
    populateCubeNetworksPanel(cube, taxonomyData);
    
    // Populate locations (networks and domains where this cube appears)
    populateLocationsPanel(name, taxonomyData);
}

/**
 * Show details for a group with specialized layout showing group contents
 * @param {Object} group - The group object to display
 */
export function showGroupDetails(group) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Details Panel] No taxonomy data available for group details');
        return;
    }
    
    const name = group.name;

    // Show the details tabs for groups (reuse cube tabs structure)
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    
    // Manage tab visibility - show only Properties and Grid View for groups
    manageTabVisibility('group');

    // Make sure Properties tab is active by default
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById('properties-tab').classList.add('active');
    document.querySelector('[data-details-tab="properties"]').classList.add('active');

    // Clear all panels and show group-specific content
    const details = document.getElementById('details-content');
    details.textContent = JSON.stringify(group, null, 2);

    // Update panel titles for Properties tab
    document.querySelector('#attributes-panel h3').textContent = 'Group Properties';
    document.querySelector('#labels-panel h3').textContent = 'Labels';
    document.querySelector('#labels-panel h3').style.display = 'block';
    document.querySelector('#references-panel h3').textContent = 'References';
    
    // Reset panel styles for Properties tab
    const attributesPanel = document.getElementById('attributes-panel');
    attributesPanel.style.flex = '';
    attributesPanel.style.maxHeight = '';
    attributesPanel.style.overflowY = '';
    
    const labelsPanel = document.getElementById('labels-panel');
    labelsPanel.style.flex = '';
    labelsPanel.style.maxHeight = '';
    labelsPanel.style.overflowY = '';
    labelsPanel.style.padding = '';
    labelsPanel.style.borderBottom = '';
    labelsPanel.style.overflow = '';
    
    const referencesPanel = document.getElementById('references-panel');
    referencesPanel.style.flex = '';
    referencesPanel.style.minHeight = '';
    referencesPanel.style.overflowY = '';

    // Show Group Properties in Attributes panel
    const attributesContent = document.getElementById('attributes-content');
    attributesContent.innerHTML = '';
    
    const propsTable = document.createElement('table');
    const propsTbody = document.createElement('tbody');
    
    // Add group name
    const nameRow = document.createElement('tr');
    const nameKeyCell = document.createElement('td');
    nameKeyCell.textContent = 'Name';
    nameKeyCell.style.fontWeight = 'bold';
    const nameValueCell = document.createElement('td');
    nameValueCell.textContent = group.name;
    nameRow.appendChild(nameKeyCell);
    nameRow.appendChild(nameValueCell);
    propsTbody.appendChild(nameRow);
    
    propsTable.appendChild(propsTbody);
    attributesContent.appendChild(propsTable);

    // Find labels for the group
    const labels = xbrlModel.labels ? xbrlModel.labels.filter(l => l.relatedName === name) : [];

    // Populate labels table
    const labelsContent = document.getElementById('labels-content');
    labelsContent.innerHTML = '';
    if (labels.length > 0) {
        populateLabelsPanel(labels, taxonomyData);
    } else {
        labelsContent.textContent = 'No labels found.';
    }

    // Populate references in references panel (Properties tab)
    const referencesContent = document.getElementById('references-content');
    referencesContent.innerHTML = '';
    
    // Find and display references for the group
    console.log('[Group Details] Looking for references for group:', name);
    console.log('[Group Details] All references:', xbrlModel.references);
    const references = xbrlModel.references ? 
        xbrlModel.references.filter(r => r.relatedNames && r.relatedNames.includes(name)) : [];
    console.log('[Group Details] Found references:', references);
    
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
            typeDiv.style.marginBottom = '15px';
            
            const typeHeader = document.createElement('h4');
            typeHeader.textContent = `Reference Type: ${type}`;
            typeHeader.style.marginBottom = '8px';
            typeHeader.style.color = '#495057';
            typeDiv.appendChild(typeHeader);

            const table = document.createElement('table');
            table.style.width = '100%';
            table.style.borderCollapse = 'collapse';
            
            const thead = document.createElement('thead');
            const headerRow = document.createElement('tr');
            headerRow.style.backgroundColor = '#e9ecef';
            
            ['Property', 'Value'].forEach(text => {
                const th = document.createElement('th');
                th.textContent = text;
                th.style.padding = '8px';
                th.style.textAlign = 'left';
                th.style.borderBottom = '2px solid #dee2e6';
                th.style.fontWeight = 'bold';
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            const tbody = document.createElement('tbody');
            
            // Build a map of property names to their dataTypes for link rendering
            const propertyTypeDataTypes = new Map();
            if (xbrlModel && xbrlModel.propertyTypes) {
                xbrlModel.propertyTypes.forEach(propType => {
                    if (propType.name && propType.dataType) {
                        propertyTypeDataTypes.set(propType.name, propType.dataType);
                    }
                });
            }
            
            grouped[type].forEach((ref, refIndex) => {
                if (ref.properties) {
                    const backgroundColor = refIndex % 2 === 0 ? '#e3f2fd' : '#ffffff';
                    
                    ref.properties.forEach(prop => {
                        const row = document.createElement('tr');
                        row.style.backgroundColor = backgroundColor;
                        
                        const propCell = document.createElement('td');
                        propCell.textContent = prop.property;
                        propCell.style.padding = '8px';
                        propCell.style.borderBottom = '1px solid #dee2e6';
                        
                        const valueCell = document.createElement('td');
                        valueCell.style.padding = '8px';
                        valueCell.style.borderBottom = '1px solid #dee2e6';
                        
                        // Check if this property has a dataType of xbrli:realURL
                        const dataType = propertyTypeDataTypes.get(prop.property);
                        if (dataType === 'xbrli:realURL' && prop.value && typeof prop.value === 'string') {
                            // Render as a clickable link
                            const link = document.createElement('a');
                            link.href = prop.value;
                            link.textContent = prop.value;
                            link.target = '_blank';
                            link.rel = 'noopener noreferrer';
                            link.style.color = '#0066cc';
                            link.style.textDecoration = 'underline';
                            valueCell.appendChild(link);
                        } else {
                            // Render as plain text
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
    
    // Populate locations (networks and domains where this group appears)
    populateLocationsPanel(name, taxonomyData);
    
    // Populate Group Contents in Contents tab
    const groupContentsContent = document.getElementById('group-contents-content');
    groupContentsContent.innerHTML = '';
    
    // Add padding to the container for better spacing
    groupContentsContent.style.padding = '20px';
    groupContentsContent.style.overflowY = 'auto';
    
    // Find group contents for this group
    const groupContents = xbrlModel.groupContents ? 
        xbrlModel.groupContents.filter(gc => gc.groupName === name) : [];
    
    if (groupContents.length > 0) {
        groupContents.forEach(gc => {
            if (gc.relatedNames && gc.relatedNames.length > 0) {
                // Categorize related names into networks, domains, cubes, and layouts
                const networks = [];
                const domains = [];
                const cubes = [];
                const layouts = [];
                const other = [];
                
                gc.relatedNames.forEach(relatedName => {
                    // Check what type this related name is
                    if (xbrlModel.networks && xbrlModel.networks.find(n => n.name === relatedName)) {
                        const network = xbrlModel.networks.find(n => n.name === relatedName);
                        networks.push(network);
                    } else if (xbrlModel.domains && xbrlModel.domains.find(d => d.name === relatedName)) {
                        const domain = xbrlModel.domains.find(d => d.name === relatedName);
                        domains.push(domain);
                    } else if (xbrlModel.cubes && xbrlModel.cubes.find(c => c.name === relatedName)) {
                        const cube = xbrlModel.cubes.find(c => c.name === relatedName);
                        cubes.push(cube);
                    } else if (xbrlModel.layouts && xbrlModel.layouts.find(l => l.name === relatedName)) {
                        const layout = xbrlModel.layouts.find(l => l.name === relatedName);
                        layouts.push(layout);
                    } else {
                        other.push(relatedName);
                    }
                });
                
                // Display Networks
                if (networks.length > 0) {
                    const networksSection = document.createElement('div');
                    networksSection.style.marginBottom = '30px';
                    
                    const networksTitle = document.createElement('h3');
                    networksTitle.textContent = `Networks (${networks.length})`;
                    networksTitle.style.marginTop = '0';
                    networksTitle.style.marginBottom = '15px';
                    networksTitle.style.color = '#2c3e50';
                    networksTitle.style.fontSize = '18px';
                    networksTitle.style.fontWeight = 'bold';
                    networksTitle.style.borderBottom = '2px solid #e0e0e0';
                    networksTitle.style.paddingBottom = '8px';
                    networksSection.appendChild(networksTitle);
                    
                    networks.forEach((network, index) => {
                        const networkDiv = buildNetworkSection(network, taxonomyData);
                        if (index > 0) {
                            networkDiv.style.marginTop = '15px';
                        }
                        networksSection.appendChild(networkDiv);
                    });
                    
                    groupContentsContent.appendChild(networksSection);
                }
                
                // Display Domains
                if (domains.length > 0) {
                    const domainsSection = document.createElement('div');
                    domainsSection.style.marginBottom = '30px';
                    
                    const domainsTitle = document.createElement('h3');
                    domainsTitle.textContent = `Domains (${domains.length})`;
                    domainsTitle.style.marginTop = '0';
                    domainsTitle.style.marginBottom = '15px';
                    domainsTitle.style.color = '#2c3e50';
                    domainsTitle.style.fontSize = '18px';
                    domainsTitle.style.fontWeight = 'bold';
                    domainsTitle.style.borderBottom = '2px solid #e0e0e0';
                    domainsTitle.style.paddingBottom = '8px';
                    domainsSection.appendChild(domainsTitle);
                    
                    domains.forEach((domain, index) => {
                        const domainDiv = buildDomainSection(domain, taxonomyData);
                        if (index > 0) {
                            domainDiv.style.marginTop = '15px';
                        }
                        domainsSection.appendChild(domainDiv);
                    });
                    
                    groupContentsContent.appendChild(domainsSection);
                }
                
                // Display Cubes
                if (cubes.length > 0) {
                    const cubesSection = document.createElement('div');
                    cubesSection.style.marginBottom = '30px';
                    
                    const cubesTitle = document.createElement('h3');
                    cubesTitle.textContent = `Cubes (${cubes.length})`;
                    cubesTitle.style.marginTop = '0';
                    cubesTitle.style.marginBottom = '15px';
                    cubesTitle.style.color = '#2c3e50';
                    cubesTitle.style.fontSize = '18px';
                    cubesTitle.style.fontWeight = 'bold';
                    cubesTitle.style.borderBottom = '2px solid #e0e0e0';
                    cubesTitle.style.paddingBottom = '8px';
                    cubesSection.appendChild(cubesTitle);
                    
                    cubes.forEach((cube, index) => {
                        const cubeDiv = buildCubeSection(cube, taxonomyData);
                        if (index > 0) {
                            cubeDiv.style.marginTop = '15px';
                        }
                        cubesSection.appendChild(cubeDiv);
                    });
                    
                    groupContentsContent.appendChild(cubesSection);
                    
                    // Automatically display the first cube in the Grid View tab
                    if (cubes.length > 0 && window.buildCubeGrid && typeof window.buildCubeGrid === 'function') {
                        console.log('[Group Details] Building grid view for first cube:', cubes[0].name);
                        window.buildCubeGrid(cubes[0]);
                    }
                }
                
                // Display Layouts
                if (layouts.length > 0) {
                    const layoutsSection = document.createElement('div');
                    layoutsSection.style.marginBottom = '30px';
                    
                    const layoutsTitle = document.createElement('h3');
                    layoutsTitle.textContent = `Layouts (${layouts.length})`;
                    layoutsTitle.style.marginTop = '0';
                    layoutsTitle.style.marginBottom = '15px';
                    layoutsTitle.style.color = '#2c3e50';
                    layoutsTitle.style.fontSize = '18px';
                    layoutsTitle.style.fontWeight = 'bold';
                    layoutsTitle.style.borderBottom = '2px solid #e0e0e0';
                    layoutsTitle.style.paddingBottom = '8px';
                    layoutsSection.appendChild(layoutsTitle);
                    
                    layouts.forEach((layout, index) => {
                        const layoutDiv = buildLayoutSection(layout, taxonomyData);
                        if (index > 0) {
                            layoutDiv.style.marginTop = '15px';
                        }
                        layoutsSection.appendChild(layoutDiv);
                    });
                    
                    groupContentsContent.appendChild(layoutsSection);
                }
                
                // Display Other items
                if (other.length > 0) {
                    const otherSection = document.createElement('div');
                    otherSection.style.marginBottom = '30px';
                    
                    const otherTitle = document.createElement('h3');
                    otherTitle.textContent = `Other Items (${other.length})`;
                    otherTitle.style.marginTop = '0';
                    otherTitle.style.marginBottom = '15px';
                    otherTitle.style.color = '#2c3e50';
                    otherTitle.style.fontSize = '18px';
                    otherTitle.style.fontWeight = 'bold';
                    otherTitle.style.borderBottom = '2px solid #e0e0e0';
                    otherTitle.style.paddingBottom = '8px';
                    otherSection.appendChild(otherTitle);
                    
                    const otherList = document.createElement('ul');
                    otherList.style.listStyleType = 'disc';
                    otherList.style.paddingLeft = '20px';
                    otherList.style.marginTop = '10px';
                    
                    other.forEach(itemName => {
                        const li = document.createElement('li');
                        li.textContent = itemName;
                        li.style.marginBottom = '8px';
                        li.style.fontSize = '14px';
                        otherList.appendChild(li);
                    });
                    
                    otherSection.appendChild(otherList);
                    groupContentsContent.appendChild(otherSection);
                }
            }
        });
    } else {
        const noContents = document.createElement('p');
        noContents.textContent = 'No group contents defined.';
        noContents.style.fontStyle = 'italic';
        noContents.style.color = '#888';
        noContents.style.padding = '10px 0';
        groupContentsContent.appendChild(noContents);
    }
}

/**
 * Build a collapsible cube section showing cube details
 */
function buildCubeSection(cube, taxonomyData) {
    const cubeSection = document.createElement('div');
    cubeSection.style.marginBottom = '15px';
    cubeSection.style.border = '1px solid #ddd';
    cubeSection.style.borderRadius = '4px';
    
    // Create header
    const header = document.createElement('div');
    header.style.cursor = 'pointer';
    header.style.padding = '10px';
    header.style.backgroundColor = '#f8f9fa';
    header.style.borderRadius = '4px 4px 0 0';
    header.style.fontWeight = 'bold';
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.userSelect = 'none';
    
    // Add expand/collapse icon
    const icon = document.createElement('span');
    icon.textContent = '▶';
    icon.style.marginRight = '8px';
    icon.style.fontSize = '10px';
    icon.style.transition = 'transform 0.2s';
    header.appendChild(icon);
    
    // Add cube name
    const cubeName = document.createElement('span');
    cubeName.textContent = cube.name;
    header.appendChild(cubeName);
    
    // Create content area (initially hidden)
    const content = document.createElement('div');
    content.style.display = 'none';
    content.style.padding = '10px';
    content.style.backgroundColor = '#fff';
    content.style.borderTop = '1px solid #ddd';
    
    // Add cube type
    if (cube.cubeType) {
        const typeDiv = document.createElement('div');
        typeDiv.style.marginBottom = '10px';
        typeDiv.innerHTML = `<strong>Cube Type:</strong> ${cube.cubeType}`;
        content.appendChild(typeDiv);
    }
    
    // Add cube dimensions
    if (cube.cubeDimensions && cube.cubeDimensions.length > 0) {
        const dimsTitle = document.createElement('div');
        dimsTitle.textContent = 'Dimensions:';
        dimsTitle.style.fontWeight = 'bold';
        dimsTitle.style.marginTop = '10px';
        dimsTitle.style.marginBottom = '5px';
        content.appendChild(dimsTitle);
        
        const dimsList = document.createElement('ul');
        dimsList.style.listStyleType = 'disc';
        dimsList.style.paddingLeft = '20px';
        dimsList.style.marginTop = '5px';
        
        cube.cubeDimensions.forEach(dim => {
            const li = document.createElement('li');
            li.textContent = `${dim.dimensionName}${dim.domainName ? ` (${dim.domainName})` : ''}`;
            li.style.marginBottom = '3px';
            dimsList.appendChild(li);
        });
        
        content.appendChild(dimsList);
    }
    
    // Add "View Grid" button
    const viewGridButton = document.createElement('button');
    viewGridButton.textContent = '📊 View Grid';
    viewGridButton.style.marginTop = '10px';
    viewGridButton.style.padding = '6px 12px';
    viewGridButton.style.backgroundColor = '#007bff';
    viewGridButton.style.color = '#fff';
    viewGridButton.style.border = 'none';
    viewGridButton.style.borderRadius = '4px';
    viewGridButton.style.cursor = 'pointer';
    viewGridButton.style.fontSize = '13px';
    viewGridButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent toggling the section
        if (window.buildCubeGrid && typeof window.buildCubeGrid === 'function') {
            console.log('[Cube Section] Building grid view for cube:', cube.name);
            window.buildCubeGrid(cube);
            
            // Switch to Grid View tab
            // Hide all tab contents
            document.querySelectorAll('.details-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.details-tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Activate Grid View tab
            const gridTabButton = document.querySelector('[data-details-tab="grid"]');
            const gridTab = document.getElementById('grid-tab');
            
            if (gridTabButton && gridTab) {
                gridTabButton.classList.add('active');
                gridTab.classList.add('active');
            }
        }
    });
    content.appendChild(viewGridButton);
    
    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.style.display = isExpanded ? 'block' : 'none';
        icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0deg)';
    });
    
    cubeSection.appendChild(header);
    cubeSection.appendChild(content);
    
    return cubeSection;
}

/**
 * Build a collapsible layout section showing layout details
 */
function buildLayoutSection(layout, taxonomyData) {
    const layoutSection = document.createElement('div');
    layoutSection.style.marginBottom = '15px';
    layoutSection.style.border = '1px solid #ddd';
    layoutSection.style.borderRadius = '4px';
    
    // Create header
    const header = document.createElement('div');
    header.style.cursor = 'pointer';
    header.style.padding = '10px';
    header.style.backgroundColor = '#e8f5e9';
    header.style.borderRadius = '4px 4px 0 0';
    header.style.fontWeight = 'bold';
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.userSelect = 'none';
    
    // Add expand/collapse icon
    const icon = document.createElement('span');
    icon.textContent = '▶';
    icon.style.marginRight = '8px';
    icon.style.fontSize = '10px';
    icon.style.transition = 'transform 0.2s';
    header.appendChild(icon);
    
    // Add layout icon
    const layoutIcon = document.createElement('span');
    layoutIcon.textContent = '⊞';
    layoutIcon.style.marginRight = '8px';
    layoutIcon.style.fontSize = '16px';
    header.appendChild(layoutIcon);
    
    // Add layout name
    const layoutName = document.createElement('span');
    layoutName.textContent = layout.name;
    header.appendChild(layoutName);
    
    // Create content area (initially hidden)
    const content = document.createElement('div');
    content.style.display = 'none';
    content.style.padding = '10px';
    content.style.backgroundColor = '#fff';
    content.style.borderTop = '1px solid #ddd';
    
    // Add table construction type if present
    if (layout.tableConstruction) {
        const constructionDiv = document.createElement('div');
        constructionDiv.style.marginBottom = '10px';
        constructionDiv.innerHTML = `<strong>Table Construction:</strong> ${layout.tableConstruction}`;
        content.appendChild(constructionDiv);
    }
    
    // Add data tables
    if (layout.dataTables && layout.dataTables.length > 0) {
        const tablesTitle = document.createElement('div');
        tablesTitle.textContent = 'Data Tables:';
        tablesTitle.style.fontWeight = 'bold';
        tablesTitle.style.marginTop = '10px';
        tablesTitle.style.marginBottom = '5px';
        content.appendChild(tablesTitle);
        
        const tablesList = document.createElement('ul');
        tablesList.style.listStyleType = 'disc';
        tablesList.style.paddingLeft = '20px';
        tablesList.style.marginTop = '5px';
        
        layout.dataTables.forEach(table => {
            const li = document.createElement('li');
            let tableInfo = table.name;
            if (table.tableType) {
                tableInfo += ` (${table.tableType})`;
            }
            if (table.cubeName) {
                tableInfo += ` - Cube: ${table.cubeName}`;
            }
            li.textContent = tableInfo;
            li.style.marginBottom = '3px';
            tablesList.appendChild(li);
        });
        
        content.appendChild(tablesList);
    }
    
    // Add "View Layout" button
    const viewLayoutButton = document.createElement('button');
    viewLayoutButton.textContent = '⊞ View Layout';
    viewLayoutButton.style.marginTop = '10px';
    viewLayoutButton.style.padding = '6px 12px';
    viewLayoutButton.style.backgroundColor = '#4caf50';
    viewLayoutButton.style.color = '#fff';
    viewLayoutButton.style.border = 'none';
    viewLayoutButton.style.borderRadius = '4px';
    viewLayoutButton.style.cursor = 'pointer';
    viewLayoutButton.style.fontSize = '13px';
    viewLayoutButton.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent toggling the section
        
        // Switch to Layout tab and render this layout
        // Hide all tab contents
        document.querySelectorAll('.details-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // Remove active class from all tab buttons
        document.querySelectorAll('.details-tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Activate Layout tab
        const layoutTabButton = document.querySelector('[data-details-tab="layout"]');
        const layoutTab = document.getElementById('layout-tab');
        
        if (layoutTabButton && layoutTab) {
            layoutTabButton.classList.add('active');
            layoutTab.classList.add('active');
            
            // Show the Layout tab button if it's hidden
            layoutTabButton.style.display = 'block';
            
            // Render the layout
            renderLayoutInTab(layout, taxonomyData);
        }
    });
    content.appendChild(viewLayoutButton);
    
    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.style.display = isExpanded ? 'block' : 'none';
        icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0deg)';
    });
    
    layoutSection.appendChild(header);
    layoutSection.appendChild(content);
    
    return layoutSection;
}

/**
 * Build a collapsible domain section showing domain tree
 */
function buildDomainSection(domain, taxonomyData) {
    const domainSection = document.createElement('div');
    domainSection.style.marginBottom = '15px';
    domainSection.style.border = '1px solid #ddd';
    domainSection.style.borderRadius = '4px';
    
    // Create header
    const header = document.createElement('div');
    header.style.cursor = 'pointer';
    header.style.padding = '10px';
    header.style.backgroundColor = '#f0f8ff';
    header.style.borderRadius = '4px 4px 0 0';
    header.style.fontWeight = 'bold';
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.userSelect = 'none';
    
    // Add expand/collapse icon
    const icon = document.createElement('span');
    icon.textContent = '▶';
    icon.style.marginRight = '8px';
    icon.style.fontSize = '10px';
    icon.style.transition = 'transform 0.2s';
    header.appendChild(icon);
    
    // Add domain name
    const domainName = document.createElement('span');
    domainName.textContent = domain.name;
    header.appendChild(domainName);
    
    // Create content area (initially hidden)
    const content = document.createElement('div');
    content.style.display = 'none';
    content.style.padding = '10px';
    content.style.backgroundColor = '#fff';
    content.style.borderTop = '1px solid #ddd';
    
    // Build the domain tree (reuse existing logic)
    if (domain.relationships && domain.relationships.length > 0 && domain.root) {
        // Build children map
        const childrenMap = {};
        const selfReferences = new Set();
        
        domain.relationships.forEach(rel => {
            if (!childrenMap[rel.source]) childrenMap[rel.source] = [];
            childrenMap[rel.source].push({ target: rel.target, order: rel.order || 0 });
            if (rel.source === rel.target) {
                selfReferences.add(rel.source);
            }
        });
        
        // Sort children by order descending
        Object.keys(childrenMap).forEach(source => {
            childrenMap[source].sort((a, b) => b.order - a.order);
        });
        
        const treeUl = document.createElement('ul');
        treeUl.style.listStyleType = 'none';
        treeUl.style.paddingLeft = '0';
        treeUl.style.marginTop = '10px';
        
        // Build tree from root - use window function if available
        if (window.buildRelationshipTree) {
            window.buildRelationshipTree(treeUl, domain.root, childrenMap, domain.relationships, selfReferences, null, 'name', 0);
        }
        
        content.appendChild(treeUl);
        
        // Attach node handlers
        if (window.attachNodeHandlers) {
            window.attachNodeHandlers(content);
        }
    } else {
        const noRels = document.createElement('div');
        noRels.style.fontStyle = 'italic';
        noRels.style.color = '#888';
        noRels.style.fontSize = '13px';
        noRels.style.padding = '10px 0';
        noRels.textContent = 'No relationships defined.';
        content.appendChild(noRels);
    }
    
    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.style.display = isExpanded ? 'block' : 'none';
        icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0deg)';
    });
    
    domainSection.appendChild(header);
    domainSection.appendChild(content);
    
    return domainSection;
}

// The following functions have been moved to separate modules in ./details-panel/
// - resetPanelTitles() -> tab-management.js
// - adjustPanelSizesForCube() -> tab-management.js
// - populateAttributesPanel() -> attributes-panel.js
// - createPropertiesTable() -> table-builders.js  
// - createFactValuesTable() -> table-builders.js
// - createFactDimensionsTable() -> table-builders.js
// - populateLabelsPanel() -> labels-panel.js
// - populateReferencesPanel() -> references-panel.js
// - getPropertyLabelForReference() -> references-panel.js (internal helper)
// - populateLocationsPanel() -> locations-panel.js

/**
 * Populate the cube dimensions panel
 * @param {Object} cube - The cube object
 * @param {Object} taxonomyData - The taxonomy data
 */
function populateCubeDimensionsPanel(cube, taxonomyData) {
    const attributesContent = document.getElementById('attributes-content');
    attributesContent.innerHTML = '';
    
    // Add Cube Type label at the top
    const cubeTypeDiv = document.createElement('div');
    cubeTypeDiv.style.padding = '12px';
    cubeTypeDiv.style.backgroundColor = '#f5f5f5';
    cubeTypeDiv.style.marginBottom = '20px';
    cubeTypeDiv.style.borderRadius = '4px';
    cubeTypeDiv.style.border = '1px solid #ddd';
    
    const cubeTypeLabel = document.createElement('span');
    cubeTypeLabel.textContent = 'Cube Type: ';
    cubeTypeLabel.style.fontWeight = 'bold';
    cubeTypeLabel.style.fontSize = '14px';
    
    const cubeTypeValue = document.createElement('span');
    cubeTypeValue.textContent = cube.cubeType || 'Not specified';
    cubeTypeValue.style.fontSize = '14px';
    
    cubeTypeDiv.appendChild(cubeTypeLabel);
    cubeTypeDiv.appendChild(cubeTypeValue);
    attributesContent.appendChild(cubeTypeDiv);
    
    if (cube.cubeDimensions && cube.cubeDimensions.length > 0) {
        // Create a block for each dimension
        cube.cubeDimensions.forEach((dim, index) => {
            const dimensionBlock = document.createElement('div');
            dimensionBlock.style.marginBottom = '25px';
            dimensionBlock.style.padding = '15px';
            dimensionBlock.style.backgroundColor = index % 2 === 0 ? '#f9f9f9' : '#ffffff';
            dimensionBlock.style.border = '1px solid #ddd';
            dimensionBlock.style.borderRadius = '6px';
            dimensionBlock.style.borderLeft = '4px solid #1976D2';
            
            // Dimension name header (clickable)
            const dimensionHeader = document.createElement('div');
            dimensionHeader.style.marginBottom = '12px';
            dimensionHeader.style.paddingBottom = '8px';
            dimensionHeader.style.borderBottom = '2px solid #1976D2';
            dimensionHeader.style.cursor = 'pointer';
            dimensionHeader.style.display = 'flex';
            dimensionHeader.style.alignItems = 'center';
            dimensionHeader.style.justifyContent = 'space-between';
            
            const dimensionName = document.createElement('h4');
            dimensionName.textContent = dim.dimensionName || 'Unnamed Dimension';
            dimensionName.style.margin = '0';
            dimensionName.style.color = '#1976D2';
            dimensionName.style.fontSize = '16px';
            dimensionName.style.fontWeight = 'bold';
            
            // Toggle icon
            const toggleIcon = document.createElement('span');
            toggleIcon.textContent = '▼';
            toggleIcon.style.fontSize = '12px';
            toggleIcon.style.color = '#1976D2';
            toggleIcon.style.transition = 'transform 0.3s';
            
            dimensionHeader.appendChild(dimensionName);
            dimensionHeader.appendChild(toggleIcon);
            dimensionBlock.appendChild(dimensionHeader);
            
            // Collapsible content container
            const collapsibleContent = document.createElement('div');
            collapsibleContent.style.overflow = 'hidden';
            collapsibleContent.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
            collapsibleContent.style.maxHeight = '3000px'; // Open by default
            collapsibleContent.style.opacity = '1';
            
            // Optional Dimension line
            const optionalLine = document.createElement('div');
            optionalLine.style.marginBottom = '15px';
            optionalLine.style.padding = '8px';
            optionalLine.style.backgroundColor = '#e3f2fd';
            optionalLine.style.borderRadius = '4px';
            
            const optionalLabel = document.createElement('span');
            optionalLabel.textContent = 'Optional Dimension: ';
            optionalLabel.style.fontWeight = 'bold';
            optionalLabel.style.fontSize = '13px';
            
            const optionalValue = document.createElement('span');
            optionalValue.textContent = dim.allowDomainFacts !== undefined ? String(dim.allowDomainFacts) : 'false';
            optionalValue.style.fontSize = '13px';
            optionalValue.style.color = dim.allowDomainFacts ? '#2e7d32' : '#d32f2f';
            
            optionalLine.appendChild(optionalLabel);
            optionalLine.appendChild(optionalValue);
            collapsibleContent.appendChild(optionalLine);
            
            // Domain Data Type (if present)
            if (dim.domainDataType) {
                const dataTypeLine = document.createElement('div');
                dataTypeLine.style.marginBottom = '15px';
                dataTypeLine.style.padding = '8px';
                dataTypeLine.style.backgroundColor = '#e3f2fd';
                dataTypeLine.style.borderRadius = '4px';
                
                const dataTypeLabel = document.createElement('span');
                dataTypeLabel.textContent = 'Domain Data Type: ';
                dataTypeLabel.style.fontWeight = 'bold';
                dataTypeLabel.style.fontSize = '13px';
                
                const dataTypeValue = document.createElement('span');
                dataTypeValue.textContent = dim.domainDataType;
                dataTypeValue.style.fontSize = '13px';
                dataTypeValue.style.color = '#1976d2';
                
                dataTypeLine.appendChild(dataTypeLabel);
                dataTypeLine.appendChild(dataTypeValue);
                collapsibleContent.appendChild(dataTypeLine);
            }
            
            // Period Constraints (if present)
            if (dim.periodConstraints && dim.periodConstraints.length > 0) {
                const constraintsSection = createPeriodConstraintsBlock(dim.periodConstraints);
                collapsibleContent.appendChild(constraintsSection);
            }
            
            // Dimension Properties
            if (dim.dimensionName && getXbrlModel(taxonomyData).dimensions) {
                const dimensionObj = getXbrlModel(taxonomyData).dimensions.find(d => d.name === dim.dimensionName);
                if (dimensionObj) {
                    const dimPropsSection = createDimensionPropertiesBlock(dimensionObj);
                    collapsibleContent.appendChild(dimPropsSection);
                }
            }
            
            // Domain Class Properties
            if (dim.dimensionName && getXbrlModel(taxonomyData).dimensions) {
                const dimensionObj = getXbrlModel(taxonomyData).dimensions.find(d => d.name === dim.dimensionName);
                if (dimensionObj && dimensionObj.domainClass && getXbrlModel(taxonomyData).domainClasses) {
                    const domainClassObj = getXbrlModel(taxonomyData).domainClasses.find(dr => dr.name === dimensionObj.domainClass);
                    if (domainClassObj) {
                        const rootPropsSection = createDomainClassPropertiesBlock(domainClassObj);
                        collapsibleContent.appendChild(rootPropsSection);
                    }
                }
            }
            
            // Domain Properties
            const allDomainNames = [];
            if (dim.domainName) {
                allDomainNames.push(dim.domainName);
            }
            if (dim.typedDomainNames && Array.isArray(dim.typedDomainNames) && dim.typedDomainNames.length > 0) {
                allDomainNames.push(...dim.typedDomainNames);
            }
            
            if (allDomainNames.length > 0 && getXbrlModel(taxonomyData).domains) {
                allDomainNames.forEach(domainName => {
                    const domainObj = getXbrlModel(taxonomyData).domains.find(d => d.name === domainName);
                    if (domainObj) {
                        const domainPropsSection = createDomainPropertiesBlock(domainObj);
                        collapsibleContent.appendChild(domainPropsSection);
                    }
                });
            }
            
            dimensionBlock.appendChild(collapsibleContent);
            
            // Toggle functionality
            let isExpanded = true;
            dimensionHeader.addEventListener('click', () => {
                isExpanded = !isExpanded;
                if (isExpanded) {
                    collapsibleContent.style.maxHeight = '3000px';
                    collapsibleContent.style.opacity = '1';
                    toggleIcon.style.transform = 'rotate(0deg)';
                } else {
                    collapsibleContent.style.maxHeight = '0';
                    collapsibleContent.style.opacity = '0';
                    toggleIcon.style.transform = 'rotate(-90deg)';
                }
            });
            
            attributesContent.appendChild(dimensionBlock);
        });
    } else {
        attributesContent.textContent = 'No cube dimensions available.';
    }
}

/**
 * Helper to get label for a QName property
 */
function getPropertyLabel(propertyQName) {
    if (!propertyQName) return propertyQName;
    
    const labels = getXbrlModel(taxonomyData).labels ? 
        getXbrlModel(taxonomyData).labels.filter(l => l.relatedName === propertyQName && l.labelType === 'xbrl:label') : [];
    
    return labels.length > 0 ? labels[0].value : propertyQName;
}

/**
 * Create a properties subsection with property rows
 */
function createPropertiesSubsection(properties, title, bgColor, borderColor) {
    if (!properties || properties.length === 0) {
        return null;
    }
    
    const section = document.createElement('div');
    section.style.marginTop = '10px';
    section.style.marginBottom = '5px';
    section.style.padding = '8px';
    section.style.backgroundColor = bgColor;
    section.style.borderRadius = '3px';
    section.style.border = `1px solid ${borderColor}`;
    
    const subtitle = document.createElement('h6');
    subtitle.textContent = title;
    subtitle.style.margin = '0 0 8px 0';
    subtitle.style.color = borderColor;
    subtitle.style.fontSize = '13px';
    subtitle.style.fontWeight = 'bold';
    section.appendChild(subtitle);
    
    properties.forEach(prop => {
        const line = document.createElement('div');
        const propertyLabel = getPropertyLabel(prop.property);
        line.innerHTML = `<strong>${propertyLabel}:</strong> ${typeof prop.value === 'object' ? JSON.stringify(prop.value) : prop.value}`;
        line.style.marginBottom = '4px';
        line.style.fontSize = '12px';
        section.appendChild(line);
    });
    
    return section;
}

/**
 * Create a period constraints block
 */
function createPeriodConstraintsBlock(periodConstraints) {
    const section = document.createElement('div');
    section.style.marginBottom = '15px';
    section.style.padding = '10px';
    section.style.backgroundColor = '#fff8e1';
    section.style.borderRadius = '4px';
    section.style.border = '1px solid #f9a825';
    
    const title = document.createElement('h5');
    title.textContent = 'Period Constraints';
    title.style.margin = '0 0 10px 0';
    title.style.color = '#f57f17';
    title.style.fontSize = '14px';
    title.style.fontWeight = 'bold';
    section.appendChild(title);
    
    // Add explanatory text
    const explanation = document.createElement('div');
    explanation.style.marginBottom = '12px';
    explanation.style.padding = '8px';
    explanation.style.backgroundColor = '#fff9e6';
    explanation.style.borderLeft = '3px solid #f57f17';
    explanation.style.fontSize = '12px';
    explanation.style.fontStyle = 'italic';
    explanation.style.color = '#666';
    explanation.innerHTML = 'Facts must satisfy <strong>ALL</strong> conditions within a constraint. Multiple constraints are alternatives (OR).';
    section.appendChild(explanation);
    
    periodConstraints.forEach((constraint, index) => {
        const constraintDiv = document.createElement('div');
        constraintDiv.style.marginBottom = '12px';
        constraintDiv.style.paddingBottom = '12px';
        constraintDiv.style.fontSize = '13px';
        
        // Add constraint number header
        const constraintHeader = document.createElement('div');
        constraintHeader.textContent = `Constraint ${index + 1}`;
        constraintHeader.style.fontWeight = 'bold';
        constraintHeader.style.color = '#f57f17';
        constraintHeader.style.marginBottom = '6px';
        constraintHeader.style.fontSize = '13px';
        constraintDiv.appendChild(constraintHeader);
        
        // Add "All of the following must be true" text
        const allConditions = document.createElement('div');
        allConditions.textContent = 'All of the following must be true:';
        allConditions.style.fontSize = '12px';
        allConditions.style.fontStyle = 'italic';
        allConditions.style.color = '#555';
        allConditions.style.marginBottom = '6px';
        allConditions.style.paddingLeft = '10px';
        constraintDiv.appendChild(allConditions);
        
        // Container for conditions with visual AND indicators
        const conditionsContainer = document.createElement('div');
        conditionsContainer.style.paddingLeft = '20px';
        
        const fields = [
            ['Period Type', constraint.periodType],
            ['Time Span', constraint.timeSpan],
            ['Period Pattern', constraint.periodPattern]
        ];
        
        if (constraint.endDate) {
            const endDateStr = [
                constraint.endDate.conceptName,
                constraint.endDate.timeShift,
                constraint.endDate.context,
                constraint.endDate.value
            ].filter(v => v != null).join(', ');
            fields.push(['End Date', endDateStr]);
        }
        
        // Filter out null values before rendering
        const validFields = fields.filter(([label, value]) => value != null);
        
        validFields.forEach(([label, value], fieldIndex) => {
            const fieldDiv = document.createElement('div');
            fieldDiv.style.display = 'flex';
            fieldDiv.style.alignItems = 'center';
            fieldDiv.style.marginBottom = '6px';
            
            // Add checkmark bullet
            const bullet = document.createElement('span');
            bullet.textContent = '✓';
            bullet.style.color = '#4caf50';
            bullet.style.fontWeight = 'bold';
            bullet.style.marginRight = '8px';
            bullet.style.fontSize = '14px';
            fieldDiv.appendChild(bullet);
            
            // Add the field content
            const content = document.createElement('div');
            content.innerHTML = `<strong>${label}:</strong> ${value}`;
            content.style.fontSize = '13px';
            fieldDiv.appendChild(content);
            
            conditionsContainer.appendChild(fieldDiv);
            
            // Add AND indicator between conditions (except after last one)
            if (fieldIndex < validFields.length - 1) {
                const andIndicator = document.createElement('div');
                andIndicator.textContent = 'AND';
                andIndicator.style.fontSize = '11px';
                andIndicator.style.fontWeight = 'bold';
                andIndicator.style.color = '#999';
                andIndicator.style.marginLeft = '24px';
                andIndicator.style.marginBottom = '4px';
                conditionsContainer.appendChild(andIndicator);
            }
        });
        
        constraintDiv.appendChild(conditionsContainer);
        section.appendChild(constraintDiv);
        
        // Add "OR" divider between constraints (except after the last one)
        if (index < periodConstraints.length - 1) {
            const divider = document.createElement('div');
            divider.style.display = 'flex';
            divider.style.alignItems = 'center';
            divider.style.margin = '12px 0';
            divider.style.color = '#f57f17';
            divider.style.fontWeight = 'bold';
            divider.style.fontSize = '12px';
            
            const leftLine = document.createElement('div');
            leftLine.style.flex = '1';
            leftLine.style.height = '2px';
            leftLine.style.backgroundColor = '#f9a825';
            leftLine.style.marginRight = '10px';
            
            const orText = document.createElement('span');
            orText.textContent = 'OR';
            orText.style.padding = '0 5px';
            
            const rightLine = document.createElement('div');
            rightLine.style.flex = '1';
            rightLine.style.height = '2px';
            rightLine.style.backgroundColor = '#f9a825';
            rightLine.style.marginLeft = '10px';
            
            divider.appendChild(leftLine);
            divider.appendChild(orText);
            divider.appendChild(rightLine);
            
            section.appendChild(divider);
        }
    });
    
    return section;
}

/**
 * Create a dimension properties block
 */
function createDimensionPropertiesBlock(dimensionObj) {
    const section = document.createElement('div');
    section.style.marginBottom = '15px';
    section.style.padding = '10px';
    section.style.backgroundColor = '#fce4ec';
    section.style.borderRadius = '4px';
    section.style.border = '1px solid #e91e63';
    
    const title = document.createElement('h5');
    title.textContent = 'Dimension Properties';
    title.style.margin = '0 0 10px 0';
    title.style.color = '#c2185b';
    title.style.fontSize = '14px';
    title.style.fontWeight = 'bold';
    section.appendChild(title);
    
    const fields = [
        ['Name', dimensionObj.name],
        ['Namespace', dimensionObj.namespace],
        ['Type', dimensionObj.type],
        ['Period Type', dimensionObj.periodType],
        ['Domain Class', dimensionObj.domainClass]
    ];
    
    fields.forEach(([label, value]) => {
        if (value != null) {
            const line = document.createElement('div');
            line.innerHTML = `<strong>${label}:</strong> ${value}`;
            line.style.marginBottom = '4px';
            line.style.fontSize = '13px';
            section.appendChild(line);
        }
    });
    
    // Add properties subsection if present
    if (dimensionObj.properties && dimensionObj.properties.length > 0) {
        const propsSubsection = createPropertiesSubsection(
            dimensionObj.properties, 
            'Additional Properties', 
            '#fce4ec', 
            '#c2185b'
        );
        if (propsSubsection) {
            section.appendChild(propsSubsection);
        }
    }
    
    return section;
}

/**
 * Create a domain class properties block
 */
function createDomainClassPropertiesBlock(domainClassObj) {
    const section = document.createElement('div');
    section.style.marginBottom = '15px';
    section.style.padding = '10px';
    section.style.backgroundColor = '#fff3e0';
    section.style.borderRadius = '4px';
    section.style.border = '1px solid #ff9800';
    
    const title = document.createElement('h5');
    title.textContent = 'Domain Class Properties';
    title.style.margin = '0 0 10px 0';
    title.style.color = '#ef6c00';
    title.style.fontSize = '14px';
    title.style.fontWeight = 'bold';
    section.appendChild(title);
    
    const fields = [
        ['Name', domainClassObj.name],
        ['Namespace', domainClassObj.namespace],
        ['Type', domainClassObj.type]
    ];
    
    fields.forEach(([label, value]) => {
        if (value != null) {
            const line = document.createElement('div');
            line.innerHTML = `<strong>${label}:</strong> ${value}`;
            line.style.marginBottom = '4px';
            line.style.fontSize = '13px';
            section.appendChild(line);
        }
    });
    
    // Add allowedDomainItems if present
    if (domainClassObj.allowedDomainItems && Array.isArray(domainClassObj.allowedDomainItems) && domainClassObj.allowedDomainItems.length > 0) {
        const line = document.createElement('div');
        line.style.marginBottom = '8px';
        line.style.fontSize = '13px';
        line.style.marginTop = '8px';
        
        const label = document.createElement('strong');
        label.textContent = 'Allowed Domain Items:';
        line.appendChild(label);
        
        const itemsList = document.createElement('ul');
        itemsList.style.margin = '4px 0 0 20px';
        itemsList.style.padding = '0';
        
        domainClassObj.allowedDomainItems.forEach(item => {
            const listItem = document.createElement('li');
            const taxonomyData = getTaxonomyData();
            // Try to find a label for this QName
            const label = taxonomyData?.taxonomy?.labels?.find(l => 
                l.relatedName === item && 
                (l.labelType === 'xbrl:label' || !l.labelType) &&
                l.language && l.language.startsWith('en')
            );
            // Show "Label (qname)" if label exists, otherwise just the qname
            listItem.textContent = label ? `${label.value} (${item})` : item;
            listItem.style.fontSize = '13px';
            listItem.style.marginBottom = '2px';
            itemsList.appendChild(listItem);
        });
        
        line.appendChild(itemsList);
        section.appendChild(line);
    }
    
    // Add properties subsection if present
    if (domainClassObj.properties && domainClassObj.properties.length > 0) {
        const propsSubsection = createPropertiesSubsection(
            domainClassObj.properties, 
            'Additional Properties', 
            '#fff3e0', 
            '#ef6c00'
        );
        if (propsSubsection) {
            section.appendChild(propsSubsection);
        }
    }
    
    return section;
}

/**
 * Create a domain properties block
 */
function createDomainPropertiesBlock(domainObj) {
    const section = document.createElement('div');
    section.style.marginBottom = '15px';
    section.style.padding = '10px';
    section.style.backgroundColor = '#f3e5f5';
    section.style.borderRadius = '4px';
    section.style.border = '1px solid #9c27b0';
    
    const title = document.createElement('h5');
    title.textContent = `Domain Properties: ${domainObj.name}`;
    title.style.margin = '0 0 10px 0';
    title.style.color = '#7b1fa2';
    title.style.fontSize = '14px';
    title.style.fontWeight = 'bold';
    section.appendChild(title);
    
    // Count relationships
    const relationshipCount = (domainObj.relationships && Array.isArray(domainObj.relationships)) 
        ? domainObj.relationships.length 
        : 0;
    
    const fields = [
        ['Name', domainObj.name],
        ['Root', domainObj.root],
        ['Relationships', relationshipCount > 0 ? relationshipCount : 'N/A']
    ];
    
    fields.forEach(([label, value]) => {
        if (value != null) {
            const line = document.createElement('div');
            line.innerHTML = `<strong>${label}:</strong> ${value}`;
            line.style.marginBottom = '4px';
            line.style.fontSize = '13px';
            section.appendChild(line);
        }
    });
    
    // Add properties subsection if present
    if (domainObj.properties && domainObj.properties.length > 0) {
        const propsSubsection = createPropertiesSubsection(
            domainObj.properties, 
            'Additional Properties', 
            '#f3e5f5', 
            '#7b1fa2'
        );
        if (propsSubsection) {
            section.appendChild(propsSubsection);
        }
    }
    
    return section;
}

/**
 * Create period constraints row for cube dimensions
 * @param {Array} periodConstraints - Array of period constraint objects
 * @returns {HTMLElement} The constraints row element
 */
function createPeriodConstraintsRow(periodConstraints) {
    const constraintsRow = document.createElement('tr');
    const constraintsCell = document.createElement('td');
    constraintsCell.colSpan = 3;
    constraintsCell.style.padding = '10px';
    constraintsCell.style.backgroundColor = '#fff8e1';
    constraintsCell.style.borderTop = '1px solid #ddd';

    const constraintsDiv = document.createElement('div');
    const constraintsTitle = document.createElement('h5');
    constraintsTitle.textContent = 'Period Constraints:';
    constraintsTitle.style.margin = '0 0 10px 0';
    constraintsTitle.style.color = '#666';
    constraintsDiv.appendChild(constraintsTitle);

    const constraintsTable = document.createElement('table');
    constraintsTable.style.width = '100%';
    constraintsTable.style.fontSize = '0.85em';
    constraintsTable.style.marginLeft = '20px';
    constraintsTable.style.borderCollapse = 'collapse';
    constraintsTable.style.border = '1px solid #ddd';

    // Create header for constraints table
    const constraintsThead = document.createElement('thead');
    const constraintsHeaderRow = document.createElement('tr');
    constraintsHeaderRow.style.backgroundColor = '#f0f0f0';
    ['Period Type', 'Time Span', 'Period Pattern', 'End Date'].forEach(headerText => {
        const th = document.createElement('th');
        th.textContent = headerText;
        th.style.border = '1px solid #ddd';
        th.style.padding = '5px';
        th.style.fontWeight = 'bold';
        constraintsHeaderRow.appendChild(th);
    });
    constraintsThead.appendChild(constraintsHeaderRow);
    constraintsTable.appendChild(constraintsThead);

    // Add constraint rows
    const constraintsTbody = document.createElement('tbody');
    periodConstraints.forEach(constraint => {
        const constraintRow = document.createElement('tr');
        
        // Period Type
        const periodTypeCell = document.createElement('td');
        periodTypeCell.textContent = constraint.periodType || '-';
        periodTypeCell.style.border = '1px solid #ddd';
        periodTypeCell.style.padding = '5px';
        constraintRow.appendChild(periodTypeCell);
        
        // Time Span
        const timeSpanCell = document.createElement('td');
        timeSpanCell.textContent = constraint.timeSpan || '-';
        timeSpanCell.style.border = '1px solid #ddd';
        timeSpanCell.style.padding = '5px';
        constraintRow.appendChild(timeSpanCell);
        
        // Period Pattern
        const periodPatternCell = document.createElement('td');
        periodPatternCell.textContent = constraint.periodPattern || '-';
        periodPatternCell.style.border = '1px solid #ddd';
        periodPatternCell.style.padding = '5px';
        constraintRow.appendChild(periodPatternCell);
        
        // End Date
        const endDateCell = document.createElement('td');
        if (constraint.endDate) {
            const endDateParts = [];
            if (constraint.endDate.conceptName) {
                endDateParts.push(`Concept: ${constraint.endDate.conceptName}`);
            }
            if (constraint.endDate.timeShift) {
                endDateParts.push(`Shift: ${constraint.endDate.timeShift}`);
            }
            if (constraint.endDate.context) {
                endDateParts.push(`Context: ${constraint.endDate.context}`);
            }
            if (constraint.endDate.value) {
                endDateParts.push(`Value: ${constraint.endDate.value}`);
            }
            endDateCell.textContent = endDateParts.length > 0 ? endDateParts.join(', ') : '-';
        } else {
            endDateCell.textContent = '-';
        }
        endDateCell.style.border = '1px solid #ddd';
        endDateCell.style.padding = '5px';
        constraintRow.appendChild(endDateCell);
        
        constraintsTbody.appendChild(constraintRow);
    });
    constraintsTable.appendChild(constraintsTbody);
    constraintsDiv.appendChild(constraintsTable);
    constraintsCell.appendChild(constraintsDiv);
    constraintsRow.appendChild(constraintsCell);
    
    return constraintsRow;
}

/**
 * Create dimension details row
 * @param {Object} dimensionObj - The dimension object
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The details row element
 */
function createDimensionDetailsRow(dimensionObj, taxonomyData) {
    const detailsRow = document.createElement('tr');
    const detailsCell = document.createElement('td');
    detailsCell.colSpan = 3;
    detailsCell.style.padding = '10px';
    detailsCell.style.backgroundColor = '#f0f4ff'; // Light blue for dimension
    detailsCell.style.borderTop = '1px solid #ddd';

    const detailsDiv = document.createElement('div');
    const detailsTitle = document.createElement('h5');
    detailsTitle.textContent = 'Dimension Properties:';
    detailsTitle.style.margin = '0 0 10px 0';
    detailsTitle.style.color = '#1976d2'; // Blue color
    detailsTitle.style.fontWeight = 'bold';
    detailsDiv.appendChild(detailsTitle);

    const propTable = document.createElement('table');
    propTable.style.width = '100%';
    propTable.style.fontSize = '0.9em';
    propTable.style.marginLeft = '20px';
    propTable.style.borderCollapse = 'collapse';

    // Show dimension name
    const nameRow = document.createElement('tr');
    const nameCell = document.createElement('td');
    nameCell.textContent = 'Name:';
    nameCell.style.fontWeight = 'bold';
    nameCell.style.padding = '3px 10px 3px 0';
    nameCell.style.minWidth = '150px';
    const nameValueCell = document.createElement('td');
    nameValueCell.textContent = dimensionObj.name;
    nameValueCell.style.padding = '3px 0';
    nameValueCell.style.color = '#00008B'; // Dark blue
    nameRow.appendChild(nameCell);
    nameRow.appendChild(nameValueCell);
    propTable.appendChild(nameRow);

    // Show cubeTypes if present
    if (dimensionObj.cubeTypes && dimensionObj.cubeTypes.length > 0) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Cube Types:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = dimensionObj.cubeTypes.join(', ');
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        propTable.appendChild(propRow);
    }

    // Show properties array if present
    if (dimensionObj.properties && dimensionObj.properties.length > 0) {
        dimensionObj.properties.forEach(prop => {
            const propRow = document.createElement('tr');
            const propNameCell = document.createElement('td');
            propNameCell.textContent = prop.property + ':';
            propNameCell.style.fontWeight = 'bold';
            propNameCell.style.padding = '3px 10px 3px 0';
            propNameCell.style.minWidth = '150px';
            const propValueCell = document.createElement('td');
            propValueCell.textContent = typeof prop.value === 'object' ? JSON.stringify(prop.value) : prop.value;
            propValueCell.style.padding = '3px 0';
            propRow.appendChild(propNameCell);
            propRow.appendChild(propValueCell);
            propTable.appendChild(propRow);
        });
    }

    // If no additional properties found (beyond name), show a message
    if (propTable.children.length === 1) { // Only the name row
        const noPropRow = document.createElement('tr');
        const noPropCell = document.createElement('td');
        noPropCell.colSpan = 2;
        noPropCell.textContent = 'No additional properties defined.';
        noPropCell.style.fontStyle = 'italic';
        noPropCell.style.color = '#888';
        noPropCell.style.padding = '3px 0';
        noPropRow.appendChild(noPropCell);
        propTable.appendChild(noPropRow);
    }

    detailsDiv.appendChild(propTable);
    detailsCell.appendChild(detailsDiv);
    detailsRow.appendChild(detailsCell);
    
    return detailsRow;
}

/**
 * Create domain class properties row
 * @param {Object} domainClassObj - The domain class object
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The domain class properties row element
 */
function createDomainClassPropertiesRow(domainClassObj, taxonomyData) {
    const domainClassRow = document.createElement('tr');
    const domainClassCell = document.createElement('td');
    domainClassCell.colSpan = 3;
    domainClassCell.style.padding = '10px';
    domainClassCell.style.backgroundColor = '#fff3e0'; // Light orange for domain class
    domainClassCell.style.borderTop = '1px solid #ddd';

    const domainClassDiv = document.createElement('div');
    const domainClassTitle = document.createElement('h5');
    domainClassTitle.textContent = 'Domain Class Properties:';
    domainClassTitle.style.margin = '0 0 10px 0';
    domainClassTitle.style.color = '#f57c00'; // Orange color
    domainClassTitle.style.fontWeight = 'bold';
    domainClassDiv.appendChild(domainClassTitle);

    const propTable = document.createElement('table');
    propTable.style.width = '100%';
    propTable.style.fontSize = '0.9em';
    propTable.style.marginLeft = '20px';
    propTable.style.borderCollapse = 'collapse';

    // Show domain class name
    const nameRow = document.createElement('tr');
    const nameCell = document.createElement('td');
    nameCell.textContent = 'Name:';
    nameCell.style.fontWeight = 'bold';
    nameCell.style.padding = '3px 10px 3px 0';
    nameCell.style.minWidth = '150px';
    const nameValueCell = document.createElement('td');
    nameValueCell.textContent = domainClassObj.name;
    nameValueCell.style.padding = '3px 0';
    nameValueCell.style.color = '#00008B'; // Dark blue
    nameRow.appendChild(nameCell);
    nameRow.appendChild(nameValueCell);
    propTable.appendChild(nameRow);

    // Show allowedDomainItems if present
    if (domainClassObj.allowedDomainItems && domainClassObj.allowedDomainItems.length > 0) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Allowed Domain Items:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = formatQNameArrayWithLabels(domainClassObj.allowedDomainItems);
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        propTable.appendChild(propRow);
    }

    // Show properties array if present
    if (domainClassObj.properties && domainClassObj.properties.length > 0) {
        domainClassObj.properties.forEach(prop => {
            const propRow = document.createElement('tr');
            const propNameCell = document.createElement('td');
            propNameCell.textContent = prop.property + ':';
            propNameCell.style.fontWeight = 'bold';
            propNameCell.style.padding = '3px 10px 3px 0';
            propNameCell.style.minWidth = '150px';
            const propValueCell = document.createElement('td');
            propValueCell.textContent = typeof prop.value === 'object' ? JSON.stringify(prop.value) : prop.value;
            propValueCell.style.padding = '3px 0';
            propRow.appendChild(propNameCell);
            propRow.appendChild(propValueCell);
            propTable.appendChild(propRow);
        });
    }

    // If no additional properties found (beyond name), show a message
    if (propTable.children.length === 1) { // Only the name row
        const noPropRow = document.createElement('tr');
        const noPropCell = document.createElement('td');
        noPropCell.colSpan = 2;
        noPropCell.textContent = 'No additional properties defined.';
        noPropCell.style.fontStyle = 'italic';
        noPropCell.style.color = '#888';
        noPropCell.style.padding = '3px 0';
        noPropRow.appendChild(noPropCell);
        propTable.appendChild(noPropRow);
    }

    domainClassDiv.appendChild(propTable);
    domainClassCell.appendChild(domainClassDiv);
    domainClassRow.appendChild(domainClassCell);
    
    return domainClassRow;
}

/**
 * Create domain properties row
 * @param {Object} domainObj - The domain object
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The domain properties row element
 */
function createDomainPropertiesRow(domainObj, taxonomyData) {
    const domainRow = document.createElement('tr');
    const domainCell = document.createElement('td');
    domainCell.colSpan = 3;
    domainCell.style.padding = '10px';
    domainCell.style.backgroundColor = '#e8f5e9';
    domainCell.style.borderTop = '1px solid #ddd';

    const domainDiv = document.createElement('div');
    const domainTitle = document.createElement('h5');
    domainTitle.textContent = 'Domain Properties:';
    domainTitle.style.margin = '0 0 10px 0';
    domainTitle.style.color = '#666';
    domainDiv.appendChild(domainTitle);

    const domainPropTable = document.createElement('table');
    domainPropTable.style.width = '100%';
    domainPropTable.style.fontSize = '0.9em';
    domainPropTable.style.marginLeft = '20px';
    domainPropTable.style.borderCollapse = 'collapse';

    // Show domain name
    if (domainObj.name) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Domain Name:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = domainObj.name;
        propValueCell.style.padding = '3px 0';
        propValueCell.style.color = '#00008B'; // Dark blue
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show domain class
    if (domainObj.root) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Domain Class:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = domainObj.root;
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show domainDataType if present
    if (domainObj.domainDataType) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Domain Data Type:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = domainObj.domainDataType;
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show completeDomain if present
    if (domainObj.completeDomain !== undefined) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Complete Domain:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = domainObj.completeDomain ? 'Yes' : 'No';
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show extendTargetName if present
    if (domainObj.extendTargetName) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Extends:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = domainObj.extendTargetName;
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show number of relationships
    if (domainObj.relationships) {
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Relationships:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = `${domainObj.relationships.length} relationship${domainObj.relationships.length !== 1 ? 's' : ''}`;
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show members count (distinct targets in relationships)
    if (domainObj.relationships && domainObj.relationships.length > 0) {
        const members = new Set();
        domainObj.relationships.forEach(rel => {
            if (rel.target) members.add(rel.target);
            if (rel.source) members.add(rel.source);
        });
        
        const propRow = document.createElement('tr');
        const propNameCell = document.createElement('td');
        propNameCell.textContent = 'Members:';
        propNameCell.style.fontWeight = 'bold';
        propNameCell.style.padding = '3px 10px 3px 0';
        propNameCell.style.minWidth = '150px';
        const propValueCell = document.createElement('td');
        propValueCell.textContent = `${members.size} member${members.size !== 1 ? 's' : ''}`;
        propValueCell.style.padding = '3px 0';
        propRow.appendChild(propNameCell);
        propRow.appendChild(propValueCell);
        domainPropTable.appendChild(propRow);
    }

    // Show domain properties if present
    if (domainObj.properties && domainObj.properties.length > 0) {
        domainObj.properties.forEach(prop => {
            const propRow = document.createElement('tr');
            const propNameCell = document.createElement('td');
            propNameCell.textContent = prop.property + ':';
            propNameCell.style.fontWeight = 'bold';
            propNameCell.style.padding = '3px 10px 3px 0';
            propNameCell.style.minWidth = '150px';
            const propValueCell = document.createElement('td');
            propValueCell.textContent = typeof prop.value === 'object' ? JSON.stringify(prop.value) : prop.value;
            propValueCell.style.padding = '3px 0';
            propRow.appendChild(propNameCell);
            propRow.appendChild(propValueCell);
            domainPropTable.appendChild(propRow);
        });
    }

    // If no properties found, show a message
    if (domainPropTable.children.length === 0) {
        const noPropRow = document.createElement('tr');
        const noPropCell = document.createElement('td');
        noPropCell.textContent = 'No domain properties available.';
        noPropCell.style.fontStyle = 'italic';
        noPropCell.style.color = '#888';
        noPropCell.style.padding = '3px 0';
        noPropRow.appendChild(noPropCell);
        domainPropTable.appendChild(noPropRow);
    }

    domainDiv.appendChild(domainPropTable);
    domainCell.appendChild(domainDiv);
    domainRow.appendChild(domainCell);
    
    return domainRow;
}

/**
 * Create multiple domain properties row with alternating colors for each domain
 * @param {Array} domainNames - Array of domain names
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The domain properties row element with grouped domains
 */
function createMultipleDomainPropertiesRow(domainNames, taxonomyData) {
    const domainRow = document.createElement('tr');
    const domainCell = document.createElement('td');
    domainCell.colSpan = 3;
    domainCell.style.padding = '10px';
    domainCell.style.backgroundColor = '#e8f5e9';
    domainCell.style.borderTop = '1px solid #ddd';

    const domainDiv = document.createElement('div');
    const domainTitle = document.createElement('h5');
    domainTitle.textContent = `Domain Properties (${domainNames.length} domains):`;
    domainTitle.style.margin = '0 0 10px 0';
    domainTitle.style.color = '#666';
    domainDiv.appendChild(domainTitle);

    // Alternating background colors for domain groups
    const colors = ['#f1f8f4', '#e8f5e9'];
    
    domainNames.forEach((domainName, index) => {
        const domainObj = getXbrlModel(taxonomyData).domains?.find(d => d.name === domainName);
        
        if (domainObj) {
            // Create a group container for this domain
            const domainGroup = document.createElement('div');
            domainGroup.style.backgroundColor = colors[index % colors.length];
            domainGroup.style.padding = '10px';
            domainGroup.style.marginBottom = index < domainNames.length - 1 ? '8px' : '0';
            domainGroup.style.borderRadius = '4px';
            domainGroup.style.border = '1px solid #c8e6c9';
            
            // Domain header
            const domainHeader = document.createElement('div');
            domainHeader.style.fontWeight = 'bold';
            domainHeader.style.color = '#2e7d32';
            domainHeader.style.marginBottom = '8px';
            domainHeader.style.fontSize = '0.95em';
            domainHeader.textContent = `Domain ${index + 1}: ${domainObj.name}`;
            domainGroup.appendChild(domainHeader);
            
            // Create properties table for this domain
            const domainPropTable = document.createElement('table');
            domainPropTable.style.width = '100%';
            domainPropTable.style.fontSize = '0.9em';
            domainPropTable.style.marginLeft = '10px';
            domainPropTable.style.borderCollapse = 'collapse';

            // Show domain class
            if (domainObj.root) {
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Domain Class:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = domainObj.root;
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show domainDataType if present
            if (domainObj.domainDataType) {
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Domain Data Type:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = domainObj.domainDataType;
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show completeDomain if present
            if (domainObj.completeDomain !== undefined) {
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Complete Domain:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = domainObj.completeDomain ? 'Yes' : 'No';
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show extendTargetName if present
            if (domainObj.extendTargetName) {
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Extends:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = domainObj.extendTargetName;
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show number of relationships
            if (domainObj.relationships) {
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Relationships:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = `${domainObj.relationships.length} relationship${domainObj.relationships.length !== 1 ? 's' : ''}`;
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show members count (distinct targets in relationships)
            if (domainObj.relationships && domainObj.relationships.length >  0) {
                const members = new Set();
                domainObj.relationships.forEach(rel => {
                    if (rel.target) members.add(rel.target);
                    if (rel.source) members.add(rel.source);
                });
                
                const propRow = document.createElement('tr');
                const propNameCell = document.createElement('td');
                propNameCell.textContent = 'Members:';
                propNameCell.style.fontWeight = 'bold';
                propNameCell.style.padding = '3px 10px 3px 0';
                propNameCell.style.minWidth = '150px';
                const propValueCell = document.createElement('td');
                propValueCell.textContent = `${members.size} member${members.size !== 1 ? 's' : ''}`;
                propValueCell.style.padding = '3px 0';
                propRow.appendChild(propNameCell);
                propRow.appendChild(propValueCell);
                domainPropTable.appendChild(propRow);
            }

            // Show domain properties if present
            if (domainObj.properties && domainObj.properties.length > 0) {
                domainObj.properties.forEach(prop => {
                    const propRow = document.createElement('tr');
                    const propNameCell = document.createElement('td');
                    propNameCell.textContent = prop.property + ':';
                    propNameCell.style.fontWeight = 'bold';
                    propNameCell.style.padding = '3px 10px 3px 0';
                    propNameCell.style.minWidth = '150px';
                    const propValueCell = document.createElement('td');
                    propValueCell.textContent = typeof prop.value === 'object' ? JSON.stringify(prop.value) : prop.value;
                    propValueCell.style.padding = '3px 0';
                    propRow.appendChild(propNameCell);
                    propRow.appendChild(propValueCell);
                    domainPropTable.appendChild(propRow);
                });
            }

            // If no properties found for this domain
            if (domainPropTable.children.length === 0) {
                const noPropRow = document.createElement('tr');
                const noPropCell = document.createElement('td');
                noPropCell.textContent = 'No domain properties available.';
                noPropCell.style.fontStyle = 'italic';
                noPropCell.style.color = '#888';
                noPropCell.style.padding = '3px 0';
                noPropRow.appendChild(noPropCell);
                domainPropTable.appendChild(noPropRow);
            }

            domainGroup.appendChild(domainPropTable);
            domainDiv.appendChild(domainGroup);
        } else {
            // Domain not found in taxonomy
            const domainGroup = document.createElement('div');
            domainGroup.style.backgroundColor = colors[index % colors.length];
            domainGroup.style.padding = '10px';
            domainGroup.style.marginBottom = index < domainNames.length - 1 ? '8px' : '0';
            domainGroup.style.borderRadius = '4px';
            domainGroup.style.border = '1px solid #ffcdd2';
            
            const domainHeader = document.createElement('div');
            domainHeader.style.fontWeight = 'bold';
            domainHeader.style.color = '#c62828';
            domainHeader.style.marginBottom = '8px';
            domainHeader.style.fontSize = '0.95em';
            domainHeader.textContent = `Domain ${index + 1}: ${domainName}`;
            domainGroup.appendChild(domainHeader);
            
            const notFoundMsg = document.createElement('p');
            notFoundMsg.textContent = 'Domain definition not found in taxonomy.';
            notFoundMsg.style.fontStyle = 'italic';
            notFoundMsg.style.color = '#888';
            notFoundMsg.style.margin = '0 0 0 10px';
            domainGroup.appendChild(notFoundMsg);
            
            domainDiv.appendChild(domainGroup);
        }
    });

    domainCell.appendChild(domainDiv);
    domainRow.appendChild(domainCell);
    
    return domainRow;
}

/**
 * Populate cube networks panel in the references section
 * @param {Object} cube - The cube object
 * @param {Object} taxonomyData - The taxonomy data
 */
function populateCubeNetworksPanel(cube, taxonomyData) {
    const referencesContent = document.getElementById('references-content');
    referencesContent.innerHTML = '';
    
    // Show cube networks if they exist
    if (cube.cubeNetworks && cube.cubeNetworks.length > 0) {
        // Find the actual network objects from the taxonomy
        const networkObjects = cube.cubeNetworks.map(networkName => {
            return getXbrlModel(taxonomyData).networks?.find(n => n.name === networkName);
        }).filter(n => n !== undefined);
        
        if (networkObjects.length > 0) {
            networkObjects.forEach(network => {
                const networkSection = createCubeNetworkTreeSection(network, taxonomyData);
                referencesContent.appendChild(networkSection);
            });
        } else {
            const noNetworks = document.createElement('p');
            noNetworks.textContent = 'No cube networks found in taxonomy.';
            noNetworks.style.fontStyle = 'italic';
            noNetworks.style.color = '#888';
            noNetworks.style.padding = '10px 0';
            referencesContent.appendChild(noNetworks);
        }
    } else {
        const noNetworks = document.createElement('p');
        noNetworks.textContent = 'No cube networks defined.';
        noNetworks.style.fontStyle = 'italic';
        noNetworks.style.color = '#888';
        noNetworks.style.padding = '10px 0';
        referencesContent.appendChild(noNetworks);
    }
}

/**
 * Create a network tree section for cube networks panel
 * @param {Object} network - The network object
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The network section element with tree view
 */
function createCubeNetworkTreeSection(network, taxonomyData) {
    // Create expandable section for each network
    const networkSection = document.createElement('div');
    networkSection.style.marginBottom = '15px';
    
    // Create header with relationshipTypeName
    const header = document.createElement('div');
    header.style.cursor = 'pointer';
    header.style.padding = '8px';
    header.style.backgroundColor = '#f0f0f0';
    header.style.borderRadius = '4px';
    header.style.fontWeight = 'bold';
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.userSelect = 'none';
    
    // Add expand/collapse icon
    const icon = document.createElement('span');
    icon.textContent = '▶';
    icon.style.marginRight = '8px';
    icon.style.fontSize = '10px';
    icon.style.transition = 'transform 0.2s';
    header.appendChild(icon);
    
    // Add network name and relationship type
    const headerText = document.createElement('span');
    headerText.textContent = `${network.name} (${network.relationshipTypeName})`;
    header.appendChild(headerText);
    
    // Create content area (initially hidden)
    const content = document.createElement('div');
    content.style.display = 'none';
    content.style.padding = '10px';
    content.style.backgroundColor = '#fff';
    content.style.borderRadius = '0 0 4px 4px';
    content.style.border = '1px solid #ddd';
    content.style.borderTop = 'none';
    
    // Build the tree view for this network
    if (network.relationships && network.relationships.length > 0) {
        // Use the shared buildChildrenMap function
        const { childrenMap, selfReferences } = buildChildrenMap(network.relationships);
        
        // Check for root mismatch
        const rootMismatchInfo = checkRootMismatch(network);
        
        // Create tree structure
        const treeUl = document.createElement('ul');
        
        // Use roots if defined, otherwise find actual roots
        let rootNodes = network.roots && network.roots.length > 0 ? network.roots : [];
        if (rootNodes.length === 0) {
            // Find nodes that are not targets of any relationship
            const allTargets = new Set();
            network.relationships.forEach(rel => allTargets.add(rel.target));
            const allSources = new Set();
            network.relationships.forEach(rel => allSources.add(rel.source));
            
            rootNodes = Array.from(allSources).filter(source => !allTargets.has(source));
        }
        
        // Build tree for each root using the correct function from networks-builder.js
        rootNodes.forEach(root => {
            buildNetworkTree(treeUl, root, childrenMap, network.relationships, selfReferences, rootMismatchInfo, 'name');
        });
        
        content.appendChild(treeUl);
        
        // Attach node handlers for expand/collapse functionality
        attachNodeHandlers(content, false);
    } else {
        const noRels = document.createElement('div');
        noRels.style.fontStyle = 'italic';
        noRels.style.color = '#888';
        noRels.style.fontSize = '13px';
        noRels.style.padding = '10px 0';
        noRels.textContent = 'No relationships in this network.';
        content.appendChild(noRels);
    }
    
    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.style.display = isExpanded ? 'block' : 'none';
        icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0deg)';
    });
    
    networkSection.appendChild(header);
    networkSection.appendChild(content);
    
    return networkSection;
}

/**
 * Build a network section for group contents display
 * @param {Object} network - The network object
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {HTMLElement} The network section element
 */
function buildNetworkSection(network, taxonomyData) {
    const networkSection = document.createElement('div');
    networkSection.style.marginBottom = '15px';
    networkSection.style.border = '1px solid #ddd';
    networkSection.style.borderRadius = '4px';
    
    // Create header
    const header = document.createElement('div');
    header.style.cursor = 'pointer';
    header.style.padding = '10px';
    header.style.backgroundColor = '#fff3e0';
    header.style.borderRadius = '4px 4px 0 0';
    header.style.fontWeight = 'bold';
    header.style.color = '#333';
    header.style.display = 'flex';
    header.style.alignItems = 'center';
    header.style.userSelect = 'none';
    
    // Add expand/collapse icon
    const icon = document.createElement('span');
    icon.textContent = '▶';
    icon.style.marginRight = '8px';
    icon.style.fontSize = '10px';
    icon.style.transition = 'transform 0.2s';
    header.appendChild(icon);
    
    // Add network name and relationship type
    const networkName = document.createElement('span');
    networkName.textContent = `${network.name}`;
    header.appendChild(networkName);
    
    if (network.relationshipTypeName) {
        const relationshipType = document.createElement('span');
        relationshipType.textContent = ` (${network.relationshipTypeName})`;
        relationshipType.style.color = '#666';
        relationshipType.style.fontWeight = 'normal';
        relationshipType.style.fontSize = '13px';
        relationshipType.style.marginLeft = '5px';
        header.appendChild(relationshipType);
    }
    
    // Create content area (initially hidden)
    const content = document.createElement('div');
    content.style.display = 'none';
    content.style.padding = '10px';
    content.style.backgroundColor = '#fff';
    content.style.borderTop = '1px solid #ddd';
    
    // Build the network tree
    if (network.relationships && network.relationships.length > 0) {
        // Use the shared buildChildrenMap function
        const { childrenMap, selfReferences } = buildChildrenMap(network.relationships);
        
        // Check for root mismatch
        const rootMismatchInfo = checkRootMismatch(network);
        
        // Create tree structure
        const treeUl = document.createElement('ul');
        
        // Use roots if defined, otherwise find actual roots
        let rootNodes = network.roots && network.roots.length > 0 ? network.roots : [];
        if (rootNodes.length === 0) {
            // Find nodes that are not targets of any relationship
            const allTargets = new Set();
            network.relationships.forEach(rel => allTargets.add(rel.target));
            const allSources = new Set();
            network.relationships.forEach(rel => allSources.add(rel.source));
            
            rootNodes = Array.from(allSources).filter(source => !allTargets.has(source));
        }
        
        // Build tree for each root using the correct function from networks-builder.js
        rootNodes.forEach(root => {
            buildNetworkTree(treeUl, root, childrenMap, network.relationships, selfReferences, rootMismatchInfo, 'name');
        });
        
        content.appendChild(treeUl);
        
        // Attach node handlers for expand/collapse functionality
        attachNodeHandlers(content, false);
    } else {
        const noRels = document.createElement('div');
        noRels.style.fontStyle = 'italic';
        noRels.style.color = '#888';
        noRels.style.fontSize = '13px';
        noRels.style.padding = '10px 0';
        noRels.textContent = 'No relationships in this network.';
        content.appendChild(noRels);
    }
    
    // Toggle functionality
    let isExpanded = false;
    header.addEventListener('click', () => {
        isExpanded = !isExpanded;
        content.style.display = isExpanded ? 'block' : 'none';
        icon.style.transform = isExpanded ? 'rotate(90deg)' : 'rotate(0deg)';
    });
    
    networkSection.appendChild(header);
    networkSection.appendChild(content);
    
    return networkSection;
}
/**
 * Render a layout in the Layout tab
 */
function renderLayoutInTab(layout, taxonomyData) {
    console.log('[Details Panel] Rendering layout in Layout tab:', layout.name);
    
    const layoutContent = document.getElementById('layout-content');
    if (!layoutContent) {
        console.warn('[Details Panel] layout-content container not found');
        return;
    }
    
    layoutContent.innerHTML = '';
    
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.fontFamily = 'Arial, sans-serif';
    
    const title = document.createElement('h2');
    title.textContent = layout.name;
    title.style.marginTop = '0';
    title.style.marginBottom = '20px';
    title.style.color = '#333';
    wrapper.appendChild(title);
    
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        wrapper.innerHTML = '<p style="color: #d9534f;">No taxonomy data available.</p>';
        layoutContent.appendChild(wrapper);
        return;
    }
    
    if (!layout.dataTables || layout.dataTables.length === 0) {
        wrapper.innerHTML += '<p style="padding: 10px;">No data tables defined in this layout.</p>';
        layoutContent.appendChild(wrapper);
        return;
    }
    
    const tableConstruction = layout.tableConstruction || 'topDown';
    const displayMode = 'name';
    const renderedTables = [];
    const errors = [];
    
    layout.dataTables.forEach((dataTable, index) => {
        try {
            const tableInfo = renderDataTableForLayout(dataTable, displayMode, taxonomyData, xbrlModel);
            renderedTables.push(tableInfo);
        } catch (error) {
            errors.push(`Error rendering table ${dataTable.name}: ${error.message}`);
            console.error('[Details Panel] Error rendering table:', error);
        }
    });
    
    if (errors.length > 0) {
        const errorDiv = document.createElement('div');
        errorDiv.style.padding = '15px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.color = '#721c24';
        errorDiv.style.border = '1px solid #f5c6cb';
        errorDiv.style.borderRadius = '4px';
        errorDiv.style.marginBottom = '20px';
        
        const errorTitle = document.createElement('h4');
        errorTitle.textContent = 'Rendering Errors:';
        errorTitle.style.marginTop = '0';
        errorDiv.appendChild(errorTitle);
        
        errors.forEach(err => {
            const errorP = document.createElement('p');
            errorP.textContent = err;
            errorP.style.margin = '5px 0';
            errorDiv.appendChild(errorP);
        });
        
        wrapper.appendChild(errorDiv);
    }
    
    if (renderedTables.length === 1) {
        wrapper.appendChild(renderedTables[0].element);
    } else if (renderedTables.length > 1) {
        if (tableConstruction === 'topDown') {
            renderedTables.forEach((tableInfo, index) => {
                if (index > 0) {
                    const spacer = document.createElement('div');
                    spacer.style.height = '20px';
                    wrapper.appendChild(spacer);
                }
                wrapper.appendChild(tableInfo.element);
            });
        } else if (tableConstruction === 'leftRight') {
            const horizontalContainer = document.createElement('div');
            horizontalContainer.style.display = 'flex';
            horizontalContainer.style.gap = '20px';
            horizontalContainer.style.alignItems = 'flex-start';
            
            renderedTables.forEach(tableInfo => {
                horizontalContainer.appendChild(tableInfo.element);
            });
            
            wrapper.appendChild(horizontalContainer);
        }
    }
    
    layoutContent.appendChild(wrapper);
}
