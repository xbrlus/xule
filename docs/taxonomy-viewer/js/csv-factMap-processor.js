/**
 * CSV FactMap Processor
 * Converts CSV data using a factMap tableTemplate into facts
 */

/**
 * Parse a single CSV line respecting quoted fields
 * @param {string} line - A single CSV line
 * @returns {Array<string>} Array of field values
 */
function parseCSVLine(line) {
    const fields = [];
    let field = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        const nextChar = line[i + 1];
        
        if (char === '"') {
            if (inQuotes && nextChar === '"') {
                // Escaped quote - add one quote and skip next
                field += '"';
                i++;
            } else {
                // Toggle quote state
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            // Field delimiter outside quotes
            fields.push(field.trim());
            field = '';
        } else {
            field += char;
        }
    }
    
    // Add the last field
    fields.push(field.trim());
    return fields;
}

/**
 * Parse CSV text into array of objects
 * @param {string} csvText - The CSV file content
 * @returns {Array<Object>} Array of row objects with column names as keys
 */
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
        return [];
    }
    
    // Parse header row
    const headers = parseCSVLine(lines[0]);
    
    // Parse data rows
    const rows = [];
    for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        const row = {};
        headers.forEach((header, index) => {
            row[header] = values[index] || '';
        });
        rows.push(row);
    }
    
    return rows;
}

/**
 * Process a factMap with CSV data to generate facts
 * Supports variable substitution in factDimensions:
 * - $columnName: substituted with the value from that column in the CSV row
 * - $$value: treated as literal $value (escape sequence)
 * 
 * @param {Object} factMap - The factMap object with templateName reference
 * @param {string} csvText - The CSV file content
 * @param {string} baseNamespace - The namespace prefix for generated fact names
 * @param {Object} factSource - The factSource object that references the factMap
 * @param {Object} taxonomy - The taxonomy object containing tableTemplates array
 * @returns {Array<Object>} Array of fact objects
 */
export function processCSVFactMap(factMap, csvText, baseNamespace = 'exp', factSource = null, taxonomy = null) {
    // Look up the template by templateName from taxonomy.tableTemplates array
    let template = null;
    const templateName = factMap.templateName;
    
    if (templateName && taxonomy) {
        // Check tableTemplates array first
        if (taxonomy.tableTemplates) {
            template = taxonomy.tableTemplates.find(t => t.name === templateName);
        }
        
        // Table templates may also be stored in the factMaps array (objects with 'columns' property)
        if (!template && taxonomy.factMaps) {
            template = taxonomy.factMaps.find(fm => fm.name === templateName && fm.columns);
        }
    }
    
    if (!template) {
        console.error('[CSV FactMap] No tableTemplate found for templateName:', templateName, 'in factMap:', factMap.name);
        return [];
    }
    const rows = parseCSV(csvText);
    const facts = [];
    
    console.log(`[CSV FactMap] Processing ${rows.length} rows from CSV`);
    
    // Get row ID column name (optional)
    const rowIdColumn = template.rowIdColumn;
    
    // Get row-level factDimensions (may include $variable references)
    const rowLevelDimensions = template.factDimensions || {};
    
    /**
     * Resolve dimension value: handle $variable references and $$ escaping
     * @param {string} dimValue - The dimension value (may contain $variable or $$)
     * @param {Object} row - The CSV row data
     * @returns {string|null} The resolved value, or null if variable is missing
     */
    function resolveDimensionValue(dimValue, row) {
        if (typeof dimValue !== 'string') {
            return dimValue;
        }
        
        // Handle $$ escape sequence for literal $
        if (dimValue.startsWith('$$')) {
            return dimValue.substring(1); // Remove one $
        }
        
        // Handle $variable reference
        if (dimValue.startsWith('$')) {
            const columnName = dimValue.substring(1);
            const columnValue = row[columnName];
            if (columnValue === '' || columnValue === null || columnValue === undefined) {
                console.warn(`[CSV FactMap] Row missing value for dimension variable: ${dimValue}`);
                return null;
            }
            return columnValue;
        }
        
        // No special handling needed
        return dimValue;
    }
    
    // Process each row
    let rowNumber = 1; // 1-based row numbering as per specification
    for (const row of rows) {
        // Generate row identifier as per specification
        // If template has rowIdColumn and data includes that column, use its value prefixed with r_
        // Otherwise use r_N where N is the row number
        let rowIdentifier;
        if (rowIdColumn && row[rowIdColumn]) {
            rowIdentifier = `r_${row[rowIdColumn]}`;
        } else {
            rowIdentifier = `r_${rowNumber}`;
        }
        
        // Increment row number for next iteration
        rowNumber++;
        
        // Substitute variables in row-level dimensions
        const resolvedRowDimensions = {};
        for (const [dimName, dimValue] of Object.entries(rowLevelDimensions)) {
            const resolved = resolveDimensionValue(dimValue, row);
            if (resolved !== null) {
                resolvedRowDimensions[dimName] = resolved;
            }
        }
        
        // Process each column that represents a fact
        for (const column of template.columns) {
            const columnName = column.columnName;
            
            // Skip if this is the row ID column
            if (columnName === rowIdColumn) {
                continue;
            }
            
            // Skip if column has no factDimensions (not a fact column)
            if (!column.factDimensions) {
                continue;
            }
            
            // Get the cell value
            const cellValue = row[columnName];
            
            // Skip empty values
            if (cellValue === '' || cellValue === null || cellValue === undefined) {
                continue;
            }
            
            // Generate SQNames as per specification:
            // {factSource QName}.{row-identifier}.{column-identifier}
            // Column identifier is the columnName
            const factSourceQName = factSource ? factSource.name : factMap.name; // Use factSource QName if available
            const columnIdentifier = columnName;
            
            // Build the fact and fact value SQNames
            // factValueName reuses the same namespace prefix as the fact, with "_fv" appended
            // to the local name to keep it unique without introducing a new namespace prefix.
            const factName = `${factSourceQName}.${rowIdentifier}.${columnIdentifier}`;
            const factValueName = `${factName}_fv`;
            
            // Resolve variables in column-level dimensions
            const resolvedColumnDimensions = {};
            for (const [dimName, dimValue] of Object.entries(column.factDimensions)) {
                const resolved = resolveDimensionValue(dimValue, row);
                if (resolved !== null) {
                    resolvedColumnDimensions[dimName] = resolved;
                }
            }
            
            // Merge resolved column-level and row-level dimensions
            const factDimensions = {
                ...resolvedColumnDimensions,
                ...resolvedRowDimensions
            };
            
            // Create fact
            const fact = {
                name: factName,
                factValues: [
                    {
                        name: factValueName,
                        value: cellValue
                    }
                ],
                factDimensions: factDimensions
            };
            
            // Add decimals if specified
            if (column.decimals !== undefined) {
                fact.factValues[0].decimals = column.decimals;
            }
            
            facts.push(fact);
        }
    }
    
    console.log(`[CSV FactMap] Generated ${facts.length} facts from ${factMap.name}`);
    return facts;
}

/**
 * Process a factMap with CSV data using streaming approach
 * For large datasets (>= threshold), validates and generates hash/metadata instead of materializing all facts
 * 
 * @param {Object} factMap - The factMap object with templateName reference
 * @param {string} csvText - The CSV file content
 * @param {string} baseNamespace - The namespace prefix for generated fact names
 * @param {Object} factSource - The factSource object that references the factMap
 * @param {Object} taxonomy - The taxonomy object containing tableTemplates array
 * @param {Object} options - Processing options
 * @param {number} options.threshold - Fact count threshold for hash-based storage (default 10000)
 * @param {boolean} options.forceHash - Force hash-based storage regardless of count
 * @param {boolean} options.forceMaterialize - Force materialization regardless of count
 * @returns {Promise<Object>} Result object with either {facts} or {hash, metadata}
 */
export async function processCSVFactMapStreaming(factMap, csvText, baseNamespace = 'exp', factSource = null, taxonomy = null, options = {}) {
    const threshold = options.threshold || 10000;
    const forceHash = options.forceHash || false;
    const forceMaterialize = options.forceMaterialize || false;
    
    // First pass: generate all facts to count them
    const facts = processCSVFactMap(factMap, csvText, baseNamespace, factSource, taxonomy);
    
    console.log(`[CSV FactMap Streaming] Generated ${facts.length} facts (threshold: ${threshold})`);
    
    // Always validate facts regardless of mode
    const { StreamingFactValidator } = await requireStreamingValidator();
    const validator = new StreamingFactValidator(taxonomy);
    
    for (let i = 0; i < facts.length; i++) {
        validator.validate(facts[i], i);
    }
    
    const validationStats = validator.getStatistics();
    console.log(`[CSV FactMap Streaming] Validation complete: ${validationStats.factsProcessed} facts, ${validationStats.errorsFound} errors`);
    
    if (validationStats.hasErrors) {
        console.warn(`[CSV FactMap Streaming] Validation errors found:`, validator.getErrors().slice(0, 10));
    }
    
    // Decide whether to materialize or hash
    const shouldHash = forceHash || (!forceMaterialize && facts.length >= threshold);
    
    if (!shouldHash) {
        console.log(`[CSV FactMap Streaming] Using materialized mode (${facts.length} facts < ${threshold} threshold)`);
        return { 
            facts, 
            validationErrors: validator.getErrors(),
            validationStats,
            mode: 'materialized' 
        };
    }
    
    // Hash-based mode: generate hash and metadata
    console.log(`[CSV FactMap Streaming] Using hash-based mode (${facts.length} facts >= ${threshold} threshold)`);
    const { generateFactCollectionHash } = await requireHashGenerator();
    const { generateFactMetadata } = await requireMetadataGenerator();
    
    const hash = await generateFactCollectionHash(facts);
    const metadata = generateFactMetadata(facts, threshold);
    
    console.log(`[CSV FactMap Streaming] Generated hash: ${hash.substring(0, 16)}...`);
    console.log(`[CSV FactMap Streaming] Metadata: ${metadata.factCount} facts, ${metadata.concepts.length} concepts, ${metadata.dimensions.length} dimensions`);
    
    return {
        hash,
        metadata,
        validationErrors: validator.getErrors(),
        validationStats,
        mode: 'hash-based'
    };
}

/**
 * Lazy-load the hash generator module
 * @returns {Promise<Object>} Hash generator module
 */
function requireHashGenerator() {
    return import('./fact-hash-generator.js');
}

/**
 * Lazy-load the metadata generator module
 * @returns {Promise<Object>} Metadata generator module
 */
function requireMetadataGenerator() {
    return import('./fact-metadata-generator.js');
}

/**
 * Lazy-load the streaming validator module
 * @returns {Promise<Object>} Streaming validator module
 */
function requireStreamingValidator() {
    return import('./streaming-fact-validator.js');
}

/**
 * Load CSV file from URL
 * @param {string} url - The URL to the CSV file
 * @returns {Promise<string>} The CSV file content
 */
export async function loadCSVFile(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const text = await response.text();
        return text;
    } catch (error) {
        console.error('[CSV FactMap] Error loading CSV file:', url, error);
        throw error;
    }
}
