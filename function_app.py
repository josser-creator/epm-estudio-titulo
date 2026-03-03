"""
Azure Functions App para procesamiento de documentos legales.
Blob Triggers para estudio de títulos, minutas de cancelación y constitución.
Timer Trigger para limpieza automática del contenedor bronze.
"""

import azure.functions as func
import logging
import uuid
import datetime
from datetime import datetime as dt
import os

from azure.storage.filedatalake import DataLakeServiceClient

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor,
)
from services import DataLakeService, CosmosDBService
from config import get_settings

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar servicios
settings = get_settings()
datalake = DataLakeService()
cosmos = CosmosDBService()
from utils import business_days

app = func.FunctionApp()

# Mapeo para Blob Triggers: (tipo_corto, clase_procesador, prefijo_id, subpath)
BLOB_TIPO_MAP = {
    "EstudioTitulos": ("estudio_titulos", EstudioTitulosProcessor, "ET", "conecta/vivienda/estudio-titulos"),
    "MinutaCancelacion": ("minuta_cancelacion", MinutaCancelacionProcessor, "MINC", "conecta/vivienda/minuta-cancelacion"),
    "MinutaConstitucion": ("minuta_constitucion", MinutaConstitucionProcessor, "MC", "conecta/vivienda/minuta-constitucion"),
}

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
    Guarda los resultados en Data Lake (Silver) y Cosmos DB.

    Args:
        extracted_data: Datos extraídos (formato plano con PanelFields).
        caso_id: Identificador del caso.
        process_id: ID único del proceso.
        tipo_documento: Tipo de documento (partición en Cosmos DB).
        archivo_origen: Ruta original del blob.
        processor_name: Nombre del procesador (etiqueta).
        subpath: Ruta relativa en silver (ej: "conecta/vivienda/...").

    Returns:
        Ruta relativa del archivo guardado en silver.
    """
    json_result = {
        "metadata": {
            "fecha_procesamiento": dt.now().isoformat(),
            "proceso_id": process_id,
            "caso_id": caso_id,
            "tipo_documento": tipo_documento,
            "archivo_origen": archivo_origen,
        },
        "datos_extraidos": extracted_data,
    }

    # --- Data Lake (Silver) ---
    silver_relative_path = f"{subpath}/{caso_id}/{process_id}.json"
    silver_full_path = datalake.write_json(
        container="silver",
        file_path=silver_relative_path,
        data=json_result,
    )
    logger.info(f"Resultado guardado en Data Lake: {silver_full_path}")

    # --- Cosmos DB ---
    cosmos_document = {
        "id": process_id,
        "procesoId": process_id,
        "casoId": caso_id,
        "tipoDocumento": tipo_documento,
        "fechaProcesamiento": dt.now().isoformat(),
        "archivoOrigen": archivo_origen,
        "rutasDataLake": {"silver": silver_full_path},
        "datosExtraidos": extracted_data,
        "_etiquetas": {
            "sistema": "conecta",
            "procesador": processor_name,
            "origen": "blob",
        },
    }

    cosmos.upsert_document(
        document=cosmos_document,
        partition_key=tipo_documento,
    )
    logger.info(f"Documento guardado en Cosmos DB con id: {process_id}")

    return silver_relative_path

def process_blob(
    blob: func.InputStream,
    processor_class,
    tipo_key: str,
):
    """
    Procesa un blob de un tipo específico (genérico).

    Args:
        blob: Blob entrante.
        processor_class: Clase del procesador (ej: EstudioTitulosProcessor).
        tipo_key: Clave en BLOB_TIPO_MAP (ej: "EstudioTitulos").
    """
    blob_name = blob.name
    logger.info(f"Blob Trigger activado: {blob_name} (tipo: {tipo_key})")

    if not blob_name.lower().endswith(".pdf"):
        logger.warning(f"Saltando archivo no-PDF: {blob_name}")
        return

    pdf_bytes = blob.read()
    if len(pdf_bytes) == 0:
        logger.error(f"Blob vacío recibido: {blob_name}")
        return

    tipo_corto, processor_class, prefijo_id, subpath = BLOB_TIPO_MAP[tipo_key]

    nombre_base = os.path.basename(blob_name)
    caso_id = nombre_base.replace(".pdf", "").replace("_", "-")
    process_id = f"{prefijo_id}-{uuid.uuid4()}"
    logger.info(f"Iniciando procesamiento: process_id={process_id}, caso={caso_id}")

    try:
        processor = processor_class()
        extracted_data = processor.process(pdf_bytes, blob_name)
        logger.info(f"Procesamiento completado exitosamente para {blob_name}")

        persistir_resultados(
            extracted_data=extracted_data,
            caso_id=caso_id,
            process_id=process_id,
            tipo_documento=tipo_corto,
            archivo_origen=blob_name,
            processor_name=processor_class.__name__,
            subpath=subpath,
        )

    except Exception as e:
        logger.error(
            f"Error procesando {tipo_key} ({blob_name}): {str(e)}", exc_info=True
        )
        raise

# ============================================================
# Blob Triggers específicos
# ============================================================

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/estudio_de_titulos/{name}",
    connection="AzureWebJobsStorage",
)
def estudio_titulos_blob(blob: func.InputStream):
    """Blob Trigger para Estudio de Títulos."""
    process_blob(blob, EstudioTitulosProcessor, "EstudioTitulos")

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_cancelacion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_cancelacion_blob(blob: func.InputStream):
    """Blob Trigger para Minuta de Cancelación."""
    process_blob(blob, MinutaCancelacionProcessor, "MinutaCancelacion")

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_constitucion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_constitucion_blob(blob: func.InputStream):
    """Blob Trigger para Minuta de Constitución."""
    process_blob(blob, MinutaConstitucionProcessor, "MinutaConstitucion")

# ============================================================
# Timer Trigger para limpieza automática de bronze
# ============================================================

@app.timer_trigger(schedule="0 0 1 * * *", arg_name="myTimer", run_on_startup=False)
def cleanup_bronze_timer(myTimer: func.TimerRequest) -> None:
    """
    Timer diario (1:00 AM UTC) que elimina archivos del contenedor bronze
    con antigüedad superior a bronze_retention_days en días hábiles (lunes–viernes).
    """
    logger.info("Iniciando limpieza automática de bronze (días hábiles)")

    try:
        retention_days = settings.bronze_retention_days
        now_utc = datetime.datetime.now(datetime.timezone.utc)

        account_url = f"https://{settings.datalake_account_name}.dfs.core.windows.net"
        data_lake_client = DataLakeServiceClient(
            account_url=account_url,
            credential=settings.datalake_account_key
        )
        file_system_client = data_lake_client.get_file_system_client(
            settings.datalake_container_bronze
        )

        paths = file_system_client.get_paths(recursive=True)
        deleted_count = 0

        for path in paths:
            if path.is_directory:
                continue

            last_modified = path.last_modified
            if not last_modified:
                continue

            days_elapsed = business_days(last_modified, now_utc)

            if days_elapsed >= retention_days:
                file_client = file_system_client.get_file_client(path.name)
                file_client.delete_file()
                logger.info(
                    f"Eliminado archivo: {path.name} | "
                    f"Días hábiles transcurridos: {days_elapsed}"
                )
                deleted_count += 1

        logger.info(f"Limpieza completada. {deleted_count} archivos eliminados.")

    except Exception as e:
        logger.error(f"Error en limpieza automática: {str(e)}", exc_info=True)
        raise