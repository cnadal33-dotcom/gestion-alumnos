from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models.empresa import Empresa
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.extensions import db
from .forms import AlumnoForm, ImportarAlumnosExcelForm
import pandas as pd
import openpyxl
alumnos_bp = Blueprint('alumnos_bp', __name__)

# --- RUTA: Importar alumnos desde Excel ---
@alumnos_bp.route('/importar_excel', methods=['GET', 'POST'], endpoint='importar_alumnos_excel')
def importar_alumnos_excel():
    form = ImportarAlumnosExcelForm()
    if form.validate_on_submit():
        archivo = form.archivo.data
        try:
            df = pd.read_excel(archivo)
        except Exception as e:
            flash(f"Error al leer el archivo Excel: {e}", "danger")
            return render_template('alumnos/importar_alumnos_excel.html', form=form)
        requeridos = {'nombre', 'dni', 'email'}
        if not requeridos.issubset(df.columns.str.lower()):
            flash("El archivo debe tener las columnas: nombre, dni, email (y opcional: telefono, empresa)", "danger")
            return render_template('alumnos/importar_alumnos_excel.html', form=form)
        count = 0
        for _, row in df.iterrows():
            nombre = str(row.get('nombre', '')).strip().title()
            dni = str(row.get('dni', '')).strip().upper()
            email = str(row.get('email', '')).strip()
            telefono = str(row.get('telefono', '')).strip() if 'telefono' in row else None
            empresa_nombre = str(row.get('empresa', '')).strip() if 'empresa' in row else None
            if not nombre or not dni or not email:
                continue
            if Alumno.query.filter_by(dni=dni).first() or Alumno.query.filter_by(email=email).first():
                continue
            empresa_id = None
            if empresa_nombre:
                empresa = Empresa.query.filter(Empresa.nombre.ilike(empresa_nombre)).first()
                if empresa:
                    empresa_id = empresa.id
            nuevo = Alumno(nombre=nombre, dni=dni, email=email, telefono=telefono, empresa_id=empresa_id)
            db.session.add(nuevo)
            count += 1
        db.session.commit()
        flash(f"Importación completada. {count} alumnos añadidos.", "success")
        return redirect(url_for('alumnos_bp.lista_alumnos'))
    return render_template('alumnos/importar_alumnos_excel.html', form=form)
from .forms_dni import DniForm
from datetime import date, datetime
import os
import io
import pdfkit
import unicodedata
import re # Importa el módulo re
from flask import get_flashed_messages

from mi_plataforma_formacion_app.utils.diplomas import crear_y_guardar_diploma
from mi_plataforma_formacion_app.utils.emailing import enviar_diploma_por_email
from .forms_codigo import CodigoFormacionForm

# --- Configuración de Logging ---
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# --- Función de Normalización Única y Robusta ---
def normaliza_nombre_archivo(txt):
    if not isinstance(txt, str):
        logger.warning(f"Intentando normalizar un valor no string: {txt}. Convirtiendo a string vacío.")
        txt = ""
    txt = unicodedata.normalize('NFD', txt).encode('ascii', 'ignore').decode('utf-8')
    txt = re.sub(r'[^a-zA-Z0-9\\s]', '_', txt)
    txt = txt.lower().strip() 
    txt = re.sub(r'\\s+', '_', txt) 
    txt = re.sub(r'_{2,}', '_', txt)
    txt = txt.strip('_')
    logger.debug(f"normaliza_nombre_archivo('{txt}') -> '{txt}'")
    return txt

@alumnos_bp.app_context_processor
def inject_buscar_diploma_pdf():
    return dict(buscar_diploma_pdf=buscar_diploma_pdf)

def buscar_diploma_pdf(formacion, alumno):
    if not formacion or not formacion.empresa or not formacion.fecha1 or not alumno:
        logger.warning("buscar_diploma_pdf: Datos de formación o alumno incompletos.")
        return None
    empresa_normalizada = normaliza_nombre_archivo(formacion.empresa.nombre)
    fecha_formacion_str = formacion.fecha1.strftime("%Y-%m-%d")
    alumno_nombre_normalizado = normaliza_nombre_archivo(alumno.nombre)
    nombre_archivo_diploma = f"diploma_{alumno_nombre_normalizado}.pdf"
    ruta_relativa_a_static = os.path.join(
        'diplomas',
        empresa_normalizada,
        fecha_formacion_str,
        nombre_archivo_diploma
    ).replace(os.sep, '/')
    ruta_absoluta_static_dir = current_app.static_folder
    ruta_completa_en_fs = os.path.join(ruta_absoluta_static_dir, ruta_relativa_a_static)
    logger.debug(f"buscar_diploma_pdf: Buscando diploma en FS: {ruta_completa_en_fs}")
    if os.path.exists(ruta_completa_en_fs):
        url_del_diploma = url_for('static', filename=ruta_relativa_a_static)
        logger.info(f"buscar_diploma_pdf: Diploma encontrado. URL generada: {url_del_diploma}")
        return url_del_diploma
    else:
        logger.warning(f"buscar_diploma_pdf: Diploma NO ENCONTRADO en: {ruta_completa_en_fs}")
        carpeta_diploma_fs = os.path.dirname(ruta_completa_en_fs)
        if not os.path.exists(carpeta_diploma_fs):
            logger.warning(f"buscar_diploma_pdf: La CARPETA '{carpeta_diploma_fs}' NO EXISTE.")
        else:
            logger.warning(f"buscar_diploma_pdf: La CARPETA '{carpeta_diploma_fs}' EXISTE, pero el archivo '{nombre_archivo_diploma}' no está dentro.")
            logger.warning(f"Archivos encontrados en '{carpeta_diploma_fs}': {os.listdir(carpeta_diploma_fs)}")
        return None
def guardar_diploma_pdf(alumno, formacion, pdf_bytes):
    if not alumno or not formacion or not formacion.empresa or not formacion.fecha1 or not pdf_bytes:
        logger.warning("guardar_diploma_pdf: Datos incompletos. No se guardará el diploma.")
        return None
    empresa_normalizada = normaliza_nombre_archivo(formacion.empresa.nombre)
    fecha_formacion_str = formacion.fecha1.strftime("%Y-%m-%d")
    alumno_nombre_normalizado = normaliza_nombre_archivo(alumno.nombre)
    nombre_archivo_diploma = f"diploma_{alumno_nombre_normalizado}.pdf"
    ruta_absoluta_static_dir = current_app.static_folder
    ruta_carpeta_destino_fs = os.path.join(
        ruta_absoluta_static_dir,
        'diplomas',
        empresa_normalizada,
        fecha_formacion_str
    )
    try:
        os.makedirs(ruta_carpeta_destino_fs, exist_ok=True)
        logger.info(f"guardar_diploma_pdf: Carpeta de destino asegurada: {ruta_carpeta_destino_fs}")
    except OSError as e:
        logger.exception(f"guardar_diploma_pdf: Error al crear la carpeta de destino '{ruta_carpeta_destino_fs}': {e}")
        return None
    ruta_pdf_completa_fs = os.path.join(ruta_carpeta_destino_fs, nombre_archivo_diploma)
    try:
        with open(ruta_pdf_completa_fs, 'wb') as f:
            f.write(pdf_bytes)
        logger.info(f"guardar_diploma_pdf: Diploma guardado correctamente en: {ruta_pdf_completa_fs}")
        return ruta_pdf_completa_fs
    except IOError as e:
        logger.exception(f"guardar_diploma_pdf: Error al guardar el archivo PDF en '{ruta_pdf_completa_fs}': {e}")
        return None

@alumnos_bp.route('/', methods=['GET'])
def lista_alumnos():
    q = request.args.get("q", "").strip()
    alumnos = Alumno.query
    if q:
        alumnos = alumnos.filter(
            (Alumno.nombre.ilike(f"%{q}%")) |
            (Alumno.dni.ilike(f"%{q}%")) |
            (Alumno.email.ilike(f"%{q}%"))
        )
    alumnos = alumnos.order_by(Alumno.nombre).all()
    return render_template('alumnos/lista_alumnos.html', alumnos=alumnos, query=q)

@alumnos_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_alumno():
    formacion_id = request.args.get('formacion_id', type=int)
    dni_query = request.args.get('dni', type=str)
    form = AlumnoForm()
    empresas = Empresa.query.all()
    form.empresa_id.choices = [(0, 'Sin empresa')] + [(e.id, e.nombre) for e in empresas]
    if dni_query:
        form.dni.data = dni_query.upper()
    # Preseleccionar empresa si viene de acceso por formación
    if formacion_id:
        formacion = Formacion.query.get(formacion_id)
        if formacion and formacion.empresa_id:
            form.empresa_id.data = formacion.empresa_id
    if form.validate_on_submit():
        dni_value = form.dni.data.strip().upper()
        existe_email = Alumno.query.filter_by(email=form.email.data).first()
        existe_dni = Alumno.query.filter_by(dni=dni_value).first()
        if existe_email:
            form.email.errors.append("Ya existe un alumno con ese email.")
        if existe_dni:
            form.dni.errors.append("Ya existe un alumno con ese DNI.")
        if not existe_email and not existe_dni:
            # Recoger empresa_id del input oculto (autocompletado)
            empresa_id = request.form.get('empresa_id')
            try:
                empresa_id = int(empresa_id) if empresa_id and empresa_id.isdigit() else None
            except Exception:
                empresa_id = None
            if empresa_id == 0:
                empresa_id = None
            nuevo = Alumno(
                nombre=form.nombre.data.strip().title(),
                dni=dni_value,
                email=form.email.data,
                telefono=form.telefono.data,
                interesado_mas_cursos=form.interesado_mas_cursos.data,
                empresa_id=empresa_id,
                observaciones=form.observaciones.data
            )
            db.session.add(nuevo)
            db.session.commit()
            if formacion_id:
                formacion = Formacion.query.get(formacion_id)
                tipo = formacion.tipo_curso
                con_examen = tipo.examen_modelo is not None

                rel = AlumnoFormacion(alumno_id=nuevo.id, formacion_id=formacion_id)
                db.session.add(rel)
                db.session.commit()

                if not con_examen:
                    rel.aprobado = True
                    db.session.commit()
                    crear_y_guardar_diploma(nuevo, formacion)
                    return render_template("alumnos/gracias_inscripcion.html", alumno=nuevo, formacion=formacion)

                flash("Alumno registrado correctamente. ¡Ya puedes realizar el examen!", "success")
                return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=nuevo.id))
            else:
                flash("Alumno creado correctamente.", "success")
                return redirect(url_for('alumnos_bp.lista_alumnos'))
    return render_template('alumnos/nuevo_alumno.html', form=form)
@alumnos_bp.route('/acceso_formacion', methods=['GET', 'POST'])
def acceso_formacion():
    form = CodigoFormacionForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.strip()
        formacion = Formacion.query.filter_by(referencia=codigo).first()
        if formacion:
            return redirect(url_for('alumnos_bp.acceso_alumno', formacion_id=formacion.id))
        else:
            flash('Código de formación no válido.', 'danger')
    return render_template('alumnos/acceso_formacion.html', form=form)

@alumnos_bp.route('/acceso', methods=['GET', 'POST'])
def acceso_alumno():
    get_flashed_messages()
    formacion_id = request.args.get('formacion_id', type=int)
    form = DniForm()

    if form.validate_on_submit():
        dni = form.dni.data.strip().upper()
        alumno = Alumno.query.filter_by(dni=dni).first()
        formacion = Formacion.query.get(formacion_id)

        if not formacion:
            flash("Formación no encontrada.", "danger")
            return redirect(url_for('alumnos_bp.acceso_formacion'))

        tipo = formacion.tipo_curso
        con_examen = tipo.examen_modelo is not None

        if not alumno:
            return redirect(url_for('alumnos_bp.nuevo_alumno', formacion_id=formacion_id, dni=dni))

        rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion_id).first()
        if rel:
            if not con_examen:
                if not rel.aprobado:
                    rel.aprobado = True
                    db.session.commit()
                    crear_y_guardar_diploma(alumno, formacion)
                return render_template('alumnos/gracias_inscripcion.html', alumno=alumno, formacion=formacion)
            else:
                # Comprobar si ya existe un examen realizado
                if rel.examen:
                    return render_template('alumnos/examen_ya_realizado.html', alumno=alumno, formacion=formacion)
                else:
                    flash("Ya estás registrado. Solo puedes realizar el examen una vez.", "warning")
                    return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))
        else:
            rel = AlumnoFormacion(alumno_id=alumno.id, formacion_id=formacion_id)
            db.session.add(rel)
            db.session.commit()
            if not con_examen:
                rel.aprobado = True
                db.session.commit()
                crear_y_guardar_diploma(alumno, formacion)
                return render_template('alumnos/gracias_inscripcion.html', alumno=alumno, formacion=formacion)
            return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))

    return render_template('alumnos/acceso_dni.html', form=form)

@alumnos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    form = AlumnoForm(obj=alumno)
    empresas = Empresa.query.all()
    form.empresa_id.choices = [(0, 'Sin empresa')] + [(e.id, e.nombre) for e in empresas]

    if form.validate_on_submit():
        dni_value = form.dni.data.strip().upper()
        otro_email = Alumno.query.filter(Alumno.email == form.email.data, Alumno.id != alumno.id).first()
        otro_dni = Alumno.query.filter(Alumno.dni == dni_value, Alumno.id != alumno.id).first()
        if otro_email:
            form.email.errors.append("Ya existe un alumno con ese email.")
        if otro_dni:
            form.dni.errors.append("Ya existe un alumno con ese DNI.")
        if not otro_email and not otro_dni:
            empresa_id = form.empresa_id.data if form.empresa_id.data != 0 else None
            alumno.nombre = form.nombre.data.strip().title()
            alumno.dni = dni_value
            alumno.email = form.email.data
            alumno.telefono = form.telefono.data
            alumno.interesado_mas_cursos = form.interesado_mas_cursos.data
            alumno.empresa_id = empresa_id
            alumno.observaciones = form.observaciones.data
            db.session.commit()
            flash("Alumno modificado correctamente.", "success")
            return redirect(url_for('alumnos_bp.lista_alumnos'))

    return render_template('alumnos/editar_alumno.html', form=form, alumno=alumno)

@alumnos_bp.route('/borrar/<int:id>', methods=['POST'])
def borrar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    db.session.delete(alumno)
    db.session.commit()
    flash("Alumno eliminado.", "success")
    return redirect(url_for('alumnos_bp.lista_alumnos'))
@alumnos_bp.route('/ficha/<int:alumno_id>')
def ficha_alumno(alumno_id):
    alumno = Alumno.query.get_or_404(alumno_id)

    # Trae TODAS las relaciones de formaciones
    relaciones = AlumnoFormacion.query.filter_by(alumno_id=alumno_id).join(Formacion).order_by(Formacion.fecha1.desc()).all()
    formaciones_info = []

    for rel in relaciones:
        formacion = rel.formacion
        # ---- NORMALIZA la ruta como ya haces en alumnos_info ----
        empresa_norm = normaliza_nombre_archivo(formacion.empresa.nombre) if formacion.empresa else ''
        fecha_str = formacion.fecha1.strftime('%Y-%m-%d') if formacion.fecha1 else ''
        alumno_norm = normaliza_nombre_archivo(alumno.nombre)
        ruta_pdf = f"/static/diplomas/{empresa_norm}/{fecha_str}/diploma_{alumno_norm}.pdf"
        # ----
        formaciones_info.append({
            'formacion': formacion,
            'rel': rel,
            'ruta_pdf': ruta_pdf,
        })

    return render_template(
        "alumnos/ficha_alumno.html",
        alumno=alumno,
        formaciones_info=formaciones_info
    )

# ---- FUNCIÓN DE BORRADO (ahora correctamente colocada) ----
@alumnos_bp.route('/borrar_formacion_alumno/<int:alumno_formacion_id>', methods=['POST'])
def borrar_formacion_alumno(alumno_formacion_id):
    af = AlumnoFormacion.query.get_or_404(alumno_formacion_id)
    alumno_id = af.alumno_id
    db.session.delete(af)
    db.session.commit()
    flash("Formación eliminada correctamente.", "success")
    return redirect(url_for('alumnos_bp.ficha_alumno', alumno_id=alumno_id))

@alumnos_bp.route('/exportar_excel')
def exportar_excel():
    alumnos = Alumno.query.order_by(Alumno.nombre).all()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Alumnos"
    ws.append(["ID", "Nombre", "DNI", "Email", "Teléfono", "Empresa"])

    for a in alumnos:
        ws.append([
            a.id,
            a.nombre,
            a.dni,
            a.email,
            a.telefono,
            a.empresa.nombre if a.empresa else ''
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        download_name="alumnos.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@alumnos_bp.route('/ver_examen/<int:formacion_id>/<int:alumno_id>')
def ver_examen_alumno(formacion_id, alumno_id):
    import json
    from mi_plataforma_formacion_app.models import Alumno, Formacion, AlumnoFormacion, ExamenAlumno, Respuesta

    alumno = Alumno.query.get_or_404(alumno_id)
    formacion = Formacion.query.get_or_404(formacion_id)
    rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion.id).first()
    examen_alumno = ExamenAlumno.query.filter_by(alumno_formacion_id=rel.id).first() if rel else None

    # === DEBUG: Imprime los datos ===
    print("DEBUG - EXAMEN ALUMNO:", examen_alumno)
    if examen_alumno:
        print("DEBUG - RESPUESTAS_JSON:", examen_alumno.respuestas_json)
        examen_modelo = formacion.tipo_curso.examen_modelo
        if examen_modelo and examen_modelo.preguntas:
            for pregunta in examen_modelo.preguntas:
                print("PREGUNTA ID:", pregunta.id, "| TEXTO:", pregunta.texto)
    # === FIN DEBUG ===

    examen_revisado = []
    total_preguntas = 0
    aciertos = 0
    fallos = 0

    if examen_alumno and examen_alumno.respuestas_json:
        try:
            respuestas_dict = json.loads(examen_alumno.respuestas_json)
        except Exception:
            respuestas_dict = {}

        examen_modelo = formacion.tipo_curso.examen_modelo
        if examen_modelo and examen_modelo.preguntas:
            for pregunta in examen_modelo.preguntas:
                pregunta_id = str(pregunta.id)
                respuesta_dada_id = respuestas_dict.get(pregunta_id, None)
                respuesta_dada_texto = ""
                respuesta_correcta_texto = ""
                es_correcta = False

                respuestas_db = Respuesta.query.filter_by(pregunta_id=pregunta.id).all()
                for resp in respuestas_db:
                    if str(resp.id) == str(respuesta_dada_id):
                        respuesta_dada_texto = resp.texto
                        if resp.es_correcta:
                            es_correcta = True
                    if resp.es_correcta:
                        respuesta_correcta_texto = resp.texto

                if not respuesta_dada_id:
                    respuesta_dada_texto = "No respondido"

                examen_revisado.append({
                    'pregunta_texto': getattr(pregunta, 'texto', ''),
                    'respuesta_dada': respuesta_dada_texto,
                    'respuesta_correcta': respuesta_correcta_texto,
                    'es_correcta': es_correcta
                })
                total_preguntas += 1
                if es_correcta:
                    aciertos += 1
                else:
                    fallos += 1
    nota_automatica = examen_alumno.nota_automatica if examen_alumno and examen_alumno.nota_automatica is not None else None
    apto = nota_automatica is not None and nota_automatica >= 5

    return render_template(
        'formaciones/ver_examen_alumno.html',
        alumno=alumno,
        formacion=formacion,
        examen_alumno=examen_alumno,
        correccion_preguntas=examen_revisado,
        total_preguntas=total_preguntas,
        aciertos=aciertos,
        fallos=fallos,
        apto=apto,
        nota_automatica=nota_automatica
    )
