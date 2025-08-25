from pypdf import PdfReader, PdfWriter
import os

ruta_plantilla_pdf = "diploma_autorrellenable_demo.pdf"
ruta_salida_pdf = "diploma_autorrellenable_demo_aplanado.pdf"

data = {
    'NOMBRE': 'Carlos Nadal',
    'DNI': '12345678A',
    'CURSO': 'Curso de Prueba',
    'FECHA': '08/08/2025',
    'POBLACION': 'Valencia',
    'INSTRUCTOR': 'Profesor Ejemplo'
}

if not os.path.exists(ruta_plantilla_pdf):
    print(f"Error: La plantilla PDF no se encontró en '{ruta_plantilla_pdf}'")
else:
    reader = PdfReader(ruta_plantilla_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        if '/Annots' in page:
            for annot in page['/Annots']:
                if annot.get('/T'):
                    key = annot['/T'][1:-1]
                    if key in data:
                        annot.update({
                            '/V': data[key],
                            '/Ff': 1
                        })
        writer.add_page(page)
    writer.remove_annotations()
    with open(ruta_salida_pdf, 'wb') as f:
        writer.write(f)
    print(f"PDF aplanado y rellenado guardado en: {ruta_salida_pdf}")
