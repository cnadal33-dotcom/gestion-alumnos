from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

# Inicialización de extensiones
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
