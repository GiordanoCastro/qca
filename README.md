# Sistema de Reservas de Laboratorios de Química con Bitácora de Trabajo

Aplicación web desarrollada en **Python (Flask + PostgreSQL 18 + SQLAlchemy)** con interfaz moderna y responsiva (**Tailwind CSS + Lucide Icons**) para la gestión integral de reservas de laboratorios de química por parte de docentes y personal técnico.

---

## Características Principales

1. **Base de Datos PostgreSQL**:
   - Persistencia completa en PostgreSQL con modelos relacionales y claves foráneas.
   - Compatibilidad tanto en local como en la nube (Vercel Postgres, Neon, Supabase).

2. **Usuario Administrador y Control de Acceso**:
   - Sistema de autenticación con `Flask-Login` y contraseñas cifradas con `Werkzeug`.
   - Credenciales iniciales: Usuario `admin` / Contraseña `admin123`.
   - Protección de rutas de gestión mediante decorador `@login_required`.

3. **CRUD Completo de Laboratorios**:
   - Crear, consultar, editar, activar/desactivar y eliminar laboratorios con código, ubicación, capacidad y normativas de seguridad.

4. **CRUD Completo de Materiales y Equipos**:
   - Inventario por laboratorio clasificado por categorías (*Extracción y Seguridad, Instrumental de Medición, Vidriería y Reactores, Calefacción y Agitación, Equipos Especiales*).
   - Control de stock y especificaciones técnicas.

5. **Franja Horaria Obligatoria (08:30 a 18:30 hrs)**:
   - Validaciones tanto en el navegador (JavaScript) como en el servidor (Python) para garantizar que ninguna práctica inicie antes de las 08:30 am ni concluya después de las 18:30 hrs.
   - Botones de turnos rápidos (M1, M2, M3, T1, T2) o selección personalizada.
   - Prevención estricta de solapamiento en el mismo laboratorio.

6. **Módulo de Bitácora de Trabajo**:
   - **Bitácora Inicial**: Registro del objetivo experimental, procedimiento/metodología y reactivos químicos a manipular al momento de reservar.
   - **Bitácora de Cierre / Post-sesión**: Registro del trabajo efectivamente realizado, novedades o roturas de material, y estado de recepción/entrega del laboratorio.
   - **Historial y Auditoría de Bitácoras**: Buscador histórico de bitácoras por docente, asignatura, reactivos o laboratorio.

---

## Estructura del Proyecto

```
sistema-reservas-quimica/
├── app.py                     # Servidor web Flask y rutas de la API
├── models.py                  # Modelos SQLAlchemy (Usuario, Laboratorio, Elemento, Reserva)
├── seed.py                    # Poblado inicial de laboratorios, equipos y reservas
├── test_reservas.py           # Suite de pruebas unitarias automatizadas
├── requirements.txt           # Dependencias para producción y Vercel
├── vercel.json                # Configuración de despliegue serverless en Vercel
├── README.md                  # Documentación del proyecto
├── templates/
│   ├── base.html              # Layout base con navbar y alertas
│   ├── index.html             # Portal principal y catálogo de laboratorios
│   ├── login.html             # Acceso de usuario administrador
│   ├── admin.html             # Panel técnico de pañol y resumen
│   ├── admin_laboratorios.html# CRUD lista de laboratorios
│   ├── admin_laboratorio_form.html # Formulario de laboratorio
│   ├── admin_materiales.html  # CRUD lista de materiales con filtros
│   ├── admin_material_form.html    # Formulario de material
│   ├── reservar.html          # Asistente de reserva en 5 pasos
│   ├── reserva_detalle.html   # Ficha formal, comprobante y formulario de bitácora
│   ├── calendario.html        # Agenda visual de 08:30 a 18:30
│   ├── bitacoras.html         # Historial y auditoría de bitácoras
│   └── mis_reservas.html      # Consulta de reservas por docente/código
└── static/
    ├── css/styles.css         # Estilos personalizados
    └── js/main.js             # Validaciones dinámicas de horario y UI
```

---

## Cómo Ejecutar en Local

### 1. Iniciar la Aplicación

Asegúrate de que el servicio PostgreSQL esté activo (base de datos `reservas_quimica_db`) y ejecuta:

```powershell
python app.py
```

El servidor iniciará en: **`http://127.0.0.1:5000`**

### 2. Ejecutar las Pruebas Unitarias

```powershell
python test_reservas.py
```

---

## Despliegue en Vercel

El repositorio ya cuenta con los archivos `requirements.txt` y `vercel.json` configurados para Vercel Serverless Functions:

1. Ve a [vercel.com/new](https://vercel.com/new) e inicia sesión con tu cuenta de GitHub.
2. Selecciona e importa el repositorio: **`GiordanoCastro/qca`**.
3. En la sección **Environment Variables**, agrega:
   * **`DATABASE_URL`**: La URL de tu base de datos PostgreSQL en la nube (ejemplo desde [Neon.tech](https://neon.tech), [Supabase](https://supabase.com), o [Vercel Postgres](https://vercel.com/docs/storage/vercel-postgres)).
   * Formato: `postgresql://usuario:contraseña@host:5432/nombre_db?sslmode=require`
4. Haz clic en **Deploy**.
5. Al abrir tu URL de Vercel, el sistema creará y sembrará automáticamente las tablas con el usuario `admin` y los 4 laboratorios en tu base de datos de producción.
