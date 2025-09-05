import os
import unicodedata
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app
from werkzeug.utils import secure_filename
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_diploma import PlantillaDiploma
from .forms import PlantillaDiplomaForm

diplomas_bp = Blueprint('diplomas_bp', __name__)

# Palabras realmente soportadas por la app al rellenar diplomas
CAMPOS_DIPLOMA = [
    {"key": "NOMBRE_ALUMNO",    "desc": "Nombre completo del alumno"},
    {"key": "DNI_ALUMNO",       "desc": "DNI/NIE del alumno"},
    {"key": "NOMBRE_CURSO",     "desc": "Nombre del curso"},
    {"key": "HORAS_CURSO",      "desc": "Duración del curso (horas)"},
    {"key": "FECHA_EXPEDICION", "desc": "Fecha de expedición (dd/mm/aaaa)"},
    {"key": "NOMBRE_FORMADOR",  "desc": "Nombre del formador"},
    {"key": "EMPRESA",          "desc": "Nombre de la empresa"},
    {"key": "POBLACION",        "desc": "Población/ciudad"},
    {"key": "DIRECCION_AULA",   "desc": "Dirección del aula"},
    {"key": "NOTA",             "desc": "Nota del alumno (si aplica)"},
    {"key": "TEXTO_LIBRE",      "desc": "Texto libre de la formación"},
    # Compatibilidad (alias antiguos)
    {"key": "NOMBRE",     "desc": "Alias de NOMBRE_ALUMNO",    "compat": True},
    {"key": "DNI",        "desc": "Alias de DNI_ALUMNO",       "compat": True},
    {"key": "CURSO",      "desc": "Alias de NOMBRE_CURSO",     "compat": True},
    {"key": "HORAS",      "desc": "Alias de HORAS_CURSO",      "compat": True},
    {"key": "FECHA",      "desc": "Alias de FECHA_EXPEDICION", "compat": True},
    {"key": "INSTRUCTOR", "desc": "Alias de NOMBRE_FORMADOR",  "compat": True},
]

def slugify(value):
    return "".join((c if c.isalnum() or c in "-_ " else "_") for c in unicodedata.normalize("NFKD", value))

# Función usada por el sistema para generar/guardar diplomas a partir de una plantilla PDF
def crear_y_guardar_diploma(alumno, formacion):
    # Usa utilidades existentes
    from mi_plataforma_formacion_app.utils.diplomas import rellenar_y_aplanar_pdf, guardar_diploma_pdf
    plantilla = getattr(getattr(formacion, 'tipo_curso', None), 'plantilla_diploma', None)
    if not plantilla or not plantilla.ruta_pdf:
        raise ValueError("La formación no tiene una plantilla de diploma asociada.")

    ruta_plantilla = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.exists(ruta_plantilla):
        raise FileNotFoundError(f"Plantilla no encontrada: {ruta_plantilla}")

    datos = {
        # Campos nuevos (los que debes usar en tus PDFs)
        "NOMBRE_ALUMNO":    alumno.nombre.title() if getattr(alumno, 'nombre', None) else "",
        "DNI_ALUMNO":       getattr(alumno, 'dni', "") or "",
        "NOMBRE_CURSO":     getattr(getattr(formacion, 'tipo_curso', None), 'nombre', "") or "",
        "HORAS_CURSO":      str(getattr(getattr(formacion, 'tipo_curso', None), 'duracion_horas', "") or ""),
        "FECHA_EXPEDICION": formacion.fecha1.strftime('%d/%m/%Y') if getattr(formacion, 'fecha1', None) else "",
        "NOMBRE_FORMADOR":  getattr(getattr(formacion, 'formador', None), 'nombre', "") or "",
        # POBLACION debe venir de formacion.poblacion
        "POBLACION":        getattr(formacion, 'poblacion', "") or getattr(formacion, 'municipio', "") or "",
        # Añadimos DIRECCION_AULA explícito
        "DIRECCION_AULA":   getattr(formacion, 'direccion_aula', "") or "",
        "EMPRESA":          getattr(getattr(formacion, 'empresa', None), 'nombre', "") or "",
        "NOTA":             str(getattr(alumno, 'nota', "") or ""),
        "TEXTO_LIBRE":      getattr(formacion, 'texto_libre', "") or "",
        # Alias antiguos para compatibilidad
        "NOMBRE":           alumno.nombre.title() if getattr(alumno, 'nombre', None) else "",
        "DNI":              getattr(alumno, 'dni', "") or "",
        "CURSO":            getattr(getattr(formacion, 'tipo_curso', None), 'nombre', "") or "",
        "HORAS":            str(getattr(getattr(formacion, 'tipo_curso', None), 'duracion_horas', "") or ""),
        "FECHA":            formacion.fecha1.strftime('%d/%m/%Y') if getattr(formacion, 'fecha1', None) else "",
        "INSTRUCTOR":       getattr(getattr(formacion, 'formador', None), 'nombre', "") or "",
    }

    # Firma opcional del formador (si existe)
    firma_path = None
    if getattr(formacion, 'formador', None) and getattr(formacion.formador, 'firma', None):
        # Si ya viene con prefijo 'firmas_formadores/', úsalo tal cual; si no, prepéndelo
        firma_rel = formacion.formador.firma
        if not firma_rel.startswith('firmas_formadores/'):
            firma_rel = os.path.join('firmas_formadores', firma_rel)
        firma_path = os.path.join(current_app.static_folder, firma_rel)

    pdf_bytes = rellenar_y_aplanar_pdf(ruta_plantilla, datos, firma_path)
    if not pdf_bytes:
        raise Exception("No se pudo generar el PDF autorrellenable")

    return guardar_diploma_pdf(alumno, formacion, pdf_bytes)
@diplomas_bp.route('/plantillas')
def listar_plantillas():
    plantillas = PlantillaDiploma.query.all()
    return render_template('diplomas/listar_plantillas.html', plantillas=plantillas, campos_disponibles=CAMPOS_DIPLOMA)


@diplomas_bp.route('/plantillas/nueva', methods=['GET', 'POST'])
def nueva_plantilla():
    form = PlantillaDiplomaForm()
    if form.validate_on_submit():
        archivo_pdf = None
        if form.archivo.data:
            nombre_seguro = secure_filename(form.archivo.data.filename)
            nuevo_nombre = f"{uuid.uuid4().hex}_{nombre_seguro}"
            ruta_pdf_abs = os.path.join(current_app.static_folder, 'plantillas_diplomas', nuevo_nombre)
            os.makedirs(os.path.dirname(ruta_pdf_abs), exist_ok=True)
            form.archivo.data.save(ruta_pdf_abs)
            archivo_pdf = f"plantillas_diplomas/{nuevo_nombre}"

        plantilla = PlantillaDiploma(nombre=form.nombre.data, ruta_pdf=archivo_pdf)
        db.session.add(plantilla)
        db.session.commit()
        flash('Plantilla guardada correctamente.', 'success')
        return redirect(url_for('diplomas_bp.listar_plantillas'))
    return render_template('diplomas/nueva_plantilla_pdf.html', form=form, campos_disponibles=CAMPOS_DIPLOMA)


@diplomas_bp.route('/plantillas/editar/<int:id>', methods=['GET', 'POST'])
def editar_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    form = PlantillaDiplomaForm(obj=plantilla)
    if form.validate_on_submit():
        plantilla.nombre = form.nombre.data
        if form.archivo.data:
            nombre_seguro = secure_filename(form.archivo.data.filename)
            nuevo_nombre = f"{uuid.uuid4().hex}_{nombre_seguro}"
            ruta_pdf_abs = os.path.join(current_app.static_folder, 'plantillas_diplomas', nuevo_nombre)
            os.makedirs(os.path.dirname(ruta_pdf_abs), exist_ok=True)
            form.archivo.data.save(ruta_pdf_abs)
            plantilla.ruta_pdf = f"plantillas_diplomas/{nuevo_nombre}"
        db.session.commit()
        flash('Plantilla actualizada correctamente.', 'success')
        return redirect(url_for('diplomas_bp.listar_plantillas'))
    return render_template('diplomas/editar_plantilla.html', form=form, plantilla=plantilla, campos_disponibles=CAMPOS_DIPLOMA)


@diplomas_bp.route('/plantillas/eliminar/<int:id>', methods=['POST'])
def eliminar_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    db.session.delete(plantilla)
    db.session.commit()
    flash('Plantilla eliminada', 'success')
    return redirect(url_for('diplomas_bp.listar_plantillas'))


@diplomas_bp.route('/plantillas/pdf/<int:id>')
def vista_previa_pdf_plantilla(id):
    plantilla = PlantillaDiploma.query.get_or_404(id)
    if not plantilla.ruta_pdf:
        abort(404)
    ruta_pdf_abs = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.isfile(ruta_pdf_abs):
        abort(404)
    return send_file(ruta_pdf_abs, mimetype='application/pdf')


# (Opcional) API mínima para inspección
@diplomas_bp.route('/plantillas/api/<int:id>')
def api_plantilla(id):
    p = PlantillaDiploma.query.get_or_404(id)
    return {"id": p.id, "nombre": p.nombre, "ruta_pdf": p.ruta_pdf}
