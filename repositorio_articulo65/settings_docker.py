from .settings import *
import os

# Configuración específica para Docker
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Hosts permitidos para Docker
ALLOWED_HOSTS = ['172.16.35.75', 'localhost', '127.0.0.1', '*']

# Configuración de seguridad para Docker
SECURE_CROSS_ORIGIN_OPENER_POLICY = None
SECURE_REFERRER_POLICY = None

# Middleware personalizado para archivos estáticos
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'archivos.middleware.StaticFilesMiddleware',  # Middleware personalizado
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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
STATIC_URL = '/static/'

# Directorios de archivos estáticos
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
] if os.path.exists(os.path.join(BASE_DIR, 'static')) else []

# Configuración de archivos estáticos
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Archivos media para Docker
MEDIA_ROOT = '/app/media'
MEDIA_URL = '/media/'

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

# Configuración adicional para archivos estáticos en Docker
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuración de MIME types
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Asegurar que Django sirva archivos estáticos correctamente
USE_TZ = True
