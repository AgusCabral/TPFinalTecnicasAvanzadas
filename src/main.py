"""Interfaz gráfica en Flet."""
import sqlite3
from datetime import date, datetime

import flet as ft

import api_service as api
import database as db
from config import (
    COLOR_DORADO,
    COLOR_FONDO,
    COLOR_ROJO,
    COLOR_TARJETA,
    DIAS_DESCARTE,
    TMDB_API_KEY,
    TMDB_IMG_BASE,
)

COLOR_BORDE = "#6B5A1E"
COLOR_TEXTO_SUAVE = "#B8B8C4"
COLOR_FICHA = "#2A2A35"
COLOR_PENDIENTE = "#C2410C"


# ---------- Utilidades de interfaz ----------

def mostrar_snack(page, texto, color=COLOR_TARJETA):
    barra = ft.SnackBar(content=ft.Text(texto), bgcolor=color)
    page.overlay.append(barra)
    barra.open = True
    page.update()


def abrir_dialogo(page, dialogo):
    page.overlay.append(dialogo)
    dialogo.open = True
    page.update()


def cerrar_dialogo(page, dialogo):
    dialogo.open = False
    page.update()


def texto_pochoclos(puntaje):
    if not puntaje:
        return "Sin calificar"
    return f"{'🍿' * int(puntaje)}  ({puntaje}/5)"


def texto_promedio(promedio):
    return f"{promedio:.1f} 🍿" if promedio else "Sin datos"


def vacio(texto):
    return ft.Container(
        padding=20,
        content=ft.Text(texto, color=COLOR_TEXTO_SUAVE, text_align=ft.TextAlign.CENTER),
    )


def poster(ruta, ancho=90, alto=135):
    if ruta:
        return ft.Image(
            src=f"{TMDB_IMG_BASE}{ruta}",
            width=ancho,
            height=alto,
            fit=ft.BoxFit.COVER,
            border_radius=8,
        )
    return ft.Container(
        width=ancho,
        height=alto,
        border_radius=8,
        bgcolor=COLOR_TARJETA,
        border=ft.border.all(1, COLOR_DORADO),
        alignment=ft.alignment.center,
        content=ft.Icon(ft.Icons.MOVIE_OUTLINED, color=COLOR_DORADO, size=ancho // 3),
    )


def caja_ticket(contenido, ancho=None):
    return ft.Container(
        width=ancho,
        padding=16,
        bgcolor=COLOR_TARJETA,
        border=ft.border.all(1, COLOR_DORADO),
        border_radius=12,
        content=contenido,
    )


def chip_etiqueta(nombre, tipo):
    return ft.Container(
        content=ft.Text(nombre, size=11),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
        border_radius=12,
        bgcolor=COLOR_FICHA if tipo == "mood" else "#1E3A3A",
    )


def chip_seleccionable(etiqueta, seleccion, al_cambiar):
    """Chip que agrega o quita su id del conjunto 'seleccion' al tocarlo."""
    eid = etiqueta["id_etiqueta"]
    contenedor = ft.Container(
        content=ft.Text(etiqueta["nombre"], size=12),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=20,
        border=ft.border.all(1, COLOR_DORADO),
    )

    def pintar():
        activo = eid in seleccion
        contenedor.bgcolor = COLOR_ROJO if activo else None
        contenedor.content.color = "#FFFFFF" if activo else COLOR_DORADO

    def clic(_):
        if eid in seleccion:
            seleccion.remove(eid)
        else:
            seleccion.add(eid)
        pintar()
        al_cambiar()

    contenedor.on_click = clic
    pintar()
    return contenedor


class SelectorPochoclos(ft.Column):
    """Selector de 1 a 5 pochoclos. Los activos se ven con brillo; el resto, apagados."""

    def __init__(self, valor=None, habilitado=True):
        super().__init__(spacing=2)
        self.valor = valor or 0
        self.habilitado = habilitado
        self.fila = ft.Row(spacing=0)
        self.leyenda = ft.Text(size=12, color=COLOR_TEXTO_SUAVE)
        self.controls = [self.fila, self.leyenda]
        self.opacity = 1.0 if habilitado else 0.4
        self._pintar()

    def _pintar(self):
        self.fila.controls = [
            ft.Container(
                content=ft.Text("🍿", size=30),
                opacity=1.0 if n <= self.valor else 0.2,
                padding=2,
                on_click=(lambda _, n=n: self._elegir(n)),
            )
            for n in range(1, 6)
        ]
        self.leyenda.value = f"{self.valor} de 5 pochoclos" if self.valor else "Sin calificar"

    def _elegir(self, n):
        if not self.habilitado:
            return
        self.valor = n
        self._pintar()
        if self.page:
            self.page.update()

    def set_habilitado(self, habilitado):
        self.habilitado = habilitado
        self.opacity = 1.0 if habilitado else 0.4


# ---------- Aplicación ----------

class AplicacionCine:
    def __init__(self, page: ft.Page):
        self.page = page
        self.generos = db.generos()
        self.nombres_genero = {g["id_genero"]: g["nombre"] for g in self.generos}
        self.etiquetas = db.etiquetas()
        self.nombres_etiqueta = {e["id_etiqueta"]: e["nombre"] for e in self.etiquetas}
        self.generos_validos = set(self.nombres_genero)

        self.filtro_estado = "todas"
        self.filtro_genero = None
        self.filtro_texto = ""
        self.seccion = 0
        self.contenido = ft.Container(expand=True, padding=16)

        self.lista_diario = None
        self.rec_modo = None
        self.rec_genero = None
        self.rec_mood = None
        self.rec_anio = None
        self.rec_filtros = None
        self.rec_subs = None
        self.rec_carta = None

        self.cola = []
        self.excluidos = set()
        self.pagina = 1
        self.paginas_totales = 5
        self.criterio = {}
        self.carta = None

    def id_genero_compatible(self, ids_tmdb):
        for gid in ids_tmdb or []:
            if gid in self.generos_validos:
                return gid
        return 18  # Drama, como respaldo para géneros que no están en la tabla

    # ----- Navegación -----

    def construir(self):
        self.nav = ft.NavigationBar(
            selected_index=0,
            bgcolor=COLOR_TARJETA,
            indicator_color=COLOR_ROJO,
            on_change=self.cambiar_seccion,
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.MOVIE_OUTLINED, selected_icon=ft.Icons.MOVIE, label="Diario"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.CONFIRMATION_NUMBER_OUTLINED,
                    selected_icon=ft.Icons.CONFIRMATION_NUMBER,
                    label="Recomendador",
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.BAR_CHART_OUTLINED, selected_icon=ft.Icons.BAR_CHART, label="Métricas"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.SETTINGS_OUTLINED, selected_icon=ft.Icons.SETTINGS, label="Plataformas"
                ),
            ],
        )

        encabezado = ft.Container(
            padding=ft.padding.symmetric(horizontal=20, vertical=14),
            bgcolor=COLOR_TARJETA,
            border=ft.border.only(bottom=ft.BorderSide(2, COLOR_DORADO)),
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.THEATERS, color=COLOR_ROJO, size=34),
                    ft.Column(
                        [
                            ft.Text(
                                "DIARIO DE PELÍCULAS VISTAS",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=COLOR_DORADO,
                                letter_spacing=2,
                            ),
                            ft.Text(
                                "Cartelera personal · Función continua",
                                size=12,
                                italic=True,
                                color=COLOR_TEXTO_SUAVE,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.LOCAL_MOVIES, color=COLOR_DORADO, size=30),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        )

        self.mostrar_seccion(0)
        return ft.Column([encabezado, self.contenido, self.nav], expand=True, spacing=0)

    def cambiar_seccion(self, e):
        self.mostrar_seccion(e.control.selected_index)

    def mostrar_seccion(self, indice):
        self.seccion = indice
        constructores = [
            self.seccion_diario,
            self.seccion_recomendador,
            self.seccion_metricas,
            self.seccion_plataformas,
        ]
        self.contenido.content = constructores[indice]()
        self.page.update()

    # ----- Sección 1: Diario y pendientes -----

    def seccion_diario(self):
        page = self.page

        def al_cambiar(_=None):
            self.filtro_texto = buscador.value or ""
            self.filtro_estado = filtro_estado.value
            self.filtro_genero = None if filtro_genero.value == "todos" else int(filtro_genero.value)
            self.cargar_diario()
            page.update()

        buscador = ft.TextField(
            label="Buscar por título",
            value=self.filtro_texto,
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=al_cambiar,
        )
        filtro_estado = ft.Dropdown(
            label="Estado",
            width=190,
            value=self.filtro_estado,
            options=[
                ft.dropdown.Option(key="todas", text="Todas"),
                ft.dropdown.Option(key="vista", text="Vistas"),
                ft.dropdown.Option(key="pendiente", text="Pendientes"),
            ],
            on_change=al_cambiar,
        )
        filtro_genero = ft.Dropdown(
            label="Género",
            width=220,
            value=str(self.filtro_genero) if self.filtro_genero else "todos",
            options=[ft.dropdown.Option(key="todos", text="Todos los géneros")]
            + [ft.dropdown.Option(key=str(g["id_genero"]), text=g["nombre"]) for g in self.generos],
            on_change=al_cambiar,
        )

        self.lista_diario = ft.Column(spacing=12)
        self.cargar_diario()

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Mi Diario y Pendientes", size=22, weight=ft.FontWeight.BOLD,
                                color=COLOR_DORADO, expand=True),
                        ft.ElevatedButton(
                            "Nueva función",
                            icon=ft.Icons.ADD,
                            bgcolor=COLOR_ROJO,
                            color="#FFFFFF",
                            on_click=lambda _: self.abrir_formulario(),
                        ),
                    ]
                ),
                ft.Row([buscador]),
                ft.Row([filtro_estado, filtro_genero], wrap=True, spacing=10),
                self.lista_diario,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=14,
        )

    def cargar_diario(self):
        peliculas = db.listar_peliculas(self.filtro_estado, self.filtro_genero, self.filtro_texto)
        self.lista_diario.controls = [self.tarjeta_pelicula(p) for p in peliculas] or [
            vacio("Todavía no hay funciones acá. ¡Cargá la primera!")
        ]

    def tarjeta_pelicula(self, p):
        vista = p["estado"] == "vista"
        badge = ft.Container(
            content=ft.Text(
                "FUNCIÓN VISTA" if vista else "EN CARTELERA (PENDIENTE)",
                size=11,
                weight=ft.FontWeight.BOLD,
                color="#0B0B0F" if vista else "#FFFFFF",
            ),
            bgcolor=COLOR_DORADO if vista else COLOR_PENDIENTE,
            padding=ft.padding.symmetric(horizontal=8, vertical=3),
            border_radius=4,
        )
        chips = ft.Row(
            [chip_etiqueta(e["nombre"], e["tipo"]) for e in db.etiquetas_de_pelicula(p["id_pelicula"])],
            wrap=True,
            spacing=4,
            run_spacing=4,
        )
        datos = [
            str(p["anio"]) if p["anio"] else "",
            f"{p['duracion_min']} min" if p["duracion_min"] else "",
            p["nombre_genero"],
        ]
        nota = p["nota_diario"] or ""
        extracto = nota[:110] + "…" if len(nota) > 110 else nota

        info = ft.Column(
            [
                ft.Text(p["titulo"], size=18, weight=ft.FontWeight.BOLD),
                badge,
                ft.Text("  ·  ".join(d for d in datos if d), size=12, color=COLOR_TEXTO_SUAVE),
                ft.Text(texto_pochoclos(p["puntaje"]) if vista else "Aún sin pochoclos", size=14),
                ft.Text(f"Vista el {p['fecha_vista']}" if vista and p["fecha_vista"] else "", size=12),
                chips,
                ft.Text(f"“{extracto}”", italic=True, size=12) if extracto else ft.Container(),
                ft.Row(
                    [
                        ft.TextButton(
                            "Editar",
                            icon=ft.Icons.EDIT,
                            on_click=lambda _, pid=p["id_pelicula"]: self.editar(pid),
                        ),
                        ft.TextButton(
                            "Eliminar",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=lambda _, pel=p: self.confirmar_eliminar(pel),
                        ),
                    ]
                ),
            ],
            spacing=6,
            expand=True,
        )
        return ft.Container(
            padding=12,
            bgcolor=COLOR_TARJETA,
            border=ft.border.all(1, COLOR_BORDE),
            border_radius=12,
            content=ft.Row(
                [poster(p["poster_path"]), info],
                vertical_alignment=ft.CrossAxisAlignment.START,
                spacing=14,
            ),
        )

    def editar(self, id_pelicula):
        self.abrir_formulario(pelicula=db.obtener_pelicula(id_pelicula))

    def confirmar_eliminar(self, pelicula):
        page = self.page

        def eliminar(_):
            db.eliminar_pelicula(pelicula["id_pelicula"])
            cerrar_dialogo(page, dialogo)
            mostrar_snack(page, "Función eliminada de tu diario.")
            self.mostrar_seccion(self.seccion)

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=COLOR_TARJETA,
            title=ft.Text("¿Eliminar del diario?"),
            content=ft.Text(f"Se va a borrar “{pelicula['titulo']}”. Esta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar_dialogo(page, dialogo)),
                ft.ElevatedButton("Eliminar", bgcolor=COLOR_ROJO, color="#FFFFFF", on_click=eliminar),
            ],
        )
        abrir_dialogo(page, dialogo)

    def abrir_formulario(self, pelicula=None, precarga=None, al_guardar=None):
        """Modal de alta/edición. 'precarga' llena el formulario desde el recomendador."""
        page = self.page
        base = pelicula or precarga or {}
        editando = pelicula is not None
        estado_inicial = base.get("estado") or "vista"
        st = {"tmdb_id": base.get("tmdb_id"), "poster": base.get("poster_path")}
        seleccion = set(base.get("etiquetas", []))

        f_busqueda = ft.TextField(
            label="Buscar película en TMDB",
            expand=True,
            on_submit=lambda _: buscar(),
        )
        resultados = ft.Column(spacing=4)
        f_titulo = ft.TextField(label="Título", value=base.get("titulo", ""))
        f_anio = ft.TextField(
            label="Año", width=110, value=str(base.get("anio") or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        f_duracion = ft.TextField(
            label="Duración (min)", width=150, value=str(base.get("duracion_min") or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        f_genero = ft.Dropdown(
            label="Género",
            expand=True,
            value=str(base.get("id_genero") or 18),
            options=[ft.dropdown.Option(key=str(g["id_genero"]), text=g["nombre"]) for g in self.generos],
        )
        f_estado = ft.Dropdown(
            label="Estado",
            expand=True,
            value=estado_inicial,
            options=[
                ft.dropdown.Option(key="vista", text="Vista"),
                ft.dropdown.Option(key="pendiente", text="Pendiente"),
            ],
        )
        f_fecha = ft.TextField(
            label="Fecha en que se vio (AAAA-MM-DD)",
            value=base.get("fecha_vista") or date.today().isoformat(),
        )
        selector = SelectorPochoclos(valor=base.get("puntaje"), habilitado=estado_inicial == "vista")
        f_nota = ft.TextField(
            label="Nota personal (tu diario íntimo)",
            multiline=True,
            min_lines=3,
            max_lines=6,
            value=base.get("nota_diario") or "",
        )
        slot_poster = ft.Container(content=poster(st["poster"], 100, 150))

        def cambio_estado(_):
            selector.set_habilitado(f_estado.value == "vista")
            page.update()

        f_estado.on_change = cambio_estado

        def fila_resultado(r):
            anio = (r.get("release_date") or "")[:4]
            return ft.Container(
                padding=6,
                border_radius=8,
                on_click=lambda _, r=r: elegir(r),
                content=ft.Row(
                    [
                        poster(r.get("poster_path"), 40, 60),
                        ft.Column(
                            [
                                ft.Text(r.get("title", ""), weight=ft.FontWeight.BOLD),
                                ft.Text(anio or "Año desconocido", size=12, color=COLOR_TEXTO_SUAVE),
                            ],
                            spacing=2,
                        ),
                    ]
                ),
            )

        def buscar():
            consulta = (f_busqueda.value or "").strip()
            if not consulta:
                return
            try:
                encontradas = api.buscar_peliculas(consulta)
            except api.ErrorTMDB as error:
                mostrar_snack(page, str(error), COLOR_ROJO)
                return
            resultados.controls = [fila_resultado(r) for r in encontradas[:8]] or [
                ft.Text("Sin coincidencias.", color=COLOR_TEXTO_SUAVE)
            ]
            page.update()

        def elegir(r):
            detalle = r
            try:
                detalle = api.obtener_detalle_pelicula(r["id"])
            except api.ErrorTMDB as error:
                mostrar_snack(page, f"Sin detalle extendido: {error}", COLOR_ROJO)
            st["tmdb_id"] = r["id"]
            st["poster"] = detalle.get("poster_path") or r.get("poster_path")
            f_titulo.value = detalle.get("title") or r.get("title", "")
            f_anio.value = (detalle.get("release_date") or r.get("release_date") or "")[:4]
            f_duracion.value = str(detalle.get("runtime") or "")
            ids = [g["id"] for g in detalle.get("genres", [])] or r.get("genre_ids", [])
            f_genero.value = str(self.id_genero_compatible(ids))
            slot_poster.content = poster(st["poster"], 100, 150)
            resultados.controls = []
            page.update()

        def guardar(_):
            titulo = (f_titulo.value or "").strip()
            if not titulo:
                mostrar_snack(page, "Falta el título de la película.", COLOR_ROJO)
                return
            try:
                anio = int(f_anio.value) if (f_anio.value or "").strip() else None
                duracion = int(f_duracion.value) if (f_duracion.value or "").strip() else None
            except ValueError:
                mostrar_snack(page, "Año y duración deben ser números.", COLOR_ROJO)
                return

            es_vista = f_estado.value == "vista"
            fecha = None
            if es_vista:
                try:
                    fecha = datetime.strptime((f_fecha.value or "").strip(), "%Y-%m-%d").date().isoformat()
                except ValueError:
                    mostrar_snack(page, "La fecha debe tener el formato AAAA-MM-DD.", COLOR_ROJO)
                    return

            datos = {
                "tmdb_id": st["tmdb_id"] if st["tmdb_id"] is not None else db.id_manual(),
                "titulo": titulo,
                "anio": anio,
                "duracion_min": duracion,
                "poster_path": st["poster"],
                "estado": f_estado.value,
                "puntaje": selector.valor if es_vista and selector.valor else None,
                "nota_diario": (f_nota.value or "").strip() or None,
                "fecha_vista": fecha,
                "id_genero": int(f_genero.value),
                "etiquetas": list(seleccion),
            }
            try:
                db.guardar_pelicula(datos, id_pelicula=pelicula["id_pelicula"] if editando else None)
            except sqlite3.IntegrityError:
                mostrar_snack(page, "No se pudo guardar: la película ya existe o hay datos inválidos.", COLOR_ROJO)
                return

            cerrar_dialogo(page, dialogo)
            mostrar_snack(page, "Función guardada en tu diario 🍿")
            if al_guardar:
                al_guardar()
            else:
                self.mostrar_seccion(self.seccion)

        chips_contexto = ft.Row(
            [chip_seleccionable(e, seleccion, page.update) for e in self.etiquetas if e["tipo"] == "contexto"],
            wrap=True, spacing=8, run_spacing=8,
        )
        chips_mood = ft.Row(
            [chip_seleccionable(e, seleccion, page.update) for e in self.etiquetas if e["tipo"] == "mood"],
            wrap=True, spacing=8, run_spacing=8,
        )

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=COLOR_TARJETA,
            title=ft.Text("Editar función" if editando else "Nueva función", color=COLOR_DORADO),
            content=ft.Container(
                width=540,
                height=560,
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                f_busqueda,
                                ft.ElevatedButton(
                                    "Buscar en TMDB",
                                    bgcolor=COLOR_ROJO,
                                    color="#FFFFFF",
                                    on_click=lambda _: buscar(),
                                ),
                            ]
                        ),
                        resultados,
                        ft.Row(
                            [slot_poster, ft.Column([f_titulo, ft.Row([f_anio, f_duracion])], expand=True)],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                        ),
                        ft.Row([f_genero, f_estado]),
                        f_fecha,
                        ft.Text("Puntuación", weight=ft.FontWeight.BOLD),
                        selector,
                        f_nota,
                        ft.Text("Contexto", weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                        chips_contexto,
                        ft.Text("Mood", weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                        chips_mood,
                    ],
                    scroll=ft.ScrollMode.AUTO,
                    spacing=10,
                ),
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _: cerrar_dialogo(page, dialogo)),
                ft.ElevatedButton("Guardar", bgcolor=COLOR_ROJO, color="#FFFFFF", on_click=guardar),
            ],
        )
        abrir_dialogo(page, dialogo)

    # ----- Sección 2: Recomendador "Una sola carta" -----

    def seccion_recomendador(self):
        page = self.page

        def cambio_modo(_):
            self.rec_filtros.visible = self.rec_modo.value == "filtros"
            page.update()

        self.rec_modo = ft.Dropdown(
            label="Modo",
            expand=True,
            value="metricas",
            options=[
                ft.dropdown.Option(key="metricas", text="Basado en mis métricas"),
                ft.dropdown.Option(key="filtros", text="Elegir filtros"),
            ],
            on_change=cambio_modo,
        )
        self.rec_genero = ft.Dropdown(
            label="Género",
            expand=True,
            value="todos",
            options=[ft.dropdown.Option(key="todos", text="Cualquiera")]
            + [ft.dropdown.Option(key=str(g["id_genero"]), text=g["nombre"]) for g in self.generos],
        )
        self.rec_mood = ft.Dropdown(
            label="Mood o contexto (prioriza tus pendientes)",
            expand=True,
            value="ninguno",
            options=[ft.dropdown.Option(key="ninguno", text="Sin preferencia")]
            + [ft.dropdown.Option(key=str(e["id_etiqueta"]), text=e["nombre"]) for e in self.etiquetas],
        )
        self.rec_anio = ft.TextField(
            label="Año mínimo aproximado", width=220, keyboard_type=ft.KeyboardType.NUMBER
        )
        self.rec_filtros = ft.Column(
            [ft.Row([self.rec_genero, self.rec_mood], spacing=10), self.rec_anio],
            spacing=10,
            visible=False,
        )
        self.rec_subs = ft.Switch(label="Solo en mis suscripciones", value=True, active_color=COLOR_ROJO)
        self.rec_carta = ft.Container(
            alignment=ft.alignment.center,
            padding=10,
            content=ft.Text(
                "Elegí cómo buscar y tocá “Buscar recomendación”.",
                color=COLOR_TEXTO_SUAVE,
                text_align=ft.TextAlign.CENTER,
            ),
        )

        return ft.Column(
            [
                ft.Text("Una sola carta", size=22, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                self.rec_modo,
                self.rec_filtros,
                ft.Row(
                    [
                        self.rec_subs,
                        ft.ElevatedButton(
                            "Buscar recomendación",
                            icon=ft.Icons.LOCAL_MOVIES,
                            bgcolor=COLOR_ROJO,
                            color="#FFFFFF",
                            on_click=lambda _: self.buscar_recomendacion(),
                        ),
                    ],
                    wrap=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                self.rec_carta,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=14,
        )

    def buscar_recomendacion(self):
        page = self.page
        if self.rec_modo.value == "filtros":
            genero = None if self.rec_genero.value == "todos" else int(self.rec_genero.value)
            mood = None if self.rec_mood.value == "ninguno" else int(self.rec_mood.value)
            anio = None
            if (self.rec_anio.value or "").strip():
                try:
                    anio = int(self.rec_anio.value.strip())
                except ValueError:
                    mostrar_snack(page, "El año mínimo debe ser un número.", COLOR_ROJO)
                    return
        else:
            genero = db.genero_favorito_id()
            mood = None
            anio = None
            if genero is None:
                mostrar_snack(page, "Todavía no tenés películas vistas. Usá 'Elegir filtros' o cargá tu diario.", COLOR_ROJO)
                return

        proveedores = db.activas_ids() if self.rec_subs.value else None
        if proveedores is not None and not proveedores:
            mostrar_snack(page, "No tenés plataformas activas. Activalas en Mis Plataformas o apagá el filtro.", COLOR_ROJO)
            return

        self.criterio = {
            "modo": self.rec_modo.value,
            "genero": genero,
            "nombre_genero": self.nombres_genero.get(genero, ""),
            "anio": anio,
            "proveedores": proveedores,
        }
        self.excluidos = db.ids_excluidos(DIAS_DESCARTE)
        self.cola = []
        if mood:
            for p in db.pendientes_con_etiqueta(mood):
                if p["tmdb_id"] > 0:
                    self.cola.append({
                        "id": p["tmdb_id"],
                        "id_pelicula": p["id_pelicula"],
                        "es_pendiente": True,
                        "mood": self.nombres_etiqueta.get(mood, ""),
                    })
        self.pagina = 1
        self.paginas_totales = 5
        self.siguiente_carta()

    def _llenar_cola(self):
        while not self.cola and self.pagina <= min(self.paginas_totales, 5):
            resultados, total = api.descubrir_peliculas(
                genero_id=self.criterio["genero"],
                anio_desde=self.criterio["anio"],
                provider_ids=self.criterio["proveedores"],
                pagina=self.pagina,
            )
            self.paginas_totales = total
            self.pagina += 1
            for r in resultados:
                if r["id"] not in self.excluidos:
                    self.excluidos.add(r["id"])
                    self.cola.append({
                        "id": r["id"],
                        "es_pendiente": False,
                    })

    def siguiente_carta(self):
        page = self.page
        try:
            while True:
                if not self.cola:
                    self._llenar_cola()
                if not self.cola:
                    self.carta = None
                    self.rec_carta.content = vacio(
                        "No quedan candidatas con estos criterios. Probá con otros filtros."
                    )
                    page.update()
                    return

                candidata = self.cola.pop(0)
                detalle = api.obtener_detalle_pelicula(candidata["id"])
                plataformas = detalle.get("plataformas_ar", [])
                proveedores = self.criterio["proveedores"]
                if proveedores is not None:
                    plataformas = [p for p in plataformas if p["provider_id"] in proveedores]
                if not plataformas:
                    continue

                if candidata["es_pendiente"]:
                    motivo = f"Lo tenías pendiente con el mood “{candidata['mood']}”"
                elif self.criterio["modo"] == "metricas":
                    motivo = f"Porque mirás mucho {self.criterio['nombre_genero']}"
                else:
                    motivo = "Según los filtros que elegiste"
                motivo += f" y está en {plataformas[0]['provider_name']}"

                self.carta = {
                    "tmdb_id": detalle["id"],
                    "titulo": detalle.get("title", ""),
                    "anio": (detalle.get("release_date") or "")[:4],
                    "duracion": detalle.get("runtime"),
                    "poster": detalle.get("poster_path"),
                    "sinopsis": detalle.get("overview") or "Sin sinopsis disponible.",
                    "plataformas": plataformas,
                    "motivo": motivo,
                    "es_pendiente": candidata["es_pendiente"],
                    "id_pelicula": candidata.get("id_pelicula"),
                    "id_genero": self.id_genero_compatible([g["id"] for g in detalle.get("genres", [])]),
                }
                self.mostrar_carta()
                return
        except api.ErrorTMDB as error:
            self.rec_carta.content = vacio(str(error))
            mostrar_snack(page, str(error), COLOR_ROJO)
            page.update()

    def mostrar_carta(self):
        c = self.carta
        insignias = ft.Row(
            [
                ft.Container(
                    content=ft.Text(p["provider_name"], size=11, weight=ft.FontWeight.BOLD, color="#0B0B0F"),
                    bgcolor=COLOR_DORADO,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=6,
                )
                for p in c["plataformas"]
            ],
            wrap=True,
            spacing=6,
            run_spacing=6,
        )
        botones = [
            ft.ElevatedButton(
                "La veo ahora",
                icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
                bgcolor=COLOR_ROJO,
                color="#FFFFFF",
                on_click=self.ver_ahora,
            )
        ]
        if not c["es_pendiente"]:
            botones.append(
                ft.OutlinedButton(
                    "Guardar en pendientes",
                    icon=ft.Icons.BOOKMARK_ADD_OUTLINED,
                    on_click=self.guardar_pendiente,
                )
            )
        botones.append(
            ft.TextButton("Paso / Otra", icon=ft.Icons.SKIP_NEXT, on_click=self.descartar_carta)
        )
        duracion = f"{c['duracion']} min" if c["duracion"] else "Duración desconocida"

        self.rec_carta.content = ft.Container(
            width=520,
            padding=20,
            bgcolor=COLOR_TARJETA,
            border=ft.border.all(2, COLOR_DORADO),
            border_radius=12,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, color=COLOR_DORADO),
                            ft.Text("TU PRÓXIMA FUNCIÓN", size=13, weight=ft.FontWeight.BOLD,
                                    color=COLOR_DORADO, letter_spacing=2),
                        ]
                    ),
                    ft.Divider(color=COLOR_BORDE),
                    ft.Row(
                        [
                            poster(c["poster"], 170, 255),
                            ft.Column(
                                [
                                    ft.Text(c["titulo"], size=22, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{c['anio'] or '—'}  ·  {duracion}", size=13, color=COLOR_TEXTO_SUAVE),
                                    ft.Text(c["motivo"], italic=True, color=COLOR_DORADO, size=13),
                                    insignias,
                                ],
                                spacing=10,
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=16,
                    ),
                    ft.Text(c["sinopsis"], size=13),
                    ft.Divider(color=COLOR_BORDE),
                    ft.Row(botones, wrap=True, alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        self.page.update()

    def ver_ahora(self, _=None):
        c = self.carta
        if c["id_pelicula"]:
            pelicula = db.obtener_pelicula(c["id_pelicula"])
            pelicula["estado"] = "vista"
            pelicula["fecha_vista"] = date.today().isoformat()
            self.abrir_formulario(pelicula=pelicula, al_guardar=self.siguiente_carta)
            return
        precarga = {
            "tmdb_id": c["tmdb_id"],
            "titulo": c["titulo"],
            "anio": int(c["anio"]) if c["anio"] else None,
            "duracion_min": c["duracion"],
            "poster_path": c["poster"],
            "id_genero": c["id_genero"],
            "estado": "vista",
            "fecha_vista": date.today().isoformat(),
        }
        self.abrir_formulario(precarga=precarga, al_guardar=self.siguiente_carta)

    def guardar_pendiente(self, _=None):
        c = self.carta
        try:
            db.guardar_pelicula({
                "tmdb_id": c["tmdb_id"],
                "titulo": c["titulo"],
                "anio": int(c["anio"]) if c["anio"] else None,
                "duracion_min": c["duracion"],
                "poster_path": c["poster"],
                "estado": "pendiente",
                "puntaje": None,
                "nota_diario": None,
                "fecha_vista": None,
                "id_genero": c["id_genero"],
                "etiquetas": [],
            })
            mostrar_snack(self.page, f"“{c['titulo']}” quedó en tus pendientes.")
        except sqlite3.IntegrityError:
            mostrar_snack(self.page, "Esa película ya está en tu diario.", COLOR_ROJO)
        self.siguiente_carta()

    def descartar_carta(self, _=None):
        db.descartar(self.carta["tmdb_id"])
        self.excluidos.add(self.carta["tmdb_id"])
        self.siguiente_carta()

    # ----- Sección 3: Métricas -----

    def seccion_metricas(self):
        k = db.kpis()

        def ticket(titulo, valor):
            return caja_ticket(
                ft.Column(
                    [
                        ft.Row([
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, color=COLOR_DORADO),
                            ft.Text(titulo, size=12, color=COLOR_TEXTO_SUAVE),
                        ]),
                        ft.Divider(color=COLOR_BORDE),
                        ft.Text(valor, size=26, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                    ],
                    spacing=6,
                ),
                ancho=230,
            )

        kpis = ft.Row(
            [
                ticket("Películas vistas", str(k["vistas"])),
                ticket("Pendientes", str(k["pendientes"])),
                ticket("Horas acumuladas", f"{k['horas'] or 0:.1f} h"),
                ticket("Promedio de pochoclos", texto_promedio(k["promedio"])),
            ],
            wrap=True,
            spacing=14,
            run_spacing=14,
        )

        def fila_ranking(nombre, cantidad, promedio, color):
            return ft.Column(
                [
                    ft.Row([
                        ft.Text(nombre, expand=True, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{cantidad} vistas · {texto_promedio(promedio)}", size=12, color=COLOR_TEXTO_SUAVE),
                    ]),
                    ft.ProgressBar(value=(promedio or 0) / 5, color=color, bgcolor=COLOR_FICHA, bar_height=8),
                ],
                spacing=4,
            )

        generos = [fila_ranking(g["nombre"], g["cantidad"], g["promedio"], COLOR_DORADO)
                   for g in db.ranking_generos()]
        etiquetas = db.ranking_etiquetas()
        moods = [fila_ranking(e["nombre"], e["cantidad"], e["promedio"], COLOR_ROJO)
                 for e in etiquetas if e["tipo"] == "mood"]
        contextos = [fila_ranking(e["nombre"], e["cantidad"], e["promedio"], COLOR_DORADO)
                     for e in etiquetas if e["tipo"] == "contexto"]

        def bloque(titulo, filas):
            return caja_ticket(
                ft.Column(
                    [ft.Text(titulo, size=16, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                     ft.Divider(color=COLOR_BORDE)] + (filas or [vacio("Todavía no hay películas vistas.")]),
                    spacing=12,
                )
            )

        return ft.Column(
            [
                ft.Text("Mis Métricas", size=22, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                kpis,
                bloque("Géneros favoritos", generos),
                bloque("Rendimiento por mood", moods),
                bloque("Rendimiento por contexto", contextos),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=16,
        )

    # ----- Sección 4: Mis plataformas -----

    def seccion_plataformas(self):
        page = self.page
        lista = ft.Column(spacing=8)

        def cambiar(pid, valor):
            db.set_suscripcion(pid, valor)

        def fila_plataforma(s):
            logo = (
                ft.Image(src=f"https://image.tmdb.org/t/p/w92{s['logo_path']}", width=40, height=40, border_radius=8)
                if s["logo_path"]
                else ft.Icon(ft.Icons.LIVE_TV, color=COLOR_DORADO)
            )
            return ft.Container(
                padding=10,
                bgcolor=COLOR_TARJETA,
                border_radius=10,
                content=ft.Row(
                    [
                        logo,
                        ft.Text(s["nombre"], expand=True),
                        ft.Switch(
                            value=bool(s["activa"]),
                            active_color=COLOR_ROJO,
                            on_change=lambda e, pid=s["provider_id"]: cambiar(pid, e.control.value),
                        ),
                    ]
                ),
            )

        def cargar():
            lista.controls = [fila_plataforma(s) for s in db.suscripciones()]

        def sincronizar(_):
            try:
                proveedores = api.obtener_proveedores_argentina()
            except api.ErrorTMDB as error:
                mostrar_snack(page, str(error), COLOR_ROJO)
                return
            db.sincronizar_proveedores(proveedores)
            cargar()
            mostrar_snack(page, f"Sincronizadas {len(proveedores)} plataformas de Argentina.")

        cargar()
        return ft.Column(
            [
                ft.Text("Mis Plataformas", size=22, weight=ft.FontWeight.BOLD, color=COLOR_DORADO),
                ft.Text("Activá las plataformas que tenés contratadas en Argentina.", color=COLOR_TEXTO_SUAVE),
                ft.ElevatedButton(
                    "Sincronizar plataformas de Argentina desde TMDB",
                    icon=ft.Icons.SYNC,
                    bgcolor=COLOR_ROJO,
                    color="#FFFFFF",
                    on_click=sincronizar,
                ),
                lista,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=14,
        )


def main(page: ft.Page):
    page.title = "Diario de Películas Vistas"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_FONDO
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=COLOR_ROJO)
    try:
        page.window.width = 1100
        page.window.height = 800
    except Exception:
        pass

    db.inicializar_bd()
    app = AplicacionCine(page)
    page.add(app.construir())

    if not TMDB_API_KEY:
        mostrar_snack(
            page,
            "Falta la API Key de TMDB en src/config.py. Podés cargar películas a mano mientras tanto.",
            COLOR_ROJO,
        )


if __name__ == "__main__":
    ft.run(main)
