from flask import Blueprint, render_template, request, redirect, url_for, flash
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models import Comercial

comerciales_bp = Blueprint('comerciales_bp', __name__, url_prefix='/comerciales')

@comerciales_bp.route('/gestion')
def gestion_comerciales():
    comerciales = Comercial.query.order_by(Comercial.nombre).all()
    return render_template('comerciales/gestion_comerciales.html', comerciales=comerciales)

@comerciales_bp.route('/crear', methods=['GET','POST'])
def crear_comercial():
    if request.method == 'POST':
        nombre   = request.form['nombre']
        email    = request.form.get('email')
        telefono = request.form.get('telefono')
        nuevo = Comercial(nombre=nombre, email=email, telefono=telefono)
        db.session.add(nuevo)
        db.session.commit()
        flash('✅ Comercial creado.', 'success')
        return redirect(url_for('comerciales_bp.gestion_comerciales'))
    return render_template('comerciales/crear_comercial.html')

@comerciales_bp.route('/editar/<int:comercial_id>', methods=['GET','POST'])
def editar_comercial(comercial_id):
    com = Comercial.query.get_or_404(comercial_id)
    if request.method == 'POST':
        com.nombre   = request.form['nombre']
        com.email    = request.form.get('email')
        com.telefono = request.form.get('telefono')
        db.session.commit()
        flash('✏️ Comercial actualizado.', 'info')
        return redirect(url_for('comerciales_bp.gestion_comerciales'))
    return render_template('comerciales/editar_comercial.html', comercial=com)

@comerciales_bp.route('/eliminar/<int:comercial_id>', methods=['POST'])
def eliminar_comercial(comercial_id):
    com = Comercial.query.get_or_404(comercial_id)
    db.session.delete(com)
    db.session.commit()
    flash('🗑️ Comercial eliminado.', 'warning')
    return redirect(url_for('comerciales_bp.gestion_comerciales'))
