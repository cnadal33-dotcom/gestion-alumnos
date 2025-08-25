from flask import Blueprint, render_template, redirect, url_for
from mi_plataforma_formacion_app.models.comercial import Comercial
from mi_plataforma_formacion_app.extensions import db
from .forms import ComercialForm

comerciales_bp = Blueprint('comerciales_bp', __name__)

@comerciales_bp.route('/')
def gestion_comerciales():
    comerciales = Comercial.query.all()
    return render_template('comerciales/gestion_comerciales.html', comerciales=comerciales)

@comerciales_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_comercial():
    form = ComercialForm()
    if form.validate_on_submit():
        nuevo = Comercial(nombre=form.nombre.data, email=form.email.data, telefono=form.telefono.data)
        db.session.add(nuevo)
        db.session.commit()
        return redirect(url_for('comerciales_bp.gestion_comerciales'))
    return render_template('comerciales/crear_comercial.html', form=form)

@comerciales_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_comercial(id):
    comercial = Comercial.query.get_or_404(id)
    form = ComercialForm(obj=comercial)
    if form.validate_on_submit():
        comercial.nombre = form.nombre.data
        comercial.email = form.email.data
        comercial.telefono = form.telefono.data
        db.session.commit()
        return redirect(url_for('comerciales_bp.gestion_comerciales'))
    return render_template('comerciales/editar_comercial.html', form=form, comercial=comercial)

@comerciales_bp.route('/borrar/<int:id>', methods=['POST'])
def borrar_comercial(id):
    comercial = Comercial.query.get_or_404(id)
    db.session.delete(comercial)
    db.session.commit()
    return redirect(url_for('comerciales_bp.gestion_comerciales'))

# blueprints/comerciales/routes.py

@comerciales_bp.route('/<int:comercial_id>')
def ficha_comercial(comercial_id):
    comercial = Comercial.query.get_or_404(comercial_id)
    empresas = sorted(comercial.empresas, key=lambda e: e.nombre)
    return render_template('comerciales/ficha_comercial.html', comercial=comercial, empresas=empresas)
