/**
 * XBRL 2.1 XML Parser Module
 * Converts XBRL 2.1 XML instances to OIM fact objects
 */

/**
 * Generate a position-based ID for an XML element
 * Position-based ID format: e.1.2.3... where each number represents the nth child
 * @param {Element} element - The XML element
 * @returns {string} The position-based ID (e.g., "e.1.5")
 */
function generatePositionBasedId(element) {
    const positions = [];
    let current = element;
    
    // Traverse up to root, collecting positions
    while (current && current.parentNode && current.parentNode.nodeType === Node.ELEMENT_NODE) {
        const parent = current.parentNode;
        const children = Array.from(parent.children);
        const position = children.indexOf(current) + 1; // 1-based
        positions.unshift(position);
        current = parent;
    }
    
    // Add the root position (always 1)
    positions.unshift(1);
    
    return 'e.' + positions.join('.');
}

/**
 * Parse XBRL 2.1 XML instance file and convert to facts
 * @param {string} xmlContent - The XML content of the XBRL instance
 * @param {Object} taxonomy - The taxonomy object for context
 * @returns {Object} Object containing facts, footnotes, and relationships
 */
export async function parseXBRLInstance(xmlContent, taxonomy) {
    console.log('[XBRL Parser] Parsing XBRL 2.1 XML instance');
    
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlContent, 'text/xml');
    
    // Check for parse errors
    const parseError = xmlDoc.querySelector('parsererror');
    if (parseError) {
        console.error('[XBRL Parser] XML parse error:', parseError.textContent);
        throw new Error('Failed to parse XBRL XML: ' + parseError.textContent);
    }
    
    // Get namespace prefix from documentInfo
    const namespacePrefix = taxonomy?.documentInfo?.documentNamespace || '';
    const prefix = namespacePrefix ? namespacePrefix + ':' : '';
    console.log('[XBRL Parser] Using namespace prefix:', prefix || '(none)');
    
    // Extract contexts and units
    const contexts = extractContexts(xmlDoc);
    const units = extractUnits(xmlDoc);
    
    console.log('[XBRL Parser] Extracted contexts:', Object.keys(contexts).length);
    console.log('[XBRL Parser] Extracted units:', Object.keys(units).length);
    
    // Extract facts
    const facts = extractFacts(xmlDoc, contexts, units, prefix);
    
    console.log('[XBRL Parser] Generated facts:', facts.length);
    
    // Extract footnotes and relationships
    const { footnotes, relationships } = extractFootnotes(xmlDoc, prefix);
    
    console.log('[XBRL Parser] Extracted footnotes:', footnotes.length);
    console.log('[XBRL Parser] Extracted footnote relationships:', relationships.length);
    
    return { facts, footnotes, relationships };
}

/**
 * Extract all contexts from the XBRL instance
 * @param {Document} xmlDoc - Parsed XML document
 * @returns {Object} Map of context ID to context object
 */
function extractContexts(xmlDoc) {
    const contexts = {};
    const contextElements = xmlDoc.querySelectorAll('context');
    
    contextElements.forEach(contextEl => {
        const id = contextEl.getAttribute('id');
        const context = {
            id: id,
            entity: null,
            period: null,
            dimensions: {}
        };
        
        // Extract entity
        const entityEl = contextEl.querySelector('entity');
        if (entityEl) {
            const identifierEl = entityEl.querySelector('identifier');
            if (identifierEl) {
                const scheme = identifierEl.getAttribute('scheme');
                const value = identifierEl.textContent;
                
                // Extract entity identifier - convert scheme:value to prefixed form
                // For CID scheme, use cid:value format
                if (scheme && scheme.includes('CID')) {
                    context.entity = 'cid:' + value;
                } else {
                    context.entity = value;
                }
            }
            
            // Extract dimensions from segment or scenario
            const segmentEl = entityEl.querySelector('segment');
            const scenarioEl = contextEl.querySelector('scenario');
            const dimensionContainer = segmentEl || scenarioEl;
            
            if (dimensionContainer) {
                // Explicit dimensions
                const explicitMembers = dimensionContainer.querySelectorAll('explicitMember');
                explicitMembers.forEach(member => {
                    const dimension = member.getAttribute('dimension');
                    const value = member.textContent;
                    context.dimensions[dimension] = value;
                });
                
                // Typed dimensions
                const typedMembers = dimensionContainer.querySelectorAll('typedMember');
                typedMembers.forEach(member => {
                    const dimension = member.getAttribute('dimension');
                    // Get the first child element (the domain element)
                    const domainEl = member.children[0];
                    if (domainEl) {
                        const value = domainEl.textContent;
                        context.dimensions[dimension] = value;
                    }
                });
            }
        }
        
        // Extract period
        const periodEl = contextEl.querySelector('period');
        if (periodEl) {
            const instantEl = periodEl.querySelector('instant');
            const startDateEl = periodEl.querySelector('startDate');
            const endDateEl = periodEl.querySelector('endDate');
            const foreverEl = periodEl.querySelector('forever');
            
            if (instantEl) {
                context.period = instantEl.textContent + 'T00:00:00';
            } else if (startDateEl && endDateEl) {
                // For duration periods, use the end date as the period value
                // This matches the OIM model convention
                context.period = endDateEl.textContent + 'T00:00:00';
                context.periodStart = startDateEl.textContent;
                context.periodEnd = endDateEl.textContent;
            } else if (foreverEl) {
                context.period = 'forever';
            }
        }
        
        contexts[id] = context;
    });
    
    return contexts;
}

/**
 * Extract all units from the XBRL instance
 * @param {Document} xmlDoc - Parsed XML document
 * @returns {Object} Map of unit ID to unit QName
 */
function extractUnits(xmlDoc) {
    const units = {};
    const unitElements = xmlDoc.querySelectorAll('unit');
    
    unitElements.forEach(unitEl => {
        const id = unitEl.getAttribute('id');
        
        // Handle simple units (single measure)
        const measureEl = unitEl.querySelector('measure');
        if (measureEl) {
            const measure = measureEl.textContent;
            units[id] = measure;
        }
        
        // Handle complex units (divide with numerator/denominator)
        const divideEl = unitEl.querySelector('divide');
        if (divideEl) {
            const numeratorMeasures = Array.from(divideEl.querySelectorAll('unitNumerator measure'))
                .map(el => el.textContent);
            const denominatorMeasures = Array.from(divideEl.querySelectorAll('unitDenominator measure'))
                .map(el => el.textContent);
            
            // Format as numerator/denominator
            units[id] = {
                numerator: numeratorMeasures,
                denominator: denominatorMeasures
            };
        }
    });
    
    return units;
}

/**
 * Extract all facts from the XBRL instance and convert to fact objects
 * @param {Document} xmlDoc - Parsed XML document
 * @param {Object} contexts - Map of context ID to context object
 * @param {Object} units - Map of unit ID to unit QName
 * @param {string} prefix - Namespace prefix for fact names (e.g., 'ext:')
 * @returns {Array} Array of fact objects
 */
function extractFacts(xmlDoc, contexts, units, prefix = '') {
    const facts = [];
    const rootElement = xmlDoc.documentElement;
    
    // Get all child elements of the root that are not metadata elements
    const metadataElements = ['schemaRef', 'linkbaseRef', 'roleRef', 'arcroleRef', 'context', 'unit'];
    const allElements = Array.from(rootElement.children);
    
    allElements.forEach((el, index) => {
        const tagName = el.tagName;
        
        // Skip metadata elements
        if (metadataElements.includes(tagName.split(':')[1]) || 
            tagName === 'schemaRef' || tagName === 'context' || tagName === 'unit') {
            return;
        }
        
        // This is a fact element
        const factId = el.getAttribute('id');
        const contextRef = el.getAttribute('contextRef');
        const unitRef = el.getAttribute('unitRef');
        const decimals = el.getAttribute('decimals');
        const value = el.textContent;
        
        // Get the concept name (tag name with namespace)
        const conceptName = tagName;
        
        // Lookup context
        const context = contexts[contextRef];
        if (!context) {
            console.warn('[XBRL Parser] Context not found:', contextRef);
            return;
        }
        
        // Build fact dimensions from context
        const factDimensions = {
            'xbrl:concept': conceptName,
            'xbrl:entity': context.entity,
            'xbrl:period': context.period
        };
        
        // Add unit if present
        if (unitRef) {
            const unit = units[unitRef];
            if (unit) {
                if (typeof unit === 'string') {
                    factDimensions['xbrl:unit'] = unit;
                } else {
                    // Complex unit - for now just convert to string
                    factDimensions['xbrl:unit'] = `${unit.numerator.join('*')}/${unit.denominator.join('*')}`;
                }
            }
        }
        
        // Add explicit dimensions from context
        for (const [dimName, dimValue] of Object.entries(context.dimensions)) {
            factDimensions[dimName] = dimValue;
        }
        
        // Create fact object
        // Per spec: fact name should be factValue name with "fp-" prefix
        // If fact has @id attribute, use it for factValue and prepend "fp-" for fact
        // If no @id, generate position-based ID (e.g., "e.1.5") and use "fp-e.1.5"
        // All names should include the namespace prefix from documentNamespace
        const baseFactValueName = factId || generatePositionBasedId(el);
        const factValueName = prefix + baseFactValueName;
        const factName = prefix + 'fp-' + baseFactValueName;
        
        const fact = {
            name: factName,
            factValues: [
                {
                    name: factValueName,
                    value: value
                }
            ],
            factDimensions: factDimensions
        };
        
        // Add decimals if present
        if (decimals !== null) {
            fact.factValues[0].decimals = decimals;
        }
        
        facts.push(fact);
    });
    
    return facts;
}

/**
 * Extract footnotes and fact-footnote relationships from the XBRL instance
 * @param {Document} xmlDoc - Parsed XML document
 * @param {string} prefix - Namespace prefix for footnote names (e.g., 'ext:')
 * @returns {Object} Object containing footnotes array and relationships array
 */
function extractFootnotes(xmlDoc, prefix = '') {
    const footnotes = [];
    const relationships = [];
    
    // Find all footnoteLink elements
    const footnoteLinks = xmlDoc.querySelectorAll('footnoteLink');
    
    console.log('[XBRL Parser] Found', footnoteLinks.length, 'footnoteLink elements');
    
    footnoteLinks.forEach((footnoteLink, linkIdx) => {
        console.log('[XBRL Parser] Processing footnoteLink', linkIdx);
        
        // Get extended link role (defaults to http://www.xbrl.org/2003/role/link)
        const linkRole = footnoteLink.getAttribute('xlink:role') || 'http://www.xbrl.org/2003/role/link';
        
        // Extract footnote arc relationships
        const arcs = footnoteLink.querySelectorAll('footnoteArc');
        
        console.log('[XBRL Parser] Found', arcs.length, 'footnoteArc elements in link', linkIdx);
        
        arcs.forEach((arc, arcIdx) => {
            const arcrole = arc.getAttribute('xlink:arcrole');
            const fromLabel = arc.getAttribute('xlink:from');
            const toLabel = arc.getAttribute('xlink:to');
            const order = arc.getAttribute('order') || '0';
            
            console.log('[XBRL Parser] Arc', arcIdx, '- from:', fromLabel, 'to:', toLabel);
            
            // Find the corresponding locator to get the fact ID
            // Try multiple selector approaches for cross-browser compatibility
            let locator = footnoteLink.querySelector(`loc[xlink\\:label="${fromLabel}"]`);
            if (!locator) {
                // Try without namespace prefix
                locator = Array.from(footnoteLink.querySelectorAll('loc')).find(
                    loc => loc.getAttributeNS('http://www.w3.org/1999/xlink', 'label') === fromLabel
                );
            }
            
            if (!locator) {
                console.warn('[XBRL Parser] Locator not found for label:', fromLabel);
                return;
            }
            
            const href = locator.getAttributeNS('http://www.w3.org/1999/xlink', 'href') || locator.getAttribute('xlink:href');
            // Extract fact ID from href (e.g., "#f-71" -> "f-71")
            const factId = href ? href.replace(/^#/, '') : null;
            
            console.log('[XBRL Parser] Found locator - href:', href, 'factId:', factId);
            
            if (!factId) return;
            
            // Find the corresponding footnote element
            let footnoteEl = footnoteLink.querySelector(`footnote[xlink\\:label="${toLabel}"]`);
            if (!footnoteEl) {
                // Try without namespace prefix
                footnoteEl = Array.from(footnoteLink.querySelectorAll('footnote')).find(
                    fn => fn.getAttributeNS('http://www.w3.org/1999/xlink', 'label') === toLabel
                );
            }
            
            if (!footnoteEl) {
                console.warn('[XBRL Parser] Footnote element not found for label:', toLabel);
                return;
            }
            
            // Extract footnote content and language
            const content = footnoteEl.textContent || '';
            const language = footnoteEl.getAttribute('xml:lang') || 'en-US';
            
            console.log('[XBRL Parser] Footnote content length:', content.length, 'language:', language);
            
            // Generate footnote name: "fn_" + factId with namespace prefix
            // If multiple footnotes for same fact, append "_1", "_2", etc.
            const baseFootnoteName = prefix + 'fn_' + factId;
            let footnoteName = baseFootnoteName;
            
            // Check if footnote with this name already exists
            let counter = 1;
            while (footnotes.some(fn => fn.name === footnoteName)) {
                footnoteName = `${baseFootnoteName}_${counter}`;
                counter++;
            }
            
            // Create footnote object
            const footnote = {
                name: footnoteName,
                content: content,
                language: language
            };
            
            footnotes.push(footnote);
            console.log('[XBRL Parser] Created footnote:', footnoteName);
            
            // Create fact-footnote relationship
            // Source is the fact (with fp- prefix and namespace prefix)
            // Target is the footnote
            const sourceFact = prefix + 'fp-' + factId;
            
            const relationship = {
                source: sourceFact,
                target: footnoteName,
                order: parseFloat(order)
            };
            
            relationships.push(relationship);
            console.log('[XBRL Parser] Created relationship:', sourceFact, '->', footnoteName);
        });
    });
    
    console.log('[XBRL Parser] Total footnotes extracted:', footnotes.length);
    console.log('[XBRL Parser] Total relationships extracted:', relationships.length);
    
    return { footnotes, relationships };
}

/**
 * Load and parse an XBRL instance file from a URL
 * @param {string} url - URL of the XBRL instance file
 * @param {Object} taxonomy - The taxonomy object for context
 * @returns {Promise<Object>} Promise resolving to object with facts, footnotes, and relationships
 */
export async function loadXBRLInstance(url, taxonomy) {
    console.log('[XBRL Parser] Loading XBRL instance from:', url);
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load XBRL instance: ${response.statusText}`);
        }
        
        const xmlContent = await response.text();
        return await parseXBRLInstance(xmlContent, taxonomy);
    } catch (error) {
        console.error('[XBRL Parser] Error loading XBRL instance:', error);
        throw error;
    }
}
