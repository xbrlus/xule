# Domain Object

## Overview

The **domain object** is a core component of the OIM Taxonomy specification that defines hierarchical structures of concepts, members, entities, or units. It serves as the mechanism for organizing dimensional values and establishing the valid members that can be used with dimensions in reporting scenarios.

## Purpose

The domain object serves several critical purposes in the OIM Taxonomy model:

### 1. **Hierarchical Structure Definition**
Domain objects define the hierarchical relationships among their members through an ordered set of relationship objects. These relationships:
- Organize members into parent-child structures
- Support multi-level hierarchies for complex classification schemes
- Enable roll-up calculations and aggregation
- Provide navigation paths through dimensional values

### 2. **Dimension Member Specification**
Domain objects specify which members are valid for use with a dimension:
- Concept domains for the concept dimension (primary items in reports)
- Taxonomy-defined dimension domains (axes like geography, product, segment)
- Entity domains for entity-specific dimensions (subsidiaries, consolidation)
- Unit domains for specialized unit hierarchies
- Enumeration domains for concepts with constrained value sets

### 3. **Reusability Across Cubes and Contexts**
A single domain object can be referenced by:
- Multiple cubes with different granularity requirements
- Extensible enumeration concepts for value constraints
- Different dimensions through a shared domain class
- Various reporting contexts without duplication

### 4. **Extension and Modularity**
Domain objects support taxonomy extension through:
- The `extendTargetName` property for adding members to existing domains
- Import mechanisms that preserve domain integrity
- Base domain and filtered domain patterns
- Controlled extensibility via the `completeDomain` flag

### 5. **Implicit Relationship Semantics**
All relationships within a domain object have an implicit domain-member relationship type, eliminating the need to:
- Define domain-member relationships separately
- Specify relationship types within domain structures
- Manage multiple relationship type definitions for similar structures

## Domain Object Types

### Explicit Domains
Explicit domains define a finite, enumerated set of valid members through relationships. These are the most common type of domain.

**Example: Geography Domain**
```json
{
  "name": "geo:GeographyDomain",
  "root": "geo:GeographyDomainClass",
  "relationships": [
    {
      "source": "geo:GeographyDomainClass",
      "target": "geo:Americas",
      "order": 1
    },
    {
      "source": "geo:Americas",
      "target": "geo:UnitedStates",
      "order": 1
    },
    {
      "source": "geo:Americas",
      "target": "geo:Canada",
      "order": 2
    },
    {
      "source": "geo:GeographyDomainClass",
      "target": "geo:EMEA",
      "order": 2
    }
  ]
}
```

### Concept Domains
Special domains using `xbrl:conceptDomain` as the root for organizing primary reporting concepts (line items).

**Example: Balance Sheet Concept Domain**
```json
{
  "name": "us-gaap:BalanceSheetConceptsDomain",
  "root": "xbrl:conceptDomain",
  "relationships": [
    {
      "source": "xbrl:conceptDomain",
      "target": "us-gaap:Assets"
    },
    {
      "source": "us-gaap:Assets",
      "target": "us-gaap:CurrentAssets"
    },
    {
      "source": "us-gaap:CurrentAssets",
      "target": "us-gaap:CashAndCashEquivalents"
    }
  ]
}
```

### Entity Domains
Domains using `xbrl:entityDomain` as the root for organizing entities (legal entities, subsidiaries, segments).

**Example: Subsidiary Domain**
```json
{
  "name": "company:SubsidiaryDomain",
  "root": "xbrl:entityDomain",
  "relationships": [
    {
      "source": "xbrl:entityDomain",
      "target": "company:ParentCompanyEntity"
    },
    {
      "source": "company:ParentCompanyEntity",
      "target": "company:SubsidiaryAEntity"
    },
    {
      "source": "company:ParentCompanyEntity",
      "target": "company:SubsidiaryBEntity"
    }
  ]
}
```

### Unit Domains
Domains using `xbrl:unitDomain` as the root for organizing units of measure.

**Example: Currency Unit Domain**
```json
{
  "name": "currency:CurrencyDomain",
  "root": "xbrl:unitDomain",
  "relationships": [
    {
      "source": "xbrl:unitDomain",
      "target": "iso4217:USD"
    },
    {
      "source": "xbrl:unitDomain",
      "target": "iso4217:EUR"
    },
    {
      "source": "xbrl:unitDomain",
      "target": "iso4217:GBP"
    }
  ]
}
```

### Enumeration Domains
Domains referenced by concept `enumerationDomain` properties to constrain concept values to specific members.

**Example: Filing Status Domain**
```json
{
  "concepts": [
    {
      "name": "tax:FilingStatus",
      "dataType": "xs:QName",
      "periodType": "duration",
      "enumerationDomain": "tax:FilingStatusDomain"
    }
  ],
  "domains": [
    {
      "name": "tax:FilingStatusDomain",
      "root": "tax:FilingStatusDomainClass",
      "relationships": [
        {
          "source": "tax:FilingStatusDomainClass",
          "target": "tax:SingleMember"
        },
        {
          "source": "tax:FilingStatusDomainClass",
          "target": "tax:MarriedFilingJointlyMember"
        },
        {
          "source": "tax:FilingStatusDomainClass",
          "target": "tax:HeadOfHouseholdMember"
        }
      ]
    }
  ]
}
```

## Domain Object Properties

### `name` (required if no `extendTargetName`)
The QName that uniquely identifies the domain object. This name is used to reference the domain from:
- Cube dimension definitions (via `cubeDimensions[].domainName`)
- Extensible enumeration concepts (via `enumerationDomain`)
- Domain filtering operations (via `baseDomain`)

### `root` (required if no `extendTargetName`)
The QName of the domain class object that serves as the root of this domain. All relationships in the domain must ultimately connect back to this root object. The root property:
- Links the domain to a domain class for compatibility checking
- Serves as the starting point for traversing domain relationships
- Groups related domains under a common classification

### `relationships` (optional)
An ordered set of relationship objects that define the hierarchical structure of the domain. Each relationship specifies:
- **source**: The parent object in the hierarchy
- **target**: The child object in the hierarchy
- **order**: The position among siblings (optional)
- **properties**: Additional relationship metadata (optional)

The relationships create a tree structure rooted at the domain class object.

### `extendTargetName` (required if no `name`)
Names the domain object that this definition extends by appending relationships to the target domain. This property:
- Enables modular domain construction across taxonomies
- Allows importing taxonomies to add members to base domains
- Cannot be used with the `name` property (mutually exclusive)
- Should not include a `root` property when extending

### `completeDomain` (optional, default: false)
A boolean flag indicating whether the domain is complete and final. When `true`:
- Extension taxonomies cannot add members to this domain
- Provides a mechanism for taxonomy authors to seal domain definitions
- Raises an error (`oimte:cannotExtendCompleteDomain`) if extension is attempted
- Default value of `false` allows extensibility

### `properties` (optional)
An ordered set of property objects for specifying additional domain metadata using custom properties defined in the taxonomy.

## Rationale for Inclusion in the Specification

The domain object addresses several critical requirements and design goals in the OIM Taxonomy model:

### 1. **Independence from Presentation**
In traditional XBRL taxonomies, dimensional hierarchies were tightly coupled to presentation linkbases and roles. The domain object provides:
- **Semantic separation**: Domain definitions are independent of how they're displayed
- **Reduced coupling**: Domains exist as first-class objects, not artifacts of presentation
- **Simplified imports**: Import domains without importing entire role hierarchies
- **Multiple presentations**: Same domain can have different presentation layouts

Example: A geography domain can be presented alphabetically in one report, by revenue contribution in another, and by regulatory region in a third, all referencing the same domain object.

### 2. **Explicit Reusability**
Domains as independent objects enable:
- **Cross-cube usage**: Same domain used in multiple cubes with different granularity
- **Taxonomy modularity**: Base taxonomies define common domains, extensions add specifics
- **Reduced redundancy**: One domain definition instead of duplicates in each role
- **Easier maintenance**: Update domain once, changes propagate everywhere it's used

Example: A single "LegalEntityDomain" can be used in consolidation cubes, segment reporting cubes, and geographic distribution cubes without duplication.

### 3. **Clear Extension Mechanism**
The `extendTargetName` property provides a controlled mechanism for:
- **Taxonomy extension**: Add jurisdiction-specific members to international domains
- **Version evolution**: Extend existing domains in new taxonomy versions
- **Namespace separation**: Extensions clearly identify what they're extending
- **Merge semantics**: Relationships are appended, preserving base domain structure

Example: A US GAAP extension can add industry-specific members to SEC-defined domains without modifying the base taxonomy.

### 4. **Implicit Relationship Semantics**
The domain object eliminates complexity by:
- **Fixed relationship type**: All domain relationships are implicitly domain-member
- **Reduced boilerplate**: No need to define or reference relationship types
- **Semantic clarity**: Purpose of relationships is unambiguous
- **Simplified processing**: Consumers know relationship semantics without checking type

This contrasts with traditional XBRL where domain-member, dimension-domain, and other relationship types required explicit definition and reference.

### 5. **Validation and Consistency**
Domain objects enable robust validation:
- **Root uniqueness**: Each domain has exactly one root (domain class object)
- **Type constraints**: Domain members must match allowed types for the domain class
- **Completeness checking**: `completeDomain` flag prevents unwanted extension
- **Hierarchy validation**: Relationships must form a valid tree structure

### 6. **Support for Multiple Use Cases**
The domain object design accommodates diverse scenarios:
- **Explicit dimensions**: Finite enumerated member sets (geography, product lines)
- **Concept organization**: Primary line items grouped hierarchically
- **Entity hierarchies**: Subsidiaries, consolidation groups, operating segments
- **Enumeration constraints**: Restricting concept values to valid choices
- **Unit organization**: Grouping related units of measure

### 7. **Dimension-Domain Separation**
Separating dimension definitions from domain definitions enables:
- **Multiple domains per dimension**: Different cubes use different member sets for same dimension
- **Dimension reuse**: Same dimension (e.g., "GeographyAxis") used with various domain granularities
- **Compatibility checking**: Domain class ensures only compatible domains used with dimension
- **Flexibility**: Change domain granularity without redefining dimension

Example: A "ProductAxis" dimension can reference "DetailedProductDomain" for detailed analysis and "ProductLineDomain" for summary reporting, both using the same dimension.

## Relationship to Domain Class Objects

Domain objects and domain class objects work together in a two-level hierarchy:

```
Domain Class Object (root)
  ↓ (referenced by domain.root)
Domain Object 1 (specific hierarchy)
  ↓ (relationships)
  └─ Member A
     └─ Member A1
     └─ Member A2
  └─ Member B

Domain Object 2 (different hierarchy, same root)
  ↓ (relationships)
  └─ Member A
  └─ Member B
     └─ Member B1
```

**Key Distinctions:**
- **Domain Class**: Classification and compatibility (what type of domain)
- **Domain Object**: Structure and content (which specific members, how organized)
- **Domain Class**: Referenced by dimensions (`domainClass` property)
- **Domain Object**: Referenced by cubes (`domainName` in cubeDimensions)

## Key Design Principles

### Single Root Requirement
Every domain must reference exactly one domain class object as its root. This ensures:
- Unambiguous starting point for hierarchy traversal
- Clear domain identity and classification
- Simplified validation (detect disconnected subgraphs)
- Consistent processing across implementations

### Implicit Domain-Member Relationships
All relationships within a domain implicitly represent domain-member relationships:
- Eliminates need to specify relationship type
- Reduces complexity for domain authors
- Ensures semantic consistency
- Simplifies consumer processing logic

### Extension Through Composition
Domain extension uses composition (adding relationships) rather than inheritance:
- `extendTargetName` appends to existing domain
- Original domain remains unchanged
- Clear audit trail of what was added
- Supports multiple extension layers

### Relationship Order Preservation
Relationships can specify explicit `order` properties:
- Preserves author's intended sequence
- Supports stable presentation across platforms
- Enables "insert before/after" extension patterns
- Allows for meaningful semantic ordering

### Validation at Multiple Levels
Domain validation occurs at several points:
- **Structure validation**: Relationships form valid tree
- **Type validation**: Members match domain class constraints
- **Completeness validation**: `completeDomain` flag enforcement
- **Reference validation**: All referenced objects exist
- **Compatibility validation**: Domain root matches dimension requirements

## Examples

### Basic Explicit Domain
```json
{
  "name": "company:ProductLineDomain",
  "root": "company:ProductLineDomainClass",
  "relationships": [
    {
      "source": "company:ProductLineDomainClass",
      "target": "company:ConsumerProductsMember",
      "order": 1
    },
    {
      "source": "company:ProductLineDomainClass",
      "target": "company:IndustrialProductsMember",
      "order": 2
    },
    {
      "source": "company:ConsumerProductsMember",
      "target": "company:ElectronicsMember",
      "order": 1
    },
    {
      "source": "company:ConsumerProductsMember",
      "target": "company:AppliancesMember",
      "order": 2
    }
  ]
}
```

### Extended Domain
**Base Taxonomy:**
```json
{
  "name": "base:IndustryDomain",
  "root": "base:IndustryDomainClass",
  "relationships": [
    {
      "source": "base:IndustryDomainClass",
      "target": "base:ManufacturingMember"
    },
    {
      "source": "base:IndustryDomainClass",
      "target": "base:ServicesMember"
    }
  ]
}
```

**Extension Taxonomy:**
```json
{
  "extendTargetName": "base:IndustryDomain",
  "relationships": [
    {
      "source": "base:ManufacturingMember",
      "target": "extension:AutomotiveManufacturingMember"
    },
    {
      "source": "base:ManufacturingMember",
      "target": "extension:ElectronicsManufacturingMember"
    }
  ]
}
```

### Complete Domain (Sealed)
```json
{
  "name": "regulatory:CountryCodeDomain",
  "root": "regulatory:CountryCodeDomainClass",
  "completeDomain": true,
  "relationships": [
    {
      "source": "regulatory:CountryCodeDomainClass",
      "target": "iso3166:US"
    },
    {
      "source": "regulatory:CountryCodeDomainClass",
      "target": "iso3166:CA"
    },
    {
      "source": "regulatory:CountryCodeDomainClass",
      "target": "iso3166:MX"
    }
  ]
}
```

## Relationship to Requirements

The domain object directly addresses several requirements from the OIM Taxonomy Requirements specification:

**REQ-DO1 - Domain object identifier**
> "The taxonomy model should define a domain as an object that can be referenced."

The domain object provides a QName identifier that can be referenced from cube dimensions, enumeration concepts, and domain extensions.

**REQ-DO2 - Domain properties**
> "The domain object should encompass all properties that define a domain of concept members."

The domain object includes all necessary properties: name, root, relationships, extension mechanism, and completeness flag.

**REQ-DO3 - Domain root restriction**
> "The domain object can only have one domain root concept."

Each domain object must reference exactly one domain class object via the `root` property, ensuring a single root.

**REQ-DO4 - Domain is the default**
> "The default value of a dimension should be the domain concept associated with the cube dimension."

The domain class referenced by the dimension serves as the default, with specific domains providing member hierarchies.

**REQ-RD1 - Define relationships in a domain**
> "Relationships should be able to be associated with a domain object and not a role."

Domain objects contain relationships directly as a property, independent of any presentation or definition roles.

## Validation Constraints

Domain objects are subject to numerous validation rules:

### Structural Constraints
- Domain class object must be used as source in at least one relationship (`oimte:missingDomainClassSource`)
- Relationships must resolve to single root object (`oimte:multipleDomainClasses`)
- Domain class object cannot be used as target (`oimte:invalidDomainClassTarget`)
- Name and extendTargetName are mutually exclusive (`oimte:invalidJSONStructure`)

### Type-Specific Constraints
For `xbrl:conceptDomain`:
- Sources must be concepts, abstracts, or the domain class (`oimte:invalidDomainObject`)
- Targets must be concepts or abstracts (`oimte:invalidDomainObject`)

For `xbrl:entityDomain`:
- Sources must be entities or the domain class (`oimte:invalidDomainObject`)
- Targets must be entities (`oimte:invalidDomainObject`)

For `xbrl:unitDomain`:
- Sources must be units or the domain class (`oimte:invalidDomainObject`)
- Targets must be units (`oimte:invalidDomainObject`)

For custom domains (not concept/entity/unit/language):
- Sources must be members or the domain class (`oimte:invalidDomainSource`)
- Targets must be members (`oimte:invalidDomainTarget`)

### Extension Constraints
- Cannot extend complete domains (`oimte:cannotExtendCompleteDomain`)
- Model taxonomies cannot use extendTargetName (`oimte:extendedTargetNameDefinedForCompiledTaxonomy`)
- Root property must reference a valid domain class object (`oimte:invalidDomainClass`)

## Common Use Cases

### 1. Organizing Reporting Line Items
Use concept domains to structure financial statement line items:
```json
{
  "name": "us-gaap:IncomeStatementDomain",
  "root": "xbrl:conceptDomain",
  "relationships": [
    {"source": "xbrl:conceptDomain", "target": "us-gaap:Revenues"},
    {"source": "us-gaap:Revenues", "target": "us-gaap:ProductRevenues"},
    {"source": "us-gaap:Revenues", "target": "us-gaap:ServiceRevenues"}
  ]
}
```

### 2. Creating Taxonomy-Defined Dimensions
Define explicit domains for axes like geography, product, segment:
```json
{
  "dimensions": [
    {"name": "company:GeographyAxis", "domainClass": "company:GeographyDomainClass"}
  ],
  "domains": [
    {
      "name": "company:GeographyDomain",
      "root": "company:GeographyDomainClass",
      "relationships": [
        {"source": "company:GeographyDomainClass", "target": "company:NorthAmericaMember"},
        {"source": "company:GeographyDomainClass", "target": "company:EuropeMember"}
      ]
    }
  ]
}
```

### 3. Constraining Enumeration Values
Limit concept values to specific enumerated choices:
```json
{
  "concepts": [
    {
      "name": "company:ReportingStandard",
      "dataType": "xs:QName",
      "periodType": "duration",
      "enumerationDomain": "company:ReportingStandardDomain"
    }
  ],
  "domains": [
    {
      "name": "company:ReportingStandardDomain",
      "root": "company:ReportingStandardDomainClass",
      "relationships": [
        {"source": "company:ReportingStandardDomainClass", "target": "company:IFRSMember"},
        {"source": "company:ReportingStandardDomainClass", "target": "company:USGAAPMember"}
      ]
    }
  ]
}
```

### 4. Organizing Entities in Consolidation
Structure entity hierarchies for consolidation reporting:
```json
{
  "domains": [
    {
      "name": "company:ConsolidationDomain",
      "root": "xbrl:entityDomain",
      "relationships": [
        {"source": "xbrl:entityDomain", "target": "company:ParentEntity"},
        {"source": "company:ParentEntity", "target": "company:SubsidiaryAEntity"},
        {"source": "company:ParentEntity", "target": "company:SubsidiaryBEntity"}
      ]
    }
  ]
}
```

## Conclusion

The domain object is essential to the OIM Taxonomy specification because it:

1. **Provides semantic independence** from presentation structures, enabling domains to be defined once and reused across multiple contexts
2. **Enables explicit reusability** through independent object identity and reference mechanisms
3. **Supports controlled extension** via the `extendTargetName` property for modular taxonomy construction
4. **Simplifies processing** through implicit domain-member relationship semantics
5. **Ensures consistency** through single-root requirements and validation constraints
6. **Accommodates diverse use cases** from concept organization to entity hierarchies to enumeration constraints

Without domain objects, the OIM Taxonomy model would lack a mechanism to define hierarchical member structures independently from their use in specific cubes or presentation contexts, forcing a return to the tightly-coupled role-based approach of traditional XBRL taxonomies.
