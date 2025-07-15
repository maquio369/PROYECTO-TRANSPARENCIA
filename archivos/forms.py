from django import forms
from django.core.exceptions import ValidationError
from .models import Archivo, Fraccion

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
                'required': True
            }),
            'periodo_especifico': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: T1, T2, B1, etc.',
                'required': True
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
        
        # Filtrar fracciones según el tipo de usuario
        if user:
            try:
                perfil = user.perfilusuario
                self.fields['fraccion'].queryset = Fraccion.objects.filter(
                    tipo_usuario_asignado=perfil.tipo_usuario,
                    activa=True
                )
            except:
                self.fields['fraccion'].queryset = Fraccion.objects.none()
        
        # Personalizar labels
        self.fields['fraccion'].label = 'Fracción'
        self.fields['tipo_periodo'].label = 'Tipo de Periodo'
        self.fields['año'].label = 'Año'
        self.fields['periodo_especifico'].label = 'Periodo Específico'
        self.fields['archivo'].label = 'Archivo'
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        
        if archivo:
            # Validar tamaño (100 MB)
            if archivo.size > 104857600:
                raise ValidationError('El archivo no puede superar los 100 MB.')
            
            # Validar extensión
            extensiones_permitidas = ['.pdf', '.doc', '.docx', '.xls', '.xlsx']
            nombre_archivo = archivo.name.lower()
            
            if not any(nombre_archivo.endswith(ext) for ext in extensiones_permitidas):
                raise ValidationError(
                    'Solo se permiten archivos PDF, DOC, DOCX, XLS, XLSX.'
                )
        
        return archivo
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_periodo = cleaned_data.get('tipo_periodo')
        periodo_especifico = cleaned_data.get('periodo_especifico')
        
        # Validar formato del periodo específico
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
            
            cleaned_data['periodo_especifico'] = periodo_especifico
        
        return cleaned_data