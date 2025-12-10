# 🔐 Sistema de Administrador por Defecto

## 📋 Resumen

El proyecto está configurado para crear automáticamente un usuario administrador por defecto después de ejecutar las migraciones. Este sistema garantiza que siempre haya un administrador disponible para gestionar el sistema.

## 🎯 Características

- ✅ Creación automática después de las migraciones
- ✅ Usuario: `admin`
- ✅ Email: `admin@teomanager.com`
- ✅ PerfilUsuario con permisos de Administrador
- ✅ `is_superuser = True` y `is_staff = True`
- ✅ Comando manual disponible para personalización

## 🔧 Componentes Implementados

### 1. Señal Automática (`apps/accounts/signals.py`)

Se ejecuta automáticamente después de cada migración y crea el usuario admin si no existe:

```python
@receiver(post_migrate)
def crear_admin_por_defecto(sender, app_config, **kwargs):
    # Crea automáticamente el usuario 'admin' si no existe
```

**Características:**
- Solo se ejecuta para la app `accounts`
- No se ejecuta durante tests
- Usa la contraseña de la variable de entorno `ADMIN_DEFAULT_PASSWORD`
- Si no existe la variable, usa `admin123456` por defecto

### 2. Comando Manual (`python manage.py create_default_admin`)

Permite crear o personalizar el administrador manualmente:

```bash
# Crear con valores por defecto
python manage.py create_default_admin

# Personalizar username y email
python manage.py create_default_admin --username miadmin --email admin@miempresa.com

# Especificar contraseña directamente
python manage.py create_default_admin --password MiContraseñaSegura123

# Saltar si ya existe
python manage.py create_default_admin --skip-if-exists
```

## ⚙️ Configuración

### Variables de Entorno

Agrega al archivo `.env`:

```env
# Contraseña por defecto para el administrador
ADMIN_DEFAULT_PASSWORD=tu_contraseña_segura_aqui
```

**⚠️ IMPORTANTE:** 
- Cambia esta contraseña después del primer login
- En producción, usa una contraseña fuerte
- No compartas este archivo públicamente

### Credenciales por Defecto

Si no se configura `ADMIN_DEFAULT_PASSWORD`, se usan estos valores:

- **Usuario:** `admin`
- **Email:** `admin@teomanager.com`
- **Contraseña:** `admin123456` (⚠️ Cambiar inmediatamente)

## 📝 Flujo de Creación

1. **Después de `python manage.py migrate`:**
   - Se ejecuta la señal `post_migrate`
   - Verifica si el usuario `admin` existe
   - Si no existe, lo crea automáticamente
   - Crea el PerfilUsuario asociado con permisos de Administrador

2. **Primer Login:**
   - Usa las credenciales por defecto
   - **Cambia la contraseña inmediatamente**

3. **Personalización (Opcional):**
   - Usa el comando manual para crear otro admin
   - O modifica el usuario existente desde el panel de administración

## 🔒 Seguridad

### Buenas Prácticas

1. **Cambiar contraseña inmediatamente:**
   ```bash
   python manage.py changepassword admin
   ```

2. **Usar contraseña fuerte:**
   - Mínimo 12 caracteres
   - Combinar mayúsculas, minúsculas, números y símbolos
   - No usar palabras comunes

3. **En producción:**
   - Configurar `ADMIN_DEFAULT_PASSWORD` en variables de entorno del servidor
   - No usar contraseñas por defecto
   - Considerar deshabilitar la creación automática después del setup inicial

## 🛠️ Uso del Comando Manual

### Opciones Disponibles

```bash
python manage.py create_default_admin [opciones]

Opciones:
  --username USERNAME    Nombre de usuario (default: admin)
  --email EMAIL          Email del administrador
  --password PASSWORD     Contraseña (si no se proporciona, se pedirá)
  --skip-if-exists       No hacer nada si el usuario ya existe
```

### Ejemplos

```bash
# Crear admin básico (pedirá contraseña)
python manage.py create_default_admin

# Crear admin personalizado
python manage.py create_default_admin \
  --username superadmin \
  --email superadmin@miempresa.com \
  --password MiContraseñaSuperSegura123!

# Verificar si existe sin crear
python manage.py create_default_admin --skip-if-exists
```

## 🔍 Verificación

Para verificar que el administrador fue creado correctamente:

```bash
# Ver usuarios administradores
python manage.py shell
```

```python
from django.contrib.auth.models import User
from apps.accounts.models import PerfilUsuario

# Verificar usuario admin
admin = User.objects.get(username='admin')
print(f"Usuario: {admin.username}")
print(f"Email: {admin.email}")
print(f"Superuser: {admin.is_superuser}")
print(f"Staff: {admin.is_staff}")

# Verificar perfil
perfil = admin.userprofile
print(f"Permisos: {perfil.permisos}")
print(f"Tipo cuenta: {perfil.tipo_cuenta}")
```

## 🚨 Troubleshooting

### El admin no se crea automáticamente

1. Verifica que las migraciones se ejecutaron:
   ```bash
   python manage.py migrate
   ```

2. Verifica que la señal está registrada en `apps.py`:
   ```python
   def ready(self):
       import apps.accounts.signals
   ```

3. Verifica que no estás en modo test:
   - La señal no se ejecuta durante tests

### Error: "El usuario ya existe"

- Usa `--skip-if-exists` para saltar
- O elige otro username con `--username`

### No puedo hacer login

1. Verifica las credenciales:
   - Usuario: `admin`
   - Contraseña: La configurada en `ADMIN_DEFAULT_PASSWORD` o `admin123456`

2. Verifica que el usuario está activo:
   ```python
   admin = User.objects.get(username='admin')
   print(admin.is_active)  # Debe ser True
   ```

## 📚 Archivos Relacionados

- `apps/accounts/signals.py` - Señal de creación automática
- `apps/accounts/management/commands/create_default_admin.py` - Comando manual
- `apps/accounts/apps.py` - Registro de señales
- `.env` - Variables de entorno (incluir `ADMIN_DEFAULT_PASSWORD`)

## ✅ Checklist Post-Instalación

- [ ] Ejecutar migraciones: `python manage.py migrate`
- [ ] Verificar que el admin fue creado
- [ ] Hacer login con credenciales por defecto
- [ ] Cambiar contraseña inmediatamente
- [ ] Configurar `ADMIN_DEFAULT_PASSWORD` en `.env`
- [ ] (Opcional) Deshabilitar creación automática en producción

