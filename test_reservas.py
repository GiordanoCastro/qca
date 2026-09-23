import unittest
import os
from datetime import date, datetime
from app import app, validar_horario, hay_solapamiento
from models import db, Usuario, Laboratorio, ElementoLaboratorio, Reserva
from seed import seed_database

class TestSistemaReservasQuimicaPostgres(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()

        with app.app_context():
            db.create_all()
            seed_database(app)

    def tearDown(self):
        with app.app_context():
            db.session.remove()

    def test_01_laboratorios_y_admin_en_postgres(self):
        """Verifica que se hayan cargado el usuario admin, los 4 laboratorios y sus elementos en PostgreSQL"""
        with app.app_context():
            admin = Usuario.query.filter_by(username='admin').first()
            self.assertIsNotNone(admin)
            self.assertTrue(admin.check_password('admin123'))
            self.assertFalse(admin.check_password('clave_falsa'))

            labs = Laboratorio.query.all()
            self.assertEqual(len(labs), 4)

            lab_org = Laboratorio.query.filter_by(codigo='LAB-Q101').first()
            self.assertIsNotNone(lab_org)
            self.assertGreater(len(lab_org.elementos), 3)

    def test_02_autenticacion_y_proteccion_de_rutas(self):
        """Verifica login, logout y protección con @login_required"""
        # Acceso no autorizado a rutas protegidas -> debe redirigir a /login
        resp = self.app.get('/admin/laboratorios')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

        resp = self.app.get('/admin/materiales')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

        # Login fallido
        resp = self.app.post('/login', data={'username': 'admin', 'password': 'password_incorrecto'}, follow_redirects=True)
        self.assertIn('Usuario o contraseña incorrectos', resp.text)

        # Login exitoso
        resp_login = self.app.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
        self.assertEqual(resp_login.status_code, 200)

        # Ahora el acceso a /admin/laboratorios y /admin/materiales debe ser 200 OK
        resp_auth = self.app.get('/admin/laboratorios')
        self.assertEqual(resp_auth.status_code, 200)

        # Logout
        resp_logout = self.app.get('/logout', follow_redirects=True)
        self.assertIn('cerrado sesión', resp_logout.text)

    def test_03_crud_laboratorios(self):
        """Verifica el ciclo completo de CRUD para Laboratorios"""
        with app.app_context():
            # Iniciar sesión como admin en el test client
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})

            # 1. Create (Crear nuevo laboratorio)
            resp_crear = self.app.post('/admin/laboratorios/nuevo', data={
                'codigo': 'LAB-Q201',
                'nombre': 'Laboratorio de Bioquímica y Enzimología',
                'descripcion': 'Laboratorio para purificación de proteínas y ensayos de cinéticas.',
                'ubicacion': 'Edificio de Ciencias - 4to Piso',
                'capacidad_alumnos': 18,
                'color': 'purple',
                'normas_seguridad': 'Uso obligatorio de guantes y material estéril.'
            }, follow_redirects=True)
            self.assertEqual(resp_crear.status_code, 200)
            self.assertIn('creado exitosamente', resp_crear.text)

            lab_creado = Laboratorio.query.filter_by(codigo='LAB-Q201').first()
            self.assertIsNotNone(lab_creado)
            self.assertEqual(lab_creado.capacidad_alumnos, 18)

            # 2. Update (Editar laboratorio)
            resp_editar = self.app.post(f'/admin/laboratorios/{lab_creado.id}/editar', data={
                'codigo': 'LAB-Q201',
                'nombre': 'Laboratorio de Bioquímica y Biología Molecular',
                'descripcion': 'Descripción actualizada con equipos PCR.',
                'ubicacion': 'Edificio de Ciencias - 4to Piso',
                'capacidad_alumnos': 22,
                'color': 'emerald',
                'normas_seguridad': 'Uso obligatorio de guantes.',
                'activo': '1'
            }, follow_redirects=True)
            self.assertEqual(resp_editar.status_code, 200)

            lab_actualizado = db.session.get(Laboratorio, lab_creado.id)
            self.assertEqual(lab_actualizado.nombre, 'Laboratorio de Bioquímica y Biología Molecular')
            self.assertEqual(lab_actualizado.capacidad_alumnos, 22)

            # 3. Delete (Eliminar laboratorio)
            resp_eliminar = self.app.post(f'/admin/laboratorios/{lab_creado.id}/eliminar', follow_redirects=True)
            self.assertEqual(resp_eliminar.status_code, 200)

            lab_eliminado = db.session.get(Laboratorio, lab_creado.id)
            self.assertIsNone(lab_eliminado)

    def test_04_crud_materiales(self):
        """Verifica el ciclo completo de CRUD para Materiales e Instrumental"""
        with app.app_context():
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
            lab = Laboratorio.query.first()

            # 1. Create (Crear material)
            resp_crear = self.app.post('/admin/materiales/nuevo', data={
                'laboratorio_id': lab.id,
                'nombre': 'Termociclador Digital de Gradiente',
                'categoria': 'Equipos Especiales',
                'cantidad_disponible': 3,
                'descripcion': 'Bloque para 96 tubos de 0.2 mL con tapa calefactada'
            }, follow_redirects=True)
            self.assertEqual(resp_crear.status_code, 200)
            self.assertIn('agregado exitosamente', resp_crear.text)

            mat = ElementoLaboratorio.query.filter_by(nombre='Termociclador Digital de Gradiente').first()
            self.assertIsNotNone(mat)
            self.assertEqual(mat.cantidad_disponible, 3)

            # 2. Update (Editar material)
            resp_editar = self.app.post(f'/admin/materiales/{mat.id}/editar', data={
                'laboratorio_id': lab.id,
                'nombre': 'Termociclador Digital de Gradiente PCR',
                'categoria': 'Equipos Especiales',
                'cantidad_disponible': 5,
                'descripcion': 'Actualizado a 5 unidades disponibles'
            }, follow_redirects=True)
            self.assertEqual(resp_editar.status_code, 200)

            mat_act = db.session.get(ElementoLaboratorio, mat.id)
            self.assertEqual(mat_act.cantidad_disponible, 5)

            # 3. Delete (Eliminar material)
            resp_eliminar = self.app.post(f'/admin/materiales/{mat.id}/eliminar', follow_redirects=True)
            self.assertEqual(resp_eliminar.status_code, 200)

            mat_del = db.session.get(ElementoLaboratorio, mat.id)
            self.assertIsNone(mat_del)

    def test_05_validacion_horario_y_solapamiento(self):
        """Verifica horario 08:30 - 18:30 y rechazo de solapamiento en PostgreSQL"""
        valido, _ = validar_horario('08:30', '11:00')
        self.assertTrue(valido)

        valido, _ = validar_horario('08:00', '10:00')
        self.assertFalse(valido)

        valido, _ = validar_horario('17:00', '19:00')
        self.assertFalse(valido)

        with app.app_context():
            lab = Laboratorio.query.filter_by(codigo='LAB-Q102').first()
            codigo_test = Reserva.generar_codigo()
            res1 = Reserva(
                codigo_reserva=codigo_test,
                laboratorio_id=lab.id,
                docente_nombre='Profesor PostgreSQL',
                docente_email='pg@quimica.edu',
                docente_departamento='Analítica',
                asignatura='Química Instrumental',
                cantidad_alumnos=15,
                titulo_practica='Espectroscopía',
                fecha='2026-11-20',
                hora_inicio='10:00',
                hora_fin='12:30',
                bitacora_plan='Plan espectroscopía'
            )
            db.session.add(res1)
            db.session.commit()

            # Mismo lab en horario solapado -> colisión
            colision, _ = hay_solapamiento(lab.id, '2026-11-20', '11:00', '13:00')
            self.assertTrue(colision)

            # Mismo lab en horario posterior -> permitido
            colision, _ = hay_solapamiento(lab.id, '2026-11-20', '12:30', '14:30')
            self.assertFalse(colision)

    def test_06_bitacora_de_cierre_post_sesion(self):
        """Verifica cierre de bitácora y reporte de novedades en PostgreSQL"""
        with app.app_context():
            res = Reserva.query.filter_by(estado='CONFIRMADA').first()
            self.assertIsNotNone(res)

            resp = self.app.post(f'/reserva/{res.codigo_reserva}/bitacora', data={
                'bitacora_cierre': 'Práctica completada con éxito en PostgreSQL. Curvas de calibración con r2 > 0.999.',
                'incidentes_novedades': 'Sin roturas de material.',
                'estado_devolucion': 'Conforme y Limpio',
                'responsable_cierre': 'Prof. Titular'
            }, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            res_act = db.session.get(Reserva, res.id)
            self.assertEqual(res_act.estado, 'COMPLETADA')
            self.assertIn('Curvas de calibración', res_act.bitacora_cierre)

if __name__ == '__main__':
    unittest.main()
