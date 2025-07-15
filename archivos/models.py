from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
import os

# Choices para tipos de usuario
TIPO_USUARIO_CHOICES = [
    ('transparencia', 'Unidad de Transparencia'),
    ('recursos_financieros', 'Unidad de Recursos Financieros'),
]

# Choices para tipos de periodo
TIPO_PERIODO_CHOICES = [
    ('anual', 'Anual'),
    ('trimestral', 'Trimestral'),
    ('bimestral', 'Bimestral'),
]

class PerfilUsuario(models.Model):
    """Extensión del modelo User para agregar tipo de usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        verbose_name='Tipo de Usuario'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_usuario_display()}"

class Fraccion(models.Model):
    """Fracciones del Artículo 65"""
    numero = models.CharField(max_length=10, unique=True, verbose_name='Número')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    tipo_usuario_asignado = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        verbose_name='Tipo de Usuario Asignado'
    )
    activa = models.BooleanField(default=True, verbose_name='Activa')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Fracción'
        verbose_name_plural = 'Fracciones'
        ordering = ['numero']
    
    def __str__(self):
        return f"Fracción {self.numero} - {self.nombre}"

def archivo_upload_path(instance, filename):
    """Función para generar la ruta de subida de archivos"""
    # Organizar por fracción y año
    return f"archivos/{instance.fraccion.numero}/{instance.año}/{filename}"

class Archivo(models.Model):
    """Modelo principal para archivos del Artículo 65"""
    fraccion = models.ForeignKey(Fraccion, on_delete=models.CASCADE, verbose_name='Fracción')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    
    # Información del periodo
    tipo_periodo = models.CharField(
        max_length=15,
        choices=TIPO_PERIODO_CHOICES,
        verbose_name='Tipo de Periodo'
    )
    año = models.IntegerField(verbose_name='Año')
    periodo_especifico = models.CharField(
        max_length=20,
        verbose_name='Periodo Específico',
        help_text='Ej: T1, T2, B1, etc.'
    )
    
    # Archivo
    archivo = models.FileField(
        upload_to=archivo_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])],
        verbose_name='Archivo'
    )
    nombre_original = models.CharField(max_length=255, verbose_name='Nombre Original')
    tamaño = models.BigIntegerField(verbose_name='Tamaño (bytes)')
    
    # Control de versiones
    vigente = models.BooleanField(default=True, verbose_name='Vigente')
    version = models.IntegerField(default=1, verbose_name='Versión')
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Carga')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Modificación')
    
    class Meta:
        verbose_name = 'Archivo'
        verbose_name_plural = 'Archivos'
        ordering = ['-created_at']
        # Índices para optimizar consultas
        indexes = [
            models.Index(fields=['fraccion', 'año', 'periodo_especifico']),
            models.Index(fields=['vigente']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.fraccion.numero} - {self.año}-{self.periodo_especifico} - v{self.version}"
    
    def save(self, *args, **kwargs):
        # Establecer nombre original y tamaño
        if self.archivo:
            self.nombre_original = self.archivo.name
            self.tamaño = self.archivo.size
        
        # Si es un nuevo archivo vigente, marcar otros como no vigentes
        if self.vigente:
            Archivo.objects.filter(
                fraccion=self.fraccion,
                año=self.año,
                periodo_especifico=self.periodo_especifico
            ).update(vigente=False)
        
        super().save(*args, **kwargs)
    
    def get_tamaño_legible(self):
        """Convierte el tamaño en bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.tamaño < 1024.0:
                return f"{self.tamaño:.1f} {unit}"
            self.tamaño /= 1024.0
        return f"{self.tamaño:.1f} TB"

class HistorialAcceso(models.Model):
    """Registro de accesos a archivos"""
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE, verbose_name='Archivo')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    fecha_acceso = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Acceso')
    ip_address = models.GenericIPAddressField(verbose_name='IP Address')
    
    class Meta:
        verbose_name = 'Historial de Acceso'
        verbose_name_plural = 'Historial de Accesos'
        ordering = ['-fecha_acceso']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.archivo} - {self.fecha_acceso}"