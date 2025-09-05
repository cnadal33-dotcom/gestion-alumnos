from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, session
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models import Empresa
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.extensions import db
from .forms import AlumnoForm, ImportarAlumnosExcelForm
import pandas as pd
import openpyxl
# ...existing code...

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


@alumnos_bp.route('/exportar_excel', methods=['GET'], endpoint='exportar_excel')
def exportar_excel():
    """Exportar la lista de alumnos (opcionalmente filtrada por q) a un archivo Excel descargable."""
    q = request.args.get("q", "").strip()
    alumnos_q = Alumno.query
    if q:
        alumnos_q = alumnos_q.filter(
            (Alumno.nombre.ilike(f"%{q}%")) |
            (Alumno.dni.ilike(f"%{q}%")) |
            (Alumno.email.ilike(f"%{q}%"))
        )
    alumnos = alumnos_q.order_by(Alumno.nombre).all()

    # Construir DataFrame
    try:
        import pandas as pd
        from io import BytesIO
        rows = []
        for a in alumnos:
            rows.append({
                'Nombre': a.nombre,
                'DNI': a.dni,
                'Email': a.email,
                'Telefono': a.telefono or '',
                'Empresa': a.empresa.nombre if a.empresa else ''
            })
        df = pd.DataFrame(rows)
        output = BytesIO()
        # usar engine por defecto (openpyxl) para xlsx
        df.to_excel(output, index=False)
        output.seek(0)
        return send_file(output, as_attachment=True, download_name='alumnos.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        logger.exception('Error exportando alumnos a Excel: %s', e)
        flash('Error exportando alumnos a Excel.', 'danger')
        return redirect(url_for('alumnos_bp.lista_alumnos'))
from .forms_dni import DniForm
from datetime import date, datetime, timedelta
import os
import io
import pdfkit
import unicodedata
import re # Importa el módulo re
from flask import get_flashed_messages
from flask_login import current_user

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


# _set_portal_session removed — public portal flow was removed per UX requirements


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
    # Entry diagnostic: log every call to /alumnos/nuevo so we can see
    # whether requests arrive missing the expected formacion_id/dni.
    try:
        import json, time
        rec = {
            'ts': time.time(),
            'entry': True,
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': (request.headers.get('User-Agent') or '')[:200],
            'referrer': request.referrer,
            'args': dict(request.args),
            'form': dict(request.form),
        }
        with open('/tmp/nuevo_debug.log', 'a', encoding='utf-8') as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception:
        pass

    # Accept formacion_id and dni from either querystring or POST body
    formacion_id = request.values.get('formacion_id', type=int)
    dni_query = request.values.get('dni', type=str)
    form = AlumnoForm()
    if dni_query:
        form.dni.data = dni_query.upper()
    # If formacion_id is missing, try to recover it from the Referrer
    # (some clients or intermediate redirects may strip querystrings).
    if not formacion_id:
        try:
            ref = (request.referrer or '')
            if ref:
                from urllib.parse import urlparse, parse_qs
                qs = urlparse(ref).query
                qd = parse_qs(qs)
                raw = qd.get('formacion_id', [None])[0]
                if raw is not None and raw != '':
                    try:
                        if str(raw).isdigit():
                            formacion_id = int(raw)
                        else:
                            formacion_id = int(float(raw))
                    except Exception:
                        formacion_id = None
        except Exception:
            formacion_id = formacion_id

    # Heuristic: if we still don't have formacion_id or dni in the query,
    # but the request referer indicates the user came from the public
    # access flow (acceso / acceso_formacion / acceso_dni), treat this
    # GET as a public flow and force the public base template so the
    # sidebar isn't shown. Also attempt one more time to extract
    # formacion_id from the referer querystring.
    force_public = False
    if not formacion_id and not dni_query:
        try:
            ref = (request.referrer or '')
            if ref:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(ref)
                path = parsed.path or ''
                # Be permissive: any referrer under /app/alumnos/ should be
                # treated as coming from the public alumno flow.
                if '/app/alumnos/' in ref or any(pat in path for pat in ('/app/alumnos/acceso', '/app/alumnos/acceso_formacion', '/app/alumnos/acceso_dni')):
                    force_public = True
                    qs = parsed.query
                    qd = parse_qs(qs)
                    raw2 = qd.get('formacion_id', [None])[0]
                    if raw2 is not None and raw2 != '':
                        try:
                            if str(raw2).isdigit():
                                formacion_id = int(raw2)
                            else:
                                formacion_id = int(float(raw2))
                        except Exception:
                            pass
        except Exception:
            pass
    # Preseleccionar empresa si viene de acceso por formación
    if formacion_id:
        formacion = Formacion.query.get(formacion_id)
        # Si la formación está cerrada, impedir el flujo público de inscripción
        if formacion and getattr(formacion, 'cerrada', False):
            try:
                current_app.logger.info('Intento de acceso a formacion CERRADA (acceso_alumno)', extra={'id': getattr(formacion, 'id', None), 'remote_addr': request.remote_addr, 'dni': dni})
            except Exception:
                pass
            return render_template('formaciones/formacion_cerrada.html', formacion=formacion), 403
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
            # Preferir valor enviado en form.empresa_id (Select2). Si no viene, intentar fallback por empresa_nombre (datalist)
            if not form.empresa_id.data:
                nombre = (request.form.get('empresa_nombre') or '').strip()
                if nombre:
                    emp = Empresa.query.filter(Empresa.nombre == nombre).first()
                    form.empresa_id.data = emp.id if emp else None
            empresa_id = form.empresa_id.data if form.empresa_id.data not in (None, 0, '') else None
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
                    try:
                        crear_y_guardar_diploma(nuevo, formacion)
                    except Exception:
                        logger.exception("Error generando diploma al crear alumno (nuevo)")
                        flash("Alumno creado pero falló la generación automática del diploma.", "warning")
                    return render_template("alumnos/gracias_inscripcion.html", alumno=nuevo, formacion=formacion)

                flash("Alumno registrado correctamente. ¡Ya puedes realizar el examen!", "success")
                # Use the app's prefixed URL helper so redirects go to /app/...
                try:
                    session['student_mode'] = True
                except Exception:
                    pass
                try:
                    pref = current_app.jinja_env.globals.get('u')
                    return redirect(pref('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=nuevo.id))
                except Exception:
                    return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=nuevo.id))
            else:
                flash("Alumno creado correctamente.", "success")
                return redirect(url_for('alumnos_bp.lista_alumnos'))
    # Decide which base template to use: public flow (no nav) vs admin (full nav).
    # Defensive fallback: if the user is anonymous (public flow) and we don't
    # have formacion_id/dni, prefer the public base so the sidebar isn't shown.
    try:
        anon = not current_user.is_authenticated
    except Exception:
        anon = True
    base_template = 'base_public.html' if (formacion_id or dni_query or (locals().get('force_public', False)) or anon) else 'base.html'
    empresa_nombre = None
    empresa_seleccionada = None
    if formacion_id:
        ftmp = Formacion.query.get(formacion_id)
        if ftmp and ftmp.empresa:
            empresa_nombre = ftmp.empresa.nombre
            empresa_seleccionada = ftmp.empresa
    # Diagnostic trace (temporary): write compact status to /tmp for inspection
    try:
        # Write a more detailed single-line JSON record so we can inspect
        # exactly how the request arrived (headers, args, form, chosen base)
        with open('/tmp/nuevo_debug.log', 'a', encoding='utf-8') as fh:
            import json, time
            rec = {
                'ts': time.time(),
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': (request.headers.get('User-Agent') or '')[:200],
                'referrer': request.referrer,
                'formacion_id': formacion_id,
                'dni_query': dni_query,
                'force_public': locals().get('force_public', False),
                'args': dict(request.args),
                'form': dict(request.form),
                'base_template': base_template if 'base_template' in locals() else None
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception:
        pass
    # If this is a public/student flow, mark session so templates know to hide admin chrome
    try:
        if base_template == 'base_public.html':
            session['student_mode'] = True
    except Exception:
        pass
    return render_template('alumnos/nuevo_alumno.html', form=form, base_template=base_template, empresa_nombre=empresa_nombre, empresa_seleccionada=empresa_seleccionada, no_sidebar=(base_template=='base_public.html'))
@alumnos_bp.route('/acceso_formacion', methods=['GET', 'POST'])
def acceso_formacion():
    form = CodigoFormacionForm()
    if form.validate_on_submit():
        codigo = form.codigo.data.strip()
        formacion = Formacion.query.filter_by(referencia=codigo).first()
        if formacion:
            # Si la formación está cerrada, mostrar una página profesional y devolver 403
            if getattr(formacion, 'cerrada', False):
                try:
                    current_app.logger.info('Intento de acceso a formacion CERRADA (acceso_formacion)', extra={'referencia': getattr(formacion, 'referencia', None), 'id': getattr(formacion, 'id', None), 'remote_addr': request.remote_addr})
                except Exception:
                    pass
                return render_template('formaciones/formacion_cerrada.html', formacion=formacion), 403

            # Render the DNI access page directly with the formacion_id embedded
            # instead of redirecting. Some proxies/browsers may drop the
            # querystring on redirects or rewrite Location headers which can
            # cause the subsequent POST to lose the formacion_id. Rendering
            # the template here guarantees the hidden input and the form
            # action include the correct formacion_id.
            dni_form = DniForm()
            # Clear any previously flashed messages so the DNI page starts
            # without stale alerts (e.g., 'Ya estás registrado...') that
            # may have been set during a prior attempt.
            try:
                get_flashed_messages()
            except Exception:
                pass
            return render_template('alumnos/acceso_dni.html', form=dni_form, formacion_id=formacion.id, no_sidebar=True)
        else:
            flash('Código de formación no válido.', 'danger')
    return render_template('alumnos/acceso_formacion.html', form=form, no_sidebar=True)

@alumnos_bp.route('/acceso', methods=['GET', 'POST'])
def acceso_alumno():
    get_flashed_messages()
    # Robust extraction of formacion_id with detailed logging for diagnostics.
    formacion_id = None
    raw = None
    try:
        # request.values covers both form (POST) and args (GET) in priority order
        raw = request.values.get('formacion_id')
        # If not present, try parsing from Referer querystring (some clients drop qs on redirect)
        if not raw:
            ref = (request.referrer or '')
            if ref:
                from urllib.parse import urlparse, parse_qs
                qs = urlparse(ref).query
                qd = parse_qs(qs)
                raw = qd.get('formacion_id', [None])[0]
        if raw is not None and raw != '':
            raw = str(raw).strip()
            try:
                # Allow numeric strings; try int then float->int fallback
                if raw.isdigit():
                    formacion_id = int(raw)
                else:
                    formacion_id = int(float(raw))
            except Exception:
                formacion_id = None
    except Exception:
        formacion_id = None

    # Log request context to aid debugging when formacion_id is lost
    try:
        from flask import current_app
        body_preview = None
        try:
            body_preview = request.get_data(as_text=True)[:1000]
        except Exception:
            body_preview = '<unreadable body>'
        current_app.logger.info('acceso_alumno START method=%s raw=%r resolved=%r form=%s args=%s referrer=%s body_preview=%s',
                                request.method, raw, formacion_id, dict(request.form), dict(request.args), request.referrer, body_preview)
    except Exception:
        pass

    # Additionally append a compact debug record to /tmp for easy inspection
    try:
        try:
            import json, time
            record = {
                'ts': time.time(),
                'remote_addr': request.remote_addr,
                'method': request.method,
                'raw': raw,
                'resolved': formacion_id,
                'form': dict(request.form),
                'args': dict(request.args),
            }
            with open('/tmp/acceso_post_debug.log', 'a', encoding='utf-8') as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + '\n')
        except Exception:
            pass
    except Exception:
        pass

    form = DniForm()

    if form.validate_on_submit():
        dni = form.dni.data.strip().upper()
        # Re-check formacion_id in POST payload explicitly in case it arrived only in form
        if not formacion_id:
            raw2 = request.form.get('formacion_id') or request.args.get('formacion_id')
            try:
                if raw2 is not None and raw2 != '':
                    raw2 = str(raw2).strip()
                    if raw2.isdigit():
                        formacion_id = int(raw2)
                    else:
                        formacion_id = int(float(raw2))
            except Exception:
                formacion_id = None
            try:
                from flask import current_app
                current_app.logger.info('acceso_alumno AFTER_SUBMIT recheck_raw=%r resolved=%r', raw2 if 'raw2' in locals() else None, formacion_id)
            except Exception:
                pass

        alumno = Alumno.query.filter_by(dni=dni).first()
        formacion = Formacion.query.get(formacion_id) if formacion_id else None

        # Bloquear acceso si la formación está cerrada
        if formacion and getattr(formacion, 'cerrada', False):
            try:
                current_app.logger.info('Intento de acceso a formacion CERRADA (nuevo_alumno)', extra={'id': getattr(formacion, 'id', None), 'remote_addr': request.remote_addr})
            except Exception:
                pass
            return render_template('formaciones/formacion_cerrada.html', formacion=formacion), 403

        if not formacion:
            # Log full context to help debug missing formacion_id
            try:
                from flask import current_app
                current_app.logger.warning('acceso_alumno MISSING_FORMACION formacion_id=%r form=%s args=%s raw_body=%s', formacion_id, dict(request.form), dict(request.args), request.get_data(as_text=True)[:2000])
            except Exception:
                pass
            flash("Formación no encontrada.", "danger")
            # Re-render the DNI page so the user can retry without losing input
            return render_template('alumnos/acceso_dni.html', form=form, formacion_id=formacion_id, no_sidebar=True)

        tipo = formacion.tipo_curso
        con_examen = tipo.examen_modelo is not None

        if not alumno:
            # Render the nuevo_alumno template directly to avoid losing
            # query parameters on redirects and to ensure the user sees the
            # public (no-sidebar) layout. Provide an explicit action_url so
            # the HTML form will post to the proper endpoint (/alumnos/nuevo).
            form_nuevo = AlumnoForm()
            form_nuevo.dni.data = dni
            base_template = 'base_public.html'
            empresa_nombre = None
            empresa_seleccionada = None
            if formacion_id:
                ftmp = Formacion.query.get(formacion_id)
                if ftmp and getattr(ftmp, 'cerrada', False):
                    try:
                        current_app.logger.info('Intento de acceso a formacion CERRADA (acceso_alumno -> nuevo)', extra={'id': getattr(ftmp, 'id', None), 'remote_addr': request.remote_addr})
                    except Exception:
                        pass
                    return render_template('formaciones/formacion_cerrada.html', formacion=ftmp), 403
                if ftmp and ftmp.empresa:
                    empresa_nombre = ftmp.empresa.nombre
                    empresa_seleccionada = ftmp.empresa
            try:
                pref = current_app.jinja_env.globals.get('u')
                action = pref('alumnos_bp.nuevo_alumno') if pref else url_for('alumnos_bp.nuevo_alumno')
            except Exception:
                action = url_for('alumnos_bp.nuevo_alumno')
            try:
                session['student_mode'] = True
            except Exception:
                pass
            return render_template('alumnos/nuevo_alumno.html', form=form_nuevo, base_template=base_template, empresa_nombre=empresa_nombre, empresa_seleccionada=empresa_seleccionada, action_url=action)

        rel = AlumnoFormacion.query.filter_by(alumno_id=alumno.id, formacion_id=formacion_id).first()
        if rel:
            if not con_examen:
                if not rel.aprobado:
                    rel.aprobado = True
                    db.session.commit()
                    try:
                        crear_y_guardar_diploma(alumno, formacion)
                    except Exception:
                        logger.exception("Error generando diploma al confirmar acceso (existing rel)")
                        flash("Registro confirmado pero falló la generación automática del diploma.", "warning")
                # Continue original flow: show thank-you page
                return render_template('alumnos/gracias_inscripcion.html', alumno=alumno, formacion=formacion)
            else:
                # Comprobar si ya existe un examen realizado
                if rel.examen:
                    # If exam already done, show exam already done page
                    return render_template('alumnos/examen_ya_realizado.html', alumno=alumno, formacion=formacion)
                else:
                    flash("Ya estás registrado. Solo puedes realizar el examen una vez.", "exam_done")
                    try:
                        session['student_mode'] = True
                    except Exception:
                        pass
                    try:
                        pref = current_app.jinja_env.globals.get('u')
                        return redirect(pref('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))
                    except Exception:
                        return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))
        else:
            rel = AlumnoFormacion(alumno_id=alumno.id, formacion_id=formacion_id)
            db.session.add(rel)
            db.session.commit()
            if not con_examen:
                rel.aprobado = True
                db.session.commit()
                try:
                    crear_y_guardar_diploma(alumno, formacion)
                except Exception:
                    logger.exception("Error generando diploma al crear rel y confirmar acceso (new rel)")
                    flash("Registro completado pero falló la generación automática del diploma.", "warning")
                # After creating the relation and marking aprobado: show thank-you
                return render_template('alumnos/gracias_inscripcion.html', alumno=alumno, formacion=formacion)
            # Redirect to the exam route for both public and authenticated users
            try:
                session['student_mode'] = True
            except Exception:
                pass
            try:
                pref = current_app.jinja_env.globals.get('u')
                return redirect(pref('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))
            except Exception:
                return redirect(url_for('examenes_bp.hacer_examen', formacion_id=formacion_id, alumno_id=alumno.id))

    return render_template('alumnos/acceso_dni.html', form=form, formacion_id=formacion_id, no_sidebar=True)

@alumnos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_alumno(id):
    alumno = Alumno.query.get_or_404(id)
    form = AlumnoForm(obj=alumno)
    # No cargar choices: Select2 obtendrá las opciones por AJAX

    if form.validate_on_submit():
        dni_value = form.dni.data.strip().upper()
        otro_email = Alumno.query.filter(Alumno.email == form.email.data, Alumno.id != alumno.id).first()
        otro_dni = Alumno.query.filter(Alumno.dni == dni_value, Alumno.id != alumno.id).first()
        if otro_email:
            form.email.errors.append("Ya existe un alumno con ese email.")
        if otro_dni:
            form.dni.errors.append("Ya existe un alumno con ese DNI.")
        if not otro_email and not otro_dni:
            # Preferir form.empresa_id.data (Select2). Si no viene, intentar fallback por empresa_nombre (datalist)
            if not form.empresa_id.data:
                nombre = (request.form.get('empresa_nombre') or '').strip()
                if nombre:
                    emp = Empresa.query.filter(Empresa.nombre == nombre).first()
                    form.empresa_id.data = emp.id if emp else None
            empresa_id = form.empresa_id.data if form.empresa_id.data not in (None, 0, '') else None

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

    # Pre-cargar form.empresa_id.data y pasar empresa_seleccionada para la plantilla
    form.empresa_id.data = alumno.empresa_id
    empresa_seleccionada = Empresa.query.get(alumno.empresa_id) if alumno.empresa_id else None
    return render_template('alumnos/editar_alumno.html', form=form, alumno=alumno, empresa_seleccionada=empresa_seleccionada)


# portal_publico route removed — public flow now proceeds directly to exam or nuevo_alumno

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
        ruta_pdf = url_for('static', filename=f"diplomas/{empresa_norm}/{fecha_str}/diploma_{alumno_norm}.pdf")
        # ----
        formaciones_info.append({
            'formacion': formacion,
            'rel': rel,
            'ruta_pdf': ruta_pdf,
        })

    return render_template(
        'alumnos/ficha_alumno.html',
        alumno=alumno,
        formaciones_info=formaciones_info
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
    # print("DEBUG - RESPUESTAS_JSON:", examen_alumno.respuestas_json)  # Campo eliminado
        examen_modelo = formacion.tipo_curso.examen_modelo
        if examen_modelo and examen_modelo.preguntas:
            for pregunta in examen_modelo.preguntas:
                print("PREGUNTA ID:", pregunta.id, "| TEXTO:", pregunta.texto)
    # === FIN DEBUG ===

    examen_revisado = []
    total_preguntas = 0
    aciertos = 0
    fallos = 0

    # El campo respuestas_json ya no existe, así que no se recuperan respuestas previas
    examen_modelo = formacion.tipo_curso.examen_modelo
    respuestas_dict = {}
    if examen_alumno:
        # Recuperar las respuestas del alumno realmente contestadas
        from mi_plataforma_formacion_app.models import Respuesta
        respuestas_alumno = Respuesta.query.filter_by(examen_alumno_id=examen_alumno.id).all()
        for r in respuestas_alumno:
            respuestas_dict[str(r.pregunta_id)] = r
    examen_revisado = []
    total_preguntas = 0
    aciertos = 0
    fallos = 0
    if examen_modelo and examen_modelo.preguntas:
        def _norm(s):
            try:
                return s.strip().lower()
            except Exception:
                return s

        for pregunta in examen_modelo.preguntas:
            pregunta_id = str(pregunta.id)
            respuesta_dada_texto = "No respondido"
            respuesta_correcta_texto = ""
            es_correcta = False

            respuesta_alumno = respuestas_dict.get(pregunta_id)
            if respuesta_alumno:
                respuesta_dada_texto = respuesta_alumno.texto

            # Buscar entre las opciones del modelo la respuesta marcada como correcta
            correcta = next((r for r in Respuesta.query.filter_by(pregunta_id=pregunta.id).all() if r.examen_alumno_id is None and r.es_correcta), None)
            if correcta:
                respuesta_correcta_texto = correcta.texto

            # Comparar normalizando texto
            if respuesta_alumno and respuesta_correcta_texto:
                es_correcta = _norm(respuesta_dada_texto) == _norm(respuesta_correcta_texto)

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
    # Calcular nota automática
    nota_automatica = None
    if total_preguntas > 0:
        nota_automatica = round((aciertos / total_preguntas) * 10, 2)
        if examen_alumno:
            examen_alumno.nota_automatica = nota_automatica
            from mi_plataforma_formacion_app.extensions import db
            db.session.commit()
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
