// Initialization Module
// Handles page load initialization and default taxonomy loading

import { loadTaxonomy } from './taxonomy-loader.js';
import { initGroupsDisplayModeDropdown } from './groups-builder.js';
import { initAllTabs } from './tab-manager.js';
import { initAllUIHandlers } from './ui-handlers.js';
import { initErrorLabels } from './error-labels.js';

// Track initialization state
let modulesReady = false;
let domReady = false;
let taxonomySelectorInitialized = false; // Guard to prevent duplicate listeners
let pageLoadListenersInitialized = false; // Guard to prevent duplicate page load listeners

/**
 * Try to load the default taxonomy
 * Only proceeds when both modules and DOM are ready
 */
function tryLoadDefaultTaxonomy() {
    if (modulesReady && domReady) {
        const taxonomySelect = document.getElementById('taxonomy-select');
        const defaultPath = taxonomySelect ? taxonomySelect.value : null;
        
        if (defaultPath) {
            console.log('Loading default taxonomy:', defaultPath);
            loadTaxonomy(defaultPath);
        } else {
            console.log('No default taxonomy path found');
        }
    }
}

/**
 * Initialize taxonomy dropdown selector
 * Protected against duplicate initialization
 */
export function initTaxonomySelector() {
    if (taxonomySelectorInitialized) {
        console.log('Taxonomy selector already initialized, skipping');
        return;
    }
    
    const taxonomySelect = document.getElementById('taxonomy-select');
    
    if (!taxonomySelect) {
        console.warn('Taxonomy select element not found');
        return;
    }
    
    taxonomySelect.addEventListener('change', function() {
        const path = this.value;
        if (path) {
            console.log('Loading selected taxonomy:', path);
            loadTaxonomy(path);
        }
    });
    
    taxonomySelectorInitialized = true;
    console.log('Taxonomy selector initialized');
}

/**
 * Handle modules loaded event
 * Protected against duplicate initialization
 */
export function onModulesLoaded() {
    if (modulesReady) {
        console.log('Modules already initialized, skipping');
        return;
    }
    
    console.log('Taxonomy modules ready');
    modulesReady = true;
    
    // Initialize error labels from errors taxonomy
    initErrorLabels().then(() => {
        console.log('Error labels initialized');
    }).catch(err => {
        console.error('Failed to initialize error labels:', err);
    });
    
    // Initialize groups display mode dropdown
    if (window.initGroupsDisplayModeDropdown) {
        window.initGroupsDisplayModeDropdown();
    }
    
    // Initialize all tabs
    initAllTabs();
    
    // Initialize all UI handlers
    initAllUIHandlers();
    
    // Initialize taxonomy selector
    initTaxonomySelector();
    
    // Dispatch custom event to signal initialization is complete
    window.dispatchEvent(new Event('taxonomyViewerReady'));
    
    // Try to load default taxonomy
    tryLoadDefaultTaxonomy();
}

/**
 * Handle DOM loaded event
 */
export function onDOMLoaded() {
    console.log('DOM ready');
    domReady = true;
    
    // Try to load default taxonomy
    tryLoadDefaultTaxonomy();
}

/**
 * Initialize all event listeners for page load
 * Protected against duplicate initialization
 */
export function initPageLoadListeners() {
    if (pageLoadListenersInitialized) {
        console.log('Page load listeners already initialized, skipping');
        return;
    }
    
    // Listen for modules loaded event
    window.addEventListener('taxonomyModulesLoaded', onModulesLoaded);
    
    // Listen for DOM loaded event
    window.addEventListener('load', onDOMLoaded);
    
    pageLoadListenersInitialized = true;
    console.log('Page load listeners initialized');
}

// Auto-initialize when this module loads
initPageLoadListeners();
