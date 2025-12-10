"""
Vistas para la gestión de landing pages y plantillas web.

Este módulo contiene las vistas relacionadas con:
- Creación y edición de landing pages
- Visualización de landing pages
- Gestión de plantillas

Diseñado para escalabilidad: Las vistas están separadas en su propio módulo
para facilitar mantenimiento y futura migración a microservicios.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_http_methods
from apps.accounts.models import PerfilUsuario
from apps.productservice.models import Producto, Servicio
from .models import LandingPage
from .forms import LandingPageForm


@login_required(login_url='login')
def create_landing_page(request):
    """
    Vista para crear o editar la landing page de empresas.
    
    Solo empresas pueden acceder a esta funcionalidad.
    """
    # Solo empresas pueden acceder
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    if perfil.tipo_cuenta != 'empresa':
        messages.error(request, 'No tienes permiso para crear o editar la página de empresa.')
        return redirect('home')

    # Obtener landing existente o None
    landing = LandingPage.objects.filter(usuario=request.user).first()

    # Obtener algunos productos y servicios para bloques predefinidos
    products = Producto.objects.filter(usuario=request.user, activo=True)[:5]
    services = Servicio.objects.filter(usuario=request.user, activo=True)[:5]

    # Lista de categorías únicas para el slider (hasta 6)
    all_cats = (
        Producto.objects
        .filter(usuario=request.user, activo=True)
        .values_list('categoria', flat=True)
        .distinct()[:6]
    )
    categories = list(all_cats)

    if request.method == 'POST':
        # Si es una petición AJAX para actualizar solo la plantilla
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'plantilla' in request.POST:
            if landing:
                landing.plantilla = request.POST.get('plantilla')
                landing.save()
                # Devolver HTML de la vista previa actualizada
                products = Producto.objects.filter(usuario=request.user, activo=True).prefetch_related('imagenes')[:5]
                services = Servicio.objects.filter(usuario=request.user, activo=True).prefetch_related('imagenes')[:5]
                # Obtener categorías para plantillas que las necesiten
                all_cats = (
                    Producto.objects
                    .filter(usuario=request.user, activo=True)
                    .values_list('categoria', flat=True)
                    .distinct()[:6]
                )
                categories = list(all_cats)
                # Obtener perfil para el contexto
                perfil = request.user.userprofile if hasattr(request.user, 'userprofile') else None
                from django.template.loader import render_to_string
                preview_html = render_to_string('webpages/preview_snippet.html', {
                    'landing': landing,
                    'products': products,
                    'services': services,
                    'categories': categories,
                    'perfil': perfil,
                    'user_profile': perfil,
                }, request=request)
                return JsonResponse({'success': True, 'preview_html': preview_html})
            else:
                return JsonResponse({'success': False, 'error': 'No hay landing page guardada'})
        
        # Petición POST normal (guardar formulario completo)
        form = LandingPageForm(request.POST, request.FILES, instance=landing)
        if form.is_valid():
            new_lp = form.save(commit=False)
            new_lp.usuario = request.user
            new_lp.save()
            messages.success(request, '¡Tu página ha sido guardada exitosamente!')
            # Si es AJAX, devolver JSON en lugar de redirigir
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect': False})
            # Redirigir a la vista de la landing page en lugar de home
            return redirect('webpages:landingpage_view')
    else:
        form = LandingPageForm(instance=landing)

    # Preparar datos para la vista previa
    preview_landing = landing if landing else None
    if preview_landing:
        # Si hay landing, usar sus datos para preview
        preview_products = products
        preview_services = services
    else:
        # Si no hay landing, usar datos vacíos para preview
        preview_products = []
        preview_services = []

    return render(request, 'webpages/landingpage_form.html', {
        'form': form,
        'landing': preview_landing,
        'products': preview_products,
        'services': preview_services,
        'categories': categories,
        'preview_products': preview_products,
        'preview_services': preview_services,
    })


@login_required(login_url='login')
def landingpage_view(request):
    """
    Vista para mostrar la landing page en modo presentación completa.
    
    Solo empresas pueden ver sus propias landing pages.
    """
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    # Sólo empresas tienen landing page
    if perfil.tipo_cuenta != 'empresa':
        raise Http404('No tienes una página disponible')
    
    # Obtener landing page
    landing = LandingPage.objects.filter(usuario=request.user).first()
    if not landing:
        messages.info(request, 'Primero debes crear tu landing page.')
        return redirect('webpages:create_landing_page')
    
    # Datos de productos y servicios si la plantilla los necesita
    products = Producto.objects.filter(usuario=request.user, activo=True).prefetch_related('imagenes')
    services = Servicio.objects.filter(usuario=request.user, activo=True).prefetch_related('imagenes')
    
    # Obtener perfil para el contexto
    perfil = request.user.userprofile if hasattr(request.user, 'userprofile') else None
    
    return render(request, 'webpages/landingpage_view.html', {
        'landing': landing,
        'products': products,
        'services': services,
        'perfil': perfil,
        'user_profile': perfil,
    })


def public_landing_page(request, user_id):
    """
    Vista pública de landing page de una empresa.
    
    Permite ver la landing page de cualquier empresa sin necesidad de login.
    """
    from django.contrib.auth.models import User
    
    user_obj = get_object_or_404(User, id=user_id)
    company_perfil = get_object_or_404(PerfilUsuario, usuario=user_obj)
    
    if company_perfil.tipo_cuenta != 'empresa':
        raise Http404('Empresa no encontrada')
    
    # Obtener perfil del usuario actual logueado para el sidebar (si existe)
    user_perfil = None
    if request.user.is_authenticated:
        try:
            user_perfil = PerfilUsuario.objects.get(usuario=request.user)
        except PerfilUsuario.DoesNotExist:
            user_perfil = None
    
    landing = LandingPage.objects.filter(usuario=user_obj).first()
    
    if not landing:
        raise Http404('Landing page no encontrada')
    
    products = Producto.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    services = Servicio.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    
    return render(request, 'webpages/landingpage_view.html', {
        'perfil': user_perfil,  # Perfil del usuario logueado para el sidebar
        'user_profile': user_perfil,  # Alias adicional
        'company_perfil': company_perfil,  # Perfil de la empresa visitada
        'landing': landing,
        'products': products,
        'services': services,
    })

