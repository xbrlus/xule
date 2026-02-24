/**
 * Tab Management Module
 * Handles tab visibility and panel sizing based on object context
 */

/**
 * Manage tab visibility based on context
 * @param {string} context - 'cube', 'group', 'tableTemplate', 'dataTable', 'fact', or 'default'
 */
export function manageTabVisibility(context) {
    console.log('[manageTabVisibility] Context:', context);
    const propertiesTab = document.querySelector('[data-details-tab="properties"]');
    const contentsTab = document.querySelector('[data-details-tab="contents"]');
    const gridTab = document.querySelector('[data-details-tab="grid"]');
    const factViewTab = document.querySelector('[data-details-tab="fact-view"]');
    const templateViewTab = document.querySelector('[data-details-tab="templateView"]');
    const dataTableViewTab = document.querySelector('[data-details-tab="dataTableView"]');
    const markdownPreviewTab = document.querySelector('[data-details-tab="markdown-preview"]');
    const importPathsTab = document.querySelector('[data-details-tab="import-paths"]');
    const finalTaxonomyTab = document.querySelector('[data-details-tab="final-taxonomy"]');
    const jsonViewTab = document.querySelector('[data-details-tab="json-view"]');
    
    console.log('[manageTabVisibility] Found tabs:', {
        propertiesTab: !!propertiesTab,
        contentsTab: !!contentsTab,
        gridTab: !!gridTab,
        factViewTab: !!factViewTab,
        templateViewTab: !!templateViewTab,
        dataTableViewTab: !!dataTableViewTab,
        markdownPreviewTab: !!markdownPreviewTab,
        importPathsTab: !!importPathsTab,
        finalTaxonomyTab: !!finalTaxonomyTab,
        jsonViewTab: !!jsonViewTab
    });
    
    // Hide all optional tabs first
    if (contentsTab) contentsTab.style.display = 'none';
    if (templateViewTab) templateViewTab.style.display = 'none';
    if (dataTableViewTab) dataTableViewTab.style.display = 'none';
    if (gridTab) gridTab.style.display = 'none';
    if (factViewTab) factViewTab.style.display = 'none';
    if (markdownPreviewTab) markdownPreviewTab.style.display = 'none';
    if (importPathsTab) importPathsTab.style.display = 'none';
    if (finalTaxonomyTab) finalTaxonomyTab.style.display = 'none';
    if (jsonViewTab) jsonViewTab.style.display = 'none';
    
    // Show appropriate tabs based on context
    switch (context) {
        case 'cube':
            // For cubes: show Properties, Grid View, and Fact View
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (gridTab) gridTab.style.display = 'block';
            if (factViewTab) factViewTab.style.display = 'block';
            break;
            
        case 'group':
            // For groups: show Properties, Contents, and Grid View
            console.log('[manageTabVisibility] Setting group tabs');
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (contentsTab) contentsTab.style.display = 'block';
            if (gridTab) gridTab.style.display = 'block';
            console.log('[manageTabVisibility] After setting:', {
                propertiesDisplay: propertiesTab?.style.display,
                contentsDisplay: contentsTab?.style.display,
                gridDisplay: gridTab?.style.display,
                dataTableViewDisplay: dataTableViewTab?.style.display
            });
            break;
            
        case 'tableTemplate':
            // For table templates: show Properties and Template View only
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (templateViewTab) templateViewTab.style.display = 'block';
            break;
            
        case 'dataTable':
            // For data tables: show Properties and Data Table View only
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (dataTableViewTab) dataTableViewTab.style.display = 'block';
            break;
            
        case 'fact':
            // For facts: show Properties and Grid View only
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (gridTab) gridTab.style.display = 'block';
            break;
            
        case 'taxonomy':
            // For taxonomies: show Properties, Import Paths, Final Taxonomy, and JSON View
            if (propertiesTab) propertiesTab.style.display = 'block';
            if (importPathsTab) importPathsTab.style.display = 'block';
            if (finalTaxonomyTab) finalTaxonomyTab.style.display = 'block';
            if (jsonViewTab) jsonViewTab.style.display = 'block';
            break;
            
        case 'default':
        default:
            // For default view: show only Properties
            if (propertiesTab) propertiesTab.style.display = 'block';
            break;
    }
}

/**
 * Reset panel titles and styles to default state (for non-cube objects)
 */
export function resetPanelTitles() {
    // Hide the details tabs for non-cubes
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'none';
    }
    
    // Make sure Properties tab is active by default
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById('properties-tab').classList.add('active');
    
    // Reset panel titles to default values
    document.querySelector('#attributes-panel h3').textContent = 'Attributes';
    document.querySelector('#labels-panel h3').textContent = 'Labels';
    document.querySelector('#labels-panel h3').style.display = 'block'; // Show labels title for non-cubes
    document.querySelector('#references-panel h3').textContent = 'References';
    
    // Reset panel sizes and styles for non-cubes
    const attributesPanel = document.getElementById('attributes-panel');
    attributesPanel.style.flex = '0 0 auto';
    attributesPanel.style.maxHeight = '';
    attributesPanel.style.overflowY = 'auto';
    
    const labelsPanel = document.getElementById('labels-panel');
    labelsPanel.style.flex = '0 0 auto';
    labelsPanel.style.maxHeight = '';
    labelsPanel.style.minHeight = '';
    labelsPanel.style.padding = '10px';
    labelsPanel.style.borderBottom = '1px solid #ddd';
    labelsPanel.style.overflow = 'visible';
    
    const referencesPanel = document.getElementById('references-panel');
    referencesPanel.style.flex = '0 0 auto';
    referencesPanel.style.minHeight = '';
    referencesPanel.style.maxHeight = '';
    referencesPanel.style.overflowY = 'auto';
}

/**
 * Adjust panel sizes specifically for cube display
 */
export function adjustPanelSizesForCube() {
    // Attributes panel: scrollable, max 60% of container height
    const attributesPanel = document.getElementById('attributes-panel');
    attributesPanel.style.flex = '0 0 auto';
    attributesPanel.style.maxHeight = '60vh';
    attributesPanel.style.overflowY = 'auto';
    
    // Labels panel: hide it completely for cubes
    const labelsPanel = document.getElementById('labels-panel');
    labelsPanel.style.flex = '0 0 auto';
    labelsPanel.style.maxHeight = '0';
    labelsPanel.style.minHeight = '0';
    labelsPanel.style.padding = '0';
    labelsPanel.style.border = 'none';
    labelsPanel.style.overflow = 'hidden';
    
    // References panel: takes remaining space, scrollable if needed
    const referencesPanel = document.getElementById('references-panel');
    referencesPanel.style.flex = '1 1 auto';
    referencesPanel.style.minHeight = '200px';
    referencesPanel.style.overflowY = 'auto';
}
