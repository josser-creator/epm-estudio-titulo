"""
Azure Functions App - Blob Triggers para Procesamiento OCR de Documentos Legales

Este módulo registra 3 Azure Blob Triggers para procesar documentos desde Data Lake:
1. Estudio de Títulos: bronze/conecta/vivienda/estudio_de_titulos/
2. Minuta de Cancelación: bronze/conecta/vivienda/minuta_de_cancelacion/
3. Minuta de Constitución: bronze/conecta/vivienda/minuta_de_constitucion/

Los documentos procesados se guardan en:
- Data Lake: silver/conecta/vivienda/{tipo}/
- Cosmos DB: contenedor 'procesamientos' con partition key /tipoDocumento
"""

import azure.functions as func
import logging
import json
import uuid
from datetime import datetime

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor,
)
from services import DataLakeService, CosmosDBService

logger = logging.getLogger(__name__)
datalake = DataLakeService()
cosmos = CosmosDBService()
app = func.FunctionApp()


def process_blob(
    blob: func.InputStream,
    processor_class,
    tipo_documento: str,
    silver_subpath: str,
    gold_subpath: str,
    prefix_id: str,
):
    """
    Función genérica para procesar blobs de documentos legales.
    """
    blob_name = blob.name
    logger.info(f"Blob Trigger activado: {blob_name} (tipo: {tipo_documento})")

    if not blob_name.lower().endswith(".pdf"):
        logger.warning(f"Saltando archivo no-PDF: {blob_name}")
        return

    pdf_bytes = blob.read()
    if len(pdf_bytes) == 0:
        logger.error(f"Blob vacío recibido: {blob_name}")
        return

    process_id = f"{prefix_id}-{uuid.uuid4()}"
    caso_id = blob_name.replace(".pdf", "").replace("_", "-")
    logger.info(f"Iniciando procesamiento: process_id={process_id}, caso={caso_id}")

    try:
        processor = processor_class()
        extracted_data = processor.process(pdf_bytes, blob_name)
        logger.info(f"Procesamiento completado exitosamente para {blob_name}")

        json_result = {
            "metadata": {
                "fecha_procesamiento": datetime.now().isoformat(),
                "proceso_id": process_id,
                "caso_id": caso_id,
                "tipo_documento": tipo_documento,
                "archivo_origen": blob_name,
            },
            "datos_extraidos": extracted_data,
        }

        # --- 1. Guardar en Data Lake (Silver y Gold) ---
        silver_path = datalake.write_json(
            container="silver",
            file_path=f"{silver_subpath}/{caso_id}/{process_id}.json",
            data=json_result,
        )

        datalake.write_json(
            container="gold",
            file_path=f"{gold_subpath}/{caso_id}/{process_id}.json",
            data=json_result,
        )

        logger.info(f"Resultado guardado en Data Lake: {silver_path}")

        # --- 2. Guardar en Cosmos DB ---
        # Documento optimizado para consultas por caso y tipo
        cosmos_document = {
            "id": process_id,  # Identificador único
            "procesoId": process_id,
            "casoId": caso_id,
            "tipoDocumento": tipo_documento,  # Partition Key (definida en CosmosDBService)
            "fechaProcesamiento": datetime.now().isoformat(),
            "archivoOrigen": blob_name,
            "rutasDataLake": {
                "silver": silver_path,
                "gold": f"gold/{gold_subpath}/{caso_id}/{process_id}.json",
            },
            "datosExtraidos": extracted_data,
            "_etiquetas": {  # Metadatos adicionales para búsqueda
                "sistema": "conecta",
                "procesador": processor_class.__name__,
            },
        }

        cosmos.upsert_document(
            document=cosmos_document,
            partition_key=tipo_documento,  # Importante: coincide con la definición del contenedor
        )
        logger.info(f"Documento guardado en Cosmos DB con id: {process_id}")

    except Exception as e:
        logger.error(
            f"Error procesando {tipo_documento} ({blob_name}): {str(e)}", exc_info=True
        )
        raise


# ===================== BLOB TRIGGERS =====================


@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/estudio_de_titulos/{name}",
    connection="AzureWebJobsStorage",
)
def estudio_titulos_blob(blob: func.InputStream):
    process_blob(
        blob,
        processor_class=EstudioTitulosProcessor,
        tipo_documento="EstudioTitulos",
        silver_subpath="conecta/vivienda/estudio-titulos",
        gold_subpath="conecta/vivienda/estudio-titulos",
        prefix_id="ET",
    )


@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_cancelacion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_cancelacion_blob(blob: func.InputStream):
    process_blob(
        blob,
        processor_class=MinutaCancelacionProcessor,
        tipo_documento="MinutaCancelacion",
        silver_subpath="conecta/vivienda/minuta-cancelacion",
        gold_subpath="conecta/vivienda/minuta-cancelacion",
        prefix_id="MINC",
    )


@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_constitucion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_constitucion_blob(blob: func.InputStream):
    process_blob(
        blob,
        processor_class=MinutaConstitucionProcessor,
        tipo_documento="MinutaConstitucion",
        silver_subpath="conecta/vivienda/minuta-constitucion",
        gold_subpath="conecta/vivienda/minuta-constitucion",
        prefix_id="MC",
    )
    