from datetime import datetime, timedelta
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
from django.utils import timezone

class AccountAndAttendanceMiddleware:
    """Bloqueo de inactivos, recordatorio de marcación y control de horario."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.is_active:
                logout(request)
                return HttpResponseForbidden('La cuenta está desactivada.')
            perfil = getattr(request.user, 'perfil', None)
            if perfil:
                hoy = timezone.localdate()
                if request.path.startswith('/asistencia/marcar/') and request.method == 'POST':
                    from .security import registrar
                    from .views import horario_valido
                    accion = request.POST.get('accion', '')
                    if not horario_valido(perfil, accion):
                        registrar(request, 'HORARIO_DENEGADO', f'Marcación {accion} fuera del margen permitido')
                        return HttpResponseForbidden('La marcación está fuera de la ventana de ±2 horas del horario laboral.')
                if not request.session.get('recordatorio_' + str(hoy)):
                    if hoy.weekday() < 5 and not perfil.asistencias.filter(fecha=hoy, entrada__isnull=False).exists():
                        request.recordatorio_asistencia = True
                    request.session['recordatorio_' + str(hoy)] = True
        response = self.get_response(request)
        if request.user.is_authenticated and request.method == 'POST' and request.path.startswith('/admin/'):
            from .security import registrar
            registrar(request, 'ADMIN_POST', f'Operación de administración: {request.path}; HTTP {response.status_code}')
        return response
