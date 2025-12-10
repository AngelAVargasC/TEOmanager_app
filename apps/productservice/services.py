"""
Servicios para la lógica de negocio de productos y servicios.

Este módulo contiene las clases de servicio que encapsulan la lógica de negocio
relacionada con productos, servicios, imágenes y pedidos. Siguiendo el patrón de
arquitectura por capas, estos servicios actúan como intermediarios entre
las vistas y los modelos.

Beneficios:
- Separación de responsabilidades
- Reutilización de código
- Facilita el testing
- Centraliza la lógica de negocio
- Optimización de consultas a la base de datos
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Q, Prefetch, Avg
import logging
from PIL import Image
import os

from .models import Producto, Servicio, ImagenProducto, ImagenServicio, Pedido, DetallePedido
from apps.accounts.services import SuscripcionService

# Configurar logger para este módulo
logger = logging.getLogger(__name__)


class ProductService:
    """
    Servicio para operaciones relacionadas con productos.
    
    Centraliza toda la lógica de negocio relacionada con la gestión
    de productos, incluyendo creación, actualización, imágenes y validaciones.
    """
    
    @staticmethod
    @transaction.atomic
    def create_product_with_images(user, product_data, images=None):
        """
        Crea un producto con sus imágenes asociadas en una transacción atómica.
        
        Args:
            user (User): Usuario propietario del producto
            product_data (dict): Datos del producto
            images (list): Lista de archivos de imagen
            
        Returns:
            Producto: Producto creado con imágenes
            
        Raises:
            ValueError: Si se exceden los límites del plan o datos inválidos
        """
        # Verificar límites del plan
        limits = SuscripcionService.check_plan_limits(user, 'productos')
        if not limits['allowed']:
            raise ValueError(limits['message'])
        
        try:
            # Crear el producto
            producto = Producto.objects.create(
                usuario=user,
                **product_data
            )
            
            # Procesar imágenes si se proporcionaron
            if images:
                ProductService._process_product_images(producto, images)
            
            logger.info(f"Producto '{producto.nombre}' creado exitosamente para usuario {user.username}")
            
            return producto
            
        except Exception as e:
            logger.error(f"Error creando producto para usuario {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def _process_product_images(producto, images):
        """
        Procesa y guarda las imágenes de un producto.
        
        Args:
            producto (Producto): Producto al que asociar las imágenes
            images (list): Lista de archivos de imagen
        """
        for i, image_file in enumerate(images):
            # Validar imagen
            ProductService._validate_image(image_file)
            
            # Crear registro de imagen
            imagen_producto = ImagenProducto.objects.create(
                producto=producto,
                imagen=image_file,
                principal=(i == 0)  # Primera imagen como principal
            )
            
            # Optimizar imagen si es necesario
            ProductService._optimize_image(imagen_producto.imagen.path)
    
    @staticmethod
    def _validate_image(image_file):
        """
        Valida que el archivo de imagen cumpla con los requisitos.
        
        Args:
            image_file: Archivo de imagen
            
        Raises:
            ValidationError: Si la imagen no es válida
        """
        # Validar tamaño (máximo 5MB)
        if image_file.size > 5 * 1024 * 1024:
            raise ValidationError("La imagen no puede exceder 5MB")
        
        # Validar formato
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(image_file.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError("Formato de imagen no válido. Use JPG, PNG o GIF")
    
    @staticmethod
    def _optimize_image(image_path):
        """
        Optimiza una imagen para reducir su tamaño manteniendo calidad.
        
        Args:
            image_path (str): Ruta de la imagen
        """
        try:
            with Image.open(image_path) as img:
                # Redimensionar si es muy grande
                max_size = (1200, 1200)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                    img.save(image_path, optimize=True, quality=85)
                    
        except Exception as e:
            logger.warning(f"No se pudo optimizar la imagen {image_path}: {str(e)}")
    
    @staticmethod
    def update_product(producto, product_data, new_images=None, images_to_delete=None):
        """
        Actualiza un producto y gestiona sus imágenes.
        
        Args:
            producto (Producto): Producto a actualizar
            product_data (dict): Nuevos datos del producto
            new_images (list): Nuevas imágenes a agregar
            images_to_delete (list): IDs de imágenes a eliminar
            
        Returns:
            Producto: Producto actualizado
        """
        try:
            with transaction.atomic():
                # Actualizar datos del producto
                for field, value in product_data.items():
                    if hasattr(producto, field):
                        setattr(producto, field, value)
                
                producto.save()
                
                # Eliminar imágenes marcadas para eliminación
                if images_to_delete:
                    ImagenProducto.objects.filter(
                        id__in=images_to_delete,
                        producto=producto
                    ).delete()
                
                # Agregar nuevas imágenes
                if new_images:
                    ProductService._process_product_images(producto, new_images)
                
                logger.info(f"Producto '{producto.nombre}' actualizado exitosamente")
                
                return producto
                
        except Exception as e:
            logger.error(f"Error actualizando producto {producto.id}: {str(e)}")
            raise
    
    @staticmethod
    def get_products_with_images(user, filters=None):
        """
        Obtiene productos del usuario con sus imágenes optimizando consultas.
        
        Args:
            user (User): Usuario propietario
            filters (dict): Filtros adicionales
            
        Returns:
            QuerySet: Productos con imágenes precargadas
        """
        queryset = Producto.objects.filter(usuario=user).prefetch_related(
            Prefetch(
                'imagenes',
                queryset=ImagenProducto.objects.order_by('-principal', '-fecha_subida')
            )
        ).order_by('-fecha_creacion')
        
        # Aplicar filtros si se proporcionan
        if filters:
            if filters.get('categoria'):
                queryset = queryset.filter(categoria__icontains=filters['categoria'])
            
            if filters.get('activo') is not None:
                queryset = queryset.filter(activo=filters['activo'])
            
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(nombre__icontains=search_term) |
                    Q(descripcion__icontains=search_term)
                )
        
        return queryset
    
    @staticmethod
    def set_main_image(producto, imagen_id):
        """
        Establece una imagen como principal para un producto.
        
        Args:
            producto (Producto): Producto
            imagen_id (int): ID de la imagen a marcar como principal
        """
        try:
            with transaction.atomic():
                # Desmarcar todas las imágenes como principales
                producto.imagenes.update(principal=False)
                
                # Marcar la imagen seleccionada como principal
                imagen = producto.imagenes.get(id=imagen_id)
                imagen.principal = True
                imagen.save()
                
                logger.info(f"Imagen {imagen_id} marcada como principal para producto {producto.id}")
                
        except ImagenProducto.DoesNotExist:
            raise ValueError("La imagen especificada no existe")
        except Exception as e:
            logger.error(f"Error estableciendo imagen principal: {str(e)}")
            raise
    
    @staticmethod
    def get_product_stats(user):
        """
        Obtiene estadísticas de productos del usuario.
        
        Args:
            user (User): Usuario
            
        Returns:
            dict: Estadísticas de productos
        """
        productos = user.productos.all()
        
        stats = {
            'total_productos': productos.count(),
            'productos_activos': productos.filter(activo=True).count(),
            'productos_sin_stock': productos.filter(stock=0).count(),
            'productos_stock_bajo': productos.filter(stock__lt=5, stock__gt=0).count(),
            'valor_total_inventario': sum(p.precio * p.stock for p in productos if p.activo),
            'categorias': list(productos.values_list('categoria', flat=True).distinct()),
        }
        
        return stats


class ServiceService:
    """
    Servicio para operaciones relacionadas con servicios.
    
    Similar a ProductService pero específico para servicios.
    """
    
    @staticmethod
    @transaction.atomic
    def create_service_with_images(user, service_data, images=None):
        """
        Crea un servicio con sus imágenes asociadas.
        
        Args:
            user (User): Usuario propietario del servicio
            service_data (dict): Datos del servicio
            images (list): Lista de archivos de imagen
            
        Returns:
            Servicio: Servicio creado con imágenes
        """
        # Verificar límites del plan
        limits = SuscripcionService.check_plan_limits(user, 'servicios')
        if not limits['allowed']:
            raise ValueError(limits['message'])
        
        try:
            # Crear el servicio
            servicio = Servicio.objects.create(
                usuario=user,
                **service_data
            )
            
            # Procesar imágenes si se proporcionaron
            if images:
                ServiceService._process_service_images(servicio, images)
            
            logger.info(f"Servicio '{servicio.nombre}' creado exitosamente para usuario {user.username}")
            
            return servicio
            
        except Exception as e:
            logger.error(f"Error creando servicio para usuario {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def _process_service_images(servicio, images):
        """
        Procesa y guarda las imágenes de un servicio.
        
        Args:
            servicio (Servicio): Servicio al que asociar las imágenes
            images (list): Lista de archivos de imagen
        """
        for i, image_file in enumerate(images):
            # Validar imagen
            ProductService._validate_image(image_file)  # Reutilizar validación
            
            # Crear registro de imagen
            imagen_servicio = ImagenServicio.objects.create(
                servicio=servicio,
                imagen=image_file,
                principal=(i == 0)  # Primera imagen como principal
            )
            
            # Optimizar imagen
            ProductService._optimize_image(imagen_servicio.imagen.path)
    
    @staticmethod
    def get_services_with_images(user, filters=None):
        """
        Obtiene servicios del usuario con sus imágenes optimizando consultas.
        
        Args:
            user (User): Usuario propietario
            filters (dict): Filtros adicionales
            
        Returns:
            QuerySet: Servicios con imágenes precargadas
        """
        queryset = Servicio.objects.filter(usuario=user).prefetch_related(
            Prefetch(
                'imagenes',
                queryset=ImagenServicio.objects.order_by('-principal', '-fecha_subida')
            )
        ).order_by('-fecha_creacion')
        
        # Aplicar filtros
        if filters:
            if filters.get('categoria'):
                queryset = queryset.filter(categoria__icontains=filters['categoria'])
            
            if filters.get('activo') is not None:
                queryset = queryset.filter(activo=filters['activo'])
            
            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(nombre__icontains=search_term) |
                    Q(descripcion__icontains=search_term)
                )
        
        return queryset
    
    @staticmethod
    def get_service_stats(user):
        """
        Obtiene estadísticas de servicios del usuario.
        
        Args:
            user (User): Usuario
            
        Returns:
            dict: Estadísticas de servicios
        """
        servicios = user.servicios.all()
        
        stats = {
            'total_servicios': servicios.count(),
            'servicios_activos': servicios.filter(activo=True).count(),
            'precio_promedio': servicios.aggregate(
                promedio=Avg('precio')
            )['promedio'] or 0,
            'categorias': list(servicios.values_list('categoria', flat=True).distinct()),
        }
        
        return stats


class PedidoService:
    """
    Servicio para la gestión de pedidos.
    
    Maneja la creación, actualización y gestión del estado de pedidos,
    incluyendo el cálculo de totales y validaciones de negocio.
    """
    
    @staticmethod
    @transaction.atomic
    def create_pedido(user, empresa, items_data, notas=''):
        """
        Crea un nuevo pedido con sus detalles.
        
        Args:
            user (User): Usuario que realiza el pedido
            empresa (User): Empresa que recibe el pedido
            items_data (list): Lista de items del pedido
                [{'tipo': 'producto'|'servicio', 'id': int, 'cantidad': int}]
            notas (str): Notas adicionales
            
        Returns:
            Pedido: Pedido creado
        """
        try:
            # Crear pedido inicial
            pedido = Pedido.objects.create(
                usuario=user,
                empresa=empresa,
                total=0,  # Se calculará después
                notas=notas
            )
            
            total_pedido = 0
            
            # Crear detalles del pedido
            for item_data in items_data:
                detalle = PedidoService._create_detalle_pedido(pedido, item_data)
                total_pedido += detalle.subtotal
            
            # Actualizar total del pedido
            pedido.total = total_pedido
            pedido.save()
            
            logger.info(f"Pedido #{pedido.id} creado exitosamente para usuario {user.username} → {empresa.username}")
            
            return pedido
            
        except Exception as e:
            logger.error(f"Error creando pedido para usuario {user.username}: {str(e)}")
            raise
    
    @staticmethod
    @transaction.atomic
    def create_pedidos_from_cart(user, cart_session, notas_por_empresa=None):
        """
        Crea pedidos desde el carrito de sesión, agrupando por empresa.
        
        Un carrito puede contener productos de múltiples empresas, por lo que
        se crea un pedido separado para cada empresa.
        
        Args:
            user (User): Usuario que realiza la compra
            cart_session (dict): Carrito de sesión {product_id: quantity}
            notas_por_empresa (dict): Comentarios específicos por empresa {empresa_username: notas}
            
        Returns:
            list: Lista de pedidos creados
            
        Raises:
            ValueError: Si hay problemas con productos o stock
        """
        try:
            if not cart_session:
                raise ValueError("El carrito está vacío")
            
            # Inicializar diccionario de notas si no se proporciona
            if notas_por_empresa is None:
                notas_por_empresa = {}
            
            pedidos_creados = []
            
            # Agrupar productos por empresa
            empresas_productos = {}
            
            for product_id, quantity in cart_session.items():
                try:
                    producto = Producto.objects.select_related('usuario').get(
                        pk=int(product_id), 
                        activo=True
                    )
                    
                    empresa_id = producto.usuario.id
                    
                    if empresa_id not in empresas_productos:
                        empresas_productos[empresa_id] = {
                            'empresa': producto.usuario,
                            'items': []
                        }
                    
                    empresas_productos[empresa_id]['items'].append({
                        'tipo': 'producto',
                        'id': producto.id,
                        'cantidad': quantity
                    })
                    
                except (Producto.DoesNotExist, ValueError) as e:
                    logger.warning(f"Producto {product_id} no encontrado o inválido: {str(e)}")
                    continue
            
            # Crear un pedido por cada empresa
            for empresa_data in empresas_productos.values():
                empresa = empresa_data['empresa']
                items = empresa_data['items']
                
                if items:  # Solo crear pedido si hay items válidos
                    # Obtener notas específicas para esta empresa
                    notas_empresa = notas_por_empresa.get(empresa.username, '')
                    
                    pedido = PedidoService.create_pedido(
                        user=user,
                        empresa=empresa,
                        items_data=items,
                        notas=notas_empresa
                    )
                    pedidos_creados.append(pedido)
            
            if not pedidos_creados:
                raise ValueError("No se pudieron crear pedidos. Verifica que los productos estén disponibles.")
            
            logger.info(f"Se crearon {len(pedidos_creados)} pedidos para usuario {user.username} con comentarios específicos por empresa")
            
            return pedidos_creados
            
        except Exception as e:
            logger.error(f"Error creando pedidos desde carrito para usuario {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def _create_detalle_pedido(pedido, item_data):
        """
        Crea un detalle de pedido.
        
        Args:
            pedido (Pedido): Pedido padre
            item_data (dict): Datos del item
            
        Returns:
            DetallePedido: Detalle creado
        """
        tipo = item_data['tipo']
        item_id = item_data['id']
        cantidad = item_data['cantidad']
        
        if tipo == 'producto':
            producto = Producto.objects.get(id=item_id, activo=True)
            
            # Verificar stock
            if producto.stock < cantidad:
                raise ValueError(f"Stock insuficiente para {producto.nombre}")
            
            detalle = DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=producto.precio * cantidad
            )
            
            # Reducir stock
            producto.stock -= cantidad
            producto.save()
            
        elif tipo == 'servicio':
            servicio = Servicio.objects.get(id=item_id, activo=True)
            
            detalle = DetallePedido.objects.create(
                pedido=pedido,
                servicio=servicio,
                cantidad=cantidad,
                precio_unitario=servicio.precio,
                subtotal=servicio.precio * cantidad
            )
        
        else:
            raise ValueError(f"Tipo de item no válido: {tipo}")
        
        return detalle
    
    @staticmethod
    def update_pedido_status(pedido, nuevo_estado):
        """
        Actualiza el estado de un pedido con validaciones.
        
        Args:
            pedido (Pedido): Pedido a actualizar
            nuevo_estado (str): Nuevo estado
        """
        estados_validos = dict(Pedido.ESTADO_PEDIDO).keys()
        
        if nuevo_estado not in estados_validos:
            raise ValueError(f"Estado no válido: {nuevo_estado}")
        
        # Validaciones de transición de estado
        if pedido.estado == 'completado' and nuevo_estado != 'completado':
            raise ValueError("No se puede cambiar el estado de un pedido completado")
        
        if pedido.estado == 'cancelado' and nuevo_estado != 'cancelado':
            raise ValueError("No se puede cambiar el estado de un pedido cancelado")
        
        pedido.estado = nuevo_estado
        pedido.save()
        
        logger.info(f"Estado del pedido #{pedido.id} actualizado a {nuevo_estado}")
    
    @staticmethod
    def get_pedidos_with_details(user, filters=None):
        """
        Obtiene pedidos del usuario con detalles precargados.
        
        Args:
            user (User): Usuario
            filters (dict): Filtros adicionales
            
        Returns:
            QuerySet: Pedidos con detalles precargados
        """
        queryset = Pedido.objects.filter(usuario=user).prefetch_related(
            'detalles__producto',
            'detalles__servicio'
        ).order_by('-fecha_pedido')
        
        # Aplicar filtros
        if filters:
            if filters.get('estado'):
                queryset = queryset.filter(estado=filters['estado'])
        
        return queryset
    
    @staticmethod
    def get_pedido_stats(user):
        """
        Obtiene estadísticas de pedidos del usuario.
        
        Args:
            user (User): Usuario
            
        Returns:
            dict: Estadísticas de pedidos
        """
        pedidos = user.pedidos.all()
        
        stats = {
            'total_pedidos': pedidos.count(),
            'pedidos_pendientes': pedidos.filter(estado='pendiente').count(),
            'pedidos_completados': pedidos.filter(estado='completado').count(),
            'total_gastado': sum(p.total for p in pedidos.filter(estado='completado')),
            'pedido_promedio': pedidos.aggregate(
                promedio=Avg('total')
            )['promedio'] or 0,
        }
        
        return stats
    
    @staticmethod
    def get_pedidos_empresa_with_details(empresa_user, filters=None):
        """
        Obtiene pedidos recibidos por una empresa con detalles precargados.
        
        Args:
            empresa_user (User): Usuario empresa
            filters (dict): Filtros adicionales
            
        Returns:
            QuerySet: Pedidos recibidos con detalles precargados
        """
        queryset = Pedido.objects.filter(empresa=empresa_user).select_related(
            'usuario__userprofile'  # Para obtener info del cliente
        ).prefetch_related(
            'detalles__producto',
            'detalles__servicio'
        ).order_by('-fecha_pedido')
        
        # Aplicar filtros
        if filters:
            if filters.get('estado'):
                queryset = queryset.filter(estado=filters['estado'])
            if filters.get('cliente'):
                queryset = queryset.filter(usuario__username__icontains=filters['cliente'])
        
        return queryset
    
    @staticmethod
    def get_empresa_stats(empresa_user):
        """
        Obtiene estadísticas de pedidos recibidos por una empresa.
        
        Args:
            empresa_user (User): Usuario empresa
            
        Returns:
            dict: Estadísticas de pedidos de la empresa
        """
        pedidos = empresa_user.pedidos_recibidos.all()
        
        stats = {
            'total_pedidos': pedidos.count(),
            'pedidos_pendientes': pedidos.filter(estado='pendiente').count(),
            'pedidos_en_proceso': pedidos.filter(estado='en_proceso').count(),
            'pedidos_completados': pedidos.filter(estado='completado').count(),
            'pedidos_cancelados': pedidos.filter(estado='cancelado').count(),
            'total_vendido': sum(p.total for p in pedidos.filter(estado='completado')),
            'venta_promedio': pedidos.filter(estado='completado').aggregate(
                promedio=Avg('total')
            )['promedio'] or 0,
        }
        
        return stats
    
    @staticmethod
    def update_pedido_status_by_empresa(pedido_id, empresa_user, nuevo_estado):
        """
        Actualiza el estado de un pedido desde el lado de la empresa.
        
        Args:
            pedido_id (int): ID del pedido
            empresa_user (User): Usuario empresa (para verificar permisos)
            nuevo_estado (str): Nuevo estado
            
        Returns:
            Pedido: Pedido actualizado
            
        Raises:
            ValueError: Si el pedido no pertenece a la empresa o estado inválido
        """
        try:
            pedido = Pedido.objects.get(id=pedido_id, empresa=empresa_user)
            PedidoService.update_pedido_status(pedido, nuevo_estado)
            return pedido
        except Pedido.DoesNotExist:
            raise ValueError("Pedido no encontrado o no pertenece a esta empresa")


class CatalogService:
    """
    Servicio para operaciones del catálogo público.
    
    Maneja la visualización pública de productos y servicios,
    búsquedas, filtros y recomendaciones.
    """
    
    @staticmethod
    def get_public_catalog(filters=None, page_size=20):
        """
        Obtiene el catálogo público de productos y servicios.
        
        Args:
            filters (dict): Filtros de búsqueda
            page_size (int): Tamaño de página
            
        Returns:
            dict: Catálogo con productos y servicios
        """
        # Productos públicos activos
        productos = Producto.objects.filter(activo=True).select_related('usuario').prefetch_related(
            Prefetch(
                'imagenes',
                queryset=ImagenProducto.objects.filter(principal=True)
            )
        )
        
        # Servicios públicos activos
        servicios = Servicio.objects.filter(activo=True).select_related('usuario').prefetch_related(
            Prefetch(
                'imagenes',
                queryset=ImagenServicio.objects.filter(principal=True)
            )
        )
        
        # Aplicar filtros
        if filters:
            if filters.get('search'):
                search_term = filters['search']
                productos = productos.filter(
                    Q(nombre__icontains=search_term) |
                    Q(descripcion__icontains=search_term)
                )
                servicios = servicios.filter(
                    Q(nombre__icontains=search_term) |
                    Q(descripcion__icontains=search_term)
                )
            
            if filters.get('categoria'):
                categoria = filters['categoria']
                productos = productos.filter(categoria__icontains=categoria)
                servicios = servicios.filter(categoria__icontains=categoria)
        
        return {
            'productos': productos[:page_size],
            'servicios': servicios[:page_size],
            'total_productos': productos.count(),
            'total_servicios': servicios.count(),
        }
    
    @staticmethod
    def get_featured_items():
        """
        Obtiene items destacados para la página principal.
        
        Returns:
            dict: Items destacados
        """
        # Productos más recientes
        productos_recientes = Producto.objects.filter(activo=True).select_related('usuario').prefetch_related(
            'imagenes'
        ).order_by('-fecha_creacion')[:6]
        
        # Servicios más recientes
        servicios_recientes = Servicio.objects.filter(activo=True).select_related('usuario').prefetch_related(
            'imagenes'
        ).order_by('-fecha_creacion')[:6]
        
        return {
            'productos_recientes': productos_recientes,
            'servicios_recientes': servicios_recientes,
        } 