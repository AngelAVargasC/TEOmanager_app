"""
Template tags personalizados para la app webpages.

Proporciona filtros y tags útiles para trabajar con landing pages
y plantillas en los templates.
"""

from django import template

register = template.Library()


@register.filter
def get_hero_url(landing):
    """
    Obtiene la URL de la imagen hero de una landing page.
    
    Usage:
        {{ landing|get_hero_url }}
    """
    if landing:
        return landing.get_hero_image_url()
    return ''


@register.filter
def has_hero_image(landing):
    """
    Verifica si una landing page tiene imagen hero.
    
    Usage:
        {% if landing|has_hero_image %}
    """
    if landing:
        return landing.tiene_imagen_hero
    return False

