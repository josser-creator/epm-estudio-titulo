from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MetadataBase(BaseModel):
    """Metadata base comun para todos los documentos."""

    fecha_procesamiento: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Fecha y hora de procesamiento del documento"
    )
    nombre_archivo_origen: Optional[str] = Field(
        default=None,
        description="Nombre del archivo PDF original"
    )
    ruta_archivo_origen: Optional[str] = Field(
        default=None,
        description="Ruta completa del archivo PDF original"
    )


class BaseDocumentSchema(BaseModel):
    """Schema base para todos los documentos procesados."""

    class Config:
        populate_by_name = True
        str_strip_whitespace = True
        json_schema_extra = {
            "example": {}
        }
