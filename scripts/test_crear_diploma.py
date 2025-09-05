"""Script de humo para probar crear_y_guardar_diploma en un entorno aislado.
No modifica la base de datos de producción; guarda el PDF resultado en /tmp para inspección.

Uso:
  python3 scripts/test_crear_diploma.py

Requisitos: dependencia del proyecto en el entorno virtual activado (fitz, reportlab, flask, etc.)
"""
import os
import tempfile
from types import SimpleNamespace
from flask import Flask

# ajustar import path si es necesario
from mi_plataforma_formacion_app.blueprints.diplomas.routes import crear_y_guardar_diploma


def make_dummy_objects(tmp_static):
    # Alumno mínimo
    alumno = SimpleNamespace(nombre='Juan Pérez', dni='12345678A', nota=9.5)
    # Formacion mínima y tipo_curso con plantilla: usaremos una plantilla existente o copia de ejemplo
    tipo_curso = SimpleNamespace(nombre='Curso de Prueba', duracion_horas=8)
    # crear un dummy plantillas_diplomas en tmp_static
    # Preferir plantilla real del proyecto si existe
    project_tpl = os.path.join(os.path.dirname(__file__), '..', 'mi_plataforma_formacion_app', 'static', 'plantillas_diplomas', 'diploma_autorrellenable_demo.pdf')
    if os.path.isfile(project_tpl):
        plantilla_example_src = project_tpl
    else:
        plantilla_example_src = os.path.join(os.path.dirname(__file__), '..', 'diploma_autorrellenable_demo.pdf')
        if not os.path.isfile(plantilla_example_src):
            # si no existe, crea un PDF simple en tmp
            plantilla_example_src = os.path.join(tmp_static, 'dummy_template.pdf')
            from reportlab.pdfgen import canvas
            c = canvas.Canvas(plantilla_example_src)
            c.drawString(100, 800, "Plantilla dummy")
            c.save()

    # Guardar plantilla en static/plantillas_diplomas
    plantilla_dest_dir = os.path.join(tmp_static, 'plantillas_diplomas')
    os.makedirs(plantilla_dest_dir, exist_ok=True)
    plantilla_dest = os.path.join(plantilla_dest_dir, os.path.basename(plantilla_example_src))
    if not os.path.isfile(plantilla_dest):
        import shutil
        shutil.copy(plantilla_example_src, plantilla_dest)

    plantilla = SimpleNamespace(id=0, nombre='Dummy', ruta_pdf=f'plantillas_diplomas/{os.path.basename(plantilla_dest)}')

    formacion = SimpleNamespace(
        tipo_curso=tipo_curso,
        fecha1=None,
        formador=None,
        direccion_aula='Calle Falsa 123',
        poblacion='Ciudad Ejemplo',
        empresa=None,
        texto_libre='Texto de prueba'
    )

    return alumno, formacion, plantilla


def main():
    # App temporal
    app = Flask('test_app')
    tmp_static = tempfile.mkdtemp(prefix='test_static_')
    app.static_folder = tmp_static

    with app.app_context():
        alumno, formacion, plantilla = make_dummy_objects(tmp_static)
        # Añadimos la plantilla al formacion.tipo_curso para que crear_y_guardar_diploma la encuentre
        formacion.tipo_curso.plantilla_diploma = plantilla

        try:
            # llamar a la función; pasar la plantilla explícitamente
            resultado = crear_y_guardar_diploma(alumno, formacion, plantilla)
            print('Resultado:', type(resultado), resultado)
        except Exception as e:
            print('Error en crear_y_guardar_diploma:', e)

        print('Static folder usado (temporal):', tmp_static)

if __name__ == '__main__':
    main()
