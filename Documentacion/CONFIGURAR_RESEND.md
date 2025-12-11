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

### Paso 3: Verificar Dominio (Opcional pero Recomendado)

Para usar `noreply@teomanager.com`:

1. En Resend Dashboard, ve a **Domains**
2. Click **"Add Domain"**
3. Ingresa: `teomanager.com`
4. Resend te dará registros DNS para agregar en Cloudflare:
   - `TXT` record para verificación
   - `CNAME` record para DKIM
5. Agrega los registros en Cloudflare
6. Espera a que se verifique (puede tomar unos minutos)
7. Una vez verificado, puedes usar cualquier email del dominio

**Nota:** Puedes empezar a enviar emails sin verificar dominio, pero usarás el dominio de Resend (`onboarding@resend.dev`)

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
   (Reemplaza con tu API key real)

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

### Error: "Invalid API Key"

1. Verifica que copiaste la API key completa (empieza con `re_`)
2. Asegúrate de que no haya espacios al inicio o final
3. Regenera la API key si es necesario

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

