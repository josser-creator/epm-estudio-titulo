import logging
import azure.functions as func

from processors import EstudioTitulosProcessor
from utils import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)


def process_estudio_titulos(blob: func.InputStream) -> None:
    """
    Azure Function con Blob Trigger para procesar documentos de Estudio de Titulos.

    Ruta de entrada: bronze/conecta/estudio_titulos/{name}.pdf
    Ruta de salida: silver/conecta/estudio_titulos/{name}_{timestamp}.json

    Args:
        blob: Blob de entrada con el documento PDF.
    """
    try:
        blob_name = blob.name
        logger.info(f"Blob trigger activated for Estudio de Titulos: {blob_name}")

        # Validar que sea un archivo PDF
        if not blob_name.lower().endswith('.pdf'):
            logger.warning(f"Skipping non-PDF file: {blob_name}")
            return

        # Leer contenido del blob
        pdf_bytes = blob.read()
        logger.info(f"Read {len(pdf_bytes)} bytes from blob")

        if len(pdf_bytes) == 0:
            logger.error(f"Empty blob received: {blob_name}")
            return

        # Procesar documento
        processor = EstudioTitulosProcessor()
        output_path = processor.process_and_save(
            pdf_bytes=pdf_bytes,
            source_path=blob_name
        )

        logger.info(f"Processing completed successfully. Output: {output_path}")

    except Exception as e:
        logger.exception(f"Error processing Estudio de Titulos: {blob.name}")
        raise
