from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class MinutaConstitucionSchema(BaseModel):
    """Schema plano para Minuta de Constitución de Hipoteca."""

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )

    valor_comercial: Optional[float] = Field(
        None, alias="3_TPC_ValorComercial",
        description="Valor de compraventa del inmueble"
    )
    grado_hipoteca: Optional[str] = Field(
        None, alias="3_VIV_gradoHipoteca",
        description="Grado de la hipoteca (primero, segundo, etc.)"
    )
    valor_prestamo: Optional[float] = Field(
        None, alias="3_GBL_Valordeprestamo",
        description="Monto del préstamo hipotecario"
    )
    nombre_vendedor: Optional[str] = Field(
        None, alias="3_VIV_nombreVendedor",
        description="Nombre del vendedor"
    )
    compradores: Optional[str] = Field(
        None, alias="3_VIV_Compradores",
        description="Nombres de los compradores/deudores (separados por comas)"
    )
    valor_cesantias: Optional[float] = Field(
        None, alias="3_VIV_valorCesantias",
        description="Monto de cesantías utilizadas"
    )
    recursos_propios: Optional[str] = Field(
        None, alias="3_VIV_recursosPropios",
        description="Recursos propios aportados"
    )
    identificacion_compradores: Optional[str] = Field(
        None, alias="3_VIV_identificacionCompradores",
        description="Identificaciones de los compradores (separadas por comas)"
    )
    valor_en_letras_primer_parrafo: Optional[str] = Field(
        None, alias="3_BO_Valor en letras",
        description="Valor del préstamo en letras (primer párrafo)"
    )
    numero_cuotas: Optional[str] = Field(
        None, alias="3_VIV_numeroCuotas",
        description="Número de cuotas"
    )
    numero_cuotas_letras: Optional[str] = Field(
        None, alias="3_VIV_numeroCuotasLetras",
        description="Número de cuotas en letras"
    )
    valor_cuotas: Optional[str] = Field(
        None, alias="3_VIV_valorCuotas",
        description="Valor de las cuotas"
    )
    valor_cuotas_letras: Optional[str] = Field(
        None, alias="3_VIV_valorCuotasLetras",
        description="Valor de las cuotas en letras"
    )
    oferta_valor_letras: Optional[str] = Field(
        None, alias="3_VIV_OfertaValorLetras",
        description="Valor del préstamo en letras (segundo párrafo)"
    )
    