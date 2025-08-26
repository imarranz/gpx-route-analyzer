# ============================================================================================
# METRICS.PY
# ============================================================================================

# ============================================================================================
# LIBRERÍAS
# ============================================================================================

import pandas as pd
import numpy as npy

# ============================================================================================
# FUNCIONES
# ============================================================================================

# MAKE_SPLITS ================================================================================

def make_splits(df_proc: pd.DataFrame, split_km: int) -> pd.DataFrame:
    df = df_proc.copy()
    if 'km' not in df.columns:
        df['km'] = df['dist'] / 1000.0
    # índice de split según el tamaño elegido
    df['split'] = npy.floor(df['km'] / split_km).astype(int)
    # agregados por split, considerando solo puntos en movimiento para dist/tiempo
    agg = (
        df.groupby('split', as_index=False)
          .agg(dist_moving=('d_dist', lambda s: s[df.loc[s.index, 'moving']].sum()),
               time_moving=('dt',    lambda s: s[df.loc[s.index, 'moving']].sum()),
               elev_gain=('ele',     lambda s: s.diff().clip(lower=0).sum()))
    )
    if not agg.empty:
        agg['km_inicio'] = agg['split'] * split_km
        agg['ritmo_min_km'] = npy.where(
            agg['dist_moving'] > 0,
            (agg['time_moving'] / (agg['dist_moving']/1000.0)) / 60.0,
            npy.nan
        )
    return agg

# COMPUTE_METRICS ============================================================================

def compute_metrics(df: pd.DataFrame, moving_speed_threshold=0.5):
    """
    Calcula métricas agregadas de la actividad y genera columnas auxiliares y
    splits cada 5 km.

    Parámetros
    ----------
    df : pandas.DataFrame
        DataFrame de puntos del track con, al menos, las columnas:
        - 'time' : datetime64[ns] (idealmente con tz UTC)
        - 'dist' : float, distancia acumulada (m)
        - 'd_dist' : float, distancia incremental entre puntos (m)
        - 'dt' : float, tiempo incremental entre puntos (s)
        - 'speed' : float, velocidad instantánea (m/s)
        - 'ele' : float, altitud (m)
    moving_speed_threshold : float, opcional
        Umbral de velocidad (m/s) para considerar un punto "en movimiento".
        Por defecto 0.5 m/s (~1.8 km/h).

    Devuelve
    --------
    metrics : dict
        Diccionario con métricas globales:
        - 'date' : date, fecha de la actividad (inicio)
        - 'start_time' : time, hora de inicio
        - 'end_time' : time, hora de fin
        - 'distance_km' : float, distancia en movimiento (km)
        - 'elapsed_time_s' : float, tiempo total transcurrido (s)
        - 'moving_time_s' : float, tiempo en movimiento (s)
        - 'avg_moving_speed_kmh' : float, velocidad media en movimiento (km/h)
        - 'max_speed_kmh' : float, velocidad máxima (km/h)
    df_proc : pandas.DataFrame
        Copia de `df` con columnas añadidas:
        - 'moving' : bool, True si speed > umbral
        - 'km' : float, distancia acumulada en km
        - 'split' : int, índice de split cada 5 km (0, 1, 2, …)
    splits : pandas.DataFrame
        Resumen por splits de 5 km con columnas:
        - 'split' : int
        - 'dist_moving' : float, distancia en movimiento (m)
        - 'time_moving' : float, tiempo en movimiento (s)
        - 'elev_gain' : float, desnivel positivo (m)
        - 'km_inicio' : float, inicio del split (km)
        - 'ritmo_min_km' : float, ritmo en movimiento (min/km)

    Notas
    -----
    - `elapsed_time_s` se calcula como (último time − primer time), independientemente
    del movimiento.
    - Distancia, tiempo en movimiento y medias se calculan **solo** con puntos `moving`.
    - `ritmo_min_km` puede ser NaN en splits sin distancia en movimiento.
    - Se asume que `df` está ordenado por `time`. Si está vacío, devuelve `{}`, `df`
    sin cambios y un DataFrame de splits vacío.

    Ejemplos
    --------
    >>> metrics, df_proc, splits = compute_metrics(df)
    >>> metrics['distance_km'], metrics['avg_moving_speed_kmh']  # doctest: +SKIP
    (42.18, 27.3)
    >>> splits[['km_inicio','dist_moving','time_moving']].head()  # doctest: +SKIP
    """

    if df.empty:
        return {}, df, pd.DataFrame()

    df = df.copy()
    df['moving'] = df['speed'] > moving_speed_threshold
    total_dist_m = df.loc[df['moving'], 'd_dist'].sum()
    elapsed_s = (df['time'].iloc[-1] - df['time'].iloc[0]).total_seconds()
    moving_s = df.loc[df['moving'], 'dt'].sum()
    avg_moving_speed = total_dist_m / moving_s if moving_s > 0 else 0.0
    max_speed = df['speed'].max()
    df['km'] = df['dist'] / 1000.0
    df['split'] = npy.floor(df['km'] / 5).astype(int)

    splits = (
        df.groupby('split', as_index=False)
          .agg(dist_moving=('d_dist', lambda s: s[df.loc[s.index, 'moving']].sum()),
               time_moving=('dt',   lambda s: s[df.loc[s.index, 'moving']].sum()),
               elev_gain=('ele',   lambda s: s.diff().clip(lower=0).sum()))
    )
    if not splits.empty:
        splits['km_inicio'] = splits['split']*5
        splits['ritmo_min_km'] = npy.where(
            splits['dist_moving']>0,
            (splits['time_moving']/(splits['dist_moving']/1000.0))/60.0,
            npy.nan
        )
    dia_ruta = df['time'].min().date()
    hora_inicio = df['time'].min().time()
    hora_fin = df['time'].max().time()
    metrics = {
        'date': dia_ruta,
        'start_time': hora_inicio,
        'end_time': hora_fin,
        'distance_km': total_dist_m/1000.0,
        'elapsed_time_s': elapsed_s,
        'moving_time_s': moving_s,
        'avg_moving_speed_kmh': avg_moving_speed*3.6,
        'max_speed_kmh': max_speed*3.6,
    }

    return metrics, df, splits
