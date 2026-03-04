/**
 * Taxonomy Builder Module
 * Handles building the main taxonomy tree and taxonomy info panel
 */

import { getTaxonomyData } from './main.js';
import { showDetails } from './details-panel.js';
import { getErrorLabel } from './error-labels.js';
import { getAllQNames, filterQNames, displaySearchResults, refreshSearchData } from './search.js';
import { BUILTIN_OBJECT_TYPES_ARRAY } from './object-types.js';
import { getObjectTypeForQName, validateQNameReferences } from './qname-validator.js';
import { getXbrlModel } from './utils.js';
import { getXbrlModelName } from './taxonomy-loader.js';
import { buildJSONView, getRawTaxonomyData } from './json-view.js';



/**
 * Build the entire taxonomy tree and all tabs
 */
export function buildTree() {
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    console.log('[Taxonomy Builder] Building tree with data:', taxonomyData);
    
    if (xbrlModel) {
        console.log('[Taxonomy Builder] XbrlModel keys:', Object.keys(xbrlModel));
    }
    
    if (!xbrlModel) {
        console.error('[Taxonomy Builder] Invalid taxonomy data structure');
        return;
    }
    
    // Get all container elements
    const taxonomyInfo = document.getElementById('taxonomy-info');
    const networksTree = document.getElementById('networks-tree');
    const conceptsList = document.getElementById('concepts-list');
    const dimensionsList = document.getElementById('dimensions-list');
    const domainClassesList = document.getElementById('domainClasses-list');
    const unitsList = document.getElementById('units-list');
    const membersList = document.getElementById('members-list');
    const abstractsList = document.getElementById('abstracts-list');
    const entitiesList = document.getElementById('entities-list');
    const transformsList = document.getElementById('transforms-list');
    const cubesList = document.getElementById('cubes-list');
    const propertyTypesList = document.getElementById('propertyTypes-list');
    const dataTypesList = document.getElementById('dataTypes-list');
    const cubeTypesList = document.getElementById('cubeTypes-list');
    const labelTypesList = document.getElementById('labelTypes-list');
    const referenceTypesList = document.getElementById('referenceTypes-list');
    const relationshipTypesList = document.getElementById('relationshipTypes-list');
    const modelTypesList = document.getElementById('modelTypes-list');
    
    // Clear only the tree content areas, not the entire networks-tree (to preserve filter)
    taxonomyInfo.innerHTML = '';
    
    const groupsListContainer = document.getElementById('groups-list');
    if (groupsListContainer) {
        groupsListContainer.innerHTML = '';
    }
    
    const networksListContainer = document.getElementById('networks-list');
    if (networksListContainer) {
        networksListContainer.innerHTML = '';
    }
    
    const domainsListContainer = document.getElementById('domains-list');
    if (domainsListContainer) {
        domainsListContainer.innerHTML = '';
    }
    
    conceptsList.innerHTML = '';
    dimensionsList.innerHTML = '';
    domainClassesList.innerHTML = '';
    unitsList.innerHTML = '';
    membersList.innerHTML = '';
    abstractsList.innerHTML = '';
    entitiesList.innerHTML = '';
    transformsList.innerHTML = '';
    cubesList.innerHTML = '';
    propertyTypesList.innerHTML = '';
    dataTypesList.innerHTML = '';
    cubeTypesList.innerHTML = '';
    labelTypesList.innerHTML = '';
    referenceTypesList.innerHTML = '';
    relationshipTypesList.innerHTML = '';
    modelTypesList.innerHTML = '';

    // Build Taxonomy Info
    buildTaxonomyInfo();

    // Build Groups (using modular version)
    if (window.buildGroupsModule) {
        window.buildGroupsModule();
    } else {
        console.warn('[Taxonomy Builder] Groups builder module not loaded yet');
    }

    // Build Networks (using modular version)
    if (window.initNetworks) {
        window.initNetworks();
    } else {
        console.warn('[Taxonomy Builder] Networks builder module not loaded');
    }

    // Build Domains (using modular version)
    if (window.initDomains) {
        window.initDomains();
    } else {
        console.warn('[Taxonomy Builder] Domains builder module not loaded');
    }

    // Build Components (using modular version)
    if (window.buildComponentsList) {
        // Use modular version
        window.buildComponentsList('concepts', conceptsList, 'concept');
        window.buildComponentsList('dimensions', dimensionsList, 'dimension');
        window.buildComponentsList('domainClasses', domainClassesList, 'domainClass');
        window.buildComponentsList('units', unitsList, 'unit');
        window.buildComponentsList('members', membersList, 'member');
        window.buildComponentsList('abstracts', abstractsList, 'abstract');
        window.buildComponentsList('entities', entitiesList, 'entity');
        window.buildComponentsList('transforms', transformsList, 'transform');
        
        // Build Types
        window.buildComponentsList('propertyTypes', propertyTypesList, 'propertyType');
        window.buildComponentsList('dataTypes', dataTypesList, 'dataType');
        window.buildComponentsList('cubeTypes', cubeTypesList, 'cubeType');
        window.buildComponentsList('labelTypes', labelTypesList, 'labelType');
        window.buildComponentsList('referenceTypes', referenceTypesList, 'referenceType');
        window.buildComponentsList('relationshipTypes', relationshipTypesList, 'relationshipType');
        window.buildComponentsList('modelTypes', modelTypesList, 'modelType');
        
        // Build Facts tab (Fact Positions sub-tab)
        const factsList = document.getElementById('facts-list');
        if (window.buildFactsList && factsList) {
            window.buildFactsList(xbrlModel, factsList);
        } else {
            console.warn('[Taxonomy Builder] Facts builder module not loaded or container missing');
        }
        
        // Process and build FactSources tab (Fact Sources sub-tab)
        const factSourcesList = document.getElementById('factSources-list');
        if (window.processFactSources && window.buildFactSourcesList && factSourcesList) {
            // Process factSources asynchronously and then build the UI
            window.processFactSources(taxonomyData).then(() => {
                window.buildFactSourcesList(taxonomyData, factSourcesList);
                
                // Rebuild Facts list to include facts created from factSources
                const factsList = document.getElementById('facts-list');
                if (window.buildFactsList && factsList) {
                    window.buildFactsList(xbrlModel, factsList);
                }
                
                // Rebuild JSON view to show updated facts array
                buildJSONView(xbrlModel, taxonomyData.documentInfo);
                
                // Refresh search to include facts generated from factSources
                refreshSearchData();
                
                // Re-validate QName references to check fact values from factSources against concept dataTypes
                console.log('[Taxonomy Builder] Re-validating facts after factSources processing...');
                const validationErrors = validateQNameReferences(
                    xbrlModel,
                    taxonomyData.documentInfo || null,
                    getRawTaxonomyData()
                );
                // Preserve import-time errors (e.g. oimte:duplicateNamespaceURI) that were collected
                // before buildTree ran — the re-validation above would otherwise discard them.
                const persistentErrors = window._persistentValidationErrors || [];
                window.qnameValidationErrors = validationErrors.concat(persistentErrors);
                if (persistentErrors.length > 0) {
                    console.log(`[Taxonomy Builder] Re-injected ${persistentErrors.length} persistent import-time error(s) after fact-source re-validation`);
                }
                
                // Refresh taxonomy info to display any new validation errors
                buildTaxonomyInfo();
            }).catch(error => {
                console.error('[Taxonomy Builder] Error processing factSources:', error);
                factSourcesList.innerHTML = `<div class="error">Error loading factSources: ${error.message}</div>`;
            });
        } else {
            console.warn('[Taxonomy Builder] FactSources builder module not loaded or container missing');
        }
        
        // Build Layout tab
        if (window.initLayout) {
            window.initLayout();
        } else {
            console.warn('[Taxonomy Builder] Layout builder module not loaded');
        }
    } else {
        console.warn('[Taxonomy Builder] Components builder module not loaded yet');
    }

    // Build Cubes (using modular version)
    if (window.initCubes) {
        window.initCubes();
    } else {
        console.warn('[Taxonomy Builder] Cubes builder module not loaded');
    }
}

/**
 * Build the taxonomy info panel with metadata and statistics
 */
export function buildTaxonomyInfo() {
    const taxonomyData = getTaxonomyData();
    const taxonomyInfo = document.getElementById('taxonomy-info');
    const xbrlModel = getXbrlModel(taxonomyData);
    
    if (!taxonomyData || !taxonomyData.documentInfo || !xbrlModel) {
        taxonomyInfo.innerHTML = '<p>No taxonomy data available.</p>';
        return;
    }

    const docInfo = taxonomyData.documentInfo;
    const taxonomy = xbrlModel;

    // Clear existing content before rebuilding
    taxonomyInfo.innerHTML = '';

    // Create grid for taxonomy properties
    const grid = document.createElement('div');
    grid.style.padding = '10px';
    grid.style.fontSize = '14px';

    // Create table
    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginTop = '10px';

    // Helper function to add row
    function addRow(label, value, isHeader = false) {
        const row = document.createElement('tr');
        const labelCell = document.createElement('td');
        const valueCell = document.createElement('td');
        
        labelCell.textContent = label;
        labelCell.style.fontWeight = 'bold';
        labelCell.style.padding = '8px';
        labelCell.style.borderBottom = '1px solid #ddd';
        labelCell.style.width = '40%';
        labelCell.style.verticalAlign = 'top';
        
        if (typeof value === 'object' && value !== null) {
            valueCell.appendChild(value);
        } else {
            valueCell.textContent = value || 'N/A';
        }
        valueCell.style.padding = '8px';
        valueCell.style.borderBottom = '1px solid #ddd';
        valueCell.style.wordBreak = 'break-word';
        
        if (isHeader) {
            row.style.backgroundColor = '#f0f0f0';
        }
        
        row.appendChild(labelCell);
        row.appendChild(valueCell);
        table.appendChild(row);
    }

    // Model Name
    addRow('Model Name', taxonomy.name);

    // Framework Name
    if (taxonomy.frameworkName) {
        addRow('Framework Name', taxonomy.frameworkName);
    }

    // Version
    if (taxonomy.version) {
        addRow('Version', taxonomy.version);
    }

    // Namespaces
    if (docInfo.namespaces) {
        const namespacesList = document.createElement('div');
        const nsTable = document.createElement('table');
        nsTable.style.width = '100%';
        nsTable.style.fontSize = '12px';
        nsTable.style.borderCollapse = 'collapse';
        
        for (const [prefix, uri] of Object.entries(docInfo.namespaces)) {
            const nsRow = document.createElement('tr');
            const prefixCell = document.createElement('td');
            const uriCell = document.createElement('td');
            
            prefixCell.textContent = prefix + ':';
            prefixCell.style.fontWeight = 'bold';
            prefixCell.style.padding = '4px 8px';
            prefixCell.style.width = '20%';
            prefixCell.style.verticalAlign = 'top';
            prefixCell.style.borderBottom = '1px solid #eee';
            
            uriCell.textContent = uri;
            uriCell.style.padding = '4px 8px';
            uriCell.style.wordBreak = 'break-all';
            uriCell.style.borderBottom = '1px solid #eee';
            
            nsRow.appendChild(prefixCell);
            nsRow.appendChild(uriCell);
            nsTable.appendChild(nsRow);
        }
        
        namespacesList.appendChild(nsTable);
        addRow('Namespaces', namespacesList);
    }

    // Imported Taxonomies
    if (taxonomy.importedTaxonomies && taxonomy.importedTaxonomies.length > 0) {
        const importsList = document.createElement('div');
        const importTable = document.createElement('table');
        importTable.style.width = '100%';
        importTable.style.fontSize = '12px';
        importTable.style.borderCollapse = 'collapse';
        
        taxonomy.importedTaxonomies.forEach((imp, index) => {
            const impRow = document.createElement('tr');
            const indexCell = document.createElement('td');
            const nameCell = document.createElement('td');
            
            indexCell.textContent = (index + 1) + '.';
            indexCell.style.padding = '4px 8px';
            indexCell.style.width = '10%';
            indexCell.style.verticalAlign = 'top';
            indexCell.style.borderBottom = '1px solid #eee';
            
            nameCell.textContent = getXbrlModelName(imp) || 'Unnamed import';
            nameCell.style.padding = '4px 8px';
            nameCell.style.wordBreak = 'break-all';
            nameCell.style.borderBottom = '1px solid #eee';
            
            impRow.appendChild(indexCell);
            impRow.appendChild(nameCell);
            importTable.appendChild(impRow);
        });
        
        importsList.appendChild(importTable);
        addRow('Imported Taxonomies', importsList);
    }

    // Statistics Section
    const statsDiv = document.createElement('div');
    statsDiv.style.marginTop = '20px';
    statsDiv.style.padding = '15px';
    statsDiv.style.backgroundColor = '#f0f8ff';
    statsDiv.style.borderRadius = '5px';
    statsDiv.style.border = '1px solid #d0e8ff';

    const statsHeader = document.createElement('div');
    statsHeader.style.display = 'flex';
    statsHeader.style.alignItems = 'center';
    statsHeader.style.cursor = 'pointer';
    statsHeader.style.userSelect = 'none';

    const statsTitle = document.createElement('h3');
    statsTitle.textContent = 'Model Statistics';
    statsTitle.style.marginTop = '0';
    statsTitle.style.marginBottom = '0';
    statsTitle.style.marginRight = '10px';
    statsTitle.style.color = '#2c3e50';
    statsTitle.style.flex = '1';
    
    // Toggle icon
    const toggleIcon = document.createElement('span');
    toggleIcon.textContent = '▶';
    toggleIcon.style.fontSize = '12px';
    toggleIcon.style.color = '#2c3e50';
    toggleIcon.style.transition = 'transform 0.3s';
    
    statsHeader.appendChild(statsTitle);
    statsHeader.appendChild(toggleIcon);
    statsDiv.appendChild(statsHeader);

    // Collapsible content container
    const collapsibleContent = document.createElement('div');
    collapsibleContent.style.overflow = 'hidden';
    collapsibleContent.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
    collapsibleContent.style.maxHeight = '0'; // Collapsed by default
    collapsibleContent.style.opacity = '0';
    collapsibleContent.style.marginTop = '10px';

    const statsTable = document.createElement('table');
    statsTable.style.width = '100%';
    statsTable.style.borderCollapse = 'collapse';
    statsTable.style.fontSize = '13px';

    // Helper function to add stat row
    function addStatRow(label, count, details = '') {
        if (count === 0 && !details) return; // Skip if zero and no details
        
        const row = document.createElement('tr');
        const labelCell = document.createElement('td');
        const countCell = document.createElement('td');
        
        labelCell.textContent = label;
        labelCell.style.padding = '6px 8px';
        labelCell.style.borderBottom = '1px solid #ddd';
        labelCell.style.fontWeight = '500';
        
        countCell.textContent = details || count.toLocaleString();
        countCell.style.padding = '6px 8px';
        countCell.style.borderBottom = '1px solid #ddd';
        countCell.style.textAlign = 'right';
        countCell.style.fontWeight = 'bold';
        countCell.style.color = '#2c3e50';
        
        row.appendChild(labelCell);
        row.appendChild(countCell);
        statsTable.appendChild(row);
    }

    // Count objects in taxonomy
    addStatRow('Concepts', taxonomy.concepts?.length || 0);
    addStatRow('Abstracts', taxonomy.abstracts?.length || 0);
    addStatRow('Members', taxonomy.members?.length || 0);
    addStatRow('Cubes', taxonomy.cubes?.length || 0);
    addStatRow('Dimensions', taxonomy.dimensions?.length || 0);
    addStatRow('Domains', taxonomy.domains?.length || 0);
    addStatRow('Domain Classes', taxonomy.domainClasses?.length || 0);
    addStatRow('Networks', taxonomy.networks?.length || 0);
    
    // Count total relationships across all networks
    let totalNetworkRelationships = 0;
    if (taxonomy.networks) {
        taxonomy.networks.forEach(network => {
            if (network.relationships) {
                totalNetworkRelationships += network.relationships.length;
            }
        });
    }
    addStatRow('Network Relationships', totalNetworkRelationships);
    
    // Count total relationships in domains
    let totalDomainRelationships = 0;
    if (taxonomy.domains) {
        taxonomy.domains.forEach(domain => {
            if (domain.relationships) {
                totalDomainRelationships += domain.relationships.length;
            }
        });
    }
    addStatRow('Domain Relationships', totalDomainRelationships);
    
    addStatRow('Labels', taxonomy.labels?.length || 0);
    addStatRow('References', taxonomy.references?.length || 0);
    addStatRow('Property Types', taxonomy.propertyTypes?.length || 0);
    addStatRow('Model Types', taxonomy.modelTypes?.length || 0);
    addStatRow('Label Types', taxonomy.labelTypes?.length || 0);
    addStatRow('Reference Types', taxonomy.referenceTypes?.length || 0);
    addStatRow('Relationship Types', taxonomy.relationshipTypes?.length || 0);
    addStatRow('Cube Types', taxonomy.cubeTypes?.length || 0);
    addStatRow('Data Types', taxonomy.dataTypes?.length || 0);
    addStatRow('Units', taxonomy.units?.length || 0);
    addStatRow('Entities', taxonomy.entities?.length || 0);
    addStatRow('Groups', taxonomy.groups?.length || 0);
    addStatRow('Group Contents', taxonomy.groupContents?.length || 0);
    addStatRow('Facts', taxonomy.facts?.length || 0);
    addStatRow('Transforms', taxonomy.transforms?.length || 0);
    addStatRow('Fact Maps', taxonomy.factMaps?.length || 0);
    addStatRow('Fact Sources', taxonomy.factSources?.length || 0);

    collapsibleContent.appendChild(statsTable);
    statsDiv.appendChild(collapsibleContent);
    
    // Toggle functionality
    let isExpanded = false; // Start collapsed
    statsHeader.addEventListener('click', () => {
        isExpanded = !isExpanded;
        if (isExpanded) {
            collapsibleContent.style.maxHeight = '3000px';
            collapsibleContent.style.opacity = '1';
            toggleIcon.textContent = '▼';
            toggleIcon.style.transform = 'rotate(0deg)';
        } else {
            collapsibleContent.style.maxHeight = '0';
            collapsibleContent.style.opacity = '0';
            toggleIcon.textContent = '▶';
            toggleIcon.style.transform = 'rotate(0deg)';
        }
    });

    grid.appendChild(table);
    grid.appendChild(statsDiv);
    
    // Add error panel
    const errorsDiv = buildErrorPanel(taxonomy);
    if (errorsDiv) {
        grid.appendChild(errorsDiv);
    }
    
    // Add search panel
    const searchDiv = buildSearchSection();
    grid.appendChild(searchDiv);
    
    taxonomyInfo.appendChild(grid);
    
    // Initialize search functionality after DOM is ready
    setTimeout(() => initTaxonomySearch(), 0);
}

/**
 * Initialize taxonomy search functionality
 */
function initTaxonomySearch() {
    const input = document.getElementById('taxonomy-qname-search-input');
    const resultsContainer = document.getElementById('taxonomy-search-results');
    
    if (!input || !resultsContainer) {
        return;
    }
    
    // Add input listener for autocomplete
    let debounceTimer;
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = this.value;
            // Get fresh QNames each time to include facts generated from factSources
            const allQNames = getAllQNames();
            const filteredResults = filterQNames(query, allQNames);
            displaySearchResults(filteredResults, resultsContainer, query);
        }, 200);
    });
}

/**
 * Build search section for QName lookup
 * @returns {HTMLElement} The search section element
 */
function buildSearchSection() {
    const searchDiv = document.createElement('div');
    searchDiv.style.marginTop = '20px';
    searchDiv.style.padding = '15px';
    searchDiv.style.backgroundColor = '#f0fff4';
    searchDiv.style.borderRadius = '5px';
    searchDiv.style.border = '1px solid #9ae6b4';

    const searchHeader = document.createElement('div');
    searchHeader.style.display = 'flex';
    searchHeader.style.alignItems = 'center';
    searchHeader.style.cursor = 'pointer';
    searchHeader.style.userSelect = 'none';

    const searchTitle = document.createElement('h3');
    searchTitle.textContent = 'Search QNames';
    searchTitle.style.marginTop = '0';
    searchTitle.style.marginBottom = '0';
    searchTitle.style.marginRight = '10px';
    searchTitle.style.color = '#2c3e50';
    searchTitle.style.flex = '1';
    
    // Toggle icon
    const toggleIcon = document.createElement('span');
    toggleIcon.textContent = '▶';
    toggleIcon.style.fontSize = '12px';
    toggleIcon.style.color = '#2c3e50';
    toggleIcon.style.transition = 'transform 0.3s';
    
    searchHeader.appendChild(searchTitle);
    searchHeader.appendChild(toggleIcon);
    searchDiv.appendChild(searchHeader);

    // Collapsible content container
    const collapsibleContent = document.createElement('div');
    collapsibleContent.style.overflow = 'hidden';
    collapsibleContent.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out';
    collapsibleContent.style.maxHeight = '0';
    collapsibleContent.style.opacity = '0';
    collapsibleContent.style.marginTop = '10px';

    // Create search input
    const inputContainer = document.createElement('div');
    inputContainer.style.marginBottom = '10px';
    
    const input = document.createElement('input');
    input.id = 'taxonomy-qname-search-input';
    input.type = 'text';
    input.placeholder = 'Type to search for QName...';
    input.style.width = '100%';
    input.style.padding = '10px';
    input.style.fontSize = '14px';
    input.style.border = '1px solid #cbd5e0';
    input.style.borderRadius = '4px';
    input.style.boxSizing = 'border-box';
    
    inputContainer.appendChild(input);
    collapsibleContent.appendChild(inputContainer);

    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'taxonomy-search-results';
    resultsContainer.style.maxHeight = '400px';
    resultsContainer.style.overflowY = 'auto';
    resultsContainer.style.border = '1px solid #e2e8f0';
    resultsContainer.style.borderRadius = '4px';
    resultsContainer.style.backgroundColor = '#fff';
    resultsContainer.style.padding = '5px';
    
    collapsibleContent.appendChild(resultsContainer);

    searchDiv.appendChild(collapsibleContent);
    
    // Toggle functionality
    let isExpanded = false;
    searchHeader.addEventListener('click', () => {
        isExpanded = !isExpanded;
        if (isExpanded) {
            collapsibleContent.style.maxHeight = '3000px';
            collapsibleContent.style.opacity = '1';
            toggleIcon.textContent = '▼';
        } else {
            collapsibleContent.style.maxHeight = '0';
            collapsibleContent.style.opacity = '0';
            toggleIcon.textContent = '▶';
        }
    });

    return searchDiv;
}

/**
 * Build error panel showing validation errors
 * @param {Object} taxonomy - The taxonomy object to validate
 * @returns {HTMLElement|null} The error panel element or null if no errors
 */
function buildErrorPanel(taxonomy) {
    // Helper function to create error section container
    const createErrorSection = () => {
        const section = document.createElement('div');
        section.className = 'error-section';
        return section;
    };

    // Helper function to create error section title
    const createErrorTitle = (errorLabel, errorCount) => {
        const title = document.createElement('h4');
        title.className = 'error-section-title';
        title.textContent = `${errorLabel} (${errorCount})`;
        return title;
    };

    // Helper function to create error list container
    const createErrorList = () => {
        const list = document.createElement('ul');
        list.className = 'error-list';
        return list;
    };

    // Helper function to create error list item
    const createErrorListItem = () => {
        const li = document.createElement('li');
        li.className = 'error-list-item';
        return li;
    };

    const errors = validateTaxonomy(taxonomy);
    
    // Get QName validation errors from window (set by taxonomy-loader)
    const qnameErrors = window.qnameValidationErrors || [];
    
    // Get factSource validation errors from window (set by factSources-builder)
    // These are NOT stored in the model, but reported separately
    const factSourceErrors = window.factSourceValidationErrors || [];
    const factSourceErrorCount = factSourceErrors.length;
    
    if (errors.domainDefinitionErrors.length === 0 &&
        errors.invalidDomainUsage.length === 0 &&
        errors.disallowedObjectProperty.length === 0 &&
        errors.conflictingPropertyValues.length === 0 &&
        errors.cubeMissingConceptDimension.length === 0 &&
        errors.excludeCubeSelfReference.length === 0 &&
        errors.invalidDomainClass.length === 0 &&
        errors.invalidAllowDomainFactsPropertyOnConceptDimension.length === 0 &&
        errors.domainUsedOnPeriodDimension.length === 0 &&
        errors.dimensionNameNotDimensionObject.length === 0 &&
        errors.invalidPeriodConstraintDimension.length === 0 &&
        errors.redundantTimeSpanProperty.length === 0 &&
        errors.invalidDomainObject.length === 0 &&
        errors.missingDomainClassSource.length === 0 &&
        errors.multipleDomainClasses.length === 0 &&
        errors.invalidCubeType.length === 0 &&
        errors.duplicateDimension.length === 0 &&
        errors.invalidCoreDimension.length === 0 &&
        errors.invalidDataTypeExpansion.length === 0 &&
        errors.invalidDimensionRequirementRelaxation.length === 0 &&
        errors.invalidDimensionAddition.length === 0 &&
        errors.invalidDimensionClosedExpansion.length === 0 &&
        errors.invalidPropertyExpansion.length === 0 &&
        errors.coreDimensionsExpansion.length === 0 &&
        errors.invalidRelationshipConstraintRelaxation.length === 0 &&
        errors.invalidRelationshipExpansion.length === 0 &&
        errors.invalidDataTypeForDomainClass.length === 0 &&
        errors.invalidDomainClassReference.length === 0 &&
        errors.invalidQNameReferences.length === 0 &&
        errors.referenceTypeRedefined.length === 0 &&
        errors.referenceLanguageRedefined.length === 0 &&
        qnameErrors.length === 0 &&
        factSourceErrorCount === 0) {
        return null; // No errors to display
    }

    const errorsDiv = document.createElement('div');
    errorsDiv.className = 'errors-container';

    const errorsTitle = document.createElement('h3');
    errorsTitle.textContent = 'Taxonomy Errors';
    errorsTitle.style.marginTop = '0';
    errorsTitle.style.marginBottom = '10px';
    errorsTitle.style.color = '#c92a2a';
    errorsDiv.appendChild(errorsTitle);

    // Duplicate QNames Section - Now handled by qname-validator.js with error code oimte:duplicateObjects
    // The qname-validator runs more comprehensive duplicate checks across all object types
    
    // NOTE: "Missing References" section removed - this is now handled by the more comprehensive
    // "oimte:invalidQNameReference" validation from qname-validator.js below

    // Domain Definition Errors Section
    if (errors.domainDefinitionErrors.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:domainClassMismatchWithDomain');
        const title = createErrorTitle(errorLabel, errors.domainDefinitionErrors.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.domainDefinitionErrors.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Domain:</strong> ${err.domain}<br>` +
                          `<span class="error-detail-indent">Domain Class: <em>${err.domainClass}</em> (type: ${err.domainClassType})</span><br>` +
                          `<span class="error-detail-indent">Invalid Attribute: <strong>${err.invalidAttribute}</strong></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Domain Usage Section
    if (errors.invalidDomainUsage.length > 0) {
        const section = createErrorSection();
        const title = createErrorTitle('Invalid Domain Usage in Cube Dimensions', errors.invalidDomainUsage.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDomainUsage.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Cube:</strong> ${err.cube}<br>` +
                          `<span class="error-detail-indent">Dimension: <em>${err.dimension}</em></span><br>` +
                          `<span class="error-detail-indent">Invalid Domain: <strong>${err.domain}</strong></span><br>` +
                          `<span class="error-detail-indent">Domain Class: <em>${err.domainClass}</em> (expected: ${err.expectedRoot})</span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Disallowed Object Property Section
    if (errors.disallowedObjectProperty.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:disallowedObjectProperty');
        const title = createErrorTitle(errorLabel, errors.disallowedObjectProperty.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.disallowedObjectProperty.forEach(err => {
            const li = createErrorListItem();
            let contextInfo = `<strong>Object:</strong> ${err.objectName}`;
            if (err.network) {
                contextInfo = `<strong>Relationship:</strong> ${err.objectName} in network ${err.network}`;
            }
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Property:</strong> ${err.property}<br>` +
                          `<span class="error-detail-indent">${contextInfo}</span><br>` +
                          `<span class="error-detail-indent">Object Type: <em>${err.objectType}</em></span><br>` +
                          `<span class="error-detail-indent">Allowed On: <em>${err.allowedObjects.join(', ')}</em></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Conflicting Property Values Section
    if (errors.conflictingPropertyValues.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:conflictingPropertyValues');
        const title = createErrorTitle(errorLabel, errors.conflictingPropertyValues.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.conflictingPropertyValues.forEach(err => {
            const li = createErrorListItem();
            let contextInfo = `<strong>Object:</strong> ${err.objectName}`;
            if (err.network) {
                contextInfo = `<strong>Relationship:</strong> ${err.objectName} in network ${err.network}`;
            }
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Property:</strong> ${err.property}<br>` +
                          `<span class="error-detail-indent">${contextInfo}</span><br>` +
                          `<span class="error-detail-indent">Object Type: <em>${err.objectType}</em></span><br>` +
                          `<span class="error-detail-indent">Conflicting Values: <em>${err.conflictingValues.map(v => JSON.stringify(v)).join(', ')}</em></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Cube Missing Concept Dimension Section
    if (errors.cubeMissingConceptDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:cubeMissingConceptDimension');
        const title = createErrorTitle(errorLabel, errors.cubeMissingConceptDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.cubeMissingConceptDimension.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Cube:</strong> ${err.cubeName}<br>` +
                          `<span class="error-detail-indent">Cube Type: <em>${err.cubeType}</em></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Exclude Cube Self Reference Section
    if (errors.excludeCubeSelfReference.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:excludeCubeSelfReference');
        const title = createErrorTitle(errorLabel, errors.excludeCubeSelfReference.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.excludeCubeSelfReference.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Cube:</strong> ${err.cubeName}<br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Period Constraint Dimension Section
    if (errors.invalidPeriodConstraintDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidPeriodConstraintDimension');
        const title = createErrorTitle(errorLabel, errors.invalidPeriodConstraintDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidPeriodConstraintDimension.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Cube:</strong> <code class="error-highlight-code">${err.cubeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code> (at index ${err.dimensionIndex})</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Redundant TimeSpan Property Section
    if (errors.redundantTimeSpanProperty.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:redundantTimeSpanProperty');
        const title = createErrorTitle(errorLabel, errors.redundantTimeSpanProperty.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.redundantTimeSpanProperty.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Cube:</strong> <code class="error-highlight-code">${err.cubeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code> (at index ${err.dimensionIndex})</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Period Constraint:</strong> at index ${err.constraintIndex}</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Domain Object Section
    if (errors.invalidDomainObject.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDomainObject');
        const title = createErrorTitle(errorLabel, errors.invalidDomainObject.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDomainObject.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Domain:</strong> <code class="error-highlight-code">${err.domainName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Domain Class:</strong> <code class="error-highlight-code">${err.domainClass}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Invalid Object:</strong> <code class="error-highlight-code">${err.objectName}</code> (${err.objectType})</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Position:</strong> ${err.position}</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Allowed Types:</strong> ${err.allowedTypes}</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Missing Domain Class Source Section
    if (errors.missingDomainClassSource.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:missingDomainClassSource');
        const title = createErrorTitle(errorLabel, errors.missingDomainClassSource.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.missingDomainClassSource.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Domain:</strong> <code class="error-highlight-code">${err.domainName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Domain Class:</strong> <code class="error-highlight-code">${err.domainClass}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Relationship Count:</strong> ${err.relationshipCount}</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Multiple Domain Classes Section
    if (errors.multipleDomainClasses.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:multipleDomainClasses');
        const title = createErrorTitle(errorLabel, errors.multipleDomainClasses.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.multipleDomainClasses.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Domain:</strong> <code class="error-highlight-code">${err.domainName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Declared Root:</strong> <code class="error-highlight-code">${err.declaredRoot}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Actual Roots Found:</strong> <code class="error-highlight-code">${err.actualRoots.join(', ')}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Root Count:</strong> ${err.rootCount}</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Cube Type Section
    if (errors.invalidCubeType.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidCubeType');
        const title = createErrorTitle(errorLabel, errors.invalidCubeType.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidCubeType.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Invalid Reference:</strong> <code class="error-highlight-code">${err.cubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Duplicate Dimension in CubeType Section
    if (errors.duplicateDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:duplicateDimension');
        const title = createErrorTitle(errorLabel, errors.duplicateDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.duplicateDimension.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Cube Type:</strong> <code class="error-highlight-code">${err.cubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Duplicate Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Core Dimension Section
    if (errors.invalidCoreDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidCoreDimension');
        const title = createErrorTitle(errorLabel, errors.invalidCoreDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidCoreDimension.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Cube Type:</strong> <code class="error-highlight-code">${err.cubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Invalid Core Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code> (at index ${err.index})</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Data Type Expansion Section
    if (errors.invalidDataTypeExpansion.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDataTypeExpansion');
        const title = createErrorTitle(errorLabel, errors.invalidDataTypeExpansion.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDataTypeExpansion.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base DataType:</strong> <code>${err.baseDataType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Derived DataType:</strong> <code>${err.derivedDataType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Dimension Requirement Relaxation Section
    if (errors.invalidDimensionRequirementRelaxation.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDimensionRequirementRelaxation');
        const title = createErrorTitle(errorLabel, errors.invalidDimensionRequirementRelaxation.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDimensionRequirementRelaxation.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Requirement:</strong> <code>required=true</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Derived Requirement:</strong> <code>required=false</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Dimension Addition Section
    if (errors.invalidDimensionAddition.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDimensionAddition');
        const title = createErrorTitle(errorLabel, errors.invalidDimensionAddition.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDimensionAddition.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code> (closed=true)</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Added Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Dimension Closed Expansion Section
    if (errors.invalidDimensionClosedExpansion.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDimensionClosedExpansion');
        const title = createErrorTitle(errorLabel, errors.invalidDimensionClosedExpansion.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDimensionClosedExpansion.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code> (closed=true)</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Derived Constraint:</strong> <code>closed=false</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Property Expansion Section
    if (errors.invalidPropertyExpansion.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidPropertyExpansion');
        const title = createErrorTitle(errorLabel, errors.invalidPropertyExpansion.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidPropertyExpansion.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Added Property Type:</strong> <code class="error-highlight-code">${err.propertyType}</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Core Dimensions Expansion Section
    if (errors.coreDimensionsExpansion.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:coreDimensionsExpansion');
        const title = createErrorTitle(errorLabel, errors.coreDimensionsExpansion.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.coreDimensionsExpansion.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Added Core Dimension:</strong> <code class="error-highlight-code">${err.coreDimension}</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Relationship Constraint Relaxation Section
    if (errors.invalidRelationshipConstraintRelaxation.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidRelationshipConstraintRelaxation');
        const title = createErrorTitle(errorLabel, errors.invalidRelationshipConstraintRelaxation.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidRelationshipConstraintRelaxation.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Relationship Type:</strong> <code class="error-highlight-code">${err.relationshipType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Source Constraint:</strong> <code>${err.sourceConstraint}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Target Constraint:</strong> <code>${err.targetConstraint}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Relaxation:</strong> <code>${err.relaxationType}</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Relationship Expansion Section
    if (errors.invalidRelationshipExpansion.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidRelationshipExpansion');
        const title = createErrorTitle(errorLabel, errors.invalidRelationshipExpansion.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidRelationshipExpansion.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Derived Cube Type:</strong> <code class="error-highlight-code">${err.derivedCubeTypeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Base Cube Type:</strong> <code class="error-highlight-code">${err.baseCubeTypeName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Added Relationship Type:</strong> <code class="error-highlight-code">${err.relationshipType}</code> ❌</span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Source Constraint:</strong> <code>${err.sourceConstraint}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Target Constraint:</strong> <code>${err.targetConstraint}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Data Type For Domain Class Section
    if (errors.invalidDataTypeForDomainClass.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDataTypeForDomainClass');
        const title = createErrorTitle(errorLabel, errors.invalidDataTypeForDomainClass.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDataTypeForDomainClass.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Cube:</strong> <code class="error-highlight-code">${err.cubeName}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Domain Data Type:</strong> <code class="error-highlight-code">${err.domainDataType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Domain Class:</strong> <code class="error-highlight-code">${err.domainClass}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Allowed Types:</strong> <code class="error-highlight-code">${err.allowedTypes.join(', ')}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Domain Class References Section
    if (errors.invalidDomainClass.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDomainClass');
        const title = createErrorTitle(errorLabel, errors.invalidDomainClass.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDomainClass.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Referenced Domain Class:</strong> <code class="error-highlight-code">${err.domainClassName}</code><br>`;
            
            if (err.referenceType === 'dimension') {
                contextHtml += `<span class="error-detail-indent">Referenced in: <strong>Dimension</strong> <em>${err.dimensionName}</em></span><br>`;
            } else if (err.referenceType === 'domain') {
                contextHtml += `<span class="error-detail-indent">Referenced in: <strong>Domain</strong> <em>${err.domainName}</em></span><br>`;
            }
            
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid Domain Class Reference on Member Section
    if (errors.invalidDomainClassReference.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidDomainClassReference');
        const title = createErrorTitle(errorLabel, errors.invalidDomainClassReference.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidDomainClassReference.forEach(err => {
            const li = createErrorListItem();
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Member:</strong> <code class="error-highlight-code">${err.memberName}</code><br>`;
            contextHtml += `<span class="error-detail-indent">Used in: <strong>Domain</strong> <em>${err.domainName}</em> (root: <code class="error-highlight-code">${err.domainRoot}</code>)</span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid allowDomainFacts on Concept Dimension Section
    if (errors.invalidAllowDomainFactsPropertyOnConceptDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidAllowDomainFactsPropertyOnConceptDimension');
        const title = createErrorTitle(errorLabel, errors.invalidAllowDomainFactsPropertyOnConceptDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidAllowDomainFactsPropertyOnConceptDimension.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Cube:</strong> ${err.cubeName}<br>` +
                          `<span class="error-detail-indent">The xbrl:concept dimension has <code class="error-highlight-code">allowDomainFacts: true</code></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Domain Used on Period Dimension Section
    if (errors.domainUsedOnPeriodDimension.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:domainUsedOnPeriodDimension');
        const title = createErrorTitle(errorLabel, errors.domainUsedOnPeriodDimension.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.domainUsedOnPeriodDimension.forEach(err => {
            const li = createErrorListItem();
            li.innerHTML = `<strong class="error-code">[${err.code}]</strong> ` +
                          `<strong>Cube:</strong> ${err.cubeName}<br>` +
                          `<span class="error-detail-indent">The xbrl:period dimension has <code class="error-highlight-code">domainName: ${err.domainName}</code></span><br>` +
                          `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Dimension Name Not Dimension Object Section
    if (errors.dimensionNameNotDimensionObject.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:dimensionNameNotDimensionObject');
        const title = createErrorTitle(errorLabel, errors.dimensionNameNotDimensionObject.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.dimensionNameNotDimensionObject.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[${err.code}]</strong> `;
            contextHtml += `<strong>Referenced Dimension:</strong> <code class="error-highlight-code">${err.dimensionName}</code><br>`;
            
            if (err.context === 'cube') {
                contextHtml += `<span class="error-detail-indent">Referenced in: <strong>Cube</strong> <em>${err.cubeName}</em></span><br>`;
            } else if (err.context === 'cubeType') {
                contextHtml += `<span class="error-detail-indent">Referenced in: <strong>Cube Type</strong> <em>${err.cubeTypeName}</em> (allowedCubeDimensions)</span><br>`;
            } else if (err.context === 'dataTable') {
                contextHtml += `<span class="error-detail-indent">Referenced in: <strong>Data Table</strong> <em>${err.dataTableName}</em> (${err.axisType})</span><br>`;
            }
            
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Invalid QName References by Type Section
    if (errors.invalidQNameReferences.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:invalidQNameReference');
        const title = createErrorTitle(errorLabel, errors.invalidQNameReferences.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.invalidQNameReferences.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[oimte:invalidQNameReference]</strong> `;
            contextHtml += `<strong>Type:</strong> <code style="background: #e7f5ff; padding: 2px 4px; border-radius: 3px;">${err.type}</code> `;
            contextHtml += `<strong>Invalid Reference:</strong> <code class="error-highlight-code">${err.reference}</code><br>`;
            contextHtml += `<span class="error-detail-indent">In: <strong>${err.context}</strong> <em>${err.name}</em>, field: <code>${err.field}</code></span><br>`;
            
            // Use custom message if provided, otherwise use default message
            const errorMessage = err.message || `The referenced ${err.type.replace('QName', '')} does not exist in the taxonomy.`;
            contextHtml += `<span class="error-detail-indent error-message-text">${errorMessage}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Reference Type Redefined Section
    if (errors.referenceTypeRedefined && errors.referenceTypeRedefined.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:referenceTypeRedefined');
        const title = createErrorTitle(errorLabel, errors.referenceTypeRedefined.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.referenceTypeRedefined.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[oimte:referenceTypeRedefined]</strong> `;
            contextHtml += `<strong>Reference:</strong> <code class="error-highlight-code">${err.reference}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Extension referenceType:</strong> <code>${err.extensionReferenceType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Target referenceType:</strong> <code>${err.targetReferenceType}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Reference Language Redefined Section
    if (errors.referenceLanguageRedefined && errors.referenceLanguageRedefined.length > 0) {
        const section = createErrorSection();
        const errorLabel = getErrorLabel('oimte:referenceLanguageRedefined');
        const title = createErrorTitle(errorLabel, errors.referenceLanguageRedefined.length);
        section.appendChild(title);

        const list = createErrorList();
        errors.referenceLanguageRedefined.forEach(err => {
            const li = createErrorListItem();
            
            let contextHtml = `<strong class="error-code">[oimte:referenceLanguageRedefined]</strong> `;
            contextHtml += `<strong>Reference:</strong> <code class="error-highlight-code">${err.reference}</code><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Extension language:</strong> <code>${err.extensionLanguage}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent"><strong>Target language:</strong> <code>${err.targetLanguage}</code></span><br>`;
            contextHtml += `<span class="error-detail-indent error-message-text">${err.message}</span>`;
            
            li.innerHTML = contextHtml;
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
    }

    // Group QName errors by errorCode
    if (qnameErrors.length > 0) {
        console.log('[Error Display] Processing', qnameErrors.length, 'QName errors');
        const errorsByCode = {};
        
        // Group errors by their errorCode (or use 'invalidQNameReference' as default)
        qnameErrors.forEach(err => {
            const code = err.errorCode || 'oimte:invalidQNameReference';
            console.log('[Error Display] Error with code:', code, err);
            if (!errorsByCode[code]) {
                errorsByCode[code] = [];
            }
            errorsByCode[code].push(err);
        });
        
        console.log('[Error Display] Grouped errors by code:', Object.keys(errorsByCode));
        
        // Display each error type group
        Object.keys(errorsByCode).forEach(errorCode => {
            const errorsForCode = errorsByCode[errorCode];
            
            const qnameSection = document.createElement('div');
            qnameSection.style.marginBottom = '15px';

            const qnameTitle = document.createElement('h4');
            const errorLabel = getErrorLabel(errorCode);
            console.log('[Error Display] Error code:', errorCode, '-> Label:', errorLabel);
            qnameTitle.textContent = `${errorLabel} (${errorsForCode.length})`;
            qnameTitle.style.marginTop = '0';
            qnameTitle.style.marginBottom = '8px';
            qnameTitle.style.color = '#e03131';
            qnameSection.appendChild(qnameTitle);

            const qnameList = document.createElement('ul');
            qnameList.style.marginTop = '5px';
            qnameList.style.marginBottom = '5px';
            qnameList.style.fontSize = '13px';
            qnameList.style.maxHeight = '300px';
            qnameList.style.overflowY = 'auto';
            qnameList.style.backgroundColor = '#fff';
            qnameList.style.padding = '10px';
            qnameList.style.borderRadius = '3px';
            qnameList.style.border = '1px solid #ffc9c9';

            errorsForCode.forEach(err => {
                const li = document.createElement('li');
                li.style.marginBottom = '8px';
                
                // Prepend error code to message if it exists - styled in red
                const errorCodePrefix = err.errorCode ? `<strong style="color: #c92a2a;">[${err.errorCode}]</strong> ` : '';
                console.log('[Error Display] Error code prefix:', errorCodePrefix, 'for error:', err);
                
                let contextHtml = '';
                if (err.concept) contextHtml += `<strong>Concept:</strong> ${err.concept}, `;
                if (err.dimension) contextHtml += `<strong>Dimension:</strong> ${err.dimension}, `;
                if (err.domain) contextHtml += `<strong>Domain:</strong> ${err.domain}, `;
                if (err.domainClass) contextHtml += `<strong>Domain Class:</strong> ${err.domainClass}, `;
                if (err.cube) contextHtml += `<strong>Cube:</strong> ${err.cube}, `;
                if (err.relationshipType) contextHtml += `<strong>Relationship Type:</strong> ${err.relationshipType}, `;
                if (err.property) contextHtml += `<strong>Property:</strong> ${err.property}, `;
                if (err.referenceName) contextHtml += `<strong>Reference:</strong> ${err.referenceName}, `;
                if (err.relatedName) contextHtml += `<strong>Label For:</strong> ${err.relatedName}, `;
                
                // Remove trailing comma and space
                contextHtml = contextHtml.replace(/, $/, '');
                
                // Display error with appropriate formatting based on error type
                let detailHtml = '';
                if (err.invalidQName) {
                    detailHtml = `<span style="margin-left: 20px;">Invalid QName: <code style="background: #ffe0e0; padding: 2px 4px; border-radius: 3px; font-family: monospace;">${err.invalidQName}</code></span><br>`;
                } else if (err.invalidValue) {
                    detailHtml = `<span style="margin-left: 20px;">Invalid Value: <code style="background: #ffe0e0; padding: 2px 4px; border-radius: 3px; font-family: monospace;">${err.invalidValue}</code></span><br>`;
                }

                // Show resolved object type when available (helps with errors like invalidDomainRelationshipTarget)
                if (err.resolvedObjectType) {
                    detailHtml += `<span style="margin-left: 20px; color: #333;"><strong>Resolved Type:</strong> <code style=\"background:#eef6ff;padding:2px 4px;border-radius:3px;\">${err.resolvedObjectType}</code></span><br>`;
                }

                // If there are relationship examples (from extension-time errors or enhanced validators), show them
                if (Array.isArray(err.relationshipExamples) && err.relationshipExamples.length > 0) {
                    const examplesHtml = err.relationshipExamples.map(ex => `<li style=\"margin-bottom:4px;\"><code style=\"background:#f7f7f7;padding:2px 6px;border-radius:3px;\">${ex}</code></li>`).join('');
                    detailHtml += `<div style=\"margin-left:20px;margin-top:6px;color:#333;\"><strong>Example relationship(s):</strong><ul style=\"margin-top:6px;margin-bottom:6px;padding-left:20px;\">${examplesHtml}</ul></div>`;
                }

                // Show attempted relationship count if present
                if (typeof err.attemptedRelationshipCount === 'number') {
                    detailHtml += `<span style="margin-left: 20px; color: #333;"><strong>Attempted relationships:</strong> ${err.attemptedRelationshipCount}</span><br>`;
                }
                
                const finalMessage = `${errorCodePrefix}${err.message}`;
                console.log('[Error Display] Final message:', finalMessage);
                
                li.innerHTML = `${contextHtml}<br>` +
                              detailHtml +
                              `<span style="margin-left: 20px; color: #555;">${finalMessage}</span>`;
                qnameList.appendChild(li);
            });

            qnameSection.appendChild(qnameList);
            errorsDiv.appendChild(qnameSection);
            console.log('[Error Display] Added error section for', errorCode, 'to errorsDiv');
        });
    }

    // FactSource Validation Errors Section
    // Read from global window variable (not from model)
    const allFactSourceErrors = window.factSourceValidationErrors || [];
    
    if (allFactSourceErrors.length > 0) {
        const section = createErrorSection();
        const title = createErrorTitle('FactSource Data Validation Errors', allFactSourceErrors.length);
        section.appendChild(title);

        const list = createErrorList();
        list.style.marginTop = '5px';
        list.style.marginBottom = '5px';
        list.style.fontSize = '13px';
        list.style.maxHeight = '400px';
        list.style.overflowY = 'auto';
        list.style.backgroundColor = '#fff';
        list.style.padding = '10px';
        list.style.borderRadius = '3px';
        list.style.border = '1px solid #ffc9c9';

        allFactSourceErrors.forEach(err => {
            const li = document.createElement('li');
            li.style.marginBottom = '8px';

            const factIndexInfo = err.factIndex !== undefined ? ` [Fact ${err.factIndex}]` : '';
            const errorType = err.type || 'unknown';
            
            li.innerHTML = `<strong style="color: #1864ab;">FactSource:</strong> ${err.factSourceName}${factIndexInfo}<br>` +
                          `<span style="margin-left: 20px;"><strong style="color: #c92a2a;">[${errorType}]</strong> ${err.message}</span>`;
            
            list.appendChild(li);
        });

        section.appendChild(list);
        errorsDiv.appendChild(section);
        console.log('[Error Display] Added factSource validation errors:', allFactSourceErrors.length);
    }

    console.log('[Error Display] Returning errorsDiv:', errorsDiv);
    return errorsDiv;
}

/**
 * Validate taxonomy for duplicate names and missing references
 * @param {Object} taxonomy - The taxonomy object to validate
 * @returns {Object} Object containing arrays of validation errors
 */
function validateTaxonomy(taxonomy) {
    const errors = {
        // Note: duplicateQNames checking is now handled by qname-validator.js with error code oimte:duplicateObjects
        domainDefinitionErrors: [],
        invalidDomainUsage: [],
        disallowedObjectProperty: [],
        conflictingPropertyValues: [],
        cubeMissingConceptDimension: [],
        excludeCubeSelfReference: [],
        invalidDomainClass: [],
        invalidAllowDomainFactsPropertyOnConceptDimension: [],
        domainUsedOnPeriodDimension: [],
        dimensionNameNotDimensionObject: [],
        invalidPeriodConstraintDimension: [],
        redundantTimeSpanProperty: [],
        invalidDomainObject: [],
        missingDomainClassSource: [],
        multipleDomainClasses: [],
        invalidCubeType: [],
        invalidDataTypeForDomainClass: [],
        invalidQNameReferences: [],
        referenceTypeRedefined: [],
        referenceLanguageRedefined: [],
        duplicateDimension: [],
        invalidCoreDimension: [],
        invalidDataTypeExpansion: [],
        invalidDimensionRequirementRelaxation: [],
        invalidDimensionAddition: [],
        invalidDimensionClosedExpansion: [],
        invalidPropertyExpansion: [],
        coreDimensionsExpansion: [],
        invalidRelationshipConstraintRelaxation: [],
        invalidRelationshipExpansion: [],
        invalidDomainClassReference: []
    };

    // Build a set of all defined QNames in the taxonomy (still needed for reference validation)
    const definedNames = new Set();

    // Add the taxonomy name itself as a defined QName
    if (taxonomy.name) {
        definedNames.add(taxonomy.name);
    }

    // Add built-in object type names as valid objects that can be referenced
    // These are the meta-objects that define object types in the taxonomy model
    const builtInObjectTypes = [...BUILTIN_OBJECT_TYPES_ARRAY, 'xs:anySimpleType'];
    
    builtInObjectTypes.forEach(objectType => {
        definedNames.add(objectType);
        // Don't track these in occurrences as they're built-in
    });

    // Collect all defined names
    const objectTypes = [
        { array: 'concepts', type: 'concepts' },
        { array: 'abstracts', type: 'abstracts' },
        { array: 'members', type: 'members' },
        { array: 'dimensions', type: 'dimensions' },
        { array: 'cubes', type: 'cubes' },
        { array: 'domains', type: 'domains' },
        { array: 'domainClasses', type: 'domainClasses' },
        { array: 'networks', type: 'networks' },
        { array: 'propertyTypes', type: 'propertyTypes' },
        { array: 'labelTypes', type: 'labelTypes' },
        { array: 'modelTypes', type: 'modelTypes' },
        { array: 'references', type: 'references' },
        { array: 'referenceTypes', type: 'referenceTypes' },
        { array: 'relationshipTypes', type: 'relationshipTypes' },
        { array: 'cubeTypes', type: 'cubeTypes' },
        { array: 'dataTypes', type: 'dataTypes' },
        { array: 'units', type: 'units' },
        { array: 'entities', type: 'entities' },
        { array: 'groups', type: 'groups' },
        { array: 'facts', type: 'facts' },
        { array: 'transforms', type: 'transforms' }
    ];

    objectTypes.forEach(({ array, type }) => {
        if (taxonomy[array]) {
            taxonomy[array].forEach(item => {
                if (item.name) {
                    definedNames.add(item.name);
                    // No need to track occurrences - qname-validator.js handles duplicate detection
                }
            });
        }
    });

    // NOTE: Duplicate checking removed - now handled by qname-validator.js with error code oimte:duplicateObjects
    // NOTE: Missing references checking removed - this is now handled by the more comprehensive
    // qname-validator.js which checks ALL QName references in the taxonomy, not just a subset

    // Validate domain definitions against domain class types
    validateDomainDefinitionsAgainstRootTypes(taxonomy, errors);

    // Validate entity domain sources
    validateEntityDomainSources(taxonomy, errors);

    // Validate entity domain targets
    validateEntityDomainTargets(taxonomy, errors);

    // Validate unit domain sources
    validateUnitDomainSources(taxonomy, errors);

    // Validate unit domain targets
    validateUnitDomainTargets(taxonomy, errors);

    // Validate that unit objects are not present in non-unit domains
    validateUnitInNonUnitDomain(taxonomy, errors);

    // Validate that domains used in cube dimensions have matching roots
    validateDomainClassesMatchDimensions(taxonomy, errors);

    // Validate that properties are only used on allowed objects
    validatePropertyUsageOnObjects(taxonomy, errors);

    // Validate that properties don't have conflicting values on the same object
    validateConflictingPropertyValues(taxonomy, errors);

    // Validate that all cubes have xbrl:concept dimension
    validateCubeMissingConceptDimension(taxonomy, errors);

    // Validate that cubes don't exclude themselves
    validateCubeExcludeSelfReference(taxonomy, errors);

    // Validate that periodConstraints is only used on period dimension
    validatePeriodConstraintDimension(taxonomy, errors);

    // Validate that timeSpan is not redundant with both startDate and endDate
    validateRedundantTimeSpanProperty(taxonomy, errors);

    // Validate that domain objects match their domainClass's allowedDomainItems
    validateInvalidDomainObject(taxonomy, errors);

    // Validate that domain class objects appear as sources in at least one relationship
    validateMissingDomainClassSource(taxonomy, errors);

    // Validate that domains resolve to a single root object
    validateMultipleDomainClasses(taxonomy, errors);

    // Validate that domainClass references point to legitimate domainClass objects
    validateDomainClassReferences(taxonomy, errors, definedNames);

    // Validate that members used in a domain have the domain's root in their domainClasses property
    validateMemberDomainClassReference(taxonomy, errors);

    // Validate that allowDomainFacts is not true on concept dimension
    validateAllowDomainFactsOnConceptDimension(taxonomy, errors);

    // Validate that domainName is not used on period dimension
    validateDomainUsedOnPeriodDimension(taxonomy, errors);

    // Validate that cubeTypes array only references cubeType objects
    validateCubeTypeReferences(taxonomy, errors);

    // Validate that cubeTypes don't have duplicate dimensions in constraints
    validateCubeTypeDuplicateDimensions(taxonomy, errors);

    // Validate that cubeTypes only have valid core dimensions
    validateCubeTypeCoreDimensions(taxonomy, errors);

    // Validate that derived cubeTypes don't expand data type constraints
    validateCubeTypeDataTypeExpansion(taxonomy, errors);

    // Validate that derived cubeTypes don't relax dimension requirements
    validateDimensionRequirementRelaxation(taxonomy, errors);

    // Validate that derived cubeTypes don't add dimensions when base is closed
    validateDimensionAddition(taxonomy, errors);

    // Validate that derived cubeTypes don't expand closed constraint
    validateDimensionClosedExpansion(taxonomy, errors);

    // Validate that derived cubeTypes don't expand allowed properties
    validatePropertyExpansion(taxonomy, errors);

    // Validate that derived cubeTypes don't expand core dimensions
    validateCoreDimensionsExpansion(taxonomy, errors);

    // Validate that derived cubeTypes don't relax relationship constraints
    validateRelationshipConstraintRelaxation(taxonomy, errors);

    // Validate that derived cubeTypes don't expand allowed relationships
    validateRelationshipExpansion(taxonomy, errors);

    // Validate that domainDataType in cubeDimensions matches allowedDomainItems in domainClass
    validateDomainDataTypeForDomainClass(taxonomy, errors);

    // Validate that dimensionName references point to legitimate dimension objects
    validateDimensionNameReferences(taxonomy, errors, definedNames);

    // Validate reference extension properties (referenceType and language)
    validateReferenceExtensionProperties(taxonomy, errors);

    // Validate QName references by type throughout taxonomy
    validateQNameReferencesByType(taxonomy, errors);

    return errors;
}

/**
 * Validate that domain definitions match their domain class types
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDomainDefinitionsAgainstRootTypes(taxonomy, errors) {
    if (!taxonomy.domains || !taxonomy.domainClasses) {
        return;
    }

    // Build a map of domain class names to their allowed domain items
    const domainClassAllowedItems = new Map();
    taxonomy.domainClasses.forEach(root => {
        if (root.allowedDomainItems && Array.isArray(root.allowedDomainItems)) {
            domainClassAllowedItems.set(root.name, root.allowedDomainItems);
        }
    });

    // Helper to determine if allowed items are object types (member-based domain)
    function isObjectBasedDomain(allowedItems) {
        if (!allowedItems || allowedItems.length === 0) return true; // If not specified, allow both
        return allowedItems.some(item => 
            item.endsWith('Object') || 
            item.includes(':memberObject') ||
            item.includes(':conceptObject') ||
            item.includes(':entityObject') ||
            item.includes(':unitObject')
        );
    }

    // Helper to determine if allowed items are XSD datatypes (typed domain)
    function isTypedDomain(allowedItems) {
        if (!allowedItems || allowedItems.length === 0) return true; // If not specified, allow both
        return allowedItems.some(item => 
            item.startsWith('xs:') || 
            item.startsWith('xsd:') ||
            item.includes(':dateTime') ||
            item.includes(':string') ||
            item.includes(':token') ||
            item.includes(':duration')
        );
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        if (!domain.root) return;

        const allowedItems = domainClassAllowedItems.get(domain.root);
        if (!allowedItems) return; // Skip if not defined

        const isObjectBased = isObjectBasedDomain(allowedItems);
        const isTyped = isTypedDomain(allowedItems);

        // Check if domainDataType is used but domain class only allows object types
        if (domain.domainDataType) {
            if (isObjectBased && !isTyped) {
                errors.domainDefinitionErrors.push({
                    code: 'oimte:domainClassMismatchWithDomain',
                    domain: domain.name,
                    domainClass: domain.root,
                    allowedDomainItems: allowedItems,
                    invalidAttribute: 'domainDataType',
                    message: `Domain "${domain.name}" has domainDataType="${domain.domainDataType}", but its domain class "${domain.root}" has allowedDomainItems=[${allowedItems.join(', ')}] which specifies object types for a member-based domain. domainDataType is only used for typed domains with XSD datatypes.`
                });
            }
        }

        // Check if relationships are used but domain class only allows typed domains (XSD types)
        if (domain.relationships && domain.relationships.length > 0) {
            if (isTyped && !isObjectBased) {
                errors.domainDefinitionErrors.push({
                    code: 'oimte:domainClassMismatchWithDomain',
                    domain: domain.name,
                    domainClass: domain.root,
                    allowedDomainItems: allowedItems,
                    invalidAttribute: 'relationships',
                    message: `Domain "${domain.name}" has ${domain.relationships.length} relationship(s) defined, but its domain class "${domain.root}" has allowedDomainItems=[${allowedItems.join(', ')}] which specifies XSD datatypes for a typed domain. Typed domains cannot have relationship hierarchies.`
                });
            }
        }
    });
}

/**
 * Validate that entity domains only have entity objects or xbrl:entityDomain as relationship sources
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateEntityDomainSources(taxonomy, errors) {
    if (!taxonomy.domains) {
        return;
    }

    // Build a set of entity names
    const entityNames = new Set();
    if (taxonomy.entities) {
        taxonomy.entities.forEach(entity => {
            if (entity.name) {
                entityNames.add(entity.name);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        // Only check domains with root xbrl:entityDomain
        if (domain.root !== 'xbrl:entityDomain') {
            return;
        }

        // Check each relationship in the domain
        if (domain.relationships && Array.isArray(domain.relationships)) {
            domain.relationships.forEach(rel => {
                if (!rel.source) return;

                // Source must be either an entity object or xbrl:entityDomain
                const isEntityObject = entityNames.has(rel.source);
                const isEntityDomainClass = rel.source === 'xbrl:entityDomain';

                if (!isEntityObject && !isEntityDomainClass) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:invalidEntityDomainSource',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'source',
                        message: `Domain "${domain.name}" has root "xbrl:entityDomain" but relationship source "${rel.source}" is not an entity object or "xbrl:entityDomain". Entity domains must only contain entities.`
                    });
                }
            });
        }
    });
}

/**
 * Validate that entity domains only have entity objects as relationship targets
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateEntityDomainTargets(taxonomy, errors) {
    if (!taxonomy.domains) {
        return;
    }

    // Build a set of entity names
    const entityNames = new Set();
    if (taxonomy.entities) {
        taxonomy.entities.forEach(entity => {
            if (entity.name) {
                entityNames.add(entity.name);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        // Only check domains with root xbrl:entityDomain
        if (domain.root !== 'xbrl:entityDomain') {
            return;
        }

        // Check each relationship in the domain
        if (domain.relationships && Array.isArray(domain.relationships)) {
            domain.relationships.forEach(rel => {
                if (!rel.target) return;

                // Target must be an entity object
                const isEntityObject = entityNames.has(rel.target);

                if (!isEntityObject) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:invalidEntityDomainTarget',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'target',
                        message: `Domain "${domain.name}" has root "xbrl:entityDomain" but relationship target "${rel.target}" is not an entity object. Entity domains must only contain entity objects as targets.`
                    });
                }
            });
        }
    });
}

/**
 * Validate that unit domains only have unit objects or xbrl:unitDomain as relationship sources
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateUnitDomainSources(taxonomy, errors) {
    if (!taxonomy.domains) {
        return;
    }

    // Build a set of unit names
    const unitNames = new Set();
    if (taxonomy.units) {
        taxonomy.units.forEach(unit => {
            if (unit.name) {
                unitNames.add(unit.name);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        // Only check domains with root xbrl:unitDomain
        if (domain.root !== 'xbrl:unitDomain') {
            return;
        }

        // Check each relationship in the domain
        if (domain.relationships && Array.isArray(domain.relationships)) {
            domain.relationships.forEach(rel => {
                if (!rel.source) return;

                // Source must be either a unit object or xbrl:unitDomain
                const isUnitObject = unitNames.has(rel.source);
                const isUnitDomainClass = rel.source === 'xbrl:unitDomain';

                if (!isUnitObject && !isUnitDomainClass) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:invalidUnitDomainSource',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'source',
                        message: `Domain "${domain.name}" has root "xbrl:unitDomain" but relationship source "${rel.source}" is not a unit object or "xbrl:unitDomain". Unit domains must only contain units.`
                    });
                }
            });
        }
    });
}

/**
 * Validate that unit domains only have unit objects as relationship targets
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateUnitDomainTargets(taxonomy, errors) {
    if (!taxonomy.domains) {
        return;
    }

    // Build a set of unit names
    const unitNames = new Set();
    if (taxonomy.units) {
        taxonomy.units.forEach(unit => {
            if (unit.name) {
                unitNames.add(unit.name);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        // Only check domains with root xbrl:unitDomain
        if (domain.root !== 'xbrl:unitDomain') {
            return;
        }

        // Check each relationship in the domain
        if (domain.relationships && Array.isArray(domain.relationships)) {
            domain.relationships.forEach(rel => {
                if (!rel.target) return;

                // Target must be a unit object
                const isUnitObject = unitNames.has(rel.target);

                if (!isUnitObject) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:invalidUnitDomainTarget',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'target',
                        message: `Domain "${domain.name}" has root "xbrl:unitDomain" but relationship target "${rel.target}" is not a unit object. Unit domains must only contain unit objects as targets.`
                    });
                }
            });
        }
    });
}

/**
 * Validate that unit objects are not present in non-unit domains
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateUnitInNonUnitDomain(taxonomy, errors) {
    if (!taxonomy.domains) {
        return;
    }

    // Build a set of unit names
    const unitNames = new Set();
    if (taxonomy.units) {
        taxonomy.units.forEach(unit => {
            if (unit.name) {
                unitNames.add(unit.name);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        // Only check domains that are NOT unit domains
        if (domain.root === 'xbrl:unitDomain') {
            return;
        }

        // Check each relationship in the domain
        if (domain.relationships && Array.isArray(domain.relationships)) {
            domain.relationships.forEach(rel => {
                // Check if source is a unit object
                if (rel.source && unitNames.has(rel.source)) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:unitInNonUnitDomain',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'source',
                        message: `Domain "${domain.name}" has root "${domain.root}" but relationship source "${rel.source}" is a unit object. Unit objects can only be used in domains with root "xbrl:unitDomain".`
                    });
                }

                // Check if target is a unit object
                if (rel.target && unitNames.has(rel.target)) {
                    errors.domainDefinitionErrors.push({
                        code: 'oimte:unitInNonUnitDomain',
                        domain: domain.name,
                        domainClass: domain.root,
                        source: rel.source,
                        target: rel.target,
                        invalidAttribute: 'target',
                        message: `Domain "${domain.name}" has root "${domain.root}" but relationship target "${rel.target}" is a unit object. Unit objects can only be used in domains with root "xbrl:unitDomain".`
                    });
                }
            });
        }
    });
}

/**
 * Validate that domains used in cube dimensions have roots matching the dimension's domain class
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDomainClassesMatchDimensions(taxonomy, errors) {
    if (!taxonomy.cubes || !taxonomy.dimensions || !taxonomy.domains) {
        return;
    }

    // Build a map of dimension names to their domain classs
    const dimensionToDomainClass = new Map();
    taxonomy.dimensions.forEach(dim => {
        if (dim.domainClass) {
            dimensionToDomainClass.set(dim.name, dim.domainClass);
        }
    });

    // Build a map of domain names to their roots
    const domainToRoot = new Map();
    taxonomy.domains.forEach(domain => {
        if (domain.root) {
            domainToRoot.set(domain.name, domain.root);
        }
    });

    // Check each cube dimension
    taxonomy.cubes.forEach(cube => {
        if (!cube.cubeDimensions) return;

        cube.cubeDimensions.forEach(cubeDim => {
            const expectedRoot = dimensionToDomainClass.get(cubeDim.dimensionName);
            if (!expectedRoot) return; // Skip if dimension doesn't have a domain class defined

            // Check domainName (for memberDomain)
            if (cubeDim.domainName) {
                const actualRoot = domainToRoot.get(cubeDim.domainName);
                if (actualRoot && actualRoot !== expectedRoot) {
                    errors.invalidDomainUsage.push({
                        code: 'oimte:invalidCubeDimensionDomainName',
                        cube: cube.name,
                        dimension: cubeDim.dimensionName,
                        domain: cubeDim.domainName,
                        domainClass: actualRoot,
                        expectedRoot: expectedRoot,
                        message: `Cube dimension "${cubeDim.dimensionName}" in cube "${cube.name}" uses domain "${cubeDim.domainName}" with root "${actualRoot}", but the dimension requires root "${expectedRoot}".`
                    });
                }
            }

            // Check typedDomainNames (for typedDomain)
            if (cubeDim.typedDomainNames && Array.isArray(cubeDim.typedDomainNames)) {
                cubeDim.typedDomainNames.forEach(domainName => {
                    const actualRoot = domainToRoot.get(domainName);
                    if (actualRoot && actualRoot !== expectedRoot) {
                        errors.invalidDomainUsage.push({
                            code: 'oimte:invalidCubeDimensionDomainName',
                            cube: cube.name,
                            dimension: cubeDim.dimensionName,
                            domain: domainName,
                            domainClass: actualRoot,
                            expectedRoot: expectedRoot,
                            message: `Cube dimension "${cubeDim.dimensionName}" in cube "${cube.name}" uses typed domain "${domainName}" with root "${actualRoot}", but the dimension requires root "${expectedRoot}".`
                        });
                    }
                });
            }
        });
    });
}

/**
 * Validate that properties are only used on allowed objects
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validatePropertyUsageOnObjects(taxonomy, errors) {
    if (!taxonomy.propertyTypes) {
        return;
    }

    // Build a map of property names to their allowed objects
    const propertyAllowedObjects = new Map();
    taxonomy.propertyTypes.forEach(propType => {
        if (propType.name) {
            // If allowedObjects is defined, store it; otherwise property can be used anywhere
            if (propType.allowedObjects && Array.isArray(propType.allowedObjects)) {
                propertyAllowedObjects.set(propType.name, new Set(propType.allowedObjects));
            } else {
                // No restriction - property can be used on any object
                propertyAllowedObjects.set(propType.name, null);
            }
        }
    });

    // Map of object arrays to their object type
    const objectTypeMapping = [
        { array: 'members', objectType: 'xbrl:memberObject' },
        { array: 'concepts', objectType: 'xbrl:conceptObject' },
        { array: 'units', objectType: 'xbrl:unitObject' },
        { array: 'entities', objectType: 'xbrl:entityObject' },
        { array: 'groups', objectType: 'xbrl:groupObject' },
        { array: 'labels', objectType: 'xbrl:labelObject' },
        { array: 'domains', objectType: 'xbrl:domainObject' },
        { array: 'domainClasses', objectType: 'xbrl:domainClassObject' },
        { array: 'dimensions', objectType: 'xbrl:dimensionObject' },
        { array: 'abstracts', objectType: 'xbrl:abstractObject' },
        { array: 'networks', objectType: 'xbrl:networkObject' },
        { array: 'cubes', objectType: 'xbrl:cubeObject' },
        { array: 'references', objectType: 'xbrl:referenceObject' }
    ];

    // Check properties on taxonomy itself
    if (taxonomy.properties && Array.isArray(taxonomy.properties)) {
        taxonomy.properties.forEach(prop => {
            if (prop.property) {
                const allowedObjects = propertyAllowedObjects.get(prop.property);
                // Skip if property not defined (undefined means we don't know about it)
                // If allowedObjects is not null/undefined and doesn't include xbrlModelObject, it's an error
                if (allowedObjects !== null && allowedObjects !== undefined && !allowedObjects.has('xbrl:xbrlModelObject')) {
                    errors.disallowedObjectProperty.push({
                        code: 'oimte:disallowedObjectProperty',
                        property: prop.property,
                        objectType: 'xbrl:xbrlModelObject',
                        objectName: taxonomy.name,
                        allowedObjects: Array.from(allowedObjects),
                        message: `Property "${prop.property}" is used on taxonomy object "${taxonomy.name}" (xbrl:xbrlModelObject), but it is only allowed on: ${Array.from(allowedObjects).join(', ')}.`
                    });
                }
            }
        });
    }

    // Check properties on all object types
    objectTypeMapping.forEach(({ array, objectType }) => {
        if (taxonomy[array] && Array.isArray(taxonomy[array])) {
            taxonomy[array].forEach(obj => {
                if (obj.properties && Array.isArray(obj.properties)) {
                    obj.properties.forEach(prop => {
                        if (prop.property) {
                            const allowedObjects = propertyAllowedObjects.get(prop.property);
                            // Skip if property not defined (undefined means we don't know about it)
                            // If allowedObjects is not null/undefined and doesn't include this objectType, it's an error
                            if (allowedObjects !== null && allowedObjects !== undefined && !allowedObjects.has(objectType)) {
                                errors.disallowedObjectProperty.push({
                                    code: 'oimte:disallowedObjectProperty',
                                    property: prop.property,
                                    objectType: objectType,
                                    objectName: obj.name,
                                    allowedObjects: Array.from(allowedObjects),
                                    message: `Property "${prop.property}" is used on ${objectType.replace('xbrl:', '')} "${obj.name}", but it is only allowed on: ${Array.from(allowedObjects).join(', ')}.`
                                });
                            }
                        }
                    });
                }
            });
        }
    });

    // Check properties on relationships within networks
    if (taxonomy.networks && Array.isArray(taxonomy.networks)) {
        taxonomy.networks.forEach(network => {
            if (network.relationships && Array.isArray(network.relationships)) {
                network.relationships.forEach(rel => {
                    if (rel.properties && Array.isArray(rel.properties)) {
                        rel.properties.forEach(prop => {
                            if (prop.property) {
                                const allowedObjects = propertyAllowedObjects.get(prop.property);
                                // Skip if property not defined (undefined means we don't know about it)
                                // If allowedObjects is not null/undefined and doesn't include relationshipObject, it's an error
                                if (allowedObjects !== null && allowedObjects !== undefined && !allowedObjects.has('xbrl:relationshipObject')) {
                                    errors.disallowedObjectProperty.push({
                                        code: 'oimte:disallowedObjectProperty',
                                        property: prop.property,
                                        objectType: 'xbrl:relationshipObject',
                                        objectName: `${rel.source} -> ${rel.target}`,
                                        network: network.name,
                                        allowedObjects: Array.from(allowedObjects),
                                        message: `Property "${prop.property}" is used on relationship "${rel.source} -> ${rel.target}" in network "${network.name}" (xbrl:relationshipObject), but it is only allowed on: ${Array.from(allowedObjects).join(', ')}.`
                                    });
                                }
                            }
                        });
                    }
                });
            }
        });
    }
}

/**
 * Validate that properties don't have conflicting values on the same object
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateConflictingPropertyValues(taxonomy, errors) {
    // Map of object arrays to their object type
    const objectTypeMapping = [
        { array: 'members', objectType: 'xbrl:memberObject' },
        { array: 'concepts', objectType: 'xbrl:conceptObject' },
        { array: 'units', objectType: 'xbrl:unitObject' },
        { array: 'entities', objectType: 'xbrl:entityObject' },
        { array: 'groups', objectType: 'xbrl:groupObject' },
        { array: 'labels', objectType: 'xbrl:labelObject' },
        { array: 'domains', objectType: 'xbrl:domainObject' },
        { array: 'domainClasses', objectType: 'xbrl:domainClassObject' },
        { array: 'dimensions', objectType: 'xbrl:dimensionObject' },
        { array: 'abstracts', objectType: 'xbrl:abstractObject' },
        { array: 'networks', objectType: 'xbrl:networkObject' },
        { array: 'cubes', objectType: 'xbrl:cubeObject' },
        { array: 'references', objectType: 'xbrl:referenceObject' }
    ];

    // Check properties on taxonomy itself
    if (taxonomy.properties && Array.isArray(taxonomy.properties)) {
        checkPropertiesForConflicts(
            taxonomy.properties, 
            'xbrl:xbrlModelObject', 
            taxonomy.name, 
            null, 
            errors
        );
    }

    // Check properties on all object types
    objectTypeMapping.forEach(({ array, objectType }) => {
        if (taxonomy[array] && Array.isArray(taxonomy[array])) {
            taxonomy[array].forEach(obj => {
                if (obj.properties && Array.isArray(obj.properties)) {
                    checkPropertiesForConflicts(
                        obj.properties, 
                        objectType, 
                        obj.name, 
                        null, 
                        errors
                    );
                }
            });
        }
    });

    // Check properties on relationships within networks
    if (taxonomy.networks && Array.isArray(taxonomy.networks)) {
        taxonomy.networks.forEach(network => {
            if (network.relationships && Array.isArray(network.relationships)) {
                network.relationships.forEach(rel => {
                    if (rel.properties && Array.isArray(rel.properties)) {
                        checkPropertiesForConflicts(
                            rel.properties, 
                            'xbrl:relationshipObject', 
                            `${rel.source} -> ${rel.target}`, 
                            network.name, 
                            errors
                        );
                    }
                });
            }
        });
    }
}

/**
 * Helper function to check properties array for conflicting values
 * @param {Array} properties - Array of property objects
 * @param {string} objectType - The object type
 * @param {string} objectName - The object name
 * @param {string} networkName - The network name (for relationships)
 * @param {Object} errors - The errors object to add errors to
 */
function checkPropertiesForConflicts(properties, objectType, objectName, networkName, errors) {
    // Build a map of property names to their values
    const propertyValues = new Map();
    
    properties.forEach(prop => {
        if (prop.property) {
            if (!propertyValues.has(prop.property)) {
                propertyValues.set(prop.property, []);
            }
            propertyValues.get(prop.property).push(prop.value);
        }
    });

    // Check each property for conflicting values
    propertyValues.forEach((values, propertyName) => {
        if (values.length > 1) {
            // Check if all values are the same
            const uniqueValues = [...new Set(values.map(v => JSON.stringify(v)))];
            if (uniqueValues.length > 1) {
                // Found conflicting values
                const errorObj = {
                    code: 'oimte:conflictingPropertyValues',
                    property: propertyName,
                    objectType: objectType,
                    objectName: objectName,
                    conflictingValues: values,
                    message: `Property "${propertyName}" is defined ${values.length} times on ${objectType.replace('xbrl:', '')} "${objectName}" with conflicting values: ${values.map(v => JSON.stringify(v)).join(', ')}.`
                };
                
                if (networkName) {
                    errorObj.network = networkName;
                }
                
                errors.conflictingPropertyValues.push(errorObj);
            }
        }
    });
}

/**
 * Validate that all cubes have xbrl:concept as a dimension
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeMissingConceptDimension(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    taxonomy.cubes.forEach(cube => {
        // Check if the cube has cubeDimensions array defined
        if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
            return;
        }

        // Check if xbrl:concept is present in the cubeDimensions array
        const hasConceptDimension = cube.cubeDimensions.some(cd => 
            cd.dimensionName === 'xbrl:concept'
        );

        if (!hasConceptDimension) {
            errors.cubeMissingConceptDimension.push({
                code: 'oimte:cubeMissingConceptDimension',
                cubeName: cube.name,
                cubeType: cube.cubeType || 'unknown',
                message: `Cube "${cube.name}" is missing the required xbrl:concept dimension in its cubeDimensions array.`
            });
        }
    });
}

/**
 * Validate that cubes don't include themselves in the excludeCubes array
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeExcludeSelfReference(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    console.log('[validateCubeExcludeSelfReference] Checking', taxonomy.cubes.length, 'cubes');

    taxonomy.cubes.forEach(cube => {
        // Check if the cube has excludeCubes array defined
        if (!cube.excludeCubes || !Array.isArray(cube.excludeCubes)) {
            return;
        }

        console.log('[validateCubeExcludeSelfReference] Cube', cube.name, 'has excludeCubes:', cube.excludeCubes);

        // Check if the cube's own name appears in the excludeCubes array
        if (cube.excludeCubes.includes(cube.name)) {
            console.log('[validateCubeExcludeSelfReference] ERROR: Cube', cube.name, 'excludes itself!');
            errors.excludeCubeSelfReference.push({
                code: 'oimte:excludeCubeSelfReference',
                cubeName: cube.name,
                message: `Cube "${cube.name}" cannot exclude itself. The excludeCubes array includes the cube's own name.`
            });
        }
    });

    console.log('[validateCubeExcludeSelfReference] Found', errors.excludeCubeSelfReference.length, 'errors');
}

/**
 * Validate that periodConstraints property is only used on xbrl:period dimension
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validatePeriodConstraintDimension(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    console.log('[validatePeriodConstraintDimension] Checking', taxonomy.cubes.length, 'cubes');

    taxonomy.cubes.forEach(cube => {
        // Check if the cube has cubeDimensions defined
        if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
            return;
        }

        cube.cubeDimensions.forEach((cubeDim, index) => {
            // Check if this cube dimension has periodConstraints defined
            if (cubeDim.periodConstraints && Array.isArray(cubeDim.periodConstraints) && cubeDim.periodConstraints.length > 0) {
                // periodConstraints can only be used on xbrl:period dimension
                if (cubeDim.dimensionName !== 'xbrl:period') {
                    console.log('[validatePeriodConstraintDimension] ERROR: Cube', cube.name, 'dimension', cubeDim.dimensionName, 'has periodConstraints but is not xbrl:period');
                    errors.invalidPeriodConstraintDimension.push({
                        code: 'oimte:invalidPeriodConstraintDimension',
                        cubeName: cube.name,
                        dimensionName: cubeDim.dimensionName,
                        dimensionIndex: index,
                        message: `Cube "${cube.name}" has periodConstraints defined on dimension "${cubeDim.dimensionName}" at index ${index}, but periodConstraints can only be used with the xbrl:period dimension.`
                    });
                }
            }
        });
    });

    console.log('[validatePeriodConstraintDimension] Found', errors.invalidPeriodConstraintDimension.length, 'errors');
}

/**
 * Validate that timeSpan property is not used redundantly with both startDate and endDate
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateRedundantTimeSpanProperty(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    console.log('[validateRedundantTimeSpanProperty] Checking', taxonomy.cubes.length, 'cubes');

    taxonomy.cubes.forEach(cube => {
        // Check if the cube has cubeDimensions defined
        if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
            return;
        }

        cube.cubeDimensions.forEach((cubeDim, dimIndex) => {
            // Check if this cube dimension has periodConstraints defined
            if (cubeDim.periodConstraints && Array.isArray(cubeDim.periodConstraints)) {
                cubeDim.periodConstraints.forEach((constraint, constraintIndex) => {
                    // Check if timeSpan is used with both startDate and endDate
                    const hasTimeSpan = constraint.timeSpan !== undefined && constraint.timeSpan !== null;
                    const hasStartDate = constraint.startDate !== undefined && constraint.startDate !== null;
                    const hasEndDate = constraint.endDate !== undefined && constraint.endDate !== null;

                    if (hasTimeSpan && hasStartDate && hasEndDate) {
                        console.log('[validateRedundantTimeSpanProperty] ERROR: Cube', cube.name, 'has redundant timeSpan with both startDate and endDate');
                        errors.redundantTimeSpanProperty.push({
                            code: 'oimte:redundantTimeSpanProperty',
                            cubeName: cube.name,
                            dimensionName: cubeDim.dimensionName,
                            dimensionIndex: dimIndex,
                            constraintIndex: constraintIndex,
                            message: `Period constraint at index ${constraintIndex} in cube "${cube.name}" dimension "${cubeDim.dimensionName}" has redundant timeSpan property defined together with both startDate and endDate. The timeSpan property must not be used when both endpoints are already defined.`
                        });
                    }
                });
            }
        });
    });

    console.log('[validateRedundantTimeSpanProperty] Found', errors.redundantTimeSpanProperty.length, 'errors');
}

/**
 * Validate that domain objects match their domainClass's allowedDomainItems
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateInvalidDomainObject(taxonomy, errors) {
    if (!taxonomy.domains || !Array.isArray(taxonomy.domains)) {
        return;
    }

    console.log('[validateInvalidDomainObject] Checking', taxonomy.domains.length, 'domains');

    // Build a map of domainClass names to their allowedDomainItems
    const domainClassAllowedItems = new Map();
    
    // Add built-in domain classs with their implicit allowedDomainItems
    domainClassAllowedItems.set('xbrl:conceptDomain', ['xbrl:conceptObject', 'xbrl:abstractObject']);
    domainClassAllowedItems.set('xbrl:unitDomain', ['xbrl:unitObject']);
    domainClassAllowedItems.set('xbrl:entityDomain', ['xbrl:entityObject']);
    domainClassAllowedItems.set('xbrl:languageDomain', ['xbrl:memberObject']); // Language domain allows members
    
    // Add custom domain classs from taxonomy
    if (taxonomy.domainClasses && Array.isArray(taxonomy.domainClasses)) {
        taxonomy.domainClasses.forEach(root => {
            if (root.name && root.allowedDomainItems && Array.isArray(root.allowedDomainItems)) {
                domainClassAllowedItems.set(root.name, root.allowedDomainItems);
            }
        });
    }

    // Check each domain
    taxonomy.domains.forEach(domain => {
        if (!domain.root || !domain.relationships || !Array.isArray(domain.relationships)) {
            return;
        }

        const allowedItems = domainClassAllowedItems.get(domain.root);
        if (!allowedItems) {
            // If no allowedDomainItems defined, any object type is allowed
            return;
        }

        // Check each relationship in the domain
        domain.relationships.forEach((rel, relIndex) => {
            // Check source object (must be in allowedDomainItems or be the domainClass itself)
            if (rel.source && rel.source !== domain.root) {
                const sourceType = getObjectTypeForQName(taxonomy, rel.source);
                if (sourceType && !allowedItems.includes(sourceType)) {
                    console.log('[validateInvalidDomainObject] ERROR: Domain', domain.name, 'has invalid source object', rel.source);
                    errors.invalidDomainObject.push({
                        code: 'oimte:invalidDomainObject',
                        domainName: domain.name,
                        domainClass: domain.root,
                        objectName: rel.source,
                        objectType: sourceType,
                        position: `source in relationship ${relIndex}`,
                        allowedTypes: allowedItems.join(', '),
                        message: `Domain "${domain.name}" with root "${domain.root}" contains object "${rel.source}" of type "${sourceType}" as a source, but only objects of type [${allowedItems.join(', ')}] are allowed.`
                    });
                }
            }

            // Check target object (must be in allowedDomainItems, but NOT the domainClass)
            if (rel.target) {
                // Domain classs cannot be targets
                if (rel.target === domain.root) {
                    return; // Skip - this is handled by oimte:invalidDomainClassTarget
                }

                const targetType = getObjectTypeForQName(taxonomy, rel.target);
                if (targetType && !allowedItems.includes(targetType)) {
                    console.log('[validateInvalidDomainObject] ERROR: Domain', domain.name, 'has invalid target object', rel.target);
                    errors.invalidDomainObject.push({
                        code: 'oimte:invalidDomainObject',
                        domainName: domain.name,
                        domainClass: domain.root,
                        objectName: rel.target,
                        objectType: targetType,
                        position: `target in relationship ${relIndex}`,
                        allowedTypes: allowedItems.join(', '),
                        message: `Domain "${domain.name}" with root "${domain.root}" contains object "${rel.target}" of type "${targetType}" as a target, but only objects of type [${allowedItems.join(', ')}] are allowed.`
                    });
                }
            }
        });
    });

    console.log('[validateInvalidDomainObject] Found', errors.invalidDomainObject.length, 'errors');
}

/**
 * Validate that domain class objects appear as sources in at least one relationship
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateMissingDomainClassSource(taxonomy, errors) {
    if (!taxonomy.domains || !Array.isArray(taxonomy.domains)) {
        return;
    }

    console.log('[validateMissingDomainClassSource] Checking', taxonomy.domains.length, 'domains');

    // Check each domain
    taxonomy.domains.forEach(domain => {
        if (!domain.root) {
            return; // Skip domains without a root
        }

        // Skip domains without relationships or with empty relationships array
        if (!domain.relationships || !Array.isArray(domain.relationships) || domain.relationships.length === 0) {
            return;
        }

        // Check if the domain class appears as a source in any relationship
        const rootAppearsAsSource = domain.relationships.some(rel => rel.source === domain.root);

        if (!rootAppearsAsSource) {
            console.log('[validateMissingDomainClassSource] ERROR: Domain', domain.name, 'has root', domain.root, 'but it never appears as a source');
            errors.missingDomainClassSource.push({
                code: 'oimte:missingDomainClassSource',
                domainName: domain.name,
                domainClass: domain.root,
                relationshipCount: domain.relationships.length,
                message: `Domain "${domain.name}" declares root "${domain.root}" but this root object is never used as a source in any relationship. Every domain class must appear as the source of at least one relationship to define the domain's member hierarchy.`
            });
        }
    });

    console.log('[validateMissingDomainClassSource] Found', errors.missingDomainClassSource.length, 'errors');
}

/**
 * Validate that domains resolve to a single root object
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateMultipleDomainClasses(taxonomy, errors) {
    if (!taxonomy.domains || !Array.isArray(taxonomy.domains)) {
        return;
    }

    console.log('[validateMultipleDomainClasses] Checking', taxonomy.domains.length, 'domains');

    // Check each domain
    taxonomy.domains.forEach(domain => {
        if (!domain.relationships || !Array.isArray(domain.relationships)) {
            return;
        }

        // Find all nodes that are targets (children)
        const targetsSet = new Set();
        domain.relationships.forEach(rel => {
            targetsSet.add(rel.target);
        });

        // Find all nodes that are sources
        const sourcesSet = new Set();
        domain.relationships.forEach(rel => {
            sourcesSet.add(rel.source);
        });

        // Actual roots are nodes that are sources but never targets
        const actualRoots = [];
        for (const source of sourcesSet) {
            if (!targetsSet.has(source)) {
                actualRoots.push(source);
            }
        }

        // Check if there are multiple roots (more than 1)
        if (actualRoots.length > 1) {
            console.log('[validateMultipleDomainClasses] ERROR: Domain', domain.name, 'has', actualRoots.length, 'roots:', actualRoots);
            errors.multipleDomainClasses.push({
                code: 'oimte:multipleDomainClasses',
                domainName: domain.name,
                declaredRoot: domain.root || 'none',
                actualRoots: actualRoots,
                rootCount: actualRoots.length,
                message: `Domain "${domain.name}" has ${actualRoots.length} root objects in its relationship structure: [${actualRoots.join(', ')}]. A domain must resolve to a single root object.`
            });
        }
    });

    console.log('[validateMultipleDomainClasses] Found', errors.multipleDomainClasses.length, 'errors');
}

/**
 * Validate that domainClass references point to legitimate domainClass objects
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 * @param {Set} definedNames - Set of all defined QNames in the taxonomy
 */
/**
 * Validate that members included as targets in a domain have the domain's root
 * listed in their domainClasses property (oimte:invalidDomainClassReference).
 * Spec: "If the member is defined in a domain relationship with a domain class root
 * that is not included in the domainClasses property of the member, an error MUST
 * be raised (!!oimte:invalidDomainClassReference)."
 */
function validateMemberDomainClassReference(taxonomy, errors) {
    if (!taxonomy.domains || !Array.isArray(taxonomy.domains)) {
        return;
    }

    // Build a lookup map: memberName → Set of domainClasses
    const memberDomainClassesMap = new Map();
    if (taxonomy.members && Array.isArray(taxonomy.members)) {
        taxonomy.members.forEach(member => {
            if (member.name && Array.isArray(member.domainClasses) && member.domainClasses.length > 0) {
                memberDomainClassesMap.set(member.name, new Set(member.domainClasses));
            }
        });
    }

    taxonomy.domains.forEach(domain => {
        const domainRoot = domain.root;
        const domainName = domain.name || domain.extendTargetName;

        // Only check domains that have a root and relationships
        if (!domainRoot || !Array.isArray(domain.relationships)) {
            return;
        }

        domain.relationships.forEach(rel => {
            const target = rel.target;
            if (!target) return;

            // Only check members that explicitly declare domainClasses
            const memberClasses = memberDomainClassesMap.get(target);
            if (!memberClasses) {
                // Member has no domainClasses property — no constraint violation
                return;
            }

            if (!memberClasses.has(domainRoot)) {
                errors.invalidDomainClassReference.push({
                    code: 'oimte:invalidDomainClassReference',
                    domainName: domainName,
                    domainRoot: domainRoot,
                    memberName: target,
                    message: `Member "${target}" is used in domain "${domainName}" whose root is "${domainRoot}", but "${domainRoot}" is not listed in the member's domainClasses property.`
                });
            }
        });
    });
}

function validateDomainClassReferences(taxonomy, errors, definedNames) {
    // Build a set of all domainClass object names
    const domainClassNames = new Set();
    if (taxonomy.domainClasses && Array.isArray(taxonomy.domainClasses)) {
        taxonomy.domainClasses.forEach(root => {
            if (root.name) {
                domainClassNames.add(root.name);
            }
        });
    }

    // Check dimension.domainClass references
    if (taxonomy.dimensions && Array.isArray(taxonomy.dimensions)) {
        taxonomy.dimensions.forEach(dim => {
            if (dim.domainClass) {
                // Check if the domainClass reference is a valid domainClass object
                if (!domainClassNames.has(dim.domainClass)) {
                    errors.invalidDomainClass.push({
                        code: 'oimte:invalidDomainClass',
                        referenceType: 'dimension',
                        dimensionName: dim.name,
                        domainClassName: dim.domainClass,
                        message: `Dimension "${dim.name}" references domainClass "${dim.domainClass}" which is not defined as a domainClass object in the taxonomy.`
                    });
                }
            }
        });
    }

    // Check domain.root references
    if (taxonomy.domains && Array.isArray(taxonomy.domains)) {
        taxonomy.domains.forEach(domain => {
            if (domain.root) {
                // Check if the root reference is a valid domainClass object
                if (!domainClassNames.has(domain.root)) {
                    errors.invalidDomainClass.push({
                        code: 'oimte:invalidDomainClass',
                        referenceType: 'domain',
                        domainName: domain.name,
                        domainClassName: domain.root,
                        message: `Domain "${domain.name}" references root "${domain.root}" which is not defined as a domainClass object in the taxonomy.`
                    });
                }
            }
        });
    }
}

/**
 * Validate that allowDomainFacts is not set to true on the xbrl:concept dimension
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateAllowDomainFactsOnConceptDimension(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    taxonomy.cubes.forEach(cube => {
        if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
            return;
        }

        // Find the concept dimension
        const conceptDimension = cube.cubeDimensions.find(cd => 
            cd.dimensionName === 'xbrl:concept'
        );

        if (conceptDimension) {
            // Check if allowDomainFacts is explicitly set to true
            if (conceptDimension.allowDomainFacts === true) {
                errors.invalidAllowDomainFactsPropertyOnConceptDimension.push({
                    code: 'oimte:invalidAllowDomainFactsPropertyOnConceptDimension',
                    cubeName: cube.name,
                    message: `The xbrl:concept dimension in cube "${cube.name}" cannot have allowDomainFacts set to true.`
                });
            }
        }
    });
}

/**
 * Validate that domainName is not used on period dimension
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDomainUsedOnPeriodDimension(taxonomy, errors) {
    if (!taxonomy.cubes || !Array.isArray(taxonomy.cubes)) {
        return;
    }

    taxonomy.cubes.forEach(cube => {
        if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
            return;
        }

        // Find the period dimension
        const periodDimension = cube.cubeDimensions.find(cd => 
            cd.dimensionName === 'xbrl:period'
        );

        if (periodDimension) {
            // Check if domainName is specified
            if (periodDimension.domainName) {
                errors.domainUsedOnPeriodDimension.push({
                    code: 'oimte:domainUsedOnPeriodDimension',
                    cubeName: cube.name,
                    domainName: periodDimension.domainName,
                    message: `The xbrl:period dimension in cube "${cube.name}" cannot have a domainName property. The period dimension is a built-in typed dimension.`
                });
            }
            
            // Check if domainDataType is specified
            if (periodDimension.domainDataType) {
                errors.domainUsedOnPeriodDimension.push({
                    code: 'oimte:domainUsedOnPeriodDimension',
                    cubeName: cube.name,
                    domainDataType: periodDimension.domainDataType,
                    message: `The xbrl:period dimension in cube "${cube.name}" cannot have a domainDataType property. The period dimension is a built-in typed dimension.`
                });
            }
        }
    });
}

/**
 * Validate that cubeTypes array only references cubeType objects
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeTypeReferences(taxonomy, errors) {
    if (!taxonomy.dimensions || !Array.isArray(taxonomy.dimensions)) {
        return;
    }

    // First, collect all cubeType names
    const cubeTypeNames = new Set();
    if (taxonomy.cubeTypes && Array.isArray(taxonomy.cubeTypes)) {
        taxonomy.cubeTypes.forEach(cubeType => {
            if (cubeType.name) {
                cubeTypeNames.add(cubeType.name);
            }
        });
    }

    // Now validate each dimension's cubeTypes array
    taxonomy.dimensions.forEach(dimension => {
        if (!dimension.cubeTypes || !Array.isArray(dimension.cubeTypes)) {
            return;
        }

        dimension.cubeTypes.forEach(cubeTypeName => {
            if (!cubeTypeNames.has(cubeTypeName)) {
                errors.invalidCubeType.push({
                    code: 'oimte:invalidCubeType',
                    dimensionName: dimension.name,
                    cubeTypeName: cubeTypeName,
                    message: `The dimension '${dimension.name}' references '${cubeTypeName}' in cubeTypes, but it is not a cubeType object.`
                });
            }
        });
    });
}

/**
 * Validate that cubeTypes don't have duplicate dimensions in cubeDimensionConstraints.allowed
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeTypeDuplicateDimensions(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    taxonomy.cubeTypes.forEach(cubeType => {
        // Check if cubeDimensionConstraints exists and has an allowed array
        if (!cubeType.cubeDimensionConstraints || 
            !cubeType.cubeDimensionConstraints.allowed || 
            !Array.isArray(cubeType.cubeDimensionConstraints.allowed)) {
            return;
        }

        const allowed = cubeType.cubeDimensionConstraints.allowed;
        const dimensionsSeen = new Set();
        const duplicates = new Set();

        // Check for duplicate dimensionName values
        allowed.forEach((constraint, index) => {
            if (constraint.dimensionName) {
                if (dimensionsSeen.has(constraint.dimensionName)) {
                    duplicates.add(constraint.dimensionName);
                } else {
                    dimensionsSeen.add(constraint.dimensionName);
                }
            }
        });

        // Report each duplicate
        duplicates.forEach(dimensionName => {
            errors.duplicateDimension.push({
                code: 'oimte:duplicateDimension',
                cubeTypeName: cubeType.name,
                dimensionName: dimensionName,
                message: `The cubeType '${cubeType.name}' has duplicate dimension '${dimensionName}' in cubeDimensionConstraints.allowed array.`
            });
        });
    });
}

/**
 * Validate that cubeTypes only have valid core dimensions in coreDimensions array
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeTypeCoreDimensions(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Valid core dimensions
    const validCoreDimensions = new Set([
        'xbrl:concept',
        'xbrl:period',
        'xbrl:entity',
        'xbrl:unit',
        'xbrl:language'
    ]);

    taxonomy.cubeTypes.forEach(cubeType => {
        // Check if coreDimensions exists and is an array
        if (!cubeType.coreDimensions || !Array.isArray(cubeType.coreDimensions)) {
            return;
        }

        // Check each core dimension
        cubeType.coreDimensions.forEach((dimensionName, index) => {
            if (!validCoreDimensions.has(dimensionName)) {
                errors.invalidCoreDimension.push({
                    code: 'oimte:invalidCoreDimension',
                    cubeTypeName: cubeType.name,
                    dimensionName: dimensionName,
                    index: index,
                    message: `The cubeType '${cubeType.name}' has invalid core dimension '${dimensionName}' at index ${index}. Core dimensions must be one of: xbrl:concept, xbrl:period, xbrl:entity, xbrl:unit, xbrl:language.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't expand data type constraints
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCubeTypeDataTypeExpansion(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Check if both have cubeDimensionConstraints.allowed
        const derivedAllowed = derivedCubeType.cubeDimensionConstraints?.allowed;
        const baseAllowed = baseCubeType.cubeDimensionConstraints?.allowed;

        if (!derivedAllowed || !Array.isArray(derivedAllowed)) {
            return;
        }

        if (!baseAllowed || !Array.isArray(baseAllowed)) {
            return;
        }

        // For each dimension constraint in derived type, check if it modifies a base constraint
        derivedAllowed.forEach((derivedConstraint, derivedIndex) => {
            if (!derivedConstraint.dimensionName || !derivedConstraint.dataType) {
                return;
            }

            // Find matching constraint in base type
            const baseConstraint = baseAllowed.find(bc => 
                bc.dimensionName === derivedConstraint.dimensionName
            );

            if (!baseConstraint || !baseConstraint.dataType) {
                return; // No matching base constraint or no dataType in base
            }

            // Check if derived dataType is different from base dataType
            // Different dataTypes are considered an invalid expansion
            // (Same dataType or more restrictive subtypes would be valid)
            if (baseConstraint.dataType !== derivedConstraint.dataType) {
                errors.invalidDataTypeExpansion.push({
                    code: 'oimte:invalidDataTypeExpansion',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    dimensionName: derivedConstraint.dimensionName,
                    baseDataType: baseConstraint.dataType,
                    derivedDataType: derivedConstraint.dataType,
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' but changes the dataType constraint for dimension '${derivedConstraint.dimensionName}' from '${baseConstraint.dataType}' to '${derivedConstraint.dataType}'. Data type changes must be the same or more restrictive, not expanded.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't relax dimension requirements from base types
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDimensionRequirementRelaxation(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Check if both have cubeDimensionConstraints.allowed
        const derivedAllowed = derivedCubeType.cubeDimensionConstraints?.allowed;
        const baseAllowed = baseCubeType.cubeDimensionConstraints?.allowed;

        if (!derivedAllowed || !Array.isArray(derivedAllowed)) {
            return;
        }

        if (!baseAllowed || !Array.isArray(baseAllowed)) {
            return;
        }

        // For each dimension constraint in base type that has required=true,
        // check if derived type relaxes it to required=false
        baseAllowed.forEach(baseConstraint => {
            // Only check if base constraint has required=true
            if (baseConstraint.required !== true || !baseConstraint.dimensionName) {
                return;
            }

            // Find matching constraint in derived type
            const derivedConstraint = derivedAllowed.find(dc => 
                dc.dimensionName === baseConstraint.dimensionName
            );

            if (!derivedConstraint) {
                return; // No matching derived constraint
            }

            // Check if derived constraint explicitly sets required=false
            if (derivedConstraint.required === false) {
                errors.invalidDimensionRequirementRelaxation.push({
                    code: 'oimte:invalidDimensionRequirementRelaxation',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    dimensionName: baseConstraint.dimensionName,
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' but relaxes the dimension requirement for '${baseConstraint.dimensionName}' from required=true to required=false. Derived cube types can only restrict, not relax, dimension requirements.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't add dimensions when base cube type has closed=true
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDimensionAddition(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Check if base has closed=true
        const baseClosed = baseCubeType.cubeDimensionConstraints?.closed;
        if (baseClosed !== true) {
            return; // Base is not closed, additions are allowed
        }

        // Get allowed dimensions from both types
        const derivedAllowed = derivedCubeType.cubeDimensionConstraints?.allowed;
        const baseAllowed = baseCubeType.cubeDimensionConstraints?.allowed;

        if (!derivedAllowed || !Array.isArray(derivedAllowed)) {
            return;
        }

        if (!baseAllowed || !Array.isArray(baseAllowed)) {
            return;
        }

        // Build set of dimension names in base type
        const baseDimensionNames = new Set();
        baseAllowed.forEach(constraint => {
            if (constraint.dimensionName) {
                baseDimensionNames.add(constraint.dimensionName);
            }
        });

        // Check for dimensions in derived type that are not in base type
        derivedAllowed.forEach(derivedConstraint => {
            if (!derivedConstraint.dimensionName) {
                return;
            }

            // If this dimension is not in the base type, it's an invalid addition
            if (!baseDimensionNames.has(derivedConstraint.dimensionName)) {
                errors.invalidDimensionAddition.push({
                    code: 'oimte:invalidDimensionAddition',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    dimensionName: derivedConstraint.dimensionName,
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and adds dimension '${derivedConstraint.dimensionName}', but the base cube type has closed=true. No additional dimensions may be added when the base type is closed.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't set closed=false when base has closed=true
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDimensionClosedExpansion(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Check if base has closed=true and derived explicitly sets closed=false
        const baseClosed = baseCubeType.cubeDimensionConstraints?.closed;
        const derivedClosed = derivedCubeType.cubeDimensionConstraints?.closed;

        // Only report error if base has closed=true and derived explicitly sets closed=false
        if (baseClosed === true && derivedClosed === false) {
            errors.invalidDimensionClosedExpansion.push({
                code: 'oimte:invalidDimensionClosedExpansion',
                derivedCubeTypeName: derivedCubeType.name,
                baseCubeTypeName: derivedCubeType.baseCubeType,
                message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and sets closed=false, but the base cube type has closed=true. Derived cube types cannot expand the closed constraint; they can only maintain or further restrict it.`
            });
        }
    });
}

/**
 * Validate that derived cubeTypes don't expand the allowed property types
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validatePropertyExpansion(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Check if base has cubeProperties.allowed
        const baseAllowed = baseCubeType.cubeProperties?.allowed;
        const derivedAllowed = derivedCubeType.cubeProperties?.allowed;

        // If base doesn't have allowed properties specified, no restriction to validate
        if (!baseAllowed || !Array.isArray(baseAllowed)) {
            return;
        }

        // If derived doesn't have allowed properties, that's fine (inherits from base)
        if (!derivedAllowed || !Array.isArray(derivedAllowed)) {
            return;
        }

        // Build set of allowed properties in base type
        const baseAllowedSet = new Set(baseAllowed);

        // Check for properties in derived type that are not in base type
        derivedAllowed.forEach(propertyType => {
            if (!baseAllowedSet.has(propertyType)) {
                errors.invalidPropertyExpansion.push({
                    code: 'oimte:invalidPropertyExpansion',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    propertyType: propertyType,
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and adds property type '${propertyType}' to cubeProperties.allowed, but this property type was not in the base type's allowed list. Derived cube types cannot expand the set of allowed property types.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't expand core dimensions
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateCoreDimensionsExpansion(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Get core dimensions from base and derived types
        const baseCoreDimensions = baseCubeType.coreDimensions;
        const derivedCoreDimensions = derivedCubeType.coreDimensions;

        // If base doesn't have coreDimensions specified, no restriction to validate
        if (!baseCoreDimensions || !Array.isArray(baseCoreDimensions)) {
            return;
        }

        // If derived doesn't have coreDimensions, that's fine (inherits from base)
        if (!derivedCoreDimensions || !Array.isArray(derivedCoreDimensions)) {
            return;
        }

        // Build set of core dimensions in base type
        const baseCoreDimensionsSet = new Set(baseCoreDimensions);

        // Check for core dimensions in derived type that are not in base type
        derivedCoreDimensions.forEach(coreDimension => {
            if (!baseCoreDimensionsSet.has(coreDimension)) {
                errors.coreDimensionsExpansion.push({
                    code: 'oimte:coreDimensionsExpansion',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    coreDimension: coreDimension,
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and adds core dimension '${coreDimension}' that was not in the base type. Derived cube types cannot expand the set of core dimensions.`
                });
            }
        });
    });
}

/**
 * Helper function to create a relationship signature for comparison
 * @param {Object} rel - The relationship object
 * @returns {string} A string signature of the relationship
 */
function getRelationshipSignature(rel) {
    const parts = [rel.type || ''];
    
    if (rel.source) {
        parts.push('src:' + (rel.source.qname || rel.source.objectType || rel.source.dataType || ''));
    }
    
    if (rel.target) {
        parts.push('tgt:' + (rel.target.qname || rel.target.objectType || rel.target.dataType || ''));
    }
    
    return parts.join('|');
}

/**
 * Validate that derived cubeTypes don't relax relationship constraints
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateRelationshipConstraintRelaxation(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // If derived type doesn't define cubeRelationships at all, it inherits from base without modification
        if (!derivedCubeType.cubeRelationships) {
            return; // No cubeRelationships object means full inheritance - no relaxation
        }

        // Get required relationships from base type
        const baseRequired = baseCubeType.cubeRelationships?.required;
        if (!baseRequired || !Array.isArray(baseRequired)) {
            return; // No required relationships in base to validate
        }

        // Get required and allowed relationships from derived type
        const derivedRequired = derivedCubeType.cubeRelationships.required || [];
        const derivedAllowed = derivedCubeType.cubeRelationships.allowed || [];

        // Build sets of relationship signatures
        const derivedRequiredSigs = new Set(
            derivedRequired.map(rel => getRelationshipSignature(rel))
        );
        const derivedAllowedSigs = new Set(
            derivedAllowed.map(rel => getRelationshipSignature(rel))
        );

        // Check each required relationship in base type
        baseRequired.forEach(baseRel => {
            const baseSig = getRelationshipSignature(baseRel);
            
            // If the relationship is not in derived required, it's a relaxation
            if (!derivedRequiredSigs.has(baseSig)) {
                // Check if it was moved to allowed (explicit relaxation)
                const movedToAllowed = derivedAllowedSigs.has(baseSig);
                
                errors.invalidRelationshipConstraintRelaxation.push({
                    code: 'oimte:invalidRelationshipConstraintRelaxation',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    relationshipType: baseRel.type,
                    sourceConstraint: baseRel.source ? JSON.stringify(baseRel.source) : 'none',
                    targetConstraint: baseRel.target ? JSON.stringify(baseRel.target) : 'none',
                    relaxationType: movedToAllowed ? 'moved to allowed' : 'removed from required',
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and relaxes a required relationship constraint. The relationship type '${baseRel.type}' was required in the base type but is ${movedToAllowed ? 'only allowed' : 'not required'} in the derived type. Derived cube types cannot relax relationship constraints.`
                });
            }
        });
    });
}

/**
 * Validate that derived cubeTypes don't expand allowed relationships
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateRelationshipExpansion(taxonomy, errors) {
    if (!taxonomy.cubeTypes || !Array.isArray(taxonomy.cubeTypes)) {
        return;
    }

    // Build a map of cubeType names to their objects for lookup
    const cubeTypeMap = new Map();
    taxonomy.cubeTypes.forEach(cubeType => {
        if (cubeType.name) {
            cubeTypeMap.set(cubeType.name, cubeType);
        }
    });

    // Check each cubeType that has a baseCubeType
    taxonomy.cubeTypes.forEach(derivedCubeType => {
        if (!derivedCubeType.baseCubeType) {
            return; // Not a derived cube type
        }

        const baseCubeType = cubeTypeMap.get(derivedCubeType.baseCubeType);
        if (!baseCubeType) {
            return; // Base cube type not found (separate validation will catch this)
        }

        // Get allowed relationships from base and derived types
        const baseAllowed = baseCubeType.cubeRelationships?.allowed;
        const derivedAllowed = derivedCubeType.cubeRelationships?.allowed;

        // If base doesn't have allowed relationships specified, no restriction to validate
        if (!baseAllowed || !Array.isArray(baseAllowed)) {
            return;
        }

        // If derived doesn't have allowed relationships, that's fine (inherits from base)
        if (!derivedAllowed || !Array.isArray(derivedAllowed)) {
            return;
        }

        // Build set of allowed relationship signatures in base type
        const baseAllowedSigs = new Set(
            baseAllowed.map(rel => getRelationshipSignature(rel))
        );

        // Check for relationships in derived type that are not in base type
        derivedAllowed.forEach(derivedRel => {
            const derivedSig = getRelationshipSignature(derivedRel);
            
            if (!baseAllowedSigs.has(derivedSig)) {
                errors.invalidRelationshipExpansion.push({
                    code: 'oimte:invalidRelationshipExpansion',
                    derivedCubeTypeName: derivedCubeType.name,
                    baseCubeTypeName: derivedCubeType.baseCubeType,
                    relationshipType: derivedRel.type,
                    sourceConstraint: derivedRel.source ? JSON.stringify(derivedRel.source) : 'none',
                    targetConstraint: derivedRel.target ? JSON.stringify(derivedRel.target) : 'none',
                    message: `The cubeType '${derivedCubeType.name}' extends '${derivedCubeType.baseCubeType}' and adds relationship type '${derivedRel.type}' to cubeRelationships.allowed, but this relationship was not in the base type's allowed list. Derived cube types cannot expand the set of allowed relationships.`
                });
            }
        });
    });
}

/**
 * Validate that domainDataType in cubeDimensions matches allowedDomainItems in domainClass
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateDomainDataTypeForDomainClass(taxonomy, errors) {
    if (!taxonomy.cubes || !taxonomy.dimensions || !taxonomy.domainClasses) {
        return;
    }

    // Build a map of dimension names to their domain classs
    const dimensionToDomainClass = new Map();
    if (Array.isArray(taxonomy.dimensions)) {
        taxonomy.dimensions.forEach(dimension => {
            if (dimension.name && dimension.domainClass) {
                dimensionToDomainClass.set(dimension.name, dimension.domainClass);
            }
        });
    }

    // Build a map of domain class names to their allowedDomainItems
    const domainClassToAllowedItems = new Map();
    if (Array.isArray(taxonomy.domainClasses)) {
        taxonomy.domainClasses.forEach(domainClass => {
            if (domainClass.name && domainClass.allowedDomainItems) {
                domainClassToAllowedItems.set(domainClass.name, domainClass.allowedDomainItems);
            }
        });
    }

    // Check each cube's dimensions
    if (Array.isArray(taxonomy.cubes)) {
        taxonomy.cubes.forEach(cube => {
            if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
                return;
            }

            cube.cubeDimensions.forEach(cubeDim => {
                // Only check if domainDataType is specified
                if (!cubeDim.domainDataType || !cubeDim.dimensionName) {
                    return;
                }

                // Get the domain class for this dimension
                const domainClass = dimensionToDomainClass.get(cubeDim.dimensionName);
                if (!domainClass) {
                    return; // No domain class, skip (other validators will catch this)
                }

                // Get the allowed domain items for this domain class
                const allowedItems = domainClassToAllowedItems.get(domainClass);
                if (!allowedItems || !Array.isArray(allowedItems)) {
                    return; // No allowed items specified, skip
                }

                // Check if the domainDataType is in the allowed items
                if (!allowedItems.includes(cubeDim.domainDataType)) {
                    errors.invalidDataTypeForDomainClass.push({
                        code: 'oimte:invalidDataTypeForDomainClass',
                        cubeName: cube.name,
                        dimensionName: cubeDim.dimensionName,
                        domainDataType: cubeDim.domainDataType,
                        domainClass: domainClass,
                        allowedTypes: allowedItems,
                        message: `Cube dimension '${cubeDim.dimensionName}' in cube '${cube.name}' uses domainDataType '${cubeDim.domainDataType}', but the domain class '${domainClass}' only allows: ${allowedItems.join(', ')}.`
                    });
                }
            });
        });
    }
}

/**
 * Validate that dimensionName references point to legitimate dimension objects
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 * @param {Set} definedNames - Set of all defined QNames in the taxonomy
 */
function validateDimensionNameReferences(taxonomy, errors, definedNames) {
    // Build a set of all dimension object names
    const dimensionNames = new Set();
    
    // Add built-in dimensions
    dimensionNames.add('xbrl:concept');
    dimensionNames.add('xbrl:period');
    dimensionNames.add('xbrl:entity');
    dimensionNames.add('xbrl:unit');
    dimensionNames.add('xbrl:language');
    dimensionNames.add('xbrl:noteId');
    
    // Add taxonomy-defined dimensions
    if (taxonomy.dimensions && Array.isArray(taxonomy.dimensions)) {
        taxonomy.dimensions.forEach(dim => {
            if (dim.name) {
                dimensionNames.add(dim.name);
            }
        });
    }

    // Check cube.cubeDimensions
    if (taxonomy.cubes && Array.isArray(taxonomy.cubes)) {
        taxonomy.cubes.forEach(cube => {
            if (!cube.cubeDimensions || !Array.isArray(cube.cubeDimensions)) {
                return;
            }

            cube.cubeDimensions.forEach(cubeDim => {
                if (cubeDim.dimensionName && !dimensionNames.has(cubeDim.dimensionName)) {
                    errors.dimensionNameNotDimensionObject.push({
                        code: 'oimte:dimensionNameNotDimensionObject',
                        context: 'cube',
                        cubeName: cube.name,
                        dimensionName: cubeDim.dimensionName,
                        message: `Cube "${cube.name}" references dimensionName "${cubeDim.dimensionName}" which is not defined as a dimension object in the taxonomy.`
                    });
                }
            });
        });
    }

    // Check cubeType.allowedCubeDimensions
    if (taxonomy.cubeTypes && Array.isArray(taxonomy.cubeTypes)) {
        taxonomy.cubeTypes.forEach(cubeType => {
            if (!cubeType.allowedCubeDimensions || !Array.isArray(cubeType.allowedCubeDimensions)) {
                return;
            }

            cubeType.allowedCubeDimensions.forEach(allowedDim => {
                if (allowedDim.dimensionName && !dimensionNames.has(allowedDim.dimensionName)) {
                    errors.dimensionNameNotDimensionObject.push({
                        code: 'oimte:dimensionNameNotDimensionObject',
                        context: 'cubeType',
                        cubeTypeName: cubeType.name,
                        dimensionName: allowedDim.dimensionName,
                        message: `Cube type "${cubeType.name}" references dimensionName "${allowedDim.dimensionName}" in allowedCubeDimensions which is not defined as a dimension object in the taxonomy.`
                    });
                }
            });
        });
    }

    // Check layouts.dataTables (xAxis, yAxis, zAxis)
    if (taxonomy.layouts && Array.isArray(taxonomy.layouts)) {
        taxonomy.layouts.forEach(layout => {
            if (!layout.dataTables || !Array.isArray(layout.dataTables)) return;
            layout.dataTables.forEach(dataTable => {
            const axes = [
                { axis: dataTable.xAxis, type: 'xAxis' },
                { axis: dataTable.yAxis, type: 'yAxis' },
                { axis: dataTable.zAxis, type: 'zAxis' }
            ];

            axes.forEach(({ axis, type }) => {
                if (!axis || !Array.isArray(axis)) {
                    return;
                }

                axis.forEach(axisItem => {
                    if (axisItem.dimensionName && !dimensionNames.has(axisItem.dimensionName)) {
                        errors.dimensionNameNotDimensionObject.push({
                            code: 'oimte:dimensionNameNotDimensionObject',
                            context: 'dataTable',
                            dataTableName: dataTable.name || 'unnamed',
                            axisType: type,
                            dimensionName: axisItem.dimensionName,
                            message: `Data table "${dataTable.name || 'unnamed'}" references dimensionName "${axisItem.dimensionName}" in ${type} which is not defined as a dimension object in the taxonomy.`
                        });
                    }
                });
            });
            });
        });
    }
}

/**
 * Validate reference extension properties (extendTargetName)
 * Ensures that when a reference uses extendTargetName, its referenceType and language
 * match the target reference object
 * @param {Object} taxonomy - The taxonomy object
 * @param {Object} errors - The errors object to add errors to
 */
function validateReferenceExtensionProperties(taxonomy, errors) {
    if (!taxonomy.references || !Array.isArray(taxonomy.references)) {
        return;
    }

    // Build a map of reference names to their properties
    const referenceMap = new Map();
    taxonomy.references.forEach(reference => {
        if (reference.name) {
            referenceMap.set(reference.name, reference);
        }
    });

    // Check references with extendTargetName
    taxonomy.references.forEach((reference, index) => {
        if (!reference.extendTargetName) {
            return; // Skip references without extendTargetName
        }

        // Find the target reference
        const targetReference = referenceMap.get(reference.extendTargetName);
        
        if (!targetReference) {
            // Target not found - this will be caught by QName validation
            return;
        }

        // Validate referenceType matches
        if (reference.referenceType && targetReference.referenceType) {
            if (reference.referenceType !== targetReference.referenceType) {
                if (!errors.referenceTypeRedefined) {
                    errors.referenceTypeRedefined = [];
                }
                errors.referenceTypeRedefined.push({
                    code: 'oimte:referenceTypeRedefined',
                    reference: reference.extendTargetName,
                    extensionReferenceType: reference.referenceType,
                    targetReferenceType: targetReference.referenceType,
                    message: `Reference extension at index ${index} extends "${reference.extendTargetName}" but attempts to redefine referenceType from "${targetReference.referenceType}" to "${reference.referenceType}". The referenceType must match the target reference.`
                });
            }
        }

        // Validate language property is not redefined
        if (reference.language && targetReference.language) {
            if (reference.language !== targetReference.language) {
                if (!errors.referenceLanguageRedefined) {
                    errors.referenceLanguageRedefined = [];
                }
                errors.referenceLanguageRedefined.push({
                    code: 'oimte:referenceLanguageRedefined',
                    reference: reference.extendTargetName,
                    extensionLanguage: reference.language,
                    targetLanguage: targetReference.language,
                    message: `Reference extension at index ${index} extends "${reference.extendTargetName}" but attempts to redefine language from "${targetReference.language}" to "${reference.language}". The language property must not be redefined in extensions.`
                });
            }
        }
    });
}

/**
 * Validate QName references by type throughout the taxonomy
 * Uses specialized QName types (dataTypeQName, conceptQName, etc.) to ensure referential integrity
 */
function validateQNameReferencesByType(taxonomy, errors) {
    if (!taxonomy) return;
    
    // Helper function to populate a set from either an array or object
    function populateSet(targetSet, source) {
        if (!source) return;
        
        if (Array.isArray(source)) {
            // Handle array format (e.g., dataTypes: [{name: "xbrli:monetary"}, ...])
            source.forEach(item => {
                if (item && item.name) {
                    targetSet.add(item.name);
                }
            });
        } else if (typeof source === 'object') {
            // Handle object format (e.g., concepts: {"concept1": {...}, "concept2": {...}})
            Object.keys(source).forEach(name => targetSet.add(name));
        }
    }
    
    // Build sets of valid reference targets for each type
    const dataTypes = new Set();
    const concepts = new Set();
    const dimensions = new Set(['xbrl:concept', 'xbrl:period', 'xbrl:entity', 'xbrl:unit', 'xbrl:language', 'xbrl:noteId']); // Built-in dimensions
    const domains = new Set();
    const domainClasses = new Set();
    const cubes = new Set();
    const cubeTypes = new Set();
    const networks = new Set();
    const relationshipTypes = new Set();
    const labelTypes = new Set();
    const referenceTypes = new Set();
    const propertyTypes = new Set();
    const groups = new Set();
    const taxonomies = new Set();
    const units = new Set();
    
    // Populate dataTypes set
    populateSet(dataTypes, taxonomy.dataTypes);
    
    // Populate concepts set
    populateSet(concepts, taxonomy.concepts);
    
    // Populate dimensions set
    populateSet(dimensions, taxonomy.dimensions);
    
    // Populate domains set
    populateSet(domains, taxonomy.domains);
    
    // Populate domainClasses set
    populateSet(domainClasses, taxonomy.domainClasses);
    
    // Populate cubes set
    populateSet(cubes, taxonomy.cubes);
    
    // Populate cubeTypes set
    populateSet(cubeTypes, taxonomy.cubeTypes);
    
    // Populate networks set
    populateSet(networks, taxonomy.networks);
    
    // Populate relationshipTypes set
    populateSet(relationshipTypes, taxonomy.relationshipTypes);
    
    // Populate labelTypes set
    populateSet(labelTypes, taxonomy.labelTypes);
    
    // Populate referenceTypes set
    populateSet(referenceTypes, taxonomy.referenceTypes);
    
    // Populate propertyTypes set
    populateSet(propertyTypes, taxonomy.propertyTypes);
    
    // Populate modelTypes set
    const modelTypes = new Set();
    populateSet(modelTypes, taxonomy.modelTypes);
    
    // Populate groups set
    populateSet(groups, taxonomy.groups);
    
    // Populate taxonomies set
    if (taxonomy.importedTaxonomies) {
        taxonomy.importedTaxonomies.forEach(imported => {
            if (imported.taxonomyName) taxonomies.add(imported.taxonomyName);
        });
    }
    
    // Populate units set
    populateSet(units, taxonomy.units);
    
    // Helper function to iterate over array or object format
    function forEachItem(source, callback) {
        if (!source) return;
        
        if (Array.isArray(source)) {
            source.forEach((item, index) => {
                if (item && item.name) {
                    callback(item.name, item, index);
                }
            });
        } else if (typeof source === 'object') {
            Object.entries(source).forEach(([name, item]) => {
                callback(name, item);
            });
        }
    }
    
    // Validate dataTypeQName references
    
    // concepts.dataType
    forEachItem(taxonomy.concepts, (conceptName, concept) => {
        if (concept.dataType && !dataTypes.has(concept.dataType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'concept',
                name: conceptName,
                field: 'dataType',
                reference: concept.dataType
            });
        }
    });
    
    // propertyTypes.dataType
    forEachItem(taxonomy.propertyTypes, (propTypeName, propType) => {
        if (propType.dataType && !dataTypes.has(propType.dataType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'propertyType',
                name: propTypeName,
                field: 'dataType',
                reference: propType.dataType
            });
        }
    });
    
    // units.dataType
    forEachItem(taxonomy.units, (unitName, unit) => {
        if (unit.dataType && !dataTypes.has(unit.dataType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'unit',
                name: unitName,
                field: 'dataType',
                reference: unit.dataType
            });
        }
    });
    
    // dataTypes.baseType
    forEachItem(taxonomy.dataTypes, (dataTypeName, dataType) => {
        if (dataType.baseType && !dataTypes.has(dataType.baseType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'dataType',
                name: dataTypeName,
                field: 'baseType',
                reference: dataType.baseType
            });
        }
    });
    
    // transforms.inputDataType and outputDataType
    forEachItem(taxonomy.transforms, (transformName, transform) => {
        if (transform.inputDataType && !dataTypes.has(transform.inputDataType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'transform',
                name: transformName,
                field: 'inputDataType',
                reference: transform.inputDataType
            });
        }
        if (transform.outputDataType && !dataTypes.has(transform.outputDataType)) {
            errors.invalidQNameReferences.push({
                type: 'dataTypeQName',
                context: 'transform',
                name: transformName,
                field: 'outputDataType',
                reference: transform.outputDataType
            });
        }
    });
    
    // Validate conceptQName references
    
    // facts.xbrl:concept
    forEachItem(taxonomy.facts, (factName, fact) => {
        if (fact['xbrl:concept'] && !concepts.has(fact['xbrl:concept'])) {
            errors.invalidQNameReferences.push({
                    type: 'conceptQName',
                    context: 'fact',
                    name: factName,
                    field: 'xbrl:concept',
                    reference: fact['xbrl:concept']
                });
            }
        });
    
    // Validate domainQName references
    
    // propertyTypes.enumerationDomain
    forEachItem(taxonomy.propertyTypes, (propTypeName, propType) => {
        if (propType.enumerationDomain && !domains.has(propType.enumerationDomain)) {
            errors.invalidQNameReferences.push({
                type: 'domainQName',
                context: 'propertyType',
                name: propTypeName,
                field: 'enumerationDomain',
                reference: propType.enumerationDomain
            });
        }
    });
    
    // concepts.enumerationDomain
    forEachItem(taxonomy.concepts, (conceptName, concept) => {
        if (concept.enumerationDomain && !domains.has(concept.enumerationDomain)) {
            errors.invalidQNameReferences.push({
                type: 'domainQName',
                context: 'concept',
                name: conceptName,
                field: 'enumerationDomain',
                reference: concept.enumerationDomain
            });
        }
    });
    
    // Validate cubeTypeQName references
    
    // cubes.cubeType
    forEachItem(taxonomy.cubes, (cubeName, cube) => {
        if (cube.cubeType && !cubeTypes.has(cube.cubeType)) {
            errors.invalidQNameReferences.push({
                type: 'cubeTypeQName',
                context: 'cube',
                name: cubeName,
                field: 'cubeType',
                reference: cube.cubeType
            });
        }
    });
    
    // cubeTypes.baseCubeType
    forEachItem(taxonomy.cubeTypes, (cubeTypeName, cubeType) => {
        if (cubeType.baseCubeType && !cubeTypes.has(cubeType.baseCubeType)) {
            errors.invalidQNameReferences.push({
                type: 'cubeTypeQName',
                context: 'cubeType',
                name: cubeTypeName,
                field: 'baseCubeType',
                reference: cubeType.baseCubeType
            });
        }
    });
    
    // Validate modelType reference on xbrlModel
    if (taxonomy.modelType && !modelTypes.has(taxonomy.modelType)) {
        errors.invalidQNameReferences.push({
            type: 'modelTypeQName',
            context: 'xbrlModel',
            name: taxonomy.name || 'unnamed',
            field: 'modelType',
            reference: taxonomy.modelType
        });
    }
    
    // Validate cubeQName references
    
    // dataTables.cubeName
    if (taxonomy.layouts && Array.isArray(taxonomy.layouts)) {
        taxonomy.layouts.forEach((layout, layoutIdx) => {
            if (!layout.dataTables) return;
            layout.dataTables.forEach((dataTable, index) => {
            if (dataTable.cubeName && !cubes.has(dataTable.cubeName)) {
                errors.invalidQNameReferences.push({
                    type: 'cubeQName',
                    context: 'dataTable',
                    name: `dataTable[${index}]`,
                    field: 'cubeName',
                    reference: dataTable.cubeName
                });
            }
            });
        });
    }
    
    // Validate networkQName references
    
    // cubes.cubeNetworks
    forEachItem(taxonomy.cubes, (cubeName, cube) => {
        if (cube.cubeNetworks) {
            cube.cubeNetworks.forEach((networkName, index) => {
                if (!networks.has(networkName)) {
                    errors.invalidQNameReferences.push({
                        type: 'networkQName',
                        context: 'cube',
                        name: cubeName,
                        field: `cubeNetworks[${index}]`,
                        reference: networkName
                    });
                }
            });
        }
    });
    
    // cubes.excludeCubes
    forEachItem(taxonomy.cubes, (cubeName, cube) => {
        if (cube.excludeCubes) {
            cube.excludeCubes.forEach((excludeCubeName, index) => {
                if (!cubes.has(excludeCubeName)) {
                    errors.invalidQNameReferences.push({
                        type: 'cubeQName',
                        context: 'cube',
                        name: cubeName,
                        field: `excludeCubes[${index}]`,
                        reference: excludeCubeName
                    });
                }
            });
        }
    });
    
    // cubes.cubeDimensions[].domainName
    forEachItem(taxonomy.cubes, (cubeName, cube) => {
        if (cube.cubeDimensions) {
            cube.cubeDimensions.forEach((cubeDim, index) => {
                if (cubeDim.domainName && !domains.has(cubeDim.domainName)) {
                    errors.invalidQNameReferences.push({
                        type: 'domainQName',
                        context: 'cube',
                        name: cubeName,
                        field: `cubeDimensions[${index}].domainName`,
                        reference: cubeDim.domainName
                    });
                }
            });
        }
    });
    
    // cubes.cubeDimensions[].periodConstraints[].conceptName in dateResolutionObjects
    forEachItem(taxonomy.cubes, (cubeName, cube) => {
        if (cube.cubeDimensions) {
            cube.cubeDimensions.forEach((cubeDim, dimIndex) => {
                if (cubeDim.periodConstraints && Array.isArray(cubeDim.periodConstraints)) {
                    cubeDim.periodConstraints.forEach((constraint, constraintIndex) => {
                        // Check all dateResolution properties: startDate, endDate, onOrAfter, onOrBefore
                        const dateResolutionProps = ['startDate', 'endDate', 'onOrAfter', 'onOrBefore'];
                        dateResolutionProps.forEach(propName => {
                            const dateResolution = constraint[propName];
                            if (dateResolution && typeof dateResolution === 'object') {
                                // Validate conceptName property
                                if (dateResolution.conceptName) {
                                    if (!concepts.has(dateResolution.conceptName)) {
                                        errors.invalidQNameReferences.push({
                                            type: 'conceptQName',
                                            context: 'cube',
                                            name: cubeName,
                                            field: `cubeDimensions[${dimIndex}].periodConstraints[${constraintIndex}].${propName}.conceptName`,
                                            reference: dateResolution.conceptName
                                        });
                                    }
                                }
                                
                                // Validate context property
                                if (dateResolution.context) {
                                    // Strip @start or @end suffix from context value
                                    let contextQName = dateResolution.context;
                                    if (contextQName.endsWith('@start') || contextQName.endsWith('@end')) {
                                        contextQName = contextQName.substring(0, contextQName.lastIndexOf('@'));
                                    }
                                    
                                    // Check if the QName exists and get its object type
                                    const objectType = getObjectTypeForQName(taxonomy, contextQName);
                                    
                                    if (!objectType) {
                                        // QName not found at all
                                        errors.invalidQNameReferences.push({
                                            type: 'conceptQName',
                                            context: 'cube',
                                            name: cubeName,
                                            field: `cubeDimensions[${dimIndex}].periodConstraints[${constraintIndex}].${propName}.context`,
                                            reference: dateResolution.context
                                        });
                                    } else if (objectType !== 'xbrl:conceptObject') {
                                        // QName exists but is not a concept object
                                        errors.invalidQNameReferences.push({
                                            type: 'conceptQName',
                                            context: 'cube',
                                            name: cubeName,
                                            field: `cubeDimensions[${dimIndex}].periodConstraints[${constraintIndex}].${propName}.context`,
                                            reference: dateResolution.context,
                                            message: `Context property references a ${objectType} instead of a concept object`
                                        });
                                    }
                                }
                            }
                        });
                    });
                }
            });
        }
    });
    
    // Validate relationshipTypeQName references
    
    // networks.relationshipTypeName
    forEachItem(taxonomy.networks, (networkName, network) => {
        if (network.relationshipTypeName && !relationshipTypes.has(network.relationshipTypeName)) {
            errors.invalidQNameReferences.push({
                type: 'relationshipTypeQName',
                context: 'network',
                name: networkName,
                field: 'relationshipTypeName',
                reference: network.relationshipTypeName
            });
        }
    });
    
    // cubeTypes.requiredCubeRelationships
    forEachItem(taxonomy.cubeTypes, (cubeTypeName, cubeType) => {
        if (cubeType.requiredCubeRelationships) {
            cubeType.requiredCubeRelationships.forEach((relSpec, index) => {
                // requiredCubeRelationships items are objects with relationshipTypeName property
                const relTypeName = typeof relSpec === 'string' ? relSpec : relSpec.relationshipTypeName;
                if (relTypeName && !relationshipTypes.has(relTypeName)) {
                    errors.invalidQNameReferences.push({
                        type: 'relationshipTypeQName',
                        context: 'cubeType',
                        name: cubeTypeName,
                        field: `requiredCubeRelationships[${index}].relationshipTypeName`,
                        reference: relTypeName
                    });
                }
            });
        }
    });
    
    // Validate labelTypeQName references
    
    // labels.labelType
    if (taxonomy.labels) {
        taxonomy.labels.forEach((label, index) => {
            if (label.labelType && !labelTypes.has(label.labelType)) {
                errors.invalidQNameReferences.push({
                    type: 'labelTypeQName',
                    context: 'label',
                    name: `label[${index}]`,
                    field: 'labelType',
                    reference: label.labelType
                });
            }
        });
    }
    
    // Validate referenceTypeQName references
    
    // references.referenceType
    if (taxonomy.references) {
        taxonomy.references.forEach((reference, index) => {
            if (reference.referenceType && !referenceTypes.has(reference.referenceType)) {
                errors.invalidQNameReferences.push({
                    type: 'referenceTypeQName',
                    context: 'reference',
                    name: `reference[${index}]`,
                    field: 'referenceType',
                    reference: reference.referenceType
                });
            }
        });
    }
    
    // Validate propertyTypeQName references
    
    // propertyObjects.property
    function validatePropertyReferences(obj, contextType, contextName, path = '') {
        if (!obj || typeof obj !== 'object') return;
        
        Object.entries(obj).forEach(([key, value]) => {
            const currentPath = path ? `${path}.${key}` : key;
            
            if (key === 'property' && typeof value === 'string') {
                if (!propertyTypes.has(value)) {
                    errors.invalidQNameReferences.push({
                        type: 'propertyTypeQName',
                        context: contextType,
                        name: contextName,
                        field: currentPath,
                        reference: value
                    });
                }
            } else if (typeof value === 'object') {
                validatePropertyReferences(value, contextType, contextName, currentPath);
            }
        });
    }
    
    // Check property references in all taxonomy sections
    forEachItem(taxonomy.concepts, (name, concept) => {
        validatePropertyReferences(concept, 'concept', name);
    });
    forEachItem(taxonomy.dimensions, (name, dimension) => {
        validatePropertyReferences(dimension, 'dimension', name);
    });
    forEachItem(taxonomy.cubes, (name, cube) => {
        validatePropertyReferences(cube, 'cube', name);
    });
    
    // Validate groupQName references
    
    // groupContents.groupName
    forEachItem(taxonomy.groupContents, (groupContentName, groupContent) => {
        if (groupContent.groupName && !groups.has(groupContent.groupName)) {
            errors.invalidQNameReferences.push({
                type: 'groupQName',
                context: 'groupContent',
                name: groupContentName,
                field: 'groupName',
                reference: groupContent.groupName
            });
        }
    });
    
    // Validate taxonomyQName references
    // Note: layouts no longer have taxonomyName since it's part of xbrlModel now
    
    // Validate unitQName references
    
    // facts.xbrl:unit
    forEachItem(taxonomy.facts, (factName, fact) => {
        if (fact['xbrl:unit'] && !units.has(fact['xbrl:unit'])) {
            errors.invalidQNameReferences.push({
                type: 'unitQName',
                context: 'fact',
                name: factName,
                field: 'xbrl:unit',
                reference: fact['xbrl:unit']
            });
        }
    });
    
    // dataTypes.unitType (object with dataTypeNumerator, dataTypeDenominator, dataTypeMultiplier)
    forEachItem(taxonomy.dataTypes, (dataTypeName, dataType) => {
        if (dataType.unitType && typeof dataType.unitType === 'object') {
            // Validate dataTypeNumerator
            if (dataType.unitType.dataTypeNumerator && !dataTypes.has(dataType.unitType.dataTypeNumerator)) {
                errors.invalidQNameReferences.push({
                    type: 'dataTypeQName',
                    context: 'dataType',
                    name: dataTypeName,
                    field: 'unitType.dataTypeNumerator',
                    reference: dataType.unitType.dataTypeNumerator
                });
            }
            // Validate dataTypeDenominator
            if (dataType.unitType.dataTypeDenominator && !dataTypes.has(dataType.unitType.dataTypeDenominator)) {
                errors.invalidQNameReferences.push({
                    type: 'dataTypeQName',
                    context: 'dataType',
                    name: dataTypeName,
                    field: 'unitType.dataTypeDenominator',
                    reference: dataType.unitType.dataTypeDenominator
                });
            }
            // Validate dataTypeMultiplier
            if (dataType.unitType.dataTypeMultiplier && !dataTypes.has(dataType.unitType.dataTypeMultiplier)) {
                errors.invalidQNameReferences.push({
                    type: 'dataTypeQName',
                    context: 'dataType',
                    name: dataTypeName,
                    field: 'unitType.dataTypeMultiplier',
                    reference: dataType.unitType.dataTypeMultiplier
                });
            }
        }
    });
}
