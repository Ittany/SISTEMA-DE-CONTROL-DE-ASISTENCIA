from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('asistencia/', views.asistencias, name='asistencias'),
    path('asistencia/marcar/', views.marcar_asistencia, name='marcar_asistencia'),
    path('asistencia/<int:pk>/corregir/', views.corregir_asistencia, name='corregir_asistencia'),
    path('permisos/', views.mis_permisos, name='permisos'),
    path('permisos/solicitar/', views.solicitar_permiso, name='solicitar_permiso'),
    path('permisos/<int:pk>/<str:decision>/', views.resolver_permiso, name='resolver_permiso'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar/', views.exportar, name='exportar'),
    path('empleados/', views.empleados, name='empleados'),
    path('auditoria/', views.auditoria, name='auditoria'),
    path('notificaciones/', views.notificaciones, name='notificaciones'),
]
