from flask import Blueprint, render_template, redirect, url_for, request, flash, send_from_directory, current_app
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
from mi_plataforma_formacion_app.services.diplomas_safe import safe_generate_diploma
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
                # Evitar preguntas duplicadas con el mismo texto en este examen
                existente = Pregunta.query.filter_by(examen_modelo_id=examen.id, texto=texto).first()
                if existente:
                    flash("Ya existe una pregunta con ese texto.", "warning")
                else:
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
        if tipo == 'nueva_respuesta':
            pregunta_id = request.form.get('pregunta_id')
            texto = request.form.get('texto')
            # Normalizar y comprobar existencia para evitar duplicados
            try:
                pregunta_id_int = int(pregunta_id) if pregunta_id is not None else None
            except Exception:
                pregunta_id_int = None
            es_correcta_raw = request.form.get('es_correcta')
            es_correcta = True if str(es_correcta_raw).lower() in ('on', 'true', '1') else False
            if texto and pregunta_id_int:
                texto_norm = texto.strip()
                existente = Respuesta.query.filter_by(pregunta_id=pregunta_id_int, texto=texto_norm, examen_alumno_id=None).first()
                if existente:
                    # actualizar existente en vez de crear duplicado
                    existente.texto = texto_norm
                    existente.es_correcta = es_correcta
                    r = existente
                else:
                    r = Respuesta(texto=texto_norm, es_correcta=es_correcta, pregunta_id=pregunta_id_int, examen_alumno_id=None)
                    db.session.add(r)
                # Si es la correcta y la pregunta admite única correcta, apagar el resto
                if es_correcta:
                    Respuesta.query.filter(Respuesta.pregunta_id == pregunta_id_int, Respuesta.id != getattr(r, 'id', None), Respuesta.examen_alumno_id==None).update({Respuesta.es_correcta: False}, synchronize_session=False)
                db.session.commit()
                flash("Respuesta guardada", "success")
        elif tipo == 'editar_respuesta':
            respuesta_id = request.form.get('respuesta_id')
            texto = request.form.get('texto')
            es_correcta = True if str(request.form.get('es_correcta')).lower() in ('on','true','1','1') else False
            # Buscar solo entre respuestas del modelo
            from sqlalchemy import and_
            try:
                rid = int(respuesta_id)
            except Exception:
                rid = None
            if rid is None:
                flash("ID de respuesta inválido", "danger")
            else:
                respuesta = Respuesta.query.filter(and_(Respuesta.id==rid, Respuesta.examen_alumno_id==None)).first()
                if not respuesta:
                    flash("No se puede editar una respuesta de alumno o no existe la respuesta de modelo.", "danger")
                else:
                    respuesta.texto = texto.strip()
                    respuesta.es_correcta = es_correcta
                    if es_correcta:
                        # apagar el resto de opciones modelo de la pregunta
                        Respuesta.query.filter(Respuesta.pregunta_id==respuesta.pregunta_id, Respuesta.id!=respuesta.id, Respuesta.examen_alumno_id==None).update({Respuesta.es_correcta: False}, synchronize_session=False)
                    db.session.commit()
                    flash("Respuesta actualizada", "success")
        elif tipo == 'eliminar_respuesta':
            respuesta_id = request.form.get('respuesta_id')
            try:
                rid = int(respuesta_id)
            except Exception:
                rid = None
            if rid is None:
                flash("ID de respuesta inválido", "danger")
            else:
                # eliminar solo si es respuesta de modelo
                resp = Respuesta.query.filter(Respuesta.id==rid, Respuesta.examen_alumno_id==None).first()
                if not resp:
                    flash("No se puede eliminar una respuesta de alumno o no existe.", "danger")
                else:
                    db.session.delete(resp)
                    db.session.commit()
                    flash("Respuesta del modelo eliminada", "success")
        return redirect(url_for('examenes_bp.constructor_examen', examen_id=examen.id))
    return render_template('examenes/constructor_examen.html', examen=examen)

# 6. HACER EXAMEN (la ruta que usa el acceso por DNI)
@examenes_bp.route('/hacer_examen/<int:formacion_id>/<int:alumno_id>', methods=['GET', 'POST'])
def hacer_examen(formacion_id, alumno_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    alumno = Alumno.query.get_or_404(alumno_id)
    # Si la formación está cerrada, solo permitir GET para usuarios internos; bloquear en student_mode o para métodos mutantes
    from flask import g
    if formacion and getattr(formacion, 'cerrada', False):
        if request.method != 'GET' or getattr(g, 'student_mode', False):
            try:
                current_app.logger.info('Intento de acceso a formacion CERRADA (hacer_examen) - bloqueado', extra={'id': getattr(formacion, 'id', None), 'remote_addr': request.remote_addr, 'alumno_id': getattr(alumno, 'id', None)})
            except Exception:
                pass
            return render_template('formaciones/formacion_cerrada.html', formacion=formacion), 403
    examen_modelo = getattr(formacion.tipo_curso, 'examen_modelo', None)
    if not examen_modelo:
        flash("Este curso no tiene examen asociado.", "danger")
        return redirect(url_for('alumnos_bp.ficha_alumno', alumno_id=alumno.id))

    preguntas = examen_modelo.preguntas

    class DynamicExamenForm(FlaskForm):
        submit = SubmitField('Finalizar examen')

    for pregunta in preguntas:
        # `pregunta.respuestas` now already returns only the model options (examen_alumno_id is NULL).
        # Deduplicar por texto para evitar mostrar varias veces la misma etiqueta
        seen = set()
        opciones = []
        for r in pregunta.respuestas:
            texto = (r.texto or '').strip()
            if texto in seen:
                continue
            seen.add(texto)
            opciones.append((str(r.id), texto))
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
            # Buscar únicamente entre las opciones originales (relationship already filtered)
            opciones_originales = list(pregunta.respuestas)
            respuesta_obj = next((r for r in opciones_originales if str(r.id) == respuesta_id), None)
            correcta_obj = next((r for r in opciones_originales if r.es_correcta), None)
            explicacion = getattr(correcta_obj, "descripcion", "") if correcta_obj and hasattr(correcta_obj, "descripcion") else ""

            # Construir lista de opciones únicas por texto, preservando el id
            seen = set()
            opciones = []
            for opcion in opciones_originales:
                texto = (opcion.texto or '').strip()
                if texto in seen:
                    continue
                seen.add(texto)
                opciones.append({
                    "id": opcion.id,
                    "texto": texto,
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
        # Guardar respuestas del alumno asociadas al ExamenAlumno
        from mi_plataforma_formacion_app.models import ExamenAlumno, Respuesta
        examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first()
        if not examen_alumno:
            examen_alumno = ExamenAlumno(
                alumno_formacion_id=rel.id,
                nota=nota
            )
            db.session.add(examen_alumno)
            db.session.commit()  # Commit para obtener el id
        # Eliminar respuestas previas del alumno para este examen
        Respuesta.query.filter_by(examen_alumno_id=examen_alumno.id).delete()
        db.session.commit()
        for pregunta in preguntas:
            respuesta_id = respuestas_dict.get(str(pregunta.id))
            if respuesta_id:
                # Obtener la opción original seleccionada
                opciones_originales = list(pregunta.respuestas)
                respuesta_obj = next((r for r in opciones_originales if str(r.id) == respuesta_id), None)
                if respuesta_obj:
                    nueva_respuesta = Respuesta(
                        texto=respuesta_obj.texto,
                        # No copiar el flag es_correcta desde la opción del modelo;
                        # las respuestas del alumno deben almacenarse separadas.
                        es_correcta=False,
                        pregunta_id=pregunta.id,
                        examen_alumno_id=examen_alumno.id
                    )
                    db.session.add(nueva_respuesta)
        db.session.commit()

    # ====== NUEVO: GUARDAR RESPUESTAS DEL EXAMEN ======
    # Este bloque ya está gestionado arriba, se elimina duplicidad y se corrige indentación

        if aprobado:
            plantilla = formacion.tipo_curso.plantilla_diploma
            if plantilla and plantilla.ruta_pdf:
                try:
                    ruta_pdf, msg = safe_generate_diploma(
                        alumno,
                        formacion,
                        lambda a, f, dest: crear_y_guardar_diploma(a, f, plantilla),
                        lambda a, f, dest: crear_y_guardar_diploma(a, f, None)
                    )
                    if ruta_pdf:
                        try:
                            enviar_diploma_por_email(alumno, ruta_pdf)
                        except Exception:
                            current_app.logger.exception("Error enviando diploma por email")
                            flash("Diploma generado, pero no se pudo enviar por email.", "warning")
                    else:
                        # fallback fallido
                        current_app.logger.error("safe_generate_diploma devolvió None para alumno_id=%s formacion_id=%s", getattr(alumno, 'id', '<none>'), getattr(formacion, 'id', '<none>'))
                        flash(msg or "No se pudo generar el diploma.", "danger")
                except Exception:
                    current_app.logger.exception("Error generando diploma para alumno_id=%s formacion_id=%s", getattr(alumno, 'id', '<none>'), getattr(formacion, 'id', '<none>'))
                    flash("Error generando el diploma. El administrador ha sido notificado.", "danger")
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
    # Bloquear acceso si la formación está marcada como cerrada
    if formacion and getattr(formacion, 'cerrada', False):
        try:
            current_app.logger.info('Intento de ver_examen a formacion CERRADA', extra={'id': getattr(formacion, 'id', None), 'remote_addr': request.remote_addr, 'alumno_id': getattr(alumno, 'id', None)})
        except Exception:
            pass
        return render_template('formaciones/formacion_cerrada.html', formacion=formacion), 403
    rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion.id).first()
    examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first() if rel else None

    correccion_preguntas = []
    aciertos = 0
    fallos = 0
    total_preguntas = 0
    nota = 0

    # El campo respuestas_json ya no existe; cargamos el modelo y las respuestas del alumno
    examen_modelo = getattr(formacion.tipo_curso, 'examen_modelo', None)
    if examen_modelo and examen_modelo.preguntas:
        # Cargar respuestas guardadas del alumno para este examen (filtradas por examen_alumno_id)
        respuestas_guardadas = {}
        from mi_plataforma_formacion_app.models.respuesta import Respuesta as RespuestaModel
        # Caso normal: tenemos un ExamenAlumno y cargamos sus respuestas
        if examen_alumno:
            filas = RespuestaModel.query.filter_by(examen_alumno_id=examen_alumno.id).all()
            for fila in filas:
                respuestas_guardadas[str(fila.pregunta_id)] = fila
        else:
            # Fallback defensivo: buscar respuestas existentes para las preguntas de este examen
            pregunta_ids = [p.id for p in examen_modelo.preguntas]
            if pregunta_ids:
                filas = RespuestaModel.query.filter(RespuestaModel.pregunta_id.in_(pregunta_ids), RespuestaModel.examen_alumno_id!=None).all()
            else:
                filas = []
            if filas:
                # Elegir la examen_alumno_id más frecuente (probablemente la correcta)
                from collections import Counter
                counts = Counter([f.examen_alumno_id for f in filas if f.examen_alumno_id is not None])
                if counts:
                    best_ea_id = counts.most_common(1)[0][0]
                    # Cargar ese ExamenAlumno para mostrar nota si existe
                    try:
                        examen_alumno = ExamenAlumno.query.get(best_ea_id)
                    except Exception:
                        examen_alumno = None
                    for fila in filas:
                        if fila.examen_alumno_id == best_ea_id:
                            respuestas_guardadas[str(fila.pregunta_id)] = fila

        def norm(s):
            try:
                return s.strip().lower()
            except Exception:
                return s

        for pregunta in examen_modelo.preguntas:
            total_preguntas += 1
            # Respuesta dada por el alumno (guardada en la tabla respuesta)
            r_guardada = respuestas_guardadas.get(str(pregunta.id))
            respuesta_dada = r_guardada.texto if r_guardada else "No respondido"

            # Buscar la respuesta correcta entre las opciones originales (filtradas por modelo)
            correcta_obj = next((r for r in pregunta.respuestas if r.examen_alumno_id is None and r.es_correcta), None)
            respuesta_correcta = correcta_obj.texto if correcta_obj else None

            # Determinar acierto comparando textos normalizados (no confiar en es_correcta de la fila del alumno)
            es_ok = False
            if r_guardada and respuesta_correcta is not None:
                es_ok = norm(respuesta_dada) == norm(respuesta_correcta)

            if es_ok:
                aciertos += 1
            else:
                fallos += 1

            correccion_preguntas.append({
                "pregunta": getattr(pregunta, 'texto', ''),
                "respuesta_dada": respuesta_dada,
                "respuesta_correcta": respuesta_correcta or '-',
                "es_correcta": bool(es_ok)
            })

        # Preferir la nota automática si existe, si no usar la nota almacenada en 'nota'
        if examen_alumno:
            if getattr(examen_alumno, 'nota_automatica', None) is not None:
                nota = examen_alumno.nota_automatica
            elif getattr(examen_alumno, 'nota', None) is not None:
                nota = examen_alumno.nota
            else:
                nota = 0
        else:
            nota = 0

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
