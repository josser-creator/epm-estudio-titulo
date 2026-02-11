import re
import json
from typing import Any, Dict, List, Optional, Union


class JsonCleaner:
    """Utilidad para limpiar y normalizar datos JSON extraidos de documentos."""

    @staticmethod
    def clean_string(value: Optional[str]) -> Optional[str]:
        """
        Limpia una cadena de texto.

        Args:
            value: Cadena a limpiar.

        Returns:
            Cadena limpia o None si esta vacia.
        """
        if not value:
            return None

        # Remover espacios multiples
        cleaned = re.sub(r'\s+', ' ', str(value))
        # Remover espacios al inicio y final
        cleaned = cleaned.strip()
        # Retornar None si quedo vacio
        return cleaned if cleaned else None

    @staticmethod
    def clean_number(value: Optional[str]) -> Optional[str]:
        """
        Limpia un valor numerico manteniendo formato legible.

        Args:
            value: Valor numerico como string.

        Returns:
            Valor numerico limpio o None.
        """
        if not value:
            return None

        # Remover caracteres no numericos excepto . , - y espacios
        cleaned = str(value).strip()

        # Si esta vacio despues de limpiar
        if not cleaned:
            return None

        return cleaned

    @staticmethod
    def clean_currency(value: Optional[str]) -> Dict[str, Any]:
        """
        Extrae y normaliza un valor monetario.

        Args:
            value: Valor monetario como string (ej: "$50.000.000,00 COP").

        Returns:
            Dict con valor numerico y moneda.
        """
        if not value:
            return {"valor": None, "moneda": None, "original": None}

        original = str(value).strip()

        # Detectar moneda
        moneda = "COP"  # Default
        if "USD" in original.upper() or "DOLAR" in original.upper():
            moneda = "USD"
        elif "UVR" in original.upper():
            moneda = "UVR"
        elif "EUR" in original.upper():
            moneda = "EUR"

        # Extraer valor numerico
        # Remover simbolo de moneda y texto
        numero = re.sub(r'[^\d.,]', '', original)

        # Normalizar separadores (Colombia usa . para miles y , para decimales)
        # Detectar formato
        if ',' in numero and '.' in numero:
            # Formato colombiano: 1.000.000,00
            if numero.rfind(',') > numero.rfind('.'):
                numero = numero.replace('.', '').replace(',', '.')
            else:
                # Formato americano: 1,000,000.00
                numero = numero.replace(',', '')
        elif ',' in numero:
            # Solo comas - asumir formato colombiano
            numero = numero.replace(',', '.')

        try:
            valor_numerico = float(numero) if numero else None
        except ValueError:
            valor_numerico = None

        return {
            "valor": valor_numerico,
            "moneda": moneda,
            "original": original
        }

    @staticmethod
    def clean_date(value: Optional[str]) -> Optional[str]:
        """
        Normaliza una fecha manteniendo el formato original.

        Args:
            value: Fecha como string.

        Returns:
            Fecha limpia o None.
        """
        if not value:
            return None

        cleaned = str(value).strip()

        # Remover texto adicional comun
        cleaned = re.sub(r'\s*(del|de|ano|año)\s*', ' ', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned if cleaned else None

    @staticmethod
    def clean_identification(value: Optional[str]) -> Dict[str, Any]:
        """
        Limpia y extrae tipo y numero de identificacion.

        Args:
            value: Identificacion como string (ej: "C.C. 1.234.567").

        Returns:
            Dict con tipo y numero de identificacion.
        """
        if not value:
            return {"tipo": None, "numero": None, "original": None}

        original = str(value).strip().upper()

        # Detectar tipo de documento
        tipo = None
        if "NIT" in original:
            tipo = "NIT"
        elif "C.C" in original or "CC" in original or "CEDULA" in original:
            tipo = "CC"
        elif "C.E" in original or "CE" in original or "EXTRANJERIA" in original:
            tipo = "CE"
        elif "PASAPORTE" in original:
            tipo = "PASAPORTE"

        # Extraer numero
        numero = re.sub(r'[^\d\-]', '', original)

        return {
            "tipo": tipo,
            "numero": numero if numero else None,
            "original": original
        }

    @staticmethod
    def clean_percentage(value: Optional[str]) -> Optional[str]:
        """
        Limpia un porcentaje.

        Args:
            value: Porcentaje como string.

        Returns:
            Porcentaje limpio o None.
        """
        if not value:
            return None

        # Extraer numero y agregar %
        numero = re.sub(r'[^\d.,]', '', str(value))
        if numero:
            # Normalizar decimal
            numero = numero.replace(',', '.')
            return f"{numero}%"
        return None

    @staticmethod
    def clean_dict(data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """
        Limpia un diccionario completo.

        Args:
            data: Diccionario a limpiar.
            deep: Si True, limpia recursivamente.

        Returns:
            Diccionario limpio.
        """
        cleaned = {}

        for key, value in data.items():
            if value is None:
                cleaned[key] = None
            elif isinstance(value, str):
                cleaned[key] = JsonCleaner.clean_string(value)
            elif isinstance(value, dict) and deep:
                cleaned[key] = JsonCleaner.clean_dict(value, deep=True)
            elif isinstance(value, list) and deep:
                cleaned[key] = JsonCleaner.clean_list(value, deep=True)
            else:
                cleaned[key] = value

        return cleaned

    @staticmethod
    def clean_list(data: List[Any], deep: bool = True) -> List[Any]:
        """
        Limpia una lista.

        Args:
            data: Lista a limpiar.
            deep: Si True, limpia recursivamente.

        Returns:
            Lista limpia.
        """
        cleaned = []

        for item in data:
            if item is None:
                continue  # Omitir None en listas
            elif isinstance(item, str):
                clean_item = JsonCleaner.clean_string(item)
                if clean_item:
                    cleaned.append(clean_item)
            elif isinstance(item, dict) and deep:
                cleaned.append(JsonCleaner.clean_dict(item, deep=True))
            elif isinstance(item, list) and deep:
                cleaned.append(JsonCleaner.clean_list(item, deep=True))
            else:
                cleaned.append(item)

        return cleaned

    @staticmethod
    def remove_empty_values(data: Union[Dict, List]) -> Union[Dict, List]:
        """
        Remueve valores vacios de un diccionario o lista.

        Args:
            data: Diccionario o lista a limpiar.

        Returns:
            Estructura sin valores vacios.
        """
        if isinstance(data, dict):
            return {
                k: JsonCleaner.remove_empty_values(v)
                for k, v in data.items()
                if v is not None and v != "" and v != [] and v != {}
            }
        elif isinstance(data, list):
            return [
                JsonCleaner.remove_empty_values(item)
                for item in data
                if item is not None and item != "" and item != [] and item != {}
            ]
        else:
            return data

    @staticmethod
    def extract_json_from_text(text: str) -> Optional[Dict]:
        """
        Extrae JSON de un texto que puede contener contenido adicional.

        Args:
            text: Texto que contiene JSON.

        Returns:
            Diccionario parseado o None si no se encuentra JSON valido.
        """
        if not text:
            return None

        # Intentar parsear directamente
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Buscar JSON entre llaves
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Buscar JSON en bloques de codigo markdown
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        return None
