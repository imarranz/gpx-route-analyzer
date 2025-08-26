 
# GPX Route Analyzer

> Visualiza y analiza archivos **GPX** de ciclismo (y también running/senderismo) con **Streamlit**, **Folium** y **Altair**. Mapas interactivos, métricas automáticas, parciales configurables y gráficas bonitas — todo en tu navegador.

<p align="center">
  <img src="docs/banner_1280x640.png" alt="GPX Route Analyzer banner" width="100%" />
</p>

---

## ✨ Características

* **Carga múltiple de GPX** y selección de actividad.
* **Métricas automáticas**: fecha/hora, distancia, tiempo total y en movimiento, velocidad media (mov.), velocidad máxima.
* **Parciales configurables** (1–10 km) con tabla estilizada y barras por columna.
* **Mapas interactivos** (Folium):

  * Modos: **Posición (línea)**, **Por velocidad** (gradiente) y **Por altitud** (gradiente).
  * **Capas opcionales** con *LayerControl* (Inicio/Fin, Altitud, Rendimiento, Paradas).
  * **Marcadores automáticos**: altitud máx/min, velocidad máx, pendiente máx/mín (suavizada), **pausas ≥ N s**.
  * **Flechas del sentido de marcha** y **hitos cada N km** (opcionales).

* **Gráficas Altair**: Altitud (área), Velocidad, Pendiente, HR y Cadencia (si existen), **dispersión Velocidad–Altitud** con correlación.
* **Colores y estilos**: selector de color para todas las gráficas, grosor de línea, rango de color robusto (P2–P98) para evitar outliers.
* **Descargar datos**: botón para **descargar CSV** de los puntos procesados y **CSV de parciales**.
* **Guía integrada**: pestaña **Guía** renderiza el fichero `GUIA.md`.

---

## 🖥️ Demo rápida

```bash
streamlit run gpxra.py
```

Abre el navegador (normalmente en `http://localhost:8501`), sube uno o más `.gpx` y explora las pestañas **Resumen**, **Mapa**, **Estadísticas** y **Guía**.

---

## 📦 Instalación

### conda (recomendada)

```bash
conda create -n gpx python=3.11 streamlit pandas numpy gpxpy altair folium -c conda-forge
conda activate gpx
pip install streamlit-folium
```

> **Nota sobre Folium/ColorLine**: según la versión, `ColorLine` puede importarse de `folium` o de `folium.plugins`. El proyecto incluye un import robusto. Si tu versión carece de `ColorLine`, se usa un **fallback** que colorea la línea por segmentos.

---

## 🧭 Uso

1. **Sube tus archivos GPX** (arrastrar/soltar o selector).
2. Si hay varios, elige la actividad en **“Selecciona una actividad”**.
3. Ajusta los **controles de la barra lateral** (umbral de movimiento, modo de mapa, color, etc.).
4. Consulta:

   * **Resumen**: métricas, tablas y **parciales** (con slider para el tamaño del split).
   * **Mapa**: línea o línea coloreada por **velocidad/altitud**, capas y marcadores.
   * **Estadísticas**: series temporales, scatter, zonas HR y más.
   * **Guía**: contenido de `GUIA.md` (editable sin tocar código).

---

## 🔧 Ajustes clave (barra lateral)

* **Umbral de movimiento (m/s)**: velocidades por debajo se consideran parada.
* **Representación en mapa**: `Posición (línea)` · `Por velocidad` · `Por altitud`.
* **Rango de color**: `Min–Max` o `Min–Max (robusto)` (usa P2–P98; satura outliers).
* **Máximo de puntos a dibujar**: submuestreo para rendimiento.
* **Color de las gráficas** y **grosor**.
* **Suavizado de pendiente** (ventana mediana) y **clip ±%**.
* **Capas en el mapa** (checkbox): activa grupos encendibles/apagables.
* **Pausas ≥ N s** (configurable) para mostrar marcadores de paradas.

---

## 🗺️ Mapa y capas

* **Capas disponibles** (cuando el checkbox está activo):

  * `Ruta (posición/velocidad/altitud)`
  * `Inicio/fin`
  * `Altitud` (puntos de alt máx/mín)
  * `Rendimiento` (velocidad máx, pendiente máx/mín)
  * `Paradas` (pausas ≥ N s)
* **Flechas del sentido de marcha**: `PolyLineTextPath` sobre la ruta.
* **Hitos cada N km**: marcadores con `DivIcon` numerado.
* **Mapas base**: OpenStreetMap, Carto Light/Dark, Satélite (Esri). Puedes añadir otros (OpenTopoMap, hillshade, etc.).

---

## 📊 Estadísticas

* **Altitud (área)**, **Velocidad**, **Pendiente (%)** con eje de distancia.
* **Frecuencia cardiaca** y **Cadencia** (si existen).
* **Zonas de HR**: <100, 100–133, 133–149, 149–165, >165.
* **Parciales**: distancia en movimiento, tiempo en movimiento, desnivel +, ritmo (min/km).

---

## 🧱 Estructura del proyecto

```
├─ gpxra.py                # Aplicación Streamlit (UI)
├─ GUIA.md                 # Guía visible en la pestaña "Guía"
├─ gpxra/                  # Paquete con utilidades
│  ├─ __init__.py
│  ├─ geo.py               # haversine(), etc.
│  ├─ io.py                # parse_gpx(), lectura y normalización
│  ├─ metrics.py           # compute_metrics(), parciales, etc.
│  ├─ formatting.py        # format_time(), helpers de formato
│  ├─ maps.py              # build_map(), draw_route(), capas/markers
│  └─ ...
├─ requirements.txt        # (opcional) dependencias
├─ docs/
│  └─ banner_1280x640.png  # imagen para el README (opcional)
├─ README.md
└─ LICENSE
```

---

## 🧪 API de utilidades (resumen)

* `haversine(lat1, lon1, lat2, lon2) -> float`: distancia en metros.
* `parse_gpx(file) -> pd.DataFrame`: puntos ordenados (time, lat, lon, ele, hr, cad, dist, d\_dist, dt, speed).
* `compute_metrics(df, moving_speed_threshold=0.5) -> (metrics, df_proc, splits)`: métricas globales y parciales (por defecto, 5 km).
* `format_time(seconds) -> str`: "Hh Mm Ss" o "Mm Ss".
* `build_map(center, base, ...) -> folium.Map`: mapa con tiles y controles.
* `draw_route(m, coords_df, map_mode, color_range_mode, ...)`: línea simple o coloreada por velocidad/altitud (ColorLine o fallback por segmentos).
* `add_start_end_markers(m, coords_df, layer=None)`: inicio/fin.
* `add_key_point_markers(m, df_proc, grade_window, min_stop_seconds, ...)`: alt máx/mín, vel máx, pendiente máx/mín, pausas ≥ N s.

---

## 💾 Exportar

* **Datos por punto**: botón de **CSV** (resume lat/lon, ele, speed, hr, cad, etc.).
* **Parciales**: **CSV** con el tamaño de split elegido (1–10 km).
* (Futuro) **PDF** con resumen, mapa y figuras.

---

## 🤝 Contribuir

¡Las PRs son bienvenidas! Ideas útiles:

* Detección de **puertos** y laps automáticos.
* Comparador de rutas / ghost racer.
* Exportación a **PDF** y **PNG** de gráficas.
* Soporte de **potencia** (watts) cuando el GPX/TCX lo incluya.

Pasos:

1. Haz un fork y crea una rama (`feat/mi-idea`).
2. Asegura estilo y tipados (opcional): `ruff`, `black`, `mypy`.
3. Añade ejemplos/GPX de prueba si hace falta.
4. Abre tu PR con una descripción clara.

---

## 📜 Licencia

Este proyecto se publica bajo licencia **MIT**. Consulta el fichero `LICENSE`.

---

## 🗺️ Roadmap

* Exportación **PDF** (1 hoja: resumen + mapa + figuras).
* Detección de **climbs/puertos** (pendiente y duración) y resaltado en mapa.
* Comparativa entre actividades y “replay”.
* Más mapas base: OpenTopoMap / Hillshade.
* Guardar y restaurar **ajustes** de usuario.

---

## 🙌 Créditos

* Autor: **Ibon Martínez-Arranz**.
* Icono/emoji: 🚴.
* Agradecimientos a la comunidad de **Streamlit**, **Folium** y **Altair**.
