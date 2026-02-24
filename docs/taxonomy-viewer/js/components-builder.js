/**
 * Components Builder Module
 * Handles building component lists for:
 * - Concepts
 * - Dimensions
 * - Domain Classes
 * - Units
 * - Members
 * - Abstracts
 * - Entities
 * - Transforms
 * - Property Types
 * - Data Types
 * - Cube Types
 * - Label Types
 * - Reference Types
 */

import { getTaxonomyData } from './state.js';
import { getIconForType, getXbrlModel } from './utils.js';
import { attachNodeHandlers } from './tree-handlers.js';

/**
 * Build a list of taxonomy components (concepts, dimensions, units, members, abstracts, entities, or types)
 * @param {string} arrayName - The name of the array in taxonomy data (e.g., 'concepts', 'dimensions')
 * @param {HTMLElement} container - The DOM container to append the list to
 * @param {string} typeName - The type identifier for dataset (e.g., 'concept', 'dimension')
 */
export function buildComponentsList(arrayName, container, typeName) {
    console.log(`[Components Builder] Building ${arrayName} list`);
    
    const taxonomyData = getTaxonomyData();
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.warn(`[Components Builder] No taxonomy data available for ${arrayName}`);
        return;
    }

    const ul = document.createElement('ul');
    
    if (xbrlModel[arrayName]) {
        console.log(`[Components Builder] ${arrayName} found:`, xbrlModel[arrayName].length);
        
        // Create a sorted list by name
        const sortedItems = [...xbrlModel[arrayName]].sort((a, b) => {
            return a.name.localeCompare(b.name);
        });
        
        sortedItems.forEach(item => {
            const li = document.createElement('li');
            
            // Add icon based on type (check for custom iconLabel first)
            const icon = document.createElement('span');
            icon.className = 'node-icon';
            icon.textContent = getIconForType(typeName, item.name);
            li.appendChild(icon);
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = item.name;
            li.appendChild(nameSpan);
            
            li.classList.add('node');
            li.dataset.type = typeName;
            // Store either the name (for concepts) or the full object
            li.dataset.obj = typeName === 'concept' ? item.name : JSON.stringify(item);
            ul.appendChild(li);
        });
    } else {
        console.warn(`[Components Builder] No ${arrayName} found in taxonomy data`);
    }
    
    container.appendChild(ul);
    
    // Attach node handlers from tree-handlers module
    attachNodeHandlers(container);
}

/**
 * Build all component lists
 * @param {Object} containers - Object with container elements for each component type
 */
export function buildAllComponents(containers) {
    console.log('[Components Builder] Building all component lists');
    
    // Build Components (Concepts, Dimensions, Domain Classes, Units, Members, Abstracts, Entities)
    if (containers.concepts) {
        buildComponentsList('concepts', containers.concepts, 'concept');
    }
    if (containers.dimensions) {
        buildComponentsList('dimensions', containers.dimensions, 'dimension');
    }
    if (containers.domainClasses) {
        buildComponentsList('domainClasses', containers.domainClasses, 'domainClass');
    }
    if (containers.units) {
        buildComponentsList('units', containers.units, 'unit');
    }
    if (containers.members) {
        buildComponentsList('members', containers.members, 'member');
    }
    if (containers.abstracts) {
        buildComponentsList('abstracts', containers.abstracts, 'abstract');
    }
    if (containers.entities) {
        buildComponentsList('entities', containers.entities, 'entity');
    }
    if (containers.transforms) {
        buildComponentsList('transforms', containers.transforms, 'transform');
    }
    
    // Build Types (Property Types, Data Types, Cube Types, Label Types, Reference Types)
    if (containers.propertyTypes) {
        buildComponentsList('propertyTypes', containers.propertyTypes, 'propertyType');
    }
    if (containers.dataTypes) {
        buildComponentsList('dataTypes', containers.dataTypes, 'dataType');
    }
    if (containers.cubeTypes) {
        buildComponentsList('cubeTypes', containers.cubeTypes, 'cubeType');
    }
    if (containers.labelTypes) {
        buildComponentsList('labelTypes', containers.labelTypes, 'labelType');
    }
    if (containers.referenceTypes) {
        buildComponentsList('referenceTypes', containers.referenceTypes, 'referenceType');
    }
    if (containers.relationshipTypes) {
        buildComponentsList('relationshipTypes', containers.relationshipTypes, 'relationshipType');
    }
}
