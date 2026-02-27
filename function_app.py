import azure.functions as func
import logging
import uuid
from datetime import datetime
import os

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

app = func.FunctionApp()

# Mapeo para Blob Triggers: (tipo_corto, clase_procesador, prefijo_id, subpath)
# - tipo_corto: se usará como partition key en Cosmos DB y como identificador del tipo.
# - subpath: ruta relativa dentro del contenedor silver (sin el contenedor).
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
    Guarda los resultados del procesamiento en Data Lake (Silver) y Cosmos DB.
    Retorna la ruta relativa dentro del contenedor silver.
    """
    # Estructura del resultado final con metadata
    json_result = {
        "metadata": {
            "fecha_procesamiento": datetime.now().isoformat(),
            "proceso_id": process_id,
            "caso_id": caso_id,
            "tipo_documento": tipo_documento,
            "archivo_origen": archivo_origen,
        },
        "datos_extraidos": extracted_data,   # Aquí va el JSON plano (con PanelFields)
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
        "tipoDocumento": tipo_documento,          # Partition Key
        "fechaProcesamiento": datetime.now().isoformat(),
        "archivoOrigen": archivo_origen,
        "rutasDataLake": {
            "silver": silver_full_path,            # Ruta completa (container + relative)
        },
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
    Función genérica para procesar blobs de documentos legales.
    """
    blob_name = blob.name
    logger.info(f"Blob Trigger activado: {blob_name} (tipo: {tipo_key})")

    # Validar extensión
    if not blob_name.lower().endswith(".pdf"):
        logger.warning(f"Saltando archivo no-PDF: {blob_name}")
        return

    # Leer contenido
    pdf_bytes = blob.read()
    if len(pdf_bytes) == 0:
        logger.error(f"Blob vacío recibido: {blob_name}")
        return

    # Obtener datos del mapeo
    tipo_corto, processor_class, prefijo_id, subpath = BLOB_TIPO_MAP[tipo_key]

    # Extraer nombre base del archivo (sin ruta ni extensión) para caso_id
    nombre_base = os.path.basename(blob_name)                     # "documento.pdf"
    caso_id = nombre_base.replace(".pdf", "").replace("_", "-")   # Ej: "HV-JOSSER-CORDOBA-RIVAS"
    # Nota: Reemplazamos guiones bajos por guiones medios para evitar problemas en rutas

    process_id = f"{prefijo_id}-{uuid.uuid4()}"
    logger.info(f"Iniciando procesamiento: process_id={process_id}, caso={caso_id}")

    try:
        # Instanciar procesador
        processor = processor_class()
        # El método process ya debe devolver los datos planos según el schema correspondiente
        extracted_data = processor.process(pdf_bytes, blob_name)
        logger.info(f"Procesamiento completado exitosamente para {blob_name}")

        # Persistir resultados
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
        # Relanzar la excepción para que Azure Functions registre el error y reintente si está configurado
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
    process_blob(blob, EstudioTitulosProcessor, "EstudioTitulos")

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_cancelacion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_cancelacion_blob(blob: func.InputStream):
    process_blob(blob, MinutaCancelacionProcessor, "MinutaCancelacion")

@app.blob_trigger(
    arg_name="blob",
    path="bronze/conecta/vivienda/minuta_de_constitucion/{name}",
    connection="AzureWebJobsStorage",
)
def minuta_constitucion_blob(blob: func.InputStream):
    process_blob(blob, MinutaConstitucionProcessor, "MinutaConstitucion")