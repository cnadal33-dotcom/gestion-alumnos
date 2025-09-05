from flask import Blueprint, render_template, redirect, url_for, request, flash
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.permission import Permission

permisos_bp = Blueprint('permisos_bp', __name__, url_prefix='/configuracion/permisos')

@permisos_bp.route('/')
def lista_permisos():
    permisos = Permission.query.all()
    return render_template('configuracion/permisos/lista.html', permisos=permisos)

@permisos_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_permiso():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        if Permission.query.filter_by(name=name).first():
            flash('El permiso ya existe', 'danger')
            return redirect(url_for('permisos_bp.nuevo_permiso'))
        permiso = Permission(name=name, description=description)
        db.session.add(permiso)
        db.session.commit()
        flash('Permiso creado correctamente', 'success')
        return redirect(url_for('permisos_bp.lista_permisos'))
    return render_template('configuracion/permisos/nuevo.html')

@permisos_bp.route('/eliminar/<int:permiso_id>', methods=['POST'])
def eliminar_permiso(permiso_id):
    permiso = Permission.query.get_or_404(permiso_id)
    db.session.delete(permiso)
    db.session.commit()
    flash('Permiso eliminado', 'success')
    return redirect(url_for('permisos_bp.lista_permisos'))
