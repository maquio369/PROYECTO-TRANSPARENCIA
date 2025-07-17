from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import transaction
from django.core.exceptions import ValidationError
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
    # Limpiar el nombre del archivo para evitar problemas
    import re
    from django.utils.text import slugify
    
    # Extraer nombre y extensión
    name, ext = os.path.splitext(filename)
    # Limpiar nombre (mantener solo caracteres seguros)
    clean_name = slugify(name)
    if not clean_name:  # Si el nombre queda vacío después del slugify
        clean_name = "archivo"
    
    clean_filename = f"{clean_name}{ext.lower()}"
    
    # Organizar por fracción y año
    path = f"archivos/{instance.fraccion.numero}/{instance.año}/{clean_filename}"
    
    print(f"📁 Ruta generada para archivo: {path}")
    return path

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
        verbose_name='Archivo',
        max_length=500  # Aumentar para rutas largas
    )
    nombre_original = models.CharField(max_length=255, verbose_name='Nombre Original', blank=True)
    tamaño = models.BigIntegerField(verbose_name='Tamaño (bytes)', default=0)
    
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
        # Constraint para evitar duplicados
        constraints = [
            models.UniqueConstraint(
                fields=['fraccion', 'año', 'periodo_especifico', 'version'],
                name='unique_archivo_version'
            )
        ]
    
    def __str__(self):
        return f"{self.fraccion.numero} - {self.año}-{self.periodo_especifico} - v{self.version}"
    
    def clean(self):
        """Validaciones a nivel de modelo"""
        super().clean()
        
        # Validar que el año sea razonable
        if self.año and (self.año < 2020 or self.año > 2030):
            raise ValidationError({'año': 'El año debe estar entre 2020 y 2030'})
        
        # Validar archivo si existe
        if self.archivo:
            # Verificar tamaño
            if self.archivo.size > 104857600:  # 100 MB
                raise ValidationError({'archivo': 'El archivo no puede superar los 100 MB'})
            
            # Verificar que no esté vacío
            if self.archivo.size == 0:
                raise ValidationError({'archivo': 'El archivo no puede estar vacío'})
    
    def save(self, *args, **kwargs):
        """
        Método save mejorado que evita problemas de concurrencia
        y maneja correctamente el control de versiones
        """
        print(f"=== DEBUG MODEL SAVE ===")
        print(f"Guardando archivo: {self}")
        print(f"Tiene archivo: {bool(self.archivo)}")
        print(f"PK existente: {self.pk}")
        
        # Establecer nombre original y tamaño si hay archivo
        if self.archivo:
            if not self.nombre_original:
                self.nombre_original = self.archivo.name
            self.tamaño = self.archivo.size
            print(f"Nombre original: {self.nombre_original}")
            print(f"Tamaño: {self.tamaño} bytes")
        
        # Solo manejar versiones si es un archivo vigente y nuevo
        if self.vigente and not self.pk:
            print("📝 Archivo nuevo y vigente - manejando versiones")
            
            # Usar transacción para evitar race conditions
            with transaction.atomic():
                # Buscar archivos existentes para esta combinación
                archivos_existentes = Archivo.objects.filter(
                    fraccion=self.fraccion,
                    año=self.año,
                    periodo_especifico=self.periodo_especifico
                ).select_for_update()
                
                if archivos_existentes.exists():
                    print(f"📂 Encontrados {archivos_existentes.count()} archivos existentes")
                    
                    # Obtener la última versión
                    ultima_version = archivos_existentes.aggregate(
                        max_version=models.Max('version')
                    )['max_version'] or 0
                    
                    # Asignar nueva versión
                    if not self.version or self.version <= ultima_version:
                        self.version = ultima_version + 1
                    
                    print(f"📋 Nueva versión asignada: {self.version}")
                    
                    # Marcar archivos anteriores como no vigentes
                    archivos_existentes.update(vigente=False)
                    print("🔄 Archivos anteriores marcados como no vigentes")
                else:
                    print("📄 Primer archivo para esta combinación")
                    if not self.version:
                        self.version = 1
        
        try:
            # Validar antes de guardar
            self.full_clean()
            
            # Llamar al save original
            super().save(*args, **kwargs)
            
            print(f"✅ Archivo guardado exitosamente con ID: {self.pk}")
            
            # Verificar que el archivo físico existe
            if self.archivo:
                archivo_path = self.archivo.path
                if os.path.exists(archivo_path):
                    print(f"✅ Archivo físico confirmado en: {archivo_path}")
                else:
                    print(f"❌ Archivo físico NO encontrado en: {archivo_path}")
            
        except Exception as e:
            print(f"❌ Error al guardar archivo: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        print("=== FIN DEBUG MODEL SAVE ===")
    
    def get_tamaño_legible(self):
        """Convierte el tamaño en bytes a formato legible"""
        if not self.tamaño:
            return "0 B"
        
        tamaño = float(self.tamaño)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if tamaño < 1024.0:
                return f"{tamaño:.1f} {unit}"
            tamaño /= 1024.0
        return f"{tamaño:.1f} TB"
    
    def get_archivo_url(self):
        """Obtiene la URL del archivo de forma segura"""
        if self.archivo:
            try:
                return self.archivo.url
            except:
                return None
        return None
    
    def archivo_existe(self):
        """Verifica si el archivo físico existe"""
        if self.archivo:
            try:
                return os.path.exists(self.archivo.path)
            except:
                return False
        return False

# ✅ REEMPLAZAR LA CLASE HistorialAcceso EN archivos/models.py

class HistorialAcceso(models.Model):
    """Registro de accesos a archivos (públicos y privados)"""
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE, verbose_name='Archivo')
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Usuario',
        null=True,  # ✅ PERMITIR NULL para accesos anónimos
        blank=True
    )
    fecha_acceso = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Acceso')
    ip_address = models.GenericIPAddressField(verbose_name='IP Address', null=True, blank=True)
    es_acceso_publico = models.BooleanField(default=False, verbose_name='Acceso Público')  # ✅ NUEVO CAMPO
    user_agent = models.TextField(blank=True, verbose_name='User Agent')  # ✅ NUEVO CAMPO
    
    class Meta:
        verbose_name = 'Historial de Acceso'
        verbose_name_plural = 'Historial de Accesos'
        ordering = ['-fecha_acceso']
        indexes = [
            models.Index(fields=['fecha_acceso']),
            models.Index(fields=['es_acceso_publico']),
            models.Index(fields=['archivo', 'fecha_acceso']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else "Anónimo"
        tipo_acceso = "Público" if self.es_acceso_publico else "Privado"
        return f"{usuario_str} - {self.archivo} - {self.fecha_acceso} ({tipo_acceso})"
    
    def get_usuario_display(self):
        """Obtiene el display del usuario de forma segura"""
        if self.usuario:
            return self.usuario.get_full_name() or self.usuario.username
        return "Usuario Anónimo"