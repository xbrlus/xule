/**
 * Calculation Validator Module
 *
 * Implements calculation consistency checking per the XBRL Calculations 1.1 specification:
 * https://www.xbrl.org/Specification/calculation-1.1/REC-2023-02-22+corrected-errata-2024-02-14/
 *
 * Amended by oim-taxonomy.md §"Calculation relationship":
 *   - Validation is only performed on xbrl:summation-item networks associated with a cube.
 *   - Binding only considers facts that are valid within the cube's domain constraints.
 *
 * Also implements structural concept-property consistency checks for summation-item
 * relationships per oim-taxonomy.md §"Summation item relationship" lines 3968-3977:
 *   - Source and target concepts MUST have the same periodType.
 *   - xbrla:balance must be consistent with weight and reconciliation values.
 * Error code: oimte:conceptPropertiesInconsistentWithSummationItemRelationship
 *
 * Rounding mode: round-to-nearest (§5.2.1).
 * Error code raised: calc11e:inconsistentCalculationUsingRounding (§5.2).
 */

/**
 * Build a Map from concept QName to concept object.
 * @param {Object} taxonomy
 * @returns {Map<string, Object>}
 */
function buildConceptMap(taxonomy) {
    const map = new Map();
    if (!Array.isArray(taxonomy.concepts)) return map;
    for (const concept of taxonomy.concepts) {
        if (concept.name) map.set(concept.name, concept);
    }
    return map;
}

/**
 * Get the value of a named property from a concept's properties array.
 * Returns undefined if the concept has no properties or the property is not found.
 * @param {Object} concept
 * @param {string} propertyQName
 * @returns {string|undefined}
 */
function getConceptProperty(concept, propertyQName) {
    if (!Array.isArray(concept.properties)) return undefined;
    const prop = concept.properties.find(p => p.property === propertyQName);
    return prop?.value;
}

/**
 * Validate that all summation-item relationships in cube-associated networks have
 * consistent concept properties, per oim-taxonomy.md §"Summation item relationship":
 *
 *   1. Source and target MUST have the same periodType.
 *      → oimte:conceptPropertiesInconsistentWithSummationItemRelationship
 *
 *   2. xbrla:balance consistency with xbrl:weight and xbrl:reconciliation
 *      (only applied when both concepts define xbrla:balance):
 *      - weight=1,  reconciliation not defined/false → source and target MUST have SAME balance
 *      - weight=-1, reconciliation not defined/false → source and target MUST have DIFFERENT balance
 *      - weight=1,  reconciliation=true             → source and target MUST have DIFFERENT balance
 *      - weight=-1, reconciliation=true             → source and target MUST have SAME balance
 *      → oimte:conceptPropertiesInconsistentWithSummationItemRelationship
 *
 * Applied to ALL summation-item networks in the model regardless of whether they are
 * associated with a cube. This check validates taxonomy structure (concept properties),
 * not fact data — so the cube restriction that applies to fact-level calculation
 * consistency checking does not apply here.
 *
 * @param {Object} taxonomy - The merged taxonomy object
 * @param {function(string, Object): void} addError - Callback to record errors;
 *   receives (message, context) where context includes an errorCode property.
 */
export function validateSummationItemRelationshipProperties(taxonomy, addError) {
    if (!Array.isArray(taxonomy.networks) || taxonomy.networks.length === 0) return;

    const conceptMap = buildConceptMap(taxonomy);
    if (conceptMap.size === 0) return;

    for (const network of taxonomy.networks) {
        if (network.relationshipTypeName !== 'xbrl:summation-item') continue;
        const netName = network.name;
        if (!Array.isArray(network.relationships) || network.relationships.length === 0) continue;

        for (const rel of network.relationships) {
            const sourceName = rel.source;
            const targetName = rel.target;
            if (!sourceName || !targetName) continue;

            const sourceConcept = conceptMap.get(sourceName);
            const targetConcept = conceptMap.get(targetName);
            if (!sourceConcept || !targetConcept) continue;

            // ── 1. Period type consistency ──────────────────────────────────────────────
            const sourcePeriodType = sourceConcept.periodType;
            const targetPeriodType = targetConcept.periodType;
            if (sourcePeriodType && targetPeriodType && sourcePeriodType !== targetPeriodType) {
                addError(
                    `Summation-item relationship in network '${netName}': ` +
                    `source concept '${sourceName}' has periodType '${sourcePeriodType}' but ` +
                    `target concept '${targetName}' has periodType '${targetPeriodType}'. ` +
                    `Source and target must have the same periodType.`,
                    {
                        networkName: netName,
                        sourceConcept: sourceName,
                        targetConcept: targetName,
                        errorCode: 'oimte:conceptPropertiesInconsistentWithSummationItemRelationship'
                    }
                );
            }

            // ── 2. Balance / weight / reconciliation consistency ────────────────────────
            const sourceBalance = getConceptProperty(sourceConcept, 'xbrla:balance');
            const targetBalance = getConceptProperty(targetConcept, 'xbrla:balance');

            // Spec: "if both have a balance property defined"
            if (!sourceBalance || !targetBalance) continue;

            const weightProp = rel.properties?.find(p => p.property === 'xbrl:weight');
            const weight = weightProp ? parseFloat(weightProp.value) : 1;

            const reconciliationProp = rel.properties?.find(p => p.property === 'xbrl:reconciliation');
            const reconciliation = reconciliationProp
                ? (reconciliationProp.value === 'true' || reconciliationProp.value === true)
                : false;

            const sameBalance = sourceBalance === targetBalance;
            let errorDesc = null;

            if (!reconciliation) {
                if (weight === 1 && !sameBalance) {
                    errorDesc = `weight=1 without reconciliation requires both concepts to have the same xbrla:balance ` +
                                `(source '${sourceName}': '${sourceBalance}', target '${targetName}': '${targetBalance}')`;
                } else if (weight === -1 && sameBalance) {
                    errorDesc = `weight=-1 without reconciliation requires the concepts to have different xbrla:balance values ` +
                                `(both '${sourceName}' and '${targetName}' have '${sourceBalance}')`;
                }
            } else {
                if (weight === 1 && sameBalance) {
                    errorDesc = `weight=1 with reconciliation=true requires the concepts to have different xbrla:balance values ` +
                                `(both '${sourceName}' and '${targetName}' have '${sourceBalance}')`;
                } else if (weight === -1 && !sameBalance) {
                    errorDesc = `weight=-1 with reconciliation=true requires both concepts to have the same xbrla:balance ` +
                                `(source '${sourceName}': '${sourceBalance}', target '${targetName}': '${targetBalance}')`;
                }
            }

            if (errorDesc) {
                addError(
                    `Summation-item relationship in network '${netName}' (${sourceName} → ${targetName}): ${errorDesc}.`,
                    {
                        networkName: netName,
                        sourceConcept: sourceName,
                        targetConcept: targetName,
                        weight,
                        reconciliation,
                        sourceBalance,
                        targetBalance,
                        errorCode: 'oimte:conceptPropertiesInconsistentWithSummationItemRelationship'
                    }
                );
            }
        }
    }
}


/**
 * Validate that no summation-item network contains duplicate relationships —
 * i.e. more than one relationship with the same source (total) concept and the
 * same target (contributing) concept within a single network.
 * Error code: calc11e:duplicateCalculationRelationships
 * Applied to ALL summation-item networks (structural check, not fact-level).
 * @param {Object} taxonomy
 * @param {Function} addError
 */
export function validateDuplicateCalculationRelationships(taxonomy, addError) {
    if (!Array.isArray(taxonomy.networks) || taxonomy.networks.length === 0) return;
    for (const network of taxonomy.networks) {
        if (network.relationshipTypeName !== 'xbrl:summation-item') continue;
        if (!Array.isArray(network.relationships) || network.relationships.length === 0) continue;
        const seen = new Set();
        for (const rel of network.relationships) {
            const key = `${rel.source}\0${rel.target}`;
            if (seen.has(key)) {
                addError(
                    `Duplicate summation-item relationship in network '${network.name}': ` +
                    `source '${rel.source}' \u2192 target '${rel.target}' appears more than once.`,
                    {
                        networkName: network.name,
                        sourceConcept: rel.source,
                        targetConcept: rel.target,
                        errorCode: 'calc11e:duplicateCalculationRelationships'
                    }
                );
            } else {
                seen.add(key);
            }
        }
    }
}


/**
 * Build a Map from domainName → Set of all member QNames in that domain.
 * Members are derived from domain.root plus all relationship source/target values.
 * @param {Object} taxonomy
 * @returns {Map<string, Set<string>>}
 */
function buildDomainMembersMap(taxonomy) {
    const map = new Map();
    if (!Array.isArray(taxonomy.domains)) return map;
    for (const domain of taxonomy.domains) {
        if (!domain.name) continue;
        const members = new Set();
        if (domain.root) members.add(domain.root);
        if (Array.isArray(domain.relationships)) {
            for (const rel of domain.relationships) {
                if (rel.source) members.add(rel.source);
                if (rel.target) members.add(rel.target);
            }
        }
        map.set(domain.name, members);
    }
    return map;
}

/**
 * Returns true if a fact satisfies all cube dimension domain restrictions.
 * A fact is excluded from the cube if any dimension with a domainName has a
 * value not found in that domain's member set.
 * @param {Object} fact
 * @param {Object} cube
 * @param {Map<string, Set<string>>} domainMembersMap
 * @returns {boolean}
 */
function isFactInCubeDomains(fact, cube, domainMembersMap) {
    if (!Array.isArray(cube.cubeDimensions)) return true;
    for (const cubeDim of cube.cubeDimensions) {
        const { dimensionName, domainName } = cubeDim;
        if (!domainName) continue;
        const factValue = fact.factDimensions?.[dimensionName];
        if (factValue === undefined) continue; // dimension absent in fact — domain check not applicable
        const members = domainMembersMap.get(domainName);
        if (!members || !members.has(factValue)) return false;
    }
    return true;
}

/**
 * Two reported data points are dimensionally aligned if, for every dimension
 * other than xbrl:concept in T, the same dimension with an equal value exists in S.
 * (Calculation 1.1 §5.1)
 * @param {Object} tFact - total fact
 * @param {Object} sFact - contributing fact
 * @returns {boolean}
 */
function areDimensionallyAligned(tFact, sFact) {
    const tDims = tFact.factDimensions || {};
    const sDims = sFact.factDimensions || {};
    for (const [dim, val] of Object.entries(tDims)) {
        if (dim === 'xbrl:concept') continue;
        if (sDims[dim] !== val) return false;
    }
    return true;
}

/**
 * Compute the rounded fact value interval [v - 0.5*10^(-d), v + 0.5*10^(-d)]
 * for a fact (round-to-nearest mode per Calculation 1.1 §5.2.3).
 * Uses only the first factValue.
 * @param {Object} fact
 * @returns {[number, number] | null} interval, or null if the fact has no numeric value
 */
function getFactValueInterval(fact) {
    const fv = fact.factValues?.[0];
    if (!fv || fv.value === undefined || fv.value === null) return null;
    const v = parseFloat(fv.value);
    if (isNaN(v)) return null;
    const decimals = fv.decimals;
    if (decimals === 'infinity' || decimals === undefined || decimals === null) {
        return [v, v]; // §5.2.3: decimals=infinity → single-point interval
    }
    const d = parseInt(decimals, 10);
    const epsilon = 0.5 * Math.pow(10, -d);
    return [v - epsilon, v + epsilon];
}

/**
 * Format the dimensional context of a fact (everything except xbrl:concept) into a
 * human-readable string for use in error messages.
 * Core dimensions are listed first in a fixed order, then any user-defined dimensions.
 * Example output: "period: 2025-06-30, entity: ext:Company1, unit: iso4217:NZD"
 * @param {Object|undefined} factDimensions
 * @returns {string} formatted context string, or '' if no dimensions
 */
function formatFactContext(factDimensions) {
    if (!factDimensions) return '';
    const CORE_ORDER = ['xbrl:period', 'xbrl:entity', 'xbrl:unit', 'xbrl:language'];
    const LABELS = {
        'xbrl:period':   'period',
        'xbrl:entity':   'entity',
        'xbrl:unit':     'unit',
        'xbrl:language': 'language'
    };
    const parts = [];
    // Core dimensions first, in fixed order
    for (const key of CORE_ORDER) {
        if (factDimensions[key] === undefined) continue;
        let val = factDimensions[key];
        // Duration periods are stored as 'startT.../endT...' — strip the time component for readability
        if (key === 'xbrl:period' && val.includes('/')) {
            val = val.replace(/T00:00:00/g, '');
        } else if (key === 'xbrl:period' && val.endsWith('T00:00:00')) {
            val = val.replace('T00:00:00', '');
        }
        parts.push(`${LABELS[key]}: ${val}`);
    }
    // Any remaining (model-defined) dimensions, excluding xbrl:concept
    for (const [key, value] of Object.entries(factDimensions)) {
        if (key === 'xbrl:concept') continue;
        if (LABELS[key]) continue; // already handled above
        parts.push(`${key}: ${value}`);
    }
    return parts.join(', ');
}

/**
 * Validate calculation consistency for all cubes per the Calculation 1.1 specification,
 * restricted to facts valid within each cube as required by oim-taxonomy.md §"Calculation relationship".
 *
 * Uses round-to-nearest rounding mode. Calls addError for each binding where the sum
 * of contribution intervals does not overlap the reported total interval.
 *
 * @param {Object} taxonomy - The merged taxonomy object
 * @param {function(string, Object): void} addError - Callback to record a validation error;
 *   receives (message, context) where context includes an errorCode property.
 */
export function validateCalculations(taxonomy, addError) {
    if (!Array.isArray(taxonomy.facts) || taxonomy.facts.length === 0) return;
    if (!Array.isArray(taxonomy.cubes) || taxonomy.cubes.length === 0) return;
    if (!Array.isArray(taxonomy.networks) || taxonomy.networks.length === 0) return;

    // Build domain membership lookup
    const domainMembersMap = buildDomainMembersMap(taxonomy);

    // Build network name → network object map
    const networkMap = new Map();
    for (const network of taxonomy.networks) {
        if (network.name) networkMap.set(network.name, network);
    }

    // Process each cube
    for (const cube of taxonomy.cubes) {
        if (!Array.isArray(cube.cubeNetworks)) continue;

        // Find xbrl:summation-item networks referenced by this cube
        const calcNetworks = cube.cubeNetworks
            .map(n => networkMap.get(n))
            .filter(n => n && n.relationshipTypeName === 'xbrl:summation-item');

        if (calcNetworks.length === 0) continue;

        // Restrict facts to those valid within this cube's domain constraints (oim-taxonomy.md §"Calculation relationship")
        const cubeFacts = taxonomy.facts.filter(f => isFactInCubeDomains(f, cube, domainMembersMap));

        for (const network of calcNetworks) {
            if (!Array.isArray(network.relationships) || network.relationships.length === 0) continue;

            // Group relationships by source concept (total concept) → [{target, weight}]
            const calcMap = new Map();
            for (const rel of network.relationships) {
                const weightProp = rel.properties?.find(p => p.property === 'xbrl:weight');
                const weight = weightProp ? parseFloat(weightProp.value) : 1;
                if (!calcMap.has(rel.source)) calcMap.set(rel.source, []);
                calcMap.get(rel.source).push({ target: rel.target, weight });
            }

            // Check consistency for each total concept (§5.2)
            for (const [totalConcept, contributors] of calcMap) {
                const contributingConcepts = new Set(contributors.map(c => c.target));

                // Find all T facts (total) for this concept within the cube
                const totalFacts = cubeFacts.filter(
                    f => f.factDimensions?.['xbrl:concept'] === totalConcept
                );

                for (const tFact of totalFacts) {
                    const tInterval = getFactValueInterval(tFact);
                    if (!tInterval) continue; // nil or non-numeric total — skip

                    // Find contributing facts dimensionally aligned with T, grouped by concept (§5.1)
                    const factsByConcept = new Map();
                    for (const sFact of cubeFacts) {
                        const sConcept = sFact.factDimensions?.['xbrl:concept'];
                        if (!contributingConcepts.has(sConcept)) continue;
                        if (!areDimensionallyAligned(tFact, sFact)) continue;
                        if (!factsByConcept.has(sConcept)) factsByConcept.set(sConcept, []);
                        factsByConcept.get(sConcept).push(sFact);
                    }

                    // Calculation only binds when at least one contributing fact is present (§5.1)
                    if (factsByConcept.size === 0) continue;

                    // Compute CT = Σ (factValueInterval(S) × weight) for each contributor (§5.2, §5.7)
                    let ctLow = 0, ctHigh = 0;
                    for (const { target, weight } of contributors) {
                        const sFactsForTarget = factsByConcept.get(target);
                        if (!sFactsForTarget || sFactsForTarget.length === 0) continue;

                        // Intersection of fact value intervals to handle consistent duplicates (§5.5)
                        let intLow = -Infinity, intHigh = Infinity;
                        for (const sf of sFactsForTarget) {
                            const iv = getFactValueInterval(sf);
                            if (!iv) continue;
                            intLow = Math.max(intLow, iv[0]);
                            intHigh = Math.min(intHigh, iv[1]);
                        }
                        if (!isFinite(intLow)) continue; // no valid value found

                        // Multiply interval by weight: [x1,x2] * w = [min(x1*w,x2*w), max(x1*w,x2*w)] (§5.7)
                        const cLow = Math.min(intLow * weight, intHigh * weight);
                        const cHigh = Math.max(intLow * weight, intHigh * weight);
                        ctLow += cLow;
                        ctHigh += cHigh;
                    }

                    // RT = factValueInterval(T)
                    const [rtLow, rtHigh] = tInterval;

                    // CT overlaps RT iff ctLow <= rtHigh AND ctHigh >= rtLow (§5.2)
                    if (!(ctLow <= rtHigh && ctHigh >= rtLow)) {
                        const ctxDesc = formatFactContext(tFact.factDimensions);
                        addError(
                            `Calculation inconsistency in cube '${cube.name}', network '${network.name}': ` +
                            `total concept '${totalConcept}' reported interval [${rtLow}, ${rtHigh}] ` +
                            `does not overlap calculated interval [${ctLow}, ${ctHigh}]` +
                            (ctxDesc ? ` (${ctxDesc})` : ''),
                            {
                                cubeName: cube.name,
                                networkName: network.name,
                                totalConcept,
                                factName: tFact.name,
                                errorCode: 'calc11e:inconsistentCalculationUsingRounding'
                            }
                        );
                    }
                }
            }
        }
    }
}
