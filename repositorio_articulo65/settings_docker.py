from .settings import *
import os

# Configuración específica para Docker
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'  # Cambiar a True temporalmente

# Hosts permitidos para Docker
ALLOWED_HOSTS = ['172.16.35.75', 'localhost', '127.0.0.1', '*']

# Base de datos para Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'repositorio_articulo65'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres123'),
        'HOST': os.environ.get('DB_HOST', 'db'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 60,
    }
}

# Archivos estáticos para Docker
STATIC_ROOT = '/app/staticfiles'
STATICFILES_DIRS = []

# Servir archivos estáticos en desarrollo
if DEBUG:
    import os
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Archivos media para Docker
MEDIA_ROOT = '/app/media'

# Configuración de logging para Docker
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Configuración de seguridad para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = False  # Configurar según tu proxy
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'