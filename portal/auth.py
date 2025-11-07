from functools import wraps
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash
from database import get_db

# /auth
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


#Decoradores de protección 

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Necesitas iniciar sesión para acceder a esta página.")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if g.user is None:
            flash("Necesitas iniciar sesión.")
            return redirect(url_for("auth.login", next=request.path))
        if g.user["rol"] != "admin":
            flash("No tenés permisos de administrador para acceder a esta sección.")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return wrapper


#Rutas de Autenticación

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for('main.home'))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM usuarios WHERE LOWER(username) = ?", (username,)
        ).fetchone()

        if user is None:
            error = "Usuario incorrecto."
        elif not check_password_hash(user["password_hash"], password):
            error = "Contraseña incorrecta."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Bienvenido de nuevo, {user['username']} 👋")
            next_url = request.args.get("next") or url_for("main.home")
            return redirect(next_url)
        
        flash(error)

    return render_template("auth_login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.")
    return redirect(url_for("main.home"))

