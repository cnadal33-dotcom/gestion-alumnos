
from mi_plataforma_formacion_app import create_app
from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.user import User

app = create_app()

# Crear usuario admin si no existe
with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', email='admin@localhost', role='admin', is_active=True)
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        print('Usuario admin creado (usuario: admin, contraseña: admin)')

if __name__ == "__main__":
    app.run(debug=True, port=5001)
