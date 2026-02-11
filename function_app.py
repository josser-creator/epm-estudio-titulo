"""
Azure Functions App - Blob Triggers para Procesamiento OCR de Documentos Legales

Blob Triggers:
  - Estudio de Títulos: bronze/conecta/vivienda/estudio_de_titulos/
  - Minuta de Cancelación: bronze/conecta/vivienda/minuta_de_cancelacion/
  - Minuta de Constitución: bronze/conecta/vivienda/minuta_de_constitucion/

Almacenamiento:
  - Data Lake: contenedores silver/gold
  - Cosmos DB: contenedor 'procesamientos' con partition key /tipoDocumento
"""

import azure.functions as func
import logging
import json
import uuid
from datetime import datetime
from typing import Type

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor,
)
from services import DataLakeService, CosmosDBService
from processors.base_processor import BaseDocumentProcessor

# Configuración de logging y servicios globales
logger = logging.getLogger(__name__)
datalake = DataLakeService()
cosmos = CosmosDBService()
app = func.FunctionApp()

# Mapeo para Blob Triggers (compatibilidad)
BLOB_TIPO_MAP = {
    "EstudioTitulos": ("estudio-titulos", EstudioTitulosProcessor, "ET", "conecta/vivienda/estudio-titulos"),
    "MinutaCancelacion": ("minuta-cancelacion", MinutaCancelacionProcessor, "MINC", "conecta/vivienda/minuta-cancelacion"),
    "MinutaConstitucion": ("minuta-constitucion", MinutaConstitucionProcessor, "MC", "conecta/vivienda/minuta-constitucion"),
}

# Función común para guardar resultados en Data Lake y Cosmos DB
def persistir_resultados(
    extracted_data: dict,
    caso_id: str,
    process_id: str,
    tipo_documento: str,        
    archivo_origen: str,
    processor_name: str,
    subpath: str
) -> str:
    """
    Guarda los resultados del procesamiento en Data Lake (Silver/Gold) y Cosmos DB.
    Retorna la ruta Silver generada.
    """
    json_result = {
        "metadata": {
            "fecha_procesamiento": datetime.now().isoformat(),
            "proceso_id": process_id,
            "caso_id": caso_id,
            "tipo_documento": tipo_documento,
            "archivo_origen": archivo_origen,
        },
        "datos_extraidos": extracted_data,
    }

    # --- Data Lake (Silver) ---
    silver_path = datalake.write_json(
        container="silver",
        file_path=f"{subpath}/{caso_id}/{process_id}.json",
        data=json_result,
    )

    # --- Data Lake (Gold) ---
    datalake.write_json(
        container="gold",
        file_path=f"{subpath}/{caso_id}/{process_id}.json",
        data=json_result,
    )

    logger.info(f"Resultado guardado en Data Lake: {silver_path}")

    # --- Cosmos DB ---
    cosmos_document = {
        "id": process_id,
        "procesoId": process_id,
        "casoId": caso_id,
        "tipoDocumento": tipo_documento,          # Partition Key
        "fechaProcesamiento": datetime.now().isoformat(),
        "archivoOrigen": archivo_origen,
        "rutasDataLake": {
            "silver": silver_path,
            "gold": f"gold/{subpath}/{caso_id}/{process_id}.json",
        },
        "datosExtraidos": extracted_data,
        "_etiquetas": {
            "sistema": "conecta",
            "procesador": processor_name,
            "origen": "blob",                     # Solo origen Blob Trigger
        },
    }

    cosmos.upsert_document(
        document=cosmos_document,
        partition_key=tipo_documento,
    )
    logger.info(f"Documento guardado en Cosmos DB con id: {process_id}")

    return silver_path


# ------------------------------------------------------------
# Blob Triggers
# ------------------------------------------------------------

def process_blob(
    blob: func.InputStream,
    processor_class: Type[BaseDocumentProcessor],
    tipo_documento_blob: str,    # ej: "EstudioTitulos"
    silver_subpath: str,
    gold_subpath: str,
    prefix_id: str,
):
    """
    Función genérica para procesar blobs de documentos legales.
    """
    blob_name = blob.name
    logger.info(f"Blob Trigger activado: {blob_name} (tipo: {tipo_documento_blob})")

    if not blob_name.lower().endswith(".pdf"):
        logger.warning(f"Saltando archivo no-PDF: {blob_name}")
        return

    pdf_bytes = blob.read()
    if len(pdf_bytes) == 0:
        logger.error(f"Blob vacío recibido: {blob_name}")
        return

    # Obtener datos del mapeo
    tipo_doc_corto, _, _, subpath = BLOB_TIPO_MAP[tipo_documento_blob]

    process_id = f"{prefix_id}-{uuid.uuid4()}"
    caso_id = blob_name.replace(".pdf", "").replace("_", "-")
    logger.info(f"Iniciando procesamiento: process_id={process_id}, caso={caso_id}")

    try:
        processor = processor_class()
        extracted_data = processor.process(pdf_bytes, blob_name)
        logger.info(f"Procesamiento completado exitosamente para {blob_name}")

        # Persistir resultados usando la función común
        persistir_resultados(
            extracted_data=extracted_data,
            caso_id=caso_id,
            process_id=process_id,
            tipo_documento=tipo_doc_corto,
            archivo_origen=blob_name,
            processor_name=processor_class.__name__,
            subpath=subpath,
        )

    except Exception as e:
        logger.error(
            f"Error procesando {tipo_documento_blob} ({blob_name}): {str(e)}", exc_info=True
        )
        raise


@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/estudio_de_titulos/{name}",
    connection="AzureWebJobsStorage",
)
def estudio_titulos_blob(blob: func.InputStream):
    process_blob(
        blob,
        processor_class=EstudioTitulosProcessor,
        tipo_documento_blob="EstudioTitulos",
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
        tipo_documento_blob="MinutaCancelacion",
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
        tipo_documento_blob="MinutaConstitucion",
        silver_subpath="conecta/vivienda/minuta-constitucion",
        gold_subpath="conecta/vivienda/minuta-constitucion",
        prefix_id="MC",
    )
