/**
 * Networks Builder Module
 * Handles the building and display of the Networks tab, including:
 * - Network tree rendering
 * - Relationship type filtering
 * - Display mode switching
 * - Recursion detection
 * - Root mismatch detection
 */

import { getTaxonomyData } from './state.js';
import { getIconForType, getNodeType, getXbrlModel } from './utils.js';
import { attachNodeHandlers } from './tree-handlers.js';

const MAX_DEPTH = 100;

/**
 * Get the display label for a node based on display mode
 */
function getNodeLabel(nodeName, displayMode) {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (displayMode === 'name' || !xbrlModel || !xbrlModel.labels) {
        return nodeName;
    }

    // Find the xbrl:label for this node
    // Support multiple English language variants: 'en', 'en-US', 'en-GB', etc.
    const label = xbrlModel.labels.find(l => 
        l.relatedName === nodeName && 
        (l.labelType === 'xbrl:label' || !l.labelType) &&
        l.language && l.language.startsWith('en')
    );

    return label ? label.value : nodeName;
}

/**
 * Check if a network contains recursion/cycles
 */
function hasNetworkRecursion(network) {
    if (!network.relationships || network.relationships.length === 0) {
        return false;
    }
    
    // Build adjacency map
    const childrenMap = {};
    network.relationships.forEach(rel => {
        if (!childrenMap[rel.source]) childrenMap[rel.source] = [];
        childrenMap[rel.source].push(rel.target);
    });

    // Check each node to see if it can reach itself (cycle detection)
    const allNodes = new Set();
    network.relationships.forEach(rel => {
        allNodes.add(rel.source);
        allNodes.add(rel.target);
    });

    for (const startNode of allNodes) {
        const visited = new Set();
        const stack = [startNode];
        
        while (stack.length > 0) {
            const current = stack.pop();
            
            if (visited.has(current)) {
                continue;
            }
            
            visited.add(current);
            
            const children = childrenMap[current] || [];
            for (const child of children) {
                if (child === startNode && current === startNode) {
                    // Direct self-reference
                    return true;
                }
                if (child === startNode) {
                    // Found a cycle back to start
                    return true;
                }
                if (!visited.has(child)) {
                    stack.push(child);
                }
            }
        }
    }

    return false;
}

/**
 * Check for root mismatches in a network
 * Returns an object with: { hasMismatch: boolean, actualRoots: Set, declaredRoots: Set }
 */
function checkRootMismatch(obj) {
    // Extract declared roots - networks use 'roots' array, domains use 'root' string
    const declaredRootsArray = obj.roots ? obj.roots : (obj.root ? [obj.root] : []);
    
    if (!obj.relationships || obj.relationships.length === 0) {
        return { hasMismatch: false, actualRoots: new Set(), declaredRoots: new Set(declaredRootsArray) };
    }

    // Find all nodes that are targets (children)
    const targetsSet = new Set();
    obj.relationships.forEach(rel => {
        targetsSet.add(rel.target);
    });

    // Find all nodes that are sources
    const sourcesSet = new Set();
    obj.relationships.forEach(rel => {
        sourcesSet.add(rel.source);
    });

    // Actual roots are nodes that are sources but never targets
    const actualRoots = new Set();
    for (const source of sourcesSet) {
        if (!targetsSet.has(source)) {
            actualRoots.add(source);
        }
    }

    // Declared roots (converted to Set for easy comparison)
    const declaredRoots = new Set(declaredRootsArray);

    // Check if there's a mismatch
    let hasMismatch = false;

    // Check if actual roots match declared roots
    if (actualRoots.size !== declaredRoots.size) {
        hasMismatch = true;
    } else {
        for (const root of actualRoots) {
            if (!declaredRoots.has(root)) {
                hasMismatch = true;
                break;
            }
        }
    }

    return { hasMismatch, actualRoots, declaredRoots };
}

/**
 * Show a popup with root mismatch details
 */
function showRootMismatchPopup(event, actualNotDeclared, declaredNotActual, networkName) {
    // Remove any existing popup
    const existingPopup = document.querySelector('.root-mismatch-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create popup
    const popup = document.createElement('div');
    popup.className = 'root-mismatch-popup';
    
    // Position popup near the click
    popup.style.left = (event.pageX + 10) + 'px';
    popup.style.top = (event.pageY + 10) + 'px';

    // Header
    const header = document.createElement('h4');
    header.innerHTML = `Root Mismatch: ${networkName}`;
    const closeBtn = document.createElement('button');
    closeBtn.className = 'close-btn';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => popup.remove();
    header.appendChild(closeBtn);
    popup.appendChild(header);

    // Section for actual roots not in declared
    if (actualNotDeclared.length > 0) {
        const section = document.createElement('div');
        section.className = 'section';
        
        const title = document.createElement('div');
        title.className = 'section-title';
        title.textContent = 'Actual roots NOT in declared roots array:';
        section.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'item-list';
        actualNotDeclared.forEach(root => {
            const item = document.createElement('li');
            item.textContent = root;
            list.appendChild(item);
        });
        section.appendChild(list);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-all-btn';
        copyBtn.textContent = 'Copy All';
        const copiedMsg = document.createElement('span');
        copiedMsg.className = 'copied-message';
        copiedMsg.textContent = 'Copied!';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(actualNotDeclared.join('\n')).then(() => {
                copiedMsg.style.display = 'inline';
                setTimeout(() => copiedMsg.style.display = 'none', 2000);
            });
        };
        section.appendChild(copyBtn);
        section.appendChild(copiedMsg);
        
        popup.appendChild(section);
    }

    // Section for declared roots not actual
    if (declaredNotActual.length > 0) {
        const section = document.createElement('div');
        section.className = 'section';
        
        const title = document.createElement('div');
        title.className = 'section-title';
        title.textContent = 'Declared roots NOT actual roots:';
        section.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'item-list';
        declaredNotActual.forEach(root => {
            const item = document.createElement('li');
            item.textContent = root;
            list.appendChild(item);
        });
        section.appendChild(list);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-all-btn';
        copyBtn.textContent = 'Copy All';
        const copiedMsg = document.createElement('span');
        copiedMsg.className = 'copied-message';
        copiedMsg.textContent = 'Copied!';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(declaredNotActual.join('\n')).then(() => {
                copiedMsg.style.display = 'inline';
                setTimeout(() => copiedMsg.style.display = 'none', 2000);
            });
        };
        section.appendChild(copyBtn);
        section.appendChild(copiedMsg);
        
        popup.appendChild(section);
    }

    document.body.appendChild(popup);

    // Close popup when clicking outside
    const closePopup = (e) => {
        if (!popup.contains(e.target)) {
            popup.remove();
            document.removeEventListener('click', closePopup);
        }
    };
    setTimeout(() => {
        document.addEventListener('click', closePopup);
    }, 0);

    // Adjust position if popup goes off screen
    const rect = popup.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        popup.style.left = (window.innerWidth - rect.width - 10) + 'px';
    }
    if (rect.bottom > window.innerHeight) {
        popup.style.top = (window.innerHeight - rect.height - 10) + 'px';
    }
}

/**
 * Add visual indicators (recursion and root mismatch) to a network name span
 */
function addNetworkIndicators(nameSpan, obj, hasRecursion, rootMismatchInfo, objName) {
    // Add red dot if recursion detected
    if (hasRecursion) {
        const redDot = document.createElement('span');
        redDot.textContent = ' 🔴';
        redDot.title = `Warning: This ${obj.roots ? 'network' : 'domain'} contains recursion/cycles`;
        redDot.style.fontSize = '8px';
        redDot.style.marginLeft = '5px';
        nameSpan.appendChild(redDot);
    }
    
    // Add blue icon if root mismatch detected
    if (rootMismatchInfo.hasMismatch) {
        const blueDot = document.createElement('span');
        blueDot.textContent = ' 🔵';
        
        // Build detailed tooltip
        const actualNotDeclared = Array.from(rootMismatchInfo.actualRoots).filter(r => !rootMismatchInfo.declaredRoots.has(r));
        const declaredNotActual = Array.from(rootMismatchInfo.declaredRoots).filter(r => !rootMismatchInfo.actualRoots.has(r));
        
        const rootWord = obj.roots ? 'roots' : 'root';
        blueDot.title = `Warning: Declared ${rootWord} do not match actual roots (Click for details)`;
        blueDot.style.fontSize = '8px';
        blueDot.style.marginLeft = '5px';
        blueDot.style.cursor = 'pointer';
        
        // Add click handler to show popup
        blueDot.addEventListener('click', function(e) {
            e.stopPropagation();
            showRootMismatchPopup(e, actualNotDeclared, declaredNotActual, objName);
        });
        
        nameSpan.appendChild(blueDot);
    }
}

/**
 * Build a childrenMap and selfReferences from relationships
 */
function buildChildrenMap(relationships) {
    const childrenMap = {};
    const selfReferences = new Set();
    
    if (relationships) {
        relationships.forEach(rel => {
            if (!childrenMap[rel.source]) childrenMap[rel.source] = [];
            childrenMap[rel.source].push({ target: rel.target, order: rel.order || 0 });
            
            // Check for self-reference
            if (rel.source === rel.target) {
                selfReferences.add(rel.source);
            }
        });
        
        // Sort children by order descending (higher order first)
        Object.keys(childrenMap).forEach(source => {
            childrenMap[source].sort((a, b) => b.order - a.order);
        });
    }
    
    return { childrenMap, selfReferences };
}

/**
 * Build a network tree from root nodes and relationships
 */
function buildNetworkTree(ul, node, childrenMap, relationships, selfReferences, rootMismatchInfo, displayMode = 'name') {
    const stack = [{ node: node, parentUl: ul, depth: 0, relationshipProps: null }];
    
    // Create a map of relationships by source-target pair for quick lookup
    const relationshipMap = {};
    if (relationships) {
        relationships.forEach(rel => {
            const key = `${rel.source}|||${rel.target}`;
            relationshipMap[key] = rel;
        });
    }
    
    while (stack.length > 0) {
        const { node: currentNode, parentUl: currentUl, depth, relationshipProps } = stack.pop();
        const li = document.createElement('li');
        
        // Determine the actual type of this node
        const nodeType = getNodeType(currentNode);
        
        // Create a span for the node text and weight
        const nodeSpan = document.createElement('span');
        nodeSpan.style.display = 'flex';
        nodeSpan.style.alignItems = 'center';
        nodeSpan.style.width = '100%';
        
        // Create a left-aligned container for icon and text
        const leftContainer = document.createElement('span');
        leftContainer.style.display = 'flex';
        leftContainer.style.alignItems = 'center';
        
        // Add icon based on actual node type (check for custom iconLabel first)
        const icon = document.createElement('span');
        icon.className = 'node-icon';
        icon.textContent = getIconForType(nodeType, currentNode);
        leftContainer.appendChild(icon);
        
        const nodeText = document.createElement('span');
        nodeText.textContent = getNodeLabel(currentNode, displayMode);
        
        // Check if this node is an actual root but not in declared roots
        if (rootMismatchInfo && 
            rootMismatchInfo.actualRoots.has(currentNode) && 
            !rootMismatchInfo.declaredRoots.has(currentNode)) {
            nodeText.style.color = 'blue';
            nodeText.style.fontWeight = 'bold';
            nodeText.title = 'This is an actual root (not a child of any node) but is not declared in the roots array';
        }
        
        leftContainer.appendChild(nodeText);
        nodeSpan.appendChild(leftContainer);
        
        // Add weight if present in relationship properties
        if (relationshipProps && relationshipProps.properties) {
            const weightProp = relationshipProps.properties.find(p => p.property === 'xbrl:weight');
            if (weightProp) {
                const weightSpan = document.createElement('span');
                weightSpan.textContent = `[${weightProp.value}]`;
                weightSpan.style.marginLeft = 'auto';
                weightSpan.style.paddingLeft = '10px';
                weightSpan.style.fontWeight = 'bold';
                weightSpan.style.color = '#666';
                nodeSpan.appendChild(weightSpan);
            }
        }
        
        li.appendChild(nodeSpan);
        li.classList.add('node', 'collapsed');
        
        // Check if this node has a self-reference and mark it with error class
        if (selfReferences && selfReferences.has(currentNode)) {
            li.classList.add('self-reference-error');
            li.title = 'Warning: This node has a self-reference (source equals target)';
        }
        
        // Use the correctly identified node type
        li.dataset.type = nodeType;
        
        // For cubes, store the full object as JSON; for other types, store just the name
        const taxonomyData = getTaxonomyData();
        const xbrlModel = getXbrlModel(taxonomyData);
        if (nodeType === 'cube' && xbrlModel && xbrlModel.cubes) {
            const cubeObj = xbrlModel.cubes.find(c => c.name === currentNode);
            if (cubeObj) {
                li.dataset.obj = JSON.stringify(cubeObj);
            } else {
                li.dataset.obj = currentNode;
            }
        } else {
            li.dataset.obj = currentNode;
        }
        
        currentUl.appendChild(li);
        const subUl = document.createElement('ul');
        li.appendChild(subUl);
        
        if (depth < MAX_DEPTH) {
            const children = childrenMap[currentNode] || [];
            children.forEach(child => {
                // Find the relationship for this source-target pair
                const relKey = `${currentNode}|||${child.target}`;
                const rel = relationshipMap[relKey];
                stack.push({ 
                    node: child.target, 
                    parentUl: subUl, 
                    depth: depth + 1,
                    relationshipProps: rel
                });
            });
        }
    }
}

/**
 * Build and display the networks list with filtering
 */
function buildNetworks(filterType, displayMode = 'name') {
    const networksListContainer = document.getElementById('networks-list');
    if (!networksListContainer) return;

    networksListContainer.innerHTML = '';
    const networksUl = document.createElement('ul');

    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (xbrlModel && xbrlModel.networks) {
        console.log('[Networks] Total networks found:', xbrlModel.networks.length);
        console.log('[Networks] Network names:', xbrlModel.networks.map(n => n.name));
        
        // Filter networks by relationship type
        const filteredNetworks = filterType === 'all' 
            ? xbrlModel.networks 
            : xbrlModel.networks.filter(network => network.relationshipTypeName === filterType);

        console.log(`[Networks] Showing ${filteredNetworks.length} networks for filter: ${filterType}`);

        filteredNetworks.forEach(network => {
            console.log('[Networks] Processing network:', network.name, 'roots:', network.roots, 'relationships:', network.relationships?.length);
            
            const li = document.createElement('li');
            
            // Check if network has recursion
            const hasRecursion = hasNetworkRecursion(network);
            
            // Check if network has root mismatch
            const rootMismatchInfo = checkRootMismatch(network);
            
            // Add icon for network (check for custom iconLabel first)
            const icon = document.createElement('span');
            icon.className = 'node-icon';
            icon.textContent = getIconForType('network', network.name);
            li.appendChild(icon);
            
            // Create a span container for the network name and indicators
            const nameSpan = document.createElement('span');
            nameSpan.textContent = getNodeLabel(network.name, displayMode);
            
            // Add recursion and root mismatch indicators
            addNetworkIndicators(nameSpan, network, hasRecursion, rootMismatchInfo, network.name);
            
            li.appendChild(nameSpan);
            li.classList.add('node', 'collapsed');
            li.dataset.type = 'network';
            li.dataset.obj = JSON.stringify(network);
            networksUl.appendChild(li);

            const subUl = document.createElement('ul');
            li.appendChild(subUl);

            // Build tree from roots and relationships
            const { childrenMap, selfReferences } = buildChildrenMap(network.relationships);
            console.log('[Networks] Children map for network', network.name, ':', childrenMap);
            console.log('[Networks] Network roots:', network.roots);
            
            if (network.roots) {
                network.roots.forEach(root => {
                    console.log('[Networks] Building tree for root:', root);
                    buildNetworkTree(subUl, root, childrenMap, network.relationships, selfReferences, rootMismatchInfo, displayMode);
                });
            } else {
                console.warn('[Networks] Network has no roots:', network.name);
            }
        });

        if (filteredNetworks.length === 0) {
            const noNetworksMsg = document.createElement('p');
            noNetworksMsg.textContent = `No networks found for relationship type: ${filterType}`;
            noNetworksMsg.style.padding = '10px';
            noNetworksMsg.style.fontStyle = 'italic';
            noNetworksMsg.style.color = '#888';
            networksListContainer.appendChild(noNetworksMsg);
            return;
        }
    } else {
        console.warn('No networks found in taxonomy data');
    }

    networksListContainer.appendChild(networksUl);

    // Attach node handlers from tree-handlers module
    attachNodeHandlers(networksListContainer);
}

/**
 * Populate the relationship type filter dropdown
 */
function populateRelationshipTypeFilter() {
    const filterSelect = document.getElementById('relationship-type-filter');
    if (!filterSelect) return;

    // Clear existing options except "All"
    filterSelect.innerHTML = '<option value="all">All Relationship Types</option>';

    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.networks) return;

    // Collect unique relationship types
    const relationshipTypes = new Set();
    xbrlModel.networks.forEach(network => {
        if (network.relationshipTypeName) {
            relationshipTypes.add(network.relationshipTypeName);
        }
    });

    // Sort and add to dropdown
    const sortedTypes = Array.from(relationshipTypes).sort();
    sortedTypes.forEach(type => {
        const option = document.createElement('option');
        option.value = type;
        option.textContent = type;
        filterSelect.appendChild(option);
    });

    // Add event listener for filter changes
    filterSelect.onchange = function() {
        const displayMode = document.getElementById('display-mode-filter')?.value || 'name';
        buildNetworks(this.value, displayMode);
    };
    
    // Add event listener for display mode changes
    const displayModeFilter = document.getElementById('display-mode-filter');
    if (displayModeFilter) {
        displayModeFilter.onchange = function() {
            const relationshipType = filterSelect.value || 'all';
            buildNetworks(relationshipType, this.value);
        };
    }
}

/**
 * Initialize the networks tab
 */
export function initNetworks() {
    populateRelationshipTypeFilter();
    buildNetworks('all');
}

// Expose functions for use in other modules
export { buildNetworks, buildNetworkTree, buildChildrenMap, checkRootMismatch };
