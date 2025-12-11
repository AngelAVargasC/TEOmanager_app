# 📧 Configurar SendGrid para Emails en Railway

## ⚠️ Problema con Gmail SMTP en Railway

Railway bloquea conexiones SMTP salientes a Gmail (`smtp.gmail.com`), causando el error:
```
OSError: [Errno 101] Network is unreachable
```

## ✅ Solución: Usar SendGrid

SendGrid es un servicio de email transaccional diseñado para producción y funciona perfectamente con Railway.

### Paso 1: Crear Cuenta en SendGrid

1. Ve a: https://signup.sendgrid.com/
2. Crea una cuenta gratuita (100 emails/día gratis)
3. Verifica tu email

### Paso 2: Crear API Key

1. En SendGrid Dashboard, ve a **Settings** → **API Keys**
2. Click en **Create API Key**
3. Nombre: "TEOmanager Railway"
4. Permisos: **Full Access** (o al menos "Mail Send")
5. Click **Create & View**
6. **COPIA LA API KEY** (solo se muestra una vez)

### Paso 3: Verificar Dominio (Opcional pero Recomendado)

Para usar `noreply@teomanager.com`:

1. En SendGrid Dashboard, ve a **Settings** → **Sender Authentication**
2. Click en **Authenticate Your Domain**
3. Sigue las instrucciones para agregar registros DNS en Cloudflare
4. Una vez verificado, puedes usar cualquier email del dominio

### Paso 4: Configurar en Railway

Agrega estas variables de entorno en Railway:

```env
# SendGrid Configuration (RECOMENDADO)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Email Configuration
DEFAULT_FROM_EMAIL=TEOmanager <noreply@teomanager.com>
```

**IMPORTANTE:** Si `SENDGRID_API_KEY` está configurado, el sistema usará SendGrid automáticamente. Si no, usará Gmail como fallback.

### Paso 5: Verificar Configuración

Después del deploy, en los logs deberías ver:
```
✅ Configurado SendGrid para envío de emails
```

## 🔄 Alternativa: Resend (Más Moderno)

Si prefieres Resend (más moderno y fácil de usar):

1. Ve a: https://resend.com/
2. Crea cuenta gratuita (100 emails/día)
3. Obtén tu API Key
4. Agrega a Railway:
   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

Luego actualiza `settings.py` para usar Resend (requiere instalar `resend` package).

## 📊 Comparación

| Servicio | Gratis | Límite Gratis | Facilidad |
|----------|--------|---------------|-----------|
| SendGrid | ✅ | 100 emails/día | ⭐⭐⭐ |
| Resend | ✅ | 100 emails/día | ⭐⭐⭐⭐ |
| Gmail SMTP | ✅ | Sin límite | ❌ No funciona en Railway |

## 🧪 Probar Envío

Después de configurar, prueba:

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    subject='Test Email',
    message='Este es un email de prueba',
    from_email='TEOmanager <noreply@teomanager.com>',
    recipient_list=['tu-email@ejemplo.com'],
    fail_silently=False,
)
```

## ⚠️ Notas Importantes

- **SendGrid es gratuito hasta 100 emails/día**
- **Después del límite, se cobra por email enviado**
- **Para producción, considera un plan de pago**
- **El dominio debe estar verificado para usar emails personalizados**

