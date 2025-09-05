from flask import Flask
from mi_plataforma_formacion_app.extensions import db
from flask_migrate import Migrate

# Inicializa Migrate
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configuración de base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    from mi_plataforma_formacion_app.blueprints.empresas.routes import empresas_bp
    app.register_blueprint(empresas_bp, url_prefix='/empresas')

    from mi_plataforma_formacion_app.blueprints.alumnos.routes import alumnos_bp
    app.register_blueprint(alumnos_bp, url_prefix='/alumnos')

    from mi_plataforma_formacion_app.blueprints.comerciales.routes import comerciales_bp
    app.register_blueprint(comerciales_bp, url_prefix='/comerciales')

    from mi_plataforma_formacion_app.blueprints.tipo_curso.routes import tipo_curso_bp
    app.register_blueprint(tipo_curso_bp, url_prefix='/tipo_curso')

    from mi_plataforma_formacion_app.blueprints.formadores.routes import formadores_bp
    app.register_blueprint(formadores_bp, url_prefix='/formadores')

    from mi_plataforma_formacion_app.blueprints.formaciones.routes import formaciones_bp
    app.register_blueprint(formaciones_bp, url_prefix='/formaciones')

    from mi_plataforma_formacion_app.blueprints.diplomas.routes import diplomas_bp
    app.register_blueprint(diplomas_bp, url_prefix='/diplomas')

    from mi_plataforma_formacion_app.blueprints.preguntas.routes import preguntas_bp
    app.register_blueprint(preguntas_bp, url_prefix='/preguntas')

    return app
