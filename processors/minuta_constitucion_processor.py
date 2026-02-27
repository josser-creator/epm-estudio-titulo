from typing import Type
from pydantic import BaseModel
from .base_processor import BaseDocumentProcessor
from schemas.panel_schemas import MinutaConstitucionPlano
from prompts import MINUTA_CONSTITUCION_SYSTEM_PROMPT

class MinutaConstitucionProcessor(BaseDocumentProcessor):
    """
    Procesador especializado en extracción de información de minutas de constitución de hipotecas en Colombia. 
    Utiliza un sistema prompt detallado para guiar la extracción de datos relevantes sobre la resolución de nombramiento, 
    detalles de la escritura pública de constitución, información del inmueble afectado,"""
    
    @property
    def system_name(self) -> str:
        return "minuta_constitucion"

    @property
    def system_prompt(self) -> str:
        return MINUTA_CONSTITUCION_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return MinutaConstitucionPlano

    def _validate_extracted_data(self, data: dict) -> dict:
        field_dict = {item['InternalName']: item.get('TextValue') or item.get('NumberValue')
                      for item in data.get('PanelFields', [])}
        if not field_dict.get('VIV_Compradores'):
            self.logger.warning("No se encontraron compradores")
        if not field_dict.get('TPC_ValorComercial'):
            self.logger.warning("No se encontró valor de compraventa")
        return data