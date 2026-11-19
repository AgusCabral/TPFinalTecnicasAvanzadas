"""Acceso a SQLite: conexión, CRUD, métricas (GROUP BY) y memoria de descartes."""
import sqlite3
import time

from config import DB_PATH, SCHEMA_PATH


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _consulta(sql, params=()):
    con = conectar()
    try:
        return [dict(fila) for fila in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def _ejecutar(sql, params=()):
    con = conectar()
    try:
        cursor = con.execute(sql, params)
        con.commit()
        return cursor.lastrowid
    finally:
        con.close()


def inicializar_bd():
    """Si la base no existe, crea las tablas y los datos iniciales desde schema.sql."""
    if DB_PATH.exists():
        return
    con = conectar()
    try:
        con.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    finally:
        con.close()


def id_manual():
    """ID negativo único para películas cargadas sin TMDB."""
    return -int(time.time() * 1000)


# ---------- Catálogos ----------

def generos():
    return _consulta("SELECT id_genero, nombre FROM generos ORDER BY nombre")


def etiquetas():
    return _consulta("SELECT id_etiqueta, nombre, tipo FROM etiquetas ORDER BY tipo, nombre")


def etiquetas_de_pelicula(id_pelicula):
    return _consulta(
        """SELECT e.id_etiqueta, e.nombre, e.tipo
           FROM etiquetas e
           JOIN pelicula_etiquetas pe ON pe.id_etiqueta = e.id_etiqueta
           WHERE pe.id_pelicula = ?
           ORDER BY e.nombre""",
        (id_pelicula,),
    )


# ---------- CRUD de películas ----------

def guardar_pelicula(datos, id_pelicula=None):
    """Inserta (id_pelicula=None) o actualiza una película y sus etiquetas."""
    datos = dict(datos)
    etiquetas_ids = datos.pop("etiquetas", [])
    con = conectar()
    try:
        if id_pelicula is None:
            cursor = con.execute(
                """INSERT INTO peliculas
                   (tmdb_id, titulo, anio, duracion_min, poster_path, estado,
                    puntaje, nota_diario, fecha_vista, id_genero)
                   VALUES (:tmdb_id, :titulo, :anio, :duracion_min, :poster_path, :estado,
                           :puntaje, :nota_diario, :fecha_vista, :id_genero)""",
                datos,
            )
            id_pelicula = cursor.lastrowid
        else:
            con.execute(
                """UPDATE peliculas SET
                       titulo = :titulo, anio = :anio, duracion_min = :duracion_min,
                       poster_path = :poster_path, estado = :estado, puntaje = :puntaje,
                       nota_diario = :nota_diario, fecha_vista = :fecha_vista,
                       id_genero = :id_genero
                   WHERE id_pelicula = :id""",
                {**datos, "id": id_pelicula},
            )
        con.execute("DELETE FROM pelicula_etiquetas WHERE id_pelicula = ?", (id_pelicula,))
        con.executemany(
            "INSERT INTO pelicula_etiquetas (id_pelicula, id_etiqueta) VALUES (?, ?)",
            [(id_pelicula, eid) for eid in etiquetas_ids],
        )
        con.commit()
        return id_pelicula
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def eliminar_pelicula(id_pelicula):
    _ejecutar("DELETE FROM peliculas WHERE id_pelicula = ?", (id_pelicula,))


def obtener_pelicula(id_pelicula):
    filas = _consulta("SELECT * FROM peliculas WHERE id_pelicula = ?", (id_pelicula,))
    if not filas:
        return None
    pelicula = filas[0]
    pelicula["etiquetas"] = [
        f["id_etiqueta"]
        for f in _consulta(
            "SELECT id_etiqueta FROM pelicula_etiquetas WHERE id_pelicula = ?", (id_pelicula,)
        )
    ]
    return pelicula


def listar_peliculas(estado="todas", id_genero=None, texto=""):
    sql = """SELECT p.*, g.nombre AS nombre_genero
             FROM peliculas p
             JOIN generos g ON g.id_genero = p.id_genero
             WHERE 1 = 1"""
    params = []
    if estado in ("vista", "pendiente"):
        sql += " AND p.estado = ?"
        params.append(estado)
    if id_genero:
        sql += " AND p.id_genero = ?"
        params.append(id_genero)
    if texto:
        sql += " AND p.titulo LIKE ?"
        params.append(f"%{texto}%")
    sql += " ORDER BY p.fecha_vista DESC, p.id_pelicula DESC"
    return _consulta(sql, params)


def pendientes_con_etiqueta(id_etiqueta):
    return _consulta(
        """SELECT p.id_pelicula, p.tmdb_id, p.titulo
           FROM peliculas p
           JOIN pelicula_etiquetas pe ON pe.id_pelicula = p.id_pelicula
           WHERE p.estado = 'pendiente' AND pe.id_etiqueta = ?""",
        (id_etiqueta,),
    )


# ---------- Suscripciones / plataformas ----------

def suscripciones():
    return _consulta(
        "SELECT provider_id, nombre, logo_path, activa FROM suscripciones_usuario "
        "ORDER BY activa DESC, nombre"
    )


def set_suscripcion(provider_id, activa):
    _ejecutar(
        "UPDATE suscripciones_usuario SET activa = ? WHERE provider_id = ?",
        (int(bool(activa)), provider_id),
    )


def activas_ids():
    filas = _consulta("SELECT provider_id FROM suscripciones_usuario WHERE activa = 1")
    return [f["provider_id"] for f in filas]


def sincronizar_proveedores(proveedores):
    """Inserta o actualiza nombre y logo sin pisar el campo 'activa' del usuario."""
    con = conectar()
    try:
        for p in proveedores:
            con.execute(
                """INSERT INTO suscripciones_usuario (provider_id, nombre, logo_path, activa)
                   VALUES (?, ?, ?, 0)
                   ON CONFLICT(provider_id) DO UPDATE SET
                       nombre = excluded.nombre,
                       logo_path = excluded.logo_path""",
                (p["provider_id"], p["provider_name"], p.get("logo_path")),
            )
        con.commit()
    finally:
        con.close()


# ---------- Descartes y exclusiones del recomendador ----------

def descartar(tmdb_id, motivo=None):
    _ejecutar(
        """INSERT OR REPLACE INTO peliculas_descartadas (tmdb_id, fecha_descarte, motivo)
           VALUES (?, DATE('now'), ?)""",
        (tmdb_id, motivo),
    )


def ids_excluidos(dias):
    """TMDB IDs del diario (vista o pendiente) y descartes de los últimos N días."""
    filas = _consulta(
        """SELECT tmdb_id FROM peliculas
           UNION
           SELECT tmdb_id FROM peliculas_descartadas
           WHERE fecha_descarte >= DATE('now', ?)""",
        (f"-{dias} days",),
    )
    return {f["tmdb_id"] for f in filas}


def genero_favorito_id():
    """Género con más películas vistas; en caso de empate, el de mejor promedio."""
    filas = _consulta(
        """SELECT id_genero FROM peliculas
           WHERE estado = 'vista'
           GROUP BY id_genero
           ORDER BY COUNT(*) DESC, AVG(puntaje) DESC
           LIMIT 1"""
    )
    return filas[0]["id_genero"] if filas else None


# ---------- Métricas ----------

def kpis():
    filas = _consulta(
        """SELECT
               COALESCE(SUM(CASE WHEN estado = 'vista' THEN 1 ELSE 0 END), 0) AS vistas,
               COALESCE(SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END), 0) AS pendientes,
               COALESCE(SUM(CASE WHEN estado = 'vista' THEN duracion_min ELSE 0 END), 0) / 60.0 AS horas,
               AVG(CASE WHEN estado = 'vista' THEN puntaje END) AS promedio
           FROM peliculas"""
    )
    return filas[0]


def ranking_generos():
    return _consulta(
        """SELECT g.nombre, COUNT(p.id_pelicula) AS cantidad, AVG(p.puntaje) AS promedio
           FROM peliculas p
           JOIN generos g ON g.id_genero = p.id_genero
           WHERE p.estado = 'vista'
           GROUP BY g.id_genero
           ORDER BY cantidad DESC, promedio DESC"""
    )


def ranking_etiquetas():
    return _consulta(
        """SELECT e.nombre, e.tipo, COUNT(p.id_pelicula) AS cantidad, AVG(p.puntaje) AS promedio
           FROM etiquetas e
           JOIN pelicula_etiquetas pe ON pe.id_etiqueta = e.id_etiqueta
           JOIN peliculas p ON p.id_pelicula = pe.id_pelicula
           WHERE p.estado = 'vista'
           GROUP BY e.id_etiqueta
           ORDER BY promedio DESC, cantidad DESC"""
    )
