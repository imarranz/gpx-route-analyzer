import numpy as npy

def haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia de gran círculo entre dos coordenadas (WGS84)
    usando la fórmula de *haversine*.


    Parámetros
    ----------
    lat1, lon1 : float o array-like
    Latitud y longitud del primer punto en grados decimales.
    lat2, lon2 : float o array-like
    Latitud y longitud del segundo punto en grados decimales.


    Devuelve
    --------
    float o numpy.ndarray
    Distancia(s) en metros entre los puntos. Si las entradas son arrays,
    se aplica *broadcasting* y se devuelve un array.


    Notas
    -----
    - Se asume una Tierra esférica con radio medio ``R = 6_371_000`` metros (aprox. WGS84).
    - Acepta escalares o arrays NumPy del mismo tamaño (o compatibles para *broadcasting*).
    - Adecuado para distancias habituales en actividades al aire libre. Para precisión
    geodésica submétrica, considere librerías elipsoidales (p. ej., GeographicLib).


    Ejemplos
    --------
    >>> haversine(43.2627, -2.9350, 43.2965, -2.9876) # doctest: +SKIP
    1234.56


    >>> lats1 = npy.array([43.0, 44.0])
    >>> lons1 = npy.array([-2.0, -3.0])
    >>> lats2 = npy.array([43.1, 44.1])
    >>> lons2 = npy.array([-2.1, -3.1])
    >>> haversine(lats1, lons1, lats2, lons2) # doctest: +SKIP
    array([...])
    """

    R = 6371000.0
    phi1, phi2 = npy.radians(lat1), npy.radians(lat2)
    dphi = npy.radians(lat2 - lat1)
    dlambda = npy.radians(lon2 - lon1)
    a = npy.sin(dphi/2.0)**2 + npy.cos(phi1) * npy.cos(phi2) * npy.sin(dlambda/2.0)**2
    c = 2 * npy.arctan2(npy.sqrt(a), npy.sqrt(1 - a))

    return R * c
