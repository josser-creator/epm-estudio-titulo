from abc import ABC, abstractmethod
import logging
from typing import Any


class BaseService(ABC):
    """Clase base abstracta para todos los servicios de Azure."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def initialize(self) -> None:
        """Inicializa el cliente del servicio."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica que el servicio este disponible."""
        pass

    def _log_info(self, message: str, **kwargs: Any) -> None:
        """Log de informacion con contexto adicional."""
        self.logger.info(message, extra=kwargs)

    def _log_error(self, message: str, error: Exception = None, **kwargs: Any) -> None:
        """Log de errores con contexto adicional."""
        if error:
            self.logger.error(f"{message}: {str(error)}", extra=kwargs, exc_info=True)
        else:
            self.logger.error(message, extra=kwargs)

    def _log_warning(self, message: str, **kwargs: Any) -> None:
        """Log de advertencias con contexto adicional."""
        self.logger.warning(message, extra=kwargs)
