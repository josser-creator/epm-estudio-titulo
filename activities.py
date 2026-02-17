import logging
import azure.durable_functions as df
from typing import List, Dict, Any
from datetime import datetime

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor
)
from services import DataLakeService, DocumentIntelligenceService, AzureOpenAIService
from utils import JsonCleaner
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
datalake = DataLakeService()
doc_intel = DocumentIntelligenceService()
openai = AzureOpenAIService()

# Mapeo de tipo de documento a procesador
PROCESSOR_MAP = {
    "estudio_titulos": EstudioTitulosProcessor,
    "minuta_cancelacion": MinutaCancelacionProcessor,
    "minuta_constitucion": MinutaConstitucionProcessor,
}

def activity_procesar_documento(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Actividad que procesa un único documento.
    payload: {
        "process_id": str,
        "tipo": str (estudio_titulos, minuta_cancelacion, minuta_constitucion),
        "blob_path": str (ruta en bronze, ej: "bronze/casos/{process_id}/documento.pdf"),
        "caso_id": str
    }
    Retorna: dict con los datos extraídos y metadatos.
    """
    process_id = payload["process_id"]
    tipo = payload["tipo"]
    blob_path = payload["blob_path"]
    caso_id = payload["caso_id"]

    logger.info(f"Procesando documento {tipo} para caso {caso_id}, process {process_id}")

    # Leer PDF desde Data Lake bronze
    pdf_bytes = datalake.read_file(settings.datalake_container_bronze, blob_path)

    # Obtener procesador correspondiente
    processor_class = PROCESSOR_MAP.get(tipo)
    if not processor_class:
        raise ValueError(f"Tipo de documento desconocido: {tipo}")

    processor = processor_class()
    # El método process ahora debe ser adaptado para usar el servicio OpenAI con chunking.
    # Modificamos base_processor para que use el servicio con chunking (ya lo hemos cambiado).
    extracted_data = processor.process(pdf_bytes, blob_path)

    # Guardar el resultado en silver (opcional, para trazabilidad)
    silver_path = f"conecta/{tipo}/{caso_id}/{process_id}.json"
    datalake.write_json(settings.datalake_container_silver, silver_path, extracted_data)

    # Retornar los datos extraídos junto con metadatos
    return {
        "tipo": tipo,
        "datos": extracted_data,
        "blob_path": blob_path,
        "silver_path": silver_path
    }

def activity_sintetizar_resultados(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Actividad que consolida los resultados de todos los documentos de un caso
    y genera el Master JSON (gold).
    resultados: lista de salidas de activity_procesar_documento.
    Retorna el Master JSON.
    """
    logger.info(f"Sintetizando {len(resultados)} documentos")

    # Extraer campos clave según las tablas proporcionadas
    master = {
        "matricula_inmobiliaria": None,
        "cedulas": [],
        "nombres": [],
        "viabilidad_prestamo": None,
        "confianza": None,
        "razon_rechazo": None,
        "metadata": {
            "process_id": None,  # lo pondremos después
            "caso_id": None,
            "fecha_sintesis": None
        }
    }

    # Recorrer resultados y poblar master
    for res in resultados:
        datos = res["datos"]
        tipo = res["tipo"]

        if tipo == "estudio_titulos":
            # Extraer matrícula del inmueble
            if datos.get("inmueble") and datos["inmueble"].get("matricula_inmobiliaria"):
                master["matricula_inmobiliaria"] = datos["inmueble"]["matricula_inmobiliaria"]
            # Extraer propietarios (nombres y cédulas)
            for prop in datos.get("propietarios", []):
                if prop.get("nombre") and prop["nombre"] not in master["nombres"]:
                    master["nombres"].append(prop["nombre"])
                if prop.get("identificacion") and prop["identificacion"] not in master["cedulas"]:
                    master["cedulas"].append(prop["identificacion"])
            # Concepto jurídico como viabilidad (simplificado)
            concepto = datos.get("concepto_juridico")
            if concepto:
                if "favorable" in concepto.lower():
                    master["viabilidad_prestamo"] = "favorable"
                elif "desfavorable" in concepto.lower():
                    master["viabilidad_prestamo"] = "desfavorable"
                else:
                    master["viabilidad_prestamo"] = "condicionado"

        elif tipo == "minuta_constitucion":
            # Podríamos extraer también compradores
            for deudor in datos.get("deudores", []):
                if deudor.get("nombre") and deudor["nombre"] not in master["nombres"]:
                    master["nombres"].append(deudor["nombre"])
                if deudor.get("identificacion") and deudor["identificacion"] not in master["cedulas"]:
                    master["cedulas"].append(deudor["identificacion"])
            # También podemos tomar el nombre del vendedor
            if datos.get("nombre_vendedor") and datos["nombre_vendedor"] not in master["nombres"]:
                master["nombres"].append(datos["nombre_vendedor"])

        elif tipo == "minuta_cancelacion":
            # Similar
            for deudor in datos.get("deudores", []):
                if deudor.get("nombre") and deudor["nombre"] not in master["nombres"]:
                    master["nombres"].append(deudor["nombre"])
                if deudor.get("identificacion") and deudor["identificacion"] not in master["cedulas"]:
                    master["cedulas"].append(deudor["identificacion"])

    # Calcular confianza (promedio simple de confianza por documento si existiera)
    # Por ahora, ponemos un valor fijo
    master["confianza"] = 0.95

    # Si no hay viabilidad, poner "pendiente"
    if not master["viabilidad_prestamo"]:
        master["viabilidad_prestamo"] = "pendiente"

    # Agregar metadatos
    # Tomamos process_id y caso_id del primer resultado (todos iguales)
    if resultados:
        master["metadata"]["process_id"] = resultados[0].get("process_id")  # habría que pasarlo en el payload
        master["metadata"]["caso_id"] = resultados[0].get("caso_id")
    master["metadata"]["fecha_sintesis"] = datetime.utcnow().isoformat()

    # Guardar en gold
    gold_path = f"conecta/master/{master['metadata']['caso_id']}/{master['metadata']['process_id']}.json"
    datalake.write_json(settings.datalake_container_gold, gold_path, master)

    # También podríamos guardar en silver el master
    datalake.write_json(settings.datalake_container_silver, gold_path.replace("gold", "silver"), master)

    return master