"""
Azure Functions App para procesamiento de documentos legales.
Blob Trigger único para la carpeta bronze/conecta/vivienda/1/ que clasifica
automáticamente el tipo de documento según palabras clave en el nombre del archivo.
Timer Trigger para limpieza automática del contenedor bronze.
Incluye orquestación Durable para consolidar resultados de un caso.
"""

import azure.functions as func
import azure.durable_functions as df
import logging
import uuid
import datetime
from datetime import datetime as dt
import os
from typing import List, Dict, Any, Union

from azure.storage.filedatalake import DataLakeServiceClient

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor,
)

from services import DataLakeService, CosmosDBService
from config import get_settings
from utils.business_days import business_days_between as business_days


# =========================================================
# Configuración
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
datalake = DataLakeService()
cosmos = CosmosDBService()

# Usamos DFApp para habilitar durable functions
app = df.DFApp()


# =========================================================
# Durable Activity Functions (ya definidas)
# =========================================================

@app.activity_trigger(input_name="caso_id")
def leer_resultados_intermedios_activity(caso_id: str):
    from activities import activity_leer_resultados_intermedios
    return activity_leer_resultados_intermedios(caso_id)


@app.activity_trigger(input_name="resultados")
def generar_resumen_activity(resultados: List[Dict[str, Any]]):
    from activities import activity_generar_resumen_reducido
    return activity_generar_resumen_reducido(resultados)


# =========================================================
# Durable Orchestrator
# =========================================================

@app.orchestration_trigger(context_name="context")
def sintetizar_caso_orchestrator(context: df.DurableOrchestrationContext):
    """
    Orquestador que, dado un caso_id, lee todos los resultados intermedios
    (de silver) y genera los archivos maestros en gold.
    """
    caso_id = context.get_input()
    if not caso_id:
        return {"error": "No se proporcionó caso_id"}

    # 1. Leer todos los resultados intermedios
    resultados = yield context.call_activity("leer_resultados_intermedios_activity", caso_id)

    if not resultados:
        return {"error": f"No se encontraron documentos para el caso {caso_id}"}

    # 2. Sintetizar y generar master JSON
    rutas = yield context.call_activity("generar_resumen_activity", resultados)

    return rutas


# =========================================================
# HTTP Starter
# =========================================================

@app.route(route="orquestar/sintesis/{caso_id}", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_sintesis(req: func.HttpRequest, client):
    """
    Inicia la orquestación para un caso específico.
    Ejemplo: POST /orquestar/sintesis/caso-123
    """
    caso_id = req.route_params.get("caso_id")
    if not caso_id:
        return func.HttpResponse("Debe proporcionar un caso_id", status_code=400)

    instance_id = f"sintesis-{caso_id}-{uuid.uuid4()}"
    await client.start_new("sintetizar_caso_orchestrator", instance_id, caso_id)

    return client.create_check_status_response(req, instance_id)


# =========================================================
# Configuración de tipos
# =========================================================

BLOB_TIPO_MAP = {
    "EstudioTitulos": (
        "estudio_titulos",
        EstudioTitulosProcessor,
        "VIV-514.2_1901",
        "conecta/vivienda/estudio-titulos",
    ),
    "MinutaCancelacion": (
        "minuta_cancelacion",
        MinutaCancelacionProcessor,
        "VIV-514.2_1903",
        "conecta/vivienda/minuta-cancelacion",
    ),
    "MinutaConstitucion": (
        "minuta_constitucion",
        MinutaConstitucionProcessor,
        "VIV-514.2_1902",
        "conecta/vivienda/minuta-constitucion",
    ),
}


# =========================================================
# Detección de tipo de documento
# =========================================================

def detectar_tipo_por_nombre(nombre_archivo: str) -> str | None:
    """
    Detecta el tipo de documento basado en el nombre del archivo.

    Soporta:
    - mayúsculas/minúsculas
    - espacios
    - guiones bajos
    """

    nombre = nombre_archivo.lower()

    if "estudio_de_titulos" in nombre or "estudio de titulos" in nombre:
        return "EstudioTitulos"

    if "minuta_cancelacion" in nombre or "cancelacion" in nombre:
        return "MinutaCancelacion"

    if "minuta_constitucion" in nombre or "constitucion" in nombre:
        return "MinutaConstitucion"

    return None


# =========================================================
# Persistencia
# =========================================================

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
    Persiste los resultados extraídos en Data Lake (Silver) y Cosmos DB.
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

    silver_relative_path = f"{subpath}/{caso_id}/{process_id}.json"

    silver_full_path = datalake.write_json(
        container="silver",
        file_path=silver_relative_path,
        data=json_result,
    )

    logger.info(f"Resultado guardado en Data Lake: {silver_full_path}")

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


# =========================================================
# Procesamiento de Blob
# =========================================================

def process_blob(
    blob: func.InputStream,
    tipo_key: str,  # Cambiado: ahora recibimos el string key directamente
):

    blob_name = blob.name
    logger.info(f"Blob Trigger activado: {blob_name} (tipo: {tipo_key})")

    if not blob_name.lower().endswith(".pdf"):
        logger.warning(f"Saltando archivo no-PDF: {blob_name}")
        return

    pdf_bytes = blob.read()

    if len(pdf_bytes) == 0:
        logger.error(f"Blob vacío recibido: {blob_name}")
        return

    # Obtenemos la configuración del tipo de documento
    tipo_corto, processor_cls, prefijo_id, subpath = BLOB_TIPO_MAP[tipo_key]

    nombre_base = os.path.basename(blob_name)
    caso_id = nombre_base.replace(".pdf", "").replace("_", "-")
    process_id = f"{prefijo_id}-{uuid.uuid4()}"

    logger.info(f"Iniciando procesamiento: process_id={process_id}, caso={caso_id}")

    try:
        # Instanciamos el procesador correspondiente
        processor = processor_cls()

        extracted_data = processor.process(pdf_bytes, blob_name)

        logger.info(f"Procesamiento completado exitosamente para {blob_name}")

        persistir_resultados(
            extracted_data=extracted_data,
            caso_id=caso_id,
            process_id=process_id,
            tipo_documento=tipo_corto,
            archivo_origen=blob_name,
            processor_name=processor.__class__.__name__,
            subpath=subpath,
        )

    except Exception as e:
        logger.error(
            f"Error procesando {tipo_key} ({blob_name}): {str(e)}",
            exc_info=True
        )
        raise


# =========================================================
# Blob Trigger principal
# =========================================================

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/1/{name}",
    connection="AzureWebJobsStorage",
)
def procesar_documento_blob(blob: func.InputStream):
    """
    Función principal que se activa cuando se sube un blob a la carpeta
    bronze/conecta/vivienda/1/
    """

    blob_name = blob.name
    logger.info(f"Blob Trigger activado (raíz): {blob_name}")

    nombre_archivo = os.path.basename(blob_name)
    tipo_key = detectar_tipo_por_nombre(nombre_archivo)

    if not tipo_key:
        logger.error(
            f"No se pudo determinar el tipo de documento para {blob_name}. Se omite."
        )
        return

    # Llamamos a process_blob con el tipo_key
    process_blob(blob, tipo_key)


# =========================================================
# Timer Trigger limpieza bronze
# =========================================================

@app.timer_trigger(
    schedule="0 0 1 * * *",
    arg_name="myTimer",
    run_on_startup=False
)
def cleanup_bronze_timer(myTimer: func.TimerRequest) -> None:
    """
    Timer trigger que se ejecuta el primer día de cada mes para limpiar
    archivos antiguos del contenedor bronze basado en días hábiles.
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