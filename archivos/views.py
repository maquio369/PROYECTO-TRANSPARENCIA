from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView, ListView, CreateView
from django.views import View
from django.http import HttpResponse, Http404, FileResponse
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction
import mimetypes
import os

from .models import Archivo, Fraccion, PerfilUsuario, HistorialAcceso
from .forms import ArchivoForm

class DashboardView(LoginRequiredMixin, TemplateView):
    """Vista principal del dashboard"""
    template_name = 'archivos/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener perfil del usuario
        try:
            perfil = self.request.user.perfilusuario
            tipo_usuario = perfil.tipo_usuario
        except PerfilUsuario.DoesNotExist:
            tipo_usuario = None
            messages.warning(self.request, 'Tu usuario no tiene un perfil asignado. Contacta al administrador.')
        
        # Filtrar fracciones según el tipo de usuario
        if tipo_usuario:
            fracciones = Fraccion.objects.filter(
                tipo_usuario_asignado=tipo_usuario,
                activa=True
            )
        else:
            fracciones = Fraccion.objects.filter(activa=True)
        
        # Estadísticas básicas
        total_archivos = Archivo.objects.filter(
            fraccion__in=fracciones,
            vigente=True
        ).count()
        
        archivos_recientes = Archivo.objects.filter(
            fraccion__in=fracciones
        ).order_by('-created_at')[:5]
        
        context.update({
            'fracciones': fracciones,
            'total_archivos': total_archivos,
            'archivos_recientes': archivos_recientes,
            'tipo_usuario': tipo_usuario,
        })
        
        return context

class CargarArchivoView(LoginRequiredMixin, CreateView):
    """Vista para cargar archivos"""
    model = Archivo
    form_class = ArchivoForm
    template_name = 'archivos/cargar_archivo.html'
    success_url = reverse_lazy('archivos:dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        """
        Manejo mejorado de la subida de archivos con mejor debug y transacciones
        """
        # DEBUG: Imprimir datos recibidos
        print("=== DEBUG FORMULARIO ===")
        print(f"POST data: {self.request.POST}")
        print(f"FILES data: {self.request.FILES}")
        print(f"Form cleaned data: {form.cleaned_data}")
        print(f"Usuario: {self.request.user}")
        print("========================")
        
        # Verificar perfil de usuario
        try:
            perfil = self.request.user.perfilusuario
            print(f"Perfil usuario: {perfil.tipo_usuario}")
        except PerfilUsuario.DoesNotExist:
            messages.error(self.request, 'Tu usuario no tiene un perfil asignado. Contacta al administrador.')
            return self.form_invalid(form)
        
        # Verificar si hay archivo
        if 'archivo' not in form.cleaned_data or not form.cleaned_data['archivo']:
            print("❌ No se recibió archivo en form.cleaned_data")
            messages.error(self.request, 'No se recibió ningún archivo.')
            return self.form_invalid(form)
        
        archivo_file = form.cleaned_data['archivo']
        print(f"✅ Archivo recibido: {archivo_file.name}, Tamaño: {archivo_file.size} bytes")
        
        # Validar tamaño del archivo (100 MB)
        if archivo_file.size > 104857600:  # 100 MB en bytes
            print(f"❌ Archivo muy grande: {archivo_file.size} bytes")
            messages.error(self.request, 'El archivo no puede superar los 100 MB.')
            return self.form_invalid(form)
        
        # Verificar que la fracción corresponde al usuario
        fraccion = form.cleaned_data['fraccion']
        if fraccion.tipo_usuario_asignado != perfil.tipo_usuario:
            print(f"❌ Fracción no permitida para usuario: {fraccion.tipo_usuario_asignado} != {perfil.tipo_usuario}")
            messages.error(self.request, 'No tienes permisos para cargar archivos en esta fracción.')
            return self.form_invalid(form)
        
        # Usar transacción atómica para evitar problemas de concurrencia
        try:
            with transaction.atomic():
                # Asignar datos al formulario
                form.instance.usuario = self.request.user
                
                # Calcular versión
                archivos_existentes = Archivo.objects.filter(
                    fraccion=form.instance.fraccion,
                    año=form.instance.año,
                    periodo_especifico=form.instance.periodo_especifico
                ).select_for_update()  # Lock para evitar race conditions
                
                if archivos_existentes.exists():
                    ultima_version = archivos_existentes.order_by('-version').first().version
                    form.instance.version = ultima_version + 1
                    print(f"📝 Nueva versión calculada: {form.instance.version}")
                    
                    # Marcar archivos anteriores como no vigentes
                    archivos_existentes.update(vigente=False)
                else:
                    form.instance.version = 1
                    print("📝 Primera versión del archivo")
                
                # Establecer como vigente
                form.instance.vigente = True
                
                # Guardar el archivo
                print("💾 Intentando guardar archivo...")
                archivo_instance = form.save()
                
                print(f"✅ Archivo guardado exitosamente con ID: {archivo_instance.id}")
                print(f"📁 Ruta del archivo: {archivo_instance.archivo.path}")
                
                # Verificar que el archivo se guardó físicamente
                if os.path.exists(archivo_instance.archivo.path):
                    print(f"✅ Archivo físico confirmado en: {archivo_instance.archivo.path}")
                else:
                    print(f"❌ Archivo físico NO encontrado en: {archivo_instance.archivo.path}")
                
                messages.success(
                    self.request, 
                    f'Archivo "{archivo_file.name}" cargado exitosamente como versión {archivo_instance.version}.'
                )
                
                return redirect(self.success_url)
                
        except Exception as e:
            print(f"❌ Error en transacción: {type(e).__name__}: {e}")
            import traceback
            print(f"Traceback completo:")
            traceback.print_exc()
            
            messages.error(self.request, f'Error al guardar el archivo: {e}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Manejo mejorado de formularios inválidos"""
        print("=== FORMULARIO INVÁLIDO ===")
        print(f"Errores del formulario: {form.errors}")
        print(f"Errores no de campo: {form.non_field_errors()}")
        print("===========================")
        
        # Agregar errores como mensajes
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    messages.error(self.request, f"Error: {error}")
                else:
                    messages.error(self.request, f"Error en {field}: {error}")
        
        return super().form_invalid(form)

class ListadoArchivosView(LoginRequiredMixin, ListView):
    """Vista para listar archivos"""
    model = Archivo
    template_name = 'archivos/listado_archivos.html'
    context_object_name = 'archivos'
    paginate_by = 20
    
    def get_queryset(self):
        # Obtener perfil del usuario
        try:
            perfil = self.request.user.perfilusuario
            tipo_usuario = perfil.tipo_usuario
        except PerfilUsuario.DoesNotExist:
            messages.warning(self.request, 'Tu usuario no tiene un perfil asignado.')
            return Archivo.objects.none()
        
        # Filtrar por tipo de usuario
        queryset = Archivo.objects.filter(
            fraccion__tipo_usuario_asignado=tipo_usuario,
            vigente=True
        ).select_related('fraccion', 'usuario').order_by('-created_at')
        
        # Filtros adicionales
        fraccion_id = self.request.GET.get('fraccion')
        año = self.request.GET.get('año')
        
        if fraccion_id:
            queryset = queryset.filter(fraccion_id=fraccion_id)
        
        if año:
            queryset = queryset.filter(año=año)
        
        # Funcionalidad de búsqueda
        busqueda = self.request.GET.get('busqueda')
        if busqueda:
            queryset = queryset.filter(
                Q(nombre_original__icontains=busqueda) |
                Q(fraccion__nombre__icontains=busqueda) |
                Q(fraccion__numero__icontains=busqueda)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener fracciones para filtros
        try:
            perfil = self.request.user.perfilusuario
            tipo_usuario = perfil.tipo_usuario
            fracciones = Fraccion.objects.filter(
                tipo_usuario_asignado=tipo_usuario,
                activa=True
            )
        except PerfilUsuario.DoesNotExist:
            fracciones = Fraccion.objects.none()
        
        # Años disponibles
        años = Archivo.objects.filter(
            fraccion__in=fracciones
        ).values_list('año', flat=True).distinct().order_by('-año')
        
        context.update({
            'fracciones': fracciones,
            'años': años,
            'fraccion_seleccionada': self.request.GET.get('fraccion'),
            'año_seleccionado': self.request.GET.get('año'),
            'busqueda_actual': self.request.GET.get('busqueda', ''),
        })
        
        return context

class HistorialView(LoginRequiredMixin, ListView):
    """Vista para mostrar historial de una fracción"""
    model = Archivo
    template_name = 'archivos/historial.html'
    context_object_name = 'archivos'
    
    def get_queryset(self):
        fraccion_id = self.kwargs['fraccion_id']
        
        # Verificar permisos
        try:
            perfil = self.request.user.perfilusuario
            fraccion = get_object_or_404(Fraccion, id=fraccion_id)
            
            if fraccion.tipo_usuario_asignado != perfil.tipo_usuario:
                messages.error(self.request, 'No tienes permisos para ver el historial de esta fracción.')
                return Archivo.objects.none()
                
        except PerfilUsuario.DoesNotExist:
            messages.error(self.request, 'Tu usuario no tiene un perfil asignado.')
            return Archivo.objects.none()
        
        return Archivo.objects.filter(
            fraccion_id=fraccion_id
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fraccion_id = self.kwargs['fraccion_id']
        context['fraccion'] = get_object_or_404(Fraccion, id=fraccion_id)
        return context

class DescargarArchivoView(LoginRequiredMixin, View):
    """Vista para descargar archivos con URL pública"""
    
    def get(self, request, archivo_id):
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        # Verificar permisos
        try:
            perfil = request.user.perfilusuario
            if archivo.fraccion.tipo_usuario_asignado != perfil.tipo_usuario:
                raise Http404("No tienes permisos para acceder a este archivo")
        except PerfilUsuario.DoesNotExist:
            raise Http404("Tu usuario no tiene un perfil asignado")
        
        # Registrar acceso
        try:
            HistorialAcceso.objects.create(
                archivo=archivo,
                usuario=request.user,
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            print(f"Error al registrar acceso: {e}")
        
        # Servir archivo
        try:
            if archivo.archivo and os.path.exists(archivo.archivo.path):
                response = FileResponse(
                    open(archivo.archivo.path, 'rb'),
                    as_attachment=True,
                    filename=archivo.nombre_original
                )
                return response
            else:
                raise Http404("Archivo físico no encontrado")
        except Exception as e:
            print(f"Error al servir archivo: {e}")
            raise Http404("Error al acceder al archivo")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class VerArchivoView(LoginRequiredMixin, View):
    """Vista para visualizar archivos en el navegador"""
    
    def get(self, request, archivo_id):
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        # Verificar permisos (mismo código que DescargarArchivoView)
        try:
            perfil = request.user.perfilusuario
            if archivo.fraccion.tipo_usuario_asignado != perfil.tipo_usuario:
                raise Http404("No tienes permisos para acceder a este archivo")
        except PerfilUsuario.DoesNotExist:
            raise Http404("Tu usuario no tiene un perfil asignado")
        
        # Registrar acceso
        try:
            HistorialAcceso.objects.create(
                archivo=archivo,
                usuario=request.user,
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            print(f"Error al registrar acceso: {e}")
        
        # Servir archivo para visualización
        try:
            if archivo.archivo and os.path.exists(archivo.archivo.path):
                content_type, _ = mimetypes.guess_type(archivo.archivo.path)
                response = FileResponse(
                    open(archivo.archivo.path, 'rb'),
                    content_type=content_type
                )
                return response
            else:
                raise Http404("Archivo físico no encontrado")
        except Exception as e:
            print(f"Error al servir archivo: {e}")
            raise Http404("Error al acceder al archivo")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class EstadisticasView(LoginRequiredMixin, TemplateView):
    """Vista para mostrar estadísticas"""
    template_name = 'archivos/estadisticas.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener tipo de usuario
        try:
            perfil = self.request.user.perfilusuario
            tipo_usuario = perfil.tipo_usuario
        except PerfilUsuario.DoesNotExist:
            tipo_usuario = None
            messages.warning(self.request, 'Tu usuario no tiene un perfil asignado.')
        
        if tipo_usuario:
            # Estadísticas por fracción
            stats_fraccion = Archivo.objects.filter(
                fraccion__tipo_usuario_asignado=tipo_usuario,
                vigente=True
            ).values(
                'fraccion__numero', 'fraccion__nombre'
            ).annotate(
                total=Count('id')
            ).order_by('fraccion__numero')
            
            # Estadísticas por año
            stats_año = Archivo.objects.filter(
                fraccion__tipo_usuario_asignado=tipo_usuario
            ).values('año').annotate(
                total=Count('id')
            ).order_by('año')
            
            context.update({
                'stats_fraccion': stats_fraccion,
                'stats_año': stats_año,
                'tipo_usuario': tipo_usuario,
            })
        
        return context