# Usar imagen oficial de Python
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/media/archivos /app/staticfiles

# Establecer permisos
RUN chmod -R 755 /app/media

# Exponer puerto
EXPOSE 8000

# Script de entrada
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Comando por defecto
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]