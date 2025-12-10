"""
Modelos para la gestión de usuarios y perfiles en el sistema ERP.

Este módulo contiene los modelos relacionados con:
- Perfiles extendidos de usuarios (PerfilUsuario)
- Sistema de suscripciones (Suscripcion)

Arquitectura MVT: Estos modelos representan la capa de datos (Model) 
para la funcionalidad de cuentas de usuario.

NOTA: Las landing pages han sido movidas a apps.webpages para mejor
modularización y escalabilidad.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class PerfilUsuario(models.Model):
    """
    Modelo que extiende el User de Django con información adicional del perfil.
    
    Este modelo implementa el patrón de perfil extendido usando OneToOneField,
    permitiendo almacenar información específica del negocio sin modificar
    el modelo User nativo de Django.
    
    Funcionalidades:
    - Diferenciación entre cuentas de empresa y usuario consumidor
    - Gestión de suscripciones y permisos
    - Información de contacto y empresa
    - Sistema de roles (Usuario/Administrador)
    
    Relaciones:
    - OneToOne con User (Django auth)
    - Relacionado con Suscripcion via ForeignKey
    """
    
    # Opciones de tipo de cuenta - Permite diferenciar el comportamiento de la app
    CUENTA_TIPO_CHOICES = [
        ('empresa', 'Empresa'),    # Cuenta empresarial - acceso completo a funciones ERP
        ('usuario', 'Usuario'),    # Cuenta de consumidor - funciones limitadas
    ]

    # Relación uno a uno con el modelo User de Django
    # related_name='userprofile' permite acceder desde User: user.userprofile
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='userprofile',
        help_text="Usuario de Django asociado a este perfil"
    )
    
    # Campo para distinguir el tipo de cuenta y personalizar la experiencia
    tipo_cuenta = models.CharField(
        max_length=10,
        choices=CUENTA_TIPO_CHOICES,
        default='usuario',
        help_text="Determina si es una cuenta empresarial o de consumidor final",
        verbose_name="Tipo de Cuenta"
    )

    # Información empresarial - Requerida para empresas, opcional para usuarios
    empresa = models.CharField(
        max_length=100, 
        blank=True,  # Permite valores vacíos en formularios
        help_text="Nombre de la empresa (requerido para cuentas empresariales)",
        verbose_name="Nombre de la Empresa"
    )
    
    # Información de contacto
    telefono = models.CharField(
        max_length=15,
        help_text="Número de teléfono de contacto",
        verbose_name="Teléfono"
    )
    
    direccion = models.TextField(
        help_text="Dirección completa del usuario o empresa",
        verbose_name="Dirección"
    )
    
    # Metadatos de registro
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del perfil",
        verbose_name="Fecha de Registro"
    )
    
    # Sistema de suscripciones para funcionalidades premium
    ESTADO_SUSCRIPCION = [
        ('activa',   'Activa'),     # Suscripción vigente
        ('inactiva', 'Inactiva'),   # Sin suscripción o vencida
        ('vencida',  'Vencida'),    # Suscripción expirada
    ]
    
    estado_suscripcion = models.CharField(
        max_length=10, 
        choices=ESTADO_SUSCRIPCION, 
        default='inactiva',
        help_text="Estado actual de la suscripción del usuario",
        verbose_name="Estado de Suscripción"
    )
    
    fecha_vencimiento = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha de vencimiento de la suscripción actual",
        verbose_name="Fecha de Vencimiento"
    )
    
    # Sistema de permisos interno de la aplicación
    PERMISOS = [
        ('Usuario',      'Usuario'),         # Permisos básicos
        ('Administrador','Administrador'),   # Permisos completos
    ]
    
    permisos = models.CharField(
        max_length=20, 
        choices=PERMISOS, 
        default='Usuario',
        help_text="Nivel de permisos dentro de la aplicación",
        verbose_name="Nivel de Permisos"
    )

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"
        # Índices para optimizar consultas frecuentes
        indexes = [
            models.Index(fields=['tipo_cuenta']),
            models.Index(fields=['estado_suscripcion']),
            models.Index(fields=['permisos']),
        ]

    def __str__(self):
        """Representación string del modelo para admin y debugging."""
        return f"{self.usuario.username} ({self.get_tipo_cuenta_display()})"

    @property
    def is_admin(self):
        """
        Propiedad que determina si el usuario tiene permisos de administrador.
        
        Returns:
            bool: True si el usuario es administrador, False en caso contrario
            
        Usage:
            if request.user.userprofile.is_admin:
                # Lógica para administradores
        """
        return self.permisos == 'Administrador'
    
    @property
    def is_empresa(self):
        """
        Propiedad que determina si es una cuenta empresarial.
        
        Returns:
            bool: True si es cuenta de empresa, False si es usuario consumidor
        """
        return self.tipo_cuenta == 'empresa'
    
    @property
    def suscripcion_activa(self):
        """
        Verifica si la suscripción está activa y no ha vencido.
        
        Returns:
            bool: True si la suscripción está activa y vigente
        """
        if self.estado_suscripcion != 'activa':
            return False
        
        if self.fecha_vencimiento and self.fecha_vencimiento < timezone.now():
            # Auto-actualizar estado si la suscripción venció
            self.estado_suscripcion = 'vencida'
            self.save(update_fields=['estado_suscripcion'])
            return False
            
        return True

    def clean(self):
        """
        Validaciones personalizadas del modelo.
        
        Raises:
            ValidationError: Si los datos no cumplen las reglas de negocio
        """
        super().clean()
        
        # Validar que las empresas tengan nombre de empresa
        if self.tipo_cuenta == 'empresa' and not self.empresa:
            raise ValidationError({
                'empresa': 'El nombre de la empresa es requerido para cuentas empresariales.'
            })
        
        # Validar fecha de vencimiento para suscripciones activas
        if self.estado_suscripcion == 'activa' and not self.fecha_vencimiento:
            raise ValidationError({
                'fecha_vencimiento': 'La fecha de vencimiento es requerida para suscripciones activas.'
            })

    def save(self, *args, **kwargs):
        """
        Override del método save para lógica personalizada.
        
        Ejecuta validaciones y lógica de negocio antes de guardar.
        """
        # Ejecutar validaciones personalizadas
        self.full_clean()
        
        # Limpiar nombre de empresa para usuarios no empresariales
        if self.tipo_cuenta != 'empresa':
            self.empresa = ''
            
        super().save(*args, **kwargs)


class Suscripcion(models.Model):
    """
    Modelo que gestiona las suscripciones de usuarios a diferentes planes.
    
    Este modelo maneja el sistema de monetización de la plataforma,
    permitiendo diferentes niveles de acceso según el plan contratado.
    
    Funcionalidades:
    - Gestión de planes (básico, premium, empresarial)
    - Control de fechas de vigencia
    - Historial de suscripciones por usuario
    - Integración con sistema de pagos
    """
    
    # Planes disponibles en la plataforma
    PLANES = [
        ('basico', 'Básico'),           # Plan gratuito con funciones limitadas
        ('premium', 'Premium'),         # Plan individual con funciones avanzadas
        ('empresarial', 'Empresarial'), # Plan para empresas con todas las funciones
    ]
    
    # Usuario que posee la suscripción
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='suscripciones',
        help_text="Usuario propietario de la suscripción"
    )
    
    # Tipo de plan contratado
    plan = models.CharField(
        max_length=20, 
        choices=PLANES,
        help_text="Tipo de plan de suscripción",
        verbose_name="Plan"
    )
    
    # Fechas de vigencia
    fecha_inicio = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de inicio de la suscripción",
        verbose_name="Fecha de Inicio"
    )
    
    fecha_vencimiento = models.DateTimeField(
        help_text="Fecha de vencimiento de la suscripción",
        verbose_name="Fecha de Vencimiento"
    )
    
    # Información financiera
    precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio pagado por la suscripción",
        verbose_name="Precio"
    )
    
    # Estado de la suscripción
    activa = models.BooleanField(
        default=True,
        help_text="Indica si la suscripción está activa",
        verbose_name="Activa"
    )

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ['-fecha_inicio']  # Más recientes primero
        indexes = [
            models.Index(fields=['usuario', 'activa']),
            models.Index(fields=['plan']),
            models.Index(fields=['fecha_vencimiento']),
        ]

    def __str__(self):
        """Representación string del modelo."""
        return f"{self.usuario.username} - {self.get_plan_display()}"
    
    @property
    def esta_vigente(self):
        """
        Verifica si la suscripción está vigente.
        
        Returns:
            bool: True si está activa y no ha vencido
        """
        return self.activa and self.fecha_vencimiento > timezone.now()
    
    @property
    def dias_restantes(self):
        """
        Calcula los días restantes de la suscripción.
        
        Returns:
            int: Número de días restantes (0 si ya venció)
        """
        if not self.esta_vigente:
            return 0
        
        delta = self.fecha_vencimiento - timezone.now()
        return max(0, delta.days)
