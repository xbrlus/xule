# Domain Class Object

## Overview

The **domain class object** is a fundamental component of the OIM Taxonomy specification that serves as the root identifier for domain objects. It acts as a classification mechanism that groups related domains and enables dimension-domain compatibility validation.

## Purpose

The domain class object serves several critical purposes in the OIM Taxonomy model:

### 1. **Domain Root Identification**
Every domain object must reference a domain class object through its `root` property. This establishes the domain class as the conceptual root of the domain hierarchy, providing a single point of reference for the entire domain structure.

### 2. **Dimension-Domain Compatibility**
When defining a dimension, the associated domain class object specifies which domains are compatible with that dimension. Multiple domains can be associated with a dimension across different cubes, but each of those domains must share the same domain class object. This ensures semantic consistency and prevents incompatible domains from being used with a given dimension.

### 3. **Domain Reusability**
A single domain class object can be referenced by multiple domains. This enables:
- Different cubes to use different domains with the same dimension
- Taxonomies to organize related domains under a common classification
- Clear identification and grouping of related dimensional domains

### 4. **Type Constraint Enforcement**
The domain class object can specify the types of objects or data types allowed in domains through the `allowedDomainItems` property. This enables:
- Typed domains (when only simple types are specified)
- Explicit domains (when object types are specified)
- Validation that domain members conform to expected types

## Built-in Domain Classes

The OIM Taxonomy specification defines four built-in domain class objects that correspond to the core XBRL dimensions:

| Domain Class | Associated Dimension | Usage |
|--------------|---------------------|-------|
| `xbrl:conceptDomain` | `xbrl:concept` | Can only be used with the concept dimension |
| `xbrl:entityDomain` | `xbrl:entity` | Can only be used with the entity dimension; may also be used for taxonomy-defined entity-specific dimensions (e.g., BusinessAcquisitionAxis) |
| `xbrl:unitDomain` | `xbrl:unit` | Can only be used with the unit dimension |
| `xbrl:languageDomain` | `xbrl:language` | Can only be used with the language dimension |

These built-in domain classes have strict constraints - they can only be used with their designated core dimensions.

## Domain Class Properties

### `name` (required)
The QName that uniquely identifies the domain class object. This name is referenced by:
- Domain objects (via the `root` property)
- Dimension objects (via the `domainClass` property)

### `baseDomainClass` (optional)
The QName of another domain class object that serves as the base for this domain class. This enables:
- Property inheritance from parent domain classes
- Hierarchical organization of domain class definitions
- Reuse of common domain class constraints

### `allowedDomainItems` (optional)
An ordered set of object types and data types that can be included in domains associated with this domain class. Each entry is a QName of either:
- An object type (e.g., `xbrl:conceptObject`, `xbrl:memberObject`, `xbrl:entityObject`, `xbrl:unitObject`)
- A data type (e.g., `xs:string`, `xs:decimal`)

This property enforces type constraints:
- If only simple types are defined, domains are typed domains
- If object types are defined, domains are explicit domains
- If not defined, any object type or data type may be used

### `properties` (optional)
An ordered set of property objects used to specify additional custom properties associated with the domain class.

## Rationale for Inclusion in the Specification

The domain class object addresses several critical requirements and design goals in the OIM Taxonomy model:

### 1. **Separation of Concerns**
In traditional XBRL taxonomies, dimension-domain relationships were tightly coupled and often tied to specific presentation roles. The domain class object provides a layer of abstraction that:
- Decouples domain definitions from presentation structures
- Enables domains to be defined as independent, reusable objects
- Eliminates the need to import entire roles just to access domain definitions

### 2. **Enhanced Validation**
By requiring dimensions to specify a domain class, the specification enables:
- **Compile-time validation**: Ensures domains used with a dimension are compatible
- **Semantic consistency**: Prevents accidental use of incompatible domains
- **Type safety**: Validates that domain members match expected types

Example: If a dimension specifies `domainClass: "geo:GeographyClass"`, only domains with `root: "geo:GeographyClass"` can be used with that dimension, preventing semantic errors.

### 3. **Taxonomy Simplification**
The domain class mechanism simplifies taxonomy authoring and maintenance:
- **Reduces redundancy**: Multiple domains can share the same domain class
- **Improves clarity**: The classification structure is explicit and discoverable
- **Facilitates extension**: Extension taxonomies can add new domains to existing domain classes

### 4. **Multi-Cube Flexibility**
Different cubes can use different domains with the same dimension, as long as they share the same domain class. This supports scenarios like:
- A "Balance Sheet" cube using a simplified geography domain
- A "Detailed Disclosure" cube using a comprehensive geography domain
- Both cubes using the same `GeographyAxis` dimension, which specifies `geo:GeographyClass`

### 5. **Support for Both Typed and Explicit Dimensions**
The `allowedDomainItems` property enables a single mechanism to support both:
- **Typed dimensions**: When `allowedDomainItems` contains only simple types
- **Explicit dimensions**: When `allowedDomainItems` contains object types

This unifies what were previously separate concepts in XBRL 2.1.

### 6. **Entity Domain Specialization**
The `xbrl:entityDomain` can be associated with taxonomy-defined dimensions representing domains of legal entities (e.g., `BusinessAcquisitionAxis`, `ConsolidatedEntitiesAxis`). This enables:
- Proper modeling of entity hierarchies in consolidation scenarios
- Constraints ensuring only entity objects appear in entity-specific domains
- Clear semantic distinction between entity dimensions and other dimension types

## Key Design Principles

### One Root Per Domain
Every domain must have exactly one domain class root. This ensures:
- Clear hierarchical structure
- Unambiguous interpretation of domain membership
- Simplified validation logic

### Compatibility Through Shared Classification
Domains are compatible with a dimension only if they share the dimension's domain class. This:
- Prevents semantic errors at the taxonomy level
- Makes compatibility rules explicit and machine-checkable
- Reduces runtime errors in consuming applications

### Flexibility Within Constraints
While enforcing strict compatibility rules, the domain class mechanism provides flexibility:
- Multiple domains per domain class (different levels of detail)
- Domain class inheritance (reuse of constraints)
- Both typed and explicit domain support

## Examples

### Custom Dimension with Domain Class

```json
{
  "domainClasses": [
    {
      "name": "geo:GeographyClass",
      "allowedDomainItems": ["xbrl:memberObject"]
    }
  ],
  "dimensions": [
    {
      "name": "geo:GeographyAxis",
      "domainClass": "geo:GeographyClass"
    }
  ],
  "domains": [
    {
      "name": "geo:SimpleGeographyDomain",
      "root": "geo:GeographyClass",
      "relationships": [
        {"source": "geo:GeographyClass", "target": "geo:Americas"},
        {"source": "geo:GeographyClass", "target": "geo:EMEA"}
      ]
    },
    {
      "name": "geo:DetailedGeographyDomain",
      "root": "geo:GeographyClass",
      "relationships": [
        {"source": "geo:GeographyClass", "target": "geo:NorthAmerica"},
        {"source": "geo:GeographyClass", "target": "geo:SouthAmerica"},
        {"source": "geo:GeographyClass", "target": "geo:Europe"},
        {"source": "geo:GeographyClass", "target": "geo:MiddleEast"},
        {"source": "geo:GeographyClass", "target": "geo:Africa"}
      ]
    }
  ]
}
```

In this example:
- Both domains share the `geo:GeographyClass` domain class
- Both can be used with the `geo:GeographyAxis` dimension
- Different cubes can choose which domain to use based on reporting requirements
- The `allowedDomainItems` constraint ensures only member objects can be used

### Typed Domain with Domain Class

```json
{
  "domainClasses": [
    {
      "name": "prod:ProductCodeClass",
      "allowedDomainItems": ["xs:string"]
    }
  ],
  "dimensions": [
    {
      "name": "prod:ProductAxis",
      "domainClass": "prod:ProductCodeClass"
    }
  ]
}
```

This creates a typed dimension where:
- The `allowedDomainItems` contains only a simple type (`xs:string`)
- No explicit domain object is defined
- Facts can use any string value as the dimension value
- The domain class still provides classification and validation

## Relationship to Requirements

The domain class object directly addresses several requirements from the OIM Taxonomy Requirements specification:

- **REQ-DO1**: "The taxonomy model should define a domain as an object that can be referenced" - The domain class provides a stable reference point for domain identification

- **REQ-DO2**: "The domain object should encompass all properties that define a domain of concept members" - The domain class enables property definition and constraint specification

- **REQ-DO3**: "The domain object can only have one domain root concept" - The domain class serves as this single root

- **REQ-DO4**: "The default value of a dimension should be the domain concept associated with the cube dimension" - The domain class mechanism ensures all domains for a dimension share a common root

## Conclusion

The domain class object is essential to the OIM Taxonomy specification because it:

1. **Establishes clear semantic boundaries** between compatible and incompatible domains
2. **Enables reusability** of domain structures across multiple cubes and taxonomies
3. **Simplifies validation** by making dimension-domain compatibility explicit
4. **Unifies typed and explicit dimensions** under a single conceptual framework
5. **Facilitates taxonomy extension** by providing a stable classification structure

Without domain classes, the OIM Taxonomy model would lack a mechanism to ensure semantic consistency of dimension-domain relationships, leading to potential modeling errors and incompatibilities across taxonomies.
