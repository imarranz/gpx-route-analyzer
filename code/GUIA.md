# GPX Route Analyzer — Guía de uso

Bienvenido/a. Esta aplicación te permite **cargar archivos GPX** y obtener **métricas**, **mapas** y **gráficas** interactivas para ciclismo, running o senderismo.

> **Consejo**: El contenido de esta guía está en el fichero `GUIA.md`. Puedes editarlo libremente y los cambios se verán en la pestaña **Guía** sin tocar el código.

---

## 1. Requisitos e instalación

1. Crea el entorno (ejemplo con conda):

   ```bash
   conda create -n gpx python=3.11 streamlit pandas numpy gpxpy altair folium -c conda-forge
   conda activate gpx
   pip install streamlit-folium
   ```
2. Ejecuta la aplicación desde la carpeta del proyecto:

   ```bash
   streamlit run app.py
   ```

---

## 2. Cargar archivos GPX

* En la parte principal, usa **“Sube tus .gpx”** para arrastrar/seleccionar uno o varios ficheros.
* Si subes varios, selecciona la actividad en el desplegable **“Selecciona una actividad”**.
* El GPX debería contener puntos con **lat/lon/tiempo**; si incluye **HR** (frecuencia cardiaca) y **cadencia**, también se mostrarán.

---

## 3. Ajustes (barra lateral)

* **Umbral de movimiento (m/s)**: puntos por debajo se consideran parados.
* **Representación en mapa**:

  * *Línea*; *Puntos por velocidad*; *Puntos por altitud*.
* **Rango de color**:

  * *Min–Max* (todo el rango) o *robusto* (usa P2–P98 y satura outliers).
* **Máximo de puntos a dibujar**: muestreo para no sobrecargar el navegador.
* **Radio de los puntos (px)**: tamaño de marcadores en modo puntos.
* **Mostrar HR / cadencia**: activa/desactiva series si existen.
* **Color de las gráficas**: selector para todas las series.
* **Suavizado pendiente (puntos)**: ventana de mediana para el % de pendiente.
* **Clip pendiente ± (%)**: limita picos irreales de pendiente.
* **Grosor de línea (px)**: tamaño de las líneas en las gráficas.

---

## 4. Pestañas

### 4.1. Resumen

* **Métricas** en cuadrícula: fecha, hora inicio/fin, distancia, tiempo total y en movimiento, velocidad media (mov.) y máxima.
* **Tabla resumen**: misma info tabulada.
* **Parciales (cada 5 km)**: distancia/tpo en movimiento, desnivel + y ritmo min/km.

### 4.2. Mapa

* Vista interactiva con *Folium*.
* Modos: **línea** o **puntos coloreados** por velocidad/altitud.
* **Leyenda** con escala de color dinámica (Min–Max o P2–P98).
* Tooltips por punto (hora • velocidad • altitud).

### 4.3. Estadísticas

* **Altitud** (área + línea), **Velocidad**, **Pendiente (%)**.
* **Frecuencia cardiaca** y **Cadencia** (si existen).
* (Opcional) Zonas de HR en **gráfico de “quesito”** por tiempo en movimiento.

### 4.4. Guía

* Muestra este documento `GUIA.md`.

---

## 5. Exportación y datos

* Puedes **descargar CSV** con los puntos procesados y métricas por punto (si el botón está habilitado en la sección Resumen).
* La **velocidad** se calcula como `d_dist / dt` con división segura (0 cuando `dt<=0`).
* La **pendiente** se calcula como `100 * Δaltitud / Δdistancia` con suavizado configurable y *clip*.

---

## 6. Consejos y resolución de problemas

* **Tiempos/fechas**: se muestran tal y como vienen en el GPX. Si tu dispositivo guarda en UTC, verás UTC. (Se puede añadir conversión a zona horaria si la necesitas.)
* **HR/Cadencia**: solo aparecen si el GPX contiene esas extensiones (p. ej. dispositivos Garmin/TCX compatibles).
* **Picos espurios**: usa el **rango robusto (P2–P98)** y el **clip de pendiente** para minimizar su efecto visual.
* **Rendimiento**: si la ruta es muy larga, reduce **máximo de puntos** o usa **modo línea**.
* **Estilo**: puedes cambiar el **color** de todas las gráficas y el **grosor** desde Ajustes.
* **Favicon/logo**: se puede cambiar con `st.set_page_config(page_icon="🚴")` o un PNG local.

---

## 7. Créditos y licencia

* Autor: **Ibon Martínez-Arranz**
* Repositorio: `https://github.com/imarranz/gpx-route-analyzer`
* Licencia: MIT License

---

## 8. Roadmap (ideas futuras)

* Línea coloreada por velocidad/altitud (segmentando el track).
* Detección automática de **puertos** (pendiente/duración) y “auto-laps”.
* Comparador de rutas y “replay”.
* Posibilidad de exportar a **PDF** con métricas y figuras.
