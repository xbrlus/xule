/**
 * Layout Builder - Handles rendering of Table Templates and Data Tables
 */

import { getTaxonomyData } from './main.js';
import { getNodeLabel, getXbrlModel } from './utils.js';
import { manageTabVisibility } from './details-panel.js';

let currentDisplayMode = 'name';

/**
 * Build table templates list
 */
export function buildTableTemplates(displayMode = 'name') {
    console.log('[Layout Builder] Building table templates with display mode:', displayMode);
    currentDisplayMode = displayMode;
    
    const container = document.getElementById('table-templates-content');
    if (!container) {
        console.warn('[Layout Builder] table-templates-content container not found');
        return;
    }

    container.innerHTML = '';
    
    const taxonomyData = getTaxonomyData();
    const taxonomy = getXbrlModel(taxonomyData);
    
    if (!taxonomy || !taxonomy.factMaps || taxonomy.factMaps.length === 0) {
        container.innerHTML = '<p style="padding: 10px;">No fact maps defined in this taxonomy.</p>';
        return;
    }

    // Filter factMaps that have templateName property
    const factMapsWithTemplates = taxonomy.factMaps.filter(fm => fm.templateName);
    
    if (factMapsWithTemplates.length === 0) {
        container.innerHTML = '<p style="padding: 10px;">No table templates defined in fact maps.</p>';
        return;
    }

    // Create list of table templates in the left panel
    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.padding = '0';

    factMapsWithTemplates.forEach((factMap, index) => {
        const li = document.createElement('li');
        li.style.padding = '8px';
        li.style.cursor = 'pointer';
        li.style.borderBottom = '1px solid #eee';
        li.textContent = getNodeLabel(factMap.name, displayMode);
        li.dataset.index = index;
        
        li.addEventListener('click', function() {
            // Remove active class from all items
            ul.querySelectorAll('li').forEach(item => item.classList.remove('active'));
            li.classList.add('active');
            
            // Display template details in right panel
            displayTableTemplate(factMap, displayMode);
        });
        
        if (index === 0) {
            li.classList.add('active');
        }
        
        ul.appendChild(li);
    });

    container.appendChild(ul);

    // Display first template by default in the right details panel
    if (factMapsWithTemplates.length > 0) {
        displayTableTemplate(factMapsWithTemplates[0], displayMode);
    }
}

/**
 * Display a single table template as a grid in the right details panel
 */
function displayTableTemplate(factMap, displayMode) {
    console.log('[Layout Builder] Displaying fact map:', factMap.name);
    
    // Look up the template by templateName from taxonomy.tableTemplates array
    const taxonomyData = getTaxonomyData();
    const taxonomy = getXbrlModel(taxonomyData);
    
    let template = null;
    const templateName = factMap.templateName;
    
    if (templateName && taxonomy) {
        // Check tableTemplates array first
        if (taxonomy.tableTemplates) {
            template = taxonomy.tableTemplates.find(t => t.name === templateName);
        }
        
        // Table templates may also be stored in the factMaps array (objects with 'columns' property)
        if (!template && taxonomy.factMaps) {
            template = taxonomy.factMaps.find(fm => fm.name === templateName && fm.columns);
        }
    }
    
    if (!template) {
        console.warn('[Layout Builder] No tableTemplate found for templateName:', templateName);
        return;
    }
    
    // Show the details tabs
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    
    // Manage tab visibility - show only Properties and Template View for table templates
    manageTabVisibility('tableTemplate');
    
    // Check if Template View tab already exists, if not create it
    let templateViewButton = document.querySelector('[data-details-tab="templateView"]');
    if (!templateViewButton) {
        // Create Template View tab button
        templateViewButton = document.createElement('button');
        templateViewButton.className = 'details-tab-button';
        templateViewButton.setAttribute('data-details-tab', 'templateView');
        templateViewButton.textContent = 'Template View';
        
        // Insert after Properties button
        const propertiesButton = document.querySelector('[data-details-tab="properties"]');
        if (propertiesButton && detailsTabs) {
            propertiesButton.after(templateViewButton);
        }
        
        // Create Template View tab content container
        const propertiesTab = document.getElementById('properties-tab');
        if (propertiesTab) {
            const templateViewTab = document.createElement('div');
            templateViewTab.id = 'templateView-tab';
            templateViewTab.className = 'details-tab-content';
            propertiesTab.after(templateViewTab);
        }
        
        // Add click handler
        templateViewButton.addEventListener('click', function() {
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
    }
    
    // Switch to Template View tab
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    templateViewButton.classList.add('active');
    
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const templateViewTab = document.getElementById('templateView-tab');
    if (templateViewTab) {
        templateViewTab.classList.add('active');
        templateViewTab.innerHTML = ''; // Clear previous content
    } else {
        console.warn('[Layout Builder] templateView-tab not found');
        return;
    }

    // Populate the Properties tab with template attributes
    populatePropertiesForTemplate(factMap, template, displayMode);

    // Create a wrapper div for template content
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.fontFamily = 'Arial, sans-serif';
    // Remove overflowX - let the parent tab container handle scrolling

    // Create title
    const title = document.createElement('h3');
    title.textContent = getNodeLabel(factMap.name, displayMode);
    title.style.marginBottom = '20px';
    title.style.marginTop = '0';
    wrapper.appendChild(title);

    // Check if columns is an array (new structure) or object (old structure)
    const columns = Array.isArray(template.columns) ? template.columns : Object.entries(template.columns).map(([name, data]) => ({ columnName: name, ...data }));
    
    if (columns.length === 0) {
        const noColumns = document.createElement('p');
        noColumns.textContent = 'No columns defined for this template.';
        wrapper.appendChild(noColumns);
        templateViewTab.appendChild(wrapper);
        return;
    }

    // Create grid container
    const gridContainer = document.createElement('div');
    gridContainer.style.marginBottom = '20px';
    // Remove overflowX - let the parent tab container handle scrolling
    
    // Create table
    const table = document.createElement('table');
    table.style.borderCollapse = 'collapse';
    table.style.width = 'auto'; // Allow table to grow as needed
    table.style.border = '1px solid #ccc';

    // Create header row with column names
    const headerRow = document.createElement('tr');
    headerRow.style.backgroundColor = '#f5f5f5';
    headerRow.style.fontWeight = 'bold';
    
    columns.forEach(column => {
        const th = document.createElement('th');
        th.textContent = column.columnName || 'Unnamed';
        th.style.border = '1px solid #ccc';
        th.style.padding = '8px';
        th.style.textAlign = 'left';
        headerRow.appendChild(th);
    });
    
    table.appendChild(headerRow);

    // Create data row with dimensions
    const dataRow = document.createElement('tr');
    
    columns.forEach(column => {
        const td = document.createElement('td');
        td.style.border = '1px solid #ccc';
        td.style.padding = '8px';
        td.style.verticalAlign = 'top';
        
        if (column && column.factDimensions) {
            // Create mini table for dimensions
            const miniTable = document.createElement('table');
            miniTable.style.width = '100%';
            miniTable.style.fontSize = '0.9em';
            
            Object.entries(column.factDimensions).forEach(([dimKey, dimValue]) => {
                const miniRow = document.createElement('tr');
                
                const keyCell = document.createElement('td');
                keyCell.textContent = dimKey;
                keyCell.style.fontWeight = 'bold';
                keyCell.style.paddingRight = '10px';
                keyCell.style.whiteSpace = 'nowrap';
                
                const valueCell = document.createElement('td');
                valueCell.textContent = getNodeLabel(dimValue, displayMode);
                
                miniRow.appendChild(keyCell);
                miniRow.appendChild(valueCell);
                miniTable.appendChild(miniRow);
            });
            
            td.appendChild(miniTable);
        } else {
            td.textContent = '-';
            td.style.color = '#999';
        }
        
        dataRow.appendChild(td);
    });
    
    table.appendChild(dataRow);
    gridContainer.appendChild(table);
    wrapper.appendChild(gridContainer);

    // Display additional properties
    if (template.rowIdColumn) {
        const rowIdInfo = document.createElement('p');
        rowIdInfo.style.marginTop = '20px';
        rowIdInfo.innerHTML = `<strong>Row ID Column:</strong> ${template.rowIdColumn}`;
        wrapper.appendChild(rowIdInfo);
    }

    if (template.factDimensions) {
        const dimsTitle = document.createElement('h4');
        dimsTitle.textContent = 'Template Dimensions';
        dimsTitle.style.marginTop = '20px';
        wrapper.appendChild(dimsTitle);

        const dimsTable = document.createElement('table');
        dimsTable.style.borderCollapse = 'collapse';
        dimsTable.style.width = '100%';
        dimsTable.style.border = '1px solid #ccc';

        Object.entries(template.factDimensions).forEach(([dimKey, dimValue]) => {
            const row = document.createElement('tr');
            
            const keyCell = document.createElement('td');
            keyCell.textContent = dimKey;
            keyCell.style.border = '1px solid #ccc';
            keyCell.style.padding = '8px';
            keyCell.style.fontWeight = 'bold';
            keyCell.style.backgroundColor = '#f9f9f9';
            
            const valueCell = document.createElement('td');
            valueCell.textContent = dimValue;
            valueCell.style.border = '1px solid #ccc';
            valueCell.style.padding = '8px';
            
            row.appendChild(keyCell);
            row.appendChild(valueCell);
            dimsTable.appendChild(row);
        });

        wrapper.appendChild(dimsTable);
    }

    // Finally, append wrapper to Template View tab
    templateViewTab.appendChild(wrapper);
}

/**
 * Populate the Properties tab with table template attributes
 */
function populatePropertiesForTemplate(factMap, template, displayMode) {
    // Clear the attributes panel
    const attributesContent = document.getElementById('attributes-content');
    if (attributesContent) {
        attributesContent.innerHTML = '';
        
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.fontSize = '0.9em';
        
        // Add factMap name
        const nameRow = document.createElement('tr');
        const nameLabel = document.createElement('td');
        nameLabel.textContent = 'Fact Map Name:';
        nameLabel.style.fontWeight = 'bold';
        nameLabel.style.paddingRight = '10px';
        nameLabel.style.verticalAlign = 'top';
        const nameValue = document.createElement('td');
        nameValue.textContent = factMap.name;
        nameRow.appendChild(nameLabel);
        nameRow.appendChild(nameValue);
        table.appendChild(nameRow);
        
        // Add templateName if present
        if (factMap.templateName) {
            const templateNameRow = document.createElement('tr');
            const templateNameLabel = document.createElement('td');
            templateNameLabel.textContent = 'Template Name:';
            templateNameLabel.style.fontWeight = 'bold';
            templateNameLabel.style.paddingRight = '10px';
            templateNameLabel.style.verticalAlign = 'top';
            const templateNameValue = document.createElement('td');
            templateNameValue.textContent = factMap.templateName;
            templateNameRow.appendChild(templateNameLabel);
            templateNameRow.appendChild(templateNameValue);
            table.appendChild(templateNameRow);
        }
        
        // Add cubeName if present
        if (factMap.cubeName) {
            const cubeNameRow = document.createElement('tr');
            const cubeNameLabel = document.createElement('td');
            cubeNameLabel.textContent = 'Cube Name:';
            cubeNameLabel.style.fontWeight = 'bold';
            cubeNameLabel.style.paddingRight = '10px';
            cubeNameLabel.style.verticalAlign = 'top';
            const cubeNameValue = document.createElement('td');
            cubeNameValue.textContent = factMap.cubeName;
            cubeNameRow.appendChild(cubeNameLabel);
            cubeNameRow.appendChild(cubeNameValue);
            table.appendChild(cubeNameRow);
        }
        
        // Add rowIdColumn if present
        if (template.rowIdColumn) {
            const rowIdRow = document.createElement('tr');
            const rowIdLabel = document.createElement('td');
            rowIdLabel.textContent = 'Row ID Column:';
            rowIdLabel.style.fontWeight = 'bold';
            rowIdLabel.style.paddingRight = '10px';
            rowIdLabel.style.verticalAlign = 'top';
            const rowIdValue = document.createElement('td');
            rowIdValue.textContent = template.rowIdColumn;
            rowIdRow.appendChild(rowIdLabel);
            rowIdRow.appendChild(rowIdValue);
            table.appendChild(rowIdRow);
        }
        
        // Add column count
        const colCountRow = document.createElement('tr');
        const colCountLabel = document.createElement('td');
        colCountLabel.textContent = 'Column Count:';
        colCountLabel.style.fontWeight = 'bold';
        colCountLabel.style.paddingRight = '10px';
        colCountLabel.style.verticalAlign = 'top';
        const colCountValue = document.createElement('td');
        colCountValue.textContent = Array.isArray(template.columns) ? template.columns.length : Object.keys(template.columns).length;
        colCountRow.appendChild(colCountLabel);
        colCountRow.appendChild(colCountValue);
        table.appendChild(colCountRow);
        
        // Add template dimensions if present
        if (template.factDimensions) {
            const dimsRow = document.createElement('tr');
            const dimsLabel = document.createElement('td');
            dimsLabel.textContent = 'Template Dimensions:';
            dimsLabel.style.fontWeight = 'bold';
            dimsLabel.style.paddingRight = '10px';
            dimsLabel.style.verticalAlign = 'top';
            const dimsValue = document.createElement('td');
            dimsValue.textContent = JSON.stringify(template.factDimensions, null, 2);
            dimsValue.style.whiteSpace = 'pre-wrap';
            dimsValue.style.fontFamily = 'monospace';
            dimsValue.style.fontSize = '0.85em';
            dimsRow.appendChild(dimsLabel);
            dimsRow.appendChild(dimsValue);
            table.appendChild(dimsRow);
        }
        
        attributesContent.appendChild(table);
    }
    
    // Clear labels and references panels (templates don't have these)
    const labelsContent = document.getElementById('labels-content');
    if (labelsContent) {
        labelsContent.innerHTML = '<p style="color: #999;">Not applicable for table templates.</p>';
    }
    
    const referencesContent = document.getElementById('references-content');
    if (referencesContent) {
        referencesContent.innerHTML = '<p style="color: #999;">Not applicable for table templates.</p>';
    }
}

/**
 * Build data tables list
 */
export function buildDataTables(displayMode = 'name') {
    console.log('[Layout Builder] Building layouts with display mode:', displayMode);
    currentDisplayMode = displayMode;
    
    const container = document.getElementById('data-tables-content');
    if (!container) {
        console.warn('[Layout Builder] data-tables-content container not found');
        return;
    }

    container.innerHTML = '';
    
    const taxonomyData = getTaxonomyData();
    const taxonomy = getXbrlModel(taxonomyData);
    
    // Get all layouts
    if (!taxonomy || !taxonomy.layouts || taxonomy.layouts.length === 0) {
        container.innerHTML = '<p style="padding: 10px;">No layouts defined in this taxonomy.</p>';
        return;
    }

    // Create list of layouts in the left panel
    const ul = document.createElement('ul');
    ul.style.listStyle = 'none';
    ul.style.padding = '0';

    taxonomy.layouts.forEach((layout, index) => {
        const li = document.createElement('li');
        li.style.padding = '8px';
        li.style.cursor = 'pointer';
        li.style.borderBottom = '1px solid #eee';
        li.textContent = getNodeLabel(layout.name, displayMode);
        li.dataset.index = index;
        
        li.addEventListener('click', function() {
            // Remove active class from all items
            ul.querySelectorAll('li').forEach(item => item.classList.remove('active'));
            li.classList.add('active');
            
            // Display layout with all its data tables in right panel
            displayLayout(layout, displayMode);
        });
        
        if (index === 0) {
            li.classList.add('active');
        }
        
        ul.appendChild(li);
    });

    container.appendChild(ul);

    // Display first layout by default in the right details panel
    if (taxonomy.layouts.length > 0) {
        displayLayout(taxonomy.layouts[0], displayMode);
    }
}

/**
 * Populate the Properties tab with data table attributes
 */
function populatePropertiesForDataTable(dataTable, displayMode) {
    // Clear the attributes panel
    const attributesContent = document.getElementById('attributes-content');
    if (attributesContent) {
        attributesContent.innerHTML = '';
        
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.fontSize = '0.9em';
        
        // Add data table name
        const nameRow = document.createElement('tr');
        const nameLabel = document.createElement('td');
        nameLabel.textContent = 'Name:';
        nameLabel.style.fontWeight = 'bold';
        nameLabel.style.paddingRight = '10px';
        nameLabel.style.verticalAlign = 'top';
        const nameValue = document.createElement('td');
        nameValue.textContent = dataTable.name;
        nameRow.appendChild(nameLabel);
        nameRow.appendChild(nameValue);
        table.appendChild(nameRow);
        
        // Add cube name
        if (dataTable.cubeName) {
            const cubeRow = document.createElement('tr');
            const cubeLabel = document.createElement('td');
            cubeLabel.textContent = 'Cube Name:';
            cubeLabel.style.fontWeight = 'bold';
            cubeLabel.style.paddingRight = '10px';
            cubeLabel.style.verticalAlign = 'top';
            const cubeValue = document.createElement('td');
            cubeValue.textContent = dataTable.cubeName;
            cubeRow.appendChild(cubeLabel);
            cubeRow.appendChild(cubeValue);
            table.appendChild(cubeRow);
        }
        
        // Add table type
        if (dataTable.tableType) {
            const tableTypeRow = document.createElement('tr');
            const tableTypeLabel = document.createElement('td');
            tableTypeLabel.textContent = 'Table Type:';
            tableTypeLabel.style.fontWeight = 'bold';
            tableTypeLabel.style.paddingRight = '10px';
            tableTypeLabel.style.verticalAlign = 'top';
            const tableTypeValue = document.createElement('td');
            tableTypeValue.textContent = dataTable.tableType;
            tableTypeRow.appendChild(tableTypeLabel);
            tableTypeRow.appendChild(tableTypeValue);
            table.appendChild(tableTypeRow);
        }
        
        // Add axis information
        if (dataTable.xAxis) {
            const xAxisRow = document.createElement('tr');
            const xAxisLabel = document.createElement('td');
            xAxisLabel.textContent = 'X-Axis:';
            xAxisLabel.style.fontWeight = 'bold';
            xAxisLabel.style.paddingRight = '10px';
            xAxisLabel.style.verticalAlign = 'top';
            const xAxisValue = document.createElement('td');
            xAxisValue.textContent = JSON.stringify(dataTable.xAxis, null, 2);
            xAxisValue.style.whiteSpace = 'pre-wrap';
            xAxisValue.style.fontFamily = 'monospace';
            xAxisValue.style.fontSize = '0.85em';
            xAxisRow.appendChild(xAxisLabel);
            xAxisRow.appendChild(xAxisValue);
            table.appendChild(xAxisRow);
        }
        
        if (dataTable.yAxis) {
            const yAxisRow = document.createElement('tr');
            const yAxisLabel = document.createElement('td');
            yAxisLabel.textContent = 'Y-Axis:';
            yAxisLabel.style.fontWeight = 'bold';
            yAxisLabel.style.paddingRight = '10px';
            yAxisLabel.style.verticalAlign = 'top';
            const yAxisValue = document.createElement('td');
            yAxisValue.textContent = JSON.stringify(dataTable.yAxis, null, 2);
            yAxisValue.style.whiteSpace = 'pre-wrap';
            yAxisValue.style.fontFamily = 'monospace';
            yAxisValue.style.fontSize = '0.85em';
            yAxisRow.appendChild(yAxisLabel);
            yAxisRow.appendChild(yAxisValue);
            table.appendChild(yAxisRow);
        }
        
        if (dataTable.zAxis) {
            const zAxisRow = document.createElement('tr');
            const zAxisLabel = document.createElement('td');
            zAxisLabel.textContent = 'Z-Axis:';
            zAxisLabel.style.fontWeight = 'bold';
            zAxisLabel.style.paddingRight = '10px';
            zAxisLabel.style.verticalAlign = 'top';
            const zAxisValue = document.createElement('td');
            zAxisValue.textContent = JSON.stringify(dataTable.zAxis, null, 2);
            zAxisValue.style.whiteSpace = 'pre-wrap';
            zAxisValue.style.fontFamily = 'monospace';
            zAxisValue.style.fontSize = '0.85em';
            zAxisRow.appendChild(zAxisLabel);
            zAxisRow.appendChild(zAxisValue);
            table.appendChild(zAxisRow);
        }
        
        attributesContent.appendChild(table);
    }
    
    // Clear labels and references panels (data tables don't have these)
    const labelsContent = document.getElementById('labels-content');
    if (labelsContent) {
        labelsContent.innerHTML = '<p style="color: #999;">Not applicable for data tables.</p>';
    }
    
    const referencesContent = document.getElementById('references-content');
    if (referencesContent) {
        referencesContent.innerHTML = '<p style="color: #999;">Not applicable for data tables.</p>';
    }
}

/**
 * Display a layout with all its data tables in the right details panel
 */
function displayLayout(layout, displayMode) {
    console.log('[Layout Builder] Displaying layout:', layout.name);
    
    // Show the details tabs
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    
    // Manage tab visibility - show only Properties and Data Table View for layouts
    manageTabVisibility('dataTable');
    
    // Check if Data Table View tab already exists, if not create it
    let dataTableViewButton = document.querySelector('[data-details-tab="dataTableView"]');
    if (!dataTableViewButton) {
        // Create Data Table View tab button
        dataTableViewButton = document.createElement('button');
        dataTableViewButton.className = 'details-tab-button';
        dataTableViewButton.setAttribute('data-details-tab', 'dataTableView');
        dataTableViewButton.textContent = 'Layout View';
        
        // Insert after Properties button (or after Template View if it exists)
        const propertiesButton = document.querySelector('[data-details-tab="properties"]');
        const templateViewButton = document.querySelector('[data-details-tab="templateView"]');
        const insertAfter = templateViewButton || propertiesButton;
        if (insertAfter && detailsTabs) {
            insertAfter.after(dataTableViewButton);
        }
        
        // Create Data Table View tab content container
        const propertiesTab = document.getElementById('properties-tab');
        if (propertiesTab) {
            const dataTableViewTab = document.createElement('div');
            dataTableViewTab.id = 'dataTableView-tab';
            dataTableViewTab.className = 'details-tab-content';
            
            // Insert after templateView-tab if it exists, otherwise after properties-tab
            const templateViewTab = document.getElementById('templateView-tab');
            const insertAfterTab = templateViewTab || propertiesTab;
            insertAfterTab.after(dataTableViewTab);
        }
        
        // Add click handler
        dataTableViewButton.addEventListener('click', function() {
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
    }
    
    // Switch to Layout View tab
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    dataTableViewButton.classList.add('active');
    
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const dataTableViewTab = document.getElementById('dataTableView-tab');
    if (dataTableViewTab) {
        dataTableViewTab.classList.add('active');
        dataTableViewTab.innerHTML = ''; // Clear previous content
    } else {
        console.warn('[Layout Builder] dataTableView-tab not found');
        return;
    }

    // Populate the Properties tab with layout attributes
    populatePropertiesForLayout(layout, displayMode);

    // Create a wrapper div for layout content
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.fontFamily = 'Arial, sans-serif';

    // Get the taxonomy data
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);

    // Check if layout has datatables
    if (!layout.dataTables || layout.dataTables.length === 0) {
        wrapper.innerHTML = '<p style="padding: 10px;">No data tables defined in this layout.</p>';
        dataTableViewTab.appendChild(wrapper);
        return;
    }

    // Get tableConstruction attribute, default to 'topDown'
    const tableConstruction = layout.tableConstruction || 'topDown';

    // Render all datatables
    const renderedTables = [];
    const errors = [];

    layout.dataTables.forEach((dataTable, index) => {
        try {
            const tableInfo = renderDataTableForLayout(dataTable, displayMode, taxonomyData, xbrlModel);
            renderedTables.push(tableInfo);
        } catch (error) {
            errors.push(`Error rendering table ${dataTable.name}: ${error.message}`);
            console.error('[Layout Builder] Error rendering table:', error);
        }
    });

    // Display errors if any
    if (errors.length > 0) {
        const errorDiv = document.createElement('div');
        errorDiv.style.padding = '15px';
        errorDiv.style.backgroundColor = '#f8d7da';
        errorDiv.style.color = '#721c24';
        errorDiv.style.border = '1px solid #f5c6cb';
        errorDiv.style.borderRadius = '4px';
        errorDiv.style.marginBottom = '20px';
        
        const errorTitle = document.createElement('h4');
        errorTitle.textContent = 'Rendering Errors:';
        errorTitle.style.marginTop = '0';
        errorDiv.appendChild(errorTitle);
        
        errors.forEach(err => {
            const errorP = document.createElement('p');
            errorP.textContent = err;
            errorP.style.margin = '5px 0';
            errorDiv.appendChild(errorP);
        });
        
        wrapper.appendChild(errorDiv);
    }

    // Validate and concatenate tables based on tableConstruction
    if (renderedTables.length === 1) {
        // Single table - just append it
        wrapper.appendChild(renderedTables[0].element);
    } else if (renderedTables.length > 1) {
        // Multiple tables - validate and concatenate
        if (tableConstruction === 'topDown') {
            // Debug: log column counts
            console.log('[Layout Builder] Table column counts:', renderedTables.map((t, i) => ({
                index: i,
                name: t.name,
                columnCount: t.columnCount,
                dataColumnCount: t.dataColumnCount
            })));
            
            // Group consecutive tables with matching data column counts and merge them
            const mergedTables = [];
            let currentGroup = [renderedTables[0]];
            
            for (let i = 1; i < renderedTables.length; i++) {
                const prevTable = renderedTables[i - 1];
                const currTable = renderedTables[i];
                
                console.log(`[Layout Builder] Comparing table ${i-1} (data cols: ${prevTable.dataColumnCount}) with table ${i} (data cols: ${currTable.dataColumnCount})`);
                
                // If data column counts match, add to current group
                if (prevTable.dataColumnCount === currTable.dataColumnCount && prevTable.dataColumnCount > 0) {
                    console.log(`[Layout Builder] Merging table ${i} into current group (matching data columns)`);
                    currentGroup.push(currTable);
                } else {
                    // Different data column count - save current group and start new one
                    console.log(`[Layout Builder] Starting new group with table ${i} (different data columns)`);
                    mergedTables.push(currentGroup);
                    currentGroup = [currTable];
                }
            }
            // Add the last group
            mergedTables.push(currentGroup);
            
            // Merge tables within each group
            mergedTables.forEach((group, groupIndex) => {
                if (group.length === 1) {
                    // Single table - just append it
                    if (groupIndex > 0) {
                        const spacer = document.createElement('div');
                        spacer.style.height = '20px';
                        wrapper.appendChild(spacer);
                    }
                    wrapper.appendChild(group[0].element);
                } else {
                    // Multiple tables with same column count - merge them
                    const firstTable = group[0];
                    const firstTableElement = firstTable.element.querySelector('table');
                    
                    if (firstTableElement) {
                        // Append rows from subsequent tables
                        for (let i = 1; i < group.length; i++) {
                            const nextTableElement = group[i].element.querySelector('table');
                            if (nextTableElement) {
                                // Get all rows from the next table and append to first table
                                const rows = Array.from(nextTableElement.querySelectorAll('tr'));
                                rows.forEach(row => {
                                    firstTableElement.appendChild(row);
                                });
                            }
                        }
                    }
                    
                    // Append the merged table (first element which now contains all rows)
                    if (groupIndex > 0) {
                        const spacer = document.createElement('div');
                        spacer.style.height = '20px';
                        wrapper.appendChild(spacer);
                    }
                    wrapper.appendChild(firstTable.element);
                }
            });
            
        } else if (tableConstruction === 'leftRight') {
            // Validate all tables have the same number of rows
            const firstRowCount = renderedTables[0].rowCount;
            const allMatch = renderedTables.every(t => t.rowCount === firstRowCount);
            
            if (!allMatch) {
                const validationError = document.createElement('div');
                validationError.style.padding = '15px';
                validationError.style.backgroundColor = '#f8d7da';
                validationError.style.color = '#721c24';
                validationError.style.border = '1px solid #f5c6cb';
                validationError.style.borderRadius = '4px';
                validationError.style.marginBottom = '20px';
                
                validationError.innerHTML = `<h4 style="margin-top: 0;">Validation Error:</h4>
                    <p>For 'leftRight' table construction, all data tables must have the same number of rows.</p>
                    <p>Row counts: ${renderedTables.map((t, i) => `Table ${i+1}: ${t.rowCount}`).join(', ')}</p>`;
                
                wrapper.appendChild(validationError);
            }
            
            // Append all tables horizontally using flexbox
            const horizontalContainer = document.createElement('div');
            horizontalContainer.style.display = 'flex';
            horizontalContainer.style.gap = '20px';
            horizontalContainer.style.alignItems = 'flex-start';
            
            renderedTables.forEach(tableInfo => {
                horizontalContainer.appendChild(tableInfo.element);
            });
            
            wrapper.appendChild(horizontalContainer);
        }
    }

    dataTableViewTab.appendChild(wrapper);
}

/**
 * Render a single data table for a layout and return table info
 */
export function renderDataTableForLayout(dataTable, displayMode, taxonomyData, xbrlModel) {
    const container = document.createElement('div');
    
    // Don't show title for datatable within a layout
    // The layout name is already shown at the top

    // Find the cube if cubeName is specified
    let cube = null;
    if (dataTable.cubeName) {
        cube = xbrlModel?.cubes?.find(c => c.name === dataTable.cubeName);
        if (!cube) {
            const noCube = document.createElement('p');
            noCube.textContent = `Cube "${dataTable.cubeName}" not found.`;
            noCube.style.color = '#d9534f';
            container.appendChild(noCube);
            return { element: container, columnCount: 0, rowCount: 0, dataColumnCount: 0 };
        }
    }

    // Get z-axis dimension values
    const zAxisValues = getAxisValues(dataTable.zAxis, taxonomyData, displayMode);
    
    let tableElement;
    let columnCount = 0;
    let rowCount = 0;
    let dataColumnCount = 0;
    
    if (zAxisValues.length === 0) {
        // No z-axis or single grid
        const grid = createDataTableGrid(dataTable, cube, null, taxonomyData, displayMode);
        container.appendChild(grid);
        
        // Extract table dimensions from the grid
        const table = grid.querySelector('table');
        if (table) {
            const headerRow = table.querySelector('tr');
            if (headerRow) {
                columnCount = headerRow.querySelectorAll('th, td').length;
            }
            rowCount = table.querySelectorAll('tr').length;
            
            // Calculate data columns (columns after AxisID)
            // Find a data row (row with td elements) that has AxisID to count data columns
            const allRows = Array.from(table.querySelectorAll('tr'));
            const dataRowWithAxisId = allRows.find(row => {
                const hasTdCells = row.querySelector('td') !== null;
                const hasAxisId = row.querySelector('.AxisID') !== null;
                return hasTdCells && hasAxisId;
            });
            
            if (dataRowWithAxisId) {
                // Count td elements (data cells) in this row
                dataColumnCount = dataRowWithAxisId.querySelectorAll('td').length;
                console.log('[Layout Builder] Found data row with', dataColumnCount, 'data columns');
            } else {
                // Fallback: assume all columns after first are data columns
                dataColumnCount = columnCount > 0 ? columnCount - 1 : 0;
                console.log('[Layout Builder] No data row found, using fallback:', dataColumnCount);
            }
        }
    } else {
        // Multiple grids for z-axis - use tabbed interface
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'z-axis-tabs';
        tabsContainer.style.marginBottom = '10px';

        const gridsContainer = document.createElement('div');
        gridsContainer.className = 'z-axis-grids';

        zAxisValues.forEach((zValue, index) => {
            // Create tab button
            const tabButton = document.createElement('button');
            tabButton.textContent = zValue.label;
            tabButton.className = 'z-axis-tab-button';
            tabButton.style.padding = '8px 16px';
            tabButton.style.marginRight = '5px';
            tabButton.style.cursor = 'pointer';
            tabButton.style.border = '1px solid #ccc';
            tabButton.style.backgroundColor = index === 0 ? '#007bff' : '#f5f5f5';
            tabButton.style.color = index === 0 ? 'white' : 'black';
            
            tabButton.addEventListener('click', function() {
                // Update active tab
                tabsContainer.querySelectorAll('button').forEach(btn => {
                    btn.style.backgroundColor = '#f5f5f5';
                    btn.style.color = 'black';
                });
                tabButton.style.backgroundColor = '#007bff';
                tabButton.style.color = 'white';

                // Show corresponding grid
                gridsContainer.querySelectorAll('.z-axis-grid').forEach((grid, i) => {
                    grid.style.display = i === index ? 'block' : 'none';
                });
            });

            tabsContainer.appendChild(tabButton);

            // Create grid
            const gridWrapper = document.createElement('div');
            gridWrapper.className = 'z-axis-grid';
            gridWrapper.style.display = index === 0 ? 'block' : 'none';
            
            const grid = createDataTableGrid(dataTable, cube, zValue, taxonomyData, displayMode);
            gridWrapper.appendChild(grid);
            gridsContainer.appendChild(gridWrapper);
            
            // Get dimensions from first grid only
            if (index === 0) {
                const table = grid.querySelector('table');
                if (table) {
                    const headerRow = table.querySelector('tr');
                    if (headerRow) {
                        columnCount = headerRow.querySelectorAll('th, td').length;
                    }
                    rowCount = table.querySelectorAll('tr').length;
                    
                    // Calculate data columns (columns after AxisID)
                    // Find a data row (row with td elements) that has AxisID
                    const allRows = Array.from(table.querySelectorAll('tr'));
                    const dataRowWithAxisId = allRows.find(row => {
                        const hasTdCells = row.querySelector('td') !== null;
                        const hasAxisId = row.querySelector('.AxisID') !== null;
                        return hasTdCells && hasAxisId;
                    });
                    
                    if (dataRowWithAxisId) {
                        // Count td elements (data cells) in this row
                        dataColumnCount = dataRowWithAxisId.querySelectorAll('td').length;
                        console.log('[Layout Builder] Z-axis grid found data row with', dataColumnCount, 'data columns');
                    } else {
                        dataColumnCount = columnCount > 0 ? columnCount - 1 : 0;
                        console.log('[Layout Builder] Z-axis grid no data row found, using fallback:', dataColumnCount);
                    }
                }
            }
        });

        container.appendChild(tabsContainer);
        container.appendChild(gridsContainer);
    }

    return { 
        element: container, 
        columnCount: columnCount, 
        rowCount: rowCount,
        dataColumnCount: dataColumnCount,
        name: dataTable.name
    };
}

/**
 * Populate the Properties tab with layout attributes
 */
function populatePropertiesForLayout(layout, displayMode) {
    const attributesContent = document.getElementById('attributes-content');
    if (attributesContent) {
        attributesContent.innerHTML = '';
        
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.fontSize = '0.9em';
        
        // Add layout name
        const nameRow = document.createElement('tr');
        const nameLabel = document.createElement('td');
        nameLabel.textContent = 'Layout Name:';
        nameLabel.style.fontWeight = 'bold';
        nameLabel.style.paddingRight = '10px';
        nameLabel.style.verticalAlign = 'top';
        const nameValue = document.createElement('td');
        nameValue.textContent = layout.name;
        nameRow.appendChild(nameLabel);
        nameRow.appendChild(nameValue);
        table.appendChild(nameRow);
        
        // Add tableConstruction
        const tcRow = document.createElement('tr');
        const tcLabel = document.createElement('td');
        tcLabel.textContent = 'Table Construction:';
        tcLabel.style.fontWeight = 'bold';
        tcLabel.style.paddingRight = '10px';
        tcLabel.style.verticalAlign = 'top';
        const tcValue = document.createElement('td');
        tcValue.textContent = layout.tableConstruction || 'topDown (default)';
        tcRow.appendChild(tcLabel);
        tcRow.appendChild(tcValue);
        table.appendChild(tcRow);
        
        // Add datatable count
        const dtCountRow = document.createElement('tr');
        const dtCountLabel = document.createElement('td');
        dtCountLabel.textContent = 'Data Tables Count:';
        dtCountLabel.style.fontWeight = 'bold';
        dtCountLabel.style.paddingRight = '10px';
        dtCountLabel.style.verticalAlign = 'top';
        const dtCountValue = document.createElement('td');
        dtCountValue.textContent = layout.dataTables ? layout.dataTables.length : 0;
        dtCountRow.appendChild(dtCountLabel);
        dtCountRow.appendChild(dtCountValue);
        table.appendChild(dtCountRow);
        
        // List datatable names
        if (layout.dataTables && layout.dataTables.length > 0) {
            const dtNamesRow = document.createElement('tr');
            const dtNamesLabel = document.createElement('td');
            dtNamesLabel.textContent = 'Data Tables:';
            dtNamesLabel.style.fontWeight = 'bold';
            dtNamesLabel.style.paddingRight = '10px';
            dtNamesLabel.style.verticalAlign = 'top';
            const dtNamesValue = document.createElement('td');
            const dtList = document.createElement('ul');
            dtList.style.margin = '0';
            dtList.style.paddingLeft = '20px';
            layout.dataTables.forEach(dt => {
                const li = document.createElement('li');
                li.textContent = dt.name;
                dtList.appendChild(li);
            });
            dtNamesValue.appendChild(dtList);
            dtNamesRow.appendChild(dtNamesLabel);
            dtNamesRow.appendChild(dtNamesValue);
            table.appendChild(dtNamesRow);
        }
        
        attributesContent.appendChild(table);
    }
    
    // Clear labels and references panels
    const labelsContent = document.getElementById('labels-content');
    if (labelsContent) {
        labelsContent.innerHTML = '<p style="color: #999;">Not applicable for layouts.</p>';
    }
    
    const referencesContent = document.getElementById('references-content');
    if (referencesContent) {
        referencesContent.innerHTML = '<p style="color: #999;">Not applicable for layouts.</p>';
    }
}

/**
 * Display a data table as a grid in the right details panel
 */
function displayDataTable(dataTable, displayMode) {
    console.log('[Layout Builder] Displaying data table:', dataTable.name);
    
    // Show the details tabs
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'flex';
    }
    
    // Manage tab visibility - show only Properties and Data Table View for data tables
    manageTabVisibility('dataTable');
    
    // Check if Data Table View tab already exists, if not create it
    let dataTableViewButton = document.querySelector('[data-details-tab="dataTableView"]');
    if (!dataTableViewButton) {
        // Create Data Table View tab button
        dataTableViewButton = document.createElement('button');
        dataTableViewButton.className = 'details-tab-button';
        dataTableViewButton.setAttribute('data-details-tab', 'dataTableView');
        dataTableViewButton.textContent = 'Data Table View';
        
        // Insert after Properties button (or after Template View if it exists)
        const propertiesButton = document.querySelector('[data-details-tab="properties"]');
        const templateViewButton = document.querySelector('[data-details-tab="templateView"]');
        const insertAfter = templateViewButton || propertiesButton;
        if (insertAfter && detailsTabs) {
            insertAfter.after(dataTableViewButton);
        }
        
        // Create Data Table View tab content container
        const propertiesTab = document.getElementById('properties-tab');
        if (propertiesTab) {
            const dataTableViewTab = document.createElement('div');
            dataTableViewTab.id = 'dataTableView-tab';
            dataTableViewTab.className = 'details-tab-content';
            
            // Insert after templateView-tab if it exists, otherwise after properties-tab
            const templateViewTab = document.getElementById('templateView-tab');
            const insertAfterTab = templateViewTab || propertiesTab;
            insertAfterTab.after(dataTableViewTab);
        }
        
        // Add click handler
        dataTableViewButton.addEventListener('click', function() {
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
    }
    
    // Switch to Data Table View tab
    document.querySelectorAll('.details-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    dataTableViewButton.classList.add('active');
    
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const dataTableViewTab = document.getElementById('dataTableView-tab');
    if (dataTableViewTab) {
        dataTableViewTab.classList.add('active');
        dataTableViewTab.innerHTML = ''; // Clear previous content
    } else {
        console.warn('[Layout Builder] dataTableView-tab not found');
        return;
    }

    // Populate the Properties tab with data table attributes
    populatePropertiesForDataTable(dataTable, displayMode);

    // Create a wrapper div for data table content
    const wrapper = document.createElement('div');
    wrapper.style.padding = '20px';
    wrapper.style.fontFamily = 'Arial, sans-serif';
    // Remove overflowX - let the parent tab container handle scrolling

    // Get the taxonomy data
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);

    // Create title - try to find a label for the dataTable, otherwise use QName
    const title = document.createElement('h3');
    const dataTableLabel = xbrlModel?.labels?.find(l => 
        l.relatedName === dataTable.name && 
        l.labelType === 'xbrl:label'
    );
    title.textContent = dataTableLabel ? dataTableLabel.value : getNodeLabel(dataTable.name, displayMode);
    title.style.marginBottom = '20px';
    title.style.marginTop = '0';
    wrapper.appendChild(title);

    // Find the cube if cubeName is specified
    let cube = null;
    if (dataTable.cubeName) {
        cube = xbrlModel?.cubes?.find(c => c.name === dataTable.cubeName);
        if (!cube) {
            const noCube = document.createElement('p');
            noCube.textContent = `Cube "${dataTable.cubeName}" not found.`;
            noCube.style.color = '#d9534f';
            wrapper.appendChild(noCube);
            dataTableViewTab.appendChild(wrapper);
            return;
        }
    }

    // Get z-axis dimension values
    const zAxisValues = getAxisValues(dataTable.zAxis, taxonomyData, displayMode);
    
    if (zAxisValues.length === 0) {
        // No z-axis or single grid
        const grid = createDataTableGrid(dataTable, cube, null, taxonomyData, displayMode);
        wrapper.appendChild(grid);
    } else {
        // Multiple grids for z-axis
        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'z-axis-tabs';
        tabsContainer.style.marginBottom = '10px';

        const gridsContainer = document.createElement('div');
        gridsContainer.className = 'z-axis-grids';

        zAxisValues.forEach((zValue, index) => {
            // Create tab button
            const tabButton = document.createElement('button');
            tabButton.textContent = zValue.label;
            tabButton.className = 'z-axis-tab-button';
            tabButton.style.padding = '8px 16px';
            tabButton.style.marginRight = '5px';
            tabButton.style.cursor = 'pointer';
            tabButton.style.border = '1px solid #ccc';
            tabButton.style.backgroundColor = index === 0 ? '#007bff' : '#f5f5f5';
            tabButton.style.color = index === 0 ? 'white' : 'black';
            
            tabButton.addEventListener('click', function() {
                // Update active tab
                tabsContainer.querySelectorAll('button').forEach(btn => {
                    btn.style.backgroundColor = '#f5f5f5';
                    btn.style.color = 'black';
                });
                tabButton.style.backgroundColor = '#007bff';
                tabButton.style.color = 'white';

                // Show corresponding grid
                gridsContainer.querySelectorAll('.z-axis-grid').forEach((grid, i) => {
                    grid.style.display = i === index ? 'block' : 'none';
                });
            });

            tabsContainer.appendChild(tabButton);

            // Create grid
            const gridWrapper = document.createElement('div');
            gridWrapper.className = 'z-axis-grid';
            gridWrapper.style.display = index === 0 ? 'block' : 'none';
            
            const grid = createDataTableGrid(dataTable, cube, zValue, taxonomyData, displayMode);
            gridWrapper.appendChild(grid);
            gridsContainer.appendChild(gridWrapper);
        });

        wrapper.appendChild(tabsContainer);
        wrapper.appendChild(gridsContainer);
    }

    // Finally, append wrapper to Data Table View tab
    dataTableViewTab.appendChild(wrapper);
}

/**
 * Create a single data table grid
 */
export function createDataTableGrid(dataTable, cube, zValue, taxonomyData, displayMode, selectedZValues = {}) {
    const gridContainer = document.createElement('div');
    const xbrlModel = getXbrlModel(taxonomyData);

    // Get facts that match the cube (or all facts if no cube)
    const relevantFacts = getRelevantFacts(xbrlModel, cube ? cube.name : null);

    // Get z-axis header information if zAxis is defined
    let zAxisHeaders = [];
    let tableContainer = null; // Container for just the table (not controls)
    
    if (dataTable.zAxis) {
        zAxisHeaders = getAxisHeaderInfo(dataTable.zAxis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube);
        
        // Create z-axis controls (dropdowns) if we have z-axis dimensions
        if (zAxisHeaders.length > 0) {
            const zAxisControlsContainer = document.createElement('div');
            zAxisControlsContainer.style.marginBottom = '15px';
            zAxisControlsContainer.style.display = 'flex';
            zAxisControlsContainer.style.gap = '15px';
            zAxisControlsContainer.style.alignItems = 'center';
            
            // Create table container that will be replaced on dropdown change
            tableContainer = document.createElement('div');
            
            zAxisHeaders.forEach((zHeader, zIndex) => {
                const controlGroup = document.createElement('div');
                controlGroup.style.display = 'flex';
                controlGroup.style.alignItems = 'center';
                controlGroup.style.gap = '8px';
                
                // Get label for the dimension
                const dimensionLabel = getMemberLabel(zHeader.dimensionName, 'xbrl:label', 'en', xbrlModel, displayMode) || zHeader.dimensionName;
                
                const label = document.createElement('label');
                label.textContent = dimensionLabel + ':';
                label.style.fontWeight = 'bold';
                
                const select = document.createElement('select');
                select.style.padding = '5px';
                select.style.minWidth = '200px';
                
                // Add options for each member
                zHeader.members.forEach((member, memberIndex) => {
                    const option = document.createElement('option');
                    option.value = memberIndex;
                    option.textContent = member.label;
                    
                    // Select the current value if set, otherwise select first
                    if (selectedZValues[zHeader.dimensionName] !== undefined) {
                        if (memberIndex === selectedZValues[zHeader.dimensionName]) {
                            option.selected = true;
                        }
                    } else if (memberIndex === 0) {
                        option.selected = true;
                        selectedZValues[zHeader.dimensionName] = 0;
                    }
                    
                    select.appendChild(option);
                });
                
                // Handle dropdown change - re-render only the table, not the controls
                select.addEventListener('change', (e) => {
                    selectedZValues[zHeader.dimensionName] = parseInt(e.target.value);
                    
                    // Clear only the table container and re-render the table
                    tableContainer.innerHTML = '';
                    const newTable = createDataTable(dataTable, cube, zValue, taxonomyData, displayMode, selectedZValues, xbrlModel, relevantFacts, zAxisHeaders);
                    tableContainer.appendChild(newTable);
                });
                
                controlGroup.appendChild(label);
                controlGroup.appendChild(select);
                zAxisControlsContainer.appendChild(controlGroup);
            });
            
            gridContainer.appendChild(zAxisControlsContainer);
            gridContainer.appendChild(tableContainer);
        }
    }

    // Create and append the table
    const table = createDataTable(dataTable, cube, zValue, taxonomyData, displayMode, selectedZValues, xbrlModel, relevantFacts, zAxisHeaders);
    
    if (tableContainer) {
        // If we have zAxis controls, append to the table container
        tableContainer.appendChild(table);
    } else {
        // No zAxis controls, append directly to grid container
        gridContainer.appendChild(table);
    }

    return gridContainer;
}

/**
 * Build the dimension combination for a specific cell
 * Combines dimensions from x-axis, y-axis, z-axis, and tablePoints
 */
function buildCellDimensions(xCombo, yCombo, xAxisHeaders, yAxisHeaders, zAxisHeaders, selectedZValues, dataTable, xComboIdx, yComboIdx, networkHierarchy) {
    const dimensions = {};
    
    // Check if this is a gridLayout - if so, use different logic
    const isGridLayout = dataTable.tableType === 'gridLayout';
    
    if (isGridLayout) {
        // For gridLayout, dimensions come from gridAxis and tablePoints
        // X-axis dimensions from gridAxis
        if (dataTable.xAxis?.gridAxis?.axisItems && xComboIdx < dataTable.xAxis.gridAxis.axisItems.length) {
            const axisItem = dataTable.xAxis.gridAxis.axisItems[xComboIdx];
            if (axisItem.dimensions) {
                Object.assign(dimensions, axisItem.dimensions);
            }
        }
        
        // Y-axis dimensions from gridAxis
        if (dataTable.yAxis?.gridAxis) {
            // Handle axisItems
            if (dataTable.yAxis.gridAxis.axisItems && yComboIdx < dataTable.yAxis.gridAxis.axisItems.length) {
                const axisItem = dataTable.yAxis.gridAxis.axisItems[yComboIdx];
                if (axisItem.dimensions) {
                    Object.assign(dimensions, axisItem.dimensions);
                }
            }
            // Handle axisGroups - dimensions come from the network hierarchy
            else if (dataTable.yAxis.gridAxis.axisGroups && dataTable.yAxis.gridAxis.axisGroups.length > 0) {
                // For gridLayout with axisGroups, get the actual dimension value from networkHierarchy
                if (networkHierarchy && yComboIdx < networkHierarchy.length) {
                    const networkMember = networkHierarchy[yComboIdx];
                    // Use the concept qname from the network member
                    const group = dataTable.yAxis.gridAxis.axisGroups[0]; // Assume single group for now
                    if (group.dimensionName && networkMember.qname) {
                        dimensions[group.dimensionName] = networkMember.qname;
                    }
                } else {
                    // Fallback to axisId if networkHierarchy not available
                    let currentRow = 0;
                    for (const group of dataTable.yAxis.gridAxis.axisGroups) {
                        const groupStart = group.axisStart || 1;
                        const groupSize = group.axisIds ? group.axisIds.length : 0;
                        
                        if (yComboIdx >= currentRow && yComboIdx < currentRow + groupSize) {
                            // This row is in this group
                            const indexInGroup = yComboIdx - currentRow;
                            const axisId = group.axisIds[indexInGroup];
                            
                            // For axisGroups, the dimension comes from dimensionName
                            if (group.dimensionName) {
                                dimensions[group.dimensionName] = axisId;
                            }
                            break;
                        }
                        currentRow += groupSize;
                    }
                }
            }
        }
    } else {
        // For cubeLayout, use the traditional axis headers approach
        // Add x-axis dimensions
        if (xCombo && xAxisHeaders) {
            xCombo.forEach((member, index) => {
                if (xAxisHeaders[index] && xAxisHeaders[index].dimensionName) {
                    // Skip optional dimensions (Total columns) - they should not be included in coordinates
                    if (member.isOptional) {
                        return;
                    }
                    const dimName = xAxisHeaders[index].dimensionName;
                    dimensions[dimName] = member.qname || member.label;
                }
            });
        }
        
        // Add y-axis dimensions
        if (yCombo && yAxisHeaders) {
            yCombo.forEach((member, index) => {
                if (yAxisHeaders[index] && yAxisHeaders[index].dimensionName) {
                    // Skip optional dimensions (Total columns) - they should not be included in coordinates
                    if (member.isOptional) {
                        return;
                    }
                    const dimName = yAxisHeaders[index].dimensionName;
                    dimensions[dimName] = member.qname || member.label;
                }
            });
        }
    }
    
    // Add z-axis dimensions (same for both layout types)
    if (zAxisHeaders && zAxisHeaders.length > 0 && selectedZValues) {
        zAxisHeaders.forEach(zHeader => {
            if (zHeader.dimensionName && selectedZValues[zHeader.dimensionName] !== undefined) {
                const memberIndex = selectedZValues[zHeader.dimensionName];
                if (zHeader.members && zHeader.members[memberIndex]) {
                    const member = zHeader.members[memberIndex];
                    dimensions[zHeader.dimensionName] = member.qname || member.label;
                }
            }
        });
    }
    
    // Check for tablePoints that apply to this cell
    // NOTE: tablePoints use 1-based indexing, so we need to add 1 to our 0-based indices
    if (dataTable.tablePoints && Array.isArray(dataTable.tablePoints)) {
        dataTable.tablePoints.forEach(tablePoint => {
            if (tablePoint.gridCoordinates) {
                const coords = tablePoint.gridCoordinates;
                
                // Check if this tablePoint applies to the current cell
                // Convert 0-based indices to 1-based coordinates for comparison
                let matches = true;
                
                // Check xAxis coordinate (1-based)
                if (coords.xAxis !== undefined) {
                    const coordX = String(coords.xAxis);
                    const cellX = String(xComboIdx + 1);  // Convert to 1-based
                    if (coordX !== cellX) {
                        matches = false;
                    }
                }
                
                // Check yAxis coordinate (1-based)
                if (coords.yAxis !== undefined) {
                    const coordY = String(coords.yAxis);
                    const cellY = String(yComboIdx + 1);  // Convert to 1-based
                    if (coordY !== cellY) {
                        matches = false;
                    }
                }
                
                // If this tablePoint matches the current cell, add its dimensions
                if (matches && tablePoint.dimensions) {
                    Object.entries(tablePoint.dimensions).forEach(([dimName, dimValue]) => {
                        dimensions[dimName] = dimValue;
                    });
                }
            }
        });
    }
    
    return dimensions;
}

/**
 * Create the actual data table (separated from controls)
 */
function createDataTable(dataTable, cube, zValue, taxonomyData, displayMode, selectedZValues, xbrlModel, relevantFacts, zAxisHeaders) {
    // Check if this is a gridLayout table type
    const isGridLayout = dataTable.tableType === 'gridLayout';
    
    // Detect which axis has gridHeaders
    const xAxisHasGridHeaders = isGridLayout && dataTable.xAxis?.gridHeaders;
    const yAxisHasGridHeaders = isGridLayout && dataTable.yAxis?.gridHeaders;
    
    let xAxisHeaders, yAxisHeaders, xAxisMemberCombinations, yAxisMemberCombinations;
    let xAxisLabelGroups = null, yAxisLabelGroups = null;
    
    // Always process axisHeaders for label information (for both gridLayout and cubeLayout)
    const xAxisHeadersForLabels = getAxisHeaderInfo(dataTable.xAxis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube);
    const yAxisHeadersForLabels = getAxisHeaderInfo(dataTable.yAxis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube);
    
    if (isGridLayout) {
        // For gridLayout, use gridAxis for structure but axisHeaders for labels
        // Set xAxisHeaders/yAxisHeaders for label info (will be used for rendering labels)
        xAxisHeaders = xAxisHeadersForLabels;
        yAxisHeaders = yAxisHeadersForLabels;
        
        // Handle X-axis gridAxis
        if (dataTable.xAxis?.gridAxis?.axisItems) {
            // Create combinations based on gridAxis structure
            xAxisMemberCombinations = [];
            xAxisLabelGroups = [];
            
            dataTable.xAxis.gridAxis.axisItems.forEach(axisItem => {
                // Each axisItem represents one column
                xAxisLabelGroups.push(axisItem.axisId);
                
                // Build member combination for this axisItem based on its dimensions and xAxisHeaders
                const xCombo = [];
                if (xAxisHeadersForLabels && axisItem.dimensions) {
                    // For each xAxisHeader, find the corresponding dimension value in axisItem
                    xAxisHeadersForLabels.forEach(xHeader => {
                        const memberQName = axisItem.dimensions[xHeader.dimensionName];
                        if (memberQName) {
                            // Look up the member label
                            const memberLabel = xbrlModel.labels.find(l => 
                                l.relatedName === memberQName && l.labelType === xHeader.labelType
                            );
                            xCombo.push({
                                qname: memberQName,
                                label: memberLabel ? memberLabel.value : memberQName,
                                dimensionName: xHeader.dimensionName
                            });
                        }
                    });
                }
                xAxisMemberCombinations.push(xCombo);
            });
        } else {
            xAxisMemberCombinations = [[]];
        }
        
        // Handle Y-axis gridAxis
        if (dataTable.yAxis?.gridAxis) {
            yAxisMemberCombinations = [];
            yAxisLabelGroups = [];
            
            // Handle axisItems
            if (dataTable.yAxis.gridAxis.axisItems) {
                dataTable.yAxis.gridAxis.axisItems.forEach(axisItem => {
                    yAxisLabelGroups.push(axisItem.axisId);
                    
                    // Build member combination for this axisItem based on its dimensions and yAxisHeaders
                    const yCombo = [];
                    if (yAxisHeadersForLabels && axisItem.dimensions) {
                        // For each yAxisHeader, find the corresponding dimension value in axisItem
                        yAxisHeadersForLabels.forEach(yHeader => {
                            const memberQName = axisItem.dimensions[yHeader.dimensionName];
                            if (memberQName) {
                                // Look up the member label
                                const memberLabel = xbrlModel.labels.find(l => 
                                    l.relatedName === memberQName && l.labelType === yHeader.labelType
                                );
                                yCombo.push({
                                    qname: memberQName,
                                    label: memberLabel ? memberLabel.value : memberQName,
                                    dimensionName: yHeader.dimensionName
                                });
                            }
                        });
                    }
                    yAxisMemberCombinations.push(yCombo);
                });
            }
            // Handle axisGroups
            else if (dataTable.yAxis.gridAxis.axisGroups) {
                dataTable.yAxis.gridAxis.axisGroups.forEach(group => {
                    if (group.axisIds) {
                        group.axisIds.forEach(axisId => {
                            yAxisLabelGroups.push(axisId);
                            yAxisMemberCombinations.push([]);
                        });
                    }
                });
            }
        } else {
            yAxisMemberCombinations = [[]];
        }
        
    } else {
        // For cubeLayout (traditional), use axisHeaders
        xAxisHeaders = getAxisHeaderInfo(dataTable.xAxis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube);
        yAxisHeaders = getAxisHeaderInfo(dataTable.yAxis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube);

        // Generate all combinations of y-axis members (cartesian product)
        yAxisMemberCombinations = generateMemberCombinations(yAxisHeaders);

        // Generate all combinations of x-axis members (cartesian product)
        const allXAxisMemberCombinations = generateMemberCombinations(xAxisHeaders);
        
        // Determine if x-axis has explicitly defined members (via axisMembers or axisNetwork)
        const hasExplicitXAxisMembers = dataTable.xAxis?.axisHeaders?.some(header => 
            header.axisMembers || header.axisNetwork
        );
        
        // Filter to only include x-axis combinations that have at least one fact
        // BUT only if members were NOT explicitly defined
        if (hasExplicitXAxisMembers) {
            // Keep all combinations when members are explicitly defined
            xAxisMemberCombinations = allXAxisMemberCombinations;
        } else {
            // Filter to only show combinations with facts when auto-detecting from facts
            xAxisMemberCombinations = allXAxisMemberCombinations.filter(xCombo => {
                return yAxisMemberCombinations.some(yCombo => {
                    const matchingFacts = findMatchingFacts(relevantFacts, xCombo, yCombo, xAxisHeaders, yAxisHeaders, zAxisHeaders, selectedZValues, cube);
                    return matchingFacts.length > 0;
                });
            });
        }

        // Handle axisLabelsGroup for both axes
        if (dataTable.xAxis?.axisLabelsGroup) {
            if (dataTable.xAxis.axisLabelsGroup.valueArray) {
                xAxisLabelGroups = dataTable.xAxis.axisLabelsGroup.valueArray;
            } else if (dataTable.xAxis.axisLabelsGroup.range) {
                xAxisLabelGroups = generateRangeLabels(dataTable.xAxis.axisLabelsGroup.range, xAxisMemberCombinations.length);
            }
        }
        
        if (dataTable.yAxis?.axisLabelsGroup) {
            if (dataTable.yAxis.axisLabelsGroup.valueArray) {
                yAxisLabelGroups = dataTable.yAxis.axisLabelsGroup.valueArray;
            } else if (dataTable.yAxis.axisLabelsGroup.range) {
                yAxisLabelGroups = generateRangeLabels(dataTable.yAxis.axisLabelsGroup.range, yAxisMemberCombinations.length);
            }
        }
    }

    // Create table
    const table = document.createElement('table');
    table.style.borderCollapse = 'collapse';
    table.style.border = '1px solid #ccc';

    // Calculate number of y-axis header columns
    const yAxisHeaderCount = yAxisHeaders.length;

    // Determine total header rows (including axisLabelsGroup row if present)
    const totalXAxisRows = xAxisHeaders.length + (xAxisLabelGroups ? 1 : 0);

    // Pre-calculate network hierarchy for gridLayout if yAxis has a network
    // BUT ONLY if using axisGroups (not axisItems) - axisItems already specify members explicitly
    let networkHierarchy = null;
    let fullNetworkHierarchy = null; // Keep full hierarchy for parent lookups
    let maxNetworkDepth = 0;
    if (isGridLayout && yAxisHeaders && yAxisHeaders.length > 0 && !dataTable.yAxis?.gridAxis?.axisItems) {
        // Check if any yAxisHeader has a network
        const networkHeader = yAxisHeaders.find(h => dataTable.yAxis?.axisHeaders?.find(ah => 
            ah.dimensionName === h.dimensionName && ah.axisNetwork
        ));
        
        if (networkHeader) {
            const axisHeaderDef = dataTable.yAxis.axisHeaders.find(ah => 
                ah.dimensionName === networkHeader.dimensionName && ah.axisNetwork
            );
            
            // Find the network
            const network = xbrlModel?.networks?.find(n => n.name === axisHeaderDef.axisNetwork);
            if (network) {
                fullNetworkHierarchy = getNetworkHierarchyWithParents(
                    network,
                    axisHeaderDef.labelType,
                    axisHeaderDef.language,
                    xbrlModel,
                    displayMode
                );
                
                // Filter to only include leaf nodes (nodes that don't have children)
                // and exclude the root level (level 0)
                const sources = new Set(network.relationships.map(r => r.source));
                networkHierarchy = fullNetworkHierarchy.filter(node => {
                    // Exclude root level
                    if (node.level === 0) return false;
                    // Only include leaf nodes (nodes that are not sources of any relationship)
                    return !sources.has(node.qname);
                });
                
                // Calculate max depth for column count (excluding root level 0)
                // This is the depth of parent levels that will show as spanning headers
                const maxLevel = Math.max(...fullNetworkHierarchy.map(m => m.level));
                maxNetworkDepth = maxLevel; // Don't add 1 since we're excluding level 0
            }
        }
    }

    // Get gridHeaders from whichever axis has them
    const yGridHeaders = yAxisHasGridHeaders ? dataTable.yAxis.gridHeaders : null;
    const xGridHeaders = xAxisHasGridHeaders ? dataTable.xAxis.gridHeaders : null;
    const maxYGridHeaderLevel = yGridHeaders ? Math.max(...yGridHeaders.map(gh => gh.labelLevel)) : 0;
    const maxXGridHeaderLevel = xGridHeaders ? Math.max(...xGridHeaders.map(gh => gh.labelLevel)) : 0;
    
    // Create header rows for x-axis
    if (isGridLayout && xAxisLabelGroups && xAxisLabelGroups.length > 0) {
        // For gridLayout, create header rows with labels from axisHeaders (if defined) + axisIds
        // Calculate Y-axis column count (gridHeaders levels + Row ID, or network hierarchy columns + Row ID, or member labels + Row ID)
        let yAxisColCount;
        if (yGridHeaders) {
            // gridHeaders define hierarchical row labels - need columns for each level + 1 for row ID
            yAxisColCount = maxYGridHeaderLevel + 1;
        } else if (networkHierarchy && maxNetworkDepth > 0) {
            yAxisColCount = maxNetworkDepth + 1;
        } else if (yAxisHeaders && yAxisHeaders.length > 0) {
            // For axisItems with axisHeaders, count member label columns + axisId column
            yAxisColCount = yAxisHeaders.length + 1;
        } else {
            yAxisColCount = 1;
        }
        
        // If xAxisHeaders has members, create label rows
        if (xAxisHeaders && xAxisHeaders.length > 0 && xAxisHeaders.some(h => h.members && h.members.length > 0)) {
            xAxisHeaders.forEach((xHeader, headerIndex) => {
                const headerRow = document.createElement('tr');
                headerRow.style.backgroundColor = '#f5f5f5';
                
                // Add empty cell for y-axis columns
                // When yAxis has gridHeaders, don't use rowSpan - each row gets its own empty cell
                const yAxisHeaderCell = document.createElement('th');
                yAxisHeaderCell.style.border = '1px solid #ccc';
                yAxisHeaderCell.style.padding = '8px';
                yAxisHeaderCell.style.backgroundColor = '#e9ecef';
                yAxisHeaderCell.colSpan = yAxisColCount;
                
                // Only use rowSpan when yAxis does NOT have gridHeaders
                if (!yGridHeaders && headerIndex === 0) {
                    yAxisHeaderCell.rowSpan = xAxisHeaders.length + 1; // +1 for axisId row
                }
                headerRow.appendChild(yAxisHeaderCell);
                
                // For gridLayout, we need to match labels from axisHeaders with columns defined by gridAxis
                // Show member labels for each column
                xAxisLabelGroups.forEach((axisId, idx) => {
                    const headerCell = document.createElement('th');
                    
                    // Try to find matching member from xAxisHeaders
                    // For gridLayout, axisItems have dimensions - we can try to match those
                    let labelText = '';
                    if (dataTable.xAxis?.gridAxis?.axisItems && idx < dataTable.xAxis.gridAxis.axisItems.length) {
                        const axisItem = dataTable.xAxis.gridAxis.axisItems[idx];
                        if (axisItem.dimensions && xHeader.dimensionName) {
                            const dimValue = axisItem.dimensions[xHeader.dimensionName];
                            if (dimValue) {
                                // Find the label for this dimension value
                                const member = xHeader.members.find(m => m.qname === dimValue);
                                if (member) {
                                    labelText = member.label;
                                }
                            }
                        }
                    }
                    
                    headerCell.textContent = labelText;
                    headerCell.classList.add('AxisHeader');
                    headerCell.style.border = '1px solid #ccc';
                    headerCell.style.padding = '8px';
                    headerCell.style.fontWeight = 'bold';
                    headerCell.style.textAlign = 'center';
                    headerCell.style.backgroundColor = '#f0f0f0';
                    headerRow.appendChild(headerCell);
                });
                
                table.appendChild(headerRow);
            });
        }
        
        // Add xGridHeaders rows if defined (render BEFORE axisId row)
        if (xGridHeaders && xGridHeaders.length > 0) {
            // Build cell structure for each level
            // rowCells[level] = array of {label, colSpan, rowSpan, isBlank}
            const rowCells = {};
            for (let level = maxXGridHeaderLevel; level >= 1; level--) {
                rowCells[level] = [];
            }
            
            // Process gridHeaders array to build cell definitions
            let currentColIdx = 0; // Track which physical column we're at
            
            for (let i = 0; i < xGridHeaders.length; i++) {
                const gh = xGridHeaders[i];
                const level = gh.labelLevel;
                
                if (gh.rollUpLocation === 'none') {
                    // This is a parent that spans its children but doesn't create a data column
                    // Count how many items until we find the next item at this same level or higher
                    let childCount = 0;
                    for (let j = i + 1; j < xGridHeaders.length; j++) {
                        const nextItem = xGridHeaders[j];
                        if (nextItem.labelLevel >= level) {
                            break;
                        }
                        if (nextItem.rollUpLocation !== 'none') {
                            childCount++;
                        }
                    }
                    
                    // Calculate rowSpan: check if there are items at levels below
                    let hasChildrenBelow = false;
                    for (let j = i + 1; j < xGridHeaders.length && xGridHeaders[j].labelLevel < level; j++) {
                        hasChildrenBelow = true;
                        break;
                    }
                    const rowSpan = hasChildrenBelow ? 1 : level;
                    
                    // Add cell at this level
                    rowCells[level].push({
                        label: gh.label,
                        colSpan: childCount,
                        rowSpan: rowSpan,
                        isBlank: false,
                        rollUpLocation: 'none'
                    });
                } else if (gh.rollUpLocation === 'start') {
                    // This creates TWO cells: a blank rollup cell and a label cell
                    // Count children (items at lower levels until we find same/higher level)
                    let childCount = 0;
                    for (let j = i + 1; j < xGridHeaders.length; j++) {
                        const nextItem = xGridHeaders[j];
                        if (nextItem.labelLevel >= level) {
                            break;
                        }
                        if (nextItem.rollUpLocation !== 'none') {
                            childCount++;
                        }
                    }
                    
                    // Blank rollup cell: colSpan=1, rowSpan=level
                    rowCells[level].push({
                        label: '',
                        colSpan: 1,
                        rowSpan: level,
                        isBlank: true,
                        rollUpLocation: 'start'
                    });
                    
                    // Label cell: colSpan=childCount, rowSpan=1
                    rowCells[level].push({
                        label: gh.label,
                        colSpan: childCount,
                        rowSpan: 1,
                        isBlank: false,
                        rollUpLocation: 'start'
                    });
                    
                    currentColIdx += 1 + childCount;
                } else if (gh.rollUpLocation === 'end') {
                    // This creates TWO cells: a label cell and a blank rollup cell (reversed order from 'start')
                    // For 'end', the parent comes AFTER its children in the array
                    // Count children BACKWARDS (items at lower levels until we find same/higher level)
                    let childCount = 0;
                    for (let j = i - 1; j >= 0; j--) {
                        const prevItem = xGridHeaders[j];
                        if (prevItem.labelLevel >= level) {
                            break;
                        }
                        if (prevItem.rollUpLocation !== 'none') {
                            childCount++;
                        }
                    }
                    
                    // Label cell: colSpan=childCount, rowSpan=1
                    rowCells[level].push({
                        label: gh.label,
                        colSpan: childCount,
                        rowSpan: 1,
                        isBlank: false,
                        rollUpLocation: 'end'
                    });
                    
                    // Blank rollup cell: colSpan=1, rowSpan=level  
                    rowCells[level].push({
                        label: '',
                        colSpan: 1,
                        rowSpan: level,
                        isBlank: true,
                        rollUpLocation: 'end'
                    });
                    
                    currentColIdx += childCount + 1;
                } else {
                    // Regular item (no rollUpLocation or other values)
                    // Check if next item is at a lower level (has children)
                    let hasChildren = false;
                    if (i + 1 < xGridHeaders.length && xGridHeaders[i + 1].labelLevel < level) {
                        // Next item is at lower level, but check if it belongs to a later parent with rollUpLocation: end
                        // Look ahead to see if there's a rollUpLocation: end at the same level that claims those children
                        let foundEndParent = false;
                        for (let j = i + 1; j < xGridHeaders.length; j++) {
                            const futureItem = xGridHeaders[j];
                            if (futureItem.labelLevel === level && futureItem.rollUpLocation === 'end') {
                                // Found a parent at same level with rollUpLocation: end
                                // This parent claims the children between i+1 and j
                                foundEndParent = true;
                                break;
                            }
                            if (futureItem.labelLevel >= level && futureItem.rollUpLocation !== 'end') {
                                // Found an item at same or higher level that's not a rollup end
                                // So the children do belong to current item
                                break;
                            }
                        }
                        hasChildren = !foundEndParent;
                    }
                    
                    const colSpan = 1;
                    const rowSpan = hasChildren ? 1 : level;
                    
                    rowCells[level].push({
                        label: gh.label,
                        colSpan: colSpan,
                        rowSpan: rowSpan,
                        isBlank: false,
                        rollUpLocation: gh.rollUpLocation || 'default'
                    });
                    
                    currentColIdx++;
                }
            }
            
            // Now render the rows
            for (let level = maxXGridHeaderLevel; level >= 1; level--) {
                const headerRow = document.createElement('tr');
                headerRow.style.backgroundColor = '#f5f5f5';
                
                // Add y-axis header cell (only on first row)
                if (level === maxXGridHeaderLevel) {
                    const yAxisCell = document.createElement('th');
                    yAxisCell.style.border = '1px solid #ccc';
                    yAxisCell.style.padding = '8px';
                    yAxisCell.style.backgroundColor = '#e9ecef';
                    yAxisCell.colSpan = yAxisColCount;
                    yAxisCell.rowSpan = maxXGridHeaderLevel;
                    
                    // Use label from yAxisHeaders - this cell shows what's on the y-axis
                    if (yAxisHeaders && yAxisHeaders.length > 0) {
                        const labels = [];
                        yAxisHeaders.forEach(yHeader => {
                            const dimDef = xbrlModel.dimensions.find(d => d.name === yHeader.dimensionName);
                            if (dimDef) {
                                const dimLabel = xbrlModel.labels.find(l => l.relatedName === yHeader.dimensionName && l.labelType === yHeader.labelType);
                                if (dimLabel) {
                                    labels.push(dimLabel.value);
                                }
                            }
                        });
                        if (labels.length > 0) {
                            yAxisCell.textContent = labels.join(', ');
                        }
                    }
                    
                    headerRow.appendChild(yAxisCell);
                }
                
                // Render cells for this level
                const cells = rowCells[level];
                cells.forEach((cellDef, index) => {
                    const cell = document.createElement('th');
                    cell.textContent = cellDef.label;
                    cell.classList.add('GridHeader');
                    cell.style.border = '1px solid #ccc';
                    cell.style.padding = '8px';
                    cell.style.backgroundColor = '#f5f5f5';
                    
                    // Add debug classes
                    if (cellDef.rollUpLocation) {
                        cell.classList.add(`rollup-${cellDef.rollUpLocation}`);
                    }
                    if (cellDef.isBlank) {
                        cell.classList.add('rollup-blank');
                    }
                    cell.classList.add(`level-${level}`);
                    
                    // Check if we should remove border between rollup pairs
                    if (index > 0) {
                        const prevCellDef = cells[index - 1];
                        // Handle rollup-start pairs (blank cell before label cell)
                        if (prevCellDef.isBlank && 
                            prevCellDef.rollUpLocation === 'start' && 
                            prevCellDef.rowSpan > 1 &&
                            cellDef.rollUpLocation === 'start' && 
                            !cellDef.isBlank &&
                            cellDef.colSpan > 1) {
                            // Remove left border from current cell
                            cell.style.borderLeft = 'none';
                            // Remove right border from previous cell
                            const prevCell = headerRow.lastChild;
                            if (prevCell && prevCell.tagName === 'TH') {
                                prevCell.style.borderRight = 'none';
                            }
                        }
                        // Handle rollup-end pairs (label cell before blank cell)
                        if (prevCellDef.rollUpLocation === 'end' && 
                            !prevCellDef.isBlank &&
                            prevCellDef.colSpan > 1 &&
                            cellDef.isBlank && 
                            cellDef.rollUpLocation === 'end' && 
                            cellDef.rowSpan > 1) {
                            // Remove left border from current cell (the blank)
                            cell.style.borderLeft = 'none';
                            // Remove right border from previous cell (the label)
                            const prevCell = headerRow.lastChild;
                            if (prevCell && prevCell.tagName === 'TH') {
                                prevCell.style.borderRight = 'none';
                            }
                        }
                    }
                    
                    if (!cellDef.isBlank) {
                        cell.style.fontWeight = 'bold';
                        cell.style.textAlign = 'center';
                    }
                    
                    if (cellDef.colSpan > 1) {
                        cell.colSpan = cellDef.colSpan;
                    }
                    if (cellDef.rowSpan > 1) {
                        cell.rowSpan = cellDef.rowSpan;
                    }
                    
                    headerRow.appendChild(cell);
                });
                
                table.appendChild(headerRow);
            }
        }
        
        // Check if any axisItems have axisId defined - only create row if at least one does
        const hasAxisIds = xAxisLabelGroups && xAxisLabelGroups.length > 0 && 
                          xAxisLabelGroups.some(axisId => axisId !== undefined && axisId !== null && axisId !== '');
        
        // Add axisId row (AFTER xGridHeaders) - only if axisIds are defined
        if (hasAxisIds) {
            const axisIdRow = document.createElement('tr');
            axisIdRow.classList.add('AxisIDRow');
            axisIdRow.style.backgroundColor = '#f5f5f5';
            
            // Only add empty cell if xAxisHeaders member rows didn't create a rowSpan covering this row
            // rowSpan is used when: !yGridHeaders AND xAxisHeaders has members
            const hasRowSpanFromAbove = !yGridHeaders && xAxisHeaders && xAxisHeaders.length > 0 && 
                                        xAxisHeaders.some(h => h.members && h.members.length > 0);
            
            if (!hasRowSpanFromAbove) {
                // Add empty cell for y-axis columns (yAxisColCount already calculated in outer scope)
                const yAxisHeaderCell = document.createElement('th');
                yAxisHeaderCell.style.border = '1px solid #ccc';
                yAxisHeaderCell.style.padding = '8px';
                yAxisHeaderCell.style.backgroundColor = '#e9ecef';
                yAxisHeaderCell.colSpan = yAxisColCount;
                axisIdRow.appendChild(yAxisHeaderCell);
            }
            
            // Add column header for each axisId
            xAxisLabelGroups.forEach((axisId, idx) => {
                const headerCell = document.createElement('th');
                headerCell.textContent = axisId;
                headerCell.classList.add('AxisID');
                headerCell.style.border = '1px solid #ccc';
                headerCell.style.padding = '8px';
                headerCell.style.fontWeight = 'bold';
                headerCell.style.textAlign = 'center';
                headerCell.style.backgroundColor = '#f8f9fa';
                headerCell.style.cursor = 'help';
            
            // Add tooltip with dimensions from axisItem
            if (dataTable.xAxis?.gridAxis?.axisItems && idx < dataTable.xAxis.gridAxis.axisItems.length) {
                const axisItem = dataTable.xAxis.gridAxis.axisItems[idx];
                if (axisItem.dimensions) {
                    const tooltipLines = [];
                    for (const [dimName, dimValue] of Object.entries(axisItem.dimensions)) {
                        tooltipLines.push(`"${dimName}": "${dimValue}"`);
                    }
                    headerCell.title = tooltipLines.join('\n');
                }
            }
            
            axisIdRow.appendChild(headerCell);
            });
            
            table.appendChild(axisIdRow);
        }
        
    } else if (!isGridLayout && xAxisHeaders.length > 0) {
        // For cubeLayout, use the traditional header generation
        xAxisHeaders.forEach((xHeader, headerIndex) => {
            const headerRow = document.createElement('tr');
            headerRow.style.backgroundColor = '#f5f5f5';
            
            // Add empty cell(s) for y-axis columns (only on first row)
            if (headerIndex === 0) {
                // Add empty cell for y-axis headers with rowSpan to cover all x-axis header rows
                const yAxisHeaderCell = document.createElement('th');
                yAxisHeaderCell.style.border = '1px solid #ccc';
                yAxisHeaderCell.style.padding = '8px';
                yAxisHeaderCell.style.backgroundColor = '#e9ecef';
                yAxisHeaderCell.rowSpan = xAxisHeaders.length + (xAxisLabelGroups ? 1 : 0);
                yAxisHeaderCell.colSpan = yAxisHeaders.length;
                headerRow.appendChild(yAxisHeaderCell);
                
                // Add y-axis labels group header cell if present (after y-axis headers)
                if (yAxisLabelGroups) {
                    const yLabelGroupHeader = document.createElement('th');
                    yLabelGroupHeader.style.border = '1px solid #ccc';
                    yLabelGroupHeader.style.padding = '8px';
                    yLabelGroupHeader.style.backgroundColor = '#e9ecef';
                    yLabelGroupHeader.rowSpan = xAxisHeaders.length + (xAxisLabelGroups ? 1 : 0);
                    headerRow.appendChild(yLabelGroupHeader);
                }
            }

            // Extract labels for this dimension from the filtered combinations
            const labels = xAxisMemberCombinations.map(combo => {
                const member = combo.find(m => m.dimensionName === xHeader.dimensionName);
                return member ? member.label : '';
            });
            
            // Group consecutive identical labels and create cells with colSpan
            let i = 0;
            while (i < labels.length) {
                const currentLabel = labels[i];
                let spanCount = 1;
                
                // Count consecutive identical labels
                while (i + spanCount < labels.length && labels[i + spanCount] === currentLabel) {
                    spanCount++;
                }
                
                // Create cell with appropriate colSpan
                const headerCell = document.createElement('th');
                headerCell.textContent = currentLabel;
                if (spanCount > 1) {
                    headerCell.colSpan = spanCount;
                }
                headerCell.style.border = '1px solid #ccc';
                headerCell.style.padding = '8px';
                headerCell.style.fontWeight = 'bold';
                headerCell.style.textAlign = 'center';
                headerCell.style.backgroundColor = '#f0f0f0';
                headerCell.style.cursor = 'help';
                
                // Add tooltip showing dimension and member
                const member = xAxisMemberCombinations[i].find(m => m.dimensionName === xHeader.dimensionName);
                if (member && xHeader.dimensionName) {
                    const memberQName = member.qname || member.label;
                    headerCell.title = `"${xHeader.dimensionName}": "${memberQName}"`;
                }
                
                headerRow.appendChild(headerCell);
                
                i += spanCount;
            }

            table.appendChild(headerRow);
        });
    }

    // Add axisLabelsGroup row if present for x-axis (only for cubeLayout)
    if (!isGridLayout && xAxisLabelGroups) {
        const labelGroupRow = document.createElement('tr');
        labelGroupRow.style.backgroundColor = '#f5f5f5';
        
        // Skip y-axis cells (they have rowSpan from previous rows)
        
        xAxisLabelGroups.forEach((label, idx) => {
            if (idx < xAxisMemberCombinations.length) {
                const labelCell = document.createElement('th');
                labelCell.textContent = label;
                labelCell.style.border = '1px solid #ccc';
                labelCell.style.padding = '8px';
                labelCell.style.fontWeight = 'bold';
                labelCell.style.textAlign = 'center';
                labelCell.style.backgroundColor = '#f8f9fa';
                labelGroupRow.appendChild(labelCell);
            }
        });
        
        // Fill remaining cells if axisLabelsGroup doesn't cover all columns
        const remainingCells = xAxisMemberCombinations.length - xAxisLabelGroups.length;
        for (let i = 0; i < remainingCells; i++) {
            const emptyCell = document.createElement('th');
            emptyCell.style.border = '1px solid #ccc';
            emptyCell.style.padding = '8px';
            emptyCell.style.backgroundColor = '#f8f9fa';
            labelGroupRow.appendChild(emptyCell);
        }
        
        table.appendChild(labelGroupRow);
    }

    // Pre-calculate rowSpan for dimensions with groupDuplicateLabels (only for cubeLayout)
    const rowSpanInfo = !isGridLayout ? yAxisHeaders.map((header, headerIndex) => {
        if (!header.groupDuplicateLabels) return null;
        
        const spans = [];
        let i = 0;
        while (i < yAxisMemberCombinations.length) {
            const currentLabel = yAxisMemberCombinations[i][headerIndex].label;
            let spanCount = 1;
            
            // Count consecutive rows with the same label for this dimension
            while (i + spanCount < yAxisMemberCombinations.length && 
                   yAxisMemberCombinations[i + spanCount][headerIndex].label === currentLabel) {
                spanCount++;
            }
            
            // Record span info for this group
            for (let j = 0; j < spanCount; j++) {
                spans.push({
                    rowSpan: j === 0 ? spanCount : 0, // 0 means skip this cell
                    isFirst: j === 0
                });
            }
            
            i += spanCount;
        }
        
        return spans;
    }) : [];

    // Create data rows for y-axis combinations
    yAxisMemberCombinations.forEach((yCombo, yComboIdx) => {
        const row = document.createElement('tr');
        
        if (isGridLayout) {
            // Check if yGridHeaders are defined - use those instead of network hierarchy
            if (yGridHeaders && yGridHeaders.length > 0) {
                // First pass: Calculate span for each yGridHeader based on hierarchy
                for (let i = 0; i < yGridHeaders.length; i++) {
                    const gh = yGridHeaders[i];
                    
                    if (gh.rollUpLocation === 'end') {
                        // For "end", count backwards to include all lower-level items
                        // The span includes this item PLUS all items being rolled up
                        let span = 1; // Start with the rollup item itself
                        for (let j = i - 1; j >= 0; j--) {
                            if (yGridHeaders[j].labelLevel >= gh.labelLevel) {
                                // Hit previous item at same or higher level, stop counting
                                break;
                            }
                            span++;
                        }
                        gh.span = span;
                    } else if (gh.rollUpLocation === 'none') {
                        // For "none", this is a visual header that doesn't represent a row
                        // Count forwards to include all lower-level items until next same/higher level
                        let span = 0; // Don't include the header itself
                        for (let j = i + 1; j < yGridHeaders.length; j++) {
                            if (yGridHeaders[j].labelLevel >= gh.labelLevel) {
                                // Hit next item at same or higher level, stop counting
                                break;
                            }
                            span++;
                        }
                        gh.span = span;
                    } else {
                        // For "start" or default, count forwards to include all lower-level items
                        // The span includes this item plus all its children
                        // But first check if lower-level items belong to a later parent with rollUpLocation: end
                        let hasChildren = false;
                        if (i + 1 < yGridHeaders.length && yGridHeaders[i + 1].labelLevel < gh.labelLevel) {
                            // Next item is at lower level, check if it belongs to a later parent with rollUpLocation: end
                            let foundEndParent = false;
                            for (let j = i + 1; j < yGridHeaders.length; j++) {
                                const futureItem = yGridHeaders[j];
                                if (futureItem.labelLevel === gh.labelLevel && futureItem.rollUpLocation === 'end') {
                                    // Found a parent at same level with rollUpLocation: end
                                    foundEndParent = true;
                                    break;
                                }
                                if (futureItem.labelLevel >= gh.labelLevel && futureItem.rollUpLocation !== 'end') {
                                    // Found an item at same or higher level that's not a rollup end
                                    break;
                                }
                            }
                            hasChildren = !foundEndParent;
                        }
                        
                        let span = 1; // Start with current item
                        if (hasChildren) {
                            // Count forward to include children
                            for (let j = i + 1; j < yGridHeaders.length; j++) {
                                if (yGridHeaders[j].labelLevel >= gh.labelLevel) {
                                    // Hit next item at same or higher level, stop counting
                                    break;
                                }
                                span++;
                            }
                        }
                        gh.span = span;
                    }
                }
                
                // Second pass: Calculate axisNumber for each yGridHeader based on array position
                // Items with rollUpLocation="none" don't represent rows, so they skip row numbering
                let rowNumber = 1;
                for (let i = 0; i < yGridHeaders.length; i++) {
                    const gh = yGridHeaders[i];
                    
                    if (gh.rollUpLocation === 'none') {
                        // This is a header-only item, doesn't get a row number
                        gh.axisNumber = null;
                    } else {
                        // Normal item, gets the current row number
                        gh.axisNumber = rowNumber;
                        rowNumber++;
                    }
                }
                
                // Track which levels should be skipped due to colspan from higher levels
                const skipLevels = new Set();
                // Track cells in this row for border removal logic
                const rowCells = [];
                
                // Render cells for each labelLevel from maxYGridHeaderLevel down to 1
                for (let level = maxYGridHeaderLevel; level >= 1; level--) {
                    // Skip this level if it's covered by a colspan from a higher level
                    if (skipLevels.has(level)) {
                        continue;
                    }
                    
                    let cellRendered = false;
                    let shouldSkipCell = false;
                    
                    // Check if any header at this level should render on this row
                    for (const gh of yGridHeaders) {
                        if (gh.labelLevel !== level) continue;
                        
                        // Calculate the render row for this header based on span and rollUpLocation
                        let renderRow;
                        let spanStart;
                        let spanEnd;
                        
                        if (gh.rollUpLocation === 'none') {
                            // This is a header-only item, render at the position of the first child
                            // Find the axisNumber of the next item (first child)
                            const ghIndex = yGridHeaders.indexOf(gh);
                            const nextItem = yGridHeaders[ghIndex + 1];
                            if (nextItem && nextItem.axisNumber !== null) {
                                renderRow = nextItem.axisNumber;
                                spanStart = nextItem.axisNumber;
                                spanEnd = spanStart + gh.span - 1; // span is the count of children
                            } else {
                                // No valid next item, skip rendering
                                continue;
                            }
                        } else if (gh.span && gh.span > 1) {
                            if (gh.rollUpLocation === 'end') {
                                // For "end", axisNumber is the last row, so render at first row of span
                                spanStart = gh.axisNumber - gh.span + 1;
                                spanEnd = gh.axisNumber;
                                renderRow = spanStart;
                            } else {
                                // For "start" or default, axisNumber is the first row
                                spanStart = gh.axisNumber;
                                spanEnd = gh.axisNumber + gh.span - 1;
                                renderRow = spanStart;
                            }
                        } else {
                            // No span
                            renderRow = gh.axisNumber;
                            spanStart = gh.axisNumber;
                            spanEnd = gh.axisNumber;
                        }
                        
                        // Check if we should render this header on the current row
                        if (renderRow === yComboIdx + 1) {
                            const labelCell = document.createElement('th');
                            labelCell.textContent = gh.label;
                            labelCell.classList.add('GridHeader');
                            labelCell.style.border = '1px solid #ccc';
                            labelCell.style.padding = '8px';
                            labelCell.style.fontWeight = 'bold';
                            labelCell.style.backgroundColor = '#f9f9f9';
                            labelCell.style.textAlign = 'left';
                            labelCell.style.whiteSpace = 'normal';
                            labelCell.style.wordBreak = 'break-word';
                            labelCell.style.maxWidth = '200px';
                            labelCell.style.minWidth = '80px';
                            
                            // Apply rowSpan if needed
                            if (gh.span && gh.span > 1) {
                                labelCell.rowSpan = gh.span;
                                // Adjust vertical alignment based on rollUpLocation
                                if (gh.rollUpLocation === 'end') {
                                    labelCell.style.verticalAlign = 'bottom';
                                } else {
                                    labelCell.style.verticalAlign = 'top';
                                }
                            }
                            
                            // Apply colSpan based on labelLevel if no rowSpan or rowSpan is 1
                            if (!gh.span || gh.span === 1) {
                                const colspan = gh.labelLevel;
                                if (colspan > 1) {
                                    labelCell.colSpan = colspan;
                                    // Mark lower levels as skipped for this row
                                    for (let skipLevel = level - 1; skipLevel >= level - colspan + 1; skipLevel--) {
                                        skipLevels.add(skipLevel);
                                    }
                                }
                            }
                            
                            row.appendChild(labelCell);
                            rowCells.push({ element: labelCell, hasText: true });
                            cellRendered = true;
                            break;
                        }
                        // Check if current row is within this header's span (but not the render row)
                        else if (yComboIdx + 1 >= spanStart && yComboIdx + 1 <= spanEnd) {
                            shouldSkipCell = true;
                            break;
                        }
                    }
                    
                    // If no cell was rendered and we shouldn't skip, add empty cell
                    if (!cellRendered && !shouldSkipCell) {
                        const emptyCell = document.createElement('th');
                        emptyCell.style.border = '1px solid #ccc';
                        emptyCell.style.padding = '8px';
                        emptyCell.style.backgroundColor = '#fafafa';
                        row.appendChild(emptyCell);
                        rowCells.push({ element: emptyCell, hasText: false });
                    }
                }
                
                // Remove borders between text cell and blank cells to its right
                for (let i = 0; i < rowCells.length; i++) {
                    if (rowCells[i].hasText) {
                        // Check if all cells to the right are empty
                        let allRightEmpty = true;
                        for (let j = i + 1; j < rowCells.length; j++) {
                            if (rowCells[j].hasText) {
                                allRightEmpty = false;
                                break;
                            }
                        }
                        
                        // If all cells to the right are empty, remove vertical borders
                        if (allRightEmpty && i < rowCells.length - 1) {
                            // Remove right border from text cell
                            rowCells[i].element.style.borderRight = 'none';
                            
                            // Remove left and right borders from empty cells (keep top/bottom)
                            for (let j = i + 1; j < rowCells.length; j++) {
                                rowCells[j].element.style.borderLeft = 'none';
                                rowCells[j].element.style.borderRight = 'none';
                            }
                        }
                    }
                }
            }
            // For gridLayout, show network hierarchy labels + axisId
            else if (networkHierarchy && networkHierarchy.length > 0) {
                // Get the network member for this row (if exists)
                const networkMember = yComboIdx < networkHierarchy.length ? networkHierarchy[yComboIdx] : null;
                
                // Check if groupDuplicateLabels is enabled
                const groupDuplicates = dataTable.yAxis?.axisHeaders?.some(ah => ah.groupDuplicateLabels);
                
                // Track which levels should show labels (for rowSpan calculation)
                const shouldShowCell = [];
                
                if (networkMember && groupDuplicates) {
                    // Check if this is the first occurrence of parent labels
                    // Start from level 1 (since we excluded level 0 root)
                    for (let level = 1; level <= networkMember.level; level++) {
                        // First row always shows all cells
                        if (yComboIdx === 0) {
                            shouldShowCell[level] = true;
                        } else {
                            // Check if the parent at this level changed from the previous row
                            const prevMember = networkHierarchy[yComboIdx - 1];
                            const currentParent = getParentAtLevel(networkMember, fullNetworkHierarchy, level);
                            const prevParent = getParentAtLevel(prevMember, fullNetworkHierarchy, level);
                            
                            shouldShowCell[level] = currentParent?.qname !== prevParent?.qname;
                        }
                    }
                }
                
                // Create cells for each hierarchy level (starting from 1, excluding root level 0)
                for (let level = 1; level <= maxNetworkDepth; level++) {
                    if (networkMember && level <= networkMember.level) {
                        // Find the parent at this level
                        const parentAtLevel = getParentAtLevel(networkMember, fullNetworkHierarchy, level);
                        
                        if (parentAtLevel) {
                            // Check if we should skip this cell (part of rowSpan)
                            if (groupDuplicates && !shouldShowCell[level]) {
                                continue; // Skip this cell - it's part of a rowSpan from a previous row
                            }
                            
                            const labelCell = document.createElement('th');
                            labelCell.textContent = parentAtLevel.label;
                            labelCell.classList.add('NetworkHeader');
                            labelCell.style.border = '1px solid #ccc';
                            labelCell.style.padding = '8px';
                            labelCell.style.fontWeight = 'bold';
                            labelCell.style.backgroundColor = level === networkMember.level ? '#f9f9f9' : '#f5f5f5';
                            labelCell.style.textAlign = 'left';
                            labelCell.style.cursor = 'help';
                            labelCell.title = `${parentAtLevel.qname} (level ${level})`;
                            
                            // Calculate rowSpan if groupDuplicateLabels is enabled
                            if (groupDuplicates) {
                                let spanCount = 1;
                                for (let i = yComboIdx + 1; i < networkHierarchy.length; i++) {
                                    const nextMember = networkHierarchy[i];
                                    if (nextMember.level < level) {
                                        // Next member is at a shallower level, stop counting
                                        break;
                                    }
                                    const nextParent = getParentAtLevel(nextMember, fullNetworkHierarchy, level);
                                    if (nextParent?.qname === parentAtLevel.qname) {
                                        spanCount++;
                                    } else {
                                        break;
                                    }
                                }
                                if (spanCount > 1) {
                                    labelCell.rowSpan = spanCount;
                                }
                            }
                            
                            row.appendChild(labelCell);
                        }
                    }
                    // Note: If level > networkMember.level, we don't create a cell
                    // This is intentional - the hierarchy doesn't go that deep for this member
                }            } else if (!networkHierarchy || networkHierarchy.length === 0) {
                // No network hierarchy - render member labels from yCombo
                // This handles the case where yAxis has axisHeaders with member dimensions
                yCombo.forEach((member, colIndex) => {
                    const yCell = document.createElement('th');
                    yCell.textContent = member.label;
                    yCell.style.border = '1px solid #ccc';
                    yCell.style.padding = '8px';
                    yCell.style.fontWeight = 'bold';
                    yCell.style.backgroundColor = '#f9f9f9';
                    yCell.style.textAlign = 'left';
                    yCell.style.cursor = 'help';
                    
                    // Add tooltip showing dimension and member
                    if (yAxisHeaders[colIndex] && yAxisHeaders[colIndex].dimensionName) {
                        const dimName = yAxisHeaders[colIndex].dimensionName;
                        const memberQName = member.qname || member.label;
                        yCell.title = `"${dimName}": "${memberQName}"`;
                    }
                    
                    row.appendChild(yCell);
                });
            }
            
            // Add axisId cell (only if axisId is defined)
            if (yAxisLabelGroups && yComboIdx < yAxisLabelGroups.length) {
                const axisId = yAxisLabelGroups[yComboIdx];
                if (axisId !== undefined && axisId !== null && axisId !== '') {
                    const yCell = document.createElement('th');
                    yCell.textContent = axisId;
                    yCell.classList.add('AxisID');
                    yCell.classList.add('AxisHeader');
                    yCell.style.border = '1px solid #ccc';
                    yCell.style.padding = '8px';
                    yCell.style.fontWeight = 'bold';
                    yCell.style.backgroundColor = '#f9f9f9';
                    yCell.style.textAlign = 'left';
                    yCell.style.cursor = 'help';
                
                // Add tooltip with dimensions from axisItem or axisGroup
                if (dataTable.yAxis?.gridAxis?.axisItems && yComboIdx < dataTable.yAxis.gridAxis.axisItems.length) {
                    const axisItem = dataTable.yAxis.gridAxis.axisItems[yComboIdx];
                    if (axisItem.dimensions) {
                        const tooltipLines = [];
                        for (const [dimName, dimValue] of Object.entries(axisItem.dimensions)) {
                            tooltipLines.push(`"${dimName}": "${dimValue}"`);
                        }
                        yCell.title = tooltipLines.join('\n');
                    }
                } else if (dataTable.yAxis?.gridAxis?.axisGroups) {
                    // For axisGroups, find which group this row belongs to
                    let currentRow = 0;
                    for (const group of dataTable.yAxis.gridAxis.axisGroups) {
                        const groupSize = group.axisIds ? group.axisIds.length : 0;
                        if (yComboIdx >= currentRow && yComboIdx < currentRow + groupSize) {
                            const indexInGroup = yComboIdx - currentRow;
                            const axisId = group.axisIds[indexInGroup];
                            if (group.dimensionName) {
                                yCell.title = `"${group.dimensionName}": "${axisId}"`;
                            }
                            break;
                        }
                        currentRow += groupSize;
                    }
                }
                
                row.appendChild(yCell);
                }
            }
        } else {
            // For cubeLayout, use traditional y-axis header cells
            yCombo.forEach((member, colIndex) => {
                // Check if this dimension has groupDuplicateLabels and should be skipped
                const spanInfo = rowSpanInfo[colIndex];
                if (spanInfo && spanInfo[yComboIdx].rowSpan === 0) {
                    // Skip this cell - it's part of a rowSpan group
                    return;
                }
                
                const yCell = document.createElement('th');
                yCell.textContent = member.label;
                yCell.classList.add('AxisHeader');
                yCell.style.border = '1px solid #ccc';
                yCell.style.padding = '8px';
                yCell.style.fontWeight = 'bold';
                yCell.style.backgroundColor = '#f9f9f9';
                yCell.style.textAlign = 'left';
                yCell.style.cursor = 'help';
                
                // Add tooltip showing dimension and member
                if (yAxisHeaders[colIndex] && yAxisHeaders[colIndex].dimensionName) {
                    const dimName = yAxisHeaders[colIndex].dimensionName;
                    const memberQName = member.qname || member.label;
                    yCell.title = `"${dimName}": "${memberQName}"`;
                }
                
                // Apply rowSpan if this dimension groups duplicate labels
                if (spanInfo && spanInfo[yComboIdx].rowSpan > 1) {
                    yCell.rowSpan = spanInfo[yComboIdx].rowSpan;
                }
                
                row.appendChild(yCell);
            });
            
            // Add yAxisLabelsGroup cell if present (after y-axis headers) - only for cubeLayout
            if (yAxisLabelGroups && yComboIdx < yAxisLabelGroups.length) {
                const axisId = yAxisLabelGroups[yComboIdx];
                if (axisId !== undefined && axisId !== null && axisId !== '') {
                    const yLabelCell = document.createElement('th');
                    yLabelCell.textContent = axisId;
                    yLabelCell.classList.add('AxisID');
                    yLabelCell.classList.add('AxisHeader');
                    yLabelCell.style.border = '1px solid #ccc';
                    yLabelCell.style.padding = '8px';
                    yLabelCell.style.fontWeight = 'bold';
                    yLabelCell.style.backgroundColor = '#f8f9fa';
                    yLabelCell.style.textAlign = 'left';
                    row.appendChild(yLabelCell);
                }
            } else if (yAxisLabelGroups) {
                // Empty cell if we're beyond the label group array
                const emptyCell = document.createElement('th');
                emptyCell.style.border = '1px solid #ccc';
                emptyCell.style.padding = '8px';
                emptyCell.style.backgroundColor = '#f8f9fa';
                row.appendChild(emptyCell);
            }
        }

        // Data cells for each x-axis combination (using pre-filtered combinations)
        xAxisMemberCombinations.forEach((xCombo, xComboIdx) => {
            const dataCell = document.createElement('td');
            dataCell.style.border = '1px solid #ccc';
            dataCell.style.padding = '8px';
            dataCell.style.textAlign = 'right';
            dataCell.style.cursor = 'help';
            
            // Build dimension combination for tooltip
            const cellDimensions = buildCellDimensions(
                xCombo, 
                yCombo, 
                xAxisHeaders, 
                yAxisHeaders, 
                zAxisHeaders, 
                selectedZValues,
                dataTable,
                xComboIdx,
                yComboIdx,
                networkHierarchy
            );
            
            // Validate if this dimensional space is valid in the cube
            const isValidCell = cube ? isValidDimensionalSpace(cellDimensions, cube, xbrlModel, dataTable) : true;
            
            // Create tooltip with dimension combinations
            const tooltipLines = [];
            for (const [dimName, dimValue] of Object.entries(cellDimensions)) {
                tooltipLines.push(`"${dimName}": "${dimValue}"`);
            }
            
            // Add validation status to tooltip
            if (!isValidCell) {
                tooltipLines.push('');
                tooltipLines.push('[Invalid dimensional space for this cube]');
            }
            
            dataCell.title = tooltipLines.join('\n');
            
            // Apply dark grey background to invalid cells
            if (!isValidCell) {
                dataCell.style.backgroundColor = '#d3d3d3';
            }
            
            // Find matching facts for this cell
            const matchingFacts = findMatchingFacts(relevantFacts, xCombo, yCombo, xAxisHeaders, yAxisHeaders, zAxisHeaders, selectedZValues, cube);
            
            if (matchingFacts.length === 0) {
                dataCell.textContent = '-';
            } else if (matchingFacts.length === 1) {
                dataCell.textContent = getFactValue(matchingFacts[0]);
            } else {
                // Multiple facts - check if values are the same
                const values = matchingFacts.map(f => getFactValue(f));
                const uniqueValues = [...new Set(values)];
                
                if (uniqueValues.length === 1) {
                    // All values are the same
                    dataCell.textContent = uniqueValues[0];
                } else {
                    // Different values - show first value and highlight in red
                    dataCell.textContent = values[0];
                    dataCell.style.backgroundColor = '#ffcccc';
                    // Append conflict info to existing tooltip
                    dataCell.title = tooltipLines.join('\n') + `\n\nConflict: ${values.join(', ')}`;
                }
            }
            
            row.appendChild(dataCell);
        });

        table.appendChild(row);
    });

    return table;
}

/**
 * Extract all dimension names from a gridAxis structure
 * Handles both axisItems (with dimensions property) and axisGroups (with dimensionName property)
 * @param {Object} gridAxis - The gridAxis object
 * @returns {Array<string>} Array of dimension names
 */
function extractDimensionNamesFromGridAxis(gridAxis) {
    const dimensionNames = new Set();
    
    if (!gridAxis) {
        return [];
    }
    
    // Extract from axisItems
    if (gridAxis.axisItems && Array.isArray(gridAxis.axisItems)) {
        gridAxis.axisItems.forEach(axisItem => {
            if (axisItem.dimensions) {
                Object.keys(axisItem.dimensions).forEach(dimName => {
                    dimensionNames.add(dimName);
                });
            }
        });
    }
    
    // Extract from axisGroups
    if (gridAxis.axisGroups && Array.isArray(gridAxis.axisGroups)) {
        gridAxis.axisGroups.forEach(axisGroup => {
            if (axisGroup.dimensionName) {
                dimensionNames.add(axisGroup.dimensionName);
            }
        });
    }
    
    return Array.from(dimensionNames);
}

/**
 * Validate if a dimensional space is valid in a cube
 * Based on the same logic used in Fact Positions tab
 * @param {Object} cellDimensions - The dimensional space of the cell (e.g., {exp:VG: "exp:x80", xbrl:concept: "exp:mi251"})
 * @param {Object} cube - The cube object
 * @param {Object} xbrlModel - The taxonomy xbrlModel
 * @param {Object} dataTable - The data table object (used to extract Z-axis dimensions)
 * @returns {boolean} True if the dimensional space is valid in the cube
 */
function isValidDimensionalSpace(cellDimensions, cube, xbrlModel, dataTable = null) {
    if (!cube || !cube.cubeDimensions || !cellDimensions) {
        return true; // If no cube or no dimensions, allow by default
    }
    
    // Extract Z-axis dimensions if dataTable is provided
    const zAxisDimensions = new Set();
    if (dataTable && dataTable.zAxis && dataTable.zAxis.gridAxis) {
        const zAxisDimensionNames = extractDimensionNamesFromGridAxis(dataTable.zAxis.gridAxis);
        zAxisDimensionNames.forEach(dimName => zAxisDimensions.add(dimName));
    }
    
    // Also check Z-axis axisHeaders for dimensions
    if (dataTable && dataTable.zAxis && dataTable.zAxis.axisHeaders) {
        dataTable.zAxis.axisHeaders.forEach(header => {
            if (header.dimensionName) {
                zAxisDimensions.add(header.dimensionName);
            }
        });
    }
    
    // Combine cell dimensions with Z-axis dimensions
    const effectiveCellDimensions = { ...cellDimensions };
    
    // For Z-axis dimensions, we need to add them to the effective cell dimensions
    // even if they don't have specific values in cellDimensions
    // This is because Z-axis dimensions apply to all cells
    zAxisDimensions.forEach(dimName => {
        if (!effectiveCellDimensions[dimName]) {
            // Z-axis dimension exists but no value specified
            // This means the cell should be considered as having this dimension
            // but we don't know the specific value yet
            // For validation purposes, we'll mark it as present
            effectiveCellDimensions[dimName] = null;
        }
    });
    
    const cubeDimensionNames = cube.cubeDimensions.map(d => d.dimensionName);
    const cellDimensionNames = Object.keys(effectiveCellDimensions);
    
    // Check if cell has all REQUIRED cube dimensions
    const hasAllRequiredDimensions = cube.cubeDimensions.every(cubeDim => {
        const allowDomainFacts = cubeDim.allowDomainFacts === true;
        const cellHasDimension = cellDimensionNames.includes(cubeDim.dimensionName);
        
        // If allowDomainFacts is true, dimension is optional
        // If allowDomainFacts is false/undefined, dimension is required
        if (!allowDomainFacts && !cellHasDimension) {
            return false; // Required dimension is missing
        }
        
        return true;
    });
    
    if (!hasAllRequiredDimensions) {
        return false;
    }
    
    // Check if all cell dimensions are valid dimensions in the cube
    const cellDimensionsInCube = cellDimensionNames.every(dimName => 
        cubeDimensionNames.includes(dimName)
    );
    
    if (!cellDimensionsInCube) {
        return false;
    }
    
    // Check if the cell's dimension values are valid for this cube
    const isAllowedInCube = cellDimensionNames.every(dimName => {
        const cellValue = effectiveCellDimensions[dimName];
        const cubeDimension = cube.cubeDimensions.find(cd => cd.dimensionName === dimName);
        
        if (!cubeDimension) return false;
        
        // Skip validation for Z-axis dimensions with null values (they're just markers)
        if (cellValue === null && zAxisDimensions.has(dimName)) {
            return true;
        }
        
        // For defaultCube, the concept dimension implicitly includes all concepts
        const isDefaultCube = cube.cubeType === 'xbrl:openCube';
        if (isDefaultCube && dimName === 'xbrl:concept') {
            const isConcept = xbrlModel.concepts?.some(c => c.name === cellValue) ||
                              xbrlModel.abstracts?.some(a => a.name === cellValue);
            return isConcept;
        }
        
        // If cubeDimension has a domainName, check if the value is in that domain
        if (cubeDimension.domainName && dimName === 'xbrl:concept') {
            const domain = xbrlModel.domains?.find(d => d.name === cubeDimension.domainName);
            if (!domain) {
                return true; // Domain not found, conservatively allow
            }
            
            // Check if the concept is in the domain
            if (domain.roots && domain.roots.includes(cellValue)) {
                return true;
            }
            
            if (domain.relationships) {
                const inDomain = domain.relationships.some(rel => 
                    rel.source === cellValue || rel.target === cellValue
                );
                return inDomain;
            }
            
            return false; // Not in domain
        }
        
        // For other dimensions with domainName, check if member is in that domain
        if (cubeDimension.domainName) {
            const domain = xbrlModel.domains?.find(d => d.name === cubeDimension.domainName);
            if (!domain) {
                return true; // Domain not found, conservatively allow
            }
            
            // Check if the member is in the domain
            if (domain.roots && domain.roots.includes(cellValue)) {
                return true;
            }
            
            if (domain.relationships) {
                const inDomain = domain.relationships.some(rel => 
                    rel.source === cellValue || rel.target === cellValue
                );
                return inDomain;
            }
            
            return false; // Not in domain
        }
        
        // No specific validation needed
        return true;
    });
    
    if (!isAllowedInCube) {
        return false;
    }
    
    // Check excludeCubes if defined
    if (cube.excludeCubes && cube.excludeCubes.length > 0) {
        // Find all excluded cubes
        const excludedCubes = cube.excludeCubes.map(excludeName => 
            xbrlModel.cubes?.find(c => c.name === excludeName)
        ).filter(c => c); // Remove nulls
        
        // If the cell is valid in any excluded cube, it's invalid in this cube
        for (const excludedCube of excludedCubes) {
            if (isValidDimensionalSpace(effectiveCellDimensions, excludedCube, xbrlModel, dataTable)) {
                return false; // This dimensional space is excluded
            }
        }
    }
    
    return true; // Passed all validations
}

/**
 * Get relevant facts for a cube (or all facts if no cube specified)
 */
function getRelevantFacts(xbrlModel, cubeName) {
    if (!xbrlModel || !xbrlModel.facts) {
        return [];
    }

    // If no cube specified, return all facts
    if (!cubeName) {
        return xbrlModel.facts;
    }

    // Find the cube
    const cube = xbrlModel.cubes?.find(c => c.name === cubeName);
    if (!cube) {
        return [];
    }

    // Filter facts that match cube dimensions
    // For now, return all facts that have all required cube dimensions
    return xbrlModel.facts.filter(fact => {
        if (!fact.factDimensions) return false;
        
        // Check if fact has all required dimensions from cube
        const cubeDimensions = cube.cubeDimensions?.map(cd => cd.dimensionName) || [];
        
        // For this implementation, we'll be permissive and return facts that have
        // at least the concept dimension
        return fact.factDimensions['xbrl:concept'] !== undefined;
    });
}

/**
 * Extract unique dimension members from facts for a specific dimension
 * Only includes members from facts that have values for ALL dimensions in the axis headers
 */
function extractDimensionMembersFromFacts(facts, dimensionName, xbrlModel, allAxisDimensions) {
    if (!facts || facts.length === 0) {
        return [];
    }

    const memberSet = new Set();
    
    facts.forEach(fact => {
        if (!fact.factDimensions) return;
        
        // Check if this fact has values for all axis dimensions (or at least the current one)
        // If allAxisDimensions is provided, only include facts that have all of them
        if (allAxisDimensions && allAxisDimensions.length > 0) {
            const hasAllDimensions = allAxisDimensions.every(dim => 
                fact.factDimensions[dim] !== undefined
            );
            if (!hasAllDimensions) {
                return; // Skip this fact
            }
        }
        
        if (fact.factDimensions[dimensionName]) {
            const memberValue = fact.factDimensions[dimensionName];
            
            // Handle period dimension specially - extract just date values
            if (dimensionName === 'xbrl:period') {
                // Period can be instant (single date) or duration (start/end)
                if (memberValue.includes('/')) {
                    // Duration format: start/end
                    memberSet.add(memberValue);
                } else {
                    // Instant format
                    memberSet.add(memberValue);
                }
            } else {
                memberSet.add(memberValue);
            }
        }
    });

    // Convert set to sorted array
    return Array.from(memberSet).sort();
}

/**
 * Find facts that match the given axis member combinations
 */
function findMatchingFacts(facts, xCombo, yCombo, xAxisHeaders, yAxisHeaders, zAxisHeaders = [], selectedZValues = {}, cube = null) {
    return facts.filter(fact => {
        if (!fact.factDimensions) return false;
        
        // Build set of dimensions that are in the table axes
        const tableDimensions = new Set();
        xAxisHeaders.forEach(header => tableDimensions.add(header.dimensionName));
        yAxisHeaders.forEach(header => tableDimensions.add(header.dimensionName));
        zAxisHeaders.forEach(header => tableDimensions.add(header.dimensionName));
        
        // Check x-axis dimensions
        for (let i = 0; i < xCombo.length; i++) {
            const member = xCombo[i];
            const header = xAxisHeaders[i];
            
            if (member.isOptional) {
                // Optional dimension - fact should NOT have this dimension
                if (fact.factDimensions[header.dimensionName] !== undefined) {
                    return false;
                }
            } else if (member.qname) {
                // Explicit member - fact must match
                if (fact.factDimensions[header.dimensionName] !== member.qname) {
                    return false;
                }
            } else if (member.label) {
                // May be a direct value (e.g., period, entity, unit)
                const factValue = fact.factDimensions[header.dimensionName];
                if (factValue !== member.label && factValue !== member.qname) {
                    return false;
                }
            }
        }
        
        // Check y-axis dimensions
        for (let i = 0; i < yCombo.length; i++) {
            const member = yCombo[i];
            const header = yAxisHeaders[i];
            
            if (member.isOptional) {
                // Optional dimension - fact should NOT have this dimension
                if (fact.factDimensions[header.dimensionName] !== undefined) {
                    return false;
                }
            } else if (member.qname) {
                // Explicit member - fact must match
                if (fact.factDimensions[header.dimensionName] !== member.qname) {
                    return false;
                }
            } else if (member.label) {
                // May be a direct value
                const factValue = fact.factDimensions[header.dimensionName];
                if (factValue !== member.label && factValue !== member.qname) {
                    return false;
                }
            }
        }
        
        // Check z-axis dimensions (selected values from dropdowns)
        for (let i = 0; i < zAxisHeaders.length; i++) {
            const header = zAxisHeaders[i];
            const selectedMemberIndex = selectedZValues[header.dimensionName];
            
            if (selectedMemberIndex !== undefined && header.members && header.members[selectedMemberIndex]) {
                const selectedMember = header.members[selectedMemberIndex];
                
                if (selectedMember.qname) {
                    // Explicit member - fact must match
                    if (fact.factDimensions[header.dimensionName] !== selectedMember.qname) {
                        return false;
                    }
                } else if (selectedMember.label) {
                    // May be a direct value
                    const factValue = fact.factDimensions[header.dimensionName];
                    if (factValue !== selectedMember.label && factValue !== selectedMember.qname) {
                        return false;
                    }
                }
            }
        }
        
        // Check for extra dimensions: fact should not have dimensions from the cube
        // that are not in the table axes (unless marked as dimensionOptional)
        if (cube && cube.cubeDimensions) {
            for (const cubeDim of cube.cubeDimensions) {
                const dimName = cubeDim.dimensionName;
                
                // Skip if this dimension is in the table axes
                if (tableDimensions.has(dimName)) {
                    continue;
                }
                
                // Check if fact has this dimension
                if (fact.factDimensions[dimName] !== undefined) {
                    // Fact has a dimension that's not in the table - exclude this fact
                    return false;
                }
            }
        }
        
        return true;
    });
}

/**
 * Get the display value from a fact
 */
function getFactValue(fact) {
    if (!fact) return '';
    
    // Check factValues array first
    if (fact.factValues && fact.factValues.length > 0) {
        const factValue = fact.factValues[0];
        if (factValue.value !== undefined) {
            // Format with decimals if specified
            if (factValue.decimals !== undefined) {
                const num = parseFloat(factValue.value);
                if (!isNaN(num)) {
                    return num.toFixed(Math.max(0, factValue.decimals)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                }
            }
            return factValue.value;
        }
    }
    
    // Fallback to value property if it exists
    if (fact.value !== undefined) {
        return fact.value;
    }
    
    return '';
}

/**
 * Get axis header information including all members for each header
 */
function getAxisHeaderInfo(axis, xbrlModel, taxonomyData, displayMode, relevantFacts, cube) {
    if (!axis || !axis.axisHeaders || axis.axisHeaders.length === 0) {
        return [];
    }

    const headerInfoArray = [];

    axis.axisHeaders.forEach(axisHeader => {
        const headerInfo = {
            dimensionName: axisHeader.dimensionName,
            labelType: axisHeader.labelType || 'xbrl:label',
            language: axisHeader.language || 'en',
            groupDuplicateLabels: axisHeader.groupDuplicateLabels || false,
            members: []
        };

        // Get members based on axisMembers, axisNetwork, typedLabel, or facts
        if (axisHeader.axisMembers && axisHeader.axisMembers.length > 0) {
            // Explicit members list
            const members = axisHeader.axisMembers.map(memberQName => ({
                qname: memberQName,
                label: getMemberLabel(memberQName, headerInfo.labelType, headerInfo.language, xbrlModel, displayMode),
                dimensionName: headerInfo.dimensionName
            }));

            // Add optional dimension column if specified
            if (axisHeader.dimensionOptional) {
                const totalMember = {
                    qname: null,
                    label: 'Total',
                    isOptional: true,
                    dimensionName: headerInfo.dimensionName
                };

                if (axisHeader.totalLocation === 'start') {
                    members.unshift(totalMember);
                } else {
                    // Default to 'end'
                    members.push(totalMember);
                }
            }

            headerInfo.members = members;

        } else if (axisHeader.axisNetwork) {
            // Members from network or domain
            let networkMembers = [];
            
            // First check if it's a network
            const network = xbrlModel?.networks?.find(n => n.name === axisHeader.axisNetwork);
            if (network) {
                networkMembers = getNetworkMembers(network, xbrlModel);
            } else {
                // Check if it's a domain
                const domain = xbrlModel?.domains?.find(d => d.name === axisHeader.axisNetwork);
                if (domain) {
                    networkMembers = getDomainMembers(domain, xbrlModel);
                }
            }
            
            if (networkMembers.length > 0) {
                const members = networkMembers.map(memberQName => ({
                    qname: memberQName,
                    label: getMemberLabel(memberQName, headerInfo.labelType, headerInfo.language, xbrlModel, displayMode),
                    dimensionName: headerInfo.dimensionName
                }));

                // Add optional dimension column if specified
                if (axisHeader.dimensionOptional) {
                    const totalMember = {
                        qname: null,
                        label: 'Total',
                        isOptional: true,
                        dimensionName: headerInfo.dimensionName
                    };

                    if (axisHeader.totalLocation === 'start') {
                        members.unshift(totalMember);
                    } else {
                        members.push(totalMember);
                    }
                }

                headerInfo.members = members;
            }

        } else if (axisHeader.typedLabel) {
            // Typed dimension labels
            const typedLabel = axisHeader.typedLabel;
            
            if (typedLabel.range) {
                // Generate labels from range
                const rangeLabels = generateRangeLabels(typedLabel.range);
                headerInfo.members = rangeLabels.map(label => ({
                    qname: null,
                    label: label,
                    isTyped: true,
                    dimensionName: headerInfo.dimensionName
                }));
                
            } else if (typedLabel.use) {
                // Use typed values directly or with transform
                // For now, create placeholder typed labels
                // In a real implementation, you'd need actual data values
                headerInfo.members = [{
                    qname: null,
                    label: `[Typed: ${typedLabel.use}]`,
                    isTyped: true,
                    dimensionName: headerInfo.dimensionName
                }];
            }
        } else {
            // No explicit members - extract from facts
            // Only extract members from facts that have the current dimension
            // Don't filter by other axis dimensions as facts may have partial dimension coverage
            const dimensionMembers = extractDimensionMembersFromFacts(
                relevantFacts, 
                axisHeader.dimensionName, 
                xbrlModel,
                null  // Don't filter by other dimensions
            );
            
            headerInfo.members = dimensionMembers.map(memberQName => ({
                qname: memberQName,
                label: getMemberLabel(memberQName, headerInfo.labelType, headerInfo.language, xbrlModel, displayMode),
                dimensionName: headerInfo.dimensionName
            }));

            // Add optional dimension column if specified
            if (axisHeader.dimensionOptional) {
                const totalMember = {
                    qname: null,
                    label: 'Total',
                    isOptional: true,
                    dimensionName: headerInfo.dimensionName
                };

                if (axisHeader.totalLocation === 'start') {
                    headerInfo.members.unshift(totalMember);
                } else {
                    headerInfo.members.push(totalMember);
                }
            }
        }

        // If still no members and axisLabelsGroup exists at axis level
        if (headerInfo.members.length === 0 && axis.axisLabelsGroup) {
            if (axis.axisLabelsGroup.valueArray) {
                headerInfo.members = axis.axisLabelsGroup.valueArray.map(label => ({
                    qname: null,
                    label: label,
                    dimensionName: headerInfo.dimensionName
                }));
            } else if (axis.axisLabelsGroup.range) {
                const rangeLabels = generateRangeLabels(axis.axisLabelsGroup.range);
                headerInfo.members = rangeLabels.map(label => ({
                    qname: null,
                    label: label,
                    dimensionName: headerInfo.dimensionName
                }));
            }
        }

        if (headerInfo.members.length > 0) {
            headerInfoArray.push(headerInfo);
        }
    });

    return headerInfoArray;
}

/**
 * Get member label from taxonomy labels
 */
function getMemberLabel(memberQName, labelType, language, xbrlModel, displayMode) {
    if (!memberQName) return '';
    
    // Always look for label in taxonomy first (even if displayMode is 'name')
    const label = xbrlModel?.labels?.find(l => 
        l.relatedName === memberQName && 
        l.labelType === labelType && 
        l.language === language
    );

    if (label) {
        return label.value;
    }

    // Fallback to QName if no label found
    // If displayMode is 'name', return the full QName
    // Otherwise use getNodeLabel for prettier formatting
    if (displayMode === 'name') {
        return memberQName;
    }
    
    return getNodeLabel(memberQName, displayMode);
}

/**
 * Get the parent of a network member at a specific level
 */
function getParentAtLevel(member, networkHierarchy, targetLevel) {
    if (!member) return null;
    
    // If this member is at the target level, return it
    if (member.level === targetLevel) {
        return member;
    }
    
    // If this member is above the target level, return null
    if (member.level < targetLevel) {
        return null;
    }
    
    // Find the parent by walking up the hierarchy
    let current = member;
    while (current && current.level > targetLevel) {
        // Find the parent of current
        const parent = networkHierarchy.find(m => m.qname === current.parentQName);
        if (!parent) break;
        current = parent;
    }
    
    return current && current.level === targetLevel ? current : null;
}

/**
 * Get network members with hierarchy preserved (includes parent/abstract items)
 * Returns an array of objects: { qname, label, level, parentQName }
 */
function getNetworkHierarchyWithParents(network, labelType, language, xbrlModel, displayMode) {
    if (!network || !network.relationships) {
        return [];
    }

    const members = [];
    const visited = new Set();
    
    // Helper function to traverse network with depth tracking
    function traverseNetwork(nodeName, level, parentName) {
        if (visited.has(nodeName)) return;
        visited.add(nodeName);
        
        // Add this node (including abstracts)
        const isAbstract = xbrlModel?.abstracts?.some(a => a.name === nodeName);
        members.push({
            qname: nodeName,
            label: getMemberLabel(nodeName, labelType || 'xbrl:label', language || 'en', xbrlModel, displayMode),
            level: level,
            parentQName: parentName,
            isAbstract: isAbstract
        });
        
        // Find relationships where this node is the source
        const childRels = network.relationships.filter(r => r.source === nodeName);
        
        // Sort by order if available
        childRels.sort((a, b) => {
            const orderA = a.order || 0;
            const orderB = b.order || 0;
            return orderA - orderB;
        });
        
        // Process each child
        childRels.forEach(rel => {
            traverseNetwork(rel.target, level + 1, nodeName);
        });
    }
    
    // Start from roots or find root nodes
    const roots = network.roots || [];
    if (roots.length > 0) {
        roots.forEach(root => traverseNetwork(root, 0, null));
    } else {
        // Find nodes that are not targets (these are roots)
        const targets = new Set(network.relationships.map(r => r.target));
        const sources = new Set(network.relationships.map(r => r.source));
        const rootNodes = [...sources].filter(s => !targets.has(s));
        rootNodes.forEach(root => traverseNetwork(root, 0, null));
    }
    
    return members;
}

/**
 * Get network members in order
 */
function getNetworkMembers(network, xbrlModel) {
    if (!network || !network.relationships) {
        return [];
    }

    const members = [];
    const visited = new Set();
    
    // Helper function to traverse network in order
    function traverseNetwork(nodeName) {
        if (visited.has(nodeName)) return;
        visited.add(nodeName);
        
        // Add this node if it's not abstract
        const isAbstract = xbrlModel?.abstracts?.some(a => a.name === nodeName);
        if (!isAbstract) {
            members.push(nodeName);
        }
        
        // Find relationships where this node is the source
        const childRels = network.relationships.filter(r => r.source === nodeName);
        
        // Sort by order if available
        childRels.sort((a, b) => {
            const orderA = a.order || 0;
            const orderB = b.order || 0;
            return orderA - orderB;
        });
        
        // Process each child
        childRels.forEach(rel => {
            traverseNetwork(rel.target);
        });
    }
    
    // Start from roots or find root nodes
    const roots = network.roots || [];
    if (roots.length > 0) {
        roots.forEach(root => traverseNetwork(root));
    } else {
        // Find nodes that are not targets (these are roots)
        const targets = new Set(network.relationships.map(r => r.target));
        const sources = new Set(network.relationships.map(r => r.source));
        const rootNodes = [...sources].filter(s => !targets.has(s));
        rootNodes.forEach(root => traverseNetwork(root));
    }
    
    return members;
}

/**
 * Get ordered members from a domain
 */
function getDomainMembers(domain, xbrlModel) {
    if (!domain || !domain.relationships) {
        return [];
    }

    const members = [];
    const visited = new Set();
    
    // Helper function to traverse domain in order
    function traverseDomain(nodeName) {
        if (visited.has(nodeName)) return;
        visited.add(nodeName);
        
        // Skip the root node itself - we only want the actual members
        if (nodeName !== domain.root) {
            members.push(nodeName);
        }
        
        // Find relationships where this node is the source
        const childRels = domain.relationships.filter(r => r.source === nodeName);
        
        // Sort by order if available
        childRels.sort((a, b) => {
            const orderA = a.order || 0;
            const orderB = b.order || 0;
            return orderA - orderB;
        });
        
        // Process each child
        childRels.forEach(rel => {
            traverseDomain(rel.target);
        });
    }
    
    // Start from the domain root
    if (domain.root) {
        traverseDomain(domain.root);
    }
    
    return members;
}

/**
 * Generate labels from range specification
 */
function generateRangeLabels(range, count) {
    if (!range || !range.startValue) {
        return [];
    }

    const labels = [];
    // Default to xs:integer if dataType is not provided
    const dataType = range.dataType || 'xs:integer';
    const interval = parseFloat(range.interval) || 1;
    const startValue = parseFloat(range.startValue);
    const order = range.order || 'ascending';
    const prefix = range.prefix || '';
    const suffix = range.suffix || '';
    
    // Use stopValue if provided, otherwise generate 'count' labels
    const stopValue = range.stopValue ? parseFloat(range.stopValue) : null;
    const maxIterations = count || 1000; // Use count if provided, otherwise safety limit

    if (dataType === 'xs:integer' || dataType === 'xs:decimal') {
        let current = startValue;
        let iterations = 0;

        if (order === 'ascending') {
            while (iterations < maxIterations) {
                // Stop if we have stopValue and reached it
                if (stopValue !== null && current > stopValue) break;
                
                labels.push(prefix + current.toString() + suffix);
                current += interval;
                iterations++;
            }
        } else {
            while (iterations < maxIterations) {
                // Stop if we have stopValue and reached it
                if (stopValue !== null && current < stopValue) break;
                
                labels.push(prefix + current.toString() + suffix);
                current -= interval;
                iterations++;
            }
        }
    } else {
        // For other data types, just use start value as placeholder
        labels.push(prefix + range.startValue.toString() + suffix);
    }

    return labels;
}

/**
 * Generate all combinations of members across multiple headers (cartesian product)
 */
function generateMemberCombinations(headerInfoArray) {
    if (headerInfoArray.length === 0) {
        return [];
    }

    // Extract member arrays
    const memberArrays = headerInfoArray.map(headerInfo => headerInfo.members);

    // Generate cartesian product
    const combinations = cartesianProduct(...memberArrays);

    return combinations;
}

/**
 * Calculate cartesian product of arrays
 */
function cartesianProduct(...arrays) {
    if (arrays.length === 0) return [];
    if (arrays.length === 1) return arrays[0].map(item => [item]);

    const [first, ...rest] = arrays;
    const restProduct = cartesianProduct(...rest);

    return first.flatMap(item =>
        restProduct.map(combo => [item, ...combo])
    );
}

/**
 * Get axis values from axis definition (deprecated - kept for compatibility)
 */
function getAxisValues(axis, taxonomyData, displayMode) {
    const xbrlModel = getXbrlModel(taxonomyData);
    const headerInfo = getAxisHeaderInfo(axis, xbrlModel, taxonomyData, displayMode);
    
    // For z-axis, we typically want just the first header's members
    if (headerInfo.length > 0) {
        return headerInfo[0].members.map(m => ({
            value: m.qname || m.label,
            label: m.label
        }));
    }
    
    return [];
}

/**
 * Setup display mode filters
 */
export function setupLayoutDisplayModeFilters() {
    // Table templates filter
    const templateFilter = document.getElementById('template-display-mode');
    if (templateFilter) {
        templateFilter.onchange = function() {
            buildTableTemplates(this.value);
        };
    }

    // Data tables filter
    const dataTableFilter = document.getElementById('datatable-display-mode');
    if (dataTableFilter) {
        dataTableFilter.onchange = function() {
            buildDataTables(this.value);
        };
    }
}

/**
 * Initialize layout tab
 */
export function initLayout() {
    console.log('[Layout Builder] Initializing layout');
    setupLayoutDisplayModeFilters();
    buildTableTemplates('name');
    buildDataTables('name');
}
