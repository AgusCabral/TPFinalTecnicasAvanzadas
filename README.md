# TP Final

**Alumna:** Agustina Lujan Cabral

## Descripción

**LaPochoclera** funciona como un diario de películas, que permite registrar las películas que tenes pendientes y las que viste, con la fecha en que las viste, una calificación de 1 a 5 pochoclos, una nota personal y etiquetas según el contexto en que las viste y el mood que te transmitieron.
La información de cada película se busca en The Movie Database (TMDB), y la app muestra estadísticas sobre tu historial: cantidad de películas vistas, horas acumuladas, géneros favoritos, promedio de pochoclos de todas tus peliculas vistas y qué etiquetas tienen mejor promedio de pochoclos.
Además, incluye un recomendador, que sugiere una película a la vez según tus gustos o según filtros que elijas. Este apartado, tiene la opción de mostrar películas disponibles en las plataformas de streaming que tenés contratadas en Argentina, y permite guardarlas en pendientes o descartarlas, con memoria de descarte para no volver a verlas en la recomendación. Cada recomendación recibida te muestra también en qué plataformas podes encontrarla.

### Tecnologías y Base de Datos
* **Lenguaje e interfaz:** Python + Flet
* **Base de datos:** SQLite (`dbf/schema.sql`)
* **API externa:** TMDB API v3 (`es-AR`) para búsqueda de películas, pósters y disponibilidad por plataforma

## Ejecución
* **Ejecutable:** Abrir `dist/LaPochoclera.exe` (crea automáticamente `peliculas.db` al iniciar).
* **Código fuente:** Ejecutar `pip install -r requirements.txt` y luego `python src/main.py`.