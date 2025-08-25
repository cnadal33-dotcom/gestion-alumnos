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

