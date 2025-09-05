from flask import Blueprint, render_template, request, send_file
from mi_plataforma_formacion_app.models.alumno_formacion import AlumnoFormacion
from datetime import date
import io
import pandas as pd

caducidades_bp = Blueprint('caducidades_bp', __name__)

@caducidades_bp.route('/caducidades')
def listado_caducidades():
    hoy = date.today()
    query = AlumnoFormacion.query
    busqueda = request.args.get('q', '').strip().lower()
    estado_filtro = request.args.get('estado', 'todos')  # 'todos', 'vigente', 'proximo', 'caducado'

    # Filtra por búsqueda
    if busqueda:
        rels = []
        for rel in query.all():
            alumno = rel.alumno.nombre.lower() if rel.alumno and rel.alumno.nombre else ""
            empresa = rel.formacion.empresa.nombre.lower() if rel.formacion and rel.formacion.empresa and rel.formacion.empresa.nombre else ""
            curso = rel.formacion.tipo_curso.nombre.lower() if rel.formacion and rel.formacion.tipo_curso and rel.formacion.tipo_curso.nombre else ""
            if busqueda in alumno or busqueda in empresa or busqueda in curso:
                rels.append(rel)
    else:
        rels = query.all()

    # Filtra por estado
    if estado_filtro == 'vigente':
        rels = [rel for rel in rels if rel.estado_validez == 'Vigente']
    elif estado_filtro == 'proximo':
        rels = [rel for rel in rels if rel.estado_validez == 'Próxima a caducar']
    elif estado_filtro == 'caducado':
        rels = [rel for rel in rels if rel.estado_validez == 'Caducado']

    # Listas por estado para tablas
    proximos = [rel for rel in rels if rel.estado_validez == 'Próxima a caducar']
    caducados = [rel for rel in rels if rel.estado_validez == 'Caducado']
    vigentes = [rel for rel in rels if rel.estado_validez == 'Vigente']

    # Si filtras por estado, solo rellena esa tabla
    if estado_filtro == 'vigente':
        caducados = []
        proximos = []
    elif estado_filtro == 'proximo':
        caducados = []
        vigentes = []
    elif estado_filtro == 'caducado':
        vigentes = []
        proximos = []

    return render_template(
        'caducidades/listado_caducidades.html',
        caducados=caducados,
        proximos=proximos,
        vigentes=vigentes,
        busqueda=busqueda,
        estado_filtro=estado_filtro
    )

@caducidades_bp.route('/caducidades/excel')
def exportar_caducidades_excel():
    busqueda = request.args.get('q', '').strip().lower()
    estado_filtro = request.args.get('estado', 'todos')
    query = AlumnoFormacion.query

    # Filtra por búsqueda
    if busqueda:
        rels = []
        for rel in query.all():
            alumno = rel.alumno.nombre.lower() if rel.alumno and rel.alumno.nombre else ""
            empresa = rel.formacion.empresa.nombre.lower() if rel.formacion and rel.formacion.empresa and rel.formacion.empresa.nombre else ""
            curso = rel.formacion.tipo_curso.nombre.lower() if rel.formacion and rel.formacion.tipo_curso and rel.formacion.tipo_curso.nombre else ""
            if busqueda in alumno or busqueda in empresa or busqueda in curso:
                rels.append(rel)
    else:
        rels = query.all()

    # Filtra por estado
    if estado_filtro == 'vigente':
        rels = [rel for rel in rels if rel.estado_validez == 'Vigente']
    elif estado_filtro == 'proximo':
        rels = [rel for rel in rels if rel.estado_validez == 'Próxima a caducar']
    elif estado_filtro == 'caducado':
        rels = [rel for rel in rels if rel.estado_validez == 'Caducado']

    data = []
    for rel in rels:
        data.append({
            "Alumno": rel.alumno.nombre,
            "DNI": rel.alumno.dni,
            "Empresa": rel.formacion.empresa.nombre if rel.formacion.empresa else "-",
            "Curso": rel.formacion.tipo_curso.nombre,
            "Fecha realización": rel.fecha_realizacion.strftime("%d/%m/%Y") if rel.fecha_realizacion else "",
            "Fecha caducidad": rel.fecha_caducidad.strftime("%d/%m/%Y") if rel.fecha_caducidad else "",
            "Estado": rel.estado_validez
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Caducidades')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="caducidades.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
