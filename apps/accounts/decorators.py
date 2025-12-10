"""
Decoradores personalizados para control de acceso y permisos.

Este módulo contiene decoradores que implementan lógica de autorización
y control de acceso específica para la aplicación. Complementan el sistema
de autenticación de Django con reglas de negocio personalizadas.

Decoradores disponibles:
- empresa_required: Requiere cuenta empresarial
- admin_required: Requiere permisos de administrador
- subscription_required: Requiere suscripción activa
- plan_limit_check: Verifica límites del plan
- profile_complete_required: Requiere perfil completo
"""

from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.exceptions import PermissionDenied
import logging

from .services import SuscripcionService

logger = logging.getLogger(__name__)


def empresa_required(view_func=None, *, redirect_url=None, message=None):
    """
    Decorador que requiere que el usuario sea de tipo empresa.
    
    Args:
        view_func: Función de vista a decorar
        redirect_url: URL de redirección si no cumple el requisito
        message: Mensaje personalizado de error
        
    Usage:
        @empresa_required
        def mi_vista(request):
            # Solo usuarios empresariales pueden acceder
            pass
            
        @empresa_required(redirect_url='upgrade_account', message='Necesitas una cuenta empresarial')
        def vista_premium(request):
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar perfil
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, "Perfil de usuario no encontrado")
                return redirect('perfil')
            
            # Verificar tipo de cuenta
            if request.user.userprofile.tipo_cuenta != 'empresa':
                error_message = message or "Acceso denegado: Solo para cuentas empresariales"
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': error_message}, status=403)
                
                messages.error(request, error_message)
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(error_message)
            
            return func(request, *args, **kwargs)
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def admin_required(view_func=None, *, redirect_url=None, message=None):
    """
    Decorador que requiere permisos de administrador.
    
    Args:
        view_func: Función de vista a decorar
        redirect_url: URL de redirección si no cumple el requisito
        message: Mensaje personalizado de error
        
    Usage:
        @admin_required
        def panel_admin(request):
            # Solo administradores pueden acceder
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar perfil y permisos
            if not hasattr(request.user, 'userprofile') or not request.user.userprofile.is_admin:
                error_message = message or "Acceso denegado: Permisos de administrador requeridos"
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': error_message}, status=403)
                
                messages.error(request, error_message)
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(error_message)
            
            return func(request, *args, **kwargs)
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def subscription_required(plans=None, redirect_url=None, message=None):
    """
    Decorador que requiere suscripción activa.
    
    Args:
        plans: Lista de planes permitidos (None = cualquier plan activo)
        redirect_url: URL de redirección si no cumple el requisito
        message: Mensaje personalizado de error
        
    Usage:
        @subscription_required()
        def feature_premium(request):
            # Requiere cualquier suscripción activa
            pass
            
        @subscription_required(plans=['premium', 'empresarial'])
        def feature_advanced(request):
            # Requiere plan premium o empresarial
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar perfil
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, "Perfil de usuario no encontrado")
                return redirect('perfil')
            
            perfil = request.user.userprofile
            
            # Verificar suscripción activa
            if not perfil.suscripcion_activa:
                error_message = message or "Suscripción activa requerida para acceder a esta función"
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': error_message}, status=403)
                
                messages.warning(request, error_message)
                return redirect(redirect_url or 'suscripciones')
            
            # Verificar plan específico si se especifica
            if plans:
                suscripcion_actual = request.user.suscripciones.filter(activa=True).first()
                if not suscripcion_actual or suscripcion_actual.plan not in plans:
                    error_message = message or f"Plan {' o '.join(plans)} requerido para esta función"
                    
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({'error': error_message}, status=403)
                    
                    messages.warning(request, error_message)
                    return redirect(redirect_url or 'suscripciones')
            
            return func(request, *args, **kwargs)
        return wrapper
    
    return decorator


def plan_limit_check(resource_type, redirect_url=None, message=None):
    """
    Decorador que verifica los límites del plan antes de crear recursos.
    
    Args:
        resource_type: Tipo de recurso ('productos', 'servicios', 'landing_pages')
        redirect_url: URL de redirección si se excede el límite
        message: Mensaje personalizado de error
        
    Usage:
        @plan_limit_check('productos')
        def crear_producto(request):
            # Verifica límite de productos antes de crear
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Solo verificar en métodos POST (creación)
            if request.method == 'POST':
                limits = SuscripcionService.check_plan_limits(request.user, resource_type)
                
                if not limits['allowed']:
                    error_message = message or limits['message']
                    
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({
                            'error': error_message,
                            'limits': limits
                        }, status=403)
                    
                    messages.warning(request, error_message)
                    
                    if redirect_url:
                        return redirect(redirect_url)
                    else:
                        # Redirigir a la página de suscripciones
                        return redirect('suscripciones')
            
            return func(request, *args, **kwargs)
        return wrapper
    
    return decorator


def profile_complete_required(view_func=None, *, redirect_url=None, message=None):
    """
    Decorador que requiere que el perfil del usuario esté completo.
    
    Args:
        view_func: Función de vista a decorar
        redirect_url: URL de redirección si el perfil no está completo
        message: Mensaje personalizado de error
        
    Usage:
        @profile_complete_required
        def dashboard(request):
            # Requiere perfil completo
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Verificar perfil
            if not hasattr(request.user, 'userprofile'):
                messages.info(request, "Por favor completa tu perfil")
                return redirect('editar_perfil')
            
            perfil = request.user.userprofile
            
            # Verificar campos requeridos según tipo de cuenta
            campos_faltantes = []
            
            if perfil.tipo_cuenta == 'empresa':
                if not perfil.empresa:
                    campos_faltantes.append('nombre de empresa')
            else:
                if not request.user.first_name:
                    campos_faltantes.append('nombre')
                if not request.user.last_name:
                    campos_faltantes.append('apellido')
            
            if not perfil.telefono:
                campos_faltantes.append('teléfono')
            
            if not perfil.direccion:
                campos_faltantes.append('dirección')
            
            if campos_faltantes:
                error_message = message or f"Por favor completa los siguientes campos: {', '.join(campos_faltantes)}"
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'error': error_message,
                        'missing_fields': campos_faltantes
                    }, status=400)
                
                messages.info(request, error_message)
                return redirect(redirect_url or 'editar_perfil')
            
            return func(request, *args, **kwargs)
        return wrapper
    
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)


def ajax_required(view_func):
    """
    Decorador que requiere que la petición sea AJAX.
    
    Usage:
        @ajax_required
        def api_endpoint(request):
            # Solo peticiones AJAX
            pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Esta función requiere una petición AJAX'}, status=400)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def owner_required(model_class, pk_url_kwarg='pk', redirect_url=None):
    """
    Decorador que verifica que el usuario sea propietario del objeto.
    
    Args:
        model_class: Clase del modelo a verificar
        pk_url_kwarg: Nombre del parámetro URL que contiene el ID
        redirect_url: URL de redirección si no es propietario
        
    Usage:
        @owner_required(Producto, 'producto_id')
        def editar_producto(request, producto_id):
            # Solo el propietario puede editar
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Obtener ID del objeto
            object_id = kwargs.get(pk_url_kwarg)
            if not object_id:
                return HttpResponseForbidden("ID de objeto no proporcionado")
            
            try:
                # Verificar que el objeto existe y pertenece al usuario
                obj = model_class.objects.get(pk=object_id, usuario=request.user)
                
                # Agregar objeto al contexto de la vista
                kwargs['object'] = obj
                
            except model_class.DoesNotExist:
                error_message = "Objeto no encontrado o no tienes permisos para acceder"
                
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'error': error_message}, status=404)
                
                messages.error(request, error_message)
                
                if redirect_url:
                    return redirect(redirect_url)
                else:
                    return HttpResponseForbidden(error_message)
            
            return func(request, *args, **kwargs)
        return wrapper
    
    return decorator


def rate_limit(max_requests=10, window_minutes=1):
    """
    Decorador simple de rate limiting por usuario.
    
    Args:
        max_requests: Máximo número de peticiones
        window_minutes: Ventana de tiempo en minutos
        
    Usage:
        @rate_limit(max_requests=5, window_minutes=1)
        def api_endpoint(request):
            # Máximo 5 peticiones por minuto
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Implementación básica usando cache de Django
            from django.core.cache import cache
            from django.utils import timezone
            
            if request.user.is_authenticated:
                cache_key = f"rate_limit_{request.user.id}_{func.__name__}"
                
                # Obtener contador actual
                current_requests = cache.get(cache_key, 0)
                
                if current_requests >= max_requests:
                    if request.headers.get('Content-Type') == 'application/json':
                        return JsonResponse({
                            'error': 'Demasiadas peticiones. Intenta más tarde.'
                        }, status=429)
                    
                    messages.warning(request, 'Demasiadas peticiones. Intenta más tarde.')
                    return HttpResponseForbidden('Rate limit exceeded')
                
                # Incrementar contador
                cache.set(cache_key, current_requests + 1, window_minutes * 60)
            
            return func(request, *args, **kwargs)
        return wrapper
    
    return decorator


class PermissionMixin:
    """
    Mixin para vistas basadas en clases que agrega verificaciones de permisos.
    
    Usage:
        class MiVista(PermissionMixin, View):
            required_permissions = ['empresa']
            required_subscription = True
            
            def get(self, request):
                # Vista con permisos verificados
                pass
    """
    
    required_permissions = []  # ['empresa', 'admin']
    required_subscription = False
    required_plans = None  # ['premium', 'empresarial']
    check_profile_complete = False
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch para verificar permisos antes de procesar la vista."""
        
        # Verificar autenticación
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificar perfil completo si es requerido
        if self.check_profile_complete:
            if not hasattr(request.user, 'userprofile'):
                messages.info(request, "Por favor completa tu perfil")
                return redirect('editar_perfil')
        
        # Verificar permisos específicos
        if 'empresa' in self.required_permissions:
            if not hasattr(request.user, 'userprofile') or request.user.userprofile.tipo_cuenta != 'empresa':
                messages.error(request, "Acceso denegado: Solo para cuentas empresariales")
                return HttpResponseForbidden()
        
        if 'admin' in self.required_permissions:
            if not hasattr(request.user, 'userprofile') or not request.user.userprofile.is_admin:
                messages.error(request, "Acceso denegado: Permisos de administrador requeridos")
                return HttpResponseForbidden()
        
        # Verificar suscripción si es requerida
        if self.required_subscription:
            if not hasattr(request.user, 'userprofile') or not request.user.userprofile.suscripcion_activa:
                messages.warning(request, "Suscripción activa requerida")
                return redirect('suscripciones')
        
        # Verificar plan específico
        if self.required_plans:
            suscripcion = request.user.suscripciones.filter(activa=True).first()
            if not suscripcion or suscripcion.plan not in self.required_plans:
                messages.warning(request, f"Plan {' o '.join(self.required_plans)} requerido")
                return redirect('suscripciones')
        
        return super().dispatch(request, *args, **kwargs) 