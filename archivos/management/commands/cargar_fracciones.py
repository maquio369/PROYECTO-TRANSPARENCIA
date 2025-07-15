from django.core.management.base import BaseCommand
from archivos.models import Fraccion

class Command(BaseCommand):
    help = 'Carga las fracciones oficiales del Artículo 65'

    def handle(self, *args, **options):
        # Mapeo de áreas a tipos de usuario
        area_mapping = {
            'Unidad de Transparencia': 'transparencia',
            'Recursos Financieros': 'recursos_financieros',
            'Área': 'transparencia'  # Por defecto
        }
        
        # Fracciones oficiales extraídas del Excel
        fracciones_oficiales = [
            ("I", "Marco normativo al Sujeto Obligado", "Unidad de Transparencia"),
            ("II", "Estructura orgánica", "Unidad de Transparencia"),
            ("III", "Las atribuciones, facultades, competencias y funciones de cada área u órgano administrativo", "Unidad de Transparencia"),
            ("IV", "Las metas y objetivos de las áreas u órganos administrativos de conformidad con sus programas operativos", "Unidad de Transparencia"),
            ("V", "Los indicadores relacionados con temas de interés público o trascendencia social", "Unidad de Transparencia"),
            ("VI", "El directorio de todas las personas servidoras públicas", "Unidad de Transparencia"),
            ("VII", "La remuneración bruta y neta de todas las personas servidoras públicas de base y de confianza", "Unidad de Transparencia"),
            ("VIII", "Los gastos de representación y viáticos", "Recursos Financieros"),
            ("IX", "El número total de las plazas y del personal de base y confianza", "Unidad de Transparencia"),
            ("X", "Las contrataciones de servicios profesionales por honorarios", "Unidad de Transparencia"),
            ("XI", "La versión pública de las declaraciones patrimoniales de las personas servidoras públicas", "Unidad de Transparencia"),
            ("XII", "El domicilio y otros datos de contacto de la Unidad de Transparencia", "Unidad de Transparencia"),
            ("XV", "Las condiciones generales de trabajo, contratos o convenios que regulen las relaciones laborales", "Unidad de Transparencia"),
            ("XVI", "La información curricular", "Unidad de Transparencia"),
            ("XVII", "El listado de personas servidoras públicas con sanciones administrativas firmes", "Unidad de Transparencia"),
            ("XVIII", "Los servicios y trámites que ofrecen", "Unidad de Transparencia"),
            ("XIX", "La información financiera sobre el presupuesto asignado", "Unidad de Transparencia"),
            ("XXI", "Los montos destinados a gastos relativos a comunicación social y publicidad oficial", "Recursos Financieros"),
            ("XXII", "Los informes de resultados de las auditorías al ejercicio presupuestal de cada Sujeto Obligado", "Unidad de Transparencia"),
            ("XXV", "Las concesiones, contratos, convenios, permisos, licencias o autorizaciones otorgados", "Unidad de Transparencia"),
            ("XXVI", "Los resultados de los procedimientos de adjudicación directa, invitación restringida y licitación", "Unidad de Transparencia"),
            ("XXVII", "Los informes que generen de conformidad con las disposiciones jurídicas", "Unidad de Transparencia"),
            ("XXVIII", "Las estadísticas que generen en cumplimiento de sus atribuciones, facultades, competencias y funciones", "Unidad de Transparencia"),
            ("XXIX", "Los informes de avances programáticos o presupuestales, balances generales y su estado financiero", "Unidad de Transparencia"),
            ("XXX", "El padrón de proveedores y contratistas en los sistemas o medios habilitados para ello", "Unidad de Transparencia"),
            ("XXXI", "Los convenios de colaboración, coordinación y concertación con los sectores público, social y privado", "Unidad de Transparencia"),
            ("XXXII", "El inventario de bienes muebles e inmuebles en posesión y propiedad", "Unidad de Transparencia"),
            ("XXXIII", "Las recomendaciones emitidas por los órganos públicos del Estado mexicano u organismos internacionales", "Unidad de Transparencia"),
            ("XXXIV", "Las resoluciones que se emitan en procesos o procedimientos seguidos en forma de juicio", "Unidad de Transparencia"),
            ("XXXV", "Los mecanismos de participación ciudadana", "Unidad de Transparencia"),
            ("XXXVII", "Las actas y resoluciones del Comité de Transparencia", "Unidad de Transparencia"),
            ("XLII", "Las donaciones hechas a terceros en dinero o en especie", "Recursos Financieros"),
            ("XLIII", "El catálogo de disposición documental y la guía simple de archivo o documental", "Unidad de Transparencia"),
            ("XLVI", "Cualquier otra información que sea de utilidad o se considere relevante", "Unidad de Transparencia"),
        ]

        # Crear/actualizar fracciones
        created_count = 0
        updated_count = 0
        
        for numero, nombre, area in fracciones_oficiales:
            tipo_usuario = area_mapping.get(area, 'transparencia')
            
            fraccion, created = Fraccion.objects.get_or_create(
                numero=numero,
                defaults={
                    'nombre': nombre,
                    'descripcion': f"Fracción {numero} del Artículo 65 - {nombre}",
                    'tipo_usuario_asignado': tipo_usuario,
                    'activa': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Fracción {numero} creada: {nombre[:50]}...')
                )
            else:
                # Actualizar datos existentes
                fraccion.nombre = nombre
                fraccion.descripcion = f"Fracción {numero} del Artículo 65 - {nombre}"
                fraccion.tipo_usuario_asignado = tipo_usuario
                fraccion.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'🔄 Fracción {numero} actualizada: {nombre[:50]}...')
                )

        # Resumen final
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 FRACCIONES OFICIALES CARGADAS:')
        )
        self.stdout.write(f'✅ Nuevas: {created_count}')
        self.stdout.write(f'🔄 Actualizadas: {updated_count}')
        self.stdout.write(f'📋 Total: {len(fracciones_oficiales)} fracciones')
        self.stdout.write(f'🔍 Transparencia: 31 fracciones')
        self.stdout.write(f'💰 Recursos Financieros: 3 fracciones')
        self.stdout.write(f'📊 Otras: 1 fracción')