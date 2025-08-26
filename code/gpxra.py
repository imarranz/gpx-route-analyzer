# ============================================================================================
#
# https://patorjk.com/software/taag/?p=display&f=Doom&t=GPX%20Route%20Analyzer&x=none
#
#  _____ ________   __ ______            _          ___              _
# |  __ \| ___ \ \ / / | ___ \          | |        / _ \            | |
# | |  \/| |_/ /\ V /  | |_/ /___  _   _| |_ ___  / /_\ \_ __   __ _| |_   _ _______ _ __
# | | __ |  __/ /   \  |    // _ \| | | | __/ _ \ |  _  | '_ \ / _` | | | | |_  / _ \ '__|
# | |_\ \| |   / /^\ \ | |\ \ (_) | |_| | ||  __/ | | | | | | | (_| | | |_| |/ /  __/ |
#  \____/\_|   \/   \/ \_| \_\___/ \__,_|\__\___| \_| |_/_| |_|\__,_|_|\__, /___\___|_|
#                                                                       __/ |
#                                                                      |___/
#
# ============================================================================================
# Librerías
# ============================================================================================

import streamlit as st
import pandas as pd
import numpy as npy
import gpxpy
import gpxpy.gpx
import altair as alt
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw

from datetime import datetime, timezone
from branca.colormap import LinearColormap
import locale
import os

# ============================================================================================
# Configuración y Variables
# ============================================================================================

try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    # En Cloud no hay locales instalados: seguimos sin cambiar el locale del sistema
    pass

# ============================================================================================
# Utilidades
# ============================================================================================

from gpxra.geo import haversine
from gpxra.io import parse_gpx
from gpxra.metrics import compute_metrics, make_splits
from gpxra.formatting import format_time, hex_to_rgba
from gpxra.maps import (
    TILE_SOURCES, build_map, prepare_coords,
    draw_route, add_start_end_markers, add_key_point_markers,
    create_layers, _add_marker
)

# ============================================================================================
# Funciones
# ============================================================================================

def format_date_es(dt: datetime) -> str:

    meses = [
        "enero","febrero","marzo",
        "abril","mayo","junio",
        "julio","agosto","septiembre",
        "octubre","noviembre","diciembre"
    ]
    return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"

# ============================================================================================
# Streamlit UI
# ============================================================================================

ABOUT_MD = """
## 🚴 GPX Route Analyzer

Analiza archivos **GPX** de ciclismo, running o senderismo. Calcula métricas (distancia, desnivel, tiempos), muestra **mapas** con escala robusta por velocidad/altitud y **gráficas** interactivas para la altitud y la velocidad. También para la frecuencia cardiaca (HR) y la cadencia si están disponibles en el fichero **GPX**.

  * Autor: *Ibon Martínez-Arranz*
  * Repositorio: *https://github.com/imarranz/gpx-route-analyzer*
  * Licencia: *MIT License*
"""

st.set_page_config(
    page_title="GPX Route Analyzer",
    layout="wide",
    page_icon="🚴",
    menu_items={
        "About": ABOUT_MD,
        # "Get help": "https://…",
        # "Report a bug": "https://…/issues",
        })

APP_URL = "https://gpx-route-analyzer.streamlit.app/"     # opcional
REPO_URL = "https://github.com/imarranz/gpx-route-analyzer"

st.markdown(f"""
<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin: 6px 0 14px 0;">
  <!-- Autor -->
  <img src="https://img.shields.io/badge/Autor-Ibon%20Martinez--Arranz-2c7bb6?style=flat-square" alt="Autor: Ibon">
  <!-- Streamlit -->
  <a href="{APP_URL}" target="_blank" rel="noopener">
    <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit" height="20">
  </a>
  <!-- Repo -->
  <a href="{REPO_URL}" target="_blank" rel="noopener">
    <img src="https://img.shields.io/badge/GitHub-repo-24292e?style=flat-square&logo=github" alt="GitHub">
  </a>
  <!-- Python -->
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+">
  <!-- Licencia -->
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT">
  <!-- Pandas -->
  <img src="https://img.shields.io/badge/Pandas-2.2.3-150458?style=for-the-badge" alt="Pandas 2.2.3">
  <!-- GPXPy -->
  <img src="https://img.shields.io/badge/GPXPy-1.6.2-0A7FFF?style=for-the-badge" alt="GPXPy 1.6.2">
  <!-- Streamlit -->
  <img src="https://img.shields.io/badge/Streamlit-1.48.1-FF4B4B?style=for-the-badge" alt="Streamlit 1.48.1">
  <!-- streamlit-folium -->
  <img src="https://img.shields.io/badge/streamlit--folium-0.25.1-2c7bb6?style=for-the-badge" alt="streamlit-folium 0.25.1">
  <!-- Altair -->
  <img src="https://img.shields.io/badge/Altair-5.5.0-FF4B4B?style=for-the-badge" alt="Altair 5.5.0">
  <!-- Folium -->
  <img src="https://img.shields.io/badge/Folium-0.20.0-77B829?style=for-the-badge" alt="Folium 0.20.0">
</div>
""", unsafe_allow_html=True)


st.title("🚴 GPX Route Analyzer: Rutas de Ciclismo")

with st.sidebar:
    st.header("🚴 GPX Route Analyzer")
    st.text("Analiza tus archivos GPX: calcula métricas, muestra el mapa y gráficos interactivos. Configura la visualización y filtros en esta barra.")

    st.header("⚙️ Ajustes")
    moving_speed_threshold = st.slider(
        label="Umbral de movimiento (m/s)",
        min_value=0.0, max_value=3.0, value=0.5, step=0.1,
        help=(
            "Velocidades ≤ a este umbral se consideran PARADA. "
            "Afecta al tiempo en movimiento, a los parciales y a la detección de pausas."
        ),
        key="moving_speed_threshold_slider",
    )

    map_mode = st.selectbox(
        label="Representación en mapa",
        options=["Posición", "Velocidad", "Altitud"],
        index=0,
        help=(
            "• Posición: traza una línea única con el color elegido.\n"
            "• Velocidad: línea coloreada por km/h (con leyenda).\n"
            "• Altitud: línea coloreada por metros de altitud.\n"
            "Sugerencia: con 'Rango de color' en modo robusto evitas que outliers distorsionen la escala."
        ),
        key="map_mode_select",
    )

    color_range_mode = st.selectbox(
        label="Rango de color",
        options=["Min–Max", "Min-Max (robusto)"],
        index=1,
        help=(
            "Min–Max: usa el rango completo de valores.\n"
            "Robusto: usa P2–P98 y satura por debajo/encima (ideal para picos producidos por un error de medida)."
        ),
        key="color_range_mode_select",
    )

    max_points = st.slider(
        label="Máximo de puntos a dibujar",
        min_value=100, max_value=1000, value=200, step=100,
        help=(
            "Submuestreo para rendimiento:\n"
            "• En 'Posición' y 'Velocidad/Altitud' (línea), reduce vértices de la polilínea.\n"
            "• En modo puntos, limita el nº de marcadores.\n"
            "Incrementa si tu equipo va sobrado, reduce si el mapa va lento."
        ),
        key="max_points_slider",
    )

    point_radius = st.slider(
        label="Radio de los puntos (px)",
        min_value=2, max_value=10, value=4, step=1,
        help=(
            "Tamaño de los CircleMarker cuando el mapa pinta PUNTOS.\n"
            "Nota: en modos de LÍNEA (posición/velocidad/altitud) no tiene efecto."
        ),
        key="point_radius_slider",
    )

    show_hr = st.checkbox(
        label="Mostrar HR si está disponible",
        value=True,
        help=(
            "Muestra la serie de frecuencia cardiaca en 'Estadísticas' "
            "y activa el análisis de zonas (quesito) si hay datos."
        ),
        key="show_hr_check",
    )

    show_cad = st.checkbox(
        label="Mostrar cadencia si está disponible",
        value=True,
        help=(
            "Muestra la serie de cadencia (rpm) en 'Estadísticas' y su distribución si existe en el GPX."
        ),
        key="show_cad_check",
    )

    grade_window = st.slider(
        label="Suavizado pendiente (puntos)",
        min_value=1, max_value=51, value=9, step=2,
        help=(
            "Ventana de mediana centrada para suavizar la pendiente (%). "
            "Recomendado impar (3, 5, 7, 9...). Afecta a la serie y a los marcadores de pendiente máx/mín."
        ),
        key="grade_window_slider",
    )

    grade_clip = st.slider(
        label="Clip pendiente ± (%)",
        min_value=2, max_value=25, value=15, step=1,
        help=(
            "Limita la pendiente mostrada (saturación visual) para evitar picos irreales. "
            "Solo afecta a la visualización, NO a los cálculos."
        ),
        key="grade_clip_slider",
    )

    color_hex = st.color_picker(
        label="Color de las gráficas",
        value="#1f77b4",
        help=(
            "Color base de las líneas en las GRÁFICAS y de la LÍNEA en modo 'Posición'. "
            "No afecta a las líneas coloreadas por velocidad/altitud (usan su colormap)."
        ),
        key="color_hex_picker",
    )

    line_width = st.slider(
        label="Grosor de línea (px)",
        min_value=1.0, max_value=8.0, value=2.5, step=0.5,
        help=(
            "Grosor de las líneas en las gráficas (Altair). "
            "No cambia el grosor de la polilínea del mapa, que se controla aparte."
        ),
        key="line_width_slider",
    )


BG_ = hex_to_rgba(color_hex, 0.10)   # fondo suave (10% opacidad)
BD_ = hex_to_rgba(color_hex, 0.35)   # borde
TAB_FONT_SIZE_ = 26


st.markdown(f"""
<style>
/* Tarjeta de cada st.metric */
div[data-testid="stMetric"] {{
  background: {BG_};
  padding: 0.75rem 0.9rem;
  border-radius: 12px;
  border: 3px solid {BD_};
}}

/* Label más legible */
div[data-testid="stMetric"] label p {{
  margin-bottom: 0;
  font-weight: 600;
  opacity: 0.9;
}}

/* Forzar tamaño en todo el tablist */
div[data-testid="stTabs"] [role="tablist"] * {{
  font-size: {TAB_FONT_SIZE_}px !important;
  padding: 0.1rem 0.2rem !important;
}}

/* Oculta encabezado del índice y las celdas de índice en tablas de pandas */
thead tr th:first-child {{display: none !important;}}
tbody th {{display: none !important;}}
</style>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader("Sube tus ficheros .gpx", type=["gpx"], accept_multiple_files=True)
if not uploaded_files:
    st.stop()

sessions = {}
for f in uploaded_files:
    try:
        df_points = parse_gpx(f)
        sessions[f.name] = df_points
    except Exception as e:
        st.warning(f"No se pudo procesar {f.name}: {e}")

file_names = list(sessions.keys())
activity_selected = st.selectbox(label="Selecciona una actividad",
                                 options=file_names,
                                 key="activity_selected_select")
df = sessions[activity_selected]

metrics, df_proc, splits = compute_metrics(df, moving_speed_threshold)

tab_resumen, tab_mapa, tab_stats, tab_guide = st.tabs(["Resumen", "Mapa", "Estadísticas", "Guía"])

# ============================================================================================
# TAB: RESUMEN
# ============================================================================================

def make_summary(metrics):
    """
    Genera un texto resumen extendido y dinámico en HTML (para st.markdown con unsafe_allow_html=True).
    Requiere:
        - date, start_time, end_time: datetime
        - elapsed_time_s, distance_km, moving_time_s: numéricos (segundos / km)
        - avg_moving_speed_kmh, max_speed_kmh: numéricos (km/h)
    Opcionales:
        - 'gain_m' o 'elevation_gain_m' o 'elev_gain_m': desnivel positivo en metros
    Además, debe existir la función format_time(segundos) -> "Hh Mm".
    """

    # --- Datos base y derivados seguros ---
    distance = float(metrics.get('distance_km', 0.0))
    v_avg = float(metrics.get('avg_moving_speed_kmh', 0.0))
    v_max = float(metrics.get('max_speed_kmh', 0.0))
    elapsed_s = int(metrics.get('elapsed_time_s', 0) or 0)
    moving_s  = int(metrics.get('moving_time_s', 0) or 0)
    pausa_s   = max(elapsed_s - moving_s, 0)
    pausas_ratio = (pausa_s / elapsed_s) if elapsed_s > 0 else 0.0

    # Fecha y horas (con fallback por si faltan)
    #date_str = metrics['date'].strftime('%d de %B de %Y') if metrics.get('date') else 'fecha desconocida'
    date_str = format_date_es(metrics['date']) if metrics.get('date') else 'fecha desconocida'
    start_str = metrics['start_time'].strftime('%H:%M:%S') if metrics.get('start_time') else '--:--:--'
    end_str   = metrics['end_time'].strftime('%H:%M:%S') if metrics.get('end_time') else '--:--:--'
    start_hour = metrics['start_time'].hour if metrics.get('start_time') else None

    # Desnivel opcional
    elev_gain = None
    for k in ('gain_m', 'elevation_gain_m', 'elev_gain_m'):
        if k in metrics and metrics[k] is not None:
            elev_gain = float(metrics[k])
            break

    # --- Frases adaptativas ---

    # Pausas
    if pausa_s < 5 * 60:
        frase_pausa = "🚴‍♂️ ¡apenas paraste a coger aire!"
    elif pausa_s <= 30 * 60:
        frase_pausa = "🌄 espero que admiraras el paisaje y descansaras un poco."
    else:
        frase_pausa = "🔧 ojalá fuera para disfrutar del entorno y no por una avería en la bicicleta."

    # Distancia
    if distance < 5:
        frase_dist = "una salida breve, perfecta para estirar las piernas 🚶‍♂️"
    elif distance < 20:
        frase_dist = "una ruta de buena duración para mantener la forma 🚴‍♂️"
    elif distance < 50:
        frase_dist = "una salida larga que demuestra tu resistencia 💪"
    else:
        frase_dist = "¡una gran ruta digna de ciclistas experimentados! 🏆"

    # Ritmo medio en movimiento
    if v_avg < 12:
        frase_ritmo = "ritmo tranquilo, ideal para disfrutar del paisaje 🌳"
    elif v_avg <= 20:
        frase_ritmo = "ritmo moderado con buen equilibrio entre esfuerzo y disfrute 🚴"
    else:
        frase_ritmo = "ritmo alto, una sesión exigente 💨"

    # Velocidad máxima
    if v_max > 40:
        frase_vmax = "alcanzaste velocidades de vértigo 🚀"
    elif v_max >= 30:
        frase_vmax = "tuviste picos de velocidad muy respetables ⚡"
    else:
        frase_vmax = "mantuviste un ritmo constante y seguro ✅"

    # Hora de inicio
    if start_hour is None:
        frase_hora = ""
    elif 5 <= start_hour < 12:
        frase_hora = "aprovechando las primeras horas del día ☀️"
    elif 12 <= start_hour < 20:
        frase_hora = "disfrutando de la luz de la tarde 🌇"
    else:
        frase_hora = "pedaleando bajo el cielo nocturno 🌙"

    # Proporción de paradas
    if pausas_ratio > 0.30:
        frase_pausas_ratio = "fue una salida pausada, con bastantes paradas 🛑"
    elif pausas_ratio < 0.10:
        frase_pausas_ratio = "fue una salida muy fluida, casi sin interrupciones 🔄"
    else:
        frase_pausas_ratio = ""  # intermedio, no añadimos texto

    # Desnivel (si existe)
    frase_desnivel = ""
    if elev_gain is not None:
        if elev_gain < 100:
            frase_desnivel = "recorrido prácticamente llano 🟢"
        elif elev_gain <= 500:
            frase_desnivel = "con algunos desniveles para darle intensidad ⛰️"
        else:
            frase_desnivel = "un desafío serio con un desnivel considerable 🏔️"

    # --- Construcción del texto resumen ---
    resumen = (
        f"<b>Memoria de la ruta</b><br>"
        f"El {date_str} realizaste una actividad en bicicleta que comenzó a las {start_str} "
        f"y finalizó a las {end_str}. "
        f"En total, estuviste <b>{format_time(elapsed_s)}</b> desde el inicio hasta el final, "
        f"recorriendo una distancia de <b>{distance:.2f} km</b>. "
        f"Durante la mayor parte del recorrido estuviste en movimiento durante {format_time(moving_s)}, "
        f"manteniendo una velocidad media en movimiento de <b>{v_avg:.1f} km/h</b>. "
        f"En los tramos más rápidos alcanzaste una velocidad máxima de {v_max:.1f} km/h. "
    )

    # Bloque “contexto” combinando reglas (solo añadimos las que aportan)
    contexto_por_partes = []

    # Hora
    if frase_hora:
        contexto_por_partes.append(frase_hora)
    # Distancia + Ritmo
    if frase_dist:
        contexto_por_partes.append(frase_dist)
    if frase_ritmo:
        contexto_por_partes.append(frase_ritmo)
    # Vmax
    if frase_vmax:
        contexto_por_partes.append(frase_vmax)
    # Desnivel
    if frase_desnivel:
        contexto_por_partes.append(frase_desnivel)
    # Fluidez por pausas
    if frase_pausas_ratio:
        contexto_por_partes.append(frase_pausas_ratio)

    if contexto_por_partes:
        resumen += "Fue una sesión que combinó esfuerzo y disfrute, " + ", ".join(contexto_por_partes) + "."

    # Frase final sobre pausa concreta
    resumen += f" Además, estuviste parado {format_time(pausa_s)}, {frase_pausa}"

    return resumen


with tab_resumen:
    st.subheader("Resumen")

    # Métricas en cuadrícula (4 columnas x N filas)
    metrics_items = [
        ("Fecha", format_date_es(metrics['date'])),
        ("Hora inicio", metrics['start_time'].strftime("%H:%M:%S")),
        ("Hora fin", metrics['end_time'].strftime("%H:%M:%S")),
        ("Tiempo total", format_time(metrics['elapsed_time_s'])),
        ("Distancia", f"{metrics['distance_km']:.2f} km"),
        ("Tiempo en movimiento", format_time(metrics['moving_time_s'])),
        ("Velocidad media (mov.)", f"{metrics['avg_moving_speed_kmh']:.1f} km/h"),
        ("Velocidad máx.", f"{metrics['max_speed_kmh']:.1f} km/h"),
    ]

    for i in range(0, len(metrics_items), 4):
        cols = st.columns(4)
        for (label, value), col in zip(metrics_items[i:i+4], cols):
            with col:
                st.metric(label, value, border = True)

    resumen_df = pd.DataFrame([{'Fecha': metrics['date'],
                                'Inicio': metrics['start_time'],
                                'Fin': metrics['end_time'],
                                'Distancia (km)': round(metrics['distance_km'], 2),
                                'Tiempo mov.': format_time(metrics['moving_time_s']),
                                'Vmed (km/h)': round(metrics['avg_moving_speed_kmh'], 1),
                                'Vmax (km/h)': round(metrics['max_speed_kmh'], 1) }])


    st.markdown(
        f"""
        <br>
        <div style="
            border-left: 16px solid {BD_};
            background-color: {BG_};
            padding: 14px 16px;
            border-radius: 8px;
            font-size: 24px;
            line-height: 1.5;
        ">
            {make_summary(metrics)}
        </div>
        <br>
        """,
        unsafe_allow_html=True
    )

    if not splits.empty:
        # Recalcular splits según el slider
        c1, _ = st.columns([1, 5])    # ~16% / 84%
        with c1:
            split_km = st.slider("Tamaño del parcial (km)", 1, 10, 5, 1, key="split_km")
        splits_dyn = make_splits(df_proc, split_km)

        st.markdown(f"### Parciales (cada {split_km} km)")
        if not splits_dyn.empty:
            cols_show = ['km_inicio', 'dist_moving', 'time_moving', 'elev_gain', 'ritmo_min_km']
            df_show = splits_dyn[cols_show].copy()

            # Nombres legibles en castellano
            col_map = {
                'km_inicio': 'Inicio (km)',
                'dist_moving': 'Distancia mov. (m)',
                'time_moving': 'Tiempo en mov. (s)',
                'elev_gain': 'Desnivel + (m)',
                'ritmo_min_km': 'Ritmo (min/km)',
            }
            df_show = df_show.rename(columns=col_map)
            cols_show_es = list(col_map.values())

            # Styler con barras y sin índice
            styler = (
                df_show.style
                .format({
                    'Inicio (km)': '{:.0f}',
                    'Distancia mov. (m)': '{:.0f}',
                    'Tiempo en mov. (s)': '{:.0f}',
                    'Desnivel + (m)': '{:.0f}',
                    'Ritmo (min/km)': '{:.1f}',
                })
                .bar(subset=cols_show_es, color=color_hex, height=70, width=60)
                .hide(axis="index")
                .set_caption("Parciales por tramos de N km (configurable): inicio del tramo (km), distancia y tiempo en movimiento, desnivel positivo y ritmo medio (min/km).")
            )
            st.table(styler)
        else:
            st.info("No hay datos suficientes para calcular parciales.")

    # --- Descarga de datos (CSV) ---
    st.markdown("### Descarga de datos")

    # Nombre base del fichero (sin extensión)
    fname = activity_selected.rsplit(".", 1)[0] if isinstance(activity_selected, str) else "actividad"

    # Columnas típicas; si HR/Cad no existen, se omiten automáticamente
    cols_points = ['time','lat','lon','ele','dist','d_dist','dt','speed','moving','hr','cad']
    cols_points = [c for c in cols_points if c in df_proc.columns]

    csv_points = df_proc[cols_points].to_csv(index=False).encode("utf-8")

    date_str = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_fname = fname.replace(" ", "_").replace("/", "-")

    st.download_button(
        label="⬇️ Descargar puntos (CSV)",
        data=csv_points,
        file_name=f"{date_str}_{safe_fname}_points.csv",
        mime="text/csv"
    )

# ============================================================================================
# TAB: MAPA
# ============================================================================================

with tab_mapa:

    st.subheader("Mapa")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        base_layer = st.selectbox(
            label="Mapa base",
            options=list(TILE_SOURCES.keys()),
            index=0,
            label_visibility="visible",
            help=(
                "Elige la capa de fondo.\n"
                "• OpenStreetMap: estándar\n"
                "• Carto Light/Dark: estilo limpio para ver datos\n"
                "• Satélite (Esri): ortofoto, útil en montaña"
            ),
            key="map_base_select",
        )

    with c2:
        show_minimap = st.checkbox(
            label="Mini-map",
            value=True,
            help="Muestra un minimapa en la esquina con una vista general. Útil para orientarte en rutas largas.",
            key="map_minimap_check",
        )

    with c3:
        show_measure = st.checkbox(
            label="Regla de medir",
            value=True,
            help="Activa la herramienta de medición para calcular distancias (km) y áreas directamente sobre el mapa.",
            key="map_measure_check",
        )

    with c4:
        use_layers = st.checkbox(
            label="Capas",
            value=True,
            help=(
                "Permite encender/apagar grupos en el mapa: Ruta, Inicio/fin, Altitud (máx/mín), "
                "Rendimiento (vel/pte máx/min) y Paradas (≥ umbral)."
            ),
            key="map_layers_check",
        )


    center = [df_proc['lat'].mean(), df_proc['lon'].mean()]
    m = build_map(center, base_layer, show_minimap=show_minimap, show_measure=show_measure)

    coords_df = prepare_coords(df_proc, max_points)
    draw_route(m, coords_df, map_mode, color_range_mode, point_radius, color_hex)

    # Crear capas si procede
    layers = create_layers(m, enabled=use_layers)

    # Inicio/fin a su capa si existe
    add_start_end_markers(m, coords_df, layer=layers.get("start_end") if layers else None)

    # Puntos clave usando capas (o mapa si no hay capas)
    add_key_point_markers(
        m, df_proc,
        grade_window=grade_window,
        min_stop_seconds=60,
        format_time_fn=format_time,
        layers=layers if layers else None
    )

    st_folium(m, width=None)

# ============================================================================================
# TAB: ESTADÍSTICAS
# ============================================================================================

with tab_stats:
    st.subheader("Perfiles y Series")

    chart_df = pd.DataFrame({
        'km': df_proc['dist']/1000.0,
        'ele': df_proc['ele'],
        'speed_kmh': df_proc['speed']*3.6,
        'hr': df_proc['hr'] if 'hr' in df_proc.columns else npy.nan,
        'cad': df_proc['cad'] if 'cad' in df_proc.columns else npy.nan
    })

    # ==== Pendiente (%), suavizado y recorte ====
    grade_raw = 100.0 * df_proc['ele'].diff() / df_proc['d_dist'].replace(0, npy.nan)
    grade_pct = grade_raw.rolling(window=grade_window, min_periods=1, center=True).median()
    grade_pct = grade_pct.clip(-grade_clip, grade_clip).fillna(0)
    chart_df['grade_pct'] = grade_pct

    # Perfil de altitud
    st.markdown("#### ⛰️ Altitud")

    y_min = chart_df["ele"].min() - 5
    y_max = chart_df["ele"].max() + 5

    alt_area = alt.Chart(chart_df).mark_area(opacity=0.25, color=color_hex, size=line_width, clip=True).encode(
        x=alt.X('km:Q', title='Distancia (km)'),
        y=alt.Y('ele:Q', title='Altitud (m)', scale=alt.Scale(domain=[y_min, y_max], zero=False)),
    )
    alt_line = alt.Chart(chart_df).mark_line(color=color_hex, size=line_width).encode(
        x=alt.X('km:Q', title='Distancia (km)'),
        y=alt.Y('ele:Q', title='Altitud (m)', scale=alt.Scale(domain=[y_min, y_max])),
        tooltip=[
            alt.Tooltip("km:Q", title="Distancia (km)", format=".1f"),
            alt.Tooltip("ele:Q", title="Altitud (m)", format=".1f"),
        ],
    )
    alt_chart_elev = (alt_line+alt_area).properties(height=300)
    st.altair_chart(alt_chart_elev, use_container_width=True)

    # Velocidad
    st.markdown("#### ⚡ Velocidad")
    alt_chart_speed = alt.Chart(chart_df).mark_line(color=color_hex, size=line_width).encode(
        x=alt.X('km:Q', title='Distancia (km)'),
        y=alt.Y('speed_kmh:Q', title='Velocidad (km/h)'),
        tooltip=[
            alt.Tooltip("km:Q", title="Distancia (km)", format=".1f"),
            alt.Tooltip("speed_kmh:Q", title="Velocidad (km/h)", format=".1f"),
        ],
    ).properties(height=300)
    st.altair_chart(alt_chart_speed, use_container_width=True)

    # Pendiente (%)
    st.markdown("#### ↗️ Pendiente (%)")

    alt_chart_grade = alt.Chart(chart_df).mark_line(color=color_hex, size=line_width).encode(
        x=alt.X('km:Q', title='Distancia (km)'),
        y=alt.Y('grade_pct:Q',
                title='Pendiente (%)'),
        tooltip=[
            alt.Tooltip("km:Q", title="Distancia (km)", format=".1f"),
            alt.Tooltip("grade_pct:Q", title="Pendiente (%)", format=".0f"),
        ],
    ).properties(height=300)
    st.altair_chart(alt_chart_grade, use_container_width=True)

    # HR (si existe)
    if show_hr and chart_df['hr'].notnull().any():
        st.markdown("#### ❤️‍ Frecuencia Cardiaca")
        # Línea HR
        hr_df = chart_df.dropna(subset=['hr'])
        alt_chart_hr = alt.Chart(hr_df).mark_line(color=color_hex, size=line_width).encode(
            x=alt.X('km:Q', title='Distancia (km)'),
            y=alt.Y('hr:Q', title='Frecuencia Cardiaca (bpm)'),
            tooltip=[
                alt.Tooltip("km:Q", title="Distancia (km)", format=".1f"),
                alt.Tooltip("hr:Q", title="Frecuencia Cardiaca", format=".0f"),
            ],
        ).properties(height=300)

        # Zonas HR (tiempo en movimiento)
        hr_zones_df = df_proc[['hr','dt','moving']].dropna(subset=['hr']).copy()
        hr_zones_df = hr_zones_df[(hr_zones_df['dt'] > 0) & (hr_zones_df['moving'])]
        pie = None

        if not hr_zones_df.empty:

            bins = [-npy.inf, 100, 133, 149, 165, npy.inf]
            palette = ["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"]
            labels = ["<100", "100–133", "133–149", "149–165", ">165"]

            hr_zones_df['zona'] = pd.cut(hr_zones_df['hr'], bins=bins, labels=labels, right=False)
            zones = hr_zones_df.groupby('zona', observed=True)['dt'].sum().reindex(labels, fill_value=0)
            zones_df = zones.reset_index().rename(columns={'dt': 'segundos'})
            total_s = zones_df['segundos'].sum()
            zones_df['porcentaje'] = npy.where(total_s > 0, 100 * zones_df['segundos'] / total_s, 0)

            # (opcional) fuerza el orden de los sectores en el dibujo:
            order_map = {lab: i for i, lab in enumerate(labels)}
            zones_df["orden"] = zones_df["zona"].map(order_map).astype(int)

            pie = (
                alt.Chart(zones_df)
                .mark_arc(stroke="white", strokeWidth=1)
                .encode(
                    theta=alt.Theta("segundos:Q", stack=True),
                    color=alt.Color(
                        "zona:N",
                        title="Zona HR",
                        scale=alt.Scale(domain=labels, range=palette),  # fija colores y orden de leyenda
                    ),
                    order=alt.Order("orden:Q"),  # <- opcional (garantiza orden de sectores)
                    tooltip=[
                        alt.Tooltip("zona:N", title="Zona"),
                        alt.Tooltip("segundos:Q", title="Segundos", format=".0f"),
                        alt.Tooltip("porcentaje:Q", title="%", format=".1f"),
                    ],
                )
                .properties(height=260)
            )

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Frecuencia cardiaca")
            st.altair_chart(alt_chart_hr, use_container_width=True)
        with c2:
            st.markdown("##### Zonas de frecuencia cardiaca (tiempo en movimiento)")
            if pie is not None:
                st.altair_chart(pie, use_container_width=True)
            else:
                st.info("No hay datos de HR suficientes para calcular zonas.")

    # Cadencia (si existe)
    if show_cad and chart_df['cad'].notnull().any():
        st.markdown("#### ⚙️ Cadencia")

        alt_chart_cad = alt.Chart(chart_df.dropna(subset=['cad'])).mark_line(color=color_hex, size=line_width).encode(
            x='km:Q', y=alt.Y('cad:Q', title='Cadencia (rpm)'), tooltip=['km','cad']
        ).properties(height=220)

        st.altair_chart(alt_chart_cad, use_container_width=True)

# ============================================================================================
# TAB:GUÍA
# ============================================================================================

with tab_guide:

    st.subheader("Guía de uso")
    # Construir ruta absoluta al fichero GUIA.md que está junto a gpxra.py
    guia_path = os.path.join(os.path.dirname(__file__), "GUIA.md")

    try:
        with open(guia_path, "r", encoding="utf-8") as f:
            guia_md = f.read()
        if guia_md.strip():
            st.markdown(guia_md)
        else:
            st.info(f"El fichero `{guia_path}` está vacío. Añade contenido Markdown y actualiza la página.")
    except FileNotFoundError:
        st.warning(f"No se encontró `{guia_path}`. Crea ese fichero Markdown en tu proyecto o cambia la ruta en Ajustes.")
    except Exception as e:
        st.error(f"No se pudo leer la guía: {e}")
