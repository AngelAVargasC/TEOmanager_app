// Simplified main.js - optimized for performance

// ===== APPLY SIDEBAR STATE IMMEDIATELY (NO FLASH) =====
(function() {
    'use strict';
    
    function isMobile() {
        return window.innerWidth <= 1024;
    }
    
    function getSidebarState() {
        return localStorage.getItem('teomanager_sidebar_state') || '';
    }
    
    // Aplicar estado INMEDIATAMENTE sin esperar DOMContentLoaded
    function applyInstantSidebarState() {
        const sidebar = document.getElementById('sidebar');
        const navbar = document.getElementById('navbar');
        const mainContent = document.getElementById('mainContent');
        const savedState = getSidebarState();
        
        if (!sidebar) return;
        
        // DISABLE TRANSITIONS TEMPORARILY to prevent flash
        sidebar.style.transition = 'none';
        if (navbar) navbar.style.transition = 'none';
        if (mainContent) mainContent.style.transition = 'none';
        
        if (isMobile()) {
            // En móvil, cerrado por defecto (sin overlay en carga inicial)
            if (savedState === 'mobile_open') {
                sidebar.classList.add('active');
            } else {
                sidebar.classList.remove('active');
            }
        } else {
            // En desktop, aplicar estado colapsado si está guardado
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
        
        // Re-enable transitions after applying state
        setTimeout(() => {
            sidebar.style.transition = '';
            if (navbar) navbar.style.transition = '';
            if (mainContent) mainContent.style.transition = '';
        }, 50);
    }
    
    // Execute immediately if DOM is ready, otherwise wait
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyInstantSidebarState);
    } else {
        applyInstantSidebarState();
    }
})();

document.addEventListener('DOMContentLoaded', function() {
    // ===== SIDEBAR FUNCTIONALITY =====
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const navbar = document.getElementById('navbar');
    const mainContent = document.getElementById('mainContent');
    
    if (sidebar && sidebarToggle) {
        
        // ===== UTILITY FUNCTIONS =====
        function isMobile() {
            return window.innerWidth <= 1024;
        }
        
        function getSidebarState() {
            return window.SidebarPersistence ? 
                   window.SidebarPersistence.get() : 
                   localStorage.getItem('teomanager_sidebar_state') || '';
        }
        
        function setSidebarState(state) {
            if (window.SidebarPersistence) {
                window.SidebarPersistence.set(state);
            } else {
                if (state) {
                    localStorage.setItem('teomanager_sidebar_state', state);
                } else {
                    localStorage.removeItem('teomanager_sidebar_state');
                }
            }
        }
        
        // ===== APPLY SIDEBAR OVERLAY STATE (Mobile only) =====
        function applyOverlayState() {
            const savedState = getSidebarState();
            
            if (isMobile() && savedState === 'mobile_open') {
                // Solo aplicar overlay si está abierto en móvil
                if (sidebarOverlay) sidebarOverlay.style.display = 'block';
            } else {
                if (sidebarOverlay) sidebarOverlay.style.display = 'none';
            }
        }
        
        // ===== TOGGLE FUNCTIONALITY =====
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (isMobile()) {
                // Comportamiento móvil
                sidebar.classList.toggle('active');
                const isActive = sidebar.classList.contains('active');
                
                if (sidebarOverlay) {
                    sidebarOverlay.style.display = isActive ? 'block' : 'none';
                }
                
                setSidebarState(isActive ? 'mobile_open' : 'mobile_closed');
            } else {
                // Comportamiento desktop
                sidebar.classList.toggle('collapsed');
                if (navbar) navbar.classList.toggle('sidebar-collapsed');
                if (mainContent) mainContent.classList.toggle('sidebar-collapsed');
                
                const isCollapsed = sidebar.classList.contains('collapsed');
                setSidebarState(isCollapsed ? 'desktop_collapsed' : '');
            }
        });
        
        // ===== OVERLAY CLICK =====
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('active');
                sidebarOverlay.style.display = 'none';
                setSidebarState('mobile_closed');
            });
        }
        
        // ===== CLICK OUTSIDE TO CLOSE (MOBILE) =====
        document.addEventListener('click', function(e) {
            if (isMobile() && 
                sidebar.classList.contains('active') &&
                !sidebar.contains(e.target) && 
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('active');
                if (sidebarOverlay) sidebarOverlay.style.display = 'none';
                setSidebarState('mobile_closed');
            }
        });
        
        // ===== RESIZE HANDLER =====
        window.addEventListener('resize', function() {
            if (!isMobile()) {
                // Cambio a desktop - limpiar clases móviles
                sidebar.classList.remove('active');
                if (sidebarOverlay) sidebarOverlay.style.display = 'none';
                
                // Aplicar estado desktop guardado
                const savedState = getSidebarState();
                if (savedState === 'desktop_collapsed') {
                    sidebar.classList.add('collapsed');
                    if (navbar) navbar.classList.add('sidebar-collapsed');
                    if (mainContent) mainContent.classList.add('sidebar-collapsed');
                } else {
                    sidebar.classList.remove('collapsed');
                    if (navbar) navbar.classList.remove('sidebar-collapsed');
                    if (mainContent) mainContent.classList.remove('sidebar-collapsed');
                }
            } else {
                // Cambio a móvil - limpiar clases desktop
                sidebar.classList.remove('collapsed');
                if (navbar) navbar.classList.remove('sidebar-collapsed');
                if (mainContent) mainContent.classList.remove('sidebar-collapsed');
                
                // En móvil cerrado por defecto
                const savedState = getSidebarState();
                if (savedState === 'mobile_open') {
                    sidebar.classList.add('active');
                    if (sidebarOverlay) sidebarOverlay.style.display = 'block';
                } else {
                    sidebar.classList.remove('active');
                    if (sidebarOverlay) sidebarOverlay.style.display = 'none';
                }
            }
        });
        
        // ===== APPLY INITIAL OVERLAY STATE =====
        applyOverlayState();
    }
    
    // ===== AUTO-HIDE MESSAGES =====
    const messages = document.querySelectorAll('.alert');
    messages.forEach(function(message) {
        setTimeout(() => {
            if (message && message.parentElement) {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }
        }, 5000);
    });
    
    console.log('TEOmanager initialized successfully');
}); 