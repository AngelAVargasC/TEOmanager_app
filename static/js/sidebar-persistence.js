/**
 * SIDEBAR PERSISTENCE MANAGER
 * Mantiene el estado del sidebar entre páginas y recargas
 * Sin flash de animación - Estado aplicado instantáneamente
 */

(function() {
    'use strict';
    
    const STORAGE_KEY = 'teomanager_sidebar_state';
    
    // ===== UTILITY FUNCTIONS =====
    function isMobile() {
        return window.innerWidth <= 1024;
    }
    
    function getSidebarState() {
        return localStorage.getItem(STORAGE_KEY) || '';
    }
    
    function setSidebarState(state) {
        if (state) {
            localStorage.setItem(STORAGE_KEY, state);
        } else {
            localStorage.removeItem(STORAGE_KEY);
        }
    }
    
    // ===== INSTANT STATE APPLICATION (NO FLASH) =====
    function applyInstantSidebarState() {
        const sidebar = document.getElementById('sidebar');
        const navbar = document.getElementById('navbar');
        const mainContent = document.getElementById('mainContent');
        const savedState = getSidebarState();
        
        if (!sidebar) return;
        
        // Disable ALL transitions temporarily
        const elementsToDisable = [sidebar, navbar, mainContent].filter(el => el);
        elementsToDisable.forEach(el => {
            el.classList.add('no-transition');
        });
        
        // Apply state based on device and saved preference
        if (isMobile()) {
            // Mobile: usually closed, open only if specifically saved as open
            if (savedState === 'mobile_open') {
                sidebar.classList.add('active');
            } else {
                sidebar.classList.remove('active');
            }
        } else {
            // Desktop: apply collapsed state if saved
            if (savedState === 'desktop_collapsed') {
                sidebar.classList.add('collapsed');
                if (navbar) navbar.classList.add('sidebar-collapsed');
                if (mainContent) mainContent.classList.add('sidebar-collapsed');
            } else {
                sidebar.classList.remove('collapsed');
                if (navbar) navbar.classList.remove('sidebar-collapsed');
                if (mainContent) mainContent.classList.remove('sidebar-collapsed');
            }
        }
        
        // Re-enable transitions after state is applied
        setTimeout(() => {
            elementsToDisable.forEach(el => {
                el.classList.remove('no-transition');
            });
        }, 50);
        
        console.log(`✅ Sidebar state applied: ${savedState || 'default'}`);
    }
    
    // ===== HANDLE PAGE NAVIGATION (SPA-like behavior) =====
    function handlePageChange() {
        // Reapply state on any navigation (including back/forward)
        applyInstantSidebarState();
    }
    
    // ===== RESPONSIVE HANDLER =====
    function handleResize() {
        // Reapply appropriate state when switching mobile/desktop
        applyInstantSidebarState();
    }
    
    // ===== INITIALIZATION =====
    function initializeSidebarPersistence() {
        // Apply state immediately
        applyInstantSidebarState();
        
        // Handle browser navigation
        window.addEventListener('popstate', handlePageChange);
        
        // Handle resize events (mobile/desktop switch)
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(handleResize, 100);
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                applyInstantSidebarState();
            }
        });
    }
    
    // ===== PUBLIC API =====
    window.SidebarPersistence = {
        get: getSidebarState,
        set: setSidebarState,
        apply: applyInstantSidebarState,
        isMobile: isMobile
    };
    
    // ===== AUTO-INITIALIZE =====
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSidebarPersistence);
    } else {
        initializeSidebarPersistence();
    }
    
})(); 