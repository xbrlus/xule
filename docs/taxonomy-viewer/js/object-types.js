/**
 * Central definition of all built-in XBRL object types
 * This is the single source of truth for object type definitions across the application
 */

/**
 * Canonical list of all built-in object type definitions
 * Each entry defines:
 * - qname: The fully qualified object type name (e.g., 'xbrl:conceptObject')
 * - arrayName: The taxonomy array property name (e.g., 'concepts')
 * - importable: Whether objects of this type can be imported via importObjectTypes
 * - aliases: Alternative names that can be used in selections
 */
export const OBJECT_TYPE_DEFINITIONS = [
    { 
        qname: 'xbrl:abstractObject', 
        arrayName: 'abstracts', 
        importable: true,
        aliases: ['xbrl:abstract', 'abstract', 'abstracts']
    },
    { 
        qname: 'xbrl:conceptObject', 
        arrayName: 'concepts', 
        importable: true,
        aliases: ['xbrl:concept', 'concept', 'concepts']
    },
    { 
        qname: 'xbrl:cubeDimensionObject', 
        arrayName: 'cubeDimensions', 
        importable: false, // Cannot import cubeDimension objects (nested in cubes)
        aliases: []
    },
    { 
        qname: 'xbrl:cubeObject', 
        arrayName: 'cubes', 
        importable: true,
        aliases: ['xbrl:cube', 'cube', 'cubes']
    },
    { 
        qname: 'xbrl:cubeTypeObject', 
        arrayName: 'cubeTypes', 
        importable: true,
        aliases: ['xbrl:cubeType', 'cubeType', 'cubeTypes']
    },
    { 
        qname: 'xbrl:dataTypeObject', 
        arrayName: 'dataTypes', 
        importable: true,
        aliases: ['xbrl:dataType', 'dataType', 'dataTypes']
    },
    { 
        qname: 'xbrl:dimensionObject', 
        arrayName: 'dimensions', 
        importable: true,
        aliases: ['xbrl:dimension', 'dimension', 'dimensions']
    },
    { 
        qname: 'xbrl:domainObject', 
        arrayName: 'domains', 
        importable: true,
        aliases: ['xbrl:domain', 'domain', 'domains']
    },
    { 
        qname: 'xbrl:domainClassObject', 
        arrayName: 'domainClasses', 
        importable: true,
        aliases: ['xbrl:domainClass', 'domainClass', 'domainClasses']
    },
    { 
        qname: 'xbrl:entityObject', 
        arrayName: 'entities', 
        importable: true,
        aliases: ['xbrl:entity', 'entity', 'entities']
    },
    { 
        qname: 'xbrl:factObject', 
        arrayName: 'facts', 
        importable: true,
        aliases: ['xbrl:fact', 'fact', 'facts']
    },
    { 
        qname: 'xbrl:finalTaxonomyObject', 
        arrayName: 'finalTaxonomy', 
        importable: false, // Cannot import finalTaxonomy objects (single object, not array)
        aliases: []
    },
    { 
        qname: 'xbrl:footnoteObject', 
        arrayName: 'footnotes', 
        importable: true,
        aliases: ['xbrl:footnote', 'footnote', 'footnotes']
    },
    { 
        qname: 'xbrl:groupObject', 
        arrayName: 'groups', 
        importable: true,
        aliases: ['xbrl:group', 'group', 'groups']
    },
    { 
        qname: 'xbrl:groupContentObject', 
        arrayName: 'groupContents', 
        importable: true,
        aliases: ['xbrl:groupContent', 'groupContent', 'groupContents']
    },
    { 
        qname: 'xbrl:groupTreeObject', 
        arrayName: 'groupTree', 
        importable: false, // Cannot import groupTree objects (single object, not array)
        aliases: []
    },
    { 
        qname: 'xbrl:importTaxonomyObject', 
        arrayName: 'importedTaxonomies', 
        importable: false, // Cannot import importTaxonomy objects
        aliases: []
    },
    { 
        qname: 'xbrl:labelObject', 
        arrayName: 'labels', 
        importable: true,
        aliases: ['xbrl:label', 'label', 'labels']
    },
    { 
        qname: 'xbrl:labelTypeObject', 
        arrayName: 'labelTypes', 
        importable: true,
        aliases: ['xbrl:labelType', 'labelType', 'labelTypes']
    },
    { 
        qname: 'xbrl:layoutObject', 
        arrayName: 'layouts', 
        importable: true,
        aliases: ['xbrl:layout', 'layout', 'layouts']
    },
    { 
        qname: 'xbrl:memberObject', 
        arrayName: 'members', 
        importable: true,
        aliases: ['xbrl:member', 'member', 'members']
    },
    { 
        qname: 'xbrl:networkObject', 
        arrayName: 'networks', 
        importable: true,
        aliases: ['xbrl:network', 'network', 'networks']
    },
    { 
        qname: 'xbrl:propertyObject', 
        arrayName: 'properties', 
        importable: false, // Cannot import property objects (nested in other objects)
        aliases: []
    },
    { 
        qname: 'xbrl:propertyTypeObject', 
        arrayName: 'propertyTypes', 
        importable: true,
        aliases: ['xbrl:propertyType', 'propertyType', 'propertyTypes']
    },
    { 
        qname: 'xbrl:modelTypeObject', 
        arrayName: 'modelTypes', 
        importable: true,
        aliases: ['xbrl:modelType', 'modelType', 'modelTypes']
    },
    { 
        qname: 'xbrl:referenceObject', 
        arrayName: 'references', 
        importable: true,
        aliases: ['xbrl:reference', 'reference', 'references']
    },
    { 
        qname: 'xbrl:referenceTypeObject', 
        arrayName: 'referenceTypes', 
        importable: true,
        aliases: ['xbrl:referenceType', 'referenceType', 'referenceTypes']
    },
    { 
        qname: 'xbrl:relationshipObject', 
        arrayName: 'relationshipTypes', 
        importable: true,
        aliases: ['xbrl:relationshipType', 'relationshipType', 'relationshipTypes']
    },
    { 
        qname: 'xbrl:factMapObject', 
        arrayName: 'factMaps', 
        importable: true,
        aliases: ['xbrl:factMap', 'factMap', 'factMaps']
    },
    { 
        qname: 'xbrl:factSourceObject', 
        arrayName: 'factSources', 
        importable: true,
        aliases: ['xbrl:factSource', 'factSource', 'factSources']
    },
    { 
        qname: 'xbrl:xbrlModelObject', 
        arrayName: 'xbrlModels', 
        importable: false, // Cannot import xbrlModel objects (single object, not array)
        aliases: []
    },
    { 
        qname: 'xbrl:tableTemplateObject', 
        arrayName: 'tableTemplates', 
        importable: true,
        aliases: ['xbrl:tableTemplate', 'tableTemplate', 'tableTemplates']
    },
    { 
        qname: 'xbrl:unitObject', 
        arrayName: 'units', 
        importable: true,
        aliases: ['xbrl:unit', 'unit', 'units']
    }
];

/**
 * Set of all built-in object type QNames for fast lookup
 * Used for validation to check if a QName is a valid built-in object type
 */
export const BUILTIN_OBJECT_TYPES_SET = new Set(
    OBJECT_TYPE_DEFINITIONS.map(def => def.qname)
);

/**
 * Set of built-in object type QNames that CANNOT be used in importObjectTypes.
 * These are nested sub-objects (live inside a parent object, not at the top-level
 * model array), singleton objects (only one instance per model), and structural
 * meta-objects that define the import mechanism itself.
 */
export const NON_IMPORTABLE_OBJECT_TYPES_SET = new Set(
    OBJECT_TYPE_DEFINITIONS.filter(def => !def.importable).map(def => def.qname)
);

/**
 * Map of object type QNames to taxonomy array property names
 * Used for importObjectTypes processing
 * Returns null for non-importable types
 */
export const BUILTIN_OBJECT_TYPES_MAP = Object.fromEntries(
    OBJECT_TYPE_DEFINITIONS.map(def => [
        def.qname, 
        def.importable ? def.arrayName : null
    ])
);

/**
 * Backward compatibility: Export BUILTIN_OBJECT_TYPES_MAP as BUILTIN_OBJECT_TYPES
 * @deprecated Use BUILTIN_OBJECT_TYPES_MAP instead
 */
export const BUILTIN_OBJECT_TYPES = BUILTIN_OBJECT_TYPES_MAP;

/**
 * Map of object type QNames and aliases to taxonomy array property names
 * Used for selections parsing (allows shorthand like 'concept' or 'xbrl:concept')
 * Includes all QNames and their aliases
 */
export const OBJECT_TYPE_TO_ARRAY_MAP = (() => {
    const map = {};
    OBJECT_TYPE_DEFINITIONS.forEach(def => {
        // Add the canonical QName
        map[def.qname] = def.arrayName;
        // Add all aliases
        def.aliases.forEach(alias => {
            map[alias] = def.arrayName;
        });
        // Also add lowercase versions for case-insensitive matching
        map[def.qname.toLowerCase()] = def.arrayName;
    });
    return map;
})();

/**
 * Array of all built-in object type QNames
 * Used for iteration and UI rendering
 */
export const BUILTIN_OBJECT_TYPES_ARRAY = OBJECT_TYPE_DEFINITIONS.map(def => def.qname);

/**
 * Get the array name for a given object type or alias
 * @param {string} typeOrAlias - Object type QName or alias
 * @returns {string|null} - Array name or null if not found
 */
export function getArrayNameForType(typeOrAlias) {
    return OBJECT_TYPE_TO_ARRAY_MAP[typeOrAlias] || 
           OBJECT_TYPE_TO_ARRAY_MAP[typeOrAlias.toLowerCase()] || 
           null;
}

/**
 * Check if a QName is a built-in object type
 * @param {string} qname - QName to check
 * @returns {boolean}
 */
export function isBuiltinObjectType(qname) {
    return BUILTIN_OBJECT_TYPES_SET.has(qname);
}

/**
 * Check if an object type is importable
 * @param {string} qname - Object type QName
 * @returns {boolean}
 */
export function isImportableType(qname) {
    const def = OBJECT_TYPE_DEFINITIONS.find(d => d.qname === qname);
    return def ? def.importable : false;
}

/**
 * Get all importable object types
 * @returns {Array<string>} - Array of importable object type QNames
 */
export function getImportableTypes() {
    return OBJECT_TYPE_DEFINITIONS
        .filter(def => def.importable)
        .map(def => def.qname);
}
