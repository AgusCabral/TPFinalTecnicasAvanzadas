"""Interfaz La Pochoclera realizada en FLET"""
import sqlite3
from datetime import date, datetime

import flet as ft

import api_service as api
import database as db
from config import (
    COLOR_DORADO,
    COLOR_FONDO,
    COLOR_ROJO,
    DIAS_DESCARTE,
    TMDB_API_KEY,
    TMDB_IMG_BASE,
)

APP_NOMBRE = "LaPochoclera"

COLOR_SUPERFICIE = "#16161E"
COLOR_SUPERFICIE_ALTA = "#20202A"
COLOR_BORDE = "#2A2A36"
COLOR_BORDE_DORADO = "#6B5A1E"
COLOR_TEXTO = "#F2F2F5"
COLOR_TEXTO_SUAVE = "#9A9AAB"
COLOR_PENDIENTE = "#C2410C"
COLOR_MOOD = "#3A2350"
COLOR_CONTEXTO = "#1B3A44"

ANCHO_CARTA = 220
ANCHO_POSTER = 200
ALTO_POSTER = 290
CENTRO = ft.Alignment(0, 0)


# ---------- Helpers de estilo (compatibles con Flet 1.x) ----------

def pad_simetrico(horizontal=0, vertical=0):
    return ft.Padding(left=horizontal, right=horizontal, top=vertical, bottom=vertical)


def pad_todo(valor=0):
    return ft.Padding(left=valor, right=valor, top=valor, bottom=valor)


def borde_todo(ancho, color):
    lado = ft.BorderSide(ancho, color)
    return ft.Border(top=lado, right=lado, bottom=lado, left=lado)


def estilo(negrita=False, cursiva=False, espaciado=None):
    return ft.TextStyle(
        weight=ft.FontWeight.BOLD if negrita else None,
        italic=True if cursiva else None,
        letter_spacing=espaciado,
    )


def texto(valor, size=14, color=COLOR_TEXTO, negrita=False, cursiva=False,
          espaciado=None, max_lineas=None, alineacion=None):
    return ft.Text(
        valor,
        size=size,
        color=color,
        style=estilo(negrita, cursiva, espaciado),
        max_lines=max_lineas,
        text_align=alineacion,
    )


def campo(label, **kwargs):
    return ft.TextField(
        label=label,
        border_radius=12,
        filled=True,
        bgcolor=COLOR_SUPERFICIE_ALTA,
        border_color=COLOR_BORDE,
        focused_border_color=COLOR_DORADO,
        **kwargs,
    )


def desplegable(label, opciones, valor, **kwargs):
    return ft.Dropdown(
        label=label,
        value=valor,
        options=[ft.DropdownOption(key=k, text=t) for k, t in opciones],
        border_radius=12,
        filled=True,
        bgcolor=COLOR_SUPERFICIE_ALTA,
        border_color=COLOR_BORDE,
        focused_border_color=COLOR_DORADO,
        **kwargs,
    )


def degradado(colores):
    return ft.LinearGradient(begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1), colors=colores)


def BotonRojo(texto_boton, icon=None, on_click=None, **_):
    contenido = [ft.Icon(icon, color="#FFFFFF", size=18)] if icon else []
    contenido.append(ft.Text(texto_boton, color="#FFFFFF", style=estilo(negrita=True)))
    return ft.FilledButton(
        content=ft.Row(contenido, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_click,
        style=ft.ButtonStyle(bgcolor=COLOR_ROJO),
    )


def BotonContorno(texto_boton, icon=None, on_click=None, **_):
    contenido = [ft.Icon(icon, color=COLOR_DORADO, size=18)] if icon else []
    contenido.append(ft.Text(texto_boton, color=COLOR_DORADO))
    return ft.OutlinedButton(
        content=ft.Row(contenido, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_click,
    )


def BotonTexto(texto_boton, icon=None, on_click=None, **_):
    contenido = [ft.Icon(icon, color=COLOR_DORADO, size=18)] if icon else []
    contenido.append(ft.Text(texto_boton, color=COLOR_DORADO))
    return ft.TextButton(
        content=ft.Row(contenido, spacing=6, alignment=ft.MainAxisAlignment.CENTER),
        on_click=on_click,
    )


def pildora(etiqueta_texto, activa, on_click):
    return ft.Container(
        content=texto(etiqueta_texto, 13, "#FFFFFF" if activa else COLOR_TEXTO_SUAVE, negrita=activa),
        padding=pad_simetrico(16, 8),
        border_radius=20,
        bgcolor=COLOR_ROJO if activa else COLOR_SUPERFICIE_ALTA,
        border=borde_todo(1, COLOR_ROJO if activa else COLOR_BORDE),
        on_click=on_click,
    )


def titulo_seccion(valor):
    return texto(valor.upper(), 11, COLOR_DORADO, negrita=True, espaciado=1.5)


# ---------- Utilidades de interfaz ----------

def mostrar_snack(page, mensaje, color=COLOR_SUPERFICIE_ALTA):
    barra = ft.SnackBar(content=ft.Text(mensaje), bgcolor=color)
    if hasattr(page, "show_dialog"):
        page.show_dialog(barra)
    else:
        page.overlay.append(barra)
        barra.open = True
        page.update()


def abrir_dialogo(page, dialogo):
    if hasattr(page, "show_dialog"):
        page.show_dialog(dialogo)
    else:
        page.overlay.append(dialogo)
        dialogo.open = True
        page.update()


def cerrar_dialogo(page, dialogo):
    if hasattr(page, "pop_dialog"):
        page.pop_dialog()
    else:
        dialogo.open = False
        page.update()


def texto_pochoclos(puntaje):
    if not puntaje:
        return "Sin calificar"
    return f"{'🍿' * int(puntaje)}  ({puntaje}/5)"


def texto_promedio(promedio):
    return f"{promedio:.1f} 🍿" if promedio else "Sin datos"


def vacio(mensaje):
    return ft.Container(
        padding=40,
        content=texto(mensaje, 14, COLOR_TEXTO_SUAVE, alineacion=ft.TextAlign.CENTER),
    )


def poster(ruta, ancho=90, alto=135):
    if ruta:
        return ft.Image(
            src=f"{TMDB_IMG_BASE}{ruta}",
            width=ancho,
            height=alto,
            fit=ft.BoxFit.COVER,
            border_radius=10,
        )
    return ft.Container(
        width=ancho,
        height=alto,
        border_radius=10,
        bgcolor=COLOR_SUPERFICIE_ALTA,
        border=borde_todo(1, COLOR_BORDE_DORADO),
        alignment=CENTRO,
        content=ft.Icon(ft.Icons.MOVIE_OUTLINED, color=COLOR_DORADO, size=ancho // 3),
    )


def chip_etiqueta(nombre, tipo):
    es_mood = tipo == "mood"
    return ft.Container(
        content=texto(nombre, 11, "#E9DDFB" if es_mood else "#CDEFFA"),
        padding=pad_simetrico(9, 4),
        border_radius=12,
        bgcolor=COLOR_MOOD if es_mood else COLOR_CONTEXTO,
    )


def chip_seleccionable(etiqueta, seleccion, al_cambiar):
    """Chip que agrega o quita su id del conjunto 'seleccion' al tocarlo."""
    eid = etiqueta["id_etiqueta"]
    contenedor = ft.Container(
        content=texto(etiqueta["nombre"], 12),
        padding=pad_simetrico(14, 8),
        border_radius=20,
        border=borde_todo(1, COLOR_BORDE),
        bgcolor=COLOR_SUPERFICIE_ALTA,
    )

    def pintar():
        activo = eid in seleccion
        contenedor.bgcolor = COLOR_ROJO if activo else COLOR_SUPERFICIE_ALTA
        contenedor.border = borde_todo(1, COLOR_ROJO if activo else COLOR_BORDE)
        contenedor.content.color = "#FFFFFF" if activo else COLOR_TEXTO_SUAVE

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
        super().__init__(spacing=4)
        self.valor = valor or 0
        self.habilitado = habilitado
        self.fila = ft.Row(spacing=2)
        self.leyenda = texto("", 12, COLOR_TEXTO_SUAVE)
        self.controls = [self.fila, self.leyenda]
        self.opacity = 1.0 if habilitado else 0.4
        self._pintar()

    def _pintar(self):
        self.fila.controls = [
            ft.Container(
                content=ft.Text("🍿", size=32),
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


def kpi(icono, titulo_kpi, valor):
    return ft.Container(
        width=250,
        padding=20,
        border_radius=16,
        bgcolor=COLOR_SUPERFICIE,
        border=borde_todo(1, COLOR_BORDE),
        content=ft.Row(
            [
                ft.Container(
                    width=52,
                    height=52,
                    border_radius=16,
                    bgcolor=COLOR_SUPERFICIE_ALTA,
                    alignment=CENTRO,
                    content=ft.Icon(icono, color=COLOR_DORADO, size=26),
                ),
                ft.Column(
                    [
                        texto(titulo_kpi, 12, COLOR_TEXTO_SUAVE),
                        texto(valor, 24, COLOR_TEXTO, negrita=True),
                    ],
                    spacing=2,
                ),
            ],
            spacing=16,
        ),
    )


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
        self.contenido = ft.Container(expand=True, padding=pad_simetrico(24, 16))

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
            bgcolor=COLOR_SUPERFICIE,
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
            padding=pad_simetrico(28, 20),
            gradient=degradado(["#3B0A0F", COLOR_SUPERFICIE, COLOR_FONDO]),
            border=ft.Border(bottom=ft.BorderSide(1, COLOR_BORDE)),
            content=ft.Row(
                [
                    ft.Container(
                        width=56,
                        height=56,
                        border_radius=28,
                        bgcolor=COLOR_MOOD,
                        alignment=CENTRO,
                        content=ft.Text(value="🍿", size=40),
                    ),
                    ft.Column(
                        [
                            texto(APP_NOMBRE, 26, COLOR_TEXTO, negrita=True, espaciado=1),
                            texto("Tu diario de películas, con pochoclos", 13, COLOR_TEXTO_SUAVE),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                spacing=16,
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

        def cambiar_estado(valor):
            self.filtro_estado = valor
            self.mostrar_seccion(0)

        def al_cambiar_texto(_):
            self.filtro_texto = buscador.value or ""
            self.cargar_diario()
            page.update()

        def al_cambiar_genero(_):
            self.filtro_genero = None if filtro_genero.value == "todos" else int(filtro_genero.value)
            self.cargar_diario()
            page.update()

        buscador = campo(
            "Buscar por título",
            value=self.filtro_texto,
            expand=True,
            prefix_icon=ft.Icons.SEARCH,
            on_change=al_cambiar_texto,
        )
        filtro_genero = desplegable(
            "Género",
            [("todos", "Todos los géneros")] + [(str(g["id_genero"]), g["nombre"]) for g in self.generos],
            str(self.filtro_genero) if self.filtro_genero else "todos",
            width=240,
            on_select=al_cambiar_genero,
        )
        pildoras = ft.Row(
            [
                pildora("Todas", self.filtro_estado == "todas", lambda _: cambiar_estado("todas")),
                pildora("Vistas", self.filtro_estado == "vista", lambda _: cambiar_estado("vista")),
                pildora("Pendientes", self.filtro_estado == "pendiente", lambda _: cambiar_estado("pendiente")),
            ],
            spacing=8,
        )

        self.lista_diario = ft.Row(wrap=True, spacing=18, run_spacing=18, alignment=ft.MainAxisAlignment.START)
        self.cargar_diario()

        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Column(
                            [
                                texto("Mi diario", 26, COLOR_TEXTO, negrita=True),
                                texto("Películas vistas y pendientes", 13, COLOR_TEXTO_SUAVE),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        BotonRojo("Nueva película", icon=ft.Icons.ADD, on_click=lambda _: self.abrir_formulario()),
                    ]
                ),
                ft.Row([buscador, filtro_genero], spacing=12),
                pildoras,
                self.lista_diario,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=18,
        )

    def cargar_diario(self):
        peliculas = db.listar_peliculas(self.filtro_estado, self.filtro_genero, self.filtro_texto)
        self.lista_diario.controls = [self.tarjeta_pelicula(p) for p in peliculas] or [
            vacio("Todavía no hay funciones acá. ¡Cargá la primera!")
        ]

    def tarjeta_pelicula(self, p):
        vista = p["estado"] == "vista"
        insignia = ft.Container(
            content=texto(
                "VISTA" if vista else "PENDIENTE",
                10,
                "#0B0B0F" if vista else "#FFFFFF",
                negrita=True,
                espaciado=1,
            ),
            bgcolor=COLOR_DORADO if vista else COLOR_PENDIENTE,
            padding=pad_simetrico(8, 4),
            border_radius=6,
            left=10,
            top=10,
        )
        imagen = ft.Stack(
            [poster(p["poster_path"], ANCHO_POSTER, ALTO_POSTER), insignia],
            width=ANCHO_POSTER,
            height=ALTO_POSTER,
        )
        etiquetas = db.etiquetas_de_pelicula(p["id_pelicula"])
        chips = ft.Row(
            [chip_etiqueta(e["nombre"], e["tipo"]) for e in etiquetas[:3]],
            wrap=True,
            spacing=4,
            run_spacing=4,
        )
        meta = "  ·  ".join(
            x for x in [str(p["anio"] or ""), f"{p['duracion_min']} min" if p["duracion_min"] else ""] if x
        )
        pochos = texto(
            texto_pochoclos(p["puntaje"]) if vista else "Aún sin calificar",
            13,
            COLOR_DORADO if vista else COLOR_TEXTO_SUAVE,
        )

        cuerpo = ft.Column(
            [
                texto(p["titulo"], 15, COLOR_TEXTO, negrita=True, max_lineas=2),
                texto(meta or p["nombre_genero"], 12, COLOR_TEXTO_SUAVE),
                pochos,
                chips,
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.EDIT_OUTLINED,
                            icon_color=COLOR_TEXTO_SUAVE,
                            tooltip="Editar",
                            on_click=lambda _, pid=p["id_pelicula"]: self.editar(pid),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_color=COLOR_TEXTO_SUAVE,
                            tooltip="Eliminar",
                            on_click=lambda _, pel=p: self.confirmar_eliminar(pel),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.END,
                ),
            ],
            spacing=6,
        )

        return ft.Container(
            width=ANCHO_CARTA,
            padding=10,
            border_radius=16,
            bgcolor=COLOR_SUPERFICIE,
            border=borde_todo(1, COLOR_BORDE),
            content=ft.Column([imagen, ft.Container(padding=pad_simetrico(4, 6), content=cuerpo)], spacing=8),
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
            bgcolor=COLOR_SUPERFICIE,
            title=texto("¿Eliminar del diario?", 18, negrita=True),
            content=texto(f"Se va a borrar “{pelicula['titulo']}”. Esta acción no se puede deshacer."),
            actions=[
                BotonTexto("Cancelar", on_click=lambda _: cerrar_dialogo(page, dialogo)),
                BotonRojo("Eliminar", on_click=eliminar),
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

        # Panel de sugerencias: altura fija con scroll, flotando sobre el formulario
        lista_sugerencias = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
        panel_sugerencias = ft.Container(
            top=90,
            left=0,
            width=440,
            height=236,
            visible=False,
            padding=8,
            border_radius=12,
            bgcolor=COLOR_SUPERFICIE_ALTA,
            border=borde_todo(1, COLOR_BORDE_DORADO),
            content=lista_sugerencias,
        )

        f_busqueda = campo(
            "Escribí el título de la película",
            expand=True,
            on_change=lambda _: al_escribir(),
            on_submit=lambda _: al_escribir(),
        )
        f_titulo = campo("Título", value=base.get("titulo", ""))
        f_anio = campo(
            "Año", width=100, value=str(base.get("anio") or ""), keyboard_type=ft.KeyboardType.NUMBER
        )
        f_duracion = campo(
            "Duración (min)", width=140, value=str(base.get("duracion_min") or ""),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        f_genero = desplegable(
            "Género",
            [(str(g["id_genero"]), g["nombre"]) for g in self.generos],
            str(base.get("id_genero") or 18),
            expand=True,
        )
        f_estado = desplegable(
            "Estado",
            [("vista", "Vista"), ("pendiente", "Pendiente")],
            estado_inicial,
            expand=True,
        )
        f_fecha = campo(
            "Fecha en que se vio (AAAA-MM-DD)",
            value=base.get("fecha_vista") or date.today().isoformat(),
        )
        selector = SelectorPochoclos(valor=base.get("puntaje"), habilitado=estado_inicial == "vista")
        f_nota = campo(
            "Nota personal (tu diario íntimo)",
            multiline=True,
            min_lines=4,
            max_lines=6,
            value=base.get("nota_diario") or "",
        )
        slot_poster = ft.Container(content=poster(st["poster"], 100, 150))

        def cambio_estado(_):
            selector.set_habilitado(f_estado.value == "vista")
            page.update()

        f_estado.on_select = cambio_estado

        def fila_sugerencia(r):
            anio = (r.get("release_date") or "")[:4]
            return ft.Container(
                padding=8,
                border_radius=10,
                bgcolor=COLOR_SUPERFICIE,
                on_click=lambda _, r=r: elegir(r),
                content=ft.Row(
                    [
                        poster(r.get("poster_path"), 36, 54),
                        ft.Column(
                            [
                                texto(r.get("title", ""), 13, negrita=True),
                                texto(anio or "Año desconocido", 12, COLOR_TEXTO_SUAVE),
                            ],
                            spacing=2,
                        ),
                    ],
                    spacing=12,
                ),
            )

        def al_escribir():
            consulta = (f_busqueda.value or "").strip()
            if len(consulta) < 3:
                panel_sugerencias.visible = False
                page.update()
                return
            try:
                encontradas = api.buscar_peliculas(consulta)
            except api.ErrorTMDB as error:
                mostrar_snack(page, str(error), COLOR_ROJO)
                return
            lista_sugerencias.controls = [fila_sugerencia(r) for r in encontradas[:20]] or [
                texto("Sin coincidencias.", 13, COLOR_TEXTO_SUAVE)
            ]
            panel_sugerencias.visible = True
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
            f_busqueda.value = ""
            lista_sugerencias.controls = []
            panel_sugerencias.visible = False
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

        columna_datos = ft.Column(
            [
                titulo_seccion("Datos de la función"),
                f_busqueda,
                ft.Row(
                    [slot_poster, ft.Column([f_titulo, ft.Row([f_anio, f_duracion], spacing=8)],
                                            expand=True, spacing=10)],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    spacing=14,
                ),
                ft.Row([f_genero, f_estado], spacing=8),
                f_fecha,
            ],
            width=440,
            spacing=12,
        )

        columna_experiencia = ft.Column(
            [
                titulo_seccion("Tu experiencia"),
                selector,
                f_nota,
                titulo_seccion("Contexto"),
                chips_contexto,
                titulo_seccion("Mood"),
                chips_mood,
            ],
            expand=True,
            spacing=12,
        )

        dialogo = ft.AlertDialog(
            modal=True,
            bgcolor=COLOR_SUPERFICIE,
            title=texto("Editar película" if editando else "Nueva película", 20, COLOR_TEXTO, negrita=True),
            content=ft.Container(
                width=940,
                height=600,
                content=ft.Stack(
                    [
                        ft.Row(
                            [
                                columna_datos,
                                ft.Container(width=1, bgcolor=COLOR_BORDE),
                                columna_experiencia,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.START,
                            spacing=24,
                        ),
                        panel_sugerencias,
                    ]
                ),
            ),
            actions=[
                BotonTexto("Cancelar", on_click=lambda _: cerrar_dialogo(page, dialogo)),
                BotonRojo("Guardar", icon=ft.Icons.CHECK, on_click=guardar),
            ],
        )
        abrir_dialogo(page, dialogo)

    # ----- Sección 2: Recomendador -----

    def seccion_recomendador(self):
        page = self.page

        def cambio_modo(_):
            self.rec_filtros.visible = self.rec_modo.value == "filtros"
            page.update()

        self.rec_modo = desplegable(
            "Modo",
            [("metricas", "Basado en mis métricas"), ("filtros", "Elegir filtros")],
            "metricas",
            expand=True,
            on_select=cambio_modo,
        )
        self.rec_genero = desplegable(
            "Género",
            [("todos", "Cualquiera")] + [(str(g["id_genero"]), g["nombre"]) for g in self.generos],
            "todos",
            expand=True,
        )
        self.rec_mood = desplegable(
            "Mood o contexto (prioriza tus pendientes)",
            [("ninguno", "Sin preferencia")] + [(str(e["id_etiqueta"]), e["nombre"]) for e in self.etiquetas],
            "ninguno",
            expand=True,
        )
        self.rec_anio = campo("Año mínimo aproximado", width=220, keyboard_type=ft.KeyboardType.NUMBER)
        self.rec_filtros = ft.Column(
            [ft.Row([self.rec_genero, self.rec_mood], spacing=12), self.rec_anio],
            spacing=12,
            visible=False,
        )
        self.rec_subs = ft.Switch(label="Solo en mis suscripciones", value=True, active_color=COLOR_ROJO)
        self.rec_carta = ft.Container(
            alignment=CENTRO,
            padding=10,
            content=vacio("Elegí cómo buscar y tocá “Buscar recomendación”."),
        )

        panel = ft.Container(
            padding=20,
            border_radius=16,
            bgcolor=COLOR_SUPERFICIE,
            border=borde_todo(1, COLOR_BORDE),
            content=ft.Column(
                [
                    ft.Row([self.rec_modo], spacing=12),
                    self.rec_filtros,
                    ft.Row(
                        [
                            self.rec_subs,
                            BotonRojo(
                                "Buscar recomendación",
                                icon=ft.Icons.LOCAL_MOVIES,
                                on_click=lambda _: self.buscar_recomendacion(),
                            ),
                        ],
                        wrap=True,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=14,
            ),
        )

        return ft.Column(
            [
                ft.Column(
                    [
                        texto("Recomendador", 26, COLOR_TEXTO, negrita=True),
                        texto("¿No sabes qué ver? ¡El recomendador te ayuda! Podes buscar recomendaciones que estén solo en tus plataformas, usar filtros o dejar que tus métricas te sorprendan.", 13, COLOR_TEXTO_SUAVE),
                    ],
                    spacing=2,
                ),
                panel,
                self.rec_carta,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=18,
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
                mostrar_snack(
                    page,
                    "Todavía no tenés películas vistas. Usá 'Elegir filtros' o cargá tu diario.",
                    COLOR_ROJO,
                )
                return

        proveedores = db.activas_ids() if self.rec_subs.value else None
        if proveedores is not None and not proveedores:
            mostrar_snack(
                page,
                "No tenés plataformas activas. Activalas en Mis Plataformas o apagá el filtro.",
                COLOR_ROJO,
            )
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
                    self.cola.append({"id": r["id"], "es_pendiente": False})

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
                    content=texto(p["provider_name"], 11, "#0B0B0F", negrita=True),
                    bgcolor=COLOR_DORADO,
                    padding=pad_simetrico(10, 5),
                    border_radius=8,
                )
                for p in c["plataformas"]
            ],
            wrap=True,
            spacing=6,
            run_spacing=6,
        )
        botones = [BotonRojo("La veo ahora", icon=ft.Icons.PLAY_CIRCLE_OUTLINE, on_click=self.ver_ahora)]
        if not c["es_pendiente"]:
            botones.append(
                BotonContorno("Guardar en pendientes", icon=ft.Icons.BOOKMARK_ADD_OUTLINED,
                              on_click=self.guardar_pendiente)
            )
        botones.append(BotonTexto("Paso / Otra", icon=ft.Icons.SKIP_NEXT, on_click=self.descartar_carta))
        duracion = f"{c['duracion']} min" if c["duracion"] else "Duración desconocida"

        ticket = ft.Container(
            width=780,
            padding=24,
            border_radius=20,
            border=borde_todo(1, COLOR_BORDE_DORADO),
            gradient=degradado(["#3B0A0F", COLOR_SUPERFICIE, COLOR_SUPERFICIE]),
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, color=COLOR_DORADO),
                            texto("TU PRÓXIMA FUNCIÓN", 12, COLOR_DORADO, negrita=True, espaciado=2),
                        ],
                        spacing=8,
                    ),
                    ft.Divider(color=COLOR_BORDE),
                    ft.Row(
                        [
                            poster(c["poster"], 200, 300),
                            ft.Column(
                                [
                                    texto(c["titulo"], 26, COLOR_TEXTO, negrita=True),
                                    texto(f"{c['anio'] or '—'}  ·  {duracion}", 13, COLOR_TEXTO_SUAVE),
                                    texto(c["motivo"], 14, COLOR_DORADO, cursiva=True),
                                    insignias,
                                    texto(c["sinopsis"], 14, COLOR_TEXTO, max_lineas=6),
                                ],
                                spacing=12,
                                expand=True,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=24,
                    ),
                    ft.Divider(color=COLOR_BORDE),
                    ft.Row(botones, wrap=True, alignment=ft.MainAxisAlignment.END, spacing=10),
                ],
                spacing=16,
            ),
        )
        self.rec_carta.content = ft.Row([ticket], alignment=ft.MainAxisAlignment.CENTER)
        self.page.update()

    def ir_al_diario(self):
        self.nav.selected_index = 0
        self.mostrar_seccion(0)

    def ver_ahora(self, _=None):
        c = self.carta
        if c["id_pelicula"]:
            pelicula = db.obtener_pelicula(c["id_pelicula"])
            pelicula["estado"] = "vista"
            pelicula["fecha_vista"] = date.today().isoformat()
            self.abrir_formulario(pelicula=pelicula, al_guardar=self.ir_al_diario)
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
        self.abrir_formulario(precarga=precarga, al_guardar=self.ir_al_diario)
    
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

        kpis = ft.Row(
            [
                kpi(ft.Icons.CHECK_CIRCLE_OUTLINE, "Películas vistas", str(k["vistas"])),
                kpi(ft.Icons.SCHEDULE, "Pendientes", str(k["pendientes"])),
                kpi(ft.Icons.TIMER_OUTLINED, "Horas acumuladas", f"{k['horas'] or 0:.1f} h"),
                kpi(ft.Icons.STAR_OUTLINE, "Promedio de pochoclos", texto_promedio(k["promedio"])),
            ],
            wrap=True,
            spacing=16,
            run_spacing=16,
        )

        def fila_ranking(nombre, cantidad, promedio, color):
            return ft.Column(
                [
                    ft.Row(
                        [
                            texto(nombre, 14, negrita=True, espaciado=None),
                            ft.Container(expand=True),
                            texto(f"{cantidad} vistas · {texto_promedio(promedio)}", 12, COLOR_TEXTO_SUAVE),
                        ]
                    ),
                    ft.ProgressBar(value=(promedio or 0) / 5, color=color, bgcolor=COLOR_SUPERFICIE_ALTA, bar_height=8),
                ],
                spacing=6,
            )

        generos = [fila_ranking(g["nombre"], g["cantidad"], g["promedio"], COLOR_DORADO)
                   for g in db.ranking_generos()]
        etiquetas = db.ranking_etiquetas()
        moods = [fila_ranking(e["nombre"], e["cantidad"], e["promedio"], COLOR_ROJO)
                 for e in etiquetas if e["tipo"] == "mood"]
        contextos = [fila_ranking(e["nombre"], e["cantidad"], e["promedio"], COLOR_DORADO)
                     for e in etiquetas if e["tipo"] == "contexto"]

        def bloque(titulo_bloque, filas):
            return ft.Container(
                expand=True,
                padding=20,
                border_radius=16,
                bgcolor=COLOR_SUPERFICIE,
                border=borde_todo(1, COLOR_BORDE),
                content=ft.Column(
                    [titulo_seccion(titulo_bloque), ft.Divider(color=COLOR_BORDE)]
                    + (filas or [texto("Todavía no hay películas vistas.", 13, COLOR_TEXTO_SUAVE)]),
                    spacing=14,
                ),
            )

        return ft.Column(
            [
                ft.Column(
                    [
                        texto("Mis métricas", 26, COLOR_TEXTO, negrita=True),
                        texto("Lo que dice tu historial de películas", 13, COLOR_TEXTO_SUAVE),
                    ],
                    spacing=2,
                ),
                kpis,
                ft.Row(
                    [bloque("Géneros favoritos", generos)],
                    spacing=16,
                ),
                ft.Row(
                    [
                        bloque("Rendimiento por mood", moods),
                        bloque("Rendimiento por contexto", contextos),
                    ],
                    spacing=16,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=18,
        )

    # ----- Sección 4: Mis plataformas -----

    def seccion_plataformas(self):
        page = self.page
        lista = ft.Row(wrap=True, spacing=12, run_spacing=12)

        def cambiar(pid, valor):
            db.set_suscripcion(pid, valor)

        def tarjeta_plataforma(s):
            logo = (
                ft.Image(
                    src=f"https://image.tmdb.org/t/p/w92{s['logo_path']}",
                    width=44,
                    height=44,
                    border_radius=10,
                )
                if s["logo_path"]
                else ft.Container(
                    width=44,
                    height=44,
                    border_radius=10,
                    bgcolor=COLOR_SUPERFICIE_ALTA,
                    alignment=CENTRO,
                    content=ft.Icon(ft.Icons.LIVE_TV, color=COLOR_DORADO),
                )
            )
            return ft.Container(
                width=340,
                padding=pad_simetrico(14, 12),
                border_radius=14,
                bgcolor=COLOR_SUPERFICIE,
                border=borde_todo(1, COLOR_DORADO if s["activa"] else COLOR_BORDE),
                content=ft.Row(
                    [
                        logo,
                        texto(s["nombre"], 15, negrita=True),
                        ft.Container(expand=True),
                        ft.Switch(
                            value=bool(s["activa"]),
                            active_color=COLOR_ROJO,
                            on_change=lambda e, pid=s["provider_id"]: cambiar(pid, e.control.value),
                        ),
                    ],
                    spacing=14,
                ),
            )

        def cargar():
            lista.controls = [tarjeta_plataforma(s) for s in db.suscripciones()]

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
                ft.Row(
                    [
                        ft.Column(
                            [
                                texto("Mis plataformas", 26, COLOR_TEXTO, negrita=True),
                                texto("Activá las que tenés contratadas en Argentina. Mantené actualizado el catálogo de plataformas con el botón de sincronización.", 13, COLOR_TEXTO_SUAVE),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        BotonContorno(
                            "Sincronizar desde TMDB",
                            icon=ft.Icons.SYNC,
                            on_click=sincronizar,
                        ),
                    ]
                ),
                lista,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            spacing=18,
        )


def main(page: ft.Page):
    page.title = APP_NOMBRE
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = COLOR_FONDO
    page.padding = 0
    page.theme = ft.Theme(color_scheme_seed=COLOR_ROJO)
    try:
        page.window.width = 1200
        page.window.height = 820
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