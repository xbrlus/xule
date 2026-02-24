# Cube Type Object

## Overview

The **cube type object** (`xbrl:cubeTypeObject`) defines constraints on the structure and content of cubes within an XBRL taxonomy. A cube type specifies which dimensions (core and taxonomy-defined), relationships, and properties are permitted or required in cubes of that type. This enables taxonomies to enforce data quality rules, ensure semantic consistency, and align XBRL data structures with specific use cases such as event tracking, reference data management, time series reporting, and traditional financial reporting.

## Purpose

The cube type object serves several critical purposes in the OIM Taxonomy specification:

### 1. **Dimensional Constraint Definition**
Cube types define precisely which dimensions can appear in a cube and whether they are required or optional. This includes:
- **Core dimensions**: `xbrl:concept`, `xbrl:period`, `xbrl:entity`, `xbrl:unit`, `xbrl:language`
- **Taxonomy-defined dimensions**: typed or explicit dimensions specific to the taxonomy
- **Dimension type constraints**: whether typed or explicit dimensions are allowed
- **Data type constraints**: for typed dimensions, what data types are permitted

### 2. **Use-Case Specialization**
Different types of business data have fundamentally different structural requirements. Cube types enable the specification to provide pre-defined structures optimized for specific use cases:
- **Event data**: capturing discrete occurrences without period-based discrimination
- **Reference data**: static information that doesn't change over time
- **Time series data**: measurements at regular intervals
- **Position data**: balance sheet positions at specific points in time
- **Journal entries**: double-entry accounting transactions
- **Report data**: traditional financial statement data

### 3. **Relationship Enforcement**
Cube types can mandate specific relationships between objects in a cube, such as:
- Requiring date concepts to reference the period dimension
- Requiring concepts to connect to aggregation dimensions
- Enforcing reference dimension linkages in position cubes
- Defining event detail relationships

### 4. **Property Requirements**
Cube types can specify which properties must or may be associated with cubes, enabling:
- Required metadata for specific cube types
- Constrained property usage for validation
- Custom extensions with enforced documentation

### 5. **Type Inheritance and Restriction**
Through the `baseCubeType` property, cube types support inheritance, allowing:
- Definition of specialized cube types from base types
- Restriction (but not expansion) of base type constraints
- Reuse of common structural patterns across cube types

## Cube Type Object Properties

The cube type object includes the following properties:

### `name` (required)
- **Type**: `xs:QName`
- **Description**: Uniquely identifies the cube type object
- **Example**: `"xbrl:eventCube"`, `"exp:CustomCubeType"`

### `baseCubeType` (optional)
- **Type**: `xbrli:cubeTypeQName`
- **Description**: References a parent cube type from which this cube type inherits constraints. Derived cube types must restrict (not expand) the base type's constraints.
- **Example**: `"xbrl:eventDetailsCube"` (for journal cube)

### `coreDimensions` (optional)
- **Type**: Ordered set of QNames
- **Description**: Specifies which core dimensions are permitted in cubes of this type. The `xbrl:concept` dimension is always included and need not be listed. If not specified, all core dimensions except `xbrl:concept` are allowed by default.
- **Allowed values**: `xbrl:concept`, `xbrl:period`, `xbrl:entity`, `xbrl:unit`, `xbrl:language`
- **Example**: `["xbrl:period", "xbrl:entity", "xbrl:unit"]` (for report cube)

### `cubeDimensionConstraints` (optional)
- **Type**: `xbrl:dimensionsAllowedObject`
- **Description**: Defines constraints on taxonomy-defined dimensions that can be included in cubes of this type
- **Sub-properties**:
  - `allowed`: Array of dimension constraint objects
  - `closed`: Boolean indicating whether only listed dimensions are allowed

### `cubeRelationships` (optional)
- **Type**: `xbrl:cubeRelationshipAllowedObject`
- **Description**: Defines constraints on relationships that can be associated with cubes of this type
- **Sub-properties**:
  - `required`: Array of relationship constraint objects that must be present
  - `allowed`: Array of relationship constraint objects that are permitted

### `cubeProperties` (optional)
- **Type**: `xbrl:cubePropertiesConstraintObject`
- **Description**: Defines constraints on properties that can be associated with cubes of this type
- **Sub-properties**:
  - `required`: Array of property type QNames that must be present
  - `allowed`: Array of property type QNames that are permitted

## Rationale for Inclusion

The cube type object is fundamental to the OIM Taxonomy specification for the following reasons:

### 1. **Data Quality and Validation**
Without cube types, taxonomies would have no mechanism to enforce structural constraints on multidimensional data. Cube types enable:
- Detection of invalid dimension combinations (e.g., period dimension in event cubes)
- Verification that required relationships are present
- Validation that all mandatory metadata properties are included
- Prevention of incompatible data structure definitions

### 2. **Semantic Clarity**
Cube types make the intended use of a cube explicit through its type declaration. When a processor encounters an `xbrl:eventCube`, it immediately understands:
- This represents discrete events, not periodic measurements
- The period dimension should not be used for event discrimination
- An event dimension identifier is required
- Date concepts must reference the period dimension

This semantic clarity reduces ambiguity and implementation errors.

### 3. **Format Alignment**
Different cube types naturally align with different presentation formats:
- **Event cubes** → CSV files with event identifiers as keys
- **Time series cubes** → Time-indexed data files
- **Reference cubes** → Lookup tables or master data files
- **Report cubes** → Traditional financial statement templates

Explicit cube typing enables processors to optimize rendering and transformation based on the cube type.

### 4. **Evolution and Extension**
The `baseCubeType` mechanism enables:
- Gradual specialization of cube types as new use cases emerge
- Reuse of well-defined structural patterns
- Maintenance of backward compatibility while adding restrictions
- Community-driven development of standardized cube type taxonomies

### 5. **Interoperability**
By standardizing cube types across taxonomies, the specification ensures that:
- Different organizations can recognize and correctly process each other's data structures
- Software tools can implement optimized processing for standard cube types
- Data exchange formats can be more precisely specified
- Validation rules can be consistently applied across implementations

### 6. **Reduced Taxonomy Complexity**
Cube types encapsulate common structural patterns, reducing the need for:
- Repetitive dimension constraint definitions
- Custom validation rules for each cube
- Extensive documentation of cube structure requirements
- Manual enforcement of dimensional compatibility rules

### 7. **Support for Non-Traditional Use Cases**
Traditional XBRL focused primarily on report cubes with period/entity/unit dimensions. Cube types enable XBRL to effectively model:
- Event-driven systems (transactions, alerts, audit logs)
- Master data management (reference tables, hierarchies)
- Time series analytics (sensor data, market feeds)
- Position tracking (securities portfolios, inventory)
- Journal entry systems (accounting transaction details)

## Built-in Cube Types

The specification defines eight standard cube types that cover common business reporting scenarios:

| Cube Type QName | Primary Use Case | Core Dimensions | Taxonomy Dimension Requirements |
|----------------|------------------|----------------|--------------------------------|
| `xbrl:eventCube` | Discrete event tracking | None | One required typed dimension (non-date) |
| `xbrl:journalCube` | Accounting journal entries | None | One required typed dimension |
| `xbrl:eventDetailsCube` | Event supplementary data | None | One required typed dimension |
| `xbrl:referenceCube` | Static reference data | None | One required typed dimension |
| `xbrla:timeSeriesCube` | Time series measurements | None | One required typed date/time dimension |
| `xbrl:positionCube` | Balance positions | period, entity, unit | One required typed dimension |
| `xbrl:reportCube` | Traditional financial reports | period, entity, unit | Optional explicit/typed dimensions |
| `xbrl:defaultCube` | Unstructured fact collection | period, entity, unit | Optional any dimensions |

Each built-in cube type is precisely defined with specific constraints on dimensions, relationships, and properties, as detailed in the specification.

## Key Design Principles

### 1. **Restriction-Only Inheritance**
Derived cube types can only restrict, never expand, the constraints of their base type. This ensures that:
- A cube valid for a derived type is also valid for its base type
- Processing logic for base types can safely handle derived types
- Type hierarchies maintain logical consistency

### 2. **Explicit Over Implicit**
Cube types make structural requirements explicit rather than relying on conventions or documentation. This reduces implementation errors and ambiguity.

### 3. **Flexibility Within Constraints**
Cube types provide strong structural guardrails while allowing taxonomies to:
- Define custom cube types when needed
- Extend standard types with additional restrictions
- Use unrestricted dimensions where appropriate (e.g., in report cubes)

### 4. **Separation of Structure and Content**
Cube types define structural rules (what dimensions, relationships, properties are allowed) but do not dictate content (what specific concepts, members, or values appear). This separation enables structural validation without content-specific dependencies.

### 5. **Processing Optimization**
By declaring cube type explicitly, processors can:
- Select appropriate rendering algorithms
- Apply type-specific validation rules
- Optimize query execution
- Generate type-appropriate output formats

## Example: Custom Cube Type

Here's an example of defining a custom cube type for tracking customer complaints:

```json
{
  "cubeTypes": [
    {
      "name": "exp:complaintCube",
      "baseCubeType": "xbrl:eventCube",
      "cubeDimensionConstraints": {
        "allowed": [
          {
            "dimensionName": "exp:complaintDimension",
            "type": "typed",
            "dataType": "xs:token",
            "required": true
          }
        ],
        "closed": true
      },
      "cubeRelationships": {
        "required": [
          {
            "type": "xbrl:concept-refDimension",
            "source": {
              "dataType": "xs:dateTime"
            },
            "target": {
              "qname": "xbrl:period"
            }
          }
        ]
      },
      "cubeProperties": {
        "required": [
          "exp:complaintCategory",
          "exp:resolutionStatus"
        ]
      }
    }
  ]
}
```

This custom cube type:
- Extends the standard event cube
- Requires a specific complaint dimension
- Mandates date-to-period relationships
- Enforces required metadata properties for complaint categorization

## Relationship to Requirements

The cube type object directly supports several key requirements:

- **REQ-CT1**: Define structural constraints on cubes through dimension, relationship, and property restrictions
- **REQ-CT2**: Support inheritance and restriction of cube type definitions
- **REQ-CT3**: Enable validation of cube structure against declared cube type
- **REQ-CT4**: Provide standard cube types for common use cases (event, reference, time series, position, report)
- **REQ-CT5**: Allow custom cube type definitions for domain-specific needs
- **REQ-VL1**: Enable validation of dimensional consistency within cubes
- **REQ-VL2**: Verify required relationships and properties are present

## Validation Constraints

The specification defines numerous validation rules for cube type objects, including:

### Structural Constraints
- Core dimensions must be valid core dimension QNames
- No duplicate dimensions allowed
- Dimension references must resolve to valid dimension objects
- Relationship type references must resolve to valid relationship types
- Property type references must resolve to valid property types

### Type Constraint Constraints
- Data type constraints only apply to typed dimensions
- Required dimensions cannot be made optional in derived types
- Closed dimension sets cannot be opened in derived types
- Dimension additions must respect base type's closed constraint

### Inheritance Constraints
- Derived types can only restrict base type constraints
- Core dimensions in derived types must be subset of base type
- Required relationships in base type must remain in derived type
- Required properties in base type must remain in derived type
- Data types cannot be made less restrictive in derived types

These constraints ensure cube types remain logically consistent and that type hierarchies are well-formed.

## Common Use Cases

### Use Case 1: Event Tracking System
**Scenario**: Track customer service interactions as discrete events

**Solution**: Use `xbrl:eventCube` with an event dimension for interaction ID
- No period dimension (events are not periodic)
- Date concepts reference period dimension for timestamp
- Event dimension uniquely identifies each interaction

### Use Case 2: Securities Master Data
**Scenario**: Maintain reference data for financial instruments

**Solution**: Use `xbrl:referenceCube` with a security identifier dimension
- No period dimension (reference data is timeless)
- Security dimension provides unique key
- Facts describe instrument characteristics

### Use Case 3: IoT Sensor Readings
**Scenario**: Capture temperature measurements every minute

**Solution**: Use `xbrla:timeSeriesCube` with timestamp dimension
- Time dimension holds measurement timestamp
- Concept dimension for different sensor types
- Optional unit dimension for measurement units

### Use Case 4: Quarterly Financial Statements
**Scenario**: Traditional GAAP financial reporting

**Solution**: Use `xbrl:reportCube` with full core dimensions
- Period dimension for reporting period
- Entity dimension for legal entity
- Unit dimension for currency
- Optional explicit dimensions for reportable segments

## Conclusion

The cube type object is an essential architectural component of the OIM Taxonomy specification. By providing a formal mechanism for defining dimensional constraints, relationship requirements, and property specifications, cube types enable:

- **Stronger validation**: Catching structural errors early in the development cycle
- **Better semantics**: Making the intended use of cubes explicit and machine-readable
- **Format alignment**: Mapping XBRL structures to appropriate output formats
- **Extensibility**: Supporting custom use cases while maintaining interoperability
- **Processing optimization**: Enabling type-specific algorithms and renderings

The eight built-in cube types address common business reporting scenarios while the extension mechanism allows taxonomies to define specialized types for domain-specific needs. Through restriction-based inheritance, cube types maintain logical consistency while enabling incremental specialization.

Without cube types, the XBRL specification would lack a critical mechanism for enforcing data structure integrity and communicating semantic intent, significantly limiting its applicability to modern business reporting requirements.
