/**
 * Fact Metadata Generator
 * 
 * Generates metadata summaries for fact collections to enable querying,
 * validation, and cube membership determination without materializing all facts.
 */

/**
 * Generates comprehensive metadata for a fact collection
 * @param {Array} facts - Array of fact objects
 * @param {number} threshold - Fact count threshold (default 10000)
 * @returns {Object} - factSourceMetadata object
 */
function generateFactMetadata(facts, threshold = 10000) {
    if (!facts || facts.length === 0) {
        throw new Error('Cannot generate metadata for empty fact collection');
    }
    
    return {
        factCount: facts.length,
        validationTimestamp: new Date().toISOString(),
        concepts: extractUniqueConcepts(facts),
        dimensions: generateDimensionSummaries(facts),
        threshold: threshold
    };
}

/**
 * Extracts unique concept QNames from fact collection
 * @param {Array} facts - Array of fact objects
 * @returns {Array} - Ordered set of concept QNames
 */
function extractUniqueConcepts(facts) {
    const conceptSet = new Set();
    
    for (const fact of facts) {
        if (fact.factDimensions && fact.factDimensions['xbrl:concept']) {
            conceptSet.add(fact.factDimensions['xbrl:concept']);
        }
    }
    
    // Return sorted array for consistency
    return Array.from(conceptSet).sort();
}

/**
 * Generates dimension summaries for all dimensions in fact collection
 * @param {Array} facts - Array of fact objects
 * @returns {Array} - Array of factSourceDimensionSummary objects
 */
function generateDimensionSummaries(facts) {
    // Collect all unique dimensions and their members
    const dimensionData = new Map();
    
    for (const fact of facts) {
        if (!fact.factDimensions) continue;
        
        for (const [dimName, dimValue] of Object.entries(fact.factDimensions)) {
            if (!dimensionData.has(dimName)) {
                dimensionData.set(dimName, {
                    members: new Set(),
                    values: []
                });
            }
            
            const data = dimensionData.get(dimName);
            
            // Store member value
            if (typeof dimValue === 'object' && dimValue !== null) {
                const serialized = JSON.stringify(dimValue);
                data.members.add(serialized);
                data.values.push(dimValue);
            } else {
                data.members.add(dimValue);
                data.values.push(dimValue);
            }
        }
    }
    
    // Generate summary for each dimension
    const summaries = [];
    
    for (const [dimName, data] of dimensionData.entries()) {
        const summary = generateDimensionSummary(dimName, data.members, data.values);
        summaries.push(summary);
    }
    
    // Sort by dimension name for consistency
    return summaries.sort((a, b) => a.dimensionName.localeCompare(b.dimensionName));
}

/**
 * Generates summary for a specific dimension
 * @param {string} dimensionName - Dimension QName
 * @param {Set} members - Set of unique member values
 * @param {Array} values - Array of all member values
 * @returns {Object} - factSourceDimensionSummary object
 */
function generateDimensionSummary(dimensionName, members, values) {
    const isTyped = isTypedDimension(dimensionName, values);
    const sampleMembers = generateSampleMembers(members, isTyped);
    const memberRange = isTyped ? calculateMemberRange(values) : undefined;
    
    return {
        dimensionName: dimensionName,
        memberCount: members.size,
        isTyped: isTyped,
        sampleMembers: sampleMembers,
        memberRange: memberRange
    };
}

/**
 * Determines if a dimension uses typed domain
 * @param {string} dimensionName - Dimension QName
 * @param {Array} values - Array of member values
 * @returns {boolean} - True if typed dimension
 */
function isTypedDimension(dimensionName, values) {
    // Core dimensions with typed values
    if (dimensionName === 'xbrl:period') {
        return true;
    }
    
    // Check if values are primitive types (not QNames)
    if (values.length === 0) return false;
    
    const firstValue = values[0];
    
    // If it's a complex object (like period), it's typed
    if (typeof firstValue === 'object' && firstValue !== null) {
        return true;
    }
    
    // If it's a string that looks like a QName (prefix:localName), it's explicit
    if (typeof firstValue === 'string' && firstValue.includes(':')) {
        return false; // Explicit member
    }
    
    // Otherwise assume typed (numbers, dates, simple strings)
    return true;
}

/**
 * Generates sample members (up to 100)
 * @param {Set} members - Set of unique members
 * @param {boolean} isTyped - Whether dimension is typed
 * @returns {Array} - Sample members (up to 100)
 */
function generateSampleMembers(members, isTyped) {
    const memberArray = Array.from(members);
    
    // Limit to 100 samples
    const samples = memberArray.slice(0, 100);
    
    // For typed dimensions with many values, prefer distributed sampling
    if (isTyped && memberArray.length > 100) {
        return distributedSample(memberArray, 100);
    }
    
    return samples;
}

/**
 * Creates a distributed sample from an array
 * @param {Array} array - Source array
 * @param {number} count - Number of samples
 * @returns {Array} - Distributed sample
 */
function distributedSample(array, count) {
    if (array.length <= count) {
        return array;
    }
    
    const step = array.length / count;
    const samples = [];
    
    for (let i = 0; i < count; i++) {
        const index = Math.floor(i * step);
        samples.push(array[index]);
    }
    
    return samples;
}

/**
 * Calculates min/max range for typed dimensions with orderable values
 * @param {Array} values - Array of values
 * @returns {Object|undefined} - {min, max} or undefined if not orderable
 */
function calculateMemberRange(values) {
    if (values.length === 0) return undefined;
    
    // Check if values are orderable (numbers or dates)
    const firstValue = values[0];
    
    if (typeof firstValue === 'number') {
        const numbers = values.filter(v => typeof v === 'number');
        if (numbers.length === 0) return undefined;
        
        return {
            min: Math.min(...numbers),
            max: Math.max(...numbers)
        };
    }
    
    // Try to parse as dates
    if (typeof firstValue === 'string') {
        const dates = values
            .map(v => typeof v === 'string' ? new Date(v) : null)
            .filter(d => d && !isNaN(d.getTime()));
        
        if (dates.length > 0) {
            const timestamps = dates.map(d => d.getTime());
            return {
                min: new Date(Math.min(...timestamps)).toISOString(),
                max: new Date(Math.max(...timestamps)).toISOString()
            };
        }
    }
    
    // For complex objects, check if they have numeric or date properties
    if (typeof firstValue === 'object' && firstValue !== null) {
        // Handle period objects with start/end dates
        if (firstValue.start || firstValue.end || firstValue.instant) {
            return calculatePeriodRange(values);
        }
    }
    
    return undefined;
}

/**
 * Calculates date range for period dimension
 * @param {Array} periods - Array of period objects
 * @returns {Object|undefined} - {min, max} dates
 */
function calculatePeriodRange(periods) {
    const dates = [];
    
    for (const period of periods) {
        if (typeof period !== 'object' || period === null) continue;
        
        if (period.instant) {
            dates.push(new Date(period.instant));
        }
        if (period.start) {
            dates.push(new Date(period.start));
        }
        if (period.end) {
            dates.push(new Date(period.end));
        }
    }
    
    const validDates = dates.filter(d => !isNaN(d.getTime()));
    if (validDates.length === 0) return undefined;
    
    const timestamps = validDates.map(d => d.getTime());
    return {
        min: new Date(Math.min(...timestamps)).toISOString(),
        max: new Date(Math.max(...timestamps)).toISOString()
    };
}

/**
 * Checks if a factSource is relevant to a cube based on metadata
 * @param {Object} metadata - factSourceMetadata object
 * @param {Object} cube - Cube object
 * @returns {boolean} - True if factSource might contain relevant facts
 */
function isFactSourceRelevantToCube(metadata, cube) {
    if (!metadata || !cube) return false;
    
    // Check if any concepts in the factSource match concepts in the cube
    const cubeConcepts = extractCubeConceptDomain(cube);
    if (cubeConcepts && cubeConcepts.length > 0) {
        const hasMatchingConcept = metadata.concepts.some(c => cubeConcepts.includes(c));
        if (!hasMatchingConcept) {
            return false; // No matching concepts
        }
    }
    
    // Check if dimensions are compatible
    const cubeDimensions = cube.cubeDimensions || [];
    const factSourceDimensions = metadata.dimensions.map(d => d.dimensionName);
    
    // All required cube dimensions must be present in factSource
    for (const cubeDim of cubeDimensions) {
        const dimName = cubeDim.dimensionName;
        if (!factSourceDimensions.includes(dimName)) {
            // Dimension missing - check if optional
            if (!cubeDim.allowDomainFacts) {
                return false; // Required dimension missing
            }
        }
    }
    
    return true;
}

/**
 * Extracts concept domain from cube
 * @param {Object} cube - Cube object
 * @returns {Array|null} - Array of concept QNames or null if unrestricted
 */
function extractCubeConceptDomain(cube) {
    if (!cube.cubeDimensions) return null;
    
    const conceptDim = cube.cubeDimensions.find(d => d.dimensionName === 'xbrl:concept');
    if (!conceptDim || !conceptDim.domainName) {
        return null; // Unrestricted concept domain
    }
    
    // Would need to resolve domain members from taxonomy
    // For now return null - implementation would query domain structure
    return null;
}

// Export functions
export {
    generateFactMetadata,
    extractUniqueConcepts,
    generateDimensionSummaries,
    isFactSourceRelevantToCube
};
