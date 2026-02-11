from typing import List, Optional
from pydantic import BaseModel, Field

from .base_schema import BaseDocumentSchema


class MetadataMinutaConstitucion(BaseModel):
    """Metadata especifica de la minuta de constitucion."""

    numero_escritura: Optional[str] = Field(
        default=None,
        alias="VIV_numeroEscrituraPublica",      
        description="Numero de escritura publica"
    )
    fecha: Optional[str] = Field(
        default=None,
        alias="VIV_fechaEscrituraPublica",       
        description="Fecha de la escritura"
    )
    notaria: Optional[str] = Field(
        default=None,
        alias="VIV_notariaEscrituraPublica",     
        description="Notaria donde se otorga"
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


class AcreedorHipotecario(BaseModel):
    """Informacion del acreedor hipotecario."""

    nombre: Optional[str] = Field(
        default=None,
        alias="VIV_nombreAcreedor",
        description="Razon social del acreedor"
    )
    tipo_entidad: Optional[str] = Field(
        default=None,
        alias="VIV_tipoEntidad",
        description="Tipo de entidad (banco, cooperativa, etc.)"
    )
    nit: Optional[str] = Field(
        default=None,
        alias="VIV_nitAcreedor",
        description="NIT del acreedor"
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
    direccion: Optional[str] = Field(
        default=None,
        alias="VIV_direccionAcreedor",
        description="Direccion de la entidad"
    )
    ciudad: Optional[str] = Field(
        default=None,
        alias="VIV_ciudadAcreedor",
        description="Ciudad de la entidad"
    )


class DeudorHipotecario(BaseModel):
    """Informacion del deudor hipotecario (comprador)."""

    nombre: Optional[str] = Field(
        default=None,
        alias="VIV_Compradores",                
        description="Nombre completo del comprador/deudor"
    )
    tipo_identificacion: Optional[str] = Field(
        default=None,
        alias="VIV_tipoIdentificacionComprador",
        description="Tipo de documento"
    )
    identificacion: Optional[str] = Field(
        default=None,
        alias="VIV_identificacionCompradores",  
        description="Numero de identificacion del comprador"
    )
    estado_civil: Optional[str] = Field(
        default=None,
        alias="VIV_estadoCivilDeudor",
        description="Estado civil"
    )
    direccion: Optional[str] = Field(
        default=None,
        alias="VIV_direccionDeudor",
        description="Direccion de residencia"
    )
    ciudad: Optional[str] = Field(
        default=None,
        alias="VIV_ciudadDeudor",
        description="Ciudad de residencia"
    )
    telefono: Optional[str] = Field(
        default=None,
        alias="VIV_telefonoDeudor",
        description="Telefono de contacto"
    )
    correo_electronico: Optional[str] = Field(
        default=None,
        alias="VIV_correoDeudor",
        description="Correo electronico"
    )
    es_codeudor: Optional[bool] = Field(
        default=False,
        alias="VIV_esCodeudor",
        description="Indica si es codeudor"
    )


class CondicionesCredito(BaseModel):
    """Condiciones del credito hipotecario."""

    # --- Monto y moneda ---
    monto_credito: Optional[str] = Field(
        default=None,
        alias="GBL_Valordeprestamo",           
        description="Valor del prestamo"
    )
    moneda: Optional[str] = Field(
        default=None,
        alias="VIV_monedaPrestamo",
        description="Moneda del credito"
    )
    monto_en_letras: Optional[str] = Field(
        default=None,
        alias="VIV_montoPrestamoLetras",       
        description="Monto del credito en letras (general)"
    )

    # --- Valor de compraventa ---
    valor_compraventa: Optional[str] = Field(
        default=None,
        alias="TPC_ValorComercial",            
        description="Valor de compra venta del inmueble"
    )

    # --- Plazo ---
    plazo_meses: Optional[str] = Field(
        default=None,
        alias="VIV_plazoMeses",
        description="Plazo del credito en meses"
    )
    plazo_anos: Optional[str] = Field(
        default=None,
        alias="VIV_plazoAnos",
        description="Plazo del credito en anos"
    )

    # --- Tasas ---
    tasa_interes: Optional[str] = Field(
        default=None,
        alias="VIV_tasaInteres",
        description="Tasa de interes pactada"
    )
    tipo_tasa: Optional[str] = Field(
        default=None,
        alias="VIV_tipoTasa",
        description="Tipo de tasa (fija, variable, DTF, etc.)"
    )
    spread: Optional[str] = Field(
        default=None,
        alias="VIV_spread",
        description="Spread o puntos adicionales"
    )
    tasa_mora: Optional[str] = Field(
        default=None,
        alias="VIV_tasaMora",
        description="Tasa de interes moratorio"
    )

    # --- Destino y línea ---
    destino_credito: Optional[str] = Field(
        default=None,
        alias="VIV_destinoCredito",
        description="Destino del credito (vivienda, libre inversion, etc.)"
    )
    linea_credito: Optional[str] = Field(
        default=None,
        alias="VIV_lineaCredito",
        description="Linea de credito"
    )

    # --- Amortización ---
    sistema_amortizacion: Optional[str] = Field(
        default=None,
        alias="VIV_sistemaAmortizacion",
        description="Sistema de amortizacion (cuota fija, UVR, etc.)"
    )

    # --- Cuotas (mensuales) ---
    valor_cuota_mensual: Optional[str] = Field(
        default=None,
        alias="VIV_valorCuotaMensual",         
        description="Valor de la cuota mensual"
    )
    fecha_primer_pago: Optional[str] = Field(
        default=None,
        alias="VIV_fechaPrimerPago",
        description="Fecha del primer pago"
    )

    # --- NUEVOS CAMPOS PARA EL SEGUNDO PÁRRAFO ---
    valor_en_letras_primer_parrafo: Optional[str] = Field(
        default=None,
        alias="BO_Valor en letras",            
        description="Valor en letras (primer paragrafo)"
    )
    numero_cuotas: Optional[str] = Field(
        default=None,
        alias="VIV_numeroCuotas",              
        description="Numero de cuotas (segundo paragrafo)"
    )
    numero_cuotas_letras: Optional[str] = Field(
        default=None,
        alias="VIV_numeroCuotasLetras",        
        description="Numero de cuotas en letras (segundo paragrafo)"
    )
    valor_cuotas: Optional[str] = Field(
        default=None,
        alias="VIV_valorCuotas",              
        description="Valor de las cuotas (segundo paragrafo)"
    )
    valor_cuotas_letras: Optional[str] = Field(
        default=None,
        alias="VIV_valorCuotasLetras",         
        description="Valor de las cuotas en letras (segundo paragrafo)"
    )
    valor_prestamo_letras_segundo_parrafo: Optional[str] = Field(
        default=None,
        alias="VIV_OfertaValorLetras",         
        description="Valor del prestamo en letras (segundo paragrafo)"
    )


class InmuebleHipotecado(BaseModel):
    """Informacion del inmueble a hipotecar."""

    matricula_inmobiliaria: Optional[str] = Field(
        default=None,
        alias="VIV_PrestamoDireccionMatricula", 
        description="Numero de matricula inmobiliaria"
    )
    circulo_registral: Optional[str] = Field(
        default=None,
        alias="VIV_circuloRegistral",
        description="Circulo registral"
    )
    direccion: Optional[str] = Field(
        default=None,
        alias="VIV_direccionInmueble",          
        description="Direccion del inmueble"
    )
    ciudad: Optional[str] = Field(
        default=None,
        alias="VIV_ciudadInmueble",
        description="Ciudad"
    )
    departamento: Optional[str] = Field(
        default=None,
        alias="VIV_departamentoInmueble",
        description="Departamento"
    )
    tipo_inmueble: Optional[str] = Field(
        default=None,
        alias="VIV_tipoPredio",                
        description="Tipo de inmueble"
    )
    area_construida: Optional[str] = Field(
        default=None,
        alias="VIV_areaConstruida",
        description="Area construida en m2"
    )
    area_terreno: Optional[str] = Field(
        default=None,
        alias="VIV_areaTerreno",
        description="Area del terreno en m2"
    )
    linderos: Optional[str] = Field(
        default=None,
        alias="VIV_descripcionLinderos",      
        description="Descripcion de linderos"
    )
    estrato: Optional[str] = Field(
        default=None,
        alias="VIV_estrato",
        description="Estrato socioeconomico"
    )
    avaluo_comercial: Optional[str] = Field(
        default=None,
        alias="VIV_avaluoComercial",
        description="Valor del avaluo comercial"
    )
    fecha_avaluo: Optional[str] = Field(
        default=None,
        alias="VIV_fechaAvaluo",
        description="Fecha del avaluo"
    )
    perito_avaluador: Optional[str] = Field(
        default=None,
        alias="VIV_peritoAvaluador",
        description="Nombre del perito avaluador"
    )


class CondicionesGarantia(BaseModel):
    """Condiciones y clausulas de la garantia hipotecaria."""

    tipo_garantia: Optional[str] = Field(
        default=None,
        alias="VIV_tipoGarantia",
        description="Tipo de garantia (hipoteca abierta, cerrada)"
    )
    grado_hipoteca: Optional[str] = Field(
        default=None,
        alias="VIV_gradoHipoteca",             
        description="Grado de la hipoteca (primero, segundo)"
    )
    clausula_aceleracion: Optional[bool] = Field(
        default=None,
        alias="VIV_clausulaAceleracion",
        description="Incluye clausula de aceleracion"
    )
    clausula_venta_judicial: Optional[bool] = Field(
        default=None,
        alias="VIV_clausulaVentaJudicial",
        description="Incluye clausula de venta judicial"
    )
    seguro_incendio_terremoto: Optional[bool] = Field(
        default=None,
        alias="VIV_seguroIncendioTerremoto",
        description="Requiere seguro contra incendio y terremoto"
    )
    seguro_vida_deudores: Optional[bool] = Field(
        default=None,
        alias="VIV_seguroVidaDeudores",
        description="Requiere seguro de vida de deudores"
    )
    aseguradora: Optional[str] = Field(
        default=None,
        alias="VIV_aseguradora",
        description="Compania aseguradora"
    )
    numero_poliza: Optional[str] = Field(
        default=None,
        alias="VIV_numeroPoliza",
        description="Numero de poliza de seguros"
    )
    prohibicion_enajenar: Optional[bool] = Field(
        default=None,
        alias="VIV_prohibicionEnajenar",
        description="Prohibicion de enajenar sin autorizacion"
    )
    prohibicion_arrendar: Optional[bool] = Field(
        default=None,
        alias="VIV_prohibicionArrendar",
        description="Prohibicion de arrendar sin autorizacion"
    )
    otras_prohibiciones: List[str] = Field(
        default_factory=list,
        alias="VIV_otrasProhibiciones",
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
        description="Lista de compradores/deudores (con VIV_Compradores, VIV_identificacionCompradores)"
    )
    credito: CondicionesCredito = Field(
        default_factory=CondicionesCredito,
        description="Condiciones del credito (incluye TPC_ValorComercial, GBL_Valordeprestamo, etc.)"
    )
    inmuebles: List[InmuebleHipotecado] = Field(
        default_factory=list,
        description="Inmuebles objeto de la hipoteca"
    )
    condiciones_garantia: CondicionesGarantia = Field(
        default_factory=CondicionesGarantia,
        description="Condiciones y clausulas de la garantia (incluye VIV_gradoHipoteca)"
    )

    # --- NUEVOS CAMPOS A NIVEL RAÍZ (Vendedor, Cesantías, Recursos propios) ---
    nombre_vendedor: Optional[str] = Field(
        default=None,
        alias="VIV_nombreVendedor",            
        description="Nombre del vendedor del inmueble"
    )
    valor_cesantias: Optional[str] = Field(
        default=None,
        alias="VIV_valorCesantias",           
        description="Monto de cesantías utilizadas como parte del pago"
    )
    recursos_propios: Optional[str] = Field(
        default=None,
        alias="VIV_recursosPropios",           
        description="Monto de recursos propios aportados"
    )

    declaraciones_deudor: Optional[str] = Field(
        default=None,
        alias="VIV_declaracionesDeudor",
        description="Declaraciones del deudor"
    )
    autorizaciones: Optional[str] = Field(
        default=None,
        alias="VIV_autorizaciones",
        description="Autorizaciones otorgadas"
    )
    observaciones: Optional[str] = Field(
        default=None,
        alias="VIV_observaciones",
        description="Observaciones adicionales"
    )
