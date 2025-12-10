import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.productservice.models import ImagenProducto, ImagenServicio, Servicio

class Command(BaseCommand):
    help = 'Elimina archivos de imagen huérfanos que no tienen registro en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué archivos se eliminarían sin eliminarlos realmente',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: Solo mostrando archivos que se eliminarían'))
        
        # Directorios de imágenes
        productos_dir = os.path.join(settings.MEDIA_ROOT, 'productos')
        servicios_dir = os.path.join(settings.MEDIA_ROOT, 'servicios')
        
        archivos_eliminados = 0
        
        # Limpiar imágenes de productos
        if os.path.exists(productos_dir):
            archivos_eliminados += self.limpiar_directorio(
                productos_dir, 
                ImagenProducto, 
                'imagen', 
                'productos/',
                dry_run
            )
        
        # Limpiar imágenes de servicios (múltiples)
        if os.path.exists(servicios_dir):
            archivos_eliminados += self.limpiar_directorio(
                servicios_dir, 
                ImagenServicio, 
                'imagen', 
                'servicios/',
                dry_run
            )
            
            # También limpiar imágenes principales de servicios
            archivos_eliminados += self.limpiar_imagenes_principales_servicios(
                servicios_dir,
                dry_run
            )
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'Se eliminarían {archivos_eliminados} archivos huérfanos')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Se eliminaron {archivos_eliminados} archivos huérfanos')
            )

    def limpiar_directorio(self, directorio, modelo, campo_imagen, prefijo_url, dry_run):
        """Limpia archivos huérfanos en un directorio específico"""
        archivos_eliminados = 0
        
        # Obtener todas las rutas de imágenes en la BD
        imagenes_bd = set()
        for obj in modelo.objects.all():
            imagen_field = getattr(obj, campo_imagen)
            if imagen_field:
                # Obtener solo el nombre del archivo sin el prefijo
                nombre_archivo = imagen_field.name.replace(prefijo_url, '')
                imagenes_bd.add(nombre_archivo)
        
        # Recorrer archivos en el directorio
        for archivo in os.listdir(directorio):
            ruta_completa = os.path.join(directorio, archivo)
            
            # Solo procesar archivos (no directorios)
            if os.path.isfile(ruta_completa):
                if archivo not in imagenes_bd:
                    if dry_run:
                        self.stdout.write(f'Se eliminaría: {ruta_completa}')
                    else:
                        try:
                            os.remove(ruta_completa)
                            self.stdout.write(f'Eliminado: {ruta_completa}')
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error eliminando {ruta_completa}: {e}')
                            )
                    archivos_eliminados += 1
        
        return archivos_eliminados

    def limpiar_imagenes_principales_servicios(self, directorio, dry_run):
        """Limpia imágenes principales de servicios huérfanas"""
        archivos_eliminados = 0
        
        # Obtener todas las rutas de imágenes principales de servicios en la BD
        imagenes_principales_bd = set()
        for servicio in Servicio.objects.all():
            if servicio.imagen:
                nombre_archivo = servicio.imagen.name.replace('servicios/', '')
                imagenes_principales_bd.add(nombre_archivo)
        
        # Obtener todas las imágenes múltiples de servicios
        imagenes_multiples_bd = set()
        for imagen in ImagenServicio.objects.all():
            if imagen.imagen:
                nombre_archivo = imagen.imagen.name.replace('servicios/', '')
                imagenes_multiples_bd.add(nombre_archivo)
        
        # Combinar ambos conjuntos
        todas_imagenes_servicios = imagenes_principales_bd.union(imagenes_multiples_bd)
        
        # Recorrer archivos en el directorio
        for archivo in os.listdir(directorio):
            ruta_completa = os.path.join(directorio, archivo)
            
            # Solo procesar archivos (no directorios)
            if os.path.isfile(ruta_completa):
                if archivo not in todas_imagenes_servicios:
                    if dry_run:
                        self.stdout.write(f'Se eliminaría (servicio): {ruta_completa}')
                    else:
                        try:
                            os.remove(ruta_completa)
                            self.stdout.write(f'Eliminado (servicio): {ruta_completa}')
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'Error eliminando {ruta_completa}: {e}')
                            )
                    archivos_eliminados += 1
        
        return archivos_eliminados 