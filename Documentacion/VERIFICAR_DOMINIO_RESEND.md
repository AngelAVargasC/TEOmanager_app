# 🔐 Verificar Dominio en Resend (OBLIGATORIO)

## ⚠️ Problema Actual

Resend en modo gratuito tiene una **restricción de seguridad**:
- ✅ Puedes enviar **3,000 emails/mes** (según tu plan)
- ❌ Pero **solo a tu propia dirección** hasta que verifiques un dominio
- ✅ Después de verificar dominio → puedes enviar a **cualquier destinatario**

## 🚀 Solución: Verificar tu Dominio

### Paso 1: Agregar Dominio en Resend

1. Ve a: https://resend.com/domains
2. Click **"Add Domain"**
3. Ingresa: `teomanager.com`
4. Click **"Add"**

### Paso 2: Obtener Registros DNS

Resend te mostrará registros DNS que debes agregar en Cloudflare:

**Ejemplo de registros (Resend te dará los valores exactos):**

1. **TXT Record (SPF):**
   - Name: `@` (o `teomanager.com`)
   - Value: `v=spf1 include:resend.com ~all`
   - TTL: Auto

2. **CNAME Record (DKIM):**
   - Name: `resend._domainkey` (o similar)
   - Value: `resend.com` (o el valor que Resend te dé)
   - TTL: Auto

3. **TXT Record (DMARC) - Opcional pero recomendado:**
   - Name: `_dmarc`
   - Value: `v=DMARC1; p=none;`
   - TTL: Auto

### Paso 3: Agregar Registros en Cloudflare

1. Ve a: https://dash.cloudflare.com/
2. Selecciona tu dominio `teomanager.com`
3. Ve a **DNS** → **Records**
4. Click **"Add record"**
5. Agrega cada registro que Resend te indicó:
   - Tipo: `TXT` o `CNAME` según corresponda
   - Nombre: El que Resend te indique
   - Contenido: El valor que Resend te dé
   - TTL: Auto
6. Click **"Save"** para cada registro

### Paso 4: Esperar Verificación

1. Vuelve a Resend Dashboard → **Domains**
2. Verás el estado de verificación
3. Puede tomar **5-30 minutos** para que se verifique
4. Cuando esté verificado, verás un ✅ verde

### Paso 5: Actualizar en Railway

Una vez verificado el dominio:

1. Ve a Railway → Tu proyecto → Variables
2. Agrega o actualiza:
   ```
   DEFAULT_FROM_EMAIL=TEOmanager <noreply@teomanager.com>
   ```
3. O usa cualquier email de tu dominio:
   ```
   DEFAULT_FROM_EMAIL=TEOmanager <contacto@teomanager.com>
   ```

### Paso 6: Verificar

Después del deploy, intenta enviar un email a cualquier destinatario. Debería funcionar.

## 📋 Registros DNS Completos (Ejemplo)

Aquí está un ejemplo de cómo deberían verse los registros en Cloudflare:

```
Tipo    Nombre                    Contenido
----    ------                    ---------
TXT     @                         v=spf1 include:resend.com ~all
CNAME   resend._domainkey         xxxxx.resend.com
TXT     _dmarc                    v=DMARC1; p=none;
```

**⚠️ IMPORTANTE:** Resend te dará los valores exactos. Usa esos, no estos ejemplos.

## ✅ Después de Verificar

Una vez verificado:
- ✅ Puedes enviar a **cualquier destinatario**
- ✅ Puedes usar cualquier email de tu dominio (`noreply@teomanager.com`, `contacto@teomanager.com`, etc.)
- ✅ Los emails no irán a spam (mejor entregabilidad)
- ✅ Tendrás 3,000 emails/mes disponibles

## 🆘 Troubleshooting

### El dominio no se verifica después de 30 minutos

1. Verifica que los registros DNS estén correctos en Cloudflare
2. Asegúrate de que los valores sean exactos (sin espacios extra)
3. Espera hasta 24 horas (a veces DNS tarda más)
4. Contacta soporte de Resend si sigue sin funcionar

### Los emails siguen fallando

1. Verifica que `DEFAULT_FROM_EMAIL` use tu dominio verificado
2. Revisa los logs de Railway para ver el error específico
3. Asegúrate de que el dominio esté completamente verificado (✅ verde en Resend)

