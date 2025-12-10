# 🗂️ Resumen: Volumen Persistente en Railway

## ⚡ Respuesta Rápida

**Sí, tus imágenes se perderán al actualizar** si NO configuras un volumen persistente.

**Solución**: Configurar un **Volume** en Railway para la carpeta `media/`.

---

## 📊 Comparación: Con vs Sin Volumen

| Aspecto | ❌ Sin Volumen | ✅ Con Volumen |
|---------|----------------|----------------|
| **Archivos al redeployar** | Se pierden | Se mantienen |
| **Imágenes de productos** | Se pierden | Se mantienen |
| **Configuración** | Ninguna | Crear volumen + variable |
| **Costo** | Gratis | Según tamaño usado |

---

## 🚀 Configuración Rápida (3 Pasos)

### 1️⃣ Crear Volumen en Railway
```
Railway → Tu Servicio → Volumes → New Volume
- Name: media-storage
- Mount Path: /data
- Size: 10GB (o según necesites)
```

### 2️⃣ Agregar Variable de Entorno
```
Railway → Tu Servicio → Variables
- Key: USE_RAILWAY_VOLUME
- Value: True
```

### 3️⃣ Verificar
Después del redeploy, en los logs deberías ver:
```
✅ Usando VOLUMEN PERSISTENTE de Railway para media: /data/media
```

---

## 🔄 ¿Qué Pasa al Actualizar?

### Sin Volumen ❌
```
1. Push a GitHub
2. Railway construye nuevo contenedor
3. ❌ Archivos en media/ se pierden
4. ❌ Imágenes desaparecen
```

### Con Volumen ✅
```
1. Push a GitHub
2. Railway construye nuevo contenedor
3. Railway monta volumen en /data
4. ✅ Archivos en /data/media se mantienen
5. ✅ Imágenes siguen disponibles
```

---

## 📁 Estructura de Archivos

### Local (Desarrollo)
```
TEOmanager/
  └── media/          ← Archivos aquí (local)
      ├── productos/
      └── servicios/
```

### Railway (Con Volumen)
```
Contenedor:
  └── /app/           ← Código de la app (se actualiza)
  
Volumen Persistente:
  └── /data/          ← Volumen montado
      └── media/      ← Archivos aquí (persisten)
          ├── productos/
          └── servicios/
```

---

## ✅ Checklist

- [ ] Volumen creado en Railway (`/data`)
- [ ] Variable `USE_RAILWAY_VOLUME=True` configurada
- [ ] Redeploy realizado
- [ ] Logs muestran "VOLUMEN PERSISTENTE"
- [ ] Archivo de prueba subido y verificado

---

## 📚 Documentación Completa

Para más detalles, ver: `CONFIGURACION_VOLUMEN_RAILWAY.md`

---

**💡 Tip**: Configura el volumen ANTES de subir archivos importantes para evitar pérdidas.

