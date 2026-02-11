from typing import List, Optional
from pydantic import BaseModel, Field

from .base_schema import BaseDocumentSchema


class MetadataEstudioTitulos(BaseModel):
    """Metadata especifica del estudio de titulos."""

    numero_radicado: Optional[str] = Field(
        default=None,
        description="Numero de radicado del estudio"
    )
    fecha_estudio: Optional[str] = Field(
        default=None,
        description="Fecha de realizacion del estudio"
    )
    notaria: Optional[str] = Field(
        default=None,
        description="Notaria donde se realizo el estudio"
    )
    circulo_registral: Optional[str] = Field(
        default=None,
        description="Circulo registral correspondiente"
    )
    elaborado_por: Optional[str] = Field(
        default=None,
        description="Nombre del profesional que elaboro el estudio"
    )


class InmuebleInfo(BaseModel):
    """Informacion del inmueble."""

    matricula_inmobiliaria: Optional[str] = Field(
        default=None,
        description="Numero de matricula inmobiliaria"
    )
    direccion: Optional[str] = Field(
        default=None,
        description="Direccion del inmueble"
    )
    tipo_inmueble: Optional[str] = Field(
        default=None,
        description="Tipo de inmueble (casa, apartamento, lote, etc.)"
    )
    area_construida: Optional[str] = Field(
        default=None,
        description="Area construida en metros cuadrados"
    )
    area_terreno: Optional[str] = Field(
        default=None,
        description="Area del terreno en metros cuadrados"
    )
    linderos: Optional[str] = Field(
        default=None,
        description="Descripcion de los linderos del inmueble"
    )
    estrato: Optional[str] = Field(
        default=None,
        description="Estrato socioeconomico"
    )
    ciudad: Optional[str] = Field(
        default=None,
        description="Ciudad donde se ubica el inmueble"
    )
    departamento: Optional[str] = Field(
        default=None,
        description="Departamento donde se ubica el inmueble"
    )


class Propietario(BaseModel):
    """Informacion de un propietario."""

    nombre: Optional[str] = Field(
        default=None,
        description="Nombre completo del propietario"
    )
    tipo_identificacion: Optional[str] = Field(
        default=None,
        description="Tipo de documento (CC, NIT, CE, etc.)"
    )
    identificacion: Optional[str] = Field(
        default=None,
        description="Numero de identificacion"
    )
    porcentaje_propiedad: Optional[str] = Field(
        default=None,
        description="Porcentaje de propiedad sobre el inmueble"
    )
    estado_civil: Optional[str] = Field(
        default=None,
        description="Estado civil del propietario"
    )


class AnotacionTradicion(BaseModel):
    """Informacion de una anotacion en la tradicion."""

    numero_anotacion: Optional[str] = Field(
        default=None,
        description="Numero de la anotacion"
    )
    fecha: Optional[str] = Field(
        default=None,
        description="Fecha de la anotacion"
    )
    tipo_acto: Optional[str] = Field(
        default=None,
        description="Tipo de acto juridico (compraventa, hipoteca, etc.)"
    )
    especificacion: Optional[str] = Field(
        default=None,
        description="Especificacion o detalle del acto"
    )
    numero_escritura: Optional[str] = Field(
        default=None,
        description="Numero de escritura publica"
    )
    notaria: Optional[str] = Field(
        default=None,
        description="Notaria donde se otorgo la escritura"
    )
    personas_de: Optional[str] = Field(
        default=None,
        description="Persona(s) que transfieren o gravan"
    )
    personas_a: Optional[str] = Field(
        default=None,
        description="Persona(s) que adquieren o benefician"
    )


class Gravamen(BaseModel):
    """Informacion de un gravamen sobre el inmueble."""

    tipo: Optional[str] = Field(
        default=None,
        description="Tipo de gravamen (hipoteca, embargo, etc.)"
    )
    beneficiario: Optional[str] = Field(
        default=None,
        description="Entidad o persona beneficiaria del gravamen"
    )
    monto: Optional[str] = Field(
        default=None,
        description="Monto del gravamen"
    )
    fecha_constitucion: Optional[str] = Field(
        default=None,
        description="Fecha de constitucion del gravamen"
    )
    numero_anotacion: Optional[str] = Field(
        default=None,
        description="Numero de anotacion en el folio"
    )
    estado: Optional[str] = Field(
        default=None,
        description="Estado actual (vigente, cancelado, etc.)"
    )


class Limitacion(BaseModel):
    """Informacion de una limitacion al dominio."""

    tipo: Optional[str] = Field(
        default=None,
        description="Tipo de limitacion (usufructo, condicion resolutoria, etc.)"
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripcion de la limitacion"
    )
    beneficiario: Optional[str] = Field(
        default=None,
        description="Beneficiario de la limitacion"
    )
    fecha: Optional[str] = Field(
        default=None,
        description="Fecha de la limitacion"
    )
    estado: Optional[str] = Field(
        default=None,
        description="Estado actual de la limitacion"
    )


class EstudioTitulosSchema(BaseDocumentSchema):
    """Schema completo para Estudio de Titulos."""

    metadata: MetadataEstudioTitulos = Field(
        default_factory=MetadataEstudioTitulos,
        description="Metadata del estudio de titulos"
    )
    inmueble: InmuebleInfo = Field(
        default_factory=InmuebleInfo,
        description="Informacion del inmueble objeto del estudio"
    )
    propietarios: List[Propietario] = Field(
        default_factory=list,
        description="Lista de propietarios actuales del inmueble"
    )
    tradicion: List[AnotacionTradicion] = Field(
        default_factory=list,
        description="Historia de la tradicion del inmueble"
    )
    gravamenes: List[Gravamen] = Field(
        default_factory=list,
        description="Gravamenes registrados sobre el inmueble"
    )
    limitaciones: List[Limitacion] = Field(
        default_factory=list,
        description="Limitaciones al dominio del inmueble"
    )
    concepto_juridico: Optional[str] = Field(
        default=None,
        description="Concepto juridico sobre la viabilidad del negocio"
    )
    observaciones: Optional[str] = Field(
        default=None,
        description="Observaciones adicionales del estudio"
    )
    recomendaciones: Optional[str] = Field(
        default=None,
        description="Recomendaciones del profesional"
    )
