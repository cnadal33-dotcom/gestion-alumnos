from flask import Blueprint, render_template, request
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models import Empresa
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from mi_plataforma_formacion_app.extensions import db
from datetime import date
from sqlalchemy import func
import collections
from flask import jsonify, request
from sqlalchemy import inspect, text

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    # Recogemos filtros
    empresa_id     = request.args.get('empresa_id',   type=int)
    empresa_nombre = request.args.get('empresa_nombre', type=str)
    tipo_curso_id  = request.args.get('tipo_curso_id',type=int)
    anio           = request.args.get('anio',         type=int)
    hoy            = date.today()

    # Listas para los selects
    empresas     = Empresa.query.order_by(Empresa.nombre).all()
    tipos_curso  = TipoCurso.query.order_by(TipoCurso.nombre).all()
    lista_anios  = sorted(
        {f.fecha1.year for f in Formacion.query if f.fecha1},
        reverse=True
    )

    # 1) Filtrado de formaciones
    query = Formacion.query
    if empresa_id:
        query = query.filter(Formacion.empresa_id == empresa_id)
    elif empresa_nombre:
        empresa = Empresa.query.filter(Empresa.nombre.ilike(f"%{empresa_nombre}%")).first()
        if empresa:
            query = query.filter(Formacion.empresa_id == empresa.id)
        else:
            # Si no hay coincidencia, devolver lista vacía
            query = query.filter(Formacion.empresa_id == -1)
    if tipo_curso_id:
        query = query.filter(Formacion.tipo_curso_id == tipo_curso_id)
    if anio:
        query = query.filter(db.extract('year', Formacion.fecha1) == anio)

    formaciones_filtradas = query.order_by(Formacion.fecha1.desc()).all()

    # 2) Métricas
    total_formaciones   = len(formaciones_filtradas)
    total_empresas      = Empresa.query.count()            # TOTAL GLOBAL
    total_alumnos       = Alumno.query.count()             # TOTAL GLOBAL
    caducidades_proximas = 0   # tu lógica aquí
    avisos_caducidad     = []  # tu lógica aquí

    # 3) Próximas formaciones (si quieres, también podrías filtrar aquí con `query`)
    proximas_formaciones = Formacion.query\
        .filter(Formacion.fecha1 >= hoy)\
        .order_by(Formacion.fecha1.asc())\
        .limit(6).all()

    # 4) Datos para el gráfico (formaciones por año)
    conteo_anios = collections.OrderedDict()
    for f in formaciones_filtradas:
        if f.fecha1:
            y = f.fecha1.year
            conteo_anios[y] = conteo_anios.get(y, 0) + 1

    if conteo_anios:
        chart_labels = [str(y) for y in conteo_anios.keys()]
        chart_data   = [conteo_anios[y] for y in conteo_anios.keys()]
    else:
        chart_labels = [str(a) for a in lista_anios]
        chart_data   = [0] * len(chart_labels)

    # 5) Renderizamos todo
    empresas_json = [{"id": e.id, "nombre": e.nombre} for e in empresas]
    return render_template('index.html',
        empresas=empresas,
        empresas_json=empresas_json,
        tipos_curso=tipos_curso,
        lista_anios=lista_anios,
        empresa_id=empresa_id,
        tipo_curso_id=tipo_curso_id,
        anio=anio,
        total_formaciones=total_formaciones,
        total_empresas=total_empresas,
        total_alumnos=total_alumnos,
        caducidades_proximas=caducidades_proximas,
        proximas_formaciones=proximas_formaciones,
        avisos_caducidad=avisos_caducidad,
        chart_labels=chart_labels,
        chart_data=chart_data,
    )


@main_bp.route('/debug/schema/empresa')
def debug_schema_empresa():
    # Solo permitir acceso local
    if request.remote_addr not in ('127.0.0.1', '::1'):
        return "Forbidden", 403

    mapped = []
    try:
        tbl = db.Model.metadata.tables.get('empresa')
        if tbl is not None:
            mapped = [c.name for c in tbl.columns]
        else:
            inspector = inspect(db.engine)
            if 'empresa' in inspector.get_table_names():
                cols = inspector.get_columns('empresa')
                mapped = [c['name'] for c in cols]
    except Exception as e:
        mapped = [f"error: {e}"]

    pragma_cols = []
    try:
        with db.engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info('empresa')"))
            pragma_cols = [tuple(r) for r in res.fetchall()]
    except Exception as e:
        pragma_cols = [f"error: {e}"]

    return jsonify(mapped_columns=mapped, pragma=pragma_cols)
