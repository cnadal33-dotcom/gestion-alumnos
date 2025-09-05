pdf_path = 'RUTA_A_TU_PDF.pdf'  # Cambia esto por la ruta real

import sys
from pdfrw import PdfReader

if len(sys.argv) < 2:
    print('Uso: python listar_campos_pdf.py <ruta_al_pdf>')
    sys.exit(1)

pdf_path = sys.argv[1]
pdf = PdfReader(pdf_path)

print('Campos de formulario encontrados:')
for idx, page in enumerate(pdf.pages):
    annots = getattr(page, 'Annots', None)
    if annots:
        for a in annots:
            t = str(a.T)
            nombre = t[1:-1] if t.startswith('(') and t.endswith(')') else t
            print(f"Página {idx+1}: '{nombre}'")
