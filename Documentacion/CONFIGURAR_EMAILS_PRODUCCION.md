# 📧 Configuración de Emails en Producción

## ✅ Cambios Realizados

Se ha actualizado el sistema de correos para usar el dominio correcto en producción:

1. **Agregado `django.contrib.sites`** a `INSTALLED_APPS`
2. **Configurado `SITE_ID = 1`** en `settings.py`
3. **Agregado `SITE_URL`** como variable de entorno con detección automática
4. **Creado método `UserService.get_site_base_url()`** para obtener el dominio correcto
5. **Actualizado `send_welcome_email()`** para usar el dominio correcto

## 🔧 Configuración en Railway

### Paso 1: Agregar Variables de Entorno

En Railway, agrega estas variables de entorno:

```env
# Email Configuration
EMAIL_HOST_USER=vctechmx@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-de-gmail
DEFAULT_FROM_EMAIL=TEOmanager <vctechmx@gmail.com>

# Site Configuration (IMPORTANTE)
SITE_URL=https://teomanager.com
```

### Paso 2: Configurar Django Sites Framework

Después del primer deploy, ejecuta en Railway (o localmente conectado a la BD de Railway):

```bash
python manage.py migrate sites
```

Luego, configura el dominio en la base de datos:

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site

# Obtener el sitio por defecto
site = Site.objects.get(id=1)
site.domain = 'teomanager.com'  # Tu dominio real
site.name = 'TEOmanager'
site.save()

print(f"✅ Sitio configurado: {site.domain}")
```

### Paso 3: Verificar Configuración

Para verificar que todo está correcto:

```bash
python manage.py shell
```

```python
from apps.accounts.services import UserService
from django.conf import settings

# Verificar SITE_URL
print(f"SITE_URL: {settings.SITE_URL}")

# Verificar método helper
base_url = UserService.get_site_base_url()
print(f"Base URL detectada: {base_url}")

# Verificar Sites Framework
from django.contrib.sites.models import Site
site = Site.objects.get_current()
print(f"Sites Framework: {site.domain}")
```

## 📋 Prioridad de Detección de Dominio

El sistema detecta el dominio en este orden:

1. **`SITE_URL`** (variable de entorno) - **MÁS PRIORITARIO**
2. **Django Sites Framework** (si está configurado en BD)
3. **`RAILWAY_PUBLIC_DOMAIN`** (dominio personalizado de Railway)
4. **`RAILWAY_DOMAIN`** (dominio de Railway por defecto)
5. **Fallback**: `https://teomanager.com` (producción) o `http://localhost:5490` (desarrollo)

## 🔐 Gmail App Password

Si usas Gmail, necesitas crear una "Contraseña de aplicación":

1. Ve a: https://myaccount.google.com/
2. **Seguridad** → **Verificación en 2 pasos** (debe estar activada)
3. **Contraseñas de aplicaciones** → **Generar nueva**
4. Nombre: "TEOmanager Railway"
5. Copia la contraseña generada (16 caracteres)
6. Úsala en `EMAIL_HOST_PASSWORD` en Railway

## ✉️ Emails Afectados

Los siguientes emails ahora usan el dominio correcto:

1. **Email de bienvenida** (`send_welcome_email`)
   - Usa `UserService.get_site_base_url()` para el enlace de login

2. **Password Reset** (Django built-in)
   - Usa automáticamente Django Sites Framework
   - El template `password_reset_email.html` usa `{{ protocol }}://{{ domain }}`

## 🧪 Pruebas

### Probar Email de Bienvenida

```python
from django.contrib.auth.models import User
from apps.accounts.services import UserService

user = User.objects.first()
result = UserService.send_welcome_email(user)
print(f"Email enviado: {result}")
```

### Probar Password Reset

1. Ve a: `https://teomanager.com/password_reset/`
2. Ingresa un email válido
3. Verifica que el email recibido tenga el enlace correcto: `https://teomanager.com/reset/...`

## ⚠️ Notas Importantes

- **SITE_URL debe ser la variable de entorno principal** en Railway
- El dominio debe incluir el protocolo: `https://teomanager.com` (sin barra final)
- Si cambias el dominio, actualiza tanto `SITE_URL` como el registro en Sites Framework
- Los emails se envían de forma asíncrona para evitar timeouts

## 🐛 Troubleshooting

### Los emails no se envían

1. Verifica que `EMAIL_HOST_PASSWORD` sea una App Password válida (no la contraseña normal)
2. Verifica que la verificación en 2 pasos esté activada en Gmail
3. Revisa los logs de Railway para errores de SMTP

### Los enlaces apuntan a localhost

1. Verifica que `SITE_URL` esté configurado en Railway
2. Ejecuta la migración de Sites: `python manage.py migrate sites`
3. Configura el dominio en Sites Framework (ver Paso 2)

### Los enlaces apuntan al dominio de Railway

1. Asegúrate de que `SITE_URL=https://teomanager.com` esté en Railway
2. Verifica que el dominio personalizado esté configurado en Railway
3. Actualiza el registro en Sites Framework con el dominio correcto

