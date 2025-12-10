"""
URLs para la aplicación de páginas web.

Este módulo define las rutas relacionadas con:
- Creación y edición de landing pages
- Visualización de landing pages
"""

from django.urls import path
from . import views

app_name = 'webpages'

urlpatterns = [
    # Crear/editar landing page (solo empresas)
    path('landingpage/create/', views.create_landing_page, name='create_landing_page'),
    
    # Ver landing page propia (solo empresas)
    path('landingpage/view/', views.landingpage_view, name='landingpage_view'),
    
    # Vista pública de landing page de empresa
    path('landingpage/<int:user_id>/', views.public_landing_page, name='public_landing_page'),
]

