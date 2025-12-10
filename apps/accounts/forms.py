# apps/accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from apps.accounts.models import PerfilUsuario
from apps.accounts.services import UserService

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        label="Correo electrónico",
        required=True,
        help_text="Requerido, debe ser único."
    )
    tipo_cuenta = forms.ChoiceField(
        label="¿Te registras como…?",
        choices=PerfilUsuario.CUENTA_TIPO_CHOICES,
        widget=forms.RadioSelect,
        initial='usuario',
        help_text="Elige 'Empresa' si vas a vender, o 'Usuario' si vas a comprar."
    )

    # Campos específicos para "Usuario"
    first_name = forms.CharField(
        label="Nombre",
        max_length=30,
        required=False,
        help_text="Obligatorio si te registras como Usuario."
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=30,
        required=False,
        help_text="Obligatorio si te registras como Usuario."
    )

    # Campos para "Empresa"
    empresa = forms.CharField(
        label="Empresa",
        max_length=100,
        required=False,
        help_text="Obligatorio si te registras como Empresa."
    )
    telefono = forms.CharField(
        label="Teléfono",
        max_length=15,
        required=False,
        help_text="Obligatorio si te registras como Empresa."
    )
    direccion = forms.CharField(
        label="Dirección",
        widget=forms.Textarea,
        required=False,
        help_text="Obligatorio si te registras como Empresa."
    )

    class Meta:
        model = User
        fields = [
            'username','email',
            'password1','password2',
            'tipo_cuenta',
            'first_name','last_name',
            'empresa','telefono','direccion',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inyectar clases y placeholders
        self.fields['username'].widget.attrs.update({
            'class':'form-input','placeholder':'Ingresa tu nombre de usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class':'form-input','placeholder':'ejemplo@correo.com'
        })
        self.fields['password1'].widget.attrs.update({
            'class':'form-input','placeholder':'Mínimo 8 caracteres'
        })
        self.fields['password2'].widget.attrs.update({
            'class':'form-input','placeholder':'Repite tu contraseña'
        })
        self.fields['tipo_cuenta'].widget.attrs.update({
            'class':'radio-group'
        })
        self.fields['first_name'].widget.attrs.update({
            'class':'form-input','placeholder':'Tu nombre'
        })
        self.fields['last_name'].widget.attrs.update({
            'class':'form-input','placeholder':'Tu apellido'
        })
        self.fields['empresa'].widget.attrs.update({
            'class':'form-input','placeholder':'Nombre de tu empresa'
        })
        self.fields['telefono'].widget.attrs.update({
            'class':'form-input','placeholder':'Número de contacto'
        })
        self.fields['direccion'].widget.attrs.update({
            'class':'form-input','placeholder':'Dirección completa','rows':3
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Solo verificar usuarios activos (los eliminados no deberían existir, pero por seguridad)
        if User.objects.filter(email__iexact=email, is_active=True).exists():
            raise ValidationError('Ya existe un usuario registrado con este correo electrónico.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Solo verificar usuarios activos
        if User.objects.filter(username__iexact=username, is_active=True).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número.')
        if not any(c.isupper() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
        if not any(c.islower() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for c in password):
            raise ValidationError('La contraseña debe contener al menos un carácter especial.')
        return password

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_cuenta')
        if tipo == 'empresa':
            # Requerir datos de empresa
            for f in ('empresa','telefono','direccion'):
                if not cleaned.get(f):
                    self.add_error(f, 'Requerido para cuentas de empresa.')
        else:
            # Requerir nombre y apellido
            for f in ('first_name','last_name'):
                if not cleaned.get(f):
                    self.add_error(f, 'Requerido para cuentas de usuario.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name','')
        user.last_name  = self.cleaned_data.get('last_name','')
        if commit:
            user.save()
            # Usar el servicio para crear el perfil y enviar el correo de bienvenida
            UserService.create_user_profile(
                user=user,
                tipo_cuenta=self.cleaned_data['tipo_cuenta'],
                empresa=self.cleaned_data.get('empresa','').strip(),
                telefono=self.cleaned_data.get('telefono','').strip(),
                direccion=self.cleaned_data.get('direccion','').strip()
            )
        return user

class EditarPerfilForm(forms.ModelForm):
    """Formulario para editar el perfil del usuario."""
    
    # Campos del User
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'erp-input', 'placeholder': 'Nombre de usuario'})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={'class': 'erp-input', 'placeholder': 'correo@ejemplo.com'})
    )
    first_name = forms.CharField(
        label="Nombre",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'erp-input', 'placeholder': 'Tu nombre'})
    )
    last_name = forms.CharField(
        label="Apellido",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'erp-input', 'placeholder': 'Tu apellido'})
    )
    
    class Meta:
        model = PerfilUsuario
        fields = ['empresa', 'telefono', 'direccion']
        widgets = {
            'empresa': forms.TextInput(attrs={
                'class': 'erp-input',
                'placeholder': 'Nombre de tu empresa'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'erp-input',
                'placeholder': 'Número de contacto'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'erp-input',
                'placeholder': 'Dirección completa',
                'rows': 3
            }),
        }
        labels = {
            'empresa': 'Nombre de la Empresa',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
        
        # CORREGIDO: Ocultar campos según tipo de cuenta
        if hasattr(self, 'instance') and self.instance:
            if self.instance.tipo_cuenta == 'usuario':
                # Para usuarios consumidores: ocultar campo empresa
                if 'empresa' in self.fields:
                    del self.fields['empresa']
                # Hacer nombre y apellido obligatorios con placeholders específicos
                self.fields['first_name'].required = True
                self.fields['first_name'].widget.attrs.update({'placeholder': 'Tu nombre'})
                self.fields['last_name'].required = True  
                self.fields['last_name'].widget.attrs.update({'placeholder': 'Tu apellido'})
                # Teléfono y dirección opcionales para consumidores
                self.fields['telefono'].required = False
                self.fields['telefono'].label = 'Teléfono (opcional)'
                self.fields['telefono'].widget.attrs.update({'placeholder': 'Número de contacto (opcional)'})
                self.fields['direccion'].required = False
                self.fields['direccion'].label = 'Dirección (opcional)'
                self.fields['direccion'].widget.attrs.update({'placeholder': 'Dirección (opcional)'})
                
            elif self.instance.tipo_cuenta == 'empresa':
                # Para empresas: hacer empresa obligatoria con placeholders específicos
                self.fields['empresa'].required = True
                self.fields['empresa'].widget.attrs.update({'placeholder': 'Nombre de tu empresa'})
                self.fields['first_name'].required = False
                self.fields['last_name'].required = False
                # Teléfono y dirección obligatorios para empresas
                self.fields['telefono'].required = True
                self.fields['telefono'].label = 'Teléfono Empresarial'
                self.fields['telefono'].widget.attrs.update({'placeholder': 'Número de contacto empresarial'})
                self.fields['direccion'].required = True
                self.fields['direccion'].label = 'Dirección de la Empresa'
                self.fields['direccion'].widget.attrs.update({'placeholder': 'Dirección de la empresa'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Solo verificar usuarios activos (excluyendo el usuario actual)
        if self.user and User.objects.filter(email__iexact=email, is_active=True).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe otro usuario registrado con este correo electrónico.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Solo verificar usuarios activos (excluyendo el usuario actual)
        if self.user and User.objects.filter(username__iexact=username, is_active=True).exclude(pk=self.user.pk).exists():
            raise ValidationError('Ya existe otro usuario con este nombre de usuario.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        
        # Obtener el perfil para verificar el tipo de cuenta
        if hasattr(self, 'instance') and self.instance:
            tipo_cuenta = self.instance.tipo_cuenta
            
            # Validaciones específicas según el tipo de cuenta
            if tipo_cuenta == 'empresa':
                # Para empresas: empresa, teléfono y dirección son obligatorios
                if 'empresa' in self.fields and not cleaned_data.get('empresa'):
                    self.add_error('empresa', 'Este campo es obligatorio para cuentas de empresa.')
                if 'telefono' in self.fields and not cleaned_data.get('telefono'):
                    self.add_error('telefono', 'Este campo es obligatorio para cuentas de empresa.')
                if 'direccion' in self.fields and not cleaned_data.get('direccion'):
                    self.add_error('direccion', 'Este campo es obligatorio para cuentas de empresa.')
            
            elif tipo_cuenta == 'usuario':
                # Para usuarios consumidores: nombre y apellido son obligatorios
                if 'first_name' in self.fields and not cleaned_data.get('first_name'):
                    self.add_error('first_name', 'Este campo es obligatorio para cuentas de usuario.')
                if 'last_name' in self.fields and not cleaned_data.get('last_name'):
                    self.add_error('last_name', 'Este campo es obligatorio para cuentas de usuario.')
        
        return cleaned_data

    def save(self, commit=True):
        perfil = super().save(commit=False)
        
        if self.user:
            # Actualizar campos del User
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            
            # Solo actualizar nombre y apellido si los campos están presentes
            if 'first_name' in self.cleaned_data:
                self.user.first_name = self.cleaned_data.get('first_name', '')
            if 'last_name' in self.cleaned_data:
                self.user.last_name = self.cleaned_data.get('last_name', '')
            
            # Para empresas, limpiar nombre y apellido si no están en el formulario
            if perfil.tipo_cuenta == 'empresa':
                if 'first_name' not in self.fields:
                    self.user.first_name = ''
                if 'last_name' not in self.fields:
                    self.user.last_name = ''
            
            if commit:
                self.user.save()
                perfil.save()
        
        return perfil
