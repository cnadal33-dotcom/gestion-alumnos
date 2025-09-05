from mi_plataforma_formacion_app.extensions import db

class Comercial(db.Model):
    __tablename__ = 'comercial'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(128), nullable=False)
    email    = db.Column(db.String(128))
    telefono = db.Column(db.String(32))
    empresas = db.relationship('Empresa', backref='comercial', lazy=True)
