import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app
from werkzeug.utils import secure_filename
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from .forms import PlantillaActaForm

actas_bp = Blueprint('actas_bp', __name__, url_prefix='/actas')

# === Placeholders REALES admitidos para ACTAS ===
CAMPOS_ACTA = [
    {"key":"EMPRESA",         "desc":"Nombre de la empresa"},
    {"key":"NOMBRE_CURSO",    "desc":"Nombre del curso"},
    {"key":"CURSO",           "desc":"Alias de NOMBRE_CURSO", "compat":True},
    {"key":"FECHA",           "desc":"Fecha de la formación (dd/mm/aaaa)"},
    {"key":"FECHA2",          "desc":"Fecha de la segunda sesión (si existe)"},
    {"key":"HORARIO",         "desc":"Horario de la formación"},
    {"key":"HORARIO2",        "desc":"Horario de la segunda sesión (si existe)"},
    {"key":"HORAS",           "desc":"Número de horas del curso"},
    {"key":"LUGAR",           "desc":"Nombre del aula/centro"},
    {"key":"DIRECCION_AULA",  "desc":"Dirección postal del aula"},
    {"key":"POBLACION",       "desc":"Población/ciudad"},
    {"key":"REFERENCIA",      "desc":"Referencia de la formación"},
    {"key":"FUNDAE",          "desc":"Sí/No (formación bonificable)"},
    {"key":"FORMADOR",        "desc":"Nombre del formador"},
    {"key":"FIRMA_FORMADOR",  "desc":"Firma del formador (si se inserta como imagen)"},
    {"key":"ALUMNOS",         "desc":"Listado de alumnos (uno por línea: Nombre — DNI)"},
]


def _ensure_dirs(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)


@actas_bp.route('/plantillas')
def listar_plantillas():
    plantillas = PlantillaActa.query.all()
    return render_template('actas/listar_plantillas.html', plantillas=plantillas, campos_disponibles=CAMPOS_ACTA)


@actas_bp.route('/plantillas/nueva', methods=['GET','POST'])
def nueva_plantilla():
    form = PlantillaActaForm()
    if form.validate_on_submit():
        archivo_pdf = None
        if hasattr(form, 'archivo') and form.archivo.data:
            seguro = secure_filename(form.archivo.data.filename)
            nuevo = f"{uuid.uuid4().hex}_{seguro}"
            fs_path = os.path.join(current_app.static_folder, 'plantillas_actas', nuevo)
            _ensure_dirs(fs_path)
            form.archivo.data.save(fs_path)
            archivo_pdf = f"plantillas_actas/{nuevo}"

        db.session.add(PlantillaActa(nombre=form.nombre.data, ruta_pdf=archivo_pdf))
        db.session.commit()
        flash('Plantilla de acta guardada correctamente.', 'success')
        return redirect(url_for('actas_bp.listar_plantillas'))
    return render_template('actas/nueva_plantilla_pdf.html', form=form, campos_disponibles=CAMPOS_ACTA)


@actas_bp.route('/plantillas/editar/<int:id>', methods=['GET','POST'])
def editar_plantilla(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    form = PlantillaActaForm(obj=plantilla)
    if form.validate_on_submit():
        plantilla.nombre = form.nombre.data
        if hasattr(form, 'archivo') and form.archivo.data:
            seguro = secure_filename(form.archivo.data.filename)
            nuevo = f"{uuid.uuid4().hex}_{seguro}"
            fs_path = os.path.join(current_app.static_folder, 'plantillas_actas', nuevo)
            _ensure_dirs(fs_path)
            form.archivo.data.save(fs_path)
            plantilla.ruta_pdf = f"plantillas_actas/{nuevo}"
        db.session.commit()
        flash('Plantilla de acta actualizada correctamente.', 'success')
        return redirect(url_for('actas_bp.listar_plantillas'))
    if request.method == 'GET':
        form.nombre.data = plantilla.nombre
    return render_template('actas/editar_plantilla.html', form=form, plantilla=plantilla, campos_disponibles=CAMPOS_ACTA)


@actas_bp.route('/plantillas/eliminar/<int:id>', methods=['POST'])
def eliminar_plantilla(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    db.session.delete(plantilla)
    db.session.commit()
    flash('Plantilla de acta eliminada.', 'success')
    return redirect(url_for('actas_bp.listar_plantillas'))


@actas_bp.route('/plantillas/pdf/<int:id>')
def vista_previa_pdf_plantilla(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    if not plantilla.ruta_pdf:
        abort(404)
    ruta_pdf = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.isfile(ruta_pdf):
        abort(404)
    return send_file(ruta_pdf, mimetype='application/pdf')


@actas_bp.route('/plantillas/generar_desde_formacion/<int:formacion_id>')
def generar_acta_desde_formacion(formacion_id):
    """Genera un acta PDF rellenando la plantilla asociada a la formación.

    Usa la misma lógica que en Diplomas: construye el diccionario de datos,
    llama a `rellenar_y_aplanar_pdf` y devuelve el PDF generado. Maneja errores
    y evita 500s devolviendo un flash y redirección cuando falla.
    """
    try:
        # import modelos relacionados aquí para evitar import cycles
        from mi_plataforma_formacion_app.models.formacion import Formacion
        from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
        from mi_plataforma_formacion_app.models.alumno import Alumno
        import io
        # Obtener la formación
        formacion = Formacion.query.get_or_404(formacion_id)

        # Intentar obtener la plantilla asociada al tipo de curso
        plantilla_id = None
        try:
            plantilla_id = getattr(getattr(formacion, 'tipo_curso', None), 'plantilla_acta_id', None)
        except Exception:
            plantilla_id = None

        plantilla = None
        if plantilla_id:
            plantilla = PlantillaActa.query.get(plantilla_id)
        # Si no hay plantilla asociada, intentar usar la primera disponible
        if not plantilla:
            plantilla = PlantillaActa.query.first()

        if not plantilla or not plantilla.ruta_pdf:
            flash('No hay plantilla de acta disponible para esta formación.', 'danger')
            return redirect(request.referrer or url_for('actas_bp.listar_plantillas'))

        ruta_plantilla = plantilla.ruta_pdf
        # Aceptar rutas relativas dentro de static/
        if not os.path.isabs(ruta_plantilla):
            ruta_plantilla = os.path.join(current_app.static_folder, ruta_plantilla)

        if not os.path.exists(ruta_plantilla):
            flash('Archivo de plantilla PDF no encontrado en el servidor.', 'danger')
            return redirect(request.referrer or url_for('actas_bp.listar_plantillas'))

        # Construir diccionario de datos (keys insensibles a mayúsculas) — seguir CAMPOS_ACTA
        datos = {
            'EMPRESA': getattr(getattr(formacion, 'empresa', None), 'nombre', '') or '',
            'NOMBRE_CURSO': getattr(getattr(formacion, 'tipo_curso', None), 'nombre', '') or '',
            'CURSO': getattr(getattr(formacion, 'tipo_curso', None), 'nombre', '') or '',
            'FECHA': formacion.fecha1.strftime('%d/%m/%Y') if getattr(formacion, 'fecha1', None) else '',
            'FECHA2': formacion.fecha2.strftime('%d/%m/%Y') if getattr(formacion, 'fecha2', None) else '',
            'HORARIO': getattr(formacion, 'horario', '') or '',
            'HORARIO2': getattr(formacion, 'horario2', '') or '',
            'HORAS': str(getattr(getattr(formacion, 'tipo_curso', None), 'duracion_horas', '') or ''),
            'LUGAR': getattr(formacion, 'direccion_aula', '') or getattr(formacion, 'lugar', '') or '',
            'DIRECCION_AULA': getattr(formacion, 'direccion_aula', '') or '',
            'POBLACION': getattr(formacion, 'poblacion', '') or getattr(formacion, 'municipio', '') or '',
            'REFERENCIA': getattr(formacion, 'referencia', '') or '',
            'FUNDAE': 'Sí' if getattr(formacion, 'fundae', False) else 'No',
            'FORMADOR': getattr(getattr(formacion, 'formador', None), 'nombre', '') or '',
        }

        # alumnos: listar nombres y dnis si existen
        try:
            relaciones = getattr(formacion, 'alumno_formaciones', None) or getattr(formacion, 'alumnos_rel', None) or []
            if relaciones:
                alumnos_txt = '\n'.join([f"{getattr(r, 'alumno', r).nombre} - {getattr(getattr(r, 'alumno', r), 'dni', '')}" for r in relaciones])
            else:
                alumnos_txt = ''
            datos['ALUMNOS'] = alumnos_txt
        except Exception:
            datos['ALUMNOS'] = ''

        # Firma opcional
        firma_path = None
        try:
            if getattr(formacion, 'formador', None) and getattr(formacion.formador, 'firma', None):
                firma_rel = formacion.formador.firma
                if not firma_rel.startswith('firmas_formadores/'):
                    firma_rel = os.path.join('firmas_formadores', firma_rel)
                firma_path = os.path.join(current_app.static_folder, firma_rel)
                if not os.path.isfile(firma_path):
                    firma_path = None
        except Exception:
            firma_path = None

        # Llamar utilitario de diplomas que sabe aplanar campos y soporta key case-insensitive
        from mi_plataforma_formacion_app.utils.diplomas import rellenar_y_aplanar_pdf

        pdf_bytes = rellenar_y_aplanar_pdf(ruta_plantilla, datos, firma_path)
        if not pdf_bytes:
            flash('No se pudo generar el PDF del acta.', 'danger')
            return redirect(request.referrer or url_for('actas_bp.listar_plantillas'))

        # Devolver PDF en memoria
        return send_file(io.BytesIO(pdf_bytes), download_name=f"acta_{formacion_id}.pdf", mimetype='application/pdf')

    except Exception as e:
        # No mostrar stack al usuario; loguear en consola y devolver mensaje amigable
        current_app.logger.exception('Error generando acta PDF')
        flash('Ha ocurrido un error al generar el acta. Comprueba los logs del servidor.', 'danger')
        return redirect(request.referrer or url_for('actas_bp.listar_plantillas'))
