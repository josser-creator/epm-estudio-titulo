import logging
import azure.durable_functions as df
from typing import List, Dict, Any
from datetime import datetime

"""
Este módulo define las actividades de procesamiento de documentos y síntesis de resultados para el proyecto de estudio de títulos 
inmobiliarios.
"""

from processors import (
    EstudioTitulosProcessor,
    MinutaCancelacionProcessor,
    MinutaConstitucionProcessor
)
from services import DataLakeService
from utils import JsonCleaner
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
datalake = DataLakeService()

PROCESSOR_MAP = {
    "estudio_titulos": EstudioTitulosProcessor,
    "minuta_cancelacion": MinutaCancelacionProcessor,
    "minuta_constitucion": MinutaConstitucionProcessor,
}

def activity_procesar_documento(payload: Dict[str, Any]) -> Dict[str, Any]:
    process_id = payload["process_id"]
    tipo = payload["tipo"]
    blob_path = payload["blob_path"]
    caso_id = payload["caso_id"]

    logger.info(f"Procesando documento {tipo} para caso {caso_id}, process {process_id}")

    pdf_bytes = datalake.read_file(settings.datalake_container_bronze, blob_path)

    processor_class = PROCESSOR_MAP.get(tipo)
    if not processor_class:
        raise ValueError(f"Tipo de documento desconocido: {tipo}")

    processor = processor_class()
    extracted_data = processor.process(pdf_bytes, blob_path)

    # Guardar en silver
    silver_path = f"conecta/{tipo}/{caso_id}/{process_id}.json"
    datalake.write_json(settings.datalake_container_silver, silver_path, extracted_data)

    return {
        "tipo": tipo,
        "datos": extracted_data,
        "blob_path": blob_path,
        "silver_path": silver_path,
        "process_id": process_id,
        "caso_id": caso_id
    }

def panel_fields_to_dict(panel_fields: List[Dict]) -> Dict[str, Any]:
    """Convierte la lista PanelFields a un diccionario clave -> valor."""
    result = {}
    for item in panel_fields:
        name = item["InternalName"]
        if item["Type"] == "Text":
            result[name] = item.get("TextValue")
        else:  # Number
            result[name] = item.get("NumberValue")
    return result

def activity_sintetizar_resultados(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    logger.info(f"Sintetizando {len(resultados)} documentos")

    # Inicializar estructura del master reducido
    master = {
        "matricula_inmobiliaria": None,
        "cedulas": [],
        "nombres": [],
        "viabilidad_prestamo": "pendiente",
        "status": "APPROVED",  # por defecto aprobado, se cambiará si hay problemas
        "reasons": [],
        "metadata": {
            "process_id": None,
            "caso_id": None,
            "fecha_sintesis": datetime.utcnow().isoformat(),
            "confianza": 0.95  # valor fijo por ahora
        }
    }

    # Recopilar todos los nombres y cédulas de los diferentes documentos
    nombres_set = set()
    cedulas_set = set()

    for res in resultados:
        datos = res["datos"]
        tipo = res["tipo"]
        panel_fields = datos.get("PanelFields", [])
        field_dict = panel_fields_to_dict(panel_fields)

        if tipo == "estudio_titulos":
            # Matrícula
            if not master["matricula_inmobiliaria"]:
                master["matricula_inmobiliaria"] = field_dict.get("VIV_PrestamoDireccionMatricula")

            # Propietarios (nombres y cédulas)
            nombres = field_dict.get("VIV_Compradores", "")
            if nombres:
                for n in nombres.split(";"):
                    nombres_set.add(n.strip())
            cedulas = field_dict.get("VIV_identificacionCompradores", "")
            if cedulas:
                for c in cedulas.split(";"):
                    cedulas_set.add(c.strip())

            # Viabilidad basada en concepto jurídico (si existe)
            concepto = field_dict.get("VIV_conceptoJuridico", "").lower()
            if concepto:
                if "favorable" in concepto:
                    master["viabilidad_prestamo"] = "favorable"
                elif "desfavorable" in concepto:
                    master["viabilidad_prestamo"] = "desfavorable"
                    master["status"] = "REJECTED"
                    master["reasons"].append({
                        "code": "CREDIT_SCORE_LOW",
                        "message": "Concepto jurídico desfavorable"
                    })
                else:
                    master["viabilidad_prestamo"] = "condicionado"

        elif tipo == "minuta_constitucion":
            # Compradores
            nombres = field_dict.get("VIV_Compradores", "")
            if nombres:
                for n in nombres.split(";"):
                    nombres_set.add(n.strip())
            cedulas = field_dict.get("VIV_identificacionCompradores", "")
            if cedulas:
                for c in cedulas.split(";"):
                    cedulas_set.add(c.strip())
            # Vendedor también puede ser un nombre relevante
            vendedor = field_dict.get("VIV_nombreVendedor")
            if vendedor:
                nombres_set.add(vendedor)

        elif tipo == "minuta_cancelacion":
            # Podría tener deudores, pero no están en los campos planos actuales.
            # Si se añadieran, se procesarían aquí.
            pass

    # Si no se encontró matrícula, marcar como rechazado
    if not master["matricula_inmobiliaria"]:
        master["status"] = "REJECTED"
        master["reasons"].append({
            "code": "DOC_INVALID",
            "message": "No se encontró matrícula inmobiliaria en el estudio de títulos"
        })

    # Convertir sets a listas
    master["nombres"] = list(nombres_set)
    master["cedulas"] = list(cedulas_set)

    # Tomar process_id y caso_id del primer resultado (todos deberían ser iguales)
    if resultados:
        master["metadata"]["process_id"] = resultados[0].get("process_id")
        master["metadata"]["caso_id"] = resultados[0].get("caso_id")

    # Guardar master en gold y silver
    gold_path = f"conecta/master/{master['metadata']['caso_id']}/{master['metadata']['process_id']}.json"
    datalake.write_json(settings.datalake_container_gold, gold_path, master)
    datalake.write_json(settings.datalake_container_silver, gold_path.replace("gold", "silver"), master)

    return master