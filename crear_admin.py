from flask import Flask
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.user import User

# Configuración de la app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///formacion.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)

with app.app_context():
    # Crear todas las tablas si no existen
    db.create_all()

    # Buscar usuario admin
    user = User.query.filter_by(username='admin').first()

    if not user:
        # Crear usuario admin
        user = User(
            username='admin',
            email='admin@admin.com',
            role='admin',
            is_active=True
        )
        user.set_password('admin')  # Cambiar contraseña en producción
        db.session.add(user)
        db.session.commit()
        print('Usuario admin creado.')
    else:
        # Actualizar usuario admin
        user.set_password('admin')  # Cambiar contraseña en producción
        user.is_active = True
        db.session.commit()
        print('Usuario admin actualizado.')
