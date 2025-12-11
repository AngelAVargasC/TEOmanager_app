from django import forms
from apps.productservice.models import Producto, Servicio, ReservaServicio
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import json

# Top 20 categorías estándar para productos
CATEGORIAS_PRODUCTO = [
    ("Electronica", "Electrónica"),
    ("Computadoras", "Computadoras"),
    ("Laptops", "Laptops"),
    ("Celulares", "Celulares"),
    ("Hogar", "Hogar"),
    ("Limpieza", "Limpieza"),
    ("Comida", "Comida"),
    ("Belleza", "Belleza"),
    ("Juguetes", "Juguetes"),
    ("Ropa", "Ropa"),
    ("Calzado", "Calzado"),
    ("Deportes", "Deportes"),
    ("Herramientas", "Herramientas"),
    ("Oficina", "Oficina"),
    ("Mascotas", "Mascotas"),
    ("Salud", "Salud"),
    ("Videojuegos", "Videojuegos"),
    ("Accesorios", "Accesorios"),
    ("Automotriz", "Automotriz"),
    ("Otros", "Otros"),
]

# Top 20 categorías estándar para servicios
CATEGORIAS_SERVICIO = [
    ("Consultoria", "Consultoría"),
    ("Reparacion", "Reparación"),
    ("Mantenimiento", "Mantenimiento"),
    ("Limpieza", "Limpieza"),
    ("Transporte", "Transporte"),
    ("Capacitacion", "Capacitación"),
    ("Salud", "Salud"),
    ("Belleza", "Belleza"),
    ("Entretenimiento", "Entretenimiento"),
    ("Tecnologia", "Tecnología"),
    ("Eventos", "Eventos"),
    ("Construccion", "Construcción"),
    ("Finanzas", "Finanzas"),
    ("Legal", "Legal"),
    ("Marketing", "Marketing"),
    ("Diseño", "Diseño"),
    ("Educacion", "Educación"),
    ("Deportes", "Deportes"),
    ("Mascotas", "Mascotas"),
    ("Otros", "Otros"),
]

class ProductoForm(forms.ModelForm):
    categoria = forms.ChoiceField(choices=CATEGORIAS_PRODUCTO, label="Categoría")
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'stock', 'categoria', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'min': 0}),
            'stock': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise ValidationError('El precio debe ser mayor que cero.')
        return precio

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock < 0:
            raise ValidationError('El stock no puede ser negativo.')
        return stock

class ServicioForm(forms.ModelForm):
    categoria = forms.ChoiceField(choices=CATEGORIAS_SERVICIO, label="Categoría")
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio', 'duracion', 'categoria', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio': forms.NumberInput(attrs={'min': 0}),
            'duracion': forms.TextInput(attrs={'placeholder': 'Ej: 1 hora, 2 días, etc.'}),
        }

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio <= 0:
            raise ValidationError('El precio debe ser mayor que cero.')
        return precio

    def clean_duracion(self):
        duracion = self.cleaned_data.get('duracion')
        if not duracion:
            raise ValidationError('La duración es obligatoria.')
        return duracion 


# Formularios para políticas personalizables
class PoliticaItemForm(forms.Form):
    """Formulario para un item individual de política"""
    icon = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: fas fa-truck'
        }),
        label="Icono (FontAwesome)"
    )
    text = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Texto descriptivo de la política'
        }),
        label="Texto"
    )


class PoliticasProductoForm(forms.ModelForm):
    """Formulario para editar las políticas de un producto"""
    
    # Campos dinámicos para políticas de envío
    envio_items = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='[]'
    )
    
    # Campos dinámicos para políticas de devoluciones
    devoluciones_items = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='[]'
    )
    
    class Meta:
        model = Producto
        fields = []  # No incluimos los campos del modelo, los manejamos en clean()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar políticas existentes
            envio_politicas = self.instance.get_politicas_envio_completas()
            devoluciones_politicas = self.instance.get_politicas_devoluciones_completas()
            
            self.fields['envio_items'].initial = json.dumps(envio_politicas)
            self.fields['devoluciones_items'].initial = json.dumps(devoluciones_politicas)
    
    def clean(self):
        print("=== CLEAN METHOD EXECUTING (PRODUCTO) ===")
        cleaned_data = super().clean()
        print(f"Cleaned data keys: {list(cleaned_data.keys())}")
        
        # Procesar envio_items
        envio_items_data = cleaned_data.get('envio_items')
        print(f"Envio items data: {envio_items_data}")
        if envio_items_data:
            try:
                parsed_envio = json.loads(envio_items_data) if envio_items_data else []
                print(f"Parsed envio: {parsed_envio}")
                # Validar estructura
                for item in parsed_envio:
                    if not isinstance(item, dict) or 'icon' not in item or 'text' not in item:
                        raise ValidationError('Formato de datos inválido en políticas de envío')
                # Asignar al campo real
                cleaned_data['politicas_envio'] = parsed_envio
                print(f"Assigned politicas_envio: {cleaned_data['politicas_envio']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                raise ValidationError('Formato JSON inválido en políticas de envío')
        else:
            # Si no hay datos, usar diccionario vacío (políticas por defecto)
            cleaned_data['politicas_envio'] = {}
            print("No envio data, using empty dict")
        
        # Procesar devoluciones_items
        devoluciones_items_data = cleaned_data.get('devoluciones_items')
        print(f"Devoluciones items data: {devoluciones_items_data}")
        if devoluciones_items_data:
            try:
                parsed_devoluciones = json.loads(devoluciones_items_data) if devoluciones_items_data else []
                print(f"Parsed devoluciones: {parsed_devoluciones}")
                # Validar estructura
                for item in parsed_devoluciones:
                    if not isinstance(item, dict) or 'icon' not in item or 'text' not in item:
                        raise ValidationError('Formato de datos inválido en políticas de devolución')
                # Asignar al campo real
                cleaned_data['politicas_devoluciones'] = parsed_devoluciones
                print(f"Assigned politicas_devoluciones: {cleaned_data['politicas_devoluciones']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                raise ValidationError('Formato JSON inválido en políticas de devolución')
        else:
            # Si no hay datos, usar diccionario vacío (políticas por defecto)
            cleaned_data['politicas_devoluciones'] = {}
            print("No devoluciones data, using empty dict")
        
        print(f"Final cleaned_data keys: {list(cleaned_data.keys())}")
        print("=== CLEAN METHOD FINISHED (PRODUCTO) ===")
        return cleaned_data
    
    def save(self, commit=True):
        # Los datos ya fueron procesados en clean(), asignamos a la instancia
        instance = super().save(commit=False)
        
        # Asignar los valores procesados
        instance.politicas_envio = self.cleaned_data.get('politicas_envio', {})
        instance.politicas_devoluciones = self.cleaned_data.get('politicas_devoluciones', {})
        
        if commit:
            instance.save()
        return instance


class PoliticasServicioForm(forms.ModelForm):
    """Formulario para editar las políticas de un servicio"""
    
    # Campos dinámicos para políticas de reserva
    reserva_items = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='[]'
    )
    
    # Campos dinámicos para políticas de cancelación
    cancelacion_items = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        initial='[]'
    )
    
    class Meta:
        model = Servicio
        fields = []  # No incluimos los campos del modelo, los manejamos en clean()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Cargar políticas existentes
            reserva_politicas = self.instance.get_politicas_reserva_completas()
            cancelacion_politicas = self.instance.get_politicas_cancelacion_completas()
            
            self.fields['reserva_items'].initial = json.dumps(reserva_politicas)
            self.fields['cancelacion_items'].initial = json.dumps(cancelacion_politicas)
    
    def clean(self):
        print("=== CLEAN METHOD EXECUTING ===")
        cleaned_data = super().clean()
        print(f"Cleaned data keys: {list(cleaned_data.keys())}")
        
        # Procesar reserva_items
        reserva_items_data = cleaned_data.get('reserva_items')
        print(f"Reserva items data: {reserva_items_data}")
        if reserva_items_data:
            try:
                parsed_reserva = json.loads(reserva_items_data) if reserva_items_data else []
                print(f"Parsed reserva: {parsed_reserva}")
                # Validar estructura
                for item in parsed_reserva:
                    if not isinstance(item, dict) or 'icon' not in item or 'text' not in item:
                        raise ValidationError('Formato de datos inválido en políticas de reserva')
                # Asignar al campo real
                cleaned_data['politicas_reserva'] = parsed_reserva
                print(f"Assigned politicas_reserva: {cleaned_data['politicas_reserva']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                raise ValidationError('Formato JSON inválido en políticas de reserva')
        else:
            # Si no hay datos, usar diccionario vacío (políticas por defecto)
            cleaned_data['politicas_reserva'] = {}
            print("No reserva data, using empty dict")
        
        # Procesar cancelacion_items
        cancelacion_items_data = cleaned_data.get('cancelacion_items')
        print(f"Cancelacion items data: {cancelacion_items_data}")
        if cancelacion_items_data:
            try:
                parsed_cancelacion = json.loads(cancelacion_items_data) if cancelacion_items_data else []
                print(f"Parsed cancelacion: {parsed_cancelacion}")
                # Validar estructura
                for item in parsed_cancelacion:
                    if not isinstance(item, dict) or 'icon' not in item or 'text' not in item:
                        raise ValidationError('Formato de datos inválido en políticas de cancelación')
                # Asignar al campo real
                cleaned_data['politicas_cancelacion'] = parsed_cancelacion
                print(f"Assigned politicas_cancelacion: {cleaned_data['politicas_cancelacion']}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
                raise ValidationError('Formato JSON inválido en políticas de cancelación')
        else:
            # Si no hay datos, usar diccionario vacío (políticas por defecto)
            cleaned_data['politicas_cancelacion'] = {}
            print("No cancelacion data, using empty dict")
        
        print(f"Final cleaned_data keys: {list(cleaned_data.keys())}")
        print("=== CLEAN METHOD FINISHED ===")
        return cleaned_data
    
    def save(self, commit=True):
        # Los datos ya fueron procesados en clean(), asignamos a la instancia
        instance = super().save(commit=False)
        
        # Asignar los valores procesados
        instance.politicas_reserva = self.cleaned_data.get('politicas_reserva', {})
        instance.politicas_cancelacion = self.cleaned_data.get('politicas_cancelacion', {})
        
        if commit:
            instance.save()
        return instance


class ReservaServicioForm(forms.ModelForm):
    """Formulario para crear una reserva de servicio"""
    
    class Meta:
        model = ReservaServicio
        fields = ['fecha_reserva', 'telefono_contacto', 'direccion_servicio', 'notas']
        widgets = {
            'fecha_reserva': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                    'required': True
                },
                format='%Y-%m-%dT%H:%M'
            ),
            'telefono_contacto': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej: +52 123 456 7890'
                }
            ),
            'direccion_servicio': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Dirección donde se ejecutará el servicio (opcional)'
                }
            ),
            'notas': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Notas adicionales, instrucciones especiales o requisitos (opcional)'
                }
            ),
        }
        labels = {
            'fecha_reserva': 'Fecha y Hora de la Reserva',
            'telefono_contacto': 'Teléfono de Contacto',
            'direccion_servicio': 'Dirección del Servicio',
            'notas': 'Notas Adicionales'
        }
    
    def __init__(self, *args, **kwargs):
        self.servicio = kwargs.pop('servicio', None)
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Establecer fecha mínima (ahora)
        if self.fields['fecha_reserva'].widget.attrs.get('type') == 'datetime-local':
            ahora = timezone.now()
            fecha_minima = ahora.strftime('%Y-%m-%dT%H:%M')
            self.fields['fecha_reserva'].widget.attrs['min'] = fecha_minima
    
    def clean_fecha_reserva(self):
        """Validar que la fecha de reserva sea en el futuro"""
        fecha_reserva = self.cleaned_data.get('fecha_reserva')
        
        if fecha_reserva:
            ahora = timezone.now()
            if fecha_reserva < ahora:
                raise ValidationError('La fecha y hora de la reserva debe ser en el futuro.')
            
            # Validar que la reserva sea con al menos 24 horas de anticipación
            # (puede ajustarse según políticas del servicio)
            diferencia = fecha_reserva - ahora
            horas_anticipacion = diferencia.total_seconds() / 3600
            
            if horas_anticipacion < 24:
                raise ValidationError(
                    'La reserva debe realizarse con al menos 24 horas de anticipación. '
                    f'Por favor, selecciona una fecha posterior a {(ahora + timezone.timedelta(hours=24)).strftime("%d/%m/%Y %H:%M")}.'
                )
        
        return fecha_reserva
    
    def clean_telefono_contacto(self):
        """Validar formato básico del teléfono"""
        telefono = self.cleaned_data.get('telefono_contacto', '').strip()
        
        if telefono:
            # Validación básica: debe tener al menos 10 caracteres
            if len(telefono) < 10:
                raise ValidationError('El teléfono debe tener al menos 10 dígitos.')
        
        return telefono
    
    def save(self, commit=True):
        """Guardar la reserva con servicio y usuario"""
        instance = super().save(commit=False)
        
        if self.servicio:
            instance.servicio = self.servicio
            instance.empresa = self.servicio.usuario
            # Asegurar que precio_total esté establecido
            if not instance.precio_total:
                instance.precio_total = self.servicio.precio
        
        if self.usuario:
            instance.usuario = self.usuario
        
        if commit:
            instance.save()
        
        return instance