from typing import Type
from pydantic import BaseModel

from .base_processor import BaseDocumentProcessor
from schemas import MinutaConstitucionSchema
from prompts import MINUTA_CONSTITUCION_SYSTEM_PROMPT


class MinutaConstitucionProcessor(BaseDocumentProcessor):
    """Procesador especializado para documentos de Minuta de Constitucion de Hipoteca."""

    @property
    def system_name(self) -> str:
        return "minuta_constitucion"

    @property
    def system_prompt(self) -> str:
        return MINUTA_CONSTITUCION_SYSTEM_PROMPT

    @property
    def schema_class(self) -> Type[BaseModel]:
        return MinutaConstitucionSchema

    def _validate_extracted_data(self, data: dict) -> dict:
        """
        Validaciones especificas para Minuta de Constitucion.

        Args:
            data: Datos extraidos a validar.

        Returns:
            dict: Datos validados.
        """
        # Validar datos del acreedor
        acreedor = data.get("acreedor", {})
        if not acreedor.get("nombre"):
            self.logger.warning("No se identifico el nombre del acreedor hipotecario")

        if not acreedor.get("nit"):
            self.logger.warning("No se encontro NIT del acreedor")

        # Validar datos del credito
        credito = data.get("credito", {})
        campos_credito_requeridos = ["monto_credito", "plazo_meses", "tasa_interes"]
        campos_faltantes = [c for c in campos_credito_requeridos if not credito.get(c)]

        if campos_faltantes:
            self.logger.warning(f"Campos de credito faltantes: {campos_faltantes}")

        # Validar inmuebles
        inmuebles = data.get("inmuebles", [])
        if not inmuebles:
            self.logger.warning("No se encontraron inmuebles a hipotecar")

        for i, inmueble in enumerate(inmuebles):
            if not inmueble.get("matricula_inmobiliaria"):
                self.logger.warning(f"Inmueble {i+1}: sin matricula inmobiliaria")

        # Validar deudores
        deudores = data.get("deudores", [])
        if not deudores:
            self.logger.warning("No se encontraron deudores en el documento")

        deudores_principales = [d for d in deudores if not d.get("es_codeudor", False)]
        codeudores = [d for d in deudores if d.get("es_codeudor", False)]

        # Validar condiciones de garantia
        condiciones = data.get("condiciones_garantia", {})

        # Crear resumen de la constitucion
        data["_resumen_constitucion"] = {
            "acreedor": acreedor.get("nombre", "No identificado"),
            "tipo_entidad": acreedor.get("tipo_entidad", "Banco"),
            "cantidad_deudores_principales": len(deudores_principales),
            "cantidad_codeudores": len(codeudores),
            "cantidad_inmuebles": len(inmuebles),
            "monto_credito": credito.get("monto_credito", "No especificado"),
            "plazo": credito.get("plazo_meses") or credito.get("plazo_anos", "No especificado"),
            "tasa_interes": credito.get("tasa_interes", "No especificada"),
            "destino_credito": credito.get("destino_credito", "No especificado"),
            "tipo_garantia": condiciones.get("tipo_garantia", "Hipoteca"),
            "grado_hipoteca": condiciones.get("grado_hipoteca", "Primer grado"),
            "matriculas_hipotecadas": [
                inm.get("matricula_inmobiliaria", "N/A")
                for inm in inmuebles
                if inm.get("matricula_inmobiliaria")
            ],
            "deudores_nombres": [
                d.get("nombre", "N/A")
                for d in deudores_principales
                if d.get("nombre")
            ]
        }

        # Calcular LTV (Loan to Value) si hay datos de avaluo
        total_avaluo = 0
        for inmueble in inmuebles:
            avaluo = inmueble.get("avaluo_comercial", "0")
            if avaluo:
                try:
                    # Limpiar el valor (remover $ , . y convertir)
                    avaluo_limpio = avaluo.replace("$", "").replace(".", "").replace(",", "").strip()
                    total_avaluo += float(avaluo_limpio)
                except (ValueError, AttributeError):
                    pass

        monto = credito.get("monto_credito", "0")
        if monto and total_avaluo > 0:
            try:
                monto_limpio = monto.replace("$", "").replace(".", "").replace(",", "").strip()
                monto_num = float(monto_limpio)
                ltv = (monto_num / total_avaluo) * 100
                data["_resumen_constitucion"]["ltv_estimado"] = f"{ltv:.2f}%"
            except (ValueError, AttributeError):
                pass

        # Resumen de seguros requeridos
        seguros_requeridos = []
        if condiciones.get("seguro_incendio_terremoto"):
            seguros_requeridos.append("Incendio y Terremoto")
        if condiciones.get("seguro_vida_deudores"):
            seguros_requeridos.append("Vida Deudores")

        data["_resumen_constitucion"]["seguros_requeridos"] = seguros_requeridos

        return data
