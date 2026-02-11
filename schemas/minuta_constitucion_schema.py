from typing import List, Optional
from pydantic import BaseModel, Field

from .base_schema import BaseDocumentSchema


class MetadataMinutaConstitucion(BaseModel):
    """Metadata especifica de la minuta de constitucion."""

    numero_escritura: Optional[str] = Field(
        default=None,
        description="Numero de escritura publica"
    )
    fecha: Optional[str] = Field(
        default=None,
        description="Fecha de la escritura"
    )
    notaria: Optional[str] = Field(
        default=None,
        description="Notaria donde se otorga"
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad de la notaria"
    )
    departamento: Optional[str] = Field(
        default=None,
        description="Departamento"
    )


class AcreedorHipotecario(BaseModel):
    """Informacion del acreedor hipotecario."""

    nombre: Optional[str] = Field(
        default=None,
        description="Razon social del acreedor"
    )
    tipo_entidad: Optional[str] = Field(
        default=None,
        description="Tipo de entidad (banco, cooperativa, etc.)"
    )
    nit: Optional[str] = Field(
        default=None,
        description="NIT del acreedor"
    )
    representante_legal: Optional[str] = Field(
        default=None,
        description="Nombre del representante legal"
    )
    identificacion_representante: Optional[str] = Field(
        default=None,
        description="Cedula del representante legal"
    )
    direccion: Optional[str] = Field(
        default=None,
        description="Direccion de la entidad"
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad de la entidad"
    )


class DeudorHipotecario(BaseModel):
    """Informacion del deudor hipotecario."""

    nombre: Optional[str] = Field(
        default=None,
        description="Nombre completo del deudor"
    )
    tipo_identificacion: Optional[str] = Field(
        default=None,
        description="Tipo de documento"
    )
    identificacion: Optional[str] = Field(
        default=None,
        description="Numero de identificacion"
    )
    estado_civil: Optional[str] = Field(
        default=None,
        description="Estado civil"
    )
    direccion: Optional[str] = Field(
        default=None,
        description="Direccion de residencia"
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad de residencia"
    )
    telefono: Optional[str] = Field(
        default=None,
        description="Telefono de contacto"
    )
    correo_electronico: Optional[str] = Field(
        default=None,
        description="Correo electronico"
    )
    es_codeudor: Optional[bool] = Field(
        default=False,
        description="Indica si es codeudor"
    )


class CondicionesCredito(BaseModel):
    """Condiciones del credito hipotecario."""

    monto_credito: Optional[str] = Field(
        default=None,
        description="Monto del credito"
    )
    moneda: Optional[str] = Field(
        default=None,
        description="Moneda del credito"
    )
    monto_en_letras: Optional[str] = Field(
        default=None,
        description="Monto del credito en letras"
    )
    plazo_meses: Optional[str] = Field(
        default=None,
        description="Plazo del credito en meses"
    )
    plazo_anos: Optional[str] = Field(
        default=None,
        description="Plazo del credito en anos"
    )
    tasa_interes: Optional[str] = Field(
        default=None,
        description="Tasa de interes pactada"
    )
    tipo_tasa: Optional[str] = Field(
        default=None,
        description="Tipo de tasa (fija, variable, DTF, etc.)"
    )
    spread: Optional[str] = Field(
        default=None,
        description="Spread o puntos adicionales"
    )
    tasa_mora: Optional[str] = Field(
        default=None,
        description="Tasa de interes moratorio"
    )
    destino_credito: Optional[str] = Field(
        default=None,
        description="Destino del credito (vivienda, libre inversion, etc.)"
    )
    linea_credito: Optional[str] = Field(
        default=None,
        description="Linea de credito"
    )
    sistema_amortizacion: Optional[str] = Field(
        default=None,
        description="Sistema de amortizacion (cuota fija, UVR, etc.)"
    )
    valor_cuota: Optional[str] = Field(
        default=None,
        description="Valor de la cuota mensual"
    )
    fecha_primer_pago: Optional[str] = Field(
        default=None,
        description="Fecha del primer pago"
    )


class InmuebleHipotecado(BaseModel):
    """Informacion del inmueble a hipotecar."""

    matricula_inmobiliaria: Optional[str] = Field(
        default=None,
        description="Numero de matricula inmobiliaria"
    )
    circulo_registral: Optional[str] = Field(
        default=None,
        description="Circulo registral"
    )
    direccion: Optional[str] = Field(
        default=None,
        description="Direccion del inmueble"
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad"
    )
    departamento: Optional[str] = Field(
        default=None,
        description="Departamento"
    )
    tipo_inmueble: Optional[str] = Field(
        default=None,
        description="Tipo de inmueble"
    )
    area_construida: Optional[str] = Field(
        default=None,
        description="Area construida en m2"
    )
    area_terreno: Optional[str] = Field(
        default=None,
        description="Area del terreno en m2"
    )
    linderos: Optional[str] = Field(
        default=None,
        description="Descripcion de linderos"
    )
    estrato: Optional[str] = Field(
        default=None,
        description="Estrato socioeconomico"
    )
    avaluo_comercial: Optional[str] = Field(
        default=None,
        description="Valor del avaluo comercial"
    )
    fecha_avaluo: Optional[str] = Field(
        default=None,
        description="Fecha del avaluo"
    )
    perito_avaluador: Optional[str] = Field(
        default=None,
        description="Nombre del perito avaluador"
    )


class CondicionesGarantia(BaseModel):
    """Condiciones y clausulas de la garantia hipotecaria."""

    tipo_garantia: Optional[str] = Field(
        default=None,
        description="Tipo de garantia (hipoteca abierta, cerrada)"
    )
    grado_hipoteca: Optional[str] = Field(
        default=None,
        description="Grado de la hipoteca (primero, segundo)"
    )
    clausula_aceleracion: Optional[bool] = Field(
        default=None,
        description="Incluye clausula de aceleracion"
    )
    clausula_venta_judicial: Optional[bool] = Field(
        default=None,
        description="Incluye clausula de venta judicial"
    )
    seguro_incendio_terremoto: Optional[bool] = Field(
        default=None,
        description="Requiere seguro contra incendio y terremoto"
    )
    seguro_vida_deudores: Optional[bool] = Field(
        default=None,
        description="Requiere seguro de vida de deudores"
    )
    aseguradora: Optional[str] = Field(
        default=None,
        description="Compania aseguradora"
    )
    numero_poliza: Optional[str] = Field(
        default=None,
        description="Numero de poliza de seguros"
    )
    prohibicion_enajenar: Optional[bool] = Field(
        default=None,
        description="Prohibicion de enajenar sin autorizacion"
    )
    prohibicion_arrendar: Optional[bool] = Field(
        default=None,
        description="Prohibicion de arrendar sin autorizacion"
    )
    otras_prohibiciones: List[str] = Field(
        default_factory=list,
        description="Otras prohibiciones o restricciones"
    )


class MinutaConstitucionSchema(BaseDocumentSchema):
    """Schema completo para Minuta de Constitucion de Hipoteca."""

    metadata: MetadataMinutaConstitucion = Field(
        default_factory=MetadataMinutaConstitucion,
        description="Metadata de la minuta de constitucion"
    )
    acreedor: AcreedorHipotecario = Field(
        default_factory=AcreedorHipotecario,
        description="Informacion del acreedor hipotecario"
    )
    deudores: List[DeudorHipotecario] = Field(
        default_factory=list,
        description="Lista de deudores e hipotecantes"
    )
    credito: CondicionesCredito = Field(
        default_factory=CondicionesCredito,
        description="Condiciones del credito"
    )
    inmuebles: List[InmuebleHipotecado] = Field(
        default_factory=list,
        description="Inmuebles objeto de la hipoteca"
    )
    condiciones_garantia: CondicionesGarantia = Field(
        default_factory=CondicionesGarantia,
        description="Condiciones y clausulas de la garantia"
    )
    declaraciones_deudor: Optional[str] = Field(
        default=None,
        description="Declaraciones del deudor"
    )
    autorizaciones: Optional[str] = Field(
        default=None,
        description="Autorizaciones otorgadas"
    )
    observaciones: Optional[str] = Field(
        default=None,
        description="Observaciones adicionales"
    )
