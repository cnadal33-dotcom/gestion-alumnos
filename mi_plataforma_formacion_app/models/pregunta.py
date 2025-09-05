from mi_plataforma_formacion_app.extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy import and_

class Pregunta(db.Model):
    __tablename__ = 'pregunta'
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    examen_modelo_id = db.Column(db.Integer, db.ForeignKey('examen_modelo.id'))
    # Todas las respuestas (incluye respuestas de alumnos y del modelo)
    respuestas = db.relationship('Respuesta', backref='pregunta', lazy=True, cascade="all, delete-orphan")

    # Relación filtrada: solo las opciones del modelo (examen_alumno_id IS NULL)
    respuestas_modelo = relationship(
        "Respuesta",
        primaryjoin="and_(Respuesta.pregunta_id==Pregunta.id, Respuesta.examen_alumno_id==None)",
        viewonly=True,
        lazy="selectin"
    )
