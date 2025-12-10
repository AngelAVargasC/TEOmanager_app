// ===== FUNCIONES DE ADMIN - JAVASCRIPT UNIFICADO =====

// === FUNCIONES GENERALES ===

// Función para exportar usuarios
function exportUsers() {
    // Mostrar loading en el botón
    const btn = event.target.closest('.btn-export');
    btn.classList.add('btn-loading');
    btn.disabled = true;
    
    // Simular exportación (aquí iría la lógica real)
    setTimeout(() => {
        // Crear y descargar archivo CSV de ejemplo
        const csvContent = generateUsersCSV();
        downloadCSV(csvContent, 'usuarios_export.csv');
        
        // Remover loading
        btn.classList.remove('btn-loading');
        btn.disabled = false;
        
        // Mostrar notificación de éxito
        showNotification('Usuarios exportados exitosamente', 'success');
    }, 2000);
}

// Función para generar CSV de usuarios
function generateUsersCSV() {
    const headers = ['ID', 'Usuario', 'Email', 'Empresa', 'Estado', 'Fecha Registro'];
    const rows = [];
    
    // Obtener datos de la tabla
    document.querySelectorAll('.user-row').forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            const rowData = [
                row.dataset.userId || '',
                cells[0]?.querySelector('.username')?.textContent?.trim() || '',
                cells[1]?.querySelector('.email')?.textContent?.trim() || '',
                cells[2]?.querySelector('.company-name')?.textContent?.trim() || '',
                cells[4]?.querySelector('.status-badge')?.textContent?.trim() || '',
                cells[3]?.querySelector('.date')?.textContent?.trim() || ''
            ];
            rows.push(rowData);
        }
    });
    
    // Convertir a CSV
    const csvRows = [headers, ...rows];
    return csvRows.map(row => row.map(field => `"${field}"`).join(',')).join('\n');
}

// Función para descargar CSV
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Función para mostrar/ocultar filtros avanzados
function toggleAdvancedFilters() {
    const filters = document.getElementById('advancedFilters');
    const btn = event.target.closest('.btn-icon');
    
    if (filters) {
        const isVisible = filters.style.display !== 'none';
        filters.style.display = isVisible ? 'none' : 'block';
        
        // Cambiar icono del botón
        const icon = btn.querySelector('i');
        if (icon) {
            icon.className = isVisible ? 'fas fa-filter' : 'fas fa-filter-circle-xmark';
        }
        
        // Agregar clase activa
        btn.classList.toggle('active', !isVisible);
    }
}

// === FUNCIONES DE PRODUCTOS ===

// Función para editar producto
function editProduct(productId) {
    const btn = event.target.closest('.btn-edit');
    btn.classList.add('btn-loading');
    
    // Simular carga
    setTimeout(() => {
        btn.classList.remove('btn-loading');
        showNotification(`Editando producto ID: ${productId}`, 'info');
        // Aquí iría la lógica real de edición
    }, 1000);
}

// Función para eliminar producto
function deleteProduct(productId) {
    if (confirm('¿Estás seguro de que quieres eliminar este producto?')) {
        const btn = event.target.closest('.btn-delete');
        btn.classList.add('btn-loading');
        
        // Simular eliminación
        setTimeout(() => {
            btn.classList.remove('btn-loading');
            
            // Remover la tarjeta del producto
            const productCard = btn.closest('.product-card');
            if (productCard) {
                productCard.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => {
                    productCard.remove();
                    showNotification('Producto eliminado exitosamente', 'success');
                }, 500);
            }
        }, 1000);
    }
}

// === FUNCIONES DE SERVICIOS ===

// Función para editar servicio
function editService(serviceId) {
    const btn = event.target.closest('.btn-edit');
    btn.classList.add('btn-loading');
    
    // Simular carga
    setTimeout(() => {
        btn.classList.remove('btn-loading');
        showNotification(`Editando servicio ID: ${serviceId}`, 'info');
        // Aquí iría la lógica real de edición
    }, 1000);
}

// Función para eliminar servicio
function deleteService(serviceId) {
    if (confirm('¿Estás seguro de que quieres eliminar este servicio?')) {
        const btn = event.target.closest('.btn-delete');
        btn.classList.add('btn-loading');
        
        // Simular eliminación
        setTimeout(() => {
            btn.classList.remove('btn-loading');
            
            // Remover la tarjeta del servicio
            const serviceCard = btn.closest('.service-card');
            if (serviceCard) {
                serviceCard.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => {
                    serviceCard.remove();
                    showNotification('Servicio eliminado exitosamente', 'success');
                }, 500);
            }
        }, 1000);
    }
}

// === FUNCIONES DE PEDIDOS ===

// Función para ver detalles del pedido
function viewOrderDetails(orderId) {
    const btn = event.target.closest('.btn-view');
    btn.classList.add('btn-loading');
    
    // Simular carga
    setTimeout(() => {
        btn.classList.remove('btn-loading');
        showNotification(`Viendo detalles del pedido ID: ${orderId}`, 'info');
        // Aquí iría la lógica real para mostrar detalles
    }, 1000);
}

// === FUNCIONES DE NOTIFICACIONES ===

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="closeNotification(this)">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Agregar estilos si no existen
    if (!document.querySelector('#notification-styles')) {
        const styles = document.createElement('style');
        styles.id = 'notification-styles';
        styles.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                background: white;
                border-radius: 10px;
                padding: 1rem 1.5rem;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                z-index: 10000;
                display: flex;
                align-items: center;
                gap: 1rem;
                min-width: 300px;
                animation: slideInRight 0.3s ease-out;
                border-left: 4px solid #3b82f6;
            }
            
            .notification-success { border-left-color: #10b981; }
            .notification-error { border-left-color: #ef4444; }
            .notification-warning { border-left-color: #f59e0b; }
            .notification-info { border-left-color: #3b82f6; }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                flex: 1;
            }
            
            .notification-close {
                background: none;
                border: none;
                color: #6b7280;
                cursor: pointer;
                padding: 0.25rem;
                border-radius: 4px;
            }
            
            .notification-close:hover {
                background: #f3f4f6;
                color: #374151;
            }
            
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            
            @keyframes fadeOut {
                from {
                    opacity: 1;
                    transform: scale(1);
                }
                to {
                    opacity: 0;
                    transform: scale(0.95);
                }
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Agregar al DOM
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
        closeNotification(notification.querySelector('.notification-close'));
    }, 5000);
}

// Función para obtener icono de notificación
function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Función para cerrar notificación
function closeNotification(btn) {
    const notification = btn.closest('.notification');
    if (notification) {
        notification.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }
}

// === FUNCIONES DE UTILIDAD ===

// Función para confirmar acciones peligrosas
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Función para formatear fechas
function formatDate(date) {
    return new Date(date).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// === FUNCIONES DE ELIMINACIÓN DE USUARIOS ===

// Variable global para almacenar el userId actual
let currentDeleteUserId = null;

// Función para abrir el modal de eliminación
function deleteUser(userId, username) {
    console.log('deleteUser llamado con:', userId, username);
    
    currentDeleteUserId = userId;
    
    // Obtener elementos del modal
    const modal = document.getElementById('deleteUserModal');
    const usernameSpan = document.getElementById('deleteModalUsername');
    const confirmInput = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('deleteModalConfirmBtn');
    
    if (!modal) {
        console.error('Modal de eliminación no encontrado');
        return;
    }
    
    // Configurar el nombre de usuario
    if (usernameSpan) {
        usernameSpan.textContent = username;
    }
    
    // Limpiar el input y deshabilitar el botón
    if (confirmInput) {
        confirmInput.value = '';
        confirmInput.classList.remove('error', 'success');
        confirmInput.focus();
    }
    
    if (confirmBtn) {
        confirmBtn.disabled = true;
    }
    
    // Mostrar el modal
    modal.classList.add('show');
    document.body.style.overflow = 'hidden'; // Prevenir scroll del body
    
    // Agregar listener al input para validar en tiempo real
    if (confirmInput) {
        confirmInput.addEventListener('input', validateDeleteInput);
    }
    
    // Agregar listener al botón de confirmar
    if (confirmBtn) {
        confirmBtn.onclick = function() {
            if (confirmInput && confirmInput.value.toUpperCase() === 'ELIMINAR') {
                executeUserDeletion(userId);
            }
        };
    }
    
    // Cerrar modal con ESC
    document.addEventListener('keydown', handleModalEscape);
}

// Función para validar el input de confirmación
function validateDeleteInput() {
    const input = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('deleteModalConfirmBtn');
    
    if (!input || !confirmBtn) return;
    
    const value = input.value.toUpperCase().trim();
    
    // Remover clases anteriores
    input.classList.remove('error', 'success');
    
    if (value === '') {
        confirmBtn.disabled = true;
    } else if (value === 'ELIMINAR') {
        input.classList.add('success');
        confirmBtn.disabled = false;
    } else {
        input.classList.add('error');
        confirmBtn.disabled = true;
    }
}

// Función para cerrar el modal
function closeDeleteModal() {
    const modal = document.getElementById('deleteUserModal');
    const confirmInput = document.getElementById('deleteConfirmInput');
    
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = ''; // Restaurar scroll
    }
    
    if (confirmInput) {
        confirmInput.removeEventListener('input', validateDeleteInput);
        confirmInput.value = '';
        confirmInput.classList.remove('error', 'success');
    }
    
    // Remover listener de ESC
    document.removeEventListener('keydown', handleModalEscape);
    
    currentDeleteUserId = null;
}

// Función para manejar la tecla ESC
function handleModalEscape(e) {
    if (e.key === 'Escape') {
        closeDeleteModal();
    }
}

// Función para ejecutar la eliminación
function executeUserDeletion(userId) {
    // Crear formulario para enviar POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/dashboard/users/${userId}/delete/`;
    
    // Agregar CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken.value;
        form.appendChild(csrfInput);
    } else {
        // Obtener CSRF token de cookies
        const csrfCookie = getCookie('csrftoken');
        if (csrfCookie) {
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfCookie;
            form.appendChild(csrfInput);
        } else {
            closeDeleteModal();
            showNotification('Error: No se pudo obtener el token CSRF. Por favor, recarga la página.', 'error');
            return;
        }
    }
    
    // Cerrar el modal antes de enviar
    closeDeleteModal();
    
    // Agregar al DOM y enviar
    document.body.appendChild(form);
    console.log('Enviando formulario de eliminación...');
    form.submit();
}

// Función auxiliar para obtener cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// === INICIALIZACIÓN ===

// Inicializar funciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Agregar event listeners para eliminar usuarios (usando delegación de eventos para dropdowns)
    document.addEventListener('click', function(e) {
        const deleteBtn = e.target.closest('.delete-user');
        if (deleteBtn) {
            e.preventDefault();
            e.stopPropagation();
            const userId = deleteBtn.dataset.userId;
            const username = deleteBtn.dataset.username || 'este usuario';
            deleteUser(userId, username);
        }
    });
    
    // Cerrar modal al hacer clic fuera de él
    const modal = document.getElementById('deleteUserModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeDeleteModal();
            }
        });
    }
    // Agregar tooltips mejorados a botones
    document.querySelectorAll('[title]').forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.setAttribute('data-original-title', this.getAttribute('title'));
            this.removeAttribute('title');
        });
        
        element.addEventListener('mouseleave', function() {
            const originalTitle = this.getAttribute('data-original-title');
            if (originalTitle) {
                this.setAttribute('title', originalTitle);
                this.removeAttribute('data-original-title');
            }
        });
    });
    
    // Agregar efectos de ripple a botones
    document.querySelectorAll('button, .btn-export, .btn-refresh, .btn-back').forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    console.log('Admin functions initialized successfully');
});

// Agregar estilos para el efecto ripple
const rippleStyles = document.createElement('style');
rippleStyles.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(rippleStyles); 