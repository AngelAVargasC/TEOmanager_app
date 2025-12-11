"""
Comando de gestión para inicializar el sitio de Django Sites Framework.

Este comando configura automáticamente el sitio con el dominio correcto
según el entorno (producción, staging, desarrollo).
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Inicializa el sitio de Django Sites Framework con el dominio correcto'

    def handle(self, *args, **options):
        try:
            # Obtener el dominio desde SITE_URL o configuración
            domain = None
            
            # Prioridad 1: SITE_URL de settings
            if hasattr(settings, 'SITE_URL') and settings.SITE_URL:
                site_url = settings.SITE_URL
                # Extraer dominio sin protocolo
                domain = site_url.replace('https://', '').replace('http://', '').rstrip('/')
            
            # Prioridad 2: RAILWAY_PUBLIC_DOMAIN
            if not domain:
                railway_custom = os.getenv('RAILWAY_PUBLIC_DOMAIN', '')
                if railway_custom:
                    domain = railway_custom.replace('https://', '').replace('http://', '').rstrip('/')
            
            # Prioridad 3: RAILWAY_DOMAIN
            if not domain:
                if settings.IS_RAILWAY:
                    railway_domain = os.getenv('RAILWAY_DOMAIN', 'web-production-8666.up.railway.app')
                    domain = railway_domain
            
            # Prioridad 4: Fallback según entorno
            if not domain:
                if settings.IS_PRODUCTION:
                    domain = 'teomanager.com'
                elif settings.IS_STAGING:
                    domain = 'teomanager.com'
                else:
                    domain = 'localhost:5490'
            
            # Obtener o crear el sitio
            site, created = Site.objects.get_or_create(
                pk=settings.SITE_ID,
                defaults={
                    'domain': domain,
                    'name': 'TEOmanager'
                }
            )
            
            # Actualizar si ya existía pero con dominio diferente
            if not created and (site.domain != domain or site.name != 'TEOmanager'):
                site.domain = domain
                site.name = 'TEOmanager'
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Sitio actualizado: {site.domain}')
                )
            elif created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Sitio creado: {site.domain}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Sitio ya configurado: {site.domain}')
                )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n📋 Configuración del sitio:')
            )
            self.stdout.write(f'   ID: {site.id}')
            self.stdout.write(f'   Dominio: {site.domain}')
            self.stdout.write(f'   Nombre: {site.name}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error inicializando sitio: {str(e)}')
            )
            # No lanzar excepción para que el deployment continúe
            return

