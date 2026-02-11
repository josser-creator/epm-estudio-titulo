from typing import Type
from pydantic import BaseModel

from .base_processor import BaseDocumentProcessor
from schemas import EstudioTitulosSchema
from prompts import ESTUDIO_TITULOS_SYSTEM_PROMPT


class EstudioTitulosProcessor(BaseDocumentProcessor):
    """Procesador especializado para documentos de Estudio de Titulos."""

    @property
    def system_name(self) -> str:
        return "estudio_titulos"

    @property
    def system_prompt(self) -> str:
        return ESTUDIO_TITULOS_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return EstudioTitulosSchema

    def _validate_extracted_data(self, data: dict) -> dict:
        """
        Validaciones especificas para Estudio de Titulos.

        Args:
            data: Datos extraidos a validar.

        Returns:
            dict: Datos validados.
        """
        # Validar que exista matricula inmobiliaria
        inmueble = data.get("inmueble", {})
        if not inmueble.get("matricula_inmobiliaria"):
            self.logger.warning("No se encontro matricula inmobiliaria en el documento")

        # Validar tradicion
        tradicion = data.get("tradicion", [])
        if not tradicion:
            self.logger.warning("No se encontraron anotaciones de tradicion")

        # Validar gravamenes - separar vigentes de cancelados
        gravamenes = data.get("gravamenes", [])
        gravamenes_vigentes = [g for g in gravamenes if g.get("estado", "").lower() == "vigente"]
        gravamenes_cancelados = [g for g in gravamenes if g.get("estado", "").lower() == "cancelado"]

        data["_resumen_gravamenes"] = {
            "total": len(gravamenes),
            "vigentes": len(gravamenes_vigentes),
            "cancelados": len(gravamenes_cancelados)
        }

        # Validar propietarios
        propietarios = data.get("propietarios", [])
        if not propietarios:
            self.logger.warning("No se encontraron propietarios en el documento")

        # Calcular porcentaje total de propiedad
        total_porcentaje = 0
        for prop in propietarios:
            porcentaje = prop.get("porcentaje_propiedad", "0")
            if porcentaje:
                # Limpiar el porcentaje (remover % y convertir)
                try:
                    porcentaje_limpio = porcentaje.replace("%", "").replace(",", ".").strip()
                    total_porcentaje += float(porcentaje_limpio)
                except (ValueError, AttributeError):
                    pass

        data["_resumen_propietarios"] = {
            "total": len(propietarios),
            "porcentaje_total": f"{total_porcentaje}%"
        }

        return data
