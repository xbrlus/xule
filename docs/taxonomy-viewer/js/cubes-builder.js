/**
 * Cubes Builder Module
 * Handles the cubes tab functionality, including:
 * - Cube list rendering
 * - Cube grid visualization
 * - Concept tree building from domains
 */

import { getTaxonomyData } from './main.js';
import { getIconForType, getXbrlModel } from './utils.js';

/**
 * Build and display the cubes list
 */
export function buildCubes() {
    console.log('[Cubes Builder] Building cubes list');
    
    const taxonomyData = getTaxonomyData();
    if (!taxonomyData) {
        console.error('[Cubes Builder] No taxonomy data available');
        return;
    }

    const cubesList = document.getElementById('cubes-list');
    if (!cubesList) {
        console.warn('[Cubes Builder] cubes-list container not found');
        return;
    }

    // Clear existing content
    cubesList.innerHTML = '';

    const cubesUl = document.createElement('ul');
    const xbrlModel = getXbrlModel(taxonomyData);
    if (xbrlModel?.cubes) {
        console.log('[Cubes Builder] Cubes found:', xbrlModel.cubes.length);
        
        // Create a sorted list of cubes by name
        const sortedCubes = [...xbrlModel.cubes].sort((a, b) => {
            return a.name.localeCompare(b.name);
        });
        
        sortedCubes.forEach(cube => {
            const li = document.createElement('li');
            
            // Add icon for cube (check for custom iconLabel first)
            const icon = document.createElement('span');
            icon.className = 'node-icon';
            icon.textContent = getIconForType('cube', cube.name);
            li.appendChild(icon);
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = cube.name;
            li.appendChild(nameSpan);
            
            li.classList.add('node');
            li.dataset.type = 'cube';
            li.dataset.obj = JSON.stringify(cube);
            cubesUl.appendChild(li);
        });
    } else {
        console.warn('[Cubes Builder] No cubes found in taxonomy data');
    }

    cubesList.appendChild(cubesUl);

    // Attach event handlers using legacy handlers from window
    if (typeof window.attachNodeHandlers === 'function') {
        window.attachNodeHandlers(cubesList);
    } else {
        console.warn('[Cubes Builder] attachNodeHandlers not available');
    }
}

/**
 * Build concept tree structure from domain relationships
 * @param {Object} domain - Domain object with relationships
 * @returns {Array} Array of concept tree nodes
 */
function buildConceptTreeFromDomain(domain) {
    // Build a tree structure from domain relationships
    const childrenMap = {};
    const allNodes = new Set();
    
    if (domain.relationships) {
        domain.relationships.forEach(rel => {
            if (!childrenMap[rel.source]) {
                childrenMap[rel.source] = [];
            }
            childrenMap[rel.source].push({
                target: rel.target,
                order: rel.order || 0
            });
            allNodes.add(rel.source);
            allNodes.add(rel.target);
        });
        
        // Sort children by order
        Object.keys(childrenMap).forEach(source => {
            childrenMap[source].sort((a, b) => a.order - b.order);
        });
    }
    
    // Build tree starting from a node
    function buildTree(nodeName) {
        const children = childrenMap[nodeName] || [];
        return {
            name: nodeName,
            children: children.map(child => buildTree(child.target))
        };
    }
    
    // Start from root
    if (domain.root) {
        const rootChildren = childrenMap[domain.root] || [];
        return rootChildren.map(child => buildTree(child.target));
    }
    
    return [];
}

/**
 * Build and display the cube grid visualization
 * @param {Object} cube - Cube object to visualize
 */
export function buildCubeGrid(cube) {
    console.log('[Cubes Builder] Building cube grid for:', cube.name);
    
    const taxonomyData = getTaxonomyData();
    const gridContent = document.getElementById('cube-grid-content');
    if (!gridContent) {
        console.warn('[Cubes Builder] cube-grid-content container not found');
        return;
    }
    
    gridContent.innerHTML = '';
    
    if (!cube.cubeDimensions || cube.cubeDimensions.length === 0) {
        gridContent.innerHTML = '<p style="padding: 20px;">No dimensions defined for this cube.</p>';
        return;
    }
    
    // Check if this is a default cube
    const isDefaultCube = cube.cubeType === 'xbrl:defaultCube';
    
    // Find the concept dimension
    const conceptDim = cube.cubeDimensions.find(d => d.dimensionName === 'xbrl:concept');
    if (!conceptDim) {
        gridContent.innerHTML = '<p style="padding: 20px;">No concept dimension found for this cube.</p>';
        return;
    }
    
    // For defaultCube, create an implicit domain containing all concepts
    let domain;
    let hasMoreConcepts = false;
    if (isDefaultCube) {
        // Build an implicit domain with limited concepts (max 10)
        domain = {
            name: 'xbrl:implicitConceptDomain',
            root: 'xbrl:conceptDomain',
            relationships: []
        };
        
        const maxConcepts = 10;
        const conceptsToAdd = [];
        const xbrlModel = getXbrlModel(taxonomyData);
        
        // Add abstracts up to limit
        if (xbrlModel?.abstracts) {
            for (const abs of xbrlModel.abstracts) {
                if (conceptsToAdd.length >= maxConcepts) break;
                conceptsToAdd.push(abs.name);
            }
        }
        
        // Add concepts up to limit
        if (xbrlModel?.concepts && conceptsToAdd.length < maxConcepts) {
            for (const concept of xbrlModel.concepts) {
                if (conceptsToAdd.length >= maxConcepts) break;
                conceptsToAdd.push(concept.name);
            }
        }
        
        // Check if there are more concepts than we're showing
        const totalConcepts = (xbrlModel?.abstracts?.length || 0) + 
                             (xbrlModel?.concepts?.length || 0);
        hasMoreConcepts = totalConcepts > maxConcepts;
        
        // Build relationships
        conceptsToAdd.forEach(conceptName => {
            domain.relationships.push({
                source: 'xbrl:conceptDomain',
                target: conceptName
            });
        });
    } else {
        // For non-default cubes, require a domainName
        if (!conceptDim.domainName) {
            gridContent.innerHTML = '<p style="padding: 20px;">No concept domain found for this cube.</p>';
            return;
        }
        
        // Find the domain for the concept dimension
        const xbrlModel = getXbrlModel(taxonomyData);
        domain = xbrlModel?.domains?.find(d => d.name === conceptDim.domainName);
        if (!domain || !domain.relationships || domain.relationships.length === 0) {
            gridContent.innerHTML = '<p style="padding: 20px;">Concept domain not found or has no relationships.</p>';
            return;
        }
    }
    
    // Get other dimensions (exclude concept)
    const otherDimensions = cube.cubeDimensions.filter(d => 
        d.dimensionName !== 'xbrl:concept'
    );
    
    // Build concept tree structure from domain
    const conceptTree = buildConceptTreeFromDomain(domain);
    
    // For each dimension, get its members
    const dimensionMembers = [];
    for (const dim of otherDimensions) {
        const dimInfo = {
            dimension: dim,
            members: []
        };
        
        // Find members for this dimension if it has a domain
        if (dim.domainName) {
            const xbrlModel = getXbrlModel(taxonomyData);
            const dimDomain = xbrlModel?.domains?.find(d => d.name === dim.domainName);
            if (dimDomain && dimDomain.relationships) {
                // Extract all target members from domain relationships
                const memberSet = new Set();
                dimDomain.relationships.forEach(rel => {
                    memberSet.add(rel.target);
                });
                dimInfo.members = Array.from(memberSet);
            }
        }
        
        dimensionMembers.push(dimInfo);
    }
    
    // Calculate the maximum number of member columns needed
    const maxMembers = Math.max(...dimensionMembers.map(d => d.members.length), 1);
    
    // Create table
    const table = document.createElement('table');
    table.id = 'cube-grid';
    
    // Create header section
    const thead = document.createElement('thead');
    
    // Row 1: First column is "Concept", then member columns
    const firstRow = document.createElement('tr');
    const conceptHeader = document.createElement('th');
    conceptHeader.textContent = 'Concept';
    conceptHeader.style.minWidth = '200px';
    conceptHeader.rowSpan = (otherDimensions.length * 2) || 1; // Spans all dimension + member rows
    firstRow.appendChild(conceptHeader);
    
    // Add member column headers
    for (let i = 0; i < maxMembers; i++) {
        const memberHeader = document.createElement('th');
        memberHeader.textContent = `Member ${i + 1}`;
        memberHeader.classList.add('dimension-header');
        memberHeader.style.minWidth = '120px';
        firstRow.appendChild(memberHeader);
    }
    thead.appendChild(firstRow);
    
    // Add dimension rows (dimension name + members below it)
    otherDimensions.forEach((dim, dimIndex) => {
        // Dimension name row
        const dimNameRow = document.createElement('tr');
        const dimInfo = dimensionMembers[dimIndex];
        
        // Add dimension name across all member columns
        for (let i = 0; i < maxMembers; i++) {
            const dimCell = document.createElement('th');
            if (i === 0) {
                // Build dimension text with attributes
                let dimText = dim.dimensionName || 'Dimension';
                
                // Add allowDomainFacts indicator (defaults to false if not defined)
                const allowDomainFacts = dim.allowDomainFacts !== undefined ? dim.allowDomainFacts : false;
                const optionalText = allowDomainFacts ? 'optional' : 'required';
                const optionalColor = allowDomainFacts ? '#2e7d32' : '#d32f2f';
                
                dimCell.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <span>${dimText}</span>
                        <span style="font-size: 11px; color: ${optionalColor}; font-weight: normal; margin-left: 10px;">
                            (${optionalText})
                        </span>
                    </div>
                `;
                
                // Add domainDataType if present and domainName is not provided
                if (dim.domainDataType && !dim.domainName) {
                    const dataTypeDiv = document.createElement('div');
                    dataTypeDiv.style.fontSize = '11px';
                    dataTypeDiv.style.fontWeight = 'normal';
                    dataTypeDiv.style.color = '#666';
                    dataTypeDiv.style.marginTop = '4px';
                    dataTypeDiv.textContent = `Type: ${dim.domainDataType}`;
                    dimCell.appendChild(dataTypeDiv);
                }
                
                dimCell.colSpan = maxMembers;
                dimCell.classList.add('dimension-header');
                dimCell.style.backgroundColor = '#e3f2fd';
                dimCell.style.textAlign = 'left';
                dimCell.style.fontWeight = 'bold';
                dimNameRow.appendChild(dimCell);
                break;
            }
        }
        thead.appendChild(dimNameRow);
        
        // Member row below dimension
        const memberRow = document.createElement('tr');
        for (let i = 0; i < maxMembers; i++) {
            const memberCell = document.createElement('th');
            if (i < dimInfo.members.length) {
                memberCell.textContent = dimInfo.members[i];
                memberCell.style.fontSize = '11px';
                memberCell.style.backgroundColor = '#f5f5f5';
            } else {
                memberCell.textContent = '-';
                memberCell.style.color = '#ccc';
                memberCell.style.backgroundColor = '#fafafa';
            }
            memberCell.style.textAlign = 'center';
            memberRow.appendChild(memberCell);
        }
        thead.appendChild(memberRow);
    });
    
    table.appendChild(thead);
    
    // Create body with concept rows
    const tbody = document.createElement('tbody');
    
    function addConceptRows(concepts, level = 0) {
        concepts.forEach(conceptItem => {
            const row = document.createElement('tr');
            
            // Concept cell
            const conceptCell = document.createElement('td');
            conceptCell.classList.add('concept-cell');
            conceptCell.style.paddingLeft = (level * 20 + 5) + 'px';
            conceptCell.textContent = conceptItem.name;
            row.appendChild(conceptCell);
            
            // Add empty cells for each member column
            for (let i = 0; i < maxMembers; i++) {
                const dimCell = document.createElement('td');
                dimCell.textContent = '';
                dimCell.style.textAlign = 'center';
                dimCell.style.color = '#999';
                dimCell.style.backgroundColor = '#fff';
                row.appendChild(dimCell);
            }
            
            tbody.appendChild(row);
            
            // Recursively add children
            if (conceptItem.children && conceptItem.children.length > 0) {
                addConceptRows(conceptItem.children, level + 1);
            }
        });
    }
    
    addConceptRows(conceptTree);
    table.appendChild(tbody);
    
    gridContent.appendChild(table);
    
    // Add indicator if there are more concepts in the default cube
    if (isDefaultCube && hasMoreConcepts) {
        const moreConceptsNote = document.createElement('div');
        moreConceptsNote.style.padding = '10px';
        moreConceptsNote.style.marginTop = '10px';
        moreConceptsNote.style.backgroundColor = '#fff3cd';
        moreConceptsNote.style.border = '1px solid #ffc107';
        moreConceptsNote.style.borderRadius = '4px';
        moreConceptsNote.style.fontSize = '13px';
        moreConceptsNote.innerHTML = `
            <strong>Note:</strong> This default cube contains more concepts than shown. 
            Only the first 10 concepts are displayed for performance.
        `;
        gridContent.appendChild(moreConceptsNote);
    }
}

/**
 * Initialize cubes tab
 */
export function initCubes() {
    console.log('[Cubes Builder] Initializing cubes tab');
    buildCubes();
}
