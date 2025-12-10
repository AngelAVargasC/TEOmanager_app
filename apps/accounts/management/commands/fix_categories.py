from django.core.management.base import BaseCommand
from django.core.cache import cache
from apps.productservice.models import Producto, Servicio
from django.db import transaction


class Command(BaseCommand):
    help = 'Limpia y normaliza las categorías duplicadas en productos y servicios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Limpiar el caché de categorías después de la corrección',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué cambios se harían sin aplicarlos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Iniciando limpieza de categorías...'))
        
        # Obtener todas las categorías existentes
        product_categories = Producto.objects.values_list('categoria', flat=True).distinct()
        service_categories = Servicio.objects.values_list('categoria', flat=True).distinct()
        
        all_categories = set(list(product_categories) + list(service_categories))
        
        # Mapear categorías similares
        category_mapping = {}
        processed_categories = set()
        
        for category in all_categories:
            if not category:
                continue
                
            clean_category = category.strip().title()
            
            # Buscar si ya existe una categoría similar
            found_similar = False
            for processed in processed_categories:
                if clean_category.lower() == processed.lower():
                    category_mapping[category] = processed
                    found_similar = True
                    break
            
            if not found_similar:
                category_mapping[category] = clean_category
                processed_categories.add(clean_category)
        
        # Mostrar cambios propuestos
        changes_count = 0
        for original, clean in category_mapping.items():
            if original != clean:
                changes_count += 1
                self.stdout.write(f'  📝 "{original}" → "{clean}"')
        
        if changes_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No se encontraron categorías duplicadas'))
            return
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'🔍 DRY RUN: Se aplicarían {changes_count} cambios'))
            return
        
        # Aplicar cambios
        with transaction.atomic():
            # Actualizar productos
            for original, clean in category_mapping.items():
                if original != clean:
                    productos_updated = Producto.objects.filter(categoria=original).update(categoria=clean)
                    servicios_updated = Servicio.objects.filter(categoria=original).update(categoria=clean)
                    
                    if productos_updated > 0:
                        self.stdout.write(f'  ✅ {productos_updated} productos actualizados: "{original}" → "{clean}"')
                    if servicios_updated > 0:
                        self.stdout.write(f'  ✅ {servicios_updated} servicios actualizados: "{original}" → "{clean}"')
        
        # Limpiar caché si se solicita
        if options['clear_cache']:
            cache.delete('product_categories')
            cache.delete('category_counts')
            self.stdout.write(self.style.SUCCESS('🗑️ Caché de categorías limpiado'))
        
        # Mostrar resumen final
        final_categories = set(Producto.objects.values_list('categoria', flat=True).distinct())
        final_categories.update(Servicio.objects.values_list('categoria', flat=True).distinct())
        final_categories.discard(None)
        final_categories.discard('')
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Limpieza completada!'))
        self.stdout.write(f'📊 Categorías finales ({len(final_categories)}):')
        for cat in sorted(final_categories):
            self.stdout.write(f'  - {cat}') 