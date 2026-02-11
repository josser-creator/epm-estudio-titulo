from typing import List, Optional
from pydantic import BaseModel, Field

from .base_schema import BaseDocumentSchema


class MetadataMinutaCancelacion(BaseModel):
    """Metadata especifica de la minuta de cancelacion."""

    numero_escritura: Optional[str] = Field(
        default=None,
        alias="VIV_numeroEscrituraPublica",      
        description="Numero de escritura publica de cancelacion"
    )
    fecha: Optional[str] = Field(
        default=None,
        alias="VIV_fechaEscrituraPublica",       
        description="Fecha de la escritura de cancelacion"
    )
    notaria: Optional[str] = Field(
        default=None,
        alias="VIV_notariaEscrituraPublica",     
        description="Notaria donde se otorga la cancelacion"
    )
    # --- NUEVO CAMPO ---
    resolucion_nombramiento: Optional[str] = Field(
        default=None,
        alias="VIV_resolucionNombramiento",      
        description="Resolucion del nombramiento del lider experiencia empleado"
    )
    ciudad: Optional[str] = Field(
        default=None,
        alias="VIV_ciudadNotaria",              
        description="Ciudad de la notaria"
    )
    departamento: Optional[str] = Field(
        default=None,
        alias="VIV_departamentoNotaria",        
        description="Departamento"
    )


class Acreedor(BaseModel):
    """Informacion del acreedor (entidad financiera)."""

    nombre: Optional[str] = Field(
        default=None,
        alias="VIV_nombreAcreedor",             
        description="Razon social del acreedor"
    )
    tipo_identificacion: Optional[str] = Field(
        default=None,
        alias="VIV_tipoIdentificacionAcreedor",
        description="Tipo de identificacion (NIT, CC)"
    )
    nit_cc: Optional[str] = Field(
        default=None,
        alias="VIV_nitAcreedor",               
        description="NIT o cedula del acreedor"
    )
    representante_legal: Optional[str] = Field(
        default=None,
        alias="VIV_representanteLegalAcreedor",
        description="Nombre del representante legal"
    )
    identificacion_representante: Optional[str] = Field(
        default=None,
        alias="VIV_identificacionRepresentante",
        description="Cedula del representante legal"
    )
    cargo_representante: Optional[str] = Field(
        default=None,
        alias="VIV_cargoRepresentante",
        description="Cargo del representante"
    )
    poder_otorgado_por: Optional[str] = Field(
        default=None,
        alias="VIV_poderOtorgadoPor",
        description="Entidad que otorgo el poder"
    )
    numero_poder: Optional[str] = Field(
        default=None,
        alias="VIV_numeroPoder",
        description="Numero del poder"
    )


class Deudor(BaseModel):
    """Informacion del deudor."""

    nombre: Optional[str] = Field(
        default=None,
        alias="VIV_nombreDeudor",              
        description="Nombre completo del deudor"
    )
    tipo_identificacion: Optional[str] = Field(
        default=None,
        alias="VIV_tipoIdentificacionDeudor",
        description="Tipo de documento"
    )
    identificacion: Optional[str] = Field(
        default=None,
        alias="VIV_identificacionDeudor",
        description="Numero de identificacion del deudor"
    )
    estado_civil: Optional[str] = Field(
        default=None,
        alias="VIV_estadoCivilDeudor",
        description="Estado civil del deudor"
    )


class ObligacionCancelada(BaseModel):
    """Informacion de la obligacion que se cancela."""

    tipo: Optional[str] = Field(
        default=None,
        alias="VIV_tipoObligacion",
        description="Tipo de obligacion (hipoteca, prenda, etc.)"
    )
    numero_credito: Optional[str] = Field(
        default=None,
        alias="VIV_numeroCredito",
        description="Numero del credito u obligacion"
    )
    monto_original: Optional[str] = Field(
        default=None,
        alias="VIV_montoOriginalObligacion",
        description="Monto original de la obligacion"
    )
    moneda: Optional[str] = Field(
        default=None,
        alias="VIV_monedaObligacion",
        description="Moneda de la obligacion"
    )
    fecha_constitucion: Optional[str] = Field(
        default=None,
        alias="VIV_fechaConstitucionObligacion",
        description="Fecha de constitucion de la garantia"
    )
    escritura_constitucion: Optional[str] = Field(
        default=None,
        alias="VIV_escrituraConstitucion",
        description="Numero de escritura de constitucion"
    )
    notaria_constitucion: Optional[str] = Field(
        default=None,
        alias="VIV_notariaConstitucion",
        description="Notaria de la escritura de constitucion"
    )
    numero_anotacion: Optional[str] = Field(
        default=None,
        alias="VIV_numeroAnotacionObligacion",
        description="Numero de anotacion en el folio de matricula"
    )


class InmuebleGarantia(BaseModel):
    """Informacion del inmueble que servia como garantia."""

    matricula_inmobiliaria: Optional[str] = Field(
        default=None,
        alias="VIV_folioMatriculaInmobiliaria",   
        description="Numero de folio / matricula inmobiliaria"
    )
    # --- NUEVO CAMPO ---
    oficina_matricula: Optional[str] = Field(
        default=None,
        alias="VIV_oficinaMatriculaInmobiliaria", 
        description="Oficina de expedicion de la matricula inmobiliaria"
    )
    circulo_registral: Optional[str] = Field(
        default=None,
        alias="VIV_circuloRegistral",
        description="Circulo registral"
    )
    direccion: Optional[str] = Field(
        default=None,
        alias="VIV_direccionInmueble",            
        description="Direccion catastral del inmueble"
    )
    ciudad: Optional[str] = Field(
        default=None,
        alias="VIV_ciudadInmueble",
        description="Ciudad del inmueble"
    )
    departamento: Optional[str] = Field(
        default=None,
        alias="VIV_departamentoInmueble",
        description="Departamento"
    )
    tipo_inmueble: Optional[str] = Field(
        default=None,
        alias="VIV_tipoInmueble",
        description="Tipo de inmueble"
    )
    descripcion: Optional[str] = Field(
        default=None,
        alias="VIV_descripcionInmueble",
        description="Descripcion adicional del inmueble"
    )


class DatosCancelacion(BaseModel):
    """Datos especificos de la cancelacion."""

    motivo: Optional[str] = Field(
        default=None,
        alias="VIV_motivoCancelacion",
        description="Motivo de la cancelacion (pago total, subrogacion, etc.)"
    )
    fecha_pago_total: Optional[str] = Field(
        default=None,
        alias="VIV_fechaPagoTotal",
        description="Fecha del pago total de la obligacion"
    )
    autorizacion_cancelacion: Optional[str] = Field(
        default=None,
        alias="VIV_autorizacionCancelacion",
        description="Numero o referencia de autorizacion de cancelacion"
    )
    fecha_autorizacion: Optional[str] = Field(
        default=None,
        alias="VIV_fechaAutorizacion",
        description="Fecha de la autorizacion"
    )
    paz_y_salvo: Optional[bool] = Field(
        default=None,
        alias="VIV_pazYSalvo",
        description="Indica si se emite paz y salvo"
    )


class MinutaCancelacionSchema(BaseDocumentSchema):
    """Schema completo para Minuta de Cancelacion de Hipoteca."""

    metadata: MetadataMinutaCancelacion = Field(
        default_factory=MetadataMinutaCancelacion,
        description="Metadata de la minuta de cancelacion"
    )
    acreedor: Acreedor = Field(
        default_factory=Acreedor,
        description="Informacion del acreedor hipotecario"
    )
    deudores: List[Deudor] = Field(
        default_factory=list,
        description="Lista de deudores de la obligacion"
    )
    obligacion: ObligacionCancelada = Field(
        default_factory=ObligacionCancelada,
        description="Informacion de la obligacion que se cancela"
    )
    inmuebles: List[InmuebleGarantia] = Field(
        default_factory=list,
        description="Inmuebles que servian como garantia"
    )
    cancelacion: DatosCancelacion = Field(
        default_factory=DatosCancelacion,
        description="Datos de la cancelacion"
    )
    declaraciones: Optional[str] = Field(
        default=None,
        alias="VIV_declaraciones",
        description="Declaraciones incluidas en la minuta"
    )
    observaciones: Optional[str] = Field(
        default=None,
        alias="VIV_observaciones",
        description="Observaciones adicionales"
    )
