from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .password_reset_views import PasswordResetView

urlpatterns = [
    path('', views.landing, name='landing'),  # Página de inicio pública
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),  # Login de usuario
    path('logout/', views.logout_view, name='logout'),  # Logout de usuario
    path('register/', views.register, name='register'),  # Registro de usuario
    path('home/', views.home, name='home'),  # Dashboard del usuario autenticado
    path('perfil/', views.perfil, name='perfil'),  # Perfil del usuario
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),  # Editar perfil del usuario
    
    # Marketplace global para consumidores
    path('marketplace/', views.marketplace, name='marketplace'),
    # Vista pública de empresa: landing o catálogo
    path('company/<int:user_id>/', views.public_company_page, name='company_page'),
    # Catálogo completo de empresa (plantilla premium)
    path('company/<int:user_id>/catalog/', views.company_full_catalog, name='company_catalog_full'),
    
    # URLs del panel de administración
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Dashboard de admin
    path('dashboard/users/', views.manage_users, name='manage_users'),  # Gestión de usuarios
    path('dashboard/users/<int:user_id>/', views.user_detail, name='user_detail'),  # Detalle de usuario
    path('dashboard/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),  # Eliminar usuario
    path('dashboard/users/<int:user_id>/products/', views.admin_products, name='admin_products'),  # Productos de usuario
    path('dashboard/users/<int:user_id>/services/', views.admin_services, name='admin_services'),  # Servicios de usuario
    path('dashboard/users/<int:user_id>/orders/', views.admin_orders, name='admin_orders'),  # Pedidos de usuario
    path('dashboard/toggle-user-status/', views.toggle_user_status, name='toggle_user_status'),  # Activar/desactivar usuario
    
    # URLs de recuperación de contraseña
    path('password_reset/', PasswordResetView.as_view(template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
    
    # Rutas para carrito de compras (usuarios consumidores)
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/buy/<int:product_id>/', views.buy_now, name='buy_now'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart-preview/', views.cart_preview, name='cart_preview'),
    
    # URLs de pedidos - Vista del consumidor
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('pedido/<int:pedido_id>/', views.pedido_detail, name='pedido_detail'),
    
    # URLs de pedidos - Vista de la empresa
    path('pedidos-empresa/', views.pedidos_empresa, name='pedidos_empresa'),
    path('pedido-empresa/<int:pedido_id>/', views.pedido_empresa_detail, name='pedido_empresa_detail'),
    path('pedido/<int:pedido_id>/update-status/', views.update_pedido_status, name='update_pedido_status'),
] 