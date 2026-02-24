# Recursive Import Algorithm - Technical Details

## Algorithm Overview

The recursive import implementation uses a **breadth-first queue-based approach** to load and merge taxonomies at any depth level.

## Key Components

### 1. Import Queue
```javascript
const importQueue = [...taxonomyData.taxonomy.importedTaxonomies];
```
- Initialized with direct imports from main taxonomy
- Dynamically grows as nested imports are discovered
- Processes imports in breadth-first order

### 2. Loaded Taxonomies Tracker
```javascript
const loadedTaxonomies = new Set([currentTaxonomyName]);
```
- Tracks taxonomy names that have been loaded
- Prevents duplicate loading
- Protects against circular dependencies

### 3. Processing Loop
```javascript
while (importQueue.length > 0) {
    const importSpec = importQueue.shift();
    // Process import...
    // Add nested imports to queue...
}
```

## Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ START: Load Main Taxonomy (extension.json)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ Initialize:                                                     │
│ - loadedTaxonomies = Set(['exp_ext:ExtensionTaxonomy'])       │
│ - importQueue = [{ taxonomyName: 'exp:SampleTaxonomy' }]      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ ITERATION 1: Process 'exp:SampleTaxonomy'                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. Extract prefix: 'exp'                                       │
│ 2. Lookup in urlMapping: ['exampleTaxonomy.json']             │
│ 3. Load file: ./examples/exampleTaxonomy.json                 │
│ 4. Check for nested imports: Found 1                           │
│    → Add 'dei:SEC-dei-taxonomy' to importQueue                 │
│ 5. Merge arrays: concepts, labels, domains, networks, etc.     │
│ 6. Add 'exp:SampleTaxonomy' to loadedTaxonomies              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ importQueue now = [{ taxonomyName: 'dei:SEC-dei-taxonomy' }]  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ ITERATION 2: Process 'dei:SEC-dei-taxonomy'                    │
├─────────────────────────────────────────────────────────────────┤
│ 1. Extract prefix: 'dei'                                       │
│ 2. Lookup in urlMapping: ['dei-taxonomy.json']                │
│ 3. Load file: ./examples/dei-taxonomy.json                    │
│ 4. Check for nested imports: Found 0 (or more...)             │
│ 5. Merge arrays: concepts, labels, etc.                       │
│ 6. Add 'dei:SEC-dei-taxonomy' to loadedTaxonomies            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ importQueue now = [] (empty)                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: Process Extensions (NEW!)                              │
├─────────────────────────────────────────────────────────────────┤
│ 1. Scan domains for extendTargetName (without name)           │
│    → Found: { extendTargetName: "exp:DomainOfCountries" }     │
│ 2. Find target: "exp:DomainOfCountries" in merged taxonomy    │
│ 3. Merge relationships into target domain                      │
│ 4. Remove extension object from domains array                  │
│                                                                 │
│ 5. Scan networks for extendTargetName (without name)          │
│    → Found: { extendTargetName: "exp:Network2" }              │
│ 6. Find target: "exp:Network2" in merged taxonomy             │
│ 7. Merge relationships into target network                     │
│ 8. Remove extension object from networks array                 │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ END: All imports processed and extensions applied               │
│ Loaded: exp_ext:ExtensionTaxonomy,                            │
│         exp:SampleTaxonomy,                                     │
│         dei:SEC-dei-taxonomy                                    │
│ Extended: exp:DomainOfCountries, exp:Network2                 │
└─────────────────────────────────────────────────────────────────┘
```

## Circular Dependency Handling

### Example Scenario
```
A imports B
B imports C
C imports A  (circular!)
```

### How It's Handled
```
Step 1: Load A
  - Add A to loadedTaxonomies
  - Queue B for loading

Step 2: Load B
  - Add B to loadedTaxonomies
  - Queue C for loading

Step 3: Load C
  - Add C to loadedTaxonomies
  - Try to queue A
  - CHECK: Is A in loadedTaxonomies? YES!
  - SKIP: Don't add A to queue
  - LOG: "Skipping A - already loaded"

Step 4: Queue is empty, done
```

### Protection Code
```javascript
if (loadedTaxonomies.has(taxonomyName)) {
    console.log(`Skipping ${taxonomyName} - already loaded`);
    continue;
}
```

## Multi-File Support

A single prefix can map to multiple files:

```json
{
  "urlMapping": {
    "exp": [
      "base-concepts.json",
      "extended-concepts.json",
      "domains.json"
    ]
  }
}
```

### Processing Flow
```
For each file in urlMapping['exp']:
  1. Load file
  2. Check if taxonomy name matches
  3. Discover nested imports (add to queue)
  4. Merge taxonomy objects
```

All files are processed sequentially, but imports are discovered and queued as encountered.

## Extension Processing

After all imports are loaded and merged, the viewer processes **extension objects** that use `extendTargetName` to add relationships to existing domains and networks.

### What Are Extensions?

Extensions are domain or network objects that:
1. Have an `extendTargetName` property (instead of `name`)
2. Do NOT have a `name` property
3. Contain relationships to be added to an existing target

### Extension Processing Algorithm

```javascript
function processExtensions() {
    // Process domains
    for each domain in taxonomy.domains:
        if domain.extendTargetName AND NOT domain.name:
            targetDomain = findDomain(domain.extendTargetName)
            
            if targetDomain exists:
                // Merge relationships
                targetDomain.relationships += domain.relationships
                
                // Mark extension for removal
                markForRemoval(domain)
            else:
                warn("Target not found, keeping extension")
    
    // Remove marked extensions
    removeMarkedDomains()
    
    // Process networks (same logic)
    for each network in taxonomy.networks:
        if network.extendTargetName AND NOT network.name:
            targetNetwork = findNetwork(network.extendTargetName)
            
            if targetNetwork exists:
                // Merge relationships
                targetNetwork.relationships += network.relationships
                
                // Merge roots if present
                targetNetwork.roots += network.roots
                
                // Mark extension for removal
                markForRemoval(network)
            else:
                warn("Target not found, keeping extension")
    
    // Remove marked extensions
    removeMarkedNetworks()
}
```

### Extension Example Flow

#### Initial State (After Import)

**Main Taxonomy (extension.json):**
```json
{
  "domains": [
    {
      "extendTargetName": "exp:DomainOfCountries",
      "relationships": [
        { "source": "exp:DomainOfCountriesRoot", "target": "exp:Country_Mexico", "order": 3 }
      ]
    }
  ]
}
```

**Imported Taxonomy (exampleTaxonomy.json):**
```json
{
  "domains": [
    {
      "name": "exp:DomainOfCountries",
      "root": "exp:DomainOfCountriesRoot",
      "relationships": [
        { "source": "exp:DomainOfCountriesRoot", "target": "exp:Country_USA", "order": 1 },
        { "source": "exp:DomainOfCountriesRoot", "target": "exp:Country_Canada", "order": 2 }
      ]
    }
  ]
}
```

**Merged (Before Extension Processing):**
```json
{
  "domains": [
    {
      "name": "exp:DomainOfCountries",
      "root": "exp:DomainOfCountriesRoot",
      "relationships": [
        { "source": "...", "target": "exp:Country_USA", "order": 1 },
        { "source": "...", "target": "exp:Country_Canada", "order": 2 }
      ]
    },
    {
      "extendTargetName": "exp:DomainOfCountries",
      "relationships": [
        { "source": "...", "target": "exp:Country_Mexico", "order": 3 }
      ]
    }
  ]
}
```

#### Processing Steps

```
1. Identify extension:
   → domain.extendTargetName = "exp:DomainOfCountries"
   → domain.name = undefined (not present)
   → This is an extension!

2. Find target:
   → Search domains for name = "exp:DomainOfCountries"
   → Target found at index 0

3. Merge relationships:
   → targetDomain.relationships = [USA, Canada]
   → extension.relationships = [Mexico]
   → Merge: targetDomain.relationships = [USA, Canada, Mexico]

4. Mark for removal:
   → extensionsToRemove = [1] (index of extension object)

5. Remove extensions:
   → domains.splice(1, 1)
   → Extension object removed
```

#### Final State (After Extension Processing)

```json
{
  "domains": [
    {
      "name": "exp:DomainOfCountries",
      "root": "exp:DomainOfCountriesRoot",
      "relationships": [
        { "source": "...", "target": "exp:Country_USA", "order": 1 },
        { "source": "...", "target": "exp:Country_Canada", "order": 2 },
        { "source": "...", "target": "exp:Country_Mexico", "order": 3 }
      ]
    }
  ]
}
```

### Why Extensions Are Removed

Extensions are **not standalone objects**—they are modifications to existing objects:

1. **No Name**: Extensions don't have a `name` property, so they can't be referenced
2. **Incomplete Definition**: They typically only contain relationships, not a full definition
3. **Cleaner Model**: After merging, keeping them would create duplicate/partial entries
4. **Semantic Correctness**: The extension's purpose is fulfilled once merged

### Extension Properties Merged

#### Domains
- `relationships[]` - Added to target domain's relationships

#### Networks
- `relationships[]` - Added to target network's relationships
- `roots[]` - Added to target network's roots (if present)
- Additional properties can be added as needed

### Error Handling

#### Target Not Found

If the target domain/network doesn't exist:

```
Console: "Target domain exp:DomainOfCountries not found, extension will be kept"
```

The extension object is **kept** in the array so it can be:
- Debugged in the viewer
- Used if the target is loaded later
- Identified as a potential error

#### Multiple Extensions to Same Target

Multiple extensions can target the same domain/network:

```json
{
  "domains": [
    { "extendTargetName": "exp:Domain1", "relationships": [...] },
    { "extendTargetName": "exp:Domain1", "relationships": [...] }
  ]
}
```

All relationships are merged in order:
```
Target = [original relationships]
After extension 1: Target = [original, extension1 rels]
After extension 2: Target = [original, extension1 rels, extension2 rels]
```

### Processing Order

Extensions are processed **after** all imports are loaded:

```
1. Load main taxonomy
2. Process importedTaxonomies (recursive)
3. Merge all imported objects
4. Process extensions ← Extensions applied here
5. Display in viewer
```

This ensures:
- All target objects are available
- Extensions can reference imported objects
- Nested imports are fully resolved first

### Console Logging

```
Processing extensions...
Found domain extension targeting: exp:DomainOfCountries
  - Added 1 relationships to domain exp:DomainOfCountries
Found network extension targeting: exp:Network2
  - Added 1 relationships to network exp:Network2
Removed 1 domain extension(s)
Removed 1 network extension(s)
Extension processing complete
```

### Use Cases

#### 1. Adding Enum Members
```json
{
  "domains": [
    {
      "extendTargetName": "gaap:ProductCategories",
      "relationships": [
        { "source": "gaap:ProductCategoriesRoot", "target": "myco:CustomCategory" }
      ]
    }
  ]
}
```

#### 2. Extending Presentation Networks
```json
{
  "networks": [
    {
      "extendTargetName": "gaap:BalanceSheet",
      "relationships": [
        { "source": "gaap:Assets", "target": "myco:CustomAsset" }
      ]
    }
  ]
}
```

#### 3. Adding Calculation Relationships
```json
{
  "networks": [
    {
      "extendTargetName": "gaap:IncomeCalculation",
      "relationships": [
        {
          "source": "gaap:Revenue",
          "target": "myco:RevenueAdjustment",
          "properties": [{ "property": "xbrl:weight", "value": "1" }]
        }
      ]
    }
  ]
}
```

## Array Merging Strategy

### Simple Concatenation
```javascript
taxonomyData.taxonomy[prop] = 
    taxonomyData.taxonomy[prop].concat(importedTaxonomy.taxonomy[prop]);
```

### Properties Merged
- ✓ concepts
- ✓ members
- ✓ dimensions
- ✓ abstracts
- ✓ entities
- ✓ units
- ✓ groups
- ✓ groupContents
- ✓ domains
- ✓ domainRoots
- ✓ networks
- ✓ cubes
- ✓ labels
- ✓ references
- ✓ facts
- ✓ dataTypes
- ✓ propertyTypes
- ✓ relationshipTypes
- ✓ cubeTypes
- ✓ labelTypes
- ✓ referenceTypes

### Merge Order
Objects are merged in the order they're loaded:
1. Main taxonomy objects (from currently opened file)
2. First import's objects
3. Nested imports from first import
4. Second import's objects
5. Nested imports from second import
6. ... and so on

This means:
- **Later imports can override earlier ones** (if viewer uses last-wins logic)
- **Labels and references are additive** (all are kept)

## Performance Considerations

### Breadth-First vs Depth-First

**Current: Breadth-First**
```
A imports [B, C]
B imports [D]
C imports [E]

Load order: A → B → C → D → E
```

**Alternative: Depth-First** (not implemented)
```
A imports [B, C]
B imports [D]
C imports [E]

Load order: A → B → D → C → E
```

Breadth-first was chosen because:
- Simpler to implement with a queue
- More predictable merge order
- Easier to debug (imports at same level load together)

### Optimization Opportunities

1. **Parallel Loading**: Could load multiple imports concurrently
   ```javascript
   // Current: Sequential
   for (const file of files) { await fetch(file); }
   
   // Potential: Parallel
   await Promise.all(files.map(file => fetch(file)));
   ```

2. **Caching**: Could cache loaded taxonomies across different loads
   ```javascript
   const taxonomyCache = new Map();
   if (taxonomyCache.has(taxonomyName)) {
       return taxonomyCache.get(taxonomyName);
   }
   ```

3. **Lazy Loading**: Could defer loading until objects are actually accessed

## Error Recovery

### Graceful Degradation
```javascript
try {
    // Load and merge taxonomy
} catch (error) {
    console.error(`Error loading ${taxonomyName}:`, error);
    // Continue with next import
}
```

Each import failure is isolated:
- Error logged to console
- Import skipped
- Other imports continue normally
- Main taxonomy still displays

### Error Types Handled
1. **Network Errors**: File not found, network timeout
2. **Parse Errors**: Invalid JSON format
3. **Schema Errors**: Missing required fields
4. **Reference Errors**: Invalid taxonomy name format

## Console Output Example

```
Starting merge of imported taxonomies...
Loading imported taxonomy from: ./examples/exampleTaxonomy.json
Found 1 nested imports in exp:SampleTaxonomy
  - Queued nested import: dei:SEC-dei-taxonomy
Merged 25 concepts from exp:SampleTaxonomy
Merged 48 labels from exp:SampleTaxonomy
Merged 12 domains from exp:SampleTaxonomy
Merged 8 networks from exp:SampleTaxonomy
Loading imported taxonomy from: ./examples/dei-taxonomy.json
Merged 15 concepts from dei:SEC-dei-taxonomy
Merged 30 labels from dei:SEC-dei-taxonomy
Imported taxonomies merge complete. Loaded taxonomies: 
  exp_ext:ExtensionTaxonomy, exp:SampleTaxonomy, dei:SEC-dei-taxonomy
```

## Testing Recursive Imports

### Test Case 1: Linear Chain
```
A → B → C → D
```
Expected: All 4 loaded in order

### Test Case 2: Diamond Dependency
```
    A
   / \
  B   C
   \ /
    D
```
Expected: A → B → C → D (D loaded once)

### Test Case 3: Circular Reference
```
A → B → C → A
```
Expected: A → B → C (A skipped on second encounter)

### Test Case 4: Missing Import
```
A → B (missing) → continue
```
Expected: Warning logged, A still loads

## Future Enhancements

### 1. Import Versioning
```json
{
  "importedTaxonomies": [
    {
      "taxonomyName": "exp:SampleTaxonomy",
      "version": "2.0.0"
    }
  ]
}
```

### 2. Selective Imports
```json
{
  "importedTaxonomies": [
    {
      "taxonomyName": "exp:SampleTaxonomy",
      "include": ["concepts", "labels"],
      "exclude": ["networks"]
    }
  ]
}
```

### 3. Import Metadata
Track which objects came from which imports for debugging:
```javascript
{
  conceptName: "exp:Revenue",
  sourceFile: "exampleTaxonomy.json",
  importChain: ["extension.json", "exampleTaxonomy.json"]
}
```
