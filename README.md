# TecnoAndes S.A.C. · Caso 3

**Sistema Web de Control de Asistencia, Permisos y Vacaciones**  
Universidad Nacional del Centro del Perú · Facultad de Ingeniería de Sistemas  
Práctica Semana 12 · Desarrollo de Aplicaciones Web

## Alcance

Proyecto individual desarrollado **exclusivamente para el Caso 3** de la guía. La empresa tecnológica ficticia **TecnoAndes S.A.C.** administra las asistencias, permisos, vacaciones y reportes de su personal mediante Django 5.2 y SQLite. Diseño empresarial en **celeste, blanco y plomo**, sin imágenes decorativas ni emojis.

## Funcionalidades

- Empleados con DNI único, correo `@tecnoandes.pe`, cargo, área, contrato, antigüedad y salario exclusivo de RR. HH.
- Áreas de Sistemas, Contabilidad, Ventas, Logística y RRHH.
- Marcación de entrada y salida con hora real; una entrada por día, cálculo de horas trabajadas y extras por encima de ocho horas.
- Validación de marcaciones de lunes a viernes dentro del margen de **±2 horas del horario individual**.
- Corrección de asistencias solo por RRHH, con motivo, justificación de al menos 50 caracteres y registro histórico.
- Solicitudes de permiso personal, médico, duelo, maternidad/paternidad, otros y vacaciones; validación de fechas, motivo, superposiciones y saldo anual de 30 días.
- Flujo pendiente, aprobado o rechazado con autorizaciones por área o RRHH y notificaciones internas.
- Roles: administrador RRHH, jefe de área, empleado y contador. Restricciones jerárquicas en vistas y consultas.
- Recordatorio de entrada al ingresar durante días laborables; bloqueo de cuentas inactivas y auditoría de operaciones críticas.
- Reportes de horas y horas extra con ámbito global o por área; exportación demostrativa como `.txt`.
- Django Admin personalizado con búsquedas, filtros, campos calculados y aprobación masiva.
- CSRF en todos los formularios POST, contraseñas hasheadas, sesión HttpOnly con **45 minutos de inactividad**, consultas con `select_related`.
- Datos demo: **12 empleados, 5 áreas, 72 asistencias y 12 permisos** (repetible sin duplicar la información).

## Requisitos

- Python 3.11 o superior
- Git Bash o PowerShell
- Conexión a internet para instalar Django

## Instalación: Git Bash (Windows)

```bash
python -m venv .venv
source .venv/Scripts/activate
python -m pip install -r requirements.txt
python manage.py makemigrations gestion
python manage.py migrate
python manage.py cargar_demo --password 'Cambiar2026!'
python manage.py runserver
```

## Instalación: PowerShell (Windows)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations gestion
python manage.py migrate
python manage.py cargar_demo --password "Cambiar2026!"
python manage.py runserver
```

Acceso: `http://127.0.0.1:8000/`  
Inicio de sesión: `http://127.0.0.1:8000/cuentas/login/`  
Django Admin: `http://127.0.0.1:8000/admin/`

## Usuarios de demostración

| Usuario | Perfil | Contraseña local inicial |
|---|---|---|
| `rrhh01` | Administrador RRHH | `Cambiar2026!` |
| `jefe_sis` | Jefe de Sistemas | `Cambiar2026!` |
| `jefe_ven` | Jefa de Ventas | `Cambiar2026!` |
| `contador01` | Contador | `Cambiar2026!` |
| `empleado01` a `empleado08` | Empleados | `Cambiar2026!` |

**Solo para datos ficticios y pruebas locales.** Nunca reutilizar estas contraseñas para cuentas reales. Al volver a ejecutar `cargar_demo`, no se sobrescriben las contraseñas existentes.

## Roles y permisos

| Operación | RRHH | Jefe | Empleado | Contador |
|---|---|---|---|---|
| Marcación personal | Sí | Sí | Sí | Sí |
| Solicitud propia de permiso | Sí | Sí | Sí | Sí |
| Consultar asistencia | Global | Su área | Propia | Global |
| Aprobar permisos | Todos | Su área | No | No |
| Corregir asistencia | Sí | No | No | No |
| Reportes | Global | Su área | No | Global |
| Datos laborales y salarios | Sí | No | No | No |
| Auditoría | Sí | No | No | No |

## Flujo de uso

1. Inicia sesión con el usuario correspondiente.
2. En el panel, consulta tus estadísticas y el recordatorio de asistencia.
3. En **Asistencias**, registra entrada y salida durante la ventana del horario laboral; los registros quedan asociados a tu usuario.
4. En **Nueva solicitud**, registra tipo de permiso, fechas, motivo (30 caracteres mínimo) y descripción del adjunto.
5. Inicia sesión como jefe del área o RRHH; revisa **Permisos y vacaciones** y aprueba o rechaza solicitudes pendientes.
6. El empleado puede revisar el estado y encontrar una notificación interna.
7. RRHH puede corregir una marcación con justificación y revisar el registro en **Auditoría**.
8. Los jefes, RRHH y contador consultan los reportes permitidos por su nivel de acceso.

## Manual breve para empleados

**Inicio de sesión:** usa las credenciales proporcionadas en el entorno de práctica.  
**Asistencia:** selecciona «Registrar entrada» al comenzar y «Registrar salida» al finalizar; el sistema verifica el horario y evita duplicados.  
**Permiso o vacaciones:** ingresa a «Nueva solicitud», completa las fechas y explica el motivo. El estado inicial será pendiente.  
**Seguimiento:** revisa «Permisos y vacaciones» y «Notificaciones». Una aprobación o rechazo se refleja en ambos apartados.  
**Errores:** una marcación fuera del horario permitido se rechaza; si necesitas corregir un registro, comunícate con RRHH. Cierra sesión al terminar.

## Pruebas

```bash
python manage.py check
python manage.py test gestion
```

Se incluyen pruebas de acceso, restricciones entre áreas, aprobaciones, notificaciones, validaciones de fechas/correo, privacidad del contador y vacaciones.

## Estructura

```text
tecnoandes_caso3/
├── config/                  Configuración, seguridad y rutas Django
├── gestion/                 Modelos, vistas, formularios, permisos y middleware
│   ├── management/commands/ Carga de datos demostrativos
│   ├── migrations/          Migraciones generadas al instalar
│   ├── admin.py             Administración personalizada
│   ├── services.py          Lógica de aprobación y notificación
│   ├── security.py          Roles y auditoría
│   └── tests.py             Pruebas automatizadas
├── capturas/                Evidencias visuales de las pruebas
├── templates/               Pantallas corporativas y formularios
├── static/css/              Diseño celeste, blanco y plomo
├── manage.py
├── requirements.txt
└── README.md
```

## Consideraciones técnicas

- Este proyecto usa **Django Auth local**; no conecta con un directorio corporativo real.
- Las notificaciones se almacenan dentro del sistema; **no se envían correos reales**.
- La cuota de vacaciones usa la regla académica simplificada de **30 días**, sin cálculo de devengo ni renovaciones de periodo. En una aplicación real se requiere reglamento laboral y política de acumulación.
- La exportación es un documento de texto de ejemplo, sin integración con planillas reales.
- Los datos de asistencia no pueden editarse desde cuentas de empleado; la corrección explícita corresponde a RRHH.
- Se utiliza SQLite para evaluación local; para concurrencia y bloqueo de filas efectivo en producción se recomienda PostgreSQL.
- Antes de desplegar: definir `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, HTTPS, servidor SMTP (si aplica) y controles adicionales de seguridad.

## 10. Evidencias de funcionamiento y seguridad

Las siguientes capturas documentan el funcionamiento del **Caso 3** desde los perfiles de RR. HH., jefe de Sistemas, contador y empleado, así como las validaciones de formularios, la autorización y las sesiones. Se conservan los títulos y la numeración de las pruebas realizadas; se agrupan algunos apartados que funcionan como encabezados.

> **Rutas de las imágenes:** las referencias se han preparado con nombres `Captura01.png` a `Captura21.png` dentro de la carpeta `capturas/`, situada junto a este `README.md`. Si tus archivos tienen otros nombres o extensiones, ajusta las rutas Markdown. Las imágenes no se han incluido en este archivo: deben estar presentes en el repositorio para que GitHub las muestre.

### 10.1. Panel principal de Recursos Humanos

Vista general del panel administrativo de RR. HH., con indicadores y acceso a los módulos de gestión de asistencia, permisos y personal.

![Evidencia 01: 10.1. Panel principal de Recursos Humanos](capturas/Captura01.png)

#### 10.1.1. Marcación de asistencia fuera del horario

Prueba de control horario al intentar registrar una entrada tardía; el sistema aplica la validación del margen permitido.

![Evidencia 02: 10.1.1. Marcación de asistencia fuera del horario](capturas/Captura02.png)

#### 10.1.2. Reporte de asistencia

Consulta de registros de asistencia, horas trabajadas y horas extra desde el perfil autorizado.

![Evidencia 03: 10.1.2. Reporte de asistencia](capturas/Captura03.png)

#### 10.1.3. Directorio de empleados

Visualización del personal registrado, organizado mediante la información laboral y de sus áreas.

![Evidencia 04: 10.1.3. Directorio de empleados](capturas/Captura04.png)

#### 10.1.4. Auditoría de marcación fuera del horario

Evidencia de los registros de control y auditoría relacionados con una marcación fuera del horario establecido.

![Evidencia 05: 10.1.4. Auditoría de marcación fuera del horario](capturas/Captura05.png)

#### 10.1.5. Django Admin

Interfaz de administración de Django, con módulos, filtros y operaciones autorizadas para RR. HH.

![Evidencia 06: 10.1.5. Django Admin](capturas/Captura06.png)

#### 10.1.6. Permisos y vacaciones

Listado de solicitudes y sus estados de gestión dentro del módulo de permisos y vacaciones.

![Evidencia 07: 10.1.6. Permisos y vacaciones](capturas/Captura07.png)

#### 10.1.7. Nueva solicitud

Formulario para solicitar permisos o vacaciones con selección de fechas, tipo de solicitud y motivo.

![Evidencia 08: 10.1.7. Nueva solicitud](capturas/Captura08.png)

### 10.2. Solicitud registrada correctamente

Confirmación visual del registro exitoso de una solicitud, que queda con estado pendiente hasta su evaluación.

![Evidencia 09: 10.2. Solicitud registrada correctamente](capturas/Captura09.png)

### 10.3. Validaciones y errores de solicitud

Las siguientes evidencias muestran mensajes de validación antes de registrar una solicitud con información incorrecta.

#### 10.3.1. Validación de la extensión mínima del motivo

Prueba de validación cuando el motivo no cumple el mínimo exigido de 30 caracteres.

![Evidencia 10: 10.3.1. Validación de la extensión mínima del motivo](capturas/Captura10.png)

#### 10.3.2. Fechas anteriores y solicitud pendiente superpuesta

Prueba de validación de fechas no permitidas y de solicitudes que coinciden con una pendiente existente.

![Evidencia 11: 10.3.2. Fechas anteriores y solicitud pendiente superpuesta](capturas/Captura11.png)

#### 10.3.4. Fecha inicial posterior a la fecha final

Mensaje de error ante una solicitud cuya fecha de inicio es posterior a la fecha de finalización.

![Evidencia 12: 10.3.4. Fecha inicial posterior a la fecha final](capturas/Captura12.png)

### 10.4. Panel del jefe de Sistemas

Vista del panel correspondiente al jefe de área con las opciones disponibles para su perfil.

![Evidencia 13: 10.4. Panel del jefe de Sistemas](capturas/Captura13.png)

#### 10.4.1. Reporte del sistema

Consulta de los reportes de asistencia limitados al personal del área bajo responsabilidad del jefe.

![Evidencia 14: 10.4.1. Reporte del sistema](capturas/Captura14.png)

#### 10.4.2. Registro diario de asistencia del jefe

Visualización de las marcaciones personales del jefe de Sistemas.

![Evidencia 15: 10.4.2. Registro diario de asistencia del jefe](capturas/Captura15.png)

### 10.5. Panel del contador

El contador dispone de acceso de consulta a reportes, pero no de permisos para modificar información laboral o aprobar solicitudes.

#### 10.5.1. Registro de asistencia del contador

Consulta y registro de asistencia desde el usuario contador, respetando sus permisos de solo lectura para reportes.

![Evidencia 16: 10.5.1. Registro de asistencia del contador](capturas/Captura16.png)

### 10.6. Panel de control del empleado

El empleado accede a sus registros personales y solicitudes, sin privilegios administrativos.

#### 10.6.1. Panel de asistencias del empleado

Vista del historial personal y de las opciones de marcación del empleado.

![Evidencia 17: 10.6.1. Panel de asistencias del empleado](capturas/Captura17.png)

### 10.7. Intento de acceso a reportes restringidos

Prueba de un usuario sin autorización que intenta abrir una sección de reportes fuera de sus permisos.

![Evidencia 18: 10.7. Intento de acceso a reportes restringidos](capturas/Captura18.png)

### 10.8. Control de acceso: 403 Forbidden

Pantalla de acceso denegado que demuestra la restricción de funciones por rol.

![Evidencia 19: 10.8. Control de acceso: 403 Forbidden](capturas/Captura19.png)

### 10.9. Permisos del empleado: consulta y solicitud sin aprobación

Verificación de que el empleado puede consultar y registrar sus propias solicitudes, pero no aprobarlas.

![Evidencia 20: 10.9. Permisos del empleado: consulta y solicitud sin aprobación](capturas/Captura20.png)

### 10.10. Prueba de cookies de sesión

Evidencia de la cookie de sesión generada por Django y de sus atributos de seguridad, examinados con las herramientas del navegador.

![Evidencia 21: 10.10. Prueba de cookies de sesión](capturas/Captura21.png)

