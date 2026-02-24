/**
 * Cube Fact View Module
 * Displays all facts in a cube in a grid format with pagination
 */

import { getTaxonomyData } from './main.js';
import { getXbrlModel } from './utils.js';
import { generateFactsWithPagination, filterFactsToCube } from './fact-generator.js';
import { isFactSourceRelevantToCube } from './fact-metadata-generator.js';
import { validateCalculations } from './calculation-validator.js';

// Pagination state
const BATCH_SIZE = 500; // Load 500 CSV rows at a time
let currentCube = null;
let loadedFacts = [];
let factSourceStates = new Map(); // Track pagination state per factSource

/**
 * Build and display the fact view for a cube with pagination
 * Shows facts incrementally to avoid browser memory issues
 * @param {Object} cube - The cube object
 */
export async function buildCubeFactView(cube) {
    console.log('[Cube Fact View] Building fact view for cube:', cube.name);
    
    const taxonomyData = getTaxonomyData();
    if (!taxonomyData) {
        console.error('[Cube Fact View] No taxonomy data available');
        return;
    }
    
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Cube Fact View] No xbrlModel available');
        return;
    }
    
    // Reset pagination state for new cube
    currentCube = cube;
    loadedFacts = [];
    factSourceStates.clear();
    
    const container = document.getElementById('cube-fact-view-content');
    if (!container) {
        console.warn('[Cube Fact View] cube-fact-view-content container not found');
        return;
    }
    
    // Show initial loading message
    container.innerHTML = `
        <div style="padding: 20px;">
            <h3>Loading Facts...</h3>
            <p>Loading first batch of facts...</p>
        </div>
    `;
    
    // Load first batch of facts
    await loadNextBatch(cube, xbrlModel, container);
}

/**
 * Load the next batch of facts and update the display
 * @param {Object} cube - The cube object
 * @param {Object} xbrlModel - The XBRL model
 * @param {HTMLElement} container - The container element
 */
async function loadNextBatch(cube, xbrlModel, container) {
    console.log('[Cube Fact View] Loading next batch...');
    
    const batchStartTime = performance.now();
    let newFacts = [];
    let hasMoreData = false;
    
    // 1. Check materialized facts (only on first load)
    if (loadedFacts.length === 0 && xbrlModel.facts && xbrlModel.facts.length > 0) {
        console.log('[Cube Fact View] Including materialized facts:', xbrlModel.facts.length);
        const materializedFacts = filterFactsToCube(xbrlModel.facts, cube, xbrlModel);
        newFacts.push(...materializedFacts);
    }
    
    // 2. Load batch from hash-based factSources
    if (xbrlModel.factSources && xbrlModel.factSources.length > 0) {
        for (const factSource of xbrlModel.factSources) {
            // Only process hash-based factSources
            if (!factSource.hash || !factSource.metadata) {
                continue;
            }
            
            // Check if factSource is relevant to this cube
            const isRelevant = isFactSourceRelevantToCube(factSource.metadata, cube);
            if (!isRelevant) {
                continue;
            }
            
            // Get or initialize state for this factSource
            let state = factSourceStates.get(factSource.name);
            if (!state) {
                state = { currentRow: 1, hasMore: true }; // Row 1 (skip header at row 0)
                factSourceStates.set(factSource.name, state);
            }
            
            // Skip if this factSource is exhausted
            if (!state.hasMore) {
                continue;
            }
            
            try {
                console.log(`[Cube Fact View] Loading batch from ${factSource.name}, row ${state.currentRow}`);
                
                const result = await generateFactsWithPagination(
                    factSource,
                    state.currentRow,
                    BATCH_SIZE,
                    xbrlModel,
                    cube // Pass cube for filtering
                );
                
                console.log(`[Cube Fact View] Batch loaded: ${result.facts.length} facts (filtered to cube)`);
                
                newFacts.push(...result.facts);
                state.currentRow = result.endRow + 1;
                state.hasMore = result.hasMore;
                
                if (result.hasMore) {
                    hasMoreData = true;
                }
            } catch (error) {
                console.error(`[Cube Fact View] Error loading batch from ${factSource.name}:`, error);
                state.hasMore = false;
            }
        }
    }
    
    const batchTime = performance.now() - batchStartTime;
    console.log(`[Cube Fact View] Batch loaded in ${batchTime.toFixed(0)}ms: ${newFacts.length} new facts`);
    
    // Add new facts to loaded collection
    loadedFacts.push(...newFacts);
    
    // Update display
    renderFactView(cube, xbrlModel, container, hasMoreData);
}

/**
 * Render the fact view with current loaded facts
 * @param {Object} cube - The cube object
 * @param {Object} xbrlModel - The XBRL model
 * @param {HTMLElement} container - The container element
 * @param {boolean} hasMoreData - Whether more data can be loaded
 */
function renderFactView(cube, xbrlModel, container, hasMoreData) {
    if (loadedFacts.length === 0) {
        container.innerHTML = `
            <div style="padding: 20px;">
                <h3>No Facts Found</h3>
                <p>No facts found for this cube.</p>
            </div>
        `;
        return;
    }
    
    // Clear container
    container.innerHTML = '';
    
    // Add header
    const header = document.createElement('div');
    header.style.padding = '10px 20px';
    header.style.backgroundColor = '#f5f5f5';
    header.style.borderBottom = '2px solid #ddd';
    header.innerHTML = `
        <h3 style="margin: 0;">Fact View: ${cube.name}</h3>
        <p style="margin: 5px 0 0 0; color: #666;">Showing ${loadedFacts.length} fact(s)${hasMoreData ? ' (more available)' : ''}</p>
    `;
    container.appendChild(header);
    
    // Run calculation validation for this cube and collect inconsistent fact names
    const calcErrors = [];
    validateCalculations(xbrlModel, (msg, ctx) => calcErrors.push(ctx));
    const errorFactNames = new Set(
        calcErrors
            .filter(e => e.cubeName === cube.name)
            .map(e => e.factName)
    );

    // Show calculation error legend if any errors found
    if (errorFactNames.size > 0) {
        const legend = document.createElement('div');
        legend.style.padding = '6px 20px';
        legend.style.backgroundColor = '#fff3f3';
        legend.style.borderBottom = '1px solid #f5c6cb';
        legend.style.fontSize = '12px';
        legend.style.color = '#721c24';
        legend.innerHTML = '<span style="display:inline-block;width:14px;height:14px;background:rgba(220,53,69,0.2);border:1px solid rgba(220,53,69,0.6);vertical-align:middle;margin-right:6px;"></span>' +
            'Calculation inconsistency \u2014 reported total does not match the sum of contributing facts (calc11e:inconsistentCalculationUsingRounding)';
        container.appendChild(legend);
    }

    // Build the grid
    const gridContainer = document.createElement('div');
    gridContainer.style.padding = '20px';
    gridContainer.style.overflowX = 'auto';
    gridContainer.style.overflowY = 'auto';
    gridContainer.style.maxHeight = 'calc(100vh - 300px)';
    
    // Analyze the facts to determine dimensions and create grid structure
    const gridData = buildGridData(loadedFacts, cube, xbrlModel);
    
    // Create the table
    const table = createFactTable(gridData, loadedFacts, errorFactNames);
    gridContainer.appendChild(table);
    
    container.appendChild(gridContainer);
    
    // Add "Load More" button if there's more data
    if (hasMoreData) {
        const loadMoreDiv = document.createElement('div');
        loadMoreDiv.style.padding = '20px';
        loadMoreDiv.style.textAlign = 'center';
        loadMoreDiv.style.borderTop = '1px solid #ddd';
        
        const loadMoreBtn = document.createElement('button');
        loadMoreBtn.textContent = `Load More Facts (${BATCH_SIZE} rows)`;
        loadMoreBtn.style.padding = '10px 20px';
        loadMoreBtn.style.fontSize = '14px';
        loadMoreBtn.style.cursor = 'pointer';
        loadMoreBtn.style.backgroundColor = '#007bff';
        loadMoreBtn.style.color = 'white';
        loadMoreBtn.style.border = 'none';
        loadMoreBtn.style.borderRadius = '4px';
        
        loadMoreBtn.onclick = async () => {
            loadMoreBtn.disabled = true;
            loadMoreBtn.textContent = 'Loading...';
            
            try {
                await loadNextBatch(cube, xbrlModel, container);
            } catch (error) {
                console.error('[Cube Fact View] Error loading more facts:', error);
                alert('Error loading more facts. See console for details.');
            } finally {
                // Button will be recreated by renderFactView
            }
        };
        
        loadMoreDiv.appendChild(loadMoreBtn);
        container.appendChild(loadMoreDiv);
    }
}

// Note: filterFactsToCube is now imported from fact-generator.js
// Note: findFactsInCube has been replaced by loadNextBatch for pagination

/**
 * Order concepts by network or domain order
 * @param {Array} concepts - Array of concept names
 * @param {Object} cube - The cube object
 * @param {Object} xbrlModel - The taxonomy xbrlModel
 * @returns {Array} Ordered array of concept names
 */
function orderConceptsByNetworkOrDomain(concepts, cube, xbrlModel) {
    // First try to use cubeNetworks order
    if (cube.cubeNetworks && cube.cubeNetworks.length > 0 && xbrlModel.networks) {
        // Find the first network that has xbrl:parent-child relationships
        for (const networkName of cube.cubeNetworks) {
            const network = xbrlModel.networks.find(n => n.name === networkName);
            if (network && network.relationshipTypeName === 'xbrl:parent-child' && network.relationships) {
                console.log('[Cube Fact View] Using network order from:', networkName);
                return orderConceptsByHierarchy(concepts, network.relationships, network.roots);
            }
        }
    }
    
    // Fall back to domain order
    if (xbrlModel.domains) {
        // Find the domain for the concept dimension
        const conceptDim = cube.cubeDimensions.find(d => d.dimensionName === 'xbrl:concept');
        if (conceptDim && conceptDim.domainName) {
            const domain = xbrlModel.domains.find(d => d.name === conceptDim.domainName);
            if (domain && domain.relationships) {
                console.log('[Cube Fact View] Using domain order from:', conceptDim.domainName);
                return orderConceptsByHierarchy(concepts, domain.relationships, domain.root ? [domain.root] : null);
            }
        }
    }
    
    // Fall back to alphabetical sort
    console.log('[Cube Fact View] No network or domain order found, using alphabetical sort');
    return concepts.sort();
}

/**
 * Order concepts by hierarchical tree traversal (matching Grid View order)
 * @param {Array} concepts - Array of concept names to order
 * @param {Array} relationships - Array of relationship objects with source, target, and order
 * @param {Array|string} roots - Root node(s) or single root
 * @returns {Array} Ordered array of concept names
 */
function orderConceptsByHierarchy(concepts, relationships, roots) {
    // Build children map with order
    const childrenMap = {};
    const allNodes = new Set();
    
    relationships.forEach(rel => {
        if (!childrenMap[rel.source]) {
            childrenMap[rel.source] = [];
        }
        childrenMap[rel.source].push({
            target: rel.target,
            order: rel.order !== undefined ? rel.order : 999999
        });
        allNodes.add(rel.source);
        allNodes.add(rel.target);
    });
    
    // Sort children by order
    Object.keys(childrenMap).forEach(source => {
        childrenMap[source].sort((a, b) => a.order - b.order);
    });
    
    // Traverse tree depth-first to build ordered list
    const orderedList = [];
    const visited = new Set();
    
    function traverse(nodeName) {
        if (visited.has(nodeName)) return;
        visited.add(nodeName);
        
        // Add this node if it's in our concepts list
        if (concepts.includes(nodeName)) {
            orderedList.push(nodeName);
        }
        
        // Traverse children
        const children = childrenMap[nodeName] || [];
        children.forEach(child => {
            traverse(child.target);
        });
    }
    
    // Start from roots
    if (roots) {
        const rootArray = Array.isArray(roots) ? roots : [roots];
        rootArray.forEach(root => {
            // Start with the root's children
            const children = childrenMap[root] || [];
            children.forEach(child => {
                traverse(child.target);
            });
        });
    } else {
        // No explicit roots - find nodes that are never targets
        const targets = new Set();
        relationships.forEach(rel => targets.add(rel.target));
        const implicitRoots = Array.from(allNodes).filter(node => !targets.has(node));
        
        implicitRoots.forEach(root => {
            traverse(root);
        });
    }
    
    // Add any remaining concepts that weren't in the tree (alphabetically)
    const remaining = concepts.filter(c => !orderedList.includes(c)).sort();
    return [...orderedList, ...remaining];
}

/**
 * Build grid data structure from facts
 * Determines which dimension should be rows vs columns
 * @param {Array} facts - Array of fact objects
 * @param {Object} cube - The cube object
 * @param {Object} xbrlModel - The taxonomy xbrlModel
 * @returns {Object} Grid data structure
 */
function buildGridData(facts, cube, xbrlModel) {
    // Collect all unique values for each dimension
    const dimensionValues = {};
    const dimensions = [];
    const optionalDimensions = new Set();
    
    // Initialize dimension values map - only for dimensions that appear in facts
    cube.cubeDimensions.forEach(cubeDim => {
        const dimName = cubeDim.dimensionName;
        // Only include dimensions that are not optional OR that appear in at least one fact
        const isOptional = cubeDim.allowDomainFacts === true;
        const appearsInFacts = facts.some(f => f.factDimensions && f.factDimensions[dimName] !== undefined);
        
        if (!isOptional || appearsInFacts) {
            dimensions.push(dimName);
            dimensionValues[dimName] = new Set();
            if (isOptional) {
                optionalDimensions.add(dimName);
            }
        }
    });
    
    console.log('[Cube Fact View] Dimensions to display:', dimensions);
    console.log('[Cube Fact View] Optional dimensions:', Array.from(optionalDimensions));
    
    // Collect all unique dimension values from facts
    facts.forEach(fact => {
        if (!fact.factDimensions) return;
        
        Object.entries(fact.factDimensions).forEach(([dimName, value]) => {
            if (dimensionValues[dimName]) {
                dimensionValues[dimName].add(value);
            }
        });
        
        // For optional dimensions that don't appear in this fact, add a placeholder
        optionalDimensions.forEach(dimName => {
            if (fact.factDimensions[dimName] === undefined) {
                dimensionValues[dimName].add('(no value)');
            }
        });
    });
    
    // Convert sets to sorted arrays
    Object.keys(dimensionValues).forEach(dimName => {
        dimensionValues[dimName] = Array.from(dimensionValues[dimName]);
        
        // For concept dimension, use network or domain order if available
        if (dimName === 'xbrl:concept') {
            dimensionValues[dimName] = orderConceptsByNetworkOrDomain(dimensionValues[dimName], cube, xbrlModel);
        } else {
            // For other dimensions, sort alphabetically
            dimensionValues[dimName].sort();
        }
        
        console.log(`[Cube Fact View] Dimension ${dimName} has ${dimensionValues[dimName].length} unique values:`, dimensionValues[dimName]);
    });
    
    // Determine row and column dimensions
    // Use concept as rows by default, other dimensions as columns
    let rowDimension = 'xbrl:concept';
    let columnDimensions = dimensions.filter(d => d !== 'xbrl:concept');
    
    // If no concept dimension, use first dimension as rows
    if (!dimensions.includes('xbrl:concept') && dimensions.length > 0) {
        rowDimension = dimensions[0];
        columnDimensions = dimensions.slice(1);
    }
    
    console.log('[Cube Fact View] Row dimension:', rowDimension);
    console.log('[Cube Fact View] Column dimensions:', columnDimensions);
    
    return {
        rowDimension,
        columnDimensions,
        dimensionValues,
        dimensions
    };
}

/**
 * Create the fact table with data
 * @param {Object} gridData - Grid data structure
 * @param {Array} facts - Array of fact objects
 * @param {Set<string>} [errorFactNames] - Set of fact names that have calculation inconsistencies
 * @returns {HTMLElement} Table element
 */
function createFactTable(gridData, facts, errorFactNames = new Set()) {
    const { rowDimension, columnDimensions, dimensionValues } = gridData;
    
    const table = document.createElement('table');
    table.style.borderCollapse = 'collapse';
    table.style.fontSize = '12px';
    table.style.minWidth = '100%';
    
    // Create header
    const thead = document.createElement('thead');
    
    // If we have column dimensions, create combination headers
    if (columnDimensions.length > 0) {
        // Create column combinations
        const columnCombinations = createDimensionCombinations(columnDimensions, dimensionValues);
        
        // Filter out empty columns
        const nonEmptyColumns = columnCombinations.filter(combo => 
            hasFactsForColumnCombination(combo, rowDimension, dimensionValues[rowDimension], facts)
        );
        
        // Create header rows for each column dimension
        columnDimensions.forEach((dimName, idx) => {
            const headerRow = document.createElement('tr');
            
            // Add empty cell for row dimension header
            if (idx === 0) {
                const cornerCell = document.createElement('th');
                cornerCell.textContent = rowDimension;
                cornerCell.rowSpan = columnDimensions.length;
                cornerCell.style.border = '1px solid #ddd';
                cornerCell.style.padding = '8px';
                cornerCell.style.backgroundColor = '#e3f2fd';
                cornerCell.style.fontWeight = 'bold';
                cornerCell.style.position = 'sticky';
                cornerCell.style.left = '0';
                cornerCell.style.zIndex = '3';
                headerRow.appendChild(cornerCell);
            }
            
            // Add column headers
            let currentValue = null;
            let colspan = 0;
            
            nonEmptyColumns.forEach((combo, colIdx) => {
                const value = combo[dimName];
                
                if (value === currentValue) {
                    colspan++;
                } else {
                    if (currentValue !== null) {
                        // Add the previous cell
                        const th = document.createElement('th');
                        th.textContent = currentValue;
                        th.colSpan = colspan;
                        th.style.border = '1px solid #ddd';
                        th.style.padding = '8px';
                        th.style.backgroundColor = idx === 0 ? '#e3f2fd' : '#f5f5f5';
                        th.style.textAlign = 'center';
                        headerRow.appendChild(th);
                    }
                    currentValue = value;
                    colspan = 1;
                }
                
                // Add the last cell
                if (colIdx === nonEmptyColumns.length - 1) {
                    const th = document.createElement('th');
                    th.textContent = currentValue;
                    th.colSpan = colspan;
                    th.style.border = '1px solid #ddd';
                    th.style.padding = '8px';
                    th.style.backgroundColor = idx === 0 ? '#e3f2fd' : '#f5f5f5';
                    th.style.textAlign = 'center';
                    headerRow.appendChild(th);
                }
            });
            
            thead.appendChild(headerRow);
        });
        
        table.appendChild(thead);
        
        // Create body with data
        const tbody = document.createElement('tbody');
        
        // Get all row values
        const rowValues = dimensionValues[rowDimension] || [];
        
        // Filter out empty rows
        const nonEmptyRows = rowValues.filter(rowValue => 
            hasFactsForRowValue(rowValue, rowDimension, nonEmptyColumns, facts)
        );
        
        nonEmptyRows.forEach(rowValue => {
            const row = document.createElement('tr');
            
            // Add row header
            const rowHeader = document.createElement('th');
            rowHeader.textContent = rowValue;
            rowHeader.style.border = '1px solid #ddd';
            rowHeader.style.padding = '8px';
            rowHeader.style.backgroundColor = '#f5f5f5';
            rowHeader.style.textAlign = 'left';
            rowHeader.style.fontWeight = 'normal';
            rowHeader.style.position = 'sticky';
            rowHeader.style.left = '0';
            rowHeader.style.zIndex = '2';
            rowHeader.style.backgroundColor = '#fff';
            row.appendChild(rowHeader);
            
            // Add data cells
            nonEmptyColumns.forEach(combo => {
                const cell = document.createElement('td');
                cell.style.border = '1px solid #ddd';
                cell.style.padding = '8px';
                cell.style.textAlign = 'right';
                
                // Find fact for this combination
                const fact = findFactForCombination(rowValue, rowDimension, combo, facts);
                
                if (fact && fact.factValues && fact.factValues.length > 0) {
                    // Display the fact value(s)
                    const values = fact.factValues.map(fv => fv.value || '').join(', ');
                    cell.textContent = values;
                    if (errorFactNames.has(fact.name)) {
                        cell.style.backgroundColor = 'rgba(220,53,69,0.15)';
                        cell.style.outline = '1px solid rgba(220,53,69,0.5)';
                        cell.title = 'Calculation inconsistency: reported total does not match the sum of contributing facts (calc11e:inconsistentCalculationUsingRounding)';
                    } else {
                        cell.style.backgroundColor = '#fff';
                    }
                } else {
                    cell.textContent = '';
                    cell.style.backgroundColor = '#fafafa';
                }
                
                row.appendChild(cell);
            });
            
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        
    } else {
        // Simple case: only one dimension (rows only)
        const headerRow = document.createElement('tr');
        
        const dimHeader = document.createElement('th');
        dimHeader.textContent = rowDimension;
        dimHeader.style.border = '1px solid #ddd';
        dimHeader.style.padding = '8px';
        dimHeader.style.backgroundColor = '#e3f2fd';
        dimHeader.style.fontWeight = 'bold';
        headerRow.appendChild(dimHeader);
        
        const valueHeader = document.createElement('th');
        valueHeader.textContent = 'Value';
        valueHeader.style.border = '1px solid #ddd';
        valueHeader.style.padding = '8px';
        valueHeader.style.backgroundColor = '#e3f2fd';
        valueHeader.style.fontWeight = 'bold';
        headerRow.appendChild(valueHeader);
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        
        const rowValues = dimensionValues[rowDimension] || [];
        
        // Filter out empty rows
        const nonEmptyRows = rowValues.filter(rowValue => {
            const fact = facts.find(f => f.factDimensions && f.factDimensions[rowDimension] === rowValue);
            return fact && fact.factValues && fact.factValues.length > 0;
        });
        
        nonEmptyRows.forEach(rowValue => {
            const row = document.createElement('tr');
            
            const nameCell = document.createElement('td');
            nameCell.textContent = rowValue;
            nameCell.style.border = '1px solid #ddd';
            nameCell.style.padding = '8px';
            nameCell.style.backgroundColor = '#f5f5f5';
            row.appendChild(nameCell);
            
            const valueCell = document.createElement('td');
            valueCell.style.border = '1px solid #ddd';
            valueCell.style.padding = '8px';
            valueCell.style.textAlign = 'right';
            
            const fact = facts.find(f => f.factDimensions && f.factDimensions[rowDimension] === rowValue);
            if (fact && fact.factValues && fact.factValues.length > 0) {
                const values = fact.factValues.map(fv => fv.value || '').join(', ');
                valueCell.textContent = values;
                if (errorFactNames.has(fact.name)) {
                    valueCell.style.backgroundColor = 'rgba(220,53,69,0.15)';
                    valueCell.style.outline = '1px solid rgba(220,53,69,0.5)';
                    valueCell.title = 'Calculation inconsistency: reported total does not match the sum of contributing facts (calc11e:inconsistentCalculationUsingRounding)';
                }
            }
            
            row.appendChild(valueCell);
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
    }
    
    return table;
}

/**
 * Create all combinations of dimension values for columns
 * @param {Array} dimensions - Array of dimension names
 * @param {Object} dimensionValues - Map of dimension name to array of values
 * @returns {Array} Array of combination objects
 */
function createDimensionCombinations(dimensions, dimensionValues) {
    if (dimensions.length === 0) return [{}];
    
    const [firstDim, ...restDims] = dimensions;
    const firstValues = dimensionValues[firstDim] || [];
    
    if (restDims.length === 0) {
        return firstValues.map(val => ({ [firstDim]: val }));
    }
    
    const restCombos = createDimensionCombinations(restDims, dimensionValues);
    const result = [];
    
    firstValues.forEach(val => {
        restCombos.forEach(combo => {
            result.push({ [firstDim]: val, ...combo });
        });
    });
    
    return result;
}

/**
 * Check if there are any facts for a column combination
 * @param {Object} columnCombo - Column dimension combination
 * @param {string} rowDimension - Row dimension name
 * @param {Array} rowValues - Array of row values
 * @param {Array} facts - Array of fact objects
 * @returns {boolean} True if there are facts for this column
 */
function hasFactsForColumnCombination(columnCombo, rowDimension, rowValues, facts) {
    return rowValues.some(rowValue => {
        const fact = findFactForCombination(rowValue, rowDimension, columnCombo, facts);
        return fact && fact.factValues && fact.factValues.length > 0;
    });
}

/**
 * Check if there are any facts for a row value
 * @param {string} rowValue - Row value
 * @param {string} rowDimension - Row dimension name
 * @param {Array} columnCombinations - Array of column combinations
 * @param {Array} facts - Array of fact objects
 * @returns {boolean} True if there are facts for this row
 */
function hasFactsForRowValue(rowValue, rowDimension, columnCombinations, facts) {
    return columnCombinations.some(combo => {
        const fact = findFactForCombination(rowValue, rowDimension, combo, facts);
        return fact && fact.factValues && fact.factValues.length > 0;
    });
}

/**
 * Find fact for a specific dimension combination
 * @param {string} rowValue - Row value
 * @param {string} rowDimension - Row dimension name
 * @param {Object} columnCombo - Column dimension combination
 * @param {Array} facts - Array of fact objects
 * @returns {Object|null} Fact object or null
 */
function findFactForCombination(rowValue, rowDimension, columnCombo, facts) {
    return facts.find(fact => {
        if (!fact.factDimensions) return false;
        
        // Check if row dimension matches
        if (fact.factDimensions[rowDimension] !== rowValue) return false;
        
        // Check if all column dimensions match
        return Object.entries(columnCombo).every(([dimName, value]) => {
            const factValue = fact.factDimensions[dimName];
            
            // Handle the "(no value)" placeholder for optional dimensions
            if (value === '(no value)') {
                return factValue === undefined;
            }
            
            // Otherwise, the values must match exactly
            return factValue === value;
        });
    });
}
