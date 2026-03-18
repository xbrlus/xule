// Shared application state - connects to global window.taxonomyData
export let taxonomyData = null;
export const MAX_DEPTH = 10;
export let contextMenu = null;

// Store references to all registered cache-clearing functions
// Using an array so multiple modules can register without clobbering each other.
const _cacheClearFns = [];

export function registerCacheClearFunction(fn) {
    _cacheClearFns.push(fn);
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
    
    // OPTIMIZATION: Clear all registered caches when taxonomy changes
    _cacheClearFns.forEach(fn => fn());
}

export function setContextMenu(menu) {
    contextMenu = menu;
}

// Create a getter that always returns the current global taxonomyData
export function getTaxonomyData() {
    return window.taxonomyData || taxonomyData;
}
