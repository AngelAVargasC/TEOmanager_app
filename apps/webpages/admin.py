from django.contrib import admin
from .models import LandingPage


@admin.register(LandingPage)
class LandingPageAdmin(admin.ModelAdmin):
    """Configuración del admin para LandingPage."""
    list_display = ('titulo', 'usuario', 'plantilla', 'fecha_creacion', 'tiene_imagen_hero')
    list_filter = ('plantilla', 'fecha_creacion')
    search_fields = ('titulo', 'usuario__username', 'usuario__email')
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'titulo', 'descripcion')
        }),
        ('Diseño', {
            'fields': ('plantilla', 'color_scheme')
        }),
        ('Contenido', {
            'fields': ('contenido',)
        }),
        ('Imagen Hero', {
            'fields': ('hero_image', 'hero_image_file')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion',)
        }),
    )

