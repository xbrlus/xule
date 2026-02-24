/**
 * On-demand Fact Generation Module
 * 
 * Generates facts from hash-based factSources when needed for cube rendering,
 * Facts tab display, or queries. Enables lazy evaluation to avoid materializing
 * all facts in memory.
 */

import { processCSVFactMap } from './csv-factMap-processor.js';

/**
 * Generate facts from a hash-based factSource for a specific cube
 * @param {Object} factSource - The factSource object (with hash and metadata)
 * @param {Object} cube - The cube object to filter facts for
 * @param {Object} xbrlModel - The XBRL model containing factMaps and table templates
 * @returns {Promise<Array>} - Array of fact objects matching the cube
 */
export async function generateFactsForCube(factSource, cube, xbrlModel) {
    if (!factSource || !factSource.hash || !factSource.metadata) {
        throw new Error('Invalid factSource: must be hash-based with metadata');
    }
    
    console.log('[Fact Generator] Generating facts for cube:', {
        factSource: factSource.name,
        cube: cube.name,
        totalFacts: factSource.metadata.factCount
    });
    
    // Generate all facts from the factSource
    const allFacts = await generateAllFacts(factSource, xbrlModel);
    
    // Filter facts to match cube dimensional space
    const relevantFacts = filterFactsToCube(allFacts, cube, xbrlModel);
    
    console.log('[Fact Generator] Generated facts:', {
        total: allFacts.length,
        relevant: relevantFacts.length
    });
    
    return relevantFacts;
}

/**
 * Generate facts from a hash-based factSource with pagination
 * Uses streaming to only process requested rows from CSV
 * @param {Object} factSource - The factSource object
 * @param {number} startRow - Starting CSV row (1-based, after header)
 * @param {number} rowCount - Number of CSV rows to process
 * @param {Object} xbrlModel - The XBRL model
 * @param {Object} cube - Optional cube to filter facts
 * @returns {Promise<Object>} - { facts: Array, hasMore: boolean, total: number, startRow, endRow }
 */
export async function generateFactsWithPagination(factSource, startRow, rowCount, xbrlModel, cube = null) {
    if (!factSource || !factSource.hash || !factSource.metadata) {
        throw new Error('Invalid factSource: must be hash-based with metadata');
    }
    
    console.log('[Fact Generator] Pagination request:', {
        factSource: factSource.name,
        startRow,
        rowCount,
        hasCubeFilter: !!cube
    });
    
    const totalFacts = factSource.metadata.factCount;
    
    // Find the factMap
    const factMapName = factSource.factMapName;
    const factMap = xbrlModel.factMaps?.find(fm => fm.name === factMapName);
    if (!factMap) {
        throw new Error(`FactMap not found: ${factMapName}`);
    }
    
    // Read CSV as text
    const csvText = await readCSVFile(factSource.name);
    const lines = csvText.trim().split('\n');
    
    if (lines.length < 2) {
        // No data rows
        return {
            facts: [],
            hasMore: false,
            total: 0,
            startRow,
            endRow: startRow,
            totalRows: 0
        };
    }
    
    // Extract header and requested data rows
    // startRow is 1-based and refers to data rows (row 1 = first data row after header)
    const header = lines[0];
    const dataLines = lines.slice(1); // All data rows
    const endIndex = Math.min(startRow - 1 + rowCount, dataLines.length);
    const requestedDataLines = dataLines.slice(startRow - 1, endIndex);
    
    console.log('[Fact Generator] Processing rows:', {
        totalDataRows: dataLines.length,
        requestedStart: startRow,
        requestedEnd: startRow - 1 + requestedDataLines.length,
        actualRowsExtracted: requestedDataLines.length
    });
    
    if (requestedDataLines.length === 0) {
        // No more data
        return {
            facts: [],
            hasMore: false,
            total: totalFacts,
            startRow,
            endRow: startRow - 1,
            totalRows: dataLines.length
        };
    }
    
    // Create mini-CSV with header + requested rows
    const miniCSV = [header, ...requestedDataLines].join('\n');
    
    // Process this batch through the factMap
    const baseNamespace = extractNamespace(factSource.name);
    const batchFacts = processCSVFactMap(
        factMap,
        miniCSV,
        baseNamespace,
        factSource.name,
        xbrlModel
    );
    
    // Filter to cube if provided
    const filteredFacts = cube ? filterFactsToCube(batchFacts, cube, xbrlModel) : batchFacts;
    
    console.log('[Fact Generator] Batch results:', {
        generated: batchFacts.length,
        afterCubeFilter: filteredFacts.length
    });
    
    return {
        facts: filteredFacts,
        hasMore: endIndex < dataLines.length,
        total: totalFacts,
        startRow,
        endRow: startRow - 1 + requestedDataLines.length,
        totalRows: dataLines.length
    };
}

// Helper to parse CSV (extracted from csv-factMap-processor.js pattern)
function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    
    return lines.slice(1).map((line, idx) => {
        const values = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                values.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        values.push(current.trim());
        
        const row = {};
        headers.forEach((header, i) => {
            row[header] = values[i]?.replace(/^"|"$/g, '') || '';
        });
        return row;
    });
}

/**
 * Generate all facts from a hash-based factSource
 * @param {Object} factSource - The factSource object
 * @param {Object} xbrlModel - The XBRL model
 * @returns {Promise<Array>} - Array of all fact objects
 */
export async function generateAllFacts(factSource, xbrlModel) {
    if (!factSource || !factSource.hash || !factSource.metadata) {
        throw new Error('Invalid factSource: must be hash-based with metadata');
    }
    
    console.log('[Fact Generator] Generating all facts for:', {
        factSource: factSource.name,
        totalFacts: factSource.metadata.factCount
    });
    
    // Find the factMap
    const factMapName = factSource.factMapName;
    const factMap = xbrlModel.factMaps?.find(fm => fm.name === factMapName);
    if (!factMap) {
        throw new Error(`FactMap not found: ${factMapName}`);
    }
    
    console.log('[Fact Generator] Found factMap:', factMap.name);
    
    // Re-read CSV file
    const csvText = await readCSVFile(factSource.name);
    
    // Process CSV to generate facts (synchronous)
    const baseNamespace = extractNamespace(factSource.name);
    const facts = processCSVFactMap(
        factMap,  // Pass factMap, not tableTemplate - processCSVFactMap will look up the template
        csvText,
        baseNamespace,
        factSource.name,
        xbrlModel
    );
    
    console.log('[Fact Generator] Generated facts:', facts.length);
    
    return facts;
}

/**
 * Filter facts to match a cube's dimensional requirements.
 * Checks:
 *   1. Fact has all required cube dimensions (dimensions without allowDomainFacts).
 *   2. All fact dimensions are listed in the cube's cubeDimensions.
 *   3. For each dimension, the fact's value is within the domain specified by domainName
 *      (if domainName is present on that cubeDimension).
 *
 * @param {Array} facts - Array of fact objects
 * @param {Object} cube - The cube object
 * @param {Object|null} xbrlModel - The XBRL model (needed for domain membership checks)
 * @returns {Array} - Filtered facts
 */
export function filterFactsToCube(facts, cube, xbrlModel = null) {
    if (!cube || !cube.cubeDimensions) {
        return facts;
    }
    
    const cubeDimensionNames = cube.cubeDimensions.map(d => d.dimensionName);
    
    return facts.filter(fact => {
        if (!fact.factDimensions) return false;
        
        const factDimensionNames = Object.keys(fact.factDimensions);
        
        // 1. Check that the fact has all REQUIRED cube dimensions
        const hasAllRequiredDimensions = cube.cubeDimensions.every(cubeDim => {
            const allowDomainFacts = cubeDim.allowDomainFacts === true;
            const factHasDimension = factDimensionNames.includes(cubeDim.dimensionName);
            if (!allowDomainFacts && !factHasDimension) {
                return false;
            }
            return true;
        });
        
        if (!hasAllRequiredDimensions) return false;
        
        // 2. Check that all fact dimensions are recognised by this cube
        const factDimensionsInCube = factDimensionNames.every(dimName =>
            cubeDimensionNames.includes(dimName)
        );
        
        if (!factDimensionsInCube) return false;
        
        // 3. For every cube dimension that restricts values via domainName,
        //    verify the fact's value for that dimension is a member of the domain.
        if (xbrlModel) {
            const domainValueIsValid = cube.cubeDimensions.every(cubeDim => {
                if (!cubeDim.domainName) return true; // no restriction – allow
                
                const factValue = fact.factDimensions[cubeDim.dimensionName];
                if (factValue === undefined) return true; // dimension absent – already handled above
                
                const domain = xbrlModel.domains?.find(d => d.name === cubeDim.domainName);
                if (!domain) return false; // domain defined but not found – reject
                
                // Accept if the value appears as the domain root
                if (domain.roots && domain.roots.includes(factValue)) return true;
                
                // Accept if the value appears as a source or target in any domain relationship
                if (domain.relationships) {
                    return domain.relationships.some(
                        rel => rel.source === factValue || rel.target === factValue
                    );
                }
                
                return false;
            });
            
            if (!domainValueIsValid) return false;
        }
        
        return true;
    });
}

/**
 * Find table template from factMap
 * @param {Object} factMap - The factMap object
 * @param {Object} xbrlModel - The XBRL model
 * @returns {Object|null} - Table template object
 */
function findTableTemplate(factMap, xbrlModel) {
    const templateName = factMap.templateName;
    
    if (!templateName) {
        console.error('[Fact Generator] factMap has no templateName:', factMap);
        return null;
    }
    
    // Check tableTemplates array first
    if (xbrlModel.tableTemplates) {
        const template = xbrlModel.tableTemplates.find(t => t.name === templateName);
        if (template) return template;
    }
    
    // Table templates may also be stored in the factMaps array (objects with 'columns' property)
    if (xbrlModel.factMaps) {
        const template = xbrlModel.factMaps.find(fm => fm.name === templateName && fm.columns);
        if (template) return template;
    }
    
    // Could also check jsonTemplates, xmlTemplates
    
    return null;
}

/**
 * Get CSV file path from factSource name
 * Assumes pattern: namespace:TableName -> examples/namespace/TableName.csv
 * @param {string} factSourceName - QName of factSource (e.g., "gl-exp:Journals")
 * @returns {string} - Path to CSV file
 */
function getCSVPath(factSourceName) {
    if (!factSourceName || !factSourceName.includes(':')) {
        throw new Error(`Invalid factSource name: ${factSourceName}`);
    }
    
    const [namespace, tableName] = factSourceName.split(':');
    
    // Convert namespace prefix to directory
    // This is a simplification - ideally would use namespace mappings
    const dir = namespace === 'gl-exp' ? 'GL' : namespace;
    
    return `examples/${dir}/${tableName}.csv`;
}

/**
 * Extract namespace prefix from factSource name
 * @param {string} factSourceName - QName like "gl-exp:Journals"
 * @returns {string} - Namespace prefix like "gl-exp"
 */
function extractNamespace(factSourceName) {
    if (!factSourceName || !factSourceName.includes(':')) {
        return 'exp'; // default
    }
    return factSourceName.split(':')[0];
}

/**
 * Read CSV file content
 * @param {string} factSourceName - FactSource name to derive path
 * @returns {Promise<string>} - CSV file content
 */
async function readCSVFile(factSourceName) {
    const csvPath = getCSVPath(factSourceName);
    
    try {
        const response = await fetch(csvPath);
        if (!response.ok) {
            throw new Error(`Failed to fetch CSV: ${response.statusText}`);
        }
        return await response.text();
    } catch (error) {
        throw new Error(`Failed to read CSV file ${csvPath}: ${error.message}`);
    }
}
