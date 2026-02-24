/**
 * Locations Panel Module
 * Displays tree-based visualization showing where an object appears in networks and domains
 */

import { getNodeLabel, getIconForType, getXbrlModel } from '../utils.js';

/**
 * Build a path tree showing only ancestors and direct children of the target node
 * @param {Object} structure - Network or domain object with relationships
 * @param {string} targetQName - The QName to find paths for
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {Object} Tree structure with only relevant paths
 */
function buildPathTree(structure, targetQName, taxonomyData) {
    // Build a full children map
    const childrenMap = new Map();
    const parentsMap = new Map();
    
    if (structure.relationships) {
        structure.relationships.forEach(rel => {
            if (!childrenMap.has(rel.source)) {
                childrenMap.set(rel.source, []);
            }
            childrenMap.get(rel.source).push(rel.target);
            
            if (!parentsMap.has(rel.target)) {
                parentsMap.set(rel.target, []);
            }
            parentsMap.get(rel.target).push(rel.source);
        });
    }
    
    // Find all paths from roots to target
    const roots = structure.roots || (structure.root ? [structure.root] : []);
    const pathsToTarget = [];
    
    function findPaths(current, path) {
        const newPath = [...path, current];
        
        if (current === targetQName) {
            pathsToTarget.push(newPath);
            return;
        }
        
        const children = childrenMap.get(current) || [];
        children.forEach(child => {
            if (!newPath.includes(child)) { // Avoid cycles
                findPaths(child, newPath);
            }
        });
    }
    
    roots.forEach(root => findPaths(root, []));
    
    // Build tree structure with only nodes in paths plus direct children of target
    const relevantNodes = new Set();
    pathsToTarget.forEach(path => path.forEach(node => relevantNodes.add(node)));
    
    // Add direct children of target
    const targetChildren = childrenMap.get(targetQName) || [];
    targetChildren.forEach(child => relevantNodes.add(child));
    
    // Build tree from relevant nodes
    const tree = {
        roots: roots.filter(r => relevantNodes.has(r)),
        relationships: (structure.relationships || []).filter(rel => 
            relevantNodes.has(rel.source) && relevantNodes.has(rel.target)
        )
    };
    
    return { tree, targetChildren };
}

/**
 * Create a visual tree element for a network or domain showing the path to target
 * @param {Object} structure - Network or domain object
 * @param {string} targetQName - The QName being located
 * @param {Object} taxonomyData - The taxonomy data
 * @param {string} type - 'network' or 'domain'
 * @returns {HTMLElement} The tree container
 */
function createLocationTree(structure, targetQName, taxonomyData, type) {
    const { tree, targetChildren } = buildPathTree(structure, targetQName, taxonomyData);
    
    const container = document.createElement('div');
    container.style.marginBottom = '15px';
    container.style.padding = '10px';
    container.style.backgroundColor = '#f8f9fa';
    container.style.border = '1px solid #dee2e6';
    container.style.borderRadius = '4px';
    
    // Header with name and relationship type
    const header = document.createElement('div');
    header.style.marginBottom = '10px';
    header.style.paddingBottom = '8px';
    header.style.borderBottom = '2px solid #007bff';
    
    const title = document.createElement('strong');
    title.textContent = structure.name;
    title.style.fontSize = '14px';
    title.style.color = '#495057';
    header.appendChild(title);
    
    const isSummationNetwork = type === 'network' && structure.relationshipTypeName === 'xbrl:summation-item';
    
    if (type === 'network' && structure.relationshipTypeName) {
        const relType = document.createElement('span');
        relType.textContent = ` (${structure.relationshipTypeName})`;
        relType.style.fontSize = '12px';
        relType.style.color = '#6c757d';
        relType.style.fontStyle = 'italic';
        header.appendChild(relType);
    }
    
    container.appendChild(header);
    
    // Build tree visualization
    const treeContainer = document.createElement('div');
    treeContainer.style.fontFamily = 'Consolas, "Courier New", monospace';
    treeContainer.style.fontSize = '13px';
    treeContainer.style.paddingLeft = '5px';
    treeContainer.style.whiteSpace = 'pre';
    treeContainer.style.overflowX = 'auto';
    
    // Build children map for tree traversal and weight map for summation networks
    const childrenMap = new Map();
    const weightMap = new Map(); // Maps "source->target" to weight
    
    tree.relationships.forEach(rel => {
        if (!childrenMap.has(rel.source)) {
            childrenMap.set(rel.source, []);
        }
        childrenMap.get(rel.source).push(rel.target);
        
        // Store weight for summation networks
        if (isSummationNetwork && rel.properties) {
            const weightProp = rel.properties.find(p => p.property === 'xbrl:weight');
            if (weightProp) {
                const key = `${rel.source}->${rel.target}`;
                weightMap.set(key, parseFloat(weightProp.value));
            }
        }
    });
    
    // Render tree recursively
    function renderNode(nodeName, depth, isLast, prefix, parentName) {
        const nodeDiv = document.createElement('div');
        nodeDiv.style.marginBottom = '2px';
        nodeDiv.style.whiteSpace = 'pre';
        nodeDiv.style.fontFamily = 'Consolas, "Courier New", monospace';
        nodeDiv.style.lineHeight = '1.6';
        
        // Build tree structure with proper spacing
        const connector = isLast ? '└── ' : '├── ';
        const fullIndent = prefix + connector;
        
        // Determine line color based on weight for summation networks
        let lineColor = '#adb5bd'; // Default gray
        if (isSummationNetwork && parentName) {
            const key = `${parentName}->${nodeName}`;
            const weight = weightMap.get(key);
            if (weight !== undefined) {
                if (weight < 0) {
                    lineColor = '#dc3545'; // Red for negative weights
                } else if (weight > 0) {
                    lineColor = '#0056b3'; // Dark blue for positive weights
                }
            }
        }
        
        // Create the full line with proper indentation preserved
        const line = document.createElement('span');
        line.style.color = lineColor;
        line.textContent = fullIndent;
        nodeDiv.appendChild(line);
        
        // Get icon and label
        const nodeType = getNodeTypeForQName(nodeName, taxonomyData);
        const icon = getIconForType(nodeType);
        const label = getNodeLabel(nodeName, taxonomyData);
        
        const iconSpan = document.createElement('span');
        iconSpan.textContent = icon + ' ';
        iconSpan.style.marginRight = '4px';
        nodeDiv.appendChild(iconSpan);
        
        const labelSpan = document.createElement('span');
        labelSpan.textContent = label;
        
        // Highlight the target node
        if (nodeName === targetQName) {
            labelSpan.style.backgroundColor = '#fff3cd';
            labelSpan.style.padding = '2px 6px';
            labelSpan.style.borderRadius = '3px';
            labelSpan.style.fontWeight = 'bold';
            labelSpan.style.color = '#856404';
        } else {
            labelSpan.style.color = '#495057';
        }
        
        nodeDiv.appendChild(labelSpan);
        treeContainer.appendChild(nodeDiv);
        
        // Render children
        const children = childrenMap.get(nodeName) || [];
        children.forEach((child, idx) => {
            const childIsLast = idx === children.length - 1;
            const childPrefix = prefix + (isLast ? '    ' : '│   ');
            renderNode(child, depth + 1, childIsLast, childPrefix, nodeName);
        });
    }
    
    // Render from each root
    tree.roots.forEach((root, idx) => {
        const isLast = idx === tree.roots.length - 1;
        renderNode(root, 0, isLast, '');
    });
    
    container.appendChild(treeContainer);
    
    return container;
}

/**
 * Get the type of a node by QName
 * @param {string} qname - The QName to look up
 * @param {Object} taxonomyData - The taxonomy data
 * @returns {string} The node type
 */
function getNodeTypeForQName(qname, taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) return 'unknown';
    
    const collections = [
        { array: xbrlModel.concepts, type: 'concept' },
        { array: xbrlModel.members, type: 'member' },
        { array: xbrlModel.dimensions, type: 'dimension' },
        { array: xbrlModel.abstracts, type: 'abstract' },
        { array: xbrlModel.entities, type: 'entity' },
        { array: xbrlModel.units, type: 'unit' },
        { array: xbrlModel.domainClasses, type: 'domainClass' }
    ];
    
    for (const { array, type } of collections) {
        if (array && array.find(item => item.name === qname)) {
            return type;
        }
    }
    
    return 'unknown';
}

/**
 * Populate the locations panel with tree-based visualization
 * @param {string} qname - The QName to find locations for
 * @param {Object} taxonomyData - The taxonomy data
 */
export function populateLocationsPanel(qname, taxonomyData) {
    const locationsContent = document.getElementById('locations-content');
    locationsContent.innerHTML = '';
    
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!qname || !xbrlModel) {
        locationsContent.textContent = 'No location data available.';
        return;
    }
    
    const networksWithQName = [];
    const domainsWithQName = [];
    
    // Search networks for this QName
    if (xbrlModel.networks && xbrlModel.networks.length > 0) {
        xbrlModel.networks.forEach(network => {
            let found = false;
            
            // Check if QName is in roots
            if (network.roots && network.roots.includes(qname)) {
                found = true;
            }
            
            // Check if QName appears in relationships
            if (network.relationships && network.relationships.length > 0) {
                network.relationships.forEach(rel => {
                    if (rel.source === qname || rel.target === qname) {
                        found = true;
                    }
                });
            }
            
            if (found) {
                networksWithQName.push(network);
            }
        });
    }
    
    // Search domains for this QName
    if (xbrlModel.domains && xbrlModel.domains.length > 0) {
        xbrlModel.domains.forEach(domain => {
            let found = false;
            
            // Check if QName is the domain class
            if (domain.root === qname) {
                found = true;
            }
            
            // Check if QName appears in relationships
            if (domain.relationships && domain.relationships.length > 0) {
                domain.relationships.forEach(rel => {
                    if (rel.source === qname || rel.target === qname) {
                        found = true;
                    }
                });
            }
            
            if (found) {
                domainsWithQName.push(domain);
            }
        });
    }
    
    // Display Networks section
    if (networksWithQName.length > 0) {
        const networksSection = document.createElement('div');
        networksSection.style.marginBottom = '15px';
        
        // Collapsible header
        const networksHeader = document.createElement('div');
        networksHeader.style.padding = '10px';
        networksHeader.style.backgroundColor = '#28a745';
        networksHeader.style.color = 'white';
        networksHeader.style.cursor = 'pointer';
        networksHeader.style.borderRadius = '4px';
        networksHeader.style.fontWeight = 'bold';
        networksHeader.style.fontSize = '14px';
        networksHeader.style.display = 'flex';
        networksHeader.style.justifyContent = 'space-between';
        networksHeader.style.alignItems = 'center';
        networksHeader.style.userSelect = 'none';
        
        const networksTitle = document.createElement('span');
        networksTitle.textContent = `Networks (${networksWithQName.length})`;
        networksHeader.appendChild(networksTitle);
        
        const toggleIcon = document.createElement('span');
        toggleIcon.textContent = '▼';
        toggleIcon.style.fontSize = '12px';
        toggleIcon.style.transition = 'transform 0.2s';
        networksHeader.appendChild(toggleIcon);
        
        // Content container
        const networksContent = document.createElement('div');
        networksContent.style.marginTop = '10px';
        networksContent.style.display = 'block';
        
        networksWithQName.forEach(network => {
            const tree = createLocationTree(network, qname, taxonomyData, 'network');
            networksContent.appendChild(tree);
        });
        
        // Toggle functionality
        networksHeader.addEventListener('click', () => {
            if (networksContent.style.display === 'none') {
                networksContent.style.display = 'block';
                toggleIcon.style.transform = 'rotate(0deg)';
            } else {
                networksContent.style.display = 'none';
                toggleIcon.style.transform = 'rotate(-90deg)';
            }
        });
        
        networksSection.appendChild(networksHeader);
        networksSection.appendChild(networksContent);
        locationsContent.appendChild(networksSection);
    }
    
    // Display Domains section
    if (domainsWithQName.length > 0) {
        const domainsSection = document.createElement('div');
        domainsSection.style.marginBottom = '15px';
        
        // Collapsible header
        const domainsHeader = document.createElement('div');
        domainsHeader.style.padding = '10px';
        domainsHeader.style.backgroundColor = '#20c997';
        domainsHeader.style.color = 'white';
        domainsHeader.style.cursor = 'pointer';
        domainsHeader.style.borderRadius = '4px';
        domainsHeader.style.fontWeight = 'bold';
        domainsHeader.style.fontSize = '14px';
        domainsHeader.style.display = 'flex';
        domainsHeader.style.justifyContent = 'space-between';
        domainsHeader.style.alignItems = 'center';
        domainsHeader.style.userSelect = 'none';
        
        const domainsTitle = document.createElement('span');
        domainsTitle.textContent = `Domains (${domainsWithQName.length})`;
        domainsHeader.appendChild(domainsTitle);
        
        const toggleIcon = document.createElement('span');
        toggleIcon.textContent = '▼';
        toggleIcon.style.fontSize = '12px';
        toggleIcon.style.transition = 'transform 0.2s';
        domainsHeader.appendChild(toggleIcon);
        
        // Content container
        const domainsContent = document.createElement('div');
        domainsContent.style.marginTop = '10px';
        domainsContent.style.display = 'block';
        
        domainsWithQName.forEach(domain => {
            const tree = createLocationTree(domain, qname, taxonomyData, 'domain');
            domainsContent.appendChild(tree);
        });
        
        // Toggle functionality
        domainsHeader.addEventListener('click', () => {
            if (domainsContent.style.display === 'none') {
                domainsContent.style.display = 'block';
                toggleIcon.style.transform = 'rotate(0deg)';
            } else {
                domainsContent.style.display = 'none';
                toggleIcon.style.transform = 'rotate(-90deg)';
            }
        });
        
        domainsSection.appendChild(domainsHeader);
        domainsSection.appendChild(domainsContent);
        locationsContent.appendChild(domainsSection);
    }
    
    // Show message if no locations found
    if (networksWithQName.length === 0 && domainsWithQName.length === 0) {
        const noLocations = document.createElement('p');
        noLocations.textContent = 'This object does not appear in any networks or domains.';
        noLocations.style.fontStyle = 'italic';
        noLocations.style.color = '#6c757d';
        noLocations.style.padding = '20px';
        locationsContent.appendChild(noLocations);
    }
}
