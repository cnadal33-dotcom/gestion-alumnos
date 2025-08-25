from flask import Blueprint, render_template, request
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.models.empresa import Empresa
from datetime import date, timedelta

renovaciones_bp = Blueprint('renovaciones_bp', __name__)

@renovaciones_bp.route('/renovaciones')
def panel_renovaciones():
    # Filtro opcional por empresa, tipo de curso o fecha hasta
    empresa_id = request.args.get('empresa_id', type=int)
    tipo_curso_id = request.args.get('tipo_curso_id', type=int)
    dias = request.args.get('dias', default=90, type=int)
    fecha_limite = date.today() + timedelta(days=dias)

    query = Formacion.query.filter(Formacion.fecha1 != None)
    # Filtrar solo las realizadas hace más de 21 meses (para que queden 3 meses para los 2 años)
    query = query.filter(Formacion.fecha1 + timedelta(days=730) <= fecha_limite)
    if empresa_id:
        query = query.filter(Formacion.empresa_id == empresa_id)
    if tipo_curso_id:
        query = query.filter(Formacion.tipo_curso_id == tipo_curso_id)

    formaciones = query.order_by(Formacion.fecha1.desc()).all()
    empresas = Empresa.query.order_by(Empresa.nombre).all()
    tipos = TipoCurso.query.order_by(TipoCurso.nombre).all()
    hoy = date.today()

    return render_template(
        'renovaciones/panel_renovaciones.html',
        formaciones=formaciones,
        empresas=empresas,
        tipos=tipos,
        hoy=hoy,
        empresa_id=empresa_id,
        tipo_curso_id=tipo_curso_id,
        dias=dias,
        fecha_limite=fecha_limite,
        timedelta=timedelta # <--- ¡Solo un nombre de argumento y su valor!
    )