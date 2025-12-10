from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib import messages
from django.contrib.auth.models import User
from apps.accounts.models import PerfilUsuario
from django.utils import timezone
from datetime import timedelta
import os


@receiver(user_logged_in)
def mostrar_mensaje_login(sender, user, request, **kwargs):
    messages.success(request, '¡Has iniciado sesión correctamente!')


@receiver(post_migrate)
def crear_admin_por_defecto(sender, app_config, **kwargs):
    """
    Crea automáticamente el usuario administrador por defecto después de las migraciones.
    
    Solo se ejecuta si:
    - La app es 'accounts'
    - El usuario 'admin' no existe
    - No estamos en modo test
    """
    # Solo ejecutar para la app accounts
    if app_config.name != 'apps.accounts':
        return
    
    # No ejecutar durante tests
    if 'test' in os.environ.get('DJANGO_SETTINGS_MODULE', '').lower():
        return
    
    # Verificar si el usuario admin ya existe
    if User.objects.filter(username='admin').exists():
        return
    
    # Crear usuario administrador por defecto
    try:
        # Usar contraseña por defecto (debe cambiarse en producción)
        default_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'admin123456')
        
        user = User.objects.create_user(
            username='admin',
            email='admin@teomanager.com',
            password=default_password,
            is_superuser=True,
            is_staff=True,
            is_active=True,
            first_name='Administrador',
            last_name='Sistema'
        )
        
        # Crear perfil de usuario con permisos de administrador
        # Fecha de vencimiento: 1 año desde ahora (suscripción permanente para admin)
        fecha_vencimiento = timezone.now() + timedelta(days=365)
        
        PerfilUsuario.objects.create(
            usuario=user,
            tipo_cuenta='empresa',
            empresa='Administración del Sistema',
            telefono='0000000000',
            direccion='Sistema',
            permisos='Administrador',
            estado_suscripcion='activa',
            fecha_vencimiento=fecha_vencimiento
        )
        
        # Log para debugging (solo en desarrollo)
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print('✅ Usuario administrador por defecto creado automáticamente')
            print(f'   Usuario: admin')
            print(f'   Contraseña: {default_password}')
            print('   ⚠️  IMPORTANTE: Cambia la contraseña después del primer login')
            
    except Exception as e:
        # No fallar si hay un error, solo loguear
        if os.getenv('DEBUG', 'False').lower() == 'true':
            print(f'⚠️  No se pudo crear el admin por defecto: {e}') 