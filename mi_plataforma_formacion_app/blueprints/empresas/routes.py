import csv
import os
import io
import openpyxl
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, send_file
from mi_plataforma_formacion_app.models.comercial import Comercial
from mi_plataforma_formacion_app.models.empresa import Empresa
from mi_plataforma_formacion_app.extensions import db

empresas_bp = Blueprint('empresas_bp', __name__, template_folder='templates')

# --- Endpoint API para autocompletar empresas (autocomplete) ---
@empresas_bp.route('/api/empresas_autocomplete')
def api_empresas_autocomplete():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    empresas = Empresa.query.filter(Empresa.nombre.ilike(f'%{q}%')).order_by(Empresa.nombre).limit(20).all()
    return jsonify([{'id': e.id, 'nombre': e.nombre} for e in empresas])

# --- Endpoint API para autocompletar poblaciones ---
@empresas_bp.route('/api/poblaciones')
def api_poblaciones():
    q = request.args.get('q', '').strip().lower()
    resultados = []
    try:
        poblaciones_path = os.path.join(current_app.root_path, '..', 'poblaciones.csv')
        with open(poblaciones_path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keys = {str(k).strip().lower().replace('\ufeff', ''): k for k in row if k}
                pob_key = next((keys[k] for k in keys if 'poblacion' in k), None)
                prov_key = next((keys[k] for k in keys if 'provincia' in k or 'ciudad' in k), None)
                if not pob_key or not prov_key:
                    continue
                poblacion = row.get(pob_key)
                provincia = row.get(prov_key)
                if not poblacion or not provincia:
                    continue
                poblacion = str(poblacion).strip()
                provincia = str(provincia).strip()
                if not poblacion or not provincia:
                    continue
                if q in poblacion.lower():
                    resultados.append({'poblacion': poblacion, 'provincia': provincia})
                if len(resultados) >= 15:
                    break
    except Exception as e:
        return jsonify({"error": str(e)})
    return jsonify(resultados)

# --- Vista principal (listado de empresas) ---
@empresas_bp.route('/', methods=['GET'])
def gestion_empresas():
    query = request.args.get("q", "").strip()
    comercial_id_filtro = request.args.get("comercial_id", type=int)

    empresas = Empresa.query
    if query:
        empresas = empresas.filter(
            (Empresa.nombre.ilike(f"%{query}%")) |
            (Empresa.cif.ilike(f"%{query}%")) |
            (Empresa.poblacion.ilike(f"%{query}%"))
        )

    if comercial_id_filtro:
        empresas = empresas.filter_by(comercial_id=comercial_id_filtro)

    empresas = empresas.order_by(Empresa.nombre).all()

    comerciales = Comercial.query.order_by(Comercial.nombre).all()

    # Obtener el nombre del comercial seleccionado para la alerta
    comercial_seleccionado_nombre = None
    if comercial_id_filtro:
        comercial_obj = Comercial.query.get(comercial_id_filtro)
        if comercial_obj:
            comercial_seleccionado_nombre = comercial_obj.nombre

    return render_template(
        'empresas/gestion_empresas.html',
        empresas=empresas,
        query=query,
        comerciales=comerciales,
        comercial_id_filtro=comercial_id_filtro,
        comercial_seleccionado_nombre=comercial_seleccionado_nombre
    )

# --- Crear nueva empresa ---
@empresas_bp.route('/nueva', methods=['GET', 'POST'])
def nueva_empresa():
    comerciales = Comercial.query.all()
    errores = {}

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        cif = request.form['cif'].strip()
        direccion = request.form['direccion']
        poblacion = request.form['poblacion']
        provincia = request.form['provincia']
        contacto = request.form['contacto']
        email = request.form['email']
        telefono = request.form['telefono']
        comercial_id = request.form.get('comercial_id') or None

        # --- Validación de duplicados ---
        existe_nombre = Empresa.query.filter_by(nombre=nombre).first()
        existe_cif = Empresa.query.filter_by(cif=cif).first()

        if existe_nombre:
            errores['nombre'] = "Ya existe una empresa con ese nombre."
        if existe_cif:
            errores['cif'] = "Ya existe una empresa con ese CIF."

        if not errores:
            nueva = Empresa(
                nombre=nombre,
                cif=cif,
                direccion=direccion,
                poblacion=poblacion,
                provincia=provincia,
                contacto=contacto,
                email=email,
                telefono=telefono,
                comercial_id=comercial_id
            )
            db.session.add(nueva)
            db.session.commit()
            flash('Empresa creada correctamente.', 'success')
            return redirect(url_for('empresas_bp.gestion_empresas'))
        else:
            for campo, mensaje in errores.items():
                flash(f"{mensaje}", 'warning')

    return render_template('empresas/nueva_empresa.html', comerciales=comerciales, errores=errores)

# --- Editar empresa ---
@empresas_bp.route('/editar/<int:empresa_id>', methods=['GET', 'POST'])
def editar_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    comerciales = Comercial.query.all()
    errores = {}

    if request.method == 'POST':
        nombre = request.form['nombre'].strip()
        cif = request.form['cif'].strip()
        direccion = request.form['direccion']
        poblacion = request.form['poblacion']
        provincia = request.form['provincia']
        contacto = request.form['contacto']
        email = request.form['email']
        telefono = request.form['telefono']
        comercial_id = request.form.get('comercial_id') or None

        # --- Validación de duplicados (que no sea la misma empresa) ---
        otro_nombre = Empresa.query.filter(Empresa.nombre == nombre, Empresa.id != empresa.id).first()
        otro_cif = Empresa.query.filter(Empresa.cif == cif, Empresa.id != empresa.id).first()

        if otro_nombre:
            errores['nombre'] = "Ya existe una empresa con ese nombre."
        if otro_cif:
            errores['cif'] = "Ya existe una empresa con ese CIF."

        if not errores:
            empresa.nombre = nombre
            empresa.cif = cif
            empresa.direccion = direccion
            empresa.poblacion = poblacion
            empresa.provincia = provincia
            empresa.contacto = contacto
            empresa.email = email
            empresa.telefono = telefono
            empresa.comercial_id = comercial_id
            db.session.commit()
            flash('Empresa actualizada correctamente.', 'success')
            return redirect(url_for('empresas_bp.gestion_empresas'))
        else:
            for campo, mensaje in errores.items():
                flash(f"{mensaje}", 'warning')

    return render_template('empresas/editar_empresa.html', empresa=empresa, comerciales=comerciales, errores=errores)

# --- Eliminar empresa ---
@empresas_bp.route('/eliminar/<int:empresa_id>', methods=['POST'])
def eliminar_empresa(empresa_id):
    empresa = Empresa.query.get_or_404(empresa_id)
    db.session.delete(empresa)
    db.session.commit()
    flash('Empresa eliminada correctamente.', 'success')
    return redirect(url_for('empresas_bp.gestion_empresas'))

# --- Crear empresa rápido desde modal (AJAX) ---
@empresas_bp.route('/crear_rapido', methods=['POST'])
def crear_rapido_empresa():
    nombre = request.form.get("nombre", "").strip()
    cif = request.form.get("cif", "").strip()
    comercial_id = request.form.get("comercial_id") or None
    if not nombre or not cif:
        return jsonify(ok=False, error="Nombre y CIF son obligatorios")
    if Empresa.query.filter_by(nombre=nombre).first():
        return jsonify(ok=False, error="Ya existe una empresa con ese nombre")
    if Empresa.query.filter_by(cif=cif).first():
        return jsonify(ok=False, error="Ya existe una empresa con ese CIF")
    empresa = Empresa(
        nombre=nombre,
        cif=cif,
        direccion=request.form.get("direccion", ""),
        poblacion=request.form.get("poblacion", ""),
        provincia=request.form.get("provincia", ""),
        contacto=request.form.get("contacto", ""),
        email=request.form.get("email", ""),
        telefono=request.form.get("telefono", ""),
        comercial_id=comercial_id
    )
    db.session.add(empresa)
    db.session.commit()
    return jsonify(ok=True, id=empresa.id, nombre=empresa.nombre)

import io
import openpyxl

@empresas_bp.route('/exportar_excel')
def exportar_excel():
    query = request.args.get("q", "").strip()
    comercial_id_filtro = request.args.get("comercial_id", type=int)

    empresas = Empresa.query
    if query:
        empresas = empresas.filter(
            (Empresa.nombre.ilike(f"%{query}%")) |
            (Empresa.cif.ilike(f"%{query}%")) |
            (Empresa.poblacion.ilike(f"%{query}%"))
        )
    if comercial_id_filtro:
        empresas = empresas.filter_by(comercial_id=comercial_id_filtro)

    empresas = empresas.order_by(Empresa.nombre).all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Empresas"
    ws.append(["ID", "Nombre", "CIF", "Email", "Teléfono", "Comercial"])

    for e in empresas:
        ws.append([
            e.id,
            e.nombre,
            e.cif if hasattr(e, "cif") else '',
            e.email if hasattr(e, "email") else '',
            e.telefono if hasattr(e, "telefono") else '',
            e.comercial.nombre if hasattr(e, "comercial") and e.comercial else ''
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        download_name="empresas.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
@empresas_bp.route('/api/buscar_empresas')
def api_buscar_empresas():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify(results=[])
    empresas = Empresa.query.filter(Empresa.nombre.ilike(f'%{q}%')).order_by(Empresa.nombre).limit(25).all()
    return jsonify(results=[{'id': e.id, 'nombre': e.nombre} for e in empresas])