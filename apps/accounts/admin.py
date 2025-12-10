from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PerfilUsuario, Suscripcion
from .services import UserService

# Desregistrar el UserAdmin por defecto de Django si está registrado
if admin.site.is_registered(User):
    admin.site.unregister(User)

# Configuración del panel de administración para el modelo PerfilUsuario.
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'telefono', 'permisos', 'estado_suscripcion')  # Columnas visibles en la lista
    list_filter = ('permisos', 'estado_suscripcion')  # Filtros laterales
    search_fields = ('usuario__username', 'empresa', 'telefono')  # Campos de búsqueda
    list_editable = ('permisos', 'estado_suscripcion')  # Permite editar estos campos directamente en la lista

# Configuración del panel de administración para el modelo Suscripcion.
@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plan', 'fecha_inicio', 'fecha_vencimiento', 'precio', 'activa')  # Columnas visibles
    list_filter = ('plan', 'activa')  # Filtros laterales
    search_fields = ('usuario__username',)  # Campos de búsqueda


# Configuración personalizada del admin de User para eliminar completamente
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin personalizado para User que elimina completamente los usuarios
    y todos sus datos relacionados cuando se eliminan desde el admin.
    """
    
    def delete_model(self, request, obj):
        """
        Elimina completamente un usuario cuando se elimina desde el admin.
        """
        # Prevenir auto-eliminación
        if request.user.id == obj.id:
            messages.error(request, 'No puedes eliminar tu propia cuenta.')
            return
        
        # Prevenir eliminación de superusuarios
        if obj.is_superuser:
            messages.error(request, 'No se pueden eliminar superusuarios desde esta interfaz.')
            return
        
        try:
            # Usar el servicio para eliminar completamente
            deleted_summary = UserService.delete_user_completely(obj)
            
            # Mensaje de éxito
            summary_text = f"Usuario '{obj.username}' eliminado completamente. "
            summary_text += f"Eliminados: {deleted_summary['productos']} productos, "
            summary_text += f"{deleted_summary['servicios']} servicios, "
            summary_text += f"{deleted_summary['pedidos']} pedidos."
            
            messages.success(request, summary_text)
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error al eliminar el usuario: {str(e)}')
    
    def delete_queryset(self, request, queryset):
        """
        Elimina completamente múltiples usuarios cuando se eliminan desde el admin.
        """
        deleted_count = 0
        errors = []
        
        for user in queryset:
            # Prevenir auto-eliminación
            if request.user.id == user.id:
                errors.append(f"No puedes eliminar tu propia cuenta ({user.username})")
                continue
            
            # Prevenir eliminación de superusuarios
            if user.is_superuser:
                errors.append(f"No se pueden eliminar superusuarios ({user.username})")
                continue
            
            try:
                UserService.delete_user_completely(user)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Error eliminando {user.username}: {str(e)}")
        
        if deleted_count > 0:
            messages.success(request, f'{deleted_count} usuario(s) eliminado(s) completamente.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
