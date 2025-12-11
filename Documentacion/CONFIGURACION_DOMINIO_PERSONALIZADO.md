# Configuración de Dominio Personalizado en Railway

## 🌐 Opciones de Dominio en Railway

Railway ofrece dos opciones para el dominio de tu aplicación:

1. **Dominio de Railway** (automático): `tu-app.up.railway.app`
2. **Dominio Personalizado** (custom domain): `tudominio.com`

---

## 📋 Configurar Dominio Personalizado en Railway

### Paso 1: Agregar Dominio en Railway

1. Ve a tu proyecto en Railway: https://railway.app
2. Selecciona tu servicio **web**
3. Ve a la pestaña **"Settings"** o **"Domains"**
4. Busca la sección **"Custom Domain"** o **"Add Domain"**
5. Ingresa tu dominio personalizado (ej: `app.tudominio.com` o `tudominio.com`)
6. Railway te dará instrucciones para configurar los registros DNS

### Paso 2: Configurar DNS en tu Proveedor de Dominio

Railway te proporcionará registros DNS que debes agregar en tu proveedor de dominio (GoDaddy, Namecheap, Cloudflare, etc.):

**Ejemplo de registros DNS:**
```
Tipo: CNAME
Nombre: @ (o www, o app)
Valor: tu-app.up.railway.app
```

O si Railway requiere un registro A:
```
Tipo: A
Nombre: @
Valor: [IP proporcionada por Railway]
```

**Nota:** La propagación DNS puede tardar de 5 minutos a 48 horas.

### Paso 3: Verificar Dominio en Railway

1. Railway verificará automáticamente el dominio
2. Cuando esté verificado, verás un check verde ✅
3. Railway emitirá un certificado SSL automáticamente (HTTPS)

---

## ⚙️ Configurar Django para el Dominio Personalizado

Una vez que Railway tenga tu dominio configurado, necesitas actualizar Django:

### Opción 1: Usar Variable de Entorno (Recomendado)

1. En Railway → Tu servicio → **Variables**
2. Agrega la variable:
   ```
   CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com
   ```
   
   **Nota:** Si tienes múltiples dominios, sepáralos con comas:
   ```
   CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://www.tudominio.com,https://app.tudominio.com
   ```

3. Railway redeployará automáticamente

### Opción 2: Actualizar settings.py (Solo si es necesario)

Si prefieres hardcodear el dominio (no recomendado para producción), puedes actualizar `settings.py`:

```python
# En la sección CSRF_TRUSTED_ORIGINS
if not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [
        'https://tudominio.com',
        'https://www.tudominio.com',
    ]
```

**⚠️ Recomendación:** Usa la Opción 1 (variable de entorno) para mayor flexibilidad.

---

## 🔍 Verificación

### Verificar que el Dominio Funciona

1. **Accede a tu dominio:** `https://tudominio.com`
2. **Verifica HTTPS:** Debe mostrar el candado verde 🔒
3. **Prueba login/registro:** Debe funcionar sin errores CSRF
4. **Revisa logs:** No debe haber errores de `ALLOWED_HOSTS` o `CSRF`

### Verificar en Logs de Railway

Después del deployment, los logs deberían mostrar:
- ✅ Sin errores de `DisallowedHost`
- ✅ Sin errores de `CSRF verification failed`

---

## 🔄 Cambiar de Dominio de Railway a Dominio Personalizado

Si ya tienes la app funcionando con el dominio de Railway y quieres cambiar a un dominio personalizado:

### Paso 1: Agregar el Nuevo Dominio en Railway
(Sigue los pasos de arriba)

### Paso 2: Actualizar Variable CSRF_TRUSTED_ORIGINS

En Railway → Variables, actualiza:
```
CSRF_TRUSTED_ORIGINS=https://tudominio.com,https://web-production-8666.up.railway.app
```

Esto permite que ambos dominios funcionen durante la transición.

### Paso 3: Una vez Verificado, Remover el Dominio Antiguo

Después de verificar que el nuevo dominio funciona:
```
CSRF_TRUSTED_ORIGINS=https://tudominio.com
```

---

## 📝 Configuración Actual de Django

Tu aplicación ya está configurada para:

✅ **Detectar automáticamente** el dominio de Railway (`RAILWAY_PUBLIC_DOMAIN`)
✅ **Leer dominios personalizados** desde `CSRF_TRUSTED_ORIGINS`
✅ **Permitir dominios de Railway** (`*.railway.app`, `*.up.railway.app`)

### Cómo Funciona Actualmente

1. **ALLOWED_HOSTS:**
   - Lee `RAILWAY_PUBLIC_DOMAIN` automáticamente
   - Permite `*.railway.app` y `*.up.railway.app`
   - Si no hay configuración, permite todos (`*`)

2. **CSRF_TRUSTED_ORIGINS:**
   - Lee `RAILWAY_PUBLIC_DOMAIN` automáticamente
   - Lee `CSRF_TRUSTED_ORIGINS` desde variables de entorno
   - Formato: `https://dominio1.com,https://dominio2.com`

---

## 🐛 Troubleshooting

### Error: "DisallowedHost at /"

**Causa:** El dominio no está en `ALLOWED_HOSTS`

**Solución:**
1. Verifica que Railway detectó el dominio (`RAILWAY_PUBLIC_DOMAIN`)
2. O agrega el dominio manualmente en `CSRF_TRUSTED_ORIGINS`

### Error: "CSRF verification failed"

**Causa:** El dominio no está en `CSRF_TRUSTED_ORIGINS`

**Solución:**
1. Agrega el dominio en Railway Variables:
   ```
   CSRF_TRUSTED_ORIGINS=https://tudominio.com
   ```
2. Asegúrate de incluir `https://` (no solo el dominio)

### El Dominio No Carga

**Causa:** DNS no propagado o configuración incorrecta

**Solución:**
1. Verifica los registros DNS en tu proveedor
2. Usa herramientas como `nslookup` o `dig` para verificar
3. Espera la propagación DNS (puede tardar hasta 48 horas)

### Certificado SSL No Funciona

**Causa:** Railway aún está generando el certificado

**Solución:**
1. Espera unos minutos (Railway genera SSL automáticamente)
2. Verifica en Railway que el dominio esté verificado
3. Si persiste, contacta soporte de Railway

---

## ✅ Checklist de Configuración

- [ ] Dominio agregado en Railway
- [ ] Registros DNS configurados en proveedor de dominio
- [ ] Dominio verificado en Railway (check verde ✅)
- [ ] Certificado SSL activo (HTTPS funcionando)
- [ ] Variable `CSRF_TRUSTED_ORIGINS` configurada en Railway
- [ ] Deployment exitoso
- [ ] Acceso al dominio funciona
- [ ] Login/registro funciona sin errores CSRF
- [ ] Logs sin errores de `ALLOWED_HOSTS`

---

## 📚 Referencias

- [Railway Custom Domains](https://docs.railway.app/deploy/custom-domains)
- [Django ALLOWED_HOSTS](https://docs.djangoproject.com/en/5.2/ref/settings/#allowed-hosts)
- [Django CSRF_TRUSTED_ORIGINS](https://docs.djangoproject.com/en/5.2/ref/settings/#csrf-trusted-origins)

---

**Última actualización:** Diciembre 2025

