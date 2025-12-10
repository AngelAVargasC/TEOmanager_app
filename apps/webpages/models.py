"""
Modelos para la gestión de landing pages y plantillas web.

Este módulo contiene los modelos relacionados con:
- Landing pages personalizadas (LandingPage)

Arquitectura MVT: Estos modelos representan la capa de datos (Model) 
para la funcionalidad de páginas web personalizables.

Diseñado para escalabilidad: Este módulo está separado para permitir
escalabilidad horizontal y vertical, preparado para migración futura
a microservicios si es necesario.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class LandingPage(models.Model):
    """
    Modelo para gestionar landing pages personalizadas de empresas.
    
    Permite a las empresas crear páginas de aterrizaje personalizadas
    para mostrar sus productos y servicios de manera profesional.
    
    Funcionalidades:
    - Múltiples plantillas de diseño
    - Personalización de contenido y colores
    - Gestión de imágenes hero
    - SEO básico integrado
    """
    
    # Usuario propietario de la landing page
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='landing_pages',
        help_text="Usuario propietario de la landing page"
    )
    
    # Contenido principal
    titulo = models.CharField(
        max_length=200, 
        help_text='Título principal que aparecerá en la página',
        verbose_name="Título Principal"
    )
    
    descripcion = models.TextField(
        blank=True, 
        help_text='Descripción o slogan de la empresa',
        verbose_name="Descripción"
    )
    
    # Hero Section - Campos adicionales
    subtitulo_hero = models.CharField(
        max_length=300,
        blank=True,
        help_text='Subtítulo adicional para la sección hero (opcional)',
        verbose_name="Subtítulo Hero"
    )
    
    texto_boton_hero = models.CharField(
        max_length=50,
        blank=True,
        default='Ver Catálogo',
        help_text='Texto del botón CTA en el hero',
        verbose_name="Texto Botón Hero"
    )
    
    url_boton_hero = models.CharField(
        max_length=200,
        blank=True,
        help_text='URL del botón CTA (ej: /products/productos/)',
        verbose_name="URL Botón Hero"
    )
    
    # Imagen de cabecera (hero image)
    hero_image = models.URLField(
        blank=True, 
        null=True, 
        help_text='URL de imagen externa para la cabecera',
        verbose_name="URL de Imagen Hero"
    )
    
    hero_image_file = models.ImageField(
        upload_to='landing_hero/', 
        blank=True, 
        null=True, 
        help_text='Archivo de imagen subido para la cabecera (tiene prioridad sobre URL)',
        verbose_name="Archivo de Imagen Hero"
    )
    
    # Contenido enriquecido
    contenido = models.TextField(
        blank=True, 
        help_text='Contenido principal de la página (acepta HTML básico)',
        verbose_name="Contenido Principal"
    )
    
    # Sección Sobre Nosotros
    seccion_sobre_nosotros_titulo = models.CharField(
        max_length=200,
        blank=True,
        default='Sobre Nosotros',
        help_text='Título personalizado para la sección "Sobre Nosotros"',
        verbose_name="Título Sobre Nosotros"
    )
    
    seccion_sobre_nosotros_texto = models.TextField(
        blank=True,
        help_text='Texto descriptivo para la sección "Sobre Nosotros"',
        verbose_name="Texto Sobre Nosotros"
    )
    
    # Sección Productos
    seccion_productos_titulo = models.CharField(
        max_length=200,
        blank=True,
        default='Nuestros Productos',
        help_text='Título personalizado para la sección de productos',
        verbose_name="Título Sección Productos"
    )
    
    seccion_productos_subtitulo = models.CharField(
        max_length=300,
        blank=True,
        help_text='Subtítulo o descripción para la sección de productos',
        verbose_name="Subtítulo Sección Productos"
    )
    
    # Sección Servicios
    seccion_servicios_titulo = models.CharField(
        max_length=200,
        blank=True,
        default='Nuestros Servicios',
        help_text='Título personalizado para la sección de servicios',
        verbose_name="Título Sección Servicios"
    )
    
    seccion_servicios_subtitulo = models.CharField(
        max_length=300,
        blank=True,
        help_text='Subtítulo o descripción para la sección de servicios',
        verbose_name="Subtítulo Sección Servicios"
    )
    
    # Sección Testimonios/Reseñas
    seccion_testimonios_titulo = models.CharField(
        max_length=200,
        blank=True,
        default='Lo que dicen nuestros clientes',
        help_text='Título para la sección de testimonios',
        verbose_name="Título Testimonios"
    )
    
    seccion_testimonios_texto = models.TextField(
        blank=True,
        help_text='Testimonios o reseñas de clientes (acepta HTML)',
        verbose_name="Texto Testimonios"
    )
    
    # Sección Contacto/CTA Final
    seccion_contacto_titulo = models.CharField(
        max_length=200,
        blank=True,
        default='¿Listo para comenzar?',
        help_text='Título para la sección de contacto o CTA final',
        verbose_name="Título Contacto"
    )
    
    seccion_contacto_texto = models.TextField(
        blank=True,
        help_text='Texto de la sección de contacto o llamada a la acción',
        verbose_name="Texto Contacto"
    )
    
    seccion_contacto_boton_texto = models.CharField(
        max_length=50,
        blank=True,
        default='Contáctanos',
        help_text='Texto del botón de contacto',
        verbose_name="Texto Botón Contacto"
    )
    
    seccion_contacto_boton_url = models.CharField(
        max_length=200,
        blank=True,
        help_text='URL del botón de contacto',
        verbose_name="URL Botón Contacto"
    )
    
    # Configuración de diseño
    PLANTILLA_CHOICES = [
        ('plantilla1', 'Plantilla Clásica (FREE)'),           # Diseño tradicional y elegante
        ('plantilla2', 'Plantilla Moderna (FREE)'),            # Diseño contemporáneo y dinámico
        ('plantilla3', 'Plantilla Corporativa (PREMIUM)'),        # Estilo WordPress - Profesional corporativo
        ('plantilla4', 'Plantilla Minimalista (PREMIUM)'),       # Estilo WordPress - Diseño limpio y minimalista
        ('plantilla5', 'Plantilla Tech (PREMIUM)'),             # Estilo Mac Store - Elegante y minimalista
        ('plantilla6', 'Plantilla Autos (PREMIUM)'),            # Diseño para concesionarios y autos
        ('plantilla7', 'Plantilla Motos (PREMIUM)'),            # Diseño para motocicletas y motos
    ]
    
    plantilla = models.CharField(
        max_length=50, 
        choices=PLANTILLA_CHOICES, 
        default='plantilla1', 
        help_text='Diseño visual de la landing page',
        verbose_name="Plantilla de Diseño"
    )
    
    color_scheme = models.CharField(
        max_length=50, 
        default='default', 
        help_text='Esquema de colores para personalizar la apariencia',
        verbose_name="Esquema de Colores"
    )
    
    # Colores personalizados (opcional, para algunas plantillas)
    color_primario = models.CharField(
        max_length=7,
        blank=True,
        default='#2563eb',
        help_text='Color primario en formato HEX (ej: #2563eb)',
        verbose_name="Color Primario"
    )
    
    color_secundario = models.CharField(
        max_length=7,
        blank=True,
        default='#22c55e',
        help_text='Color secundario en formato HEX (ej: #22c55e)',
        verbose_name="Color Secundario"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha de creación de la landing page",
        verbose_name="Fecha de Creación"
    )

    class Meta:
        verbose_name = "Landing Page"
        verbose_name_plural = "Landing Pages"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario']),
            models.Index(fields=['plantilla']),
        ]

    def get_hero_image_url(self):
        """
        Obtiene la URL de la imagen hero con prioridad.
        
        Prioriza el archivo subido sobre la URL externa para mejor control
        y rendimiento de la aplicación.
        
        Returns:
            str: URL de la imagen hero o string vacío si no hay imagen
        """
        if self.hero_image_file:
            return self.hero_image_file.url
        return self.hero_image or ''

    def __str__(self):
        """Representación string del modelo."""
        return f"Landing Page de {self.usuario.username} - {self.get_plantilla_display()}"
    
    @property
    def tiene_imagen_hero(self):
        """
        Verifica si la landing page tiene imagen hero configurada.
        
        Returns:
            bool: True si tiene imagen hero (archivo o URL)
        """
        return bool(self.hero_image_file or self.hero_image)
    
    def clean(self):
        """Validaciones personalizadas del modelo."""
        super().clean()
        
        # Validar que al menos uno de los campos de imagen esté presente
        # (Esta validación es opcional, se puede remover si se permite sin imagen)
        if not self.hero_image_file and not self.hero_image:
            # Solo advertencia, no error crítico
            pass

