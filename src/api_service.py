import requests

from config import TIMEOUT, TMDB_API_KEY, TMDB_BASE_URL, TMDB_IDIOMA, TMDB_REGION


class ErrorTMDB(Exception):
    """Error al consultar TMDB: falta la API Key o no hay conexión."""


def _get(ruta, params=None):
    if not TMDB_API_KEY:
        raise ErrorTMDB("Falta cargar la API Key en src/config.py.")

    query = {"api_key": TMDB_API_KEY, "language": TMDB_IDIOMA}
    if params:
        query.update(params)
    try:
        respuesta = requests.get(f"{TMDB_BASE_URL}{ruta}", params=query, timeout=TIMEOUT)
        respuesta.raise_for_status()
        return respuesta.json()
    except requests.RequestException as error:
        raise ErrorTMDB(f"No se pudo consultar TMDB: {error}") from error


def buscar_peliculas(query):
    """Coincidencias por título: id, title, release_date, genre_ids, poster_path, overview."""
    datos = _get("/search/movie", {"query": query, "include_adult": "false"})
    return datos.get("results", [])


def obtener_detalle_pelicula(tmdb_id):
    """Detalle con runtime, géneros y plataformas disponibles en Argentina (flatrate y free)."""
    datos = _get(f"/movie/{tmdb_id}", {"append_to_response": "watch/providers"})
    region = datos.get("watch/providers", {}).get("results", {}).get(TMDB_REGION, {})

    vistos = set()
    plataformas = []
    for tipo in ("flatrate", "free"):
        for proveedor in region.get(tipo, []):
            pid = proveedor["provider_id"]
            if pid not in vistos:
                vistos.add(pid)
                plataformas.append({
                    "provider_id": pid,
                    "provider_name": proveedor["provider_name"],
                    "logo_path": proveedor.get("logo_path"),
                })
    datos["plataformas_ar"] = plataformas
    return datos


def obtener_proveedores_argentina():
    """Lista oficial de plataformas disponibles en Argentina (para sincronizar la BD)."""
    datos = _get("/watch/providers/movie", {"watch_region": TMDB_REGION})
    return datos.get("results", [])


def descubrir_peliculas(genero_id=None, anio_desde=None, provider_ids=None, pagina=1):
    """Devuelve (resultados, total_paginas) de películas disponibles en Argentina."""
    params = {
        "watch_region": TMDB_REGION,
        "with_watch_monetization_types": "flatrate|free",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": pagina,
    }
    if genero_id:
        params["with_genres"] = str(genero_id)
    if anio_desde:
        params["primary_release_date.gte"] = f"{anio_desde}-01-01"
    if provider_ids:
        params["with_watch_providers"] = "|".join(map(str, provider_ids))

    datos = _get("/discover/movie", params)
    return datos.get("results", []), datos.get("total_pages", 0)
