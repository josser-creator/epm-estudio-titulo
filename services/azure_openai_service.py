import json
from typing import Optional, Type
from openai import AzureOpenAI
from pydantic import BaseModel

from .base_service import BaseService
from config import get_settings


class AzureOpenAIService(BaseService):
    """Servicio para procesar texto usando Azure OpenAI GPT-4o."""

    def __init__(self):
        super().__init__()
        self._client: Optional[AzureOpenAI] = None
        self._settings = get_settings()
        self.initialize()

    def initialize(self) -> None:
        """Inicializa el cliente de Azure OpenAI."""
        try:
            self._client = AzureOpenAI(
                api_key=self._settings.azure_openai_key,
                api_version=self._settings.azure_openai_api_version,
                azure_endpoint=self._settings.azure_openai_endpoint
            )
            self._log_info("Azure OpenAI client initialized successfully")
        except Exception as e:
            self._log_error("Failed to initialize Azure OpenAI client", error=e)
            raise

    def health_check(self) -> bool:
        """Verifica que el servicio este disponible."""
        return self._client is not None

    def extract_structured_data(
        self,
        document_text: str,
        system_prompt: str,
        schema_class: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> dict:
        """
        Extrae datos estructurados del texto usando GPT-4o.

        Args:
            document_text: Texto del documento a procesar.
            system_prompt: Prompt del sistema con instrucciones de extraccion.
            schema_class: Clase Pydantic que define el schema esperado.
            temperature: Temperatura para la generacion (0.0-1.0).
            max_tokens: Maximo de tokens en la respuesta.

        Returns:
            dict: Datos estructurados extraidos del documento,
                  con las claves en el formato de alias definido en el schema.
        """
        try:
            schema_json = schema_class.model_json_schema()

            user_prompt = self._build_extraction_prompt(document_text, schema_json)

            self._log_info("Sending request to Azure OpenAI for data extraction")

            response = self._client.chat.completions.create(
                model=self._settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            response_content = response.choices[0].message.content
            extracted_data = json.loads(response_content)

            # Validar contra el schema Pydantic
            validated_data = schema_class.model_validate(extracted_data)

            self._log_info(
                "Data extraction completed successfully",
                tokens_used=response.usage.total_tokens if response.usage else 0
            )

            # Usar by_alias=True para exportar con los alias definidos
            return validated_data.model_dump(by_alias=True, exclude_none=False)

        except json.JSONDecodeError as e:
            self._log_error("Failed to parse JSON response", error=e)
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            self._log_error("Data extraction failed", error=e)
            raise

    def _build_extraction_prompt(self, document_text: str, schema: dict) -> str:
        """
        Construye el prompt de extraccion con el texto y schema.

        Args:
            document_text: Texto del documento.
            schema: Schema JSON esperado.

        Returns:
            str: Prompt formateado para la extraccion.
        """
        return f"""
Analiza el siguiente documento y extrae la informacion estructurada segun el schema JSON proporcionado.

## DOCUMENTO:
{document_text}

## SCHEMA JSON ESPERADO:
{json.dumps(schema, indent=2, ensure_ascii=False)}

## INSTRUCCIONES:
1. Extrae TODA la informacion relevante del documento que coincida con los campos del schema.
2. Si un campo no se encuentra en el documento, usa null o una cadena vacia segun corresponda.
3. Para listas, incluye todos los elementos encontrados.
4. Mantén los formatos de fecha, numeros y montos tal como aparecen en el documento.
5. Responde UNICAMENTE con el JSON estructurado, sin texto adicional.

## RESPUESTA JSON:
"""

    def analyze_with_custom_prompt(
        self,
        text: str,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """
        Analiza texto con un prompt personalizado.

        Args:
            text: Texto a analizar.
            prompt: Prompt personalizado.
            temperature: Temperatura para la generacion.
            max_tokens: Maximo de tokens en la respuesta.

        Returns:
            str: Respuesta del modelo.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": text}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content

        except Exception as e:
            self._log_error("Custom analysis failed", error=e)
            raise
