import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from werkzeug.utils import secure_filename
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.models.plantilla_diploma import PlantillaDiploma
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from .forms import TipoCursoForm

tipo_curso_bp = Blueprint('tipo_curso_bp', __name__)

UPLOAD_FOLDER = os.path.join('static', 'pdf_tipos_curso')

@tipo_curso_bp.route('/')
def gestion_tipo_curso():
    tipos = TipoCurso.query.all()
    return render_template('tipo_curso/gestion_tipo_curso.html', tipos=tipos)

@tipo_curso_bp.route('/nuevo', methods=['GET', 'POST'])
def crear_tipo_curso():
    form = TipoCursoForm()
    form.set_plantilla_choices()
    form.set_examen_choices()
    form.set_plantilla_acta_choices()

    if form.validate_on_submit():

        pdf_filename = None
        if form.pdf_temario.data:
            file = form.pdf_temario.data
            pdf_filename = secure_filename(file.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file.save(os.path.join(UPLOAD_FOLDER, pdf_filename))

        pdf_objetivos_filename = None
        if form.pdf_objetivos.data:
            file_obj = form.pdf_objetivos.data
            pdf_objetivos_filename = secure_filename(file_obj.filename)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file_obj.save(os.path.join(UPLOAD_FOLDER, pdf_objetivos_filename))

        if form.validez_permanente.data:
            validez_meses = 0
            requiere_renovacion = False
        else:
            validez_meses = form.validez_meses.data or 0
            requiere_renovacion = validez_meses > 0

        tipo = TipoCurso(
            nombre=form.nombre.data,
            duracion_horas=form.duracion_horas.data,
            temario=form.temario.data,
            # objetivos=form.objetivos.data,  # Ya no se usa campo texto
            pdf_temario=pdf_filename,
            pdf_objetivos=pdf_objetivos_filename,
            examen_modelo_id=form.examen_modelo_id.data or None,
            validez_meses=validez_meses,
            requiere_renovacion=requiere_renovacion,
            color=form.color.data,
            plantilla_diploma_id=form.plantilla_diploma_id.data or None,
            plantilla_acta_id=form.plantilla_acta_id.data or None
        )
        db.session.add(tipo)
        db.session.commit()
        flash('Tipo de curso creado', 'success')
        return redirect(url_for('tipo_curso_bp.gestion_tipo_curso'))
    return render_template('tipo_curso/crear_tipo_curso.html', form=form)

@tipo_curso_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_tipo_curso(id):
    tipo = TipoCurso.query.get_or_404(id)
    form = TipoCursoForm(obj=tipo)
    form.set_examen_choices()
    form.set_plantilla_choices()
    form.set_plantilla_acta_choices()

    if request.method == 'GET':
        form.examen_modelo_id.data = tipo.examen_modelo_id or 0
        form.validez_permanente.data = (tipo.validez_meses == 0)
        form.validez_meses.data = tipo.validez_meses
        form.color.data = tipo.color or "#4287f5"
        form.plantilla_diploma_id.data = tipo.plantilla_diploma_id or 0
        form.plantilla_acta_id.data = tipo.plantilla_acta_id or 0

    if form.validate_on_submit():
        tipo.nombre = form.nombre.data
        tipo.duracion_horas = form.duracion_horas.data
        tipo.temario = form.temario.data
        # tipo.objetivos = form.objetivos.data  # Ya no se usa campo texto
        tipo.examen_modelo_id = form.examen_modelo_id.data or None
        tipo.color = form.color.data
        tipo.plantilla_diploma_id = form.plantilla_diploma_id.data or None
        tipo.plantilla_acta_id = form.plantilla_acta_id.data or None


        file_field = form.pdf_temario.data
        if file_field and hasattr(file_field, "filename") and file_field.filename:
            pdf_filename = secure_filename(file_field.filename)
            folder = os.path.join(current_app.root_path, 'static', 'pdf_tipos_curso')
            os.makedirs(folder, exist_ok=True)
            file_field.save(os.path.join(folder, pdf_filename))
            tipo.pdf_temario = pdf_filename

        file_objetivos = form.pdf_objetivos.data
        if file_objetivos and hasattr(file_objetivos, "filename") and file_objetivos.filename:
            pdf_objetivos_filename = secure_filename(file_objetivos.filename)
            folder = os.path.join(current_app.root_path, 'static', 'pdf_tipos_curso')
            os.makedirs(folder, exist_ok=True)
            file_objetivos.save(os.path.join(folder, pdf_objetivos_filename))
            tipo.pdf_objetivos = pdf_objetivos_filename

        if form.validez_permanente.data:
            tipo.validez_meses = 0
            tipo.requiere_renovacion = False
        else:
            tipo.validez_meses = form.validez_meses.data or 0
            tipo.requiere_renovacion = tipo.validez_meses > 0

        db.session.commit()
        flash('Tipo de curso actualizado', 'success')
        return redirect(url_for('tipo_curso_bp.gestion_tipo_curso'))
    return render_template('tipo_curso/editar_tipo_curso.html', form=form, tipo=tipo)

@tipo_curso_bp.route('/borrar/<int:id>', methods=['POST'])
def borrar_tipo_curso(id):
    tipo = TipoCurso.query.get_or_404(id)
    db.session.delete(tipo)
    db.session.commit()
    flash('Tipo de curso borrado', 'success')
    return redirect(url_for('tipo_curso_bp.gestion_tipo_curso'))

@tipo_curso_bp.route('/info/<int:id>')
def info_tipo_curso(id):
    tipo = TipoCurso.query.get_or_404(id)
    return jsonify({
        "nombre": tipo.nombre,
        "duracion_horas": tipo.duracion_horas,
        "temario": tipo.temario,
        "pdf_url": url_for('static', filename='pdf_tipos_curso/' + tipo.pdf_temario) if tipo.pdf_temario else None,
        "pdf_objetivos_url": url_for('static', filename='pdf_tipos_curso/' + tipo.pdf_objetivos) if tipo.pdf_objetivos else None,
        "validez_meses": tipo.validez_meses,
        "validez_permanente": tipo.validez_meses == 0
    })
