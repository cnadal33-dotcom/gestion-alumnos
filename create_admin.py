from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.user import User
from flask import Flask
from mi_plataforma_formacion_app import create_app

app = create_app()

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@admin.com', role='admin', is_active=True)
    admin.set_password('admin')
    admin.is_active = True
    admin.role = 'admin'
    db.session.add(admin)
    db.session.commit()
    print('Usuario admin creado/actualizado con contraseña "admin".')
