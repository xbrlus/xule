// Groups Builder Module
import { getTaxonomyData } from './state.js';
import { getIconForType, getXbrlModel } from './utils.js';
import { attachNodeHandlers } from './tree-handlers.js';

// Display mode state (name or label)
let groupsDisplayMode = 'name';

/**
 * Get the display text for a group based on current display mode
 */
function getGroupDisplayText(group, taxonomyData) {
    if (groupsDisplayMode === 'label') {
        // Look up labels in the taxonomy.labels array
        const xbrlModel = getXbrlModel(taxonomyData);
        if (xbrlModel?.labels) {
            // Find the standard xbrl:label for this group in English
            const label = xbrlModel.labels.find(l => 
                l.relatedName === group.name && 
                (l.labelType === 'xbrl:label' || !l.labelType) &&
                l.language && l.language.startsWith('en')
            );
            if (label && label.value) {
                return label.value;
            }
        }
        // Fallback to name if no label found
        return group.name;
    }
    // Default to name
    return group.name;
}

/**
 * Build a hierarchical tree structure from groupTree relationships
 */
function buildGroupTree(groups, groupTree, taxonomyData) {
    const groupsMap = new Map();
    groups.forEach(group => {
        groupsMap.set(group.name, group);
    });

    // Build parent-child relationships from groupTree
    const childrenMap = new Map();
    const allTargets = new Set();
    
    // Initialize childrenMap for all groups
    groups.forEach(group => {
        childrenMap.set(group.name, []);
    });
    
    // Add taxonomy as a potential source
    const xbrlModel = getXbrlModel(taxonomyData);
    const taxonomyName = xbrlModel?.name;
    childrenMap.set(taxonomyName, []);

    // Process relationships
    groupTree.relationships.forEach(rel => {
        const source = rel.source;
        const target = rel.target;
        allTargets.add(target);
        
        if (!childrenMap.has(source)) {
            childrenMap.set(source, []);
        }
        childrenMap.get(source).push({ target, order: rel.order || 0 });
    });

    // Sort children by order
    childrenMap.forEach((children, source) => {
        children.sort((a, b) => a.order - b.order);
    });

    // Find root nodes (sources that are not targets, or taxonomy itself)
    const rootSources = new Set();
    groupTree.relationships.forEach(rel => {
        if (!allTargets.has(rel.source)) {
            rootSources.add(rel.source);
        }
    });

    // Build the tree recursively
    function buildNode(nodeName, isRoot = false) {
        const li = document.createElement('li');
        
        // Check if this is the taxonomy node
        const isTaxonomy = nodeName === taxonomyName;
        const group = groupsMap.get(nodeName);
        
        // Add icon
        const icon = document.createElement('span');
        icon.className = 'node-icon';
        if (isTaxonomy) {
            icon.textContent = getIconForType('taxonomy', nodeName);
        } else {
            icon.textContent = getIconForType('group', nodeName);
        }
        li.appendChild(icon);
        
        // Add name
        const nameSpan = document.createElement('span');
        if (isTaxonomy) {
            nameSpan.textContent = nodeName;
        } else if (group) {
            nameSpan.textContent = getGroupDisplayText(group, taxonomyData);
        } else {
            nameSpan.textContent = nodeName;
        }
        li.appendChild(nameSpan);
        
        li.classList.add('node');
        if (isTaxonomy) {
            li.dataset.type = 'taxonomy';
            li.dataset.obj = JSON.stringify({ name: taxonomyName });
        } else {
            li.dataset.type = 'group';
            li.dataset.obj = JSON.stringify(group || { name: nodeName });
        }
        
        // Add children if any
        const children = childrenMap.get(nodeName) || [];
        if (children.length > 0) {
            li.classList.add('collapsed');
            const childUl = document.createElement('ul');
            children.forEach(child => {
                childUl.appendChild(buildNode(child.target));
            });
            li.appendChild(childUl);
        }
        
        return li;
    }

    // Build tree from root sources
    const ul = document.createElement('ul');
    rootSources.forEach(rootSource => {
        ul.appendChild(buildNode(rootSource, true));
    });

    return ul;
}

/**
 * Get the label for a group (for sorting purposes)
 */
function getGroupLabel(group, taxonomyData) {
    const xbrlModel = getXbrlModel(taxonomyData);
    if (xbrlModel?.labels) {
        // Find the standard xbrl:label for this group in English
        const label = xbrlModel.labels.find(l => 
            l.relatedName === group.name && 
            (l.labelType === 'xbrl:label' || !l.labelType) &&
            l.language && l.language.startsWith('en')
        );
        if (label && label.value) {
            return label.value;
        }
    }
    return null;
}

/**
 * Build a flat sorted list of groups
 */
function buildGroupList(groups, taxonomyData) {
    const ul = document.createElement('ul');
    
    // Sort groups: first by label (if exists) alphabetically, then by name
    // Groups with labels come before groups without labels
    const sortedGroups = [...groups].sort((a, b) => {
        const labelA = getGroupLabel(a, taxonomyData);
        const labelB = getGroupLabel(b, taxonomyData);
        
        // If both have labels, sort alphabetically by label
        if (labelA && labelB) {
            return labelA.localeCompare(labelB);
        }
        
        // If only a has a label, it comes first
        if (labelA && !labelB) {
            return -1;
        }
        
        // If only b has a label, it comes first
        if (!labelA && labelB) {
            return 1;
        }
        
        // If neither has a label, sort by element name
        return a.name.localeCompare(b.name);
    });
    
    sortedGroups.forEach(group => {
        const li = document.createElement('li');
        
        // Add icon for group (check for custom iconLabel first)
        const icon = document.createElement('span');
        icon.className = 'node-icon';
        icon.textContent = getIconForType('group', group.name);
        li.appendChild(icon);
        
        const nameSpan = document.createElement('span');
        nameSpan.textContent = getGroupDisplayText(group, taxonomyData);
        li.appendChild(nameSpan);
        
        li.classList.add('node');
        li.dataset.type = 'group';
        li.dataset.obj = JSON.stringify(group);
        ul.appendChild(li);
    });
    
    return ul;
}

/**
 * Build and display the groups list or tree
 */
export function buildGroups() {
    console.log('[Groups Builder] buildGroups called');
    const taxonomyData = getTaxonomyData();
    console.log('[Groups Builder] taxonomyData:', taxonomyData);
    const groupsContentContainer = document.getElementById('groups-content');
    console.log('[Groups Builder] groupsContentContainer:', groupsContentContainer);
    if (!groupsContentContainer) {
        console.warn('[Groups Builder] groups-content container not found!');
        return;
    }

    groupsContentContainer.innerHTML = '';

    const xbrlModel = getXbrlModel(taxonomyData);
    if (xbrlModel?.groups) {
        console.log('[Groups Builder] Groups found:', xbrlModel.groups.length);
        
        let groupsUl;
        
        // Check if groupTree exists
        if (xbrlModel.groupTree && xbrlModel.groupTree.relationships) {
            console.log('[Groups Builder] Building group tree structure');
            groupsUl = buildGroupTree(
                xbrlModel.groups,
                xbrlModel.groupTree,
                taxonomyData
            );
        } else {
            console.log('[Groups Builder] Building flat group list');
            groupsUl = buildGroupList(xbrlModel.groups, taxonomyData);
        }
        
        groupsContentContainer.appendChild(groupsUl);
        
        // Attach node handlers from tree-handlers module
        attachNodeHandlers(groupsUl);
    } else {
        console.warn('[Groups Builder] No groups found in taxonomy data');
        console.warn('[Groups Builder] taxonomyData structure:', {
            hasTaxonomyData: !!taxonomyData,
            hasXbrlModel: !!xbrlModel,
            hasGroups: !!(xbrlModel?.groups)
        });
    }
}

/**
 * Set the display mode for groups
 */
export function setGroupsDisplayMode(mode) {
    if (mode === 'name' || mode === 'label') {
        groupsDisplayMode = mode;
        buildGroups(); // Rebuild to apply new display mode
    }
}

/**
 * Initialize groups display mode dropdown
 */
export function initGroupsDisplayModeDropdown() {
    const dropdown = document.getElementById('groups-display-mode');
    if (dropdown) {
        dropdown.addEventListener('change', (e) => {
            setGroupsDisplayMode(e.target.value);
        });
        console.log('[Groups Builder] Display mode dropdown initialized');
    } else {
        console.warn('[Groups Builder] groups-display-mode dropdown not found');
    }
}
