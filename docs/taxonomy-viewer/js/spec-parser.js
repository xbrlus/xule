/**
 * Specification Parser Module
 * Extracts property descriptions from oim-taxonomy.md specification
 */

// Property descriptions extracted from oim-taxonomy.md
export const propertyDescriptions = {
    // DocumentInfo properties
    "documentInfo": "Provides document-level information about the taxonomy.",
    "documentType": "The fixed value https://xbrl.org/2026/model",
    "namespaces": "A namespace object defining the prefix and associated URI.",
    "documentNamespace": "A string that identifies the namespace of the document.",
    "urlMapping": "A ulMapping object defining the namespace prefix and associated URL locations.",
    "description": "A string that provides a description of the taxonomy module.",
    
    // XBRL Model object properties (previously 'taxonomy')
    "xbrlModel": "The container object that includes all the component objects that comprise an XBRL model.",
    "taxonomy": "DEPRECATED: Use 'xbrlModel' instead. The container object that includes all the component objects that comprise a taxonomy.",
    "name": "The name is a QName that uniquely identifies the object.",
    "frameworkName": "The framework name of the taxonomy such as 'US-GAAP' that indicates the taxonomy broad taxonomy family.",
    "version": "Used to identify the version of the taxonomy such as the year of release.",
    "importedTaxonomies": "Ordered set of importTaxonomy objects that can comprise QName of the XBRL model to be imported.",
    "finalTaxonomy": "A final taxonomy object that indicates those components of the taxonomy that are final and cannot be amended or added by an importing taxonomy.",
    "abstracts": "Ordered set of abstract objects.",
    "concepts": "Ordered set of concept objects.",
    "cubes": "Ordered set of cube objects.",
    "cubeTypes": "Ordered set of cubeType objects.",
    "dataTypes": "Ordered set of dataType objects.",
    "dimensions": "Ordered set of dimension objects.",
    "domains": "Ordered set of domain objects.",
    "domainClasses": "Ordered set of domain class objects.",
    "entities": "Ordered set of entity objects.",
    "facts": "Ordered set of fact objects.",
    "footnotes": "Ordered set of footnote objects.",
    "groups": "Ordered set of group objects.",
    "groupContents": "Ordered set of groupContent objects that link a group QName to a list of network or cube objects.",
    "groupTree": "A groupTree object that defines the hierarchical organization of groups within the taxonomy.",
    "labels": "Ordered set of label objects.",
    "members": "Ordered set of member objects.",
    "networks": "Ordered set of network objects.",
    "propertyTypes": "Ordered set of propertyType objects.",
    "references": "Ordered set of reference objects.",
    "referenceTypes": "Ordered set of referenceType objects.",
    "relationshipTypes": "Ordered set of relationshipType objects.",
    "units": "Ordered set of unit objects.",
    "properties": "Ordered set of property objects used to specify additional properties associated with the object.",
    "transforms": "An ordered set of transform objects.",
    
    // ImportTaxonomy properties
    "xbrlModelName": "The QName of the XBRL model to import. The processor MUST retrieve and process the module located at the specified location to import the objects defined in the importTaxonomy object.",
    "taxonomyName": "DEPRECATED: Use 'xbrlModelName' instead. The QName of the taxonomy to import. The processor MUST retrieve and process the taxonomy module located at the specified location.",
    "selections": "Specifies a set of select statements or structured select objects that define the objects to be included in the import.",
    "importObjects": "A set of object QNames that should be imported from the xbrlModelName location. Only the objects defined in the importObjects set and any referenced objects will be added to the XBRL model.",
    "importObjectTypes": "A set of object type QNames that should be imported from the xbrlModelName location. All objects of the specified object types and any referenced objects will be imported.",
    "excludeLabels": "If set to true, any labels attached to the objects comprising the XBRL model deriving from the xbrlModelName property will be excluded. Default is false.",
    
    // Select statement properties
    "objectType": "The type of the object to be selected. This is a QName that identifies the object type, such as xbrl:conceptObject, xbrl:dimensionObject, etc.",
    "where": "An array of filter conditions that define the selection criteria.",
    "property": "The name of the property to be used for filtering the objects.",
    "operator": "The operator to be used for filtering the objects. Can be: =, !=, in, not in, contains, not contains, >, <, >=, <=.",
    "value": "The value to be used for filtering the objects. The value can be a string, number, or boolean.",
    
    // FinalTaxonomy properties
    "finalTaxonomyFlag": "If set to true, indicates that the taxonomy is final and cannot be extended by importing taxonomies. Default is false.",
    "finalObjectTypes": "A set of object type QNames that define the types of objects that are considered final.",
    "finalObjects": "A set of object QNames that define the specific extendable objects that are considered final.",
    
    // Concept properties
    "dataType": "Specifies the data type of the value. The value MUST be a QName referencing either a built-in XML Schema simple type, a data type defined in this specification, or a custom data type.",
    "periodType": "Indicates the period type of the concept. The value can be either 'instant', 'duration' or 'none'.",
    "enumerationDomain": "Used to specify enumerated domain members that are associated with a domain object defined in the taxonomy.",
    "nillable": "Used to specify if the concept can have a nil value. Default is false.",
    
    // Dimension properties
    "domainClass": "The QName of the domain class object for the dimension. All dimensions, whether typed or explicit, must reference a domain class.",
    
    // Domain properties
    "root": "The QName that uniquely identifies the root of the domain object. This must be a domain class object.",
    "relationships": "An ordered set of relationship objects that associate taxonomy objects with the domain.",
    "extendTargetName": "Names the domain object that the defined domain relationships should be appended to.",
    "completeDomain": "If set to true, the domain is considered complete. If false, additional relationships or members may be added by an extension taxonomy. Default is false.",
    
    // DomainClass properties
    "allowedDomainItems": "An ordered set of object types and data types that can be included in domains associated with the domain class object.",
    
    // Cube properties
    "cubeType": "The cubeType property identifies the type of cube being defined. Must match a defined cubeType object or specification defined cube object. Default is xbrl:reportCube.",
    "cubeDimensions": "An ordered set of cubeDimension objects that identify the dimensions and associated domains used on the cube.",
    "cubeNetworks": "An ordered set of network object QNames that reference network objects that are directly related to the cube.",
    "excludeCubes": "An ordered set of cube object QNames that remove the facts of the exclude cube from the facts of the defined cube.",
    "cubeComplete": "A boolean flag that indicates if all cells in the cube are required to have a value. Default is false.",
    
    // CubeDimension properties
    "dimensionName": "The QName of the dimension object that is used to identify the dimension. For core dimensions, use xbrl:concept, xbrl:period, xbrl:entity, xbrl:unit, or xbrl:language.",
    "domainName": "The QName of the domain object that is used to identify the domain associated with the dimension. Only one explicit domain can be associated with a dimension.",
    "domainDataType": "A datatype object that indicates the type that can be represented on the domain. This property allows a typed domain to be associated with a dimension.",
    "typedSort": "A string value that indicates the sort order of the typed domain. Values can be either 'asc' or 'desc'.",
    "allowDomainFacts": "A boolean value that indicates if facts not identified with the dimension are included in the cube. Default is false for typed and explicit dimensions.",
    "periodConstraints": "Defines an ordered set of periodConstraint objects to restrict fact values in a cube to fact values with a specified period.",
    
    // PeriodConstraint properties
    "timeSpan": "Duration value specifying the time span for period constraints.",
    "periodPattern": "Pattern for matching dates or durations (e.g., YYYY-MM-DD for December dates, YYYY-12-31/YYYY-12-31 for year-end durations). Supports wildcards like 'eom' for end of month.",
    "endDate": "A dateResolutionObject specifying the end date constraint.",
    "startDate": "A dateResolutionObject specifying the start date constraint.",
    "onOrAfter": "A dateResolutionObject specifying the earliest allowed date.",
    "onOrBefore": "A dateResolutionObject specifying the latest allowed date.",
    
    // DateResolution properties
    "conceptName": "The QName of a concept used in date resolution.",
    "context": "A string providing context for date resolution.",
    "timeShift": "Duration value for shifting time periods.",
    
    // Layout properties
    "layout": "A layout object that defines the layout of a data structure that conforms with a taxonomy model.",
    
    // Relationship properties
    "source": "Identifies the source concept of the relationship type. The value must be a QName.",
    "target": "Identifies the target concept of the relationship type. The value must be a QName.",
    "order": "Used to order the relationships relative to their level in a hierarchy. If no order attribute is provided, the order of appearance in the array is used as default.",
    
    // RelationshipType properties
    "uri": "The URI of the relationship type for historical and backward compatibility purposes.",
    "cycles": "Indicates if the relationship when used in a hierarchy can include cycles. Possible values are 'any', 'none', and 'undirected'.",
    "allowedLinkProperties": "Defines an ordered set of property QNames that can be included on the relationship type. Only properties defined in this list can be added to the specific relationship type.",
    "requiredLinkProperties": "Defines an ordered set of property QNames that MUST be included on the relationship type.",
    "sourceObjects": "Defines an ordered set of source object types that can be used as the source for the relationship. Only referenceable taxonomy objects are permitted.",
    "targetObjects": "Defines an ordered set of target object types that can be used as the target for the relationship. Only referenceable taxonomy objects are permitted.",
    "constraints": "An ordered set of relationshipConstraint objects that define the allowable properties of source, target and links comprising the relationship.",
    
    // PropertyType properties
    "definitional": "Indicates if the property is definitional. If changes to the property change the meaning of the object it is definitional. Defaults to false.",
    "allowedObjects": "Set of object type QNames that the property can be used with. For example, the balance property can only be used with xbrl:conceptObject.",
    "allowedAsLinkProperty": "Indicates if the property can be used as a property on the link between two objects in a relationship. Defaults to false.",
    
    // Property object properties
    "property": "The name is a QName that uniquely identifies the propertyType object.",
    
    // Network properties
    "relationshipTypeName": "The relationshipType object of the network expressed as a QName such as xbrl:parent-child.",
    "roots": "A list of the root objects of the network object. The order of roots in the list indicates the order in which the roots should appear.",
    
    // Label properties
    "relatedName": "Defines a QName that the label is associated with.",
    "labelType": "A QName representing the label type of the label. Can be a taxonomy defined label type or a standard XBRL label type.",
    "language": "Defines the language of the label using a valid BCP 47 language code.",
    
    // Reference properties
    "relatedNames": "Defines a set of ordered QNames that the reference is associated with.",
    "referenceType": "A QName representing the reference type of the reference.",
    
    // Unit properties
    "numerator": "Defines the numerator units of a ratio unit.",
    "denominator": "Defines the denominator units of a ratio unit.",
    "multiply": "Defines units that are multiplied together.",
    "divide": "Defines units that are divided.",
    
    // Fact properties
    "dimensions": "An ordered set of factDimension objects that define the dimensions of the fact.",
    "factValues": "An ordered set of factValues objects that define the fact values in the fact.",
    
    // Group properties
    "groupType": "Identifies the type of group being defined.",
    "groupName": "The QName of the group object.",
    
    // CubeType properties
    "requiredDimensions": "Defines an ordered set of dimension QNames that must be present in cubes of this type.",
    "optionalDimensions": "Defines an ordered set of dimension QNames that may be present in cubes of this type.",
    "excludedDimensions": "Defines an ordered set of dimension QNames that must not be present in cubes of this type.",
    
    // Transform properties
    "transformType": "The QName of the transform type.",
    "inputFormat": "Specifies the expected input format for the transform.",
    "outputFormat": "Specifies the output format produced by the transform.",
    
    // Common metadata properties
    "id": "A unique identifier for the object.",
    "type": "Specifies the type of the object.",
    "role": "Specifies the role of the object in the taxonomy.",
    "title": "A human-readable title for the object.",
    "href": "A URL reference to an external resource."
};

/**
 * Get the description for a property
 * @param {string} propertyName - The name of the property
 * @returns {string|null} The description or null if not found
 */
export function getPropertyDescription(propertyName) {
    return propertyDescriptions[propertyName] || null;
}
