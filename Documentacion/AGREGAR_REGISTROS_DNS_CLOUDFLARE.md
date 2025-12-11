# 📝 Agregar Registros DNS en Cloudflare para Resend

## ⚠️ Estado Actual

Tu dominio `teomanager.com` está en **"Pendiente"** en Resend porque aún no encuentra los registros DNS. Necesitas agregarlos manualmente en Cloudflare.

## 🚀 Pasos para Agregar Registros DNS

### Paso 1: Acceder a Cloudflare

1. Ve a: https://dash.cloudflare.com/
2. Selecciona tu dominio `teomanager.com`
3. Ve a la sección **DNS** → **Records**

### Paso 2: Agregar Registro DKIM (Verificación de dominio)

1. Click **"Add record"**
2. Configura:
   - **Type:** `TXT`
   - **Name:** `resend._domainkey`
   - **Content:** Copia el valor completo que Resend muestra (empieza con `p=MIGfMAOGCSqGSIb3DQEB...`)
   - **TTL:** `Auto`
3. Click **"Save"**

### Paso 3: Agregar Registro MX (Habilitar envío)

1. Click **"Add record"** de nuevo
2. Configura:
   - **Type:** `MX`
   - **Name:** `send`
   - **Mail server:** Copia el valor que Resend muestra (empieza con `feedback-smtp.us-east-...`)
   - **Priority:** `10`
   - **TTL:** `Auto`
3. Click **"Save"**

### Paso 4: Agregar Registro TXT SPF (Habilitar envío)

1. Click **"Add record"** de nuevo
2. Configura:
   - **Type:** `TXT`
   - **Name:** `send`
   - **Content:** Copia el valor completo que Resend muestra (empieza con `v=spf1 include:amazons...`)
   - **TTL:** `Auto`
3. Click **"Save"**

### Paso 5: Verificar en Resend

1. Vuelve a Resend Dashboard → **Domains** → `teomanager.com`
2. Click en el botón **"Reanudar"** (refresh) o espera unos minutos
3. Resend buscará los registros automáticamente
4. El estado cambiará de "Pendiente" a "Verificado" (✅ verde)

## ⏱️ Tiempo de Propagación

- **Normal:** 5-30 minutos
- **Máximo:** Hasta 24 horas (raro)
- **Cloudflare:** Generalmente rápido (5-15 minutos)

## ✅ Cómo Saber que Está Verificado

En Resend verás:
- Estado cambia de "Pendiente" (naranja) a "Verificado" (verde)
- Los registros DNS muestran estado "Verificado" en lugar de "Pendiente"
- Puedes usar cualquier email de tu dominio (`noreply@teomanager.com`)

## 🔧 Después de Verificar

1. **Actualiza en Railway:**
   ```
   DEFAULT_FROM_EMAIL=TEOmanager <noreply@teomanager.com>
   ```

2. **Redeploy** (o espera a que Railway detecte el cambio)

3. **Prueba enviar un email** a cualquier destinatario

## 🆘 Si No Se Verifica

1. Verifica que los registros estén exactamente como Resend los muestra
2. Asegúrate de que no haya espacios extra
3. Verifica que los valores estén completos (no truncados)
4. Espera hasta 24 horas
5. Si sigue sin funcionar, contacta soporte de Resend

## 📋 Resumen de Registros a Agregar

| Tipo | Nombre | Contenido | Prioridad |
|------|--------|-----------|-----------|
| TXT | `resend._domainkey` | (Valor completo de Resend) | - |
| MX | `send` | (Valor completo de Resend) | 10 |
| TXT | `send` | (Valor completo de Resend) | - |

**⚠️ IMPORTANTE:** Copia los valores **completos** desde Resend, no uses valores truncados.

