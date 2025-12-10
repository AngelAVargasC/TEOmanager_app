#!/usr/bin/env python
"""
Script de optimización de rendimiento para el dashboard.
Crea índices en la base de datos y configura caché para mejorar la velocidad.

Uso:
    python optimization_script.py
"""

import os
import django
import sys
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django.core.cache import cache
from django.contrib.auth.models import User
from apps.accounts.models import PerfilUsuario
from apps.productservice.models import Producto, Servicio, Pedido
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """Optimizador de base de datos para mejorar el rendimiento."""
    
    def __init__(self):
        self.cursor = connection.cursor()
        
    def create_dashboard_indexes(self):
        """Crea índices específicos para optimizar el dashboard."""
        
        indexes = [
            # Índices para PerfilUsuario
            {
                'name': 'idx_perfilusuario_tipo_cuenta',
                'table': 'accounts_perfilusuario',
                'fields': ['tipo_cuenta'],
                'description': 'Optimiza filtros por tipo de cuenta'
            },
            {
                'name': 'idx_perfilusuario_permisos',
                'table': 'accounts_perfilusuario', 
                'fields': ['permisos'],
                'description': 'Optimiza filtros por permisos de admin'
            },
            {
                'name': 'idx_perfilusuario_usuario_tipo',
                'table': 'accounts_perfilusuario',
                'fields': ['usuario_id', 'tipo_cuenta'],
                'description': 'Optimiza consultas de usuario + tipo'
            },
            
            # Índices para Producto
            {
                'name': 'idx_producto_usuario_activo',
                'table': 'productservice_producto',
                'fields': ['usuario_id', 'activo'],
                'description': 'Optimiza consultas de productos por usuario y estado'
            },
            {
                'name': 'idx_producto_activo_fecha',
                'table': 'productservice_producto',
                'fields': ['activo', 'fecha_creacion'],
                'description': 'Optimiza listados de productos activos por fecha'
            },
            {
                'name': 'idx_producto_categoria_activo',
                'table': 'productservice_producto',
                'fields': ['categoria', 'activo'],
                'description': 'Optimiza filtros por categoría'
            },
            
            # Índices para Servicio
            {
                'name': 'idx_servicio_usuario_activo',
                'table': 'productservice_servicio',
                'fields': ['usuario_id', 'activo'],
                'description': 'Optimiza consultas de servicios por usuario y estado'
            },
            {
                'name': 'idx_servicio_activo_fecha',
                'table': 'productservice_servicio',
                'fields': ['activo', 'fecha_creacion'],
                'description': 'Optimiza listados de servicios activos por fecha'
            },
            
            # Índices para Pedido
            {
                'name': 'idx_pedido_usuario_fecha',
                'table': 'productservice_pedido',
                'fields': ['usuario_id', 'fecha_pedido'],
                'description': 'Optimiza consultas de pedidos por usuario y fecha'
            },
            {
                'name': 'idx_pedido_fecha_desc',
                'table': 'productservice_pedido',
                'fields': ['fecha_pedido DESC'],
                'description': 'Optimiza ordenamiento de pedidos por fecha descendente'
            },
            
            # Índices para User
            {
                'name': 'idx_user_active',
                'table': 'auth_user',
                'fields': ['is_active'],
                'description': 'Optimiza filtros por usuario activo'
            },
            
            # Índices para imágenes
            {
                'name': 'idx_imagenproducto_principal',
                'table': 'productservice_imagenproducto',
                'fields': ['producto_id', 'principal'],
                'description': 'Optimiza búsqueda de imagen principal'
            },
            {
                'name': 'idx_imagenservicio_principal',
                'table': 'productservice_imagenservicio',
                'fields': ['servicio_id', 'principal'],
                'description': 'Optimiza búsqueda de imagen principal de servicio'
            }
        ]
        
        logger.info("🔧 Iniciando creación de índices de base de datos...")
        
        for index in indexes:
            try:
                # Verificar si el índice ya existe
                check_query = f"""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='{index['name']}'
                """
                self.cursor.execute(check_query)
                
                if self.cursor.fetchone():
                    logger.info(f"⚠️  Índice {index['name']} ya existe, omitiendo...")
                    continue
                
                # Crear el índice
                fields_str = ', '.join(index['fields'])
                create_query = f"""
                CREATE INDEX {index['name']} 
                ON {index['table']} ({fields_str})
                """
                
                self.cursor.execute(create_query)
                logger.info(f"✅ Índice creado: {index['name']} - {index['description']}")
                
            except Exception as e:
                logger.error(f"❌ Error creando índice {index['name']}: {e}")
        
        logger.info("🎉 Índices de base de datos creados exitosamente!")
    
    def analyze_database(self):
        """Analiza y actualiza estadísticas de la base de datos."""
        try:
            self.cursor.execute("ANALYZE")
            logger.info("📊 Estadísticas de base de datos actualizadas")
        except Exception as e:
            logger.error(f"❌ Error analizando base de datos: {e}")
    
    def get_database_info(self):
        """Obtiene información sobre el estado de la base de datos."""
        try:
            # Obtener información de tablas
            self.cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='table' AND name LIKE '%product%' 
                OR name LIKE '%user%' OR name LIKE '%perfil%'
            """)
            
            tables = self.cursor.fetchall()
            logger.info("📋 Tablas principales encontradas:")
            for table in tables:
                logger.info(f"  - {table[0]}")
            
            # Obtener información de índices
            self.cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name LIKE 'idx_%'
            """)
            
            indexes = self.cursor.fetchall()
            logger.info(f"📇 Índices personalizados: {len(indexes)}")
            for index in indexes:
                logger.info(f"  - {index[0]}")
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo información de BD: {e}")


class CacheOptimizer:
    """Optimizador de caché para el dashboard."""
    
    def __init__(self):
        self.cache = cache
        
    def warm_up_cache(self):
        """Precarga datos frecuentemente usados en caché."""
        logger.info("🔥 Iniciando precarga de caché...")
        
        try:
            from apps.accounts.services import DashboardService
            
            # Precargar métricas de admin
            logger.info("📊 Precargando métricas de administración...")
            DashboardService.get_admin_metrics(force_refresh=True)
            
            # Precargar categorías de productos
            logger.info("🏷️  Precargando categorías de productos...")
            categories = Producto.objects.filter(
                usuario__userprofile__tipo_cuenta='empresa',
                activo=True
            ).values_list('categoria', flat=True).distinct()
            self.cache.set('product_categories', list(categories), 300)
            
            # Precargar dashboards de empresas activas (primeras 10)
            logger.info("🏢 Precargando dashboards de empresas...")
            empresas = User.objects.filter(
                userprofile__tipo_cuenta='empresa',
                is_active=True
            )[:10]
            
            for empresa in empresas:
                DashboardService.get_company_dashboard_data(empresa, force_refresh=True)
            
            logger.info("✅ Caché precargado exitosamente!")
            
        except Exception as e:
            logger.error(f"❌ Error precargando caché: {e}")
    
    def clear_all_cache(self):
        """Limpia todo el caché."""
        try:
            self.cache.clear()
            logger.info("🧹 Caché limpiado completamente")
        except Exception as e:
            logger.error(f"❌ Error limpiando caché: {e}")
    
    def get_cache_stats(self):
        """Obtiene estadísticas del caché."""
        try:
            # Test básico de caché
            test_key = 'optimization_test'
            self.cache.set(test_key, 'test_value', 10)
            
            if self.cache.get(test_key) == 'test_value':
                logger.info("✅ Caché funcionando correctamente")
                self.cache.delete(test_key)
            else:
                logger.warning("⚠️  Caché no está funcionando correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error verificando caché: {e}")


class PerformanceOptimizer:
    """Optimizador general de rendimiento."""
    
    def __init__(self):
        self.db_optimizer = DatabaseOptimizer()
        self.cache_optimizer = CacheOptimizer()
    
    def run_full_optimization(self):
        """Ejecuta optimización completa del sistema."""
        logger.info("🚀 Iniciando optimización completa del sistema...")
        logger.info("=" * 60)
        
        # 1. Optimizar base de datos
        logger.info("🔧 FASE 1: Optimización de Base de Datos")
        self.db_optimizer.get_database_info()
        self.db_optimizer.create_dashboard_indexes()
        self.db_optimizer.analyze_database()
        
        logger.info("")
        
        # 2. Optimizar caché
        logger.info("🔥 FASE 2: Optimización de Caché")
        self.cache_optimizer.get_cache_stats()
        self.cache_optimizer.clear_all_cache()
        self.cache_optimizer.warm_up_cache()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 ¡Optimización completa finalizada!")
        logger.info("📈 Tu dashboard debería cargar mucho más rápido ahora.")
        logger.info("=" * 60)
    
    def run_quick_optimization(self):
        """Ejecuta optimización rápida (solo caché)."""
        logger.info("⚡ Ejecutando optimización rápida...")
        self.cache_optimizer.clear_all_cache()
        self.cache_optimizer.warm_up_cache()
        logger.info("✅ Optimización rápida completada!")


def main():
    """Función principal del script."""
    optimizer = PerformanceOptimizer()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'quick':
        optimizer.run_quick_optimization()
    else:
        optimizer.run_full_optimization()


if __name__ == '__main__':
    main() 