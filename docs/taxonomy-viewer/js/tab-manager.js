// Tab Manager Module
// Handles all tab switching functionality for the taxonomy viewer

// Track if taxonomy details have been built to avoid rebuilding
let taxonomyDetailsBuilt = false;
let currentlyDisplayedObject = null;
let currentlyDisplayedType = null; // Track the type of object currently displayed

/**
 * Initialize main tab switching (Model, Groups, Networks, etc.)
 */
export function initMainTabs() {
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab content
            // Special case for model tab which uses 'taxonomy-info' instead of 'taxonomy-tree'
            const contentId = tabName === 'taxonomy' ? 'taxonomy-info' : tabName + '-tree';
            const contentElement = document.getElementById(contentId);
            if (contentElement) {
                contentElement.classList.add('active');
            }
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // If clicking on model tab, show taxonomy details in right panel
            if (tabName === 'taxonomy' && window.showDetails && window.getTaxonomyData) {
                const taxonomyData = window.getTaxonomyData();
                if (taxonomyData && taxonomyData.xbrlModel) {
                    // Always ensure the details tabs are visible for Model tab
                    const detailsTabs = document.getElementById('details-tabs');
                    if (detailsTabs) {
                        detailsTabs.style.display = 'flex';
                    }
                    
                    // Ensure proper tab visibility for taxonomy context
                    if (window.manageTabVisibility) {
                        window.manageTabVisibility('taxonomy');
                    }
                    
                    // Always activate the Properties tab when returning to Model tab
                    document.querySelectorAll('.details-tab-button').forEach(btn => {
                        btn.classList.remove('active');
                        if (btn.dataset.detailsTab === 'properties') {
                            btn.classList.add('active');
                        }
                    });
                    document.querySelectorAll('.details-tab-content').forEach(content => {
                        content.classList.remove('active');
                    });
                    const propertiesTab = document.getElementById('properties-tab');
                    if (propertiesTab) {
                        propertiesTab.classList.add('active');
                    }
                    
                    // Show taxonomy details if:
                    // 1. Never built before, OR
                    // 2. Different taxonomy object, OR
                    // 3. Currently displaying a different type of object (not taxonomy)
                    if (!taxonomyDetailsBuilt || 
                        currentlyDisplayedObject !== taxonomyData.xbrlModel ||
                        currentlyDisplayedType !== 'taxonomy') {
                        window.showDetails(taxonomyData.xbrlModel, 'taxonomy');
                        taxonomyDetailsBuilt = true;
                        currentlyDisplayedObject = taxonomyData.xbrlModel;
                        currentlyDisplayedType = 'taxonomy';
                    }
                }
            }
        });
    });
    
    console.log('Main tabs initialized');
}

/**
 * Reset taxonomy details cache (call when loading a new taxonomy)
 */
export function resetTaxonomyDetailsCache() {
    taxonomyDetailsBuilt = false;
    currentlyDisplayedObject = null;
    currentlyDisplayedType = null;
}

/**
 * Mark that a non-taxonomy object is being displayed
 * This ensures taxonomy details will be reshown when returning to model tab
 * @param {string} type - The type of object being displayed
 */
export function setCurrentDisplayedObject(type) {
    currentlyDisplayedType = type;
}

/**
 * Initialize details panel tab switching (Properties, Grid View)
 */
export function initDetailsTabs() {
    document.querySelectorAll('.details-tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-details-tab');
            
            // Hide all tab contents
            document.querySelectorAll('.details-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all buttons
            document.querySelectorAll('.details-tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab content
            const contentId = tabName + '-tab';
            const contentElement = document.getElementById(contentId);
            if (contentElement) {
                contentElement.classList.add('active');
            }
            
            // Add active class to clicked button
            this.classList.add('active');
        });
    });
    
    console.log('Details tabs initialized');
}

/**
 * Initialize component sub-tabs (Concepts, Dimensions, etc.)
 */
export function initComponentTabs() {
    document.querySelectorAll('.component-tab-button').forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.getAttribute('data-component-tab');
            
            // Hide all component tab contents
            document.querySelectorAll('.component-tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Remove active class from all component tab buttons
            document.querySelectorAll('.component-tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected component tab content
            const contentId = tabName + '-list';
            const contentElement = document.getElementById(contentId);
            if (contentElement) {
                contentElement.classList.add('active');
            }
            
            // Add active class to clicked button
            this.classList.add('active');
        });
    });
    
    console.log('Component tabs initialized');
}

/**
 * Programmatically switch to a main tab
 * @param {string} tabName - The tab to switch to (e.g., 'components', 'cubes', 'networks')
 */
export function switchToMainTab(tabName) {
    // Find the tab button
    const button = document.querySelector(`.tab-button[data-tab="${tabName}"]`);
    if (button) {
        button.click();
    }
}

/**
 * Programmatically switch to a component sub-tab
 * @param {string} componentName - The component tab to switch to (e.g., 'concepts', 'dimensions', 'referenceTypes')
 */
export function switchToComponentTab(componentName) {
    // First switch to components main tab
    switchToMainTab('components');
    
    // Then switch to the specific component sub-tab
    setTimeout(() => {
        const button = document.querySelector(`.component-tab-button[data-component-tab="${componentName}"]`);
        if (button) {
            button.click();
        }
    }, 50); // Small delay to ensure components tab is visible
}

/**
 * Programmatically switch to a fact component sub-tab (under facts main tab)
 * @param {string} componentName - The component tab to switch to (e.g., 'factSources', 'tableTemplates')
 */
export function switchToFactComponentTab(componentName) {
    // The facts main tab should already be active
    // Just switch to the specific component sub-tab
    const button = document.querySelector(`.component-tab-button[data-component-tab="${componentName}"]`);
    if (button) {
        button.click();
    }
}

/**
 * Highlight an item in the tree by its QName
 * @param {string} qname - The QName of the item to highlight
 */
export function highlightItemInTree(qname) {
    // Remove existing highlights
    document.querySelectorAll('.tree-item.highlighted').forEach(item => {
        item.classList.remove('highlighted');
        item.style.backgroundColor = '';
    });
    
    // Find and highlight the item
    const treeItems = document.querySelectorAll('.tree-item');
    for (const item of treeItems) {
        const itemQName = item.getAttribute('data-qname') || item.textContent.trim().split(' ')[0];
        if (itemQName === qname) {
            item.classList.add('highlighted');
            item.style.backgroundColor = '#fff3cd';
            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            break;
        }
    }
}

/**
 * Programmatically switch to a types sub-tab
 * @param {string} typeName - The type tab to switch to (e.g., 'propertyTypes', 'dataTypes')
 */
export function switchToTypesTab(typeName) {
    // First switch to types main tab
    switchToMainTab('types');
    
    // Then switch to the specific type sub-tab
    setTimeout(() => {
        const button = document.querySelector(`.component-tab-button[data-component-tab="${typeName}"]`);
        if (button) {
            button.click();
        }
    }, 50); // Small delay to ensure types tab is visible
}

/**
 * Navigate to the appropriate tab and highlight an object based on its type
 * @param {string} type - The object type (e.g., 'concept', 'dimension', 'referenceType')
 * @param {string} qname - The QName of the object
 */
export function navigateToObject(type, qname) {
    const typeToTabMapping = {
        'concept': 'concepts',
        'abstract': 'abstracts',
        'member': 'members',
        'dimension': 'dimensions',
        'domain': 'domains',
        'domainClass': 'domainClasses',
        'cube': 'cubes',
        'cubeType': 'cubeTypes',
        'network': 'networks',
        'group': 'groups',
        'dataType': 'dataTypes',
        'propertyType': 'propertyTypes',
        'labelType': 'labelTypes',
        'referenceType': 'referenceTypes',
        'relationshipType': 'relationshipTypes',
        'unit': 'units',
        'entity': 'entities',
        'fact': 'facts',
        'factSource': 'factSources',
        'factMap': 'tableTemplates',
        'transform': 'transforms',
        'reference': 'references'
    };
    
    const tabName = typeToTabMapping[type];
    
    if (tabName) {
        // Main tabs
        if (tabName === 'networks') {
            switchToMainTab('networks');
        } else if (tabName === 'groups') {
            switchToMainTab('groups');
        } else if (tabName === 'facts') {
            switchToMainTab('facts');
        } else if (tabName === 'factSources') {
            // Switch to facts main tab, then to factSources component tab
            switchToMainTab('facts');
            setTimeout(() => switchToFactComponentTab('factSources'), 100);
        } else if (tabName === 'tableTemplates') {
            // Switch to facts main tab, then to tableTemplates component tab
            switchToMainTab('facts');
            setTimeout(() => switchToFactComponentTab('tableTemplates'), 100);
        } else if (tabName === 'domains') {
            switchToMainTab('domains');
        }
        // Types tabs (under types main tab)
        else if (['propertyTypes', 'dataTypes', 'cubeTypes', 'labelTypes', 'referenceTypes', 'relationshipTypes'].includes(tabName)) {
            switchToTypesTab(tabName);
        }
        // Components tabs (under components main tab)
        else {
            switchToComponentTab(tabName);
        }
        
        // Highlight the item after switching tabs
        setTimeout(() => {
            highlightItemInTree(qname);
        }, 150);
    }
}

/**
 * Initialize all tab switching functionality
 */
export function initAllTabs() {
    initMainTabs();
    initDetailsTabs();
    initComponentTabs();
    console.log('All tabs initialized');
}
