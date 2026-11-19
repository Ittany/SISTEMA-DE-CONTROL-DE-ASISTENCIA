from datetime import date, datetime, timedelta
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone

class Area(models.Model):
    nombre = models.CharField(max_length=70, unique=True)
    def __str__(self): return self.nombre
    class Meta:
        verbose_name = 'Área'
        ordering = ['nombre']

class Empleado(models.Model):
    RRHH, JEFE, EMPLEADO, CONTADOR = 'rrhh', 'jefe', 'empleado', 'contador'
    ROLES = [(RRHH, 'Administrador RRHH'), (JEFE, 'Jefe de área'), (EMPLEADO, 'Empleado'), (CONTADOR, 'Contador')]
    PLANILLA, LOCACION = 'planilla', 'locacion'
    CONTRATOS = [(PLANILLA, 'Planilla'), (LOCACION, 'Locación')]
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='perfil')
    dni = models.CharField(max_length=8, unique=True, validators=[RegexValidator(r'^\d{8}$', 'DNI: exactamente 8 dígitos.')])
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    cargo = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name='empleados')
    ingreso = models.DateField('Fecha de ingreso')
    contrato = models.CharField(max_length=12, choices=CONTRATOS, default=PLANILLA)
    email = models.EmailField('Correo corporativo', unique=True)
    rol = models.CharField(max_length=12, choices=ROLES, default=EMPLEADO)
    salario = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0'))], help_text='Dato reservado para RRHH')
    horario_entrada = models.TimeField(default='08:00')
    horario_salida = models.TimeField(default='17:00')
    def clean(self):
        super().clean()
        if self.ingreso and self.ingreso > timezone.localdate(): raise ValidationError({'ingreso': 'La fecha de ingreso no puede ser futura.'})
        if self.email and not self.email.lower().endswith('@tecnoandes.pe'):
            raise ValidationError({'email': 'Debe utilizar una cuenta @tecnoandes.pe.'})
        if not self.cargo or not self.cargo.strip(): raise ValidationError({'cargo': 'El cargo es obligatorio.'})
        if self.horario_entrada and self.horario_salida and self.horario_salida <= self.horario_entrada:
            raise ValidationError({'horario_salida': 'La salida debe ser posterior a la entrada.'})
    @property
    def antiguedad(self):
        hoy = timezone.localdate()
        meses = (hoy.year - self.ingreso.year) * 12 + hoy.month - self.ingreso.month - (hoy.day < self.ingreso.day)
        meses = max(meses, 0)
        return f'{meses // 12} años y {meses % 12} meses'
    @property
    def vacaciones_disponibles(self):
        # Cuota académica anual de 30 días; las vacaciones aprobadas descuentan su duración.
        aprobados = self.permisos.filter(tipo=Permiso.VACACIONES, estado=Permiso.APROBADO)
        tomados = sum((p.dias for p in aprobados), 0)
        return max(30 - tomados, 0)
    def __str__(self): return f'{self.nombres} {self.apellidos} ({self.dni})'
    class Meta:
        ordering = ['apellidos', 'nombres']
        verbose_name_plural = 'Empleados'
        permissions = [('ver_reportes_globales', 'Puede consultar reportes globales'), ('ver_reportes_area', 'Puede consultar reportes de su área'), ('corregir_asistencia', 'Puede corregir asistencias')]

class Asistencia(models.Model):
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='asistencias')
    fecha = models.DateField(default=timezone.localdate)
    entrada = models.DateTimeField()
    salida = models.DateTimeField(null=True, blank=True)
    observacion = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-fecha', '-entrada']
        verbose_name_plural = 'Asistencias'
        constraints = [models.UniqueConstraint(fields=['empleado', 'fecha'], name='asistencia_unica_por_dia')]
    def clean(self):
        super().clean()
        if self.entrada and timezone.localtime(self.entrada).date() != self.fecha:
            raise ValidationError({'entrada': 'La entrada debe corresponder a la fecha indicada.'})
        if self.salida and self.entrada and self.salida <= self.entrada:
            raise ValidationError({'salida': 'La salida debe ser posterior a la entrada.'})
    @property
    def horas(self):
        if not self.salida or not self.entrada: return Decimal('0.00')
        return Decimal(str(round((self.salida - self.entrada).total_seconds() / 3600, 2)))
    @property
    def extras(self): return max(self.horas - Decimal('8'), Decimal('0'))
    def __str__(self): return f'{self.empleado} · {self.fecha}'

class Correccion(models.Model):
    SISTEMA, OLVIDO, OTRO = 'sistema', 'olvido', 'otro'
    MOTIVOS = [(SISTEMA, 'Error del sistema'), (OLVIDO, 'Olvido'), (OTRO, 'Otro')]
    asistencia = models.ForeignKey(Asistencia, on_delete=models.PROTECT, related_name='correcciones')
    administrador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    motivo = models.CharField(max_length=12, choices=MOTIVOS)
    justificacion = models.TextField()
    entrada_anterior = models.DateTimeField()
    salida_anterior = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    def clean(self):
        super().clean()
        if len(self.justificacion.strip()) < 50: raise ValidationError({'justificacion': 'La justificación debe contener al menos 50 caracteres.'})
    class Meta:
        verbose_name_plural = 'Correcciones'

class Permiso(models.Model):
    PERSONAL, MEDICO, DUELO, FAMILIAR, OTRO, VACACIONES = 'personal', 'medico', 'duelo', 'familiar', 'otro', 'vacaciones'
    TIPOS = [(PERSONAL, 'Personal'), (MEDICO, 'Médico'), (DUELO, 'Duelo'), (FAMILIAR, 'Maternidad/Paternidad'), (OTRO, 'Otro'), (VACACIONES, 'Vacaciones')]
    PENDIENTE, APROBADO, RECHAZADO = 'pendiente', 'aprobado', 'rechazado'
    ESTADOS = [(PENDIENTE, 'Pendiente'), (APROBADO, 'Aprobado'), (RECHAZADO, 'Rechazado')]
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name='permisos')
    tipo = models.CharField(max_length=12, choices=TIPOS)
    inicio = models.DateField()
    fin = models.DateField()
    motivo = models.TextField()
    documento = models.CharField('Descripción del adjunto', max_length=200, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=PENDIENTE)
    revisado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='permisos_revisados')
    revisado_en = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = 'Permisos y vacaciones'
        ordering = ['-creado']
    @property
    def dias(self):
        if not self.inicio or not self.fin: return 0
        return (self.fin - self.inicio).days + 1
    def clean(self):
        super().clean()
        if self.inicio and self.fin and self.fin < self.inicio:
            raise ValidationError({'fin': 'La fecha final debe ser igual o posterior al inicio.'})
        if self.motivo and len(self.motivo.strip()) < 30:
            raise ValidationError({'motivo': 'El motivo requiere al menos 30 caracteres.'})
        if self.empleado_id and self.inicio and self.fin and self.estado != self.RECHAZADO:
            qs = Permiso.objects.filter(empleado_id=self.empleado_id, estado__in=[self.PENDIENTE, self.APROBADO], inicio__lte=self.fin, fin__gte=self.inicio)
            if self.pk: qs = qs.exclude(pk=self.pk)
            if qs.exists(): raise ValidationError('Ya existe otro permiso pendiente o aprobado en esas fechas.')
        if self.empleado_id and self.tipo == self.VACACIONES and self.estado in [self.PENDIENTE, self.APROBADO]:
            previos = Permiso.objects.filter(empleado_id=self.empleado_id, tipo=self.VACACIONES, estado__in=[self.PENDIENTE, self.APROBADO]).exclude(pk=self.pk)
            dias_usados = sum(p.dias for p in previos)
            if self.dias + dias_usados > 30:
                raise ValidationError(f'Días de vacaciones insuficientes: disponibles {max(30 - dias_usados, 0)}.')
    def __str__(self): return f'{self.empleado} · {self.get_tipo_display()} ({self.estado})'

class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='avisos')
    texto = models.CharField(max_length=255)
    visto = models.BooleanField(default=False)
    creado = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-creado']
        verbose_name_plural = 'Notificaciones'

class Auditoria(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=80)
    detalle = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = 'Registros de auditoría'
