from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from archivos.models import Archivo, Fraccion
import random

class Command(BaseCommand):
    help = 'Crea archivos de demostración para el sistema'

    def handle(self, *args, **options):
        # Obtener usuarios
        try:
            usuario_transparencia = User.objects.get(username='transparencia')
            usuario_financieros = User.objects.get(username='financieros')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Primero ejecuta: python manage.py crear_usuarios_demo')
            )
            return

        # Obtener fracciones
        fracciones_transparencia = Fraccion.objects.filter(tipo_usuario_asignado='transparencia')
        fracciones_financieros = Fraccion.objects.filter(tipo_usuario_asignado='recursos_financieros')

        # Datos de ejemplo para archivos
        archivos_demo = [
            # Transparencia
            {
                'fraccion': fracciones_transparencia.first(),
                'usuario': usuario_transparencia,
                'año': 2024,
                'periodo_especifico': 'T1',
                'tipo_periodo': 'trimestral',
                'nombre': 'Estructura_Organica_T1_2024.pdf'
            },
            {
                'fraccion': fracciones_transparencia.first(),
                'usuario': usuario_transparencia,
                'año': 2024,
                'periodo_especifico': 'T2',
                'tipo_periodo': 'trimestral',
                'nombre': 'Estructura_Organica_T2_2024.pdf'
            },
            # Recursos Financieros
            {
                'fraccion': fracciones_financieros.first(),
                'usuario': usuario_financieros,
                'año': 2024,
                'periodo_especifico': 'T1',
                'tipo_periodo': 'trimestral',
                'nombre': 'Remuneraciones_T1_2024.xlsx'
            },
            {
                'fraccion': fracciones_financieros.first(),
                'usuario': usuario_financieros,
                'año': 2024,
                'periodo_especifico': 'T2',
                'tipo_periodo': 'trimestral',
                'nombre': 'Remuneraciones_T2_2024.xlsx'
            }
        ]

        # Crear archivos demo
        for datos in archivos_demo:
            if datos['fraccion']:  # Solo si existe la fracción
                # Crear contenido ficticio para el archivo
                contenido = f"Archivo de demostración: {datos['nombre']}\nGenerado automáticamente para pruebas del sistema.\nFecha: {timezone.now()}"
                archivo_content = ContentFile(contenido.encode('utf-8'))
                archivo_content.name = datos['nombre']

                # Crear el archivo
                archivo, created = Archivo.objects.get_or_create(
                    fraccion=datos['fraccion'],
                    año=datos['año'],
                    periodo_especifico=datos['periodo_especifico'],
                    defaults={
                        'usuario': datos['usuario'],
                        'tipo_periodo': datos['tipo_periodo'],
                        'archivo': archivo_content,
                        'nombre_original': datos['nombre'],
                        'tamaño': len(contenido.encode('utf-8')),
                        'vigente': True,
                        'version': 1
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Archivo creado: {datos["nombre"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Archivo ya existe: {datos["nombre"]}')
                    )

        self.stdout.write(
            self.style.SUCCESS('\n🎉 ARCHIVOS DEMO CREADOS EXITOSAMENTE')
        )