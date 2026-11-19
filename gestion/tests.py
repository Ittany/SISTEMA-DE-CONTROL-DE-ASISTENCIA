from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Area, Empleado, Asistencia, Permiso, Auditoria

class CasoTresTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.area = Area.objects.create(nombre='Sistemas')
        cls.otra = Area.objects.create(nombre='Ventas')
        for username, rol, area, n in [('rrhh','rrhh',cls.area,1),('jefe','jefe',cls.area,2),('empleado','empleado',cls.area,3),('ajeno','empleado',cls.otra,4),('contador','contador',cls.otra,5)]:
            user = User.objects.create_user(username=username, password='ClaveSegura123!')
            Empleado.objects.create(usuario=user, dni=f'7011000{n}', nombres=username.title(), apellidos='Pruebas', cargo='Especialista', area=area, ingreso=date(2023,1,1), email=f'{username}@tecnoandes.pe', rol=rol)

    def test_login_obligatorio(self):
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 302)

    def test_empleado_no_ve_directorio_ni_auditoria(self):
        self.client.login(username='empleado', password='ClaveSegura123!')
        self.assertEqual(self.client.get(reverse('empleados')).status_code, 403)
        self.assertEqual(self.client.get(reverse('auditoria')).status_code, 403)
        self.assertTrue(Auditoria.objects.filter(accion='ACCESO_DENEGADO').exists())

    def test_jefe_solo_su_area(self):
        permiso = Permiso.objects.create(empleado=Empleado.objects.get(usuario__username='ajeno'), tipo='personal', inicio=date(2027,2,10), fin=date(2027,2,10), motivo='Motivo suficientemente extenso para la prueba de autorización.')
        self.client.login(username='jefe', password='ClaveSegura123!')
        resp = self.client.post(reverse('resolver_permiso', args=[permiso.pk,'aprobado']))
        self.assertEqual(resp.status_code, 403)
        permiso.refresh_from_db()
        self.assertEqual(permiso.estado, 'pendiente')

    def test_rrhh_aprueba_y_notifica(self):
        perfil = Empleado.objects.get(usuario__username='empleado')
        permiso = Permiso.objects.create(empleado=perfil, tipo='personal', inicio=date(2027,3,10), fin=date(2027,3,10), motivo='Motivo suficientemente extenso para una solicitud correcta.')
        self.client.login(username='rrhh', password='ClaveSegura123!')
        self.client.post(reverse('resolver_permiso', args=[permiso.pk,'aprobado']))
        permiso.refresh_from_db()
        self.assertEqual(permiso.estado, 'aprobado')
        self.assertTrue(perfil.usuario.avisos.exists())

    def test_rechaza_fechas_solapadas(self):
        perfil = Empleado.objects.get(usuario__username='empleado')
        Permiso.objects.create(empleado=perfil, tipo='personal', inicio=date(2027,5,10), fin=date(2027,5,12), motivo='Motivo de más de treinta caracteres en un permiso existente.')
        nuevo = Permiso(empleado=perfil, tipo='medico', inicio=date(2027,5,11), fin=date(2027,5,13), motivo='Motivo de más de treinta caracteres para nueva solicitud.')
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError): nuevo.full_clean()

    def test_validacion_dni_y_correo(self):
        perfil = Empleado.objects.get(usuario__username='empleado')
        perfil.email = 'ejemplo@gmail.com'
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError): perfil.full_clean()

    def test_incompatibilidad_salida_entrada(self):
        perfil = Empleado.objects.get(usuario__username='empleado')
        entrada = timezone.now()
        item = Asistencia(empleado=perfil, fecha=timezone.localdate(), entrada=entrada, salida=entrada-timedelta(minutes=1))
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError): item.full_clean()

    def test_reporte_contador_sin_auditoria(self):
        self.client.login(username='contador', password='ClaveSegura123!')
        self.assertEqual(self.client.get(reverse('reportes')).status_code, 200)
        self.assertEqual(self.client.get(reverse('auditoria')).status_code, 403)

    def test_maximo_treinta_dias_vacaciones(self):
        perfil = Empleado.objects.get(usuario__username='empleado')
        v = Permiso(empleado=perfil, tipo='vacaciones', inicio=date(2027,1,1), fin=date(2027,2,5), motivo='Vacaciones de prueba con duración superior a los treinta días.')
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError): v.full_clean()
