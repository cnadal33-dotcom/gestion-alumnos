from flask import Blueprint, render_template, redirect, url_for, request, flash
from mi_plataforma_formacion_app.models.pregunta import Pregunta
from mi_plataforma_formacion_app.models.respuesta import Respuesta
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.extensions import db
from .forms import PreguntaForm, RespuestaForm

preguntas_bp = Blueprint('preguntas_bp', __name__)

# Listar preguntas por tipo de curso
@preguntas_bp.route('/<int:tipo_curso_id>/preguntas')
def lista_preguntas(tipo_curso_id):
    curso = TipoCurso.query.get_or_404(tipo_curso_id)
    preguntas = Pregunta.query.filter_by(tipo_curso_id=tipo_curso_id).all()
    return render_template('examenes/lista_preguntas.html', preguntas=preguntas, curso=curso)

# Crear nueva pregunta
@preguntas_bp.route('/<int:tipo_curso_id>/pregunta_nueva', methods=['GET', 'POST'])
def nueva_pregunta(tipo_curso_id):
    form = PreguntaForm()
    if form.validate_on_submit():
        p = Pregunta(texto=form.texto.data, tipo_curso_id=tipo_curso_id)
        db.session.add(p)
        db.session.commit()
        return redirect(url_for('preguntas_bp.lista_preguntas', tipo_curso_id=tipo_curso_id))
    return render_template('examenes/crear_pregunta.html', form=form)

# Editar pregunta
@preguntas_bp.route('/pregunta/<int:id>/editar', methods=['GET', 'POST'])
def editar_pregunta(id):
    pregunta = Pregunta.query.get_or_404(id)
    form = PreguntaForm(obj=pregunta)
    if form.validate_on_submit():
        pregunta.texto = form.texto.data
        db.session.commit()
        return redirect(url_for('preguntas_bp.lista_preguntas', tipo_curso_id=pregunta.tipo_curso_id))
    return render_template('examenes/crear_pregunta.html', form=form)

# Borrar pregunta
@preguntas_bp.route('/pregunta/<int:id>/borrar', methods=['POST'])
def borrar_pregunta(id):
    pregunta = Pregunta.query.get_or_404(id)
    tipo_curso_id = pregunta.tipo_curso_id
    db.session.delete(pregunta)
    db.session.commit()
    return redirect(url_for('preguntas_bp.lista_preguntas', tipo_curso_id=tipo_curso_id))

# Gestionar respuestas para una pregunta
@preguntas_bp.route('/pregunta/<int:pregunta_id>/respuestas')
def lista_respuestas(pregunta_id):
    pregunta = Pregunta.query.get_or_404(pregunta_id)
    respuestas = Respuesta.query.filter_by(pregunta_id=pregunta_id).all()
    return render_template('examenes/lista_respuestas.html', pregunta=pregunta, respuestas=respuestas)

# Crear nueva respuesta
@preguntas_bp.route('/pregunta/<int:pregunta_id>/respuesta_nueva', methods=['GET', 'POST'])
def nueva_respuesta(pregunta_id):
    form = RespuestaForm()
    if form.validate_on_submit():
        if form.es_correcta.data:
            Respuesta.query.filter_by(pregunta_id=pregunta_id).update({"es_correcta": False})
        r = Respuesta(texto=form.texto.data, es_correcta=form.es_correcta.data, pregunta_id=pregunta_id)
        db.session.add(r)
        db.session.commit()
        return redirect(url_for('preguntas_bp.lista_respuestas', pregunta_id=pregunta_id))
    return render_template('examenes/crear_respuesta.html', form=form)

# Editar respuesta
@preguntas_bp.route('/respuesta/<int:id>/editar', methods=['GET', 'POST'])
def editar_respuesta(id):
    respuesta = Respuesta.query.get_or_404(id)
    form = RespuestaForm(obj=respuesta)
    if form.validate_on_submit():
        if form.es_correcta.data:
            Respuesta.query.filter_by(pregunta_id=respuesta.pregunta_id).update({"es_correcta": False})
        respuesta.texto = form.texto.data
        respuesta.es_correcta = form.es_correcta.data
        db.session.commit()
        return redirect(url_for('preguntas_bp.lista_respuestas', pregunta_id=respuesta.pregunta_id))
    return render_template('examenes/crear_respuesta.html', form=form)

# Borrar respuesta
@preguntas_bp.route('/respuesta/<int:id>/borrar', methods=['POST'])
def borrar_respuesta(id):
    respuesta = Respuesta.query.get_or_404(id)
    pregunta_id = respuesta.pregunta_id
    db.session.delete(respuesta)
    db.session.commit()
    return redirect(url_for('preguntas_bp.lista_respuestas', pregunta_id=pregunta_id))
