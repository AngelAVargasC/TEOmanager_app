"""
Servicios para la gestión de landing pages.

Este módulo contiene la lógica de negocio relacionada con:
- Creación y gestión de landing pages
- Preparación de contextos para renderizado
- Validaciones de límites de plan

Diseñado para escalabilidad: La lógica de negocio está separada
en servicios para facilitar mantenimiento y futura migración a microservicios.
"""

import logging
from .models import LandingPage
from apps.accounts.services import SuscripcionService

logger = logging.getLogger(__name__)


class LandingPageService:
    """
    Servicio para la gestión de landing pages.
    
    Maneja la creación, actualización y gestión de landing pages
    personalizadas para empresas.
    """
    
    @staticmethod
    def create_landing_page(user, titulo, descripcion='', plantilla='plantilla1', **kwargs):
        """
        Crea una nueva landing page para el usuario.
        
        Args:
            user (User): Usuario propietario
            titulo (str): Título de la landing page
            descripcion (str): Descripción
            plantilla (str): Plantilla a usar
            **kwargs: Campos adicionales
            
        Returns:
            LandingPage: Landing page creada
            
        Raises:
            ValueError: Si el plan del usuario no permite crear más landing pages
        """
        # Verificar límites del plan
        limits = SuscripcionService.check_plan_limits(user, 'landing_pages')
        if not limits['allowed']:
            raise ValueError(limits['message'])
        
        try:
            landing_page = LandingPage.objects.create(
                usuario=user,
                titulo=titulo,
                descripcion=descripcion,
                plantilla=plantilla,
                **kwargs
            )
            
            logger.info(f"Landing page creada para usuario {user.username}")
            return landing_page
            
        except Exception as e:
            logger.error(f"Error creando landing page para {user.username}: {str(e)}")
            raise
    
    @staticmethod
    def get_landing_page_context(landing_page):
        """
        Prepara el contexto para renderizar una landing page.
        
        Args:
            landing_page (LandingPage): Landing page
            
        Returns:
            dict: Contexto para el template
        """
        user = landing_page.usuario
        
        context = {
            'landing_page': landing_page,
            'empresa': user.userprofile.empresa if hasattr(user, 'userprofile') else '',
            'productos_destacados': user.productos.filter(activo=True)[:6],
            'servicios_destacados': user.servicios.filter(activo=True)[:6],
            'hero_image_url': landing_page.get_hero_image_url(),
            'tiene_imagen_hero': landing_page.tiene_imagen_hero,
        }
        
        return context

