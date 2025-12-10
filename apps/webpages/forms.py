"""
Formularios para la gestión de landing pages.

Este módulo contiene los formularios relacionados con:
- Creación y edición de landing pages
"""

from django import forms
from .models import LandingPage


class LandingPageForm(forms.ModelForm):
    """Formulario para crear o editar la landing page de una empresa."""
    class Meta:
        model = LandingPage
        fields = [
            # Campos básicos
            'titulo', 'descripcion', 'plantilla',
            # Hero Section
            'hero_image', 'hero_image_file', 'subtitulo_hero', 'texto_boton_hero', 'url_boton_hero',
            # Contenido general
            'contenido',
            # Sección Sobre Nosotros
            'seccion_sobre_nosotros_titulo', 'seccion_sobre_nosotros_texto',
            # Sección Productos
            'seccion_productos_titulo', 'seccion_productos_subtitulo',
            # Sección Servicios
            'seccion_servicios_titulo', 'seccion_servicios_subtitulo',
            # Sección Testimonios
            'seccion_testimonios_titulo', 'seccion_testimonios_texto',
            # Sección Contacto
            'seccion_contacto_titulo', 'seccion_contacto_texto', 
            'seccion_contacto_boton_texto', 'seccion_contacto_boton_url',
            # Colores
            'color_primario', 'color_secundario',
        ]
        widgets = {
            # Campos básicos
            'titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Título de tu página',
                'id': 'id_titulo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class':'form-input',
                'placeholder':'Breve descripción o slogan',
                'rows':3,
                'id': 'id_descripcion'
            }),
            'plantilla': forms.Select(attrs={
                'class':'form-input',
                'id': 'id_plantilla'
            }),
            # Hero Section
            'hero_image': forms.URLInput(attrs={
                'class':'form-input',
                'placeholder':'https://ejemplo.com/imagen.jpg',
                'id': 'id_hero_image'
            }),
            'hero_image_file': forms.ClearableFileInput(attrs={
                'class':'form-input',
                'accept':'image/*',
                'id': 'id_hero_image_file'
            }),
            'subtitulo_hero': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Subtítulo adicional para el hero (opcional)',
                'id': 'id_subtitulo_hero'
            }),
            'texto_boton_hero': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Ej: Ver Catálogo, Comenzar, etc.',
                'id': 'id_texto_boton_hero'
            }),
            'url_boton_hero': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'/products/productos/ o URL completa',
                'id': 'id_url_boton_hero'
            }),
            # Contenido general
            'contenido': forms.Textarea(attrs={
                'class':'form-input',
                'placeholder':'Contenido principal (acepta HTML básico)',
                'rows':6,
                'id': 'id_contenido'
            }),
            # Sección Sobre Nosotros
            'seccion_sobre_nosotros_titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Sobre Nosotros',
                'id': 'id_seccion_sobre_nosotros_titulo'
            }),
            'seccion_sobre_nosotros_texto': forms.Textarea(attrs={
                'class':'form-input',
                'placeholder':'Describe tu empresa, misión, valores...',
                'rows':4,
                'id': 'id_seccion_sobre_nosotros_texto'
            }),
            # Sección Productos
            'seccion_productos_titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Nuestros Productos',
                'id': 'id_seccion_productos_titulo'
            }),
            'seccion_productos_subtitulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Descripción breve de tus productos',
                'id': 'id_seccion_productos_subtitulo'
            }),
            # Sección Servicios
            'seccion_servicios_titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Nuestros Servicios',
                'id': 'id_seccion_servicios_titulo'
            }),
            'seccion_servicios_subtitulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Descripción breve de tus servicios',
                'id': 'id_seccion_servicios_subtitulo'
            }),
            # Sección Testimonios
            'seccion_testimonios_titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Lo que dicen nuestros clientes',
                'id': 'id_seccion_testimonios_titulo'
            }),
            'seccion_testimonios_texto': forms.Textarea(attrs={
                'class':'form-input',
                'placeholder':'Testimonios de clientes (puedes usar HTML)',
                'rows':4,
                'id': 'id_seccion_testimonios_texto'
            }),
            # Sección Contacto
            'seccion_contacto_titulo': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'¿Listo para comenzar?',
                'id': 'id_seccion_contacto_titulo'
            }),
            'seccion_contacto_texto': forms.Textarea(attrs={
                'class':'form-input',
                'placeholder':'Texto de llamada a la acción',
                'rows':3,
                'id': 'id_seccion_contacto_texto'
            }),
            'seccion_contacto_boton_texto': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'Contáctanos',
                'id': 'id_seccion_contacto_boton_texto'
            }),
            'seccion_contacto_boton_url': forms.TextInput(attrs={
                'class':'form-input',
                'placeholder':'/perfil/ o URL de contacto',
                'id': 'id_seccion_contacto_boton_url'
            }),
            # Colores
            'color_primario': forms.TextInput(attrs={
                'class':'form-input',
                'type': 'color',
                'id': 'id_color_primario'
            }),
            'color_secundario': forms.TextInput(attrs={
                'class':'form-input',
                'type': 'color',
                'id': 'id_color_secundario'
            }),
        }
    
    def clean_titulo(self):
        titulo = self.cleaned_data.get('titulo','').strip()
        if not titulo:
            raise forms.ValidationError('El título no puede estar vacío.')
        return titulo
    
    def clean(self):
        cleaned_data = super().clean()
        hero_image = cleaned_data.get('hero_image')
        hero_image_file = cleaned_data.get('hero_image_file')
        
        # Validar que al menos una opción de imagen esté presente (opcional)
        # Si ambas están vacías, está bien (se puede crear sin imagen)
        return cleaned_data

