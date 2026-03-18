# Model Type Object - Purpose and Use Cases

## Overview

The **Model Type object** (`xbrl:modelTypeObject`) enables model authors to define custom model types that enforce specific constraints on XBRL models. A model type specifies which object types are allowed in a model, which properties can be used, and which properties are mandatory on the XBRL Model object itself.

## Purpose

The Model Type object serves several critical purposes:

1. **Enforce Model Structure**: Define what types of objects (concepts, cubes, networks, etc.) are permitted in a specific model type
2. **Mandate Required Properties**: Require specific properties to be present on the XBRL Model object (e.g., reportDate, reportType, jurisdiction)
3. **Restrict Property Usage**: Limit which properties can be used within a model type to ensure consistency and compliance
4. **Enable Regulatory Profiles**: Allow regulatory authorities to define standardized model types that filers must conform to

## Properties

The Model Type object has the following properties:

### name (required)
A QName that uniquely identifies the model type. Examples include `xbrl:taxonomy`, `xbrl:report`, or custom types like `reg:AnnualFinancialReport`.

### allowedObjects (optional)
A set of QNames representing object types that may be included in models of this type. If not specified, all object types are allowed. If specified, only the listed object types (and their descendant objects) may be used.

**Example:**
```json
"allowedObjects": [
  "xbrl:conceptObject",
  "xbrl:cubeObject",
  "xbrl:dimensionObject",
  "xbrl:domainObject",
  "xbrl:networkObject"
]
```

### allowedProperties (optional)
A set of property QNames that can be used with this model type. If not specified, any property can be used. If specified, only the listed properties are permitted.

**Example:**
```json
"allowedProperties": [
  "xbrla:balance",
  "xbrl:periodType",
  "xbrl:aggregation"
]
```

### requiredProperties (optional)
A set of property QNames that MUST be present as properties on the `xbrl:xbrlModelObject` itself. These are model-level metadata requirements.

**Example:**
```json
"requiredProperties": [
  "reg:reportDate",
  "reg:reportType",
  "reg:filingEntity",
  "reg:jurisdiction"
]
```

## Standard Model Types

The XBRL specification defines two fundamental model types:

### xbrl:taxonomy
Represents a taxonomy model - a reusable definition of concepts, dimensions, relationships, and validation rules. Taxonomies are designed to be imported by other models and do not typically contain facts.

**Characteristics:**
- Allows comprehensive object types for defining data dictionaries
- Does not require report-specific properties
- Designed for reuse across multiple reports

### xbrl:report
Represents an instance report - a specific submission containing facts, dimensions, and data. Reports typically import taxonomies and add fact data.

**Characteristics:**
- Allows fact objects and fact-related structures
- May require report metadata properties (filing date, period, entity, etc.)
- Represents a point-in-time data submission

## Use Cases

### Use Case 1: Regulatory Financial Filing Requirements

**Scenario**: A securities regulator requires all annual financial reports to include specific metadata and follow a standardized structure.

**Solution**: Define a `reg:AnnualFinancialReport` model type that:

```json
{
  "name": "reg:AnnualFinancialReport",
  "requiredProperties": [
    "reg:reportDate",
    "reg:fiscalYearEnd",
    "reg:reportingEntity",
    "reg:auditorName",
    "reg:filingDate",
    "reg:reportCurrency",
    "reg:accountingStandard"
  ],
  "allowedObjects": [
    "xbrl:conceptObject",
    "xbrl:factObject",
    "xbrl:cubeObject",
    "xbrl:dimensionObject",
    "xbrl:footnoteObject",
    "xbrl:networkObject"
  ]
}
```

**Benefits:**
- **Automated Validation**: Processors automatically verify that all required metadata is present
- **Consistency**: All annual reports follow the same structure and include the same metadata
- **Auditability**: Clear traceability of report metadata for regulatory review
- **Interoperability**: Standardized metadata enables automated processing and analysis

**Implementation:**
```json
{
  "documentInfo": {
    "documentType": "https://xbrl.org/2026/model",
    "modelType": "reg:AnnualFinancialReport"
  },
  "xbrlModel": {
    "name": "company:AnnualReport2024",
    "properties": [
      {"property": "reg:reportDate", "value": "2024-12-31"},
      {"property": "reg:fiscalYearEnd", "value": "2024-12-31"},
      {"property": "reg:reportingEntity", "value": "http://www.sec.gov/CIK:0001234567"},
      {"property": "reg:auditorName", "value": "KPMG LLP"},
      {"property": "reg:filingDate", "value": "2025-02-28"},
      {"property": "reg:reportCurrency", "value": "iso4217:USD"},
      {"property": "reg:accountingStandard", "value": "US-GAAP"}
    ]
  }
}
```

---

### Use Case 2: Statistical Reporting Framework

**Scenario**: A central bank collects monthly statistical reports from financial institutions. These reports must be concise, focused only on specific metrics, and exclude certain types of narrative content.

**Solution**: Define a `cb:MonthlyStatisticalReport` model type that:

```json
{
  "name": "cb:MonthlyStatisticalReport",
  "requiredProperties": [
    "cb:reportPeriod",
    "cb:institutionCode",
    "cb:reportType",
    "cb:submissionDate"
  ],
  "allowedObjects": [
    "xbrl:conceptObject",
    "xbrl:factObject",
    "xbrl:dimensionObject",
    "xbrl:cubeObject"
  ],
  "allowedProperties": [
    "xbrl:periodType",
    "xbrl:aggregation",
    "cb:reportingCategory"
  ]
}
```

**Key Restrictions:**
- **No footnotes**: `xbrl:footnoteObject` is not in allowedObjects
- **No references**: `xbrl:referenceObject` is not in allowedObjects
- **Limited properties**: Only specific properties relevant to statistical data are allowed

**Benefits:**
- **Focused Submissions**: Institutions cannot include extraneous narrative content
- **Standardized Processing**: All submissions follow the same structure
- **Reduced Validation Complexity**: Simpler model type means faster validation
- **Data Quality**: Required properties ensure complete metadata

**Example Report:**
```json
{
  "documentInfo": {
    "documentType": "https://xbrl.org/2026/model",
    "modelType": "cb:MonthlyStatisticalReport"
  },
  "xbrlModel": {
    "name": "bank:StatsReport202401",
    "properties": [
      {"property": "cb:reportPeriod", "value": "2024-01"},
      {"property": "cb:institutionCode", "value": "BANK001"},
      {"property": "cb:reportType", "value": "LiquidityMetrics"},
      {"property": "cb:submissionDate", "value": "2024-02-15"}
    ],
    "facts": [
      {
        "name": "bank:fp_f1",
        "factValues": [{"name": "bank:f1", "value": 1500000000}],
        "factDimensions": {
          "xbrl:concept": "cb:TotalLiquidAssets",
          "xbrl:period": "2024-01-31",
          "xbrl:entity": "BANK001",
          "xbrl:unit": "iso4217:USD"
        }
      }
    ]
  }
}
```

---

### Use Case 3: Sustainability Reporting Standard

**Scenario**: An environmental agency establishes a sustainability reporting framework that requires specific environmental, social, and governance (ESG) metadata and restricts the types of data that can be reported.

**Solution**: Define an `esg:SustainabilityReport` model type that:

```json
{
  "name": "esg:SustainabilityReport",
  "requiredProperties": [
    "esg:reportingPeriod",
    "esg:reportingEntity",
    "esg:reportingFramework",
    "esg:assuranceProvider",
    "esg:assuranceLevel",
    "esg:publicationDate",
    "esg:reportBoundary",
    "esg:complianceStandard"
  ],
  "allowedObjects": [
    "xbrl:conceptObject",
    "xbrl:factObject",
    "xbrl:cubeObject",
    "xbrl:dimensionObject",
    "xbrl:domainObject",
    "xbrl:networkObject",
    "xbrl:footnoteObject"
  ],
  "allowedProperties": [
    "xbrl:periodType",
    "xbrl:aggregation",
    "esg:emissionScope",
    "esg:dataQuality",
    "esg:verificationStatus"
  ]
}
```

**Benefits:**
- **Mandatory Assurance Information**: Requires disclosure of assurance provider and level
- **Framework Identification**: Clear identification of which ESG framework is used (GRI, SASB, TCFD, etc.)
- **Boundary Clarity**: Explicit statement of organizational and operational boundaries
- **Custom Properties**: ESG-specific properties like emission scopes and data quality indicators

**Example Report:**
```json
{
  "documentInfo": {
    "documentType": "https://xbrl.org/2026/model",
    "modelType": "esg:SustainabilityReport"
  },
  "xbrlModel": {
    "name": "company:ESGReport2024",
    "properties": [
      {"property": "esg:reportingPeriod", "value": "2024-01-01/2024-12-31"},
      {"property": "esg:reportingEntity", "value": "company:Corp"},
      {"property": "esg:reportingFramework", "value": "GRI:2021"},
      {"property": "esg:assuranceProvider", "value": "EY"},
      {"property": "esg:assuranceLevel", "value": "Limited"},
      {"property": "esg:publicationDate", "value": "2025-03-31"},
      {"property": "esg:reportBoundary", "value": "Consolidated operations"},
      {"property": "esg:complianceStandard", "value": "TCFD"}
    ],
    "facts": [
      {
        "name": "company:fp_ghg1",
        "factValues": [
          {
            "name": "company:ghg1", 
            "value": 125000
          }
        ],
        "factDimensions": {
          "xbrl:concept": "esg:GHGEmissions",
          "xbrl:period": "2024-01-01/2024-12-31",
          "xbrl:entity": "company:Corp",
          "xbrl:unit": "utr:tCO2e",
          "esg:EmissionScope": "esg:Scope1"
        },
        "properties": [
          {"property": "esg:dataQuality", "value": "Measured"},
          {"property": "esg:verificationStatus", "value": "Verified"}
        ]
      }
    ]
  }
}
```

---

## How Model Types Are Used

### In the Document Info

The `modelType` property in `documentInfo` declares which model type the document conforms to:

```json
{
  "documentInfo": {
    "documentType": "https://xbrl.org/2026/model",
    "modelType": "reg:AnnualFinancialReport"
  }
}
```

### Validation Process

When a processor loads a model with a declared model type:

1. **Locate Model Type Definition**: Find the modelTypeObject referenced by the QName
2. **Validate Required Properties**: Check that all properties in `requiredProperties` are present on the xbrlModelObject
3. **Validate Allowed Objects**: Verify that only object types in `allowedObjects` (or their descendants) are used
4. **Validate Allowed Properties**: Ensure only properties in `allowedProperties` are used (if specified)
5. **Report Errors**: Generate validation errors for any violations

### Error Reporting

**Missing Required Property:**
```
Error: oimte:missingRequiredModelTypeProperty
Model type 'reg:AnnualFinancialReport' requires property 'reg:reportDate' 
but it is not present on the XBRL Model object.
```

**Disallowed Object Type:**
```
Error: oimte:disallowedObjectModelType
Model type 'cb:MonthlyStatisticalReport' does not allow objects of type 
'xbrl:footnoteObject' but footnote 'bank:fn1' is present in the model.
```

## Design Considerations

### Inheritance
Model types can reference other model types through imports, allowing hierarchical definitions. For example, `reg:QuarterlyReport` might be a specialization of `xbrl:report`.

### Extensibility
Regulators can define domain-specific model types without modifying the core XBRL specification, ensuring backward compatibility and flexibility.

### Constraints Apply to Model Only
Model type constraints only apply to objects defined directly in the model, not to imported taxonomies. This allows models to import comprehensive taxonomies while restricting what can be defined locally.

### Required Properties on XBRL Model Object
The `requiredProperties` constraint applies specifically to the `xbrl:xbrlModelObject` itself (the root model object), not to individual concepts, facts, or other objects. This ensures model-level metadata is always present.

## Conclusion

The Model Type object provides a powerful mechanism for defining standardized model profiles that enforce structural and metadata requirements. By enabling regulators and standards bodies to codify their requirements as model types, the XBRL specification supports diverse use cases while maintaining consistent validation and processing semantics. The three standard model types - `xbrl:taxonomy` and `xbrl:report` - provide foundational profiles, while custom model types enable domain-specific requirements for financial reporting, statistical submissions, sustainability reporting, and other specialized applications.
