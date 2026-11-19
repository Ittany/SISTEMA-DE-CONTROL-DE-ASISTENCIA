from django.contrib import admin
from django.urls import path, include

admin.site.site_header = 'TecnoAndes | Administración de RR. HH.'
admin.site.site_title = 'TecnoAndes RR. HH.'
admin.site.index_title = 'Gestión administrativa'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuentas/', include('django.contrib.auth.urls')),
    path('', include('gestion.urls')),
]
