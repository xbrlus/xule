// UI Handlers Module
// Handles UI interactions like resizable panels

/**
 * Initialize resizable panel functionality
 * Allows users to drag the divider to resize the left panel
 */
export function initResizablePanel() {
    const resizeHandle = document.getElementById('resize-handle');
    const treeContainer = document.getElementById('tree-container');
    
    if (!resizeHandle || !treeContainer) {
        console.warn('Resize handle or tree container not found');
        return;
    }
    
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;

    resizeHandle.addEventListener('mousedown', function(e) {
        isResizing = true;
        startX = e.clientX;
        startWidth = treeContainer.offsetWidth;
        resizeHandle.classList.add('dragging');
        
        // Prevent text selection during drag
        e.preventDefault();
        
        // Add pointer-events: none to prevent interference
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    });

    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        
        const deltaX = e.clientX - startX;
        const newWidth = startWidth + deltaX;
        const minWidth = 200;
        const maxWidth = window.innerWidth * 0.8;
        
        // Constrain the width
        if (newWidth >= minWidth && newWidth <= maxWidth) {
            treeContainer.style.width = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            resizeHandle.classList.remove('dragging');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
        }
    });
    
    console.log('Resizable panel initialized');
}

/**
 * Initialize all UI handlers
 */
export function initAllUIHandlers() {
    initResizablePanel();
    console.log('All UI handlers initialized');
}
