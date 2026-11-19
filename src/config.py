"""Configuración general: rutas, API Key de TMDB y colores de la aplicación."""
import sys
from pathlib import Path

# API Key de TMDB (v3). Se carga acá y la app la usa directamente.
TMDB_API_KEY = "0128c82f8d0bee5cd544f83c83e970b8"

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMG_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_IDIOMA = "es-AR"
TMDB_REGION = "AR"
TIMEOUT = 8
DIAS_DESCARTE = 60

# Rutas compatibles con desarrollo y con el ejecutable empaquetado (sys.frozen)
if getattr(sys, "frozen", False):
    RECURSOS_DIR = Path(sys._MEIPASS)
    DIRECTORIO_DATOS = Path(sys.executable).parent
else:
    RECURSOS_DIR = Path(__file__).resolve().parent.parent
    DIRECTORIO_DATOS = RECURSOS_DIR

SCHEMA_PATH = RECURSOS_DIR / "dbf" / "schema.sql"
DB_PATH = DIRECTORIO_DATOS / "peliculas.db"

COLOR_FONDO = "#0B0B0F"
COLOR_TARJETA = "#16161E"
COLOR_ROJO = "#E50914"
COLOR_DORADO = "#F5C518"