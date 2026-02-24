/**
 * Module for resolving fact value sources
 * Handles id resolution from HTML documents and transformation application
 */

import { getTaxonomyData } from './main.js';
import { getXbrlModel } from './utils.js';

// Cache for loaded HTML documents
const documentCache = new Map();

/**
 * Resolve the source file URL from valueSource.source or documentInfo.sourceMapping
 * @param {Object} valueSource - The value source object
 * @param {Object} documentInfo - The documentInfo object from taxonomy
 * @returns {Object} Object with {filename: string, error: string|null}
 */
function resolveSourceFile(valueSource, documentInfo) {
    // If source is explicitly provided as a QName, resolve it from sourceMapping
    if (valueSource.source) {
        if (!documentInfo || !documentInfo.sourceMapping) {
            return {
                filename: null,
                error: 'oimte:invalidQNameReference',
                message: `No sourceMapping found in documentInfo for source '${valueSource.source}'`
            };
        }

        // Resolve the QName to get the namespace prefix
        const sourceQName = valueSource.source;
        const urls = documentInfo.sourceMapping[sourceQName];
        
        if (!urls || urls.length === 0) {
            return {
                filename: null,
                error: 'oimte:invalidQNameReference',
                message: `Source '${sourceQName}' not found in sourceMapping`
            };
        }

        // Use the first URL from the array
        return { filename: urls[0], error: null };
    }

    // No explicit source, try to use sourceMapping default
    if (documentInfo && documentInfo.sourceMapping) {
        const sourceMappingKeys = Object.keys(documentInfo.sourceMapping);
        
        if (sourceMappingKeys.length === 0) {
            // No source mapping available, might be embedded document
            return { filename: null, error: null };
        } else if (sourceMappingKeys.length === 1) {
            // Only one source file, use it as default
            const urls = documentInfo.sourceMapping[sourceMappingKeys[0]];
            if (urls && urls.length > 0) {
                return { filename: urls[0], error: null };
            }
        } else {
            // Multiple source files and no explicit source - ambiguous!
            return {
                filename: null,
                error: 'oimte:ambiguousFileReference',
                message: `Multiple source files in sourceMapping (${sourceMappingKeys.join(', ')}) but no 'source' attribute specified in valueSource`
            };
        }
    }

    // No sourceMapping, assume embedded or same document
    return { filename: null, error: null };
}

/**
 * Load and cache an HTML document
 * @param {string} href - The href to the HTML document (relative path)
 * @returns {Promise<Document>} The parsed HTML document
 */
async function loadHTMLDocument(href) {
    // Extract just the filename from the href (remove fragment)
    const filename = href.split('#')[0];
    
    if (documentCache.has(filename)) {
        return documentCache.get(filename);
    }

    try {
        // Try to load from examples directory
        const response = await fetch(`./examples/${filename}`);
        if (!response.ok) {
            console.warn(`[ValueSource] Could not load document: ${filename}`);
            return null;
        }

        const htmlText = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, 'text/html');
        
        documentCache.set(filename, doc);
        console.log(`[ValueSource] Loaded and cached document: ${filename}`);
        return doc;
    } catch (error) {
        console.error(`[ValueSource] Error loading document ${filename}:`, error);
        return null;
    }
}

/**
 * Extract value from HTML document using ID
 * @param {Document} doc - The HTML document
 * @param {string} id - The element ID to find
 * @param {boolean} escape - If true, return escaped HTML; if false, return text content
 * @returns {string|null} The extracted content, or null if not found
 */
function extractValueFromHTML(doc, id, escape = false) {
    if (!doc || !id) {
        return null;
    }

    const element = doc.getElementById(id);
    if (!element) {
        return null;
    }

    if (escape) {
        // Return outerHTML to preserve the element's own attributes and structure
        return element.outerHTML || '';
    }

    // Get the text content and normalize whitespace
    const textContent = element.textContent || element.innerText || '';
    return textContent.trim();
}

/**
 * Apply transformation to a value
 * @param {string} value - The value to transform
 * @param {string} transformName - The transformation QName (e.g., "ixt:date-monthname-day-year-en")
 * @returns {Promise<{value: string|null, error: string|null}>} Object with transformed value or error
 */
async function applyTransformation(value, transformName) {
    if (!transformName) {
        return { value, error: null };
    }

    // Get transforms from the merged taxonomy data
    const taxonomyData = getTaxonomyData();
    if (!taxonomyData) {
        return {
            value: null,
            error: 'oimte:unknownFactTransformation',
            message: 'Taxonomy data not available'
        };
    }

    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel || !xbrlModel.transforms) {
        return {
            value: null,
            error: 'oimte:unknownFactTransformation',
            message: `No transforms available in taxonomy`
        };
    }

    // Look for the transform in transforms array
    const transform = xbrlModel.transforms.find(t => t.name === transformName);
    if (!transform) {
        return {
            value: null,
            error: 'oimte:unknownFactTransformation',
            message: `Unknown transformation: ${transformName}`
        };
    }

    // For now, we'll implement a subset of common transformations
    // Full implementation would require all the regex patterns and date parsing logic
    try {
        const transformedValue = await executeTransformation(value, transformName, transform);
        return { value: transformedValue, error: null };
    } catch (error) {
        return {
            value: null,
            error: 'oimte:unknownFactTransformation',
            message: `Error applying transformation ${transformName}: ${error.message}`
        };
    }
}

/**
 * Execute a specific transformation
 * @param {string} value - The value to transform
 * @param {string} transformName - The transformation QName
 * @param {Object} transform - The transform object from taxonomy
 * @returns {Promise<string>} The transformed value
 */
async function executeTransformation(value, transformName, transform) {
    // Simplified implementation of common transformations
    // A full implementation would need to handle all transformation types from the taxonomy
    
    const transformShortName = transformName.split(':')[1] || transformName;

    // Boolean transformations
    if (transformShortName === 'boolballotbox' || transformShortName.includes('bool')) {
        // Check for checkmark or ballot box symbols
        if (value.includes('☑') || value.includes('☒') || value.includes('✓') || value.includes('✔')) {
            return 'true';
        } else if (value.includes('☐') || value.includes('✗') || value.includes('✘')) {
            return 'false';
        }
        // Otherwise try to parse as text
        const lowerValue = value.toLowerCase().trim();
        if (lowerValue === 'true' || lowerValue === 'yes' || lowerValue === 'y') {
            return 'true';
        } else if (lowerValue === 'false' || lowerValue === 'no' || lowerValue === 'n') {
            return 'false';
        }
        return value; // Return as-is if can't determine
    }

    // Date transformations - simplified
    if (transformShortName.startsWith('date-')) {
        // For date transformations, we'd need to parse various date formats
        // This is a simplified version that attempts basic date parsing
        try {
            // Try to parse common date formats
            const dateValue = parseDateFormat(value, transformShortName);
            if (dateValue) {
                return dateValue;
            }
        } catch (e) {
            console.warn(`[ValueSource] Could not parse date: ${value}`, e);
        }
        return value; // Return original if parsing fails
    }

    // Numeric transformations
    if (transformShortName.startsWith('num-')) {
        return parseNumericFormat(value, transformShortName);
    }

    // Exchange name transformation (ixt-sec:exchnameen)
    if (transformShortName === 'exchnameen') {
        return transformExchangeName(value);
    }

    // Fixed transformations
    if (transformShortName.startsWith('fixed-')) {
        if (transformShortName === 'fixed-empty') return '';
        if (transformShortName === 'fixed-false') return 'false';
        if (transformShortName === 'fixed-true') return 'true';
        if (transformShortName === 'fixed-zero') return '0';
    }

    // Default: return the value as-is
    return value;
}

/**
 * Transform exchange full names to short codes
 * @param {string} value - The exchange full name
 * @returns {string} The exchange short code
 */
function transformExchangeName(value) {
    // Exchange name mappings (case-insensitive matching)
    const exchangeMappings = {
        'the new york stock exchange': 'NYSE',
        'new york stock exchange llc': 'NYSE',
        'nasdaq global select market': 'NASDAQ',
        'the nasdaq stock market llc': 'NASDAQ',
        'box exchange llc': 'BOX',
        'nasdaq bx, inc.': 'BX',
        'cboe c2 exchange, inc.': 'C2',
        'cboe exchange, inc.': 'CBOE',
        'chicago stock exchange, inc.': 'CHX',
        'cboe byx exchange, inc.': 'CboeBYX',
        'cboe bzx exchange, inc.': 'CboeBZX',
        'cboe edga exchange, inc.': 'CboeEDGA',
        'cboe edgx exchange, inc.': 'CboeEDGX',
        'nasdaq gemx, llc': 'GEMX'
    };
    
    // Normalize the input: trim and convert to lowercase
    const normalizedValue = value.trim().toLowerCase();
    
    // Look up the mapping
    if (exchangeMappings[normalizedValue]) {
        return exchangeMappings[normalizedValue];
    }
    
    // If no mapping found, return original value
    return value;
}

/**
 * Parse date format (simplified implementation)
 * @param {string} value - The date string
 * @param {string} format - The date format name
 * @returns {string|null} ISO date string or null
 */
function parseDateFormat(value, format) {
    // This is a very simplified implementation
    // Full implementation would need to handle all the date formats in transform-types.json
    
    // Try common English date formats
    const monthNames = {
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
        'oct': '10', 'nov': '11', 'dec': '12'
    };

    // Try to extract month name, day, and year
    const lowerValue = value.toLowerCase();
    
    // Pattern: "Month Day, Year" or "Month Day Year"
    for (const [monthName, monthNum] of Object.entries(monthNames)) {
        if (lowerValue.includes(monthName)) {
            const regex = new RegExp(`${monthName}[\\s,]+([0-9]{1,2})[\\s,]+([0-9]{4})`, 'i');
            const match = value.match(regex);
            if (match) {
                const day = match[1].padStart(2, '0');
                const year = match[2];
                
                // Return format based on transformation name
                if (format.includes('gYearMonth')) {
                    return `${year}-${monthNum}`;
                }
                return `${year}-${monthNum}-${day}`;
            }
            
            // Pattern without year: "Month Day"
            const regexNoYear = new RegExp(`${monthName}[\\s,]+([0-9]{1,2})`, 'i');
            const matchNoYear = value.match(regexNoYear);
            if (matchNoYear && format.includes('monthname-day-en')) {
                const day = matchNoYear[1].padStart(2, '0');
                return `--${monthNum}-${day}`;
            }
        }
    }

    // Try standard date formats
    const standardDatePattern = /([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})/;
    const match = value.match(standardDatePattern);
    if (match) {
        const year = match[1];
        const month = match[2].padStart(2, '0');
        const day = match[3].padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    return null;
}

/**
 * Parse numeric format
 * Handles various numeric formats with different thousand separators and decimal markers
 * @param {string} value - The numeric string (e.g., "28,813,396.08", "1.234.567,89")
 * @param {string} format - The numeric format name
 * @returns {string} Parsed numeric value as decimal string
 */
function parseNumericFormat(value, format) {
    // Remove leading/trailing whitespace
    let cleaned = value.trim();
    
    // Store sign if present
    const isNegative = cleaned.startsWith('-') || cleaned.startsWith('(');
    if (cleaned.startsWith('-')) {
        cleaned = cleaned.substring(1).trim();
    }
    // Handle parentheses notation for negatives (e.g., "(123.45)")
    if (cleaned.startsWith('(') && cleaned.endsWith(')')) {
        cleaned = cleaned.substring(1, cleaned.length - 1).trim();
    }

    // Handle different decimal/thousand separator combinations
    if (format.includes('comma-decimal')) {
        // Format: 1.234.567,89 -> thousand separator is dot, decimal is comma
        // Remove all dots (thousands), replace comma with dot (decimal)
        cleaned = cleaned.replace(/\./g, '').replace(',', '.');
    } else if (format.includes('dot-decimal')) {
        // Format: 1,234,567.89 or 28,813,396.08 -> thousand separator is comma, decimal is dot
        // Remove all commas (thousands), keep dot as decimal
        cleaned = cleaned.replace(/,/g, '');
    } else if (format.includes('unit-decimal')) {
        // Format: 1 234 567.89 -> thousand separator is space, decimal is dot
        // Remove all spaces (thousands), keep dot as decimal
        cleaned = cleaned.replace(/\s/g, '');
    }

    // Handle apostrophe thousand separator (e.g., "1'234'567.89")
    if (format.includes('apos')) {
        cleaned = cleaned.replace(/'/g, '');
    }

    // Remove any remaining non-numeric characters except decimal point
    // This handles currency symbols ($, €, £, etc.), percent signs, and other characters
    cleaned = cleaned.replace(/[^0-9.]/g, '');
    
    // Ensure only one decimal point (keep the last one if multiple exist)
    const parts = cleaned.split('.');
    if (parts.length > 2) {
        // Multiple dots found - join all but last as integer, last as decimal
        cleaned = parts.slice(0, -1).join('') + '.' + parts[parts.length - 1];
    }

    // Restore negative sign if needed
    if (isNegative && cleaned !== '0' && cleaned !== '') {
        cleaned = '-' + cleaned;
    }

    return cleaned;
}

/**
 * Resolve a single value source
 * @param {Object} valueSource - The value source object
 * @returns {Promise<Object>} Object with resolved value and any errors
 */
export async function resolveValueSource(valueSource) {
    if (!valueSource) {
        return { value: null, error: null };
    }

    // Default medium to 'html' if id is present but medium is not specified
    const medium = valueSource.medium || (valueSource.id ? 'html' : null);

    // Check if this is an HTML id reference
    if (medium === 'html' && valueSource.id) {
        const id = valueSource.id;
        
        // Get taxonomy data to access documentInfo
        const taxonomyData = getTaxonomyData();
        const documentInfo = taxonomyData?.documentInfo;
        
        // Resolve the source file
        const sourceResult = resolveSourceFile(valueSource, documentInfo);
        if (sourceResult.error) {
            return {
                value: null,
                error: sourceResult.error,
                message: sourceResult.message,
                id: id
            };
        }

        const filename = sourceResult.filename;

        // Load the HTML document (if filename provided)
        let doc;
        if (filename) {
            doc = await loadHTMLDocument(filename);
            if (!doc) {
                return {
                    value: null,
                    error: 'oimte:hrefIDNotFound',
                    message: `Could not load document: ${filename}`,
                    id: id,
                    source: valueSource.source
                };
            }
        } else {
            // No filename means embedded or same document - not yet implemented
            return {
                value: null,
                error: null,
                message: 'Embedded document sources not yet implemented',
                id: id
            };
        }

        // Extract the value (use escape flag if present)
        const extractedValue = extractValueFromHTML(doc, id, valueSource.escape);
        if (extractedValue === null) {
            return {
                value: null,
                error: 'oimte:hrefIDNotFound',
                message: `Element with ID '${id}' not found in ${filename}`,
                id: id,
                source: valueSource.source
            };
        }

        let finalValue = extractedValue;
        let originalValue = extractedValue;

        // Apply transformation if specified (only for non-escaped values)
        if (valueSource.transformation && !valueSource.escape) {
            const result = await applyTransformation(finalValue, valueSource.transformation);
            if (result.error) {
                return {
                    value: result.value,
                    error: result.error,
                    message: result.message,
                    originalValue: extractedValue,
                    id: id,
                    source: valueSource.source
                };
            }
            finalValue = result.value;
        }

        // Apply scale if specified (multiply by 10^scale) - only for non-escaped values
        if (valueSource.scale !== undefined && valueSource.scale !== null && !valueSource.escape) {
            const numValue = parseFloat(finalValue);
            if (!isNaN(numValue)) {
                const scaleFactor = Math.pow(10, valueSource.scale);
                finalValue = String(numValue * scaleFactor);
            }
        }

        // Apply sign if specified (make negative if sign is "-") - only for non-escaped values
        if (valueSource.sign === '-' && !valueSource.escape) {
            const numValue = parseFloat(finalValue);
            if (!isNaN(numValue) && numValue > 0) {
                finalValue = String(-numValue);
            }
        }

        return { 
            value: finalValue, 
            error: null,
            originalValue: finalValue !== originalValue ? originalValue : undefined,
            id: id,
            source: valueSource.source,
            filename: filename,
            escape: valueSource.escape
        };
    }

    // Other medium types (pdf, xml, etc.) not yet implemented
    return {
        value: null,
        error: null,
        message: `Medium type '${medium}' not yet supported`,
        id: valueSource.id,
        source: valueSource.source
    };
}

/**
 * Resolve all value sources for a fact value
 * @param {Object} factValue - The fact value object with valueSources array
 * @returns {Promise<Object>} Object with resolved value and any errors
 */
export async function resolveFactValue(factValue) {
    if (!factValue.valueSources || factValue.valueSources.length === 0) {
        // No value sources, return the existing value
        return {
            value: factValue.value,
            error: null,
            hasValueSources: false
        };
    }

    // If there's an explicit value, prefer it over value sources
    if (factValue.value !== undefined && factValue.value !== null) {
        return {
            value: factValue.value,
            error: null,
            hasValueSources: true,
            valueSourcesIgnored: true
        };
    }

    // Check if ANY valueSource has escape: true
    const hasEscapedSource = factValue.valueSources.some(vs => vs.escape === true);
    
    if (hasEscapedSource) {
        // Concatenate ALL value sources
        const resolvedSources = [];
        const allSourceRefs = [];
        let hasError = false;
        let errorInfo = null;
        
        for (const source of factValue.valueSources) {
            const result = await resolveValueSource(source);
            
            // Track source references (filename#id)
            const sourceRef = result.id ? `${result.filename || 'unknown'}#${result.id}` : null;
            if (sourceRef) {
                allSourceRefs.push(sourceRef);
            }
            
            if (result.error && !hasError) {
                hasError = true;
                errorInfo = {
                    error: result.error,
                    message: result.message
                };
            }
            
            if (result.value !== null) {
                resolvedSources.push(result.value);
            }
        }
        
        // Concatenate all resolved values
        const concatenatedValue = resolvedSources.join('');
        
        return {
            value: concatenatedValue,
            error: hasError ? errorInfo.error : null,
            message: hasError ? errorInfo.message : null,
            hasValueSources: true,
            sourceRefs: allSourceRefs,
            isEscaped: true,
            concatenated: true
        };
    }

    // No escaped sources - resolve the first value source
    // (Spec says if there are multiple values for a single ID, return the first)
    const firstSource = factValue.valueSources[0];
    const result = await resolveValueSource(firstSource);

    const sourceRef = result.id ? `${result.filename || 'unknown'}#${result.id}` : null;

    return {
        value: result.value,
        error: result.error,
        message: result.message,
        originalValue: result.originalValue,
        hasValueSources: true,
        transformation: firstSource.transformation,
        sourceRefs: sourceRef ? [sourceRef] : []
    };
}

/**
 * Clear the document cache (useful for testing/reloading)
 */
export function clearCache() {
    documentCache.clear();
    transformTypesTaxonomy = null;
    console.log('[ValueSource] Cache cleared');
}
