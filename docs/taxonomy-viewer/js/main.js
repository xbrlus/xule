// Main entry point - imports all modules
import { taxonomyData, setTaxonomyData, MAX_DEPTH } from './state.js';
import { getIconForType, getNodeType, getNodeLabel } from './utils.js';
import { 
    attachNodeHandlers, 
    showContextMenu, 
    expandAllNodes, 
    collapseAllNodes, 
    showRootMismatchPopup,
    setShowDetailsFunction 
} from './tree-handlers.js';
import { buildGroups, setGroupsDisplayMode, initGroupsDisplayModeDropdown } from './groups-builder.js';
import { buildNetworks, initNetworks } from './networks-builder.js';
import { buildComponentsList, buildAllComponents } from './components-builder.js';
import { buildDomains, setupDomainDisplayModeFilter, initDomains } from './domains-builder.js';
import { buildCubes, buildCubeGrid, initCubes } from './cubes-builder.js';
import { buildCubeFactView } from './cube-fact-view.js';
import { loadTaxonomy } from './taxonomy-loader.js';
import { buildTree, buildTaxonomyInfo } from './taxonomy-builder.js';
import { showDetails, showCubeDetails, showGroupDetails, manageTabVisibility } from './details-panel.js';
import { buildFactsList } from './facts-builder.js';
import { showFactGrids } from './fact-grid.js';
import { processFactSources, buildFactSourcesList } from './factSources-builder.js';
import { buildTableTemplates, buildDataTables, setupLayoutDisplayModeFilters, initLayout } from './layout-builder.js';
import { buildImportPathsView, buildFinalTaxonomyView, populateTaxonomyPropertiesTab } from './taxonomy-imports.js';
import { initAllTabs } from './tab-manager.js';
import { initAllUIHandlers } from './ui-handlers.js';
import './init.js';  // Import initialization module (auto-runs)

// Export getTaxonomyData function for use by other modules
export function getTaxonomyData() {
    return taxonomyData;
}

// Register showDetails function with tree-handlers
setShowDetailsFunction(showDetails);

// For now, we'll keep the rest of the code here and gradually move it to modules
// This allows the application to keep working while we refactor

// COMPLETED MODULES:
// ✓ state.js (shared state management)
// ✓ utils.js (icon, type, and label utilities)
// ✓ tree-handlers.js (node interaction handlers - COMPLETE!)
// ✓ groups-builder.js (Groups tab)
// ✓ networks-builder.js (Networks tab with filtering and indicators)
// ✓ components-builder.js (Component lists for concepts, dimensions, etc.)
// ✓ domains-builder.js (Domains tab with recursion and root mismatch detection)
// ✓ cubes-builder.js (Cubes tab with list and grid visualization)
// ✓ taxonomy-loader.js (Taxonomy loading, merging imports and spec-taxonomies)
// ✓ taxonomy-builder.js (buildTree, buildTaxonomyInfo, validation)
// ✓ details-panel.js (showDetails, showCubeDetails, panel management)
// ✓ facts-builder.js (Facts tab)
// ✓ fact-grid.js (Fact grid visualization)
// ✓ tab-manager.js (Tab switching for all tabs)
// ✓ ui-handlers.js (Resizable panel and UI interactions)
// ✓ init.js (Page load initialization and default taxonomy loading)

// Export functions globally for legacy compatibility
window.setTaxonomyData = setTaxonomyData;  // Export state setter for legacy code
window.getTaxonomyData = () => taxonomyData;  // Export taxonomy data getter for modules
window.attachNodeHandlers = attachNodeHandlers;  // Export tree handlers
window.showContextMenu = showContextMenu;  // Export context menu
window.expandAllNodes = expandAllNodes;  // Export expand all
window.collapseAllNodes = collapseAllNodes;  // Export collapse all
window.showRootMismatchPopup = showRootMismatchPopup;  // Export root mismatch popup
window.buildGroups = buildGroups;
window.buildGroupsModule = buildGroups;  // Also export with Module suffix for legacy code
window.setGroupsDisplayMode = setGroupsDisplayMode;  // Export groups display mode setter
window.initGroupsDisplayModeDropdown = initGroupsDisplayModeDropdown;  // Export groups dropdown initializer
window.buildNetworks = buildNetworks;
window.initNetworks = initNetworks;
window.buildComponentsList = buildComponentsList;  // Export components builder
window.buildAllComponents = buildAllComponents;  // Export batch component builder
window.buildDomains = buildDomains;  // Export domains builder
window.setupDomainDisplayModeFilter = setupDomainDisplayModeFilter;  // Export domain filter setup
window.initDomains = initDomains;  // Export domains initializer
window.buildCubes = buildCubes;  // Export cubes builder
window.buildCubeGrid = buildCubeGrid;  // Export cube grid builder
window.buildCubeFactView = buildCubeFactView;  // Export cube fact view builder
window.initCubes = initCubes;  // Export cubes initializer
window.buildFactsList = buildFactsList;  // Export facts builder
window.showFactGrids = showFactGrids;  // Export fact grid viewer
window.processFactSources = processFactSources;  // Export factSources processor
window.buildFactSourcesList = buildFactSourcesList;  // Export factSources list builder
window.buildTableTemplates = buildTableTemplates;  // Export table templates builder
window.buildDataTables = buildDataTables;  // Export data tables builder
window.setupLayoutDisplayModeFilters = setupLayoutDisplayModeFilters;  // Export layout display mode filters
window.initLayout = initLayout;  // Export layout initializer
window.loadTaxonomy = loadTaxonomy;  // Export taxonomy loader
window.buildTree = buildTree;  // Export tree builder
window.buildTaxonomyInfo = buildTaxonomyInfo;  // Export taxonomy info builder
window.showDetails = showDetails;  // Export details panel function
window.showCubeDetails = showCubeDetails;  // Export cube details panel function
window.showGroupDetails = showGroupDetails;  // Export group details panel function
window.manageTabVisibility = manageTabVisibility;  // Export tab visibility manager
window.buildImportPathsView = buildImportPathsView;  // Export taxonomy imports viewer
window.buildFinalTaxonomyView = buildFinalTaxonomyView;  // Export final taxonomy viewer
window.populateTaxonomyPropertiesTab = populateTaxonomyPropertiesTab;  // Export taxonomy properties tab
window.initAllTabs = initAllTabs;  // Export tab manager
window.initAllUIHandlers = initAllUIHandlers;  // Export UI handlers

console.log('Taxonomy viewer modules loaded');
console.log('Exported functions:', {
    setTaxonomyData: typeof window.setTaxonomyData,
    getTaxonomyData: typeof window.getTaxonomyData,
    attachNodeHandlers: typeof window.attachNodeHandlers,
    showContextMenu: typeof window.showContextMenu,
    expandAllNodes: typeof window.expandAllNodes,
    collapseAllNodes: typeof window.collapseAllNodes,
    showRootMismatchPopup: typeof window.showRootMismatchPopup,
    buildGroups: typeof window.buildGroups,
    buildGroupsModule: typeof window.buildGroupsModule,
    setGroupsDisplayMode: typeof window.setGroupsDisplayMode,
    initGroupsDisplayModeDropdown: typeof window.initGroupsDisplayModeDropdown,
    buildNetworks: typeof window.buildNetworks,
    initNetworks: typeof window.initNetworks,
    buildComponentsList: typeof window.buildComponentsList,
    buildAllComponents: typeof window.buildAllComponents,
    buildDomains: typeof window.buildDomains,
    setupDomainDisplayModeFilter: typeof window.setupDomainDisplayModeFilter,
    initDomains: typeof window.initDomains,
    buildCubes: typeof window.buildCubes,
    buildCubeGrid: typeof window.buildCubeGrid,
    initCubes: typeof window.initCubes,
    buildFactsList: typeof window.buildFactsList,
    showFactGrids: typeof window.showFactGrids,
    buildTableTemplates: typeof window.buildTableTemplates,
    buildDataTables: typeof window.buildDataTables,
    setupLayoutDisplayModeFilters: typeof window.setupLayoutDisplayModeFilters,
    initLayout: typeof window.initLayout,
    loadTaxonomy: typeof window.loadTaxonomy,
    buildTree: typeof window.buildTree,
    buildTaxonomyInfo: typeof window.buildTaxonomyInfo,
    showDetails: typeof window.showDetails,
    showCubeDetails: typeof window.showCubeDetails,
    showGroupDetails: typeof window.showGroupDetails,
    initAllTabs: typeof window.initAllTabs,
    initAllUIHandlers: typeof window.initAllUIHandlers,
});

// Dispatch event to signal that modules are ready
// Note: init.js will handle the taxonomyModulesLoaded event
window.dispatchEvent(new CustomEvent('taxonomyModulesLoaded'));
