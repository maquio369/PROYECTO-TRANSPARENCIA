from django import forms
from django.core.exceptions import ValidationError
from .models import Archivo, Fraccion, PerfilUsuario

class ArchivoForm(forms.ModelForm):
    """Formulario para cargar archivos"""
    
    class Meta:
        model = Archivo
        fields = ['fraccion', 'tipo_periodo', 'año', 'periodo_especifico', 'archivo']
        
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
                'value': 2024  # Valor por defecto
            }),
            'periodo_especifico': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: T1, T2, B1, etc.',
                'required': True,
                'maxlength': 20
            }),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx',
                'required': True
            })
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
        self.fields['archivo'].label = 'Archivo'
        
        # Agregar help_text útil
        self.fields['año'].help_text = 'Año del periodo que cubre el archivo'
        self.fields['archivo'].help_text = 'Formatos permitidos: PDF, DOC, DOCX, XLS, XLSX. Tamaño máximo: 100 MB'
        
        print("=== FIN DEBUG FORMS INIT ===")
    
    def clean_archivo(self):
        """Validación del archivo subido"""
        archivo = self.cleaned_data.get('archivo')
        
        print(f"=== DEBUG CLEAN_ARCHIVO ===")
        print(f"Archivo recibido: {archivo}")
        
        if not archivo:
            print("❌ No se recibió archivo")
            raise ValidationError('Debe seleccionar un archivo.')
        
        print(f"Nombre: {archivo.name}")
        print(f"Tamaño: {archivo.size} bytes ({archivo.size / (1024*1024):.2f} MB)")
        print(f"Content type: {getattr(archivo, 'content_type', 'No disponible')}")
        
        # Validar que el archivo tenga contenido
        if archivo.size == 0:
            print("❌ Archivo vacío")
            raise ValidationError('El archivo está vacío.')
        
        # Validar tamaño (100 MB)
        max_size = 104857600  # 100 MB en bytes
        if archivo.size > max_size:
            print(f"❌ Archivo muy grande: {archivo.size} > {max_size}")
            raise ValidationError(f'El archivo no puede superar los 100 MB. Tu archivo: {archivo.size / (1024*1024):.2f} MB')
        
        # Validar extensión
        extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
        nombre_archivo = archivo.name.lower()
        
        print(f"Validando extensión de: {nombre_archivo}")
        
        extension_valida = False
        for ext in extensiones_permitidas:
            if nombre_archivo.endswith(ext):
                extension_valida = True
                print(f"✅ Extensión válida encontrada: {ext}")
                break
        
        if not extension_valida:
            print(f"❌ Extensión no válida. Extensiones permitidas: {extensiones_permitidas}")
            raise ValidationError(
                f'Solo se permiten archivos PDF, DOC, DOCX, XLS, XLSX. '
                f'Tu archivo: {archivo.name}'
            )
        
        print(f"✅ Archivo válido: {archivo.name}")
        print("=== FIN DEBUG CLEAN_ARCHIVO ===")
        
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