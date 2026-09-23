# Sistema de Reservas de Laboratorios de Química con Bitácora de Trabajo

Aplicación web desarrollada en **Python (Flask + SQLite + SQLAlchemy)** con interfaz moderna y responsiva (**Tailwind CSS + Lucide Icons**) para la gestión integral de reservas de laboratorios de química por parte de docentes y personal técnico.

---

## Características Principales

1. **Reserva Exclusiva de Laboratorio**:
   - Cada reserva asigna el laboratorio completo para el docente y su grupo durante la sesión programada.
   - Control estricto para evitar solapamientos o colisiones horarias en el mismo espacio.

2. **Selección de Elementos e Instrumental de Pañol**:
   - Cada laboratorio dispone de su propio inventario clasificado de equipos y elementos (campanas de extracción, balanzas analíticas, rotavapores, espectrofotómetros, mecheros Bunsen, vidriería esmerilada, etc.).
   - Al reservar, el docente marca mediante casillas interactivas qué elementos requerirá para la práctica.

3. **Franja Horaria Obligatoria (08:30 a 18:30 hrs)**:
   - Validaciones tanto en el navegador (JavaScript) como en el servidor (Python) para garantizar que ninguna práctica inicie antes de las 08:30 am ni concluya después de las 18:30 hrs.
   - Botones de turnos rápidos (M1, M2, M3, T1, T2) o selección personalizada.

4. **Módulo de Bitácora de Trabajo**:
   - **Bitácora Inicial**: Registro del objetivo experimental, procedimiento/metodología y reactivos químicos a manipular al momento de reservar.
   - **Bitácora de Cierre / Post-sesión**: Registro del trabajo efectivamente realizado, novedades o roturas de material, y estado de recepción/entrega del laboratorio.
   - **Historial y Auditoría de Bitácoras**: Buscador histórico de bitácoras por docente, asignatura, reactivos o laboratorio.

5. **Comprobante Oficial Imprimible y Panel de Pañol**:
   - Generación de comprobante con código único (ej. `LQ-ORG-4401`) formateado para impresión con firmas de recepción.
   - Panel de control para el pañolero con la lista de equipos que deben estar alistados para cada práctica del día.

---

## Estructura del Proyecto

```
sistema-reservas-quimica/
├── app.py                  # Servidor web Flask y rutas de la API
├── models.py               # Modelos SQLAlchemy (Laboratorio, Elemento, Reserva)
├── seed.py                 # Poblado inicial de laboratorios, equipos y reservas
├── test_reservas.py        # Suite de pruebas unitarias automatizadas
├── README.md               # Documentación del proyecto
├── instance/
│   └── reservas_quimica.db # Base de datos SQLite
├── templates/
│   ├── base.html           # Layout base con navbar y alertas
│   ├── index.html          # Portal principal y catálogo de laboratorios
│   ├── reservar.html       # Asistente de reserva en 5 pasos
│   ├── reserva_detalle.html# Ficha formal, comprobante y formulario de bitácora
│   ├── calendario.html     # Agenda visual de 08:30 a 18:30
│   ├── bitacoras.html      # Historial y auditoría de bitácoras
│   ├── mis_reservas.html   # Consulta de reservas por docente/código
│   └── admin.html          # Panel técnico de pañol y preparación de equipos
└── static/
    ├── css/styles.css      # Estilos personalizados
    └── js/main.js          # Validaciones dinámicas de horario y UI
```

---

## Cómo Ejecutar el Sistema

### 1. Iniciar la Aplicación

Abre una terminal PowerShell en este directorio y ejecuta:

```powershell
python app.py
```

El servidor iniciará en: **`http://127.0.0.1:5000`**

*(Si la base de datos no existe o está vacía, se inicializará y precargará automáticamente con 4 laboratorios y datos de ejemplo).*

### 2. Ejecutar las Pruebas Unitarias

Para verificar las validaciones de horario, control de colisiones y persistencia de bitácoras:

```powershell
python test_reservas.py
```

### 3. Reinicializar los Datos de Prueba

Si deseas restablecer la base de datos con los laboratorios y reservas iniciales:

```powershell
python seed.py
```
