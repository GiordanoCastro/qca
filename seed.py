from datetime import datetime, date, timedelta
from models import db, Usuario, Laboratorio, ElementoLaboratorio, Reserva

def seed_database(app, reset=False):
    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()

        # Si ya existe información y no es reset, salir para evitar duplicados
        if not reset and (Usuario.query.count() > 0 and Laboratorio.query.count() > 0):
            print("La base de datos ya cuenta con datos iniciales.")
            return

        # 0. Usuario Administrador del Sistema
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                email='admin@quimica.edu',
                nombre_completo='Administrador General de Laboratorios',
                rol='admin',
                activo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # 1. Laboratorio de Química Orgánica y Síntesis
        lab_organica = Laboratorio(
            codigo='LAB-Q101',
            nombre='Laboratorio de Química Orgánica y Síntesis',
            descripcion='Laboratorio equipado para síntesis orgánica, destilación fraccionada, reflujo y extracción con solventes volátiles. Cuenta con sistemas de extracción de vapores y gases.',
            ubicacion='Edificio de Ciencias Químicas - 2do Piso, Ala Norte',
            capacidad_alumnos=24,
            color='emerald',
            normas_seguridad='Uso obligatorio de gafas de seguridad herméticas, bata 100% algodón, guantes de nitrilo. Prohibido manipular solventes clorados o inflamables fuera de las campanas.'
        )

        # 2. Laboratorio de Química Analítica e Instrumental
        lab_analitica = Laboratorio(
            codigo='LAB-Q102',
            nombre='Laboratorio de Química Analítica e Instrumental',
            descripcion='Espacio climatizado de alta precisión para volumetría, gravimetría, espectrofotometría y análisis electroquímico.',
            ubicacion='Edificio de Ciencias Químicas - 1er Piso, Sala 104',
            capacidad_alumnos=20,
            color='blue',
            normas_seguridad='Calibrar instrumentos antes de iniciar. No mover balanzas analíticas de sus mesas antivibratorias de granito. Manejo cuidadoso de celdas de cuarzo.'
        )

        # 3. Laboratorio de Química General e Inorgánica
        lab_general = Laboratorio(
            codigo='LAB-Q103',
            nombre='Laboratorio de Química General e Inorgánica',
            descripcion='Laboratorio amplio para prácticas fundamentales, cinética química, estequiometría, reacciones ácido-base y precipitación inorgánica.',
            ubicacion='Edificio de Ciencias Químicas - Planta Baja, Sala 02',
            capacidad_alumnos=30,
            color='amber',
            normas_seguridad='Revisar conexiones de mangueras de gas antes de encender mecheros. Cabello recogido indispensable. Uso de pinzas de madera y guantes térmicos para crisoles.'
        )

        # 4. Laboratorio de Fisicoquímica y Termodinámica
        lab_fisicoquimica = Laboratorio(
            codigo='LAB-Q104',
            nombre='Laboratorio de Fisicoquímica y Termodinámica',
            descripcion='Equipamiento para determinación de propiedades termodinámicas, equilibrio de fases, refractometría, polarimetría y cinética físico-química.',
            ubicacion='Edificio de Ciencias Químicas - 3er Piso, Sala 301',
            capacidad_alumnos=18,
            color='purple',
            normas_seguridad='Control estricto de temperatura en baños termostáticos. Cuidado con líquidos manométricos y sustancias reactivas a alta temperatura.'
        )

        db.session.add_all([lab_organica, lab_analitica, lab_general, lab_fisicoquimica])
        db.session.flush()

        # Elementos para Química Orgánica
        elem_org = [
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Campana de Extracción de Gases y Vapores', categoria='Extracción y Seguridad', cantidad_disponible=4, descripcion='Campana de flujo laminar con guillotina de vidrio templado y extracción forzada'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Rotavapor Buchi con Baño Calefactor', categoria='Equipos Especiales', cantidad_disponible=2, descripcion='Evaporador rotatorio con refrigerante en espiral y bomba de vacío diafragma'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Plancha Calefactora con Agitación Magnética Digital', categoria='Calefacción y Agitación', cantidad_disponible=8, descripcion='Temperatura hasta 350°C y agitación hasta 1500 rpm'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Manta Calefactora para Balón de 250/500 mL', categoria='Calefacción y Agitación', cantidad_disponible=4, descripcion='Controlador de potencia analógico para ebullición suave'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Kit de Vidriería Esmerilada 24/40 (Balones, Refrigerantes Liebig/Allihn)', categoria='Vidriería y Reactores', cantidad_disponible=12, descripcion='Set completo para reflujo, destilación simple y destilación fraccionada'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Embudo de Decantación / Separación de 250 mL con Teflón', categoria='Vidriería y Reactores', cantidad_disponible=10, descripcion='Llave de paso PTFE estanca a solventes orgánicos'),
            ElementoLaboratorio(laboratorio_id=lab_organica.id, nombre='Línea de Vacío y Trampa Fría', categoria='Equipos Especiales', cantidad_disponible=2, descripcion='Para filtración rápida en embudo Büchner con Kitasato')
        ]

        # Elementos para Química Analítica
        elem_ana = [
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='Balanza Analítica Ohaus (Sensibilidad 0.0001 g)', categoria='Instrumental de Medición', cantidad_disponible=4, descripcion='Con cámara de pesada antiviento y calibración interna automática'),
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='Espectrofotómetro UV-Visible Shimadzu UV-1800', categoria='Equipos Especiales', cantidad_disponible=2, descripcion='Rango 190 a 1100 nm, con juego de cubetas de cuarzo y vidrio óptico'),
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='pH-metro de Mesa con Compensación Automática de Temperatura', categoria='Instrumental de Medición', cantidad_disponible=6, descripcion='Electrodo combinado de pH y soluciones buffer pH 4.00, 7.00 y 10.00'),
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='Conductímetro Digital de Precisión', categoria='Instrumental de Medición', cantidad_disponible=3, descripcion='Celda de conductividad con constante k=1.0 para aguas y soluciones salinas'),
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='Centrífuga Clínica para Tubos de 15 mL', categoria='Equipos Especiales', cantidad_disponible=2, descripcion='Rotor angular para 8 tubos, velocidad hasta 4000 rpm con timer'),
            ElementoLaboratorio(laboratorio_id=lab_analitica.id, nombre='Buretas Digitales de Titulación Titrette 50 mL', categoria='Vidriería y Reactores', cantidad_disponible=8, descripcion='Dispensador de alta resolución con frasco ámbar de reserva')
        ]

        # Elementos para Química General
        elem_gen = [
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Mecheros Bunsen con Válvula de Aguja y Manguera Reforzada', categoria='Calefacción y Agitación', cantidad_disponible=15, descripcion='Incluye trípode de acero y tela metálica con disco cerámico'),
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Campana de Extracción de Seguridad General', categoria='Extracción y Seguridad', cantidad_disponible=1, descripcion='Para manipulación de ácidos concentrados (HCl, HNO3, H2SO4)'),
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Balanza Granataria Digital 0.01 g', categoria='Instrumental de Medición', cantidad_disponible=6, descripcion='Capacidad hasta 600 g para preparación de soluciones'),
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Set de Buretas de Vidrio Borosilicato de 50 mL con Soporte Universal', categoria='Vidriería y Reactores', cantidad_disponible=12, descripcion='Pinzas dobles para bureta y soporte de hierro fundido'),
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Termómetros Químicos de Inmersión Parcial (-10 a 110°C)', categoria='Instrumental de Medición', cantidad_disponible=15, descripcion='Sin mercurio, líquido orgánico de alta visibilidad'),
            ElementoLaboratorio(laboratorio_id=lab_general.id, nombre='Baño María Regulado con Termostato', categoria='Calefacción y Agitación', cantidad_disponible=2, descripcion='Tina de acero inoxidable con aros concéntricos reductores')
        ]

        # Elementos para Fisicoquímica
        elem_fis = [
            ElementoLaboratorio(laboratorio_id=lab_fisicoquimica.id, nombre='Calorímetro Adiabático con Termómetro Digital de Alta Resolución', categoria='Equipos Especiales', cantidad_disponible=2, descripcion='Para calores de neutralización, combustión y disolución'),
            ElementoLaboratorio(laboratorio_id=lab_fisicoquimica.id, nombre='Refractómetro de Abbe con Control Termostático', categoria='Instrumental de Medición', cantidad_disponible=2, descripcion='Medición de índice de refracción nD con precisión de 4 decimales y prismas termorregulables'),
            ElementoLaboratorio(laboratorio_id=lab_fisicoquimica.id, nombre='Polarímetro Circular con Lámpara de Sodio', categoria='Instrumental de Medición', cantidad_disponible=2, descripcion='Para cinética de inversión de sacarosa y actividad óptica'),
            ElementoLaboratorio(laboratorio_id=lab_fisicoquimica.id, nombre='Viscosímetros de Ostwald y Ubbelohde con Baño Termostático', categoria='Equipos Especiales', cantidad_disponible=4, descripcion='Determinación de viscosidad relativa y pesos moleculares poliméricos'),
            ElementoLaboratorio(laboratorio_id=lab_fisicoquimica.id, nombre='Potenciómetro / Titulador Potenciométrico', categoria='Instrumental de Medición', cantidad_disponible=2, descripcion='Electrodo de referencia Ag/AgCl y electrodo indicador')
        ]

        db.session.add_all(elem_org + elem_ana + elem_gen + elem_fis)
        db.session.commit()

        # Crear algunas reservas iniciales con bitácoras
        hoy = date.today().strftime('%Y-%m-%d')
        manana = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        ayer = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 1. Reserva ayer (COMPLETADA con Bitácora de Cierre)
        res_ayer = Reserva(
            codigo_reserva='LQ-ORG-4401',
            laboratorio_id=lab_organica.id,
            docente_nombre='Dra. Marcela Fuenzalida',
            docente_email='m.fuenzalida@quimica.edu',
            docente_departamento='Departamento de Química Orgánica',
            asignatura='Química Orgánica II (QMC-204)',
            cantidad_alumnos=20,
            titulo_practica='Síntesis de Ácido Acetilsalicílico (Aspirina) y Recristalización',
            fecha=ayer,
            hora_inicio='09:00',
            hora_fin='12:30',
            estado='COMPLETADA',
            bitacora_plan='Síntesis a partir de ácido salicílico y anhídrido acético con ácido fosfórico catalizador a 60°C. Posterior filtración al vacío en embudo Büchner y recristalización en mezcla etanol/agua.',
            reactivos_utilizados='Ácido salicílico (50 g), Anhídrido acético (80 mL), Ácido fosfórico 85% (10 mL), Etanol 95% (200 mL), Cloruro férrico 1% (revelador).',
            observaciones_seguridad='Trabajo exclusivo en campanas de extracción por vapores de anhídrido acético. Neutralización de aguas madres con bicarbonato sódico antes de verter a bidón de residuos clorados/ácidos.',
            bitacora_cierre='La práctica finalizó a las 12:15 hrs. Los 10 grupos obtuvieron el producto crudo con rendimientos entre 68% y 82%. Se verificó pureza por punto de fusión y prueba de FeCl3 negativa.',
            incidentes_novedades='Sin accidentes personales. Un matraz Kitasato de 250 mL presentó una pequeña fisura en el tubo lateral de vacío y fue retirado y entregado al pañol para su reposición.',
            estado_devolucion='Conforme con observación de material',
            responsable_cierre='Dra. Marcela Fuenzalida / Técnico Carlos Morales',
            fecha_cierre_bitacora=datetime.now() - timedelta(days=1)
        )
        db.session.add(res_ayer)
        res_ayer.elementos.append(elem_org[0])
        res_ayer.elementos.append(elem_org[2])
        res_ayer.elementos.append(elem_org[4])
        res_ayer.elementos.append(elem_org[6])

        # 2. Reserva hoy (CONFIRMADA - Práctica en la mañana)
        res_hoy = Reserva(
            codigo_reserva='LQ-ANA-7720',
            laboratorio_id=lab_analitica.id,
            docente_nombre='Prof. Roberto Valenzuela',
            docente_email='r.valenzuela@quimica.edu',
            docente_departamento='Departamento de Química Analítica',
            asignatura='Análisis Instrumental Cuantitativo (QMC-310)',
            cantidad_alumnos=16,
            titulo_practica='Determinación Espectrofotométrica de Hierro en Muestras de Agua Potable por Formación del Complejo de Fenantrolina',
            fecha=hoy,
            hora_inicio='10:00',
            hora_fin='13:00',
            estado='CONFIRMADA',
            bitacora_plan='Construcción de curva de calibración de Fe(II) a 510 nm con ortofenantrolina y reducción con clorhidrato de hidroxilamina. Lectura por duplicado de muestras problema.',
            reactivos_utilizados='Solución estándar Fe 100 ppm, 1,10-fenantrolina 0.1%, Clorhidrato de hidroxilamina 10%, Buffer acetato de sodio pH 4.5.',
            observaciones_seguridad='Uso estricto de celdas de cuarzo limpias con papel lente. No tocar superficies ópticas con los dedos.'
        )
        db.session.add(res_hoy)
        res_hoy.elementos.append(elem_ana[0])
        res_hoy.elementos.append(elem_ana[1])
        res_hoy.elementos.append(elem_ana[2])

        # 3. Reserva mañana (CONFIRMADA - Práctica de la tarde)
        res_manana = Reserva(
            codigo_reserva='LQ-GEN-8914',
            laboratorio_id=lab_general.id,
            docente_nombre='Dra. Elena Santis',
            docente_email='e.santis@quimica.edu',
            docente_departamento='Departamento de Ciencias Básicas',
            asignatura='Química General (BIO-101)',
            cantidad_alumnos=28,
            titulo_practica='Leyes de los Gases y Determinación del Volumen Molar de Hidrógeno',
            fecha=manana,
            hora_inicio='14:30',
            hora_fin='17:00',
            estado='CONFIRMADA',
            bitacora_plan='Reacción de cinta de magnesio con ácido clorhídrico concentrado en tubo eudiómetro recogiendo gas sobre agua a presión y temperatura ambiente.',
            reactivos_utilizados='Cinta de magnesio pulida con lija (50 cm), Ácido clorhídrico 6 M (150 mL), Agua destilada.',
            observaciones_seguridad='Manipulación de ácido clorhídrico 6 M bajo supervisión de ayudantes. Gafas de protección obligatorias en todo momento.'
        )
        db.session.add(res_manana)
        res_manana.elementos.append(elem_gen[0])
        res_manana.elementos.append(elem_gen[1])
        res_manana.elementos.append(elem_gen[2])
        res_manana.elementos.append(elem_gen[3])

        db.session.commit()
        print("Base de datos inicializada exitosamente.")

if __name__ == '__main__':
    from app import app
    seed_database(app, reset=True)
