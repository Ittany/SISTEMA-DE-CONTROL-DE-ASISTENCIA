from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone
from .models import Area, Empleado, Asistencia, Permiso, Correccion, Notificacion, Auditoria
from .services import decidir_permiso
from .security import registrar

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        registrar(request, 'MODIFICAR_AREA', f'Área #{obj.pk}; cambio={change}')

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('dni', 'nombre_completo', 'area', 'rol', 'cargo', 'antiguedad', 'vacaciones_disponibles')
    search_fields = ('dni', 'nombres', 'apellidos', 'email')
    list_filter = ('area', 'rol', 'contrato')
    list_select_related = ('area', 'usuario')
    fieldsets = [('Identidad', {'fields': ('usuario', 'dni', 'nombres', 'apellidos', 'email')}), ('Vínculo laboral', {'fields': ('cargo', 'area', 'ingreso', 'contrato', 'rol', 'salario')}), ('Horario', {'fields': ('horario_entrada', 'horario_salida')})]
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        registrar(request, 'ACTUALIZAR_EMPLEADO' if change else 'CREAR_EMPLEADO', f'Empleado #{obj.pk}; campos {list(form.changed_data)}')

    def delete_model(self, request, obj):
        registrar(request, 'ELIMINAR_EMPLEADO', f'Empleado #{obj.pk}')
        super().delete_model(request, obj)

    @admin.display(description='Empleado')
    def nombre_completo(self, obj): return f'{obj.nombres} {obj.apellidos}'

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'area', 'fecha', 'entrada', 'salida', 'horas', 'extras')
    list_filter = ('fecha', 'empleado__area')
    search_fields = ('empleado__dni', 'empleado__nombres', 'empleado__apellidos')
    list_select_related = ('empleado', 'empleado__area')
    readonly_fields = ('empleado', 'fecha', 'entrada', 'salida', 'observacion', 'creado', 'actualizado')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    @admin.display(description='Área')
    def area(self, obj): return obj.empleado.area

@admin.action(description='Aprobar permisos seleccionados', permissions=['view'])
def aprobar_seleccionados(modeladmin, request, queryset):
    aprobados = 0
    for permiso in queryset:
        try:
            decidir_permiso(request, permiso.pk, Permiso.APROBADO)
            aprobados += 1
        except (ValidationError, PermissionError) as exc:
            modeladmin.message_user(request, f'Permiso #{permiso.pk}: {exc}', level=messages.WARNING)
    modeladmin.message_user(request, f'{aprobados} permisos aprobados; notificaciones internas creadas.')

@admin.register(Permiso)
class PermisoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'tipo', 'inicio', 'fin', 'dias', 'estado', 'area')
    list_filter = ('estado', 'tipo', 'inicio', 'empleado__area')
    search_fields = ('empleado__dni', 'empleado__nombres', 'empleado__apellidos')
    list_select_related = ('empleado', 'empleado__area')
    readonly_fields = ('empleado', 'tipo', 'inicio', 'fin', 'motivo', 'documento', 'estado', 'revisado_por', 'revisado_en', 'creado')
    actions = [aprobar_seleccionados]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
    @admin.display(description='Área')
    def area(self, obj): return obj.empleado.area

@admin.register(Correccion)
class CorreccionAdmin(admin.ModelAdmin):
    list_display = ('asistencia', 'administrador', 'motivo', 'creado')
    readonly_fields = ('asistencia', 'administrador', 'motivo', 'justificacion', 'entrada_anterior', 'salida_anterior', 'creado')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'texto', 'visto', 'creado')
    readonly_fields = ('usuario', 'texto', 'visto', 'creado')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'ip', 'detalle')
    list_filter = ('accion', 'fecha')
    search_fields = ('usuario__username', 'detalle', 'accion')
    readonly_fields = ('usuario', 'accion', 'detalle', 'ip', 'fecha')
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
