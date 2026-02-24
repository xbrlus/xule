/**
 * FactSources Module
 * Handles loading and displaying factSources that use factMaps to convert external data
 */

import { loadXBRLInstance } from './xbrl-parser.js';
import { showDetails } from './details-panel.js';
import { showFactGrids } from './fact-grid.js';
import { getTaxonomyData } from './main.js';
import { processCSVFactMap, processCSVFactMapStreaming, loadCSVFile } from './csv-factMap-processor.js';

/**
 * Check if a URL is absolute (starts with http:// or https://)
 * @param {string} url - The URL to check
 * @returns {boolean} True if URL is absolute
 */
function isAbsoluteURL(url) {
    return url.startsWith('http://') || url.startsWith('https://');
}

/**
 * Process all factSources in the taxonomy
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Promise<void>}
 */
export async function processFactSources(taxonomy) {
    console.log('[FactSources] Processing factSources');
    
    // Initialize global validation errors array (separate from model)
    if (!window.factSourceValidationErrors) {
        window.factSourceValidationErrors = [];
    }
    
    const xbrlModel = taxonomy.xbrlModel || taxonomy;
    if (!xbrlModel.factSources || xbrlModel.factSources.length === 0) {
        console.log('[FactSources] No factSources defined in taxonomy');
        return;
    }
    
    // Process each factSource
    for (const factSource of xbrlModel.factSources) {
        try {
            await processFactSource(factSource, taxonomy);
        } catch (error) {
            console.error('[FactSources] Error processing factSource:', factSource.name, error);
        }
    }
}

/**
 * Process a single factSource
 * @param {Object} factSource - The factSource object
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Promise<void>}
 */
async function processFactSource(factSource, taxonomy) {
    console.log('[FactSources] Processing factSource:', factSource.name);
    
    // Get the factMap name
    const factMapName = factSource.factMapName;
    if (!factMapName) {
        console.warn('[FactSources] No factMapName specified for factSource:', factSource.name);
        return;
    }
    
    // Check if this is the XBRL21XML built-in map
    if (factMapName === 'xbrl:XBRL21XML') {
        await processXBRLFactSource(factSource, taxonomy);
    } else {
        // Check if it's a custom factMap with tableTemplate
        await processCustomFactMapFactSource(factSource, factMapName, taxonomy);
    }
}

/**
 * Process a factSource using XBRL-XML fact map
 * @param {Object} factSource - The factSource object
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Promise<void>}
 */
async function processXBRLFactSource(factSource, taxonomy) {
    console.log('[FactSources] Processing XBRL-XML factSource:', factSource.name);
    
    // Get the URL from sourceMapping in documentInfo
    const documentInfo = taxonomy.documentInfo;
    if (!documentInfo || !documentInfo.sourceMapping) {
        console.warn('[FactSources] No sourceMapping found in documentInfo');
        return;
    }
    
    const urls = documentInfo.sourceMapping[factSource.name];
    if (!urls || urls.length === 0) {
        console.warn('[FactSources] No URLs found for factSource:', factSource.name);
        return;
    }
    
    // Get base path for resolving relative URLs
    const basePath = documentInfo.basePath || '';
    
    // Load and parse each XBRL instance
    for (const url of urls) {
        try {
            // Resolve relative URL (only prepend basePath if not already absolute)
            const fullUrl = isAbsoluteURL(url) ? url : basePath + url;
            
            const result = await loadXBRLInstance(fullUrl, taxonomy);
            const { facts, footnotes, relationships } = result;
            
            // Store the facts in the factSource
            if (!factSource.facts) {
                factSource.facts = [];
            }
            factSource.facts.push(...facts);
            
            // Populate factNames with the SQNames of all materialized facts
            if (!factSource.factNames) {
                factSource.factNames = [];
            }
            factSource.factNames.push(...facts.map(f => f.name));
            
            // Also add facts to the main taxonomy so they appear in cube fact views
            const xbrlModel = taxonomy.xbrlModel || taxonomy;
            if (!xbrlModel.facts) {
                xbrlModel.facts = [];
            }
            xbrlModel.facts.push(...facts);
            
            // Add footnotes if any
            if (footnotes && footnotes.length > 0) {
                if (!xbrlModel.footnotes) {
                    xbrlModel.footnotes = [];
                }
                xbrlModel.footnotes.push(...footnotes);
                console.log('[FactSources] Added', footnotes.length, 'footnotes');
            }
            
            // Add fact-footnote relationships to the xbrl:fact-footnote network
            if (relationships && relationships.length > 0) {
                // Find or create the xbrl:fact-footnote network
                if (!xbrlModel.networks) {
                    xbrlModel.networks = [];
                }
                
                let factFootnoteNetwork = xbrlModel.networks.find(n => n.name === 'xbrl:fact-footnote-network');
                if (!factFootnoteNetwork) {
                    factFootnoteNetwork = {
                        name: 'xbrl:fact-footnote-network',
                        relationshipTypeName: 'xbrl:fact-footnote',
                        relationships: [],
                        roots: []
                    };
                    xbrlModel.networks.push(factFootnoteNetwork);
                }
                
                // Add the relationships
                if (!factFootnoteNetwork.relationships) {
                    factFootnoteNetwork.relationships = [];
                }
                factFootnoteNetwork.relationships.push(...relationships);
                
                // Update roots: all sources that are not targets of any relationship
                const sources = new Set(factFootnoteNetwork.relationships.map(r => r.source));
                const targets = new Set(factFootnoteNetwork.relationships.map(r => r.target));
                const roots = Array.from(sources).filter(s => !targets.has(s));
                factFootnoteNetwork.roots = roots;
                
                console.log('[FactSources] Added', relationships.length, 'fact-footnote relationships');
                console.log('[FactSources] Network roots:', roots);
                
                // Refresh the Networks tab if it exists
                if (window.initNetworks) {
                    console.log('[FactSources] Refreshing Networks tab');
                    window.initNetworks();
                }
            }
            
            console.log('[FactSources] Loaded', facts.length, 'facts from', url);
        } catch (error) {
            console.error('[FactSources] Error loading XBRL instance:', url, error);
        }
    }
}

/**
 * Process a factSource using a custom factMap with tableTemplate
 * @param {Object} factSource - The factSource object
 * @param {string} factMapName - The name of the factMap to use
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Promise<void>}
 */
async function processCustomFactMapFactSource(factSource, factMapName, taxonomy) {
    console.log('[FactSources] Processing custom factMap factSource:', factSource.name, 'with factMap:', factMapName);
    
    const xbrlModel = taxonomy.xbrlModel || taxonomy;
    
    // Find the factMap in the taxonomy
    const factMap = xbrlModel.factMaps?.find(fm => fm.name === factMapName);
    if (!factMap) {
        console.warn('[FactSources] FactMap not found:', factMapName);
        return;
    }
    
    // Check if factMap has a templateName reference
    if (!factMap.templateName) {
        console.warn('[FactSources] FactMap has no templateName:', factMapName);
        return;
    }
    
    // Get the URL from sourceMapping in documentInfo
    const documentInfo = taxonomy.documentInfo;
    if (!documentInfo || !documentInfo.sourceMapping) {
        console.warn('[FactSources] No sourceMapping found in documentInfo');
        return;
    }
    
    const urls = documentInfo.sourceMapping[factSource.name];
    if (!urls || urls.length === 0) {
        console.warn('[FactSources] No URLs found for factSource:', factSource.name);
        return;
    }
    
    // Get base path for resolving relative URLs
    const basePath = documentInfo.basePath || '';
    
    // Extract namespace from factMap name
    const namespaceParts = factMapName.split(':');
    const baseNamespace = namespaceParts.length > 1 ? namespaceParts[0] : 'exp';
    
    // Load and process each CSV file
    for (const url of urls) {
        try {
            // Resolve relative URL (only prepend basePath if not already absolute)
            const fullUrl = isAbsoluteURL(url) ? url : basePath + url;
            
            // Determine file type from extension
            if (url.toLowerCase().endsWith('.csv')) {
                const csvText = await loadCSVFile(fullUrl);
                
                // Use streaming processor with default threshold of 10,000
                const result = await processCSVFactMapStreaming(factMap, csvText, baseNamespace, factSource, xbrlModel);
                
                if (result.mode === 'materialized') {
                    // Small dataset: store materialized facts
                    const facts = result.facts;
                    
                    // Store the facts in the factSource
                    if (!factSource.facts) {
                        factSource.facts = [];
                    }
                    factSource.facts.push(...facts);
                    
                    // Populate factNames with the SQNames of all materialized facts
                    if (!factSource.factNames) {
                        factSource.factNames = [];
                    }
                    factSource.factNames.push(...facts.map(f => f.name));
                    
                    // Also add facts to the main taxonomy so they appear in cube fact views
                    if (!xbrlModel.facts) {
                        xbrlModel.facts = [];
                    }
                    xbrlModel.facts.push(...facts);
                    
                    // Store validation errors globally (not in model)
                    if (result.validationErrors && result.validationErrors.length > 0) {
                        console.warn(`[FactSources] ${result.validationErrors.length} validation errors found in`, url);
                        result.validationErrors.forEach(error => {
                            window.factSourceValidationErrors.push({
                                ...error,
                                factSourceName: factSource.name,
                                factSourceFactMapName: factSource.factMapName
                            });
                        });
                    }
                    
                    console.log('[FactSources] Loaded', facts.length, 'facts from', url, '(materialized)');
                } else {
                    // Large dataset: store hash and metadata only
                    factSource.hash = result.hash;
                    factSource.metadata = result.metadata;
                    
                    // Store validation errors globally (not in model)
                    if (result.validationErrors && result.validationErrors.length > 0) {
                        console.warn(`[FactSources] ${result.validationErrors.length} validation errors found in`, url);
                        result.validationErrors.forEach(error => {
                            window.factSourceValidationErrors.push({
                                ...error,
                                factSourceName: factSource.name,
                                factSourceFactMapName: factSource.factMapName
                            });
                        });
                    }
                    
                    console.log(`[FactSources] Loaded ${result.metadata.factCount} facts from ${url} (hash-based)`);
                    console.log(`[FactSources] Hash: ${result.hash.substring(0, 16)}...`);
                    console.log(`[FactSources] Concepts: ${result.metadata.concepts.length}, Dimensions: ${result.metadata.dimensions.length}`);
                }
            } else {
                console.warn('[FactSources] Unsupported file type:', url);
            }
        } catch (error) {
            console.error('[FactSources] Error loading CSV file:', url, error);
        }
    }
}

/**
 * Build the factSources list for the Fact Sets tab
 * @param {Object} taxonomy - The loaded taxonomy object
 * @param {HTMLElement} container - The container element for the factSources list
 */
export function buildFactSourcesList(taxonomy, container) {
    console.log('[FactSources] buildFactSourcesList called');
    
    const xbrlModel = taxonomy.xbrlModel || taxonomy;
    if (!xbrlModel.factSources || xbrlModel.factSources.length === 0) {
        container.innerHTML = '<div class="no-data">No factSources defined in this taxonomy.</div>';
        return;
    }
    
    console.log('[FactSources] Building list with', xbrlModel.factSources.length, 'factSources');
    
    const list = document.createElement('ul');
    list.className = 'factSources-list';
    
    xbrlModel.factSources.forEach((factSource, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'factSource-item';
        
        // Create expandable header for factSource
        const header = document.createElement('div');
        header.className = 'factSource-header';
        header.style.cssText = 'cursor: pointer; padding: 5px; background: #f0f0f0; border-bottom: 1px solid #ccc;';
        
        const expandIcon = document.createElement('span');
        expandIcon.className = 'expand-icon';
        expandIcon.textContent = '▶ ';
        expandIcon.style.cssText = 'display: inline-block; width: 20px;';
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'factSource-name';
        
        // Display different info based on materialized vs hash-based mode
        let factInfo;
        if (factSource.hash && factSource.metadata) {
            // Hash-based mode: show metadata summary
            const factCount = factSource.metadata.factCount;
            factInfo = `${factCount.toLocaleString()} facts (hash-based)`;
        } else {
            // Materialized mode: show direct fact count
            const factCount = factSource.facts ? factSource.facts.length : 0;
            factInfo = `${factCount} facts`;
        }
        
        const propertiesInfo = factSource.properties && factSource.properties.length > 0 
            ? ` [${factSource.properties.length} properties]` 
            : '';
        nameSpan.textContent = `📦 ${factSource.name} (${factInfo})${propertiesInfo}`;
        nameSpan.style.fontWeight = 'bold';
        
        header.appendChild(expandIcon);
        header.appendChild(nameSpan);
        
        // Create container for factSource metadata and facts
        const factSourceContent = document.createElement('div');
        factSourceContent.className = 'factSource-content';
        factSourceContent.style.display = 'none';
        factSourceContent.style.paddingLeft = '20px';
        
        // Add properties section if present
        if (factSource.properties && factSource.properties.length > 0) {
            const propertiesSection = document.createElement('div');
            propertiesSection.className = 'factSource-properties';
            propertiesSection.style.cssText = 'margin: 10px 0; padding: 10px; background: #f9f9f9; border-left: 3px solid #4CAF50;';
            
            const propertiesTitle = document.createElement('div');
            propertiesTitle.textContent = 'Properties:';
            propertiesTitle.style.cssText = 'font-weight: bold; margin-bottom: 5px;';
            propertiesSection.appendChild(propertiesTitle);
            
            const propertiesList = document.createElement('ul');
            propertiesList.style.cssText = 'margin: 5px 0; padding-left: 20px;';
            
            factSource.properties.forEach(prop => {
                const propItem = document.createElement('li');
                propItem.style.cssText = 'margin: 3px 0;';
                propItem.innerHTML = `<strong>${prop.property}:</strong> ${JSON.stringify(prop.value)}`;
                propertiesList.appendChild(propItem);
            });
            
            propertiesSection.appendChild(propertiesList);
            factSourceContent.appendChild(propertiesSection);
        }
        
        // Add validation errors section if present (read from global, not from factSource)
        const factSourceErrors = (window.factSourceValidationErrors || []).filter(err => err.factSourceName === factSource.name);
        if (factSourceErrors.length > 0) {
            const errorsSection = document.createElement('div');
            errorsSection.className = 'factSource-validation-errors';
            errorsSection.style.cssText = 'margin: 10px 0; padding: 10px; background: #fff5f5; border-left: 3px solid #ff6b6b;';
            
            const errorsTitle = document.createElement('div');
            errorsTitle.textContent = `⚠️ Validation Errors (${factSourceErrors.length}):`;
            errorsTitle.style.cssText = 'font-weight: bold; margin-bottom: 5px; color: #c92a2a;';
            errorsSection.appendChild(errorsTitle);
            
            const errorsList = document.createElement('ul');
            errorsList.style.cssText = 'margin: 5px 0; padding-left: 20px; max-height: 300px; overflow-y: auto;';
            
            // Show first 10 errors
            const errorsToShow = factSourceErrors.slice(0, 10);
            errorsToShow.forEach(error => {
                const errorItem = document.createElement('li');
                errorItem.style.cssText = 'margin: 3px 0; font-size: 13px; color: #c92a2a;';
                const factIndex = error.factIndex !== undefined ? `[Fact ${error.factIndex}] ` : '';
                errorItem.textContent = `${factIndex}${error.type}: ${error.message}`;
                errorsList.appendChild(errorItem);
            });
            
            if (factSourceErrors.length > 10) {
                const moreItem = document.createElement('li');
                moreItem.style.cssText = 'margin: 5px 0; font-style: italic; color: #868e96;';
                moreItem.textContent = `... and ${factSourceErrors.length - 10} more errors`;
                errorsList.appendChild(moreItem);
            }
            
            errorsSection.appendChild(errorsList);
            factSourceContent.appendChild(errorsSection);
        }
        
        // Create container for facts or metadata
        const factsContainer = document.createElement('div');
        factsContainer.className = 'facts-container';
        
        // Display hash-based metadata if present
        if (factSource.hash && factSource.metadata) {
            const metadataSection = document.createElement('div');
            metadataSection.className = 'factSource-metadata';
            metadataSection.style.cssText = 'margin: 10px 0; padding: 10px; background: #f0f8ff; border-left: 3px solid #228be6;';
            
            const metadataTitle = document.createElement('div');
            metadataTitle.textContent = '📊 Hash-Based FactSource Metadata:';
            metadataTitle.style.cssText = 'font-weight: bold; margin-bottom: 10px; color: #228be6;';
            metadataSection.appendChild(metadataTitle);
            
            const metadataList = document.createElement('dl');
            metadataList.style.cssText = 'margin: 0; font-size: 13px;';
            
            // Hash
            const hashDt = document.createElement('dt');
            hashDt.textContent = 'Hash:';
            hashDt.style.cssText = 'font-weight: bold; margin-top: 5px;';
            const hashDd = document.createElement('dd');
            hashDd.textContent = factSource.hash.substring(0, 32) + '...';
            hashDd.style.cssText = 'margin-left: 20px; font-family: monospace; color: #666;';
            metadataList.appendChild(hashDt);
            metadataList.appendChild(hashDd);
            
            // Fact Count
            const countDt = document.createElement('dt');
            countDt.textContent = 'Fact Count:';
            countDt.style.cssText = 'font-weight: bold; margin-top: 5px;';
            const countDd = document.createElement('dd');
            countDd.textContent = factSource.metadata.factCount.toLocaleString();
            countDd.style.cssText = 'margin-left: 20px;';
            metadataList.appendChild(countDt);
            metadataList.appendChild(countDd);
            
            // Concepts
            const conceptsDt = document.createElement('dt');
            conceptsDt.textContent = 'Concepts:';
            conceptsDt.style.cssText = 'font-weight: bold; margin-top: 5px;';
            const conceptsDd = document.createElement('dd');
            conceptsDd.textContent = `${factSource.metadata.concepts.length} unique (${factSource.metadata.concepts.slice(0, 3).join(', ')}${factSource.metadata.concepts.length > 3 ? '...' : ''})`;
            conceptsDd.style.cssText = 'margin-left: 20px;';
            metadataList.appendChild(conceptsDt);
            metadataList.appendChild(conceptsDd);
            
            // Dimensions
            const dimsDt = document.createElement('dt');
            dimsDt.textContent = 'Dimensions:';
            dimsDt.style.cssText = 'font-weight: bold; margin-top: 5px;';
            const dimsDd = document.createElement('dd');
            const dimInfo = factSource.metadata.dimensions.map(d => `${d.dimensionName} (${d.memberCount} members)`).join(', ');
            dimsDd.textContent = dimInfo;
            dimsDd.style.cssText = 'margin-left: 20px;';
            metadataList.appendChild(dimsDt);
            metadataList.appendChild(dimsDd);
            
            // Validation timestamp
            if (factSource.metadata.validationTimestamp) {
                const timestampDt = document.createElement('dt');
                timestampDt.textContent = 'Validated:';
                timestampDt.style.cssText = 'font-weight: bold; margin-top: 5px;';
                const timestampDd = document.createElement('dd');
                timestampDd.textContent = new Date(factSource.metadata.validationTimestamp).toLocaleString();
                timestampDd.style.cssText = 'margin-left: 20px; color: #666;';
                metadataList.appendChild(timestampDt);
                metadataList.appendChild(timestampDd);
            }
            
            metadataSection.appendChild(metadataList);
            
            // Info note
            const infoNote = document.createElement('div');
            infoNote.style.cssText = 'margin-top: 10px; padding: 8px; background: #fff3cd; border-left: 3px solid #ffc107; font-size: 12px;';
            infoNote.textContent = '💡 Facts are not materialized to save memory. Metadata enables efficient querying and cube relevance checking.';
            metadataSection.appendChild(infoNote);
            
            factsContainer.appendChild(metadataSection);
        } else if (factSource.facts && factSource.facts.length > 0) {
            // Materialized facts: show as before
            const factsList = document.createElement('ul');
            factsList.className = 'facts-list';
            
            factSource.facts.forEach((fact, fpIndex) => {
                const fpItem = document.createElement('li');
                fpItem.className = 'fact-item';
                
                const fpNameSpan = document.createElement('span');
                fpNameSpan.className = 'fact-name';
                fpNameSpan.textContent = `💠 ${fact.name}`;
                fpNameSpan.style.cursor = 'pointer';
                
                fpNameSpan.addEventListener('click', () => {
                    // Remove previous selection
                    container.querySelectorAll('.selected').forEach(el => {
                        el.classList.remove('selected');
                    });
                    fpItem.classList.add('selected');
                    
                    // Show fact details
                    showDetails(fact, 'fact');
                    
                    // Show grid view with highlighted cells
                    showFactGrids(fact, taxonomy);
                });
                
                fpItem.appendChild(fpNameSpan);
                factsList.appendChild(fpItem);
            });
            
            factsContainer.appendChild(factsList);
        } else {
            factsContainer.innerHTML = '<div class="no-data">No facts loaded</div>';
        }
        
        factSourceContent.appendChild(factsContainer);
        
        // Toggle expand/collapse
        header.addEventListener('click', () => {
            const isExpanded = factSourceContent.style.display !== 'none';
            factSourceContent.style.display = isExpanded ? 'none' : 'block';
            expandIcon.textContent = isExpanded ? '▶ ' : '▼ ';
        });
        
        listItem.appendChild(header);
        listItem.appendChild(factSourceContent);
        list.appendChild(listItem);
    });
    
    container.innerHTML = '';
    container.appendChild(list);
}
