from typing import Type
from pydantic import BaseModel
from .base_processor import BaseDocumentProcessor
from schemas.panel_schemas import EstudioTitulosPlano
from prompts import ESTUDIO_TITULOS_SYSTEM_PROMPT

class EstudioTitulosProcessor(BaseDocumentProcessor):
    """
    Procesador especializado en extracción de información de estudios de títulos inmobiliarios en Colombia. 
    Utiliza un sistema prompt detallado para guiar la extracción de datos relevantes sobre el inmueble, sus propietarios, 
    historia de tradición, gravámenes y limitaciones al dominio. Devuelve la información estructurada según el esquema definido en 
    EstudioTitulosPlano.
    """

    @property
    def system_name(self) -> str:
        return "estudio_titulos"

    @property
    def system_prompt(self) -> str:
        return ESTUDIO_TITULOS_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return EstudioTitulosPlano

    def _validate_extracted_data(self, data: dict) -> dict:
        # Convertir PanelFields a dict para fácil acceso
        field_dict = {item['InternalName']: item.get('TextValue') or item.get('NumberValue')
                      for item in data.get('PanelFields', [])}
        # Validar campos críticos
        if not field_dict.get('VIV_PrestamoDireccionMatricula'):
            self.logger.warning("No se encontró matrícula inmobiliaria en el documento")
        if not field_dict.get('VIV_Compradores'):
            self.logger.warning("No se encontraron propietarios")
        # Agregar resumen simple (opcional)
        data['_resumen'] = {
            'matricula': field_dict.get('VIV_PrestamoDireccionMatricula'),
            'propietarios': field_dict.get('VIV_Compradores'),
        }
        return data