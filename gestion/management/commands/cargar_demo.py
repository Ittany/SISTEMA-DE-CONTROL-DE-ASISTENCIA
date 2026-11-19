"""Carga reproducible de datos académicos sin contraseñas reales."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from gestion.models import Area, Empleado, Asistencia, Permiso, Notificacion

class Command(BaseCommand):
    help = 'Crea 5 áreas, 12 usuarios, 60+ asistencias y 12 permisos para demostración.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='Cambiar2026!', help='Contraseña únicamente para usuarios nuevos de demostración.')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        nombres_areas = ['Sistemas', 'Contabilidad', 'Ventas', 'Logística', 'RRHH']
        areas = {n: Area.objects.get_or_create(nombre=n)[0] for n in nombres_areas}
        personas = [
            ('rrhh01','Andrea','Rojas','RRHH','Gerente de RRHH','rrhh'),
            ('jefe_sis','Marco','Quispe','Sistemas','Jefe de Sistemas','jefe'),
            ('jefe_ven','Lucía','Campos','Ventas','Jefa Comercial','jefe'),
            ('contador01','Héctor','Flores','Contabilidad','Contador','contador'),
            ('empleado01','Carlos','Paredes','Sistemas','Analista de soporte','empleado'),
            ('empleado02','María','García','Sistemas','Desarrolladora','empleado'),
            ('empleado03','Pedro','Vargas','Ventas','Ejecutivo comercial','empleado'),
            ('empleado04','Elena','Huamán','Ventas','Especialista comercial','empleado'),
            ('empleado05','Jorge','Salazar','Logística','Coordinador de almacén','empleado'),
            ('empleado06','Rosa','Torres','Logística','Asistente logístico','empleado'),
            ('empleado07','Diego','Medina','Contabilidad','Auxiliar contable','empleado'),
            ('empleado08','Paola','Soto','RRHH','Analista de personal','empleado'),
        ]
        perfiles = []
        for i, (username, nombres, apellidos, area, cargo, rol) in enumerate(personas):
            user, created = User.objects.get_or_create(username=username, defaults={'first_name': nombres, 'last_name': apellidos, 'email': username+'@tecnoandes.pe'})
            if created:
                user.set_password(options['password'])
                user.is_staff = rol == 'rrhh'
                user.is_superuser = rol == 'rrhh'
                user.save()
            perfil, _ = Empleado.objects.get_or_create(usuario=user, defaults={
                'dni': f'{74100001+i}', 'nombres': nombres, 'apellidos': apellidos,
                'email': username+'@tecnoandes.pe', 'area': areas[area], 'cargo': cargo,
                'rol': rol, 'ingreso': date(2023+(i%3), 2+(i%9), 5),
                'contrato': 'planilla' if i%3 else 'locacion',
                'salario': Decimal('3200') + i*100,
            })
            perfiles.append(perfil)
        inicio = timezone.localdate() - timedelta(days=35)
        for i, perfil in enumerate(perfiles):
            dia = inicio
            creados = 0
            while creados < 6:
                if dia.weekday() < 5:
                    entrada = timezone.make_aware(datetime.combine(dia, time(8, 2 + i%5)))
                    salida = entrada + timedelta(hours=8+(1 if i%4 == 0 else 0), minutes=15)
                    Asistencia.objects.get_or_create(empleado=perfil, fecha=dia, defaults={'entrada': entrada, 'salida': salida})
                    creados += 1
                dia += timedelta(days=1)
        # Fechas no superpuestas por empleado. No duplica registros al ejecutar de nuevo.
        inicio_permiso = timezone.localdate() + timedelta(days=8)
        for i, perfil in enumerate(perfiles):
            primer_dia = inicio_permiso + timedelta(days=i*3)
            Permiso.objects.get_or_create(empleado=perfil, tipo='vacaciones' if i%4 == 0 else 'personal', inicio=primer_dia,
                defaults={'fin': primer_dia+timedelta(days=1 if i%4 == 0 else 0),
                          'motivo': 'Solicitud académica de prueba para verificar la gestión de permisos del personal.',
                          'documento': 'Documento de respaldo simulado', 'estado': 'pendiente'})
        self.stdout.write(self.style.SUCCESS(
            f'Demo lista: {Area.objects.count()} áreas, {Empleado.objects.count()} empleados, '
            f'{Asistencia.objects.count()} asistencias, {Permiso.objects.count()} permisos.'))
        self.stdout.write('Usuarios: rrhh01, jefe_sis, jefe_ven, contador01, empleado01 ... empleado08')
        self.stdout.write('Clave demo para cuentas nuevas: ' + options['password'])
