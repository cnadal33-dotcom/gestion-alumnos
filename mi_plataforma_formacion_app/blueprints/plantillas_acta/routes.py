from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
import os
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.formador import Formador
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from .forms import PlantillaActaForm
from .generar_acta_form import GenerarActaForm

# Definir blueprint en la primera línea
plantillas_acta_bp = Blueprint('plantillas_acta_bp', __name__, url_prefix='/actas/plantillas')

@plantillas_acta_bp.route('/generar_acta_pdf/<int:formacion_id>')
def generar_acta_pdf(formacion_id):
    import tempfile
    from flask import send_file, flash, redirect, request
    from mi_plataforma_formacion_app.utils.pdf_fill import rellenar_pdf
    formacion = Formacion.query.get_or_404(formacion_id)
    plantilla = PlantillaActa.query.filter(PlantillaActa.id == formacion.tipo_curso.plantilla_acta_id).first()
    if not plantilla or not plantilla.ruta_pdf:
        flash("La plantilla de acta no tiene PDF asociado.", "danger")
        return redirect(request.referrer or url_for('formaciones_bp.ficha_formacion', formacion_id=formacion_id))
    data = {
        'curso': formacion.tipo_curso.nombre if formacion.tipo_curso else '',
        'empresa': formacion.empresa.nombre if formacion.empresa else '',
        'fecha': formacion.fecha1.strftime('%d/%m/%Y') if formacion.fecha1 else '',
        'lugar': formacion.lugar if hasattr(formacion, 'lugar') else '',
        'horario': f"{formacion.hora_inicio1.strftime('%H:%M') if formacion.hora_inicio1 else ''} - {formacion.hora_fin1.strftime('%H:%M') if formacion.hora_fin1 else ''}",
        'formador': formacion.formador.nombre if formacion.formador else '',
    }
    alumnos_str = '\n'.join([
        f"{idx+1}. {rel.alumno.nombre} - {rel.alumno.dni} - {rel.alumno.email or ''}"
        for idx, rel in enumerate(formacion.alumno_formaciones)
    ])
    data['alumnos'] = alumnos_str
    ruta_absoluta_plantilla = plantilla.ruta_pdf
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        ruta_temporal = temp_file.name
        rellenar_pdf(ruta_absoluta_plantilla, ruta_temporal, data)
    return send_file(ruta_temporal, download_name=f"acta_{formacion_id}.pdf", as_attachment=True, mimetype='application/pdf')
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.formador import Formador
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.alumno import Alumno
from .forms import PlantillaActaForm
from .generar_acta_form import GenerarActaForm

plantillas_acta_bp = Blueprint('plantillas_acta_bp', __name__, url_prefix='/actas/plantillas')

@plantillas_acta_bp.route('/generar_desde_formacion/<int:formacion_id>', methods=['GET', 'POST'])
def generar_desde_formacion(formacion_id):
    formacion = Formacion.query.get_or_404(formacion_id)
    alumnos = AlumnoFormacion.query.filter_by(formacion_id=formacion.id).all()
    formador = formacion.formador
    plantilla_pdf = None
    if request.method == 'POST' and 'plantilla_pdf' in request.files:
        archivo = request.files['plantilla_pdf']
        if archivo.filename:
            from werkzeug.utils import secure_filename
            nombre_seguro = secure_filename(archivo.filename)
            ruta_pdf_abs = os.path.join(current_app.static_folder, 'plantillas_acta', nombre_seguro)
            os.makedirs(os.path.dirname(ruta_pdf_abs), exist_ok=True)
            archivo.save(ruta_pdf_abs)
            plantilla_pdf = f"plantillas_acta/{nombre_seguro}"
    return render_template('plantillas_acta/generar_desde_formacion.html', formacion=formacion, alumnos=alumnos, formador=formador, plantilla_pdf=plantilla_pdf)
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.formador import Formador
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.alumno import Alumno
from .forms import PlantillaActaForm
from .generar_acta_form import GenerarActaForm

plantillas_acta_bp = Blueprint('plantillas_acta_bp', __name__, url_prefix='/actas/plantillas')

@plantillas_acta_bp.route('/generar', methods=['GET', 'POST'])
def generar_acta():
    form = GenerarActaForm()
    # Cargar opciones de formaciones y formadores
    form.formacion_id.choices = [(f.id, f.referencia or f.id) for f in Formacion.query.order_by(Formacion.id.desc()).all()]
    form.formador_id.choices = [(fo.id, fo.nombre) for fo in Formador.query.order_by(Formador.nombre).all()]
    alumnos = []
    datos_formacion = None
    datos_formador = None
    mostrar_datos = False
    if form.validate_on_submit():
        formacion = Formacion.query.get(form.formacion_id.data)
        formador = Formador.query.get(form.formador_id.data)
        alumnos = AlumnoFormacion.query.filter_by(formacion_id=formacion.id).all()
        datos_formacion = formacion
        datos_formador = formador
        mostrar_datos = True
    return render_template('plantillas_acta/generar_acta.html', form=form, alumnos=alumnos, datos_formacion=datos_formacion, datos_formador=datos_formador, mostrar_datos=mostrar_datos)

@plantillas_acta_bp.route('/pdf/<int:id>')
def vista_previa_pdf(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    if not plantilla.ruta_pdf:
        return "No hay PDF para esta plantilla", 404
    ruta_pdf = os.path.join(current_app.static_folder, plantilla.ruta_pdf)
    if not os.path.isfile(ruta_pdf):
        return "Archivo PDF no encontrado", 404
    from flask import send_file
    return send_file(ruta_pdf, mimetype='application/pdf')

@plantillas_acta_bp.route('/')
def listar():
    plantillas = PlantillaActa.query.order_by(PlantillaActa.nombre).all()
    return render_template('plantillas_acta/listar.html', plantillas=plantillas)

@plantillas_acta_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    form = PlantillaActaForm(obj=plantilla)
    if form.validate_on_submit():
        plantilla.nombre = form.nombre.data
    # plantilla.html = form.html.data  # Eliminado: ya no se usa código HTML
        if form.archivo_pdf.data:
            from werkzeug.utils import secure_filename
            nombre_seguro = secure_filename(form.archivo_pdf.data.filename)
            ruta_pdf_abs = os.path.join(current_app.static_folder, 'plantillas_acta', nombre_seguro)
            os.makedirs(os.path.dirname(ruta_pdf_abs), exist_ok=True)
            form.archivo_pdf.data.save(ruta_pdf_abs)
            plantilla.ruta_pdf = f"plantillas_acta/{nombre_seguro}"
        db.session.commit()
        flash('Plantilla de acta actualizada correctamente.', 'success')
        return redirect(url_for('plantillas_acta_bp.listar'))
    return render_template('plantillas_acta/editar.html', form=form, plantilla=plantilla)

@plantillas_acta_bp.route('/borrar/<int:id>', methods=['POST'])
def borrar(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    db.session.delete(plantilla)
    db.session.commit()
    flash('Plantilla de acta eliminada.', 'success')
    return redirect(url_for('plantillas_acta_bp.listar'))

@plantillas_acta_bp.route('/api/<int:id>')
def api_plantilla(id):
    plantilla = PlantillaActa.query.get_or_404(id)
    return {'html': None}  # Eliminado: ya no se usa código HTML

# Ruta para crear nueva plantilla de acta
@plantillas_acta_bp.route('/crear', methods=['GET', 'POST'])
def crear():
    form = PlantillaActaForm()
    if form.validate_on_submit():
        plantilla = PlantillaActa(nombre=form.nombre.data)
        if form.archivo_pdf.data:
            from werkzeug.utils import secure_filename
            nombre_seguro = secure_filename(form.archivo_pdf.data.filename)
            ruta_pdf_abs = os.path.join(current_app.static_folder, 'plantillas_acta', nombre_seguro)
            os.makedirs(os.path.dirname(ruta_pdf_abs), exist_ok=True)
            form.archivo_pdf.data.save(ruta_pdf_abs)
            plantilla.ruta_pdf = f"plantillas_acta/{nombre_seguro}"
        db.session.add(plantilla)
        db.session.commit()
        flash('Plantilla de acta creada correctamente.', 'success')
        return redirect(url_for('plantillas_acta_bp.listar'))
    return render_template('plantillas_acta/crear.html', form=form)
