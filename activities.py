import logging
from typing import List, Dict, Any
from datetime import datetime

from services import DataLakeService
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
datalake = DataLakeService()


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


def calcular_confianza(resultados: List[Dict]) -> float:
    """
    Calcula un porcentaje de confianza promedio basado en la presencia de campos clave.
    Utiliza los pesos definidos en settings.confidence_weights.
    """
    pesos = settings.confidence_weights
    total_peso = 0.0
    total_aciertos = 0.0

    for res in resultados:
        datos = res["datos"]
        panel = datos.get("PanelFields", [])
        field_dict = panel_fields_to_dict(panel)

        for campo, peso in pesos.items():
            if campo in field_dict and field_dict[campo]:
                total_aciertos += peso
            total_peso += peso

    if total_peso == 0:
        return 0.0

    return round(total_aciertos / total_peso, 4)


def evaluar_viabilidad(resultados: List[Dict], field_dicts: Dict[str, Dict]) -> Dict:
    """
    Evalúa la viabilidad del préstamo según reglas de negocio configurables.
    Retorna un dict con status, reasons y un log de la decisión.
    """
    status = "APPROVED"
    reasons = []
    decision_log = []

    estudio_dict = field_dicts.get("estudio_titulos", {})

    # -------------------------------------------------
    # Regla 0: Documento ilegible
    # -------------------------------------------------
    for res in resultados:
        if not res.get("datos", {}).get("is_legible", True):
            status = "REJECTED"
            reasons.append({
                "code": "DOC_INVALID",
                "message": "Documento ilegible"
            })
            decision_log.append("Regla 0: Documento ilegible detectado → RECHAZADO")
            break

    # -------------------------------------------------
    # Regla 1: Matrícula obligatoria
    # -------------------------------------------------
    if not estudio_dict.get("VIV_PrestamoDireccionMatricula"):
        status = "REJECTED"
        reasons.append({
            "code": "MISSING_MATRICULA",
            "message": "No se encontró matrícula inmobiliaria en el estudio de títulos"
        })
        decision_log.append("Regla 1: Matrícula ausente → RECHAZADO")

    # -------------------------------------------------
    # Regla 2: Concepto jurídico
    # -------------------------------------------------
    concepto = estudio_dict.get("VIV_conceptoJuridico", "").lower()

    if "desfavorable" in concepto:
        status = "REJECTED"
        reasons.append({
            "code": "CONCEPTO_DESFAVORABLE",
            "message": "El concepto jurídico del estudio de títulos es desfavorable"
        })
        decision_log.append("Regla 2: Concepto desfavorable → RECHAZADO")

    elif "favorable" not in concepto and status != "REJECTED":
        status = "CONDITIONAL"
        reasons.append({
            "code": "CONCEPTO_NO_CLARO",
            "message": "El concepto jurídico no es claro o no se encontró"
        })
        decision_log.append("Regla 2: Concepto no claro → CONDICIONAL")

    # -------------------------------------------------
    # Regla 3: Gravámenes vigentes
    # -------------------------------------------------
    if settings.reject_if_encumbrances:
        gravamenes = estudio_dict.get("VIV_gravamenes", "")
        if gravamenes and "embargo" in gravamenes.lower() and "cancelado" not in gravamenes.lower():
            status = "REJECTED"
            reasons.append({
                "code": "EMBARGO_VIGENTE",
                "message": "Existe un embargo vigente sobre el inmueble"
            })
            decision_log.append("Regla 3: Embargo vigente detectado → RECHAZADO")

    # -------------------------------------------------
    # Regla 4: Edad fuera de rango
    # -------------------------------------------------
    edad_str = estudio_dict.get("VIV_edadSolicitante")

    try:
        if edad_str:
            edad = int(edad_str)
            if edad < settings.min_age or edad > settings.max_age:
                status = "REJECTED"
                reasons.append({
                    "code": "AGE_LIMIT",
                    "message": "Edad fuera de rango"
                })
                decision_log.append(
                    f"Regla 4: Edad {edad} fuera de rango "
                    f"({settings.min_age}-{settings.max_age}) → RECHAZADO"
                )
    except (ValueError, TypeError):
        pass

    # -------------------------------------------------
    # Regla 5: Score insuficiente
    # -------------------------------------------------
    score_str = estudio_dict.get("VIV_creditScore")

    try:
        if score_str:
            score = int(score_str)
            if score < settings.min_credit_score:
                status = "REJECTED"
                reasons.append({
                    "code": "CREDIT_SCORE_LOW",
                    "message": "Score insuficiente"
                })
                decision_log.append(
                    f"Regla 5: Score {score} < mínimo "
                    f"({settings.min_credit_score}) → RECHAZADO"
                )
    except (ValueError, TypeError):
        pass

    if status == "APPROVED":
        decision_log.append("Todas las reglas se cumplieron → APROBADO")

    return {
        "status": status,
        "reasons": reasons,
        "decision_log": decision_log
    }


def activity_sintetizar_resultados(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    logger.info(f"Sintetizando {len(resultados)} documentos")

    master = {
        "matricula_inmobiliaria": None,
        "cedulas": [],
        "nombres": [],
        "viabilidad_prestamo": "pendiente",
        "status": "APPROVED",
        "reasons": [],
        "metadata": {
            "process_id": None,
            "caso_id": None,
            "fecha_sintesis": datetime.utcnow().isoformat(),
            "confianza": 0.0,
            "decision_log": []
        }
    }

    nombres_set = set()
    cedulas_set = set()
    field_dicts = {}

    for res in resultados:
        tipo = res["tipo"]
        datos = res["datos"]
        panel = datos.get("PanelFields", [])
        field_dict = panel_fields_to_dict(panel)
        field_dicts[tipo] = field_dict

        if "VIV_Compradores" in field_dict:
            nombres = field_dict["VIV_Compradores"]
            if nombres:
                for n in nombres.split(";"):
                    nombres_set.add(n.strip())

        if "VIV_identificacionCompradores" in field_dict:
            cedulas = field_dict["VIV_identificacionCompradores"]
            if cedulas:
                for c in cedulas.split(";"):
                    cedulas_set.add(c.strip())

        if tipo == "estudio_titulos" and not master["matricula_inmobiliaria"]:
            master["matricula_inmobiliaria"] = field_dict.get("VIV_PrestamoDireccionMatricula")

    confianza = calcular_confianza(resultados)
    master["metadata"]["confianza"] = confianza

    decision = evaluar_viabilidad(resultados, field_dicts)
    master["status"] = decision["status"]
    master["reasons"] = decision["reasons"]
    master["metadata"]["decision_log"] = decision["decision_log"]

    if decision["status"] == "APPROVED":
        master["viabilidad_prestamo"] = "favorable"
    elif decision["status"] == "CONDITIONAL":
        master["viabilidad_prestamo"] = "condicionado"
    else:
        master["viabilidad_prestamo"] = "desfavorable"

    master["nombres"] = list(nombres_set)
    master["cedulas"] = list(cedulas_set)

    if resultados:
        master["metadata"]["process_id"] = resultados[0].get("process_id")
        master["metadata"]["caso_id"] = resultados[0].get("caso_id")

    gold_path = f"conecta/master/{master['metadata']['caso_id']}/{master['metadata']['process_id']}.json"

    datalake.write_json(settings.datalake_container_gold, gold_path, master)
    datalake.write_json(
        settings.datalake_container_silver,
        gold_path.replace("gold", "silver"),
        master
    )

    return master
