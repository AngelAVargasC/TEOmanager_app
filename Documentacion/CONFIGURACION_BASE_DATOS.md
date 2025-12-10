# Configuración de Base de Datos

## Cambio Rápido entre Base de Datos Local y Railway

El proyecto ahora permite cambiar fácilmente entre usar una base de datos local (SQLite) o la base de datos de Railway (PostgreSQL) mediante una simple variable de entorno.

## Configuración en `.env`

### Para usar Base de Datos LOCAL (SQLite) - Desarrollo

Agrega o modifica en tu archivo `.env`:

```env
USE_LOCAL_DB=True
```

**Ventajas:**
- No requiere conexión a internet
- Más rápido para desarrollo local
- No consume recursos de Railway
- Ideal para desarrollo y pruebas locales

**Desventajas:**
- Los datos son locales (no se sincronizan con producción)
- No puedes probar funcionalidades que dependan de PostgreSQL

### Para usar Base de Datos RAILWAY (PostgreSQL) - Producción/Staging

Agrega o modifica en tu archivo `.env`:

```env
USE_LOCAL_DB=False
```

O simplemente **no incluyas** la variable `USE_LOCAL_DB` en tu `.env`.

Además, asegúrate de tener configuradas las credenciales de PostgreSQL:

```env
# Opción 1: Usar DATABASE_URL (Railway lo proporciona automáticamente)
# No necesitas configurar nada más si Railway está conectado

# Opción 2: Usar variables individuales
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=tu_password_aqui
PGHOST=mainline.proxy.rlwy.net
PGPORT=54586
```

**Ventajas:**
- Datos sincronizados con producción
- Puedes probar funcionalidades específicas de PostgreSQL
- Ideal para staging y producción

**Desventajas:**
- Requiere conexión a internet
- Puede ser más lento
- Consume recursos de Railway

## Ejemplo de `.env` Completo

### Para Desarrollo Local (SQLite)

```env
# Base de datos LOCAL
USE_LOCAL_DB=True

# Django
SECRET_KEY=django-insecure-cambiar-en-produccion
DEBUG=True
ENVIRONMENT=development

# Email
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_aqui

# Admin
ADMIN_DEFAULT_PASSWORD=CambiarEnProduccion123!
```

### Para Railway/Producción (PostgreSQL)

```env
# Base de datos RAILWAY
USE_LOCAL_DB=False

# Base de datos PostgreSQL
PGDATABASE=railway
PGUSER=postgres
PGPASSWORD=tu_password_aqui
PGHOST=mainline.proxy.rlwy.net
PGPORT=54586

# Django
SECRET_KEY=django-insecure-cambiar-en-produccion
DEBUG=True
ENVIRONMENT=staging

# Email
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password_aqui

# Admin
ADMIN_DEFAULT_PASSWORD=CambiarEnProduccion123!

# CSRF
CSRF_TRUSTED_ORIGINS=https://tu-dominio.up.railway.app
```

## Cómo Funciona

1. El sistema lee la variable `USE_LOCAL_DB` del archivo `.env`
2. Si `USE_LOCAL_DB=True` → Usa SQLite local (`db.sqlite3`)
3. Si `USE_LOCAL_DB=False` o no existe → Usa PostgreSQL de Railway
4. Para PostgreSQL, primero intenta usar `DATABASE_URL` (si Railway lo proporciona)
5. Si no hay `DATABASE_URL`, usa las variables individuales (`PGDATABASE`, `PGUSER`, etc.)

## Verificación

Al iniciar el servidor Django, verás un mensaje en la consola indicando qué base de datos está usando:

- `✅ Usando base de datos LOCAL (SQLite)` - Si está usando SQLite
- `✅ Usando base de datos RAILWAY (PostgreSQL) - DATABASE_URL` - Si usa Railway con DATABASE_URL
- `✅ Usando base de datos RAILWAY (PostgreSQL) - Variables individuales` - Si usa Railway con variables individuales

## Migraciones

**IMPORTANTE:** Las migraciones se aplican a la base de datos que esté configurada actualmente.

- Si cambias de local a Railway, necesitas ejecutar `python manage.py migrate` para aplicar las migraciones a Railway
- Si cambias de Railway a local, necesitas ejecutar `python manage.py migrate` para crear las tablas en SQLite

## Recomendaciones

- **Desarrollo local**: Usa `USE_LOCAL_DB=True` para trabajar más rápido
- **Pruebas de integración**: Usa `USE_LOCAL_DB=False` para probar con la misma base de datos que producción
- **Producción en Railway**: No configures `USE_LOCAL_DB` (o ponlo en `False`) y asegúrate de tener las credenciales de PostgreSQL configuradas en Railway Variables

