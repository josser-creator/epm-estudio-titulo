from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MinutaCancelacionSchema(BaseModel):
    """Schema plano para Minuta de Cancelación de Hipoteca."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )

    resolucion_nombramiento: Optional[str] = Field(
        None,
        alias="3_VIV_resolucionNombramiento",
        description="Resolución del nombramiento del líder experiencia"
    )

    numero_escritura_publica: Optional[str] = Field(
        None,
        alias="3_VIV_numeroEscrituraPublica",
        description="Número de escritura pública de cancelación"
    )

    fecha_escritura_publica: Optional[str] = Field(
        None,
        alias="3_VIV_fechaEscrituraPublica",
        description="Fecha de la escritura"
    )

    notaria_escritura_publica: Optional[str] = Field(
        None,
        alias="3_VIV_notariaEscrituraPublica",
        description="Notaría donde se otorgó"
    )

    folio_matricula_inmobiliaria: Optional[str] = Field(
        None,
        alias="3_VIV_folioMatriculaInmobiliaria",
        description="Número de folio/matricula inmobiliaria"
    )

    oficina_matricula_inmobiliaria: Optional[str] = Field(
        None,
        alias="3_VIV_oficinaMatriculaInmobiliaria",
        description="Oficina de expedición de la matrícula"
    )

    direccion_inmueble: Optional[str] = Field(
        None,
        alias="3_VIV_direccionInmueble",
        description="Dirección del inmueble"
    )
    