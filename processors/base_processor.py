from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Type
from pydantic import BaseModel

from services import DocumentIntelligenceService, AzureOpenAIService, DataLakeService
from config import get_settings


class BaseDocumentProcessor(ABC):
    """Procesador base abstracto para documentos PDF."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._settings = get_settings()

        # Inicializar servicios
        self._doc_intelligence = DocumentIntelligenceService()
        self._openai = AzureOpenAIService()
        self._datalake = DataLakeService()

    @property
    @abstractmethod
    def system_name(self) -> str:
        """Nombre del sistema (estudio_titulos, minuta_cancelacion, minuta_constitucion)."""
        pass

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Prompt del sistema para la extraccion."""
        pass

    @property
    @abstractmethod
    def schema_class(self) -> Type[BaseModel]:
        """Clase Pydantic del schema de salida."""
        pass

    def process(self, pdf_bytes: bytes, source_path: str) -> dict:
        """
        Procesa un documento PDF y retorna los datos estructurados.

        Args:
            pdf_bytes: Contenido del PDF en bytes.
            source_path: Ruta del archivo origen para metadata.

        Returns:
            dict: Datos estructurados extraidos del documento.
        """
        try:
            self.logger.info(f"Starting processing for {self.system_name}: {source_path}")
            start_time = datetime.now()

            # Paso 1: OCR con Document Intelligence
            self.logger.info("Step 1: Running Document Intelligence OCR")
            ocr_result = self._doc_intelligence.analyze_document(pdf_bytes)
            document_text = ocr_result.get("content", "")

            if not document_text.strip():
                raise ValueError("Document Intelligence returned empty content")

            self.logger.info(f"OCR completed. Extracted {len(document_text)} characters")

            # Paso 2: Extraccion estructurada con OpenAI
            self.logger.info("Step 2: Extracting structured data with Azure OpenAI")
            extracted_data = self._openai.extract_structured_data(
                document_text=document_text,
                system_prompt=self.system_prompt,
                schema_class=self.schema_class
            )

            # Paso 3: Enriquecer con metadata de procesamiento
            self.logger.info("Step 3: Enriching with processing metadata")
            enriched_data = self._enrich_metadata(extracted_data, source_path, ocr_result)

            # Paso 4: Validacion adicional
            self.logger.info("Step 4: Running additional validations")
            validated_data = self._validate_extracted_data(enriched_data)

            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Processing completed in {processing_time:.2f} seconds")

            return validated_data

        except Exception as e:
            self.logger.error(f"Processing failed for {source_path}: {str(e)}")
            raise

    def process_and_save(self, pdf_bytes: bytes, source_path: str) -> str:
        """
        Procesa un documento y guarda el resultado en el Data Lake silver.

        Args:
            pdf_bytes: Contenido del PDF en bytes.
            source_path: Ruta del archivo origen.

        Returns:
            str: Ruta del archivo JSON guardado en silver.
        """
        try:
            # Procesar documento
            extracted_data = self.process(pdf_bytes, source_path)

            # Construir ruta de destino en silver
            output_path = self._build_output_path(source_path)

            # Guardar en silver
            self.logger.info(f"Saving extracted data to: {output_path}")
            saved_path = self._datalake.write_json(
                container=self._settings.datalake_container_silver,
                file_path=output_path,
                data=extracted_data
            )

            self.logger.info(f"Data saved successfully to: {saved_path}")
            return saved_path

        except Exception as e:
            self.logger.error(f"Process and save failed: {str(e)}")
            raise

    def _enrich_metadata(self, data: dict, source_path: str, ocr_result: dict) -> dict:
        """
        Enriquece los datos con metadata de procesamiento.

        Args:
            data: Datos extraidos.
            source_path: Ruta del archivo origen.
            ocr_result: Resultado del OCR.

        Returns:
            dict: Datos enriquecidos con metadata.
        """
        # Extraer nombre del archivo
        file_name = source_path.split("/")[-1] if "/" in source_path else source_path

        # Agregar metadata de procesamiento
        processing_metadata = {
            "_procesamiento": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "archivo_origen": file_name,
                "ruta_origen": source_path,
                "sistema": self.system_name,
                "paginas_procesadas": len(ocr_result.get("pages", [])),
                "tablas_detectadas": len(ocr_result.get("tables", [])),
                "caracteres_extraidos": len(ocr_result.get("content", ""))
            }
        }

        return {**data, **processing_metadata}

    def _validate_extracted_data(self, data: dict) -> dict:
        """
        Realiza validaciones adicionales sobre los datos extraidos.
        Puede ser sobrescrito por procesadores especificos.

        Args:
            data: Datos a validar.

        Returns:
            dict: Datos validados (posiblemente modificados).
        """
        return data

    def _build_output_path(self, source_path: str) -> str:
        """
        Construye la ruta de salida para el archivo JSON.

        Args:
            source_path: Ruta del archivo origen en bronze.

        Returns:
            str: Ruta de destino en silver.
        """
        # Extraer nombre del archivo sin extension
        file_name = source_path.split("/")[-1] if "/" in source_path else source_path
        base_name = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

        # Agregar timestamp para evitar colisiones
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Construir ruta: conecta/[sistema]/[nombre_archivo]_[timestamp].json
        return f"conecta/{self.system_name}/{base_name}_{timestamp}.json"
