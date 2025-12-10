# 🚀 Guía Completa de Deployment en Railway - Versión de Testeo

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Prerrequisitos](#prerrequisitos)
3. [Arquitectura del Deployment](#arquitectura-del-deployment)
4. [Configuración Inicial](#configuración-inicial)
5. [Proceso de Deployment Paso a Paso](#proceso-de-deployment-paso-a-paso)
6. [Configuración de Variables de Entorno](#configuración-de-variables-de-entorno)
7. [CI/CD Automático](#cicd-automático)
8. [Verificación Post-Deployment](#verificación-post-deployment)
9. [Solución de Problemas](#solución-de-problemas)
10. [Checklist Completo](#checklist-completo)
11. [Próximos Pasos](#próximos-pasos)

---

## 🎯 Resumen Ejecutivo

Esta guía documenta el proceso completo para desplegar **TEOmanager** en Railway, utilizando la base de datos PostgreSQL existente. Esta es una **versión de testeo/staging** que permitirá validar la aplicación antes del deployment de producción con suscripciones y pagos.

### Características del Deployment

- ✅ **Base de datos PostgreSQL** ya configurada en Railway
- ✅ **CI/CD automático** con Railway (deploy en cada push)
- ✅ **Configuración de entorno** automática (staging/producción)
- ✅ **Archivos estáticos** servidos con WhiteNoise
- ✅ **Admin automático** creado después de migraciones
- ✅ **Variables de entorno** seguras

---

## 📦 Prerrequisitos

### Cuentas y Servicios Necesarios

1. ✅ **Cuenta en Railway** ([railway.app](https://railway.app))
   - Conectada con GitHub
   - Proyecto creado con base de datos PostgreSQL

2. ✅ **Repositorio en GitHub**
   - Código del proyecto commiteado
   - Branch `main` o `master` activo

3. ✅ **Base de datos PostgreSQL en Railway**
   - Ya configurada y funcionando
   - Credenciales disponibles

### Archivos del Proyecto

Los siguientes archivos ya están creados en el proyecto:

- ✅ `Procfile` - Comandos de inicio y release
- ✅ `runtime.txt` - Versión de Python
- ✅ `railway.json` - Configuración de Railway
- ✅ `requirements.txt` - Dependencias Python
- ✅ `.gitignore` - Archivos excluidos del repositorio

---

## 🏗️ Arquitectura del Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    RAILWAY PROJECT                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐   │
│  │  PostgreSQL DB   │◄────────┤  Django Web App   │   │
│  │  (Existente)     │         │  (Nuevo Servicio) │   │
│  └──────────────────┘         └──────────────────┘   │
│         │                            │                │
│         │                            │                │
│         └──────────┬─────────────────┘                │
│                   │                                    │
│            Variables de Entorno                        │
│            (PGDATABASE, PGUSER, etc.)                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          │
                          │
                    GitHub Repo
                    (Auto-deploy)
```

### Flujo de Deployment

1. **Push a GitHub** → Trigger automático
2. **Railway detecta cambios** → Inicia build
3. **Build Process:**
   - Instala dependencias (`pip install -r requirements.txt`)
   - Ejecuta `release` command (migraciones + collectstatic)
4. **Deploy:**
   - Inicia servidor Gunicorn
   - Aplica migraciones a base de datos existente
   - Crea admin automáticamente (si no existe)

---

## ⚙️ Configuración Inicial

### Paso 1: Preparar el Repositorio

```bash
# 1. Verificar que todos los archivos están commiteados
git status

# 2. Agregar archivos nuevos si es necesario
git add Procfile runtime.txt railway.json core/settings.py
git add Documentacion/GUIA_DEPLOYMENT_RAILWAY.md

# 3. Commit de los cambios
git commit -m "Configurar deployment en Railway - Versión testeo"

# 4. Push a GitHub
git push origin main
```

### Paso 2: Acceder a Railway

1. Ve a [railway.app](https://railway.app)
2. Inicia sesión con tu cuenta (GitHub OAuth recomendado)
3. Localiza tu proyecto existente (donde está la base de datos PostgreSQL)

---

## 🚀 Proceso de Deployment Paso a Paso

### Paso 1: Crear Servicio Web en Railway

1. **En tu proyecto Railway:**
   - Click en el botón **"New"** (arriba a la derecha)
   - Selecciona **"GitHub Repo"**

2. **Conectar Repositorio:**
   - Si es la primera vez, autoriza Railway a acceder a tus repositorios
   - Busca y selecciona tu repositorio `TEOmanager`
   - Railway detectará automáticamente que es un proyecto Django

3. **Configuración Automática:**
   - Railway creará un nuevo servicio llamado igual que tu repositorio
   - Detectará automáticamente Python y Django
   - Configurará el build automáticamente

### Paso 2: Conectar a Base de Datos Existente

1. **En tu nuevo servicio web (Django):**
   - Ve a la pestaña **"Variables"**
   - Railway debería detectar automáticamente tu base de datos PostgreSQL

2. **Si no se detecta automáticamente:**
   - Ve a tu servicio PostgreSQL → **"Variables"**
   - Copia las siguientes variables:
     - `PGDATABASE`
     - `PGUSER`
     - `PGPASSWORD`
     - `PGHOST`
     - `PGPORT`
   - Vuelve a tu servicio web → **"Variables"**
   - Click en **"New Variable"**
   - Agrega cada variable manualmente

3. **Verificar Conexión:**
   - Las variables deberían aparecer en tu servicio web
   - Railway las inyectará automáticamente en el entorno

### Paso 3: Configurar Variables de Entorno Adicionales

En tu servicio web Django, ve a **"Variables"** y agrega:

#### Variables Obligatorias

```env
SECRET_KEY=tu-clave-secreta-super-segura-aqui
DEBUG=True
ENVIRONMENT=staging
```

**⚠️ IMPORTANTE:** Para generar un `SECRET_KEY` seguro:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Variables de Email

```env
EMAIL_HOST_USER=vctechmx@gmail.com
EMAIL_HOST_PASSWORD=vycyysxlyrildgot
```

#### Variables del Admin

```env
ADMIN_DEFAULT_PASSWORD=tu-contraseña-segura-admin
```

**Nota:** El admin se creará automáticamente después de las migraciones con estas credenciales:
- Usuario: `admin`
- Email: `admin@teomanager.com`
- Contraseña: Valor de `ADMIN_DEFAULT_PASSWORD` o `admin123456` por defecto

### Paso 4: Configurar el Servicio Web

1. **En tu servicio web Django:**
   - Ve a **"Settings"**

2. **Start Command:**
   - En el campo **"Start Command"**, verifica que esté:
     ```
     gunicorn core.wsgi --bind 0.0.0.0:$PORT
     ```
   - Si está vacío, agrégalo manualmente

3. **Build Command:**
   - Puede quedar vacío (Railway lo detecta automáticamente)
   - O puedes especificar: `pip install -r requirements.txt`

4. **Healthcheck (Opcional):**
   - Railway tiene healthcheck automático
   - Puedes agregar uno personalizado si lo necesitas

### Paso 5: Conectar Servicios (Si es Necesario)

1. **En tu servicio web Django:**
   - Ve a **"Settings"**
   - Busca la sección **"Service Connections"** o **"Connected Services"**
   - Si tu base de datos no aparece conectada:
     - Click en **"Connect Service"**
     - Selecciona tu servicio PostgreSQL
     - Esto hará que las variables de base de datos estén disponibles automáticamente

### Paso 6: Primer Deployment

1. **Railway iniciará el build automáticamente:**
   - Puedes ver el progreso en la pestaña **"Deployments"**
   - Click en el deployment activo para ver logs en tiempo real

2. **Proceso del Build:**
   ```
   → Detectando lenguaje (Python)
   → Instalando dependencias (pip install -r requirements.txt)
   → Ejecutando release command:
      - python manage.py migrate
      - python manage.py collectstatic --noinput
   → Iniciando servidor (gunicorn)
   ```

3. **Verificar Logs:**
   - Busca mensajes como:
     - ✅ "Operations to perform: Apply all migrations"
     - ✅ "Static files copied"
     - ✅ "Starting gunicorn"
     - ✅ "Application startup complete"

4. **Si hay errores:**
   - Revisa la sección [Solución de Problemas](#solución-de-problemas)

### Paso 7: Generar Dominio Público

1. **En tu servicio web Django:**
   - Ve a **"Settings"**
   - Busca la sección **"Networking"**
   - Click en **"Generate Domain"**
   - Railway generará una URL como: `tu-proyecto-production.up.railway.app`

2. **Guardar la URL:**
   - Esta será tu URL de acceso
   - Puedes compartirla para testeo

---

## 🔐 Configuración de Variables de Entorno

### Variables Automáticas de Railway

Railway proporciona estas variables automáticamente (no necesitas crearlas):

- `RAILWAY_ENVIRONMENT` - Detecta que estás en Railway
- `RAILWAY_PUBLIC_DOMAIN` - Tu dominio público
- `PORT` - Puerto del servidor (usado por Gunicorn)
- `RAILWAY_STATIC_URL` - URL para archivos estáticos

### Variables de Base de Datos (Desde PostgreSQL Service)

Si conectaste los servicios, estas estarán disponibles automáticamente:

- `PGDATABASE` - Nombre de la base de datos
- `PGUSER` - Usuario de PostgreSQL
- `PGPASSWORD` - Contraseña de PostgreSQL
- `PGHOST` - Host de la base de datos
- `PGPORT` - Puerto de la base de datos

### Variables que DEBES Configurar Manualmente

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `SECRET_KEY` | `[generar con comando]` | Clave secreta de Django (obligatorio) |
| `DEBUG` | `True` (testeo) / `False` (producción) | Modo debug |
| `ENVIRONMENT` | `staging` (testeo) / `production` | Entorno de deployment |
| `EMAIL_HOST_USER` | `vctechmx@gmail.com` | Usuario SMTP |
| `EMAIL_HOST_PASSWORD` | `[tu-contraseña]` | Contraseña SMTP |
| `ADMIN_DEFAULT_PASSWORD` | `[tu-contraseña]` | Contraseña del admin por defecto |

### Tabla de Configuración por Entorno

| Variable | Desarrollo Local | Staging (Railway) | Producción |
|----------|------------------|-------------------|------------|
| `DEBUG` | `True` | `True` | `False` |
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `SECRET_KEY` | `.env` | Railway Variables | Railway Variables |
| `ALLOWED_HOSTS` | `['*']` | Auto-detectado | Específico |

---

## 🔄 CI/CD Automático

### Cómo Funciona el CI/CD en Railway

Railway implementa **CI/CD automático** de la siguiente manera:

1. **Trigger:** Cada push a la branch principal (`main` o `master`)
2. **Build Automático:** Railway detecta cambios y inicia build
3. **Deploy Automático:** Si el build es exitoso, despliega automáticamente
4. **Rollback:** Si el deploy falla, mantiene la versión anterior

### Configuración de Auto-Deploy

1. **En tu servicio web Django:**
   - Ve a **"Settings"**
   - Busca **"Source"** o **"Repository"**
   - Verifica que esté conectado a tu repositorio GitHub
   - Verifica que la branch sea `main` (o la que uses)

2. **Branch de Deploy:**
   - Railway despliega automáticamente desde la branch configurada
   - Por defecto: `main` o `master`

### Workflow de Desarrollo

```bash
# 1. Desarrollo local
git checkout -b feature/nueva-funcionalidad
# ... hacer cambios ...
git commit -m "Agregar nueva funcionalidad"

# 2. Push a GitHub
git push origin feature/nueva-funcionalidad

# 3. Crear Pull Request (opcional)
# Revisar cambios en GitHub

# 4. Merge a main
git checkout main
git merge feature/nueva-funcionalidad
git push origin main

# 5. Railway detecta el push y despliega automáticamente
# → Build inicia automáticamente
# → Deploy se ejecuta si build es exitoso
```

### Monitoreo de Deployments

1. **Ver Deployments:**
   - Ve a tu servicio → **"Deployments"**
   - Verás historial de todos los deployments

2. **Ver Logs:**
   - Click en cualquier deployment
   - Verás logs completos del build y deploy

3. **Rollback Manual:**
   - Si un deployment falla, puedes hacer rollback:
     - Ve a **"Deployments"**
     - Click en el deployment anterior exitoso
     - Click en **"Redeploy"**

---

## ✅ Verificación Post-Deployment

### Paso 1: Verificar que el Servicio Está Activo

1. **En Railway:**
   - Ve a tu servicio web
   - Verifica que el estado sea **"Active"** (círculo verde)
   - Verifica que no haya errores en los logs

2. **Verificar Healthcheck:**
   - Railway tiene healthcheck automático
   - Si hay problemas, aparecerá un warning

### Paso 2: Acceder a la Aplicación

1. **Abrir en Navegador:**
   - Ve a tu dominio Railway: `tu-proyecto-production.up.railway.app`
   - Deberías ver la página principal de tu aplicación

2. **Verificar Funcionalidades Básicas:**
   - ✅ Página principal carga
   - ✅ CSS y JavaScript se cargan correctamente
   - ✅ No hay errores en la consola del navegador

### Paso 3: Verificar Admin de Django

1. **Acceder al Admin:**
   - Ve a: `tu-proyecto-production.up.railway.app/admin`
   - Deberías ver la pantalla de login

2. **Login con Admin:**
   - Usuario: `admin`
   - Contraseña: La que configuraste en `ADMIN_DEFAULT_PASSWORD` o `admin123456`

3. **Verificar que el Admin Funciona:**
   - ✅ Puedes hacer login
   - ✅ Ves el dashboard del admin
   - ✅ Puedes ver usuarios, productos, etc.

### Paso 4: Verificar Base de Datos

1. **Verificar Migraciones:**
   ```bash
   # En Railway, ve a tu servicio → "Settings" → "Run Command"
   python manage.py showmigrations
   ```
   - Todas las migraciones deberían estar aplicadas `[X]`

2. **Verificar Datos:**
   - En el admin, verifica que puedas ver:
     - Usuarios (debería existir el admin)
     - Perfiles de usuario
     - Productos/Servicios (si los hay)

### Paso 5: Verificar Archivos Estáticos

1. **Verificar que CSS/JS se Cargan:**
   - Abre las herramientas de desarrollador (F12)
   - Ve a la pestaña **"Network"**
   - Recarga la página
   - Verifica que los archivos estáticos se cargan (status 200)

2. **Verificar WhiteNoise:**
   - Los archivos estáticos deberían servirse desde `/static/`
   - No deberían dar error 404

### Paso 6: Probar Funcionalidades Principales

1. **Registro de Usuario:**
   - Intenta registrar un nuevo usuario
   - Verifica que se crea correctamente

2. **Login:**
   - Intenta hacer login con el usuario creado
   - Verifica que funciona

3. **Funcionalidades Específicas:**
   - Prueba las funcionalidades principales de tu app
   - Verifica que todo funciona en el entorno de staging

---

## 🔧 Solución de Problemas

### Error: "DisallowedHost"

**Síntoma:**
```
Invalid HTTP_HOST header: 'tu-dominio.railway.app'. You may need to add 'tu-dominio.railway.app' to ALLOWED_HOSTS.
```

**Solución:**
1. Verifica que `ALLOWED_HOSTS` en `settings.py` incluye `*.railway.app`
2. O agrega tu dominio específico a las variables de entorno
3. Verifica que `RAILWAY_PUBLIC_DOMAIN` está disponible

### Error: "Static files not found"

**Síntoma:**
- Los archivos CSS/JS no se cargan (404)
- La página se ve sin estilos

**Solución:**
1. Verifica que WhiteNoise está en `MIDDLEWARE`:
   ```python
   'whitenoise.middleware.WhiteNoiseMiddleware',
   ```

2. Verifica que `collectstatic` se ejecuta en el release command:
   ```
   release: python manage.py migrate && python manage.py collectstatic --noinput
   ```

3. Verifica los logs del deployment para ver si `collectstatic` se ejecutó

### Error: "Database connection failed"

**Síntoma:**
```
django.db.utils.OperationalError: could not connect to server
```

**Solución:**
1. Verifica que las variables de base de datos están configuradas:
   - `PGDATABASE`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGHOST`
   - `PGPORT`

2. Verifica que los servicios están conectados:
   - Ve a tu servicio web → "Settings" → "Service Connections"
   - Asegúrate de que PostgreSQL está conectado

3. Verifica que la base de datos está activa:
   - Ve a tu servicio PostgreSQL
   - Verifica que está "Active"

### Error: "Module not found"

**Síntoma:**
```
ModuleNotFoundError: No module named 'X'
```

**Solución:**
1. Verifica que todas las dependencias están en `requirements.txt`
2. Verifica los logs del build para ver qué módulo falta
3. Agrega la dependencia faltante a `requirements.txt`
4. Haz push y redeploy

### Error: "SECRET_KEY not set"

**Síntoma:**
- La aplicación no inicia
- Error sobre SECRET_KEY

**Solución:**
1. Genera un SECRET_KEY:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. Agrégalo a las variables de entorno en Railway:
   - Variable: `SECRET_KEY`
   - Valor: El generado arriba

### Error: "Admin no se crea automáticamente"

**Síntoma:**
- No puedes hacer login al admin
- El usuario admin no existe

**Solución:**
1. Verifica los logs del deployment
2. Busca mensajes sobre la creación del admin
3. Si hay errores, verifica que `ADMIN_DEFAULT_PASSWORD` está configurado
4. Crea el admin manualmente:
   ```bash
   # En Railway → Run Command
   python manage.py create_default_admin
   ```

### Build Falla

**Síntoma:**
- El deployment muestra "Build Failed"
- Logs muestran errores

**Solución:**
1. Revisa los logs completos del build
2. Busca el error específico
3. Errores comunes:
   - Dependencias faltantes → Agregar a `requirements.txt`
   - Error de sintaxis → Revisar código
   - Error de permisos → Verificar configuración

### Deploy se Queda en "Building"

**Síntoma:**
- El deployment está en "Building" por mucho tiempo

**Solución:**
1. Espera unos minutos (primer build puede tardar)
2. Si pasa más de 10 minutos, cancela y revisa logs
3. Verifica que no hay dependencias muy pesadas
4. Considera usar build cache si es posible

---

## ✅ Checklist Completo

### Pre-Deployment

- [ ] Repositorio en GitHub con código actualizado
- [ ] `Procfile` creado y configurado
- [ ] `runtime.txt` creado con versión correcta de Python
- [ ] `railway.json` creado (opcional)
- [ ] `requirements.txt` actualizado con todas las dependencias
- [ ] `settings.py` configurado para producción/staging
- [ ] `.gitignore` incluye `.env` y archivos sensibles
- [ ] Código commiteado y pusheado a GitHub

### Configuración en Railway

- [ ] Proyecto creado en Railway
- [ ] Servicio web Django creado y conectado a GitHub
- [ ] Base de datos PostgreSQL conectada al servicio web
- [ ] Variables de entorno configuradas:
  - [ ] `SECRET_KEY` (generado y configurado)
  - [ ] `DEBUG=True` (para testeo)
  - [ ] `ENVIRONMENT=staging`
  - [ ] `EMAIL_HOST_USER`
  - [ ] `EMAIL_HOST_PASSWORD`
  - [ ] `ADMIN_DEFAULT_PASSWORD`
- [ ] Variables de base de datos disponibles (automáticas o manuales)
- [ ] Start Command configurado: `gunicorn core.wsgi --bind 0.0.0.0:$PORT`

### Post-Deployment

- [ ] Build completado exitosamente
- [ ] Deployment activo y funcionando
- [ ] Dominio público generado
- [ ] Aplicación accesible en el navegador
- [ ] Admin de Django accesible y funcional
- [ ] Login con admin funciona
- [ ] Archivos estáticos se cargan correctamente
- [ ] Base de datos conectada y migraciones aplicadas
- [ ] Funcionalidades principales probadas y funcionando

### Verificación de Funcionalidades

- [ ] Registro de usuarios funciona
- [ ] Login funciona
- [ ] Dashboard carga correctamente
- [ ] Productos/Servicios se muestran
- [ ] Formularios funcionan
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs de Railway

---

## 📝 Próximos Pasos

### Para la Versión de Producción (Después de Implementar Suscripciones y Pagos)

1. **Actualizar Configuración:**
   - Cambiar `ENVIRONMENT=production` en variables de entorno
   - Cambiar `DEBUG=False`
   - Configurar `ALLOWED_HOSTS` específicos
   - Habilitar todas las configuraciones de seguridad

2. **Dominio Personalizado:**
   - Configurar dominio propio (ej: `app.tuempresa.com`)
   - Configurar SSL/HTTPS
   - Actualizar `ALLOWED_HOSTS` con el dominio

3. **Monitoreo:**
   - Configurar logging avanzado
   - Configurar alertas
   - Configurar monitoreo de performance

4. **Backup:**
   - Configurar backups automáticos de la base de datos
   - Configurar estrategia de recuperación

5. **Escalabilidad:**
   - Considerar múltiples instancias si es necesario
   - Configurar load balancing si es necesario

### Mejoras Futuras

- [ ] Implementar CI/CD con GitHub Actions (además de Railway)
- [ ] Configurar tests automatizados antes del deploy
- [ ] Configurar staging y producción separados
- [ ] Implementar feature flags
- [ ] Configurar CDN para archivos estáticos
- [ ] Implementar cache (Redis)
- [ ] Configurar monitoreo con Sentry o similar

---

## 📚 Recursos Adicionales

### Documentación Oficial

- [Railway Documentation](https://docs.railway.app/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [WhiteNoise Documentation](https://whitenoise.readthedocs.io/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

### Comandos Útiles

```bash
# Ver logs en tiempo real
railway logs

# Ejecutar comandos Django
railway run python manage.py [comando]

# Ver variables de entorno
railway variables

# Conectar a base de datos
railway connect
```

### Contacto y Soporte

- Railway Support: [support@railway.app](mailto:support@railway.app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)
- Documentación del Proyecto: `Documentacion/`

---

## 📅 Historial de Versiones

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2024-12-10 | Versión inicial - Deployment para testeo |

---

**Última actualización:** 2024-12-10  
**Versión del documento:** 1.0  
**Estado:** ✅ Listo para deployment de testeo

