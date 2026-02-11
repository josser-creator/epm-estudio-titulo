from typing import Type
from pydantic import BaseModel

from .base_processor import BaseDocumentProcessor
from schemas import MinutaCancelacionSchema
from prompts import MINUTA_CANCELACION_SYSTEM_PROMPT


class MinutaCancelacionProcessor(BaseDocumentProcessor):
    """Procesador especializado para documentos de Minuta de Cancelacion."""

    @property
    def system_name(self) -> str:
        return "minuta_cancelacion"

    @property
    def system_prompt(self) -> str:
        return MINUTA_CANCELACION_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return MinutaCancelacionSchema

    def _validate_extracted_data(self, data: dict) -> dict:
        """
        Validaciones especificas para Minuta de Cancelacion.

        Args:
            data: Datos extraidos a validar.

        Returns:
            dict: Datos validados.
        """
        # Validar datos del acreedor
        acreedor = data.get("acreedor", {})
        if not acreedor.get("nombre"):
            self.logger.warning("No se identifico el nombre del acreedor")

        if not acreedor.get("nit_cc"):
            self.logger.warning("No se encontro NIT/CC del acreedor")

        # Validar datos de la obligacion
        obligacion = data.get("obligacion", {})
        if not obligacion.get("escritura_constitucion"):
            self.logger.warning("No se encontro la escritura de constitucion original")

        # Validar inmuebles
        inmuebles = data.get("inmuebles", [])
        if not inmuebles:
            self.logger.warning("No se encontraron inmuebles en la cancelacion")

        # Crear resumen de la cancelacion
        deudores = data.get("deudores", [])
        cancelacion = data.get("cancelacion", {})

        data["_resumen_cancelacion"] = {
            "acreedor": acreedor.get("nombre", "No identificado"),
            "cantidad_deudores": len(deudores),
            "cantidad_inmuebles": len(inmuebles),
            "tipo_obligacion": obligacion.get("tipo", "No especificado"),
            "monto_original": obligacion.get("monto_original", "No especificado"),
            "motivo_cancelacion": cancelacion.get("motivo", "Pago total"),
            "matriculas_liberadas": [
                inm.get("matricula_inmobiliaria", "N/A")
                for inm in inmuebles
                if inm.get("matricula_inmobiliaria")
            ]
        }

        # Validar coherencia: fecha de pago debe ser anterior o igual a fecha de cancelacion
        fecha_pago = cancelacion.get("fecha_pago_total")
        fecha_escritura = data.get("metadata", {}).get("fecha")

        if fecha_pago and fecha_escritura:
            data["_resumen_cancelacion"]["fecha_pago"] = fecha_pago
            data["_resumen_cancelacion"]["fecha_escritura"] = fecha_escritura

        return data
