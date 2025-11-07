import os

from flask import Flask, g, session
from .auth import auth_bp
from .main import main_bp
from .admin import admin_bp
from database import close_db

def create_app():
    """
    Función de fábrica para la aplicación Flask.
    """
    app = Flask(__name__, instance_relative_config=True, template_folder='../templates', static_folder='../static')
    
    # Configuración 
    app.config.from_mapping(
        SECRET_KEY='dev-secret-poné-otra-luego', #Cambiar
    )

    # --- Configuración de Subida de Archivos ---
    BASE_DIR = os.path.dirname(os.path.abspath(app.instance_path))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Crear carpeta de uploads si no existe
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # Registro de Funciones y Blueprints
    
    # Cerrar DB al final de cada request
    app.teardown_appcontext(close_db)

    # decorador para cargar usuario actual en g.user antes de cada request
    @app.before_request
    def load_current_user():
        from database import get_db
        g.user = None
        uid = session.get("user_id")
        if uid is not None:
            db = get_db()
            g.user = db.execute(
                "SELECT id, username, rol FROM usuarios WHERE id = ?", (uid,)
            ).fetchone()

    #Registro de las variables que importamos
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    return app

