from typing import Type
from pydantic import BaseModel
from .base_processor import BaseDocumentProcessor
from schemas.panel_schemas import MinutaCancelacionPlano
from prompts import MINUTA_CANCELACION_SYSTEM_PROMPT

class MinutaCancelacionProcessor(BaseDocumentProcessor):
    """
    Procesador especializado en extracción de información de minutas de cancelación de hipotecas en Colombia. 
    Utiliza un sistema prompt detallado para guiar la extracción de datos relevantes sobre la resolución de nombramiento, 
    detalles de la escritura pública de cancelación, y la información del inmueble afectado. Devuelve la información 
    estructurada según el esquema definido en MinutaCancelacionPlano.
    """
    @property
    def system_name(self) -> str:
        return "minuta_cancelacion"

    @property
    def system_prompt(self) -> str:
        return MINUTA_CANCELACION_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return MinutaCancelacionPlano

    def _validate_extracted_data(self, data: dict) -> dict:
        field_dict = {item['InternalName']: item.get('TextValue') or item.get('NumberValue')
                      for item in data.get('PanelFields', [])}
        if not field_dict.get('VIV_numeroEscrituraPublica'):
            self.logger.warning("No se encontró número de escritura de cancelación")
        return data

