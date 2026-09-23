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
        """Verifica cierre de bitácora y reporte de novedades por el docente titular o admin"""
        with app.app_context():
            res = Reserva.query.filter_by(estado='CONFIRMADA').first()
            self.assertIsNotNone(res)

            # Iniciar sesión como admin o dueño de la reserva
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})

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

    def test_07_aislamiento_cancelacion_reservas(self):
        """Asegura que un docente NO pueda cancelar la reserva de otro docente, pero sí la suya y el admin cualquiera"""
        with app.app_context():
            d1 = Usuario.query.filter_by(username='docente1').first()
            d2 = Usuario.query.filter_by(username='docente2').first()
            lab = Laboratorio.query.first()
            self.assertIsNotNone(d1)
            self.assertIsNotNone(d2)

            # Crear reservas explícitas para la prueba
            res_d1 = Reserva(
                codigo_reserva=Reserva.generar_codigo(),
                laboratorio_id=lab.id,
                usuario_id=d1.id,
                docente_nombre=d1.nombre_completo,
                docente_email=d1.email,
                docente_departamento=d1.departamento,
                asignatura='Química Orgánica Experimental',
                cantidad_alumnos=10,
                titulo_practica='Aislamiento Test D1',
                fecha='2026-12-01',
                hora_inicio='09:00',
                hora_fin='11:00',
                estado='CONFIRMADA',
                bitacora_plan='Plan D1'
            )
            res_d2 = Reserva(
                codigo_reserva=Reserva.generar_codigo(),
                laboratorio_id=lab.id,
                usuario_id=d2.id,
                docente_nombre=d2.nombre_completo,
                docente_email=d2.email,
                docente_departamento=d2.departamento,
                asignatura='Química Analítica Experimental',
                cantidad_alumnos=12,
                titulo_practica='Aislamiento Test D2',
                fecha='2026-12-01',
                hora_inicio='14:00',
                hora_fin='16:00',
                estado='CONFIRMADA',
                bitacora_plan='Plan D2'
            )
            db.session.add_all([res_d1, res_d2])
            db.session.commit()

            # Caso 1: docente1 intenta cancelar la reserva de docente2 -> RECHAZADO
            self.app.get('/logout')
            self.app.post('/login', data={'username': 'docente1', 'password': 'docente123'})
            resp_bloqueo = self.app.post(f'/reserva/{res_d2.codigo_reserva}/cancelar', follow_redirects=True)
            self.assertEqual(resp_bloqueo.status_code, 200)
            self.assertIn('No puedes cancelar una reserva perteneciente a otro docente', resp_bloqueo.text)

            # Verificar en BD que la reserva de docente2 sigue CONFIRMADA
            res_d2_db = db.session.get(Reserva, res_d2.id)
            self.assertEqual(res_d2_db.estado, 'CONFIRMADA')

            # Caso 2: docente1 cancela SU PROPIA reserva -> PERMITIDO
            resp_propia = self.app.post(f'/reserva/{res_d1.codigo_reserva}/cancelar', follow_redirects=True)
            self.assertEqual(resp_propia.status_code, 200)
            self.assertIn('ha sido cancelada correctamente', resp_propia.text)

            res_d1_db = db.session.get(Reserva, res_d1.id)
            self.assertEqual(res_d1_db.estado, 'CANCELADA')

            # Caso 3: Admin puede cancelar cualquier reserva (ej. la de docente2) -> PERMITIDO
            self.app.get('/logout')
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
            resp_admin = self.app.post(f'/reserva/{res_d2.codigo_reserva}/cancelar', follow_redirects=True)
            self.assertEqual(resp_admin.status_code, 200)
            self.assertIn('ha sido cancelada correctamente', resp_admin.text)

            res_d2_db_post = db.session.get(Reserva, res_d2.id)
            self.assertEqual(res_d2_db_post.estado, 'CANCELADA')

    def test_08_crud_usuarios_admin(self):
        """Verifica control de acceso y ciclo de CRUD de Usuarios en el Panel Administrativo"""
        with app.app_context():
            # 1. Un docente regular NO puede acceder al CRUD de usuarios
            self.app.get('/logout')
            self.app.post('/login', data={'username': 'docente1', 'password': 'docente123'})
            resp_unauth = self.app.get('/admin/usuarios', follow_redirects=True)
            self.assertIn('Se requieren permisos de Administrador', resp_unauth.text)

            # 2. El Admin accede exitosamente
            self.app.get('/logout')
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
            resp_admin = self.app.get('/admin/usuarios')
            self.assertEqual(resp_admin.status_code, 200)

            # 3. Create: Crear nuevo usuario docente
            resp_crear = self.app.post('/admin/usuarios/nuevo', data={
                'username': 'prof_carolina',
                'email': 'c.soto@quimica.edu',
                'password': 'password123',
                'nombre_completo': 'Dra. Carolina Soto',
                'departamento': 'Bioquímica Clínica',
                'rol': 'docente',
                'activo': '1'
            }, follow_redirects=True)
            self.assertEqual(resp_crear.status_code, 200)
            self.assertIn('creado exitosamente', resp_crear.text)

            user_creado = Usuario.query.filter_by(username='prof_carolina').first()
            self.assertIsNotNone(user_creado)
            self.assertEqual(user_creado.email, 'c.soto@quimica.edu')
            self.assertTrue(user_creado.check_password('password123'))

            # 4. Update: Modificar usuario
            resp_edit = self.app.post(f'/admin/usuarios/{user_creado.id}/editar', data={
                'username': 'prof_carolina',
                'email': 'c.soto.mod@quimica.edu',
                'password': 'nuevaclave456',
                'nombre_completo': 'Dra. Carolina Soto Vidal',
                'departamento': 'Bioquímica y Biología Molecular',
                'rol': 'docente',
                'activo': '1'
            }, follow_redirects=True)
            self.assertEqual(resp_edit.status_code, 200)

            user_act = db.session.get(Usuario, user_creado.id)
            self.assertEqual(user_act.nombre_completo, 'Dra. Carolina Soto Vidal')
            self.assertTrue(user_act.check_password('nuevaclave456'))

            # 5. Toggle activo/inactivo
            resp_toggle = self.app.post(f'/admin/usuarios/{user_act.id}/toggle', follow_redirects=True)
            self.assertEqual(resp_toggle.status_code, 200)
            self.assertIn('desactivado', resp_toggle.text)

            user_inactivo = db.session.get(Usuario, user_act.id)
            self.assertFalse(user_inactivo.activo)

            # Usuario inactivo no puede iniciar sesión
            self.app.get('/logout')
            resp_login_inactivo = self.app.post('/login', data={'username': 'prof_carolina', 'password': 'nuevaclave456'}, follow_redirects=True)
            self.assertIn('Tu cuenta se encuentra inactiva', resp_login_inactivo.text)

            # 6. Delete: Eliminar usuario
            self.app.post('/login', data={'username': 'admin', 'password': 'admin123'})
            resp_del = self.app.post(f'/admin/usuarios/{user_inactivo.id}/eliminar', follow_redirects=True)
            self.assertEqual(resp_del.status_code, 200)
            self.assertIn('eliminado exitosamente', resp_del.text)

            self.assertIsNone(db.session.get(Usuario, user_inactivo.id))

    def test_09_aislamiento_mis_reservas(self):
        """Verifica que /mis-reservas muestre únicamente las reservas pertenecientes al docente autenticado"""
        with app.app_context():
            d1 = Usuario.query.filter_by(username='docente1').first()
            d2 = Usuario.query.filter_by(username='docente2').first()

            # Iniciar sesión como docente1
            self.app.get('/logout')
            self.app.post('/login', data={'username': 'docente1', 'password': 'docente123'})
            resp = self.app.get('/mis-reservas')
            self.assertEqual(resp.status_code, 200)

            # docente1 debe ver sus reservas o datos pero no los códigos exclusivos de docente2
            res_d2 = Reserva.query.filter_by(usuario_id=d2.id).first()
            if res_d2:
                self.assertNotIn(res_d2.codigo_reserva, resp.text)

if __name__ == '__main__':
    unittest.main()
