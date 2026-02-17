import logging
from typing import List

class ChunkingService:
    """Servicio para dividir textos largos en fragmentos con solapamiento."""

    def __init__(self, max_chars: int = 100000, overlap: int = 1000):
        self.max_chars = max_chars
        self.overlap = overlap
        self.logger = logging.getLogger(self.__class__.__name__)

    def chunk_text(self, text: str) -> List[str]:
        """Divide el texto en fragmentos que no excedan max_chars, con solapamiento."""
        if len(text) <= self.max_chars:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.max_chars
            if end > text_len:
                end = text_len
            else:
                # Buscar un límite de párrafo o frase para no cortar palabras
                # Buscamos el último punto y espacio antes de end
                last_period = text.rfind('. ', start, end)
                if last_period != -1 and last_period > start + self.max_chars // 2:
                    end = last_period + 1  # Incluir el punto
                else:
                    # Buscar último espacio
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1:
                        end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Mover inicio con solapamiento
            start = end - self.overlap
            if start < 0:
                start = 0

        self.logger.info(f"Texto dividido en {len(chunks)} fragmentos")
        return chunks