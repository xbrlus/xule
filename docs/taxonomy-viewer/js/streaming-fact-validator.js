/**
 * Streaming Fact Validator
 * 
 * Validates facts in streaming fashion without storing all in memory.
 * Accumulates validation errors and basic statistics while processing.
 */

/**
 * Calendar-aware date/dateTime validator.
 * Uses regex + days-in-month arithmetic rather than new Date() so that
 * out-of-range day values such as 2020-06-31 (June has 30 days) are
 * correctly rejected instead of being silently rolled over.
 *
 * @param {*} value - Value to check
 * @param {string} dataType - xs:date or xs:dateTime (or any string containing 'dateTime' or 'date')
 * @returns {boolean} true if the value is a valid calendar date for the given type
 */
function isValidXSDateValue(value, dataType) {
    const str = String(value);
    const isDateTime = dataType === 'xs:dateTime' || dataType.includes('dateTime');

    if (isDateTime) {
        // xs:dateTime must match YYYY-MM-DDThh:mm:ss with optional fractional seconds and timezone
        if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$/.test(str)) return false;
        const m = str.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/);
        if (!m) return false;
        const year = parseInt(m[1], 10), month = parseInt(m[2], 10), day = parseInt(m[3], 10);
        const hour = parseInt(m[4], 10), minute = parseInt(m[5], 10), second = parseInt(m[6], 10);
        if (month < 1 || month > 12) return false;
        if (hour > 23 || minute > 59 || second > 59) return false;
        if (day < 1) return false;
        const leap = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
        return day <= [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
    }

    // xs:date must match YYYY-MM-DD with optional timezone
    if (!/^\d{4}-\d{2}-\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(str)) return false;
    const m = str.match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return false;
    const year = parseInt(m[1], 10), month = parseInt(m[2], 10), day = parseInt(m[3], 10);
    if (month < 1 || month > 12) return false;
    if (day < 1) return false;
    const leap = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
    return day <= [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
}

class StreamingFactValidator {
    /**
     * Creates a new streaming validator
     * @param {Object} taxonomy - The taxonomy model
     * @param {Object} options - Validation options
     */
    constructor(taxonomy, options = {}) {
        this.taxonomy = taxonomy;
        this.options = {
            validateConcepts: options.validateConcepts !== false,
            validateDimensions: options.validateDimensions !== false,
            validateDataTypes: options.validateDataTypes !== false,
            maxErrors: options.maxErrors || 1000,
            ...options
        };
        
        this.validationErrors = [];
        this.factCount = 0;
        this.errorCount = 0;
        
        // Cache frequently accessed taxonomy objects
        this.conceptMap = this.buildConceptMap();
        this.dimensionMap = this.buildDimensionMap();
    }
    
    /**
     * Builds a map of concepts for fast lookup
     * @returns {Map} - Map of concept QName to concept object
     */
    buildConceptMap() {
        const map = new Map();
        if (this.taxonomy && this.taxonomy.concepts) {
            for (const concept of this.taxonomy.concepts) {
                if (concept.name) {
                    map.set(concept.name, concept);
                }
            }
        }
        return map;
    }
    
    /**
     * Builds a map of dimensions for fast lookup
     * @returns {Map} - Map of dimension QName to dimension object
     */
    buildDimensionMap() {
        const map = new Map();
        if (this.taxonomy && this.taxonomy.dimensions) {
            for (const dimension of this.taxonomy.dimensions) {
                if (dimension.name) {
                    map.set(dimension.name, dimension);
                }
            }
        }
        return map;
    }
    
    /**
     * Validates a single fact
     * @param {Object} fact - Fact object to validate
     * @param {number} factIndex - Index of the fact (for error reporting)
     * @returns {boolean} - True if valid, false if errors found
     */
    validate(fact, factIndex = null) {
        this.factCount++;
        
        if (!fact) {
            this.addError('missingFact', 'Fact is null or undefined', factIndex);
            return false;
        }
        
        let isValid = true;
        
        // Validate fact dimensions
        if (this.options.validateDimensions) {
            if (!this.validateFactDimensions(fact, factIndex)) {
                isValid = false;
            }
        }
        
        // Validate concept
        if (this.options.validateConcepts) {
            if (!this.validateFactConcept(fact, factIndex)) {
                isValid = false;
            }
        }
        
        // Validate data type
        if (this.options.validateDataTypes) {
            if (!this.validateFactDataType(fact, factIndex)) {
                isValid = false;
            }
        }
        
        // Validate fact values
        if (!this.validateFactValues(fact, factIndex)) {
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Validates fact dimensions
     * @param {Object} fact - Fact object
     * @param {number} factIndex - Fact index
     * @returns {boolean} - True if valid
     */
    validateFactDimensions(fact, factIndex) {
        if (!fact.factDimensions) {
            this.addError('missingFactDimensions', 'Fact has no factDimensions property', factIndex, fact);
            return false;
        }
        
        let isValid = true;
        
        // Validate each dimension
        for (const [dimName, dimValue] of Object.entries(fact.factDimensions)) {
            // Check if dimension exists in taxonomy (for non-core dimensions)
            if (!dimName.startsWith('xbrl:')) {
                if (!this.dimensionMap.has(dimName)) {
                    this.addError('undefinedDimension', `Dimension ${dimName} not defined in taxonomy`, factIndex, fact);
                    isValid = false;
                }
            }
            
            // Validate dimension value is not empty
            if (dimValue === null || dimValue === undefined || dimValue === '') {
                this.addError('emptyDimensionValue', `Dimension ${dimName} has empty value`, factIndex, fact);
                isValid = false;
            }
        }
        
        // Check for required core dimensions
        if (!fact.factDimensions['xbrl:concept']) {
            this.addError('missingConceptDimension', 'Fact missing xbrl:concept dimension', factIndex, fact);
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Validates fact concept
     * @param {Object} fact - Fact object
     * @param {number} factIndex - Fact index
     * @returns {boolean} - True if valid
     */
    validateFactConcept(fact, factIndex) {
        const conceptName = fact.factDimensions && fact.factDimensions['xbrl:concept'];
        
        if (!conceptName) {
            return false; // Already reported by validateFactDimensions
        }
        
        // Check if concept exists in taxonomy
        if (!this.conceptMap.has(conceptName)) {
            this.addError('undefinedConcept', `Concept ${conceptName} not defined in taxonomy`, factIndex, fact);
            return false;
        }
        
        return true;
    }
    
    /**
     * Validates fact data type
     * @param {Object} fact - Fact object
     * @param {number} factIndex - Fact index
     * @returns {boolean} - True if valid
     */
    validateFactDataType(fact, factIndex) {
        const conceptName = fact.factDimensions && fact.factDimensions['xbrl:concept'];
        if (!conceptName) return false;
        
        const concept = this.conceptMap.get(conceptName);
        if (!concept || !concept.dataType) return true; // Can't validate without concept/dataType
        
        // Get fact value
        if (!fact.factValues || fact.factValues.length === 0) {
            return true; // No value to validate
        }
        
        const factValue = fact.factValues[0];
        if (factValue.value === null || factValue.value === undefined) {
            return true; // Nil value
        }
        
        // Basic type validation
        const dataType = concept.dataType;
        const value = factValue.value;
        
        // This would need to integrate with qname-validator.js for full validation
        // For now, do basic checks
        
        if (dataType.includes('decimal') || dataType.includes('integer')) {
            if (typeof value !== 'number' && isNaN(Number(value))) {
                this.addError('invalidDataType', `Value ${value} is not numeric for concept ${conceptName} with type ${dataType}`, factIndex, fact);
                return false;
            }
        }
        
        if (dataType.includes('date')) {
            if (!isValidXSDateValue(value, dataType)) {
                this.addError('invalidDataType', `Value '${value}' is not a valid date for concept '${conceptName}' with type '${dataType}'`, factIndex, fact);
                return false;
            }
        }
        
        return true;
    }
    
    /**
     * Validates fact values
     * @param {Object} fact - Fact object
     * @param {number} factIndex - Fact index
     * @returns {boolean} - True if valid
     */
    validateFactValues(fact, factIndex) {
        if (!fact.factValues || fact.factValues.length === 0) {
            // Facts without values are allowed (e.g., for structure)
            return true;
        }
        
        let isValid = true;
        
        for (const factValue of fact.factValues) {
            // Validate factValue has name
            if (!factValue.name) {
                this.addError('missingFactValueName', 'FactValue missing name property', factIndex, fact);
                isValid = false;
            }
            
            // Validate decimals for numeric facts
            if (factValue.decimals !== undefined) {
                if (typeof factValue.decimals !== 'number') {
                    this.addError('invalidDecimals', `Decimals value ${factValue.decimals} is not a number`, factIndex, fact);
                    isValid = false;
                }
            }
            
            // Validate language format
            if (factValue.language !== undefined) {
                if (typeof factValue.language !== 'string' || factValue.language.length === 0) {
                    this.addError('invalidLanguage', `Language value ${factValue.language} is not a valid string`, factIndex, fact);
                    isValid = false;
                }
            }
        }
        
        return isValid;
    }
    
    /**
     * Adds a validation error
     * @param {string} errorCode - Error code
     * @param {string} message - Error message
     * @param {number} factIndex - Fact index
     * @param {Object} fact - Fact object (optional)
     */
    addError(errorCode, message, factIndex, fact = null) {
        if (this.errorCount >= this.options.maxErrors) {
            if (this.errorCount === this.options.maxErrors) {
                this.validationErrors.push({
                    errorCode: 'maxErrorsReached',
                    message: `Maximum error count (${this.options.maxErrors}) reached. Additional errors not reported.`,
                    factIndex: null
                });
            }
            this.errorCount++;
            return;
        }
        
        this.validationErrors.push({
            errorCode,
            message,
            factIndex,
            factName: fact && fact.name ? fact.name : undefined,
            concept: fact && fact.factDimensions ? fact.factDimensions['xbrl:concept'] : undefined
        });
        
        this.errorCount++;
    }
    
    /**
     * Gets validation errors
     * @returns {Array} - Array of error objects
     */
    getErrors() {
        return this.validationErrors;
    }
    
    /**
     * Gets validation statistics
     * @returns {Object} - Statistics object
     */
    getStatistics() {
        return {
            factsProcessed: this.factCount,
            errorsFound: this.errorCount,
            hasErrors: this.errorCount > 0,
            maxErrorsReached: this.errorCount >= this.options.maxErrors
        };
    }
    
    /**
     * Checks if validation passed
     * @returns {boolean} - True if no errors
     */
    isValid() {
        return this.errorCount === 0;
    }
    
    /**
     * Resets the validator
     */
    reset() {
        this.validationErrors = [];
        this.factCount = 0;
        this.errorCount = 0;
    }
}

// Export class
export { StreamingFactValidator };
