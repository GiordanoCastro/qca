import os
import random
import string
from datetime import datetime, date, time
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# Modelo de Usuario Administrador / Encargado de Laboratorio
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(120), nullable=True)
    rol = db.Column(db.String(20), default='admin')  # admin, tecnico
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.username} ({self.rol})>"

# Tabla intermedia para elementos reservados por sesión
reserva_elementos = db.Table(
    'reserva_elementos',
    db.Column('reserva_id', db.Integer, db.ForeignKey('reservas.id'), primary_key=True),
    db.Column('elemento_id', db.Integer, db.ForeignKey('elementos_laboratorio.id'), primary_key=True)
)

class Laboratorio(db.Model):
    __tablename__ = 'laboratorios'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    ubicacion = db.Column(db.String(100), nullable=False)
    capacidad_alumnos = db.Column(db.Integer, nullable=False, default=20)
    color = db.Column(db.String(30), default='blue')  # blue, emerald, purple, amber
    normas_seguridad = db.Column(db.Text, nullable=True)
    activo = db.Column(db.Boolean, default=True)

    elementos = db.relationship('ElementoLaboratorio', backref='laboratorio', lazy=True, cascade='all, delete-orphan')
    reservas = db.relationship('Reserva', backref='laboratorio', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'ubicacion': self.ubicacion,
            'capacidad_alumnos': self.capacidad_alumnos,
            'color': self.color,
            'normas_seguridad': self.normas_seguridad,
            'activo': self.activo,
            'elementos': [e.to_dict() for e in self.elementos]
        }

class ElementoLaboratorio(db.Model):
    __tablename__ = 'elementos_laboratorio'

    id = db.Column(db.Integer, primary_key=True)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey('laboratorios.id'), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(60), nullable=False)  # Instrumental, Extracción y Seguridad, Vidriería, Calefacción y Agitación
    cantidad_disponible = db.Column(db.Integer, default=1)
    descripcion = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'laboratorio_id': self.laboratorio_id,
            'nombre': self.nombre,
            'categoria': self.categoria,
            'cantidad_disponible': self.cantidad_disponible,
            'descripcion': self.descripcion
        }

class Reserva(db.Model):
    __tablename__ = 'reservas'

    id = db.Column(db.Integer, primary_key=True)
    codigo_reserva = db.Column(db.String(20), unique=True, nullable=False, index=True)
    laboratorio_id = db.Column(db.Integer, db.ForeignKey('laboratorios.id'), nullable=False)
    
    # Datos del Docente
    docente_nombre = db.Column(db.String(120), nullable=False)
    docente_email = db.Column(db.String(120), nullable=False)
    docente_departamento = db.Column(db.String(120), nullable=False)
    asignatura = db.Column(db.String(120), nullable=False)
    cantidad_alumnos = db.Column(db.Integer, nullable=False, default=1)
    titulo_practica = db.Column(db.String(150), nullable=False)

    # Horario (Límite operativo: 08:30 a 18:30)
    fecha = db.Column(db.String(10), nullable=False, index=True)  # Formato YYYY-MM-DD
    hora_inicio = db.Column(db.String(5), nullable=False)        # Formato HH:MM
    hora_fin = db.Column(db.String(5), nullable=False)           # Formato HH:MM
    
    # Estado: CONFIRMADA, EN_CURSO, COMPLETADA, CANCELADA
    estado = db.Column(db.String(20), default='CONFIRMADA', index=True)
    
    # Bitácora Inicial (Plan de trabajo y reactivos)
    bitacora_plan = db.Column(db.Text, nullable=False)
    reactivos_utilizados = db.Column(db.Text, nullable=True)
    observaciones_seguridad = db.Column(db.Text, nullable=True)

    # Bitácora de Cierre / Post-sesión
    bitacora_cierre = db.Column(db.Text, nullable=True)
    incidentes_novedades = db.Column(db.Text, nullable=True)
    estado_devolucion = db.Column(db.String(50), nullable=True)  # 'Conforme y Limpio', 'Observaciones en Material', 'Pendiente Limpieza', 'Incidente Reportado'
    fecha_cierre_bitacora = db.Column(db.DateTime, nullable=True)
    responsable_cierre = db.Column(db.String(120), nullable=True)

    fecha_creacion = db.Column(db.DateTime, default=datetime.now)

    # Elementos seleccionados para esta reserva
    elementos = db.relationship('ElementoLaboratorio', secondary=reserva_elementos, backref=db.backref('reservas_asociadas', lazy='dynamic'))

    @staticmethod
    def generar_codigo():
        letras = ''.join(random.choices(string.ascii_uppercase, k=3))
        numeros = ''.join(random.choices(string.digits, k=4))
        return f"LQ-{letras}-{numeros}"

    def to_dict(self):
        return {
            'id': self.id,
            'codigo_reserva': self.codigo_reserva,
            'laboratorio_id': self.laboratorio_id,
            'laboratorio_nombre': self.laboratorio.nombre if self.laboratorio else '',
            'laboratorio_codigo': self.laboratorio.codigo if self.laboratorio else '',
            'laboratorio_color': self.laboratorio.color if self.laboratorio else 'blue',
            'docente_nombre': self.docente_nombre,
            'docente_email': self.docente_email,
            'docente_departamento': self.docente_departamento,
            'asignatura': self.asignatura,
            'cantidad_alumnos': self.cantidad_alumnos,
            'titulo_practica': self.titulo_practica,
            'fecha': self.fecha,
            'hora_inicio': self.hora_inicio,
            'hora_fin': self.hora_fin,
            'estado': self.estado,
            'bitacora_plan': self.bitacora_plan,
            'reactivos_utilizados': self.reactivos_utilizados,
            'observaciones_seguridad': self.observaciones_seguridad,
            'bitacora_cierre': self.bitacora_cierre,
            'incidentes_novedades': self.incidentes_novedades,
            'estado_devolucion': self.estado_devolucion,
            'fecha_cierre_bitacora': self.fecha_cierre_bitacora.strftime('%d/%m/%Y %H:%M') if self.fecha_cierre_bitacora else None,
            'responsable_cierre': self.responsable_cierre,
            'elementos': [{'id': e.id, 'nombre': e.nombre, 'categoria': e.categoria} for e in self.elementos]
        }
