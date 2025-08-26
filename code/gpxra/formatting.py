import numpy as npy

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    """
    Convierte un color en formato HEX (#RRGGBB) a una cadena CSS `rgba(r, g, b, a)`.

    Parámetros
    ----------
    hex_color : str
        Color en hexadecimal con o sin almohadilla inicial, en formato de **6 dígitos**
        (p. ej., `"#1f77b4"` o `"1f77b4"`).
    alpha : float
        Componente alfa para la opacidad. Típicamente en el rango `[0.0, 1.0]`.

    Devuelve
    --------
    str
        Cadena con el color en formato CSS `rgba(R, G, B, A)`, por ejemplo
        `"rgba(31, 119, 180, 0.25)"`.

    Notas
    -----
    - La función **no valida** que `hex_color` tenga una longitud correcta distinta de 6
    ni que `alpha` esté en `[0, 1]`; se asume entrada válida.
    - Solo se admiten colores HEX de 6 dígitos. No soporta abreviados de 3 dígitos.

    Ejemplos
    --------
    >>> hex_to_rgba("#1f77b4", 0.25)
    'rgba(31, 119, 180, 0.25)'
    >>> hex_to_rgba("FF0000", 1.0)
    'rgba(255, 0, 0, 1.0)'
    """

    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"

def format_time(seconds: float) -> str:
    """
    Formatea una duración en segundos a una cadena legible `Hh MMm SSs` o `Mm SSs`.

    Parámetros
    ----------
    seconds : float
        Duración en segundos. Puede ser `None` o `NaN`.

    Devuelve
    --------
    str
        Cadena formateada. Si `seconds` es `None` o `NaN`, devuelve `"—"`.
        - Si la duración es de 1 hora o más: `"Hh MMm SSs"`.
        - Si es menor de 1 hora: `"Mm SSs"`.

    Notas
    -----
    - Los segundos se convierten a `int` (truncado hacia abajo).
    - Soporta valores `float` o `int`. Para negativos, el resultado será
    el formateo del valor truncado (no se aplica signo).

    Ejemplos
    --------
    >>> format_time(3725)
    '1h 02m 05s'
    >>> format_time(125)
    '2m 05s'
    >>> format_time(float('nan'))
    '—'
    >>> format_time(None)
    '—'
    """

    if seconds is None or npy.isnan(seconds):
        return "—"

    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h:
        return f"{h:d}h {m:02d}m {s:02d}s"

    return f"{m:d}m {s:02d}s"
