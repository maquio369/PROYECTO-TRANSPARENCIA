# 🐳 Dockerización del Sistema Artículo 65

## 📋 Archivos Creados

- `Dockerfile` - Imagen base para desarrollo
- `Dockerfile.prod` - Imagen optimizada para producción
- `docker-compose.yml` - Orquestación para desarrollo
- `docker-compose.prod.yml` - Orquestación para producción
- `docker-entrypoint.sh` - Script de inicialización
- `settings_docker.py` - Configuración específica para Docker
- `requirements-docker.txt` - Dependencias con servidor de producción
- `nginx.conf` - Configuración de proxy reverso
- `.dockerignore` - Archivos excluidos del build

## 🚀 Uso con Portainer

### 1. Desarrollo (Recomendado para pruebas)

En Portainer, crear stack con este `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: repositorio_articulo65
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  web:
    build: https://github.com/tu-usuario/tu-repo.git
    environment:
      - DEBUG=False
      - SECRET_KEY=tu-clave-secreta-aqui
      - DB_NAME=repositorio_articulo65
      - DB_USER=postgres
      - DB_PASSWORD=postgres123
      - DB_HOST=db
      - DB_PORT=5432
    volumes:
      - media_files:/app/media
    ports:
      - "3018:8000"
    depends_on:
      - db
    restart: unless-stopped

volumes:
  postgres_data:
  media_files:
```

### 2. Producción (Con Nginx)

Para producción, usar `docker-compose.prod.yml` en Portainer.

## 🛠️ Comandos Locales

```bash
# Desarrollo
docker-compose up -d

# Producción
docker-compose -f docker-compose.prod.yml up -d

# Ver logs
docker-compose logs -f web

# Ejecutar comandos Django
docker-compose exec web python manage.py createsuperuser
```

## 🔧 Variables de Entorno

Configurar en Portainer:

- `SECRET_KEY` - Clave secreta de Django
- `DB_PASSWORD` - Contraseña de PostgreSQL
- `DEBUG` - true/false para modo debug

## 📊 Acceso

- **Aplicación:** http://172.16.35.75:3018
- **Admin:** http://172.16.35.75:3018/admin/

## 🔍 Solución de Problemas

1. **Error de conexión DB:** Verificar que el servicio `db` esté corriendo
2. **Archivos no cargan:** Verificar volúmenes de `media_files`
3. **Error 500:** Revisar logs con `docker logs articulo65_web`

## 📝 Notas Importantes

- Los datos se persisten en volúmenes Docker
- Los usuarios demo se crean automáticamente
- Las migraciones se ejecutan al iniciar
- Los archivos media se almacenan en volumen persistente