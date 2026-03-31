import logging
from typing import List


class ChunkingService:
    """Servicio para dividir textos largos en fragmentos con solapamiento."""

    def __init__(self, max_chars: int = 100000, overlap: int = 1000):
        if max_chars <= 0:
            raise ValueError("max_chars debe ser > 0")
        if overlap < 0:
            raise ValueError("overlap debe ser >= 0")

        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_chars = int(max_chars)
        self.overlap = int(overlap)

        # Evita configuraciones inválidas que puedan bloquear el avance
        if self.overlap >= self.max_chars:
            self.logger.warning(
                "overlap (%s) >= max_chars (%s). Ajustando overlap a max_chars - 1.",
                self.overlap,
                self.max_chars,
            )
            self.overlap = max(0, self.max_chars - 1)

    def chunk_text(self, text: str) -> List[str]:
        """Divide el texto en fragmentos que no excedan max_chars, con solapamiento."""
        if text is None:
            return []

        text = str(text)
        if len(text) <= self.max_chars:
            return [text]

        chunks: List[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end_limit = min(start + self.max_chars, text_len)
            end = end_limit

            # Si no estamos en el último segmento, intenta cortar "bonito"
            if end_limit < text_len:
                last_period = text.rfind(". ", start, end_limit)
                if last_period != -1 and last_period > start + (self.max_chars // 2):
                    end = last_period + 1  # incluye el punto
                else:
                    last_space = text.rfind(" ", start, end_limit)
                    if last_space != -1 and last_space > start:
                        end = last_space

            # Invariante: end debe ser > start (progreso)
            if end <= start:
                end = end_limit
                if end <= start:
                    end = min(start + 1, text_len)

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # ---------------------------
            # ✅ PROGRESO + OVERLAP SEGURO
            # ---------------------------
            next_start = max(0, end - self.overlap)

            # ✅ Alinear a inicio de palabra (evita "inal." por caer dentro de "final.")
            if 0 < next_start < text_len:
                # Si estamos en medio de una palabra (no whitespace antes y no whitespace en el índice)
                if (not text[next_start].isspace()) and (not text[next_start - 1].isspace()):
                    while next_start > 0 and not text[next_start - 1].isspace():
                        next_start -= 1

            # Garantiza avance; si no avanza, elimina overlap en esa transición
            if next_start <= start:
                next_start = end

            start = next_start

        self.logger.info("Texto dividido en %s fragmentos", len(chunks))
        return chunks