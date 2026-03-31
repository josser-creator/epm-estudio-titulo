from pydantic import BaseModel
from services.azure_openai_service import AzureOpenAIService


class DemoSchema(BaseModel):
    nombre: str | None = None
    tags: list[str] = []
    nested: dict = {}


def test_deep_merge_combina_dicts_y_listas_sin_duplicar():
    service = AzureOpenAIService()
    target = {"nombre": "base", "tags": ["a"], "nested": {"x": 1}}
    source = {"nombre": "nuevo", "tags": ["a", "b"], "nested": {"y": 2}}
    service._deep_merge(target, source)
    assert target == {"nombre": "base", "tags": ["a", "b"], "nested": {"x": 1, "y": 2}}


def test_extract_with_chunking_fusiona_fragmentos(monkeypatch):
    service = AzureOpenAIService()
    monkeypatch.setattr(service.chunker, "chunk_text", lambda text: ["chunk-1", "chunk-2"])
    responses = [
        {"nombre": "documento", "tags": ["uno"], "nested": {"x": 1}},
        {"tags": ["uno", "dos"], "nested": {"y": 2}},
    ]

    def fake_extract_single(text, system_prompt, schema_class, temperature, max_tokens):
        return responses.pop(0)

    monkeypatch.setattr(service, "_extract_single", fake_extract_single)
    result = service._extract_with_chunking("texto largo", "prompt", DemoSchema, 0.1, 300)
    assert result == {"nombre": "documento", "tags": ["uno", "dos"], "nested": {"x": 1, "y": 2}}
