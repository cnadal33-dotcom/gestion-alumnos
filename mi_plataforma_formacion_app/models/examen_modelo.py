from mi_plataforma_formacion_app.extensions import db

class ExamenModelo(db.Model):
    __tablename__ = 'examen_modelo'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(128), nullable=False)
    descripcion = db.Column(db.Text)
    preguntas = db.relationship('Pregunta', backref='examen_modelo', lazy=True, cascade="all, delete-orphan")
    tipos_curso = db.relationship('TipoCurso', back_populates='examen_modelo')
