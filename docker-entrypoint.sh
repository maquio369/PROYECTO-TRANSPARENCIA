#!/bin/bash

# Configurar Django settings para Docker
export DJANGO_SETTINGS_MODULE=repositorio_articulo65.settings_docker

# Esperar a que PostgreSQL esté disponible
echo "Esperando a PostgreSQL..."
until python -c "import psycopg2; psycopg2.connect(host='172.16.35.75', port='32768', user='maquio', password='maquio92', dbname='repositorio_transparencia')" 2>/dev/null; do
  echo "Esperando conexión a la base de datos..."
  sleep 2
done
echo "PostgreSQL está disponible"

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Verificar que los archivos estáticos se copiaron correctamente
echo "Verificando archivos estáticos..."
ls -la /app/staticfiles/css/ || echo "Directorio CSS no encontrado"
ls -la /app/static/css/ || echo "Directorio static/css no encontrado"

# Cargar datos iniciales si no existen
echo "Cargando datos iniciales..."
python manage.py cargar_fracciones || echo "Fracciones ya cargadas"
python manage.py crear_usuarios_demo || echo "Usuarios demo ya existen"

# Ejecutar comando pasado como argumento
exec "$@"