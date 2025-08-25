from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory
from flask_wtf import FlaskForm
from wtforms import RadioField, SubmitField
from .forms import ExamenModeloForm
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.examen_modelo import ExamenModelo
from mi_plataforma_formacion_app.models.pregunta import Pregunta
from mi_plataforma_formacion_app.models.respuesta import Respuesta
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.examen_alumno import ExamenAlumno
from mi_plataforma_formacion_app.utils.diplomas import crear_y_guardar_diploma
from mi_plataforma_formacion_app.utils.emailing import enviar_diploma_por_email
import json

examenes_bp = Blueprint('examenes_bp', __name__, template_folder='templates/examenes')

# 1. Listar exámenes modelo
@examenes_bp.route('/examenes_modelo')
def listar_examenes_modelo():
    examenes = ExamenModelo.query.all()
    return render_template('examenes/listar_examenes_modelo.html', examenes=examenes)

# 2. Crear examen modelo
@examenes_bp.route('/examenes_modelo/nuevo', methods=['GET', 'POST'])
def crear_examen_modelo():
    form = ExamenModeloForm()
    if form.validate_on_submit():
        examen = ExamenModelo(nombre=form.nombre.data, descripcion=form.descripcion.data)
        db.session.add(examen)
        db.session.commit()
        flash("Examen creado", "success")
        return redirect(url_for('examenes_bp.listar_examenes_modelo'))
    return render_template('examenes/crear_examen_modelo.html', form=form, examen=None)

# 3. Editar examen modelo
@examenes_bp.route('/examenes_modelo/<int:examen_id>/editar', methods=['GET', 'POST'])
def editar_examen_modelo(examen_id):
    examen = ExamenModelo.query.get_or_404(examen_id)
    form = ExamenModeloForm(obj=examen)
    if form.validate_on_submit():
        examen.nombre = form.nombre.data
        examen.descripcion = form.descripcion.data
        db.session.commit()
        flash("Examen actualizado", "success")
        return redirect(url_for('examenes_bp.listar_examenes_modelo'))
    return render_template('examenes/crear_examen_modelo.html', form=form, examen=examen)

# 4. Eliminar examen modelo
@examenes_bp.route('/examenes_modelo/<int:examen_id>/eliminar', methods=['POST'])
def eliminar_examen_modelo(examen_id):
    examen = ExamenModelo.query.get_or_404(examen_id)
    db.session.delete(examen)
    db.session.commit()
    flash("Examen eliminado", "success")
    return redirect(url_for('examenes_bp.listar_examenes_modelo'))

# 5. Constructor de examen (añadir/editar/eliminar preguntas y respuestas)
@examenes_bp.route('/constructor/<int:examen_id>', methods=['GET', 'POST'])
def constructor_examen(examen_id):
    examen = ExamenModelo.query.get_or_404(examen_id)
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        if tipo == 'nueva_pregunta':
            texto = request.form.get('texto')
            if texto:
                pregunta = Pregunta(texto=texto, examen_modelo_id=examen.id)
                db.session.add(pregunta)
                db.session.commit()
                flash("Pregunta añadida", "success")
        elif tipo == 'editar_pregunta':
            pregunta_id = request.form.get('pregunta_id')
            texto = request.form.get('texto')
            pregunta = Pregunta.query.get(pregunta_id)
            if pregunta and texto:
                pregunta.texto = texto
                db.session.commit()
                flash("Pregunta actualizada", "success")
        elif tipo == 'eliminar_pregunta':
            pregunta_id = request.form.get('pregunta_id')
            pregunta = Pregunta.query.get(pregunta_id)
            if pregunta:
                db.session.delete(pregunta)
                db.session.commit()
                flash("Pregunta eliminada", "success")
        elif tipo == 'nueva_respuesta':
            pregunta_id = request.form.get('pregunta_id')
            texto = request.form.get('texto')
            es_correcta = bool(request.form.get('es_correcta'))
            if texto and pregunta_id:
                respuesta = Respuesta(texto=texto, es_correcta=es_correcta, pregunta_id=pregunta_id)
                db.session.add(respuesta)
                db.session.commit()
                flash("Respuesta añadida", "success")
        elif tipo == 'editar_respuesta':
            respuesta_id = request.form.get('respuesta_id')
            texto = request.form.get('texto')
            es_correcta = bool(request.form.get('es_correcta'))
            respuesta = Respuesta.query.get(respuesta_id)
            if respuesta and texto:
                respuesta.texto = texto
                respuesta.es_correcta = es_correcta
                db.session.commit()
                flash("Respuesta actualizada", "success")
        elif tipo == 'eliminar_respuesta':
            respuesta_id = request.form.get('respuesta_id')
            respuesta = Respuesta.query.get(respuesta_id)
            if respuesta:
                db.session.delete(respuesta)
                db.session.commit()
                flash("Respuesta eliminada", "success")
        return redirect(url_for('examenes_bp.constructor_examen', examen_id=examen.id))
    return render_template('examenes/constructor_examen.html', examen=examen)

# 6. HACER EXAMEN (la ruta que usa el acceso por DNI)
@examenes_bp.route('/hacer_examen/<int:formacion_id>/<int:alumno_id>', methods=['GET', 'POST'])
def hacer_examen(formacion_id, alumno_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    alumno = Alumno.query.get_or_404(alumno_id)
    examen_modelo = getattr(formacion.tipo_curso, 'examen_modelo', None)
    if not examen_modelo:
        flash("Este curso no tiene examen asociado.", "danger")
        return redirect(url_for('alumnos_bp.ficha_alumno', alumno_id=alumno.id))

    preguntas = examen_modelo.preguntas

    class DynamicExamenForm(FlaskForm):
        submit = SubmitField('Finalizar examen')

    for pregunta in preguntas:
        opciones = [(str(r.id), r.texto) for r in pregunta.respuestas]
        if opciones:
            setattr(DynamicExamenForm, f"preg_{pregunta.id}", RadioField(
                pregunta.texto,
                choices=opciones,
                coerce=str,
                validators=[],
                render_kw={"required": True}
            ))

    form = DynamicExamenForm()
    resultado = None
    ruta_pdf = None
    correccion_preguntas = []

    # ==== RELACIÓN alumno_formacion, siempre disponible ====
    rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion.id).first()

    if form.validate_on_submit():
        correctas = 0
        total = 0
        correccion_preguntas = []
        respuestas_dict = {}

        for pregunta in preguntas:
            if not pregunta.respuestas:
                continue
            fieldname = f"preg_{pregunta.id}"
            respuesta_id = getattr(form, fieldname).data
            respuestas_dict[str(pregunta.id)] = respuesta_id
            respuesta_obj = next((r for r in pregunta.respuestas if str(r.id) == respuesta_id), None)
            correcta_obj = next((r for r in pregunta.respuestas if r.es_correcta), None)
            explicacion = getattr(correcta_obj, "descripcion", "") if correcta_obj and hasattr(correcta_obj, "descripcion") else ""

            opciones = []
            for opcion in pregunta.respuestas:
                opciones.append({
                    "id": opcion.id,
                    "texto": opcion.texto,
                    "es_correcta": opcion.es_correcta,
                    "marcada": str(opcion.id) == respuesta_id
                })

            acertada = respuesta_obj and respuesta_obj.es_correcta
            correccion_preguntas.append({
                "pregunta": pregunta.texto,
                "opciones": opciones,
                "acertada": acertada,
                "explicacion": explicacion
            })

            if acertada:
                correctas += 1
            total += 1

        nota = int((correctas / total) * 10) if total > 0 else 0
        aprobado = nota >= 5
        resultado = {
            "aciertos": correctas,
            "total": total,
            "nota": nota,
            "aprobado": aprobado,
        }

        if rel:
            rel.aprobado = aprobado
            rel.nota = nota
            db.session.commit()

            # ====== NUEVO: GUARDAR RESPUESTAS DEL EXAMEN ======
            examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first()
            if not examen_alumno:
                examen_alumno = ExamenAlumno(
                    alumno_formacion_id=rel.id,
                    respuestas_json=json.dumps(respuestas_dict),
                    nota_automatica=nota
                )
                db.session.add(examen_alumno)
            else:
                examen_alumno.respuestas_json = json.dumps(respuestas_dict)
                examen_alumno.nota_automatica = nota
            db.session.commit()
            # ================================================

        if aprobado:
            plantilla = formacion.tipo_curso.plantilla_diploma
            if plantilla and plantilla.ruta_pdf:
                ruta_pdf = crear_y_guardar_diploma(alumno, formacion, plantilla)
                enviar_diploma_por_email(alumno, ruta_pdf)
            else:
                flash("No hay plantilla asignada a esta formación.", "danger")
                return redirect(url_for('formaciones_bp.gestion_formaciones'))
        else:
            flash("Examen no aprobado. No se genera diploma.", "warning")

        return render_template(
            'examenes/examen.html',
            form=form,
            formacion=formacion,
            alumno=alumno,
            examen=examen_modelo,
            resultado=resultado,
            ruta_pdf=ruta_pdf,
            correccion_preguntas=correccion_preguntas,
            preguntas=preguntas,
            alumno_formacion=rel   # <-- ¡Esto es lo importante!
        )

    # GET: mostrar solo el examen para rellenar
    return render_template(
        'examenes/examen.html',
        form=form,
        formacion=formacion,
        alumno=alumno,
        examen=examen_modelo,
        resultado=resultado,
        ruta_pdf=ruta_pdf,
        correccion_preguntas=[],
        preguntas=preguntas,
        alumno_formacion=rel   # <-- ¡Esto es lo importante!
    )

def new_func(formacion, alumno):
    from mi_plataforma_formacion_app.models import PlantillaDiploma  # si no lo tienes ya

    plantilla = PlantillaDiploma.query.first()
    ruta_pdf = crear_y_guardar_diploma(alumno, formacion, plantilla)
    return ruta_pdf

# 7. Descargar diploma (opcional)
@examenes_bp.route('/diplomas/<path:filename>')
def descargar_diploma(filename):
    return send_from_directory('diplomas', filename)

# 8. VER EXAMEN Y RESPUESTAS
@examenes_bp.route('/ver_examen/<int:formacion_id>/<int:alumno_id>')
def ver_examen_alumno(formacion_id, alumno_id):
    import json
    from mi_plataforma_formacion_app.models import Alumno, Formacion, AlumnoFormacion, ExamenAlumno

    alumno = Alumno.query.get_or_404(alumno_id)
    formacion = Formacion.query.get_or_404(formacion_id)
    rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion.id).first()
    examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first() if rel else None

    correccion_preguntas = []
    aciertos = 0
    fallos = 0
    total_preguntas = 0
    nota = 0

    if examen_alumno and examen_alumno.respuestas_json:
        respuestas_dict = json.loads(examen_alumno.respuestas_json)
        examen_modelo = getattr(formacion.tipo_curso, 'examen_modelo', None)
        if examen_modelo and examen_modelo.preguntas:
            for pregunta in examen_modelo.preguntas:
                total_preguntas += 1
                respuesta_id = respuestas_dict.get(str(pregunta.id))
                # Buscar la respuesta del alumno (por id)
                respuesta_obj = next((r for r in pregunta.respuestas if str(r.id) == str(respuesta_id)), None)
                respuesta_dada = respuesta_obj.texto if respuesta_obj else "No respondido"
                # Buscar la respuesta correcta
                correcta_obj = next((r for r in pregunta.respuestas if r.es_correcta), None)
                respuesta_correcta = correcta_obj.texto if correcta_obj else "-"
                es_correcta = respuesta_obj is not None and respuesta_obj.es_correcta

                if es_correcta:
                    aciertos += 1
                else:
                    fallos += 1

                correccion_preguntas.append({
                    "pregunta": pregunta.texto,
                    "respuesta_dada": respuesta_dada,
                    "respuesta_correcta": respuesta_correcta,
                    "es_correcta": es_correcta
                })
        nota = examen_alumno.nota_automatica if examen_alumno.nota_automatica is not None else 0

    aprobado = nota >= 5

    return render_template(
        'formaciones/ver_examen_alumno.html',
        alumno=alumno,
        formacion=formacion,
        examen_alumno=examen_alumno,
        correccion_preguntas=correccion_preguntas,
        aciertos=aciertos,
        fallos=fallos,
        nota=nota,
        aprobado=aprobado,
        total_preguntas=total_preguntas
    )
