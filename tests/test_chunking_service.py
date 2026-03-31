from services.chunking_service import ChunkingService


def test_chunk_text_retorna_texto_unico_si_no_supera_limite():
    service = ChunkingService(max_chars=50, overlap=10)
    text = "texto corto"
    assert service.chunk_text(text) == [text]


def test_chunk_text_divide_texto_largo_y_preserva_orden():
    service = ChunkingService(max_chars=40, overlap=5)
    text = (
        "Primera oración suficientemente larga para cortar. "
        "Segunda oración también extensa para otro fragmento. "
        "Tercera oración final."
    )
    chunks = service.chunk_text(text)

    assert len(chunks) >= 2
    assert chunks[0].startswith("Primera")
    assert "Segunda" in " ".join(chunks)
    assert chunks[-1].endswith("final.")
    assert all(len(chunk) <= 40 for chunk in chunks)


def test_chunk_text_usa_espacios_cuando_no_hay_punto():
    service = ChunkingService(max_chars=20, overlap=3)
    text = "palabra1 palabra2 palabra3 palabra4 palabra5"
    chunks = service.chunk_text(text)

    assert len(chunks) >= 2
    assert all(len(chunk) <= 20 for chunk in chunks)


def test_chunk_text_no_loop_infinito_en_texto_con_espacios_y_overlap():
    """
    Anti-regresión:
    - Configuración agresiva (overlap casi igual a max_chars) que históricamente puede causar
      falta de avance si el algoritmo corta en un espacio exactamente en `start`.
    - El objetivo es asegurar que el algoritmo siempre progresa y termina.
    """
    service = ChunkingService(max_chars=10, overlap=9)
    text = "a b c d e f g h i j k l m n o"
    chunks = service.chunk_text(text)

    # Debe producir algo
    assert len(chunks) > 0

    # Sanity check: nunca debería explotar en miles de chunks para un texto tan pequeño
    assert len(chunks) < 1000

    # Guardrail extra: no deberían existir chunks idénticos consecutivos (síntoma de no-progreso)
    for i in range(1, len(chunks)):
        assert chunks[i] != chunks[i - 1]