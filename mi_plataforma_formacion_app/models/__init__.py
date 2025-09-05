


# Importar el modelo ExamenAlumno para que esté disponible en el paquete
from .examen_alumno import ExamenAlumno
# Importar el modelo Alumno para que esté disponible en el paquete
from .alumno import Alumno
# Importar el modelo Formacion para que esté disponible en el paquete
from .formacion import Formacion
from .alumno_formacion import AlumnoFormacion
from .respuesta import Respuesta
"""
Exposición de modelos en el paquete `mi_plataforma_formacion_app.models`.
Permite importar por ejemplo: `from mi_plataforma_formacion_app.models import Pregunta`.
"""

# Modelos principales
from .examen_alumno import ExamenAlumno
from .alumno import Alumno
from .formacion import Formacion
from .alumno_formacion import AlumnoFormacion
from .respuesta import Respuesta
from .pregunta import Pregunta

# (Opcional) otros modelos que suelen importarse desde el paquete
from .examen_modelo import ExamenModelo
from .tipo_curso import TipoCurso
from .empresa import Empresa
from .comercial import Comercial


