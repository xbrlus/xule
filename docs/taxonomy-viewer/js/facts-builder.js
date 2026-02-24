/**
 * Module for building and managing the Facts tab
 */

console.log('[Facts Module] Loading facts-builder.js');

import { showDetails } from './details-panel.js';
import { showFactGrids } from './fact-grid.js';
import { resolveFactValue } from './valueSource-resolver.js';

console.log('[Facts Module] showDetails imported:', typeof showDetails);
console.log('[Facts Module] showFactGrids imported:', typeof showFactGrids);
console.log('[Facts Module] resolveFactValue imported:', typeof resolveFactValue);

/**
 * Build the facts list for the Facts tab
 * @param {Object} taxonomy - The loaded taxonomy object
 * @param {HTMLElement} container - The container element for the facts list
 */
export function buildFactsList(taxonomy, container) {
    console.log('[Facts] buildFactsList called with:', { taxonomy, container });
    console.log('[Facts] taxonomy.facts:', taxonomy?.facts);
    
    if (!taxonomy || !taxonomy.facts || taxonomy.facts.length === 0) {
        const message = !taxonomy ? 'No taxonomy data' : 
                       !taxonomy.facts ? 'No facts array' : 
                       'No facts defined in this taxonomy.';
        console.log('[Facts]', message);
        container.innerHTML = `<div class="no-data">${message}</div>`;
        return;
    }

    console.log('[Facts] Building list with', taxonomy.facts.length, 'facts');
    const list = document.createElement('ul');
    list.className = 'facts-list';

    taxonomy.facts.forEach((fact, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'fact-item';
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'fact-name';
        // Add fact icon before the name
        const displayName = fact.name || `Fact ${index + 1}`;
        nameSpan.textContent = `💠 ${displayName}`;
        nameSpan.style.cursor = 'pointer';
        nameSpan.addEventListener('click', () => {
            // Remove previous selection
            container.querySelectorAll('.selected').forEach(el => {
                el.classList.remove('selected');
            });
            listItem.classList.add('selected');
            
            // Show fact details
            showDetails(fact, 'fact');
            
            // Show grid view with highlighted cells
            showFactGrids(fact, taxonomy);
        });

        listItem.appendChild(nameSpan);
        list.appendChild(listItem);
    });

    container.innerHTML = '';
    container.appendChild(list);
}

/**
 * Display fact details in the details panel
 * @param {Object} fact - The fact object
 * @param {Object} taxonomy - The full taxonomy object
 * @returns {string} HTML string for the details panel
 */
export async function formatFactDetails(fact, taxonomy) {
    let html = '<div class="fact-details">';
    
    // Basic info
    html += `<h3>${fact.name}</h3>`;
    
    // Fact Dimensions
    if (fact.factDimensions) {
        html += '<h4>Fact Dimensions</h4>';
        html += '<table class="fact-dimensions-table">';
        html += '<tr><th>Dimension</th><th>Value</th></tr>';
        
        for (const [dimName, dimValue] of Object.entries(fact.factDimensions)) {
            const displayValue = typeof dimValue === 'object' ? JSON.stringify(dimValue) : dimValue;
            html += `<tr><td>${dimName}</td><td>${displayValue}</td></tr>`;
        }
        html += '</table>';
    }
    
    // Fact Values (with value source resolution)
    if (fact.factValues && fact.factValues.length > 0) {
        html += '<h4>Fact Values</h4>';
        html += '<table class="fact-values-table">';
        html += '<tr><th>Name</th><th>Value</th><th>Decimals</th><th>Source</th></tr>';
        
        for (const factValue of fact.factValues) {
            html += '<tr>';
            // Add fact icon before the fact name
            const factName = factValue.name ? `💠 ${factValue.name}` : '';
            html += `<td>${factName}</td>`;
            
            // Resolve value if it has value sources
            let displayValue = factValue.value || '';
            let sourceInfo = '';
            
            if (factValue.valueSources && factValue.valueSources.length > 0) {
                const resolved = await resolveFactValue(factValue);
                
                if (resolved.error) {
                    // Show error
                    displayValue = `<span class="error-text" title="${resolved.message || resolved.error}">⚠️ ${resolved.error}</span>`;
                    sourceInfo = factValue.valueSources[0].id || 'Error';
                } else if (resolved.value !== null) {
                    // Show resolved value
                    displayValue = resolved.value;
                    const vs = factValue.valueSources[0];
                    sourceInfo = vs.id || '';
                    if (vs.transformation) {
                        sourceInfo += ` (${vs.transformation})`;
                    }
                    if (resolved.originalValue && resolved.originalValue !== resolved.value) {
                        displayValue += ` <span class="original-value" title="Original: ${resolved.originalValue}">📄</span>`;
                    }
                }
            }
            
            html += `<td>${displayValue}</td>`;
            html += `<td>${factValue.decimals !== undefined ? factValue.decimals : ''}</td>`;
            html += `<td class="value-source-info">${sourceInfo}</td>`;
            html += '</tr>';
        }
        html += '</table>';
    }
    
    html += '</div>';
    return html;
}
