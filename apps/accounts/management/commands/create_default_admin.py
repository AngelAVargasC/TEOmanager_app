"""
Comando de Django para crear el usuario administrador por defecto.

Este comando crea automáticamente un usuario administrador con:
- Usuario: admin
- Email: admin@teomanager.com
- PerfilUsuario con permisos de Administrador
- is_superuser = True
- is_staff = True

Uso:
    python manage.py create_default_admin
    python manage.py create_default_admin --username miadmin --email admin@miempresa.com
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import PerfilUsuario
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import getpass


class Command(BaseCommand):
    help = 'Crea el usuario administrador por defecto del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='admin',
            help='Nombre de usuario para el administrador (default: admin)'
        )
        
        parser.add_argument(
            '--email',
            type=str,
            default='admin@teomanager.com',
            help='Email para el administrador (default: admin@teomanager.com)'
        )
        
        parser.add_argument(
            '--password',
            type=str,
            help='Contraseña para el administrador (si no se proporciona, se pedirá)'
        )
        
        parser.add_argument(
            '--skip-if-exists',
            action='store_true',
            help='No hacer nada si el usuario ya existe'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        skip_if_exists = options['skip_if_exists']
        
        self.stdout.write(
            self.style.WARNING('🔐 Creando usuario administrador por defecto...')
        )
        
        # Verificar si el usuario ya existe
        if User.objects.filter(username=username).exists():
            if skip_if_exists:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  El usuario "{username}" ya existe. Saltando creación.'
                    )
                )
                return
            
            self.stdout.write(
                self.style.ERROR(
                    f'❌ El usuario "{username}" ya existe. '
                    'Usa --skip-if-exists para saltar o elige otro username.'
                )
            )
            return
        
        # Solicitar contraseña si no se proporcionó
        if not password:
            self.stdout.write('Por favor, ingresa la contraseña para el administrador:')
            password = getpass.getpass('Contraseña: ')
            password_confirm = getpass.getpass('Confirma la contraseña: ')
            
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('❌ Las contraseñas no coinciden')
                )
                return
            
            if len(password) < 8:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  La contraseña es muy corta (mínimo 8 caracteres recomendado)'
                    )
                )
        
        try:
            with transaction.atomic():
                # Crear usuario
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_superuser=True,
                    is_staff=True,
                    is_active=True,
                    first_name='Administrador',
                    last_name='Sistema'
                )
                
                # Crear perfil de usuario con permisos de administrador
                # Fecha de vencimiento: 1 año desde ahora (suscripción permanente para admin)
                fecha_vencimiento = timezone.now() + timedelta(days=365)
                
                perfil = PerfilUsuario.objects.create(
                    usuario=user,
                    tipo_cuenta='empresa',
                    empresa='Administración del Sistema',
                    telefono='0000000000',
                    direccion='Sistema',
                    permisos='Administrador',
                    estado_suscripcion='activa',
                    fecha_vencimiento=fecha_vencimiento
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Usuario administrador creado exitosamente!\n'
                        f'   Usuario: {username}\n'
                        f'   Email: {email}\n'
                        f'   Perfil: {perfil.get_permisos_display()}\n'
                        f'   Tipo de cuenta: {perfil.get_tipo_cuenta_display()}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando administrador: {e}')
            )
            raise

