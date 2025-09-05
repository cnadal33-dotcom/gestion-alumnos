import csv
from flask import Blueprint, jsonify, request

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/api/poblaciones')
def api_poblaciones():
    q = request.args.get('q', '').strip().lower()
    resultados = []
    with open('poblaciones.csv', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if q in row['poblacion'].lower():
                resultados.append({
                    "label": f"{row['poblacion']} ({row['provincia']})",
                    "value": row["poblacion"],
                    "provincia": row["provincia"]
                })
    return jsonify(resultados)
from mi_plataforma_formacion_app.models.alumno import Alumno

@api_bp.route('/api/buscar_alumnos')
def buscar_alumnos():
    q = request.args.get('q', '')
    alumnos = Alumno.query.filter(
        (Alumno.nombre.ilike(f"%{q}%")) | (Alumno.dni.ilike(f"%{q}%"))
    ).all()
    results = []
    for alumno in alumnos:
        results.append({
            "id": alumno.id,
            "nombre": alumno.nombre,
            "dni": alumno.dni
        })
    return jsonify({"results": results})


@api_bp.route('/api/empresas/select2')
def empresas_select2():
    from flask import jsonify, request
    from mi_plataforma_formacion_app.models.empresa import Empresa
    q = request.args.get('q', '').strip()
    page = max(int(request.args.get('page', 1)), 1)
    per_page = 20
    query = Empresa.query
    if q:
        query = query.filter(Empresa.nombre.ilike(f'%{q}%'))
    pagination = query.order_by(Empresa.nombre.asc()).paginate(page=page, per_page=per_page, error_out=False)
    items = [{'id': e.id, 'text': e.nombre} for e in pagination.items]
    return jsonify({'items': items, 'more': pagination.has_next})


@api_bp.route('/api/empresas/datalist')
def empresas_datalist():
    from flask import jsonify
    from mi_plataforma_formacion_app.models.empresa import Empresa
    nombres = [e.nombre for e in Empresa.query.order_by(Empresa.nombre.asc()).limit(500).all()]
    return jsonify(nombres)

