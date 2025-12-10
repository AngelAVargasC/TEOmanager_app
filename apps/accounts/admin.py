from django.contrib import admin
from .models import PerfilUsuario, Suscripcion

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
