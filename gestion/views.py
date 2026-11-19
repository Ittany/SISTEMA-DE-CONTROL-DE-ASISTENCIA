import csv
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Q, Sum, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import PermisoForm, CorreccionForm
from .models import Area, Empleado, Asistencia, Permiso, Correccion, Auditoria, Notificacion
from .security import roles_permitidos, registrar
from .services import decidir_permiso

@login_required
def dashboard(request):
    perfil = getattr(request.user, 'perfil', None)
    if perfil is None: raise PermissionDenied('Su usuario no tiene ficha de empleado.')
    hoy = timezone.localdate()
    if perfil.rol == Empleado.RRHH:
        metrics = [('Empleados', Empleado.objects.count()), ('Asistencias hoy', Asistencia.objects.filter(fecha=hoy).count()), ('Permisos pendientes', Permiso.objects.filter(estado='pendiente').count()), ('Áreas', Area.objects.count())]
    elif perfil.rol == Empleado.JEFE:
        qs = Empleado.objects.filter(area=perfil.area)
        metrics = [('Equipo', qs.count()), ('Asistencias hoy', Asistencia.objects.filter(fecha=hoy, empleado__in=qs).count()), ('Permisos pendientes', Permiso.objects.filter(empleado__in=qs, estado='pendiente').count()), ('Mi saldo vacacional', perfil.vacaciones_disponibles)]
    elif perfil.rol == Empleado.CONTADOR:
        metrics = [('Asistencias del mes', Asistencia.objects.filter(fecha__month=hoy.month, fecha__year=hoy.year).count()), ('Registros con horas extra', sum(a.extras > 0 for a in Asistencia.objects.filter(salida__isnull=False))), ('Áreas', Area.objects.count())]
    else:
        metrics = [('Asistencias este mes', perfil.asistencias.filter(fecha__month=hoy.month, fecha__year=hoy.year).count()), ('Permisos pendientes', perfil.permisos.filter(estado='pendiente').count()), ('Permisos aprobados', perfil.permisos.filter(estado='aprobado').count()), ('Vacaciones disponibles', perfil.vacaciones_disponibles)]
    recientes = Permiso.objects.select_related('empleado', 'empleado__area')
    if perfil.rol == Empleado.JEFE: recientes = recientes.filter(empleado__area=perfil.area)
    elif perfil.rol not in (Empleado.RRHH, Empleado.CONTADOR): recientes = recientes.filter(empleado=perfil)
    elif perfil.rol == Empleado.CONTADOR: recientes = recientes.none()
    return render(request, 'gestion/dashboard.html', {'metrics': metrics, 'recientes': recientes[:7], 'hoy': hoy})

def horario_valido(perfil, accion, ahora=None):
    ahora = timezone.localtime(ahora or timezone.now())
    if ahora.weekday() >= 5: return False
    hora = perfil.horario_entrada if accion == 'entrada' else perfil.horario_salida if accion == 'salida' else None
    if hora is None: return False
    centro = timezone.make_aware(datetime.combine(ahora.date(), hora), timezone.get_current_timezone())
    return abs((ahora - centro).total_seconds()) <= 2 * 3600

@login_required
def asistencias(request):
    perfil = request.user.perfil
    qs = Asistencia.objects.select_related('empleado', 'empleado__area')
    if perfil.rol == Empleado.JEFE: qs = qs.filter(empleado__area=perfil.area)
    elif perfil.rol == Empleado.EMPLEADO: qs = qs.filter(empleado=perfil)
    elif perfil.rol == Empleado.CONTADOR: pass
    fecha = request.GET.get('fecha', '')
    area = request.GET.get('area', '')
    if fecha:
        try: qs = qs.filter(fecha=datetime.strptime(fecha, '%Y-%m-%d').date())
        except ValueError: fecha = ''
    if area and perfil.rol in (Empleado.RRHH, Empleado.CONTADOR): qs = qs.filter(empleado__area_id=area)
    return render(request, 'gestion/asistencias.html', {'registros': qs[:150], 'areas': Area.objects.all(), 'fecha': fecha, 'area_seleccionada': area})

@roles_permitidos(Empleado.RRHH, Empleado.JEFE, Empleado.EMPLEADO, Empleado.CONTADOR)
@require_POST
def marcar_asistencia(request):
    perfil = request.user.perfil
    accion = request.POST.get('accion')
    if accion not in ['entrada', 'salida']:
        messages.error(request, 'Tipo de marcación inválido.')
        return redirect('asistencias')
    if not horario_valido(perfil, accion):
        registrar(request, 'HORARIO_DENEGADO', f'{accion} fuera de ±2 horas')
        return HttpResponseForbidden('Fuera del margen de dos horas del turno de trabajo.')
    ahora = timezone.now()
    hoy = timezone.localdate()
    with transaction.atomic():
        if accion == 'entrada':
            try:
                registro, creado = Asistencia.objects.get_or_create(empleado=perfil, fecha=hoy, defaults={'entrada': ahora})
            except IntegrityError:
                creado = False
            if not creado:
                messages.error(request, 'Ya existe una entrada registrada para hoy.')
                return redirect('asistencias')
            registrar(request, 'MARCAR_ENTRADA', f'Asistencia de {perfil} - {hoy}')
            messages.success(request, 'Entrada registrada correctamente.')
        else:
            registro = Asistencia.objects.select_for_update().filter(empleado=perfil, fecha=hoy).first()
            if not registro or registro.salida:
                messages.error(request, 'No existe una entrada abierta para hoy.')
                return redirect('asistencias')
            registro.salida = ahora
            try: registro.full_clean()
            except ValidationError as exc:
                messages.error(request, str(exc))
                return redirect('asistencias')
            registro.save(update_fields=['salida', 'actualizado'])
            registrar(request, 'MARCAR_SALIDA', f'Asistencia #{registro.pk}; horas {registro.horas}; extra {registro.extras}')
            messages.success(request, 'Salida registrada correctamente.')
    return redirect('asistencias')

@login_required
def mis_permisos(request):
    perfil = request.user.perfil
    qs = Permiso.objects.select_related('empleado', 'empleado__area', 'revisado_por')
    if perfil.rol == Empleado.JEFE: qs = qs.filter(Q(empleado=perfil) | Q(empleado__area=perfil.area))
    elif perfil.rol == Empleado.RRHH: pass
    else: qs = qs.filter(empleado=perfil)
    estado = request.GET.get('estado')
    if estado in dict(Permiso.ESTADOS): qs = qs.filter(estado=estado)
    return render(request, 'gestion/permisos.html', {'permisos': qs[:150], 'estado': estado})

@roles_permitidos(Empleado.RRHH, Empleado.JEFE, Empleado.EMPLEADO, Empleado.CONTADOR)
def solicitar_permiso(request):
    form = PermisoForm(request.POST or None, empleado=request.user.perfil)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                # Serializa las altas por empleado cuando la BD soporta bloqueos de fila.
                Empleado.objects.select_for_update().get(pk=request.user.perfil.pk)
                permiso = form.save(commit=False)
                permiso.empleado = request.user.perfil
                permiso.full_clean()
                permiso.save()
                registrar(request, 'SOLICITAR_PERMISO', f'Permiso #{permiso.pk} tipo {permiso.tipo}')
            messages.success(request, 'Solicitud registrada. Estado inicial: pendiente.')
            return redirect('permisos')
        except ValidationError as exc:
            for error in exc.messages: form.add_error(None, error)
    return render(request, 'gestion/permiso_form.html', {'form': form})

@roles_permitidos(Empleado.RRHH, Empleado.JEFE)
@require_POST
def resolver_permiso(request, pk, decision):
    try:
        permiso = decidir_permiso(request, pk, decision)
    except PermissionError as exc:
        raise PermissionDenied(str(exc))
    except (ValidationError, Permiso.DoesNotExist) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f'Permiso #{permiso.pk}: {permiso.get_estado_display()}. Notificación interna creada.')
    return redirect('permisos')

@roles_permitidos(Empleado.RRHH)
def corregir_asistencia(request, pk):
    registro = get_object_or_404(Asistencia.objects.select_related('empleado'), pk=pk)
    initial = {'entrada': timezone.localtime(registro.entrada), 'salida': timezone.localtime(registro.salida) if registro.salida else None}
    form = CorreccionForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            registro = Asistencia.objects.select_for_update().get(pk=pk)
            anterior = (registro.entrada, registro.salida)
            registro.entrada, registro.salida = form.cleaned_data['entrada'], form.cleaned_data['salida']
            registro.fecha = timezone.localtime(registro.entrada).date()
            try:
                registro.full_clean()
                registro.save()
                Correccion.objects.create(asistencia=registro, administrador=request.user,
                    motivo=form.cleaned_data['motivo'], justificacion=form.cleaned_data['justificacion'],
                    entrada_anterior=anterior[0], salida_anterior=anterior[1])
            except (ValidationError, IntegrityError) as exc:
                form.add_error(None, str(exc))
                transaction.set_rollback(True)
            else:
                registrar(request, 'CORREGIR_ASISTENCIA', f'Asistencia #{pk}. Motivo: {form.cleaned_data["motivo"]}. Justificación: {form.cleaned_data["justificacion"]}')
                messages.success(request, 'Corrección registrada con trazabilidad.')
                return redirect('asistencias')
    return render(request, 'gestion/correccion.html', {'form': form, 'registro': registro})

@roles_permitidos(Empleado.RRHH, Empleado.JEFE, Empleado.CONTADOR)
def reportes(request):
    perfil = request.user.perfil
    registros = Asistencia.objects.select_related('empleado', 'empleado__area').filter(salida__isnull=False)
    if perfil.rol == Empleado.JEFE: registros = registros.filter(empleado__area=perfil.area)
    area = request.GET.get('area', '')
    if area and perfil.rol != Empleado.JEFE: registros = registros.filter(empleado__area_id=area)
    datos = {}
    for r in registros:
        key = r.empleado_id
        fila = datos.setdefault(key, {'empleado': r.empleado, 'horas': Decimal('0'), 'extras': Decimal('0'), 'jornadas': 0})
        fila['horas'] += r.horas
        fila['extras'] += r.extras
        fila['jornadas'] += 1
    return render(request, 'gestion/reportes.html', {'filas': sorted(datos.values(), key=lambda x: -x['extras']), 'areas': Area.objects.all(), 'area_seleccionada': area})

@roles_permitidos(Empleado.RRHH, Empleado.JEFE, Empleado.CONTADOR)
def exportar(request):
    perfil = request.user.perfil
    qs = Asistencia.objects.select_related('empleado', 'empleado__area').order_by('-fecha')
    if perfil.rol == Empleado.JEFE: qs = qs.filter(empleado__area=perfil.area)
    resp = HttpResponse(content_type='text/plain; charset=utf-8')
    resp['Content-Disposition'] = 'attachment; filename="asistencias_tecnoandes.txt"'
    resp.write('Empleado | Área | Fecha | Horas trabajadas | Horas extra\n')
    for a in qs[:5000]: resp.write(f'{a.empleado} | {a.empleado.area} | {a.fecha} | {a.horas} | {a.extras}\n')
    registrar(request, 'EXPORTAR_ASISTENCIAS', f'Exportación de {perfil.rol}')
    return resp

@roles_permitidos(Empleado.RRHH)
def empleados(request):
    qs = Empleado.objects.select_related('area', 'usuario')
    q = request.GET.get('q', '').strip()
    if q: qs = qs.filter(Q(nombres__icontains=q) | Q(apellidos__icontains=q) | Q(dni__icontains=q))
    return render(request, 'gestion/empleados.html', {'empleados': qs, 'q': q})

@roles_permitidos(Empleado.RRHH)
def auditoria(request):
    qs = Auditoria.objects.select_related('usuario')
    return render(request, 'gestion/auditoria.html', {'eventos': qs[:200]})

@login_required
def notificaciones(request):
    qs = request.user.avisos.all()
    if request.method == 'POST':
        qs.filter(visto=False).update(visto=True)
        return redirect('notificaciones')
    return render(request, 'gestion/notificaciones.html', {'avisos': qs[:100]})
