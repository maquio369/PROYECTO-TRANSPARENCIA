from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Archivo, Fraccion
from .forms import ArchivoForm

@login_required
def cargar_archivo_debug(request):
    if request.method == 'POST':
        print("=== DEBUG POST ===")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        form = ArchivoForm(request.POST, request.FILES, user=request.user)
        print(f"Form is valid: {form.is_valid()}")
        
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            messages.error(request, f"Errores en formulario: {form.errors}")
            return render(request, 'archivos/cargar_archivo.html', {'form': form})
        
        try:
            # Crear archivo manualmente para debug
            archivo = form.save(commit=False)
            archivo.usuario = request.user
            archivo.version = 1  # Simplificar por ahora
            archivo.save()
            
            messages.success(request, f'✅ Archivo guardado con ID: {archivo.id}')
            return redirect('archivos:dashboard')
            
        except Exception as e:
            print(f"Error al guardar: {e}")
            messages.error(request, f'Error: {e}')
            
    else:
        form = ArchivoForm(user=request.user)
    
    return render(request, 'archivos/cargar_archivo.html', {'form': form})