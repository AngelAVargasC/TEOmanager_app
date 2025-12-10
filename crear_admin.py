#!/usr/bin/env python
"""
Script simple para convertir un usuario en administrador.
Usar: python crear_admin.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from apps.accounts.models import PerfilUsuario

def hacer_admin():
    """Convierte un usuario existente en administrador."""
    
    print("=== CREAR ADMINISTRADOR ===")
    print("Usuarios disponibles:")
    
    users = User.objects.all()
    if not users:
        print("No hay usuarios en el sistema.")
        return
    
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.username} ({user.email})")
    
    try:
        choice = int(input("Selecciona el número del usuario: ")) - 1
        selected_user = users[choice]
        
        # Crear o actualizar PerfilUsuario
        perfil, created = PerfilUsuario.objects.get_or_create(
            usuario=selected_user,
            defaults={
                'tipo_cuenta': 'empresa',
                'empresa': f'Admin Corp {selected_user.username}',
                'telefono': '123456789',
                'direccion': 'Dirección Admin',
                'permisos': 'Administrador'
            }
        )
        
        if not created:
            perfil.permisos = 'Administrador'
            perfil.save()
        
        # También hacer superuser
        selected_user.is_superuser = True
        selected_user.is_staff = True
        selected_user.save()
        
        print(f"✅ {selected_user.username} ahora es ADMINISTRADOR")
        print(f"   - PerfilUsuario.permisos = 'Administrador'")
        print(f"   - User.is_superuser = True")
        print(f"   - User.is_staff = True")
        
    except (ValueError, IndexError):
        print("❌ Selección inválida")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    hacer_admin() 