from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, jsonify, current_app
formaciones_bp = Blueprint('formaciones_bp', __name__)

from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.models.empresa import Empresa
from mi_plataforma_formacion_app.models.formador import Formador
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.examen_alumno import ExamenAlumno
from mi_plataforma_formacion_app.models.examen_modelo import ExamenModelo
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from mi_plataforma_formacion_app.models.comercial import Comercial
from mi_plataforma_formacion_app.extensions import db
from .forms import FormacionForm
from mi_plataforma_formacion_app.blueprints.alumnos.forms import AlumnoForm
from datetime import date, datetime
import io, os, json, unicodedata, re, tempfile

@formaciones_bp.route('/formaciones/api/contar_formaciones_dia', endpoint='contar_formaciones_dia')
def contar_formaciones_dia():
    fecha = request.args.get('fecha', '').strip()
    if not fecha:
        return jsonify({'total': 0})
    try:
        fecha_date = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'total': 0})
    total = Formacion.query.filter_by(fecha1=fecha_date).count()
    return jsonify({'total': total})
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa


from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch

# -------- FUNCION PARA NORMALIZAR --------
def normaliza_nombre_archivo(txt):
    if not isinstance(txt, str):
        txt = ""
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[^a-zA-Z0-9\s]', '_', txt)
    txt = txt.lower().strip() 
    txt = re.sub(r'\s+', '_', txt) 
    txt = re.sub(r'_{2,}', '_', txt)
    txt = txt.strip('_')
    return txt
# -----------------------------------------

def recalcular_referencias(fecha):
    formaciones_dia = Formacion.query.filter_by(fecha1=fecha).order_by(Formacion.hora_inicio1).all()
    for idx, formacion in enumerate(formaciones_dia, start=1):
        fecha_str = fecha.strftime('%d%m%Y')
        formacion.referencia = f"{fecha_str}{idx}"
    db.session.commit()



# Endpoint para autocompletar empresas
@formaciones_bp.route('/api/buscar_empresas')
def buscar_empresas():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    empresas = Empresa.query.filter(Empresa.nombre.ilike(f'%{q}%')).limit(10).all()
    return jsonify([{'id': e.id, 'nombre': e.nombre} for e in empresas])

@formaciones_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_formacion():
    form = FormacionForm()
    form.tipo_curso_id.choices = [(0, '--- Selecciona tipo de curso ---')] + [(tc.id, tc.nombre) for tc in TipoCurso.query.order_by('nombre').all()]
    form.empresa_id.choices = [(0, '--- Selecciona cliente ---')] + [(e.id, e.nombre) for e in Empresa.query.order_by('nombre').all()]
    form.formador_id.choices = [(0, '--- Selecciona formador ---')] + [(f.id, f.nombre) for f in Formador.query.order_by('nombre').all()]

    referencia = ""
    comerciales = Comercial.query.order_by(Comercial.nombre).all()
    if form.validate_on_submit():
        nueva_formacion = Formacion(
            # La referencia la ponemos provisional, se recalcula después
            referencia="TEMP",
            fecha1=form.fecha1.data,
            hora_inicio1=form.hora_inicio1.data,
            hora_fin1=form.hora_fin1.data,
            dos_ediciones=form.dos_ediciones.data,
            fecha2=form.fecha2.data,
            hora_inicio2=form.hora_inicio2.data,
            hora_fin2=form.hora_fin2.data,
            fundae=form.fundae.data,
            observaciones=form.observaciones.data,
            tipo_curso_id=form.tipo_curso_id.data,
            empresa_id=form.empresa_id.data,
            formador_id=form.formador_id.data,
            direccion_aula=form.direccion_aula.data
        )
        db.session.add(nueva_formacion)
        db.session.commit()
        # Recalcula TODAS las referencias de ese día, ya ordenadas por hora
        recalcular_referencias(nueva_formacion.fecha1)
        # Recarga el objeto por si quieres mostrar la referencia real en el mensaje flash
        db.session.refresh(nueva_formacion)
        flash(f'Formación creada exitosamente. Referencia: {nueva_formacion.referencia}', 'success')
        return redirect(url_for('formaciones_bp.gestion_formaciones'))

    return render_template('formaciones/nueva_formacion.html', form=form, referencia=referencia, comerciales=comerciales)

@formaciones_bp.route('/editar/<int:formacion_id>', methods=['GET', 'POST'])
def editar_formacion(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    form = FormacionForm(obj=formacion)
    form.tipo_curso_id.choices = [(0, '--- Selecciona tipo de curso ---')] + [(tc.id, tc.nombre) for tc in TipoCurso.query.order_by('nombre').all()]
    form.empresa_id.choices = [(0, '--- Selecciona cliente ---')] + [(e.id, e.nombre) for e in Empresa.query.order_by('nombre').all()]
    form.formador_id.choices = [(0, '--- Selecciona formador ---')] + [(f.id, f.nombre) for f in Formador.query.order_by('nombre').all()]

    if form.validate_on_submit():
        fecha_anterior = formacion.fecha1
        hora_anterior = formacion.hora_inicio1
        form.populate_obj(formacion)
        fecha_cambiada = formacion.fecha1 != fecha_anterior
        hora_cambiada = formacion.hora_inicio1 != hora_anterior
        db.session.commit()
        # Recalcula referencias si cambia la fecha o la hora
        if fecha_cambiada:
            recalcular_referencias(fecha_anterior)      # Día anterior
            recalcular_referencias(formacion.fecha1)     # Nuevo día
        elif hora_cambiada:
            recalcular_referencias(formacion.fecha1)     # Mismo día, nueva hora
        flash('Formación actualizada', 'success')
        return redirect(url_for('formaciones_bp.gestion_formaciones'))
    return render_template('formaciones/editar_formacion.html', form=form, referencia=formacion.referencia)

@formaciones_bp.route('/')
def gestion_formaciones():
    empresa_id = request.args.get('empresa_id')
    tipo_curso_id = request.args.get('tipo_curso_id')
    comercial_id = request.args.get('comercial_id')
    anio = request.args.get('anio')

    empresas = Empresa.query.order_by(Empresa.nombre).all()
    tipos_curso = TipoCurso.query.order_by(TipoCurso.nombre).all()
    comerciales = []
    lista_anios = sorted({f.fecha1.year for f in Formacion.query if f.fecha1}, reverse=True)

    query = Formacion.query
    if empresa_id:
        query = query.filter(Formacion.empresa_id == empresa_id)
    if tipo_curso_id:
        query = query.filter(Formacion.tipo_curso_id == tipo_curso_id)
    if anio:
        query = query.filter(db.extract('year', Formacion.fecha1) == int(anio))

    ver_cerradas = request.args.get('cerradas', '0') == '1'
    hoy = date.today()
    if ver_cerradas:
        query = query.filter(Formacion.cerrada == True)
    else:
        query = query.filter(Formacion.cerrada == False)

    formaciones = query.order_by(Formacion.fecha1.asc(), Formacion.hora_inicio1.asc()).all()
    return render_template(
        'formaciones/gestion_formaciones.html',
        formaciones=formaciones,
        ver_cerradas=ver_cerradas,
        hoy=hoy,
        empresas=empresas,
        tipos_curso=tipos_curso,
        comerciales=comerciales,
        lista_anios=lista_anios
    )

@formaciones_bp.route('/alumnos/<int:formacion_id>', methods=['GET'])
def alumnos_formacion(formacion_id):
    from mi_plataforma_formacion_app.models import ExamenAlumno  # Si no lo tienes ya importado arriba
    formacion = Formacion.query.get_or_404(formacion_id)
    alumnos_info = []

    form_nuevo_alumno = AlumnoForm()
    form_nuevo_alumno.empresa_id.choices = [(0, 'Sin empresa')] + [(e.id, e.nombre) for e in Empresa.query.order_by('nombre').all()]
    if form_nuevo_alumno.empresa_id.data in (None, '', ' '):
        form_nuevo_alumno.empresa_id.data = 0

    for rel in formacion.alumno_formaciones:
        alumno = rel.alumno

        # Busca el examen del alumno para esta formación
        examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first()
        examen_alumno_id = examen_alumno.id if examen_alumno else None
        # Esta URL es la correcta para tu sistema (va al blueprint de alumnos, ver_examen_alumno)
        url_examen = url_for('alumnos_bp.ver_examen_alumno', formacion_id=formacion.id, alumno_id=alumno.id)
        # Si usas diplomas, mantenlo igual que ya lo tienes
        nombre_archivo_diploma = f"diploma_{alumno.nombre.replace(' ', '_').lower()}.pdf"
        from mi_plataforma_formacion_app.blueprints.formaciones.routes import normaliza_nombre_archivo
        empresa_nombre_normalizada = normaliza_nombre_archivo(formacion.empresa.nombre)
        fecha_formacion_str = formacion.fecha1.strftime("%Y-%m-%d")
        ruta_pdf = f"diplomas/{empresa_nombre_normalizada}/{fecha_formacion_str}/{nombre_archivo_diploma}"

        alumnos_info.append({
            'rel': rel,
            'alumno': alumno,
            'examen_alumno_id': examen_alumno_id,
            'url_examen': url_examen,
            'ruta_pdf': ruta_pdf,
        })

    return render_template(
        'formaciones/alumnos_formacion.html',
        formacion=formacion,
        alumnos_info=alumnos_info,
        form_nuevo_alumno=form_nuevo_alumno
    )

@formaciones_bp.route('/agregar_alumno_existente/<int:formacion_id>', methods=['POST'])
def agregar_alumno_existente(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    alumno_id = request.form.get('alumno_id')

    if not alumno_id:
        flash('Por favor, selecciona un alumno.', 'warning')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion_id))

    alumno = Alumno.query.get_or_404(alumno_id)

    if AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion.id).first():
        flash(f'El alumno {alumno.nombre} ya está inscrito en esta formación.', 'warning')
    else:
        relacion = AlumnoFormacion(alumno=alumno, formacion=formacion)
        db.session.add(relacion)
        db.session.commit()
        flash(f'Alumno {alumno.nombre} añadido a la formación.', 'success')

    return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion_id))

@formaciones_bp.route('/agregar_alumno_nuevo/<int:formacion_id>', methods=['POST'])
def agregar_alumno_nuevo(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    form = AlumnoForm()
    form.empresa_id.choices = [(0, 'Sin empresa')] + [(e.id, e.nombre) for e in Empresa.query.order_by('nombre').all()]
    if form.empresa_id.data in (None, '', ' '):
        form.empresa_id.data = 0

    if form.validate_on_submit():
        nuevo_alumno = Alumno(
            nombre=form.nombre.data,
            dni=form.dni.data,
            email=form.email.data,
            telefono=form.telefono.data,
            interesado_mas_cursos=form.interesado_mas_cursos.data,
            empresa_id=form.empresa_id.data if form.empresa_id.data != 0 else None
        )
        db.session.add(nuevo_alumno)
        db.session.commit()

        relacion = AlumnoFormacion(alumno=nuevo_alumno, formacion=formacion)
        db.session.add(relacion)
        db.session.commit()

        flash(f'Nuevo alumno {nuevo_alumno.nombre} creado y añadido a la formación.', 'success')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion_id))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Error en {getattr(form, field).label.text}: {error}", 'warning')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion_id))

@formaciones_bp.route('/borrar_alumno_formacion/<int:alumno_formacion_id>', methods=['POST'])
def borrar_alumno_formacion(alumno_formacion_id):
    relacion = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    formacion_id = relacion.formacion_id

    examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=alumno_formacion_id).first()
    if examen_alumno:
        db.session.delete(examen_alumno)

    db.session.delete(relacion)
    db.session.commit()
    flash('Alumno eliminado de la formación correctamente.', 'success')
    return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion_id))

@formaciones_bp.route('/cerrar/<int:id>', methods=['POST'])
def cerrar_formacion(id):
    formacion = Formacion.query.get_or_404(id)
    formacion.cerrada = True
    db.session.commit()
    flash('Formación marcada como cerrada.', 'success')
    return redirect(url_for('formaciones_bp.gestion_formaciones'))

@formaciones_bp.route('/reabrir/<int:id>', methods=['POST'])
def reabrir_formacion(id):
    formacion = Formacion.query.get_or_404(id)
    formacion.cerrada = False
    db.session.commit()
    flash('Formación marcada como abierta.', 'success')
    return redirect(url_for('formaciones_bp.gestion_formaciones'))

@formaciones_bp.route('/realizar_examen/<int:alumno_formacion_id>', methods=['GET', 'POST'])
def realizar_examen(alumno_formacion_id):
    from mi_plataforma_formacion_app.utils.diplomas import crear_y_guardar_diploma

    alumno_formacion = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    formacion = alumno_formacion.formacion
    tipo_curso = formacion.tipo_curso
    examen_modelo = tipo_curso.examen_modelo

    if not examen_modelo or not examen_modelo.preguntas:
        flash('No hay modelo de examen tipo test asociado a este curso.', 'warning')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion.id))

    preguntas_test = []
    for pregunta in examen_modelo.preguntas:
        preguntas_test.append({
            'id': pregunta.id,
            'pregunta': pregunta.texto,
            'opciones': [resp.texto for resp in pregunta.respuestas],
            'respuesta_correcta': next((resp.texto for resp in pregunta.respuestas if resp.es_correcta), None)
        })

    examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=alumno_formacion_id).first()
    respuestas_previas = json.loads(examen_alumno.respuestas_json) if examen_alumno and examen_alumno.respuestas_json else {}

    if request.method == 'POST':
        respuestas = {}
        correctas = 0
        for pregunta in preguntas_test:
            respuesta_dada = request.form.get(f'pregunta_{pregunta["id"]}')
            respuestas[str(pregunta['id'])] = respuesta_dada
            if respuesta_dada == pregunta['respuesta_correcta']:
                correctas += 1
        nota = round((correctas / len(preguntas_test)) * 10, 2) if preguntas_test else 0

        if examen_alumno:
            examen_alumno.respuestas_json = json.dumps(respuestas)
            examen_alumno.nota_automatica = nota
        else:
            examen_alumno = ExamenAlumno(
                alumno_formacion_id=alumno_formacion_id,
                respuestas_json=json.dumps(respuestas),
                nota_automatica=nota
            )
            db.session.add(examen_alumno)

        # Marcar aprobado o no
        if nota >= 5:
            alumno_formacion.aprobado = True
        else:
            alumno_formacion.aprobado = False

        db.session.commit()

        # ✅ Generar y guardar el diploma automáticamente
        crear_y_guardar_diploma(alumno_formacion.alumno, alumno_formacion.formacion)

        flash('Examen guardado correctamente.', 'success')
        return redirect(url_for('formaciones_bp.ver_examen_alumno', examen_alumno_id=examen_alumno.id))

    return render_template('formaciones/realizar_examen.html',
        alumno_formacion=alumno_formacion,
        formacion=formacion,
        preguntas=preguntas_test,
        respuestas_previas=respuestas_previas,
        examen_alumno=examen_alumno)

@formaciones_bp.route('/ver_examen_alumno/<int:examen_alumno_id>')
def ver_examen_alumno(examen_alumno_id):
    from mi_plataforma_formacion_app.models import Pregunta, Respuesta

    examen_alumno = ExamenAlumno.query.get_or_404(examen_alumno_id)
    alumno_formacion = examen_alumno.alumno_formacion
    formacion = alumno_formacion.formacion
    alumno = alumno_formacion.alumno
    tipo_curso = formacion.tipo_curso
    examen_modelo = tipo_curso.examen_modelo if tipo_curso else None

    if not examen_modelo:
        flash('No se encontró el modelo de examen.', 'warning')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion.id))

    import json

    def safe_str(val):
        try:
            return str(val) if val is not None else ""
        except Exception:
            return ""

    respuestas_dict = json.loads(examen_alumno.respuestas_json) if examen_alumno and examen_alumno.respuestas_json else {}
    correccion_preguntas = []
    aciertos = 0
    fallos = 0
    total_preguntas = 0

    preguntas_db = Pregunta.query.filter_by(examen_modelo_id=examen_modelo.id).all()
    for pregunta in preguntas_db:
        pregunta_id = str(pregunta.id)
        respuesta_dada_id = respuestas_dict.get(pregunta_id, None)
        respuesta_dada_texto = ""
        respuesta_correcta_texto = ""
        es_correcta = False

        # Compara por ID real de la respuesta seleccionada por el alumno
        respuestas_db = Respuesta.query.filter_by(pregunta_id=pregunta.id).all()
        for resp in respuestas_db:
            if str(resp.id) == str(respuesta_dada_id):
                respuesta_dada_texto = safe_str(resp.texto)
                if resp.es_correcta:
                    es_correcta = True
            if resp.es_correcta:
                respuesta_correcta_texto = safe_str(resp.texto)

        if not respuesta_dada_id:
            respuesta_dada_texto = "No respondido"

        correccion_preguntas.append({
            'pregunta': safe_str(pregunta.texto),
            'respuesta_dada': safe_str(respuesta_dada_texto),
            'respuesta_correcta': safe_str(respuesta_correcta_texto),
            'es_correcta': bool(es_correcta)
        })

        total_preguntas += 1
        if es_correcta:
            aciertos += 1
        else:
            fallos += 1

    nota_automatica = examen_alumno.nota_automatica

    return render_template(
        "formaciones/ver_examen_alumno.html",
        alumno=alumno,
        formacion=formacion,
        examen_alumno=examen_alumno,
        correccion_preguntas=correccion_preguntas,
        nota_automatica=nota_automatica,
        aciertos=aciertos,
        fallos=fallos,
        total_preguntas=total_preguntas,
    )

@formaciones_bp.route('/imprimir_examen_realizado/<int:examen_alumno_id>')
def imprimir_examen_realizado(examen_alumno_id):
    examen_alumno = ExamenAlumno.query.get_or_404(examen_alumno_id)
    alumno_formacion = examen_alumno.alumno_formacion
    alumno = alumno_formacion.alumno
    formacion = alumno_formacion.formacion
    tipo_curso = formacion.tipo_curso
    examen_modelo = formacion.tipo_curso.examen_modelo

    if not examen_modelo:
        flash('No se encontró el modelo de examen para este tipo de curso.', 'warning')
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion.id))

    preguntas_modelo = []
    if hasattr(examen_modelo, "preguntas") and examen_modelo.preguntas:
        preguntas_modelo = []
        for pregunta in examen_modelo.preguntas:
            preguntas_modelo.append({
                'pregunta': pregunta.texto,
                # Si tienes más campos, añádelos aquí
            })

    respuestas_alumno = json.loads(examen_alumno.respuestas_json) if examen_alumno and examen_alumno.respuestas_json else {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenteredTitle', alignment=TA_CENTER, fontSize=16, spaceAfter=14))
    if 'Normal' not in styles.byName:
        styles.add(ParagraphStyle(name='Normal', fontSize=10, spaceAfter=6))
    styles.add(ParagraphStyle(name='QuestionHeader', fontName='Helvetica-Bold', fontSize=11, spaceBefore=12, spaceAfter=6))

    story = []

    story.append(Paragraph("Examen Realizado del Alumno", styles['CenteredTitle']))
    story.append(Paragraph(f"<b>Formación:</b> {tipo_curso.nombre} - {formacion.empresa.nombre}", styles['Normal']))
    story.append(Paragraph(f"<b>Alumno:</b> {alumno.nombre} (DNI: {alumno.dni})", styles['Normal']))
    story.append(Paragraph(f"<b>Fecha del Examen:</b> {alumno_formacion.fecha_realizacion.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"<b>Nota Calculada (automática):</b> {examen_alumno.nota_automatica:.2f}", styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))

    for i, pregunta_data in enumerate(preguntas_modelo):
        pregunta_id = str(i + 1)
        respuesta_dada = respuestas_alumno.get(pregunta_id, 'No respondido')
        story.append(Paragraph(f"<b>Pregunta {pregunta_id}:</b> {pregunta_data['pregunta']}", styles['QuestionHeader']))
        story.append(Paragraph(f"<b>Tu respuesta:</b> {respuesta_dada}", styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=False, download_name=f"examen_alumno_{alumno.dni}_{formacion.id}.pdf", mimetype='application/pdf')

@formaciones_bp.route('/ficha_formacion/<int:formacion_id>')
def ficha_formacion(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    alumnos_rel = formacion.alumno_formaciones
    return render_template('formaciones/ficha_formacion.html', formacion=formacion, alumnos_rel=alumnos_rel)

    
from mi_plataforma_formacion_app.utils.pdf_fill import rellenar_pdf
from mi_plataforma_formacion_app.utils.diplomas import guardar_diploma_pdf
import logging
logger = logging.getLogger(__name__)
from flask import send_file
import tempfile

@formaciones_bp.route('/generar_diploma_pdf/<int:alumno_formacion_id>')
def generar_diploma_pdf(alumno_formacion_id):
    rel = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    alumno = rel.alumno
    formacion = rel.formacion
    curso = formacion.tipo_curso

    if not curso.plantilla_diploma:
        flash("Este curso no tiene una plantilla de diploma asignada.", "warning")
        return redirect(url_for('formaciones_bp.gestion_formaciones'))

    ruta_relativa = curso.plantilla_diploma.ruta_pdf
    if not ruta_relativa:
        flash("La plantilla asignada no tiene archivo PDF asociado.", "danger")
        return redirect(url_for('formaciones_bp.gestion_formaciones'))

    ruta_absoluta_plantilla = os.path.join(current_app.static_folder, ruta_relativa)

    if not os.path.exists(ruta_absoluta_plantilla):
        flash("La plantilla PDF no existe en el sistema.", "danger")
        return redirect(url_for('formaciones_bp.gestion_formaciones'))

    # Diccionario con los datos que se van a rellenar en el PDF (adaptado a CERTIFICADO_DE_PARTICIPACION.pdf)
    data = {
        'NOMBRE_ALUMNO': alumno.nombre.title(),
        'DNI': alumno.dni,
        'INSTRUCTOR': formacion.formador.nombre if formacion.formador else "",
        'FECHA': formacion.fecha1.strftime("%d/%m/%Y"),
        'POBLACION': formacion.poblacion or "",
        'FIRMA_FORMADOR': formacion.formador.nombre if formacion.formador else "",
        'CURSO': curso.nombre,
    }
    print("==== DATOS QUE SE ENVIAN AL PDF (DIPLOMA) ====")
    for k, v in data.items():
        print(f"{k}: {v}")
    print("==== FIN DATOS PDF ====")

    # Crear archivo temporal rellenado
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        ruta_temporal = temp_file.name

    try:
        rellenar_pdf(ruta_absoluta_plantilla, ruta_temporal, data)

        with open(ruta_temporal, 'rb') as f:
            pdf_bytes = f.read()

        ruta_guardado = guardar_diploma_pdf(alumno, formacion, pdf_bytes)

        return send_file(
            io.BytesIO(pdf_bytes),
            download_name=os.path.basename(ruta_guardado),
            mimetype='application/pdf',
            as_attachment=True
        )
    except Exception as e:
        logger.exception(f"Error al generar diploma con PDF autorrellenable: {e}")
        flash("Error al generar el diploma. Consulta los logs.", "danger")
        return redirect(url_for('formaciones_bp.gestion_formaciones'))
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)

@formaciones_bp.route('/alumno_formacion/actualizar', methods=['POST'])
def actualizar_alumno_formacion():
    alumno_formacion_id = request.form.get('id')
    campo = request.form.get('campo')
    valor = request.form.get('valor')
    rel = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    if campo == 'nota':
        try:
            rel.nota = float(valor)
        except ValueError:
            return jsonify(ok=False, error="Nota no válida")
    elif campo == 'aprobado':
        rel.aprobado = (valor == 'true')
    else:
        return jsonify(ok=False, error="Campo no válido")
    db.session.commit()
    return jsonify(ok=True)

@formaciones_bp.route('/info/<int:formacion_id>')
def info_formacion(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    return jsonify({
        "referencia": formacion.referencia,
        "fecha": formacion.fecha1.strftime('%d/%m/%Y') if formacion.fecha1 else '',
        "empresa": formacion.empresa.nombre if formacion.empresa else '',
        "tipo_curso": formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        "horario1": f"{formacion.hora_inicio1} - {formacion.hora_fin1}" if formacion.hora_inicio1 and formacion.hora_fin1 else '',
        "fundae": "Sí" if formacion.fundae else "No",
        "comercial": formacion.comercial if hasattr(formacion, "comercial") else '',
        "estado": "Cerrada" if formacion.cerrada else "Pendiente",
        "observaciones": formacion.observaciones or '',
        "direccion_aula": formacion.direccion_aula or ''
    })

# ----------- CALENDARIO DE FORMACIONES -----------

@formaciones_bp.route('/calendario')
def calendario_formaciones():
    return render_template('formaciones/calendario_formaciones.html')

@formaciones_bp.route('/api/formaciones_calendario')
def api_formaciones_calendario():
    formaciones = Formacion.query.all()
    eventos = []
    for f in formaciones:
        color = f.tipo_curso.color if f.tipo_curso and f.tipo_curso.color else "#4287f5"  # azul por defecto
        # Primera edición
# Primera edición
        if f.fecha1 and f.hora_inicio1 and f.hora_fin1:
            eventos.append({
                "id": f.id,
                "title": f"{f.tipo_curso.nombre} (Día 1) - {f.empresa.nombre if f.empresa else ''}",
                "start": f"{f.fecha1.strftime('%Y-%m-%d')}T{f.hora_inicio1.strftime('%H:%M:%S')}",
                "end": f"{f.fecha1.strftime('%Y-%m-%d')}T{f.hora_fin1.strftime('%H:%M:%S')}",
                "url": url_for('formaciones_bp.ficha_formacion', formacion_id=f.id),
                "description": f"""
                    <b>Empresa:</b> {f.empresa.nombre if f.empresa else ''}<br>
                    <b>Curso:</b> {f.tipo_curso.nombre if f.tipo_curso else ''}<br>
                    <b>Formador:</b> {f.formador.nombre if f.formador else ''}<br>
                    <b>Horario:</b> {f.hora_inicio1.strftime('%H:%M')} - {f.hora_fin1.strftime('%H:%M')}
                """,
                "color": color
            })
        # Segunda edición (Día 2)
        if getattr(f, "fecha2", None) and f.hora_inicio2 and f.hora_fin2:
            eventos.append({
                "id": f"id2_{f.id}",
                "title": f"{f.tipo_curso.nombre} (Día 2) - {f.empresa.nombre if f.empresa else ''}",
                "start": f"{f.fecha2.strftime('%Y-%m-%d')}T{f.hora_inicio2.strftime('%H:%M:%S')}",
                "end": f"{f.fecha2.strftime('%Y-%m-%d')}T{f.hora_fin2.strftime('%H:%M:%S')}",
                "url": url_for('formaciones_bp.ficha_formacion', formacion_id=f.id),
                "description": f"""
                    <b>Empresa:</b> {f.empresa.nombre if f.empresa else ''}<br>
                    <b>Curso:</b> {f.tipo_curso.nombre if f.tipo_curso else ''}<br>
                    <b>Formador:</b> {f.formador.nombre if f.formador else ''}<br>
                    <b>Horario:</b> {f.hora_inicio2.strftime('%H:%M')} - {f.hora_fin2.strftime('%H:%M')}
                """,
                "color": color
            })
    return jsonify(eventos)

from flask import send_file
import io
import openpyxl
@formaciones_bp.route('/borrar/<int:formacion_id>', methods=['POST'])

@formaciones_bp.route('/borrar/<int:formacion_id>', methods=['POST'])
def borrar_formacion(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    fecha_borrada = formacion.fecha1  # Guarda la fecha antes de borrar
    db.session.delete(formacion)
    db.session.commit()
    recalcular_referencias(fecha_borrada)  # <--- RECALCULA tras borrar
    flash('Formación eliminada correctamente.', 'success')
    return redirect(url_for('formaciones_bp.gestion_formaciones'))

@formaciones_bp.route('/exportar_excel')
def exportar_excel():
    formaciones = Formacion.query.order_by(Formacion.fecha1.desc()).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Formaciones"
    ws.append([
        "ID", "Referencia", "Fecha", "Empresa", "Tipo de curso",
        "Formador", "FUNDAE", "Estado"
    ])

    for f in formaciones:
        ws.append([
            f.id,
            f.referencia or '',
            f.fecha1.strftime('%d/%m/%Y') if f.fecha1 else '',
            f.empresa.nombre if f.empresa else '',
            f.tipo_curso.nombre if f.tipo_curso else '',
            f.formador.nombre if f.formador else '',
            "Sí" if f.fundae else "No",
            "Cerrada" if getattr(f, "cerrada", False) else "Abierta"
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        download_name="formaciones.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
from flask import request, send_file, current_app
from jinja2 import Template
import pdfkit
import io

@formaciones_bp.route('/acta/generar/<int:formacion_id>/<int:plantilla_id>')
def generar_acta(formacion_id, plantilla_id):
    import tempfile
    from flask import flash
    from mi_plataforma_formacion_app.utils.pdf_fill import rellenar_pdf

    formacion = Formacion.query.get_or_404(formacion_id)
    plantilla = PlantillaActa.query.get_or_404(plantilla_id)

    if not plantilla.ruta_pdf:
        flash("La plantilla de acta no tiene PDF asociado.", "danger")
        return redirect(request.referrer or url_for('formaciones_bp.ficha_formacion', formacion_id=formacion_id))

    # Construir diccionario de datos para rellenar el PDF
    data = {
        'curso': formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        'empresa': formacion.empresa.nombre if formacion.empresa else '',
        'fecha': formacion.fecha1.strftime('%d/%m/%Y') if formacion.fecha1 else '',
        'formador': formacion.formador.nombre if formacion.formador else '',
        'horario': f"{formacion.hora_inicio1.strftime('%H:%M') if formacion.hora_inicio1 else ''} - {formacion.hora_fin1.strftime('%H:%M') if formacion.hora_fin1 else ''}",
        'lugar': getattr(formacion, 'direccion_aula', formacion.lugar if hasattr(formacion, 'lugar') else ''),
        'referencia': formacion.referencia or '',
        'poblacion': formacion.poblacion or '',
        'fundae': 'Sí' if getattr(formacion, 'fundae', False) else 'No',
        # Segunda edición
        'fecha2': formacion.fecha2.strftime('%d/%m/%Y') if getattr(formacion, 'fecha2', None) else '',
        'horario2': f"{formacion.hora_inicio2.strftime('%H:%M') if getattr(formacion, 'hora_inicio2', None) else ''} - {formacion.hora_fin2.strftime('%H:%M') if getattr(formacion, 'hora_fin2', None) else ''}",
        'horas': str(getattr(formacion.tipo_curso, 'duracion_horas', '') or ''),
    }
    alumnos_str = '\n'.join([
        f"{rel.alumno.nombre} - {rel.alumno.dni}"
        for rel in formacion.alumno_formaciones
    ])
    data['alumnos'] = alumnos_str
    print("==== DATOS QUE SE ENVIAN AL PDF ====")
    for k, v in data.items():
        print(f"{k}: {v}")
    print("==== FIN DATOS PDF ====")
    # Rellenar el PDF y servirlo
    import os
    ruta_absoluta_plantilla = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        ruta_temporal = temp_file.name
        rellenar_pdf(ruta_absoluta_plantilla, ruta_temporal, data)
    return send_file(ruta_temporal, download_name=f"acta_{formacion_id}.pdf", as_attachment=True, mimetype='application/pdf')

@formaciones_bp.route('/descargar_diploma_guardado/<int:alumno_formacion_id>')
def descargar_diploma_guardado(alumno_formacion_id):
    import os
    from flask import current_app, send_file, flash, redirect, url_for
    from mi_plataforma_formacion_app.models import AlumnoFormacion

    rel = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    alumno = rel.alumno
    formacion = rel.formacion

    # Función de normalizar nombres
    def normaliza(nombre):
        import unicodedata, re
        nombre = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode('utf-8')
        nombre = re.sub(r'[^a-zA-Z0-9\s]', '_', nombre)
        nombre = nombre.lower().strip()
        nombre = re.sub(r'\s+', '_', nombre)
        nombre = re.sub(r'_{2,}', '_', nombre)
        return nombre.strip('_')

    empresa_nombre = normaliza(formacion.empresa.nombre)
    fecha_str = formacion.fecha1.strftime("%Y-%m-%d") if formacion.fecha1 else "sin_fecha"
    alumno_nombre = normaliza(alumno.nombre)
    ruta_pdf = os.path.join(current_app.root_path, 'static', 'diplomas', empresa_nombre, fecha_str, f'diploma_{alumno_nombre}.pdf')

    print("==== DIPLOMA PATH ====")
    print(ruta_pdf)
    print("==== FIN ====")

    if not os.path.exists(ruta_pdf):
        flash("No se encuentra el diploma guardado.", "danger")
        return redirect(url_for('formaciones_bp.alumnos_formacion', formacion_id=formacion.id))

    return send_file(ruta_pdf, as_attachment=True)
from flask import render_template
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion

@formaciones_bp.route('/ver/<int:formacion_id>')
def ver_formacion(formacion_id):
    # 1) Recupera la formación (o 404 si no existe)
    formacion = Formacion.query.get_or_404(formacion_id)
    # 2) Relación AlumnoFormacion para mostrar en la tabla
    alumnos_rel = AlumnoFormacion.query\
                    .filter_by(formacion_id=formacion_id)\
                    .order_by(AlumnoFormacion.alumno_id)\
                    .all()
    # 3) Renderiza tu ficha_formacion.html
    return render_template(
        'formaciones/ficha_formacion.html',
        formacion=formacion,
        alumnos_rel=alumnos_rel
    )

@formaciones_bp.route('/diplomas', methods=['GET'])
def diplomas_emitidos():
    q = request.args.get('q', '').strip().lower()
    relaciones = AlumnoFormacion.query \
        .join(Alumno, Alumno.id == AlumnoFormacion.alumno_id) \
        .join(Formacion, Formacion.id == AlumnoFormacion.formacion_id) \
        .join(TipoCurso, TipoCurso.id == Formacion.tipo_curso_id) \
        .join(Empresa, Empresa.id == Formacion.empresa_id) \
        .filter(AlumnoFormacion.aprobado == True) \
        .order_by(Formacion.fecha1.desc()) \
        .all()

    if q:
        relaciones = [r for r in relaciones if
            q in r.alumno.nombre.lower() or
            q in r.alumno.dni.lower() or
            q in r.formacion.tipo_curso.nombre.lower() or
            q in r.formacion.empresa.nombre.lower()
        ]

    return render_template('formaciones/diplomas_emitidos.html', relaciones=relaciones, query=q)
