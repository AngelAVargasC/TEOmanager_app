from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import RegistroUsuarioForm
from apps.accounts.models import PerfilUsuario
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from apps.productservice.models import Producto, Servicio, Pedido, MensajePedido
from apps.productservice.services import PedidoService
from apps.accounts.services import UserService
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.template.context_processors import request
from django.db.models import Q, Count, Prefetch
from decimal import Decimal
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Context processor que agrega el perfil de usuario autenticado a todos los templates.
def user_profile_context(request):
    """Context processor para agregar perfil de usuario y datos de carrito a todos los templates."""
    context = {}
    # Perfil de usuario
    if request.user.is_authenticated:
        try:
            context['user_profile'] = request.user.userprofile
        except PerfilUsuario.DoesNotExist:
            context['user_profile'] = None
    else:
        context['user_profile'] = None
    # Carrito desde sesión
    cart_session = request.session.get('cart', {})
    # Contador total de items
    total_count = sum(cart_session.values()) if isinstance(cart_session, dict) else 0
    context['cart_count'] = total_count
    # Preview de primeros 3 productos
    cart_preview = []
    if total_count and isinstance(cart_session, dict):
        for prod_id, qty in list(cart_session.items())[:3]:
            try:
                producto = Producto.objects.get(pk=int(prod_id))
                cart_preview.append({'producto': producto, 'cantidad': qty})
            except Exception:
                continue
    context['cart_preview'] = cart_preview
    return context

# Vista de registro de usuario. Muestra y procesa el formulario de registro.
def register(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Verificar que el perfil se creó correctamente
                if not hasattr(user, 'userprofile'):
                    logger.error(f"Usuario {user.username} creado pero sin perfil")
                    messages.error(request, 'Hubo un error al crear tu perfil. Por favor, contacta al soporte.')
                    return redirect('register')
                messages.success(request, '¡Tu cuenta ha sido creada exitosamente! Ahora puedes iniciar sesión.')
                return redirect('login')
            except Exception as e:
                logger.error(f"Error en registro: {str(e)}")
                messages.error(request, 'Hubo un error al crear tu cuenta. Por favor, intenta nuevamente.')
                return render(request, 'accounts/register.html', {'form': form})
    else:
        form = RegistroUsuarioForm()
    return render(request, 'accounts/register.html', {'form': form})

# Vista del dashboard principal del usuario autenticado. Muestra diferentes vistas según el tipo de cuenta.
@login_required(login_url='login')
def home(request):
    from django.db.models import Count, Q, Prefetch, Min, Max
    from django.core.cache import cache
    from django.core.paginator import Paginator
    from apps.productservice.models import Producto, Servicio, Pedido, ImagenProducto
    from decimal import Decimal
    
    # Obtener o crear perfil si no existe (por seguridad)
    try:
        perfil = PerfilUsuario.objects.select_related('usuario').get(usuario=request.user)
    except PerfilUsuario.DoesNotExist:
        # Si no tiene perfil, crear uno por defecto
        from django.utils import timezone
        from datetime import timedelta
        fecha_vencimiento = timezone.now() + timedelta(days=365)
        perfil = PerfilUsuario.objects.create(
            usuario=request.user,
            tipo_cuenta='usuario',
            empresa='',
            telefono='0000000000',
            direccion='Sin dirección',
            permisos='Usuario',
            estado_suscripcion='inactiva',
            fecha_vencimiento=fecha_vencimiento
        )
    
    # Mostrar vista según tipo de usuario
    if perfil.tipo_cuenta == 'empresa':
        # Dashboard optimizado para usuarios empresa
        # Solo cargar datos básicos sin imágenes para el dashboard
        productos = Producto.objects.filter(usuario=request.user).only(
            'id', 'nombre', 'precio', 'categoria', 'activo', 'fecha_creacion'
        )
        servicios = Servicio.objects.filter(usuario=request.user).only(
            'id', 'nombre', 'precio', 'categoria', 'activo', 'fecha_creacion'
        )
        pedidos = Pedido.objects.filter(usuario=request.user).only(
            'id', 'fecha_pedido', 'estado', 'total'
        ).order_by('-fecha_pedido')[:5]
        
        # Agregar conteos optimizados
        productos_stats = productos.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )
        servicios_stats = servicios.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True))
        )
        
        context = {
            'perfil': perfil,
            'productos': productos[:10],  # Solo mostrar 10 más recientes
            'servicios': servicios[:10],  # Solo mostrar 10 más recientes
            'pedidos': pedidos,
            'user': request.user,
            'productos_count': productos_stats['total'],
            'productos_activos': productos_stats['activos'],
            'servicios_count': servicios_stats['total'],
            'servicios_activos': servicios_stats['activos'],
            'pedidos_count': pedidos.count() if pedidos else 0,
        }
        return render(request, 'accounts/home.html', context)
    else:
        # Vista optimizada para usuarios consumidores - MARKETPLACE MODERNO
        search_query = request.GET.get('q', '')
        category_filter = request.GET.get('category', '')
        min_price = request.GET.get('min_price', '')
        max_price = request.GET.get('max_price', '')
        sort_by = request.GET.get('sort', 'name')  # name, price_low, price_high, newest
        view_mode = request.GET.get('view', 'grid')  # grid, list
        
        # Query base optimizada: productos activos de empresas
        productos_qs = Producto.objects.filter(
            usuario__userprofile__tipo_cuenta='empresa', 
            activo=True
        ).select_related('usuario').only(
            'id', 'nombre', 'precio', 'categoria', 'descripcion', 'stock', 
            'fecha_creacion', 'usuario__username'
        )
        
        # Aplicar búsqueda por nombre
        if search_query:
            productos_qs = productos_qs.filter(
                Q(nombre__icontains=search_query) | 
                Q(descripcion__icontains=search_query) |
                Q(categoria__icontains=search_query)
            )
        
        # Aplicar filtro por categoría - CORREGIDO PARA USAR BÚSQUEDA INSENSIBLE A MAYÚSCULAS
        if category_filter:
            productos_qs = productos_qs.filter(categoria__iexact=category_filter.strip())
        
        # Aplicar filtros de precio
        if min_price:
            try:
                productos_qs = productos_qs.filter(precio__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
                
        if max_price:
            try:
                productos_qs = productos_qs.filter(precio__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Aplicar ordenamiento
        if sort_by == 'price_low':
            productos_qs = productos_qs.order_by('precio')
        elif sort_by == 'price_high':
            productos_qs = productos_qs.order_by('-precio')
        elif sort_by == 'newest':
            productos_qs = productos_qs.order_by('-fecha_creacion')
        else:  # name (default)
            productos_qs = productos_qs.order_by('nombre')
        
        # Cargar imágenes optimizadas
        productos_qs = productos_qs.prefetch_related(
            Prefetch('imagenes', queryset=ImagenProducto.objects.order_by('-principal', 'fecha_subida'))
        )
        
        # === SERVICIOS SIMILARES ===
        servicios_qs = Servicio.objects.filter(
            usuario__userprofile__tipo_cuenta='empresa',
            activo=True
        ).select_related('usuario').only(
            'id', 'nombre', 'precio', 'categoria', 'descripcion', 'duracion',
            'fecha_creacion', 'usuario__username'
        )
        
        # Aplicar mismo filtro de búsqueda
        if search_query:
            servicios_qs = servicios_qs.filter(
                Q(nombre__icontains=search_query) | 
                Q(descripcion__icontains=search_query) |
                Q(categoria__icontains=search_query)
            )
        
        # Aplicar filtro por categoría - CORREGIDO PARA USAR BÚSQUEDA INSENSIBLE A MAYÚSCULAS
        if category_filter:
            servicios_qs = servicios_qs.filter(categoria__iexact=category_filter.strip())
        
        # Aplicar filtros de precio para servicios
        if min_price:
            try:
                servicios_qs = servicios_qs.filter(precio__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
                
        if max_price:
            try:
                servicios_qs = servicios_qs.filter(precio__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass
        
        # Aplicar ordenamiento a servicios
        if sort_by == 'price_low':
            servicios_qs = servicios_qs.order_by('precio')
        elif sort_by == 'price_high':
            servicios_qs = servicios_qs.order_by('-precio')
        elif sort_by == 'newest':
            servicios_qs = servicios_qs.order_by('-fecha_creacion')
        else:  # name (default)
            servicios_qs = servicios_qs.order_by('nombre')
        
        # Cargar imágenes de servicios
        from apps.productservice.models import ImagenServicio
        servicios_qs = servicios_qs.prefetch_related(
            Prefetch('imagenes', queryset=ImagenServicio.objects.order_by('-fecha_subida'))
        )
        
        # Paginación para productos
        paginator = Paginator(productos_qs, 12)  # 12 productos por página
        page_number = request.GET.get('page')
        productos = paginator.get_page(page_number)
        
        # Paginación para servicios
        servicios_paginator = Paginator(servicios_qs, 12)  # 12 servicios por página
        servicios_page_number = request.GET.get('services_page')
        servicios = servicios_paginator.get_page(servicios_page_number)
        
        # Categorías optimizadas con caché - CORREGIDO PARA ELIMINAR DUPLICADOS
        categories = cache.get('product_categories')
        category_counts = cache.get('category_counts')
        
        if categories is None or category_counts is None:
            # Obtener categorías y limpiarlas
            raw_categories = Producto.objects.filter(
                usuario__userprofile__tipo_cuenta='empresa',
                activo=True
            ).values_list('categoria', flat=True).distinct()
            
            # Limpiar categorías: eliminar espacios, normalizar caso y eliminar duplicados
            cleaned_categories = {}
            for cat in raw_categories:
                if cat:  # Evitar valores None o vacíos
                    cleaned_cat = cat.strip().title()  # Limpiar espacios y capitalizar
                    if cleaned_cat not in cleaned_categories:
                        cleaned_categories[cleaned_cat] = 0
            
            # Calcular conteos para categorías limpias
            category_counts = {}
            for clean_cat in cleaned_categories.keys():
                # Contar productos que tengan esta categoría (ignorando caso y espacios)
                count = Producto.objects.filter(
                    usuario__userprofile__tipo_cuenta='empresa',
                    activo=True,
                    categoria__iexact=clean_cat.strip()
                ).count()
                if count > 0:  # Solo incluir categorías que tienen productos
                    category_counts[clean_cat] = count
            
            # Solo mantener categorías que tienen productos
            categories = list(category_counts.keys())
            
            # Guardar en caché
            cache.set('product_categories', categories, 300)  # 5 minutos de caché
            cache.set('category_counts', category_counts, 300)
        
        # Rango de precios para el filtro
        price_range = Producto.objects.filter(
            usuario__userprofile__tipo_cuenta='empresa',
            activo=True
        ).aggregate(
            min_price=Min('precio'),
            max_price=Max('precio')
        )
        
        # Estadísticas para el hero header
        total_companies = User.objects.filter(userprofile__tipo_cuenta='empresa').count()
        total_products_count = Producto.objects.filter(
            usuario__userprofile__tipo_cuenta='empresa',
            activo=True
        ).count()
        total_services_count = Servicio.objects.filter(
            usuario__userprofile__tipo_cuenta='empresa',
            activo=True
        ).count()
        
        context = {
            'perfil': perfil,
            'productos': productos,
            'servicios': servicios,
            'user': request.user,
            'search_query': search_query,
            'category_filter': category_filter,
            'categories': categories,
            'category_counts': category_counts,
            'min_price': min_price,
            'max_price': max_price,
            'sort_by': sort_by,
            'view_mode': view_mode,
            'price_range': price_range,
            'total_products': total_products_count,
            'total_services': total_services_count,
            'total_companies': total_companies,
        }
        return render(request, 'accounts/home_consumer.html', context)

# Vista para cerrar sesión del usuario.
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('login')

# Vista de perfil del usuario autenticado. Permite ver y editar datos personales.
@login_required(login_url='login')
def perfil(request):
    perfil = PerfilUsuario.objects.get(usuario=request.user)
    
    if request.method == 'POST':
        from .forms import EditarPerfilForm
        form = EditarPerfilForm(request.POST, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
            return render(request, 'accounts/editar_perfil.html', {
                'form': form,
                'perfil': perfil
            })
    
    return render(request, 'accounts/perfil.html', {'perfil': perfil})

# Vista para editar el perfil del usuario
@login_required(login_url='login')
def editar_perfil(request):
    perfil = PerfilUsuario.objects.get(usuario=request.user)
    
    if request.method == 'POST':
        from .forms import EditarPerfilForm
        form = EditarPerfilForm(request.POST, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        from .forms import EditarPerfilForm
        form = EditarPerfilForm(instance=perfil, user=request.user)
    
    return render(request, 'accounts/editar_perfil.html', {
        'form': form,
        'perfil': perfil
    })

# Vista de login personalizada. Muestra y procesa el formulario de autenticación.
@csrf_protect
def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, '¡Has iniciado sesión correctamente!')
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

# Vista landing pública (página de inicio para usuarios no autenticados).
def landing(request):
    return render(request, 'landing.html')

# Vista del dashboard de administración. Solo accesible para administradores. Muestra métricas globales.
@login_required(login_url='login')
def admin_dashboard(request):
    # Verificar permisos admin compatible con ambos modelos
    is_admin = False
    if request.user.is_superuser:
        is_admin = True
    elif hasattr(request.user, 'userprofile') and request.user.userprofile.permisos == 'Administrador':
        is_admin = True
    elif hasattr(request.user, 'userprofile'):
        try:
            perfil = PerfilUsuario.objects.get(usuario=request.user)
            if perfil.permisos == 'Administrador':
                is_admin = True
        except PerfilUsuario.DoesNotExist:
            pass
    
    if not is_admin:
        messages.error(request, 'No tienes permisos para acceder al panel de administración.')
        return redirect('home')
    
    from apps.productservice.models import Producto, Servicio, Pedido, ImagenProducto
    from django.db.models import Count, Q
    
    # Optimizar métricas con una sola consulta usando agregaciones
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        active_users=Count('id', filter=Q(is_active=True)),
        total_companies=Count('id', filter=Q(userprofile__tipo_cuenta='empresa')),
        total_admins=Count('id', filter=Q(userprofile__permisos='Administrador'))
    )
    
    # Métricas de productos y servicios (consultas separadas pero optimizadas)
    total_products = Producto.objects.count()
    total_services = Servicio.objects.count() 
    total_orders = Pedido.objects.count()
    
    # Extraer valores de user_stats
    total_users = user_stats['total_users']
    active_users = user_stats['active_users']
    total_companies = user_stats['total_companies']
    total_admins = user_stats['total_admins']
    inactive_users = total_users - active_users
    
    # Actividad reciente simulada (puedes reemplazar con datos reales)
    recent_activities = [
        {
            'user': 'Sistema',
            'action': 'Usuario registrado',
            'target': 'Nuevo usuario',
            'time': 'Hace 2 horas',
            'icon': 'fas fa-user-plus',
            'type': 'success'
        },
        {
            'user': 'Admin',
            'action': 'Producto aprobado',
            'target': 'ID #123',
            'time': 'Hace 3 horas',
            'icon': 'fas fa-check-circle',
            'type': 'success'
        },
        {
            'user': 'Sistema',
            'action': 'Pedido procesado',
            'target': 'Orden #456',
            'time': 'Hace 4 horas',
            'icon': 'fas fa-shopping-cart',
            'type': 'info'
        },
        {
            'user': 'Admin',
            'action': 'Usuario desactivado',
            'target': 'ID #789',
            'time': 'Hace 5 horas',
            'icon': 'fas fa-user-times',
            'type': 'warning'
        }
    ]
    
    return render(request, 'accounts/admin/dashboard.html', {
        'total_users': total_users,
        'total_companies': total_companies,
        'total_admins': total_admins,
        'total_products': total_products,
        'total_services': total_services,
        'total_orders': total_orders,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'recent_activities': recent_activities,
    })

# Vista para gestionar usuarios (listar, buscar, paginar). Solo para administradores.
@login_required(login_url='login')
def manage_users(request):
    if request.user.userprofile.permisos != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    users = User.objects.select_related('userprofile').all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(userprofile__empresa__icontains=search_query)
        )
    
    # Ordenar usuarios para evitar warning de Paginator
    users = users.order_by('-date_joined', 'username')
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    return render(request, 'accounts/admin/manage_users.html', {
        'users': users
    })

# Vista para eliminar un usuario completamente. Solo para administradores.
@login_required(login_url='login')
@require_POST
def delete_user(request, user_id):
    """
    Elimina completamente un usuario y todos sus datos relacionados.
    Solo accesible para administradores y mediante POST.
    """
    if request.user.userprofile.permisos != 'Administrador':
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    # Prevenir auto-eliminación
    if request.user.id == user_id:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('manage_users')
    
    try:
        user_to_delete = get_object_or_404(User, id=user_id)
        
        # Prevenir eliminación de superusuarios
        if user_to_delete.is_superuser:
            messages.error(request, 'No se pueden eliminar superusuarios desde esta interfaz.')
            return redirect('manage_users')
        
        username = user_to_delete.username
        
        # Eliminar usuario y todos sus datos
        deleted_summary = UserService.delete_user_completely(user_to_delete)
        
        # Mensaje de éxito con resumen
        summary_text = f"Usuario '{username}' eliminado completamente. "
        summary_text += f"Eliminados: {deleted_summary['productos']} productos, "
        summary_text += f"{deleted_summary['servicios']} servicios, "
        summary_text += f"{deleted_summary['pedidos']} pedidos, "
        summary_text += f"{deleted_summary['landing_pages']} landing pages, "
        summary_text += f"{deleted_summary['archivos_eliminados']} archivos."
        
        messages.success(request, summary_text)
        logger.info(f"Usuario {username} eliminado por administrador {request.user.username}")
        
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Error eliminando usuario {user_id}: {str(e)}")
        messages.error(request, f'Error al eliminar el usuario: {str(e)}')
    
    return redirect('manage_users')

# Vista de detalle y edición de un usuario específico. Solo para administradores.
@login_required(login_url='login')
def user_detail(request, user_id):
    if request.user.userprofile.permisos != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    user_detail = get_object_or_404(User.objects.select_related('userprofile'), id=user_id)
    
    if request.method == 'POST':
        user_detail.username = request.POST.get('username')
        user_detail.email = request.POST.get('email')
        user_detail.is_active = request.POST.get('is_active') == 'on'
        user_detail.save()
        
        user_detail.userprofile.empresa = request.POST.get('empresa')
        user_detail.userprofile.telefono = request.POST.get('telefono')
        user_detail.userprofile.direccion = request.POST.get('direccion')
        user_detail.userprofile.permisos = request.POST.get('permisos', 'Usuario')
        user_detail.userprofile.save()
        
        messages.success(request, 'Usuario actualizado correctamente.')
        return redirect('manage_users')
    
    return render(request, 'accounts/admin/user_detail.html', {
        'user_detail': user_detail
    })

# Vista para ver los productos de un usuario específico. Solo para administradores.
@login_required(login_url='login')
def admin_products(request, user_id):
    if request.user.userprofile.permisos != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    user_detail = get_object_or_404(User, id=user_id)
    products = Producto.objects.filter(usuario=user_detail).prefetch_related('imagenes')
    
    return render(request, 'accounts/admin/user_products.html', {
        'user_detail': user_detail,
        'products': products
    })

# Vista para ver los servicios de un usuario específico. Solo para administradores.
@login_required(login_url='login')
def admin_services(request, user_id):
    if request.user.userprofile.permisos != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    user_detail = get_object_or_404(User, id=user_id)
    services = Servicio.objects.filter(usuario=user_detail).prefetch_related('imagenes')
    
    return render(request, 'accounts/admin/user_services.html', {
        'user_detail': user_detail,
        'services': services
    })

# Vista para ver los pedidos de un usuario específico, con filtros y paginación. Solo para administradores.
@login_required(login_url='login')
def admin_orders(request, user_id):
    if not request.user.userprofile.is_admin:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    user_detail = get_object_or_404(User, id=user_id)
    orders = Pedido.objects.filter(usuario=user_detail)
    
    # Filtros
    status = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        orders = orders.filter(estado=status)
    if date_from:
        orders = orders.filter(fecha_creacion__gte=date_from)
    if date_to:
        orders = orders.filter(fecha_creacion__lte=date_to)
    
    paginator = Paginator(orders, 10)
    page = request.GET.get('page')
    orders = paginator.get_page(page)
    
    return render(request, 'accounts/admin/user_orders.html', {
        'user_detail': user_detail,
        'orders': orders
    })

# Vista para activar/desactivar usuarios vía AJAX. Solo para administradores.
@login_required(login_url='login')
@require_POST
def toggle_user_status(request):
    if not request.user.userprofile.is_admin:
        return JsonResponse({'error': 'No tienes permisos para realizar esta acción.'}, status=403)
    
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    return JsonResponse({
        'is_active': user.is_active
    })

@login_required(login_url='login')
def cart(request):
    """Muestra el carrito de compras y permite checkout."""
    cart_session = request.session.get('cart', {})
    productos_carrito = []
    total = Decimal('0')
    empresas_en_carrito = {}  # Cambiar a dict para almacenar más información
    
    # Construir vista del carrito y obtener empresas involucradas
    for prod_id, qty in cart_session.items():
        try:
            producto = get_object_or_404(Producto, pk=int(prod_id), activo=True)
            subtotal = producto.precio * qty
            total += subtotal
            
            # Obtener información completa de la empresa
            empresa_username = producto.usuario.username
            try:
                empresa_perfil = producto.usuario.userprofile
                empresa_nombre = empresa_perfil.empresa if empresa_perfil.empresa else empresa_username
            except:
                empresa_nombre = empresa_username
            
            empresas_en_carrito[empresa_username] = {
                'nombre': empresa_nombre,
                'username': empresa_username,
                'productos_count': empresas_en_carrito.get(empresa_username, {}).get('productos_count', 0) + qty
            }
            
            productos_carrito.append({
                'producto': producto,
                'cantidad': qty,
                'subtotal': subtotal,
            })
        except (Producto.DoesNotExist, ValueError):
            # Eliminar productos inválidos del carrito
            continue
    
    # Checkout real
    if request.method == 'POST':
        try:
            if not cart_session:
                messages.error(request, 'Tu carrito está vacío.')
                return redirect('cart')
            
            # Capturar comentarios específicos por empresa
            from django.utils.text import slugify
            notas_por_empresa = {}
            for empresa_username, empresa_data in empresas_en_carrito.items():
                # Usar el username para generar el slug (como en el template)
                empresa_slug = slugify(empresa_username)
                notas_empresa = request.POST.get(f'notas_{empresa_slug}', '').strip()
                if notas_empresa:
                    notas_por_empresa[empresa_username] = notas_empresa
            
            # Crear pedidos agrupados por empresa con comentarios específicos
            pedidos_creados = PedidoService.create_pedidos_from_cart(
                user=request.user,
                cart_session=cart_session,
                notas_por_empresa=notas_por_empresa
            )
            
            # Limpiar carrito después de crear pedidos exitosamente
            request.session['cart'] = {}
            
            # Mensaje de éxito personalizado
            if len(pedidos_creados) == 1:
                messages.success(request, f'¡Pedido #{pedidos_creados[0].id} creado exitosamente!')
            else:
                pedidos_ids = ', '.join([f'#{p.id}' for p in pedidos_creados])
                messages.success(request, f'¡Se crearon {len(pedidos_creados)} pedidos: {pedidos_ids}!')
            
            return redirect('mis_pedidos')  # Redirigir a vista de pedidos del usuario
            
        except ValueError as e:
            messages.error(request, f'Error en el checkout: {str(e)}')
        except Exception as e:
            messages.error(request, 'Ocurrió un error inesperado. Por favor, inténtalo de nuevo.')
            
    return render(request, 'accounts/cart.html', {
        'productos_carrito': productos_carrito,
        'total': total,
        'empresas_count': len(empresas_en_carrito),
        'empresas_data': empresas_en_carrito,  # Pasar toda la información de empresas
    })

@login_required(login_url='login')
def add_to_cart(request, product_id):
    """Agrega un producto al carrito en sesión."""
    try:
        producto = get_object_or_404(Producto, pk=product_id, activo=True)
        
        # Verificar stock
        if producto.stock <= 0:
            message = f'El producto "{producto.nombre}" no tiene stock disponible.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message})
            messages.error(request, message)
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        cart_session = request.session.get('cart', {})
        current_qty = cart_session.get(str(product_id), 0)
        
        # Verificar si no excede el stock
        if current_qty >= producto.stock:
            message = f'Ya tienes el máximo disponible de "{producto.nombre}" en tu carrito.'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': message})
            messages.warning(request, message)
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        
        cart_session[str(product_id)] = current_qty + 1
        request.session['cart'] = cart_session
        
        # Calcular totales actualizados
        total_items = sum(cart_session.values())
        cart_total = Decimal('0')
        for prod_id, qty in cart_session.items():
            try:
                prod = Producto.objects.get(pk=int(prod_id), activo=True)
                cart_total += prod.precio * qty
            except (Producto.DoesNotExist, ValueError):
                continue
        
        success_message = f'✅ "{producto.nombre}" agregado al carrito. Tienes {total_items} productos.'
        
        # Respuesta AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': success_message,
                'cart_count': total_items,
                'cart_total': str(cart_total)
            })
        
        # Respuesta normal
        messages.success(request, success_message)
        
    except Exception as e:
        error_message = 'Error al agregar el producto al carrito.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        messages.error(request, error_message)
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='login')
def remove_from_cart(request, product_id):
    """Elimina un producto del carrito."""
    try:
        cart_session = request.session.get('cart', {})
        
        if str(product_id) in cart_session:
            # Obtener nombre del producto antes de eliminarlo
            try:
                producto = Producto.objects.get(pk=product_id)
                producto_nombre = producto.nombre
            except Producto.DoesNotExist:
                producto_nombre = "Producto"
            
            del cart_session[str(product_id)]
            request.session['cart'] = cart_session
            
            total_items = sum(cart_session.values())
            if total_items > 0:
                messages.success(request, f'🗑️ "{producto_nombre}" eliminado del carrito. Te quedan {total_items} productos.')
            else:
                messages.success(request, f'🗑️ "{producto_nombre}" eliminado. Tu carrito está vacío.')
        else:
            messages.warning(request, 'El producto no estaba en tu carrito.')
            
    except Exception as e:
        messages.error(request, 'Error al eliminar el producto del carrito.')
    
    return redirect('cart')

@login_required(login_url='login')
def cart_preview(request):
    """
    Vista AJAX que devuelve la vista previa del carrito en formato JSON.
    Retorna los primeros 3 productos del carrito para mostrar en el dropdown.
    """
    try:
        cart_session = request.session.get('cart', {})
        cart_items = []
        cart_count = 0
        cart_total = Decimal('0')
        

        
        if cart_session:
            cart_count = sum(cart_session.values())
            
            # Obtener los primeros 3 productos para la vista previa
            for i, (prod_id, qty) in enumerate(cart_session.items()):
                if i >= 3:  # Solo mostrar los primeros 3
                    break
                    
                try:
                    producto = Producto.objects.prefetch_related('imagenes').get(pk=int(prod_id), activo=True)
                    
                    # Usar el método imagen_principal del modelo
                    imagen_url = producto.imagen_principal
                    
                    cart_items.append({
                        'id': producto.pk,
                        'nombre': producto.nombre,
                        'precio': str(producto.precio),
                        'cantidad': qty,
                        'imagen_principal': imagen_url,
                        'subtotal': str(producto.precio * qty)
                    })
                    
                except (Producto.DoesNotExist, ValueError) as e:
                    # Remover productos que ya no existen del carrito
                    if str(prod_id) in cart_session:
                        del cart_session[str(prod_id)]
                        request.session['cart'] = cart_session
                        cart_count = sum(cart_session.values())
            
            # Calcular total del carrito
            for prod_id, qty in cart_session.items():
                try:
                    producto = Producto.objects.get(pk=int(prod_id), activo=True)
                    cart_total += producto.precio * qty
                except (Producto.DoesNotExist, ValueError):
                    continue
        
        response_data = {
            'success': True,
            'cart_items': cart_items,
            'cart_count': cart_count,
            'cart_total': str(cart_total)
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener vista previa del carrito: {str(e)}'
        })

@login_required(login_url='login')
def buy_now(request, product_id):
    """Agrega el producto y redirige al carrito para proceder al pago."""
    cart_session = request.session.get('cart', {})
    cart_session[str(product_id)] = cart_session.get(str(product_id), 0) + 1
    request.session['cart'] = cart_session
    return redirect('cart')

# =========================== VISTAS DE PEDIDOS ===========================

@login_required(login_url='login')
def mis_pedidos(request):
    """Vista para que los consumidores vean sus pedidos realizados."""
    # Filtros disponibles
    estado_filter = request.GET.get('estado', '')
    search_query = request.GET.get('q', '')
    
    # Construir filtros
    filters = {}
    if estado_filter:
        filters['estado'] = estado_filter
    
    # Obtener pedidos del usuario con optimización de consultas
    pedidos = PedidoService.get_pedidos_with_details(request.user, filters)
    
    # Aplicar búsqueda por ID de pedido o empresa
    if search_query:
        pedidos = pedidos.filter(
            Q(id__icontains=search_query) |
            Q(empresa__username__icontains=search_query) |
            Q(empresa__userprofile__empresa__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(pedidos, 10)  # 10 pedidos por página
    page_number = request.GET.get('page')
    pedidos_page = paginator.get_page(page_number)
    
    # Estadísticas del usuario
    stats = PedidoService.get_pedido_stats(request.user)
    
    # Obtener conteo de mensajes no leídos por pedido
    pedidos_ids = [p.id for p in pedidos_page]
    mensajes_no_leidos = MensajePedido.objects.filter(
        pedido__in=pedidos_ids,
        leido=False
    ).exclude(remitente=request.user).values('pedido').annotate(
        conteo=Count('id')
    )
    mensajes_dict = {item['pedido']: item['conteo'] for item in mensajes_no_leidos}
    
    # Estados disponibles para el filtro
    estados_choices = Pedido.ESTADO_PEDIDO
    
    context = {
        'pedidos': pedidos_page,
        'stats': stats,
        'estados_choices': estados_choices,
        'estado_filter': estado_filter,
        'search_query': search_query,
        'mensajes_no_leidos': mensajes_dict,
    }
    
    return render(request, 'accounts/mis_pedidos.html', context)

@login_required(login_url='login')
def pedido_detail(request, pedido_id):
    """Vista detallada de un pedido específico para el consumidor."""
    pedido = get_object_or_404(
        Pedido.objects.select_related('empresa__userprofile').prefetch_related(
            'detalles__producto__imagenes',
            'detalles__servicio__imagenes'
        ),
        id=pedido_id,
        usuario=request.user  # Solo el usuario propietario puede ver el pedido
    )
    
    context = {
        'pedido': pedido,
        'user': request.user,
    }
    
    return render(request, 'accounts/pedido_detail.html', context)

@login_required(login_url='login')
def pedidos_empresa(request):
    """Vista para que las empresas vean los pedidos que han recibido."""
    # Verificar que el usuario sea empresa
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    if perfil.tipo_cuenta != 'empresa':
        messages.error(request, 'Solo las empresas pueden acceder a esta sección.')
        return redirect('home')
    
    # Filtros disponibles
    estado_filter = request.GET.get('estado', '')
    cliente_filter = request.GET.get('cliente', '')
    
    # Construir filtros
    filters = {}
    if estado_filter:
        filters['estado'] = estado_filter
    if cliente_filter:
        filters['cliente'] = cliente_filter
    
    # Obtener pedidos de la empresa con optimización de consultas
    pedidos = PedidoService.get_pedidos_empresa_with_details(request.user, filters)
    
    # Paginación
    paginator = Paginator(pedidos, 10)  # 10 pedidos por página
    page_number = request.GET.get('page')
    pedidos_page = paginator.get_page(page_number)
    
    # Estadísticas de la empresa
    stats = PedidoService.get_empresa_stats(request.user)
    
    # Obtener conteo de mensajes no leídos por pedido
    pedidos_ids = [p.id for p in pedidos_page]
    mensajes_no_leidos = MensajePedido.objects.filter(
        pedido__in=pedidos_ids,
        leido=False
    ).exclude(remitente=request.user).values('pedido').annotate(
        conteo=Count('id')
    )
    mensajes_dict = {item['pedido']: item['conteo'] for item in mensajes_no_leidos}
    
    # Estados disponibles para el filtro
    estados_choices = Pedido.ESTADO_PEDIDO
    
    context = {
        'pedidos': pedidos_page,
        'stats': stats,
        'estados_choices': estados_choices,
        'estado_filter': estado_filter,
        'cliente_filter': cliente_filter,
        'mensajes_no_leidos': mensajes_dict,
    }
    
    return render(request, 'accounts/pedidos_empresa.html', context)

@login_required(login_url='login')
def pedido_empresa_detail(request, pedido_id):
    """Vista detallada de un pedido específico para la empresa."""
    # Verificar que el usuario sea empresa
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)
    if perfil.tipo_cuenta != 'empresa':
        messages.error(request, 'Solo las empresas pueden acceder a esta sección.')
        return redirect('home')
    
    pedido = get_object_or_404(
        Pedido.objects.select_related('usuario__userprofile').prefetch_related(
            'detalles__producto__imagenes',
            'detalles__servicio__imagenes'
        ),
        id=pedido_id,
        empresa=request.user  # Solo la empresa destinataria puede ver el pedido
    )
    
    context = {
        'pedido': pedido,
        'user': request.user,
    }
    
    return render(request, 'accounts/pedido_empresa_detail.html', context)

@login_required(login_url='login')
@require_POST
def update_pedido_status(request, pedido_id):
    """Actualiza el estado de un pedido (solo para empresas) vía AJAX."""
    try:
        # Verificar que el usuario sea empresa
        perfil = PerfilUsuario.objects.get(usuario=request.user)
        if perfil.tipo_cuenta != 'empresa':
            return JsonResponse({
                'success': False,
                'message': 'Solo las empresas pueden actualizar pedidos.'
            }, status=403)
        
        nuevo_estado = request.POST.get('nuevo_estado')
        if not nuevo_estado:
            return JsonResponse({
                'success': False,
                'message': 'Estado requerido.'
            }, status=400)
        
        # Actualizar estado usando el servicio
        pedido = PedidoService.update_pedido_status_by_empresa(
            pedido_id=pedido_id,
            empresa_user=request.user,
            nuevo_estado=nuevo_estado
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Estado actualizado a {pedido.get_estado_display()}',
            'nuevo_estado': nuevo_estado,
            'estado_display': pedido.get_estado_display()
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Error interno del servidor.'
        }, status=500)

# Vista de marketplace público para consumidores
def marketplace(request):
    # Solo consumidores pueden acceder
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'userprofile', None)
        if perfil and perfil.tipo_cuenta == 'empresa':
            return redirect('home')
    # Listar todas las empresas registradas
    empresas = PerfilUsuario.objects.filter(tipo_cuenta='empresa').select_related('usuario')
    return render(request, 'accounts/marketplace.html', {'empresas': empresas})

# Vista pública de empresa: landing o catálogo
# IMPORTANTE: Esta vista mantiene el sidebar del usuario logueado, no de la empresa visitada
def public_company_page(request, user_id):
    """
    Vista pública de empresa que muestra landing page si existe, 
    o catálogo de productos/servicios si no hay landing page.
    """
    from django.contrib.auth.models import User
    from apps.webpages.models import LandingPage
    
    user_obj = get_object_or_404(User, id=user_id)
    company_perfil = get_object_or_404(PerfilUsuario, usuario=user_obj)
    if company_perfil.tipo_cuenta != 'empresa':
        raise Http404('Empresa no encontrada')
    
    # CORREGIDO: Obtener perfil del usuario actual logueado para el sidebar
    user_perfil = None
    if request.user.is_authenticated:
        try:
            user_perfil = PerfilUsuario.objects.get(usuario=request.user)
        except PerfilUsuario.DoesNotExist:
            user_perfil = None
    
    landing = LandingPage.objects.filter(usuario=user_obj).first()
    products = Producto.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    services = Servicio.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    
    base_context = {
        'perfil': user_perfil,  # Perfil del usuario logueado para el sidebar
        'user_profile': user_perfil,  # Alias adicional
        'company_perfil': company_perfil,  # Perfil de la empresa visitada
        'products': products,
        'services': services,
    }
    
    if landing:
        # Usar la vista pública de webpages para mostrar landing page
        from apps.webpages.views import public_landing_page
        return public_landing_page(request, user_id)
    # Si no hay landing, mostrar catálogo de productos y servicios
    return render(request, 'accounts/company_catalog.html', base_context)

# Vista de catálogo completo de empresa (plantilla premium)
# IMPORTANTE: Esta vista mantiene el sidebar del usuario logueado, no de la empresa visitada
def company_full_catalog(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    company_perfil = get_object_or_404(PerfilUsuario, usuario=user_obj)
    if company_perfil.tipo_cuenta != 'empresa':
        raise Http404('Empresa no encontrada')
    
    # CORREGIDO: Obtener perfil del usuario actual logueado para el sidebar
    user_perfil = None
    if request.user.is_authenticated:
        try:
            user_perfil = PerfilUsuario.objects.get(usuario=request.user)
        except PerfilUsuario.DoesNotExist:
            user_perfil = None
    
    products = Producto.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    services = Servicio.objects.filter(usuario=user_obj, activo=True).prefetch_related('imagenes')
    
    return render(request, 'accounts/company_full_catalog.html', {
        'perfil': user_perfil,  # Perfil del usuario logueado para el sidebar
        'user_profile': user_perfil,  # Alias adicional
        'company_perfil': company_perfil,  # Perfil de la empresa visitada
        'products': products,
        'services': services,
    })
