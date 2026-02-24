/**
 * Model Semantic Difference Tool
 * 
 * This module provides functionality to compare two XBRL models and identify
 * semantic differences between them.
 */

import { createCanonicalForm, generateModelHash } from './canonical-model.js';

/**
 * Object arrays that contain named objects
 */
const OBJECT_ARRAYS = [
    'abstracts', 'concepts', 'cubes', 'cubeTypes', 'dataTypes', 'dimensions',
    'domains', 'domainClasses', 'entities', 'facts', 'footnotes', 'factMaps',
    'groups', 'groupContents', 'labels', 'members', 'modelTypes', 'networks',
    'propertyTypes', 'references', 'referenceTypes', 'relationshipTypes',
    'units', 'transforms', 'layouts'
];

/**
 * Compare two models and generate a detailed semantic difference report
 * @param {Object} model1 - First model
 * @param {Object} model2 - Second model
 * @returns {Promise<Object>} Difference report
 */
export async function compareModels(model1, model2) {
    try {
        // Generate canonical forms
        const canonical1 = createCanonicalForm(model1);
        const canonical2 = createCanonicalForm(model2);
        
        // Generate hashes
        const hash1 = await generateModelHash(model1);
        const hash2 = await generateModelHash(model2);
        
        const identical = hash1 === hash2;
        
        // If identical, return early
        if (identical) {
            return {
                identical: true,
                hash1,
                hash2,
                summary: 'Models are semantically equivalent',
                differences: {}
            };
        }
        
        // Compute detailed differences
        const differences = computeDifferences(canonical1.xbrlModel, canonical2.xbrlModel);
        
        return {
            identical: false,
            hash1,
            hash2,
            summary: generateSummary(differences),
            differences
        };
        
    } catch (error) {
        return {
            identical: false,
            error: error.message,
            summary: 'Error comparing models: ' + error.message
        };
    }
}

/**
 * Compute differences between two xbrlModel objects
 */
function computeDifferences(model1, model2) {
    const differences = {};
    
    // Compare each object array
    for (const arrayName of OBJECT_ARRAYS) {
        const array1 = model1[arrayName] || [];
        const array2 = model2[arrayName] || [];
        
        const diff = compareObjectArrays(array1, array2, arrayName);
        
        if (diff.added.length > 0 || diff.removed.length > 0 || diff.modified.length > 0) {
            differences[arrayName] = diff;
        }
    }
    
    // Compare simple properties
    const propDiff = compareProperties(model1, model2);
    if (Object.keys(propDiff).length > 0) {
        differences.properties = propDiff;
    }
    
    return differences;
}

/**
 * Compare two arrays of objects
 */
function compareObjectArrays(array1, array2, arrayName) {
    const diff = {
        added: [],
        removed: [],
        modified: []
    };
    
    // Create maps by name/identifier
    const map1 = createObjectMap(array1, arrayName);
    const map2 = createObjectMap(array2, arrayName);
    
    // Find added objects (in model2 but not in model1)
    for (const [key, obj] of map2) {
        if (!map1.has(key)) {
            diff.added.push(key);
        }
    }
    
    // Find removed objects (in model1 but not in model2)
    for (const [key, obj] of map1) {
        if (!map2.has(key)) {
            diff.removed.push(key);
        }
    }
    
    // Find modified objects (in both but different)
    for (const [key, obj1] of map1) {
        if (map2.has(key)) {
            const obj2 = map2.get(key);
            const objDiff = compareObjects(obj1, obj2);
            
            if (objDiff.length > 0) {
                diff.modified.push({
                    name: key,
                    changes: objDiff
                });
            }
        }
    }
    
    return diff;
}

/**
 * Create a map of objects by their key (name or identifier)
 */
function createObjectMap(array, arrayName) {
    const map = new Map();
    
    for (const obj of array) {
        let key;
        
        if (arrayName === 'labels') {
            key = `${obj.relatedName}|${obj.labelType}|${obj.language}`;
        } else if (arrayName === 'references') {
            key = obj.name;
        } else if (arrayName === 'relationships') {
            key = `${obj.source}|${obj.target}`;
        } else {
            key = obj.name || JSON.stringify(obj);
        }
        
        map.set(key, obj);
    }
    
    return map;
}

/**
 * Compare two objects and return list of differences
 */
function compareObjects(obj1, obj2) {
    const changes = [];
    
    // Get all keys from both objects
    const allKeys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);
    
    for (const key of allKeys) {
        const val1 = obj1[key];
        const val2 = obj2[key];
        
        if (!deepEqual(val1, val2)) {
            changes.push({
                property: key,
                oldValue: summarizeValue(val1),
                newValue: summarizeValue(val2)
            });
        }
    }
    
    return changes;
}

/**
 * Compare simple properties of two objects
 */
function compareProperties(obj1, obj2) {
    const diff = {};
    
    const simpleProps1 = getSimpleProperties(obj1);
    const simpleProps2 = getSimpleProperties(obj2);
    
    const allProps = new Set([...Object.keys(simpleProps1), ...Object.keys(simpleProps2)]);
    
    for (const prop of allProps) {
        const val1 = simpleProps1[prop];
        const val2 = simpleProps2[prop];
        
        if (!deepEqual(val1, val2)) {
            diff[prop] = {
                oldValue: val1,
                newValue: val2
            };
        }
    }
    
    return diff;
}

/**
 * Get simple (non-array) properties from an object
 */
function getSimpleProperties(obj) {
    const simple = {};
    
    for (const [key, value] of Object.entries(obj)) {
        if (!Array.isArray(value) && typeof value !== 'object') {
            simple[key] = value;
        }
    }
    
    return simple;
}

/**
 * Deep equality check for two values
 */
function deepEqual(val1, val2) {
    if (val1 === val2) return true;
    
    if (val1 === null || val2 === null) return false;
    if (val1 === undefined || val2 === undefined) return false;
    
    if (typeof val1 !== typeof val2) return false;
    
    if (Array.isArray(val1) && Array.isArray(val2)) {
        if (val1.length !== val2.length) return false;
        for (let i = 0; i < val1.length; i++) {
            if (!deepEqual(val1[i], val2[i])) return false;
        }
        return true;
    }
    
    if (typeof val1 === 'object' && typeof val2 === 'object') {
        const keys1 = Object.keys(val1);
        const keys2 = Object.keys(val2);
        
        if (keys1.length !== keys2.length) return false;
        
        for (const key of keys1) {
            if (!keys2.includes(key)) return false;
            if (!deepEqual(val1[key], val2[key])) return false;
        }
        
        return true;
    }
    
    return false;
}

/**
 * Summarize a value for display (truncate long arrays/objects)
 */
function summarizeValue(value) {
    if (value === null || value === undefined) {
        return value;
    }
    
    if (typeof value === 'string') {
        return value.length > 100 ? value.substring(0, 100) + '...' : value;
    }
    
    if (Array.isArray(value)) {
        if (value.length === 0) return '[]';
        if (value.length === 1) return `[${summarizeValue(value[0])}]`;
        return `[${value.length} items]`;
    }
    
    if (typeof value === 'object') {
        const keys = Object.keys(value);
        if (keys.length === 0) return '{}';
        return `{${keys.length} properties}`;
    }
    
    return value;
}

/**
 * Generate a human-readable summary of differences
 */
function generateSummary(differences) {
    const parts = [];
    
    for (const [arrayName, diff] of Object.entries(differences)) {
        if (arrayName === 'properties') continue;
        
        if (diff.added && diff.added.length > 0) {
            parts.push(`${arrayName}: ${diff.added.length} added`);
        }
        if (diff.removed && diff.removed.length > 0) {
            parts.push(`${arrayName}: ${diff.removed.length} removed`);
        }
        if (diff.modified && diff.modified.length > 0) {
            parts.push(`${arrayName}: ${diff.modified.length} modified`);
        }
    }
    
    if (differences.properties && Object.keys(differences.properties).length > 0) {
        parts.push(`properties: ${Object.keys(differences.properties).length} changed`);
    }
    
    if (parts.length === 0) {
        return 'No significant differences found';
    }
    
    return parts.join('; ');
}

/**
 * Format differences for display in UI
 */
export function formatDifferencesForDisplay(diffReport) {
    if (diffReport.identical) {
        return `
            <div class="diff-report identical">
                <h3>✓ Models are semantically equivalent</h3>
                <p>Hash: ${diffReport.hash1}</p>
            </div>
        `;
    }
    
    let html = `
        <div class="diff-report">
            <h3>Models are different</h3>
            <p><strong>Summary:</strong> ${diffReport.summary}</p>
            <p><strong>Model 1 Hash:</strong> <code>${diffReport.hash1}</code></p>
            <p><strong>Model 2 Hash:</strong> <code>${diffReport.hash2}</code></p>
    `;
    
    if (diffReport.differences) {
        html += '<h4>Detailed Differences:</h4>';
        
        for (const [arrayName, diff] of Object.entries(diffReport.differences)) {
            if (arrayName === 'properties') {
                html += formatPropertyDifferences(diff);
                continue;
            }
            
            html += `<div class="diff-section">`;
            html += `<h5>${arrayName}</h5>`;
            
            if (diff.added && diff.added.length > 0) {
                html += `<div class="diff-added">
                    <strong>Added (${diff.added.length}):</strong>
                    <ul>${diff.added.map(name => `<li>${name}</li>`).join('')}</ul>
                </div>`;
            }
            
            if (diff.removed && diff.removed.length > 0) {
                html += `<div class="diff-removed">
                    <strong>Removed (${diff.removed.length}):</strong>
                    <ul>${diff.removed.map(name => `<li>${name}</li>`).join('')}</ul>
                </div>`;
            }
            
            if (diff.modified && diff.modified.length > 0) {
                html += `<div class="diff-modified">
                    <strong>Modified (${diff.modified.length}):</strong>
                    <ul>`;
                
                for (const mod of diff.modified) {
                    html += `<li><strong>${mod.name}</strong><ul>`;
                    for (const change of mod.changes) {
                        html += `<li>${change.property}: 
                            <span class="old-value">${JSON.stringify(change.oldValue)}</span> → 
                            <span class="new-value">${JSON.stringify(change.newValue)}</span>
                        </li>`;
                    }
                    html += `</ul></li>`;
                }
                
                html += `</ul></div>`;
            }
            
            html += `</div>`;
        }
    }
    
    html += '</div>';
    
    return html;
}

/**
 * Format property differences
 */
function formatPropertyDifferences(propDiff) {
    let html = `<div class="diff-section"><h5>Model Properties</h5><ul>`;
    
    for (const [prop, change] of Object.entries(propDiff)) {
        html += `<li><strong>${prop}:</strong> 
            <span class="old-value">${JSON.stringify(change.oldValue)}</span> → 
            <span class="new-value">${JSON.stringify(change.newValue)}</span>
        </li>`;
    }
    
    html += '</ul></div>';
    
    return html;
}
