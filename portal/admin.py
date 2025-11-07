import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, current_app
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from database import get_db

from .auth import admin_required

# /admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# Ayuda para archivos ---
def allowed_file(filename: str) -> bool:
    ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx"}
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

#  Rutas para el Admin: Progreso 

@admin_bp.route("/progreso")
@admin_required
def progreso_resumen():
    db = get_db()
    total_mat = db.execute("SELECT COUNT(*) AS c FROM materiales").fetchone()["c"]
    filas = db.execute("""
        SELECT u.id AS user_id, u.username, u.rol,
               COALESCE(SUM(CASE WHEN p.estado = 1 THEN 1 ELSE 0 END), 0) AS completados
        FROM usuarios u
        LEFT JOIN progreso p ON p.user_id = u.id
        GROUP BY u.id, u.username, u.rol
        ORDER BY u.rol DESC, u.username ASC
    """).fetchall()
    return render_template("admin_progreso_resumen.html", usuarios=filas, total_mat=total_mat)


@admin_bp.route("/progreso/usuario/<int:uid>")
@admin_required
def progreso_detalle(uid):
    db = get_db()
    usuario = db.execute("SELECT id, username, rol FROM usuarios WHERE id = ?", (uid,)).fetchone()
    if not usuario:
        flash("Usuario no encontrado.")
        return redirect(url_for("admin.progreso_resumen"))

    materiales = db.execute("""
        SELECT m.id, m.titulo, m.tipo, m.url, COALESCE(p.estado, 0) AS completado
        FROM materiales m
        LEFT JOIN progreso p ON p.material_id = m.id AND p.user_id = ?
        ORDER BY m.id DESC
    """, (uid,)).fetchall()

    total = len(materiales)
    hechos = sum(1 for f in materiales if f["completado"] == 1)

    return render_template("admin_progreso_detalle.html",
                           usuario=usuario, materiales=materiales,
                           total=total, hechos=hechos)

# Ruta del Admin: Materiales

@admin_bp.route("/materiales/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_material():
    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        tipo = (request.form.get("tipo") or "").strip()
        fuente = (request.form.get("fuente") or "archivo").strip()
        url = (request.form.get("url") or "").strip()
        errores = []

        if not titulo: errores.append("El título es obligatorio.")
        if tipo not in ("pdf", "ppt", "video"): errores.append("Tipo inválido.")

        archivo_subido = None
        if fuente == "archivo":
            if tipo == "video":
                errores.append("Los videos deben cargarse por URL.")
            else:
                archivo_subido = request.files.get("archivo")
                if not archivo_subido or archivo_subido.filename == "":
                    errores.append("Selecciona un archivo para subir.")
                elif not allowed_file(archivo_subido.filename):
                    errores.append("Extensión no permitida.")
        else:
            if not url: errores.append("La URL es obligatoria.")

        if errores:
            for e in errores: flash(e)
            return render_template("admin_nuevo_material.html", form={"titulo": titulo, "tipo": tipo, "url": url, "fuente": fuente})

        final_url = url
        if fuente == "archivo" and archivo_subido:
            nombre_seguro = secure_filename(archivo_subido.filename)
            nombre_final = f"{uuid.uuid4().hex}_{nombre_seguro}"
            # Usamos current_app para acceder a la configuración de la app desde un blueprint
            ruta_destino = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_final)
            archivo_subido.save(ruta_destino)
            final_url = f"/static/uploads/{nombre_final}"

        db = get_db()
        db.execute("INSERT INTO materiales (titulo, tipo, url) VALUES (?, ?, ?)", (titulo, tipo, final_url))
        db.commit()
        flash("Material creado correctamente.")
        return redirect(url_for("main.materiales"))

    return render_template("admin_nuevo_material.html", form={"titulo": "", "tipo": "pdf", "url": "", "fuente": "archivo"})


@admin_bp.route("/materiales/eliminar/<int:mid>", methods=["POST"])
@admin_required
def eliminar_material(mid):
    db = get_db()
    db.execute("DELETE FROM materiales WHERE id = ?", (mid,))
    db.commit()
    flash("Material eliminado.")
    return redirect(url_for("main.materiales"))


#Ruta del Admin: Anuncios 

@admin_bp.route("/anuncios/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_anuncio():
    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        contenido = (request.form.get("contenido") or "").strip()

        if not titulo or not contenido:
            flash("Título y contenido son obligatorios.")
            return render_template("admin_nuevo_anuncio.html", form={"titulo": titulo, "contenido": contenido})

        db = get_db()
        db.execute("INSERT INTO anuncios (titulo, contenido) VALUES (?, ?)", (titulo, contenido))
        db.commit()
        flash("Anuncio creado correctamente.")
        return redirect(url_for("main.anuncios"))

    return render_template("admin_nuevo_anuncio.html", form={"titulo": "", "contenido": ""})


@admin_bp.route("/anuncios/eliminar/<int:aid>", methods=["POST"])
@admin_required
def eliminar_anuncio(aid):
    db = get_db()
    db.execute("DELETE FROM anuncios WHERE id = ?", (aid,))
    db.commit()
    flash("Anuncio eliminado.")
    return redirect(url_for("main.anuncios"))


# --- Ruta del Admin: Usuarios

@admin_bp.route("/usuarios/nuevo", methods=["GET", "POST"])
@admin_required
def nuevo_usuario():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        rol = (request.form.get("rol") or "alumno").strip()
        errores = []

        if len(username) < 3: errores.append("El usuario debe tener al menos 3 caracteres.")
        if len(password) < 6: errores.append("La contraseña debe tener al menos 6 caracteres.")
        if rol not in ("admin", "alumno"): errores.append("Rol inválido.")

        if errores:
            for e in errores: flash(e)
            return render_template("admin_nuevo_usuario.html", form={"username": username, "rol": rol})

        db = get_db()
        ya = db.execute("SELECT id FROM usuarios WHERE LOWER(username)=?", (username,)).fetchone()
        if ya:
            flash("Ese nombre de usuario ya existe.")
            return render_template("admin_nuevo_usuario.html", form={"username": username, "rol": rol})

        pw_hash = generate_password_hash(password)
        db.execute("INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)", (username, pw_hash, rol))
        db.commit()

        flash(f"Usuario '{username}' creado correctamente.")
        return redirect(url_for("main.home"))

    return render_template("admin_nuevo_usuario.html", form={"username": "", "rol": "alumno"})

