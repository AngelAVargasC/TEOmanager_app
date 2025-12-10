from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.productservice.models import Producto, Servicio, Pedido, ImagenProducto, ImagenServicio, MensajePedido
from apps.productservice.forms import ProductoForm, ServicioForm, PoliticasProductoForm, PoliticasServicioForm
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from apps.accounts.models import PerfilUsuario
from datetime import datetime

# Decorador para verificar que el usuario sea una empresa
def empresa_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificar si el usuario tiene perfil y es empresa
        if hasattr(request.user, 'userprofile') and request.user.userprofile.tipo_cuenta == 'empresa':
            return view_func(request, *args, **kwargs)
        else:
            # Si no es empresa, redirigir al marketplace
            messages.error(request, 'Esta sección está disponible solo para usuarios empresa.')
            return redirect('marketplace')
    return wrapper

# Create your views here.

# Vista que muestra la lista de productos del usuario autenticado.
@login_required(login_url='login')
@empresa_required
def productos(request):
    productos = Producto.objects.filter(usuario=request.user).prefetch_related('imagenes')
    return render(request, 'productservice/productos.html', {'productos': productos})

# Vista para crear un nuevo producto. Muestra y procesa el formulario de creación.
@login_required(login_url='login')
@empresa_required
def crear_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.usuario = request.user
            producto.save()
            for img in request.FILES.getlist('imagen')[:5]:
                ImagenProducto.objects.create(producto=producto, imagen=img)
            messages.success(request, '¡Producto creado correctamente!')
            return redirect('products:productos')
    else:
        form = ProductoForm()
    return render(request, 'productservice/producto_form.html', {'form': form, 'titulo': 'Crear Producto'})

# Vista para editar un producto existente. Muestra y procesa el formulario de edición.
@login_required(login_url='login')
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, usuario=request.user)
    imagenes_actuales = producto.imagenes.all()
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        nuevas_imagenes = request.FILES.getlist('imagen')
        if form.is_valid():
            form.save()
            if nuevas_imagenes:
                total_imagenes = imagenes_actuales.count() + len(nuevas_imagenes)
                if total_imagenes > 5:
                    messages.error(request, 'Solo puedes tener hasta 5 imágenes por producto.')
                else:
                    for img in nuevas_imagenes:
                        ImagenProducto.objects.create(producto=producto, imagen=img)
                    messages.success(request, '¡Producto actualizado correctamente!')
            else:
                messages.success(request, '¡Producto actualizado correctamente!')
            return redirect('products:productos')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = ProductoForm(instance=producto)
    return render(request, 'productservice/producto_form.html', {
        'form': form,
        'titulo': 'Editar Producto',
        'imagenes': imagenes_actuales,
        'producto': producto
    })

# Vista para eliminar un producto existente. Confirma y procesa la eliminación.
@login_required(login_url='login')
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, usuario=request.user)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, '¡Producto eliminado correctamente!')
        return redirect('products:productos')
    return render(request, 'productservice/producto_confirm_delete.html', {'producto': producto})

# Vista para eliminar una imagen de un producto.
@login_required(login_url='login')
def eliminar_imagen_producto(request, imagen_id):
    imagen = get_object_or_404(ImagenProducto, id=imagen_id, producto__usuario=request.user)
    producto_id = imagen.producto.id
    imagen.delete()
    messages.success(request, '¡Imagen eliminada correctamente!')
    return redirect('products:editar_producto', pk=producto_id)

# Vista que muestra la lista de servicios del usuario autenticado.
@login_required(login_url='login')
@empresa_required
def servicios(request):
    servicios = Servicio.objects.filter(usuario=request.user).prefetch_related('imagenes')
    return render(request, 'productservice/servicios.html', {'servicios': servicios})

# Vista que muestra la lista de pedidos del usuario autenticado.
@login_required(login_url='login')
def pedidos(request):
    return render(request, 'productservice/pedidos.html')

# Vista para crear un nuevo servicio. Muestra y procesa el formulario de creación.
@login_required(login_url='login')
@empresa_required
def crear_servicio(request):
    if request.method == 'POST':
        form = ServicioForm(request.POST)
        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.usuario = request.user
            servicio.save()
            for img in request.FILES.getlist('imagen')[:5]:
                ImagenServicio.objects.create(servicio=servicio, imagen=img)
            messages.success(request, '¡Servicio creado correctamente!')
            return redirect('products:servicios')
    else:
        form = ServicioForm()
    return render(request, 'productservice/servicio_form.html', {'form': form, 'titulo': 'Crear Servicio'})

# Vista para editar un servicio existente. Muestra y procesa el formulario de edición.
@login_required(login_url='login')
def editar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk, usuario=request.user)
    imagenes_actuales = servicio.imagenes.all()
    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        nuevas_imagenes = request.FILES.getlist('imagen')
        if form.is_valid():
            form.save()
            if nuevas_imagenes:
                total_imagenes = imagenes_actuales.count() + len(nuevas_imagenes)
                if total_imagenes > 5:
                    messages.error(request, 'Solo puedes tener hasta 5 imágenes por servicio.')
                else:
                    for img in nuevas_imagenes:
                        ImagenServicio.objects.create(servicio=servicio, imagen=img)
                    messages.success(request, '¡Servicio actualizado correctamente!')
            else:
                messages.success(request, '¡Servicio actualizado correctamente!')
            return redirect('products:servicios')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = ServicioForm(instance=servicio)
    return render(request, 'productservice/servicio_form.html', {
        'form': form,
        'titulo': 'Editar Servicio',
        'imagenes': imagenes_actuales,
        'servicio': servicio
    })

# Vista para eliminar un servicio existente. Confirma y procesa la eliminación.
@login_required(login_url='login')
def eliminar_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk, usuario=request.user)
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, '¡Servicio eliminado correctamente!')
        return redirect('products:servicios')
    return render(request, 'productservice/servicio_confirm_delete.html', {'servicio': servicio})

# Vista para eliminar una imagen de un servicio.
@login_required(login_url='login')
def eliminar_imagen_servicio(request, imagen_id):
    imagen = get_object_or_404(ImagenServicio, id=imagen_id, servicio__usuario=request.user)
    servicio_id = imagen.servicio.id
    imagen.delete()
    messages.success(request, '¡Imagen eliminada correctamente!')
    return redirect('products:editar_servicio', pk=servicio_id)

# Vista para marcar una imagen de producto como principal.
@login_required(login_url='login')
def marcar_principal_imagen_producto(request, imagen_id):
    imagen = get_object_or_404(ImagenProducto, id=imagen_id, producto__usuario=request.user)
    producto = imagen.producto
    if request.method == 'POST':
        producto.imagenes.update(principal=False)
        imagen.principal = True
        imagen.save()
        messages.success(request, '¡Imagen marcada como principal!')
    return redirect('products:editar_producto', pk=producto.pk)

# Vista para marcar una imagen de servicio como principal.
@login_required(login_url='login')
def marcar_principal_imagen_servicio(request, imagen_id):
    imagen = get_object_or_404(ImagenServicio, id=imagen_id, servicio__usuario=request.user)
    servicio = imagen.servicio
    if request.method == 'POST':
        servicio.imagenes.update(principal=False)
        imagen.principal = True
        imagen.save()
        messages.success(request, '¡Imagen marcada como principal!')
    return redirect('products:editar_servicio', pk=servicio.pk)

# Vista de detalle de un producto público
@login_required(login_url='login')
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    
    # Obtener perfil del usuario
    perfil = PerfilUsuario.objects.get(usuario=request.user)
    
    # Si es empresa, solo puede ver sus productos
    if perfil.tipo_cuenta == 'empresa' and producto.usuario != request.user:
        raise Http404('No tienes acceso a este producto')
    
    images = producto.imagenes.all()
    
    # Lógica de productos relacionados según tipo de usuario
    similar_products = []
    prev_product = None
    next_product = None
    
    if perfil.tipo_cuenta == 'usuario':
        # Usuario consumidor: mostrar productos relacionados de todas las empresas (marketplace)
        similar_products = Producto.objects.filter(
            categoria=producto.categoria, 
            activo=True
        ).exclude(pk=pk)[:4]
        
        # Navegación: productos anterior y siguiente de todas las empresas
        all_products = list(Producto.objects.filter(activo=True).order_by('id'))
        index = next((i for i, p in enumerate(all_products) if p.pk == producto.pk), None)
        prev_product = all_products[index-1] if index is not None and index > 0 else None
        next_product = all_products[index+1] if index is not None and index < len(all_products)-1 else None
        
    elif perfil.tipo_cuenta == 'empresa':
        # Usuario empresa: solo mostrar sus propios productos relacionados (confidencialidad)
        similar_products = Producto.objects.filter(
            categoria=producto.categoria, 
            activo=True,
            usuario=request.user  # Solo productos de la misma empresa
        ).exclude(pk=pk)[:4]
        
        # Navegación: solo entre sus propios productos
        own_products = list(Producto.objects.filter(
            usuario=request.user, 
            activo=True
        ).order_by('id'))
        index = next((i for i, p in enumerate(own_products) if p.pk == producto.pk), None)
        prev_product = own_products[index-1] if index is not None and index > 0 else None
        next_product = own_products[index+1] if index is not None and index < len(own_products)-1 else None
    
    return render(request, 'productservice/producto_detail.html', {
        'producto': producto,
        'images': images,
        'similar_products': similar_products,
        'prev_product': prev_product,
        'next_product': next_product,
        'perfil': perfil,  # CORREGIDO: Pasar perfil para el sidebar
        'user_type': perfil.tipo_cuenta,  # Para usar en el template si es necesario
    })

# Vista de detalle de un servicio público
@login_required(login_url='login')
def detalle_servicio(request, pk):
    servicio = get_object_or_404(Servicio, pk=pk, activo=True)
    
    # Obtener perfil del usuario
    perfil = PerfilUsuario.objects.get(usuario=request.user)
    
    # Si es empresa, solo puede ver sus servicios
    if perfil.tipo_cuenta == 'empresa' and servicio.usuario != request.user:
        raise Http404('No tienes acceso a este servicio')
    
    images = servicio.imagenes.all()
    
    # Lógica de servicios relacionados según tipo de usuario
    similar_services = []
    
    if perfil.tipo_cuenta == 'usuario':
        # Usuario consumidor: mostrar servicios relacionados de todas las empresas (marketplace)
        similar_services = Servicio.objects.filter(
            categoria=servicio.categoria, 
            activo=True
        ).exclude(pk=pk)[:4]
        
    elif perfil.tipo_cuenta == 'empresa':
        # Usuario empresa: solo mostrar sus propios servicios relacionados (confidencialidad)
        similar_services = Servicio.objects.filter(
            categoria=servicio.categoria, 
            activo=True,
            usuario=request.user  # Solo servicios de la misma empresa
        ).exclude(pk=pk)[:4]
    
    return render(request, 'productservice/servicio_detail.html', {
        'servicio': servicio,
        'images': images,
        'similar_services': similar_services,
        'perfil': perfil,  # CORREGIDO: Pasar perfil para el sidebar
        'user_type': perfil.tipo_cuenta,  # Para usar en el template si es necesario
    })


# Vistas para editar políticas de productos y servicios
@login_required(login_url='login')
def editar_politicas_producto(request, pk):
    """Vista para editar las políticas de envío y devoluciones de un producto"""
    producto = get_object_or_404(Producto, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")  # Debug
        form = PoliticasProductoForm(request.POST, instance=producto)
        print(f"Form is valid: {form.is_valid()}")  # Debug
        if not form.is_valid():
            print(f"Form errors: {form.errors}")  # Debug
        if form.is_valid():
            try:
                producto_guardado = form.save()
                print(f"Producto guardado: {producto_guardado.pk}")  # Debug
                messages.success(request, 'Políticas actualizadas correctamente')
                return redirect('products:detalle_producto', pk=pk)
            except Exception as e:
                print(f"Error saving: {e}")  # Debug
                messages.error(request, f'Error al guardar las políticas: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = PoliticasProductoForm(instance=producto)
    
    return render(request, 'productservice/editar_politicas_producto.html', {
        'form': form,
        'producto': producto,
        'politicas_envio_default': producto.get_politicas_envio_default(),
        'politicas_devoluciones_default': producto.get_politicas_devoluciones_default(),
    })


@login_required(login_url='login')
def editar_politicas_servicio(request, pk):
    """Vista para editar las políticas de reserva y cancelación de un servicio"""
    servicio = get_object_or_404(Servicio, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")  # Debug
        form = PoliticasServicioForm(request.POST, instance=servicio)
        print(f"Form is valid: {form.is_valid()}")  # Debug
        if not form.is_valid():
            print(f"Form errors: {form.errors}")  # Debug
        if form.is_valid():
            try:
                servicio_guardado = form.save()
                print(f"Servicio guardado: {servicio_guardado.pk}")  # Debug
                messages.success(request, 'Políticas actualizadas correctamente')
                return redirect('products:detalle_servicio', pk=pk)
            except Exception as e:
                print(f"Error saving: {e}")  # Debug
                messages.error(request, f'Error al guardar las políticas: {str(e)}')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
    else:
        form = PoliticasServicioForm(instance=servicio)
    
    return render(request, 'productservice/editar_politicas_servicio.html', {
        'form': form,
        'servicio': servicio,
        'politicas_reserva_default': servicio.get_politicas_reserva_default(),
        'politicas_cancelacion_default': servicio.get_politicas_cancelacion_default(),
    })


@login_required(login_url='login')
def resetear_politicas_producto(request, pk):
    """Vista para resetear las políticas de un producto a los valores por defecto"""
    producto = get_object_or_404(Producto, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        # Resetear políticas a diccionario vacío para usar defaults
        producto.politicas_envio = {}
        producto.politicas_devoluciones = {}
        producto.save()
        messages.success(request, 'Políticas restablecidas a valores por defecto')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required(login_url='login')
def resetear_politicas_servicio(request, pk):
    """Vista para resetear las políticas de un servicio a los valores por defecto"""
    servicio = get_object_or_404(Servicio, pk=pk, usuario=request.user)
    
    if request.method == 'POST':
        # Resetear políticas a diccionario vacío para usar defaults
        servicio.politicas_reserva = {}
        servicio.politicas_cancelacion = {}
        servicio.save()
        messages.success(request, 'Políticas restablecidas a valores por defecto')
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


# =========================== VISTAS DE MENSAJERÍA DE PEDIDOS ===========================

@login_required(login_url='login')
@require_http_methods(["POST"])
def enviar_mensaje_pedido(request, pedido_id):
    """
    Vista para enviar un mensaje sobre un pedido.
    Solo el cliente o la empresa del pedido pueden enviar mensajes.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    # Verificar que el usuario tiene permiso para enviar mensajes en este pedido
    if request.user != pedido.usuario and request.user != pedido.empresa:
        return JsonResponse({'success': False, 'error': 'No tienes permiso para enviar mensajes en este pedido'}, status=403)
    
    mensaje_texto = request.POST.get('mensaje', '').strip()
    archivo = request.FILES.get('archivo_adjunto', None)
    
    if not mensaje_texto and not archivo:
        return JsonResponse({'success': False, 'error': 'El mensaje no puede estar vacío. Escribe un mensaje o adjunta un archivo.'}, status=400)
    
    try:
        # Crear el mensaje
        mensaje = MensajePedido.objects.create(
            pedido=pedido,
            remitente=request.user,
            mensaje=mensaje_texto if mensaje_texto else '',
            archivo_adjunto=archivo
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error al crear el mensaje: {str(e)}'}, status=500)
    
    return JsonResponse({
        'success': True,
        'mensaje_id': mensaje.id,
        'fecha': mensaje.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        'remitente': mensaje.remitente.username,
        'tiene_adjunto': bool(mensaje.archivo_adjunto)
    })


@login_required(login_url='login')
def obtener_mensajes_pedido(request, pedido_id):
    """
    Vista para obtener los mensajes de un pedido (JSON).
    Útil para polling o actualización automática.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    # Verificar que el usuario tiene permiso para ver mensajes de este pedido
    if request.user != pedido.usuario and request.user != pedido.empresa:
        return JsonResponse({'success': False, 'error': 'No tienes permiso para ver mensajes de este pedido'}, status=403)
    
    # Obtener mensajes
    mensajes = MensajePedido.objects.filter(pedido=pedido).select_related('remitente')
    
    # Marcar mensajes no leídos como leídos (solo los que no son del usuario actual)
    mensajes_no_leidos = mensajes.filter(leido=False).exclude(remitente=request.user)
    mensajes_no_leidos.update(leido=True)
    
    # Preparar datos para JSON
    mensajes_data = []
    for msg in mensajes:
        mensajes_data.append({
            'id': msg.id,
            'remitente': msg.remitente.username,
            'remitente_id': msg.remitente.id,
            'es_del_cliente': msg.es_del_cliente,
            'es_de_la_empresa': msg.es_de_la_empresa,
            'mensaje': msg.mensaje,
            'fecha': msg.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_iso': msg.fecha_creacion.isoformat(),
            'leido': msg.leido,
            'tiene_adjunto': bool(msg.archivo_adjunto),
            'archivo_url': msg.archivo_adjunto.url if msg.archivo_adjunto else None,
            'archivo_nombre': msg.archivo_adjunto.name.split('/')[-1] if msg.archivo_adjunto else None,
        })
    
    # Contar mensajes no leídos
    mensajes_no_leidos_count = MensajePedido.objects.filter(
        pedido=pedido,
        leido=False
    ).exclude(remitente=request.user).count()
    
    return JsonResponse({
        'success': True,
        'mensajes': mensajes_data,
        'total_mensajes': len(mensajes_data),
        'mensajes_no_leidos': mensajes_no_leidos_count
    })


@login_required(login_url='login')
@require_http_methods(["POST"])
def marcar_mensajes_leidos(request, pedido_id):
    """
    Vista para marcar todos los mensajes de un pedido como leídos.
    """
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    
    # Verificar que el usuario tiene permiso
    if request.user != pedido.usuario and request.user != pedido.empresa:
        return JsonResponse({'success': False, 'error': 'No tienes permiso'}, status=403)
    
    # Marcar mensajes no leídos como leídos (solo los que no son del usuario actual)
    MensajePedido.objects.filter(
        pedido=pedido,
        leido=False
    ).exclude(remitente=request.user).update(leido=True)
    
    return JsonResponse({'success': True})


@login_required(login_url='login')
def conteo_mensajes_no_leidos(request):
    """
    Vista para obtener el conteo total de mensajes no leídos del usuario.
    Útil para mostrar notificaciones en el navbar.
    """
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': True, 'conteo': 0})
    
    # Obtener todos los pedidos donde el usuario participa
    if perfil.tipo_cuenta == 'empresa':
        pedidos = Pedido.objects.filter(empresa=request.user)
    else:
        pedidos = Pedido.objects.filter(usuario=request.user)
    
    # Contar mensajes no leídos (excluyendo los que el usuario envió)
    conteo = MensajePedido.objects.filter(
        pedido__in=pedidos,
        leido=False
    ).exclude(remitente=request.user).count()
    
    return JsonResponse({
        'success': True,
        'conteo': conteo
    })


@login_required(login_url='login')
def obtener_chats_actualizados(request):
    """
    Vista API para obtener la información actualizada de los chats.
    Útil para actualización en tiempo real sin recargar la página.
    """
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
    except PerfilUsuario.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil no encontrado'}, status=404)
    
    # Obtener todos los pedidos donde el usuario participa
    if perfil.tipo_cuenta == 'empresa':
        pedidos = Pedido.objects.filter(empresa=request.user).select_related('usuario')
    else:
        pedidos = Pedido.objects.filter(usuario=request.user).select_related('empresa')
    
    ahora = timezone.now()
    hace_30_dias = ahora - timezone.timedelta(days=30)
    
    chats_data = []
    
    for pedido in pedidos:
        todos_mensajes = MensajePedido.objects.filter(pedido=pedido)
        
        if todos_mensajes.exists():
            mensajes_no_leidos = todos_mensajes.filter(
                leido=False
            ).exclude(remitente=request.user)
            
            conteo_no_leidos = mensajes_no_leidos.count()
            ultimo_mensaje = todos_mensajes.order_by('-fecha_creacion').first()
            total_mensajes = todos_mensajes.count()
            es_activo = ultimo_mensaje and ultimo_mensaje.fecha_creacion >= hace_30_dias
            
            chats_data.append({
                'pedido_id': pedido.id,
                'conteo_no_leidos': conteo_no_leidos,
                'total_mensajes': total_mensajes,
                'fecha_ultimo': ultimo_mensaje.fecha_creacion.isoformat() if ultimo_mensaje else None,
                'es_activo': es_activo,
                'ultimo_mensaje_texto': ultimo_mensaje.mensaje[:50] if ultimo_mensaje and ultimo_mensaje.mensaje else None,
                'ultimo_mensaje_remitente': ultimo_mensaje.remitente.username if ultimo_mensaje else None,
                'es_del_usuario': ultimo_mensaje.remitente == request.user if ultimo_mensaje else False,
                'tiene_adjunto': bool(ultimo_mensaje.archivo_adjunto) if ultimo_mensaje else False
            })
    
    # Separar en activos y pasados
    chats_activos = [c for c in chats_data if c['es_activo']]
    chats_pasados = [c for c in chats_data if not c['es_activo']]
    
    # Ordenar por fecha
    chats_activos.sort(key=lambda x: x['fecha_ultimo'] or '', reverse=True)
    chats_pasados.sort(key=lambda x: x['fecha_ultimo'] or '', reverse=True)
    
    return JsonResponse({
        'success': True,
        'chats_activos': chats_activos,
        'chats_pasados': chats_pasados,
        'total_no_leidos': sum(c['conteo_no_leidos'] for c in chats_data)
    })


@login_required(login_url='login')
def notificaciones_mensajes(request):
    """
    Vista para mostrar todas las conversaciones de mensajes del usuario.
    Incluye chats activos (mensajes recientes) y pasados (mensajes antiguos).
    """
    try:
        perfil = PerfilUsuario.objects.get(usuario=request.user)
    except PerfilUsuario.DoesNotExist:
        perfil = None
    
    # Obtener todos los pedidos donde el usuario participa
    if perfil and perfil.tipo_cuenta == 'empresa':
        pedidos = Pedido.objects.filter(empresa=request.user).select_related('usuario')
    else:
        pedidos = Pedido.objects.filter(usuario=request.user).select_related('empresa')
    
    # Obtener información de todos los pedidos con mensajes
    pedidos_con_mensajes = []
    ahora = timezone.now()
    hace_30_dias = ahora - timezone.timedelta(days=30)
    
    for pedido in pedidos:
        # Obtener todos los mensajes del pedido
        todos_mensajes = MensajePedido.objects.filter(pedido=pedido)
        
        if todos_mensajes.exists():
            # Contar mensajes no leídos
            mensajes_no_leidos = todos_mensajes.filter(
                leido=False
            ).exclude(remitente=request.user)
            
            conteo_no_leidos = mensajes_no_leidos.count()
            
            # Obtener el último mensaje (de cualquier tipo)
            ultimo_mensaje = todos_mensajes.order_by('-fecha_creacion').first()
            
            # Contar total de mensajes
            total_mensajes = todos_mensajes.count()
            
            # Determinar si es activo (mensajes en los últimos 30 días)
            es_activo = ultimo_mensaje and ultimo_mensaje.fecha_creacion >= hace_30_dias
            
            pedidos_con_mensajes.append({
                'pedido': pedido,
                'conteo_no_leidos': conteo_no_leidos,
                'total_mensajes': total_mensajes,
                'ultimo_mensaje': ultimo_mensaje,
                'fecha_ultimo': ultimo_mensaje.fecha_creacion if ultimo_mensaje else None,
                'es_activo': es_activo,
                'es_del_usuario': ultimo_mensaje.remitente == request.user if ultimo_mensaje else False
            })
    
    # Separar en activos y pasados
    chats_activos = [p for p in pedidos_con_mensajes if p['es_activo']]
    chats_pasados = [p for p in pedidos_con_mensajes if not p['es_activo']]
    
    # Ordenar por fecha del último mensaje (más reciente primero)
    chats_activos.sort(key=lambda x: x['fecha_ultimo'] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    chats_pasados.sort(key=lambda x: x['fecha_ultimo'] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    
    context = {
        'chats_activos': chats_activos,
        'chats_pasados': chats_pasados,
        'total_no_leidos': sum(p['conteo_no_leidos'] for p in pedidos_con_mensajes),
        'perfil': perfil,
        'today': timezone.now()
    }
    
    return render(request, 'productservice/notificaciones_mensajes.html', context)
