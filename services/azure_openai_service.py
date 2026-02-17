import json
import logging
from typing import Optional, Type, List
from openai import AzureOpenAI
from pydantic import BaseModel, ValidationError

from .base_service import BaseService
from config import get_settings
from .chunking_service import ChunkingService


class AzureOpenAIService(BaseService):
    def __init__(self):
        super().__init__()
        self._client: Optional[AzureOpenAI] = None
        self._settings = get_settings()
        self.chunker = ChunkingService(
            max_chars=self._settings.chunk_max_characters,
            overlap=self._settings.chunk_overlap
        )
        self.initialize()

    def initialize(self) -> None:
        try:
            self._client = AzureOpenAI(
                api_key=self._settings.azure_openai_key,
                api_version=self._settings.azure_openai_api_version,
                azure_endpoint=self._settings.azure_openai_endpoint
            )
            self._log_info("Azure OpenAI client initialized")
        except Exception as e:
            self._log_error("Failed to initialize Azure OpenAI", error=e)
            raise

    def health_check(self) -> bool:
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
        Extrae datos estructurados del texto, con chunking automático si es necesario.
        """
        # Verificar si necesita chunking
        if len(document_text) > self._settings.chunk_max_characters:
            self._log_info("Texto muy largo, aplicando chunking")
            return self._extract_with_chunking(
                document_text, system_prompt, schema_class, temperature, max_tokens
            )

        # Extracción directa
        return self._extract_single(document_text, system_prompt, schema_class, temperature, max_tokens)

    def _extract_single(self, text: str, system_prompt: str, schema_class: Type[BaseModel],
                        temperature: float, max_tokens: int) -> dict:
        user_prompt = self._build_extraction_prompt(text, schema_class.model_json_schema())
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
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            validated = schema_class.model_validate(data)
            return validated.model_dump(by_alias=True, exclude_none=False)
        except (json.JSONDecodeError, ValidationError) as e:
            self._log_error("Error parsing/extracting single chunk", error=e)
            raise

    def _extract_with_chunking(self, full_text: str, system_prompt: str,
                               schema_class: Type[BaseModel], temperature: float,
                               max_tokens: int) -> dict:
        """
        Divide el texto, extrae de cada fragmento y luego combina los resultados.
        """
        chunks = self.chunker.chunk_text(full_text)
        chunk_results = []
        for i, chunk in enumerate(chunks):
            self._log_info(f"Procesando fragmento {i+1}/{len(chunks)}")
            try:
                result = self._extract_single(chunk, system_prompt, schema_class, temperature, max_tokens)
                chunk_results.append(result)
            except Exception as e:
                self._log_error(f"Error en fragmento {i+1}", error=e)
                # Continuamos con los demás fragmentos, o podríamos lanzar excepción
                # Aquí optamos por continuar y luego combinar lo que se pudo extraer
                chunk_results.append({})

        # Combinar resultados: tomar el primer resultado no vacío como base y fusionar
        # Estrategia simple: elegir el que tenga más campos, o pedir a OpenAI que fusione.
        # Implementaremos una fusión por prioridad: si un campo aparece en varios, tomar el de mayor confianza (no tenemos).
        # En su lugar, usamos un merge recursivo simple.
        merged = {}
        for res in chunk_results:
            if not res:
                continue
            self._deep_merge(merged, res)

        # Validar contra el schema
        try:
            validated = schema_class.model_validate(merged)
            return validated.model_dump(by_alias=True, exclude_none=False)
        except ValidationError as e:
            self._log_error("Error validando resultado fusionado", error=e)
            # Devolvemos lo que tenemos aunque no sea válido según schema
            return merged

    def _deep_merge(self, target: dict, source: dict) -> None:
        """Fusiona source en target recursivamente."""
        for key, value in source.items():
            if key not in target:
                target[key] = value
            else:
                if isinstance(value, dict) and isinstance(target[key], dict):
                    self._deep_merge(target[key], value)
                elif isinstance(value, list) and isinstance(target[key], list):
                    # Para listas, concatenar (evitando duplicados simples)
                    target[key].extend([x for x in value if x not in target[key]])
                else:
                    # Si hay conflicto, mantener el valor existente (primero)
                    pass

    def _build_extraction_prompt(self, text: str, schema: dict) -> str:
        return f"""
Analiza el siguiente documento y extrae la información estructurada según el schema JSON proporcionado.

## DOCUMENTO:
{text}

## SCHEMA JSON ESPERADO:
{json.dumps(schema, indent=2, ensure_ascii=False)}

## INSTRUCCIONES:
1. Extrae TODA la información relevante del documento que coincida con los campos del schema.
2. Si un campo no se encuentra, usa null o cadena vacía.
3. Para listas, incluye todos los elementos encontrados.
4. Mantén los formatos originales.
5. Responde UNICAMENTE con el JSON estructurado.

## RESPUESTA JSON:
"""
    