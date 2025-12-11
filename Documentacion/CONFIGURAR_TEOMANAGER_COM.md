# Configurar teomanager.com con Railway

## 🎯 Pasos para Conectar tu Dominio con Railway

### Paso 1: Obtener el Dominio de Railway

1. Ve a Railway: https://railway.app
2. Selecciona tu servicio **web**
3. Ve a la pestaña **"Settings"** o **"Domains"**
4. Copia tu dominio de Railway (ej: `web-production-8666.up.railway.app`)
5. **Guarda este dominio**, lo necesitarás en el siguiente paso

---

### Paso 2: Configurar DNS en Cloudflare

1. En Cloudflare, ve a **"Domains"** en el menú lateral (o busca `teomanager.com`)
2. Selecciona tu dominio **`teomanager.com`**
3. Ve a la pestaña **"DNS"** o **"DNS Records"**
4. Verás una tabla con registros DNS

#### Configurar Registro CNAME para el Dominio Principal

1. Haz clic en **"Add record"** o **"Añadir registro"**
2. Configura así:
   - **Tipo:** `CNAME`
   - **Nombre:** `@` (esto representa el dominio raíz: teomanager.com)
   - **Target:** `tu-dominio-railway.up.railway.app` (pega el dominio que copiaste de Railway)
   - **Proxy status:** 🟠 **DNS only** (naranja, NO proxy) - **IMPORTANTE**
   - Haz clic en **"Save"**

#### Configurar Registro CNAME para www (Opcional pero Recomendado)

1. Haz clic en **"Add record"** nuevamente
2. Configura así:
   - **Tipo:** `CNAME`
   - **Nombre:** `www`
   - **Target:** `tu-dominio-railway.up.railway.app` (el mismo de arriba)
   - **Proxy status:** 🟠 **DNS only** (naranja, NO proxy)
   - Haz clic en **"Save"**

**⚠️ IMPORTANTE:** 
- El **Proxy status** debe estar en **"DNS only"** (naranja) NO en "Proxied" (naranja con nube)
- Railway necesita acceso directo al DNS, no a través del proxy de Cloudflare

---

### Paso 3: Agregar Dominio en Railway

1. En Railway, ve a tu servicio **web**
2. Ve a la pestaña **"Settings"** o **"Domains"**
3. Busca la sección **"Custom Domain"** o **"Add Domain"**
4. Ingresa: `teomanager.com`
5. Haz clic en **"Add"** o **"Save"**
6. Railway verificará el dominio (puede tardar unos minutos)

**Nota:** Si Railway te pide verificar con un registro TXT, agrégalo en Cloudflare DNS.

---

### Paso 4: Configurar Variables de Entorno en Railway

1. En Railway, ve a tu servicio **web**
2. Ve a la pestaña **"Variables"**
3. Agrega o actualiza la variable:
   ```
   CSRF_TRUSTED_ORIGINS=https://teomanager.com,https://www.teomanager.com
   ```
4. Guarda los cambios

Railway redeployará automáticamente.

---

### Paso 5: Verificar Configuración

#### En Cloudflare DNS:
- ✅ Debe haber un registro CNAME con nombre `@` apuntando a Railway
- ✅ Debe haber un registro CNAME con nombre `www` apuntando a Railway
- ✅ Ambos deben estar en modo **"DNS only"** (naranja, NO proxy)

#### En Railway:
- ✅ El dominio `teomanager.com` debe aparecer en la lista de dominios
- ✅ Debe tener un check verde ✅ (verificado)
- ✅ Debe mostrar "SSL Active" o similar

#### Probar Acceso:
1. Espera 5-10 minutos para la propagación DNS
2. Abre en tu navegador: `https://teomanager.com`
3. Debe cargar tu aplicación sin errores
4. Prueba hacer login/registro (debe funcionar sin errores CSRF)

---

## 🔍 Ubicación en Cloudflare

### Si estás en la página de confirmación:
1. Haz clic en **"Domains"** en el menú lateral izquierdo
2. O busca **"teomanager.com"** en la barra de búsqueda rápida (Ctrl+K)
3. Selecciona tu dominio
4. Ve a la pestaña **"DNS"**

### Estructura del Menú:
```
Cloudflare Dashboard
├── Account home
├── Recents
├── Register domains ← (estás aquí)
├── Analytics & logs
└── Domains ← (ve aquí para configurar DNS)
    └── teomanager.com
        └── DNS ← (aquí configuras los registros)
```

---

## ⚙️ Configuración Detallada de DNS

### Registros DNS Necesarios:

| Tipo | Nombre | Target | Proxy | TTL |
|------|--------|--------|-------|-----|
| CNAME | `@` | `web-production-8666.up.railway.app` | DNS only | Auto |
| CNAME | `www` | `web-production-8666.up.railway.app` | DNS only | Auto |

**Nota:** Reemplaza `web-production-8666.up.railway.app` con tu dominio real de Railway.

---

## 🐛 Troubleshooting

### El dominio no carga después de configurar

**Causa:** Propagación DNS (puede tardar hasta 48 horas, pero normalmente 5-30 minutos)

**Solución:**
1. Espera 10-15 minutos
2. Verifica en Cloudflare que los registros estén correctos
3. Usa herramientas como `nslookup teomanager.com` o `dig teomanager.com` para verificar

### Error: "SSL certificate pending" en Railway

**Causa:** Railway está generando el certificado SSL

**Solución:**
1. Espera 5-10 minutos
2. Railway genera SSL automáticamente
3. Verifica que el dominio esté verificado en Railway

### Error CSRF al hacer login

**Causa:** La variable `CSRF_TRUSTED_ORIGINS` no está configurada

**Solución:**
1. Ve a Railway → Variables
2. Agrega: `CSRF_TRUSTED_ORIGINS=https://teomanager.com,https://www.teomanager.com`
3. Railway redeployará automáticamente

### El proxy de Cloudflare está activado (nube naranja)

**Causa:** El registro DNS está en modo "Proxied"

**Solución:**
1. En Cloudflare DNS, haz clic en el registro
2. Cambia **"Proxy status"** de **"Proxied"** (nube naranja) a **"DNS only"** (naranja sin nube)
3. Guarda los cambios

---

## ✅ Checklist de Configuración

- [ ] Dominio comprado en Cloudflare (`teomanager.com`)
- [ ] Dominio de Railway copiado
- [ ] Registro CNAME `@` configurado en Cloudflare (DNS only)
- [ ] Registro CNAME `www` configurado en Cloudflare (DNS only)
- [ ] Dominio agregado en Railway
- [ ] Dominio verificado en Railway (check verde ✅)
- [ ] Variable `CSRF_TRUSTED_ORIGINS` configurada en Railway
- [ ] SSL activo en Railway
- [ ] Acceso a `https://teomanager.com` funciona
- [ ] Login/registro funciona sin errores

---

## 📝 Resumen Rápido

1. **Cloudflare DNS:** Agregar CNAME `@` → `tu-railway.up.railway.app` (DNS only)
2. **Railway:** Agregar dominio `teomanager.com`
3. **Railway Variables:** `CSRF_TRUSTED_ORIGINS=https://teomanager.com,https://www.teomanager.com`
4. **Esperar:** 5-10 minutos para propagación DNS
5. **Probar:** `https://teomanager.com`

---

**Última actualización:** Diciembre 2025

