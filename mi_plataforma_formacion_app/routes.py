from flask import Blueprint, render_template

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

from flask import Blueprint, render_template

preguntas_bp = Blueprint('preguntas_bp', __name__)

@preguntas_bp.route('/')
def lista_preguntas():
    return "Gestión de preguntas (en construcción)"
