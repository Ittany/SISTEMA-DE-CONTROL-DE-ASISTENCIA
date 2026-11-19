from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Permiso, Notificacion
from .security import registrar

@transaction.atomic
def decidir_permiso(request, permiso_id, decision):
    permiso = Permiso.objects.select_for_update().select_related('empleado__area', 'empleado__usuario').get(pk=permiso_id)
    actor = request.user.perfil
    autorizado = actor.rol == actor.RRHH or (actor.rol == actor.JEFE and actor.area_id == permiso.empleado.area_id)
    if not autorizado:
        registrar(request, 'ACCESO_DENEGADO', f'Aprobar permiso {permiso_id} fuera de su área')
        raise PermissionError('Solo RRHH o el jefe del área pueden gestionar el permiso.')
    if permiso.estado != permiso.PENDIENTE: raise ValidationError('El permiso ya ha sido evaluado.')
    if decision not in (Permiso.APROBADO, Permiso.RECHAZADO): raise ValidationError('Decisión inválida.')
    permiso.estado = decision
    permiso.revisado_por = request.user
    permiso.revisado_en = timezone.now()
    permiso.full_clean()
    permiso.save(update_fields=['estado', 'revisado_por', 'revisado_en'])
    Notificacion.objects.create(usuario=permiso.empleado.usuario, texto=f'Su solicitud #{permiso.pk} fue {permiso.get_estado_display().lower()}.')
    registrar(request, 'PERMISO_' + decision.upper(), f'Permiso #{permiso.pk} de {permiso.empleado}')
    return permiso
