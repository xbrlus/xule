// Initialization Module
// Handles page load initialization and default taxonomy loading

import { loadTaxonomy, loadTaxonomyFromContent } from './taxonomy-loader.js';
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
 * Initialize the "Open File" button to load a taxonomy from the local file system.
 */
export function initFileOpenButton() {
    const btn = document.getElementById('open-file-btn');
    const fileInput = document.getElementById('taxonomy-file-input');

    if (!btn || !fileInput) {
        console.warn('File open button or file input not found');
        return;
    }

    btn.addEventListener('click', () => {
        fileInput.value = ''; // Reset so re-selecting the same file triggers change
        fileInput.click();
    });

    fileInput.addEventListener('change', () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const taxonomyData = JSON.parse(event.target.result);
                console.log('Loaded taxonomy from local file:', file.name);
                loadTaxonomyFromContent(taxonomyData, file.name);
            } catch (err) {
                console.error('Failed to parse taxonomy file:', err);
                alert(`Failed to parse "${file.name}" as JSON: ${err.message}`);
            }
        };
        reader.readAsText(file);
    });

    console.log('File open button initialized');
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

    // Initialize local file open button
    initFileOpenButton();
    
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
