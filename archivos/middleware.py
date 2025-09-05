from django.http import FileResponse, Http404
from django.conf import settings
import os
import mimetypes

class StaticFilesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Manejar archivos estáticos
        if request.path.startswith(settings.STATIC_URL):
            return self.serve_static_file(request)
        
        response = self.get_response(request)
        return response

    def serve_static_file(self, request):
        # Obtener la ruta del archivo
        path = request.path[len(settings.STATIC_URL):]
        file_path = os.path.join(settings.STATIC_ROOT, path)
        
        # Verificar si el archivo existe
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # Determinar el tipo MIME
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                if file_path.endswith('.css'):
                    content_type = 'text/css'
                elif file_path.endswith('.js'):
                    content_type = 'application/javascript'
                else:
                    content_type = 'application/octet-stream'
            
            # Devolver el archivo con el tipo MIME correcto
            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            return response
        
        raise Http404("Archivo estático no encontrado")