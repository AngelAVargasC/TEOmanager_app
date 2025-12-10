"""
Context processors para hacer disponibles variables globales en todas las plantillas.
"""

def user_profile(request):
    """
    Context processor que hace disponible el perfil del usuario en todas las plantillas.
    También incluye información del carrito para usuarios consumidores.
    """
    context = {
        'perfil': None,
        'user_profile': None,
        'cart_count': 0,
        'cart_total': 0
    }
    
    if request.user.is_authenticated:
        try:
            # Intentar obtener PerfilUsuario (nuevo modelo)
            from .models import PerfilUsuario
            perfil = PerfilUsuario.objects.select_related('usuario').get(usuario=request.user)
            context['perfil'] = perfil
            
            # Agregar información del carrito para usuarios consumidores
            if perfil.tipo_cuenta == 'usuario':
                from apps.productservice.models import Producto
                from decimal import Decimal
                
                cart_session = request.session.get('cart', {})
                cart_count = sum(cart_session.values()) if cart_session else 0
                cart_total = Decimal('0')
                cart_preview = []
                
                if cart_session:
                    # Calcular total del carrito y crear preview
                    productos_a_eliminar = []
                    
                    for i, (prod_id, qty) in enumerate(cart_session.items()):
                        try:
                            producto = Producto.objects.get(pk=int(prod_id), activo=True)
                            cart_total += producto.precio * qty
                            
                            # Agregar a preview (solo primeros 3)
                            if i < 3:
                                cart_preview.append({
                                    'producto': producto,
                                    'cantidad': qty
                                })
                                
                        except (Producto.DoesNotExist, ValueError):
                            # Marcar productos que ya no existen para eliminarlos
                            productos_a_eliminar.append(str(prod_id))
                    
                    # Eliminar productos que ya no existen del carrito
                    if productos_a_eliminar:
                        for prod_id in productos_a_eliminar:
                            cart_session.pop(prod_id, None)
                        request.session['cart'] = cart_session
                        cart_count = sum(cart_session.values())
                
                context['cart_count'] = cart_count
                context['cart_total'] = cart_total
                context['cart_preview'] = cart_preview
                    
        except PerfilUsuario.DoesNotExist:
            pass
        except ImportError:
            pass
        
        # También intentar userprofile (modelo anterior)
        if hasattr(request.user, 'userprofile'):
            context['user_profile'] = request.user.userprofile
    
    return context 