from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class EstudioTitulosSchema(BaseModel):
    """Schema plano para Estudio de Títulos, según campos requeridos."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )

    prestamo_direccion_matricula: Optional[str] = Field(
        None,
        alias="3_VIV_PrestamoDireccionMatricula",
        description="Número de matrícula inmobiliaria"
    )

    fecha_expedicion_matricula: Optional[str] = Field(
        None,
        alias="3_VIV_fechaExpedicionMatricula",
        description="Fecha de expedición de la matrícula"
    )

    prestamo_direccion: Optional[str] = Field(
        None,
        alias="3_VIV_PrestamoDireccion",
        description="Dirección del inmueble"
    )

    tipo_predio: Optional[str] = Field(
        None,
        alias="3_VIV_tipoPredio",
        description="Tipo de inmueble (casa, apartamento, lote, etc.)"
    )

    descripcion_linderos: Optional[str] = Field(
        None,
        alias="3_VIV_descripcionLinderos",
        description="Descripción de los linderos"
    )

    compradores: Optional[str] = Field(
        None,
        alias="3_VIV_Compradores",
        description="Nombres de los compradores/propietarios (separados por comas)"
    )

    identificacion_compradores: Optional[str] = Field(
        None,
        alias="3_VIV_identificacionCompradores",
        description="Identificaciones de los compradores (separadas por comas)"
    )

    titulo_adquisicion: Optional[str] = Field(
        None,
        alias="3_VIV_tituloAdquisicion",
        description="Título de adquisición del propietario actual"
    )

    gravamenes: Optional[str] = Field(
        None,
        alias="3_VIV_gravamenes",
        description="Descripción de los gravámenes vigentes"
    )

    limitacion_dominio: Optional[str] = Field(
        None,
        alias="3_VIV_limitacionDominio",
        description="Limitaciones al dominio"
    )

    afectacion_dominio: Optional[str] = Field(
        None,
        alias="3_VIV_afectacionDominio",
        description="Afectaciones al dominio distintas de gravámenes"
    )

    medida_cautelar: Optional[str] = Field(
        None,
        alias="3_VIV_medidaCautelar",
        description="Medidas cautelares vigentes"
    )

    tenencia: Optional[str] = Field(
        None,
        alias="3_VIV_tenencia",
        description="Información sobre la tenencia"
    )

    documentos_revisados: Optional[str] = Field(
        None,
        alias="3_VIV_documentosRevisados",
        description="Documentos revisados en el estudio"
    )
    