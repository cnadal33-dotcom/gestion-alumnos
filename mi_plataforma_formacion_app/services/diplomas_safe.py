import os
import datetime as dt
from flask import current_app


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def slug(text):
    return "".join(c if c.isalnum() else "_" for c in (text or ""))[:60] or "curso"


def safe_generate_diploma(alumno, formacion, generate_fillable, generate_simple):
    """
    generate_fillable(alumno, formacion, destino) -> ruta_pdf
    generate_simple(alumno, formacion, destino)   -> ruta_pdf
    """
    base_dir = current_app.config.get(
        "DIPLOMAS_DIR",
        os.path.join(current_app.instance_path, "diplomas")
    )
    ensure_dir(base_dir)
    subdir = os.path.join(base_dir, f"{formacion.id}_{slug(formacion.referencia or str(formacion.id))}")
    ensure_dir(subdir)

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = os.path.join(subdir, f"diploma_{getattr(alumno, 'id', 'anon')}_{ts}.pdf")

    try:
        ruta = generate_fillable(alumno, formacion, destino)
        return ruta, None  # ok sin errores
    except Exception:
        current_app.logger.exception("Error generando diploma autorrellenable (fallback a simple)")
        try:
            simple_dest = destino.replace(".pdf", "_simple.pdf")
            ruta = generate_simple(alumno, formacion, simple_dest)
            return ruta, "No se pudo generar el diploma autorrellenable. Se creó un diploma estándar."
        except Exception:
            current_app.logger.exception("Error también en diploma simple")
            return None, "No se pudo generar el diploma. Revisa plantilla, permisos o dependencias."
