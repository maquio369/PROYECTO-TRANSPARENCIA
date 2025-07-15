from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'archivos'

urlpatterns = [
    # Página principal
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='archivos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),  # ← CAMBIO AQUÍ
    
    # Gestión de archivos
    path('cargar/', views.CargarArchivoView.as_view(), name='cargar_archivo'),
    path('listado/', views.ListadoArchivosView.as_view(), name='listado_archivos'),
    path('historial/<int:fraccion_id>/', views.HistorialView.as_view(), name='historial'),
    
    # Visualización y descarga
    path('file/<int:archivo_id>/', views.DescargarArchivoView.as_view(), name='descargar_archivo'),
    path('ver/<int:archivo_id>/', views.VerArchivoView.as_view(), name='ver_archivo'),
    
    # Estadísticas
    path('estadisticas/', views.EstadisticasView.as_view(), name='estadisticas'),
]