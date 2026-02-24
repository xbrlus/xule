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
 * Rounding mode: round-to-nearest (§5.2.1).
 * Error code raised: calc11e:inconsistentCalculationUsingRounding (§5.2).
 */

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
                        addError(
                            `Calculation inconsistency in cube '${cube.name}', network '${network.name}': ` +
                            `total concept '${totalConcept}' reported interval [${rtLow}, ${rtHigh}] ` +
                            `does not overlap calculated interval [${ctLow}, ${ctHigh}]`,
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
