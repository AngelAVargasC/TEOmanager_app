"""
Modelos para la gestión de productos y servicios en el sistema ERP.

Este módulo contiene los modelos relacionados con:
- Gestión de productos (Producto, ImagenProducto)
- Gestión de servicios (Servicio, ImagenServicio)
- Sistema de pedidos (Pedido, DetallePedido)

Arquitectura MVT: Estos modelos representan la capa de datos (Model) 
para la funcionalidad de catálogo y comercio electrónico.

Características principales:
- Soporte para múltiples imágenes por producto/servicio
- Sistema de imágenes principales y secundarias
- Gestión automática de archivos (limpieza al eliminar)
- Sistema de pedidos con detalles
- Optimización de consultas con propiedades calculadas
"""

from django.db import models
from django.contrib.auth.models import User
import os
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
import json


class Producto(models.Model):
    """
    Modelo que representa un producto en el catálogo del usuario.
    
    Este modelo gestiona toda la información relacionada con productos
    físicos o digitales que los usuarios pueden ofrecer en su catálogo.
    
    Funcionalidades:
    - Gestión completa de información del producto
    - Soporte para múltiples imágenes
    - Control de stock e inventario
    - Categorización flexible
    - Sistema de activación/desactivación
    - Limpieza automática de archivos
    
    Relaciones:
    - ForeignKey con User (propietario)
    - Relacionado con ImagenProducto (imágenes múltiples)
    - Relacionado con DetallePedido (sistema de pedidos)
    """
    
    # Usuario propietario del producto
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='productos',
        help_text="Usuario que creó y gestiona este producto",
        verbose_name="Propietario"
    )
    
    # Información básica del producto
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre comercial del producto",
        verbose_name="Nombre del Producto"
    )
    
    descripcion = models.TextField(
        help_text="Descripción detallada del producto, características y beneficios",
        verbose_name="Descripción"
    )
    
    # Información comercial
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],  # Precio mínimo de 1 centavo
        help_text="Precio de venta del producto",
        verbose_name="Precio"
    )
    
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],  # Stock no puede ser negativo
        help_text="Cantidad disponible en inventario",
        verbose_name="Stock Disponible"
    )
    
    # Categorización y organización
    categoria = models.CharField(
        max_length=50,
        help_text="Categoría del producto para organización y filtros",
        verbose_name="Categoría"
    )
    
    # Metadatos y control
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del producto",
        verbose_name="Fecha de Creación"
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Determina si el producto está visible y disponible para venta",
        verbose_name="Producto Activo"
    )

    # Políticas personalizables de envío y devoluciones
    politicas_envio = models.JSONField(
        default=dict,
        help_text="Políticas de envío personalizadas para este producto",
        verbose_name="Políticas de Envío"
    )
    
    politicas_devoluciones = models.JSONField(
        default=dict,
        help_text="Políticas de devoluciones personalizadas para este producto",
        verbose_name="Políticas de Devoluciones"
    )

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']  # Más recientes primero
        # Índices para optimizar consultas frecuentes
        indexes = [
            models.Index(fields=['usuario', 'activo']),  # Productos activos por usuario
            models.Index(fields=['categoria']),          # Filtros por categoría
            models.Index(fields=['fecha_creacion']),     # Ordenamiento temporal
            models.Index(fields=['precio']),             # Filtros por precio
        ]

    def __str__(self):
        """Representación string del modelo para admin y debugging."""
        return f"{self.nombre} - {self.usuario.username}"

    def delete(self, *args, **kwargs):
        """
        Override del método delete para limpieza de archivos.
        
        Elimina todas las imágenes asociadas al producto antes de
        eliminar el producto para evitar archivos huérfanos.
        """
        # Elimina todas las imágenes asociadas al producto
        for img in self.imagenes.all():
            img.delete()  # Esto también eliminará el archivo físico
            
        # Eliminar imagen principal si existe (campo legacy)
        if hasattr(self, 'imagen') and self.imagen:
            if self.imagen.path and os.path.isfile(self.imagen.path):
                os.remove(self.imagen.path)
                
        super().delete(*args, **kwargs)

    @property
    def imagen_principal(self):
        """
        Obtiene la URL de la imagen principal del producto.
        
        Busca primero una imagen marcada como principal, si no encuentra
        devuelve la primera imagen disponible.
        
        Returns:
            str|None: URL de la imagen principal o None si no hay imágenes
            
        Usage:
            {% if producto.imagen_principal %}
                <img src="{{ producto.imagen_principal }}" alt="{{ producto.nombre }}">
            {% endif %}
        """
        # Buscar imagen marcada como principal
        principal = self.imagenes.filter(principal=True).first()
        if principal:
            return principal.imagen.url
            
        # Si no hay principal, usar la primera disponible
        primera = self.imagenes.first()
        if primera:
            return primera.imagen.url
            
        return None
    
    @property
    def tiene_stock(self):
        """
        Verifica si el producto tiene stock disponible.
        
        Returns:
            bool: True si hay stock disponible, False en caso contrario
        """
        return self.stock > 0
    
    @property
    def stock_bajo(self):
        """
        Determina si el producto tiene stock bajo (menos de 5 unidades).
        
        Returns:
            bool: True si el stock es menor a 5 unidades
        """
        return self.stock < 5
    
    @property
    def total_imagenes(self):
        """
        Cuenta el total de imágenes asociadas al producto.
        
        Returns:
            int: Número total de imágenes
        """
        return self.imagenes.count()

    def clean(self):
        """Validaciones personalizadas del modelo."""
        super().clean()
        
        # Validar que el precio sea positivo
        if self.precio <= 0:
            raise ValidationError({
                'precio': 'El precio debe ser mayor a cero.'
            })
    

        
        # Validar que el stock no sea negativo
        if self.stock < 0:
            raise ValidationError({
                'stock': 'El stock no puede ser negativo.'
            })
    
    def get_politicas_envio_default(self):
        """Obtiene las políticas de envío por defecto."""
        return [
            {"icon": "fas fa-truck", "text": "Envío gratis en pedidos superiores a $500"},
            {"icon": "fas fa-clock", "text": "Tiempo de entrega: 2-5 días hábiles"},
            {"icon": "fas fa-shield-alt", "text": "Envío asegurado"},
            {"icon": "fas fa-map-marker-alt", "text": "Disponible en toda la región"}
        ]
    
    def get_politicas_devoluciones_default(self):
        """Obtiene las políticas de devoluciones por defecto."""
        return [
            {"icon": "fas fa-undo", "text": "30 días para devoluciones"},
            {"icon": "fas fa-money-bill-wave", "text": "Reembolso completo"},
            {"icon": "fas fa-box", "text": "Producto en condiciones originales"}
        ]
    
    def get_politicas_envio_completas(self):
        """Obtiene las políticas de envío completas (personalizadas o por defecto)."""
        if self.politicas_envio:
            return self.politicas_envio
        return self.get_politicas_envio_default()
    
    def get_politicas_devoluciones_completas(self):
        """Obtiene las políticas de devoluciones completas (personalizadas o por defecto)."""
        if self.politicas_devoluciones:
            return self.politicas_devoluciones
        return self.get_politicas_devoluciones_default()


class ImagenProducto(models.Model):
    """
    Modelo que gestiona las imágenes asociadas a un producto.
    
    Permite que cada producto tenga múltiples imágenes con la capacidad
    de marcar una como principal para mostrar en listados y vistas previas.
    
    Funcionalidades:
    - Múltiples imágenes por producto
    - Sistema de imagen principal
    - Limpieza automática de archivos
    - Metadatos de subida
    - Validación de formatos de imagen
    
    Relaciones:
    - ForeignKey con Producto (imagen pertenece a producto)
    """
    
    # Producto al que pertenece la imagen
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='imagenes',
        help_text="Producto al que pertenece esta imagen",
        verbose_name="Producto"
    )
    
    # Archivo de imagen
    imagen = models.ImageField(
        upload_to='productos/', 
        null=False, 
        blank=False,
        help_text="Archivo de imagen del producto (JPG, PNG, GIF)",
        verbose_name="Imagen"
    )
    
    # Metadatos
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de subida de la imagen",
        verbose_name="Fecha de Subida"
    )
    
    # Control de imagen principal
    principal = models.BooleanField(
        default=False,
        help_text="Marca esta imagen como la principal del producto",
        verbose_name="Imagen Principal"
    )

    class Meta:
        verbose_name = "Imagen de Producto"
        verbose_name_plural = "Imágenes de Producto"
        ordering = ['-principal', '-fecha_subida']  # Principal primero, luego por fecha
        indexes = [
            models.Index(fields=['producto', 'principal']),
            models.Index(fields=['fecha_subida']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        principal_text = " (Principal)" if self.principal else ""
        return f"Imagen de {self.producto.nombre} ({self.id}){principal_text}"

    def delete(self, *args, **kwargs):
        """
        Override del método delete para limpieza de archivos.
        
        Elimina el archivo físico de la imagen del sistema de archivos
        antes de eliminar el registro de la base de datos.
        """
        if self.imagen and self.imagen.path and os.path.isfile(self.imagen.path):
            os.remove(self.imagen.path)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Override del método save para lógica de imagen principal.
        
        Si se marca esta imagen como principal, desmarca las demás
        imágenes del mismo producto como principales.
        """
        if self.principal:
            # Desmarcar otras imágenes principales del mismo producto
            ImagenProducto.objects.filter(
                producto=self.producto, 
                principal=True
            ).exclude(pk=self.pk).update(principal=False)
            
        super().save(*args, **kwargs)


class Servicio(models.Model):
    """
    Modelo que representa un servicio ofrecido por el usuario.
    
    Gestiona servicios profesionales, consultoría, o cualquier tipo
    de servicio que no sea un producto físico.
    
    Funcionalidades:
    - Gestión completa de información del servicio
    - Soporte para múltiples imágenes
    - Control de duración estimada
    - Categorización flexible
    - Sistema de activación/desactivación
    - Limpieza automática de archivos
    
    Relaciones:
    - ForeignKey con User (propietario)
    - Relacionado con ImagenServicio (imágenes múltiples)
    - Relacionado con DetallePedido (sistema de pedidos)
    """
    
    # Usuario propietario del servicio
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='servicios',
        help_text="Usuario que creó y gestiona este servicio",
        verbose_name="Propietario"
    )
    
    # Información básica del servicio
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre comercial del servicio",
        verbose_name="Nombre del Servicio"
    )
    
    descripcion = models.TextField(
        help_text="Descripción detallada del servicio, qué incluye y beneficios",
        verbose_name="Descripción"
    )
    
    # Información comercial
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Precio del servicio",
        verbose_name="Precio"
    )
    
    # Información específica de servicios
    duracion = models.CharField(
        max_length=50,
        help_text="Duración estimada del servicio (ej: '2 horas', '1 semana')",
        verbose_name="Duración Estimada"
    )
    
    # Categorización
    categoria = models.CharField(
        max_length=50,
        help_text="Categoría del servicio para organización y filtros",
        verbose_name="Categoría"
    )
    
    # Imagen principal (campo legacy - se mantiene por compatibilidad)
    imagen = models.ImageField(
        upload_to='servicios/', 
        null=True, 
        blank=True,
        help_text="Imagen principal del servicio (opcional)",
        verbose_name="Imagen Principal"
    )
    
    # Metadatos y control
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del servicio",
        verbose_name="Fecha de Creación"
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Determina si el servicio está visible y disponible",
        verbose_name="Servicio Activo"
    )

    # Políticas personalizables de reserva y cancelación
    politicas_reserva = models.JSONField(
        default=dict,
        help_text="Políticas de reserva personalizadas para este servicio",
        verbose_name="Políticas de Reserva"
    )
    
    politicas_cancelacion = models.JSONField(
        default=dict,
        help_text="Políticas de cancelación personalizadas para este servicio",
        verbose_name="Políticas de Cancelación"
    )

    class Meta:
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'activo']),
            models.Index(fields=['categoria']),
            models.Index(fields=['fecha_creacion']),
            models.Index(fields=['precio']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        return f"{self.nombre} - {self.usuario.username}"

    def delete(self, *args, **kwargs):
        """
        Override del método delete para limpieza de archivos.
        
        Elimina todas las imágenes asociadas al servicio antes de
        eliminar el servicio para evitar archivos huérfanos.
        """
        # Elimina todas las imágenes asociadas al servicio
        for img in self.imagenes.all():
            img.delete()
            
        # Eliminar imagen principal si existe
        if self.imagen:
            if self.imagen.path and os.path.isfile(self.imagen.path):
                os.remove(self.imagen.path)
                
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Override del método save para gestión de imagen principal.
        
        Elimina la imagen anterior si se reemplaza para evitar
        acumulación de archivos no utilizados.
        """
        try:
            # Obtener la instancia actual de la base de datos
            this = Servicio.objects.get(pk=self.pk)
            # Si la imagen cambió, eliminar la anterior
            if this.imagen != self.imagen and this.imagen and os.path.isfile(this.imagen.path):
                os.remove(this.imagen.path)
        except Servicio.DoesNotExist:
            # Es un nuevo servicio, no hay imagen anterior
            pass
            
        super().save(*args, **kwargs)

    @property
    def imagen_principal(self):
        """
        Obtiene la URL de la imagen principal del servicio.
        
        Busca primero una imagen marcada como principal en las imágenes
        múltiples, si no encuentra usa la imagen del campo legacy,
        finalmente devuelve la primera imagen disponible.
        
        Returns:
            str|None: URL de la imagen principal o None si no hay imágenes
        """
        # Buscar imagen marcada como principal en imágenes múltiples
        principal = self.imagenes.filter(principal=True).first()
        if principal:
            return principal.imagen.url
            
        # Usar imagen del campo legacy si existe
        if self.imagen:
            return self.imagen.url
            
        # Si no hay principal, usar la primera disponible
        primera = self.imagenes.first()
        if primera:
            return primera.imagen.url
            
        return None
    
    @property
    def total_imagenes(self):
        """
        Cuenta el total de imágenes asociadas al servicio.
        
        Incluye tanto las imágenes múltiples como la imagen principal legacy.
        
        Returns:
            int: Número total de imágenes
        """
        total = self.imagenes.count()
        if self.imagen:
            total += 1
        return total

    def get_politicas_reserva_default(self):
        """Obtiene las políticas de reserva por defecto."""
        return [
            {"icon": "fas fa-calendar-alt", "text": "Reservas con 24 horas de anticipación"},
            {"icon": "fas fa-clock", "text": "Horarios flexibles de lunes a sábado"},
            {"icon": "fas fa-map-marker-alt", "text": "Servicio a domicilio disponible"},
            {"icon": "fas fa-phone", "text": "Confirmación por teléfono o WhatsApp"}
        ]
    
    def get_politicas_cancelacion_default(self):
        """Obtiene las políticas de cancelación por defecto."""
        return [
            {"icon": "fas fa-undo", "text": "Cancelación gratuita hasta 12 horas antes"},
            {"icon": "fas fa-money-bill-wave", "text": "Pago al finalizar el servicio"},
            {"icon": "fas fa-shield-alt", "text": "Garantía de satisfacción"},
            {"icon": "fas fa-tools", "text": "Materiales y herramientas incluidos"}
        ]
    
    def get_politicas_reserva_completas(self):
        """Obtiene las políticas de reserva completas (personalizadas o por defecto)."""
        if self.politicas_reserva:
            return self.politicas_reserva
        return self.get_politicas_reserva_default()
    
    def get_politicas_cancelacion_completas(self):
        """Obtiene las políticas de cancelación completas (personalizadas o por defecto)."""
        if self.politicas_cancelacion:
            return self.politicas_cancelacion
        return self.get_politicas_cancelacion_default()

    def clean(self):
        """Validaciones personalizadas del modelo."""
        super().clean()
        
        if self.precio <= 0:
            raise ValidationError({
                'precio': 'El precio debe ser mayor a cero.'
            })


class ImagenServicio(models.Model):
    """
    Modelo que gestiona las imágenes asociadas a un servicio.
    
    Similar a ImagenProducto pero para servicios. Permite múltiples
    imágenes por servicio con sistema de imagen principal.
    
    Funcionalidades:
    - Múltiples imágenes por servicio
    - Sistema de imagen principal
    - Limpieza automática de archivos
    - Metadatos de subida
    
    Relaciones:
    - ForeignKey con Servicio (imagen pertenece a servicio)
    """
    
    # Servicio al que pertenece la imagen
    servicio = models.ForeignKey(
        Servicio, 
        on_delete=models.CASCADE, 
        related_name='imagenes',
        help_text="Servicio al que pertenece esta imagen",
        verbose_name="Servicio"
    )
    
    # Archivo de imagen
    imagen = models.ImageField(
        upload_to='servicios/', 
        null=False, 
        blank=False,
        help_text="Archivo de imagen del servicio",
        verbose_name="Imagen"
    )
    
    # Metadatos
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de subida de la imagen",
        verbose_name="Fecha de Subida"
    )
    
    # Control de imagen principal
    principal = models.BooleanField(
        default=False,
        help_text="Marca esta imagen como la principal del servicio",
        verbose_name="Imagen Principal"
    )

    class Meta:
        verbose_name = "Imagen de Servicio"
        verbose_name_plural = "Imágenes de Servicio"
        ordering = ['-principal', '-fecha_subida']
        indexes = [
            models.Index(fields=['servicio', 'principal']),
            models.Index(fields=['fecha_subida']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        principal_text = " (Principal)" if self.principal else ""
        return f"Imagen de {self.servicio.nombre} ({self.id}){principal_text}"

    def delete(self, *args, **kwargs):
        """Override del método delete para limpieza de archivos."""
        if self.imagen and self.imagen.path and os.path.isfile(self.imagen.path):
            os.remove(self.imagen.path)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """Override del método save para lógica de imagen principal."""
        if self.principal:
            # Desmarcar otras imágenes principales del mismo servicio
            ImagenServicio.objects.filter(
                servicio=self.servicio, 
                principal=True
            ).exclude(pk=self.pk).update(principal=False)
            
        super().save(*args, **kwargs)


class Pedido(models.Model):
    """
    Modelo que representa un pedido realizado por un usuario.
    
    Gestiona el sistema de pedidos/órdenes de la plataforma,
    permitiendo a los usuarios solicitar productos y servicios.
    
    Funcionalidades:
    - Estados de pedido (pendiente, en proceso, completado, cancelado)
    - Cálculo automático de totales
    - Historial de pedidos por usuario
    - Notas y observaciones
    - Integración con sistema de productos/servicios
    
    Relaciones:
    - ForeignKey con User (cliente que realiza el pedido)
    - Relacionado con DetallePedido (productos/servicios del pedido)
    """
    
    # Estados posibles del pedido
    ESTADO_PEDIDO = [
        ('pendiente', 'Pendiente'),     # Pedido recién creado, esperando procesamiento
        ('en_proceso', 'En Proceso'),   # Pedido siendo preparado/ejecutado
        ('completado', 'Completado'),   # Pedido finalizado exitosamente
        ('cancelado', 'Cancelado'),     # Pedido cancelado por cliente o proveedor
    ]
    
    # Usuario que realiza el pedido
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='pedidos',
        help_text="Usuario que realizó el pedido",
        verbose_name="Cliente"
    )
    
    # Empresa que recibe el pedido
    empresa = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pedidos_recibidos',
        help_text="Empresa que debe procesar este pedido",
        verbose_name="Empresa Destinataria"
    )
    
    # Información temporal del pedido
    fecha_pedido = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del pedido",
        verbose_name="Fecha del Pedido"
    )
    
    # Estado actual del pedido
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_PEDIDO, 
        default='pendiente',
        help_text="Estado actual del procesamiento del pedido",
        verbose_name="Estado"
    )
    
    # Información financiera
    total = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto total del pedido",
        verbose_name="Total"
    )
    
    # Información adicional
    notas = models.TextField(
        blank=True,
        help_text="Notas adicionales o instrucciones especiales",
        verbose_name="Notas"
    )

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_pedido']  # Más recientes primero
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['empresa', 'estado']),  # Para empresas viendo sus pedidos
            models.Index(fields=['fecha_pedido']),
            models.Index(fields=['estado']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        return f"Pedido #{self.id} - {self.usuario.username} → {self.empresa_info} ({self.get_estado_display()})"
    
    @property
    def empresa_info(self):
        """
        Obtiene información legible de la empresa destinataria.
        
        Returns:
            str: Nombre de la empresa o username si no tiene perfil
        """
        try:
            perfil = self.empresa.userprofile
            return perfil.empresa if perfil.empresa else self.empresa.username
        except:
            return self.empresa.username
    
    @property
    def esta_activo(self):
        """
        Determina si el pedido está en un estado activo.
        
        Returns:
            bool: True si el pedido está pendiente o en proceso
        """
        return self.estado in ['pendiente', 'en_proceso']
    
    @property
    def puede_cancelarse(self):
        """
        Determina si el pedido puede ser cancelado.
        
        Returns:
            bool: True si el pedido puede cancelarse
        """
        return self.estado in ['pendiente', 'en_proceso']
    
    @property
    def total_items(self):
        """
        Calcula el total de items en el pedido.
        
        Returns:
            int: Número total de items (suma de cantidades)
        """
        return sum(detalle.cantidad for detalle in self.detalles.all())

    def calcular_total(self):
        """
        Calcula y actualiza el total del pedido basado en los detalles.
        
        Este método recalcula el total sumando todos los subtotales
        de los detalles del pedido.
        """
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save(update_fields=['total'])


class DetallePedido(models.Model):
    """
    Modelo que representa el detalle de cada producto o servicio en un pedido.
    
    Cada línea del pedido se representa como un DetallePedido, conteniendo
    la información específica de cantidad, precios y subtotales.
    
    Funcionalidades:
    - Referencia a producto O servicio (no ambos)
    - Cálculo automático de subtotales
    - Preservación de precios históricos
    - Validación de cantidades
    
    Relaciones:
    - ForeignKey con Pedido (detalle pertenece a pedido)
    - ForeignKey opcional con Producto
    - ForeignKey opcional con Servicio
    """
    
    # Pedido al que pertenece este detalle
    pedido = models.ForeignKey(
        Pedido, 
        on_delete=models.CASCADE,
        related_name='detalles',
        help_text="Pedido al que pertenece este detalle",
        verbose_name="Pedido"
    )
    
    # Producto solicitado (opcional - puede ser producto O servicio)
    producto = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Producto solicitado (si aplica)",
        verbose_name="Producto"
    )
    
    # Servicio solicitado (opcional - puede ser producto O servicio)
    servicio = models.ForeignKey(
        Servicio, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Servicio solicitado (si aplica)",
        verbose_name="Servicio"
    )
    
    # Información de cantidad y precios
    cantidad = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Cantidad solicitada",
        verbose_name="Cantidad"
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Precio unitario al momento del pedido",
        verbose_name="Precio Unitario"
    )
    
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Subtotal de esta línea (cantidad × precio unitario)",
        verbose_name="Subtotal"
    )

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"
        indexes = [
            models.Index(fields=['pedido']),
            models.Index(fields=['producto']),
            models.Index(fields=['servicio']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        item_name = self.producto.nombre if self.producto else self.servicio.nombre
        return f"Detalle de Pedido #{self.pedido.id} - {item_name}"
    
    @property
    def item_name(self):
        """
        Obtiene el nombre del item (producto o servicio).
        
        Returns:
            str: Nombre del producto o servicio
        """
        if self.producto:
            return self.producto.nombre
        elif self.servicio:
            return self.servicio.nombre
        return "Item no especificado"
    
    @property
    def item_type(self):
        """
        Determina el tipo de item (producto o servicio).
        
        Returns:
            str: 'producto', 'servicio' o 'desconocido'
        """
        if self.producto:
            return 'producto'
        elif self.servicio:
            return 'servicio'
        return 'desconocido'

    def clean(self):
        """Validaciones personalizadas del modelo."""
        super().clean()
        
        # Validar que se especifique producto O servicio, no ambos ni ninguno
        if not self.producto and not self.servicio:
            raise ValidationError(
                'Debe especificar un producto o un servicio.'
            )
        
        if self.producto and self.servicio:
            raise ValidationError(
                'No puede especificar tanto producto como servicio en el mismo detalle.'
            )
        
        # Validar cantidad positiva
        if self.cantidad <= 0:
            raise ValidationError({
                'cantidad': 'La cantidad debe ser mayor a cero.'
            })

    def save(self, *args, **kwargs):
        """
        Override del método save para cálculo automático de subtotal.
        
        Calcula el subtotal automáticamente basado en cantidad y precio unitario.
        """
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        
        # Ejecutar validaciones
        self.full_clean()
        
        super().save(*args, **kwargs)
        
        # Actualizar total del pedido padre
        self.pedido.calcular_total()


class MensajePedido(models.Model):
    """
    Modelo para mensajería entre usuarios y empresas sobre pedidos específicos.
    
    Permite comunicación bidireccional entre cliente y empresa para resolver
    dudas, problemas o actualizaciones sobre un pedido.
    
    Características:
    - Mensajes asociados a pedidos específicos
    - Historial completo de conversaciones
    - Soporte para archivos adjuntos (opcional)
    - Marcado de mensajes leídos/no leídos
    - Timestamps automáticos
    """
    
    # Pedido al que pertenece el mensaje
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='mensajes',
        help_text="Pedido sobre el que se está comunicando",
        verbose_name="Pedido"
    )
    
    # Usuario que envía el mensaje (puede ser cliente o empresa)
    remitente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados',
        help_text="Usuario que envía el mensaje",
        verbose_name="Remitente"
    )
    
    # Contenido del mensaje
    mensaje = models.TextField(
        blank=True,
        help_text="Contenido del mensaje (opcional si hay archivo adjunto)",
        verbose_name="Mensaje"
    )
    
    # Archivo adjunto (opcional)
    archivo_adjunto = models.FileField(
        upload_to='mensajes_pedidos/%Y/%m/%d/',
        blank=True,
        null=True,
        help_text="Archivo adjunto al mensaje (imagen, PDF, etc.)",
        verbose_name="Archivo Adjunto"
    )
    
    # Estado de lectura
    leido = models.BooleanField(
        default=False,
        help_text="Indica si el mensaje ha sido leído por el destinatario",
        verbose_name="Leído"
    )
    
    # Fecha de creación
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de envío del mensaje",
        verbose_name="Fecha de Envío"
    )
    
    class Meta:
        verbose_name = "Mensaje de Pedido"
        verbose_name_plural = "Mensajes de Pedidos"
        ordering = ['fecha_creacion']  # Más antiguos primero
        indexes = [
            models.Index(fields=['pedido', 'fecha_creacion']),
            models.Index(fields=['remitente', 'leido']),
        ]
    
    def __str__(self):
        """Representación string del modelo."""
        return f"Mensaje #{self.id} - Pedido #{self.pedido.id} - {self.remitente.username}"
    
    @property
    def destinatario(self):
        """
        Obtiene el destinatario del mensaje (el otro usuario en la conversación).
        
        Returns:
            User: El usuario destinatario (empresa si remitente es cliente, y viceversa)
        """
        if self.remitente == self.pedido.usuario:
            return self.pedido.empresa
        else:
            return self.pedido.usuario
    
    @property
    def es_del_cliente(self):
        """
        Indica si el mensaje fue enviado por el cliente.
        
        Returns:
            bool: True si el remitente es el cliente del pedido
        """
        return self.remitente == self.pedido.usuario
    
    @property
    def es_de_la_empresa(self):
        """
        Indica si el mensaje fue enviado por la empresa.
        
        Returns:
            bool: True si el remitente es la empresa del pedido
        """
        return self.remitente == self.pedido.empresa
    
    def marcar_como_leido(self):
        """
        Marca el mensaje como leído.
        """
        if not self.leido:
            self.leido = True
            self.save(update_fields=['leido'])
    
    def delete(self, *args, **kwargs):
        """
        Override del método delete para eliminar archivos adjuntos.
        """
        if self.archivo_adjunto:
            if os.path.isfile(self.archivo_adjunto.path):
                os.remove(self.archivo_adjunto.path)
        super().delete(*args, **kwargs)