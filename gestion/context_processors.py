def identity(request):
    if not request.user.is_authenticated:
        return {'perfil_actual': None, 'notificaciones_pendientes': 0, 'recordatorio_entrada': False}
    perfil = getattr(request.user, 'perfil', None)
    return {
        'perfil_actual': perfil,
        'notificaciones_pendientes': request.user.avisos.filter(visto=False).count() if perfil else 0,
        'recordatorio_entrada': getattr(request, 'recordatorio_asistencia', False),
    }
