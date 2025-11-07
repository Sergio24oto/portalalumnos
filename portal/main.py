from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from database import get_db
#Decorador que creamos en el módulo de auth
from .auth import login_required

#Blueprint principal.
main_bp = Blueprint('main', __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/materiales")
def materiales():
    db = get_db()
    user_id = session.get("user_id")

    # La consulta SQL es más dificil y larga, usamos LEFT JOIN para unir tablas
    if user_id:
        filas = db.execute("""
            SELECT m.id, m.titulo, m.tipo, m.url,
                   COALESCE(p.estado, 0) AS completado
            FROM materiales m
            LEFT JOIN progreso p
              ON p.material_id = m.id AND p.user_id = ?
            ORDER BY m.id DESC
        """, (user_id,)).fetchall()
    else:
        filas = db.execute("""
            SELECT id, titulo, tipo, url, 0 AS completado
            FROM materiales
            ORDER BY id DESC
        """).fetchall()

    total = len(filas)
    hechos = sum(1 for f in filas if f["completado"] == 1)

    return render_template("materiales.html", materiales=filas, total=total, hechos=hechos)


@main_bp.route("/progreso/toggle/<int:mid>", methods=["POST"])
@login_required
def toggle_progreso(mid):
    user_id = g.user["id"]
    db = get_db()

    fila = db.execute(
        "SELECT estado FROM progreso WHERE user_id = ? AND material_id = ?",
        (user_id, mid)
    ).fetchone()

    if fila is None:
        db.execute(
            "INSERT INTO progreso (user_id, material_id, estado) VALUES (?, ?, 1)",
            (user_id, mid)
        )
        flash("Marcado como completado ✔️")
    else:
        nuevo = 0 if fila["estado"] == 1 else 1
        db.execute(
            "UPDATE progreso SET estado = ? WHERE user_id = ? AND material_id = ?",
            (nuevo, user_id, mid)
        )
        flash("Estado de progreso actualizado.")

    db.commit()
    return redirect(url_for("main.materiales"))


@main_bp.route("/anuncios")
def anuncios():
    db = get_db()
    filas = db.execute(
        "SELECT id, titulo, contenido, fecha FROM anuncios ORDER BY id DESC"
    ).fetchall()
    return render_template("anuncios.html", anuncios=filas)

