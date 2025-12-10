"""
Comando para verificar y corregir problemas de imágenes en productos.

Uso:
    python manage.py fix_product_images
    python manage.py fix_product_images --check-only
    python manage.py fix_product_images --set-principals
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.productservice.models import Producto, ImagenProducto
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifica y corrige problemas de imágenes en productos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Solo verificar problemas sin corregir'
        )
        
        parser.add_argument(
            '--set-principals',
            action='store_true',
            help='Marcar automáticamente imágenes principales para productos que no las tienen'
        )
        
        parser.add_argument(
            '--remove-missing',
            action='store_true',
            help='Remover registros de imágenes cuyos archivos no existen'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Verificando imágenes de productos...')
        )
        
        # Estadísticas generales
        total_productos = Producto.objects.count()
        productos_con_imagenes = Producto.objects.filter(imagenes__isnull=False).distinct().count()
        productos_sin_imagenes = total_productos - productos_con_imagenes
        
        self.stdout.write(f"📊 Total de productos: {total_productos}")
        self.stdout.write(f"📷 Productos con imágenes: {productos_con_imagenes}")
        self.stdout.write(f"🚫 Productos sin imágenes: {productos_sin_imagenes}")
        
        # Verificar productos sin imagen principal
        productos_sin_principal = []
        productos_con_multiples_principales = []
        imagenes_rotas = []
        
        for producto in Producto.objects.prefetch_related('imagenes'):
            imagenes = producto.imagenes.all()
            
            if imagenes.exists():
                principales = imagenes.filter(principal=True)
                
                if principales.count() == 0:
                    productos_sin_principal.append(producto)
                elif principales.count() > 1:
                    productos_con_multiples_principales.append(producto)
                
                # Verificar si los archivos existen
                for imagen in imagenes:
                    if not os.path.exists(imagen.imagen.path):
                        imagenes_rotas.append(imagen)
        
        # Reportar problemas encontrados
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🔍 PROBLEMAS ENCONTRADOS:")
        
        if productos_sin_principal:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {len(productos_sin_principal)} productos con imágenes pero sin imagen principal"
                )
            )
            for producto in productos_sin_principal[:5]:  # Mostrar solo primeros 5
                self.stdout.write(f"  - {producto.nombre} (ID: {producto.id})")
            if len(productos_sin_principal) > 5:
                self.stdout.write(f"  ... y {len(productos_sin_principal) - 5} más")
        
        if productos_con_multiples_principales:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {len(productos_con_multiples_principales)} productos con múltiples imágenes principales"
                )
            )
            for producto in productos_con_multiples_principales:
                self.stdout.write(f"  - {producto.nombre} (ID: {producto.id})")
        
        if imagenes_rotas:
            self.stdout.write(
                self.style.ERROR(
                    f"❌ {len(imagenes_rotas)} imágenes con archivos faltantes"
                )
            )
            for imagen in imagenes_rotas[:5]:  # Mostrar solo primeras 5
                self.stdout.write(f"  - {imagen.imagen.name} (Producto: {imagen.producto.nombre})")
            if len(imagenes_rotas) > 5:
                self.stdout.write(f"  ... y {len(imagenes_rotas) - 5} más")
        
        if not any([productos_sin_principal, productos_con_multiples_principales, imagenes_rotas]):
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron problemas"))
        
        # Si solo es verificación, terminar aquí
        if options['check_only']:
            return
        
        # Aplicar correcciones
        self.stdout.write("\n" + "="*50)
        self.stdout.write("🔧 APLICANDO CORRECCIONES:")
        
        correcciones_aplicadas = 0
        
        # Corregir productos sin imagen principal
        if options['set_principals'] and productos_sin_principal:
            self.stdout.write("🖼️  Estableciendo imágenes principales...")
            
            for producto in productos_sin_principal:
                primera_imagen = producto.imagenes.first()
                if primera_imagen:
                    primera_imagen.principal = True
                    primera_imagen.save()
                    correcciones_aplicadas += 1
                    self.stdout.write(f"  ✅ {producto.nombre}: imagen principal establecida")
        
        # Corregir múltiples principales
        if productos_con_multiples_principales:
            self.stdout.write("🔄 Corrigiendo múltiples principales...")
            
            for producto in productos_con_multiples_principales:
                # Mantener solo la primera como principal
                principales = producto.imagenes.filter(principal=True).order_by('fecha_subida')
                for i, imagen in enumerate(principales):
                    if i > 0:  # Dejar solo la primera
                        imagen.principal = False
                        imagen.save()
                        correcciones_aplicadas += 1
                self.stdout.write(f"  ✅ {producto.nombre}: principal única establecida")
        
        # Remover imágenes rotas
        if options['remove_missing'] and imagenes_rotas:
            self.stdout.write("🗑️  Removiendo imágenes con archivos faltantes...")
            
            for imagen in imagenes_rotas:
                producto_nombre = imagen.producto.nombre
                imagen.delete()
                correcciones_aplicadas += 1
                self.stdout.write(f"  ✅ Removida imagen rota de: {producto_nombre}")
        
        # Estadísticas finales
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📈 RESUMEN:")
        self.stdout.write(f"🔧 Correcciones aplicadas: {correcciones_aplicadas}")
        
        if correcciones_aplicadas > 0:
            self.stdout.write(
                self.style.SUCCESS("🎉 ¡Problemas corregidos exitosamente!")
            )
            self.stdout.write("💡 Sugerencia: Recarga tu página web para ver los cambios")
        else:
            self.stdout.write("ℹ️  No se aplicaron correcciones. Usa --set-principals o --remove-missing para corregir problemas")
        
        # Mostrar comandos útiles
        self.stdout.write("\n📝 COMANDOS ÚTILES:")
        self.stdout.write("  python manage.py fix_product_images --set-principals")
        self.stdout.write("  python manage.py fix_product_images --remove-missing")
        self.stdout.write("  python manage.py clear_dashboard_cache --warm-up") 