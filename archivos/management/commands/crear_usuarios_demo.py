from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from archivos.models import PerfilUsuario

class Command(BaseCommand):
    help = 'Crea usuarios de demostración para el sistema'

    def handle(self, *args, **options):
        # Usuario admin principal (si no existe)
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_user(
                username='admin',
                email='admin@sistema.gob.mx',
                password='admin123',
                first_name='Administrador',
                last_name='Sistema',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superusuario admin creado')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Usuario admin ya existe')
            )

        # Usuario de Transparencia
        transparencia_user, created = User.objects.get_or_create(
            username='transparencia',
            defaults={
                'email': 'transparencia@sistema.gob.mx',
                'first_name': 'Usuario',
                'last_name': 'Transparencia',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            transparencia_user.set_password('transparencia123')
            transparencia_user.save()
        
        # Crear perfil de transparencia
        perfil_transparencia, created = PerfilUsuario.objects.get_or_create(
            user=transparencia_user,
            defaults={'tipo_usuario': 'transparencia'}
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Usuario transparencia {"creado" if created else "actualizado"}')
        )

        # Usuario de Recursos Financieros
        financieros_user, created = User.objects.get_or_create(
            username='financieros',
            defaults={
                'email': 'financieros@sistema.gob.mx',
                'first_name': 'Usuario',
                'last_name': 'Recursos Financieros',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            financieros_user.set_password('financieros123')
            financieros_user.save()
        
        # Crear perfil de recursos financieros
        perfil_financieros, created = PerfilUsuario.objects.get_or_create(
            user=financieros_user,
            defaults={'tipo_usuario': 'recursos_financieros'}
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Usuario financieros {"creado" if created else "actualizado"}')
        )

        # Usuario de solo lectura (para demostración)
        lectura_user, created = User.objects.get_or_create(
            username='consulta',
            defaults={
                'email': 'consulta@sistema.gob.mx',
                'first_name': 'Usuario',
                'last_name': 'Consulta',
                'is_staff': False,
                'is_superuser': False
            }
        )
        if created:
            lectura_user.set_password('consulta123')
            lectura_user.save()
        
        # Crear perfil de transparencia para consulta
        perfil_consulta, created = PerfilUsuario.objects.get_or_create(
            user=lectura_user,
            defaults={'tipo_usuario': 'transparencia'}
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Usuario consulta {"creado" if created else "actualizado"}')
        )

        # Resumen final
        self.stdout.write(
            self.style.SUCCESS('\n🎉 USUARIOS DEMO CREADOS EXITOSAMENTE')
        )
        self.stdout.write('📋 Credenciales de acceso:')
        self.stdout.write('👑 Admin: admin / admin123')
        self.stdout.write('🔍 Transparencia: transparencia / transparencia123')
        self.stdout.write('💰 Financieros: financieros / financieros123')
        self.stdout.write('👀 Consulta: consulta / consulta123')
        self.stdout.write('\n🌐 Accede en: http://127.0.0.1:8000/')