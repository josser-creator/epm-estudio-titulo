from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Type
from pydantic import BaseModel

from services import DocumentIntelligenceService, AzureOpenAIService
from config import get_settings


class BaseDocumentProcessor(ABC):
    """Procesador base abstracto para documentos PDF."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._settings = get_settings()
        self._doc_intelligence = DocumentIntelligenceService()
        self._openai = AzureOpenAIService()

    @property
    @abstractmethod
    def system_name(self) -> str:
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def schema_class(self) -> Type[BaseModel]:
        pass

    def process(self, pdf_bytes: bytes, source_path: str) -> dict:
        """
        Procesa un documento PDF y retorna los datos estructurados.
        """
        try:
            self.logger.info(f"Procesando {self.system_name}: {source_path}")
            start = datetime.now()

            # OCR con Document Intelligence
            ocr_result = self._doc_intelligence.analyze_document(pdf_bytes)
            document_text = ocr_result.get("content", "")
            if not document_text.strip():
                raise ValueError("Document Intelligence devolvió contenido vacío")

            # Extracción con OpenAI (incluye chunking automático)
            extracted_data = self._openai.extract_structured_data(
                document_text=document_text,
                system_prompt=self.system_prompt,
                schema_class=self.schema_class
            )

            # Limpieza genérica
            cleaned_data = self._clean_extracted_data(extracted_data)

            # Enriquecer con metadatos (sin guardar, solo para retorno)
            enriched = self._enrich_metadata(cleaned_data, source_path, ocr_result)

            # Validaciones específicas
            validated = self._validate_extracted_data(enriched)

            self.logger.info(f"Procesado en {(datetime.now()-start).total_seconds():.2f}s")
            return validated

        except Exception as e:
            self.logger.error(f"Error procesando {source_path}: {e}")
            raise

    def _clean_extracted_data(self, data: dict) -> dict:
        # Implementar limpieza común, por ejemplo usando JsonCleaner
        from utils import JsonCleaner
        return JsonCleaner.clean_dict(data)

    def _enrich_metadata(self, data: dict, source_path: str, ocr_result: dict) -> dict:
        file_name = source_path.split("/")[-1]
        processing_metadata = {
            "_procesamiento": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "archivo_origen": file_name,
                "ruta_origen": source_path,
                "sistema": self.system_name,
                "paginas_procesadas": len(ocr_result.get("pages", [])),
                "caracteres_extraidos": len(ocr_result.get("content", ""))
            }
        }
        return {**data, **processing_metadata}

    def _validate_extracted_data(self, data: dict) -> dict:
        # Por defecto, retorna igual
        return data
    