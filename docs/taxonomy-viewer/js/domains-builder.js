/**
 * Domains Builder Module
 * Handles building and display of the Domains tab, including:
 * - Domain tree rendering
 * - Display mode switching (name vs label)
 * - Recursion detection
 * - Root mismatch detection
 * - Shared utilities with networks
 */

import { getTaxonomyData } from './main.js';
import { getIconForType, getNodeType, getNodeLabel, getXbrlModel } from './utils.js';

/**
 * Helper function to build childrenMap and selfReferences from relationships
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
 * Check if a domain has recursion/cycles
 */
function hasNetworkRecursion(domain) {
    if (!domain.relationships || domain.relationships.length === 0) {
        return false;
    }
    // Build adjacency map
    const childrenMap = {};
    domain.relationships.forEach(rel => {
        if (!childrenMap[rel.source]) childrenMap[rel.source] = [];
        childrenMap[rel.source].push(rel.target);
    });

    // Check each node to see if it can reach itself (cycle detection)
    const allNodes = new Set();
    domain.relationships.forEach(rel => {
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
 * Check root mismatches for domains
 * Returns an object with: { hasMismatch: boolean, actualRoots: Set, declaredRoots: Set }
 */
function checkRootMismatch(domain) {
    // Extract declared root - domains use 'root' string
    const declaredRootsArray = domain.root ? [domain.root] : [];
    
    if (!domain.relationships || domain.relationships.length === 0) {
        return { hasMismatch: false, actualRoots: new Set(), declaredRoots: new Set(declaredRootsArray) };
    }

    // Find all nodes that are targets (children)
    const targetsSet = new Set();
    domain.relationships.forEach(rel => {
        targetsSet.add(rel.target);
    });

    // Find all nodes that are sources
    const sourcesSet = new Set();
    domain.relationships.forEach(rel => {
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
 * Add recursion and root mismatch indicators to a name span
 */
function addNetworkIndicators(nameSpan, obj, hasRecursion, rootMismatchInfo, objName) {
    // Add red dot if recursion detected
    if (hasRecursion) {
        const redDot = document.createElement('span');
        redDot.textContent = ' 🔴';
        redDot.title = 'Warning: This domain contains recursion/cycles';
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
        
        blueDot.title = 'Warning: Declared root does not match actual roots (Click for details)';
        blueDot.style.fontSize = '8px';
        blueDot.style.marginLeft = '5px';
        blueDot.style.cursor = 'pointer';
        
        // Add click handler to show popup
        blueDot.addEventListener('click', function(e) {
            e.stopPropagation();
            // Use legacy showRootMismatchPopup from window if available
            if (typeof window.showRootMismatchPopup === 'function') {
                window.showRootMismatchPopup(e, actualNotDeclared, declaredNotActual, objName);
            }
        });
        
        nameSpan.appendChild(blueDot);
    }
}

/**
 * Build relationship tree for domains
 */
function buildDomainTree(ul, node, childrenMap, relationships, selfReferences, depth, rootMismatchInfo, displayMode = 'name') {
    const MAX_DEPTH = 10;
    const stack = [{ node: node, parentUl: ul, depth: depth, relationshipProps: null }];
    
    // Create a map of relationships by source-target pair for quick lookup
    const relationshipMap = {};
    if (relationships) {
        relationships.forEach(rel => {
            const key = `${rel.source}|||${rel.target}`;
            relationshipMap[key] = rel;
        });
    }
    
    // Sort children alphabetically based on display mode
    const sortedChildrenMap = {};
    Object.keys(childrenMap).forEach(source => {
        sortedChildrenMap[source] = [...childrenMap[source]].sort((a, b) => {
            // Primary sort: by order (descending - higher order first)
            if (a.order !== b.order) {
                return b.order - a.order;
            }
            // Secondary sort: alphabetically by name or label
            const labelA = getNodeLabel(a.target, displayMode);
            const labelB = getNodeLabel(b.target, displayMode);
            return labelA.localeCompare(labelB);
        });
    });
    
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
            nodeText.title = 'This is an actual root (not a child of any node) but is not declared in the root';
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
            const children = sortedChildrenMap[currentNode] || [];
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
 * Build and display the domains list
 */
export function buildDomains(displayMode = 'name') {
    console.log('[Domains Builder] Building domains with display mode:', displayMode);
    
    const domainsListContainer = document.getElementById('domains-list');
    if (!domainsListContainer) {
        console.warn('[Domains Builder] domains-list container not found');
        return;
    }

    domainsListContainer.innerHTML = '';
    const domainsUl = document.createElement('ul');

    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (xbrlModel && xbrlModel.domains) {
        console.log('[Domains Builder] Domains found:', xbrlModel.domains.length);
        
        // Sort domains alphabetically based on display mode
        const sortedDomains = [...xbrlModel.domains].sort((a, b) => {
            const labelA = getNodeLabel(a.name, displayMode) || a.name || '';
            const labelB = getNodeLabel(b.name, displayMode) || b.name || '';
            return labelA.localeCompare(labelB);
        });
        
        sortedDomains.forEach(domain => {
            const li = document.createElement('li');
            
            // Check if domain has recursion
            const hasRecursion = hasNetworkRecursion(domain);
            
            // Check if domain has root mismatch
            const rootMismatchInfo = checkRootMismatch(domain);
            
            // Add icon for domain (check for custom iconLabel first)
            const icon = document.createElement('span');
            icon.className = 'node-icon';
            icon.textContent = getIconForType('domain', domain.name);
            li.appendChild(icon);
            
            // Create a span container for the domain name and indicators
            const nameSpan = document.createElement('span');
            nameSpan.textContent = getNodeLabel(domain.name, displayMode);
            
            // Add recursion and root mismatch indicators
            addNetworkIndicators(nameSpan, domain, hasRecursion, rootMismatchInfo, domain.name);
            
            li.appendChild(nameSpan);
            li.classList.add('node', 'collapsed');
            li.dataset.type = 'domain';
            li.dataset.obj = JSON.stringify(domain);
            domainsUl.appendChild(li);

            const subUl = document.createElement('ul');
            li.appendChild(subUl);

            // Build tree from root and relationships
            const { childrenMap, selfReferences } = buildChildrenMap(domain.relationships);
            if (domain.root) {
                buildDomainTree(subUl, domain.root, childrenMap, domain.relationships, selfReferences, 0, rootMismatchInfo, displayMode);
            }
        });
    } else {
        console.warn('[Domains Builder] No domains found in taxonomy data');
    }

    domainsListContainer.appendChild(domainsUl);
    
    // Use legacy attachNodeHandlers from window if available
    if (typeof window.attachNodeHandlers === 'function') {
        window.attachNodeHandlers(domainsUl);
    } else {
        console.warn('[Domains Builder] attachNodeHandlers not available');
    }
}

/**
 * Setup the domain display mode filter dropdown
 */
export function setupDomainDisplayModeFilter() {
    console.log('[Domains Builder] Setting up display mode filter');
    
    const domainDisplayModeFilter = document.getElementById('domain-display-mode-filter');
    if (domainDisplayModeFilter) {
        domainDisplayModeFilter.onchange = function() {
            console.log('[Domains Builder] Display mode changed to:', this.value);
            buildDomains(this.value);
        };
    } else {
        console.warn('[Domains Builder] domain-display-mode-filter not found');
    }
}

/**
 * Initialize domains - sets up filter and builds initial view
 */
export function initDomains() {
    console.log('[Domains Builder] Initializing domains');
    setupDomainDisplayModeFilter();
    buildDomains('name');
}
