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
from django.core.files.base import ContentFile
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from pathlib import Path
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db import transaction
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
    """Vista para listar archivos con exportación a Excel"""
    model = Archivo
    template_name = 'archivos/listado_archivos.html'
    context_object_name = 'archivos'
    paginate_by = 20
    
    def get(self, request, *args, **kwargs):
        # ✅ VERIFICAR SI ES UNA SOLICITUD DE EXPORTACIÓN
        if request.GET.get('export') == 'excel':
            return self.exportar_excel(request)
        
        return super().get(request, *args, **kwargs)
    
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
            fraccion__tipo_usuario_asignado=tipo_usuario
        ).select_related('fraccion', 'usuario').order_by('-created_at')
        
        # ✅ FILTRO POR ESTADO (VIGENTE/HISTÓRICO/TODOS)
        estado = self.request.GET.get('estado', 'vigente')  # Por defecto solo vigentes
        
        if estado == 'vigente':
            queryset = queryset.filter(vigente=True)
        elif estado == 'historico':
            queryset = queryset.filter(vigente=False)
        # Si estado == 'todos', no filtramos por vigente
        
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
            'estado_seleccionado': self.request.GET.get('estado', 'vigente'),
            'busqueda_actual': self.request.GET.get('busqueda', ''),
        })
        
        return context
    
    def exportar_excel(self, request):
        """
        ✅ FUNCIÓN OPTIMIZADA PARA EXPORTAR A EXCEL - AGRUPADA POR FRACCIÓN
        """
        print("📊 Iniciando exportación a Excel agrupada...")
        
        # Obtener queryset con los mismos filtros pero ORDENADO POR FRACCIÓN
        queryset = self.get_queryset().order_by(
            'fraccion__numero',  # ✅ PRIMERO por número de fracción
            'año',               # Luego por año  
            'periodo_especifico', # Luego por periodo
            '-created_at'        # Finalmente por fecha (más recientes primero)
        )
        
        # Obtener información del usuario
        try:
            perfil = request.user.perfilusuario
            tipo_usuario_display = perfil.get_tipo_usuario_display()
        except:
            tipo_usuario_display = "Usuario"
        
        # Crear workbook y worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Archivos Artículo 65"
        
        # ✅ CONFIGURAR ESTILOS
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        
        # Estilo para separadores de fracción
        fraccion_font = Font(bold=True, color="FFFFFF", size=11)
        fraccion_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # ✅ ENCABEZADOS OPTIMIZADOS (SIN: Estado, Versión, Tamaño, Usuario, Periodo)
        headers = [
            'Número',           # ✅ PRIMERA COLUMNA
            'Fracción',         # ✅ SEGUNDA COLUMNA  
            'Año',
            'Tipo Periodo',
            'Archivo',
            'Fecha Carga',
            'Enlace Público'
        ]
        
        # Escribir encabezados
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = border
        
        # ✅ ESCRIBIR DATOS AGRUPADOS POR FRACCIÓN
        row_num = 2
        current_fraccion = None
        
        for archivo in queryset:
            # ✅ AGREGAR SEPARADOR CUANDO CAMBIA LA FRACCIÓN
            if current_fraccion != archivo.fraccion.numero:
                if current_fraccion is not None:  # No agregar separador antes de la primera fracción
                    # Fila vacía como separador
                    row_num += 1
                
                # Fila de título de fracción
                ws.merge_cells(f'A{row_num}:G{row_num}')
                title_cell = ws.cell(row=row_num, column=1, 
                                   value=f"FRACCIÓN {archivo.fraccion.numero} - {archivo.fraccion.nombre}")
                title_cell.font = fraccion_font
                title_cell.fill = fraccion_fill
                title_cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Aplicar borde a todas las celdas de la fila fusionada
                for col in range(1, len(headers) + 1):
                    ws.cell(row=row_num, column=col).border = border
                
                row_num += 1
                current_fraccion = archivo.fraccion.numero
            
            # Generar enlace público
            enlace_publico = f"{request.scheme}://{request.get_host()}/publico/archivo/{archivo.id}/"
            
            # ✅ DATOS OPTIMIZADOS DE LA FILA (SIN campos eliminados)
            row_data = [
                archivo.fraccion.numero,                                    # Número (PRIMERA COLUMNA)
                archivo.fraccion.nombre,                                    # Fracción (SEGUNDA COLUMNA)
                archivo.año,                                               # Año
                archivo.get_tipo_periodo_display(),                        # Tipo Periodo
                archivo.nombre_original,                                   # Archivo
                archivo.created_at.strftime("%d/%m/%Y %H:%M"),            # Fecha Carga
                enlace_publico                                             # Enlace Público
            ]
            
            # Escribir fila
            for col, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col, value=value)
                cell.border = border
                
                # ✅ COLOREAR FILAS ALTERNADAS POR FRACCIÓN
                if archivo.vigente:
                    # Verde claro para archivos vigentes
                    cell.fill = PatternFill(start_color="E8F5E8", end_color="E8F5E8", fill_type="solid")
                else:
                    # Gris claro para archivos históricos
                    cell.fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
            
            row_num += 1
        
        # ✅ AJUSTAR ANCHO DE COLUMNAS OPTIMIZADO
        column_widths = [
            12,  # Número
            45,  # Fracción (más ancho para nombres largos)
            10,  # Año
            15,  # Tipo Periodo
            40,  # Archivo
            18,  # Fecha Carga
            55   # Enlace Público (más ancho)
        ]
        
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # ✅ AGREGAR INFORMACIÓN DEL REPORTE (más abajo para no interferir)
        info_row = row_num + 3
        
        # Título de información
        ws.merge_cells(f'A{info_row}:C{info_row}')
        info_title = ws.cell(row=info_row, column=1, value="INFORMACIÓN DEL REPORTE")
        info_title.font = Font(bold=True, size=11)
        info_title.fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        info_row += 1
        
        # Información del reporte
        info_data = [
            ("Reporte generado por:", f"{request.user.get_full_name() or request.user.username}"),
            ("Fecha de generación:", timezone.now().strftime("%d/%m/%Y %H:%M")),
            ("Tipo de usuario:", tipo_usuario_display),
            ("Total de archivos:", queryset.count()),
        ]
        
        # ✅ AGREGAR FILTROS APLICADOS
        filtros_info = []
        if request.GET.get('fraccion'):
            try:
                fraccion = Fraccion.objects.get(id=request.GET.get('fraccion'))
                filtros_info.append(f"Fracción: {fraccion.numero} - {fraccion.nombre}")
            except:
                pass
        
        if request.GET.get('año'):
            filtros_info.append(f"Año: {request.GET.get('año')}")
        
        if request.GET.get('estado'):
            estado = request.GET.get('estado')
            filtros_info.append(f"Estado: {estado.capitalize()}")
        
        if request.GET.get('busqueda'):
            filtros_info.append(f"Búsqueda: {request.GET.get('busqueda')}")
        
        if filtros_info:
            info_data.append(("Filtros aplicados:", " | ".join(filtros_info)))
        
        # Escribir información
        for label, value in info_data:
            ws.cell(row=info_row, column=1, value=label).font = Font(bold=True)
            ws.cell(row=info_row, column=2, value=str(value))
            info_row += 1
        
        # ✅ AGREGAR ESTADÍSTICAS DE FRACCIONES
        if queryset.count() > 0:
            # Contar archivos por fracción
            from django.db.models import Count
            stats_fraccion = queryset.values('fraccion__numero', 'fraccion__nombre').annotate(
                total=Count('id')
            ).order_by('fraccion__numero')
            
            if len(stats_fraccion) > 1:  # Solo mostrar si hay múltiples fracciones
                info_row += 1
                ws.cell(row=info_row, column=1, value="ARCHIVOS POR FRACCIÓN:").font = Font(bold=True)
                info_row += 1
                
                for stat in stats_fraccion:
                    ws.cell(row=info_row, column=1, value=f"Fracción {stat['fraccion__numero']}:")
                    ws.cell(row=info_row, column=2, value=f"{stat['total']} archivo(s)")
                    info_row += 1
        
        # ✅ PREPARAR RESPUESTA HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Generar nombre de archivo dinámico
        fecha_actual = timezone.now().strftime("%Y%m%d_%H%M")
        filtro_str = ""
        
        if request.GET.get('año'):
            filtro_str += f"_{request.GET.get('año')}"
        if request.GET.get('fraccion'):
            try:
                fraccion = Fraccion.objects.get(id=request.GET.get('fraccion'))
                filtro_str += f"_Frac{fraccion.numero}"
            except:
                pass
        elif queryset.count() > 0:
            # Si es de todas las fracciones, indicarlo
            filtro_str += "_TodasFracciones"
        
        filename = f"Archivos_Articulo65{filtro_str}_{fecha_actual}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Guardar workbook en response
        wb.save(response)
        
        print(f"✅ Excel agrupado generado: {filename}")
        print(f"📊 Registros exportados: {queryset.count()}")
        print(f"📁 Fracciones incluidas: {len(set(a.fraccion.numero for a in queryset))}")
        
        return response
    
    




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


        # ✅ AGREGAR ESTAS VISTAS AL FINAL DE TU ARCHIVO archivos/views.py

# ✅ REEMPLAZAR TODO EL FINAL DE TU views.py DESDE DONDE APARECE "class VerArchivoPublicoView"

class VerArchivoPublicoView(View):
    """Vista PÚBLICA para visualizar archivos sin autenticación"""
    
    def get(self, request, archivo_id):
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        print(f"📖 Acceso público a archivo: {archivo.nombre_original}")
        print(f"👤 IP: {self.get_client_ip(request)}")
        print(f"🌐 User Agent: {request.META.get('HTTP_USER_AGENT', 'No disponible')}")
        
        # Registrar acceso público (usuario anónimo)
        try:
            HistorialAcceso.objects.create(
                archivo=archivo,
                usuario=None,  # Usuario anónimo
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            print(f"⚠️ Error registrando acceso público: {e}")
        
        # Servir archivo para visualización
        try:
            if archivo.archivo and os.path.exists(archivo.archivo.path):
                content_type, _ = mimetypes.guess_type(archivo.archivo.path)
                
                print(f"✅ Sirviendo archivo: {archivo.archivo.path}")
                print(f"📄 Content-Type: {content_type}")
                
                response = FileResponse(
                    open(archivo.archivo.path, 'rb'),
                    content_type=content_type,
                    filename=archivo.nombre_original
                )
                
                # Headers adicionales para mejor experiencia
                response['Content-Disposition'] = f'inline; filename="{archivo.nombre_original}"'
                response['X-Frame-Options'] = 'SAMEORIGIN'  # Permitir embed en iframes del mismo origen
                
                return response
            else:
                print(f"❌ Archivo físico no encontrado: {archivo.archivo.path if archivo.archivo else 'Sin archivo'}")
                raise Http404("Archivo no encontrado")
                
        except Exception as e:
            print(f"❌ Error sirviendo archivo público: {e}")
            raise Http404("Error al acceder al archivo")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class DescargarArchivoPublicoView(View):
    """Vista PÚBLICA para descargar archivos sin autenticación"""
    
    def get(self, request, archivo_id):
        archivo = get_object_or_404(Archivo, id=archivo_id)
        
        print(f"⬇️ Descarga pública de archivo: {archivo.nombre_original}")
        print(f"👤 IP: {self.get_client_ip(request)}")
        
        # Registrar acceso público
        try:
            HistorialAcceso.objects.create(
                archivo=archivo,
                usuario=None,  # Usuario anónimo
                ip_address=self.get_client_ip(request)
            )
        except Exception as e:
            print(f"⚠️ Error registrando descarga pública: {e}")
        
        # Servir archivo para descarga
        try:
            if archivo.archivo and os.path.exists(archivo.archivo.path):
                print(f"✅ Descargando archivo: {archivo.archivo.path}")
                
                response = FileResponse(
                    open(archivo.archivo.path, 'rb'),
                    as_attachment=True,
                    filename=archivo.nombre_original
                )
                
                # Headers adicionales
                response['Content-Length'] = archivo.tamaño
                response['X-Sendfile'] = archivo.archivo.path  # Para servidores optimizados
                
                return response
            else:
                print(f"❌ Archivo físico no encontrado para descarga: {archivo.archivo.path if archivo.archivo else 'Sin archivo'}")
                raise Http404("Archivo no encontrado")
                
        except Exception as e:
            print(f"❌ Error en descarga pública: {e}")
            raise Http404("Error al descargar el archivo")
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

