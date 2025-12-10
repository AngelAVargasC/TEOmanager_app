# 📧 Guía de Configuración de Email para Producción

## ⚠️ Cambios Necesarios al Montar en Servidor

### 1. **Configuración de Email (settings.py)**

#### ✅ Lo que FUNCIONA sin cambios:
- El código de envío de correos está bien estructurado
- El template HTML es compatible con todos los clientes de correo
- La detección automática de dominio funciona correctamente

#### ⚠️ Lo que DEBES cambiar:

**En `core/settings.py`:**

```python
# Configuración de correo electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # ✅ Puede quedarse igual si usas Gmail
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# ⚠️ CAMBIAR ESTOS VALORES:
EMAIL_HOST_USER = 'tu-email@gmail.com'  # Tu email de producción
EMAIL_HOST_PASSWORD = 'tu-app-password'  # Contraseña de aplicación de Gmail
DEFAULT_FROM_EMAIL = 'TEOmanager <tu-email@gmail.com>'  # Nombre más profesional
```

### 2. **Configuración del Dominio**

#### Opción A: Usar Django Sites Framework (RECOMENDADO)

```python
# En settings.py, agregar:
INSTALLED_APPS = [
    # ... otras apps ...
    'django.contrib.sites',  # ✅ Agregar esto
]

SITE_ID = 1  # ID del sitio en la base de datos
```

Luego en el servidor, ejecutar:
```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'tudominio.com'  # Tu dominio real
site.name = 'TEOmanager'
site.save()
```

#### Opción B: Agregar SITE_URL en settings.py

```python
# Agregar al final de settings.py
SITE_URL = 'https://tudominio.com'  # Sin barra al final
```

### 3. **Variables de Entorno (RECOMENDADO para Seguridad)**

**Crear archivo `.env` en la raíz del proyecto:**

```env
# Email Configuration
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
DEFAULT_FROM_EMAIL=TEOmanager <tu-email@gmail.com>

# Site Configuration
SITE_URL=https://tudominio.com

# Security
SECRET_KEY=tu-secret-key-super-segura
DEBUG=False
ALLOWED_HOSTS=tudominio.com,www.tudominio.com
```

**Modificar `settings.py` para usar variables de entorno:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'vctechmx@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'TEOmanager <vctechmx@gmail.com>')

# Site URL
SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')
```

### 4. **Gmail App Password (Si usas Gmail)**

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Seguridad → Verificación en 2 pasos (debe estar activada)
3. Contraseñas de aplicaciones → Generar nueva
4. Copia la contraseña generada (16 caracteres)
5. Úsala en `EMAIL_HOST_PASSWORD`

### 5. **Servicios de Email Alternativos**

Si prefieres usar otro servicio de email:

#### SendGrid:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'tu-api-key-de-sendgrid'
DEFAULT_FROM_EMAIL = 'TEOmanager <noreply@tudominio.com>'
```

#### Amazon SES:
```python
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'us-east-1'
AWS_SES_REGION_ENDPOINT = 'email.us-east-1.amazonaws.com'
AWS_ACCESS_KEY_ID = 'tu-access-key'
AWS_SECRET_ACCESS_KEY = 'tu-secret-key'
DEFAULT_FROM_EMAIL = 'TEOmanager <noreply@tudominio.com>'
```

### 6. **Verificación Post-Deploy**

Después de desplegar, verifica que:

1. ✅ El correo se envía correctamente
2. ✅ Los enlaces en el correo apuntan al dominio correcto
3. ✅ El nombre de usuario se muestra correctamente
4. ✅ El diseño HTML se ve bien en Gmail, Outlook, etc.

**Comando de prueba:**
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from apps.accounts.services import UserService

user = User.objects.first()
UserService.send_welcome_email(user)
```

### 7. **Checklist de Deploy**

- [ ] Cambiar `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`
- [ ] Cambiar `DEFAULT_FROM_EMAIL` con nombre profesional
- [ ] Configurar dominio en Django Sites o agregar `SITE_URL`
- [ ] Verificar que `DEBUG = False` en producción
- [ ] Configurar `ALLOWED_HOSTS` con tu dominio
- [ ] Probar envío de correo después del deploy
- [ ] Verificar que los enlaces funcionan correctamente

### 8. **Notas Importantes**

- ⚠️ **NUNCA** subas credenciales a Git
- ✅ Usa variables de entorno o archivos `.env` (agregar a `.gitignore`)
- ✅ En producción, usa HTTPS para los enlaces
- ✅ Considera usar un servicio de email profesional para mejor deliverability

## 🎯 Resumen Rápido

**Mínimo necesario para que funcione:**
1. Cambiar `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` en `settings.py`
2. Configurar el dominio (Sites framework o `SITE_URL`)
3. Probar el envío

**Ideal para producción:**
1. Usar variables de entorno
2. Configurar Django Sites
3. Usar servicio de email profesional
4. Configurar SPF/DKIM para mejor deliverability

