/**
 * Fact Hash Generator
 * 
 * Generates deterministic semantic hashes for fact collections.
 * Ensures identical fact collections produce identical hashes regardless
 * of the order facts are processed from the data source.
 */

/**
 * Generates a deterministic SHA-256 hash for a collection of facts
 * @param {Array} facts - Array of fact objects
 * @returns {Promise<string>} - Hex-encoded SHA-256 hash
 */
async function generateFactCollectionHash(facts) {
    if (!facts || facts.length === 0) {
        throw new Error('Cannot generate hash for empty fact collection');
    }
    
    // Sort facts to ensure deterministic ordering
    const sortedFacts = sortFactsForHashing(facts);
    
    // Serialize to canonical form
    const canonicalForm = serializeFactsCanonically(sortedFacts);
    
    // Compute SHA-256 hash
    const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonicalForm));
    
    // Convert to hex string
    return bufferToHex(hashBuffer);
}

/**
 * Sorts facts by dimensional values in a consistent order
 * @param {Array} facts - Array of fact objects
 * @returns {Array} - Sorted array of facts
 */
function sortFactsForHashing(facts) {
    return [...facts].sort((a, b) => {
        // Sort by fact dimensions, then value
        const keyA = getFactSortKey(a);
        const keyB = getFactSortKey(b);
        return keyA.localeCompare(keyB);
    });
}

/**
 * Generates a sort key for a fact based on its dimensions and value
 * @param {Object} fact - Fact object
 * @returns {string} - Sort key
 */
function getFactSortKey(fact) {
    const dimensions = fact.factDimensions || {};
    
    // Extract all dimension keys and sort them
    const dimKeys = Object.keys(dimensions).sort();
    
    // Build key: concept|dimension1:value1|dimension2:value2|...|value
    const parts = [];
    
    for (const dimKey of dimKeys) {
        const dimValue = dimensions[dimKey];
        
        if (typeof dimValue === 'object' && dimValue !== null) {
            // Handle complex dimension values (e.g., periods, entities)
            parts.push(`${dimKey}:${JSON.stringify(dimValue)}`);
        } else {
            parts.push(`${dimKey}:${dimValue}`);
        }
    }
    
    // Add fact value if it exists
    if (fact.factValues && fact.factValues.length > 0) {
        const firstValue = fact.factValues[0];
        if (firstValue.value !== undefined) {
            parts.push(`value:${firstValue.value}`);
        }
        if (firstValue.decimals !== undefined) {
            parts.push(`decimals:${firstValue.decimals}`);
        }
        if (firstValue.language !== undefined) {
            parts.push(`language:${firstValue.language}`);
        }
    }
    
    return parts.join('|');
}

/**
 * Serializes facts to canonical form for hashing
 * @param {Array} facts - Sorted array of fact objects
 * @returns {string} - Canonical serialization
 */
function serializeFactsCanonically(facts) {
    const lines = [];
    
    for (const fact of facts) {
        const dimensions = fact.factDimensions || {};
        const factValue = fact.factValues && fact.factValues.length > 0 ? fact.factValues[0] : {};
        
        // Serialize each fact as: dimension1=value1,dimension2=value2,...,value=X,decimals=Y
        const parts = [];
        
        // Add dimensions in sorted order
        const dimKeys = Object.keys(dimensions).sort();
        for (const dimKey of dimKeys) {
            const dimValue = dimensions[dimKey];
            if (typeof dimValue === 'object' && dimValue !== null) {
                parts.push(`${dimKey}=${JSON.stringify(dimValue)}`);
            } else {
                parts.push(`${dimKey}=${dimValue}`);
            }
        }
        
        // Add value properties
        if (factValue.value !== undefined) {
            // Normalize numeric values to avoid floating point issues
            const normalizedValue = typeof factValue.value === 'number' 
                ? factValue.value.toPrecision(15)
                : factValue.value;
            parts.push(`value=${normalizedValue}`);
        }
        if (factValue.decimals !== undefined) {
            parts.push(`decimals=${factValue.decimals}`);
        }
        if (factValue.language !== undefined) {
            parts.push(`language=${factValue.language}`);
        }
        
        lines.push(parts.join(','));
    }
    
    return lines.join('\n');
}

/**
 * Converts ArrayBuffer to hex string
 * @param {ArrayBuffer} buffer - Buffer to convert
 * @returns {string} - Hex string
 */
function bufferToHex(buffer) {
    const byteArray = new Uint8Array(buffer);
    return Array.from(byteArray)
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

/**
 * Verifies a hash against a fact collection
 * @param {Array} facts - Array of fact objects
 * @param {string} expectedHash - Expected hash value
 * @returns {Promise<boolean>} - True if hash matches
 */
async function verifyFactCollectionHash(facts, expectedHash) {
    const actualHash = await generateFactCollectionHash(facts);
    return actualHash === expectedHash;
}

/**
 * Generates hash incrementally for streaming scenarios
 * Useful when facts are processed one at a time
 */
class StreamingHashGenerator {
    constructor() {
        this.facts = [];
    }
    
    /**
     * Adds a fact to the collection
     * @param {Object} fact - Fact object
     */
    addFact(fact) {
        this.facts.push(fact);
    }
    
    /**
     * Finalizes and computes the hash
     * @returns {Promise<string>} - Hex-encoded SHA-256 hash
     */
    async finalize() {
        return await generateFactCollectionHash(this.facts);
    }
    
    /**
     * Gets the current fact count
     * @returns {number} - Number of facts processed
     */
    getFactCount() {
        return this.facts.length;
    }
    
    /**
     * Clears the fact collection (useful for memory management)
     */
    clear() {
        this.facts = [];
    }
}

// Export functions
export {
    generateFactCollectionHash,
    verifyFactCollectionHash,
    StreamingHashGenerator
};
