import pandas as pd
import numpy as npy
from datetime import datetime, timezone
import gpxpy
import gpxpy.gpx
from .geo import haversine

def parse_gpx(file) -> pd.DataFrame:
    """
    Parsea un fichero GPX (pistas) y devuelve un DataFrame “ordenado” de puntos
    con métricas básicas por punto.

    Parámetros
    ----------
    file : IO[str] | IO[bytes] | streamlit.UploadedFile
        Objeto tipo fichero con el contenido GPX. Puede ser texto o bytes.
        Si es bytes, se decodifica como UTF-8 (errores ignorados) antes de parsear.

    Devuelve
    --------
    pandas.DataFrame
        DataFrame con una fila por punto de track y las columnas:
        - time   : datetime64[ns, UTC] – marca temporal del punto (si existe).
        - lat    : float – latitud en grados decimales.
        - lon    : float – longitud en grados decimales.
        - ele    : float – altitud en metros (se completa con ffill/bfill para evitar NaN).
        - hr     : float – frecuencia cardiaca en bpm (si está en extensiones), NaN si no.
        - cad    : float – cadencia en rpm (si está en extensiones), NaN si no.
        - dist   : float – distancia acumulada en metros a lo largo del track.
        - d_dist : float – distancia incremental (m) entre este punto y el anterior.
        - dt     : float – tiempo incremental (s) entre este punto y el anterior.
        - speed  : float – velocidad instantánea (m/s), división segura (0 si dt ≤ 0).

    Notas
    -----
    - Solo procesa puntos de pista `<trk>/<trkseg>/<trkpt>`; no analiza rutas (`<rte>`)
    ni waypoints (`<wpt>`).
    - `hr` y `cad` se intentan extraer de extensiones XML habituales (p.ej. Garmin/TCX);
    pueden no estar presentes.
    - La distancia incremental se calcula con la fórmula de haversine (Tierra esférica,
    R = 6_371_000 m). Para precisión geodésica mayor, usar métodos elipsoidales.
    - El resultado se ordena por `time` y se eliminan duplicados por (`time`, `lat`, `lon`).
    - `speed` se calcula con `npy.divide(..., where=dt>0)` para evitar avisos de división
    por cero y se sanea con `npy.nan_to_num`.

    Excepciones
    -----------
    ValueError, gpxpy.common.GPXException
        Pueden propagarse desde `gpxpy.parse` si el contenido GPX es inválido.

    Ejemplos
    --------
    >>> with open("ruta.gpx", "rb") as f:
    ...     df = parse_gpx(f)
    >>> df[["time", "lat", "lon", "ele", "speed"]].head()  # doctest: +SKIP
    """

    content = file.read()
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="ignore")
    gpx = gpxpy.parse(content)

    records = []
    for track in gpx.tracks:
        for segment in track.segments:
            for p in segment.points:
                hr = None
                cad = None
                try:
                    if p.extensions:
                        for ext in p.extensions:
                            for child in ext.iter():
                                tag = child.tag.lower()
                                if tag.endswith('heartrate') or tag.endswith('hr'):
                                    try:
                                        hr = int(child.text)
                                    except Exception:
                                        pass
                                if tag.endswith('cadence') or tag.endswith('cad'):
                                    try:
                                        cad = int(child.text)
                                    except Exception:
                                        pass
                except Exception:
                    pass
                records.append({
                    'time': p.time.replace(tzinfo=timezone.utc) if isinstance(p.time, datetime) else None,
                    'lat': p.latitude,
                    'lon': p.longitude,
                    'ele': p.elevation,
                    'hr': hr,
                    'cad': cad,
                })
    df = pd.DataFrame.from_records(records)

    if df.empty:
        return df

    df = df.sort_values('time').drop_duplicates(subset=['time', 'lat', 'lon']).reset_index(drop=True)
    lat, lon = df['lat'].values, df['lon'].values
    ele = df['ele'].ffill().bfill().values
    d, d_dist, dt = npy.zeros(len(df)), npy.zeros(len(df)), npy.zeros(len(df))

    for i in range(1, len(df)):
        dxy = haversine(lat[i-1], lon[i-1], lat[i], lon[i])
        d_dist[i] = dxy
        d[i] = d[i-1] + dxy
        if pd.notnull(df.loc[i, 'time']) and pd.notnull(df.loc[i-1, 'time']):
            dt[i] = (df.loc[i, 'time'] - df.loc[i-1, 'time']).total_seconds()

    #speed = npy.nan_to_num(d_dist / dt, nan=0.0, posinf=0.0, neginf=0.0)
    speed = npy.divide(d_dist, dt, out=npy.zeros_like(d_dist), where=dt>0)
    speed = npy.nan_to_num(speed, nan=0.0, posinf=0.0, neginf=0.0)

    df['ele'] = ele
    df['dist'], df['d_dist'], df['dt'], df['speed'] = d, d_dist, dt, speed

    return df
