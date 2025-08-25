from mi_plataforma_formacion_app.extensions import db

formador_tipo_curso = db.Table(
    'formador_tipo_curso',
    db.Column('formador_id', db.Integer, db.ForeignKey('formador.id'), primary_key=True),
    db.Column('tipo_curso_id', db.Integer, db.ForeignKey('tipo_curso.id'), primary_key=True)
)
