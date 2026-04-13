import logging
from typing import List, Dict, Any
from datetime import datetime
import json
import uuid

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


def add_prefix_to_panel_fields(panel_fields: List[Dict], prefix: str = "3_") -> List[Dict]:
    """
    Agrega el prefijo a los InternalName de cada PanelField.
    Ej: 'VIV_PrestamoDireccionMatricula' → '3_VIV_PrestamoDireccionMatricula'
    """
    prefixed = []
    for field in panel_fields:
        new_field = field.copy()
        new_field["InternalName"] = prefix + field["InternalName"]
        prefixed.append(new_field)
    return prefixed


def activity_leer_resultados_intermedios(caso_id: str) -> List[Dict[str, Any]]:
    """
    Lee todos los resultados intermedios JSON para un caso desde el contenedor *silver*.
    Busca en las carpetas de cada tipo de documento y devuelve una lista de objetos
    con la clave "tipo" (por ejemplo "estudio_titulos") y los "datos" leídos.

    Esta función está pensada para ejecutarse como Activity Function en un
    Durable Orchestrator.
    """
    resultados: List[Dict[str, Any]] = []
    tipos = ["estudio-titulos", "minuta-cancelacion", "minuta-constitucion"]
    container = settings.datalake_container_silver

    for tipo in tipos:
        directorio = f"conecta/vivienda/{tipo}/{caso_id}"
        try:
            archivos = datalake.list_files(container, directorio, extension=".json")
        except Exception as e:
            logger.warning(f"No se pudo listar archivos en {directorio}: {e}")
            archivos = []

        for ruta in archivos:
            try:
                contenido = datalake.read_file(container, ruta)
                datos_json = json.loads(contenido)
                # Extraemos los datos relevantes (dentro de 'datos_extraidos')
                extraidos = datos_json.get("datos_extraidos", {})
                resultados.append({
                    "tipo": tipo.replace("-", "_"),
                    "datos": extraidos,
                    "process_id": datos_json.get("metadata", {}).get("proceso_id"),
                    "caso_id": datos_json.get("metadata", {}).get("caso_id"),
                })
            except Exception as e:
                logger.error(f"Error leyendo {ruta}: {e}", exc_info=True)

    return resultados


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
    # Regla 0: Documento ilegible (dummy, podrías implementarlo)
    # -------------------------------------------------
    # for res in resultados:
    #     if not res.get("datos", {}).get("is_legible", True):
    #         status = "REJECTED"
    #         reasons.append({
    #             "code": "DOC_INVALID",
    #             "message": "Documento ilegible"
    #         })
    #         decision_log.append("Regla 0: Documento ilegible detectado → RECHAZADO")
    #         break

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
    # Regla 4: Edad fuera de rango (si existiera)
    # -------------------------------------------------
    edad_str = estudio_dict.get("VIV_edadSolicitante")
    min_age = getattr(settings, "min_age", 18)      # valores por defecto si no están en settings
    max_age = getattr(settings, "max_age", 75)

    try:
        if edad_str:
            edad = int(edad_str)
            if edad < min_age or edad > max_age:
                status = "REJECTED"
                reasons.append({
                    "code": "AGE_LIMIT",
                    "message": "Edad fuera de rango"
                })
                decision_log.append(
                    f"Regla 4: Edad {edad} fuera de rango "
                    f"({min_age}-{max_age}) → RECHAZADO"
                )
    except (ValueError, TypeError):
        pass

    # -------------------------------------------------
    # Regla 5: Score insuficiente (si existiera)
    # -------------------------------------------------
    score_str = estudio_dict.get("VIV_creditScore")
    min_score = getattr(settings, "min_credit_score", 600)

    try:
        if score_str:
            score = int(score_str)
            if score < min_score:
                status = "REJECTED"
                reasons.append({
                    "code": "CREDIT_SCORE_LOW",
                    "message": "Score insuficiente"
                })
                decision_log.append(
                    f"Regla 5: Score {score} < mínimo "
                    f"({min_score}) → RECHAZADO"
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
    """
    Sintetiza los resultados intermedios y genera tres Master JSON:
    - estudio_titulos: PanelFields + metadata (confianza, reasons, etc.)
    - minuta_cancelacion: solo PanelFields
    - minuta_constitucion: solo PanelFields

    Retorna un diccionario con las rutas de los archivos generados.
    """
    logger.info(f"Sintetizando {len(resultados)} documentos")

    if not resultados:
        logger.warning("No hay resultados para sintetizar")
        return {}

    # Datos comunes del caso
    caso_id = resultados[0].get("caso_id")  # podría venir en el resultado, sino extraer del path
    if not caso_id:
        # Intentar extraer del nombre de archivo o usar un valor por defecto
        caso_id = "desconocido"

    # Recolectar field_dicts por tipo
    field_dicts = {}
    panel_fields_por_tipo = {}

    for res in resultados:
        tipo = res["tipo"]
        datos = res["datos"]
        panel = datos.get("PanelFields", [])
        field_dicts[tipo] = panel_fields_to_dict(panel)
        panel_fields_por_tipo[tipo] = panel  # guardamos los originales sin prefijo

    # Calcular confianza (global, basada en todos los documentos)
    confianza = calcular_confianza(resultados)

    # Evaluar viabilidad (solo usando estudio_titulos)
    decision = evaluar_viabilidad(resultados, field_dicts)

    # Fecha de síntesis
    fecha_sintesis = datetime.utcnow().isoformat() + "Z"

    # Generar un master_id común para los tres archivos (basado en caso_id + timestamp)
    master_id = f"MASTER-{uuid.uuid4()}"

    rutas_generadas = {}

    # Tipos a procesar
    tipos_a_procesar = ["estudio_titulos", "minuta_cancelacion", "minuta_constitucion"]

    for tipo in tipos_a_procesar:
        if tipo not in panel_fields_por_tipo:
            logger.warning(f"No se encontraron datos para {tipo}, se omite")
            continue

        panel_original = panel_fields_por_tipo[tipo]
        # Agregar prefijo "3_" a cada InternalName
        panel_con_prefijo = add_prefix_to_panel_fields(panel_original)

        # Construir el objeto base
        master_obj = {
            "PanelFields": panel_con_prefijo
        }

        # Solo para estudio_titulos se agrega metadata
        if tipo == "estudio_titulos":
            master_obj["metadata"] = {
                "tipo_documento": tipo,
                "process_id": master_id,
                "caso_id": caso_id,
                "fecha_sintesis": fecha_sintesis,
                "confianza": confianza,
                "reasons": decision.get("reasons", [])
            }

        # Definir ruta en gold (y silver)
        gold_path = f"conecta/vivienda/master/{tipo}/{caso_id}/{master_id}.json"
        silver_path = gold_path.replace("gold", "silver")  # copia en silver

        # Guardar en gold
        datalake.write_json(settings.datalake_container_gold, gold_path, master_obj)
        # Copia en silver (opcional, para tener un respaldo)
        datalake.write_json(settings.datalake_container_silver, silver_path, master_obj)

        rutas_generadas[tipo] = {
            "gold": gold_path,
            "silver": silver_path
        }

        logger.info(f"Master JSON para {tipo} guardado en gold: {gold_path}")

    return rutas_generadas


def activity_generar_resumen_reducido(resultados: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    (Opcional) Genera un resumen reducido con los campos esenciales.
    Por ahora retorna el mismo master completo para mantener compatibilidad.
    """
    # Por simplicidad, llamamos a la síntesis completa y devolvemos solo las rutas
    return activity_sintetizar_resultados(resultados)