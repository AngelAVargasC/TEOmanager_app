"""
Comando de Django para limpiar el caché del dashboard.

Uso:
    python manage.py clear_dashboard_cache
    python manage.py clear_dashboard_cache --user 123
    python manage.py clear_dashboard_cache --all
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth.models import User
from apps.accounts.services import DashboardService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Limpia el caché del dashboard para mejorar el rendimiento'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=int,
            help='ID del usuario específico para limpiar su caché'
        )
        
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpia todo el caché del sistema'
        )
        
        parser.add_argument(
            '--warm-up',
            action='store_true', 
            help='Precarga el caché después de limpiarlo'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧹 Iniciando limpieza de caché del dashboard...')
        )
        
        if options['all']:
            # Limpiar todo el caché
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Todo el caché del sistema ha sido limpiado')
            )
            
        elif options['user']:
            # Limpiar caché de usuario específico
            user_id = options['user']
            try:
                user = User.objects.get(id=user_id)
                DashboardService.clear_dashboard_cache(user_id=user_id)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Caché del usuario {user.username} (ID: {user_id}) limpiado'
                    )
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Usuario con ID {user_id} no encontrado')
                )
                return
                
        else:
            # Limpiar solo caché de dashboard admin
            DashboardService.clear_dashboard_cache()
            self.stdout.write(
                self.style.SUCCESS('✅ Caché de métricas de admin limpiado')
            )
        
        # Precarga opcional
        if options['warm_up']:
            self.stdout.write('🔥 Precargando caché...')
            
            try:
                # Precargar métricas de admin
                DashboardService.get_admin_metrics(force_refresh=True)
                
                # Precargar dashboards de empresas activas (primeras 5)
                empresas = User.objects.filter(
                    userprofile__tipo_cuenta='empresa',
                    is_active=True
                )[:5]
                
                for empresa in empresas:
                    DashboardService.get_company_dashboard_data(empresa, force_refresh=True)
                    self.stdout.write(f'  📊 Dashboard de {empresa.username} precargado')
                
                self.stdout.write(
                    self.style.SUCCESS('🎉 Caché precargado exitosamente!')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error precargando caché: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Proceso completado. El dashboard debería cargar más rápido.')
        ) 