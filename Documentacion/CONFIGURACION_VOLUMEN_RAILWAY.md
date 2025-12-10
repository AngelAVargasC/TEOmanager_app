# Configuración de Volumen Persistente en Railway

## ⚠️ Problema: Archivos Media se Pierden al Actualizar

En Railway (y la mayoría de plataformas PaaS), el sistema de archivos es **efímero**. Esto significa que:

- ❌ Los archivos subidos por usuarios (imágenes, documentos) se **pierden** al redeployar
- ❌ Cada actualización de código crea un nuevo contenedor limpio
- ❌ Los archivos en `media/` no persisten entre deployments

## ✅ Solución: Volumen Persistente de Railway

Railway ofrece **Volumes** (volúmenes persistentes) que mantienen los archivos entre deployments.

---

## 📋 Paso a Paso: Configurar Volumen Persistente

### Paso 1: Crear el Volumen en Railway

1. Ve a tu proyecto en Railway: https://railway.app
2. Selecciona tu servicio **web** (el que ejecuta Django)
3. Ve a la pestaña **"Volumes"** (o busca "Add Volume" en la configuración)
4. Haz clic en **"New Volume"** o **"Add Volume"**
5. Configura el volumen:
   - **Name**: `media-storage` (o el nombre que prefieras)
   - **Mount Path**: `/data` (este es el path donde se montará el volumen)
   - **Size**: Elige el tamaño según tus necesidades (ej: 10GB, 20GB, etc.)

### Paso 2: Configurar Variable de Entorno

1. En Railway, ve a tu servicio **web**
2. Ve a la pestaña **"Variables"**
3. Agrega la siguiente variable de entorno:
   ```
   USE_RAILWAY_VOLUME=True
   ```
4. (Opcional) Si montaste el volumen en una ruta diferente a `/data`, agrega:
   ```
   RAILWAY_VOLUME_MOUNT_PATH=/tu/ruta/personalizada
   ```

### Paso 3: Verificar Configuración

Después de configurar el volumen y la variable de entorno:

1. Railway redeployará automáticamente
2. En los logs de deployment, deberías ver:
   ```
   ✅ Usando VOLUMEN PERSISTENTE de Railway para media: /data/media
   ```

### Paso 4: Migrar Archivos Existentes (Si los tienes)

Si ya tienes archivos en `media/` y quieres migrarlos al volumen:

**Opción A: Desde tu máquina local (si tienes los archivos)**
```bash
# Conectarte al contenedor de Railway (si Railway lo permite)
# O usar Railway CLI para copiar archivos
```

**Opción B: Subirlos nuevamente**
- Los usuarios pueden volver a subir las imágenes
- O puedes crear un script de migración

---

## 🔧 Configuración Técnica

### Cómo Funciona

1. **Sin Volumen** (Desarrollo/Default):
   - `MEDIA_ROOT = BASE_DIR / 'media'` → `./media/`
   - Los archivos se guardan en el contenedor (se pierden al redeployar)

2. **Con Volumen** (Railway):
   - `MEDIA_ROOT = /data/media` (o la ruta configurada)
   - Los archivos se guardan en el volumen persistente
   - Los archivos **persisten** entre deployments

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `USE_RAILWAY_VOLUME` | Activa el uso del volumen persistente | `False` |
| `RAILWAY_VOLUME_MOUNT_PATH` | Ruta donde se monta el volumen | `/data` |

### Estructura de Directorios

```
/data/                    # Volumen montado en Railway
  └── media/              # Archivos subidos por usuarios
      ├── productos/      # Imágenes de productos
      ├── servicios/      # Imágenes de servicios
      ├── landing/        # Archivos de landing pages
      └── avatares/       # Avatares de usuarios
```

---

## 🚀 Proceso de Actualización en Railway

### ¿Qué Pasa al Actualizar?

1. **Código de la App**: Se actualiza automáticamente desde GitHub
2. **Base de Datos**: Se mantiene (está en PostgreSQL separado)
3. **Archivos Media**:
   - ✅ **Con Volumen**: Se mantienen (están en el volumen persistente)
   - ❌ **Sin Volumen**: Se pierden (están en el contenedor efímero)

### Flujo de Deployment

```
1. Push a GitHub
   ↓
2. Railway detecta cambios
   ↓
3. Railway construye nuevo contenedor
   ↓
4. Railway monta el volumen persistente en /data
   ↓
5. Railway ejecuta migraciones (si es necesario)
   ↓
6. Railway inicia la aplicación
   ↓
7. La app usa /data/media (volumen persistente)
```

---

## 📝 Verificación

### Verificar que el Volumen Está Funcionando

1. **Sube una imagen** desde la aplicación
2. **Haz un redeploy** (push a GitHub o redeploy manual)
3. **Verifica que la imagen sigue disponible** después del redeploy

### Ver Logs

En Railway → Tu Servicio → Logs, deberías ver:
```
✅ Usando VOLUMEN PERSISTENTE de Railway para media: /data/media
```

Si ves:
```
✅ Usando directorio LOCAL para media: /app/media
```
Significa que el volumen NO está configurado correctamente.

---

## ⚙️ Configuración Avanzada

### Usar Ruta Personalizada para el Volumen

Si prefieres montar el volumen en otra ruta:

1. En Railway, al crear el volumen, usa una ruta diferente (ej: `/app/media`)
2. Agrega la variable de entorno:
   ```
   RAILWAY_VOLUME_MOUNT_PATH=/app/media
   ```

### Múltiples Volúmenes

Si necesitas múltiples volúmenes (ej: uno para media, otro para logs):

1. Crea múltiples volúmenes en Railway
2. Monta cada uno en una ruta diferente
3. Configura `MEDIA_ROOT` según corresponda

---

## 🔄 Migración desde Local a Railway

Si tienes archivos en tu entorno local y quieres migrarlos:

### Opción 1: Usar Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Conectar al proyecto
railway link

# Copiar archivos (ejemplo)
railway run cp -r /ruta/local/media/* /data/media/
```

### Opción 2: Script de Migración Django

Crea un comando de gestión Django para migrar archivos:

```python
# apps/accounts/management/commands/migrate_media.py
from django.core.management.base import BaseCommand
import shutil
from pathlib import Path
from django.conf import settings

class Command(BaseCommand):
    help = 'Migra archivos media al volumen persistente'

    def handle(self, *args, **options):
        local_media = Path(settings.BASE_DIR) / 'media'
        volume_media = Path('/data/media')
        
        if local_media.exists():
            volume_media.mkdir(parents=True, exist_ok=True)
            shutil.copytree(local_media, volume_media, dirs_exist_ok=True)
            self.stdout.write(self.style.SUCCESS('Archivos migrados exitosamente'))
```

---

## 💰 Costos

- **Volúmenes en Railway**: Se cobran según el tamaño y uso
- **Recomendación**: Empieza con un volumen pequeño (10GB) y aumenta según necesites
- **Monitoreo**: Railway te muestra el uso del volumen en el dashboard

---

## 🐛 Troubleshooting

### Problema: "No se encuentra el directorio /data/media"

**Solución**: Verifica que:
1. El volumen esté creado y montado en Railway
2. La variable `USE_RAILWAY_VOLUME=True` esté configurada
3. El path del volumen sea correcto (`RAILWAY_VOLUME_MOUNT_PATH`)

### Problema: "Los archivos se siguen perdiendo"

**Solución**: 
1. Verifica que el volumen esté montado correctamente
2. Revisa los logs para confirmar que usa el volumen
3. Asegúrate de que `USE_RAILWAY_VOLUME=True` esté en Railway Variables

### Problema: "No tengo permisos para escribir en /data"

**Solución**: 
1. Railway debería dar permisos automáticamente
2. Si persiste, verifica la configuración del volumen en Railway
3. Contacta soporte de Railway si el problema continúa

---

## 📚 Referencias

- [Railway Volumes Documentation](https://docs.railway.app/storage/volumes)
- [Railway CLI](https://docs.railway.app/develop/cli)
- [Django File Uploads](https://docs.djangoproject.com/en/5.2/topics/files/)

---

## ✅ Checklist de Configuración

- [ ] Volumen creado en Railway
- [ ] Volumen montado en `/data` (o ruta personalizada)
- [ ] Variable `USE_RAILWAY_VOLUME=True` configurada
- [ ] (Opcional) Variable `RAILWAY_VOLUME_MOUNT_PATH` configurada
- [ ] Deployment exitoso
- [ ] Logs muestran "Usando VOLUMEN PERSISTENTE"
- [ ] Archivo de prueba subido y verificado después de redeploy

---

**Última actualización**: Diciembre 2025

