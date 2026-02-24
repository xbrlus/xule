// Shared application state - connects to global window.taxonomyData
export let taxonomyData = null;
export const MAX_DEPTH = 10;
export let contextMenu = null;

// Store reference to cache clearing function (to avoid circular imports)
let clearCacheFn = null;

export function registerCacheClearFunction(fn) {
    clearCacheFn = fn;
}

// Initialize by getting reference to global taxonomyData
if (typeof window !== 'undefined') {
    // This will be set when the main taxonomy-viewer.js loads
    Object.defineProperty(window, 'taxonomyDataProxy', {
        get() {
            return window.taxonomyData;
        },
        set(value) {
            window.taxonomyData = value;
            taxonomyData = value;
        }
    });
}

export function setTaxonomyData(data) {
    taxonomyData = data;
    if (typeof window !== 'undefined') {
        window.taxonomyData = data;
    }
    
    // OPTIMIZATION: Clear icon label cache when taxonomy changes
    if (clearCacheFn) {
        clearCacheFn();
    }
}

export function setContextMenu(menu) {
    contextMenu = menu;
}

// Create a getter that always returns the current global taxonomyData
export function getTaxonomyData() {
    return window.taxonomyData || taxonomyData;
}
