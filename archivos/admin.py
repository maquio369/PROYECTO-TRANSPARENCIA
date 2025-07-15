from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario, Fraccion, Archivo, HistorialAcceso

# Configuración del admin para PerfilUsuario
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Fraccion)
class FraccionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nombre', 'tipo_usuario_asignado', 'activa', 'created_at']
    list_filter = ['tipo_usuario_asignado', 'activa']
    search_fields = ['numero', 'nombre']
    ordering = ['numero']

@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ['fraccion', 'año', 'periodo_especifico', 'usuario', 'vigente', 'version', 'created_at']
    list_filter = ['fraccion', 'año', 'tipo_periodo', 'vigente', 'created_at']
    search_fields = ['fraccion__numero', 'fraccion__nombre', 'nombre_original']
    ordering = ['-created_at']
    readonly_fields = ['tamaño', 'nombre_original', 'version', 'created_at', 'updated_at']

@admin.register(HistorialAcceso)
class HistorialAccesoAdmin(admin.ModelAdmin):
    list_display = ['archivo', 'usuario', 'fecha_acceso', 'ip_address']
    list_filter = ['fecha_acceso']
    search_fields = ['archivo__fraccion__numero', 'usuario__username']
    ordering = ['-fecha_acceso']
    readonly_fields = ['fecha_acceso']