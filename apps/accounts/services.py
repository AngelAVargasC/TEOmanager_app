"""
Servicios para la lógica de negocio de la aplicación accounts.

Este módulo contiene las clases de servicio que encapsulan la lógica de negocio
relacionada con usuarios, perfiles y autenticación. Siguiendo el patrón de
arquitectura por capas, estos servicios actúan como intermediarios entre
las vistas (controllers) y los modelos (data layer).

Beneficios de usar servicios:
- Separación de responsabilidades
- Reutilización de código
- Facilita el testing
- Centraliza la lógica de negocio
- Hace las vistas más limpias y enfocadas
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from datetime import datetime, timedelta
import logging
import os
from django.core.cache import cache
from django.db.models import Count, Q, Avg, Sum
from django.contrib.auth.models import User

from .models import PerfilUsuario, Suscripcion
from apps.productservice.models import Producto, Servicio, Pedido, ImagenProducto, ImagenServicio, DetallePedido, MensajePedido

# Configurar logger para este módulo
logger = logging.getLogger(__name__)


class UserService:
    """
    Servicio para operaciones relacionadas con usuarios y perfiles.
    
    Centraliza toda la lógica de negocio relacionada con la gestión
    de usuarios, creación de perfiles y operaciones de autenticación.
    """
    
    @staticmethod
    @transaction.atomic
    def create_user_profile(user, tipo_cuenta, empresa='', telefono='', direccion='', **kwargs):
        """
        Crea un perfil de usuario con validaciones de negocio.
        
        Args:
            user (User): Usuario de Django
            tipo_cuenta (str): 'empresa' o 'usuario'
            empresa (str): Nombre de la empresa (requerido para empresas)
            telefono (str): Teléfono de contacto
            direccion (str): Dirección
            **kwargs: Campos adicionales del perfil
            
        Returns:
            PerfilUsuario: Perfil creado
            
        Raises:
            ValueError: Si los datos no son válidos según las reglas de negocio
        """
        # Validaciones de negocio
        if tipo_cuenta == 'empresa' and not empresa:
            raise ValueError("El nombre de la empresa es requerido para cuentas empresariales")
        
        if not telefono:
            raise ValueError("El teléfono es requerido")
            
        if not direccion:
            raise ValueError("La dirección es requerida")
        
        try:
            # Crear perfil con transacción atómica
            perfil = PerfilUsuario.objects.create(
                usuario=user,
                tipo_cuenta=tipo_cuenta,
                empresa=empresa if tipo_cuenta == 'empresa' else '',
                telefono=telefono,
                direccion=direccion,
                **kwargs
            )
            
            logger.info(f"Perfil creado exitosamente para usuario {user.username}")
            
            # Enviar email de bienvenida de forma asíncrona
            UserService.send_welcome_email(user)
            
            return perfil
            
        except Exception as e:
            logger.error(f"Error creando perfil para usuario {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def send_welcome_email(user):
        """
        Envía email de bienvenida HTML profesional al usuario.
        
        Args:
            user (User): Usuario al que enviar el email
            
        Returns:
            bool: True si el email se envió correctamente
        """
        try:
            # Intentar obtener el perfil (puede no existir aún si se llama antes de crear el perfil)
            perfil = None
            is_empresa = False
            empresa = ''
            try:
                perfil = user.userprofile
                is_empresa = perfil.is_empresa
                empresa = perfil.empresa if is_empresa else ''
            except PerfilUsuario.DoesNotExist:
                pass
            
            # Personalizar asunto según tipo de cuenta
            if is_empresa:
                subject = 'Bienvenido a TEOmanager - Tu ERP Empresarial'
            else:
                subject = 'Bienvenido a TEOmanager'
            
            # Obtener URL de login
            # Intentar obtener el dominio del sitio, si no usar configuración por defecto
            try:
                from django.contrib.sites.models import Site
                current_site = Site.objects.get_current()
                domain = current_site.domain
                # Asegurar que tenga protocolo
                if not domain.startswith('http'):
                    protocol = 'https' if not settings.DEBUG else 'http'
                    login_url = f"{protocol}://{domain}{reverse('login')}"
                else:
                    login_url = f"{domain}{reverse('login')}"
            except:
                # Fallback: usar configuración de settings o localhost
                if hasattr(settings, 'SITE_URL'):
                    base_url = settings.SITE_URL
                else:
                    base_url = 'http://localhost:5490' if settings.DEBUG else 'https://teomanager.com'
                login_url = f"{base_url}{reverse('login')}"
            
            # Renderizar template HTML
            html_message = render_to_string('emails/welcome_email.html', {
                'user_first_name': user.first_name,
                'user_username': user.username,
                'is_empresa': is_empresa,
                'empresa': empresa,
                'login_url': login_url,
            })
            
            # Crear versión de texto plano como fallback
            plain_message = f"""Hola {user.first_name or user.username},

¡Bienvenido a TEOmanager!

Tu cuenta {'empresarial' if is_empresa else ''} ha sido creada exitosamente.
"""
            if is_empresa:
                plain_message += f"""
Ahora puedes:
- Gestionar tus productos y servicios
- Crear tu landing page personalizada
- Administrar pedidos y clientes
- Acceder a reportes y análisis

Empresa: {empresa}
"""
            else:
                plain_message += "Explora nuestros productos y servicios disponibles."
            
            plain_message += f"""

Inicia sesión aquí: {login_url}

Saludos,
El equipo de TEOmanager
"""
            
            # Enviar email con HTML y texto plano
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=True)
            
            logger.info(f"Email de bienvenida HTML enviado a {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email de bienvenida a {user.email}: {str(e)}")
            # No lanzar excepción para que el registro no falle si hay problema con el email
            return False
    
    @staticmethod
    def update_user_profile(user, **kwargs):
        """
        Actualiza el perfil de usuario con validaciones.
        
        Args:
            user (User): Usuario a actualizar
            **kwargs: Campos a actualizar
            
        Returns:
            PerfilUsuario: Perfil actualizado
        """
        try:
            perfil = user.userprofile
            
            # Validaciones específicas según tipo de cuenta
            if 'tipo_cuenta' in kwargs:
                if kwargs['tipo_cuenta'] == 'empresa' and not kwargs.get('empresa'):
                    raise ValueError("El nombre de la empresa es requerido para cuentas empresariales")
            
            # Actualizar campos
            for field, value in kwargs.items():
                if hasattr(perfil, field):
                    setattr(perfil, field, value)
            
            perfil.save()
            logger.info(f"Perfil actualizado para usuario {user.username}")
            
            return perfil
            
        except Exception as e:
            logger.error(f"Error actualizando perfil de {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def get_user_stats(user):
        """
        Obtiene estadísticas del usuario para el dashboard.
        
        Args:
            user (User): Usuario
            
        Returns:
            dict: Estadísticas del usuario
        """
        try:
            perfil = user.userprofile
            
            stats = {
                'tipo_cuenta': perfil.get_tipo_cuenta_display(),
                'fecha_registro': perfil.fecha_registro,
                'suscripcion_activa': perfil.suscripcion_activa,
                'es_admin': perfil.is_admin,
                'total_productos': user.productos.filter(activo=True).count(),
                'total_servicios': user.servicios.filter(activo=True).count(),
                'total_pedidos': user.pedidos.count(),
                'landing_pages': user.landing_pages.count(),
            }
            
            # Estadísticas adicionales para empresas
            if perfil.is_empresa:
                stats.update({
                    'empresa': perfil.empresa,
                    'estado_suscripcion': perfil.get_estado_suscripcion_display(),
                    'fecha_vencimiento': perfil.fecha_vencimiento,
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de {user.username}: {str(e)}")
            return {}
    
    @staticmethod
    @transaction.atomic
    def delete_user_completely(user):
        """
        Elimina completamente un usuario y todos sus datos relacionados.
        
        Esta función elimina:
        - Perfil de usuario
        - Suscripciones
        - Landing pages (y sus imágenes hero)
        - Productos (y todas sus imágenes)
        - Servicios (y todas sus imágenes)
        - Pedidos (y sus detalles y mensajes)
        - Mensajes de pedidos enviados
        - Archivos físicos asociados
        
        Args:
            user (User): Usuario a eliminar
            
        Returns:
            dict: Resumen de lo eliminado
            
        Raises:
            ValueError: Si se intenta eliminar un superusuario
        """
        # Prevenir eliminación de superusuarios
        if user.is_superuser:
            raise ValueError("No se puede eliminar un superusuario desde esta función")
        
        username = user.username
        deleted_summary = {
            'productos': 0,
            'servicios': 0,
            'pedidos': 0,
            'landing_pages': 0,
            'suscripciones': 0,
            'imagenes_productos': 0,
            'imagenes_servicios': 0,
            'archivos_eliminados': 0
        }
        
        try:
            # 1. Eliminar imágenes de productos y archivos físicos
            productos = Producto.objects.filter(usuario=user)
            for producto in productos:
                # Eliminar todas las imágenes del producto
                imagenes = ImagenProducto.objects.filter(producto=producto)
                for img in imagenes:
                    if img.imagen and img.imagen.path and os.path.isfile(img.imagen.path):
                        try:
                            os.remove(img.imagen.path)
                            deleted_summary['archivos_eliminados'] += 1
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar imagen de producto {img.id}: {e}")
                    deleted_summary['imagenes_productos'] += 1
                
                deleted_summary['productos'] += 1
            
            # 2. Eliminar imágenes de servicios y archivos físicos
            servicios = Servicio.objects.filter(usuario=user)
            for servicio in servicios:
                # Eliminar todas las imágenes del servicio
                imagenes = ImagenServicio.objects.filter(servicio=servicio)
                for img in imagenes:
                    if img.imagen and img.imagen.path and os.path.isfile(img.imagen.path):
                        try:
                            os.remove(img.imagen.path)
                            deleted_summary['archivos_eliminados'] += 1
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar imagen de servicio {img.id}: {e}")
                    deleted_summary['imagenes_servicios'] += 1
                
                # Eliminar imagen principal del servicio si existe
                if servicio.imagen and servicio.imagen.path and os.path.isfile(servicio.imagen.path):
                    try:
                        os.remove(servicio.imagen.path)
                        deleted_summary['archivos_eliminados'] += 1
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar imagen principal de servicio {servicio.id}: {e}")
                
                deleted_summary['servicios'] += 1
            
            # 3. Eliminar pedidos (esto eliminará automáticamente detalles y mensajes por CASCADE)
            # Primero eliminar archivos adjuntos de mensajes
            pedidos = Pedido.objects.filter(Q(usuario=user) | Q(empresa=user))
            for pedido in pedidos:
                # Eliminar archivos adjuntos de mensajes
                mensajes = MensajePedido.objects.filter(pedido=pedido)
                for mensaje in mensajes:
                    if mensaje.archivo_adjunto and mensaje.archivo_adjunto.path and os.path.isfile(mensaje.archivo_adjunto.path):
                        try:
                            os.remove(mensaje.archivo_adjunto.path)
                            deleted_summary['archivos_eliminados'] += 1
                        except Exception as e:
                            logger.warning(f"No se pudo eliminar archivo adjunto de mensaje {mensaje.id}: {e}")
                
                deleted_summary['pedidos'] += 1
            
            # 4. Eliminar landing pages y sus imágenes hero
            from apps.webpages.models import LandingPage
            landing_pages = LandingPage.objects.filter(usuario=user)
            for landing in landing_pages:
                if landing.hero_image_file and landing.hero_image_file.path and os.path.isfile(landing.hero_image_file.path):
                    try:
                        os.remove(landing.hero_image_file.path)
                        deleted_summary['archivos_eliminados'] += 1
                    except Exception as e:
                        logger.warning(f"No se pudo eliminar imagen hero de landing page {landing.id}: {e}")
                
                deleted_summary['landing_pages'] += 1
            
            # 5. Eliminar suscripciones
            suscripciones = Suscripcion.objects.filter(usuario=user)
            deleted_summary['suscripciones'] = suscripciones.count()
            
            # 6. Eliminar perfil de usuario (esto eliminará automáticamente por CASCADE)
            # El perfil se eliminará cuando se elimine el User
            
            # 7. Finalmente, eliminar el usuario (esto eliminará todo lo demás por CASCADE)
            user.delete()
            
            logger.info(f"Usuario {username} eliminado completamente. Resumen: {deleted_summary}")
            
            return deleted_summary
            
        except Exception as e:
            logger.error(f"Error eliminando usuario {username}: {str(e)}")
            raise


class SuscripcionService:
    """
    Servicio para la gestión de suscripciones y planes.
    
    Maneja toda la lógica relacionada con suscripciones, pagos,
    renovaciones y control de acceso basado en planes.
    """
    
    # Configuración de planes
    PLANES_CONFIG = {
        'basico': {
            'precio': 0.00,
            'duracion_dias': 30,
            'max_productos': 10,
            'max_servicios': 5,
            'landing_pages': 1,
            'soporte': 'email',
        },
        'premium': {
            'precio': 29.99,
            'duracion_dias': 30,
            'max_productos': 100,
            'max_servicios': 50,
            'landing_pages': 5,
            'soporte': 'prioritario',
        },
        'empresarial': {
            'precio': 99.99,
            'duracion_dias': 30,
            'max_productos': -1,  # Ilimitado
            'max_servicios': -1,  # Ilimitado
            'landing_pages': -1,  # Ilimitado
            'soporte': '24/7',
        }
    }
    
    @staticmethod
    @transaction.atomic
    def create_suscripcion(user, plan, precio=None):
        """
        Crea una nueva suscripción para el usuario.
        
        Args:
            user (User): Usuario
            plan (str): Tipo de plan
            precio (Decimal, optional): Precio personalizado
            
        Returns:
            Suscripcion: Suscripción creada
        """
        if plan not in SuscripcionService.PLANES_CONFIG:
            raise ValueError(f"Plan '{plan}' no válido")
        
        config = SuscripcionService.PLANES_CONFIG[plan]
        precio_final = precio or config['precio']
        
        # Desactivar suscripciones anteriores
        Suscripcion.objects.filter(usuario=user, activa=True).update(activa=False)
        
        # Crear nueva suscripción
        fecha_vencimiento = timezone.now() + timedelta(days=config['duracion_dias'])
        
        suscripcion = Suscripcion.objects.create(
            usuario=user,
            plan=plan,
            precio=precio_final,
            fecha_vencimiento=fecha_vencimiento,
            activa=True
        )
        
        # Actualizar perfil del usuario
        perfil = user.userprofile
        perfil.estado_suscripcion = 'activa'
        perfil.fecha_vencimiento = fecha_vencimiento
        perfil.save()
        
        logger.info(f"Suscripción {plan} creada para usuario {user.username}")
        
        return suscripcion
    
    @staticmethod
    def check_plan_limits(user, resource_type):
        """
        Verifica si el usuario puede crear más recursos según su plan.
        
        Args:
            user (User): Usuario
            resource_type (str): 'productos', 'servicios', 'landing_pages'
            
        Returns:
            dict: {'allowed': bool, 'current': int, 'limit': int, 'message': str}
        """
        try:
            perfil = user.userprofile
            suscripcion = user.suscripciones.filter(activa=True).first()
            
            if not suscripcion:
                plan = 'basico'  # Plan por defecto
            else:
                plan = suscripcion.plan
            
            config = SuscripcionService.PLANES_CONFIG.get(plan, SuscripcionService.PLANES_CONFIG['basico'])
            
            # Mapear tipos de recursos
            resource_mapping = {
                'productos': ('max_productos', user.productos.filter(activo=True).count()),
                'servicios': ('max_servicios', user.servicios.filter(activo=True).count()),
                'landing_pages': ('landing_pages', user.landing_pages.count()),
            }
            
            if resource_type not in resource_mapping:
                return {'allowed': False, 'message': 'Tipo de recurso no válido'}
            
            limit_key, current_count = resource_mapping[resource_type]
            limit = config[limit_key]
            
            # -1 significa ilimitado
            if limit == -1:
                return {
                    'allowed': True,
                    'current': current_count,
                    'limit': 'Ilimitado',
                    'message': 'Sin límites en tu plan actual'
                }
            
            allowed = current_count < limit
            message = f"Tienes {current_count} de {limit} {resource_type} permitidos"
            
            if not allowed:
                message = f"Has alcanzado el límite de {limit} {resource_type}. Considera actualizar tu plan."
            
            return {
                'allowed': allowed,
                'current': current_count,
                'limit': limit,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Error verificando límites de plan para {user.username}: {str(e)}")
            return {'allowed': False, 'message': 'Error verificando límites'}
    
    @staticmethod
    def get_plan_features(plan):
        """
        Obtiene las características de un plan específico.
        
        Args:
            plan (str): Nombre del plan
            
        Returns:
            dict: Características del plan
        """
        return SuscripcionService.PLANES_CONFIG.get(plan, {})


class NotificationService:
    """
    Servicio para el manejo de notificaciones y comunicaciones.
    
    Centraliza el envío de emails, notificaciones push y otros
    tipos de comunicación con los usuarios.
    """
    
    @staticmethod
    def send_subscription_reminder(user, days_remaining):
        """
        Envía recordatorio de vencimiento de suscripción.
        
        Args:
            user (User): Usuario
            days_remaining (int): Días restantes
        """
        try:
            subject = f'Tu suscripción vence en {days_remaining} días'
            message = f'''
            Hola {user.first_name or user.username},
            
            Tu suscripción vencerá en {days_remaining} días.
            
            Para continuar disfrutando de todos los beneficios,
            renueva tu suscripción antes del vencimiento.
            
            Saludos,
            El equipo de Admin Panel
            '''
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            
            logger.info(f"Recordatorio de suscripción enviado a {user.email}")
            
        except Exception as e:
            logger.error(f"Error enviando recordatorio a {user.email}: {str(e)}")
    
    @staticmethod
    def send_plan_limit_notification(user, resource_type):
        """
        Envía notificación cuando el usuario se acerca a los límites de su plan.
        
        Args:
            user (User): Usuario
            resource_type (str): Tipo de recurso
        """
        try:
            limits = SuscripcionService.check_plan_limits(user, resource_type)
            
            if limits['current'] >= limits['limit'] * 0.8:  # 80% del límite
                subject = f'Te acercas al límite de {resource_type}'
                message = f'''
                Hola {user.first_name or user.username},
                
                Has usado {limits['current']} de {limits['limit']} {resource_type} permitidos en tu plan actual.
                
                Considera actualizar tu plan para obtener más recursos.
                
                Saludos,
                El equipo de Admin Panel
                '''
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
                
                logger.info(f"Notificación de límite enviada a {user.email}")
                
        except Exception as e:
            logger.error(f"Error enviando notificación de límite a {user.email}: {str(e)}")


class DashboardService:
    """Servicio para manejar datos del dashboard con caché optimizado."""
    
    @staticmethod
    def get_admin_metrics(force_refresh=False):
        """
        Obtiene métricas de administración con caché.
        
        Args:
            force_refresh (bool): Forzar actualización del caché
            
        Returns:
            dict: Diccionario con todas las métricas del admin
        """
        cache_key = 'admin_dashboard_metrics'
        
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info("Métricas de admin obtenidas desde caché")
                return cached_data
        
        try:
            # Métricas de usuarios con una sola consulta optimizada
            user_stats = User.objects.select_related('userprofile').aggregate(
                total_users=Count('id'),
                active_users=Count('id', filter=Q(is_active=True)),
                total_companies=Count('id', filter=Q(userprofile__tipo_cuenta='empresa')),
                total_admins=Count('id', filter=Q(userprofile__permisos='Administrador'))
            )
            
            # Métricas de productos y servicios
            product_stats = Producto.objects.aggregate(
                total_products=Count('id'),
                active_products=Count('id', filter=Q(activo=True)),
                avg_price=Avg('precio')
            )
            
            service_stats = Servicio.objects.aggregate(
                total_services=Count('id'),
                active_services=Count('id', filter=Q(activo=True)),
                avg_price=Avg('precio')
            )
            
            # Métricas de pedidos
            order_stats = Pedido.objects.aggregate(
                total_orders=Count('id'),
                total_revenue=Sum('total')
            )
            
            # Consolidar todas las métricas
            metrics = {
                # Usuarios
                'total_users': user_stats['total_users'] or 0,
                'active_users': user_stats['active_users'] or 0,
                'inactive_users': (user_stats['total_users'] or 0) - (user_stats['active_users'] or 0),
                'total_companies': user_stats['total_companies'] or 0,
                'total_admins': user_stats['total_admins'] or 0,
                
                # Productos
                'total_products': product_stats['total_products'] or 0,
                'active_products': product_stats['active_products'] or 0,
                'avg_product_price': product_stats['avg_price'] or 0,
                
                # Servicios
                'total_services': service_stats['total_services'] or 0,
                'active_services': service_stats['active_services'] or 0,
                'avg_service_price': service_stats['avg_price'] or 0,
                
                # Pedidos
                'total_orders': order_stats['total_orders'] or 0,
                'total_revenue': order_stats['total_revenue'] or 0,
                
                # Metadatos
                'last_updated': datetime.now().isoformat(),
                'cache_version': '1.0'
            }
            
            # Guardar en caché por 5 minutos
            cache.set(cache_key, metrics, 300)
            logger.info("Métricas de admin calculadas y guardadas en caché")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error al obtener métricas de admin: {e}")
            # Retornar métricas por defecto en caso de error
            return {
                'total_users': 0, 'active_users': 0, 'inactive_users': 0,
                'total_companies': 0, 'total_admins': 0, 'total_products': 0,
                'active_products': 0, 'total_services': 0, 'active_services': 0,
                'total_orders': 0, 'total_revenue': 0, 'avg_product_price': 0,
                'avg_service_price': 0, 'last_updated': datetime.now().isoformat(),
                'cache_version': '1.0'
            }
    
    @staticmethod
    def get_company_dashboard_data(user, force_refresh=False):
        """
        Obtiene datos optimizados del dashboard para empresas.
        
        Args:
            user: Usuario de la empresa
            force_refresh (bool): Forzar actualización
            
        Returns:
            dict: Datos del dashboard de la empresa
        """
        cache_key = f'company_dashboard_{user.id}'
        
        if not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Dashboard de empresa {user.id} obtenido desde caché")
                return cached_data
        
        try:
            # Consultas optimizadas para productos
            productos_query = Producto.objects.filter(usuario=user).only(
                'id', 'nombre', 'precio', 'categoria', 'activo', 'fecha_creacion'
            )
            
            productos_stats = productos_query.aggregate(
                total=Count('id'),
                activos=Count('id', filter=Q(activo=True)),
                inactivos=Count('id', filter=Q(activo=False)),
                valor_total=Sum('precio', filter=Q(activo=True))
            )
            
            # Consultas optimizadas para servicios
            servicios_query = Servicio.objects.filter(usuario=user).only(
                'id', 'nombre', 'precio', 'categoria', 'activo', 'fecha_creacion'
            )
            
            servicios_stats = servicios_query.aggregate(
                total=Count('id'),
                activos=Count('id', filter=Q(activo=True)),
                inactivos=Count('id', filter=Q(activo=False)),
                valor_total=Sum('precio', filter=Q(activo=True))
            )
            
            # Pedidos recientes optimizados
            pedidos_recientes = Pedido.objects.filter(usuario=user).only(
                'id', 'fecha_pedido', 'estado', 'total'
            ).order_by('-fecha_pedido')[:5]
            
            pedidos_stats = Pedido.objects.filter(usuario=user).aggregate(
                total_pedidos=Count('id'),
                ingresos_totales=Sum('total')
            )
            
            # Productos y servicios recientes (solo los necesarios para mostrar)
            productos_recientes = productos_query.order_by('-fecha_creacion')[:10]
            servicios_recientes = servicios_query.order_by('-fecha_creacion')[:10]
            
            dashboard_data = {
                # Estadísticas de productos
                'productos_count': productos_stats['total'] or 0,
                'productos_activos': productos_stats['activos'] or 0,
                'productos_inactivos': productos_stats['inactivos'] or 0,
                'productos_valor_total': productos_stats['valor_total'] or 0,
                
                # Estadísticas de servicios
                'servicios_count': servicios_stats['total'] or 0,
                'servicios_activos': servicios_stats['activos'] or 0,
                'servicios_inactivos': servicios_stats['inactivos'] or 0,
                'servicios_valor_total': servicios_stats['valor_total'] or 0,
                
                # Estadísticas de pedidos
                'pedidos_count': pedidos_stats['total_pedidos'] or 0,
                'ingresos_totales': pedidos_stats['ingresos_totales'] or 0,
                
                # Datos para mostrar en el dashboard
                'productos_recientes': list(productos_recientes),
                'servicios_recientes': list(servicios_recientes),
                'pedidos_recientes': list(pedidos_recientes),
                
                # Metadatos
                'last_updated': datetime.now().isoformat(),
                'user_id': user.id
            }
            
            # Guardar en caché por 2 minutos (datos más dinámicos)
            cache.set(cache_key, dashboard_data, 120)
            logger.info(f"Dashboard de empresa {user.id} calculado y guardado en caché")
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error al obtener dashboard de empresa {user.id}: {e}")
            return {
                'productos_count': 0, 'productos_activos': 0, 'productos_inactivos': 0,
                'servicios_count': 0, 'servicios_activos': 0, 'servicios_inactivos': 0,
                'pedidos_count': 0, 'ingresos_totales': 0, 'productos_valor_total': 0,
                'servicios_valor_total': 0, 'productos_recientes': [],
                'servicios_recientes': [], 'pedidos_recientes': [],
                'last_updated': datetime.now().isoformat(), 'user_id': user.id
            }
    
    @staticmethod
    def clear_dashboard_cache(user_id=None):
        """
        Limpia el caché del dashboard.
        
        Args:
            user_id: ID del usuario (opcional, si se especifica solo limpia ese usuario)
        """
        if user_id:
            cache.delete(f'company_dashboard_{user_id}')
            logger.info(f"Caché del dashboard de empresa {user_id} limpiado")
        else:
            cache.delete('admin_dashboard_metrics')
            # También limpiar caché de categorías
            cache.delete('product_categories')
            logger.info("Caché de métricas de admin limpiado")
    
    @staticmethod
    def get_system_health():
        """
        Obtiene información sobre la salud del sistema.
        
        Returns:
            dict: Estado del sistema
        """
        try:
            # Verificar conectividad de base de datos
            db_status = "online"
            User.objects.count()  # Test query
            
            # Verificar caché
            cache_status = "online"
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') != 'ok':
                cache_status = "warning"
            
            return {
                'database': db_status,
                'cache': cache_status,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en health check: {e}")
            return {
                'database': "error",
                'cache': "error", 
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }


class MetricsService:
    """Servicio para métricas y analytics avanzados."""
    
    @staticmethod
    def get_user_activity_trends(days=30):
        """Obtiene tendencias de actividad de usuarios."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Implementar lógica de tendencias
        # Por ahora retorna datos mock
        return {
            'new_users_trend': '+12%',
            'product_creation_trend': '+8%', 
            'service_creation_trend': '+15%',
            'order_trend': '+5%'
        } 