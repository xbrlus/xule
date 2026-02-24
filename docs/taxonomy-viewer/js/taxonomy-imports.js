/**
 * Taxonomy Imports Module
 * Handles visualization of taxonomy import relationships
 */

import { getTaxonomyData } from './main.js';
import { getXbrlModelName } from './taxonomy-loader.js';
import { getXbrlModel } from './utils.js';

/**
 * Build the import paths view for a taxonomy
 * Shows a graph of the current taxonomy and its imported taxonomies
 * @param {Object} taxonomy - The taxonomy object
 */
export function buildImportPathsView(taxonomy) {
    // Get the main taxonomy data which has the merged imports with nestedImports attached
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    
    const container = document.getElementById('import-paths-content');
    if (!container) {
        console.error('[buildImportPathsView] Import paths container not found');
        return;
    }
    
    // Clear previous content
    container.innerHTML = '';
    
    // Get taxonomy name from the main xbrlModel
    const taxonomyName = xbrlModel?.xbrlModelName || taxonomy.xbrlModelName || taxonomy.name || 'Unnamed Taxonomy';
    
    // Create main structure
    const importGraph = document.createElement('div');
    importGraph.className = 'import-graph';
    importGraph.style.cssText = 'padding: 20px; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Import Hierarchy';
    title.style.cssText = 'margin: 0 0 20px 0; color: #333;';
    importGraph.appendChild(title);
    
    // Create root taxonomy node
    const rootHasFinalTaxonomy = !!(xbrlModel?.finalTaxonomy || taxonomy.finalTaxonomy);
    const rootNode = createTaxonomyNode(taxonomyName, true, false, false, rootHasFinalTaxonomy);
    importGraph.appendChild(rootNode);
    
    // Get imports from the main xbrlModel which has the nestedImports attached
    const imports = xbrlModel?.importedTaxonomies || taxonomy.importedTaxonomies || [];
    
    if (imports.length === 0) {
        const noImportsMsg = document.createElement('div');
        noImportsMsg.textContent = 'This taxonomy does not import any other taxonomies.';
        noImportsMsg.style.cssText = 'margin-top: 15px; color: #666; font-style: italic;';
        importGraph.appendChild(noImportsMsg);
    } else {
        // Create imports container
        const importsContainer = document.createElement('div');
        importsContainer.style.cssText = 'margin-left: 40px; margin-top: 10px;';
        
        // Track visited taxonomies to avoid infinite loops
        const visited = new Set([taxonomyName]);
        
        imports.forEach((imp, index) => {
            // Add connector line
            const connector = document.createElement('div');
            connector.style.cssText = 'border-left: 2px solid #ccc; height: 20px; margin-left: 10px;';
            importsContainer.appendChild(connector);
            
            // Create import node with nested imports
            const importNode = createImportNodeRecursive(imp, index, visited, 0, [taxonomyName]);
            importsContainer.appendChild(importNode);
        });
        
        importGraph.appendChild(importsContainer);
    }
    
    container.appendChild(importGraph);
}

/**
 * Create a taxonomy node element
 * @param {string} name - Taxonomy name
 * @param {boolean} isRoot - Whether this is the root taxonomy
 * @param {boolean} isCircular - Whether this is a circular import
 * @param {boolean} isConcurrent - Whether this is a concurrent import (imported by multiple branches)
 * @param {boolean} hasFinalTaxonomy - Whether this taxonomy has finalTaxonomy declarations
 * @returns {HTMLElement}
 */
function createTaxonomyNode(name, isRoot = false, isCircular = false, isConcurrent = false, hasFinalTaxonomy = false) {
    const node = document.createElement('div');
    node.className = 'taxonomy-node';
    
    let bgColor = '#E3F2FD';
    let borderColor = '#2196F3';
    
    if (isRoot) {
        bgColor = '#E8F5E9';
        borderColor = '#4CAF50';
    } else if (isCircular) {
        bgColor = '#FFEBEE';
        borderColor = '#FF5722';
    } else if (isConcurrent) {
        bgColor = '#F3E5F5';
        borderColor = '#9C27B0';
    }
    
    node.style.cssText = `
        padding: 12px 16px;
        border: 2px solid ${borderColor};
        border-radius: 8px;
        background-color: ${bgColor};
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-weight: ${isRoot ? 'bold' : 'normal'};
        font-size: ${isRoot ? '16px' : '14px'};
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ${(isCircular || isConcurrent) ? 'opacity: 0.8;' : ''}
    `;
    
    const icon = document.createElement('span');
    if (isRoot) {
        icon.textContent = '📚 ';
    } else if (isCircular) {
        icon.textContent = '🔄 ';
    } else if (isConcurrent) {
        icon.textContent = '↗️ ';
    } else {
        icon.textContent = '📖 ';
    }
    node.appendChild(icon);
    
    const nameSpan = document.createElement('span');
    nameSpan.textContent = name;
    node.appendChild(nameSpan);
    
    // Add final taxonomy indicator if present
    if (hasFinalTaxonomy) {
        const finalBadge = document.createElement('span');
        finalBadge.textContent = '🔒';
        finalBadge.title = 'Final Taxonomy: This taxonomy restricts certain object types from being extended';
        finalBadge.style.cssText = `
            font-size: 18px;
            cursor: help;
            filter: drop-shadow(0 0 2px rgba(255, 193, 7, 0.8));
        `;
        node.appendChild(finalBadge);
    }
    
    return node;
}

/**
 * Create an import node element recursively with nested imports
 * @param {Object} importObj - Import object
 * @param {number} index - Import index
 * @param {Set} visited - Set of already visited taxonomy names to prevent circular imports
 * @param {number} depth - Current depth in the import tree
 * @param {Array} importPath - Array of taxonomy names in the current import path for circular detection
 * @returns {HTMLElement}
 */
function createImportNodeRecursive(importObj, index, visited, depth, importPath = []) {
    const container = document.createElement('div');
    container.className = 'import-node-container';
    container.style.cssText = 'margin-bottom: 15px;';
    
    // Create the import node
    const node = document.createElement('div');
    node.style.cssText = 'display: flex; align-items: flex-start; gap: 10px;';
    
    // Add connector
    const connector = document.createElement('div');
    connector.style.cssText = `
        width: 30px;
        border-top: 2px solid #ccc;
        margin-top: 20px;
        flex-shrink: 0;
    `;
    node.appendChild(connector);
    
    // Create content area
    const content = document.createElement('div');
    content.style.cssText = 'flex: 1;';
    
    // Get import taxonomy name
    const qname = getXbrlModelName(importObj) || 'Unknown';
    
    // Check if this is a circular import (appears in the current import path)
    const isCircular = importPath.includes(qname);
    
    // Check if this is a concurrent import (already visited but not circular)
    const isConcurrent = !isCircular && visited.has(qname);
    
    // Debug logging for xbrla:AccountingModel
    if (qname === 'xbrla:AccountingModel') {
        console.log(`[Import Paths] xbrla:AccountingModel - isCircular: ${isCircular}, isConcurrent: ${isConcurrent}, visited size: ${visited.size}, visited contains:`, Array.from(visited));
    }
    
    // Check if this import has finalTaxonomy declaration
    const hasFinalTaxonomy = !!importObj.finalTaxonomy;
    
    // Create taxonomy node
    const taxonomyNode = createTaxonomyNode(qname, false, isCircular, isConcurrent, hasFinalTaxonomy);
    if (!isCircular && !isConcurrent) {
        taxonomyNode.style.cursor = 'pointer';
        taxonomyNode.title = 'Click to navigate to ' + qname;
        
        // Add click handler
        taxonomyNode.addEventListener('click', () => {
            if (window.selectQNameFromSearch) {
                window.selectQNameFromSearch(qname);
            }
        });
    }
    
    content.appendChild(taxonomyNode);
    
    // Add import details (selections, importObjectTypes, etc.)
    const details = createImportDetails(importObj);
    if (details) {
        content.appendChild(details);
    }
    
    // Mark this taxonomy as visited BEFORE processing nested imports
    // This ensures concurrent imports are detected even if depth limit is reached
    if (!isCircular) {
        visited.add(qname);
    }
    
    // If not circular and not already shown as concurrent, try to find and display nested imports
    if (!isCircular && !isConcurrent && depth < 5) { // Limit depth to 5 levels to prevent excessive nesting
        
        // Look for nested imports by checking if the importObj has nestedImports attached
        const nestedImports = findNestedImports(qname, importObj);
            
        if (nestedImports && nestedImports.length > 0) {
            const nestedContainer = document.createElement('div');
            nestedContainer.style.cssText = 'margin-left: 40px; margin-top: 10px;';
            
            nestedImports.forEach((nestedImp, nestedIndex) => {
                // Add connector line
                const nestedConnector = document.createElement('div');
                nestedConnector.style.cssText = 'border-left: 2px solid #ccc; height: 20px; margin-left: 10px;';
                nestedContainer.appendChild(nestedConnector);
                
                // Recursively create import node with updated path
                // Pass the same visited Set so concurrent imports across branches are detected
                const nestedNode = createImportNodeRecursive(
                    nestedImp, 
                    nestedIndex, 
                    visited, 
                    depth + 1,
                    [...importPath, qname]  // Add current taxonomy to the path
                );
                nestedContainer.appendChild(nestedNode);
            });
            
            content.appendChild(nestedContainer);
        }
    } else if (isCircular) {
        // Add circular import indicator
        const circularMsg = document.createElement('div');
        circularMsg.textContent = '⚠️ Circular import - already in import chain';
        circularMsg.style.cssText = 'margin-top: 5px; color: #FF5722; font-style: italic; font-size: 12px;';
        content.appendChild(circularMsg);
    } else if (isConcurrent) {
        // Add concurrent import indicator
        const concurrentMsg = document.createElement('div');
        concurrentMsg.textContent = '↗️ Concurrent import - already imported by another branch';
        concurrentMsg.style.cssText = 'margin-top: 5px; color: #9C27B0; font-style: italic; font-size: 12px;';
        content.appendChild(concurrentMsg);
    }
    
    node.appendChild(content);
    container.appendChild(node);
    
    return container;
}

/**
 * Find nested imports for a given taxonomy name
 * @param {string} taxonomyName - Name of the taxonomy to find imports for
 * @param {Object} importObj - The import object which may contain nested import info
 * @returns {Array} Array of nested import objects
 */
function findNestedImports(taxonomyName, importObj) {
    // Check if the import object itself has nested imports stored
    // This is populated by the taxonomy loader when it recursively loads taxonomies
    if (importObj.nestedImports && Array.isArray(importObj.nestedImports)) {
        return importObj.nestedImports;
    }
    
    return [];
}

/**
 * Create import details element showing selections, filters, etc.
 * @param {Object} importObj - Import object
 * @returns {HTMLElement|null}
 */
function createImportDetails(importObj) {
    const hasSelections = importObj.selections && Object.keys(importObj.selections).length > 0;
    const hasImportObjects = importObj.importObjects && importObj.importObjects.length > 0;
    const hasImportObjectTypes = importObj.importObjectTypes && importObj.importObjectTypes.length > 0;
    
    if (!hasSelections && !hasImportObjects && !hasImportObjectTypes) {
        return null;
    }
    
    const detailsContainer = document.createElement('div');
    detailsContainer.style.cssText = `
        margin-top: 10px;
        padding: 10px;
        background-color: #f5f5f5;
        border-radius: 4px;
        font-size: 13px;
    `;
    
    // Add partial import indicator
    const partialLabel = document.createElement('div');
    partialLabel.innerHTML = '<strong>⚠️ Partial Import</strong>';
    partialLabel.style.cssText = 'color: #FF9800; margin-bottom: 8px;';
    detailsContainer.appendChild(partialLabel);
    
    // Add import object types
    if (hasImportObjectTypes) {
        const typesDiv = document.createElement('div');
        typesDiv.style.marginBottom = '5px';
        
        const typesLabel = document.createElement('div');
        typesLabel.innerHTML = '<strong>Imported Object Types:</strong>';
        typesLabel.style.marginBottom = '3px';
        typesDiv.appendChild(typesLabel);
        
        const typesList = document.createElement('div');
        typesList.style.cssText = 'margin-left: 15px; display: flex; flex-wrap: wrap; gap: 5px;';
        
        importObj.importObjectTypes.forEach(type => {
            const typeBadge = document.createElement('span');
            typeBadge.textContent = type;
            typeBadge.style.cssText = `
                padding: 2px 8px;
                background-color: #2196F3;
                color: white;
                border-radius: 12px;
                font-size: 12px;
            `;
            typesList.appendChild(typeBadge);
        });
        
        typesDiv.appendChild(typesList);
        detailsContainer.appendChild(typesDiv);
    }
    
    // Add import objects
    if (hasImportObjects) {
        const objectsDiv = document.createElement('div');
        objectsDiv.style.marginBottom = '5px';
        
        const objectsLabel = document.createElement('div');
        objectsLabel.innerHTML = '<strong>Specific Objects:</strong>';
        objectsLabel.style.marginBottom = '3px';
        objectsDiv.appendChild(objectsLabel);
        
        const objectsList = document.createElement('div');
        objectsList.style.cssText = 'margin-left: 15px;';
        
        importObj.importObjects.slice(0, 10).forEach(obj => {
            const objItem = document.createElement('div');
            objItem.textContent = '• ' + obj;
            objItem.style.cssText = 'color: #555; cursor: pointer; padding: 2px 0;';
            objItem.title = 'Click to navigate to ' + obj;
            
            objItem.addEventListener('click', (e) => {
                e.stopPropagation();
                if (window.selectQNameFromSearch) {
                    window.selectQNameFromSearch(obj);
                }
            });
            
            objectsList.appendChild(objItem);
        });
        
        if (importObj.importObjects.length > 10) {
            const moreItem = document.createElement('div');
            moreItem.textContent = `... and ${importObj.importObjects.length - 10} more`;
            moreItem.style.cssText = 'color: #999; font-style: italic;';
            objectsList.appendChild(moreItem);
        }
        
        objectsDiv.appendChild(objectsList);
        detailsContainer.appendChild(objectsDiv);
    }
    
    // Add selections
    if (hasSelections) {
        const selectionsDiv = document.createElement('div');
        
        const selectionsLabel = document.createElement('div');
        selectionsLabel.innerHTML = '<strong>Selections:</strong>';
        selectionsLabel.style.marginBottom = '3px';
        selectionsDiv.appendChild(selectionsLabel);
        
        const selectionsList = document.createElement('div');
        selectionsList.style.cssText = 'margin-left: 15px;';
        
        Object.entries(importObj.selections).forEach(([key, value]) => {
            const selItem = document.createElement('div');
            selItem.innerHTML = `<code>${key}</code>: ${JSON.stringify(value)}`;
            selItem.style.cssText = 'color: #555; padding: 2px 0; font-size: 12px;';
            selectionsList.appendChild(selItem);
        });
        
        selectionsDiv.appendChild(selectionsList);
        detailsContainer.appendChild(selectionsDiv);
    }
    
    return detailsContainer;
}

/**
 * Collect all finalTaxonomy declarations from imported taxonomies recursively
 * @param {Object} taxonomy - The taxonomy object
 * @param {Set} visited - Set of visited taxonomy names to avoid circular references
 * @returns {Array} Array of {taxonomyName, finalTaxonomy} objects
 */
function collectFinalTaxonomyDeclarations(taxonomy, visited = new Set()) {
    const collected = [];
    
    if (!taxonomy) return collected;
    
    const taxonomyName = taxonomy.name;
    
    // Avoid circular references
    if (visited.has(taxonomyName)) {
        return collected;
    }
    visited.add(taxonomyName);
    
    console.log('[collectFinalTaxonomyDeclarations] Checking taxonomy:', taxonomyName);
    
    // Check if this taxonomy has a finalTaxonomy declaration
    if (taxonomy.finalTaxonomy) {
        console.log('[collectFinalTaxonomyDeclarations] Found finalTaxonomy in:', taxonomyName);
        collected.push({
            taxonomyName: taxonomyName,
            finalTaxonomy: taxonomy.finalTaxonomy
        });
    }
    
    // Recursively check imported taxonomies
    if (taxonomy.importedTaxonomies && Array.isArray(taxonomy.importedTaxonomies)) {
        console.log('[collectFinalTaxonomyDeclarations] Checking', taxonomy.importedTaxonomies.length, 'imports of', taxonomyName);
        
        taxonomy.importedTaxonomies.forEach((imp, idx) => {
            console.log(`[collectFinalTaxonomyDeclarations]   - Import ${idx}:`, getXbrlModelName(imp), {
                hasFinalTaxonomy: !!imp.finalTaxonomy,
                hasNestedImports: !!imp.nestedImports
            });
            
            // Check if the import itself has a finalTaxonomy stored
            if (imp.finalTaxonomy) {
                const impTaxonomyName = getXbrlModelName(imp) || 'Unknown';
                if (!visited.has(impTaxonomyName)) {
                    console.log('[collectFinalTaxonomyDeclarations]     - Found finalTaxonomy in import:', impTaxonomyName);
                    visited.add(impTaxonomyName);
                    collected.push({
                        taxonomyName: impTaxonomyName,
                        finalTaxonomy: imp.finalTaxonomy
                    });
                }
            }
            
            // Recursively check nested imports
            if (imp.nestedImports && Array.isArray(imp.nestedImports)) {
                console.log('[collectFinalTaxonomyDeclarations]     - Checking', imp.nestedImports.length, 'nested imports');
                imp.nestedImports.forEach(nestedImp => {
                    if (nestedImp.finalTaxonomy) {
                        const nestedTaxonomyName = nestedImp.taxonomyName || 'Unknown';
                        if (!visited.has(nestedTaxonomyName)) {
                            console.log('[collectFinalTaxonomyDeclarations]       - Found finalTaxonomy in nested import:', nestedTaxonomyName);
                            visited.add(nestedTaxonomyName);
                            collected.push({
                                taxonomyName: nestedTaxonomyName,
                                finalTaxonomy: nestedImp.finalTaxonomy
                            });
                        }
                    }
                    
                    // Recursively check deeper nested imports
                    if (nestedImp.nestedImports) {
                        const deeperCollected = collectFinalTaxonomyDeclarationsFromImportSpec(nestedImp, visited);
                        collected.push(...deeperCollected);
                    }
                });
            }
        });
    }
    
    return collected;
}

/**
 * Helper function to collect finalTaxonomy declarations from an import spec recursively
 * @param {Object} importSpec - Import specification object
 * @param {Set} visited - Set of visited taxonomy names
 * @returns {Array} Array of collected declarations
 */
function collectFinalTaxonomyDeclarationsFromImportSpec(importSpec, visited) {
    const collected = [];
    
    if (!importSpec || !importSpec.nestedImports) {
        return collected;
    }
    
    importSpec.nestedImports.forEach(nestedImp => {
        const nestedTaxonomyName = nestedImp.taxonomyName || 'Unknown';
        
        if (nestedImp.finalTaxonomy && !visited.has(nestedTaxonomyName)) {
            visited.add(nestedTaxonomyName);
            collected.push({
                taxonomyName: nestedTaxonomyName,
                finalTaxonomy: nestedImp.finalTaxonomy
            });
        }
        
        // Recursively check deeper levels
        if (nestedImp.nestedImports) {
            const deeperCollected = collectFinalTaxonomyDeclarationsFromImportSpec(nestedImp, visited);
            collected.push(...deeperCollected);
        }
    });
    
    return collected;
}

/**
 * Build the Final Taxonomy view for a taxonomy
 * Shows all finalTaxonomy declarations from this taxonomy and all imported taxonomies
 * @param {Object} taxonomy - The taxonomy object
 */
export function buildFinalTaxonomyView(taxonomy) {
    console.log('[buildFinalTaxonomyView] Building final taxonomy view for:', taxonomy);
    
    const container = document.getElementById('final-taxonomy-content');
    if (!container) {
        console.error('[buildFinalTaxonomyView] Final taxonomy container not found');
        return;
    }
    
    // Clear previous content
    container.innerHTML = '';
    
    // Collect all finalTaxonomy declarations from this taxonomy and imports
    const allFinalDeclarations = collectFinalTaxonomyDeclarations(taxonomy);
    
    console.log('[buildFinalTaxonomyView] Collected', allFinalDeclarations.length, 'final taxonomy declarations');
    
    // Create main structure
    const finalTaxonomyView = document.createElement('div');
    finalTaxonomyView.className = 'final-taxonomy-view';
    finalTaxonomyView.style.cssText = 'padding: 20px; font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;';
    
    // Add title
    const title = document.createElement('h3');
    title.textContent = 'Final Taxonomy Declarations';
    title.style.cssText = 'margin: 0 0 20px 0; color: #333;';
    finalTaxonomyView.appendChild(title);
    
    if (allFinalDeclarations.length === 0) {
        const noFinalTaxonomy = document.createElement('div');
        noFinalTaxonomy.style.cssText = 'padding: 20px; background-color: #f5f5f5; border: 1px solid #ddd; border-radius: 8px; color: #666; font-style: italic;';
        noFinalTaxonomy.textContent = 'This taxonomy and its imported taxonomies do not have any finalTaxonomy declarations.';
        finalTaxonomyView.appendChild(noFinalTaxonomy);
        container.appendChild(finalTaxonomyView);
        return;
    }
    
    // Add description
    const description = document.createElement('p');
    description.innerHTML = `This taxonomy inherits <strong>${allFinalDeclarations.length}</strong> final taxonomy declaration${allFinalDeclarations.length > 1 ? 's' : ''} from its import chain. Final taxonomies restrict which object types and specific objects can be extended or added to by importing taxonomies.`;
    description.style.cssText = 'margin: 0 0 20px 0; color: #666; line-height: 1.6;';
    finalTaxonomyView.appendChild(description);
    
    // Create a summary of all restrictions across all taxonomies
    const allFinalObjectTypes = new Set();
    const allFinalObjects = new Set();
    const hasFinalTaxonomyFlag = allFinalDeclarations.some(decl => decl.finalTaxonomy.finalTaxonomyFlag === true);
    
    allFinalDeclarations.forEach(decl => {
        if (decl.finalTaxonomy.finalObjectTypes && Array.isArray(decl.finalTaxonomy.finalObjectTypes)) {
            decl.finalTaxonomy.finalObjectTypes.forEach(type => allFinalObjectTypes.add(type));
        }
        if (decl.finalTaxonomy.finalObjects && Array.isArray(decl.finalTaxonomy.finalObjects)) {
            decl.finalTaxonomy.finalObjects.forEach(obj => allFinalObjects.add(obj));
        }
    });
    
    if (hasFinalTaxonomyFlag || allFinalObjectTypes.size > 0 || allFinalObjects.size > 0) {
        const summarySection = document.createElement('div');
        summarySection.style.cssText = 'background-color: #ffebee; border: 2px solid #f44336; border-radius: 8px; padding: 15px; margin-bottom: 25px;';
        
        const summaryTitle = document.createElement('h4');
        summaryTitle.innerHTML = '⚠️ Restrictions on This Taxonomy';
        summaryTitle.style.cssText = 'margin: 0 0 10px 0; color: #c62828; font-size: 16px;';
        summarySection.appendChild(summaryTitle);
        
        // Show final taxonomy flag if present
        if (hasFinalTaxonomyFlag) {
            const flagWarning = document.createElement('div');
            flagWarning.innerHTML = '<strong>🔒 COMPLETELY FINAL:</strong> This taxonomy is marked as completely final. Only fact, footnote, and entity objects can be added.';
            flagWarning.style.cssText = 'background-color: #d32f2f; color: white; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; font-weight: bold;';
            summarySection.appendChild(flagWarning);
        }
        
        // Show final object types
        if (allFinalObjectTypes.size > 0) {
            const objectTypesDiv = document.createElement('div');
            objectTypesDiv.style.marginBottom = '15px';
            
            const objectTypesLabel = document.createElement('p');
            objectTypesLabel.textContent = 'The following object types CANNOT be added to this taxonomy:';
            objectTypesLabel.style.cssText = 'margin: 0 0 10px 0; color: #666; font-size: 14px; line-height: 1.6;';
            objectTypesDiv.appendChild(objectTypesLabel);
            
            const objectTypesBadgesContainer = document.createElement('div');
            objectTypesBadgesContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 10px;';
            
            Array.from(allFinalObjectTypes).sort().forEach(objectType => {
                const badge = document.createElement('div');
                badge.textContent = objectType;
                badge.style.cssText = `
                    padding: 8px 16px;
                    background-color: #f44336;
                    color: white;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                `;
                objectTypesBadgesContainer.appendChild(badge);
            });
            
            objectTypesDiv.appendChild(objectTypesBadgesContainer);
            summarySection.appendChild(objectTypesDiv);
        }
        
        // Show final objects
        if (allFinalObjects.size > 0) {
            const objectsDiv = document.createElement('div');
            
            const objectsLabel = document.createElement('p');
            objectsLabel.textContent = 'The following specific objects CANNOT be extended:';
            objectsLabel.style.cssText = 'margin: 0 0 10px 0; color: #666; font-size: 14px; line-height: 1.6;';
            objectsDiv.appendChild(objectsLabel);
            
            const objectsBadgesContainer = document.createElement('div');
            objectsBadgesContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 10px;';
            
            Array.from(allFinalObjects).sort().forEach(obj => {
                const badge = document.createElement('div');
                badge.textContent = obj;
                badge.style.cssText = `
                    padding: 8px 16px;
                    background-color: #ff9800;
                    color: white;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                `;
                objectsBadgesContainer.appendChild(badge);
            });
            
            objectsDiv.appendChild(objectsBadgesContainer);
            summarySection.appendChild(objectsDiv);
        }
        
        finalTaxonomyView.appendChild(summarySection);
    }
    
    // Display each finalTaxonomy declaration grouped by source taxonomy
    const declarationsTitle = document.createElement('h4');
    declarationsTitle.textContent = 'Final Taxonomy Declarations by Source';
    declarationsTitle.style.cssText = 'margin: 0 0 15px 0; color: #333; font-size: 16px;';
    finalTaxonomyView.appendChild(declarationsTitle);
    
    allFinalDeclarations.forEach((decl, index) => {
        const declSection = document.createElement('div');
        declSection.style.cssText = 'background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px;';
        
        // Taxonomy source header
        const sourceHeader = document.createElement('div');
        sourceHeader.style.cssText = 'display: flex; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #2196F3;';
        
        const sourceIcon = document.createElement('span');
        sourceIcon.textContent = '📚 ';
        sourceIcon.style.cssText = 'font-size: 20px; margin-right: 10px;';
        sourceHeader.appendChild(sourceIcon);
        
        const sourceName = document.createElement('span');
        sourceName.textContent = decl.taxonomyName;
        sourceName.style.cssText = 'font-weight: bold; font-size: 15px; color: #1976D2; cursor: pointer;';
        sourceName.title = 'Click to navigate to ' + decl.taxonomyName;
        sourceName.addEventListener('click', () => {
            if (window.selectQNameFromSearch) {
                window.selectQNameFromSearch(decl.taxonomyName);
            }
        });
        sourceHeader.appendChild(sourceName);
        
        declSection.appendChild(sourceHeader);
        
        // Final Taxonomy Name
        if (decl.finalTaxonomy.name) {
            const nameDiv = document.createElement('div');
            nameDiv.style.cssText = 'margin-bottom: 15px;';
            
            const nameLabel = document.createElement('div');
            nameLabel.innerHTML = '<strong>Final Taxonomy Name:</strong>';
            nameLabel.style.cssText = 'margin-bottom: 5px; color: #666; font-size: 13px;';
            nameDiv.appendChild(nameLabel);
            
            const nameValue = document.createElement('div');
            nameValue.textContent = decl.finalTaxonomy.name;
            nameValue.style.cssText = 'font-family: monospace; background-color: white; padding: 5px 10px; border-radius: 4px; border: 1px solid #ddd;';
            nameDiv.appendChild(nameValue);
            
            declSection.appendChild(nameDiv);
        }
        
        // Final Taxonomy Flag
        if (decl.finalTaxonomy.finalTaxonomyFlag === true) {
            const flagDiv = document.createElement('div');
            flagDiv.style.cssText = 'margin-bottom: 15px;';
            
            const flagBadge = document.createElement('div');
            flagBadge.innerHTML = '<strong>🔒 COMPLETELY FINAL</strong> - Only fact, footnote, and entity objects can be added';
            flagBadge.style.cssText = 'background-color: #d32f2f; color: white; padding: 10px; border-radius: 4px; font-size: 13px; font-weight: bold;';
            flagDiv.appendChild(flagBadge);
            
            declSection.appendChild(flagDiv);
        }
        
        // Final Object Types
        if (decl.finalTaxonomy.finalObjectTypes && Array.isArray(decl.finalTaxonomy.finalObjectTypes) && decl.finalTaxonomy.finalObjectTypes.length > 0) {
            const objectTypesDiv = document.createElement('div');
            objectTypesDiv.style.cssText = 'margin-bottom: 15px;';
            
            const objectTypesLabel = document.createElement('div');
            objectTypesLabel.innerHTML = '<strong>Final Object Types:</strong>';
            objectTypesLabel.style.cssText = 'margin-bottom: 8px; color: #666; font-size: 13px;';
            objectTypesDiv.appendChild(objectTypesLabel);
            
            const objectTypesBadgesContainer = document.createElement('div');
            objectTypesBadgesContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px;';
            
            decl.finalTaxonomy.finalObjectTypes.forEach(objectType => {
                const badge = document.createElement('div');
                badge.textContent = objectType;
                badge.style.cssText = `
                    padding: 6px 14px;
                    background-color: #f44336;
                    color: white;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: 500;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                `;
                objectTypesBadgesContainer.appendChild(badge);
            });
            
            objectTypesDiv.appendChild(objectTypesBadgesContainer);
            declSection.appendChild(objectTypesDiv);
        }
        
        // Final Objects (specific objects that cannot be extended)
        if (decl.finalTaxonomy.finalObjects && Array.isArray(decl.finalTaxonomy.finalObjects) && decl.finalTaxonomy.finalObjects.length > 0) {
            const objectsDiv = document.createElement('div');
            objectsDiv.style.cssText = 'margin-bottom: 15px;';
            
            const objectsLabel = document.createElement('div');
            objectsLabel.innerHTML = '<strong>Final Objects (Cannot be Extended):</strong>';
            objectsLabel.style.cssText = 'margin-bottom: 8px; color: #666; font-size: 13px;';
            objectsDiv.appendChild(objectsLabel);
            
            const objectsBadgesContainer = document.createElement('div');
            objectsBadgesContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px;';
            
            decl.finalTaxonomy.finalObjects.forEach(obj => {
                const badge = document.createElement('div');
                badge.textContent = obj;
                badge.title = 'Click to navigate to ' + obj;
                badge.style.cssText = `
                    padding: 6px 14px;
                    background-color: #ff9800;
                    color: white;
                    border-radius: 16px;
                    font-size: 13px;
                    font-weight: 500;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    cursor: pointer;
                `;
                badge.addEventListener('click', () => {
                    if (window.selectQNameFromSearch) {
                        window.selectQNameFromSearch(obj);
                    }
                });
                objectsBadgesContainer.appendChild(badge);
            });
            
            objectsDiv.appendChild(objectsBadgesContainer);
            declSection.appendChild(objectsDiv);
        }
        
        // Selections (constraint-based final declarations)
        if (decl.finalTaxonomy.selections && Array.isArray(decl.finalTaxonomy.selections) && decl.finalTaxonomy.selections.length > 0) {
            const selectionsDiv = document.createElement('div');
            selectionsDiv.style.cssText = 'margin-bottom: 15px;';
            
            const selectionsLabel = document.createElement('div');
            selectionsLabel.innerHTML = '<strong>Selections (Constraint-based Final Declarations):</strong>';
            selectionsLabel.style.cssText = 'margin-bottom: 8px; color: #666; font-size: 13px;';
            selectionsDiv.appendChild(selectionsLabel);
            
            const selectionsList = document.createElement('div');
            selectionsList.style.cssText = 'background-color: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px;';
            
            decl.finalTaxonomy.selections.forEach((selection, idx) => {
                const selectionItem = document.createElement('div');
                selectionItem.style.cssText = 'margin-bottom: 8px; padding: 8px; background-color: #f5f5f5; border-left: 3px solid #9c27b0; border-radius: 2px;';
                
                const selectionText = document.createElement('code');
                selectionText.textContent = selection;
                selectionText.style.cssText = 'font-size: 12px; color: #333;';
                
                selectionItem.appendChild(selectionText);
                selectionsList.appendChild(selectionItem);
            });
            
            selectionsDiv.appendChild(selectionsList);
            declSection.appendChild(selectionsDiv);
        }
        
        // Show message if no restrictions defined
        const hasAnyRestrictions = 
            decl.finalTaxonomy.finalTaxonomyFlag === true ||
            (decl.finalTaxonomy.finalObjectTypes && decl.finalTaxonomy.finalObjectTypes.length > 0) ||
            (decl.finalTaxonomy.finalObjects && decl.finalTaxonomy.finalObjects.length > 0) ||
            (decl.finalTaxonomy.selections && decl.finalTaxonomy.selections.length > 0);
            
        if (!hasAnyRestrictions) {
            const noRestrictions = document.createElement('div');
            noRestrictions.textContent = 'No specific restrictions defined (finalTaxonomy declaration exists but has no constraints)';
            noRestrictions.style.cssText = 'color: #999; font-style: italic; font-size: 13px;';
            declSection.appendChild(noRestrictions);
        }
        
        finalTaxonomyView.appendChild(declSection);
    });
    
    container.appendChild(finalTaxonomyView);
}

/**
 * Populate taxonomy properties tab (mirrors default properties tab)
 * @param {Object} obj - The taxonomy object
 */
export function populateTaxonomyPropertiesTab(obj) {
    console.log('[populateTaxonomyPropertiesTab] Populating properties for:', obj);
    
    const container = document.getElementById('taxonomy-properties-content');
    if (!container) {
        console.error('[populateTaxonomyPropertiesTab] Taxonomy properties container not found');
        return;
    }
    
    // Clear previous content
    container.innerHTML = '';
    
    // Create panels structure (same as default properties tab)
    const panelsContainer = document.createElement('div');
    panelsContainer.style.cssText = 'display: flex; flex-direction: column; height: 100%;';
    
    // Attributes panel
    const attributesPanel = createAttributesPanel(obj);
    panelsContainer.appendChild(attributesPanel);
    
    // Labels panel
    const labelsPanel = createLabelsPanel(obj);
    panelsContainer.appendChild(labelsPanel);
    
    // References panel
    const referencesPanel = createReferencesPanel(obj);
    panelsContainer.appendChild(referencesPanel);
    
    // QName locations panel
    const locationsPanel = createQNameLocationsPanel(obj);
    panelsContainer.appendChild(locationsPanel);
    
    container.appendChild(panelsContainer);
}

/**
 * Helper functions to create panels (similar to details-panel.js)
 */

function createAttributesPanel(obj) {
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.cssText = 'padding: 10px; border-bottom: 1px solid #ddd;';
    
    const title = document.createElement('h3');
    title.textContent = 'Attributes';
    title.style.margin = '0 0 10px 0';
    panel.appendChild(title);
    
    const table = document.createElement('table');
    table.style.cssText = 'width: 100%; border-collapse: collapse;';
    
    // Add standard attributes
    const attrs = [
        ['Name', obj.name],
        ['Version', obj.version],
        ['Namespace', obj.namespace],
        ['Schema Ref', obj.schemaRef],
        ['Target Namespace', obj.targetNamespace]
    ];
    
    attrs.forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
            const row = table.insertRow();
            const keyCell = row.insertCell(0);
            keyCell.textContent = key;
            keyCell.style.cssText = 'font-weight: bold; padding: 4px 8px 4px 0; vertical-align: top;';
            
            const valueCell = row.insertCell(1);
            valueCell.textContent = value;
            valueCell.style.cssText = 'padding: 4px 0; word-break: break-all;';
        }
    });
    
    panel.appendChild(table);
    return panel;
}

function createLabelsPanel(obj) {
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.cssText = 'padding: 10px; border-bottom: 1px solid #ddd;';
    
    const title = document.createElement('h3');
    title.textContent = 'Labels';
    title.style.margin = '0 0 10px 0';
    panel.appendChild(title);
    
    if (obj.labels && obj.labels.length > 0) {
        const list = document.createElement('ul');
        list.style.cssText = 'margin: 0; padding-left: 20px;';
        
        obj.labels.forEach(label => {
            const item = document.createElement('li');
            item.textContent = `${label.value || label} (${label.lang || label.language || 'en'})`;
            list.appendChild(item);
        });
        
        panel.appendChild(list);
    } else {
        const noLabels = document.createElement('div');
        noLabels.textContent = 'No labels defined';
        noLabels.style.cssText = 'color: #999; font-style: italic;';
        panel.appendChild(noLabels);
    }
    
    return panel;
}

function createReferencesPanel(obj) {
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.cssText = 'padding: 10px; border-bottom: 1px solid #ddd;';
    
    const title = document.createElement('h3');
    title.textContent = 'References';
    title.style.margin = '0 0 10px 0';
    panel.appendChild(title);
    
    if (obj.references && obj.references.length > 0) {
        const list = document.createElement('ul');
        list.style.cssText = 'margin: 0; padding-left: 20px;';
        
        obj.references.forEach(ref => {
            const item = document.createElement('li');
            item.textContent = JSON.stringify(ref);
            list.appendChild(item);
        });
        
        panel.appendChild(list);
    } else {
        const noRefs = document.createElement('div');
        noRefs.textContent = 'No references defined';
        noRefs.style.cssText = 'color: #999; font-style: italic;';
        panel.appendChild(noRefs);
    }
    
    return panel;
}

function createQNameLocationsPanel(obj) {
    const panel = document.createElement('div');
    panel.className = 'panel';
    panel.style.cssText = 'padding: 10px;';
    
    const title = document.createElement('h3');
    title.textContent = 'QName Locations';
    title.style.margin = '0 0 10px 0';
    panel.appendChild(title);
    
    const locations = document.createElement('div');
    locations.textContent = 'QName: ' + (obj.name || 'Unknown');
    locations.style.cssText = 'font-family: monospace; color: #555;';
    panel.appendChild(locations);
    
    return panel;
}
