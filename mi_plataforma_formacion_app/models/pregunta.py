from mi_plataforma_formacion_app.extensions import db

class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    examen_modelo_id = db.Column(db.Integer, db.ForeignKey('examen_modelo.id'))
    respuestas = db.relationship('Respuesta', backref='pregunta', lazy=True, cascade="all, delete-orphan")
