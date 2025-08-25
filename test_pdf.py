from pdfrw import PdfReader, PdfWriter, PdfDict, PdfObject
import os

ruta_plantilla_pdf = "C:\\Users\\Carlos Nadal\\Documents\\Base de datos alumnos\\mi_plataforma_formacion_nueva\\diploma_autorrellenable_demo.pdf"
ruta_salida_pdf = "C:\\Users\\Carlos Nadal\\Documents\\Base de datos alumnos\\mi_plataforma_formacion_nueva\\diploma_autorrellenable_demo_relleno.pdf"

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
    pdf = PdfReader(ruta_plantilla_pdf)
    campos_encontrados = []
    for page in pdf.pages:
        if page.Annots:
            for annot in page.Annots:
                if annot.T:
                    key = annot.T[1:-1]
                    campos_encontrados.append(key)
                    if key in data:
                        annot.V = data[key]
                        annot.AP = None
    print(f"Campos encontrados en el PDF: {campos_encontrados}")
    if '/AcroForm' in pdf.Root:
        pdf.Root.AcroForm.update(PdfDict(NeedAppearances=PdfObject('true')))
    else:
        pdf.Root.AcroForm = PdfDict(NeedAppearances=PdfObject('true'))
    PdfWriter(ruta_salida_pdf, trailer=pdf).write()
    print(f"PDF rellenado guardado en: {ruta_salida_pdf}")

    if campos_encontrados:
        print(f"Campos rellenables detectados en el PDF:")
        for campo in campos_encontrados:
            print(f"  - {campo}")
    else:
        print("No se detectaron campos rellenables en el PDF. Asegúrate de que el PDF tiene campos AcroForm tipo texto.")