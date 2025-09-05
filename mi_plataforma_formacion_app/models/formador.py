from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.formador_tipo_curso import formador_tipo_curso

class Formador(db.Model):
    __tablename__ = 'formador'
    id       = db.Column(db.Integer, primary_key=True)
    nombre   = db.Column(db.String(128), nullable=False)
    email    = db.Column(db.String(128))
    telefono = db.Column(db.String(32))
    firma = db.Column(db.String(200))
    formaciones = db.relationship('Formacion', backref='formador', lazy=True)
    tipos_curso  = db.relationship('TipoCurso', secondary=formador_tipo_curso, back_populates='formadores')
