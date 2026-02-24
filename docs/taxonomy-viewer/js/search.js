/**
 * Search Module
 * Handles QName search with autocomplete functionality
 */

import { getTaxonomyData } from './main.js';
import { showDetails } from './details-panel.js';
import { getNodeType, getXbrlModel } from './utils.js';
import { navigateToObject } from './tab-manager.js';

/**
 * Get all QNames from the taxonomy
 * @returns {Array<{qname: string, type: string, obj: Object}>}
 */
export function getAllQNames() {
    const taxonomyData = getTaxonomyData();
    const tax = getXbrlModel(taxonomyData);
    if (!tax) {
        return [];
    }
    
    const qnames = [];
    
    // Collect the taxonomy itself
    if (tax.name) {
        qnames.push({ qname: tax.name, type: 'taxonomy', obj: { name: tax.name } });
    }
    
    // Collect concepts
    if (tax.concepts) {
        tax.concepts.forEach(concept => {
            qnames.push({ qname: concept.name, type: 'concept', obj: concept });
        });
    }
    
    // Collect dimensions
    if (tax.dimensions) {
        tax.dimensions.forEach(dim => {
            qnames.push({ qname: dim.name, type: 'dimension', obj: dim });
        });
    }
    
    // Collect members
    if (tax.members) {
        tax.members.forEach(member => {
            qnames.push({ qname: member.name, type: 'member', obj: member });
        });
    }
    
    // Collect abstracts
    if (tax.abstracts) {
        tax.abstracts.forEach(abstract => {
            qnames.push({ qname: abstract.name, type: 'abstract', obj: abstract });
        });
    }
    
    // Collect units
    if (tax.units) {
        tax.units.forEach(unit => {
            qnames.push({ qname: unit.name, type: 'unit', obj: unit });
        });
    }
    
    // Collect entities
    if (tax.entities) {
        tax.entities.forEach(entity => {
            qnames.push({ qname: entity.name, type: 'entity', obj: entity });
        });
    }
    
    // Collect domain classs
    if (tax.domainClasses) {
        tax.domainClasses.forEach(root => {
            qnames.push({ qname: root.name, type: 'domainClass', obj: root });
        });
    }
    
    // Collect cubes
    if (tax.cubes) {
        tax.cubes.forEach(cube => {
            qnames.push({ qname: cube.name, type: 'cube', obj: cube });
        });
    }
    
    // Collect groups
    if (tax.groups) {
        tax.groups.forEach(group => {
            qnames.push({ qname: group.name, type: 'group', obj: group });
        });
    }
    
    // Collect networks
    if (tax.networks) {
        tax.networks.forEach(network => {
            qnames.push({ qname: network.name, type: 'network', obj: network });
        });
    }
    
    // Collect domains
    if (tax.domains) {
        tax.domains.forEach(domain => {
            qnames.push({ qname: domain.name, type: 'domain', obj: domain });
        });
    }
    
    // Collect transforms
    if (tax.transforms) {
        tax.transforms.forEach(transform => {
            qnames.push({ qname: transform.name, type: 'transform', obj: transform });
        });
    }
    
    // Collect property types
    if (tax.propertyTypes) {
        tax.propertyTypes.forEach(propType => {
            qnames.push({ qname: propType.name, type: 'propertyType', obj: propType });
        });
    }
    
    // Collect data types
    if (tax.dataTypes) {
        tax.dataTypes.forEach(dataType => {
            qnames.push({ qname: dataType.name, type: 'dataType', obj: dataType });
        });
    }
    
    // Collect cube types
    if (tax.cubeTypes) {
        tax.cubeTypes.forEach(cubeType => {
            qnames.push({ qname: cubeType.name, type: 'cubeType', obj: cubeType });
        });
    }
    
    // Collect label types
    if (tax.labelTypes) {
        tax.labelTypes.forEach(labelType => {
            qnames.push({ qname: labelType.name, type: 'labelType', obj: labelType });
        });
    }
    
    // Collect reference types
    if (tax.referenceTypes) {
        tax.referenceTypes.forEach(refType => {
            qnames.push({ qname: refType.name, type: 'referenceType', obj: refType });
        });
    }
    
    // Collect facts
    if (tax.facts) {
        tax.facts.forEach(fact => {
            qnames.push({ qname: fact.name, type: 'fact', obj: fact });
        });
    }
    
    // Collect factSources
    if (tax.factSources) {
        tax.factSources.forEach(factSource => {
            qnames.push({ qname: factSource.name, type: 'factSource', obj: factSource });
        });
    }
    
    // Collect factMaps
    if (tax.factMaps) {
        tax.factMaps.forEach(factMap => {
            qnames.push({ qname: factMap.name, type: 'factMap', obj: factMap });
        });
    }
    
    // Collect relationship types
    if (tax.relationshipTypes) {
        tax.relationshipTypes.forEach(relType => {
            qnames.push({ qname: relType.name, type: 'relationshipType', obj: relType });
        });
    }
    
    // Collect references (have QName identifiers)
    if (tax.references) {
        tax.references.forEach(reference => {
            if (reference.name) {
                qnames.push({ qname: reference.name, type: 'reference', obj: reference });
            }
        });
    }
    
    // Collect footnotes
    if (tax.footnotes) {
        tax.footnotes.forEach(footnote => {
            if (footnote.name) {
                qnames.push({ qname: footnote.name, type: 'footnote', obj: footnote });
            }
        });
    }
    
    // Sort alphabetically, filtering out any entries with undefined qnames
    qnames.sort((a, b) => {
        if (!a.qname || !b.qname) return 0;
        return a.qname.localeCompare(b.qname);
    });
    
    return qnames.filter(item => item.qname !== undefined && item.qname !== null);
}

/**
 * Filter QNames based on search query
 * @param {string} query - Search query
 * @param {Array} allQNames - All available QNames
 * @param {number} maxResults - Maximum number of results to return
 * @returns {Array} Filtered QNames
 */
export function filterQNames(query, allQNames, maxResults = 50) {
    // Return empty array if no query
    if (!query || query.trim() === '') {
        return [];
    }
    
    const lowerQuery = query.toLowerCase();
    const results = [];
    
    // Exact matches first
    for (const item of allQNames) {
        if (item.qname.toLowerCase() === lowerQuery) {
            results.push({ ...item, matchType: 'exact' });
        }
    }
    
    // Starts with query
    for (const item of allQNames) {
        if (item.qname.toLowerCase().startsWith(lowerQuery) && 
            !results.some(r => r.qname === item.qname)) {
            results.push({ ...item, matchType: 'startsWith' });
        }
    }
    
    // Contains query
    for (const item of allQNames) {
        if (item.qname.toLowerCase().includes(lowerQuery) && 
            !results.some(r => r.qname === item.qname)) {
            results.push({ ...item, matchType: 'contains' });
        }
    }
    
    return results.slice(0, maxResults);
}

/**
 * Show the search panel in the details container
 * @param {boolean} forceRefresh - Force refresh of the search panel data
 */
export function showSearchPanel(forceRefresh = false) {
    console.log('[Search] Showing search panel (forceRefresh:', forceRefresh, ')');
    
    // Hide details tabs
    const detailsTabs = document.getElementById('details-tabs');
    if (detailsTabs) {
        detailsTabs.style.display = 'none';
    }
    
    // Hide existing tab contents
    document.querySelectorAll('.details-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Get existing search panel
    let searchPanel = document.getElementById('search-panel');
    
    // If force refresh, remove the old panel
    if (forceRefresh && searchPanel) {
        console.log('[Search] Removing old search panel for refresh');
        searchPanel.remove();
        searchPanel = null;
    }
    
    // Create or show search panel
    if (!searchPanel) {
        searchPanel = createSearchPanel();
        const detailsContainer = document.getElementById('details-container');
        if (detailsContainer) {
            detailsContainer.insertBefore(searchPanel, detailsContainer.firstChild);
        }
    }
    
    searchPanel.classList.add('active');
    searchPanel.style.display = 'block';
    
    // Focus on search input
    const searchInput = document.getElementById('qname-search-input');
    if (searchInput) {
        searchInput.focus();
    }
}

/**
 * Hide the search panel
 */
export function hideSearchPanel() {
    const searchPanel = document.getElementById('search-panel');
    if (searchPanel) {
        searchPanel.classList.remove('active');
        searchPanel.style.display = 'none';
    }
}

/**
 * Create the search panel UI
 * @returns {HTMLElement} The search panel element
 */
function createSearchPanel() {
    const panel = document.createElement('div');
    panel.id = 'search-panel';
    panel.className = 'search-panel';
    
    // Create search header
    const header = document.createElement('div');
    header.className = 'search-header';
    
    const title = document.createElement('h2');
    title.textContent = 'Search QNames';
    title.style.margin = '0';
    title.style.fontSize = '18px';
    title.style.color = '#2c3e50';
    header.appendChild(title);
    
    panel.appendChild(header);
    
    // Create search input container
    const inputContainer = document.createElement('div');
    inputContainer.className = 'search-input-container';
    
    const input = document.createElement('input');
    input.id = 'qname-search-input';
    input.type = 'text';
    input.placeholder = 'Type to search for QName...';
    input.className = 'search-input';
    
    inputContainer.appendChild(input);
    panel.appendChild(inputContainer);
    
    // Create results container
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'search-results';
    resultsContainer.className = 'search-results';
    
    panel.appendChild(resultsContainer);
    
    // Add input listener for autocomplete
    let debounceTimer;
    input.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const query = this.value;
            // Get fresh QNames each time to ensure we have latest taxonomy data
            const allQNames = getAllQNames();
            const filteredResults = filterQNames(query, allQNames);
            displaySearchResults(filteredResults, resultsContainer, query);
        }, 200);
    });
    
    // Show initial empty state with instructions
    displaySearchResults([], resultsContainer, '');
    
    return panel;
}

/**
 * Display search results
 * @param {Array} results - Filtered QName results
 * @param {HTMLElement} container - Results container element
 * @param {string} query - The current search query
 */
export function displaySearchResults(results, container, query = '') {
    container.innerHTML = '';
    
    if (results.length === 0) {
        const noResults = document.createElement('div');
        noResults.style.padding = '20px';
        noResults.style.textAlign = 'center';
        noResults.style.color = '#888';
        noResults.style.fontStyle = 'italic';
        
        if (!query || query.trim() === '') {
            // Empty state - show instructions
            noResults.innerHTML = '<p style="font-size: 14px; line-height: 1.6; margin: 20px;">Type in the search box above to find QNames in the taxonomy.</p><p style="font-size: 12px; color: #999;">Search across concepts, dimensions, members, cubes, networks, references, and more...</p>';
        } else {
            // No matches found
            noResults.textContent = 'No matching QNames found.';
        }
        
        container.appendChild(noResults);
        return;
    }
    
    // Create results list
    const resultsList = document.createElement('ul');
    resultsList.style.listStyle = 'none';
    resultsList.style.padding = '0';
    resultsList.style.margin = '0';
    
    results.forEach(result => {
        const li = document.createElement('li');
        li.className = 'search-result-item';
        li.style.padding = '10px';
        li.style.borderBottom = '1px solid #eee';
        li.style.cursor = 'pointer';
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.style.transition = 'background-color 0.2s';
        
        // Type badge
        const typeBadge = document.createElement('span');
        typeBadge.className = 'type-badge';
        typeBadge.textContent = result.type;
        typeBadge.style.display = 'inline-block';
        typeBadge.style.padding = '3px 8px';
        typeBadge.style.fontSize = '11px';
        typeBadge.style.fontWeight = 'bold';
        typeBadge.style.borderRadius = '3px';
        typeBadge.style.marginRight = '10px';
        typeBadge.style.textTransform = 'uppercase';
        typeBadge.style.minWidth = '80px';
        typeBadge.style.textAlign = 'center';
        
        // Color code by type
        const typeColors = {
            'concept': '#e3f2fd',
            'dimension': '#fff3e0',
            'member': '#f3e5f5',
            'abstract': '#e8f5e9',
            'unit': '#fce4ec',
            'entity': '#e0f2f1',
            'domainClass': '#fff9c4',
            'cube': '#ede7f6',
            'group': '#fbe9e7',
            'network': '#e0f7fa',
            'domain': '#f1f8e9',
            'transform': '#ffebee',
            'propertyType': '#e1f5fe',
            'dataType': '#f3e5f5',
            'cubeType': '#fce4ec',
            'labelType': '#fff3e0',
            'referenceType': '#e8eaf6',
            'fact': '#e0f2f1',
            'factSource': '#ffe0b2',
            'factMap': '#ffccbc',
            'relationshipType': '#ede7f6',
            'reference': '#e1bee7',
            'footnote': '#ffe0b2'
        };
        
        typeBadge.style.backgroundColor = typeColors[result.type] || '#f5f5f5';
        typeBadge.style.color = '#333';
        
        li.appendChild(typeBadge);
        
        // QName text
        const qnameText = document.createElement('span');
        qnameText.textContent = result.qname;
        qnameText.style.flex = '1';
        qnameText.style.fontSize = '13px';
        qnameText.style.fontFamily = 'monospace';
        li.appendChild(qnameText);
        
        // Hover effect
        li.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f5f5f5';
        });
        
        li.addEventListener('mouseleave', function() {
            if (!this.classList.contains('selected')) {
                this.style.backgroundColor = 'transparent';
            }
        });
        
        // Click to show details
        li.addEventListener('click', function() {
            console.log('[Search] Selected:', result.qname, 'Type:', result.type);
            showDetails(result.obj, result.type);
            
            // Navigate to the appropriate tab and highlight the item
            navigateToObject(result.type, result.qname);
            
            // Highlight selected item in search results
            document.querySelectorAll('.search-result-item').forEach(item => {
                item.classList.remove('selected');
                item.style.backgroundColor = 'transparent';
                item.style.fontWeight = 'normal';
            });
            this.classList.add('selected');
            this.style.backgroundColor = '#e3f2fd';
            this.style.fontWeight = 'bold';
        });
        
        resultsList.appendChild(li);
    });
    
    container.appendChild(resultsList);
}

/**
 * Refresh search data without recreating UI
 * Called after factSources are processed to include generated facts
 */
export function refreshSearchData() {
    // If there's an active search, re-run it to show updated results
    const searchInput = document.getElementById('qname-search-input');
    const resultsContainer = document.getElementById('search-results');
    
    if (searchInput && resultsContainer) {
        const currentQuery = searchInput.value;
        if (currentQuery && currentQuery.trim() !== '') {
            const allQNames = getAllQNames();
            const filteredResults = filterQNames(currentQuery, allQNames);
            displaySearchResults(filteredResults, resultsContainer, currentQuery);
        }
    }
}

/**
 * Initialize search when taxonomy is loaded
 * Forces a refresh to clear old taxonomy data
 */
export function initSearch() {
    console.log('[Search] Initializing search with fresh taxonomy data');
    showSearchPanel(true); // Force refresh to reload QNames from new taxonomy
}
