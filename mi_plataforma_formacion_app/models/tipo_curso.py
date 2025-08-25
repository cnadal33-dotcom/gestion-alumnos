from mi_plataforma_formacion_app.extensions import db
from mi_plataforma_formacion_app.models.formador_tipo_curso import formador_tipo_curso

class TipoCurso(db.Model):
    __tablename__ = 'tipo_curso'
    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(128), nullable=False)
    duracion_horas= db.Column(db.Integer)
    temario       = db.Column(db.Text)
    objetivos     = db.Column(db.Text)
    pdf_temario   = db.Column(db.String(255))
    pdf_objetivos = db.Column(db.String(255))
    validez_meses = db.Column(db.Integer, nullable=False, default=0)
    color = db.Column(db.String(20), default="#FFA500")
    requiere_renovacion = db.Column(db.Boolean, nullable=False, default=False)
    formaciones   = db.relationship('Formacion', backref='tipo_curso', lazy=True)
    formadores    = db.relationship('Formador', secondary=formador_tipo_curso, back_populates='tipos_curso')
    examen_modelo_id = db.Column(db.Integer, db.ForeignKey('examen_modelo.id'))
    examen_modelo = db.relationship('ExamenModelo', back_populates='tipos_curso')
    plantilla_diploma_id = db.Column(db.Integer, db.ForeignKey('plantilla_diploma.id'), nullable=True)
    plantilla_acta_id = db.Column(db.Integer, db.ForeignKey('plantilla_acta.id'), nullable=True)
