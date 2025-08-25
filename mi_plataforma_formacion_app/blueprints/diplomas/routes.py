import os
import unicodedata
import uuid
import io
import fitz  # PyMuPDF
from datetime import datetime
from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app
)
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_diploma import PlantillaDiploma
from .forms import PlantillaDiplomaForm

diplomas_bp = Blueprint('diplomas_bp', __name__)

RUTA_DIPLOMAS = r"C:\\Users\\Carlos Nadal\\Documents\\Base de datos alumnos\\mi_plataforma_formacion_nueva\\mi_plataforma_formacion_app\\static\\diplomas"

def slugify(value):
    return "".join((c if c.isalnum() or c in "-_ " else "_") for c in unicodedata.normalize("NFKD", value))

def crear_y_guardar_diploma(alumno, formacion):
    from mi_plataforma_formacion_app.utils.diplomas import rellenar_y_aplanar_pdf, guardar_diploma_pdf
    plantilla = formacion.tipo_curso.plantilla_diploma
    if not plantilla or not plantilla.ruta_pdf:
        raise ValueError("La formación no tiene una plantilla de diploma asociada.")

    ruta_plantilla = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.exists(ruta_plantilla):
        raise FileNotFoundError(f"Plantilla no encontrada: {ruta_plantilla}")

    datos = {
        # Nombres nuevos (mayúsculas y con sufijo)
        'NOMBRE_ALUMNO': alumno.nombre.title(),
        'DNI_ALUMNO': alumno.dni,
        'NOMBRE_CURSO': formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        'HORAS_CURSO': str(formacion.tipo_curso.duracion_horas) if formacion.tipo_curso and formacion.tipo_curso.duracion_horas else '',
        'FECHA_EXPEDICION': formacion.fecha1.strftime('%d/%m/%Y') if formacion.fecha1 else '',
        'NOMBRE_FORMADOR': formacion.formador.nombre if formacion.formador else '',
        'POBLACION': getattr(formacion, 'direccion_aula', '') or '',
        'EMPRESA': formacion.empresa.nombre if formacion.empresa else '',
        'NOTA': str(getattr(alumno, 'nota', '')),
        'TEXTO_LIBRE': getattr(formacion, 'texto_libre', ''),
        # Nombres antiguos (compatibilidad)
        'NOMBRE': alumno.nombre.title(),
        'DNI': alumno.dni,
        'CURSO': formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        'HORAS': str(formacion.tipo_curso.duracion_horas) if formacion.tipo_curso and formacion.tipo_curso.duracion_horas else '',
        'FECHA': formacion.fecha1.strftime('%d/%m/%Y') if formacion.fecha1 else '',
        'INSTRUCTOR': formacion.formador.nombre if formacion.formador else '',
    }
    firma_path = None
    if formacion.formador and formacion.formador.firma:
        firma_path = os.path.join(current_app.static_folder, formacion.formador.firma)
    pdf_bytes = rellenar_y_aplanar_pdf(ruta_plantilla, datos, firma_path)
    if not pdf_bytes:
        raise Exception("No se pudo generar el PDF autorrellenable")

    return guardar_diploma_pdf(alumno, formacion, pdf_bytes)

@diplomas_bp.route('/')
def listar_empresas():
    ruta_base = RUTA_DIPLOMAS
    empresas = [nombre for nombre in os.listdir(ruta_base) if os.path.isdir(os.path.join(ruta_base, nombre))] if os.path.exists(ruta_base) else []
    return render_template("diplomas/listar_empresas.html", empresas=empresas)

@diplomas_bp.route('/<empresa>')
def listar_diplomas_empresa(empresa):
    empresa = slugify(empresa)
    ruta_empresa = os.path.join(RUTA_DIPLOMAS, empresa)
    if not os.path.exists(ruta_empresa):
        abort(404)
@diplomas_bp.route('/plantillas/nueva', methods=['GET', 'POST'])
def nueva_plantilla():
    form = PlantillaDiplomaForm()
    if form.validate_on_submit():
        archivo_pdf = None
        if form.archivo.data:
            nombre_seguro = secure_filename(form.archivo.data.filename)
            nuevo_nombre = f"{uuid.uuid4().hex}_{nombre_seguro}"
            ruta_pdf = os.path.join(current_app.static_folder, 'plantillas_diplomas', nuevo_nombre)
            os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)
            form.archivo.data.save(ruta_pdf)
            archivo_pdf = f"plantillas_diplomas/{nuevo_nombre}"

        plantilla = PlantillaDiploma(
            nombre=form.nombre.data,
            html=form.html.data,
            diploma_docx=form.diploma_docx.data.filename if form.diploma_docx.data else None,
            archivo_pdf=archivo_pdf,
            ruta_pdf=archivo_pdf,
            coordenadas_nombre=form.coordenadas_nombre.data,
            coordenadas_dni=form.coordenadas_dni.data,
            coordenadas_fecha=form.coordenadas_fecha.data,
            coordenadas_curso=form.coordenadas_curso.data,
            coordenadas_empresa=form.coordenadas_empresa.data,
            coordenadas_horas=form.coordenadas_horas.data,
            coordenadas_instructor=form.coordenadas_instructor.data
        )
        db.session.add(plantilla)
        db.session.commit()
        flash('Plantilla PDF guardada correctamente.', 'success')
        return redirect(url_for('diplomas_bp.listar_plantillas'))

    return render_template('diplomas/nueva_plantilla_pdf.html', form=form)
    if not os.path.isfile(ruta):
        abort(404)
    return send_file(ruta, as_attachment=True)

@diplomas_bp.route('/plantillas')
def listar_plantillas():
    plantillas = PlantillaDiploma.query.all()
    return render_template('diplomas/listar_plantillas.html', plantillas=plantillas)

@diplomas_bp.route('/plantillas/editar/<int:id>', methods=['GET', 'POST'])
def editar_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    form = PlantillaDiplomaForm(obj=plantilla)

    if form.validate_on_submit():
        plantilla.nombre = form.nombre.data

        if form.archivo.data:
            nombre_seguro = secure_filename(form.archivo.data.filename)
            ruta_pdf = os.path.join(current_app.static_folder, 'plantillas_diplomas', nombre_seguro)
            os.makedirs(os.path.dirname(ruta_pdf), exist_ok=True)
            form.archivo.data.save(ruta_pdf)
            plantilla.ruta_pdf = f"plantillas_diplomas/{nombre_seguro}"



        db.session.commit()
        flash('Plantilla actualizada correctamente.', 'success')
        return redirect(url_for('diplomas_bp.listar_plantillas'))

    return render_template('diplomas/editar_plantilla.html', form=form, plantilla=plantilla)

@diplomas_bp.route('/plantillas/eliminar/<int:id>', methods=['POST'])
def eliminar_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    db.session.delete(plantilla)
    db.session.commit()
    flash('Plantilla eliminada', 'success')
    return redirect(url_for('diplomas_bp.listar_plantillas'))

@diplomas_bp.route('/plantillas/api/<int:id>')
def api_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    return {'html': plantilla.html}

@diplomas_bp.route("/plantillas/visual_editor", methods=["GET"])
@diplomas_bp.route("/editor")
def visual_editor():
    return render_template("diplomas/editor_visual.html")

@diplomas_bp.route('/plantillas/pdf/<int:id>')
def vista_previa_pdf_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    if not plantilla.ruta_pdf:
        abort(404)
    ruta_pdf = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.isfile(ruta_pdf):
        abort(404)
    return send_file(ruta_pdf, mimetype='application/pdf')
