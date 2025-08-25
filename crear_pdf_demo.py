from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName

# Crear PDF base con campos AcroForm
output_path = "diploma_autorrellenable_demo.pdf"
c = canvas.Canvas(output_path, pagesize=A4)
c.setFont("Helvetica-Bold", 20)
c.drawString(120, 800, "DIPLOMA DE FORMACIÓN")
c.setFont("Helvetica", 14)
c.drawString(120, 760, "Nombre del alumno:")
c.drawString(120, 720, "DNI:")
c.drawString(120, 680, "Curso:")
c.drawString(120, 640, "Fecha:")
c.drawString(120, 600, "Población:")
c.drawString(120, 560, "Formador:")
c.save()

# Añadir campos AcroForm con pdfrw
pdf = PdfReader(output_path)
fields = [
    ("NOMBRE", [120, 745, 400, 765]),
    ("DNI", [120, 705, 400, 725]),
    ("CURSO", [120, 665, 400, 685]),
    ("FECHA", [120, 625, 400, 645]),
    ("POBLACION", [120, 585, 400, 605]),
    ("INSTRUCTOR", [120, 545, 400, 565]),
]
annots = []
for name, rect in fields:
    annots.append(PdfDict(
        FT=PdfName('Tx'),
        Type=PdfName('Annot'),
        Subtype=PdfName('Widget'),
        T='({})'.format(name),
        Rect=rect,
        F=4,
        DA="/Helv 0 Tf 0 g"
    ))
pdf.pages[0].Annots = annots
pdf.Root.AcroForm = PdfDict(
    DA="/Helv 0 Tf 0 g",
    DR=PdfDict(Font=PdfDict(Helv=PdfDict(Type=PdfName('Font'), Subtype=PdfName('Type1'), BaseFont=PdfName('Helvetica')))),
    Fields=annots
)
PdfWriter(output_path, trailer=pdf).write()
print(f"PDF autorrellenable creado en: {output_path}")
