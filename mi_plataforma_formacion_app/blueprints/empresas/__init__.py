from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Importa blueprints aquí DENTRO de la función y después de crear app
    from .blueprints.empresas.routes import empresas_bp
    app.register_blueprint(empresas_bp, url_prefix='/empresas')

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
