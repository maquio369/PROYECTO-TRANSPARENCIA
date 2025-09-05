from django.http import HttpResponse, Http404
from django.conf import settings
import os
import mimetypes

def serve_static_file(request, path):
    """
    Servir archivos estáticos con el tipo MIME correcto
    """
    # Construir la ruta completa del archivo
    file_path = os.path.join(settings.STATIC_ROOT, path)
    
    # Verificar si el archivo existe
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise Http404("Archivo no encontrado")
    
    # Determinar el tipo MIME
    content_type, encoding = mimetypes.guess_type(file_path)
    
    # Tipos MIME específicos para archivos comunes
    if content_type is None:
        if path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.png'):
            content_type = 'image/png'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            content_type = 'image/jpeg'
        elif path.endswith('.gif'):
            content_type = 'image/gif'
        elif path.endswith('.svg'):
            content_type = 'image/svg+xml'
        else:
            content_type = 'application/octet-stream'
    
    # Leer y devolver el archivo
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            if encoding:
                response['Content-Encoding'] = encoding
            return response
    except IOError:
        raise Http404("Error al leer el archivo")