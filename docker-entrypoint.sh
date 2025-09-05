#!/bin/bash

# Configurar Django settings para Docker
export DJANGO_SETTINGS_MODULE=repositorio_articulo65.settings_docker

# Esperar a que PostgreSQL esté disponible
echo "Esperando a PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL está disponible"

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar archivos estáticos
echo "Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Cargar datos iniciales si no existen
echo "Cargando datos iniciales..."
python manage.py cargar_fracciones || echo "Fracciones ya cargadas"
python manage.py crear_usuarios_demo || echo "Usuarios demo ya existen"

# Ejecutar comando pasado como argumento
exec "$@"