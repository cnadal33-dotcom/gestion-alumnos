from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from mi_plataforma_formacion_app.models.formador import Formador
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.extensions import db
from .forms import FormadorForm
import os
import unicodedata
import re
from werkzeug.utils import secure_filename

formadores_bp = Blueprint('formadores_bp', __name__)

def normalizar_nombre(nombre):
    nombre = unicodedata.normalize('NFD', nombre).encode('ascii', 'ignore').decode('utf-8')
    nombre = re.sub(r'[^a-zA-Z0-9]', '_', nombre).lower()
    return nombre.strip('_')

@formadores_bp.route('/')
def gestion_formadores():
    formadores = Formador.query.all()
    return render_template('formadores/gestion_formadores.html', formadores=formadores)

@formadores_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo_formador():
    form = FormadorForm()
    form.tipos_curso.choices = [(tc.id, tc.nombre) for tc in TipoCurso.query.order_by(TipoCurso.nombre).all()]
    
    if form.validate_on_submit():
        firma_filename = None
        if form.firma.data:
            nombre_normalizado = normalizar_nombre(form.nombre.data)
            filename = secure_filename(f"firma_{nombre_normalizado}.png")
            firma_path = os.path.join(current_app.static_folder, 'firmas_formadores', filename)
            form.firma.data.save(firma_path)
            firma_filename = filename

        formador = Formador(
            nombre=form.nombre.data,
            email=form.email.data,
            telefono=form.telefono.data,
            firma=firma_filename,
            tipos_curso=TipoCurso.query.filter(TipoCurso.id.in_(form.tipos_curso.data)).all()
        )
        db.session.add(formador)
        db.session.commit()
        flash("Formador creado correctamente.", "success")
        return redirect(url_for('formadores_bp.gestion_formadores'))

    return render_template('formadores/crear_formador.html', form=form)

@formadores_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_formador(id):
    formador = Formador.query.get_or_404(id)
    form = FormadorForm(obj=formador)
    form.tipos_curso.choices = [(tc.id, tc.nombre) for tc in TipoCurso.query.order_by(TipoCurso.nombre).all()]

    if form.validate_on_submit():
        formador.nombre = form.nombre.data
        formador.email = form.email.data
        formador.telefono = form.telefono.data

        if form.firma.data:
            nombre_normalizado = normalizar_nombre(form.nombre.data)
            filename = secure_filename(f"firma_{nombre_normalizado}.png")
            firma_path = os.path.join(current_app.static_folder, 'firmas_formadores', filename)
            # SOLO guarda archivo si es un objeto FileStorage, no si es string
            if hasattr(form.firma.data, "save"):
                form.firma.data.save(firma_path)
                formador.firma = filename
            elif isinstance(form.firma.data, str):
                formador.firma = form.firma.data

        formador.tipos_curso = TipoCurso.query.filter(TipoCurso.id.in_(form.tipos_curso.data)).all()
        db.session.commit()
        flash("Formador actualizado correctamente.", "success")
        return redirect(url_for('formadores_bp.gestion_formadores'))

    form.tipos_curso.data = [tc.id for tc in formador.tipos_curso]
    return render_template('formadores/editar_formador.html', form=form, formador=formador)

@formadores_bp.route('/borrar/<int:id>', methods=['POST'])
def borrar_formador(id):
    formador = Formador.query.get_or_404(id)
    db.session.delete(formador)
    db.session.commit()
    flash("Formador eliminado correctamente.", "success")
    return redirect(url_for('formadores_bp.gestion_formadores'))
