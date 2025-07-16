import os
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'archivos',  # Nuestra app principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'repositorio_articulo65.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # ← AGREGADO para archivos media
            ],
        },
    },
]

WSGI_APPLICATION = 'repositorio_articulo65.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='repositorio_articulo65'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 60,  # Reutilizar conexiones
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Crear directorio static si no existe
STATICFILES_DIRS = []
static_dir = BASE_DIR / 'static'
if static_dir.exists():
    STATICFILES_DIRS = [static_dir]

# Media files (CONFIGURACIÓN CRÍTICA PARA ARCHIVOS)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Crear directorio media si no existe
try:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directorio media confirmado: {MEDIA_ROOT}")
    
    # Crear subdirectorio para archivos
    archivos_dir = MEDIA_ROOT / 'archivos'
    archivos_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Directorio archivos confirmado: {archivos_dir}")
    
except Exception as e:
    print(f"❌ Error creando directorios media: {e}")

# File upload settings (CONFIGURACIÓN CRÍTICA)
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB
FILE_UPLOAD_PERMISSIONS = 0o644  # Permisos de archivos
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755  # Permisos de directorios

# Configuración adicional para archivos grandes
FILE_UPLOAD_TEMP_DIR = None  # Usar directorio temporal del sistema
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = 'archivos:login'
LOGIN_REDIRECT_URL = 'archivos:dashboard'
LOGOUT_REDIRECT_URL = 'archivos:login'

# Logging para debug (IMPORTANTE PARA DIAGNOSTICAR PROBLEMAS)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'archivos': {  # Logger específico para tu app
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',  # Cambiar a DEBUG para ver queries SQL
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Configuración de seguridad para desarrollo
if DEBUG:
    # Permitir todos los hosts en desarrollo
    ALLOWED_HOSTS = ['*']
    
    # Configuración adicional para desarrollo
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
    # Mostrar errores detallados
    ADMINS = [
        ('Admin', 'admin@localhost'),
    ]
    
    # Configuración de email para desarrollo (opcional)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuración de cache (opcional, mejora rendimiento)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Configuración de sesiones
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Configuración de seguridad adicional
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Variables de entorno recomendadas para tu archivo .env
print("\n" + "="*50)
print("📋 VARIABLES DE ENTORNO RECOMENDADAS (.env):")
print("="*50)
print("SECRET_KEY=tu_clave_secreta_aqui")
print("DEBUG=True")
print("DB_NAME=repositorio_articulo65")
print("DB_USER=tu_usuario_postgres")
print("DB_PASSWORD=tu_password_postgres")
print("DB_HOST=localhost")
print("DB_PORT=5432")
print("="*50)

# Verificación de configuración crítica
if DEBUG:
    print("\n🔍 VERIFICACIÓN DE CONFIGURACIÓN:")
    print(f"✅ BASE_DIR: {BASE_DIR}")
    print(f"✅ MEDIA_ROOT: {MEDIA_ROOT}")
    print(f"✅ MEDIA_URL: {MEDIA_URL}")
    print(f"✅ DEBUG: {DEBUG}")
    print(f"✅ DB_NAME: {DATABASES['default']['NAME']}")
    
    # Verificar que los directorios existen
    if MEDIA_ROOT.exists():
        print(f"✅ Directorio media existe")
    else:
        print(f"❌ Directorio media NO existe")
    
    # Verificar permisos (en Unix/Linux)
    try:
        import stat
        media_stat = MEDIA_ROOT.stat()
        permissions = stat.filemode(media_stat.st_mode)
        print(f"📁 Permisos directorio media: {permissions}")
    except:
        print("ℹ️ No se pudieron verificar permisos (Windows?)")
    
    print("🔍 Fin verificación\n")