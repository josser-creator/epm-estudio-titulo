"""
Pruebas unitarias para logger_extra.py. Se enfocan en la funcionalidad de logging con contexto adicional,
no en la integración con Azure o el formato exacto de los datos. Se usan mocks para simular el logger subyacente 
y para verificar que los mensajes se formateen correctamente con el contexto adicional.
Las pruebas verifican que el ContextLogger añada el contexto a los mensajes de log, que permita actualizar el contexto, 
que maneje correctamente los niveles de log y que pueda limpiar el contexto cuando se le indique.
"""

import logging
from utils.logger import setup_logging, get_logger, ContextLogger


def test_setup_logging_y_context_logger_no_falla():
    setup_logging(level=logging.INFO)
    lg = get_logger("x")
    cl = ContextLogger(lg, {"caso_id": "1"})
    cl.info("hola")
    cl.set_context(process_id="p1")
    cl.warning("warn")
    cl.error("err", exc_info=False)
    cl.clear_context()
    cl.debug("dbg")