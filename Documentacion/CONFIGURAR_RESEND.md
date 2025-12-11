# 📧 Configurar Resend para Emails en Railway

## ✅ ¿Por qué Resend?

Resend es un servicio de email moderno y fácil de usar:
- ✅ **100 emails/día gratis** - Suficiente para testing
- ✅ **API moderna y simple**
- ✅ **Funciona perfectamente en Railway**
- ✅ **Verificación rápida** (solo email)
- ✅ **SMTP compatible** - No requiere paquetes adicionales

## 🚀 Configuración Paso a Paso

### Paso 1: Crear Cuenta en Resend

1. Ve a: https://resend.com/
2. Click **"Sign Up"** o **"Get Started"**
3. Completa el formulario:
   - Email
   - Contraseña
   - Nombre (opcional)
4. Verifica tu email (rápido, solo click en el enlace)

### Paso 2: Obtener API Key

1. Una vez dentro del dashboard de Resend
2. Ve a **API Keys** (en el menú lateral)
3. Click **"Create API Key"**
4. Nombre: `TEOmanager Railway`
5. Permisos: **Sending access** (o Full access)
6. Click **"Add"**
7. **COPIA LA API KEY** (empieza con `re_` y solo se muestra una vez)

### Paso 3: Verificar Dominio (OBLIGATORIO para Producción)

⚠️ **IMPORTANTE:** Sin dominio verificado, Resend solo permite enviar emails a tu propia dirección de email (la que usaste para registrarte).

Para enviar a cualquier destinatario:

1. En Resend Dashboard, ve a **Domains**
2. Click **"Add Domain"**
3. Ingresa: `teomanager.com`
4. Resend te dará registros DNS para agregar en Cloudflare:
   - `TXT` record para verificación (SPF)
   - `CNAME` record para DKIM
   - `TXT` record para DMARC (opcional pero recomendado)
5. Agrega los registros en Cloudflare:
   - Ve a Cloudflare → Tu dominio → DNS
   - Agrega cada registro exactamente como Resend lo indica
6. Espera a que se verifique (puede tomar 5-30 minutos)
7. Una vez verificado (verás un check verde en Resend), puedes usar cualquier email del dominio

**Después de verificar:**
- Actualiza en Railway: `DEFAULT_FROM_EMAIL=TEOmanager <noreply@teomanager.com>`
- Ahora podrás enviar a cualquier destinatario

### Paso 4: Configurar en Railway

Agrega esta variable de entorno en Railway:

1. Ve a tu proyecto en Railway
2. Click en tu servicio Django
3. Ve a **Variables**
4. Click **"New Variable"**
5. Agrega:
   ```
   RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
   **⚠️ IMPORTANTE:**
   - **NO** pongas comillas alrededor de la key
   - **NO** dejes espacios al inicio o final
   - Debe empezar con `re_`
   - Copia la key completa desde Resend
   
   **❌ INCORRECTO:**
   ```
   RESEND_API_KEY="re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   RESEND_API_KEY= re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx 
   ```
   
   **✅ CORRECTO:**
   ```
   RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

6. Opcional, también agrega:
   ```
   DEFAULT_FROM_EMAIL=TEOmanager <noreply@teomanager.com>
   ```
   (Solo si verificaste el dominio, sino usa `onboarding@resend.dev`)

### Paso 5: Verificar Configuración

Después del deploy, en los logs de Railway deberías ver:
```
✅ Configurado Resend para envío de emails
```

## 🧪 Probar Envío

### Opción 1: Desde la Aplicación

1. Registra un nuevo usuario
2. Deberías recibir el email de bienvenida
3. O solicita restablecimiento de contraseña

### Opción 2: Desde Django Shell

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    subject='Test Email desde Resend',
    message='Este es un email de prueba',
    from_email='TEOmanager <onboarding@resend.dev>',  # O tu dominio verificado
    recipient_list=['tu-email@ejemplo.com'],
    fail_silently=False,
)
```

## 📊 Límites y Costos

### Plan Gratuito:
- ✅ **100 emails/día**
- ✅ **3,000 emails/mes**
- ✅ Perfecto para testing y desarrollo

### Plan de Pago:
- **$20/mes**: 50,000 emails/mes
- **$80/mes**: 200,000 emails/mes
- **Custom**: Para más volumen

## ⚠️ Notas Importantes

1. **Sin dominio verificado**: Usarás `onboarding@resend.dev` como remitente
2. **Con dominio verificado**: Puedes usar cualquier email de tu dominio
3. **Los emails son asíncronos**: No bloquean la aplicación
4. **Resend tiene prioridad**: Si `RESEND_API_KEY` está configurado, se usa Resend automáticamente

## 🔧 Troubleshooting

### Los emails no se envían

1. Verifica que `RESEND_API_KEY` esté correctamente configurado en Railway
2. Revisa los logs de Railway para errores
3. Verifica que el API Key tenga permisos de "Sending access"
4. Si usas dominio personalizado, verifica que esté verificado en Resend

### Error: "API key is invalid" o "Invalid API Key"

Este error significa que Resend no reconoce tu API key. Sigue estos pasos:

1. **Verifica en Railway:**
   - Ve a Railway Dashboard → Tu proyecto → Variables
   - Busca `RESEND_API_KEY`
   - Verifica que:
     - ✅ No tenga comillas alrededor (`re_xxxxx` NO `"re_xxxxx"`)
     - ✅ No tenga espacios al inicio o final
     - ✅ Empiece con `re_`
     - ✅ Esté completa (no truncada)

2. **Verifica en Resend:**
   - Ve a https://resend.com/api-keys
   - Verifica que la key exista y esté activa
   - Si no estás seguro, crea una nueva key

3. **Regenera la API key (si es necesario):**
   - Ve a Resend Dashboard → API Keys
   - Click en la key existente → **"Revoke"** (revocar)
   - Click **"Create API Key"** → Crea una nueva
   - Copia la nueva key completa
   - Actualiza en Railway con la nueva key

4. **Redeploy en Railway:**
   - Después de actualizar la variable, Railway debería redeployar automáticamente
   - O haz click en **"Redeploy"** manualmente

5. **Verifica los logs:**
   - En los logs de Railway deberías ver:
     ```
     🔑 Resend API Key detectada: re_xxxxx...xxxxx (longitud: XX)
     ✅ Configurado Resend (API REST) para envío de emails
     ```
   - Si ves un warning sobre el formato, la key está mal configurada

### Los emails van a spam

1. Verifica tu dominio en Resend
2. Agrega los registros SPF y DKIM correctamente
3. Usa un email profesional como `noreply@teomanager.com`

## 🎯 Ventajas de Resend

- ✅ **Más moderno** que SendGrid
- ✅ **API más simple** y fácil de usar
- ✅ **Documentación excelente**
- ✅ **Dashboard intuitivo**
- ✅ **Funciona inmediatamente** después de verificar email

## 📚 Recursos

- **Website**: https://resend.com/
- **Documentación**: https://resend.com/docs
- **Dashboard**: https://resend.com/emails
- **API Reference**: https://resend.com/docs/api-reference

