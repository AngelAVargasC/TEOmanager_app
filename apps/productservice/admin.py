from django.contrib import admin
from .models import MensajePedido, Pedido

@admin.register(MensajePedido)
class MensajePedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'remitente', 'fecha_creacion', 'leido', 'tiene_adjunto')
    list_filter = ('leido', 'fecha_creacion', 'pedido__estado')
    search_fields = ('mensaje', 'pedido__id', 'remitente__username')
    readonly_fields = ('fecha_creacion',)
    date_hierarchy = 'fecha_creacion'
    
    fieldsets = (
        ('Información del Mensaje', {
            'fields': ('pedido', 'remitente', 'mensaje', 'archivo_adjunto')
        }),
        ('Estado', {
            'fields': ('leido', 'fecha_creacion')
        }),
    )
    
    def tiene_adjunto(self, obj):
        return bool(obj.archivo_adjunto)
    tiene_adjunto.boolean = True
    tiene_adjunto.short_description = 'Tiene Adjunto'
