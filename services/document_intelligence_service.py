from typing import Optional
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

from .base_service import BaseService
from config import get_settings

class DocumentIntelligenceService(BaseService):
    """Servicio para procesar documentos PDF usando Azure Document Intelligence."""

    def __init__(self):
        super().__init__()
        self._client: Optional[DocumentAnalysisClient] = None
        self._settings = get_settings()
        self.initialize()

    def initialize(self) -> None:
        """Inicializa el cliente de Document Intelligence."""
        try:
            credential = AzureKeyCredential(self._settings.document_intelligence_key)
            self._client = DocumentAnalysisClient(
                endpoint=self._settings.document_intelligence_endpoint,
                credential=credential
            )
            self._log_info("Document Intelligence client initialized successfully")
        except Exception as e:
            self._log_error("Failed to initialize Document Intelligence client", error=e)
            raise

    def health_check(self) -> bool:
        """Verifica que el servicio este disponible."""
        return self._client is not None

    def analyze_document(self, pdf_bytes: bytes) -> dict:
        """
        Analiza un documento PDF usando el modelo layout.

        Args:
            pdf_bytes: Contenido del PDF en bytes.

        Returns:
            dict: Resultado del analisis con texto estructurado.
        """
        try:
            self._log_info("Starting document analysis with layout model")

            poller = self._client.begin_analyze_document(
                model_id="prebuilt-layout",
                document=pdf_bytes
            )
            result = poller.result()

            extracted_data = self._process_analysis_result(result)

            self._log_info(
                "Document analysis completed",
                pages=len(result.pages) if result.pages else 0,
                tables=len(result.tables) if result.tables else 0
            )

            return extracted_data

        except Exception as e:
            self._log_error("Document analysis failed", error=e)
            raise

    def _process_analysis_result(self, result) -> dict:
        """
        Procesa el resultado del analisis y extrae el contenido estructurado.

        Args:
            result: Resultado del analisis de Document Intelligence.

        Returns:
            dict: Contenido estructurado del documento.
        """
        extracted = {
            "content": result.content,
            "pages": [],
            "tables": [],
            "paragraphs": []
        }

        # Procesar paginas
        if result.pages:
            for page in result.pages:
                page_data = {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "lines": []
                }
                if page.lines:
                    for line in page.lines:
                        page_data["lines"].append({
                            "content": line.content,
                            "polygon": [{"x": p.x, "y": p.y} for p in line.polygon] if line.polygon else []
                        })
                extracted["pages"].append(page_data)

        # Procesar tablas
        if result.tables:
            for table in result.tables:
                table_data = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                for cell in table.cells:
                    table_data["cells"].append({
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "content": cell.content,
                        "is_header": cell.kind == "columnHeader" if hasattr(cell, 'kind') else False
                    })
                extracted["tables"].append(table_data)

        # Procesar parrafos
        if result.paragraphs:
            for paragraph in result.paragraphs:
                extracted["paragraphs"].append({
                    "content": paragraph.content,
                    "role": paragraph.role if hasattr(paragraph, 'role') else None
                })

        return extracted

    def get_full_text(self, pdf_bytes: bytes) -> str:
        """
        Extrae solo el texto completo del documento.

        Args:
            pdf_bytes: Contenido del PDF en bytes.

        Returns:
            str: Texto completo del documento.
        """
        result = self.analyze_document(pdf_bytes)
        return result.get("content", "")
