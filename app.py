import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Usuario, Laboratorio, ElementoLaboratorio, Reserva

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave-secreta-laboratorios-quimica-2026'

# Conexión a PostgreSQL (PostgreSQL 18 en local)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'postgresql+psycopg2://postgres:123456@localhost:5432/reservas_quimica_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Debes iniciar sesión como administrador para acceder a esta función.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))

HORA_MINIMA_MINUTOS = 8 * 60 + 30   # 08:30 -> 510 min
HORA_MAXIMA_MINUTOS = 18 * 60 + 30  # 18:30 -> 1110 min

def hora_a_minutos(hora_str):
    try:
        partes = hora_str.split(':')
        return int(partes[0]) * 60 + int(partes[1])
    except Exception:
        return None

def minutos_a_hora(minutos):
    h = minutos // 60
    m = minutos % 60
    return f"{h:02d}:{m:02d}"

def validar_horario(hora_ini_str, hora_fin_str):
    m_ini = hora_a_minutos(hora_ini_str)
    m_fin = hora_a_minutos(hora_fin_str)
    
    if m_ini is None or m_fin is None:
        return False, "Formato de hora inválido."
    if m_ini < HORA_MINIMA_MINUTOS:
        return False, "La hora de inicio no puede ser antes de las 08:30 hrs."
    if m_fin > HORA_MAXIMA_MINUTOS:
        return False, "La hora de término no puede superar las 18:30 hrs."
    if m_fin <= m_ini:
        return False, "La hora de término debe ser posterior a la hora de inicio."
    if (m_fin - m_ini) < 30:
        return False, "La reserva debe durar al menos 30 minutos."
    return True, ""

def hay_solapamiento(laboratorio_id, fecha_str, hora_ini_str, hora_fin_str, excluir_reserva_id=None):
    m_ini_nuevo = hora_a_minutos(hora_ini_str)
    m_fin_nuevo = hora_a_minutos(hora_fin_str)

    query = Reserva.query.filter(
        Reserva.laboratorio_id == laboratorio_id,
        Reserva.fecha == fecha_str,
        Reserva.estado != 'CANCELADA'
    )
    if excluir_reserva_id:
        query = query.filter(Reserva.id != excluir_reserva_id)

    reservas_existentes = query.all()

    for r in reservas_existentes:
        m_ini_existente = hora_a_minutos(r.hora_inicio)
        m_fin_existente = hora_a_minutos(r.hora_fin)
        
        # Colisión si se cruzan los rangos
        if m_ini_nuevo < m_fin_existente and m_fin_nuevo > m_ini_existente:
            return True, r
    return False, None

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        username_o_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        usuario = Usuario.query.filter(
            (Usuario.username == username_o_email) | (Usuario.email == username_o_email)
        ).first()

        if usuario and usuario.check_password(password):
            if not usuario.activo:
                flash('Tu cuenta se encuentra inactiva. Contacta al soporte.', 'danger')
                return redirect(url_for('login'))

            login_user(usuario)
            flash(f'¡Bienvenido/a, {usuario.nombre_completo or usuario.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin'))
        else:
            flash('Usuario o contraseña incorrectos. Verifica tus credenciales.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('index'))

# --- RUTAS PÚBLICAS Y DE RESERVA ---

@app.route('/')
def index():
    laboratorios = Laboratorio.query.filter_by(activo=True).all()
    hoy = date.today().strftime('%Y-%m-%d')
    reservas_hoy = Reserva.query.filter(
        Reserva.fecha == hoy,
        Reserva.estado != 'CANCELADA'
    ).order_by(Reserva.hora_inicio).all()
    
    total_labs = len(laboratorios)
    total_reservas = Reserva.query.filter(Reserva.estado != 'CANCELADA').count()
    bitacoras_completadas = Reserva.query.filter(Reserva.bitacora_cierre.isnot(None)).count()

    return render_template(
        'index.html',
        laboratorios=laboratorios,
        reservas_hoy=reservas_hoy,
        hoy=hoy,
        total_labs=total_labs,
        total_reservas=total_reservas,
        bitacoras_completadas=bitacoras_completadas
    )

@app.route('/reservar', methods=['GET', 'POST'])
def reservar():
    laboratorios = Laboratorio.query.filter_by(activo=True).all()
    
    if request.method == 'POST':
        lab_id = request.form.get('laboratorio_id', type=int)
        docente_nombre = request.form.get('docente_nombre', '').strip()
        docente_email = request.form.get('docente_email', '').strip()
        docente_departamento = request.form.get('docente_departamento', '').strip()
        asignatura = request.form.get('asignatura', '').strip()
        cantidad_alumnos = request.form.get('cantidad_alumnos', type=int, default=1)
        titulo_practica = request.form.get('titulo_practica', '').strip()
        fecha = request.form.get('fecha', '').strip()
        hora_inicio = request.form.get('hora_inicio', '').strip()
        hora_fin = request.form.get('hora_fin', '').strip()
        
        # Elementos seleccionados
        elementos_ids = request.form.getlist('elementos_ids', type=int)

        # Bitácora Inicial
        bitacora_plan = request.form.get('bitacora_plan', '').strip()
        reactivos_utilizados = request.form.get('reactivos_utilizados', '').strip()
        observaciones_seguridad = request.form.get('observaciones_seguridad', '').strip()

        # Validaciones
        laboratorio = db.session.get(Laboratorio, lab_id)
        if not laboratorio or not laboratorio.activo:
            flash('Debes seleccionar un laboratorio válido y activo.', 'danger')
            return redirect(url_for('reservar'))

        if not (docente_nombre and docente_email and asignatura and titulo_practica and fecha and hora_inicio and hora_fin and bitacora_plan):
            flash('Por favor completa todos los campos obligatorios, incluyendo el plan inicial de bitácora.', 'warning')
            return redirect(url_for('reservar'))

        # Validar horario 08:30 a 18:30
        es_valido, msg_horario = validar_horario(hora_inicio, hora_fin)
        if not es_valido:
            flash(msg_horario, 'danger')
            return redirect(url_for('reservar'))

        # Validar colisión de reserva en el mismo laboratorio
        colision, res_conflictiva = hay_solapamiento(lab_id, fecha, hora_inicio, hora_fin)
        if colision:
            flash(f'El laboratorio {laboratorio.nombre} ya se encuentra reservado el {fecha} entre las {res_conflictiva.hora_inicio} y {res_conflictiva.hora_fin} hrs por {res_conflictiva.docente_nombre}. Por favor elige otro horario.', 'danger')
            return redirect(url_for('reservar'))

        # Crear código único
        codigo = Reserva.generar_codigo()
        while Reserva.query.filter_by(codigo_reserva=codigo).first():
            codigo = Reserva.generar_codigo()

        nueva_reserva = Reserva(
            codigo_reserva=codigo,
            laboratorio_id=lab_id,
            docente_nombre=docente_nombre,
            docente_email=docente_email,
            docente_departamento=docente_departamento or 'Departamento de Química',
            asignatura=asignatura,
            cantidad_alumnos=cantidad_alumnos,
            titulo_practica=titulo_practica,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            estado='CONFIRMADA',
            bitacora_plan=bitacora_plan,
            reactivos_utilizados=reactivos_utilizados,
            observaciones_seguridad=observaciones_seguridad
        )

        db.session.add(nueva_reserva)

        # Asociar elementos seleccionados
        if elementos_ids:
            elementos = ElementoLaboratorio.query.filter(
                ElementoLaboratorio.id.in_(elementos_ids),
                ElementoLaboratorio.laboratorio_id == lab_id
            ).all()
            nueva_reserva.elementos.extend(elementos)

        db.session.commit()

        flash(f'¡Reserva {codigo} registrada exitosamente para el laboratorio {laboratorio.nombre}!', 'success')
        return redirect(url_for('ver_reserva', codigo=codigo))

    lab_id_param = request.args.get('lab', type=int)
    fecha_param = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    return render_template('reservar.html', laboratorios=laboratorios, lab_id_param=lab_id_param, fecha_param=fecha_param)

@app.route('/reserva/<codigo>')
def ver_reserva(codigo):
    reserva = Reserva.query.filter_by(codigo_reserva=codigo).first_or_404()
    return render_template('reserva_detalle.html', reserva=reserva)

@app.route('/reserva/<codigo>/bitacora', methods=['POST'])
def actualizar_bitacora(codigo):
    reserva = Reserva.query.filter_by(codigo_reserva=codigo).first_or_404()
    
    bitacora_cierre = request.form.get('bitacora_cierre', '').strip()
    incidentes_novedades = request.form.get('incidentes_novedades', '').strip()
    estado_devolucion = request.form.get('estado_devolucion', 'Conforme y Limpio')
    responsable_cierre = request.form.get('responsable_cierre', '').strip()

    if not bitacora_cierre:
        flash('Debes ingresar la descripción del trabajo realizado para cerrar la bitácora.', 'warning')
        return redirect(url_for('ver_reserva', codigo=codigo))

    reserva.bitacora_cierre = bitacora_cierre
    reserva.incidentes_novedades = incidentes_novedades or 'Sin incidentes reportados.'
    reserva.estado_devolucion = estado_devolucion
    reserva.responsable_cierre = responsable_cierre or reserva.docente_nombre
    reserva.fecha_cierre_bitacora = datetime.now()
    reserva.estado = 'COMPLETADA'

    db.session.commit()
    flash('¡Bitácora de trabajo de la sesión registrada y guardada exitosamente!', 'success')
    return redirect(url_for('ver_reserva', codigo=codigo))

@app.route('/reserva/<codigo>/cancelar', methods=['POST'])
def cancelar_reserva(codigo):
    reserva = Reserva.query.filter_by(codigo_reserva=codigo).first_or_404()
    reserva.estado = 'CANCELADA'
    db.session.commit()
    flash(f'La reserva {codigo} ha sido cancelada correctamente y el laboratorio queda liberado.', 'info')
    return redirect(url_for('ver_reserva', codigo=codigo))

@app.route('/calendario')
def calendario():
    laboratorios = Laboratorio.query.filter_by(activo=True).all()
    lab_id = request.args.get('lab_id', type=int)
    fecha_sel = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    
    query = Reserva.query.filter(Reserva.estado != 'CANCELADA')
    if lab_id:
        query = query.filter(Reserva.laboratorio_id == lab_id)

    reservas = query.order_by(Reserva.fecha, Reserva.hora_inicio).all()
    
    return render_template(
        'calendario.html',
        laboratorios=laboratorios,
        lab_id_sel=lab_id,
        fecha_sel=fecha_sel,
        reservas=reservas
    )

@app.route('/bitacoras')
def bitacoras():
    laboratorios = Laboratorio.query.filter_by(activo=True).all()
    lab_id = request.args.get('lab_id', type=int)
    buscar = request.args.get('q', '').strip()

    query = Reserva.query.filter(Reserva.estado != 'CANCELADA')
    if lab_id:
        query = query.filter(Reserva.laboratorio_id == lab_id)
    if buscar:
        like_term = f"%{buscar}%"
        query = query.filter(
            (Reserva.docente_nombre.ilike(like_term)) |
            (Reserva.asignatura.ilike(like_term)) |
            (Reserva.titulo_practica.ilike(like_term)) |
            (Reserva.reactivos_utilizados.ilike(like_term)) |
            (Reserva.codigo_reserva.ilike(like_term))
        )

    reservas = query.order_by(Reserva.fecha.desc(), Reserva.hora_inicio.desc()).all()

    return render_template(
        'bitacoras.html',
        laboratorios=laboratorios,
        lab_id_sel=lab_id,
        buscar=buscar,
        reservas=reservas
    )

@app.route('/mis-reservas', methods=['GET', 'POST'])
def mis_reservas():
    email = request.args.get('email', '').strip()
    codigo = request.args.get('codigo', '').strip()
    reservas = []

    if request.method == 'POST':
        criterio = request.form.get('criterio', '').strip()
        if '@' in criterio:
            return redirect(url_for('mis_reservas', email=criterio))
        else:
            return redirect(url_for('mis_reservas', codigo=criterio.upper()))

    if email:
        reservas = Reserva.query.filter(
            Reserva.docente_email.ilike(f"%{email}%")
        ).order_by(Reserva.fecha.desc()).all()
    elif codigo:
        reservas = Reserva.query.filter(
            Reserva.codigo_reserva.ilike(f"%{codigo}%")
        ).all()

    return render_template('mis_reservas.html', reservas=reservas, email=email, codigo=codigo)

@app.route('/admin')
@login_required
def admin():
    hoy = date.today().strftime('%Y-%m-%d')
    reservas_hoy = Reserva.query.filter(
        Reserva.fecha == hoy,
        Reserva.estado != 'CANCELADA'
    ).order_by(Reserva.hora_inicio).all()

    proximas_reservas = Reserva.query.filter(
        Reserva.fecha > hoy,
        Reserva.estado != 'CANCELADA'
    ).order_by(Reserva.fecha, Reserva.hora_inicio).limit(10).all()

    laboratorios = Laboratorio.query.all()
    total_materiales = ElementoLaboratorio.query.count()

    return render_template(
        'admin.html',
        reservas_hoy=reservas_hoy,
        proximas_reservas=proximas_reservas,
        laboratorios=laboratorios,
        total_materiales=total_materiales,
        hoy=hoy
    )

# --- CRUD DE LABORATORIOS ---

@app.route('/admin/laboratorios')
@login_required
def admin_laboratorios():
    laboratorios = Laboratorio.query.order_by(Laboratorio.codigo).all()
    return render_template('admin_laboratorios.html', laboratorios=laboratorios)

@app.route('/admin/laboratorios/nuevo', methods=['GET', 'POST'])
@login_required
def admin_laboratorio_nuevo():
    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        capacidad = request.form.get('capacidad_alumnos', type=int, default=20)
        color = request.form.get('color', 'blue')
        normas = request.form.get('normas_seguridad', '').strip()

        if not (codigo and nombre and ubicacion):
            flash('Código, nombre y ubicación son campos obligatorios.', 'warning')
            return redirect(url_for('admin_laboratorio_nuevo'))

        if Laboratorio.query.filter_by(codigo=codigo).first():
            flash(f'El código {codigo} ya se encuentra asignado a otro laboratorio.', 'danger')
            return redirect(url_for('admin_laboratorio_nuevo'))

        nuevo_lab = Laboratorio(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            ubicacion=ubicacion,
            capacidad_alumnos=capacidad,
            color=color,
            normas_seguridad=normas,
            activo=True
        )
        db.session.add(nuevo_lab)
        db.session.commit()
        flash(f'Laboratorio {nombre} ({codigo}) creado exitosamente.', 'success')
        return redirect(url_for('admin_laboratorios'))

    return render_template('admin_laboratorio_form.html', lab=None)

@app.route('/admin/laboratorios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def admin_laboratorio_editar(id):
    lab = db.session.get(Laboratorio, id)
    if not lab:
        flash('Laboratorio no encontrado.', 'danger')
        return redirect(url_for('admin_laboratorios'))

    if request.method == 'POST':
        codigo = request.form.get('codigo', '').strip().upper()
        nombre = request.form.get('nombre', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        ubicacion = request.form.get('ubicacion', '').strip()
        capacidad = request.form.get('capacidad_alumnos', type=int, default=20)
        color = request.form.get('color', 'blue')
        normas = request.form.get('normas_seguridad', '').strip()
        activo = True if request.form.get('activo') else False

        if not (codigo and nombre and ubicacion):
            flash('Código, nombre y ubicación son obligatorios.', 'warning')
            return redirect(url_for('admin_laboratorio_editar', id=id))

        otro = Laboratorio.query.filter(Laboratorio.codigo == codigo, Laboratorio.id != id).first()
        if otro:
            flash(f'El código {codigo} ya está en uso por otro laboratorio.', 'danger')
            return redirect(url_for('admin_laboratorio_editar', id=id))

        lab.codigo = codigo
        lab.nombre = nombre
        lab.descripcion = descripcion
        lab.ubicacion = ubicacion
        lab.capacidad_alumnos = capacidad
        lab.color = color
        lab.normas_seguridad = normas
        lab.activo = activo

        db.session.commit()
        flash(f'Laboratorio {nombre} actualizado correctamente.', 'success')
        return redirect(url_for('admin_laboratorios'))

    return render_template('admin_laboratorio_form.html', lab=lab)

@app.route('/admin/laboratorios/<int:id>/eliminar', methods=['POST'])
@login_required
def admin_laboratorio_eliminar(id):
    lab = db.session.get(Laboratorio, id)
    if not lab:
        flash('Laboratorio no encontrado.', 'danger')
        return redirect(url_for('admin_laboratorios'))

    nombre = lab.nombre
    codigo = lab.codigo
    db.session.delete(lab)
    db.session.commit()
    flash(f'Laboratorio {nombre} ({codigo}) y sus elementos han sido eliminados del sistema.', 'info')
    return redirect(url_for('admin_laboratorios'))

@app.route('/admin/laboratorios/<int:id>/toggle', methods=['POST'])
@login_required
def admin_laboratorio_toggle(id):
    lab = db.session.get(Laboratorio, id)
    if lab:
        lab.activo = not lab.activo
        db.session.commit()
        estado_str = "activado" if lab.activo else "desactivado"
        flash(f'Laboratorio {lab.codigo} ha sido {estado_str}.', 'info')
    return redirect(url_for('admin_laboratorios'))

# --- CRUD DE MATERIALES Y EQUIPOS ---

@app.route('/admin/materiales')
@login_required
def admin_materiales():
    lab_id = request.args.get('lab_id', type=int)
    categoria = request.args.get('categoria', '').strip()
    buscar = request.args.get('q', '').strip()

    query = ElementoLaboratorio.query
    if lab_id:
        query = query.filter_by(laboratorio_id=lab_id)
    if categoria:
        query = query.filter_by(categoria=categoria)
    if buscar:
        query = query.filter(
            (ElementoLaboratorio.nombre.ilike(f"%{buscar}%")) |
            (ElementoLaboratorio.descripcion.ilike(f"%{buscar}%"))
        )

    materiales = query.order_by(ElementoLaboratorio.laboratorio_id, ElementoLaboratorio.categoria).all()
    laboratorios = Laboratorio.query.all()
    categorias_disponibles = [
        'Extracción y Seguridad',
        'Equipos Especiales',
        'Instrumental de Medición',
        'Vidriería y Reactores',
        'Calefacción y Agitación'
    ]

    return render_template(
        'admin_materiales.html',
        materiales=materiales,
        laboratorios=laboratorios,
        lab_id_sel=lab_id,
        categoria_sel=categoria,
        buscar=buscar,
        categorias_disponibles=categorias_disponibles
    )

@app.route('/admin/materiales/nuevo', methods=['GET', 'POST'])
@login_required
def admin_material_nuevo():
    laboratorios = Laboratorio.query.all()
    categorias_disponibles = [
        'Extracción y Seguridad',
        'Equipos Especiales',
        'Instrumental de Medición',
        'Vidriería y Reactores',
        'Calefacción y Agitación'
    ]

    if request.method == 'POST':
        lab_id = request.form.get('laboratorio_id', type=int)
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        cantidad = request.form.get('cantidad_disponible', type=int, default=1)
        descripcion = request.form.get('descripcion', '').strip()

        if not (lab_id and nombre and categoria):
            flash('Laboratorio, nombre y categoría son requeridos.', 'warning')
            return redirect(url_for('admin_material_nuevo'))

        nuevo_mat = ElementoLaboratorio(
            laboratorio_id=lab_id,
            nombre=nombre,
            categoria=categoria,
            cantidad_disponible=cantidad,
            descripcion=descripcion
        )
        db.session.add(nuevo_mat)
        db.session.commit()
        flash(f'Material/Equipo "{nombre}" agregado exitosamente al inventario.', 'success')
        return redirect(url_for('admin_materiales', lab_id=lab_id))

    lab_id_param = request.args.get('lab_id', type=int)
    return render_template(
        'admin_material_form.html',
        material=None,
        laboratorios=laboratorios,
        categorias=categorias_disponibles,
        lab_id_param=lab_id_param
    )

@app.route('/admin/materiales/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def admin_material_editar(id):
    mat = db.session.get(ElementoLaboratorio, id)
    if not mat:
        flash('Material no encontrado.', 'danger')
        return redirect(url_for('admin_materiales'))

    laboratorios = Laboratorio.query.all()
    categorias_disponibles = [
        'Extracción y Seguridad',
        'Equipos Especiales',
        'Instrumental de Medición',
        'Vidriería y Reactores',
        'Calefacción y Agitación'
    ]

    if request.method == 'POST':
        lab_id = request.form.get('laboratorio_id', type=int)
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        cantidad = request.form.get('cantidad_disponible', type=int, default=1)
        descripcion = request.form.get('descripcion', '').strip()

        if not (lab_id and nombre and categoria):
            flash('Laboratorio, nombre y categoría son requeridos.', 'warning')
            return redirect(url_for('admin_material_editar', id=id))

        mat.laboratorio_id = lab_id
        mat.nombre = nombre
        mat.categoria = categoria
        mat.cantidad_disponible = cantidad
        mat.descripcion = descripcion

        db.session.commit()
        flash(f'Material "{nombre}" actualizado correctamente.', 'success')
        return redirect(url_for('admin_materiales', lab_id=lab_id))

    return render_template(
        'admin_material_form.html',
        material=mat,
        laboratorios=laboratorios,
        categorias=categorias_disponibles,
        lab_id_param=mat.laboratorio_id
    )

@app.route('/admin/materiales/<int:id>/eliminar', methods=['POST'])
@login_required
def admin_material_eliminar(id):
    mat = db.session.get(ElementoLaboratorio, id)
    if not mat:
        flash('Material no encontrado.', 'danger')
        return redirect(url_for('admin_materiales'))

    nombre = mat.nombre
    lab_id = mat.laboratorio_id
    db.session.delete(mat)
    db.session.commit()
    flash(f'Material/Equipo "{nombre}" eliminado del pañol.', 'info')
    return redirect(url_for('admin_materiales', lab_id=lab_id))

# --- ENDPOINTS API JSON ---

@app.route('/api/laboratorio/<int:lab_id>/elementos')
def api_elementos_laboratorio(lab_id):
    lab = db.session.get(Laboratorio, lab_id)
    if not lab:
        return jsonify({'error': 'Laboratorio no encontrado'}), 404

    elementos = [e.to_dict() for e in lab.elementos]
    categorias = {}
    for el in elementos:
        cat = el['categoria']
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(el)
    return jsonify({
        'laboratorio': {
            'id': lab.id,
            'nombre': lab.nombre,
            'codigo': lab.codigo,
            'capacidad': lab.capacidad_alumnos,
            'normas': lab.normas_seguridad
        },
        'categorias': categorias
    })

@app.route('/api/disponibilidad')
def api_disponibilidad():
    lab_id = request.args.get('lab_id', type=int)
    fecha = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    
    if not lab_id:
        return jsonify({'error': 'Falta el id del laboratorio'}), 400

    reservas = Reserva.query.filter(
        Reserva.laboratorio_id == lab_id,
        Reserva.fecha == fecha,
        Reserva.estado != 'CANCELADA'
    ).order_by(Reserva.hora_inicio).all()

    ocupados = []
    for r in reservas:
        ocupados.append({
            'codigo': r.codigo_reserva,
            'hora_inicio': r.hora_inicio,
            'hora_fin': r.hora_fin,
            'docente': r.docente_nombre,
            'asignatura': r.asignatura,
            'titulo': r.titulo_practica
        })

    return jsonify({
        'lab_id': lab_id,
        'fecha': fecha,
        'horario_operativo': {'min': '08:30', 'max': '18:30'},
        'reservas_ocupadas': ocupados
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("=" * 65)
    print("  Sistema de Reservas de Laboratorios de Química (PostgreSQL)")
    print("  Base de Datos: PostgreSQL 18 (reservas_quimica_db)")
    print("  Credenciales Admin: admin / admin123")
    print("  Horario Operativo: 08:30 a 18:30 hrs")
    print("  Servidor iniciado en: http://127.0.0.1:5000")
    print("=" * 65)
    app.run(debug=False, port=5000)
