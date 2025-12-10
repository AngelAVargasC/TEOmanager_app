from django.urls import path
from apps.productservice import views

app_name = 'products'

urlpatterns = [
    path('productos/', views.productos, name='productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:pk>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:pk>/', views.eliminar_producto, name='eliminar_producto'),
    path('productos/imagen/eliminar/<int:imagen_id>/', views.eliminar_imagen_producto, name='eliminar_imagen_producto'),
    path('productos/imagen/principal/<int:imagen_id>/', views.marcar_principal_imagen_producto, name='marcar_principal_imagen_producto'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/crear/', views.crear_servicio, name='crear_servicio'),
    path('servicios/editar/<int:pk>/', views.editar_servicio, name='editar_servicio'),
    path('servicios/eliminar/<int:pk>/', views.eliminar_servicio, name='eliminar_servicio'),
    path('servicios/imagen/eliminar/<int:imagen_id>/', views.eliminar_imagen_servicio, name='eliminar_imagen_servicio'),
    path('servicios/imagen/principal/<int:imagen_id>/', views.marcar_principal_imagen_servicio, name='marcar_principal_imagen_servicio'),
    path('pedidos/', views.pedidos, name='pedidos'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('servicio/<int:pk>/', views.detalle_servicio, name='detalle_servicio'),
    # URLs para editar políticas
    path('producto/<int:pk>/politicas/', views.editar_politicas_producto, name='editar_politicas_producto'),
    path('servicio/<int:pk>/politicas/', views.editar_politicas_servicio, name='editar_politicas_servicio'),
    path('producto/<int:pk>/politicas/resetear/', views.resetear_politicas_producto, name='resetear_politicas_producto'),
    path('servicio/<int:pk>/politicas/resetear/', views.resetear_politicas_servicio, name='resetear_politicas_servicio'),
    # URLs para mensajería de pedidos
    path('pedido/<int:pedido_id>/mensajes/', views.obtener_mensajes_pedido, name='obtener_mensajes_pedido'),
    path('pedido/<int:pedido_id>/mensajes/enviar/', views.enviar_mensaje_pedido, name='enviar_mensaje_pedido'),
    path('pedido/<int:pedido_id>/mensajes/marcar-leidos/', views.marcar_mensajes_leidos, name='marcar_mensajes_leidos'),
    # URLs para notificaciones
    path('mensajes/conteo/', views.conteo_mensajes_no_leidos, name='conteo_mensajes_no_leidos'),
    path('mensajes/notificaciones/', views.notificaciones_mensajes, name='notificaciones_mensajes'),
    path('mensajes/chats-actualizados/', views.obtener_chats_actualizados, name='obtener_chats_actualizados'),
] 