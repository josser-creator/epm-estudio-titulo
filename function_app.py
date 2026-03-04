"""
Azure Functions App para procesamiento de documentos legales.
Blob Trigger único para la carpeta bronze/conecta/vivienda/1/ que clasifica
automáticamente el tipo de documento según palabras clave en el nombre del archivo.
Timer Trigger para limpieza automática del contenedor bronze.
"""

import azure.functions as func
import logging
import uuid
import datetime
from datetime import datetime as dt
import os
from typing import List, Dict, Any

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
from utils.business_days import business_days_between as business_days

app = func.FunctionApp()

# ============================
# Durable activity functions
# ============================

@app.activity_trigger(input_name="caso_id")
def leer_resultados_intermedios_activity(caso_id: str):
    """Activity Function que delega a la lógica en activities.py."""
    from activities import activity_leer_resultados_intermedios
    return activity_leer_resultados_intermedios(caso_id)


@app.activity_trigger(input_name="resultados")
def generar_resumen_activity(resultados: List[Dict[str, Any]]):
    """Activity que construye un JSON reducido a partir de los resultados."""
    from activities import activity_generar_resumen_reducido
    return activity_generar_resumen_reducido(resultados)

# Mapeo para Blob Triggers: (tipo_corto, clase_procesador, prefijo_id, subpath)
# Los prefijos corresponden a los códigos solicitados por el negocio.
# El `subpath` define la carpeta dentro de silver donde se guardarán los resultados.
BLOB_TIPO_MAP = {
    "EstudioTitulos": (
        "estudio_titulos",
        EstudioTitulosProcessor,
        "VIV-514.2_1901",  # prefijo para estudio de títulos
        "conecta/vivienda/estudio-titulos",
    ),
    "MinutaCancelacion": (
        "minuta_cancelacion",
        MinutaCancelacionProcessor,
        "VIV-514.2_1903",  # prefijo para minuta de cancelación
        "conecta/vivienda/minuta-cancelacion",
    ),
    "MinutaConstitucion": (
        "minuta_constitucion",
        MinutaConstitucionProcessor,
        "VIV-514.2_1902",  # prefijo para minuta de constitución
        "conecta/vivienda/minuta-constitucion",
    ),
}

# Palabras clave para identificar el tipo de documento por el nombre del archivo
KEYWORD_TO_TYPE = {
    "estudio de titulos": "EstudioTitulos",
    "estudio de títulos": "EstudioTitulos",
    "estudio_titulos": "EstudioTitulos",
    "cancelacion": "MinutaCancelacion",
    "cancelación": "MinutaCancelacion",
    "constitucion": "MinutaConstitucion",
    "constitución": "MinutaConstitucion",
}

def detectar_tipo_por_nombre(nombre_archivo: str) -> str | None:
    """
    Detecta el tipo de documento basado en palabras clave en el nombre del archivo.
    Retorna la clave de BLOB_TIPO_MAP (ej. "EstudioTitulos") o None si no se detecta.
    """
    nombre_lower = nombre_archivo.lower()
    for keyword, tipo in KEYWORD_TO_TYPE.items():
        if keyword in nombre_lower:
            return tipo
    return None

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
    (Sin cambios respecto a tu versión original)
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
    (Sin cambios respecto a tu versión original, excepto que ahora se llama con tipo_key)
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
# Blob Trigger ÚNICO para la carpeta raíz
# ============================================================

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/1/{name}",
    connection="AzureWebJobsStorage",
)
def procesar_documento_blob(blob: func.InputStream):
    """
    Blob Trigger único que captura todos los archivos en bronze/conecta/vivienda/1/,
    detecta el tipo de documento por el nombre y lo procesa con el procesador adecuado.
    """
    blob_name = blob.name
    logger.info(f"Blob Trigger activado (raíz): {blob_name}")

    # Detectar tipo por nombre
    nombre_archivo = os.path.basename(blob_name)
    tipo_key = detectar_tipo_por_nombre(nombre_archivo)

    if not tipo_key:
        logger.error(f"No se pudo determinar el tipo de documento para {blob_name}. Se omite.")
        return

    # Obtener la clase procesadora del mapa
    _, processor_class, _, _ = BLOB_TIPO_MAP[tipo_key]

    # Llamar a la función genérica de procesamiento
    process_blob(blob, processor_class, tipo_key)


# ============================================================
# Timer Trigger para limpieza automática de bronze
# ============================================================

@app.timer_trigger(
    schedule="0 0 1 * * *",
    arg_name="myTimer",
    run_on_startup=False
)
def cleanup_bronze_timer(myTimer: func.TimerRequest) -> None:
    """
    Timer diario (1:00 AM UTC) que elimina archivos del contenedor bronze
    con antigüedad superior a bronze_retention_days en días hábiles.
    """

    logger.info("Iniciando limpieza automática de bronze (días hábiles)")

    try:
        retention_days = settings.bronze_retention_days

        # SIEMPRE UTC-aware
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

            # Normalización explícita defensiva
            if last_modified.tzinfo is None:
                last_modified = last_modified.replace(
                    tzinfo=datetime.timezone.utc
                )
            else:
                last_modified = last_modified.astimezone(
                    datetime.timezone.utc
                )

            days_elapsed = business_days(last_modified, now_utc)

            if days_elapsed >= retention_days:

                file_client = file_system_client.get_file_client(path.name)
                file_client.delete_file()

                logger.info(
                    f"Eliminado archivo: {path.name} | "
                    f"Días hábiles transcurridos: {days_elapsed}"
                )

                deleted_count += 1

        logger.info(
            f"Limpieza completada. {deleted_count} archivos eliminados."
        )

    except Exception as e:
        logger.error(
            f"Error en limpieza automática: {str(e)}",
            exc_info=True
        )
        raise