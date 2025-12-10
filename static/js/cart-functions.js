/**
 * Funciones JavaScript para el manejo dinámico del carrito de compras
 * Mejora la experiencia del usuario con actualizaciones en tiempo real
 */

// Variables globales
let cartUpdateInProgress = false;

/**
 * Actualiza la información del carrito en el navbar dinámicamente
 */
function updateCartDisplay(cartCount, cartTotal) {
    const cartLink = document.querySelector('.cart-link');
    if (!cartLink) {
        console.error('Cart link not found');
        return;
    }

    console.log(`Updating cart display: count=${cartCount}, total=${cartTotal}`);

    let cartBadge = cartLink.querySelector('.cart-badge');
    let cartTotalSpan = cartLink.querySelector('.cart-total');
    let cartEmpty = cartLink.querySelector('.cart-empty');

    if (cartCount > 0) {
        // Crear elementos si no existen (para casos donde el carrito estaba vacío)
        if (!cartBadge) {
            cartBadge = document.createElement('span');
            cartBadge.className = 'cart-badge';
            cartLink.appendChild(cartBadge);
            console.log('Created cart badge element');
        }
        
        if (!cartTotalSpan) {
            cartTotalSpan = document.createElement('span');
            cartTotalSpan.className = 'cart-total';
            cartLink.appendChild(cartTotalSpan);
            console.log('Created cart total element');
        }
        
        // Actualizar contador y total
        cartBadge.textContent = cartCount;
        cartBadge.style.display = 'flex';
        
        cartTotalSpan.textContent = `$${parseFloat(cartTotal).toFixed(2)}`;
        cartTotalSpan.style.display = 'inline';
        
        // Ocultar texto "Carrito"
        if (cartEmpty) {
            cartEmpty.style.display = 'none';
        }
        
        // Animación de actualización
        cartLink.classList.add('cart-updated');
        setTimeout(() => cartLink.classList.remove('cart-updated'), 500);
        
        console.log(`Cart display updated: badge=${cartBadge.textContent}, total=${cartTotalSpan.textContent}`);
        
    } else {
        // Carrito vacío
        if (cartBadge) cartBadge.style.display = 'none';
        if (cartTotalSpan) cartTotalSpan.style.display = 'none';
        if (cartEmpty) {
            cartEmpty.style.display = 'inline';
            cartEmpty.textContent = 'Carrito';
        }
        
        console.log('Cart display updated: empty state');
    }
}

/**
 * Actualiza la vista previa del carrito dinámicamente
 */
async function updateCartPreview() {
    console.log('Updating cart preview...');
    
    try {
        const response = await fetch('/cart-preview/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        });
        
        console.log('Cart preview response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Cart preview data received:', data);
        
        if (data.success) {
            updateCartPreviewHTML(data.cart_items, data.cart_count, data.cart_total);
            
            // También actualizar el contador del navbar si es necesario
            if (data.cart_count !== undefined && data.cart_total !== undefined) {
                updateCartDisplay(data.cart_count, data.cart_total);
            }
        } else {
            console.error('Cart preview failed:', data.message);
        }
        
    } catch (error) {
        console.error('Error updating cart preview:', error);
        
        // Mostrar carrito vacío en caso de error
        const previewContent = document.querySelector('.cart-preview-content');
        if (previewContent) {
            previewContent.innerHTML = `
                <div class="cart-preview-empty">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error al cargar el carrito</p>
                    <a href="/marketplace/" class="btn-preview btn-primary">Ir al Catálogo</a>
                </div>
            `;
        }
    }
}

/**
 * Actualiza el HTML de la vista previa del carrito
 */
function updateCartPreviewHTML(cartItems, cartCount, cartTotal) {
    const previewContent = document.querySelector('.cart-preview-content');
    if (!previewContent) {
        console.error('Cart preview content element not found');
        return;
    }
    
    console.log('Updating cart preview HTML with:', { cartItems, cartCount, cartTotal });
    
    if (cartCount > 0 && cartItems && cartItems.length > 0) {
        let itemsHTML = '';
        
        cartItems.forEach(item => {
            console.log('Processing item:', item);
            
            // Manejar imagen de manera más robusta
            let imageHTML;
            if (item.imagen_principal && item.imagen_principal.trim() !== '') {
                imageHTML = `<img src="${item.imagen_principal}" alt="${item.nombre || 'Producto'}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                           <i class="fas fa-box" style="display:none;"></i>`;
            } else {
                imageHTML = `<i class="fas fa-box"></i>`;
            }
            
            const nombre = item.nombre || 'Producto sin nombre';
            const cantidad = item.cantidad || 1;
            const precio = parseFloat(item.precio || 0);
            
            itemsHTML += `
                <div class="cart-preview-item">
                    <div class="item-image">
                        ${imageHTML}
                    </div>
                    <div class="item-info">
                        <div class="item-name" title="${nombre}">${nombre}</div>
                        <div class="item-details">
                            <span class="item-qty">${cantidad}x</span>
                            <span class="item-price">$${precio.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        let moreItemsHTML = '';
        if (cartCount > 3) {
            const moreCount = cartCount - 3;
            moreItemsHTML = `
                <div class="cart-preview-more">
                    + ${moreCount} producto${moreCount > 1 ? 's' : ''} más
                </div>
            `;
        }
        
        const totalFormatted = parseFloat(cartTotal || 0).toFixed(2);
        
        previewContent.innerHTML = `
            <div class="cart-preview-items">
                ${itemsHTML}
                ${moreItemsHTML}
            </div>
            <div class="cart-preview-footer">
                <div class="cart-preview-total">
                    <strong>Total: $${totalFormatted}</strong>
                </div>
                <div class="cart-preview-actions">
                    <a href="/cart/" class="btn-preview btn-primary">Ver Carrito</a>
                    <a href="/cart/" class="btn-preview btn-success">Pagar</a>
                </div>
            </div>
        `;
        
        console.log('Cart preview updated successfully');
        
    } else {
        console.log('Showing empty cart preview');
        previewContent.innerHTML = `
            <div class="cart-preview-empty">
                <i class="fas fa-shopping-cart"></i>
                <p>Tu carrito está vacío</p>
                <a href="/marketplace/" class="btn-preview btn-primary">Ir al catálogo</a>
            </div>
        `;
    }
}

/**
 * Agrega un producto al carrito vía AJAX
 */
async function addToCartAjax(productId, csrfToken) {
    if (cartUpdateInProgress) return;
    
    cartUpdateInProgress = true;
    console.log(`Adding product ${productId} to cart via AJAX...`);
    
    try {
        const response = await fetch(`/cart/add/${productId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({})
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (data.success) {
            console.log('✅ AJAX Success! Cart data received:', {
                count: data.cart_count,
                total: data.cart_total,
                message: data.message
            });
            
            // Actualizar display del carrito inmediatamente
            console.log('🔄 Calling updateCartDisplay...');
            updateCartDisplay(data.cart_count, data.cart_total);
            
            // Actualizar vista previa del carrito con un pequeño delay
            setTimeout(() => {
                console.log('🔄 Calling updateCartPreview...');
                updateCartPreview();
            }, 100);
            
            // Mostrar notificación de éxito
            showCartNotification(data.message, 'success');
            
            // Actualizar botón si existe
            const addButton = document.querySelector(`[data-product-id="${productId}"]`);
            if (addButton) {
                addButton.classList.add('btn-success-flash');
                setTimeout(() => addButton.classList.remove('btn-success-flash'), 300);
            }
            
            console.log('✅ Product added successfully via AJAX');
            
        } else {
            console.error('❌ Server responded with error:', data.message);
            showCartNotification(data.message, 'error');
        }
        
    } catch (error) {
        console.error('AJAX Error adding to cart:', error);
        showCartNotification('Error al agregar producto al carrito', 'error');
        
        // Fallback: usar método tradicional
        console.log('Falling back to traditional method');
        window.location.href = `/cart/add/${productId}/`;
    } finally {
        cartUpdateInProgress = false;
    }
}

/**
 * Muestra notificaciones del carrito
 */
function showCartNotification(message, type = 'success') {
    // Crear notificación
    const notification = document.createElement('div');
    notification.className = `cart-notification cart-notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Agregar al DOM
    document.body.appendChild(notification);
    
    // Mostrar con animación
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

/**
 * Función simple para agregar al carrito (fallback)
 */
function addToCartSimple(productId) {
    console.log('Using simple add to cart for product:', productId);
    window.location.href = `/cart/add/${productId}/`;
}

/**
 * Inicializar event listeners cuando el DOM esté listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Cart functions loaded');
    
    // Event listener para botones de agregar al carrito
    document.addEventListener('click', function(e) {
        const addButton = e.target.closest('[data-add-to-cart]');
        if (addButton) {
            e.preventDefault();
            console.log('Add to cart button clicked');
            
            const productId = addButton.dataset.productId || addButton.dataset.addToCart;
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            
            console.log('Product ID:', productId);
            console.log('CSRF Token exists:', !!csrfToken);
            
            if (productId) {
                if (csrfToken) {
                    // Intentar AJAX primero
                    addToCartAjax(productId, csrfToken);
                } else {
                    // Usar método simple si no hay CSRF token
                    console.log('No CSRF token, using simple method');
                    addToCartSimple(productId);
                }
            } else {
                console.error('No product ID found');
            }
        }
    });
    
    // Event listener para el ícono del carrito (efectos visuales)
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
        cartLink.addEventListener('mouseenter', function() {
            const cartIcon = this.querySelector('i');
            if (cartIcon) {
                cartIcon.classList.add('fa-bounce');
                setTimeout(() => cartIcon.classList.remove('fa-bounce'), 1000);
            }
        });
    }
    
    // Event listeners para la vista previa del carrito
    const cartDropdown = document.querySelector('.cart-dropdown');
    if (cartDropdown) {
        // Prevenir que el dropdown se cierre al hacer click dentro
        const cartPreview = cartDropdown.querySelector('.cart-preview-dropdown');
        if (cartPreview) {
            cartPreview.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
        
        // Cargar vista previa al hacer hover
        cartDropdown.addEventListener('mouseenter', function() {
            updateCartPreview();
        });
    }
    
    // Actualizar carrito al cargar la página (obtener estado actual)
    const cartCount = parseInt(document.querySelector('.cart-badge')?.textContent || '0');
    const cartTotal = document.querySelector('.cart-total')?.textContent?.replace('$', '') || '0';
    
    if (cartCount > 0) {
        updateCartDisplay(cartCount, cartTotal);
        updateCartPreview(); // Cargar vista previa inicial
    }
});

/**
 * Estilos CSS dinámicos para las notificaciones
 */
const cartStyles = `
    .cart-notification {
        position: fixed;
        top: 80px;
        right: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        padding: 1rem 1.5rem;
        border-left: 4px solid #10b981;
        z-index: 9999;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
    }
    
    .cart-notification.show {
        transform: translateX(0);
    }
    
    .cart-notification-error {
        border-left-color: #ef4444;
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.9rem;
    }
    
    .cart-notification-success .notification-content i {
        color: #10b981;
    }
    
    .cart-notification-error .notification-content i {
        color: #ef4444;
    }
    
    .cart-updated {
        animation: cartPulse 0.5s ease;
    }
    
    @keyframes cartPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .btn-success-flash {
        animation: successFlash 0.3s ease;
    }
    
    @keyframes successFlash {
        0% { background: #10b981; transform: scale(1); }
        50% { background: #059669; transform: scale(1.05); }
        100% { background: #10b981; transform: scale(1); }
    }
    
    @media (max-width: 768px) {
        .cart-notification {
            right: 10px;
            left: 10px;
            max-width: none;
        }
    }
`;

// Inyectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = cartStyles;
document.head.appendChild(styleSheet); 