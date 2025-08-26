# ============================================================================================
# MAPS.PY
# ============================================================================================

# ============================================================================================
# LIBRERÍAS
# ============================================================================================

# gpxra/map_utils.py
from __future__ import annotations
import folium
from folium import ColorLine
from folium.plugins import MiniMap, Fullscreen, MeasureControl, Draw, PolyLineTextPath
from branca.colormap import LinearColormap
import numpy as npy
import pandas as pd

# ============================================================================================
# CONFIGURACIÓN
# ============================================================================================

# En esta dirección podemos encontrar diferentes maps que pueden ir anadiendose al diccionario
# Fuente: https://leaflet-extras.github.io/leaflet-providers/preview/
TILE_SOURCES = {
    "OpenStreetMap": "OpenStreetMap",
    "Carto Light": "CartoDB Positron",
    "Carto Dark": "CartoDB Dark_Matter",
    #"Stamen Terrain": "Stamen Terrain",
    #"Stamen Toner": "Stamen Toner",
    "OpenTopoMap": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    "Prueba": "ESRI World Shaded Relief",
    "Satélite (Esri)": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
}

# ============================================================================================
# FUNCIONES
# ============================================================================================

# BUILD_MAP ==================================================================================

def build_map(center, base_key: str, show_minimap: bool = True, show_measure: bool = True):
    """Crea un folium.Map con la capa base y controles opcionales."""
    m = folium.Map(location=center, zoom_start=13, control_scale=True, tiles=None)
    tl = TILE_SOURCES.get(base_key, "OpenStreetMap")

    if isinstance(tl, str) and tl.startswith("http"):
        folium.TileLayer(tiles=tl, name=base_key, attr="Esri").add_to(m)
    else:
        folium.TileLayer(tl, name=base_key).add_to(m)
    if show_minimap:
        MiniMap(toggle_display=True).add_to(m)
    Fullscreen().add_to(m)
    if show_measure:
        MeasureControl(primary_length_unit="kilometers").add_to(m)
    Draw(export=True).add_to(m)

    return m

# PREPARE_COORDS =============================================================================

def prepare_coords(df_proc: pd.DataFrame, max_points: int) -> pd.DataFrame:
    """Submuestrea puntos y añade speed_kmh para pintar en el mapa."""
    coords_df = df_proc[['lat','lon','ele','speed','dist','time']].dropna(subset=['lat','lon']).copy()
    coords_df['speed_kmh'] = coords_df['speed'] * 3.6
    n = len(coords_df)
    if n == 0:
        return coords_df
    step = max(1, n // max_points)
    return coords_df.iloc[::step]

# _ROBUST_MIN_MAX ============================================================================

def _robust_min_max(values: pd.Series, mode: str):
    robust = "robusto" in mode.lower()
    if robust:
        vmin, vmax = npy.percentile(values.dropna(), [2, 98])
    else:
        vmin, vmax = float(values.min()), float(values.max())
    return float(vmin), float(vmax)

# DRAW_ROUTE =================================================================================

def draw_route(m, coords_df: pd.DataFrame, map_mode: str, color_range_mode: str, point_radius: int, color_hex: str):
    """Dibuja línea única o puntos coloreados por velocidad/altitud."""
    if coords_df.empty:
        return

    # Decide nombre legible para la capa de ruta
    if map_mode == "Posición":
        route_name = "Ruta (posición)"
    if map_mode == "Velocidad":
        route_name = "Ruta (velocidad)"
    if map_mode == "Altitud":  # "Por altitud"
        route_name = "Ruta (altitud)"

    # Capa de la ruta con nombre (esto evita 'macro_element_div_*')
    route_layer = folium.FeatureGroup(name=route_name, show=True)

    # Helper para rango robusto
    #
    def _robust_min_max(values: pd.Series):
        if "robusto" in color_range_mode.lower():
            vmin, vmax = npy.percentile(values.dropna(), [2, 98])
        else:
            vmin, vmax = float(values.min()), float(values.max())
        return float(vmin), float(vmax)

    # Línea no coloreada, sólo representa la posición de la ruta
    if map_mode == "Posición":
        coords = coords_df[['lat','lon']].values.tolist()
        if len(coords) > 1:
            folium.PolyLine(coords, weight=5, opacity=0.9, color=color_hex).add_to(route_layer)
            route_layer.add_to(m)
        return

    # Línea coloreada por velocidad
    if map_mode == "Velocidad":
        values = coords_df['speed_kmh']
        vmin, vmax = _robust_min_max(values)
        cmap = LinearColormap(
            ["#313695","#4575b4","#74add1","#abd9e9","#e0f3f8",
             "#ffffbf",
             "#fee090","#fdae61","#f46d43","#d73027","#a50026"],
            vmin=vmin, vmax=vmax
        )
        cmap.caption = "Velocidad (km/h)"

    # Línea coloreada por altitud
    if map_mode == "Altitud":
        values = coords_df['ele']
        vmin, vmax = _robust_min_max(values)
        cmap = LinearColormap(
            ["#313695","#4575b4","#74add1","#abd9e9","#e0f3f8",
             "#ffffbf",
             "#fee090","#fdae61","#f46d43","#d73027","#a50026"],
            vmin=vmin, vmax=vmax
        )
        cmap.caption = "Altitud (m)"

    m.add_child(cmap)
    positions = coords_df[['lat','lon']].values.tolist()
    scalars = npy.clip(values.astype(float).values, vmin, vmax).tolist()

    if len(positions) > 1:
        ColorLine(
            positions=positions,
            colors=scalars,
            colormap=cmap,
            nb_steps=12,
            weight=5,
            opacity=0.95
        ).add_to(route_layer)

    # ¡Añadir la capa de ruta al mapa!
    route_layer.add_to(m)

# --- Capas opcionales ---

# CREATE_LAYERS ==============================================================================

def create_layers(m, enabled: bool = True):
    """
    Crea y añade capas (FeatureGroup) al mapa si `enabled=True`.
    Devuelve un dict con las capas o {} si está desactivado.
    """
    if not enabled:
        return {}
    layers = {
        "start_end"   : folium.FeatureGroup(name="Inicio/fin",   show=True),
        "altitude"    : folium.FeatureGroup(name="Altitud",      show=True),
        "performance" : folium.FeatureGroup(name="Rendimiento",  show=True),
        "stops"       : folium.FeatureGroup(name="Paradas",      show=True),
        "kilometers"  : folium.FeatureGroup(name="Kilometros",   show=True),

    }
    for g in layers.values():
        g.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return layers

# _ADD_MARKER ================================================================================

def _add_marker(target, row, tooltip, color, icon):
    folium.Marker(
        location=[row['lat'], row['lon']],
        tooltip=tooltip,
        icon=folium.Icon(color=color, icon=icon, prefix='fa')
    ).add_to(target)

# ADD_START_END_MARKERS ======================================================================

def add_start_end_markers(m, coords_df: pd.DataFrame, layer=None):
    if coords_df.empty:
        return
    start = coords_df.iloc[0]; end = coords_df.iloc[-1]
    target = layer if layer is not None else m
    _add_marker(target, start, f"Inicio: {start['time']}", "green", "play")
    _add_marker(target, end, f"Fin: {end['time']}", "red", "flag-checkered")

# ADD_KM_MARKERS =============================================================================

def add_km_markers(
    m,
    df_proc: pd.DataFrame,
    every_km: int = 5,
    layer=None,
    show_km_labels: bool = True,
    show_arrows: bool = True,
    arrow_char: str = "▶",
    arrow_color: str = "#1f77b4",   # o tu color_hex
    arrow_size_px: int = 18,
    arrow_offset_px: int = 8,
    arrow_spacing: int = 3,         # nº de espacios entre flechas
):
    """
    Esta función coloca marcas cada N km y/o flechas en el sentido de marcha sobre la ruta.
    - Si `layer` es None, añade al mapa directamente.
    - Si `show_arrows=True`, dibuja flechas siguiendo la polilínea de la ruta.
    """
    target = layer if layer is not None else m

    # 1) Hitos cada N km (opcional)
    if show_km_labels and every_km > 0:
        df = df_proc.copy()
        if 'km' not in df.columns:
            df['km'] = df['dist'] / 1000.0
        kms = np.arange(every_km, np.floor(df['km'].max()) + 1, every_km)
        for k in kms:
            i = (df['km'] - k).abs().idxmin()
            row = df.loc[i]
            folium.Marker(
                [row['lat'], row['lon']],
                tooltip=f"Km {int(k)}",
                icon=folium.DivIcon(
                    html=f"<div style='font-weight:700;color:#333;background:rgba(255,255,255,.8);"
                         f"padding:2px 4px;border-radius:4px;border:1px solid #999;'>"
                         f"{int(k)}</div>"
                )
            ).add_to(target)

    # 2) Flechas siguiendo la ruta (opcional)
    if show_arrows:
        coords = df_proc[['lat','lon']].dropna().values.tolist()
        if len(coords) >= 2:
            # Polilínea “invisible” para apoyar el texto (flechas)
            poly = folium.PolyLine(coords, weight=0, opacity=0).add_to(target)
            # controla la separación con espacios
            text = arrow_char + (" " * arrow_spacing)
            PolyLineTextPath(
                poly,
                text,
                repeat=True,               # repetir a lo largo de toda la línea
                offset=arrow_offset_px,    # desplaza ligeramente desde el inicio
                attributes={
                    "fill": arrow_color,
                    "font-size": f"{arrow_size_px}px",
                    "font-weight": "bold",
                    "opacity": "0.85",
                }
            ).add_to(target)

# ADD_KEY_POINT_MARKERS ======================================================================

def add_key_point_markers(
    m, df_proc: pd.DataFrame, grade_window: int = 9, min_stop_seconds: int = 60,
    format_time_fn=None, layers: dict | None = None
):
    df_full = df_proc.dropna(subset=['lat','lon']).copy()
    # Elegir destino por capa si existen; si no, el propio mapa
    L_alt  = layers.get("altitude")    if layers else m
    L_perf = layers.get("performance") if layers else m
    L_stop = layers.get("stops")       if layers else m
    L_km   = layers.get("kilometers")  if layers else m

    add_km_markers(m, df_proc, every_km=5, layer=L_km, show_km_labels=False, show_arrows=True, arrow_color="000000", arrow_spacing=20)

    # Altitud max/min
    if 'ele' in df_full and df_full['ele'].notna().any():
        r_max_e = df_full.loc[df_full['ele'].idxmax()]
        r_min_e = df_full.loc[df_full['ele'].idxmin()]
        _add_marker(L_alt,  r_max_e, f"Mayor altitud: {r_max_e['ele']:.0f} m · {r_max_e['time']}", "darkpurple", "arrow-up")
        _add_marker(L_alt,  r_min_e, f"Menor altitud: {r_min_e['ele']:.0f} m · {r_min_e['time']}", "cadetblue",  "arrow-down")

    # Velocidad máx
    if 'speed' in df_full and df_full['speed'].notna().any():
        r_max_v = df_full.loc[df_full['speed'].idxmax()]
        _add_marker(L_perf, r_max_v, f"Velocidad máx.: {r_max_v['speed']*3.6:.1f} km/h · {r_max_v['time']}", "orange", "bolt")

    # Pendiente máx/min (suavizada)
    if {'ele','d_dist'}.issubset(df_full.columns):
        grade_raw = 100.0 * df_full['ele'].diff() / df_full['d_dist'].replace(0, npy.nan)
        win = max(1, int(grade_window))
        grade_pct = grade_raw.rolling(window=win, min_periods=1, center=True).median().fillna(0)
        df_full['grade_pct'] = grade_pct
        if df_full['grade_pct'].notna().any():
            r_max_g = df_full.loc[df_full['grade_pct'].idxmax()]
            r_min_g = df_full.loc[df_full['grade_pct'].idxmin()]
            _add_marker(L_perf, r_max_g, f"Pendiente máx.: {r_max_g['grade_pct']:.1f}% · {r_max_g['time']}", "red",  "arrow-up")
            _add_marker(L_perf, r_min_g, f"Pendiente mín.: {r_min_g['grade_pct']:.1f}% · {r_min_g['time']}", "blue", "arrow-down")

    # Pausas ≥ umbral
    if {'moving','dt'}.issubset(df_full.columns) and df_full['dt'].notna().any():
        # Analizamos todas las paradas en la ruta
        tmp = df_full[['time','lat','lon','dt','moving']].copy()
        tmp['is_stop'] = ~tmp['moving']
        tmp['grp'] = (tmp['is_stop'] != tmp['is_stop'].shift()).cumsum()
        stops = tmp[tmp['is_stop']].groupby('grp').agg(dur_s=('dt','sum'))
        # Seleccionamos aquellas paradas con un tiempo superior a min_stop_seconds segundos
        # Por defecto son 60 segundos (1 minuto) aquellas paradas que se representarán en el mapa
        stops = stops[stops['dur_s'] >= int(min_stop_seconds)]
        # Anadimos un marcador por cada parada
        for gid, row_s in stops.iterrows():
            seg = tmp[tmp['grp'] == gid]
            mid_idx = seg.index[len(seg)//2]
            r_stop = df_full.loc[mid_idx]
            t0 = seg['time'].iloc[0].strftime("%H:%M:%S")
            t1 = seg['time'].iloc[-1].strftime("%H:%M:%S")
            dur_txt = format_time_fn(float(row_s['dur_s'])) if format_time_fn else f"{row_s['dur_s']:.0f}s"
            _add_marker(L_stop, r_stop, f"Pausa {dur_txt} · {t0}–{t1}", "gray", "pause")
