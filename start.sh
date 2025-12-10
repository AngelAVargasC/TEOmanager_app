#!/bin/bash
set -e

echo "🔄 Ejecutando migraciones..."
python manage.py migrate --noinput || echo "⚠️  Advertencia: Las migraciones fallaron, pero continuando..."

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || echo "⚠️  Advertencia: collectstatic falló, pero continuando..."

echo "🚀 Iniciando servidor Gunicorn..."
exec gunicorn core.wsgi --bind 0.0.0.0:$PORT --log-file -

