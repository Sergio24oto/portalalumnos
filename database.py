import sqlite3
from flask import g
from werkzeug.security import generate_password_hash

DB_NAME = "portal.db"

def get_db():
    """
    Devuelve una conexión a la base SQLite guardada en 'g' (contexto de Flask),
    para reutilizarla durante la request.
    """
    if "db" not in g:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row  # permite acceder por nombre de columna
        g.db = conn
    return g.db

def close_db(e=None):
    """
    Cierra la conexión guardada en 'g' si existe.
    Flask llamará a esta función al terminar cada request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """
    Crea tablas si no existen y carga algunos datos de ejemplo.
    Ejecutala manualmente una vez (o cuando quieras reiniciar datos).
    """
    db = sqlite3.connect(DB_NAME)
    cur = db.cursor()

    # --- Tabla de materiales ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS materiales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            url TEXT NOT NULL
        );
    """)
    cur.execute("DELETE FROM materiales;")
    cur.executemany("""
        INSERT INTO materiales (titulo, tipo, url)
        VALUES (?, ?, ?);
    """, [
        ("Programa de la materia", "pdf", "http://www.africau.edu/images/default/sample.pdf"),
        ("Clase 1 - Presentación", "ppt", "http://www.africau.edu/images/default/sample.pdf"),
        ("Video: Introducción", "video", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ])

    # --- Tabla de anuncios ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS anuncios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("DELETE FROM anuncios;")
    cur.executemany("""
        INSERT INTO anuncios (titulo, contenido) VALUES (?, ?);
    """, [
        ("Bienvenida", "Arrancamos el portal de la materia 🎉"),
        ("Entrega", "La próxima semana deberán entregar el trabajo práctico 1."),
    ])

    # --- Tabla de usuarios ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL CHECK (rol IN ('admin','alumno')),
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # --- Progreso por usuario y material ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS progreso (
        user_id INTEGER NOT NULL,
        material_id INTEGER NOT NULL,
        estado INTEGER NOT NULL DEFAULT 0,   -- 0 = pendiente, 1 = completado
        PRIMARY KEY (user_id, material_id),
        FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES materiales(id) ON DELETE CASCADE
    );
""")


    # Crear usuario admin si no existe
    admin_user = cur.execute("SELECT id FROM usuarios WHERE username = ?", ("admin",)).fetchone()
    if not admin_user:
        pw_hash = generate_password_hash("admin123")  #contraseña
        cur.execute("""
            INSERT INTO usuarios (username, password_hash, rol)
            VALUES (?, ?, ?)
        """, ("admin", pw_hash, "admin"))

    db.commit()
    db.close()
