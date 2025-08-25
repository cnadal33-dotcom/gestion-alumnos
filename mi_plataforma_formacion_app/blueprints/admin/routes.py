from flask import Blueprint, render_template, request, redirect, url_for, flash
from mi_plataforma_formacion_app.models.alumno import Alumno
from mi_plataforma_formacion_app.models.empresa import Empresa
from mi_plataforma_formacion_app.models.formacion import Formacion
from mi_plataforma_formacion_app.models.tipo_curso import TipoCurso
from sqlalchemy import extract, or_
from datetime import date, timedelta

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
def dashboard():
    # Parámetros de filtrado
    anio = request.args.get('anio', type=int)
    empresa_id = request.args.get('empresa_id', type=int)

    # Query base para filtrar formaciones
    formaciones_query = Formacion.query
    if anio:
        formaciones_query = formaciones_query.filter(extract('year', Formacion.fecha1) == anio)
    if empresa_id:
        formaciones_query = formaciones_query.filter(Formacion.empresa_id == empresa_id)
    formaciones_filtradas = formaciones_query.all()

    # Listado de años para el filtro
    lista_anios = sorted(list({f.fecha1.year for f in Formacion.query if f.fecha1}), reverse=True)
    empresas_all = Empresa.query.order_by(Empresa.nombre).all()

    # Totales globales
    total_formaciones_global = Formacion.query.count()
    total_alumnos_global = Alumno.query.count()
    total_empresas_global = Empresa.query.count()

    # Totales filtrados
    total_formaciones_filtrado = len(formaciones_filtradas)
    alumnos_filtrados = {rel.alumno_id for f in formaciones_filtradas for rel in f.alumno_formaciones}
    total_alumnos_filtrado = len(alumnos_filtrados)

    # Empresas filtradas (solo las que tienen formaciones en el filtro)
    empresas_filtradas = {f.empresa_id for f in formaciones_filtradas if f.empresa_id}
    total_empresas_filtrado = len(empresas_filtradas)

    # Próximas formaciones a caducar (90 días, según filtro)
    hoy = date.today()
    proximos_90 = hoy + timedelta(days=90)
    formaciones_caducan = [f for f in formaciones_filtradas if f.fecha1 and hoy <= f.fecha1 <= proximos_90]

    # Datos para el gráfico: cantidad de formaciones por año de la empresa filtrada
    formaciones_empresa = Formacion.query
    if empresa_id:
        formaciones_empresa = formaciones_empresa.filter(Formacion.empresa_id == empresa_id)
    formaciones_empresa = formaciones_empresa.all()
    resumen_por_anio = {}
    for f in formaciones_empresa:
        if f.fecha1:
            y = f.fecha1.year
            resumen_por_anio[y] = resumen_por_anio.get(y, 0) + 1
    chart_labels = sorted(resumen_por_anio)
    chart_data = [resumen_por_anio[y] for y in chart_labels]

    return render_template(
        'admin/dashboard.html',
        # Totales globales
        total_formaciones=total_formaciones_global,
        total_alumnos=total_alumnos_global,
        total_empresas=total_empresas_global,
        # Totales filtrados
        total_formaciones_filtrado=total_formaciones_filtrado,
        total_alumnos_filtrado=total_alumnos_filtrado,
        total_empresas_filtrado=total_empresas_filtrado,
        # Otros datos
        lista_anios=lista_anios,
        empresas_all=empresas_all,
        anio=anio,
        empresa_id=empresa_id,
        formaciones_caducan=formaciones_caducan,
        chart_labels=chart_labels,
        chart_data=chart_data
    )
@admin_bp.route('/buscar_global')
def buscar_global():
    q = request.args.get('q', '').strip()
    if not q:
        flash("Introduce un texto para buscar.", "warning")
        return redirect(url_for('admin_bp.dashboard'))

    # Buscar en alumnos
    alumnos = Alumno.query.filter(
        or_(
            Alumno.nombre.ilike(f'%{q}%'),
            Alumno.dni.ilike(f'%{q}%'),
            Alumno.email.ilike(f'%{q}%')
        )
    ).all()
    # Buscar en empresas
    empresas = Empresa.query.filter(
        or_(
            Empresa.nombre.ilike(f'%{q}%'),
            Empresa.cif.ilike(f'%{q}%') if hasattr(Empresa, 'cif') else False
        )
    ).all()
    # Buscar en formaciones
    formaciones = Formacion.query.filter(
        or_(
            Formacion.referencia.ilike(f'%{q}%'),
            Formacion.observaciones.ilike(f'%{q}%')
        )
    ).all()

    return render_template(
        'admin/resultados_busqueda.html',
        q=q,
        alumnos=alumnos,
        empresas=empresas,
        formaciones=formaciones
    )
