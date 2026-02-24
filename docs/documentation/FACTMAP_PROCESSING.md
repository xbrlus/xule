# Fact Map Processing Model

## Overview

This document describes the processing model for converting facts from various source formats into the XBRL Model format using Fact Map objects. Three specific mappings are covered:

1. **XBRL 2.1 to XBRL Model** (`xbrl:XBRL21XML`)
2. **OIM-JSON to XBRL Model** (`xbrl:OIM-JSON`)
3. **CSV/Tabular to XBRL Model** (custom `tableTemplate`)

Each mapping follows a general processing pattern but with format-specific adaptations.

---

## General Processing Model

All fact map processing follows this high-level algorithm:

```
1. Load and parse source data in native format
2. Identify fact candidates in source data
3. Extract dimension values for each fact
4. Apply transformations and type conversions
5. Generate Fact objects in XBRL Model format
6. Generate FactValue objects for each fact
7. Generate FactDimension objects with dimension values
8. Handle special cases (footnotes, nil values, etc.)
9. Validate generated objects against taxonomy constraints
10. Return collection of Fact objects
```

---

## 1. XBRL 2.1 to XBRL Model (`xbrl:XBRL21XML`)

### Purpose

The `xbrl:XBRL21XML` fact map enables processing of traditional XBRL 2.1 instance documents, converting them into the XBRL Model format while preserving all semantic information.

### Source Format

XBRL 2.1 instances are XML documents containing:
- Fact elements (items in the `xbrli:item` substitution group)
- Context elements defining dimensional information
- Unit elements defining measurement units
- Footnote links with footnote relationships

### Processing Steps

#### Step 1: Parse XBRL 2.1 Instance Document

```xml
<xbrl xmlns="http://www.xbrl.org/2003/instance"
      xmlns:us-gaap="http://fasb.org/us-gaap/2024">
  <context id="c1">
    <entity>
      <identifier scheme="http://www.sec.gov/CIK">0001234567</identifier>
    </entity>
    <period>
      <instant>2024-12-31</instant>
    </period>
  </context>
  
  <unit id="USD">
    <measure>iso4217:USD</measure>
  </unit>
  
  <us-gaap:Cash contextRef="c1" unitRef="USD" decimals="-3" id="f1">
    1000000
  </us-gaap:Cash>
</xbrl>
```

#### Step 2: Identify Fact Elements

- Locate all elements in the `xbrli:item` substitution group
- Each fact element becomes a candidate for conversion

#### Step 3: Extract Dimension Values

For each fact element:

**Concept Dimension:**
- Extract from element QName (e.g., `us-gaap:Cash`)
- Map to `xbrl:concept` dimension value

**Period Dimension:**
- Resolve `@contextRef` to context element
- Extract period from `<period>` element (instant or duration)
- Map to `xbrl:period` dimension value
- Convert to ISO 8601 format (instant: `2024-12-31`, duration: `2024-01-01/2024-12-31`)

**Entity Dimension:**
- Resolve `@contextRef` to context element
- Extract entity identifier and scheme
- Map to `xbrl:entity` dimension value
- Format as scheme:identifier (e.g., `http://www.sec.gov/CIK:0001234567`)

**Unit Dimension:**
- Resolve `@unitRef` to unit element (if present)
- Extract measure(s) from unit definition
- Map to `xbrl:unit` dimension value
- For divide units: format as numerator/denominator

**Language Dimension:**
- Extract from `@xml:lang` attribute (if present)
- Map to `xbrl:language` dimension value

**Taxonomy-Defined Dimensions:**
- Extract from `<xbrli:segment>` or `<xbrli:scenario>` in context
- For explicit dimensions: extract member QName
- For typed dimensions: extract typed value
- Map to corresponding dimension QName

#### Step 4: Generate SQNames for Facts and FactValues

**FactValue SQName:**
- If `@id` attribute present: use as local name
- If no `@id`: generate ID using algorithm from XBRL XML mapping spec
  - Based on position in document, element name, and context
- Namespace: use `documentNamespace` from model's documentInfo

**Fact SQName:**
- Derive from FactValue SQName
- Prefix local name with `fp-` (fact position)
- Example: if FactValue is `ns:f1`, Fact is `ns:fp-f1`

#### Step 5: Extract Fact Value and Precision

**Value:**
- Extract text content of fact element
- Trim whitespace
- For nil facts: value is `null`, add `xbrli:nil` property with value `true`

**Decimals:**
- If `@decimals` attribute present: use directly
- If `@precision` attribute present: convert to decimals equivalent
  - Precision P with value V: decimals = P - floor(log10(|V|)) - 1
- If neither present: decimals is "infinity" (INF)
- If decimals="INF": store as special "infinity" value

#### Step 6: Handle Footnotes

**Locate Footnote Links:**
```xml
<link:footnoteLink xmlns:link="http://www.xbrl.org/2003/linkbase">
  <link:loc xlink:href="#f1" xlink:label="f1_loc"/>
  <link:footnote xlink:label="fn1" xml:lang="en">
    This represents cash and cash equivalents.
  </link:footnote>
  <link:footnoteArc xlink:from="f1_loc" xlink:to="fn1" xlink:arcrole="http://www.xbrl.org/2003/arcrole/fact-footnote"/>
</link:footnoteLink>
```

**Create Footnote Objects:**
- Each `<link:footnote>` becomes a Footnote object
- Extract language from `@xml:lang`
- Extract content from element text

**Generate Footnote SQName:**
- Base on related fact's `@id` (or generated ID)
- Prefix with `fn_`
- If multiple footnotes for same fact: suffix with `_1`, `_2`, etc.
- Example: fact `f1` → footnote `fn_f1`, `fn_f1_1`, `fn_f1_2`

**Create Fact-Footnote Relationships:**
- For each `<link:footnoteArc>`:
  - Extract extended link role
  - Extract arcrole
- Create relationship in `xbrl:fact-footnote-network`
- Group by unique (linkrole, arcrole) combination

#### Step 7: Generate XBRL Model Objects

```json
{
  "facts": [
    {
      "name": "ns:fp-f1",
      "factValues": [
        {
          "name": "ns:f1",
          "value": 1000000,
          "decimals": -3
        }
      ],
      "factDimensions": {
        "xbrl:concept": "us-gaap:Cash",
        "xbrl:period": "2024-12-31",
        "xbrl:entity": "http://www.sec.gov/CIK:0001234567",
        "xbrl:unit": "iso4217:USD"
      }
    }
  ],
  "footnotes": [
    {
      "name": "ns:fn_f1",
      "content": "This represents cash and cash equivalents.",
      "language": "en"
    }
  ],
  "networks": [
    {
      "name": "xbrl:fact-footnote-network",
      "relationshipTypeName": "xbrl:fact-footnote",
      "relationships": [
        {
          "source": "ns:fp-f1",
          "target": "ns:fn_f1"
        }
      ]
    }
  ]
}
```

#### Step 8: Validate and Error Handling

- Check for unsupported features per XBRL XML mapping spec
- Validate that all contexts are defined
- Validate that all units are defined
- Ensure dimension values are valid per taxonomy
- Report errors for malformed facts

---

## 2. OIM-JSON to XBRL Model (`xbrl:OIM-JSON`)

### Purpose

The `xbrl:OIM-JSON` fact map processes OIM-JSON format reports, converting them into the XBRL Model format while maintaining consistency with the OIM specification.

### Source Format

OIM-JSON reports are JSON documents with:
- documentInfo section with metadata
- facts object with fact definitions
- Optional footnotes as facts with concept=`xbrl:note`

### Processing Steps

#### Step 1: Parse OIM-JSON Document

```json
{
  "documentInfo": {
    "documentType": "https://xbrl.org/2021/xbrl-json",
    "taxonomy": ["https://example.com/taxonomy.json"],
    "namespaces": {
      "us-gaap": "http://fasb.org/us-gaap/2024",
      "iso4217": "http://www.xbrl.org/2003/iso4217"
    }
  },
  "facts": {
    "f1": {
      "value": 1000000,
      "decimals": -3,
      "dimensions": {
        "concept": "us-gaap:Cash",
        "period": "2024-12-31",
        "entity": "http://www.sec.gov/CIK:0001234567",
        "unit": "iso4217:USD"
      }
    }
  }
}
```

#### Step 2: Process Fact Objects

For each property in the `facts` object:

**Extract Fact Identifier:**
- Property name is the fact ID (e.g., `f1`)
- This becomes the local name for FactValue SQName

**Extract Fact Value:**
- From `value` property
- Handle nil: if value is `null`, set `xbrli:nil` property to `true`

**Extract Decimals:**
- From `decimals` property (if present)
- Default to "infinity" if not specified

**Extract Language:**
- From `language` property in fact object (if present)
- Maps to `xbrl:language` dimension

#### Step 3: Map Dimensions

OIM-JSON has a `dimensions` object that maps directly to FactDimensions:

| OIM-JSON Dimension | XBRL Model Dimension |
|-------------------|---------------------|
| `dimensions.concept` | `xbrl:concept` |
| `dimensions.period` | `xbrl:period` |
| `dimensions.unit` | `xbrl:unit` |
| `dimensions.entity` | `xbrl:entity` |
| `dimensions.language` | `xbrl:language` |
| `dimensions.{custom}` | `{custom}` (taxonomy-defined) |

**Period Format:**
- Instant: ISO 8601 date (e.g., `2024-12-31`)
- Duration: ISO 8601 date/date (e.g., `2024-01-01/2024-12-31`)
- Forever: special value "forever"

**Unit Format:**
- Simple: QName (e.g., `iso4217:USD`)
- Divide: numerator/denominator (e.g., `iso4217:USD/xbrli:shares`)

#### Step 4: Handle Footnotes

Facts with `dimensions.concept = "xbrl:note"` are converted to Footnote objects:

**Extract Footnote Properties:**
- `dimensions.noteId` → Footnote `name`
- `dimensions.language` → Footnote `language`
- `value` → Footnote `content`

**Example:**
```json
{
  "fn1": {
    "value": "This is a footnote.",
    "dimensions": {
      "concept": "xbrl:note",
      "noteId": "n1",
      "language": "en"
    }
  }
}
```

Becomes:
```json
{
  "footnotes": [
    {
      "name": "n1",
      "content": "This is a footnote.",
      "language": "en"
    }
  ]
}
```

#### Step 5: Generate SQNames

**FactValue SQName:**
- Use fact ID from OIM-JSON as local name
- Namespace from `documentNamespace` in model's documentInfo

**Fact SQName:**
- Prefix fact ID with `fp-`
- Same namespace as FactValue

#### Step 6: Generate XBRL Model Objects

```json
{
  "facts": [
    {
      "name": "ns:fp-f1",
      "factValues": [
        {
          "name": "ns:f1",
          "value": 1000000,
          "decimals": -3
        }
      ],
      "factDimensions": {
        "xbrl:concept": "us-gaap:Cash",
        "xbrl:period": "2024-12-31",
        "xbrl:entity": "http://www.sec.gov/CIK:0001234567",
        "xbrl:unit": "iso4217:USD"
      }
    }
  ]
}
```

#### Step 7: Validate

- Ensure all required dimensions present
- Validate dimension values against taxonomy
- Check for duplicate fact IDs
- Verify concept QNames are defined in taxonomy

---

## 3. CSV/Tabular to XBRL Model (Custom `tableTemplate`)

### Purpose

The tableTemplate mapping enables conversion of CSV and other tabular data formats into XBRL facts, supporting custom layouts and business-specific data structures.

### Source Format

CSV files with:
- Header row with column names
- Data rows with fact values
- Optional metadata columns

### Processing Steps

#### Step 1: Define Table Template

```json
{
  "name": "ex:RevenueByRegionMap",
  "tableTemplate": {
    "rowIdColumn": "FactID",
    "columns": [
      {
        "name": "Year",
        "dataType": "xs:gYear"
      },
      {
        "name": "Region",
        "dataType": "xs:string"
      },
      {
        "name": "Revenue",
        "dataType": "xbrli:monetary"
      }
    ],
    "factDimensions": {
      "xbrl:concept": "ex:Revenue",
      "xbrl:period": "$Year",
      "xbrl:entity": "http://example.com/entity/001",
      "xbrl:unit": "iso4217:USD",
      "ex:RegionDimension": "$Region"
    }
  }
}
```

#### Step 2: Parse CSV File

```csv
FactID,Year,Region,Revenue
f1,2024,North America,1000000
f2,2024,Europe,750000
f3,2024,Asia,500000
```

Parse into table structure:
- Header row defines column names
- Each subsequent row is a data record
- Handle quoted values, escaped characters
- Detect encoding (UTF-8, etc.)

#### Step 3: Iterate Rows and Generate Facts

For each data row:

**Generate Fact ID:**
- Use value from `rowIdColumn` if defined
- Otherwise, generate sequential ID: `row1`, `row2`, etc.

**Extract Column Values:**
- For each column in template:
  - Locate matching column in CSV by name
  - Extract cell value
  - Apply dataType conversion

**Substitute Dimension Values:**
- In `factDimensions` template:
  - Replace `$ColumnName` with actual column value
  - Static values remain unchanged
- Example: `$Year` → `2024`, `$Region` → `North America`

#### Step 4: Apply Data Type Conversions

For each column:

**Date Types:**
```
"2024" → convert to xs:gYear
"2024-12-31" → convert to xs:date
"2024-01-01/2024-12-31" → parse as period duration
```

**Numeric Types:**
```
"1000000" → parse as decimal/integer
"1,000,000" → remove grouping separators, parse
"-1234.56" → handle negative values
```

**String Types:**
```
Trim whitespace
Handle special characters
Preserve case
```

**QName Types:**
```
"us-gaap:Cash" → validate prefix, resolve to full QName
```

#### Step 5: Handle Multi-Column to Dimension Mappings

Some patterns map multiple columns to a single dimension:

**Date Range from Start/End Columns:**
```json
"factDimensions": {
  "xbrl:period": {"start": "$StartDate", "end": "$EndDate"}
}
```

**Unit from Numerator/Denominator:**
```json
"xbrl:unit": {"numerator": "$UnitNum", "denominator": "$UnitDenom"}
```

#### Step 6: Apply Row Filters (Optional)

Table templates can include row filters:

```json
"rowFilter": "@Region='North America' and @Year=2024"
```

- Evaluate filter expression against row values
- Only process rows that match filter
- Use for selective fact extraction

#### Step 7: Apply Transformations (Optional)

Table templates can specify transformations:

```json
"transforms": [
  {
    "column": "Revenue",
    "transformation": "tr:num-comma-decimal"
  }
]
```

- Apply transformation to column value
- Transformations handle format conversions
- Examples: date formats, number formats, currency conversions

#### Step 8: Generate XBRL Model Facts

From CSV row:
```
f1,2024,North America,1000000
```

Generate:
```json
{
  "facts": [
    {
      "name": "ns:fp-f1",
      "factValues": [
        {
          "name": "ns:f1",
          "value": 1000000
        }
      ],
      "factDimensions": {
        "xbrl:concept": "ex:Revenue",
        "xbrl:period": "2024",
        "xbrl:entity": "http://example.com/entity/001",
        "xbrl:unit": "iso4217:USD",
        "ex:RegionDimension": "ex:NorthAmerica"
      }
    }
  ]
}
```

#### Step 9: Handle Complex Scenarios

**Multiple Facts per Row:**
If tableTemplate defines multiple fact patterns, generate multiple facts per row.

**Hierarchical Data:**
Use column groupings to represent parent-child relationships:
```
Level1,Level2,Value
Total,Revenue,5000
Total,Expenses,3000
```

**Sparse Data:**
Skip cells with empty values or generate nil facts based on configuration.

**Calculated Values:**
Apply formulas defined in tableTemplate to compute derived values.

#### Step 10: Validate Generated Facts

- Check all required dimensions are present
- Validate data types match expected types
- Ensure concept QNames exist in taxonomy
- Verify unit compatibility with concept data type
- Check period format is valid

---

## Error Handling

All fact map processors must handle errors consistently:

### Data Format Errors

- **Malformed source data**: Report parsing errors with location information
- **Invalid encoding**: Report encoding issues and expected encoding
- **Missing required elements**: Report missing contexts, units, or columns

### Validation Errors

- **Undefined concepts**: Report facts with concepts not in taxonomy
- **Invalid dimension values**: Report dimension values not in domain
- **Type mismatches**: Report value/type incompatibilities
- **Missing required dimensions**: Report facts lacking required dimensions

### Transformation Errors

- **Invalid transformations**: Report transformation failures
- **Conversion errors**: Report type conversion failures
- **Formula errors**: Report calculation errors in derived values

### Error Reporting Format

```json
{
  "errors": [
    {
      "code": "oimte:undefinedConcept",
      "message": "Concept 'ex:InvalidConcept' is not defined in the taxonomy",
      "location": {
        "factId": "f1",
        "sourceFile": "data.csv",
        "line": 2,
        "column": 3
      }
    }
  ]
}
```

---

## Performance Considerations

### Streaming Processing

For large datasets:
- Process facts in batches
- Use streaming parsers for CSV/JSON/XML
- Generate facts incrementally
- Limit memory footprint

### Caching

- Cache parsed contexts and units (XBRL 2.1)
- Cache column mappings (tableTemplate)
- Cache taxonomy lookups
- Reuse dimension value validations

### Parallelization

- Process independent facts in parallel
- Parallelize row processing for CSV
- Use multi-threaded parsers
- Batch validation operations

---

## Implementation Guidance

### XBRL 2.1 Processor

```python
def process_xbrl21(instance_doc, taxonomy):
    # Parse XML
    tree = parse_xml(instance_doc)
    
    # Extract contexts and units
    contexts = extract_contexts(tree)
    units = extract_units(tree)
    
    # Process each fact
    facts = []
    for fact_element in find_facts(tree):
        fact = create_fact_from_xbrl21(
            fact_element, contexts, units, taxonomy
        )
        facts.append(fact)
    
    # Process footnotes
    footnotes = extract_footnotes(tree)
    
    return facts, footnotes
```

### OIM-JSON Processor

```python
def process_oim_json(json_doc, taxonomy):
    # Parse JSON
    doc = json.loads(json_doc)
    
    # Process facts
    facts = []
    footnotes = []
    
    for fact_id, fact_data in doc['facts'].items():
        if fact_data['dimensions'].get('concept') == 'xbrl:note':
            footnote = create_footnote_from_oim(fact_id, fact_data)
            footnotes.append(footnote)
        else:
            fact = create_fact_from_oim(fact_id, fact_data, taxonomy)
            facts.append(fact)
    
    return facts, footnotes
```

### CSV/TableTemplate Processor

```python
def process_csv_with_template(csv_file, table_template, taxonomy):
    # Parse CSV
    reader = csv.DictReader(csv_file)
    
    # Process each row
    facts = []
    for row_num, row in enumerate(reader, start=1):
        try:
            fact = create_fact_from_row(
                row, row_num, table_template, taxonomy
            )
            facts.append(fact)
        except ValidationError as e:
            report_error(e, row_num)
    
    return facts
```

---

## Summary

The fact map processing model provides a unified approach to converting diverse data formats into the XBRL Model format:

- **XBRL 2.1**: Handles legacy XML instances with contexts, units, and footnote links
- **OIM-JSON**: Processes modern JSON reports with direct dimension mappings
- **TableTemplate**: Enables custom CSV layouts with flexible column mappings

Each processor follows similar steps (parse, extract, map, validate) but adapts to format-specific characteristics. The result is a consistent set of XBRL Model Fact objects regardless of input format, enabling unified downstream processing and validation.
