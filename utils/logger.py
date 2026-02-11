import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> None:
    """
    Configura el logging para la aplicacion.

    Args:
        level: Nivel de logging (default: INFO).
        format_string: Formato personalizado para los logs.
    """
    if format_string is None:
        format_string = (
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )

    # Configurar handler para stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(format_string))

    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remover handlers existentes
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)

    root_logger.addHandler(handler)

    # Reducir verbosidad de librerias externas
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un modulo.

    Args:
        name: Nombre del logger (normalmente __name__).

    Returns:
        Logger configurado.
    """
    return logging.getLogger(name)


class ContextLogger:
    """Logger con contexto adicional para tracking de procesamiento."""

    def __init__(self, logger: logging.Logger, context: dict = None):
        """
        Inicializa el logger con contexto.

        Args:
            logger: Logger base.
            context: Diccionario con contexto adicional.
        """
        self._logger = logger
        self._context = context or {}

    def _format_message(self, message: str) -> str:
        """Formatea el mensaje con el contexto."""
        if self._context:
            context_str = " | ".join(f"{k}={v}" for k, v in self._context.items())
            return f"[{context_str}] {message}"
        return message

    def set_context(self, **kwargs) -> None:
        """Actualiza el contexto."""
        self._context.update(kwargs)

    def clear_context(self) -> None:
        """Limpia el contexto."""
        self._context.clear()

    def info(self, message: str, **kwargs) -> None:
        """Log de nivel INFO."""
        self._logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log de nivel WARNING."""
        self._logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log de nivel ERROR."""
        self._logger.error(self._format_message(message), exc_info=exc_info, **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log de nivel DEBUG."""
        self._logger.debug(self._format_message(message), **kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log de excepcion."""
        self._logger.exception(self._format_message(message), **kwargs)
