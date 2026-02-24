/**
 * Tree Handlers Module
 * Handles all node interactions including:
 * - Click handling for expand/collapse
 * - Details panel display
 * - Right-click context menus
 * - Expand/collapse all functionality
 * - Root mismatch popup display
 */

import { setContextMenu } from './state.js';

// Import showDetails function (will use window version as fallback)
let showDetailsFunc = null;

/**
 * Set the showDetails function reference
 * This is called from main.js after all modules are loaded
 */
export function setShowDetailsFunction(fn) {
    showDetailsFunc = fn;
}

/**
 * Get showDetails function (use module version or fallback to window)
 */
function getShowDetails() {
    return showDetailsFunc || window.showDetails;
}

/**
 * Attach event handlers to tree nodes
 * @param {HTMLElement} container - Container element with .node elements
 * @param {boolean} skipDetailsOnClick - If true, don't show details panel on click
 */
export function attachNodeHandlers(container, skipDetailsOnClick = false) {
    if (!container) {
        console.warn('[Tree Handlers] No container provided to attachNodeHandlers');
        return;
    }

    container.querySelectorAll('.node').forEach(node => {
        // Click handler for expand/collapse and details display
        node.addEventListener('click', function(e) {
            // Check if click is on this node or its immediate children (not nested nodes)
            let target = e.target;
            let isDirectChild = false;
            
            // Walk up to see if we clicked on this node or its direct children
            // We need to check multiple levels due to nested span structure (nodeSpan > leftContainer > icon/text)
            let currentElement = target;
            let levelsToCheck = 4; // Check up to 4 levels for nested spans
            
            while (currentElement && levelsToCheck > 0) {
                if (currentElement === this) {
                    isDirectChild = true;
                    break;
                }
                // Stop if we hit another node (don't bubble to child nodes)
                if (currentElement !== target && currentElement.classList && currentElement.classList.contains('node')) {
                    break;
                }
                currentElement = currentElement.parentElement;
                levelsToCheck--;
            }
            
            // Only process if we clicked on this node level (not a child node)
            if (isDirectChild) {
                // Prevent event from bubbling to parent nodes
                e.stopPropagation();
                
                // Remove selected class from all nodes in the container
                container.querySelectorAll('.node').forEach(n => {
                    n.classList.remove('selected');
                });
                
                // Add selected class to this node
                this.classList.add('selected');
                
                // Check if this node has a child UL (meaning it can expand/collapse)
                const hasChildren = this.querySelector('ul') !== null;
                
                if (hasChildren) {
                    // If node has neither class, default to collapsed
                    if (!this.classList.contains('expanded') && !this.classList.contains('collapsed')) {
                        this.classList.add('collapsed');
                    }
                    this.classList.toggle('expanded');
                    this.classList.toggle('collapsed');
                }
                
                // Always show details if skipDetailsOnClick is false and type is set
                if (!skipDetailsOnClick && this.dataset.type) {
                    let obj = this.dataset.obj;
                    // Try to parse as JSON for object types (network, cube, etc.)
                    // But for simple node references (concept, member, dimension, etc.), use the string as-is
                    try {
                        const parsed = JSON.parse(obj);
                        if (typeof parsed === 'object') {
                            obj = parsed;
                        }
                    } catch (e) {
                        // Not JSON, use as-is (it's a node name string)
                    }
                    
                    // Get showDetails function and call it
                    const showDetails = getShowDetails();
                    if (showDetails) {
                        showDetails(obj, this.dataset.type);
                    } else {
                        console.warn('[Tree Handlers] showDetails function not available');
                    }
                }
            }
        });

        // Right-click context menu handler
        node.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            e.stopPropagation();
            showContextMenu(e.pageX, e.pageY, this);
        });
    });
}

/**
 * Show context menu at specified position
 * @param {number} x - X coordinate (pageX)
 * @param {number} y - Y coordinate (pageY)
 * @param {HTMLElement} node - The node that was right-clicked
 */
export function showContextMenu(x, y, node) {
    // Get current context menu from state or window
    let contextMenu = window.contextMenu;
    
    // Remove existing context menu if any
    if (contextMenu) {
        contextMenu.remove();
    }

    // Create context menu
    contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu';
    contextMenu.style.left = x + 'px';
    contextMenu.style.top = y + 'px';

    // Add "Expand All" option
    const expandAllItem = document.createElement('div');
    expandAllItem.className = 'context-menu-item';
    expandAllItem.textContent = 'Expand All';
    expandAllItem.addEventListener('click', function() {
        expandAllNodes(node);
        contextMenu.remove();
        window.contextMenu = null;
        setContextMenu(null);
    });
    contextMenu.appendChild(expandAllItem);

    // Add "Collapse All" option
    const collapseAllItem = document.createElement('div');
    collapseAllItem.className = 'context-menu-item';
    collapseAllItem.textContent = 'Collapse All';
    collapseAllItem.addEventListener('click', function() {
        collapseAllNodes(node);
        contextMenu.remove();
        window.contextMenu = null;
        setContextMenu(null);
    });
    contextMenu.appendChild(collapseAllItem);

    document.body.appendChild(contextMenu);
    
    // Store in window and state
    window.contextMenu = contextMenu;
    setContextMenu(contextMenu);

    // Close context menu when clicking elsewhere
    const closeMenu = function(e) {
        if (contextMenu && !contextMenu.contains(e.target)) {
            contextMenu.remove();
            window.contextMenu = null;
            setContextMenu(null);
            document.removeEventListener('click', closeMenu);
        }
    };
    setTimeout(() => {
        document.addEventListener('click', closeMenu);
    }, 0);
}

/**
 * Expand a node and all its child nodes recursively
 * @param {HTMLElement} node - The node to expand
 */
export function expandAllNodes(node) {
    if (!node) return;
    
    // Expand this node
    node.classList.remove('collapsed');
    node.classList.add('expanded');

    // Find all child nodes and expand them recursively
    const childNodes = node.querySelectorAll('.node');
    childNodes.forEach(childNode => {
        childNode.classList.remove('collapsed');
        childNode.classList.add('expanded');
    });
}

/**
 * Collapse a node and all its child nodes recursively
 * @param {HTMLElement} node - The node to collapse
 */
export function collapseAllNodes(node) {
    if (!node) return;
    
    // Find all child nodes and collapse them
    const childNodes = node.querySelectorAll('.node');
    childNodes.forEach(childNode => {
        childNode.classList.remove('expanded');
        childNode.classList.add('collapsed');
    });

    // Collapse this node last
    node.classList.remove('expanded');
    node.classList.add('collapsed');
}

/**
 * Show popup displaying root mismatch details
 * @param {Event} event - The click event (for positioning)
 * @param {Array<string>} actualNotDeclared - Actual roots not in declared array
 * @param {Array<string>} declaredNotActual - Declared roots not in actual roots
 * @param {string} networkName - Name of the network with mismatch
 */
export function showRootMismatchPopup(event, actualNotDeclared, declaredNotActual, networkName) {
    // Remove any existing popup
    const existingPopup = document.querySelector('.root-mismatch-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create popup
    const popup = document.createElement('div');
    popup.className = 'root-mismatch-popup';
    
    // Position popup near the click
    popup.style.left = (event.pageX + 10) + 'px';
    popup.style.top = (event.pageY + 10) + 'px';

    // Header
    const header = document.createElement('h4');
    header.innerHTML = `Root Mismatch: ${networkName}`;
    const closeBtn = document.createElement('button');
    closeBtn.className = 'close-btn';
    closeBtn.innerHTML = '×';
    closeBtn.onclick = () => popup.remove();
    header.appendChild(closeBtn);
    popup.appendChild(header);

    // Section for actual roots not in declared
    if (actualNotDeclared && actualNotDeclared.length > 0) {
        const section = document.createElement('div');
        section.className = 'section';
        
        const title = document.createElement('div');
        title.className = 'section-title';
        title.textContent = 'Actual roots NOT in declared roots array:';
        section.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'item-list';
        actualNotDeclared.forEach(root => {
            const item = document.createElement('li');
            item.textContent = root;
            list.appendChild(item);
        });
        section.appendChild(list);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-all-btn';
        copyBtn.textContent = 'Copy All';
        const copiedMsg = document.createElement('span');
        copiedMsg.className = 'copied-message';
        copiedMsg.textContent = 'Copied!';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(actualNotDeclared.join('\n')).then(() => {
                copiedMsg.style.display = 'inline';
                setTimeout(() => copiedMsg.style.display = 'none', 2000);
            });
        };
        section.appendChild(copyBtn);
        section.appendChild(copiedMsg);
        
        popup.appendChild(section);
    }

    // Section for declared roots not actual
    if (declaredNotActual && declaredNotActual.length > 0) {
        const section = document.createElement('div');
        section.className = 'section';
        
        const title = document.createElement('div');
        title.className = 'section-title';
        title.textContent = 'Declared roots NOT actual roots:';
        section.appendChild(title);
        
        const list = document.createElement('ul');
        list.className = 'item-list';
        declaredNotActual.forEach(root => {
            const item = document.createElement('li');
            item.textContent = root;
            list.appendChild(item);
        });
        section.appendChild(list);
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-all-btn';
        copyBtn.textContent = 'Copy All';
        const copiedMsg = document.createElement('span');
        copiedMsg.className = 'copied-message';
        copiedMsg.textContent = 'Copied!';
        copyBtn.onclick = () => {
            navigator.clipboard.writeText(declaredNotActual.join('\n')).then(() => {
                copiedMsg.style.display = 'inline';
                setTimeout(() => copiedMsg.style.display = 'none', 2000);
            });
        };
        section.appendChild(copyBtn);
        section.appendChild(copiedMsg);
        
        popup.appendChild(section);
    }

    document.body.appendChild(popup);

    // Close popup when clicking outside
    const closePopup = (e) => {
        if (!popup.contains(e.target)) {
            popup.remove();
            document.removeEventListener('click', closePopup);
        }
    };
    setTimeout(() => {
        document.addEventListener('click', closePopup);
    }, 0);

    // Adjust position if popup goes off screen
    const rect = popup.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
        popup.style.left = (window.innerWidth - rect.width - 10) + 'px';
    }
    if (rect.bottom > window.innerHeight) {
        popup.style.top = (window.innerHeight - rect.height - 10) + 'px';
    }
}

