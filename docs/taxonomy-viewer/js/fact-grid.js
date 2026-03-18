/**
 * Module for displaying fact grid views
 * Shows all cubes that contain a fact and highlights the relevant cells
 * 
 * Updated to handle dimensions with no domainName specified in cubeDimensions:
 * - If a cubeDimension has no domainName, the fact is included in the cube if
 *   the fact value's type matches one of the allowedDomainItems in the dimension's domainClass
 */

import { getTaxonomyData } from './main.js';
import { getXbrlModel } from './utils.js';

/**
 * Parse a period string into start and end dates
 * Duration format: "yyyy-mm-ddT00:00:00/yyyy-mm-ddT00:00:00"
 * Instant format: "yyyy-mm-ddT00:00:00"
 * @param {string} periodString - The period string from the fact
 * @returns {Object} Object with periodType ('instant' or 'duration'), startDate, and endDate
 */
function parsePeriodString(periodString) {
    if (!periodString) return null;
    
    // Check if it's a duration (contains '/')
    if (periodString.includes('/')) {
        const [start, end] = periodString.split('/');
        return {
            periodType: 'duration',
            startDate: new Date(start),
            endDate: new Date(end)
        };
    } else {
        // It's an instant
        const date = new Date(periodString);
        return {
            periodType: 'instant',
            startDate: date,
            endDate: date
        };
    }
}

/**
 * Calculate duration in milliseconds between two dates
 * @param {Date} date1 
 * @param {Date} date2 
 * @returns {number} Duration in milliseconds
 */
function calculateDuration(date1, date2) {
    return Math.abs(date2.getTime() - date1.getTime());
}

/**
 * Parse ISO 8601 duration string (e.g., "P1Y", "P1M", "P1D")
 * Returns approximate milliseconds for comparison
 * @param {string} durationStr - ISO 8601 duration string
 * @returns {number} Approximate milliseconds
 */
function parseDuration(durationStr) {
    if (!durationStr || !durationStr.startsWith('P')) return 0;
    
    const yearMatch = durationStr.match(/(\d+)Y/);
    const monthMatch = durationStr.match(/(\d+)M/);
    const dayMatch = durationStr.match(/(\d+)D/);
    
    let ms = 0;
    if (yearMatch) ms += parseInt(yearMatch[1]) * 365.25 * 24 * 60 * 60 * 1000;
    if (monthMatch) ms += parseInt(monthMatch[1]) * 30.44 * 24 * 60 * 60 * 1000;
    if (dayMatch) ms += parseInt(dayMatch[1]) * 24 * 60 * 60 * 1000;
    
    return ms;
}

/**
 * Match a Date (UTC) against a single date/time pattern token string.
 * Pattern tokens: YYYY, MM, DD, hh, mm, ss, eom  (all others are treated as literal values).
 * Returns an object of wildcard captures { YYYY, MM, ... } on success, or null on mismatch.
 * @param {Date} date - UTC date to test
 * @param {string} pattern - e.g. "YYYY-12-31" or "YYYY-MM-eoMT00:00:00"
 * @returns {Object|null}
 */
function matchDatePattern(date, pattern) {
    const tIdx = pattern.indexOf('T');
    const datePart = tIdx >= 0 ? pattern.substring(0, tIdx) : pattern;
    const timePart = tIdx >= 0 ? pattern.substring(tIdx + 1) : null;

    const dateTokens = datePart.split('-');
    const year  = date.getUTCFullYear();
    const month = date.getUTCMonth() + 1; // 1-indexed
    const day   = date.getUTCDate();
    const hours   = date.getUTCHours();
    const minutes = date.getUTCMinutes();
    const seconds = date.getUTCSeconds();

    const wildcards = {};

    // --- year ---
    if (dateTokens[0] === 'YYYY') {
        wildcards.YYYY = year;
    } else if (parseInt(dateTokens[0]) !== year) {
        return null;
    }

    // --- month ---
    if (dateTokens.length > 1) {
        if (dateTokens[1] === 'MM') {
            wildcards.MM = month;
        } else if (parseInt(dateTokens[1]) !== month) {
            return null;
        }
    }

    // --- day (supports literal, DD wildcard, and eom) ---
    if (dateTokens.length > 2) {
        const dayToken = dateTokens[2];
        if (dayToken === 'DD') {
            wildcards.DD = day;
        } else if (dayToken.toLowerCase() === 'eom') {
            // Last day of the actual year/month
            const lastDay = new Date(Date.UTC(year, month, 0)).getUTCDate();
            if (day !== lastDay) return null;
            wildcards.eom = day;
        } else if (parseInt(dayToken) !== day) {
            return null;
        }
    }

    // --- time components ---
    if (timePart !== null) {
        const timeTokens = timePart.split(':');
        if (timeTokens[0] === 'hh') {
            wildcards.hh = hours;
        } else if (parseInt(timeTokens[0]) !== hours) {
            return null;
        }
        if (timeTokens.length > 1) {
            if (timeTokens[1] === 'mm') {
                wildcards.mm = minutes;
            } else if (parseInt(timeTokens[1]) !== minutes) {
                return null;
            }
        }
        if (timeTokens.length > 2) {
            if (timeTokens[2] === 'ss') {
                wildcards.ss = seconds;
            } else if (parseInt(timeTokens[2]) !== seconds) {
                return null;
            }
        }
    }

    return wildcards;
}

/**
 * Match a parsed fact period against a period pattern string.
 * Instant patterns (no '/') are tested against factPeriodInfo.endDate.
 * Duration patterns (with '/') test startDate against the left half and endDate against the right half.
 * Shared wildcards (YYYY, MM) in start/end patterns must resolve to the same value.
 * @param {Object} factPeriodInfo - from parsePeriodString()
 * @param {string} pattern - e.g. "YYYY-12-31" or "YYYY-MM-01/YYYY-MM-eom"
 * @returns {boolean}
 */
function matchesPeriodPattern(factPeriodInfo, pattern) {
    const isDuration = pattern.includes('/');
    if (isDuration) {
        if (factPeriodInfo.periodType !== 'duration') return false;
        const [startPat, endPat] = pattern.split('/');
        const startWilds = matchDatePattern(factPeriodInfo.startDate, startPat);
        if (startWilds === null) return false;
        const endWilds = matchDatePattern(factPeriodInfo.endDate, endPat);
        if (endWilds === null) return false;
        // Shared wildcards (year, month, day) must agree between start and end
        for (const key of ['YYYY', 'MM', 'DD']) {
            if (key in startWilds && key in endWilds && startWilds[key] !== endWilds[key]) return false;
        }
        return true;
    } else {
        if (factPeriodInfo.periodType !== 'instant') return false;
        return matchDatePattern(factPeriodInfo.endDate, pattern) !== null;
    }
}

/**
 * Check if a fact's period matches ANY of the period constraints (OR logic between constraints)
 * Within each constraint, ALL properties must match (AND logic within constraint)
 * @param {string} factPeriod - The period string from the fact
 * @param {Array} periodConstraints - Array of period constraint objects
 * @param {Object} taxonomy - The taxonomy object
 * @returns {boolean} True if the fact period matches at least one constraint
 */
function matchesPeriodConstraints(factPeriod, periodConstraints, taxonomy) {
    if (!factPeriod || !periodConstraints || periodConstraints.length === 0) {
        return true; // No constraints means all periods are allowed
    }
    
    const factPeriodInfo = parsePeriodString(factPeriod);
    if (!factPeriodInfo) return false;
    
    // Check if the fact matches ANY constraint (OR logic)
    return periodConstraints.some(constraint => {
        return matchesSinglePeriodConstraint(factPeriodInfo, constraint, taxonomy);
    });
}

/**
 * Check if a fact's period matches a single period constraint
 * All properties in the constraint must match (AND logic)
 * @param {Object} factPeriodInfo - Parsed period info from fact
 * @param {Object} constraint - Single period constraint object
 * @param {Object} taxonomy - The taxonomy object
 * @returns {boolean} True if all constraint properties match
 */
function matchesSinglePeriodConstraint(factPeriodInfo, constraint, taxonomy) {
    // Check periodType (required)
    if (constraint.periodType) {
        if (constraint.periodType !== factPeriodInfo.periodType) {
            return false;
        }
    }
    
    // Check timeSpan for duration facts
    if (constraint.timeSpan && factPeriodInfo.periodType === 'duration') {
        const expectedDuration = parseDuration(constraint.timeSpan);
        const actualDuration = calculateDuration(factPeriodInfo.startDate, factPeriodInfo.endDate);
        
        // Allow some tolerance (1 day) for duration matching
        const tolerance = 24 * 60 * 60 * 1000;
        if (Math.abs(expectedDuration - actualDuration) > tolerance) {
            return false;
        }
    }
    
    // Check endDate constraint
    if (constraint.endDate) {
        const constraintEndDates = resolveDateConstraint(constraint.endDate, taxonomy);
        if (constraintEndDates) {
            // For instant: check if fact date matches constraint date
            // For duration: check if fact end date matches constraint date
            const factEndDate = factPeriodInfo.endDate;
            
            // Use UTC for date-only comparison to avoid timezone issues
            const factEndDateOnly = Date.UTC(factEndDate.getUTCFullYear(), factEndDate.getUTCMonth(), factEndDate.getUTCDate());
            
            // If constraintEndDates is an array, check if fact matches ANY of them (OR logic)
            const datesToCheck = Array.isArray(constraintEndDates) ? constraintEndDates : [constraintEndDates];
            const matchesAnyDate = datesToCheck.some(constraintEndDate => {
                const constraintEndDateOnly = Date.UTC(constraintEndDate.getUTCFullYear(), constraintEndDate.getUTCMonth(), constraintEndDate.getUTCDate());
                
                // Check for exact date match
                if (factEndDateOnly === constraintEndDateOnly) {
                    return true;
                }
                
                // Check if fact is at start of next day (00:00:00) which equals end of constraint date
                // Example: 2026-01-01T00:00:00 equals 2025-12-31T24:00:00 (end of 2025-12-31)
                // For instant periods, a timestamp at midnight represents the END of the previous day
                if (factPeriodInfo.periodType === 'instant' && 
                    factEndDate.getHours() === 0 && factEndDate.getMinutes() === 0 && factEndDate.getSeconds() === 0 && factEndDate.getMilliseconds() === 0) {
                    // Fact is at midnight - check if it's exactly one day after constraint date
                    // Calculate the day after using UTC to avoid timezone issues
                    const oneDayMs = 24 * 60 * 60 * 1000;
                    const dayAfter = constraintEndDateOnly + oneDayMs;
                    
                    if (factEndDateOnly === dayAfter) {
                        return true; // Fact at start of next day = end of constraint date
                    }
                }
                
                return false;
            });
            
            if (!matchesAnyDate) {
                return false;
            }
        }
    }
    
    // Check startDate constraint
    if (constraint.startDate) {
        const constraintStartDates = resolveDateConstraint(constraint.startDate, taxonomy);
        if (constraintStartDates && factPeriodInfo.periodType === 'duration') {
            const factStartDate = factPeriodInfo.startDate;
            
            // Allow same-day matching
            const factStartDateOnly = new Date(factStartDate.getFullYear(), factStartDate.getMonth(), factStartDate.getDate());
            
            // If constraintStartDates is an array, check if fact matches ANY of them (OR logic)
            const datesToCheck = Array.isArray(constraintStartDates) ? constraintStartDates : [constraintStartDates];
            const matchesAnyDate = datesToCheck.some(constraintStartDate => {
                const constraintStartDateOnly = new Date(constraintStartDate.getFullYear(), constraintStartDate.getMonth(), constraintStartDate.getDate());
                return factStartDateOnly.getTime() === constraintStartDateOnly.getTime();
            });
            
            if (!matchesAnyDate) {
                return false;
            }
        }
    }
    
    // Check periodPattern (pattern matching for dates/durations)
    if (constraint.periodPattern) {
        if (!matchesPeriodPattern(factPeriodInfo, constraint.periodPattern)) {
            return false;
        }
    }
    
    // Check onOrAfter constraint
    if (constraint.onOrAfter) {
        const constraintDates = resolveDateConstraint(constraint.onOrAfter, taxonomy);
        if (constraintDates) {
            // For instant: fact date must be on or after constraint date
            // For duration: fact end date must be on or after constraint date
            const factDate = factPeriodInfo.endDate;
            
            // If constraintDates is an array, fact must be on or after ANY of them (OR logic)
            const datesToCheck = Array.isArray(constraintDates) ? constraintDates : [constraintDates];
            const matchesAnyDate = datesToCheck.some(constraintDate => factDate >= constraintDate);
            
            if (!matchesAnyDate) {
                return false;
            }
        }
    }
    
    // Check onOrBefore constraint
    if (constraint.onOrBefore) {
        const constraintDates = resolveDateConstraint(constraint.onOrBefore, taxonomy);
        if (constraintDates) {
            // For instant: fact date must be on or before constraint date
            // For duration: fact end date must be on or before constraint date
            const factDate = factPeriodInfo.endDate;
            
            // If constraintDates is an array, fact must be on or before ANY of them (OR logic)
            const datesToCheck = Array.isArray(constraintDates) ? constraintDates : [constraintDates];
            const matchesAnyDate = datesToCheck.some(constraintDate => factDate <= constraintDate);
            
            if (!matchesAnyDate) {
                return false;
            }
        }
    }
    
    // All constraints matched
    return true;
}

/**
 * Resolve a date constraint object to an actual Date or array of Dates
 * Supports value, conceptName, context, and timeShift
 * @param {Object} dateConstraint - Date resolution object
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Date|Date[]|null} Resolved date(s) or null
 */
function resolveDateConstraint(dateConstraint, taxonomy) {
    if (!dateConstraint) return null;
    
    let resolvedDates = null;
    
    // Priority: value > conceptName > context
    if (dateConstraint.value) {
        // Literal date value
        resolvedDates = [new Date(dateConstraint.value)];
    } else if (dateConstraint.conceptName) {
        // Look up fact values for this concept in the taxonomy's facts
        if (taxonomy.facts) {
            const conceptFacts = taxonomy.facts.filter(fs => 
                fs.factDimensions && fs.factDimensions['xbrl:concept'] === dateConstraint.conceptName
            );
            
            if (conceptFacts.length > 0) {
                // Extract unique date values from factValues
                const dateSet = new Set();
                conceptFacts.forEach(fact => {
                    if (fact.factValues && fact.factValues.length > 0) {
                        fact.factValues.forEach(fv => {
                            if (fv.value) {
                                dateSet.add(fv.value);
                            }
                        });
                    }
                });
                
                if (dateSet.size > 0) {
                    resolvedDates = Array.from(dateSet).map(dateStr => new Date(dateStr));
                } else {
                    console.warn('[Period Constraints] No fact values found for conceptName:', dateConstraint.conceptName);
                    return null;
                }
            } else {
                console.warn('[Period Constraints] No facts found with concept:', dateConstraint.conceptName);
                return null;
            }
        } else {
            console.warn('[Period Constraints] No facts available in taxonomy for conceptName resolution:', dateConstraint.conceptName);
            return null;
        }
    } else if (dateConstraint.context) {
        // Context-based date resolution
        // Extract concept name and suffix (@start or @end)
        const contextMatch = dateConstraint.context.match(/^(.+?)(@(start|end))?$/);
        if (contextMatch) {
            const conceptName = contextMatch[1];
            const suffix = contextMatch[3] || 'end'; // default to 'end' if no suffix
            
            if (taxonomy.facts) {
                const conceptFacts = taxonomy.facts.filter(fs => 
                    fs.factDimensions && fs.factDimensions['xbrl:concept'] === conceptName
                );
                
                if (conceptFacts.length > 0) {
                    const dateSet = new Set();
                    conceptFacts.forEach(fact => {
                        if (fact.factDimensions && fact.factDimensions['xbrl:period']) {
                            const periodInfo = parsePeriodString(fact.factDimensions['xbrl:period']);
                            if (periodInfo) {
                                const date = suffix === 'start' ? periodInfo.startDate : periodInfo.endDate;
                                dateSet.add(date.toISOString());
                            }
                        }
                    });
                    
                    if (dateSet.size > 0) {
                        resolvedDates = Array.from(dateSet).map(dateStr => new Date(dateStr));
                    } else {
                        console.warn('[Period Constraints] No period values found for context:', dateConstraint.context);
                        return null;
                    }
                } else {
                    console.warn('[Period Constraints] No facts found with concept for context:', conceptName);
                    return null;
                }
            }
        } else {
            console.warn('[Period Constraints] Invalid context format:', dateConstraint.context);
            return null;
        }
    }
    
    if (!resolvedDates) return null;
    
    // Apply timeShift if present to all resolved dates
    if (dateConstraint.timeShift) {
        const shiftMs = parseDuration(dateConstraint.timeShift);
        resolvedDates = resolvedDates.map(date => {
            if (dateConstraint.timeShift.startsWith('-')) {
                return new Date(date.getTime() - shiftMs);
            } else {
                return new Date(date.getTime() + shiftMs);
            }
        });
    }
    
    // If only one date, return it directly; otherwise return the array
    return resolvedDates.length === 1 ? resolvedDates[0] : resolvedDates;
}

/**
 * Find all cubes that contain the given fact
 * Checks both dimensional presence and value type compatibility:
 * - For dimensions with domainName: fact must be in that domain
 * - For dimensions without domainName: fact value type must match allowedDomainItems
 * 
 * @param {Object} fact - The fact object
 * @param {Object} taxonomy - The taxonomy object
 * @returns {Array} Array of cube objects that contain this fact
 */
function findCubesForFact(fact, taxonomy) {
    if (!taxonomy.cubes || !fact.factDimensions) {
        return [];
    }
    
    const matchingCubes = [];
    const factDimensions = Object.keys(fact.factDimensions);
    
    const DEBUG = false; // Set to true to enable detailed logging
    
    if (DEBUG) {
        console.log(`[Fact Grid] Checking fact ${fact.name} against all cubes`);
        console.log(`[Fact Grid] Fact dimensions:`, fact.factDimensions);
    }
    
    taxonomy.cubes.forEach(cube => {
        if (!cube.cubeDimensions) return;
        
        // Check if this is a open cube (concept dimension implicitly includes all concepts)
        const isDefaultCube = cube.cubeType === 'xbrl:openCube';
        
        // Check if cube has all the dimensions from the fact
        const cubeDimensionNames = cube.cubeDimensions.map(d => d.dimensionName);
        const hasAllDimensions = factDimensions.every(dimName => 
            cubeDimensionNames.includes(dimName)
        );
        
        if (!hasAllDimensions) return;
        
        // Check if the fact has all REQUIRED dimensions from the cube
        // A dimension is required if allowDomainFacts is not true
        const hasAllRequiredDimensions = cube.cubeDimensions.every(cubeDim => {
            const allowDomainFacts = cubeDim.allowDomainFacts === true;
            const factHasDimension = factDimensions.includes(cubeDim.dimensionName);
            
            // If allowDomainFacts is true, dimension is optional (can be missing)
            // If allowDomainFacts is false/undefined, dimension is required (must be present)
            if (!allowDomainFacts && !factHasDimension) {
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: Missing required dimension ${cubeDim.dimensionName} (allowDomainFacts not true)`);
                return false;
            }
            
            return true;
        });
        
        if (!hasAllRequiredDimensions) return;
        
        // For each dimension in the fact, check if the fact value is allowed in the cube
        const isFactAllowedInCube = factDimensions.every(dimName => {
            const factValue = fact.factDimensions[dimName];
            const cubeDimension = cube.cubeDimensions.find(cd => cd.dimensionName === dimName);
            
            if (!cubeDimension) return false;
            
            // Special handling for xbrl:period dimension with periodConstraints
            if (dimName === 'xbrl:period') {
                // If periodConstraints are defined, check if the fact's period matches any constraint
                if (cubeDimension.periodConstraints && cubeDimension.periodConstraints.length > 0) {
                    const periodMatches = matchesPeriodConstraints(factValue, cubeDimension.periodConstraints, taxonomy);
                    if (!periodMatches) {
                        console.log(`[Fact Grid] ${cube.name}: Fact ${fact.name} period "${factValue}" does NOT match any period constraints`);
                    }
                    if (DEBUG) {
                        console.log(`[Fact Grid] ${cube.name}: Fact ${fact.name} period "${factValue}" matches constraints = ${periodMatches}`);
                        console.log(`[Fact Grid] ${cube.name}: period constraints:`, cubeDimension.periodConstraints);
                    }
                    return periodMatches;
                }
                // If no periodConstraints defined, any period is allowed
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: period "${factValue}" - no constraints, allowing`);
                return true;
            }
            
            // For defaultCube, the concept dimension implicitly includes all concepts in the taxonomy
            // So skip domain validation for the concept dimension in defaultCubes
            if (isDefaultCube && dimName === 'xbrl:concept') {
                // Check if the factValue is a valid concept in the taxonomy
                const isConcept = taxonomy.concepts?.some(c => c.name === factValue) ||
                                  taxonomy.abstracts?.some(a => a.name === factValue);
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: defaultCube concept check for "${factValue}" = ${isConcept}`);
                return isConcept;
            }
            
            // If cubeDimension has a domainName, check if the fact value is in that domain
            if (cubeDimension.domainName) {
                // Find the domain
                const domain = taxonomy.domains?.find(d => d.name === cubeDimension.domainName);
                if (!domain) {
                    // Domain not found, conservatively reject
                    if (DEBUG) console.log(`[Fact Grid] ${cube.name}: ${dimName} domainName ${cubeDimension.domainName} not found - rejecting fact`);
                    return false;
                }
                
                // Check if the fact value is in the domain
                // It could be in roots or as a source/target in relationships
                let inDomain = false;
                
                if (domain.roots && domain.roots.includes(factValue)) {
                    inDomain = true;
                }
                
                if (!inDomain && domain.relationships) {
                    inDomain = domain.relationships.some(rel => 
                        rel.source === factValue || rel.target === factValue
                    );
                }
                
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: ${dimName} value "${factValue}" in domain ${cubeDimension.domainName} = ${inDomain}`);
                return inDomain;
            }
            
            // If no domainName is specified, check if fact value type matches allowedDomainItems
            // Find the dimension definition to get its domainClass
            const dimension = taxonomy.dimensions?.find(d => d.name === dimName);
            if (!dimension || !dimension.domainClass) {
                // If no dimension definition or domainClass, allow the fact
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: ${dimName} has no dimension definition or domainClass - allowing fact`);
                return true;
            }
            
            // Find the domainClass definition
            const domainClass = taxonomy.domainClasses?.find(dr => dr.name === dimension.domainClass);
            if (!domainClass || !domainClass.allowedDomainItems) {
                // If no domainClass or no allowedDomainItems, allow the fact
                if (DEBUG) console.log(`[Fact Grid] ${cube.name}: ${dimName} domainClass ${dimension.domainClass} has no allowedDomainItems - allowing fact`);
                return true;
            }
            
            // Check if the fact value type matches one of the allowedDomainItems
            const allowed = isFactValueTypeAllowed(factValue, domainClass.allowedDomainItems, taxonomy);
            if (DEBUG) console.log(`[Fact Grid] ${cube.name}: ${dimName} fact value "${factValue}" type check = ${allowed}, allowedDomainItems:`, domainClass.allowedDomainItems);
            return allowed;
        });
        
        if (isFactAllowedInCube) {
            matchingCubes.push(cube);
        }
    });
    
    return matchingCubes;
}

/**
 * Check if a fact value's type matches any of the allowed domain items
 * @param {*} factValue - The fact value from the fact
 * @param {Array<string>} allowedDomainItems - Array of allowed types (e.g., ["xs:token", "xbrl:memberObject"])
 * @param {Object} taxonomy - The taxonomy object
 * @returns {boolean} True if the value type is allowed
 */
function isFactValueTypeAllowed(factValue, allowedDomainItems, taxonomy) {
    // If factValue is a string, check if it's a QName that references an object
    if (typeof factValue === 'string') {
        // Check if it matches allowed primitive types
        if (allowedDomainItems.includes('xs:string') || 
            allowedDomainItems.includes('xs:token') ||
            allowedDomainItems.includes('xs:dateTime') ||
            allowedDomainItems.includes('xs:date') ||
            allowedDomainItems.includes('xs:time')) {
            return true;
        }
        
        // Check if it's a QName referencing a member object
        if (allowedDomainItems.includes('xbrl:memberObject')) {
            // Check if the factValue is a defined member
            const isMember = taxonomy.members?.some(m => m.name === factValue);
            if (isMember) return true;
        }
        
        // Check if it's a QName referencing a concept object
        if (allowedDomainItems.includes('xbrl:conceptObject')) {
            const isConcept = taxonomy.concepts?.some(c => c.name === factValue);
            if (isConcept) return true;
        }
        
        // Check other object types as needed
        if (allowedDomainItems.includes('xbrl:entityObject')) {
            const isEntity = taxonomy.entities?.some(e => e.name === factValue);
            if (isEntity) return true;
        }
        
        if (allowedDomainItems.includes('xbrl:unitObject')) {
            const isUnit = taxonomy.units?.some(u => u.name === factValue);
            if (isUnit) return true;
        }
    }
    
    // If we get here, assume it's allowed (conservative approach)
    return true;
}

/**
 * Show grid views for all cubes containing the fact
 * @param {Object} fact - The fact object
 * @param {Object} taxonomy - The taxonomy object
 */
export function showFactGrids(fact, taxonomy) {
    console.log('[Fact Grid] Showing grids for fact:', fact.name);
    
    const taxonomyData = getTaxonomyData();
    if (!taxonomyData) {
        console.error('[Fact Grid] No taxonomy data available');
        return;
    }
    
    // Activate the Grid View tab
    const detailsTabs = document.getElementById('details-tabs');
    const gridTab = document.getElementById('grid-tab');
    const propertiesTab = document.getElementById('properties-tab');
    
    if (detailsTabs && gridTab && propertiesTab) {
        // Show tabs
        detailsTabs.style.display = 'flex';
        
        // Activate grid tab
        document.querySelectorAll('.details-tab-button').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.detailsTab === 'grid') {
                btn.classList.add('active');
            }
        });
        
        propertiesTab.classList.remove('active');
        gridTab.classList.add('active');
    }
    
    // Find all cubes that contain this fact
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Fact Grid] No xbrlModel available in taxonomy data');
        return;
    }
    const matchingCubes = findCubesForFact(fact, xbrlModel);
    
    const gridContent = document.getElementById('cube-grid-content');
    if (!gridContent) {
        console.warn('[Fact Grid] cube-grid-content container not found');
        return;
    }
    
    gridContent.innerHTML = '';
    
    if (matchingCubes.length === 0) {
        gridContent.innerHTML = `
            <div style="padding: 20px;">
                <h3>No Cubes Found</h3>
                <p>No cubes contain all dimensions from this fact.</p>
            </div>
        `;
        return;
    }
    
    // Add header
    const header = document.createElement('div');
    header.style.padding = '10px 20px';
    header.style.backgroundColor = '#f5f5f5';
    header.style.borderBottom = '2px solid #ddd';
    
    // Build dimension info string
    let dimensionInfo = '';
    if (fact.factDimensions) {
        const dims = Object.entries(fact.factDimensions)
            .map(([key, value]) => `<strong>${key}</strong>: ${value}`)
            .join(', ');
        dimensionInfo = `<p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">Dimensions: ${dims}</p>`;
    }
    
    header.innerHTML = `
        <h3 style="margin: 0;">Fact: ${fact.name}</h3>
        ${dimensionInfo}
        <p style="margin: 5px 0 0 0; color: #666;">Found ${matchingCubes.length} cube(s) containing this fact</p>
    `;
    gridContent.appendChild(header);
    
    // Render each matching cube with highlighting
    matchingCubes.forEach(cube => {
        buildCubeGridWithHighlight(cube, fact, gridContent, taxonomyData);
    });
}

/**
 * Build concept tree structure from domain relationships
 * @param {Object} domain - Domain object with relationships
 * @returns {Array} Array of concept tree nodes
 */
function buildConceptTreeFromDomain(domain) {
    const childrenMap = {};
    const allNodes = new Set();
    
    if (domain.relationships) {
        domain.relationships.forEach(rel => {
            if (!childrenMap[rel.source]) {
                childrenMap[rel.source] = [];
            }
            childrenMap[rel.source].push({
                target: rel.target,
                order: rel.order || 0
            });
            allNodes.add(rel.source);
            allNodes.add(rel.target);
        });
        
        // Sort children by order
        Object.keys(childrenMap).forEach(source => {
            childrenMap[source].sort((a, b) => a.order - b.order);
        });
    }
    
    // Build tree starting from a node
    function buildTree(nodeName) {
        const children = childrenMap[nodeName] || [];
        return {
            name: nodeName,
            children: children.map(child => buildTree(child.target))
        };
    }
    
    // Start from root
    if (domain.root) {
        const rootChildren = childrenMap[domain.root] || [];
        return rootChildren.map(child => buildTree(child.target));
    }
    
    return [];
}

/**
 * Build a cube grid with highlighted cells for the fact
 * @param {Object} cube - Cube object
 * @param {Object} fact - Fact object
 * @param {HTMLElement} container - Container to append grid to
 * @param {Object} taxonomyData - Full taxonomy data
 */
function buildCubeGridWithHighlight(cube, fact, container, taxonomyData) {
    console.log('[Fact Grid] Building grid for cube:', cube.name);
    
    // Get xbrlModel from taxonomyData
    const xbrlModel = getXbrlModel(taxonomyData);
    if (!xbrlModel) {
        console.error('[Fact Grid] No xbrlModel available');
        return;
    }
    
    // Create cube section
    const cubeSection = document.createElement('div');
    cubeSection.style.marginBottom = '30px';
    cubeSection.style.padding = '10px';
    
    const cubeTitle = document.createElement('h4');
    cubeTitle.textContent = cube.name;
    cubeTitle.style.margin = '10px 0';
    cubeTitle.style.padding = '10px';
    cubeTitle.style.backgroundColor = '#e3f2fd';
    cubeTitle.style.borderLeft = '4px solid #2196f3';
    cubeSection.appendChild(cubeTitle);
    
    if (!cube.cubeDimensions || cube.cubeDimensions.length === 0) {
        cubeSection.innerHTML += '<p style="padding: 10px;">No dimensions defined for this cube.</p>';
        container.appendChild(cubeSection);
        return;
    }
    
    // Check if this is a default cube
    const isDefaultCube = cube.cubeType === 'xbrl:openCube';
    
    // Find the concept dimension
    const conceptDim = cube.cubeDimensions.find(d => d.dimensionName === 'xbrl:concept');
    if (!conceptDim) {
        cubeSection.innerHTML += '<p style="padding: 10px;">No concept dimension found for this cube.</p>';
        container.appendChild(cubeSection);
        return;
    }
    
    // For defaultCube, create an implicit domain containing all concepts
    let domain;
    let hasMoreConcepts = false;
    if (isDefaultCube) {
        // Build an implicit domain with limited concepts (max 10)
        // Always include the fact's concept if present
        domain = {
            name: 'xbrl:implicitConceptDomain',
            root: 'xbrl:conceptDomain',
            relationships: []
        };
        
        const maxConcepts = 10;
        const factConcept = fact.factDimensions['xbrl:concept'];
        const conceptsToAdd = new Set();
        
        // First, add the fact's concept if it exists
        if (factConcept) {
            conceptsToAdd.add(factConcept);
        }
        
        // Add abstracts up to limit
        if (xbrlModel && xbrlModel.abstracts) {
            for (const abs of xbrlModel.abstracts) {
                if (conceptsToAdd.size >= maxConcepts) break;
                conceptsToAdd.add(abs.name);
            }
        }
        
        // Add concepts up to limit
        if (xbrlModel && xbrlModel.concepts) {
            for (const concept of xbrlModel.concepts) {
                if (conceptsToAdd.size >= maxConcepts) break;
                conceptsToAdd.add(concept.name);
            }
        }
        
        // Check if there are more concepts than we're showing
        const totalConcepts = (xbrlModel?.abstracts?.length || 0) + 
                             (xbrlModel?.concepts?.length || 0);
        hasMoreConcepts = totalConcepts > maxConcepts;
        
        // Build relationships from the set
        conceptsToAdd.forEach(conceptName => {
            domain.relationships.push({
                source: 'xbrl:conceptDomain',
                target: conceptName
            });
        });
    } else {
        // For non-default cubes, require a domainName
        if (!conceptDim.domainName) {
            cubeSection.innerHTML += '<p style="padding: 10px;">No concept domain found for this cube.</p>';
            container.appendChild(cubeSection);
            return;
        }
        
        // Find the domain for the concept dimension
        domain = xbrlModel?.domains?.find(d => d.name === conceptDim.domainName);
        if (!domain || !domain.relationships || domain.relationships.length === 0) {
            cubeSection.innerHTML += '<p style="padding: 10px;">Concept domain not found or has no relationships.</p>';
            container.appendChild(cubeSection);
            return;
        }
    }
    
    // Get other dimensions (exclude concept)
    const otherDimensions = cube.cubeDimensions.filter(d => 
        d.dimensionName !== 'xbrl:concept'
    );
    
    // Build concept tree structure from domain
    const conceptTree = buildConceptTreeFromDomain(domain);
    
    // Build column definitions from the fact dimension values
    // Each column represents the combination of dimension values in the fact
    const columnDefs = [];
    
    // Get dimension values from fact
    const factDimValues = {};
    otherDimensions.forEach(dim => {
        const value = fact.factDimensions[dim.dimensionName];
        // Normalize: undefined or null both mean no value (domain fact)
        factDimValues[dim.dimensionName] = value !== undefined ? value : null;
    });
    
    // Create a single column for this fact's dimension combination
    columnDefs.push(factDimValues);
    
    // For each dimension, collect all possible members for display
    const dimensionMembers = [];
    for (const dim of otherDimensions) {
        const dimInfo = {
            dimension: dim,
            members: [],
            allowDomainFacts: dim.allowDomainFacts === true
        };
        
        // Find members for this dimension if it has a domain
        if (dim.domainName) {
            const dimDomain = xbrlModel?.domains?.find(d => d.name === dim.domainName);
            if (dimDomain && dimDomain.relationships) {
                // Extract all target members from domain relationships
                const memberSet = new Set();
                dimDomain.relationships.forEach(rel => {
                    memberSet.add(rel.target);
                });
                dimInfo.members = Array.from(memberSet);
            }
        }
        
        dimensionMembers.push(dimInfo);
    }
    
    const numColumns = columnDefs.length;
    
    // Check if we have any non-domain dimensions
    const hasNonDomainDimensions = dimensionMembers.some(d => d.members.length === 0);
    
    // Create table
    const table = document.createElement('table');
    table.className = 'cube-grid';
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginTop = '10px';
    
    // Add note if there are non-domain dimensions
    if (hasNonDomainDimensions) {
        const note = document.createElement('div');
        note.style.padding = '10px';
        note.style.backgroundColor = '#fff3cd';
        note.style.border = '1px solid #ffc107';
        note.style.borderRadius = '4px';
        note.style.marginBottom = '10px';
        note.innerHTML = `
            <strong>Note:</strong> This cube contains dimensions without explicit domain members 
            (e.g., time series dimensions). Specific dimension values are shown in the column headers.
        `;
        cubeSection.appendChild(note);
    }
    
    // Create header section
    const thead = document.createElement('thead');
    
    // Row 1: First column is "Concept", then member columns
    const firstRow = document.createElement('tr');
    const conceptHeader = document.createElement('th');
    conceptHeader.textContent = 'Concept';
    conceptHeader.style.minWidth = '200px';
    conceptHeader.style.border = '1px solid #ddd';
    conceptHeader.style.padding = '8px';
    conceptHeader.style.backgroundColor = '#f5f5f5';
    conceptHeader.rowSpan = 1; // Only spans its own row
    firstRow.appendChild(conceptHeader);
    
    // Add column headers
    for (let i = 0; i < numColumns; i++) {
        const memberHeader = document.createElement('th');
        memberHeader.textContent = `Column ${i + 1}`;
        memberHeader.style.minWidth = '150px';
        memberHeader.style.border = '1px solid #ddd';
        memberHeader.style.padding = '8px';
        memberHeader.style.backgroundColor = '#f5f5f5';
        memberHeader.rowSpan = 1; // Only spans its own row
        firstRow.appendChild(memberHeader);
    }
    thead.appendChild(firstRow);
    
    // Add dimension rows (dimension name + values for each column)
    otherDimensions.forEach((dim, dimIndex) => {
        // Dimension name + member values row (all in one row)
        const dimRow = document.createElement('tr');
        
        // First cell: dimension name
        const dimNameCell = document.createElement('th');
        dimNameCell.textContent = dim.dimensionName || 'Dimension';
        dimNameCell.style.backgroundColor = '#e3f2fd';
        dimNameCell.style.textAlign = 'left';
        dimNameCell.style.fontWeight = 'bold';
        dimNameCell.style.border = '1px solid #ddd';
        dimNameCell.style.padding = '8px';
        dimRow.appendChild(dimNameCell);
        
        // Then cells for each column showing the member value
        for (let colIndex = 0; colIndex < numColumns; colIndex++) {
            const memberCell = document.createElement('th');
            memberCell.style.border = '1px solid #ddd';
            memberCell.style.padding = '8px';
            memberCell.style.textAlign = 'center';
            
            const columnDef = columnDefs[colIndex];
            const dimValue = columnDef[dim.dimensionName];
            
            if (dimValue === null) {
                // This is a domain fact (no member value)
                memberCell.textContent = '(Domain)';
                memberCell.style.fontSize = '11px';
                memberCell.style.backgroundColor = '#e8f5e9';
                memberCell.style.fontStyle = 'italic';
            } else if (dimValue) {
                // Has a specific member value
                memberCell.textContent = dimValue;
                memberCell.style.fontSize = '11px';
                memberCell.style.backgroundColor = '#f5f5f5';
            } else {
                // No value for this dimension in this column
                memberCell.textContent = '-';
                memberCell.style.color = '#ccc';
                memberCell.style.backgroundColor = '#fafafa';
            }
            dimRow.appendChild(memberCell);
        }
        thead.appendChild(dimRow);
    });
    
    table.appendChild(thead);
    
    // Create body with concept rows
    const tbody = document.createElement('tbody');
    
    // Helper function to check if a cell should be highlighted and get its value for a specific column
    function getCellHighlightInfo(conceptName, columnIndex) {
        // Check if concept matches
        const factConcept = fact.factDimensions['xbrl:concept'];
        if (!factConcept || factConcept !== conceptName) {
            return { highlight: false, value: null };
        }
        
        // Get the column definition
        const columnDef = columnDefs[columnIndex];
        
        // Check if all dimensions match
        for (const dim of otherDimensions) {
            const factDimValue = fact.factDimensions[dim.dimensionName];
            const columnDimValue = columnDef[dim.dimensionName];
            
            // Normalize both values: undefined becomes null
            const normalizedFactValue = factDimValue !== undefined ? factDimValue : null;
            const normalizedColumnValue = columnDimValue !== undefined ? columnDimValue : null;
            
            // Both should match (including null to null)
            if (normalizedFactValue !== normalizedColumnValue) {
                return { highlight: false, value: null };
            }
        }
        
        // All dimensions match! Find the fact value if any
        let factValue = null;
        let isEscaped = false;
        if (fact.factValues && Array.isArray(fact.factValues) && fact.factValues.length > 0) {
            // Get the first fact value (assuming single value per fact for now)
            const firstFact = fact.factValues[0];
            if (firstFact && firstFact.value !== undefined) {
                factValue = firstFact.value;
                isEscaped = firstFact._isEscaped || false;
                // Add decimals formatting if available
                if (firstFact.decimals !== undefined) {
                    factValue = `${factValue} (${firstFact.decimals} decimals)`;
                }
            }
        }
        
        return { highlight: true, value: factValue, isEscaped: isEscaped };
    }
    
    function addConceptRows(concepts, level = 0) {
        concepts.forEach(conceptItem => {
            const row = document.createElement('tr');
            
            // Check if this concept matches the fact
            const conceptMatches = fact.factDimensions['xbrl:concept'] === conceptItem.name;
            
            // Concept cell
            const conceptCell = document.createElement('td');
            conceptCell.style.paddingLeft = (level * 20 + 5) + 'px';
            conceptCell.style.border = '1px solid #ddd';
            conceptCell.style.padding = '8px';
            conceptCell.textContent = conceptItem.name;
            
            if (conceptMatches) {
                conceptCell.style.backgroundColor = '#fff9c4';
                conceptCell.style.fontWeight = 'bold';
            }
            
            row.appendChild(conceptCell);
            
            // Add cells for each column
            for (let colIndex = 0; colIndex < numColumns; colIndex++) {
                const dimCell = document.createElement('td');
                dimCell.textContent = '';
                dimCell.style.textAlign = 'center';
                dimCell.style.color = '#999';
                dimCell.style.backgroundColor = '#fff';
                dimCell.style.border = '1px solid #ddd';
                dimCell.style.padding = '8px';
                
                // Check if this cell should be highlighted and get its value
                const cellInfo = getCellHighlightInfo(conceptItem.name, colIndex);
                
                if (cellInfo.highlight) {
                    dimCell.style.backgroundColor = '#fff9c4';
                    dimCell.style.border = '2px solid #fbc02d';
                    dimCell.style.padding = '8px';
                    dimCell.style.verticalAlign = 'top';
                    
                    // Display value or checkmark
                    if (cellInfo.value !== null) {
                        if (cellInfo.isEscaped) {
                            // Render escaped HTML with proper styling
                            // Wrap in a container div to preserve all original styles
                            const htmlContainer = document.createElement('div');
                            htmlContainer.innerHTML = cellInfo.value;
                            // Minimal container styling - let inner styles control everything
                            htmlContainer.style.maxWidth = '800px';
                            htmlContainer.style.overflow = 'auto';
                            dimCell.style.fontWeight = 'normal';
                            dimCell.appendChild(htmlContainer);
                            dimCell.title = 'Escaped HTML markup';
                        } else {
                            dimCell.textContent = cellInfo.value;
                            dimCell.style.color = '#1976d2';
                            dimCell.style.fontWeight = 'bold';
                            dimCell.title = `Fact value: ${cellInfo.value}`;
                        }
                    } else {
                        dimCell.textContent = '✓';
                        dimCell.style.color = '#f57f17';
                        dimCell.style.fontSize = '18px';
                        dimCell.title = 'Fact exists (no value specified)';
                    }
                }
                
                row.appendChild(dimCell);
            }
            
            tbody.appendChild(row);
            
            // Recursively add children
            if (conceptItem.children && conceptItem.children.length > 0) {
                addConceptRows(conceptItem.children, level + 1);
            }
        });
    }
    
    addConceptRows(conceptTree);
    table.appendChild(tbody);
    
    cubeSection.appendChild(table);
    
    // Add indicator if there are more concepts in the default cube
    if (isDefaultCube && hasMoreConcepts) {
        const moreConceptsNote = document.createElement('div');
        moreConceptsNote.style.padding = '10px';
        moreConceptsNote.style.marginTop = '5px';
        moreConceptsNote.style.backgroundColor = '#fff3cd';
        moreConceptsNote.style.border = '1px solid #ffc107';
        moreConceptsNote.style.borderRadius = '4px';
        moreConceptsNote.style.fontSize = '13px';
        moreConceptsNote.innerHTML = `
            <strong>Note:</strong> This default cube contains more concepts than shown. 
            Only the first 10 concepts (including the fact concept) are displayed for performance.
        `;
        cubeSection.appendChild(moreConceptsNote);
    }
    
    container.appendChild(cubeSection);
}
