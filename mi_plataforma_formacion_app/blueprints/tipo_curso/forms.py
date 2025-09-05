from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, SelectField, BooleanField
from flask_wtf.file import FileField, FileAllowed
from wtforms.widgets import ColorInput

class TipoCursoForm(FlaskForm):
    nombre = StringField('Nombre', render_kw={"class": "form-control"})
    duracion_horas = IntegerField('Duración (horas)', render_kw={"class": "form-control"})
    temario = TextAreaField('Temario', render_kw={"class": "form-control"})
    # objetivos = TextAreaField('Objetivos', render_kw={"class": "form-control"})
    pdf_objetivos = FileField('PDF Objetivos', validators=[FileAllowed(['pdf'], 'Solo PDF')])
    examen_modelo_id = SelectField('Examen Modelo', coerce=int, render_kw={"class": "form-control"})
    pdf_temario = FileField('PDF Temario', validators=[FileAllowed(['pdf'], 'Solo PDF')])
    validez_meses = IntegerField('Validez (meses)', default=0, render_kw={"class": "form-control"})
    validez_permanente = BooleanField('Validez permanente', default=False, render_kw={"class": "form-check-input"})

    color = StringField('Color', widget=ColorInput(), default='#4287f5',
                       render_kw={"class": "form-control form-control-color", "style": "width: 4rem; height: 2.2rem; padding:0.1em;"})

    plantilla_diploma_id = SelectField('Plantilla de diploma', coerce=int, render_kw={"class": "form-control"})
    plantilla_acta_id = SelectField('Plantilla de acta', coerce=int, render_kw={"class": "form-control"})

    submit = SubmitField('Guardar')


    def set_examen_choices(self):
        from mi_plataforma_formacion_app.models.examen_modelo import ExamenModelo
        self.examen_modelo_id.choices = [(0, 'Sin examen')] + [(e.id, e.nombre) for e in ExamenModelo.query.all()]

    def set_plantilla_choices(self):
        from mi_plataforma_formacion_app.models.plantilla_diploma import PlantillaDiploma
        self.plantilla_diploma_id.choices = [(0, 'Sin plantilla')] + [(p.id, p.nombre) for p in PlantillaDiploma.query.all()]

    def set_plantilla_acta_choices(self):
        from mi_plataforma_formacion_app.models.plantilla_acta import PlantillaActa
        self.plantilla_acta_id.choices = [(0, 'Sin plantilla')] + [(p.id, p.nombre) for p in PlantillaActa.query.all()]
