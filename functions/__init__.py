from .estudio_titulos_trigger import process_estudio_titulos
from .minuta_cancelacion_trigger import process_minuta_cancelacion
from .minuta_constitucion_trigger import process_minuta_constitucion

__all__ = [
    "process_estudio_titulos",
    "process_minuta_cancelacion",
    "process_minuta_constitucion",
]
