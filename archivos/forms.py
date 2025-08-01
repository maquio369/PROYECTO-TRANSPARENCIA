from django import forms
from django.core.exceptions import ValidationError
from django import forms
from django.core.exceptions import ValidationError
from .models import Archivo, Fraccion, PerfilUsuario


class MultipleFileInput(forms.ClearableFileInput):
    """Widget personalizado para múltiples archivos"""
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    """Campo personalizado para múltiples archivos"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

TIPO_PERIODO_CHOICES = [
    ('anual', 'Anual'),
    ('trimestral', 'Trimestral'),
    ('bimestral', 'Bimestral'),
]



class ArchivoForm(forms.ModelForm):
    """Formulario para cargar archivos"""
    
    class Meta:
        model = Archivo
        fields = ['fraccion', 'tipo_periodo', 'año', 'periodo_especifico']

        # Campo personalizado para múltiples archivos
        archivo = MultipleFileField(
            widget=MultipleFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'multiple': True,
                'required': True
            }),
            label='Archivo'
        )
        widgets = {
    'fraccion': forms.Select(attrs={
        'class': 'form-control',
        'required': True
    }),
    'tipo_periodo': forms.Select(attrs={
        'class': 'form-control',
        'required': True
    }),
    'año': forms.NumberInput(attrs={
        'class': 'form-control',
        'min': 2020,
        'max': 2030,
        'required': True,
        'value': 2024
    }),
    'periodo_especifico': forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: T1, T2, B1, etc.',
        'required': True,
        'maxlength': 20
    })
    # ← Ya no incluir 'archivo' aquí
}
        
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        print(f"=== DEBUG FORMS INIT ===")
        print(f"Usuario recibido: {user}")
        
        # Filtrar fracciones según el tipo de usuario
        if user:
            try:
                perfil = user.perfilusuario
                print(f"Perfil encontrado: {perfil.tipo_usuario}")
                
                fracciones_disponibles = Fraccion.objects.filter(
                    tipo_usuario_asignado=perfil.tipo_usuario,
                    activa=True
                )
                print(f"Fracciones disponibles: {fracciones_disponibles.count()}")
                
                self.fields['fraccion'].queryset = fracciones_disponibles
                
                # Si no hay fracciones, mostrar mensaje útil
                if not fracciones_disponibles.exists():
                    self.fields['fraccion'].widget.attrs['disabled'] = True
                    self.fields['fraccion'].help_text = f"No hay fracciones asignadas para el tipo de usuario: {perfil.get_tipo_usuario_display()}"
                
            except PerfilUsuario.DoesNotExist:
                print("❌ Usuario sin perfil")
                self.fields['fraccion'].queryset = Fraccion.objects.none()
                self.fields['fraccion'].widget.attrs['disabled'] = True
                self.fields['fraccion'].help_text = "Tu usuario no tiene un perfil asignado. Contacta al administrador."
            except Exception as e:
                print(f"❌ Error inesperado en forms.__init__: {e}")
                self.fields['fraccion'].queryset = Fraccion.objects.none()
        else:
            print("❌ No se recibió usuario")
            self.fields['fraccion'].queryset = Fraccion.objects.none()
        
        # Personalizar labels y help_text
        self.fields['fraccion'].label = 'Fracción'
        self.fields['tipo_periodo'].label = 'Tipo de Periodo'
        self.fields['año'].label = 'Año'
        self.fields['periodo_especifico'].label = 'Periodo Específico'
        #self.fields['archivo'].label = 'Archivo'

        
        # Agregar help_text útil
        self.fields['año'].help_text = 'Año del periodo que cubre el archivo'
        #self.fields['archivo'].help_text = 'Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX. Tamaño máximo: 100 MB por archivo. Puedes seleccionar múltiples archivos.'
        
        print("=== FIN DEBUG FORMS INIT ===")

    def clean_archivo(self): 
        archivos = self.cleaned_data.get('archivo')
    
        print(f"=== DEBUG CLEAN_ARCHIVO MÚLTIPLE ===")
        print(f"Archivos recibidos: {archivos}")
        print(f"Tipo: {type(archivos)}")
    
    # Si no hay archivos
        if not archivos:
            print("❌ No se recibieron archivos")
            raise ValidationError('Debe seleccionar al menos un archivo.')
    
    # Si es una lista (múltiples archivos)
        if isinstance(archivos, list):
            print(f"📁 Lista de archivos: {len(archivos)} archivos")
            validated_files = []
            
            for i, archivo in enumerate(archivos):
                print(f"Validando archivo {i+1}: {archivo.name}")
                validated_files.append(self._validate_single_file(archivo))
        
            return validated_files
    
        else:
         print(f"📄 Archivo único: {archivos.name}")
        return [self._validate_single_file(archivos)]

def _validate_single_file(self, archivo):
    """Validar un archivo individual"""
    if not archivo:
        raise ValidationError('Archivo vacío.')
    
    print(f"Validando: {archivo.name}, Tamaño: {archivo.size} bytes")
    
    # Validar que el archivo tenga contenido
    if archivo.size == 0:
        raise ValidationError(f'El archivo "{archivo.name}" está vacío.')
    
    # Validar tamaño (100 MB)
    max_size = 104857600  # 100 MB en bytes
    if archivo.size > max_size:
        raise ValidationError(
            f'El archivo "{archivo.name}" no puede superar los 100 MB. '
            f'Tamaño actual: {archivo.size / (1024*1024):.2f} MB'
        )
    
    # Validar extensión
    extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
    nombre_archivo = archivo.name.lower()
    
    extension_valida = any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas)
    
    if not extension_valida:
        raise ValidationError(
            f'El archivo "{archivo.name}" tiene un formato no permitido. '
            f'Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX'
        )
    
    print(f"✅ Archivo válido: {archivo.name}")
    return archivo   
    
    
    
    def clean_año(self):
        """Validación del año"""
        año = self.cleaned_data.get('año')
        
        if año:
            if año < 2020 or año > 2030:
                raise ValidationError('El año debe estar entre 2020 y 2030.')
        
        return año
    
    def clean_periodo_especifico(self):
        """Validación del periodo específico"""
        periodo_especifico = self.cleaned_data.get('periodo_especifico')
        
        if periodo_especifico:
            # Limpiar y normalizar
            periodo_especifico = periodo_especifico.strip().upper()
            
            # Validar longitud
            if len(periodo_especifico) > 20:
                raise ValidationError('El periodo específico no puede tener más de 20 caracteres.')
        
        return periodo_especifico
    
    def clean(self):
        """Validación global del formulario"""
        cleaned_data = super().clean()
        
        print(f"=== DEBUG CLEAN GENERAL ===")
        print(f"Datos limpios recibidos: {cleaned_data}")
        
        tipo_periodo = cleaned_data.get('tipo_periodo')
        periodo_especifico = cleaned_data.get('periodo_especifico')
        fraccion = cleaned_data.get('fraccion')
        año = cleaned_data.get('año')
        archivo = cleaned_data.get('archivo')
        
        # Validar que todos los campos requeridos estén presentes
        campos_requeridos = {
            'fraccion': fraccion,
            'tipo_periodo': tipo_periodo,
            'año': año,  
            'periodo_especifico': periodo_especifico,
            'archivo': archivo
        }
        
        for campo, valor in campos_requeridos.items():
            if not valor:
                print(f"❌ Campo requerido faltante: {campo}")
                self.add_error(campo, f'Este campo es requerido.')
        
        # Validar formato del periodo específico según el tipo
        if tipo_periodo and periodo_especifico:
            periodo_especifico = periodo_especifico.upper()
            
            print(f"Validando periodo: {tipo_periodo} - {periodo_especifico}")
            
            periodo_valido = False
            
            if tipo_periodo == 'trimestral':
                if periodo_especifico in ['T1', 'T2', 'T3', 'T4']:
                    periodo_valido = True
                else:
                    self.add_error('periodo_especifico', 
                                 'Para periodo trimestral use: T1, T2, T3, T4')
            
            elif tipo_periodo == 'bimestral':
                if periodo_especifico in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']:
                    periodo_valido = True
                else:
                    self.add_error('periodo_especifico', 
                                 'Para periodo bimestral use: B1, B2, B3, B4, B5, B6')
            
            elif tipo_periodo == 'anual':
                if periodo_especifico in ['A', 'ANUAL']:
                    periodo_valido = True
                else:
                    self.add_error('periodo_especifico', 
                                 'Para periodo anual use: A o ANUAL')
            
            if periodo_valido:
                cleaned_data['periodo_especifico'] = periodo_especifico
                print(f"✅ Periodo válido: {periodo_especifico}")
            else:
                print(f"❌ Periodo inválido: {tipo_periodo} - {periodo_especifico}")
        
        # Validar que no exista un archivo vigente para la misma combinación
        if fraccion and año and periodo_especifico and not self.errors:
            archivos_existentes = Archivo.objects.filter(
                fraccion=fraccion,
                año=año,
                periodo_especifico=periodo_especifico,
                vigente=True
            )
            
            # Si estamos editando, excluir el archivo actual
            if self.instance and self.instance.pk:
                archivos_existentes = archivos_existentes.exclude(pk=self.instance.pk)
            
            if archivos_existentes.exists():
                archivo_existente = archivos_existentes.first()
                print(f"⚠️ Ya existe archivo vigente: {archivo_existente}")
                # Solo advertencia, no error, ya que se puede crear nueva versión
                # self.add_error(None, f'Ya existe un archivo vigente para {fraccion.numero}-{año}-{periodo_especifico}. Se creará una nueva versión.')
        
        print(f"Datos finales: {cleaned_data}")
        print("=== FIN DEBUG CLEAN GENERAL ===")
        
        return cleaned_data
    # ✅ AGREGAR ESTA CLASE AL FINAL DE archivos/forms.py
class ArchivoZipForm(forms.Form):
    """Formulario para cargar múltiples archivos mediante ZIP"""
    
    fraccion = forms.ModelChoiceField(
        queryset=Fraccion.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Fracción'
    )
    
    tipo_periodo = forms.ChoiceField(
        choices=TIPO_PERIODO_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Tipo de Periodo'
    )
    
    año = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 2020,
            'max': 2030,
            'required': True,
            'value': 2024
        }),
        label='Año'
    )
    
    periodo_especifico = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: T1, T2, B1, etc.',
            'required': True,
            'maxlength': 20
        }),
        label='Periodo Específico'
    )
    
    archivo_zip = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.zip,.rar,.7z',
            'required': True
        }),
        label='Archivo ZIP'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        print(f"=== DEBUG ZIP FORM INIT ===")
        print(f"Usuario recibido: {user}")
        
        # Filtrar fracciones según el tipo de usuario
        if user:
            try:
                perfil = user.perfilusuario
                print(f"Perfil encontrado: {perfil.tipo_usuario}")
                
                fracciones_disponibles = Fraccion.objects.filter(
                    tipo_usuario_asignado=perfil.tipo_usuario,
                    activa=True
                )
                print(f"Fracciones disponibles para ZIP: {fracciones_disponibles.count()}")
                
                self.fields['fraccion'].queryset = fracciones_disponibles
                
                if not fracciones_disponibles.exists():
                    self.fields['fraccion'].widget.attrs['disabled'] = True
                    self.fields['fraccion'].help_text = f"No hay fracciones asignadas para: {perfil.get_tipo_usuario_display()}"
                
            except PerfilUsuario.DoesNotExist:
                print("❌ Usuario sin perfil")
                self.fields['fraccion'].queryset = Fraccion.objects.none()
                self.fields['fraccion'].widget.attrs['disabled'] = True
                self.fields['fraccion'].help_text = "Tu usuario no tiene un perfil asignado."
        else:
            self.fields['fraccion'].queryset = Fraccion.objects.none()
        
        # Help text útil
        self.fields['año'].help_text = 'Año del periodo que cubren TODOS los archivos'
        self.fields['archivo_zip'].help_text = 'ZIP con múltiples archivos. Máximo: 500 MB'
        
        print("=== FIN DEBUG ZIP FORM INIT ===")
    
    def clean_archivo_zip(self):
        """Validación del archivo ZIP"""
        archivo_zip = self.cleaned_data.get('archivo_zip')
        
        if not archivo_zip:
            raise ValidationError('Debe seleccionar un archivo ZIP.')
        
        # Validar que no esté vacío
        if archivo_zip.size == 0:
            raise ValidationError('El archivo ZIP está vacío.')
        
        # Validar tamaño (500 MB)
        max_size = 524288000  # 500 MB
        if archivo_zip.size > max_size:
            raise ValidationError(
                f'El archivo ZIP no puede superar los 500 MB. '
                f'Tu archivo: {archivo_zip.size / (1024*1024):.2f} MB'
            )
        
        # Validar extensión
        extensiones_zip = ['.zip', '.rar', '.7z']
        nombre_archivo = archivo_zip.name.lower()
        
        extension_valida = any(nombre_archivo.endswith(ext) for ext in extensiones_zip)
        
        if not extension_valida:
            raise ValidationError(
                f'Solo se permiten archivos ZIP, RAR, 7Z. '
                f'Tu archivo: {archivo_zip.name}'
            )
        
        return archivo_zip
    
    def clean_periodo_especifico(self):
        """Validación del periodo específico"""
        periodo_especifico = self.cleaned_data.get('periodo_especifico')
        
        if periodo_especifico:
            periodo_especifico = periodo_especifico.strip().upper()
            
            if len(periodo_especifico) > 20:
                raise ValidationError('El periodo específico no puede tener más de 20 caracteres.')
        
        return periodo_especifico
    
    def clean(self):
        """Validación global del formulario"""
        cleaned_data = super().clean()
        
        tipo_periodo = cleaned_data.get('tipo_periodo')
        periodo_especifico = cleaned_data.get('periodo_especifico')
        
        # Validar formato del periodo específico según el tipo
        if tipo_periodo and periodo_especifico:
            periodo_especifico = periodo_especifico.upper()
            
            if tipo_periodo == 'trimestral':
                if periodo_especifico not in ['T1', 'T2', 'T3', 'T4']:
                    self.add_error('periodo_especifico', 
                                 'Para periodo trimestral use: T1, T2, T3, T4')
            
            elif tipo_periodo == 'bimestral':
                if periodo_especifico not in ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']:
                    self.add_error('periodo_especifico', 
                                 'Para periodo bimestral use: B1, B2, B3, B4, B5, B6')
            
            elif tipo_periodo == 'anual':
                if periodo_especifico not in ['A', 'ANUAL']:
                    self.add_error('periodo_especifico', 
                                 'Para periodo anual use: A o ANUAL')
            
            if periodo_especifico in ['T1', 'T2', 'T3', 'T4', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'A', 'ANUAL']:
                cleaned_data['periodo_especifico'] = periodo_especifico
        
        return cleaned_data

    
        
    


        


        