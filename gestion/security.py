import logging
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .models import Auditoria

logger = logging.getLogger('gestion.auditoria')

def ip_cliente(request):
    # No se confía en X-Forwarded-For sin un proxy de confianza configurado.
    return request.META.get('REMOTE_ADDR') or None

def registrar(request, accion, detalle=''):
    user = request.user if request.user.is_authenticated else None
    item = Auditoria.objects.create(usuario=user, accion=accion, detalle=str(detalle)[:2000], ip=ip_cliente(request))
    logger.info('AUDITORIA usuario=%s ip=%s accion=%s detalle=%s', user, item.ip, accion, detalle)
    return item

def roles_permitidos(*roles):
    def decorator(view):
        @login_required
        @wraps(view)
        def inner(request, *args, **kwargs):
            rol = getattr(getattr(request.user, 'perfil', None), 'rol', None)
            if rol not in roles:
                registrar(request, 'ACCESO_DENEGADO', f'Intento de ingresar a {request.path}')
                raise PermissionDenied('No tiene permisos para acceder a esta función.')
            return view(request, *args, **kwargs)
        return inner
    return decorator
